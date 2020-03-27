import json
import warnings

from util import DataSource

try:
    from .bahn_credentials import BAHN_API_TOKEN
except ImportError:
    warnings.warn("Deutsche Bahn Parking API disabled! You need to define your BAHN_API_TOKEN in bahn_credentials.py")
    BAHN_API_TOKEN = None


if BAHN_API_TOKEN:
    class ParkingBahn(DataSource):

        source_id = "bahn-api-parken"
        web_url = "https://api.deutschebahn.com/bahnpark/v1/spaces/occupancies"

        def get_snapshot_data(self):

            self.session.headers.update({
                "Accept": "application/json;charset=utf-8",
                "Authorization": f"Bearer {BAHN_API_TOKEN}"
            })
            markup = self.get_url(self.web_url)
            data = json.loads(markup)
            # print(json.dumps(data, indent=2))

            return data["allocations"]

            parking_places = []
            for entry in data["allocations"]:
                num_cur = None
                text = entry["allocation"].get("text")
                if text:
                    num_cur = self.int_or_none(text.split)
                parking_places.append({
                    "place_name": entry["space"]["name"],
                    "num_all": entry["allocation"].get("capacity"),
                    "num_current": num_cur,

                })
            return parking_places

        def transform_snapshot_data(self, data):
            ret_data = []

            text_mapping = {
                "bis 10": 10,
                "> 10": 20,
                "> 30": 40,
                "> 50": 60,
            }

            try:
                data["allocations"]
            except (AttributeError, KeyError, TypeError) as e:
                return ret_data

            for entry in data["allocations"]:
                num_cur = None
                text = entry["allocation"].get("text")
                if text:
                    num_cur = text_mapping.get(text)
                    if num_cur is None:
                        num_cur = self.int_or_none(text.split()[-1])

                ret_data.append({
                    "place_id": self.place_name_to_id(entry["space"]["name"]),
                    "num_all": entry["allocation"].get("capacity"),
                    "num_free": num_cur,
                })

            return ret_data
