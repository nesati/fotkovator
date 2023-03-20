from functools import partial

from utils.interface import BasicModule

EVENTS = {
    'stop',
    'rescan',
    'scan_done',
    'new_image',
    'tag',
    'done',
    'img_removed',
    'remove_tag',
    'rename_tag',
    'delete_tag',
    'dt',
}


class EventLogger(BasicModule):
    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

        for e in EVENTS:
            self.bus.add_listener(e, partial(self.log, e))

    def log(self, event, args):
        """
        Handles all configured events. Logs event type and arguments.

        This function is synchronous to ensure the event gets logged as soon as it is emitted before it starts to
        get handled by other modules.

        :param event: event name
        :param args: event arguments
        """
        print('EVENT', event, args)

        return self.dummy()  # this must return an awaitable

    async def dummy(self):
        pass
