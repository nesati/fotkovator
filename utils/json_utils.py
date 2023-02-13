"""
Extends built-in json encoder and decoder to support more objects (eg.: datetime).
"""
import json
import datetime


class Encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()

        return super().default(obj)


class Decoder(json.JSONDecoder):
    def object_hook(self, source):
        for k, v in source.items():
            if isinstance(v, str):
                try:
                    source[k] = datetime.datetime.fromisoformat(v)
                except ValueError:
                    pass
        return source


def encoder(value):
    return json.dumps(value, cls=Encoder)


def decoder(value):
    return json.loads(value, cls=Decoder)
