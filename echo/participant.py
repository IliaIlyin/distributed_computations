from role import  *
from message_scheduler import *


class Participant(Role):
    def __init__(self, name, neighbors, scheduler):
        self.name = name
        self.neighbors = neighbors
        self.parent = None
        self.received = False
        self.scheduler = scheduler

    def do_spec(self, label=None, guard=None, action=None, next_label=None):
        if action:
            action()

    def send_spec(self, message, addressee):
        for neighbor in addressee:
            if neighbor != self.parent:
                log_event(f"Node {self.name} schedules '{message}' for {neighbor.name}")
                self.scheduler.schedule_message(Message(message, self, neighbor))

    def receive_spec(self, variable, sender=None):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        if not self.received:
            self.received = True
            self.parent = sender
            self.send_spec("ECHO", self.neighbors)

        if self.parent:
            log_event(f"Node {self.name} schedules 'ACK' for {self.parent.name}")
            self.scheduler.schedule_message(Message("ACK", self, self.parent))
