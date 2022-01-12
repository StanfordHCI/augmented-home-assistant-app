from unity_simulator.comm_unity import UnityCommunication
import time

comm = UnityCommunication()

# all chair, 161,

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

script_0 = [
    '<char0> [switchon] <tablelamp> (377)',
    '<char0> [open] <door> (47)',
    '<char0> [switchoff] <light> (278)',
    '<char0> [switchoff] <light> (239)',
    '<char0> [switchoff] <light> (58)',
    '<char0> [switchoff] <light> (344)',
    '<char0> [switchoff] <light> (402)',
    '<char0> [close] <door> (47)',
    '<char0> [sit] <bed> (394)']  # Add here your script

# Routine B-1 B-2
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
    '<char0> [switchon] <light> (58)',
    '<char0> [open] <fridge> (163)']  # Add here your script

# Routine C-1 C-2

script_3 = [
    '<char0> [switchon] <light> (239)',
    '<char0> [sit] <couch> (214)',
    '<char0> [switchon] <light> (58)',
    '<char0> [switchon] <light> (402)',
    '<char0> [switchon] <light> (344)',
    '<char0> [sit] <toilet> (321)'
]  # Add here your script

script_4 = [
    '<char0> [open] <fridge> (163)',
    '<char0> [close] <fridge> (163)',
    '<char0> [switchon] <light> (58)',
    '<char0> [switchon] <light> (239)',
    '<char0> [sit] <couch> (214)'
]  # Add here your script


def enhanced_script_0(my_p, get_all_history=False):
    if not get_all_history:
        comm.setup_experiment_log()
        manual = 0
        time.sleep(1)
        yield '!print It\'s late now. I need to go to sleep...'
        yield '<char0> [switchoff] <light> (402)'
        # time.sleep(1)
        yield from [
            f'!print I\'ll turn on my bed side lamp ({local_lamp_name_table[2]}).',
            f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
        ]
        yield from [
            '!print OK. I\'ll go to bed now, probably watching a few YouTube videos before going to sleep...',
            '<char0> [sit] <bed> (394)'
        ]
        time.sleep(1)
        yield from [
            '!print I\'ll sleep now.',
            f'<char0> [switchoff] <tablelamp> ({local_lamp_lookup_table[2]})',
            '<char0> [sit] <bed> (394)'
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
                f'!print let me turn on my bed side lamp ({local_lamp_name_table[2]}).',
                f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
                f'!print and turn on Light 4',
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
                f'<char0> [switchoff] <tablelamp> ({local_lamp_lookup_table[2]})',
                '<char0> [sit] <bed> (394)',
            ]
        time.sleep(1)
        yield '!print Sleeping...zzz...'
        yield from [
            f'!print Summary: I have to do stuff manually {manual} time(s)'
            if manual > 0 else
            f'!print Summary: I don\'t have do things manually :)'
        ]
    else:
        yield '<char0> [switchoff] <light> (402)'
        # time.sleep(1)
        yield from [
            f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
        ]
        yield from [
            '<char0> [sit] <bed> (394)',
            f'<char0> [switchoff] <tablelamp> ({local_lamp_lookup_table[2]})',
            '<char0> [sit] <bed> (394)',
        ]
        # If any lights is still on, the user opens the door and then turns off those lights.
        yield from [
            f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
            '<char0> [switchon] <light> (402)',
            '<char0> [open] <door> (47)'
        ]
        on_light_ids = [
            local_light_lookup_table[light_idx]
            for light_idx in range(5)
            if my_p.local_states_table[light_idx] != 0
        ]
        if len(on_light_ids) != 0:
            # If any lights is still on, the user opens the door and then turns off those lights.
            yield from [
                f'<char0> [switchon] <tablelamp> ({local_lamp_lookup_table[2]})',
                '<char0> [switchon] <light> (402)',
                '<char0> [open] <door> (47)'
            ]
            for light_id in on_light_ids:
                yield f'<char0> [switchoff] <light> ({light_id})'
            yield from [
                '<char0> [switchoff] <light> (402)',
                f'<char0> [switchoff] <tablelamp> ({local_lamp_lookup_table[2]})',
                '<char0> [sit] <bed> (394)',
            ]


