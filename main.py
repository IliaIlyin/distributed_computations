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

# --- Tiny type for Role IDs ---
@dataclass(frozen=True)
class RoleId:
    value: str

    def __str__(self) -> str:
        return self.value


class MessageType(Enum):
    ECHO = auto()
    ACK = auto()


@dataclass
class Message:
    type: MessageType
    content: str
    sender_id: RoleId
    receiver_id: RoleId


# TaskQueue to store messages
class TaskQueue:
    def __init__(self):
        self._queue = []

    def enqueue(self, message: Message):
        log_event(
            f"Enqueued message {message.type.name} from {message.sender_id} to {message.receiver_id}"
        )
        self._queue.append(message)

    def dequeue(self) -> Optional[Message]:
        if not self._queue:
            return None
        return self._queue.pop(random.randrange(len(self._queue)))

    def has_tasks(self) -> bool:
        return bool(self._queue)


# Communication system
class CommunicationSystem:
    def __init__(self, queue: TaskQueue, role_registry: dict[RoleId, Role]):
        self.queue = queue
        self.roles = role_registry  # maps RoleId -> Role

    def send(self, message: Message):
        log_event(
            f"Communication: Sending {message.type.name} from {message.sender_id} to {message.receiver_id}"
        )
        self.queue.enqueue(message)

    def execute_one(self):
        """Process a single queued message if available."""
        message = self.queue.dequeue()
        if message:
            receiver = self.roles[message.receiver_id]
            sender = self.roles[message.sender_id]
            receiver.receive(message, sender)


# Abstract Role class
class Role(ABC):
    def __init__(self, role_id: RoleId, neighbors: list[RoleId], communication: CommunicationSystem):
        self.role_id = role_id
        self.neighbor_ids = neighbors
        self.communication = communication

    @abstractmethod
    def send(self, message_type: MessageType, addressees: list[RoleId]):
        pass

    @abstractmethod
    def receive(self, message: Message, sender: Optional[Role]):
        pass

    @abstractmethod
    def is_terminated(self) -> bool:
        pass


# Initiator role
class Initiator(Role):
    def __init__(self, role_id: RoleId, neighbors: list[RoleId], communication: CommunicationSystem):
        super().__init__(role_id, neighbors, communication)
        self.received_acks = 0

    def send(self, message_type: MessageType, addressees: list[RoleId]):
        for neighbor_id in addressees:
            self.communication.send(
                Message(message_type, message_type.name, self.role_id, neighbor_id)
            )

    def receive(self, message: Message, sender: Optional[Role]):
        log_event(f"Node {self.role_id} received '{message.type.name}' from {sender.role_id}")
        if message.type == MessageType.ACK:
            self.handle_ack()

    def handle_ack(self):
        self.received_acks += 1
        if self.is_terminated():
            log_event(f"Node {self.role_id}: Echo complete.")
            log_event(f"Node {self.role_id}: Algorithm finished.")

    def start(self):
        self.send(MessageType.ECHO, self.neighbor_ids)

    def is_terminated(self) -> bool:
        return self.received_acks == len(self.neighbor_ids)


# Participant role
class Participant(Role):
    def __init__(self, role_id: RoleId, neighbors: list[RoleId], communication: CommunicationSystem):
        super().__init__(role_id, neighbors, communication)
        self.parent_id: Optional[RoleId] = None
        self.received = False
        self.received_acks = 0

    def send(self, message_type: MessageType, addressees: list[RoleId]):
        for neighbor_id in addressees:
            if neighbor_id != self.parent_id:
                self.communication.send(
                    Message(message_type, message_type.name, self.role_id, neighbor_id)
                )

    def receive(self, message: Message, sender: Optional[Role]):
        log_event(f"Node {self.role_id} received '{message.type.name}' from {sender.role_id}")
        if message.type == MessageType.ECHO:
            self.handle_echo(sender.role_id)
        elif message.type == MessageType.ACK:
            self.handle_ack()

    def handle_echo(self, sender_id: RoleId):
        if not self.received:
            self.received = True
            self.parent_id = sender_id
            children = [n for n in self.neighbor_ids if n != self.parent_id]
            if children:
                self.send(MessageType.ECHO, children)
            else:
                self.finish()

    def handle_ack(self):
        self.received_acks += 1
        if self.received_acks == self.expected_acks():
            self.finish()

    def expected_acks(self) -> int:
        return len([n for n in self.neighbor_ids if n != self.parent_id])

    def finish(self):
        log_event(f"Node {self.role_id}: Echo complete.")
        if self.parent_id:
            self.communication.send(
                Message(MessageType.ACK, MessageType.ACK.name, self.role_id, self.parent_id)
            )
        log_event(f"Node {self.role_id}: Algorithm finished.")

    def is_terminated(self) -> bool:
        return self.received and self.received_acks == self.expected_acks()


# Load graph from file
def load_graph(filename: str) -> dict:
    with open(filename, "r") as f:
        return json.load(f)


# Create node instances
def create_nodes(
    graph_data: dict[str, dict], communication: CommunicationSystem
) -> dict[RoleId, Role]:
    temp_nodes: dict[RoleId, Role] = {}

    for role_name, info in graph_data.items():
        role_id = RoleId(role_name)
        neighbors = [RoleId(n) for n in info.get("neighbors", [])]
        role_type = info.get("role", "participant")

        temp_nodes[role_id] = (
            Initiator(role_id, neighbors, communication)
            if role_type == "initiator"
            else Participant(role_id, neighbors, communication)
        )

    return temp_nodes


# Main function
def main(graph_file="graph.json"):
    with open("execution_log.txt", "w") as log_file:
        log_file.write("Execution Log:\n")

    graph_data = load_graph(graph_file)
    task_queue = TaskQueue()

    # Pass role registry later after creation
    nodes: dict[RoleId, Role] = {}
    communication = CommunicationSystem(task_queue, nodes)
    nodes.update(create_nodes(graph_data, communication))

    initiator = next((n for n in nodes.values() if isinstance(n, Initiator)), None)
    if not initiator:
        print("No initiator found in the graph.")
        return

    initiator.start()

    while not all(n.is_terminated() for n in nodes.values()):
        communication.execute_one()


if __name__ == "__main__":
    main()
