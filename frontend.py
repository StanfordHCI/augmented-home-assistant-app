from backend import render_home, remove_ceiling, closest_node
from settings import *
from simulate import sim_in_unity
from controller import *
import numpy as np
import open3d as o3d
import time
import random

MAX_NUM_BUTTONS = 20
NUM_IOTS = 11
SCRIPT_IDX = 0


class AppWindow:
    def __init__(self, width, height, only_UI=False, sensors=None):
        self.iot_pos = [[3.8786, 1.2500, -4.2092],
                        [-4.1498, 1.2500, -6.2607],
                        [-1.0831, 1.2500, -12.8629],
                        [-3.8101, 1.2500, 1.1884],
                        [2.8155, 1.2500, 3.8129],
                        [3.5415, 1.2500, -0.4654],
                        [-1.9514, 1.2500, -10.4198],
                        [-2.4120, 1.2500, 1.0357],
                        [-1.5379, 1.2500, -14.3466],
                        [3, 1.2500, 7],
                        [1.1244, 1.2500, 7]]
        self.only_UI = only_UI
        self.settings = Settings()
        self.width = width
        self.height = height
        self.settings.new_ibl_name = gui.Application.instance.resource_path + "/" + "default"
        self.window = gui.Application.instance.create_window("Augmented Home Assistant", self.width, self.height)
        if not self.only_UI:
            self._scene = gui.SceneWidget()
            self._scene.scene = rendering.Open3DScene(self.window.renderer)
            self._scene.set_on_mouse(self._on_mouse_click_scene)
        em = self.window.theme.font_size
        self.separation_height = int(round(0.5 * em))
        self.separation_height_small = int(round(0.1 * em))
        self.separation_height_big = int(round(3 * em))
        self.panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 1 * em, 0.25 * em))
        self.history = gui.CollapsableVert("History", 0.25 * em, gui.Margins(em, 0, 0, 0))
        self.config = gui.CollapsableVert("Automation", 0.25 * em, gui.Margins(em, 0, 0, 0))
        self.program_layout = gui.Vert()

        # Local button list
        self.all_buttons = []
        self.all_button_states = ["0 0"] * MAX_NUM_BUTTONS
        self.all_button_labels = []
        self.all_button_and_or = []
        self.all_button_h_layout = []
        self.all_3d_labels = []
        self.all_combo_items_id = None
        self.all_combo_current_item_id = None
        self.all_histories, self.all_history_changed_idx = sim_in_unity(SCRIPT_IDX, [], get_all_history=True)

        if not self.only_UI:
            self.all_iots = sensors
        else:
            self.all_iots = []
        self.curr_button = None
        self.test_button = None
        self.initialize_all_buttons()

        # Add all collapsable
        if self.only_UI:
            self.add_iots()
        else:
            self.add_history()
        self.add_configs()
        self.add_controls()

        # Apply layout
        self._on_apply_layout()
        self._apply_settings()

        # Initialize controller
        self.controller = Controller()

    def add_history(self):
        em = self.window.theme.font_size
        self.combo = gui.Combobox()
        fake_time = 10
        for i in range(len(self.all_histories)):
            self.combo.add_item("01/01/2022 20:{} AM".format(fake_time + i * 2))
            # self.all_combo_items.append(self.all_histories[i])
            # fake_time += random.randint(1, 3)
        # History combobox
        # combo.add_item("01/01/2022 8:12 AM")
        # combo.add_item("01/01/2022 8:15 AM")
        self.combo.set_on_selection_changed(self.on_combo)

        # Content switcher
        before_trigger = gui.Button("Before Trigger")
        before_trigger.horizontal_padding_em = 0.91
        before_trigger.vertical_padding_em = 0.1
        before_trigger.set_on_clicked(self.on_content_switch_before)

        after_trigger = gui.Button("After Trigger")
        after_trigger.horizontal_padding_em = 0.91
        after_trigger.vertical_padding_em = 0.1
        after_trigger.set_on_clicked(self.on_content_switch_after)

        after_auto = gui.Button("After Automation")
        after_auto.vertical_padding_em = 0.25
        after_auto.set_on_clicked(self.on_content_switch_auto)

        h = gui.Horiz(0.1 * em)  # row 1
        h.add_child(before_trigger)
        h.add_stretch()
        h.add_child(after_trigger)

        self.history.add_child(self.combo)
        self.history.add_fixed(self.separation_height_small)
        self.history.add_child(h)
        self.history.add_child(after_auto)
        self.history.add_fixed(self.separation_height)
        self.panel.add_child(self.history)

    def add_iots(self):
        em = self.window.theme.font_size
        self.iots = gui.CollapsableVert("IoTs", 0.25 * em, gui.Margins(em, 0, 0, 0))

        # horizontal layout
        if not self.only_UI:
            h_iot = gui.Horiz(2 * em)
        else:
            h_iot = gui.Horiz(6 * em)
        # Add Lights
        v = gui.Vert(0.5 * em)
        num_lights = 5
        v.add_child(gui.Label("Lights"))
        for i in range(num_lights):
            v.add_child(self.add_iot("L" + str(i)))
        h_iot.add_child(v)

        # Add Doors
        v2 = gui.Vert(0.5 * em)
        num_doors = 3
        v2.add_child(gui.Label("Doors"))
        for i in range(num_doors):
            v2.add_child(self.add_iot("D" + str(i)))
        h_iot.add_child(v2)

        # Add Others
        v3 = gui.Vert(0.5 * em)
        num_lamps = 3
        # v3.add_child(gui.Label("Day/Nights, "))
        # v3.add_child(gui.Label("Curtain"))
        v3.add_child(gui.Label("Lamps"))
        for i in range(num_lamps):
            v3.add_child(self.add_iot("T" + str(i)))
        h_iot.add_child(v3)

        self.iots.add_child(h_iot)
        self.iots.add_fixed(self.separation_height)
        self.panel.add_child(self.iots)

    def add_configs(self):
        self.add_a_button("When", MAX_NUM_BUTTONS, toggle_visile=False)
        self.config.add_child(self.program_layout)

        condition_button = gui.Button("Condition(s)")
        action_button = gui.Button("Action(s)")
        clear_button = gui.Button("Clear")
        test_button = gui.Button("Test")
        test_button.toggleable = True
        test_button.visible = False
        deploy_button = gui.Button("Deploy")
        condition_button.set_on_clicked(self.on_condition)
        action_button.set_on_clicked(self.on_action)
        test_button.set_on_clicked(self.on_test)
        deploy_button.set_on_clicked(self.on_deploy)
        self.test_button = test_button

        self.config.add_fixed(self.separation_height_big)
        if not self.only_UI:
            self.config.add_child(gui.Label("----------------------------------------------------"))
        else:
            self.config.add_child(
                gui.Label("---------------------------------------------------------------------------------"))
        self.config.add_child(condition_button)
        self.config.add_child(action_button)
        self.config.add_fixed(self.separation_height)
        self.config.add_child(clear_button)
        self.config.add_child(test_button)
        self.config.add_fixed(self.separation_height)
        self.config.add_child(deploy_button)
        self.panel.add_child(self.config)

    def add_controls(self):
        em = self.window.theme.font_size
        view_ctrls = gui.CollapsableVert("Controls", 0.25 * em, gui.Margins(em, 0, 0, 0))
        view_ctrls.set_is_open(False)

        ## Mouse controls
        self._fly_button = gui.Button("Fly")
        self._fly_button.horizontal_padding_em = 0.5
        self._fly_button.vertical_padding_em = 0
        self._fly_button.set_on_clicked(self._set_mouse_mode_fly)
        self._model_button = gui.Button("Model")
        self._model_button.horizontal_padding_em = 0.5
        self._model_button.vertical_padding_em = 0
        self._model_button.set_on_clicked(self._set_mouse_mode_model)

        ## Show axes
        self._show_axes = gui.Checkbox("Show axes")
        # self._show_axes.checked = True
        self._show_axes.set_on_checked(self._on_show_axes)

        ## Remove ceiling
        self._remove_ceiling = gui.Checkbox("Remove ceiling")
        self._remove_ceiling.checked = True  # remove the ceiling on default
        self._remove_ceiling.set_on_checked(self._on_remove_ceiling)

        ## Remove ceiling
        self._show_labels = gui.Checkbox("Show labels")
        self._show_labels.checked = False  # remove the ceiling on default
        self._show_labels.set_on_checked(self._on_show_labels)

        ## Add the previous two items
        h = gui.Horiz(0.25 * em)  # row 1
        h.add_child(self._fly_button)
        h.add_child(self._model_button)
        view_ctrls.add_fixed(self.separation_height)
        view_ctrls.add_child(h)
        view_ctrls.add_fixed(self.separation_height)
        view_ctrls.add_child(self._show_axes)
        view_ctrls.add_fixed(self.separation_height)
        view_ctrls.add_child(self._remove_ceiling)
        view_ctrls.add_fixed(self.separation_height)
        view_ctrls.add_child(self._show_labels)
        view_ctrls.add_fixed(self.separation_height)

        ## Point size
        self._point_size = gui.Slider(gui.Slider.INT)
        self._point_size.set_limits(1, 10)
        self._point_size.set_on_value_changed(self._on_point_size)
        grid = gui.VGrid(2, 0.25 * em)
        grid.add_child(gui.Label("Point size"))
        grid.add_child(self._point_size)
        view_ctrls.add_child(grid)
        view_ctrls.add_fixed(self.separation_height)
        self.panel.add_fixed(self.separation_height)
        self.panel.add_child(view_ctrls)

    def on_content_switch_after(self):
        print("on_content_switch called")
        # if self.all_combo_current_item_id + 1 < len(self.all_histories):
        iot_states = self.all_histories[self.all_combo_current_item_id]
        print(iot_states)
        geo = render_home(iot_states)
        self.my_load(geometry=geo)

    def on_content_switch_before(self):
        print("on_content_switch before called")
        if self.all_combo_current_item_id - 1 >= 0:
            iot_states = self.all_histories[self.all_combo_current_item_id - 1]
            print(iot_states)
            geo = render_home(iot_states)
            self.my_load(geometry=geo)

    def on_content_switch_auto(self):
        print("on_content_switch called")
        # self.test_button.is_on = True
        deploy_data = self.get_test_deploy_data()
        self.controller.initialize(deploy_data)
        correct_trigger = deploy_data[0]

        # trigger = self.all_history_changed_idx[self.all_combo_current_item_id]
        # use the correct_trigger to force it to render no matter what...
        new_states = self.controller.check_udpate(correct_trigger, self.all_iots)
        if new_states:
            geo = render_home(new_states)
            self.my_load(geometry=geo)
            self.all_iots = new_states

    def on_combo(self, new_val, new_idx):
        print("combo called")
        self.all_combo_current_item_id = self.all_combo_items_id[new_idx]
        print(new_idx, new_val)

    def on_condition(self):
        reversed_all_buttons = self.all_buttons[::-1]
        latest_index_reverse = 0
        for i in range(len(reversed_all_buttons)):
            if reversed_all_buttons[i].visible:
                latest_label = self.all_button_labels[::-1][i].text
                latest_index_reverse = i
                break
        if latest_label == "When":
            self.add_a_button("If", latest_index_reverse, toggle_visile=False)
        elif latest_label == "If" or latest_label == "And":
            self.add_a_button("And", latest_index_reverse, toggle_visile=True)
        elif latest_label == "Or":
            self.add_a_button("Or", latest_index_reverse, toggle_visile=True)
        elif latest_label == "Do":
            self.add_a_button("Else", latest_index_reverse, toggle_visile=False)
        else:
            print("Not available!")

    def on_action(self):
        reversed_all_buttons = self.all_buttons[::-1]
        latest_index_reverse = 0
        for i in range(len(reversed_all_buttons)):
            if reversed_all_buttons[i].visible:
                latest_label = self.all_button_labels[::-1][i].text
                latest_index_reverse = i
                break
        # if latest_label == "When" or latest_label == "If" or latest_label == "And"
        # or latest_label == "Or" or latest_label == "Else":
        self.add_a_button("Do", latest_index_reverse, toggle_visile=False)
        # else:  # latest_label == "Do":
        #     print("Not available!")

    def on_test(self):
        if self.test_button.is_on:
            self.test_button.text = "Testing"
            self.controller.initialize(self.get_test_deploy_data())
        else:
            self.test_button.text = "Test"

    def on_deploy(self):
        sim_in_unity(SCRIPT_IDX, self.get_test_deploy_data())

    def get_test_deploy_data(self):
        all_shown_labels = [label.text for label in self.all_button_labels if label.visible]
        my_len = len(all_shown_labels)
        all_iot_states = self.all_button_states[0:my_len]

        trigger = ""
        conditions = []
        and_or = 0  # 0 is and, 1 is or
        if_action = []
        else_action = []

        else_start_idx = my_len
        for i in range(my_len):
            if all_shown_labels[i] == "When":
                trigger = all_iot_states[i]
            elif all_shown_labels[i] in ["If", "Or", "And"]:
                conditions.append(all_iot_states[i])
                if all_shown_labels[i] == "Or":
                    and_or = 1
            elif all_shown_labels[i] == "Do":
                if_action.append(all_iot_states[i])
            elif all_shown_labels[i] == "Else":
                else_start_idx = i
                break
        for i in range(else_start_idx, my_len):
            if all_shown_labels[i] in ["Else", "Do"]:
                else_action.append(all_iot_states[i])
        return [trigger, conditions, and_or, if_action, else_action]

    def add_a_button(self, name, latest_index_reverse, toggle_visile=False):
        print(latest_index_reverse)
        if latest_index_reverse >= 1:  # means there are invisiable button, we should use them first
            print("reusing button")
            button = self.all_buttons[::-1][latest_index_reverse - 1]
            select_label = self.all_button_labels[::-1][latest_index_reverse - 1]
            and_or_toggle = self.all_button_and_or[::-1][latest_index_reverse - 1]
            h_layout = self.all_button_h_layout[::-1][latest_index_reverse - 1]

            button.text = "Select"
            select_label.text = name

            button.visible = True
            if toggle_visile:
                and_or_toggle.visible = True
            select_label.visible = True
            h_layout.visible = True
            self.window.add_child(self.panel)  # this will update the layout

    def initialize_all_buttons(self):
        em = self.window.theme.font_size
        for i in range(MAX_NUM_BUTTONS):
            # self.program_layout.add_fixed(self.separation_height)
            # margin: left, top, right, bottom
            h_layout = gui.Horiz(0, gui.Margins(0 * em, 0.6 * em, 0.5 * em,
                                                0.5 * em))
            select_label = gui.Label("")
            # ZHUOYUe add toggle
            and_or_toggle = gui.ToggleSwitch("and/or")
            button_index = len(self.all_buttons)
            my_new_function = self.create_on_and_or_function(button_index)
            and_or_toggle.set_on_clicked(my_new_function)
            h_layout.add_child(select_label)
            h_layout.add_child(and_or_toggle)

            self.program_layout.add_child(h_layout)
            select_button = gui.Button("Select")
            my_new_function = self.create_on_select_function(select_button)
            select_button.toggleable = True
            select_button.set_on_clicked(my_new_function)
            select_button.visible = False
            and_or_toggle.visible = False
            select_label.visible = False
            h_layout.visible = False
            self.all_buttons.append(select_button)
            self.all_button_labels.append(select_label)
            self.all_button_and_or.append(and_or_toggle)
            self.all_button_h_layout.append(h_layout)
            self.program_layout.add_child(select_button)

    def add_iot(self, name):
        switch = gui.ToggleSwitch(name)
        switch_index = len(self.all_iots)
        my_new_function = self.create_on_switch_function(name, switch_index)
        switch.set_on_clicked(my_new_function)
        self.all_iots.append(switch)
        return switch

    def get_iot_states(self):
        iot_states = []
        if not self.only_UI:
            iot_states = self.all_iots
        else:
            for iot in self.all_iots:
                iot_states.append(int(iot.is_on))
        return iot_states

    def create_on_select_function(*args, **kwargs):
        """
        This will help us dynamically create functions with given id and type
        because the built-in set_on_clicked doesn't allow passing different arguments
        so we have to create different functions for that
        """
        self = args[0]
        button = args[1]

        # if the current button is action button, the text will be different

        def function_template(*args, **kwargs):
            self.curr_button = button
            button.text = "Selecting an IoT..."

        return function_template

    def create_on_and_or_function(*args, **kwargs):
        """
        """
        self = args[0]
        button_index = args[1]

        def function_template(*args, **kwargs):
            switch_is_on = self.all_button_and_or[button_index].is_on
            if switch_is_on:
                self.all_button_labels[button_index].text = "Or"
            else:
                self.all_button_labels[button_index].text = "And"

        return function_template

    def create_on_switch_function(*args, **kwargs):
        """
        """
        self = args[0]
        switch_name = args[1]
        switch_index = args[2]

        def function_template(*args, **kwargs):
            # get the states of all toggles
            # the order is, 5 lights, 3 doors, 3 tablelamp
            iot_states = self.get_iot_states()
            print(iot_states)
            geo = render_home(iot_states)
            self.my_load(geometry=geo)
            if self.curr_button:
                curr_button_idx = self.all_buttons.index(self.curr_button)
                self.curr_button.text, self.all_button_states[curr_button_idx] = self.get_on_off_state_message(
                    self.all_iots[switch_index].is_on, curr_button_idx, switch_index)
                self.curr_button.is_on = False  # to change the color of the button
                self.curr_button = None
            if self.test_button.is_on:  # we are in the testing mode
                # time.sleep(2) # sleep doesn't really work...it's still gonna wait until the function is done...
                trigger = str(iot_states[switch_index]) + " " + str(switch_index)
                new_states = self.controller.check_udpate(trigger, iot_states)
                if new_states:
                    geo = render_home(new_states)
                    self.my_load(geometry=geo)
                    for j in range(len(iot_states)):
                        # update the toggle
                        self.all_iots[j].is_on = bool(new_states[j])

        return function_template

    def on_switch_3d(self, switch_index):
        self.all_iots[switch_index] = 1 - self.all_iots[switch_index]  # toggle the value
        print(self.all_iots)
        geo = render_home(self.all_iots)
        self.my_load(geometry=geo)
        if self.curr_button:
            curr_button_idx = self.all_buttons.index(self.curr_button)
            self.curr_button.text, self.all_button_states[curr_button_idx] = self.get_on_off_state_message(
                self.all_iots[switch_index], curr_button_idx, switch_index, is_3d_switch=True)
            self.curr_button.is_on = False  # to change the color of the button
            self.curr_button = None
        if self.test_button.is_on:  # we are in the testing mode
            # time.sleep(2) # sleep doesn't really work...it's still gonna wait until the function is done...
            trigger = str(self.all_iots[switch_index]) + " " + str(switch_index)
            new_states = self.controller.check_udpate(trigger, self.all_iots)
            if new_states:
                geo = render_home(new_states)
                self.my_load(geometry=geo)
                self.all_iots = new_states
        if curr_button_idx == 0:  ### the "When" switch
            self.combo.clear_items()
            self.all_combo_items_id = []
            fake_time = 10
            for i in range(1, len(self.all_history_changed_idx)):  # the first item is "initial" not useful
                if self.all_history_changed_idx[i] == self.all_button_states[curr_button_idx]:
                    self.combo.add_item("01/01/2022 20:{} AM".format(fake_time + i * 2))
                    self.all_combo_items_id.append(i)
            self.all_combo_current_item_id = self.all_combo_items_id[0]  # selecting the first one by default

    def get_on_off_state_message(self, is_on, curr_button_idx, curr_iot_idx, is_3d_switch=False):
        # "state_info" the 1st digit is on/off, the second digit is the index,
        # in the order of 5 lights, 3 doors, 3 lamps
        cuur_text = self.all_button_labels[curr_button_idx].text
        curr_button_is_action = cuur_text == "Do" or cuur_text == "Else"
        if is_3d_switch:
            is_on = bool(is_on)
        if curr_iot_idx <= 4:  # lights
            state_info = str(int(is_on)) + " " + str(curr_iot_idx)
            if not curr_button_is_action:
                msg = "Light " + str(curr_iot_idx) + " is on" if is_on else "Light " + str(
                    curr_iot_idx) + " is off"
            else:
                msg = "Turn on the light " + str(curr_iot_idx) if is_on else "Turn off the light " + str(
                    curr_iot_idx)

        elif curr_iot_idx <= 7:  # doors
            state_info = str(int(is_on)) + " " + str(curr_iot_idx)
            if not curr_button_is_action:  # TODO: change this 5 to len(lights)
                msg = "Door " + str(curr_iot_idx - 5) + " is open" if is_on else "Door " + str(
                    curr_iot_idx - 5) + " is closed"
            else:
                msg = "Open the door " + str(curr_iot_idx - 5) if is_on else "Close the door " + str(
                    curr_iot_idx - 5)

        else:  # if startswith "T"
            # if msg == "T0":
            #     if not self.curr_button_is_action:
            #         msg = "It is bright outside" if is_on else "It is dark outside"
            #     else:
            #         msg = "This IoT can not be selected as an action"
            # elif msg == "T1":
            #     if not self.curr_button_is_action:
            #         msg = "The curtains are open" if is_on else "The curtains are closed"
            #     else:
            #         msg = "Open the curtains" if is_on else "Close the curtains"
            state_info = str(int(is_on)) + " " + str(curr_iot_idx)  # TODO: change this 8 to len(lights) + len(doors)
            if not curr_button_is_action:
                msg = "Lamp " + str(curr_iot_idx - 8) + " is on" if is_on else "Lamp " + str(
                    curr_iot_idx - 8) + " is off"
            else:
                msg = "Turn on the lamp " + str(curr_iot_idx - 8) if is_on else "Turn off the lamp " + str(
                    curr_iot_idx - 8)
        return msg, state_info

    # def get_state_from_message(self, msg):
    #     iot_id = [int(s) for s in msg.split() if s.isdigit()][0]
    #     iot_states = 0 if "off" in msg else 1
    #     return iot_id, iot_states

    def _on_apply_layout(self):
        self.window.set_on_layout(self._on_layout)
        if not self.only_UI:
            self.window.add_child(self._scene)
        self.window.add_child(self.panel)

    def _apply_settings(self):
        if not self.only_UI:
            self._scene.scene.show_axes(self.settings.show_axes)
            self._show_axes.checked = self.settings.show_axes
            self._point_size.double_value = self.settings.material.point_size
            if self.settings.apply_material:
                self._scene.scene.update_material(self.settings.material)
                self.settings.apply_material = False
            # !!! we have to keep the following line, if not, the model is gonna look really dark
            self._scene.scene.scene.set_indirect_light_intensity(
                self.settings.ibl_intensity)

    def _on_layout(self, layout_context):
        r = self.window.content_rect
        if not self.only_UI:
            self._scene.frame = r
            width = 17 * layout_context.theme.font_size
        else:  # this controlls the width of the panel
            width = 25 * layout_context.theme.font_size
        height = min(r.height,
                     self.panel.calc_preferred_size(layout_context, gui.Widget.Constraints()).height)
        self.panel.frame = gui.Rect(r.get_right() - width, r.y, width,
                                    height)

    def _set_mouse_mode_fly(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.FLY)

    def _set_mouse_mode_model(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_MODEL)

    def _on_show_axes(self, show):
        self.settings.show_axes = self._show_axes.checked
        self._apply_settings()

    def _on_point_size(self, size):
        self.settings.material.point_size = int(size)
        self.settings.apply_material = True
        self._apply_settings()

    def _on_remove_ceiling(self, is_on):
        self.my_load()

    def _on_show_labels(self, is_on):
        if is_on:
            if not self.all_3d_labels:
                self.add_iot_3d_labels()
        else:
            if self.all_3d_labels:
                self.remove_iot_3d_labels()

    def _on_mouse_click_scene(self, event):
        if event.type == gui.MouseEvent.Type.BUTTON_DOWN and event.is_modifier_down(
                gui.KeyModifier.CTRL):
            def depth_callback(depth_image):
                x = event.x - self._scene.frame.x
                y = event.y - self._scene.frame.y
                depth = np.asarray(depth_image)[y, x]  # Note that np.asarray() reverses the axes.
                world = None
                if depth != 1.0:  # clicked on nothing (i.e. the far plane)
                    world = self._scene.scene.camera.unproject(
                        x, (self._scene.frame.height - y), depth, self._scene.frame.width,
                        self._scene.frame.height)
                if world is not None:
                    iot_idx = closest_node([world[0], world[1], world[2]], self.iot_pos)
                    print(iot_idx)
                    self.on_switch_3d(iot_idx)

            self._scene.scene.scene.render_to_depth_image(depth_callback)
            return gui.Widget.EventCallbackResult.IGNORED
        return gui.Widget.EventCallbackResult.IGNORED

    # def _on_mouse_click_scene(self, event):
    #     if event.type == gui.MouseEvent.Type.BUTTON_DOWN  and event.is_modifier_down(
    #             gui.KeyModifier.CTRL):
    #         def depth_callback():
    #             x = event.x - self._scene.frame.x
    #             y = event.y - self._scene.frame.y
    #             depth = self.depth  # Note that np.asarray() reverses the axes.
    #             world = None
    #             if depth != 1.0:  # clicked on nothing (i.e. the far plane)
    #                 world = self._scene.scene.camera.unproject(
    #                     x, (self._scene.frame.height - y), depth, self._scene.frame.width,
    #                     self._scene.frame.height)
    #             if world is not None:
    #                 iot_idx = closest_node([world[0], world[1], world[2]], self.iot_pos)
    #                 label = self._scene.add_3d_label(np.array([world[0], world[1], world[2]]), "my click")
    #                 label.color = gui.Color(1.0, 0.0, 0.0)
    #                 # print(iot_idx)
    #                 print("here1_inside")
    #                 self.on_switch_3d(iot_idx)
    #
    #         depth_callback()
    #         print("here1")
    #         return gui.Widget.EventCallbackResult.HANDLED
    #
    #     elif event.type == gui.MouseEvent.Type.BUTTON_DOWN:
    #         def depth_callback_ss(depth_image):
    #             x = event.x - self._scene.frame.x
    #             y = event.y - self._scene.frame.y
    #             depth = np.asarray(depth_image)[y, x]  # Note that np.asarray() reverses the axes.
    #             self.depth = depth
    #
    #         kkk = self._scene.scene.scene.render_to_depth_image(depth_callback_ss)
    #         print("here2")
    #         print(kkk)
    #         return gui.Widget.EventCallbackResult.HANDLED
    #     return gui.Widget.EventCallbackResult.IGNORED

    def my_load(self, geometry=None, first_time=False):
        if not self.only_UI:
            self._scene.scene.clear_geometry()
            if not geometry:
                geometry = self.geometry
            else:
                self.geometry = geometry
            if self._remove_ceiling.checked:
                geometry = remove_ceiling(geometry)
            self._scene.scene.add_geometry("__model__", geometry,
                                           self.settings.material)
            if first_time:
                # if we comment out the following two lines of code...the camera won't be rest, which is good
                bounds = geometry.get_axis_aligned_bounding_box()
                self._scene.setup_camera(60, bounds, bounds.get_center())

    def make_point_cloud(self, npts, center, radius):
        pts = np.random.uniform(-radius, radius, size=[npts, 3]) + center
        cloud = o3d.geometry.PointCloud()
        cloud.points = o3d.utility.Vector3dVector(pts)
        colors = np.random.uniform(0.0, 1.0, size=[npts, 3])
        cloud.colors = o3d.utility.Vector3dVector(colors)
        return cloud

    def add_iot_3d_labels(self):
        for i in range(len(self.iot_pos)):
            if i <= 4:  # lights
                color = gui.Color(1.0, 1.0, 1.0)
                text = "Light " + str(i)
            elif i <= 7:  # doors
                color = gui.Color(1.0, 0.0, 0.0)
                # color = gui.Color(196/256, 140/256, 99/256)
                text = "Door " + str(i - 5)
            else:
                color = gui.Color(1.0, 1.0, 0.0)
                text = "Lamp " + str(i - 8)
            label = self._scene.add_3d_label(np.array(self.iot_pos[i]), text)
            label.color = color
            self.all_3d_labels.append(label)

    def remove_iot_3d_labels(self):
        for i in range(len(self.iot_pos)):
            label = self.all_3d_labels[i]
            self._scene.remove_3d_label(label)
        self.all_3d_labels = []


def main():
    only_UI = False
    sensors = [0] * NUM_IOTS
    gui.Application.instance.initialize()
    if not only_UI:
        width = 1024
        height = 768
    else:
        width = 400
        height = 550

    w = AppWindow(width, height, only_UI=only_UI, sensors=sensors)
    if not only_UI:
        geo = render_home(sensors)
        w.my_load(geometry=geo, first_time=True)
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
