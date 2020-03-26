import json


class JsonEncoder(json.JSONEncoder):

    def default(self, o):
        try:
            return super().default(o)
        except TypeError:
            return str(o)


def to_json(data, indent=None):
    return json.dumps(data, cls=JsonEncoder, indent=indent)