from routines import *


class Processor:
    def __init__(self, get_all_history=False):
        # the order is, 5 lights, 3 doors, 2 tablelamp
        # self.states = [1] * 10
        # because the unity side door states are not accurate, so I have to keep a local copy
        self.get_all_history = get_all_history
        self.local_states_table = [1] * 11
        self.excluded_list = [163, 172]  # 163 is fridge, 172 is microwave

    def initialize_graph(self, idx):
        graph = None
        if idx == 0:
            self.local_states_table = [1] * 5 + [0, 1, 1] + [0] * 3
            if not self.get_all_history:
                comm.reset()
                success, graph = comm.environment_graph()
                tablelamps = find_nodes(graph, class_name='tablelamp')
                for tablelamp in tablelamps:
                    tablelamp['states'] = ['OFF']
                door = find_nodes(graph, class_name='door')[0]
                door['states'] = ['CLOSED']

        elif idx == 1:
            self.local_states_table = [0, 0, 0, 0, 1] + [0, 0, 1] + [0, 0, 1]
            if not self.get_all_history:
                comm.reset()
                success, graph = comm.environment_graph()
                tablelamp = find_nodes(graph, class_name='tablelamp')[0]
                tablelamp['states'] = ['OFF']
                tablelamp = find_nodes(graph, class_name='tablelamp')[1]
                tablelamp['states'] = ['OFF']
                lights = find_nodes(graph, class_name='lightswitch')
                for l in lights:
                    l['states'] = ['OFF']
                door = find_nodes(graph, class_name='door')[0]
                door['states'] = ['CLOSED']
                door2 = find_nodes(graph, class_name='door')[1]
                door2['states'] = ['CLOSED']
                l5 = find_nodes(graph, class_name='lightswitch')[4]
                l5['states'] = ['ON']
        elif idx == 2:
            self.local_states_table = [0] * 5 + [0, 1, 1] + [0, 0, 0]
            if not self.get_all_history:
                comm.reset()
                success, graph = comm.environment_graph()
                lights = find_nodes(graph, class_name='lightswitch')
                for l in lights:
                    l['states'] = ['OFF']
                tablelamps = find_nodes(graph, class_name='tablelamp')
                for tablelamp in tablelamps:
                    tablelamp['states'] = ['OFF']
                door = find_nodes(graph, class_name='door')[0]
                door['states'] = ['CLOSED']
        elif idx == 3:
            self.local_states_table = [0] * 5 + [1, 1, 1] + [0, 0, 0]
            if not self.get_all_history:
                comm.reset()
                success, graph = comm.environment_graph()
                lights = find_nodes(graph, class_name='lightswitch')
                for l in lights:
                    l['states'] = ['OFF']
                tablelamps = find_nodes(graph, class_name='tablelamp')
                for tablelamp in tablelamps:
                    tablelamp['states'] = ['OFF']
        elif idx == 4:
            self.local_states_table = [0] * 5 + [1, 1, 1] + [0, 0, 0]
            if not self.get_all_history:
                comm.reset()
                success, graph = comm.environment_graph()
                lights = find_nodes(graph, class_name='lightswitch')
                for l in lights:
                    l['states'] = ['OFF']
                tablelamps = find_nodes(graph, class_name='tablelamp')
                for tablelamp in tablelamps:
                    tablelamp['states'] = ['OFF']
        else:
            print("none")
        return graph

    def translate_from_state_to_action(self, msg):
        if msg == "":
            return None
        local_state = int(msg.split()[0])
        local_idx = int(msg.split()[1])
        if local_idx <= 4:  # lights
            action = "switchon" if local_state else "switchoff"
            obj = "light"
        elif 4 < local_idx <= 7:  # door
            action = "open" if local_state else "close"
            obj = "door"

        else:  # 7 < local_idx lamp
            action = "switchon" if local_state else "switchoff"
            obj = "tablelamp"
        id = str(local_lookup_table[local_idx])
        return "[{}] <{}> ({})".format(action, obj, id)

    def process_programm(self, script, input):
        # maybe we will keep using one trigger for now (since if we combine both programs,
        # then their  will be two actions, we'd rather let users write two programs)

        ## Input
        if input is not None:
            trigger = self.translate_from_state_to_action(input[0])
            conditions = input[1]
            and_or = input[2]  # 0 is and, 1 is or
            if_action = input[3]
            else_action = input[4]
        else:
            # Empty
            trigger = None
            conditions = []
            and_or = 0  # 0 is and, 1 is or
            if_action = []
            else_action = []

        print(trigger)
        print(conditions)
        print(and_or)
        print(if_action)
        print(else_action)

        # ## Task 0
        # trigger = "[open] <door> (47)"
        # # trigger = '[switchon] <tablelamp> (377)'
        # conditions = ["1 9", "1 10"]
        # and_or = 1  # 0 is and, 1 is or
        # if_action = ["0 0", "0 1", "0 2", "0 3", "0 4"]
        # else_action = []


        ## Task 1
        # trigger = "[open] <door> (47)"
        # conditions = []
        # and_or = 0  # 0 is and, 1 is or
        # if_action = ["0 4", "1 0", "0 10"]
        # else_action = []

        ## Task 2
        # need to update task 1 to the following (adding the else)
        # trigger = "[open] <door> (47)"
        # conditions = ["1 4"]
        # and_or = 0  # 0 is and, 1 is or
        # if_action = ["0 4", "1 0", "0 10"]
        # else_action = ["1 0"]

        for action in script:
            if action.startswith('!'):
                if action.startswith('!print'):
                    comm.experiment_log(action[7:])
                else:
                    print("invalid action!!!")
                continue
            if trigger and trigger in action:
                self.my_render_script(action)
                # _, graph = get_current_states()
                _, graph = comm.environment_graph()
                results = []
                is_satisfied = True
                if conditions:
                    for condition in conditions:
                        local_state = int(condition.split()[0])
                        local_idx = int(condition.split()[1])
                        results.append(self.local_states_table[local_idx] == local_state)
                    if and_or == 0:  # and
                        is_satisfied = all(results)
                    else:  # or
                        is_satisfied = any(results)
                if is_satisfied:
                    for local_action in if_action:
                        local_state = int(local_action.split()[0])
                        local_idx = int(local_action.split()[1])
                        self.local_states_table[local_idx] = local_state
                else:
                    for local_action in else_action:
                        local_state = int(local_action.split()[0])
                        local_idx = int(local_action.split()[1])
                        self.local_states_table[local_idx] = local_state
                # updated_script.append(action)
                self.expand_current_states(self.local_states_table, graph)
            else:  # if the current action is not a trigger
                self.my_render_script(action)

    def my_render_script(self, action):
        obj_id = int(action[action.find("(") + 1:action.find(")")].lower())
        action_match = action[action.find("[") + 1:action.find("]")].lower()
        # if it's not "walk" and those non-iot actions
        if action_match in ['switchon', 'switchoff', 'close', 'open'] and obj_id not in self.excluded_list:
            action_state = 1 if action_match in ['switchon', 'open'] else 0

            local_index = local_lookup_table.index(obj_id)
            if self.local_states_table[local_index] == action_state:
                pass  # will ignore an action if the states already satisfied
            else:
                self.local_states_table[local_index] = action_state
                comm.render_script([action], find_solution=False)
        else:
            comm.render_script([action], find_solution=False)

    def expand_current_states(self, states, graph):
        # 0,1,2,3,4 are lights, 5,6,7 are doors, 8,9,10 are lamps
        lights = find_nodes(graph, class_name='lightswitch')
        doors = find_nodes(graph, class_name='door')
        tablelamps = find_nodes(graph, class_name='tablelamp')
        for x in range(len(lights)):
            lights[x]['states'] = ['ON'] if states[x] else ['OFF']
        for x in range(len(doors)):
            doors[x]['states'] = ['OPEN'] if states[len(lights) + x] else ['CLOSED']
        for x in range(len(tablelamps)):
            tablelamps[x]['states'] = ['ON'] if states[len(lights) + len(doors) + x] else ['OFF']
        _ = comm.expand_scene(graph)

    def return_all_history(self, script):
        all_history = [self.local_states_table.copy()]
        all_history_changed_idx = ['initial']
        for action in script:
            if action.startswith('!'):
                continue
            obj_id = int(action[action.find("(") + 1:action.find(")")].lower())
            action_match = action[action.find("[") + 1:action.find("]")].lower()
            # if it's not "walk" and those non-iot actions
            if action_match in ['switchon', 'switchoff', 'close', 'open'] and obj_id not in self.excluded_list:
                action_state = 1 if action_match in ['switchon', 'open'] else 0

                local_index = local_lookup_table.index(obj_id)
                if self.local_states_table[local_index] == action_state:
                    pass  # will ignore an action if the states already satisfied
                else:
                    self.local_states_table[local_index] = action_state
                    all_history.append(self.local_states_table.copy())
                    all_history_changed_idx.append(str(action_state) + " " + str(local_index))
        return all_history, all_history_changed_idx

    def get_current_states(self):
        light_states = []
        door_states = []
        tablelamp_states = []
        _, graph = comm.environment_graph()
        for node in graph['nodes']:
            if node['class_name'] == 'lightswitch':
                local_states = node["states"]  # tracking binary for now
                if "ON" in local_states or "OPEN" in local_states:
                    light_states.append(1)
                elif "OFF" in local_states or "CLOSED" in local_states:
                    light_states.append(0)
            elif node['class_name'] == 'door':
                local_states = node["states"]  # tracking binary for now
                if "ON" in local_states or "OPEN" in local_states:
                    door_states.append(1)
                elif "OFF" in local_states or "CLOSED" in local_states:
                    door_states.append(0)
            elif node['class_name'] == 'tablelamp':
                local_states = node["states"]  # tracking binary for now
                if "ON" in local_states or "OPEN" in local_states:
                    tablelamp_states.append(1)
                elif "OFF" in local_states or "CLOSED" in local_states:
                    tablelamp_states.append(0)

        return light_states + door_states + tablelamp_states, graph


def sim_in_unity(selected_task, input, get_all_history=False):
    my_p = Processor(get_all_history)
    if selected_task == 0:
        script_my = enhanced_script_0_zhuoyue(my_p, get_all_history)
        initial_room = "bedroom"
    elif selected_task == 1:
        script_my = script_1
        initial_room = "bedroom"
    elif selected_task == 2:
        script_my = script_2
        initial_room = "bedroom"
        #### Training
    elif selected_task == 3:
        script_my = script_3
        initial_room = "livingroom"
    elif selected_task == 4:
        script_my = script_4
        initial_room = "kitchen"
        #### Training

    if get_all_history:
        my_p.initialize_graph(selected_task)
        return my_p.return_all_history(script_my)
    else:
        graph = my_p.initialize_graph(selected_task)
        _ = comm.expand_scene(graph)
        comm.add_character('Chars/Female1', initial_room=initial_room)
        my_p.process_programm(script_my, input)


if __name__ == '__main__':
    sim_in_unity(4, None)
    # script_new = [
    #     '<char0> [open] <door> (47)']  # Add here your script
    # comm.render_script(script_new, find_solution=False)
