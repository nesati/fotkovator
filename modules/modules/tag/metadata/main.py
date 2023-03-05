from datetime import datetime

from utils.interface import TagModule
from modules.modules.tag.metadata import path_analyzer


class MetadataTagger(TagModule):
    """
    Analyzes basic information such as date, time, location, camera from file metadata, exif and path.
    Adds tags for folder names.
    """

    def __init__(self, bus, database, backend, loop, config):
        super().__init__(bus, database, backend, loop)

    async def tag(self, img):
        # analyze path
        dt = None
        if 'path' in img[4]:
            tags, dt = path_analyzer.analyze(img[4]['path'])
            for tag in tags:
                await self.bus.emit('tag', (img[0], tag, {}))

        # analyze exif
        if 'camera' in img[4]:
            await self.bus.emit('tag', (img[0], img[4]['camera'], {}))

        # analyze datetime
        if not img[3]:  # if the datetime was not taken from exif
            # if there's no date, or it is unprecise do extra analysis
            if dt is None or (dt.second == 0 and dt.minute == 0 and dt.hour == 0):
                # collect possible dates
                dts = {dt}
                if 'file_created' in img[3]:
                    dts.add(img[3]['file_created'])
                if 'file_modified' in img[3]:
                    dts.add(img[3]['file_modified'])

                # filter unix time 0 and future dates
                dts = filter(lambda dt: dt < datetime.now() and dt != datetime.fromtimestamp(0), dts)

                dt = min(dts)  # select oldest as it is most likely to be correct

            await self.bus.emit('dt', (img[1], dt))

        # add tag with datetime
        await self.bus.emit('tag', (img[0], (img[3] or dt).strftime('%-d. %-m. %Y'), {'color': (.75, .75, .75)}))
