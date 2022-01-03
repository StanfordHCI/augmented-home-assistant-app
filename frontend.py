from backend import render_home, remove_ceiling
from settings import *
from simulate import sim_in_unity
import re
import time

MAX_NUM_BUTTONS = 20


class AppWindow:
    def __init__(self, width, height):
        self.settings = Settings()
        self.width = width
        self.height = height
        self.settings.new_ibl_name = gui.Application.instance.resource_path + "/" + "default"
        self.window = gui.Application.instance.create_window("Augmented Home Assistant", self.width, self.height)
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(self.window.renderer)
        em = self.window.theme.font_size
        self.separation_height = int(round(0.5 * em))
        self.separation_height_small = int(round(0.1 * em))
        self.separation_height_big = int(round(3 * em))
        self.panel = gui.Vert(0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))

        # Local button list
        self.all_buttons = []
        self.all_button_states = ["0 0"] * MAX_NUM_BUTTONS
        self.all_button_labels = []
        self.all_button_and_or = []
        self.all_iots = []
        self.curr_button = None

        # Add all collapsable
        self.add_iots()
        self.add_configs()
        self.add_controls()

        # Apply layout
        self._on_apply_layout()
        self._apply_settings()

    def add_iots(self):
        em = self.window.theme.font_size
        self.iots = gui.CollapsableVert("IoTs", 0.25 * em, gui.Margins(em, 0, 0, 0))

        # horizontal layout
        h_iot = gui.Horiz(2 * em)

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
        em = self.window.theme.font_size
        self.config = gui.CollapsableVert("Configuration", 0.25 * em, gui.Margins(em, 0, 0, 0))
        self.program_layout = gui.Vert()

        self.add_a_button("When", False, 0)
        self.config.add_child(self.program_layout)

        condition_button = gui.Button("Condition(s)")
        action_button = gui.Button("Action(s)")
        clear_button = gui.Button("Clear")
        # test_button = gui.Button("Test This Automation")
        test_button = gui.Button("Test")
        condition_button.set_on_clicked(self.on_condition)
        action_button.set_on_clicked(self.on_action)
        test_button.set_on_clicked(self.on_test)

        self.config.add_fixed(self.separation_height_big)
        self.config.add_child(gui.Label("-------------------------------------------------------"))
        self.config.add_child(condition_button)
        self.config.add_child(action_button)
        self.config.add_child(clear_button)
        self.config.add_fixed(self.separation_height)
        self.config.add_child(test_button)
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
        self._show_axes.set_on_checked(self._on_show_axes)

        ## Remove ceiling
        self._remove_ceiling = gui.Checkbox("Remove ceiling")
        self._remove_ceiling.set_on_checked(self._on_remove_ceiling)

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

    def on_condition(self):
        reversed_all_buttons = self.all_buttons[::-1]
        latest_label = "when"
        latest_index_reverse = 0
        for i in range(len(reversed_all_buttons)):
            if reversed_all_buttons[i].visible:
                latest_label = self.all_button_labels[::-1][i].text
                latest_index_reverse = i
                break
        if latest_label == "When":
            self.add_a_button("If", False, latest_index_reverse)
        elif latest_label == "If" or latest_label == "And":
            self.add_a_button("And", False, latest_index_reverse, toggle_visile=True)
        elif latest_label == "Or":
            self.add_a_button("Or", False, latest_index_reverse, toggle_visile=True)
        elif latest_label == "Do":
            self.add_a_button("Else", True, latest_index_reverse)
        else:
            print("Not available!")

    def on_action(self):
        reversed_all_buttons = self.all_buttons[::-1]
        latest_label = "when"
        latest_index_reverse = 0
        for i in range(len(reversed_all_buttons)):
            if reversed_all_buttons[i].visible:
                latest_label = self.all_button_labels[::-1][i].text
                latest_index_reverse = i
                break
        # if latest_label == "When" or latest_label == "If" or latest_label == "And" or latest_label == "Or" or latest_label == "Else":
        self.add_a_button("Do", True, latest_index_reverse)
        # else:  # latest_label == "Do":
        #     print("Not available!")

    def on_test(self):
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

        sim_in_unity(0, [trigger, conditions, and_or, if_action, else_action])

        # testtt = ['1 5', [], 0, ['0 3', '0 4', '0 10', '1 0'], []]
        # sim_in_unity(0, testtt)

        # condition
        # do_button = all_shown_buttons[1]
        # do_label = all_shown_labels[1]
        #
        # when_iot_id, when_iot_states = self.get_state_from_message(when_button.text)
        # do_iot_id, do_iot_states = self.get_state_from_message(do_button.text)
        #
        # self.all_iots[when_iot_id].is_on = bool(when_iot_states)
        # iot_states = [1, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        # print(iot_states)
        # geo = render_home(iot_states)
        # self.my_load(geometry=geo)
        # time.sleep(10)
        # iot_states = [1, 1, 0, 0, 0, 0, 0, 0, 0, 0]
        # print(iot_states)
        # geo = render_home(iot_states)
        # self.my_load(geometry=geo)

    def add_a_button(self, name, is_action_button, latest_index_reverse, toggle_visile=False):
        em = self.window.theme.font_size
        if latest_index_reverse >= 1:  # means there are invisiable button, we should use them first
            button = self.all_buttons[::-1][latest_index_reverse - 1]
            button.visible = True
            button.text = "Select"
            self.all_button_labels[::-1][latest_index_reverse - 1].text = name
            my_new_function = self.create_on_select_function(button, is_action_button)
            button.toggleable = True
            button.set_on_clicked(my_new_function)
        else:
            self.program_layout.add_fixed(self.separation_height)
            h_layout = gui.Horiz(0.3 * em)
            select_label = gui.Label(name)
            # ZHUOYUe add toggle
            and_or_toggle = gui.ToggleSwitch("and/or")
            button_index = len(self.all_buttons)
            my_new_function = self.create_on_and_or_function(button_index)
            and_or_toggle.set_on_clicked(my_new_function)
            h_layout.add_child(select_label)
            h_layout.add_child(and_or_toggle)
            if not toggle_visile:
                and_or_toggle.visible = False
            if name == "Or":
                and_or_toggle.is_on = True
            self.program_layout.add_child(h_layout)
            select_button = gui.Button("Select")
            my_new_function = self.create_on_select_function(select_button, is_action_button)
            select_button.toggleable = True
            select_button.set_on_clicked(my_new_function)
            self.all_buttons.append(select_button)
            self.all_button_labels.append(select_label)
            self.all_button_and_or.append(and_or_toggle)
            self.program_layout.add_fixed(self.separation_height)
            self.program_layout.add_child(select_button)
            self._on_apply_layout()

    def add_iot(self, name):
        switch = gui.ToggleSwitch(name)
        switch_index = len(self.all_iots)
        my_new_function = self.create_on_switch_function(name, switch_index)
        switch.set_on_clicked(my_new_function)
        self.all_iots.append(switch)
        return switch

    def get_iot_states(self):
        iot_states = []
        for v_item in self.iots.get_children()[0].get_children():
            for switch in v_item.get_children():
                if type(switch).__name__ == "ToggleSwitch":
                    iot_states.append(int(switch.is_on))
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
        button_is_action = args[2]

        def function_template(*args, **kwargs):
            self.curr_button = button
            self.curr_button_is_action = button_is_action
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
                print("Zhuoyue checking curr_button_idx")
                print(curr_button_idx)
                self.curr_button.text, self.all_button_states[curr_button_idx] = self.get_on_off_state_message(
                    switch_name, self.all_iots[switch_index].is_on)
                self.curr_button.is_on = False  # to change the color of the button
                self.curr_button = None

        return function_template

    def get_on_off_state_message(self, msg, is_on):
        state_info = "0 0"  # the 1st digit is on/off, the second digit is the index, in the order of 5 lights, 3 doors, 3 lamps
        if msg.startswith('L'):
            state_info = str(int(is_on)) + " " + msg[1]
            if not self.curr_button_is_action:
                msg = "Light " + msg[1] + " is on" if is_on else "Light " + msg[1] + " is off"
            else:
                msg = "Turn on the light " + msg[1] if is_on else "Turn off the light " + msg[1]

        elif msg.startswith("D"):
            state_info = str(int(is_on)) + " " + str(int(msg[1]) + 5)  # TODO: change this 5 to len(lights)
            if not self.curr_button_is_action:
                msg = "Door " + msg[1] + " is open" if is_on else "Door " + msg[1] + " is closed"
            else:
                msg = "Open the door " + msg[1] if is_on else "Close the door " + msg[1]

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
            state_info = str(int(is_on)) + " " + str(int(msg[1]) + 8)  # TODO: change this 8 to len(lights) + len(doors)
            if not self.curr_button_is_action:
                msg = "Lamp " + msg[1] + " is on" if is_on else "Lamp " + msg[1] + " is off"
            else:
                msg = "Turn on the lamp " + msg[1] if is_on else "Turn off the lamp " + msg[1]
        return msg, state_info

    # def get_state_from_message(self, msg):
    #     iot_id = [int(s) for s in msg.split() if s.isdigit()][0]
    #     iot_states = 0 if "off" in msg else 1
    #     return iot_id, iot_states

    def _on_apply_layout(self):
        self.window.set_on_layout(self._on_layout)
        self.window.add_child(self._scene)
        self.window.add_child(self.panel)

    def _apply_settings(self):
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
        self._scene.frame = r
        width = 17 * layout_context.theme.font_size
        height = min(r.height,
                     self.panel.calc_preferred_size(layout_context, gui.Widget.Constraints()).height)
        self.panel.frame = gui.Rect(r.get_right() - width, r.y, width,
                                    height)

    def _set_mouse_mode_fly(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.FLY)

    def _set_mouse_mode_model(self):
        self._scene.set_view_controls(gui.SceneWidget.Controls.ROTATE_MODEL)

    def _on_show_axes(self, show):
        self.settings.show_axes = show
        self._apply_settings()

    def _on_point_size(self, size):
        self.settings.material.point_size = int(size)
        self.settings.apply_material = True
        self._apply_settings()

    def _on_remove_ceiling(self, is_on):
        self.my_load()

    def my_load(self, geometry=None, first_time=False):
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


def main():
    gui.Application.instance.initialize()
    w = AppWindow(1024, 768)
    sensors = [0] * 11
    geo = render_home(sensors)
    w.my_load(geometry=geo, first_time=True)
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
