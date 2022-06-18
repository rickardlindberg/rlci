class Observable:

    def __init__(self):
        self.event_listeners = []

    def register_event_listener(self, event_listener):
        self.event_listeners.append(event_listener)

    def notify(self, event, data):
        for event_listener in self.event_listeners:
            event_listener.notify(event, data)
