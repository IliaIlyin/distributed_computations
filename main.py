import json
import random
import time
from abc import ABC, abstractmethod

class Role(ABC):
    @abstractmethod
    def send(self, message, addressee):
        pass

    @abstractmethod
    def receive(self, variable, sender=None):
        pass

def log_event(event):
    with open("execution_log.txt", "a") as log_file:
        log_file.write(event + "\n")

class Message:
    def __init__(self, content, sender, receiver):
        self.content = content
        self.sender = sender
        self.receiver = receiver

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
            self.nodes[message.receiver.name].receive(message.content, message.sender)

scheduler = None

class Initiator(Role):
    def __init__(self, name, neighbors):
        self.name = name
        self.neighbors = neighbors
        self.received_acks = 0

    def send(self, message, addressees):
        for neighbor in addressees:
            scheduler.schedule_message(Message(message, self, neighbor))

    def receive(self, variable, sender=None):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        if variable == "ACK":
            self.received_acks += 1
            if self.received_acks == len(self.neighbors):
                log_event(f"Node {self.name}: Echo complete.")
                log_event(f"Node {self.name}: Algorithm finished.")

    def start(self):
        self.send("ECHO", self.neighbors)

class Participant(Role):
    def __init__(self, name, neighbors):
        self.name = name
        self.neighbors = neighbors
        self.parent = None
        self.received = False
        self.received_acks = 0

    def send(self, message, addressees):
        for neighbor in addressees:
            if neighbor != self.parent:
                scheduler.schedule_message(Message(message, self, neighbor))

    def receive(self, variable, sender=None):
        log_event(f"Node {self.name} received '{variable}' from {sender.name}")
        if variable == "ECHO":
            if not self.received:
                self.received = True
                self.parent = sender
                children = [n for n in self.neighbors if n != self.parent]
                if children:
                    self.send("ECHO", self.neighbors)
                else:
                    log_event(f"Node {self.name}: Echo complete.")
                    if self.parent:
                        scheduler.schedule_message(Message("ACK", self, self.parent))
                    log_event(f"Node {self.name}: Algorithm finished.")
        elif variable == "ACK":
            self.received_acks += 1
            expected_acks = len([n for n in self.neighbors if n != self.parent])
            if self.received_acks == expected_acks:
                log_event(f"Node {self.name}: Echo complete.")
                if self.parent:
                    scheduler.schedule_message(Message("ACK", self, self.parent))
                log_event(f"Node {self.name}: Algorithm finished.")


def load_graph(filename):
    with open(filename, 'r') as f:
        return json.load(f)

def create_nodes(graph_data) -> dict[str, Role]:
    nodes = {}
    for node, info in graph_data.items():
        role = info.get("role", "participant")
        nodes[node] = Initiator(node, []) if role == "initiator" else Participant(node, [])
    for node, info in graph_data.items():
        nodes[node].neighbors = [nodes[n] for n in info.get("neighbors", [])]
    return nodes

def main():
    global scheduler
    filename = "graph.json"
    graph_data = load_graph(filename)
    nodes = create_nodes(graph_data)
    scheduler = MessageScheduler(nodes)

    with open("execution_log.txt", "w") as log_file:
        log_file.write("Execution Log:\n")

    initiator = next((n for n in nodes.values() if isinstance(n, Initiator)), None)
    if initiator:
        initiator.start()
        while any(
            isinstance(n, Participant) and n.received and n.received_acks < len([x for x in n.neighbors if x != n.parent])
            or isinstance(n, Initiator) and n.received_acks < len(n.neighbors)
            for n in nodes.values()
        ):
            scheduler.process_message()
    else:
        print("No initiator found in the graph.")

if __name__ == "__main__":
    main()
