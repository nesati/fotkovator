import re
from datetime import datetime, time
from pathlib import Path

from utils.interface import TagModule


class MetadataTagger(TagModule):
    """
    Adds subreddit tag based on filename
    """

    def __init__(self, bus, database, backend, search, loop, config):
        super().__init__(bus, database, backend, search, loop)

    async def tag(self, uid, db_ready, img, uri, created, metadata):
        # wait for database
        await db_ready.wait()

        # analyze filename
        if 'path' in metadata:
            path = list(map(lambda s: s.strip(), Path(metadata['path']).parts))  # split path
            filename = path[-1]

            match = re.match(r"^([^-]+)-[a-z0-9]{6,13}(\.png)?\.(jpg|gif|png|mp4)$", filename)

            if match is not None:
                await self.bus.emit('tag', (uid, match.group(1), {}))
