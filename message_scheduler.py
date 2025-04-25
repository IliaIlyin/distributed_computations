import random
from role import *
from message import Message

class MessageScheduler:
    def __init__(self, nodes: dict[str, Role]):
        self.messages = []
        self.nodes: dict[str, Role] = nodes

    def schedule_message(self, message: Message):
        self.messages.append(message)

    def process_message(self):
        if self.messages:
            message = random.choice(self.messages)
            self.messages.remove(message)
            log_event(f"Scheduler delivers '{message.content}' from {message.sender} to {message.receiver}")
            self.nodes[message.receiver].receive_spec(message.content, self.nodes[message.sender])
