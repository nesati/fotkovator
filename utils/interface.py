class Module:
    def run_forever(self):
        """
        Main process of the module.
        """
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

        self.bus.add_listener('new_image', lambda i: self.add_image(*i[0:2]+i[3:]))
        self.bus.add_listener('tag', lambda t: self.add_tag(*t[0:2], **t[2]))
        self.bus.add_listener('done', self.mark_done)
        self.bus.add_listener('rescan', lambda args: self.rescan(*args))
        self.bus.add_listener('img_removed', self.remove_image)
        self.bus.add_listener('scan_done', lambda args: self.scan_done())
        self.bus.add_listener('remove_tag', lambda args: self.remove_tag(*args))
        self.bus.add_listener('rename_tag', lambda args: self.rename_tag(*args))
        self.bus.add_listener('delete_tag', lambda args: self.delete_tag(*args))
        self.scan_in_progress = False

    async def add_image(self, uid, db_ready, uri, dt, metadata):
        """
        Creates a record for a given image in the database.
        :param uid: int: The image's identifier
        :param db_ready: asyncio.Event signifying whether the database is ready for actions on image
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

    async def rename_tag(self, old_name, new_name):
        """
        Crates an alias for the tag. Both tags should be equivalent when adding or removing tags.

        :param old_name: tag to rename
        :param new_name: name of the alias
        """
        raise NotImplementedError()

    async def delete_tag(self, tag):
        """
        Deletes tag from tag list and all images.
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
        if self.scan_in_progress:
            raise RuntimeError('Scan already in progress')
        if scan_type in self.SCAN_RESET:
            await self.reset_db()
        self.scan_in_progress = True
        db_ready.set()

    async def scan_done(self):
        """
        Handles scan_done event. Unblocks scanning.
        """
        self.scan_in_progress = False


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
    def __init__(self, bus, database, backend, search, loop):
        self.bus = bus
        self.database = database
        self.backend = backend
        self.search = search
        self.loop = loop


class Frontend(BasicModule):
    pass


class TagModule(BasicModule):
    def __init__(self, bus, database, backend, search, loop):
        super().__init__(bus, database, backend, search, loop)

        self.bus.add_listener('new_image', lambda img: self.tag(*img))

    def tag(self, uid, db_ready, img, uri, dt, metadata):
        """
        Analyze image.
        :param uid: int: The image's identifier
        :param db_ready: asyncio.Event signifying whether the database is ready for actions on image
        :param img: PIL.Image: The image itself
        :param uri: str: The image's backend identifier
        :param dt: datetime of the image's creation
        :param metadata: dict: additional information about the image
        """
        raise NotImplementedError('TagModule must implement tag function')


class SearchModule(Module):
    def __init__(self, bus, database, backend, loop):
        self.bus = bus
        self.database = database
        self.backend = backend
        self.loop = loop

    def search(self, query):
        raise NotImplementedError()


class KNNCapability(Database):
    def knn_query(self, module, table, column, vector, distance='L2', limit=None, offset=0):
        raise NotImplementedError('KNN capable database must implement knn_query mathod')
