import datetime
import math

FRIENDLY_NAMES = {
    'path': 'Cesta',
    'file_size': 'Velikost souboru',
    'width': 'Šířka',
    'height': 'Výška',
    'file_created': 'Soubor vytvořen',
    'file_modified': 'Soubor naposledy změněn',
    'camera': 'Fotoaparát',
    'datetime_original': 'Datum pořízení',
    'datetime_digitized': 'Datum digitalizace',
}

HIDDEN = {
    'uid',
    'uri'
}

UNIT_PREFIX = {
    0: '',
    1: 'k',
    2: 'M',
    3: 'G',
    4: 'T'
}


def clean_metadata(metadata):
    out = {}

    for k, v in metadata.items():
        # hide
        if k in HIDDEN:
            continue

        # stringify
        if isinstance(v, datetime.datetime):
            v = v.strftime('%d. %m. %Y %H:%M:%S').replace(' 0', ' ')

        if k == 'file_size':
            try:
                magnitude = math.log10(v) // 3

                v = f'{round(v / 10 ** (magnitude * 3))} {UNIT_PREFIX[magnitude].upper()}B'
            except KeyError:
                pass

        # special
        if k == 'datetime_digitized' and 'datetime_original' in metadata and metadata['datetime_digitized'] == metadata['datetime_original']:
            continue  # hide digitalized date when it is the same as created

        # rename
        out[FRIENDLY_NAMES.get(k, k)] = v

    return out
