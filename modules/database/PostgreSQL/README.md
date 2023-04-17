# PostgreSQL

PostgreSQL klient implementuje modul `PostgreSQL`. Vyžaduje externí [PostgreSQL](https://www.postgresql.org/) server.

## Instalace

Závislosti klienta lze nainstalovat přes `pip`.

```shell
pip install -r modules/database/PostgreSQL/requirements.txt
```

Je nutné nainstalovat také server. Například přes [docker](https://www.docker.com/):

```shell
docker run --name fotkovatordb \
           -p 5432:5432 \
           -e POSTGRES_PASSWORD=mysecretpassword \
           -e POSTGRES_USER=fotkovator \
           -d postgres
```

## Argumenty

`user` - (volitelný, výchozí hodnota: fotkovator)

`password` - (volitelný, výchozí hodnota: proměnná prostředí `PGPASSWORD`) heslo do databáze

`host` - (volitelný, výchozí hodnota: localhost) IP nebo hostname PostgreSQL serveru

`port` - (volitelný, výchozí hodnota: proměnná prostředí `PGPORT`, nebo `5432` není-li definovaná)

`database` - (volitelný, výchozí hodnota: fotkovator) název databáze ve které fotkovátor ukládá data

## Příklad konfigurace

```yaml
database:
  module: PostgreSQL
  password: mysecretpassword
```