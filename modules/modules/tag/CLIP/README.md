# CLIP

[CLIP](https://openai.com/research/clip) je neuronová síť propojující obrázky a text. Lze ji aplikovat na rozpoznávání víceméně libovolných vizuálních konceptů popsatelných slovy. Implementuje ji modul `tag.CLIP`.

Jde o asi nejmocnější část Fotkovátoru. Je velmi obecný a lze ho specializovat na rozlišování téměř čehokoliv. Jeho obecnost má však svoje limity. Nerozumí příliš dobře věcem, které jsou na internetu málo anotované. Pokoušel jsem se tento modul využít k detekci fotek, které jsou otočené, ale bez úspěchu.

U méně používaných jazyků se jeho porozumění výrazně zhoršuje a s jazyky, které nejsou psané latinkou, je naprosto nepoužitelný. Proto konfigurace nabízí možnost zadat popis obrázku v jiném jazyce (doporučuji anglicky) než samotné přiřazené štítky.

Tvorbu klasifikátoru si můžete představit jako seznam možností odpovědi na otázku „Co nejlépe popisuje daný obrázek?“. `threshold` pak určuje, jak moc si CLIP musí být jistý odpovědí, aby se štítky přiřadily.

K tvorbě klasifikátoru je ještě nutné podotknout, že model je náchylný na formulaci daného popisu. Kolem tohoto problému již vzniká komunita tzv. prompt inženýrů, která se snaží najít metody formulování s nejlepšími výsledky.

Pokud požíváte více klafisikátorů není nutné mít víc instancí CLIP modulu.

## Argumenty

`model` - (volitelný, výchozí hodnota: `ViT-B/32`) verze CLIPu, kterou požívat

`classifiers` - (povinný) seznam klasifikátorů

`threshold` - (volitelný, výchozí hodnota: `0`) minimální pravděpodobnost nutná pro přiřazení štítku

`concepts` - (povinný) vizuální koncepty a k ním asociované štítky (viz příklady konfigurace)

Štítků spojených s daným konceptem může být libovolný počet. Pokud mají dva klasifikátory stejný název štítku, jsou tyto štítky automaticky sloučeny.

`prefix` - text co se vloží před každý koncept (např.: "a photo of ")

## Instalace


```shell
pip install -r modules/modules/tag/CLIP/requirements.txt
```

Je doporučené používat `pytorch` a `torchvision` pomocí [anacondy](https://www.anaconda.com/products/distribution) viz [konfigurátor příkazu](https://pytorch.org/get-started/locally/).

Například pro NVIDIA CUDA:

```shell
conda install pytorch torchvision pytorch-cuda=11.6 -c pytorch -c nvidia
```

## Příklad konfigurace

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

Pokročilý klasifikátor vytvořený na základě datasetu [Places2](http://places2.csail.mit.edu/index.html) najdete v [samostaném souboru](modules/modules/tag/CLIP/places.yaml).

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