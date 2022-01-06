class Controller:
    def __init__(self):
        self.trigger = None
        self.conditions = []
        self.and_or = 0  # 0 is and, 1 is or
        self.if_action = []
        self.else_action = []

        self.triggered = False  # when it's triggered we will detect the changes

    def initialize(self, data):
        self.trigger = data[0]
        self.conditions = data[1]
        self.and_or = data[2]  # 0 is and, 1 is or
        self.if_action = data[3]
        self.else_action = data[4]

    def check_udpate(self, trigger, all_states):
        # TODO (Zhuoyue) this function is similar (well...basically the logic is the same) to the
        #  process_programm function in simulate.py we might want to create a generic function for both of them
        if trigger == self.trigger:
            self.triggered = True
            results = []
            is_satisfied = True
            if self.conditions:
                for condition in self.conditions:
                    local_state = int(condition.split()[0])
                    local_idx = int(condition.split()[1])
                    results.append(all_states[local_idx] == local_state)
                if self.and_or == 0:  # and
                    is_satisfied = all(results)
                else:  # or
                    is_satisfied = any(results)
            if is_satisfied:
                for local_action in self.if_action:
                    local_state = int(local_action.split()[0])
                    local_idx = int(local_action.split()[1])
                    all_states[local_idx] = local_state
            else:
                for local_action in self.else_action:
                    local_state = int(local_action.split()[0])
                    local_idx = int(local_action.split()[1])
                    all_states[local_idx] = local_state
            # updated_script.append(action)
            return all_states
        else:  # if the current action is not a trigger
            return None
