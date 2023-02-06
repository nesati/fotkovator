import datetime
import re
from pathlib import Path

from anyascii import anyascii

REGEX_strptime = [
    (r"\d{2}\. \d{2}(?=\.|$)", "%d. %m"),
    (r"(?<!0)[123]?\d\. [1]?\d(?=\.|$)", "%-d. %-m"),
    (r"\d{2}\-\d{4}", "%m-%Y"),
    (r"(?<!0)[123]?\d\-\d{4}", "%-m-%Y"),
    (r"(^|(?<= |_))\d{2}\_\d{4}", "%m_%Y"),
    (r"(^|(?<= |_))[123]?\d\_\d{4}", "%-m_%Y"),
    (r"(^|(?<= ))\d{2}\ \d{4}", "%m %Y"),
    (r"(^|(?<= ))[123]?\d\ \d{4}", "%-m %Y"),
    (r"(^|(?<= ))[12]\d{3}((?= )|$)", "%Y"),
]

IGNORED = [
    "Netříděné",
    "foto",
    r"[^\\/]*NIKON",
    r"[^\\/]*ANDRO",
    "z mobilu",
    "různé",
    "z kamery",
]
ignore_re = re.compile('|'.join(IGNORED + list(map(anyascii, IGNORED))), flags=re.IGNORECASE)


def filename2dt(filename):
    """
    Pareses datetime from filename using regex. Example formats:
      PXL_YYYYMMDD_HHMMSS*.jpg  # Google Pixel
      PXL_YYYYMMDD_HHMMSS*.*.jpg  # special modes (MP, NIGHT, PORTRAIT...)
      IMG_YYYYMMDD_HHMMSS*.jpg  # xiaomi
      YYYYMMDD_HHMMSS_*.jpg  # samsung
      YYYYMMDD_HHMMSS.jpg

    TODO:
      IMG_YYYYMMDD-WA*.jpg

    :param filename: str: file name
    :return: datetime or None
    """
    if match := re.match(r'^.*(\d{8}_\d{6}).*$', filename):
        return datetime.datetime.strptime(match.group(1), '%Y%m%d_%H%M%S')


def analyze(path):
    path = re.sub(ignore_re, ' ', path)  # remove stopwords
    path = list(map(lambda s: s.strip(), Path(path).parts))  # split path

    tags = set()
    dt = None
    for idx, dir in enumerate(path):
        if dir == '':
            continue
        filename = idx == len(path) - 1
        for search, format in REGEX_strptime:
            if match := re.search(search, dir):
                # parse tag
                tag = dir.replace(match.group(), '')
                if filename:
                    tag = tag.rsplit('.', 1)[0]  # remove file extension
                tag = tag.strip()
                if tag:
                    tags.add(tag)

                # parse datetime
                # zero padded and non-zero padded strings are parsed
                format = format.replace('%-m', '%m').replace('%-d', '%d')

                tmp_dt = datetime.datetime.strptime(match.group(), format)

                # combine datetime (eg.: 2020/Výlet 1. 4./foto.jpg)
                if dt is None:
                    dt = tmp_dt
                else:
                    repl = {}
                    for identifier, attr in [('%m', 'month'), ('%d', 'day'), ('%Y', 'year')]:
                        if identifier in format:  # the folder name contains this information
                            repl[attr] = tmp_dt.__getattribute__(attr)
                    dt = dt.replace(**repl)  # update with information from closer folder
            if filename:
                dt = filename2dt(dir) or dt

    return tags, dt


if __name__ == '__main__':
    # tests
    ROOT = "C:/Foto/"

    FOLDERS = [
        "2009/rijen09",
        "2009/KOS_07_2009",
        "2009/Karlovy Vary 07 2009",
        "2009/stockholm0509",
        "2009/zari2009",
        "2012/leden-červen2012",
        "2012/zoo-06-2012",
        "Netřídené/od_tatinka/Nový FZ50/Opočno 2009",
        "2018/Výlet do lesa Chalupa 12-2018",
        "2018/Chalupa",
        "2018/12. 4. Zoo Praha",
        "2019/Sníh 2018-19",
        "2019/Děti na umnělém kluzišti nám. 14. října 01-2019",
    ]

    FILENAMES = [
        "DSC_1580.JPG",
        "20190323_173831_014.jpg",
        "Corona foto na Kralově mostě 05-2020.jpg",
    ]

    for folder in FOLDERS:
        for filename in FILENAMES:
            path = ROOT + folder + '/' + filename
            print(path, analyze(path), sep='\n')