def enhanced_script_1_2(my_p, get_all_history=False):
    if not get_all_history:
        comm.setup_experiment_log()
        manual = 0
        yield '!print Case 1:'
        yield '!print I\'m going to do some work...'
        yield '<char0> [sit] <chair> (392)'
        time.sleep(1)
        yield '!print I\'m hungry, let me get some food...'
        yield '!print Let me open the Door 0...'
        yield '<char0> [open] <door> (47)'

        cond_satisfied = my_p.local_states_table[0] == 1
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN ON Light 0!'
            yield f'<char0> [switchon] <light> (58))'

        cond_satisfied = my_p.local_states_table[4] == 0
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN OFF Light 4!'
            yield f'<char0> [switchoff] <light> (402))'

        cond_satisfied = my_p.local_states_table[10] == 0
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN OFF Lamp 2!'
            yield '<char0> [switchoff] <tablelamp> (377)'
        yield '<char0> [open] <microwave> (172)'

        time.sleep(1)
        graph = my_p.initialize_graph(2)
        _ = comm.expand_scene(graph)
        comm.add_character('Chars/Female1', initial_room="bedroom")

        yield '!print Case 2:'
        yield '!print It\'s midnight, but I\'m hungry... '
        yield '<char0> [switchon] <tablelamp> (377)'
        yield '!print Let me get some food... '
        yield '!print Let me open the Door 0...'
        yield '<char0> [open] <door> (47)'
        time.sleep(1)

        did_wrong = my_p.local_states_table[10] == 0
        if did_wrong:
            manual += 1
            yield f'!print What??'
            yield f'!print I have to MANUALLY TURN ON Lamp 2 again!'
            yield f'<char0> [switchon] <tablelamp> (377))'

        cond_satisfied = my_p.local_states_table[0] == 1
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN ON Light 0!'
            yield f'<char0> [switchon] <light> (58))'
        yield '<char0> [open] <fridge> (163)'

        yield from [
            f'!print Summary: I have to do stuff manually {manual} time(s)'
            if manual > 0 else
            f'!print Summary: I don\'t have do things manually :)'
        ]
    else:
        yield 'initial'
        yield from script_1
        _ = my_p.initialize_graph(2)
        yield 'initial'
        yield from script_2


def enhanced_script_3_4(my_p, get_all_history=False):
    if not get_all_history:
        comm.setup_experiment_log()
        manual = 0
        yield '!print Case 1:'
        yield '!print I\'m going to turn on the Light 1 and watch TV...'
        yield f'<char0> [switchon] <light> (239))'
        yield '<char0> [sit] <couch> (214)'
        time.sleep(1)
        yield '!print I need to use the bathroom, let me switch on Light 0'
        yield f'<char0> [switchon] <light> (58))'

        cond_satisfied = my_p.local_states_table[4] == 1
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN ON Light 4!'
            yield f'<char0> [switchon] <light> (402))'
        cond_satisfied = my_p.local_states_table[3] == 1
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN ON Light 3!'
            yield f'<char0> [switchon] <light> (344))'
        yield '<char0> [sit] <toilet> (321)'

        time.sleep(1)
        graph = my_p.initialize_graph(4)
        _ = comm.expand_scene(graph)
        comm.add_character('Chars/Female1', initial_room="kitchen")

        yield '!print Case 2:'
        yield '!print Just came back from work...'
        time.sleep(1)
        yield '!print Let me get some food... '
        yield '<char0> [open] <fridge> (163)'
        time.sleep(1)
        yield '<char0> [close] <fridge> (163)'

        yield '!print I\'m going to turn on the Light 0 and go to the livingroom...'
        yield f'<char0> [switchon] <light> (58))'

        cond_satisfied = my_p.local_states_table[4] == 0
        if not cond_satisfied:
            manual += 1
            yield f'!print What??'
            yield f'!print I have to MANUALLY TURN OFF Light 4!'
            yield f'<char0> [switchoff] <light> (402))'
        cond_satisfied = my_p.local_states_table[3] == 0
        if not cond_satisfied:
            manual += 1
            yield f'!print What??'
            yield f'!print I have to MANUALLY TURN OFF Light 3!'
            yield f'<char0> [switchoff] <light> (344))'

        cond_satisfied = my_p.local_states_table[1] == 1
        if not cond_satisfied:
            manual += 1
            yield f'!print I have to MANUALLY TURN ON Light 1!'
            yield f'<char0> [switchon] <light> (239))'

        yield '<char0> [sit] <couch> (214)'

        yield from [
            f'!print Summary: I have to do stuff manually {manual} time(s)'
            if manual > 0 else
            f'!print Summary: I don\'t have do things manually :)'
        ]
    else:
        yield 'initial'
        yield from script_3
        _ = my_p.initialize_graph(4)
        yield 'initial'
        yield from script_4


def find_nodes(graph, **kwargs):
    if len(kwargs) == 0:
        return None
    else:
        k, v = next(iter(kwargs.items()))
        return [n for n in graph['nodes'] if n[k] == v]
