import asyncio
import re
from typing import Iterable

import asyncpg

from utils.color import random_color, rgb2hex, contrast_color
from utils.json_utils import decoder, encoder
from utils.interface import Database


class PostgreDatabase(Database):
    def __init__(self, bus, loop, config):
        super().__init__(bus, loop)
        self.tag_id_max = None
        self.bus.add_listener('stop', self.stop)
        self.user = config.get('user', 'fotkovator')
        self.password = config.get('password', None)
        self.database = config.get('database', 'fotkovator')
        self.host = config.get('host', 'localhost')
        self.port = config.get('port', None)
        self.pool = None
        self.last_commit = 0
        self.db_ready = asyncio.Event()

    async def check_database(self):
        self.pool = await asyncpg.create_pool(user=self.user, password=self.password, database=self.database,
                                              host=self.host, port=self.port)

        async with self.pool.acquire() as conn:
            await conn.execute('''CREATE TABLE IF NOT EXISTS images (
                uid serial PRIMARY KEY,
                uri text UNIQUE NOT NULL,
                created timestamp,
                metadata json NOT NULL,
                done boolean NOT NULL 
            );''')
            await conn.execute('''CREATE TABLE IF NOT EXISTS tag_names(
                tag_id serial PRIMARY KEY,
                name text UNIQUE NOT NULL,
                color text NOT NULL,
                text_color text NOT NULL,
                alias text UNIQUE NOT NULL
            );''')
            await conn.execute('''CREATE TABLE IF NOT EXISTS tags(
                uid integer REFERENCES images(uid) ON UPDATE CASCADE ON DELETE CASCADE,
                tag_id integer REFERENCES tag_names(tag_id) ON UPDATE CASCADE ON DELETE CASCADE,
                CONSTRAINT image_tag_pkey PRIMARY KEY (uid, tag_id)
            );''')

        self.db_ready.set()

    async def add_image(self, uid, db_ready, uri, dt, metadata):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            await conn.set_type_codec('json', encoder=encoder, decoder=decoder, schema='pg_catalog')
            try:
                await conn.execute('INSERT INTO images(uid, uri, created, metadata, done) VALUES ($1, $2, $3, $4, false);',
                                   uid, uri, dt, metadata)
            except asyncpg.exceptions.UniqueViolationError:  # already created in previous session but not done
                pass

        db_ready.set()

    async def remove_image(self, uid):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM images WHERE uid=$1;', uid)

    async def check_image(self, uri):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT uid, done FROM images WHERE uri=$1;', uri)
            if row is None:
                # get new uid
                uid = await conn.fetchval("SELECT nextval(pg_get_serial_sequence('images', 'uid')) as new_uid;")
            else:
                uid = row['uid']
        return row is None or not row['done'], uid

    async def get_image(self, uid):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            row = await conn.fetchrow('SELECT * FROM images WHERE uid=$1;', uid)

        return dict(row)

    async def get_info(self, uid):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            await conn.set_type_codec('json', encoder=encoder, decoder=decoder, schema='pg_catalog')
            row = await conn.fetchrow('SELECT * FROM images WHERE uid=$1;', uid)

        if row is not None:
            return dict(row)

    async def get_tags(self, uid):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            results = await conn.fetch(
                'SELECT * FROM tag_names INNER JOIN tags ON tag_names.tag_id = tags.tag_id WHERE uid=$1;', uid)

        return list(map(dict, results))

    async def search(self, tagnames, **kwargs):
        await self.db_ready.wait()

        if len(tagnames) == 0:
            return await self.list_images(**kwargs)

        tag_ids = await asyncio.gather(*map(self._get_tag_id, tagnames))

        async with self.pool.acquire() as conn:
            n_imgs = await conn.fetchval("""
                SELECT COUNT(*)
                FROM (
                    SELECT images.uid
                    FROM images
                    JOIN tags ON images.uid = tags.uid
                    WHERE tags.tag_id = any($1::int[])
                    GROUP BY images.uid
                    HAVING COUNT(tags.uid) = $2
                ) AS subquery;
                """, tag_ids, len(tag_ids))

            if n_imgs is None:
                n_imgs = 0

            if 'page' in kwargs:
                out = await conn.fetch("""
                    SELECT images.uid, uri, created, metadata, done
                    FROM images
                    JOIN tags ON images.uid = tags.uid
                    WHERE tags.tag_id = any($1::int[])
                    GROUP BY images.uid
                    HAVING COUNT(tags.uid) = $2
                    ORDER BY created DESC LIMIT $3 OFFSET $4;
                    """, tag_ids, len(tag_ids), kwargs['limit'], kwargs['page'] * kwargs['limit'])
            else:
                out = await conn.fetch("""
                SELECT images.uid, uri, created, metadata, done
                FROM images
                JOIN tags ON images.uid = tags.uid
                WHERE tags.tag_id = any($1::int[])
                GROUP BY images.uid
                HAVING COUNT(tags.uid) = $2
                ORDER BY created DESC;
                """, tag_ids, len(tag_ids))

        return list(map(dict, out)), n_imgs

    async def mark_done(self, uid):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE images SET done=true WHERE uid=$1;', uid)

    async def _get_tag_id(self, tag):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            result = await conn.fetchrow('SELECT tag_id FROM tag_names WHERE name=$1 OR alias=$1;', tag)

        if result is not None:
            result = result['tag_id']

        return result

    async def add_tag(self, uid, tag, color=None, text_color=None):
        await self.db_ready.wait()

        assert text_color is None or color is not None, 'must specify color when specifying text_color'

        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            if color is None:
                color = random_color()

            if text_color is None:
                text_color = contrast_color(*color)

            color, text_color = rgb2hex(*color), rgb2hex(*text_color)

            async with self.pool.acquire() as conn:
                try:
                    await conn.execute('INSERT INTO tag_names(name, color, text_color, alias) VALUES ($1, $2, $3, $1)',
                                       tag, color, text_color)
                except asyncpg.exceptions.UniqueViolationError:  # already created in another thread
                    pass
            tag_id = await self._get_tag_id(tag)

        async with self.pool.acquire() as conn:
            try:
                await conn.execute('INSERT INTO tags VALUES ($1, $2)', uid, tag_id)
            except asyncpg.exceptions.UniqueViolationError:
                # duplicate tags not allowed. Probably partially tagged, interrupted than re-tagged
                pass

    async def remove_tag(self, uid, tag):
        await self.db_ready.wait()

        tag_id = await self._get_tag_id(tag)
        if tag_id is None:
            return False

        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM tags WHERE uid=$1 AND tag_id=$2;', uid, tag_id)

    async def rename_tag(self, old_name, new_name):
        await self.db_ready.wait()
        tag_id = await self._get_tag_id(old_name)

        # check for conflicts
        assert new_name not in map(lambda t: t['name'], await self.list_tags()) or tag_id == await self._get_tag_id(new_name)

        async with self.pool.acquire() as conn:
            await conn.execute('UPDATE tag_names SET alias=$1 WHERE tag_id=$2', new_name, tag_id)

    async def delete_tag(self, tag):
        await self.db_ready.wait()

        tag_id = await self._get_tag_id(tag)

        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM tag_names WHERE tag_id=$1', tag_id)

    async def list_tags(self):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            results = await conn.fetch('SELECT * FROM tag_names;')

        return list(map(dict, results))

    async def list_images(self, **kwargs):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            n_imgs = await conn.fetchval('SELECT COUNT(*) FROM images;')

            if n_imgs is None:
                n_imgs = 0

            if 'page' in kwargs:
                results = await conn.fetch('SELECT * FROM images ORDER BY created DESC LIMIT $1 OFFSET $2;',
                                           kwargs['limit'], kwargs['page'] * kwargs['limit'])
            else:
                results = await conn.fetch('SELECT * FROM images ORDER BY created DESC;')

        return list(map(dict, results)), n_imgs

    async def reset_db(self):
        await self.db_ready.wait()
        async with self.pool.acquire() as conn:
            await conn.execute('DELETE FROM images;')
            await conn.execute('DELETE FROM tags;')

    def _convert_selector(self, key, value, i):
        key = self._sanitize(key)  # WARNING: Do not omit this in any method extending this functionality
        if isinstance(value, (int, str)):
            return f'{key} = ${i}\n'
        elif isinstance(value, Iterable):
            return f'{key} = ANY(${i})\n'
        else:
            raise NotImplementedError()

    def _convert_selectors(self, selector, i=1):
        """
        Convert from selector dict to WHERE statement.

        :param selector: dict: selector in the format {column: value}
        :param i: int: starting i to be used in asyncpg $i syntax
        :return: str: sql WHERE statement
        """
        sql = ""
        if len(selector) > 0:
            sql += "WHERE\n"
            for key in selector.keys():
                if not sql.endswith('WHERE\n'):
                    sql += ' AND \n'
                sql += self._convert_selector(key, selector[key], i)
                i += 1
        return sql, i

    def _sanitize(self, text):
        """
        Ensure string is ASCII alphanumeric.
        """
        text = re.sub(r"[^A-Za-z0-9]+", '', text)
        assert text
        return text

    def _table_name(self, module, table):
        """
        Get the table name based on the module, and it's table name.

        TODO figure out a way to differentiate multiple instances of the same module between runs

        :param module: object: reference to the module instance
        :param table: str: name of the table
        :return: str: name of the table to be used in sql queries
        """
        return self._sanitize(module.__class__.__name__)+'_'+self._sanitize(table)

    def run_forever(self):
        return self.check_database()

    async def stop(self, signal):
        await self.db_ready.wait()
        await self.pool.close()
