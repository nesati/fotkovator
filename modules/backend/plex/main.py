import asyncio
from datetime import datetime
from io import BytesIO

import aiohttp as aiohttp
from PIL import Image
from plexapi import X_PLEX_CONTAINER_SIZE
from plexapi.server import PlexServer

from modules.backend.localfs.main import worker
from utils.interface import Backend


class PlexBackend(Backend):
    def __init__(self, bus, database, loop, config):
        super().__init__(bus, database, loop)

        self.max_concurrency = config.get('max_concurrency', 8)

        self.plex = PlexServer(config.get('base_url'), config.get('XPlexToken'))
        self.library = self.plex.library.section(config.get('section'))

        # datetime.min is considered invalid by plex
        self.last_scan = datetime(month=1, day=1, year=2000)  # before plex initial release

    async def _get_image(self, photo, load=False, return_metadata=False):
        """
        Download a plex photo and get metadata.

        :param photo: plexapi photo object
        :return: filename, PIL image, path of server
        """

        # url for full resolution photo
        part = photo.media[0].parts[0]
        url = self.plex.url(part.key + '?download=1', includeToken=True)

        async with aiohttp.ClientSession() as session:
            r = await session.get(url)
            while 1:
                try:
                    img = await r.read()
                except aiohttp.client_exceptions.ClientPayloadError:
                    await asyncio.sleep(1)  # wait for  Response payload to be completed
                else:
                    break

        if load:
            img = Image.open(BytesIO(img))

        metadata = {
            "uri": photo.guid,
            "path": part.file,
            "file_modified": photo.updatedAt,
            "file_size": part.size,
            "datetime_original": photo.originallyAvailableAt,
            "width": photo.media[0].width,
            "height": photo.media[0].height,
        }

        camera = [photo.media[0].make, photo.media[0].model]
        camera = list(filter(lambda x: x is not None, camera))
        if camera:
            metadata['camera'] = ' '.join(camera)

        if return_metadata:
            return img, photo.guid, metadata['datetime_original'], metadata
        else:
            return img

    async def _get_by_guid(self, guid):
        def _blocking_get_by_guid(guid):
            return self.plex.library.search(guid=guid)[0]
        return await self.loop.run_in_executor(None, _blocking_get_by_guid, guid)

    async def get_image(self, uri, load=False, metadata=False):
        return await self._get_image(await self._get_by_guid(uri), load=load, return_metadata=metadata)

    async def get_thumbnail(self, uri, load=False):
        photo = await self._get_by_guid(uri)

        async with aiohttp.ClientSession() as session:
            r = await session.get(photo.thumbUrl)
            img = await r.read()

        if load:
            img = Image.open(BytesIO(img))

        return img

    async def _check_photo(self, photo, images):
        new, uid = await self.database.check_image(photo.guid)
        if new:
            image = await self._get_image(photo, load=True, return_metadata=True)
            await self.bus.emit('new_image', (uid, asyncio.Event(), *image))
            await self.bus.emit('done', uid)
        if uid in images:
            images.remove(uid)  # mark as found

    async def rescan(self, scan_type, db_ready):
        images = set(
            map(lambda r: r['uid'], (await self.database.list_images())[0]))  # list of all uids found in db

        tasks = asyncio.Queue()

        async def search_task(queue, **kwargs):
            limit = X_PLEX_CONTAINER_SIZE
            i = 0

            def search_runner(container_start, container_size, kwargs):
                return self.library.search(container_start=container_start, container_size=container_size, **kwargs)

            while 1:
                # get batch
                subresults = await self.loop.run_in_executor(None, search_runner, i * limit, limit, kwargs)

                # check if at the end
                if len(subresults) == 0:
                    return

                    # add tasks
                for photo in subresults:
                    await queue.put(self._check_photo(photo, images))

        await tasks.put(search_task(tasks, **{'libtype': 'photo', 'addedAt>>=': self.last_scan}))

        workers = [asyncio.create_task(worker(tasks)) for _ in range(self.max_concurrency)]
        await tasks.join()  # wait for all tasks to be finished

        # cancel all workers
        for worker_task in workers:
            worker_task.cancel()

        await asyncio.gather(*workers)  # collect exceptions

        # remove deleted images from database
        await asyncio.gather(*map(lambda uid: asyncio.create_task(self.bus.emit('img_removed', uid)), images))

        await self.bus.emit('scan_done', ())
        self.last_scan = datetime.now()

    async def run_forever(self):
        while 1:
            if not self.database.scan_in_progress:
                await self.bus.emit('rescan', ('periodic', asyncio.Event()))
            await asyncio.sleep(20)
