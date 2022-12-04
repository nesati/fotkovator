class Module:
    def run_forever(self):
        return None


class Database(Module):
    def __init__(self, bus):
        self.bus = bus


class Backend(Module):
    def __init__(self, bus, database):
        self.bus = bus
        self.database = database

        self.bus.add_listener('rescan', self.rescan)

    async def rescan(self, *args):
        raise NotImplemented()

    def run_forever(self):
        raise NotImplemented('Backend must return a coroutine')


class BasicModule(Module):
    def __init__(self, bus, database, backend):
        self.bus = bus
        self.database = database
        self.backend = backend


class Frontend(BasicModule):
    pass


class TagModule(BasicModule):
    def tag(self, img):
        raise NotImplemented('TagModule must implement tag function')
