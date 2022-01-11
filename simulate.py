import time

from unity_simulator.comm_unity import UnityCommunication

comm = UnityCommunication()

script_1 = [
    '<char0> [sit] <chair> (392)',
    '<char0> [open] <door> (47)',
    '<char0> [switchon] <light> (58)',
    '<char0> [switchoff] <light> (402)',
    '<char0> [switchoff] <tablelamp> (377)',
    '<char0> [open] <microwave> (172)'
]  # Add here your script

script_2 = [
    '<char0> [switchon] <tablelamp> (377)',
    '<char0> [open] <door> (47)',
    '<char0> [switchoff] <light> (278)',
    '<char0> [switchoff] <light> (239)',
    '<char0> [switchoff] <light> (58)',
    '<char0> [switchoff] <light> (344)',
    '<char0> [switchoff] <light> (402)',
    '<char0> [close] <door> (47)',
    '<char0> [sit] <bed> (394)']  # Add here your script

# script_3 = [
#     '<char0> [switchon] <tablelamp> (377)',
#     '<char0> [open] <door> (47)',
#     '<char0> [switchon] <light> (58)',
#     '<char0> [open] <fridge> (163)',
#     '<char0> [close] <fridge> (163)',
#     '<char0> [switchoff] <light> (58)',
#     '<char0> [sit] <bed> (394)']  # Add here your script

script_3 = [
    '<char0> [switchon] <tablelamp> (377)',
    '<char0> [open] <door> (47)',
    '<char0> [switchon] <light> (58)',
    '<char0> [open] <fridge> (163)']  # Add here your script

# 5 lights, 3 doors, 3 lamps
local_light_lookup_table = [58, 239, 278, 344, 402]
local_light_name_table = [f"Light {i}" for i in range(len(local_light_lookup_table))]
local_door_lookup_table = [47, 254, 305]
local_door_name_table = [f"Door {i}" for i in range(len(local_door_lookup_table))]
local_lamp_lookup_table = [256, 376, 377]
local_lamp_name_table = [f"Lamp {i}" for i in range(len(local_lamp_lookup_table))]
local_lookup_table = local_light_lookup_table + local_door_lookup_table + local_lamp_lookup_table
local_name_table = local_light_name_table + local_door_name_table + local_light_name_table
local_name_lookup_table = {i: j for i, j in zip(local_lookup_table, local_name_table)}

def find_nodes(graph, **kwargs):
    if len(kwargs) == 0:
        return None
    else:
        k, v = next(iter(kwargs.items()))
        return [n for n in graph['nodes'] if n[k] == v]


class Processor:
    def __init__(self, get_all_history=False):
        # the order is, 5 lights, 3 doors, 2 tablelamp
        # self.states = [1] * 10
        # because the unity side door states are not accurate, so I have to keep a local copy
        self.get_all_history = get_all_history
        self.local_states_table = [1] * 11
        self.excluded_list = [163, 172]  # 163 is fridge, 172 is microwave

    def initialize_graph(self):
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
            return graph

    def initialize_graph_task_2(self):
        self.local_states_table = [1] * 5 + [1, 1, 1] + [0] * 3
        if not self.get_all_history:
            comm.reset()
            success, graph = comm.environment_graph()
            tablelamps = find_nodes(graph, class_name='tablelamp')
            for tablelamp in tablelamps:
                tablelamp['states'] = ['OFF']
            door = find_nodes(graph, class_name='door')[0]
            door['states'] = ['CLOSED']
            return graph

    def initialize_graph_task_3(self):
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

        ## Task 1
        # trigger = "[open] <door> (47)"
        # conditions = []
        # and_or = 0  # 0 is and, 1 is or
        # if_action = ["0 4", "1 0", "0 10"]
        # else_action = []

        # ## Task 2
        # trigger = "[open] <door> (47)"
        # # trigger = '[switchon] <tablelamp> (377)'
        # conditions = ["1 9", "1 10"]
        # and_or = 1  # 0 is and, 1 is or
        # if_action = ["0 0", "0 1", "0 2", "0 3", "0 4"]
        # else_action = []

        ## Task 3
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


