from __future__ import annotations

import json
import random
import time
from abc import ABC, abstractmethod
from typing import Optional
from dataclasses import dataclass

class MessageType:
    ECHO = "ECHO"
    ACK = "ACK"

def log_event(event: str):
    with open("execution_log.txt", "a") as log_file:
        log_file.write(event + "\n")

@dataclass
class Message:
    content: str
    sender: Role
    receiver: Role

class MessageScheduler:
    def __init__(self, nodes: dict[str, Role]):
        self.messages = []
        self.nodes = nodes

    def schedule_message(self, message: Message):
        log_event(f"Node {message.sender.name} schedules '{message.content}' for {message.receiver.name}")
        self.messages.append(message)

    def process_message(self):
        if self.messages:
            time.sleep(random.uniform(0.5, 2.0))  # Simulate network delay
            message = random.choice(self.messages)
            self.messages.remove(message)
            log_event(f"Scheduler delivers '{message.content}' from {message.sender.name} to {message.receiver.name}")
            message.receiver.receive(message.content, message.sender)

class Role(ABC):
    def __init__(self, name: str, neighbors: list[Role], scheduler: MessageScheduler):
        self.name = name
        self.neighbors = neighbors
        self.scheduler = scheduler

    @abstractmethod
    def send(self, message: str, addressees: list[Role]):
        pass

    @abstractmethod
    def receive(self, variable: str, sender: Optional[Role]):
        pass

    @abstractmethod
    def is_terminated(self) -> bool:
        pass

class Initiator(Role):
    def __init__(self, name: str, neighbors: list[Role], scheduler: MessageScheduler):
        super().__init__(name, neighbors, scheduler)
        self.received_acks = 0

    def send(self, message: str, addressees: list[Role]):
        for neighbor in addressees:
            self.scheduler.schedule_message(Message(message, self, neighbor))

    def receive(self, variable: str, sender: Optional[Role]):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        if variable == MessageType.ACK:
            self.handle_ack()

    def handle_ack(self):
        self.received_acks += 1
        if self.is_terminated():
            log_event(f"Node {self.name}: Echo complete.")
            log_event(f"Node {self.name}: Algorithm finished.")

    def start(self):
        self.send(MessageType.ECHO, self.neighbors)

    def is_terminated(self) -> bool:
        return self.received_acks == len(self.neighbors)

class Participant(Role):
    def __init__(self, name: str, neighbors: list[Role], scheduler: MessageScheduler):
        super().__init__(name, neighbors, scheduler)
        self.parent: Optional[Role] = None
        self.received = False
        self.received_acks = 0

    def send(self, message: str, addressees: list[Role]):
        for neighbor in addressees:
            if neighbor != self.parent:
                self.scheduler.schedule_message(Message(message, self, neighbor))

    def receive(self, variable: str, sender: Optional[Role]):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        if variable == MessageType.ECHO:
            self.handle_echo(sender)
        elif variable == MessageType.ACK:
            self.handle_ack()

    def handle_echo(self, sender: Role):
        if not self.received:
            self.received = True
            self.parent = sender
            children = [n for n in self.neighbors if n != self.parent]
            if children:
                self.send(MessageType.ECHO, children)
            else:
                self.finish()

    def handle_ack(self):
        self.received_acks += 1
        if self.received_acks == self.expected_acks():
            self.finish()

    def expected_acks(self) -> int:
        return len([n for n in self.neighbors if n != self.parent])

    def finish(self):
        log_event(f"Node {self.name}: Echo complete.")
        if self.parent:
            self.scheduler.schedule_message(Message(MessageType.ACK, self, self.parent))
        log_event(f"Node {self.name}: Algorithm finished.")

    def is_terminated(self) -> bool:
        return self.received and self.received_acks == self.expected_acks()

def load_graph(filename: str) -> dict:
    with open(filename, 'r') as f:
        return json.load(f)

def create_nodes(graph_data: dict[str, dict]) -> dict[str, Role]:
    temp_nodes = {}
    scheduler = MessageScheduler(temp_nodes)

    for name, info in graph_data.items():
        role_type = info.get("role", "participant")
        temp_nodes[name] = (
            Initiator(name, [], scheduler) if role_type == "initiator"
            else Participant(name, [], scheduler)
        )

    for name, info in graph_data.items():
        temp_nodes[name].neighbors = [temp_nodes[n] for n in info.get("neighbors", [])]

    return temp_nodes

def main(graph_file="graph.json"):
    with open("execution_log.txt", "w") as log_file:
        log_file.write("Execution Log:\n")

    graph_data = load_graph(graph_file)
    nodes = create_nodes(graph_data)

    initiator = next((n for n in nodes.values() if isinstance(n, Initiator)), None)
    if not initiator:
        print("No initiator found in the graph.")
        return

    initiator.start()
    scheduler = initiator.scheduler

    while not all(n.is_terminated() for n in nodes.values()):
        scheduler.process_message()

if __name__ == "__main__":
    main()
