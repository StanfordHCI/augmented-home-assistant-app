from backend import render_home, remove_ceiling
from settings import *


class AppWindow:
    def __init__(self, width, height):
        self.settings = Settings()
        resource_path = gui.Application.instance.resource_path
        self.settings.new_ibl_name = resource_path + "/" + "default"

        self.window = gui.Application.instance.create_window("Augmented Home Assistant", width, height)
        w = self.window  # to make the code more concise

        # 3D widget
        self._scene = gui.SceneWidget()
        self._scene.scene = rendering.Open3DScene(w.renderer)
        em = w.theme.font_size
        self.separation_height = int(round(0.5 * em))
        self.separation_height_small = int(round(0.1 * em))
        self.separation_height_big = int(round(2 * em))
        self._settings_panel = gui.Vert(
            0, gui.Margins(0.25 * em, 0.25 * em, 0.25 * em, 0.25 * em))

        # Add Doors and Lights
        self.iots = gui.CollapsableVert("IoTs", 0.25 * em, gui.Margins(em, 0, 0, 0))

        ## horizontal layout
        h_iot = gui.Horiz(2 * em)

        v = gui.Vert(0.5 * em)  # v1
        num_lights = 5
        v.add_child(gui.Label("Lights"))
        for i in range(num_lights):
            v.add_child(self.add_iot("L" + str(i)))
        h_iot.add_child(v)

        v2 = gui.Vert(0.5 * em)  # v2
        num_doors = 3
        v2.add_child(gui.Label("Doors"))
        for i in range(num_doors):
            v2.add_child(self.add_iot("D" + str(i)))
        h_iot.add_child(v2)

        v3 = gui.Vert(0.5 * em)  # v2
        num_lamps = 3
        v3.add_child(gui.Label("Lamps"))
        for i in range(num_lamps):
            v3.add_child(self.add_iot("T" + str(i)))
        h_iot.add_child(v3)
        self.iots.add_child(h_iot)
        ## vertical layout
        # num_lights = 5
        # self.iots.add_child(gui.Label("Lights"))
        # for i in range(num_lights):
        #     self.iots.add_child(self.add_iot("L" + str(i)))
        #
        # self.iots.add_fixed(self.separation_height_small)
        #
        # num_doors = 3
        # self.iots.add_child(gui.Label("Doors"))
        # for i in range(num_doors):
        #     self.iots.add_child(self.add_iot("D" + str(i)))
        #
        # self.iots.add_fixed(self.separation_height_small)
        #
        # num_lamps = 3
        # self.iots.add_child(gui.Label("Lamps"))
        # for i in range(num_lamps):
        #     self.iots.add_child(self.add_iot("T" + str(i)))

        self.iots.add_fixed(self.separation_height)
        self._settings_panel.add_child(self.iots)

        self.config = gui.CollapsableVert("Configuration", 0.25 * em, gui.Margins(em, 0, 0, 0))

        self.program_layout = gui.Vert()
        self.program_layout.add_child(gui.Label("When"))
        select_button = gui.Button("Select")
        select_button.set_on_clicked(self._on_select)
        self.program_layout.add_child(select_button)

        # self.config.add_child(gui.Label("When"))
        condition_button = gui.Button("Condition(s)")
        action_button = gui.Button("Action(s)")
        clear_button = gui.Button("Clear")
        condition_button.set_on_clicked(self._on_condition)
        action_button.set_on_clicked(self._on_action)
        clear_button.set_on_clicked(self._on_clear)

        self.config.add_child(self.program_layout)
        self.config.add_fixed(self.separation_height_big)
        # self.config.add_child(trigger_button)
        self.config.add_child(condition_button)
        self.config.add_child(action_button)
        self.config.add_child(clear_button)

        self._settings_panel.add_child(self.config)

        # Add other control items
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
        self._settings_panel.add_fixed(self.separation_height)
        self._settings_panel.add_child(view_ctrls)

        ## Apply layout
        self._on_apply_layout()
        self._apply_settings()

        self.recording_actions = False

    def _on_clear(self):
        print("Clear the program layout")

    def _on_select(self):
        curr_state = self.get_iot_states()
        # self.recording_actions = True
        # self.button_waiting =
        print("zzy")

    def _on_apply_layout(self):
        self.window.set_on_layout(self._on_layout)
        self.window.add_child(self._scene)
        self.window.add_child(self._settings_panel)

    def _on_condition(self):
        self.program_layout.add_fixed(self.separation_height)
        self.program_layout.add_child(gui.Label("And"))
        select_button = gui.Button("Select")
        select_button.set_on_clicked(self._on_select)
        self.program_layout.add_child(select_button)
        self._on_apply_layout()
        print("zzy")

    def _on_action(self):
        self.program_layout.add_fixed(self.separation_height)
        self.program_layout.add_child(gui.Label("Do"))
        select_button = gui.Button("Select")
        select_button.set_on_clicked(self._on_select)
        self.program_layout.add_child(select_button)
        self._on_apply_layout()
        print("zzy")

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
                     self._settings_panel.calc_preferred_size(layout_context, gui.Widget.Constraints()).height)
        self._settings_panel.frame = gui.Rect(r.get_right() - width, r.y, width,
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

    def add_iot(self, name):
        switch = gui.ToggleSwitch(name)
        switch.set_on_clicked(self.on_switch)
        return switch

    def get_iot_states(self):
        iot_states = []
        for v_item in self.iots.get_children()[0].get_children():
            for switch in v_item.get_children():
                if type(switch).__name__ == "ToggleSwitch":
                    iot_states.append(int(switch.is_on))
        return iot_states

    def on_switch(self, is_on):
        # get the states of all toggles
        # the order is, 5 lights, 3 doors, 3 tablelamp
        iot_states = self.get_iot_states()

        # iot_states = [int(x.is_on) for x in self.iots.get_children() if type(x).__name__ == "ToggleSwitch"]
        # currently D1-3, L1-5, so [0,1,2,3,4,5,6,7]
        # but in reality, it should be D1,L1,L2,D3,L3,D2,L5,L4
        # order = [0, 3, 4, 2, 5, 1, 7, 6]
        # iot_states = [iot_states[i] for i in order]
        print(iot_states)
        geo = render_home(iot_states)
        self.my_load(geometry=geo)


def main():
    gui.Application.instance.initialize()
    w = AppWindow(1024, 768)
    # initial sensors
    # sensors = [0, 0, 0, 0, 0, 0, 0, 0]
    sensors = [0] * 11
    geo = render_home(sensors)
    w.my_load(geometry=geo, first_time=True)
    gui.Application.instance.run()


if __name__ == "__main__":
    main()
