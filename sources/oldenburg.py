import bs4
import json
import xmljson
from xml.etree.ElementTree import fromstring

from util import DataSource


class ParkingOldenburg(DataSource):

    source_id = "oldenburg-service-parken"
    web_url = "https://oldenburg-service.de/cros.php"

    def get_snapshot_data(self):
        text = self.get_url(self.web_url)

        data = xmljson.parker.data(fromstring(text))
        return data["Parkhaus"]

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry["Name"]),
                "num_free": entry["Aktuell"],
            })

        return ret_data
