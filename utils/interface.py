class Module:
    def run_forever(self):
        return None


class Database(Module):
    """
    The database provides a way to store additional information about images (mainly tags).

    Only one database can be used at one time.
    """

    def __init__(self, bus, loop):
        """
        :param bus: EventBus instance
        :param loop: AsyncIO loop
        """
        self.bus = bus
        self.loop = loop

        self.bus.add_listener('new_image', lambda i: self.add_image(*i[1:], ))
        self.bus.add_listener('tag', lambda t: self.add_tag(*t))
        self.bus.add_listener('done', self.mark_done)

    async def add_image(self, uri, dt, metadata):
        """
        Creates a record for a given image in the database.
        :param uri: The image's identifier
        """
        raise NotImplementedError()

    async def check_image(self, uri):
        """
        Checks if the there exists a record for a given image in the database.
        :param uri: The image's backend identifier
        :return: bool
        """
        raise NotImplementedError()

    async def get_tags(self, uri):
        """
        Lists tags of a given image.
        :param uri: The image's identifier
        """
        raise NotImplementedError()

    async def add_tag(self, uri, tag):
        """
        Adds a tag to a given image.
        :param uri: The image's identifier
        :param tag: Tag name
        """
        raise NotImplementedError()

    async def remove_tag(self, uri, tag):
        """
        Removes a tag from a given image.
        :param uri: The image's identifier
        :param tag: Tag name
        """
        raise NotImplementedError()

    async def list_tags(self):
        """
        Lists all tags in the database.
        :return: list of tag names
        """
        raise NotImplementedError()

    async def mark_done(self, uri):
        """
        Marks image processing as done.
        :param uri: The image's identifier
        """
        raise NotImplementedError()


class Backend(Module):
    def __init__(self, bus, database, loop):
        self.bus = bus
        self.database = database
        self.loop = loop

        self.bus.add_listener('rescan', lambda *args: self.rescan)

    async def get_image(self, uri):
        raise NotImplementedError()

    async def rescan(self):
        raise NotImplementedError()

    def run_forever(self):
        raise NotImplementedError('Backend must return a coroutine')


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

        self.bus.add_listener('new_image', self.tag)

    def tag(self, img):
        raise NotImplementedError('TagModule must implement tag function')
