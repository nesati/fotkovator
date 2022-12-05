"""
https://github.com/joeltok/py-event-bus
"""
import asyncio


class EventBus:
    def __init__(self):
        self.listeners = {}

    def add_listener(self, event_name, listener):
        if not self.listeners.get(event_name, None):
            self.listeners[event_name] = {listener}
        else:
            self.listeners[event_name].add(listener)

    def remove_listener(self, event_name, listener):
        self.listeners[event_name].remove(listener)
        if len(self.listeners[event_name]) == 0:
            del self.listeners[event_name]

    async def emit(self, event_name, event):
        listeners = self.listeners.get(event_name, [])
        tasks = []
        for listener in listeners:
            tasks.append(asyncio.create_task(listener(event)))
        await asyncio.gather(*tasks)
