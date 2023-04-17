# Rozpoznání obličejů

Modul `face_recognition` poskytuje wrapper na knihovnu [`face-recognition`](https://pypi.org/project/face-recognition/). Modul sám o sobě nepřiřazuje lidem jména, ale snaží se přiřadit stejnému člověku stejný štítek (např.: Osoba 1). Jakmile však tento štítek přejmenujete asociuje si nové jméno s daným obličejem a bude ho přiřazovat i novým fotkám.

Začíná fungovat dobře až když má několik (> ~10) fotek člověka, jinak má tendenci obličeje seskupovat k sobě docela náhodným způsobem. Také do někdy samostatných skupin dává chybně označené obličeje.

## Instalace

```shell
pip install -r modules/modules/tag/face_recognition/requirements.txt
```

Je doporučené používat `dlib` z anacondy.

```shell
conda install -c conda-forge dlib
```

## Argumenty

`db_path` - (volitelný, výchozí hodnota: face.pickle) Cesta k souboru ve kterém si modul ukládá rozpoznané obličeje a další pomocné informace.

## Příklad konfigurace

```yaml
modules:
  - module: tag.face_recognition
```