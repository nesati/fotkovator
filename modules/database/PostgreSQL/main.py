import asyncpg

from utils.json_utils import decoder, encoder
from utils.interface import Database

COMMIT_INTERVAL = 60


class PostgreDatabase(Database):
    def __init__(self, bus, loop, config):
        super().__init__(bus, loop)
        self.tag_id_max = None
        self.bus.add_listener('stop', lambda *args: self.stop())
        self.user = config.get('user', 'fotkovator')
        self.password = config.get('password', None)
        self.database = config.get('database', 'fotkovator')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', None)
        self.pool = None
        self.last_commit = 0

    async def check_database(self):
        if self.pool is None:
            self.pool = await asyncpg.create_pool(user=self.user, password=self.password, database=self.database,
                                                  host=self.host, port=self.port)

            try:
                async with self.pool.acquire() as conn:
                    await conn.execute('''CREATE TABLE IF NOT EXISTS images (
                        uid serial PRIMARY KEY,
                        uri text UNIQUE NOT NULL,
                        created timestamp,
                        metadata json NOT NULL,
                        done boolean NOT NULL 
                    );''')
                    await conn.execute('''CREATE TABLE IF NOT EXISTS tags(
                        uid integer NOT NULL,
                        tag_id integer NOT NULL
                    );''')
                    await conn.execute('''CREATE TABLE IF NOT EXISTS tag_names(
                        tag_id serial PRIMARY KEY,
                         name text UNIQUE NOT NULL
                    );''')
            except asyncpg.exceptions.UniqueViolationError:  # conflict with other thread
                await self.check_database()  # retry

    async def add_image(self, uid, uri, dt, metadata):
        await self.check_database()

        async with self.pool.acquire() as conn:
            await conn.set_type_codec('json', encoder=encoder, decoder=decoder, schema='pg_catalog')
            await conn.execute('INSERT INTO images(uid, uri, created, metadata, done) VALUES ($1, $2, $3, $4, false);', uid, uri, dt,
                               metadata)

    async def check_image(self, uri):
        await self.check_database()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT uid, done FROM images WHERE uri=$1;', uri)
            if row is None:
                # get new uid
                uid = await conn.fetchval("SELECT nextval(pg_get_serial_sequence('images', 'uid')) as new_uid;")
            else:
                uid = row['uid']
        return row is None, uid  # TODO and row['done']

    async def get_image(self, uid):
        await self.check_database()

        async with self.pool.acquire() as conn:
            uri = await conn.fetchrow('SELECT uri FROM images WHERE uid=$1;', uid)

        return uri

    async def get_info(self, uid):
        await self.check_database()

        async with self.pool.acquire() as conn:
            await conn.set_type_codec('json', encoder=encoder, decoder=decoder, schema='pg_catalog')
            row = await conn.fetchrow('SELECT * FROM images WHERE uid=$1;', uid)

        return row

    async def get_tags(self, uid):
        await self.check_database()

        async with self.pool.acquire() as conn:
            results = await conn.fetch(
                'SELECT name FROM tag_names INNER JOIN tags ON tag_names.tag_id = tags.tag_id WHERE uid=$1;', uid)

        return results

    async def search(self, tagname, **kwargs):
        await self.check_database()

        tag_id = await self._get_tag_id(tagname)

        async with self.pool.acquire() as conn:
            n_imgs = await conn.fetchval('SELECT COUNT(*) FROM images INNER JOIN tags ON images.uid = tags.uid WHERE tag_id=$1;',
                                         tag_id)
            if 'page' in kwargs:
                out = await conn.fetch(
                    'SELECT images.uid, uri, created, metadata, done FROM images INNER JOIN tags ON images.uid = tags.uid WHERE tag_id=$1 ORDER BY created LIMIT $2 OFFSET $3;',
                    tag_id, kwargs['limit'], kwargs['page'] * kwargs['limit'])
            else:
                out = await conn.fetch(
                    'SELECT images.uid, uri, created, metadata, done FROM images INNER JOIN tags ON images.uid = tags.uid WHERE tag_id=$1 ORDER BY created;',
                    tag_id)

        # out = list(map(lambda t: dict(zip(('uid', 'time', 'metadata', 'done'), t)), out))
        return out, n_imgs

    async def mark_done(self, uid):
        await self.check_database()

        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE images SET done=true WHERE uid=$1;', uid)

    async def _get_tag_id(self, tag):
        await self.check_database()

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('SELECT tag_id FROM tag_names WHERE name=$1;', tag)

        if result is not None:
            result = result['tag_id']

        return result

    async def add_tag(self, uid, tag):
        await self.check_database()
        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            async with self.pool.acquire() as conn:
                await conn.execute('INSERT INTO tag_names(name) VALUES ($1)', tag)
                tag_id = await self._get_tag_id(tag)

        async with self.pool.acquire() as conn:
            await conn.execute('INSERT INTO tags VALUES ($1, $2)', uid, tag_id)

    async def remove_tag(self, uid, tag):
        await self.check_database()

        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            return False

        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM tags WHERE uid=$1 AND tag_id=$2;', uid, tag_id)

    async def list_tags(self):
        await self.check_database()

        async with self.pool.acquire() as conn:
            results = await conn.fetch('SELECT name FROM tag_names;')

        out = list(map(lambda x: x['name'], results))
        return out

    async def list_images(self, **kwargs):
        await self.check_database()

        async with self.pool.acquire() as conn:
            n_imgs = await conn.fetchval('SELECT COUNT(*) FROM images;')
            if 'page' in kwargs:
                results = await conn.fetch('SELECT * FROM images ORDER BY created LIMIT $1 OFFSET $2;', kwargs['limit'],
                                           kwargs['page'] * kwargs['limit'])
            else:
                results = await conn.fetch('SELECT * FROM images ORDER BY created;')

        return results, n_imgs

    def run_forever(self):
        return self.check_database()

    async def stop(self):
        await self.check_database()
        await self.pool.close()
