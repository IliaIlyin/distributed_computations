from role import Role, log_event
class Initiator(Role):
    def __init__(self, name, neighbors, scheduler):
        self.name = name
        self.neighbors = neighbors
        self.received_responses = 0
        self.scheduler = scheduler

    def do_spec(self, label=None, guard=None, action=None, next_label=None):
        if action:
            action()

    def send_spec(self, message, addressee):
        for neighbor in addressee:
            log_event(f"Node {self.name} schedules '{message}' for {neighbor.name}")
            self.scheduler.schedule_message(Message(message, self, neighbor))

    def receive_spec(self, variable, sender=None):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        self.received_responses += 1
        if self.received_responses == len(self.neighbors):
            log_event(f"Node {self.name}: Echo complete.")

    def start(self):
        self.send_spec("ECHO", self.neighbors)