from unity_simulator.comm_unity import UnityCommunication

script_1 = [
    '<char0> [Open] <door> (47)',
    '<char0> [switchon] <light> (58)',
    '<char0> [switchoff] <light> (344)',
    '<char0> [switchoff] <light> (402)',
    '<char0> [switchoff] <tablelamp> (377)',
    '<char0> [Walk] <kitchen> (11)']  # Add here your script

script_2 = [
    '<char0> [switchon] <tablelamp> (377)',
    '<char0> [sit] <chair> (392)',
    '<char0> [Open] <door> (47)',
    '<char0> [switchoff] <light> (278)',
    '<char0> [switchoff] <light> (239)',
    '<char0> [switchoff] <light> (58)',
    '<char0> [switchoff] <light> (344)',
    '<char0> [switchoff] <light> (402)',
    '<char0> [Close] <door> (47)',
    '<char0> [Sit] <bed> (394)']  # Add here your script

script_3 = [
    '<char0> [switchon] <tablelamp> (377)',
    '<char0> [Open] <door> (47)',
    '<char0> [switchon] <light> (58)',
    '<char0> [Open] <fridge> (163)',
    '<char0> [Close] <fridge> (163)',
    '<char0> [switchoff] <light> (58)',
    '<char0> [Sit] <bed> (394)']  # Add here your script

# 5 lights, 3 doors, 3 lamps
local_lookup_table = [58, 239, 278, 344, 402, 47, 254, 305, 256, 376, 377]


def find_nodes(graph, **kwargs):
    if len(kwargs) == 0:
        return None
    else:
        k, v = next(iter(kwargs.items()))
        return [n for n in graph['nodes'] if n[k] == v]


class Processor:
    def __init__(self):
        # the order is, 5 lights, 3 doors, 2 tablelamp
        # self.states = [1] * 10
        # because the unity side door states are not accurate, so I have to keep a local copy
        self.local_states_table = [1] * 11
        self.excluded_list = [163]  # 163 is fridge

    def initialize_graph(self):
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
        l5 = find_nodes(graph, class_name='lightswitch')[3]
        l5['states'] = ['ON']
        self.local_states_table = [0, 0, 0, 1, 1] + [0, 0, 1] + [0, 0, 1]
        return graph

    def initialize_graph_task_2(self):
        comm.reset()
        success, graph = comm.environment_graph()
        tablelamps = find_nodes(graph, class_name='tablelamp')
        for tablelamp in tablelamps:
            tablelamp['states'] = ['OFF']
        door = find_nodes(graph, class_name='door')[0]
        door['states'] = ['CLOSED']
        self.local_states_table = [1] * 5 + [0, 1, 1] + [0] * 3
        return graph

    def initialize_graph_task_3(self):
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
        self.local_states_table = [0] * 5 + [0, 1, 1] + [0, 0, 0]
        return graph

    def process_programm(self, script, input):
        # maybe we will keep using one trigger for now (since if we combine both programs,
        # then their  will be two actions, we'd rather let users write two programs)

        ## Empty
        trigger = None
        conditions = []
        and_or = 0  # 0 is and, 1 is or
        if_action = []
        else_action = []

        ## Task 1
        trigger = "[Open] <door> (47)"
        conditions = []
        and_or = 0  # 0 is and, 1 is or
        if_action = ["0 4", "1 0", "0 10", "0 3"]
        else_action = []

        # ## Task 2
        # trigger = "[Open] <door> (47)"
        # # trigger = '[switchon] <tablelamp> (377)'
        # conditions = ["1 9", "1 10"]
        # and_or = 1  # 0 is and, 1 is or
        # if_action = ["0 0", "0 1", "0 2", "0 3", "0 4"]
        # else_action = []

        ## Task 3
        # need to update task 1 to the following ( adding the else)
        trigger = "[Open] <door> (47)"
        conditions = ["1 4"]
        and_or = 0  # 0 is and, 1 is or
        if_action = ["0 4", "1 0", "0 10", "0 3"]
        else_action = ["1 0"]

        for action in script:
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


if __name__ == '__main__':
    comm = UnityCommunication()
    my_p = Processor()
    ##### Task 1
    # graph = my_p.initialize_graph()
    # _ = comm.expand_scene(graph)
    # comm.add_character('Chars/Female1', initial_room="bedroom")
    # my_p.process_programm(script_1, _)

    ##### Task 2
    # graph = my_p.initialize_graph_task_2()
    # _ = comm.expand_scene(graph)
    # comm.add_character('Chars/Female1', initial_room="bedroom")
    # my_p.process_programm(script_2, "sss")

    ##### Task 3
    graph = my_p.initialize_graph_task_3()
    _ = comm.expand_scene(graph)
    comm.add_character('Chars/Female1', initial_room="bedroom")
    my_p.process_programm(script_3, "sss")