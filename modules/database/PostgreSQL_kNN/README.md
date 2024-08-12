# Vektorový PostgreSQL

Modul `database.PostgreSQL_kNN` implementuje klient pro [PostgreSQL](https://www.postgresql.org/)) s pluginem 
[pgvector](https://github.com/pgvector/pgvector), který umožňuje vektorové operace. Vyžaduje externí server.

## Instalace

Závislosti klienta lze nainstalovat přes `pip`.

```shell
pip install -r modules/database/PostgreSQL_kNN/requirements.txt
```

Je nutné nainstalovat také server. Například přes [docker](https://www.docker.com/):

```shell
docker run --name fotkovatordb \
           -p 5432:5432 \
           -e POSTGRES_PASSWORD=mysecretpassword \
           -e POSTGRES_USER=fotkovator \
           -d pgvector/pgvector:pg16
```

## Argumenty

Stejné jako [Postges](../PostgreSQL/README.md#argumenty)

## Příklad konfigurace

Stejné jako [Postges](../PostgreSQL/README.md#příklad-konfigurace)