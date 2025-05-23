from __future__ import annotations

import json
import random
from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional
from dataclasses import dataclass

# Logging utility
def log_event(event: str):
    with open("execution_log.txt", "a") as log_file:
        log_file.write(event + "\n")

# Enum for message types
class MessageType(Enum):
    ECHO = auto()
    ACK = auto()

# Forward declaration of Role for type hinting
class Role(ABC):
    ...

# Message data class
@dataclass
class Message:
    type: MessageType
    content: str
    sender: Role
    receiver: Role

# TaskQueue to store messages
class TaskQueue:
    def __init__(self):
        self._queue = []

    def enqueue(self, message: Message):
        log_event(f"Enqueued message {message.type.name} from {message.sender.name} to {message.receiver.name}")
        self._queue.append(message)

    def dequeue(self) -> Optional[Message]:
        if not self._queue:
            return None
        return self._queue.pop(random.randrange(len(self._queue)))

    def has_tasks(self) -> bool:
        return bool(self._queue)

# TaskExecutor to process messages
class TaskExecutor:
    def __init__(self, queue: TaskQueue, role_registry: dict[str, Role]):
        self.queue = queue
        self.roles = role_registry

    def execute_one(self):
        message = self.queue.dequeue()
        if message:
            log_event(f"Executing message {message.type.name} from {message.sender.name} to {message.receiver.name}")
            self.roles[message.receiver.name].receive(message, message.sender)

# Communication system
class CommunicationSystem:
    def __init__(self, queue: TaskQueue):
        self.queue = queue

    def send(self, message: Message):
        log_event(f"Communication: Sending {message.type.name} from {message.sender.name} to {message.receiver.name}")
        self.queue.enqueue(message)

# Abstract Role class
class Role(ABC):
    def __init__(self, name: str, neighbors: list[Role], communication: CommunicationSystem):
        self.name = name
        self.neighbors = neighbors
        self.communication = communication

    @abstractmethod
    def send(self, message_type: MessageType, addressees: list[Role]):
        pass

    @abstractmethod
    def receive(self, message: Message, sender: Optional[Role]):
        pass

    @abstractmethod
    def is_terminated(self) -> bool:
        pass

# Initiator role
class Initiator(Role):
    def __init__(self, name: str, neighbors: list[Role], communication: CommunicationSystem):
        super().__init__(name, neighbors, communication)
        self.received_acks = 0

    def send(self, message_type: MessageType, addressees: list[Role]):
        for neighbor in addressees:
            self.communication.send(Message(message_type, message_type.name, self, neighbor))

    def receive(self, message: Message, sender: Optional[Role]):
        log_event(f"Node {self.name} received '{message.type.name}' from {sender.name}")
        if message.type == MessageType.ACK:
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

# Participant role
class Participant(Role):
    def __init__(self, name: str, neighbors: list[Role], communication: CommunicationSystem):
        super().__init__(name, neighbors, communication)
        self.parent: Optional[Role] = None
        self.received = False
        self.received_acks = 0

    def send(self, message_type: MessageType, addressees: list[Role]):
        for neighbor in addressees:
            if neighbor != self.parent:
                self.communication.send(Message(message_type, message_type.name, self, neighbor))

    def receive(self, message: Message, sender: Optional[Role]):
        log_event(f"Node {self.name} received '{message.type.name}' from {sender.name}")
        if message.type == MessageType.ECHO:
            self.handle_echo(sender)
        elif message.type == MessageType.ACK:
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
            self.communication.send(Message(MessageType.ACK, MessageType.ACK.name, self, self.parent))
        log_event(f"Node {self.name}: Algorithm finished.")

    def is_terminated(self) -> bool:
        return self.received and self.received_acks == self.expected_acks()

# Load graph from file
def load_graph(filename: str) -> dict:
    with open(filename, 'r') as f:
        return json.load(f)

# Create node instances
def create_nodes(graph_data: dict[str, dict], communication: CommunicationSystem) -> dict[str, Role]:
    temp_nodes = {}

    for name, info in graph_data.items():
        role_type = info.get("role", "participant")
        temp_nodes[name] = (
            Initiator(name, [], communication) if role_type == "initiator"
            else Participant(name, [], communication)
        )

    for name, info in graph_data.items():
        temp_nodes[name].neighbors = [temp_nodes[n] for n in info.get("neighbors", [])]

    return temp_nodes

# Main function
def main(graph_file="graph.json"):
    with open("execution_log.txt", "w") as log_file:
        log_file.write("Execution Log:\n")

    graph_data = load_graph(graph_file)
    task_queue = TaskQueue()
    communication = CommunicationSystem(task_queue)
    nodes = create_nodes(graph_data, communication)
    executor = TaskExecutor(task_queue, nodes)

    initiator = next((n for n in nodes.values() if isinstance(n, Initiator)), None)
    if not initiator:
        print("No initiator found in the graph.")
        return

    initiator.start()

    while not all(n.is_terminated() for n in nodes.values()):
        executor.execute_one()

if __name__ == "__main__":
    main()
