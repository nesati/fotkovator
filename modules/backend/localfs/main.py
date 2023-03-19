import asyncio
import os
from datetime import datetime
from io import BytesIO

import aiofiles.os
import PIL
import plum
from exif import Image as Exif, DATETIME_STR_FORMAT
from PIL import Image

from utils.interface import Backend


class LocalfsBackend(Backend):
    def __init__(self, bus, database, loop, config):
        super().__init__(bus, database, loop)
        self.path = config['path']
        self.max_concurrency = config.get('max_concurrency', 16)

    async def get_image(self, path, load=False, metadata=False):
        async with aiofiles.open(path, mode='rb') as f:
            if not load and not metadata:
                return await f.read()
            img = await f.read()
        img_file = BytesIO(img)
        metadata = {
            "uri": path,
            "path": os.path.abspath(path),
            "file_created": datetime.fromtimestamp(await aiofiles.os.path.getctime(path)),
            "file_modified": datetime.fromtimestamp(await aiofiles.os.path.getmtime(path)),
            "file_size": await aiofiles.os.path.getsize(path),
        }
        exif = Exif(img_file)
        if exif.has_exif:
            # extract common tags
            camera = [exif.get('make', None), exif.get('model', None)]
            camera = list(filter(lambda x: x is not None, camera))
            if camera:
                metadata['camera'] = ' '.join(camera)

            if dt_str := exif.get('datetime_original', None):
                metadata['datetime_original'] = datetime.strptime(dt_str, DATETIME_STR_FORMAT)

            if dt_str := exif.get('datetime_digitized', None):
                metadata['datetime_digitized'] = datetime.strptime(dt_str, DATETIME_STR_FORMAT)

            # TODO gps

        img_file.seek(0)
        loaded = Image.open(img_file)
        if load:
            img = loaded
        metadata['width'] = loaded.width
        metadata['height'] = loaded.height
        if 'datetime_original' in metadata:
            dt = metadata['datetime_original']
        else:
            dt = None

        if metadata:
            return img, path, dt, metadata
        else:
            return img

    async def get_thumbnail(self, path, load=False):
        async with aiofiles.open(path, mode='rb') as f:
            img = Exif(BytesIO(await f.read()))
            if load:
                return Image.open(BytesIO(img.get_thumbnail()))
            else:
                return img.get_thumbnail()

    async def rescan(self, scan_type, db_ready):
        await db_ready.wait()

        async def check_file(path, images):
            new, uid = await self.database.check_image(path)
            if new:
                try:
                    image = await self.get_image(path, load=True, metadata=True)
                    await self.bus.emit('new_image', (uid, asyncio.Event(), *image))
                    await self.bus.emit('done', uid)
                except (PIL.UnidentifiedImageError, plum.exceptions.UnpackError):
                    pass

            if uid in images:
                images.remove(uid)  # mark as found

        async def worker(q):
            encountered_exceptions = []
            try:
                while 1:
                    job = await q.get()
                    try:
                        await job
                    except Exception as e:
                        # don't raise exception now as it would stop the worker but save it for raising later
                        encountered_exceptions.append(e)
                    finally:  # this must happen even if exception is raised to prevent q.join from hanging forever
                        q.task_done()
            except asyncio.CancelledError:
                # don't raise an exception when the worker is stopped due to all tasks being done
                pass

            for e in encountered_exceptions:
                # raise exceptions for debugging
                raise e

        async def DFS(path, tasks, images):
            for item in await aiofiles.os.scandir(path):
                if item.is_file():
                    await tasks.put(check_file(item.path, images))
                elif item.is_dir():
                    await tasks.put(DFS(item.path, tasks, images))

        tasks = asyncio.Queue()
        images = set(map(lambda r: r['uid'], (await self.database.list_images())[0]))  # list of all uids found in db
        await tasks.put(DFS(self.path, tasks, images))
        workers = [asyncio.create_task(worker(tasks)) for _ in range(self.max_concurrency)]
        await tasks.join()  # wait for all tasks to be finished

        # cancel all workers
        for worker_task in workers:
            worker_task.cancel()

        await asyncio.gather(*workers)  # collect exceptions

        # remove deleted images from database
        await asyncio.gather(*map(lambda uid: asyncio.create_task(self.bus.emit('img_removed', uid)), images))

        await self.bus.emit('scan_done', ())

    async def run_forever(self):
        while 1:
            if not self.database.scan_in_progress:
                await self.bus.emit('rescan', ('periodic', asyncio.Event()))
            await asyncio.sleep(60)