def enhanced_script_2(my_p: Processor):
    comm.setup_experiment_log()
    manual = 0
    yield '!print One day:'
    time.sleep(1)
    yield '!print It\'s late now. I need to go to sleep...'
    time.sleep(1)
    yield from [
        f'!print I\'ll turn on my bed side lamp ({local_lamp_name_table[2]}).',
        f'<char0> [walk] <door> (47)',
        f'<char0> [open] <door> (47)',
        f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
        f'<char0> [walk] <door> (47)',
        f'<char0> [close] <door> (47)',
        '<char0> [switchoff] <light> (402)',
    ]
    yield from [
        '!print OK. I\'ll go to bed now.',
        '<char0> [sit] <bed> (394)',
    ]
    time.sleep(1)
    on_light_ids = [
        local_light_lookup_table[light_idx]
        for light_idx in range(5)
        if my_p.local_states_table[light_idx] != 0
    ]
    if len(on_light_ids) != 0:
        # If any lights is still on, the user opens the door and then turns off those lights.
        yield from [
            '!print OHHHH. I forgot to turn off other lights again!',
            '<char0> [switchon] <light> (402)',
            '<char0> [open] <door> (47)'
        ]
        for light_id in on_light_ids:
            manual += 1
            yield f'!print I have to MANUALLY TURN OFF {local_name_lookup_table[light_id]}!'
            yield f'<char0> [switchoff] <light> ({light_id})'
        yield from [
            '!print I can finally go to sleep now. I wish it\'s all automatic!',
            '<char0> [switchoff] <light> (402)',
            f'<char0> [walk] <bed> (394)',
            '<char0> [sit] <bed> (394)',
        ]
    time.sleep(1)
    yield '!print Sleeping...zzz...'
    time.sleep(1)
    yield '!print Next morning:'
    yield from [
        '!print What a nice day!',
        '!print I\'ll go to cooking something the living room',
        f'!print First, I\'ll turn off my bed side lamp ({local_lamp_lookup_table[2]}).',
        f'<char0> [switchon] <light> ({local_light_lookup_table[4]})',
        f'<char0> [switchoff] <tablelamp> ({local_lamp_lookup_table[2]})',
        '<char0> [open] <door> (47)',
        f'<char0> [switchon] <light> ({local_light_lookup_table[0]})',
        f'<char0> [switchoff] <light> ({local_light_lookup_table[4]})',
        '<char0> [close] <door> (47)',
    ]
    if my_p.local_states_table[0] == 0:
        manual += 1
        yield from [
            '!print WHAT!!! Why is my light off now???',
            f'!print I have to MANUALLY TURN ON {local_light_lookup_table[0]}!',
            f'<char0> [switchon] <light> ({local_light_lookup_table[0]})',
        ]
    yield from [
        '<char0> [open] <microwave> (172)',
        '!print end of story',
        f'!print Summary: I have to do stuff manually {manual} time(s)'
        if manual > 0 else
        f'!print Summary: I don\'t have do things manually ;)'
    ]


def sim_in_unity(selected_task, input, get_all_history=False):
    my_p = Processor(get_all_history)
    print(input)
    if selected_task == 0:
        #### Task 1
        if get_all_history:
            my_p.initialize_graph()
            return my_p.return_all_history(script_1)
        else:
            graph = my_p.initialize_graph()
            _ = comm.expand_scene(graph)
            comm.add_character('Chars/Female1', initial_room="bedroom")
            my_p.process_programm(script_1, input)
    elif selected_task == 1:
        #### Task 2
        if get_all_history:
            my_p.initialize_graph_task_2()
            return my_p.return_all_history(script_2)
        else:
            graph = my_p.initialize_graph_task_2()
            _ = comm.expand_scene(graph)
            comm.add_character('Chars/Female1', initial_room="livingroom")
            my_p.process_programm(enhanced_script_2(my_p), input)
    else:
        ##### Task 3
        if get_all_history:
            my_p.initialize_graph_task_3()
            return my_p.return_all_history(script_3)
        else:
            graph = my_p.initialize_graph_task_3()
            _ = comm.expand_scene(graph)
            comm.add_character('Chars/Female1', initial_room="bedroom")
            my_p.process_programm(script_3, input)


if __name__ == '__main__':
    sim_in_unity(0, None)
    # script_new = [
    #     '<char0> [open] <door> (47)']  # Add here your script
    # comm.render_script(script_new, find_solution=False)
