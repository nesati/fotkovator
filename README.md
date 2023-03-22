# Fotkovátor

Fotkovátor je modulární systém na automatické štítkování fotek napsaný v Pythonu. Tento dokument obsahuje informace o instalaci a konfiguraci pro uživatele. Hledáte-li objasnění technických detailů nebo [návod na tvorbu modulu](TECHNICAL_DOCS.md#tvorba-modulu), najdete je v [technické dokumentaci](TECHNICAL_DOCS.md).

## Instalace

Pro jakoukoliv instalaci je nejprve potřeba [Python](https://www.python.org/) 3.10 a závislosti, které lze nainstalovat příkazem: 

```shell
pip install -r requirements.txt
```

Další kroky se odvíjejí od zvolených [modulů](#konfigurace-modulů). Většinou však stačí:

```shell
pip install -r modules/<cesta k modulu>/requirements.txt
```

## Konfigurace

Celý systém se konfiguruje v souboru `fotkovator.yaml` ve formátu [yaml](https://yaml.org/). Je nutné zvolit právě jednu `database` (databázi) a právě jeden `backend` (zdroj obrázků). Všechny ostatní moduly jsou volitelné. Je však doporučené nainstalovat a nakonfigurovat alespoň jeden modul kategorie `frontend` (uživatelské rozhraní).

Nyní se podívejme na příklad konfigurace.

```yaml
backend:  # konfigurace zdroje obrázků
  module: localfs  # volba modulu (Lokální soubory)
  path: './photos'  # konfigurace modulu

database:  # konfigurace databáze
  module: PostgreSQL  # volba modulu
  password: mysecretpassword  # konfigurace modulu

modules:  # volitelné moduly
  - module: tag.metadata
  - module: frontend.basic_webserver # volba modulu (webové uživatelské rozhraní)
    # konfigurace modulu
    port: 8080
  - module: tag.face_recognition
```

Pro detailní návod na konfiguraci jednotlivých modulů zajděte do sekce [Konfigurace modulů](#konfigurace-modulů).

## Použití

Program zapnete příkazem:

```shell
python fotkovator.py
```

Program okamžitě začne zpracovávat fotky z nakonfigurovaného zdroje. Způsob otevření uživatelského rozhraní záleží na nakonfigurovaném rozhraní.

## Konfigurace modulů

### Lokální soubory

Přístup k lokálním souborům je umožněn modulem `localfs`. Periodicky kontroluje změny v souborovém systému.

#### Instalace

```shell
pip install -r modules/backend/localfs/requirements.txt
```

#### Argumenty

`path` - (povinný) Cesta ke složce s obrázky

`max_concurency` - (volitelný, výchozí: 16) Počet fotek které analyzovat současně

#### Příklad konfigurace

```yaml
backend:
  module: localfs
  path: './photos'
```

### PostgreSQL

PostgreSQL klient implementuje modul `PostgreSQL`. Vyžaduje externí [PostgreSQL](https://www.postgresql.org/) server.

#### Instalace

Závislosti klienta lze nainstalovat přes `pip`.

```shell
pip install -r modules/database/PostgreSQL/requirements.txt
```

Je nutné nainstalovat také server. Například přes [docker](https://www.docker.com/):

```shell
docker run --name fotkovatordb -p 5432:5432 -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_USER=fotkovator -d postgres
```

#### Argumenty

`user` - (volitelný, výchozí: fotkovator)

`password` - (volitelný, výchozí: proměnná prostředí `PGPASSWORD`) heslo do databáze

`host` - (volitelný, výchozí: localhost) ip nebo hostname postgres serveru

`port` - (volitelný, výchozí: proměnná prostředí `PGPORT`, nebo `5432` není-li definovaná)

`database` - (volitelný, výchozí: fotkovator) název databáze ve které fotkovátor ukládá data

#### Příklad konfigurace

```yaml
database:
  module: PostgreSQL
  password: mysecretpassword
```

### Rozpoznání obličejů

Modul `face_recognition` poskytuje wrapper na knihovnu [`face-recognition`](https://pypi.org/project/face-recognition/). Modul sám o sobě nepřiřazuje lidem jména, ale snaží se přiřadit stejnému člověku stejný štítek (např.: Osoba 1). Jakmile však tento štítek přejmenujete asociuje si nové jméno s daným obličejem a bude ho přiřazovat i novým fotkám.

Začíná fungovat dobře až když má několik (> ~10) fotek člověka, jinak míchá lidi k sobě.

#### Instalace

```shell
pip install -r modules/modules/tag/face_recognition/requirements.txt
```

Je doporučené používat `dlib` z anacondy.

```shell
conda install -c conda-forge dlib
```

#### Argumenty

`db_path` - (volitelný, výchozí: face.pickle) Cesta k souboru ve kterém si modul ukládá rozpoznané obličeje a další pomocné informace.

#### Příklad konfigurace

```yaml
modules:
  - module: tag.face_recognition
```

### Webové uživatelské rozhraní

Jednoduchý způsob jak přistupovat k Fotkovátoru je přes webový prohlížeč. Webový server implementuje modul `basic_webserver`. Pokud nezměníte konfiguraci stačí po zapnutí fotkovátoru navštívit [localhost:5000](http://localhost:5000).

#### Instalace

```shell
pip install -r modules/modules/frontend/basic_webserver/requirements.txt 
```

#### Argumenty

`port` - (volitelný, výchozí: 5000) port na kterém poslouchat

`host` - (volitelný, výchozí: localhost) interface kde poslouchat

#### Příklad konfigurace

```yaml
modules:
  - module: frontend.basic_webserver
    port: 8080 # příklad změny portu
```

### Zpracování metadat

Modul `metadata` přidává štítky na zákldě informací, které nejsou obsaženy v obraze samotném. Například datum pořízení obrázku, složky ve kterých se nachází, název fotoaparátu atd.

#### Instalace

```shell
pip install -r modules/modules/tag/metadata/requirements.txt
```

#### Příklad konfigurace

```yaml
modules:
  - module: tag.metadata
```

### CLIP

[CLIP](https://openai.com/research/clip) je neuronová síť propojující obrázky a text. Lze ji aplikovat na rozpoznávání víceméně libovolných vizuálních konceptů popsatelných slovy. Implementuje ji modul `CLIP`.
 
#### Argumenty

`model` - (volitelný, výchozí: ViT-B/32) - verze CLIPu, kterou požívat

`classifiers` - (povinný) seznam klasifikátorů
- `threshold` - (volitelný, výchozí: 0) - minimální pravděpodobnost nutná pro přiřazení štítku
- `concepts` - (povinný) vizuální koncepty a k ním asociované štítky viz příklady konfigurace
  - popis vizuálního konceptu je dopručen v angličtině (Obecně platí, čím méně používaný jazyk tím horší výsledky. Ještě horší pak jsou výsledky jazyků nepsaných latinkou.)
  - štítků spojených s daným konceptem může být libovolný počet. Pokud mají dva klasifikátory stejný název štítku, jsou tyto štítky automaticky sloučeny
- `prefix` - text co se vloží před každý koncept (např.: "a photo of ")
#### Instalace


```shell
pip install -r modules/modules/tag/CLIP/requirements.txt
```

Je doporučené používat `pytorch` a `torchvision` pomocí [anacondy](https://www.anaconda.com/products/distribution) viz [konfigurátor příkazu](https://pytorch.org/get-started/locally/).

Například pro NVIDIA CUDA:

```shell
conda install pytorch torchvision pytorch-cuda=11.6 -c pytorch -c nvidia
```

#### Příklad konfigurace

Jednoduchý klasifikátor umístění:

```yaml
modules:
  - module: tag.CLIP
    classifiers:
      - threshold: .8
        concepts:
          indoors: uvnitř
          outdoors: venku
          "in a vehicle": ve vozidle
```

Pokročilý klasifikátor umístění inspirovaný datasetem [Places2](http://places2.csail.mit.edu/index.html) najdete v [samostaném souboru](modules/modules/tag/CLIP/places.yaml).

Jednoduchý klasifikátor objektu fotky:

```yaml
modules:
  - module: tag.CLIP
    classifiers:
      - prefix: "a photo of "
        concepts:
          people: lidé
          a landscape: krajina
          architecture: architektura
          animals: zvířata
          food: jídlo
          nature: příroda
          travel: cestování
          a sport: sport
          an event: událost
          an object: předměty
          an art piece: umění
          a vehicle: vozidla
          a paper: dokument
          space: vesmír
          electronics: elektronika
```

Detektor fotek na smazání:

```yaml
modules:
  - module: tag.CLIP
    classifiers:
      - threshold: .5
        concepts:
          "bad photo": "nepovedená"
          "normal photo": []
          "good photo": []
          "excellent photo": []  # zde si můžete přidat vlastní štítek
```

Detektor ne-fotek:

```yaml
modules:
  - module: tag.CLIP
    classifiers:
      - concepts:
        "photo, photograph": []
        "diagram, chart, graph, infographic, figure": "diagram"
        "document, photo of a document, note, paper": "dokument"
        "meme, joke, text, template, deep fried": "meme"
        "drawing, scribble": "obrázek"
```

### Hlášení událostí

Modul `event_logger` slouží hlavně pro debugování. Vypisuje události a jejich argumenty do konzole.

#### Instalace

Není potřeba nic.

#### Příklad konfigurace

```yaml
modules:
  - module: misc.event_logger
```

## Možnosti rozšíření

Způsoby, kterými lze vylepšit tento projekt, ale nejsou jeho součástí.

### Moduly

Možnosti rozšíření kompatibilní se současným modulárním systémem.

- Android aplikce (backend + frontend)
- Modul co umožňuje spouštení ostatních modulů na jiném počítači (cloud GPU)

### Další

- Moduly nahrazující fotky
  - Kolorizace černobílých fotek
  - Koprese
- Automatické kombinování podobných fotek
  - live photos
  - HDR
- [CLIP](https://openai.com/blog/clip/) vyhledávání viz [clip-retrieval](https://github.com/rom1504/clip-retrieval)

## Credits

[py-event-bus](https://github.com/joeltok/py-event-bus)