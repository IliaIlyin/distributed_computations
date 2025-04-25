from abc import ABC, abstractmethod

class Role(ABC):
    @abstractmethod
    def do_spec(self, label=None, guard=None, action=None, next_label=None):
        pass

    @abstractmethod
    def send_spec(self, message, addressee):
        pass

    @abstractmethod
    def receive_spec(self, variable, sender=None):
        pass


def log_event(event):
    with open("execution_log.txt", "a") as log_file:
        log_file.write(event + "\n")