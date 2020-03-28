import bs4
import json
import xmljson
from xml.etree.ElementTree import fromstring

from util import DataSource


class ParkingOldenburg(DataSource):

    source_id = "oldenburg-service-parken"
    web_url = "https://oldenburg-service.de/cros.php"
    city_name = "Oldenburg"

    def download_snapshot_data(self):
        text = self.get_url(self.web_url)

        data = xmljson.parker.data(fromstring(text))
        return data["Parkhaus"]

    def transform_snapshot_data(self, data):
        status_mapping = {"Geschlossen": "closed", "Offen": "open"}
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry["Name"]),
                "num_free": entry["Aktuell"],
                "status": status_mapping.get(entry["Status"]),
            })

        return ret_data

    def transform_meta_data(self, data):
        ret_data = super().transform_meta_data(None)

        for entry in data:
            place_id = self.place_name_to_id(entry["Name"])
            ret_data["places"][place_id] = {
                "place_id": place_id,
                "place_name": entry["Name"],
                "num_all": entry["Gesamt"],
            }

        return ret_data
