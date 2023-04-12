from collections import OrderedDict

from modules.database.PostgreSQL.main import PostgreDatabase
from utils.interface import KNNCapability
from pgvector.asyncpg import register_vector

OPERATORS = {
    'L2': '<->',
    'euclidian': '<->',
    'inner product': '<#>',
    'cosine': '<=>'
}

INDEX = {
    'L2': 'l2',
    'euclidian': 'l2',
    'inner product': 'ip',
    'cosine': 'cosine'
}


class PostgresKNNDatabase(PostgreDatabase, KNNCapability):
    def __init__(self, bus, loop, config):
        super().__init__(bus, loop, config)

    async def ensure_knn_index(self, module, table, columns):
        await self.db_ready.wait()

        sql_columns = []
        sql_extra = []
        for column in columns:
            sql_colum = column['name'] + ' '
            if column['type'] == 'vector':
                sql_colum += f"vector({column['n_dim']}) "
                if 'optimize' in column:
                    sql_extra.append(
                        f"CREATE INDEX ON {table} USING ivfflat ({column['name']} vector_{column['optimize']}_ops) WITH (lists = 100);")
            elif column['type'] == 'int' or column['type'] == 'integer':
                sql_colum += 'integer '
            else:
                raise NotImplemented(f'Column type {column["type"]} is not implemented')
            if 'unique' in column and column['unique']:
                sql_colum += 'UNIQUE '
            if 'not null' in column and column['not null']:
                sql_colum += 'NOT NULL '
            sql_columns.append(sql_colum)

        async with self.pool.acquire() as conn:
            try:
                await register_vector(conn)
            except ValueError:  # ValueError: unknown type: public.vector
                await conn.execute("CREATE EXTENSION vector")  # enable extension
                await register_vector(conn)

            await conn.execute(f"""
               CREATE TABLE IF NOT EXISTS
               {table}
               ({','.join(sql_columns)});
               """) #  + ';'.join(sql_extra)

    async def knn_add(self, module, table, data):
        await self.db_ready.wait()
        data = OrderedDict(data)
        async with self.pool.acquire() as conn:
            await register_vector(conn)
            await conn.execute(f"""INSERT INTO {table}({', '.join(data.keys())}) VALUES ({', '.join(map(lambda i: f"${i+1}", range(len(data))))})""", *data.values())

    async def knn_query(self, module, table, column, vector, distance='L2', limit=None, offset=0):
        await self.db_ready.wait()

        async with self.pool.acquire() as conn:
            await register_vector(conn)
            return await conn.fetch(f"""
                SELECT *
                FROM {table}
                ORDER BY {column} {OPERATORS[distance]} $1
                LIMIT $2 OFFSET $3;
                """, vector, limit, offset)
