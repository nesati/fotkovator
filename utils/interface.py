class Module:
    def run_forever(self):
        return None


class Database(Module):
    def __init__(self, bus, loop):
        self.bus = bus
        self.loop = loop


class Backend(Module):
    def __init__(self, bus, database, loop):
        self.bus = bus
        self.database = database
        self.loop = loop

        self.bus.add_listener('rescan', self.rescan)

    async def rescan(self, *args):
        raise NotImplemented()

    def run_forever(self):
        raise NotImplemented('Backend must return a coroutine')


class BasicModule(Module):
    def __init__(self, bus, database, backend, loop):
        self.bus = bus
        self.database = database
        self.backend = backend
        self.loop = loop


class Frontend(BasicModule):
    pass


class TagModule(BasicModule):
    def __init__(self, bus, database, backend, loop):
        super().__init__(bus, database, backend, loop)

    def tag(self, img):
        raise NotImplemented('TagModule must implement tag function')
