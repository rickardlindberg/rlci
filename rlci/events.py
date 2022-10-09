class Observable:

    def __init__(self):
        self.event_listeners = []

    def register_event_listener(self, event_listener):
        self.event_listeners.append(event_listener)

    def notify(self, event, data):
        for event_listener in self.event_listeners:
            event_listener.notify(event, data)

class Events(list):

    @staticmethod
    def capture_from(*observalbes):
        events = Events()
        for observable in observalbes:
            observable.register_event_listener(events)
        return events

    def listen(self, observable):
        observable.register_event_listener(self)
        return observable

    def notify(self, event, data):
        self.append((event, data))

    def filter(self, *events):
        return Events(x for x in self if x[0] in events)

    def has(self, event, data):
        return (event, data) in self

    def __repr__(self):
        def data_repr(data):
            if isinstance(data, dict):
                return "".join(
                    f"\n    {key}: {repr(data[key])}"
                    for key in sorted(data.keys())
                )
            else:
                return f" {repr(data)}"
        return "\n".join(f"{event} =>{data_repr(data)}" for event, data in self)
