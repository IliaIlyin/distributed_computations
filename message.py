class Message:
    def __init__(self, message_id,
                 message,
                 receiver,
                 sender):
        self.message_id = message_id
        self.message = message
        self.receiver = receiver
        self.sender = sender