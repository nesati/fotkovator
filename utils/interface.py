class Module:
    def run_forever(self):
        return None


class Database(Module):
    """
    The database provides a way to store additional information about images (mainly tags).

    Only one database can be used at one time.
    """
    SCAN_RESET = {'manual'}

    def __init__(self, bus, loop):
        """
        :param bus: EventBus instance
        :param loop: AsyncIO loop
        """
        self.bus = bus
        self.loop = loop

        self.bus.add_listener('new_image', lambda i: self.add_image(i[0], *i[2:]))
        self.bus.add_listener('tag', lambda t: self.add_tag(*t[0:2], **t[2]))
        self.bus.add_listener('done', self.mark_done)
        self.bus.add_listener('rescan', lambda args: self.rescan(*args))
        self.bus.add_listener('img_removed', self.remove_image)

    async def add_image(self, uid, uri, dt, metadata):
        """
        Creates a record for a given image in the database.
        :param uid: int: The image's identifier
        :param uri: str: The image's backend identifier
        :param dt: datetime of the image's creation
        :param metadata: dict: additional information about the image
        """
        raise NotImplementedError()

    async def remove_image(self, uid):
        """
        Removes given image from database along with all relevant entries.
        :param uid: int: The image's identifier
        """
        raise NotImplementedError()

    async def check_image(self, uri):
        """
        Finds uid for the image (existing or new) and determines if the photo should be re-tagged.
        :param uri: str: The image's backend identifier
        :return: (bool: analyze, int: uid)
        """
        raise NotImplementedError()

    async def get_image(self, uid):
        """
        Get uri of an image.
        :param uid: int: The image's identifier
        :return: str: uri: The image's backend identifier
        """
        raise NotImplementedError()

    async def get_info(self, uid):
        """
        Get info about image.
        :param uid: int: The image's identifier
        :return: dict: must contain keys: uid, uri, dt, metadata, done
        """
        raise NotImplementedError()

    async def mark_done(self, uid):
        """
        Lists tags of a given image.
        :param uid: int: The image's identifier
        :return: list of strs
        """
        raise NotImplementedError()

    async def search(self, tagnames, **kwargs):
        """
        Search images based on tags.
        :param tagnames: list: str: names of the tag the image must have
        :return: list: dict: must contain keys: uid, uri, dt, metadata, done
        """
        raise NotImplementedError()

    async def add_tag(self, uid, tag, color=None, text_color=None):
        """
        Adds a tag to a given image.
        :param uid: int: The image's identifier
        :param tag: str: Tag name
        :param color: tuple: (R, G, B) color for the tag, values between 0-1
        :param text_color: tuple: (R, G, B) color for the tags name, values between 0-1
        """
        raise NotImplementedError()

    async def remove_tag(self, uid, tag):
        """
        Removes a tag from a given image.
        :param uid: int: The image's identifier
        :param tag: Tag name
        """
        raise NotImplementedError()

    async def list_tags(self):
        """
        Lists all tags in the database.
        :return: list of tag names
        """
        raise NotImplementedError()

    async def list_images(self, **kwargs):
        """
        Get images.
        :return: list: dict: must contain keys: uid, uri, dt, metadata, done
        """
        raise NotImplementedError()

    async def reset_db(self):
        """
        Remove all data from database
        """
        raise NotImplementedError()

    async def rescan(self, scan_type, db_ready):
        """
        Prepare database for rescanning images.

        :param scan_type: str: one of manual,
        :param db_ready: asyncio.Event: database ready, must be set
        :return:
        """
        if scan_type in self.SCAN_RESET:
            await self.reset_db()
        db_ready.set()


class Backend(Module):
    def __init__(self, bus, database, loop):
        self.bus = bus
        self.database = database
        self.loop = loop

        self.bus.add_listener('rescan', lambda args: self.rescan(*args))

    async def get_image(self, uri, load=False):
        """
        Get image data.
        :param uri: str: The image's backend identifier
        :param load: whether to open the image with PIL
        :return: if load=True PIL.image; if load=False bytes
        """
        raise NotImplementedError()

    async def get_thumbnail(self, uri, load=False):
        """
        Get thumbnail for given image.
        :param uri: str: The image's backend identifier
        :param load: whether to open the image with PIL
        :return: if load=True PIL.image; if load=False bytes
        """
        raise NotImplementedError()

    async def rescan(self, scan_type, db_ready):
        """
        Force detect new images.
        """
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
