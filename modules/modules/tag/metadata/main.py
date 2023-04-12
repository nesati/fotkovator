from datetime import datetime, time

from utils.interface import TagModule
from modules.modules.tag.metadata import path_analyzer


# https://stackoverflow.com/a/10748024
def time_in_range(start, end, x):
    """Return true if x is in the range [start, end]"""
    if start <= end:
        return start <= x <= end
    else:
        return start <= x or x <= end


class MetadataTagger(TagModule):
    """
    Analyzes basic information such as date, time, location, camera from file metadata, exif and path.
    Adds tags for folder names.
    """

    def __init__(self, bus, database, backend, search, loop, config):
        super().__init__(bus, database, backend, search, loop)

    async def tag(self, uid, db_ready, img, uri, created, metadata):
        # wait for database
        await db_ready.wait()

        # analyze path
        dt = None
        if 'path' in metadata:
            tags, dt = path_analyzer.analyze(metadata['path'])
            for tag in tags:
                await self.bus.emit('tag', (uid, tag, {}))

        # analyze exif
        if 'camera' in metadata:
            await self.bus.emit('tag', (uid, metadata['camera'], {}))

        # analyze datetime
        if not created:  # if the datetime was not taken from exif
            # if there's no date, or it is unprecise do extra analysis
            if dt is None or (dt.second == 0 and dt.minute == 0 and dt.hour == 0):
                # collect possible dates
                dts = set()
                if dt is not None:
                    dts.add(dt)
                if 'file_created' in metadata:
                    dts.add(metadata['file_created'])
                if 'file_modified' in metadata:
                    dts.add(metadata['file_modified'])

                # filter unix time 0 and future dates
                dts = filter(lambda dt: dt < datetime.now() and dt != datetime.fromtimestamp(0), dts)

                dt = min(dts)  # select oldest as it is most likely to be correct

            await self.bus.emit('dt', (uid, dt))

        # time of day
        if created:
            if created.second != 0 or created.minute != 0 or created.hour != 0:  # if time is not 00:00:00
                # extract time
                created_time = time(hour=created.hour, minute=created.minute, second=created.second)

                # categorize time
                if time_in_range(time(5, 00, 0), time(9, 30, 0), created_time):
                    await self.bus.emit('tag', (uid, 'ráno', {'color': (.8, 1, .4)}))
                elif time_in_range(time(9, 30, 0), time(11, 30, 0), created_time):
                    await self.bus.emit('tag', (uid, 'dopoledne', {'color': (.2, .6, 1)}))
                elif time_in_range(time(11, 30, 0), time(12, 30, 0), created_time):
                    await self.bus.emit('tag', (uid, 'poledne', {'color': (1, 1, .4)}))
                elif time_in_range(time(12, 30, 0), time(19, 00, 0), created_time):
                    await self.bus.emit('tag', (uid, 'odpoledne', {'color': (.4, .8, 1)}))
                elif time_in_range(time(19, 00, 0), time(23, 30, 0), created_time):
                    await self.bus.emit('tag', (uid, 'večer', {'color': (.35, .35, .35)}))
                elif time_in_range(time(23, 30, 0), time(00, 30, 0), created_time):
                    await self.bus.emit('tag', (uid, 'půlnoc', {'color': (0, 0, 0)}))
                elif time_in_range(time(00, 30, 0), time(5, 00, 0), created_time):
                    await self.bus.emit('tag', (uid, 'noc', {'color': (0, 0, 0)}))

        # add tag with datetime
        await self.bus.emit('tag', (uid, (created or dt).strftime('%d. %m. %Y').replace(' 0', ' '), {'color': (.75, .75, .75)}))
