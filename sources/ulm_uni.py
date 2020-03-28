import bs4
import json

from util import DataSource


class ParkingUlmUni(DataSource):

    source_id = "uni-ulm-parken"
    web_url = "https://www.uni-ulm.de/einrichtungen/kiz/weiteres/campus-navigation/anreise/parkplaetze/"
    city_name = "Ulm"

    def download_snapshot_data(self):
        text = self.get_url("http://tsu-app.rrooaarr.biz/front/soap.php?counterid=10021")

        parking_places = [{
            "num_free": self.int_or_none(text)
        }]

        return parking_places

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id("ulm-uni"),
                "num_free": entry.get("num_current") or entry.get("num_free"),
            })

        return ret_data