import json
import time

import aiosqlite

from utils.interface import Database

COMMIT_INTERVAL = 60


class SqliteDatabase(Database):
    def __init__(self, bus, loop, config):
        super().__init__(bus, loop)
        self.bus.add_listener('stop', lambda *args: self.stop())
        self.path = config['path']
        self.db = None
        self.last_commit = 0

    async def check_database(self):
        if self.db is None:
            self.db = await aiosqlite.connect(self.path)
            cursor = await self.db.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='images';")
            if len(await cursor.fetchall()) == 0:
                await self.db.execute('CREATE TABLE images(uid text, time interval, metadata text);')
                await self.db.execute('CREATE UNIQUE INDEX images_index ON images(uid);')
            await cursor.close()
            cursor = await self.db.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='tags';")
            if len(await cursor.fetchall()) == 0:
                await self.db.execute('CREATE TABLE tags(uid text, tag_id integer);')
                await self.db.execute('CREATE INDEX tag_index ON tags(uid, tag_id);')
            await cursor.close()
            cursor = await self.db.execute("SELECT * FROM sqlite_master WHERE type='table' AND name='tag_names';")
            if len(await cursor.fetchall()) == 0:
                await self.db.execute('CREATE TABLE tag_names(tag_id integer, name text);')
                await self.db.execute('CREATE UNIQUE INDEX tagname_index ON tag_names(tag_id);')
            await cursor.close()
        if time.time() - self.last_commit > COMMIT_INTERVAL:
            await self.db.commit()
            self.last_commit = time.time()

    async def add_image(self, uid, dt, metadata):
        await self.check_database()
        if dt is not None:
            dt = dt.timestamp()
        await self.db.execute('INSERT INTO images VALUES (?,?,?);', (uid, dt, json.dumps(metadata)))

    async def check_image(self, uid):
        await self.check_database()
        cursor = await self.db.execute('SELECT * FROM images WHERE  uid=?;', (uid,))
        out = await cursor.fetchall()
        await cursor.close()
        return out

    async def get_tags(self, uid):
        await self.check_database()
        cursor = await self.db.execute(
            'SELECT name FROM tag_names INNER JOIN tags ON tag_names.id = tags.tag_id WHERE uid=?;', (uid,))
        out = await cursor.fetchall()
        await cursor.close()
        return out

    async def _get_tag_id(self, tag):
        await self.check_database()
        cursor = await self.db.execute('SELECT id FROM tag_names WHERE name=?;', (tag,))
        out = await cursor.fetchall()
        await cursor.close()
        assert len(out) <= 1
        if len(out) == 0:
            return None
        else:
            return out[0]

    async def add_tag(self, uid, tag):
        await self.check_database()
        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            tag_id = await self.db.execute('SELECT (seq+1) FROM sqlite_sequence WHERE name="tag_names"')
            await self.db.execute('INSERT INTO tag_names VALUES (?, ?)', tag_id, tag)
        await self.db.execute('INSERT INTO tags VALUES (?, ?)', uid, tag_id)

    async def remove_tag(self, uid, tag):
        await self.check_database()
        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            return
        await self.db.execute('DELETE FROM tags WHERE uid=? AND tag_id=?;', (uid, tag_id))

    async def list_tags(self):
        await self.check_database()
        cursor = await self.db.execute('SELECT name FROM tag_names;')
        raise NotImplementedError()

    def run_forever(self):
        return self.check_database()

    async def stop(self):
        await self.check_database()
        await self.db.commit()
        await self.db.close()
