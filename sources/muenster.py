import bs4
import json

from util import DataSource


class ParkingMuenster(DataSource):

    source_id = "stadt-muenster-parken"
    web_url = "https://www.stadt-muenster.de/index.php?id=10910"
    city_name = "Münster"

    def download_snapshot_data(self):
        text = self.get_url(self.web_url)
        return json.loads(text)

    def transform_snapshot_data(self, data):
        status_mapping = {"geschlossen": "closed", "frei": "open"}
        ret_data = []
        for entry in data["features"]:
            props = entry["properties"]
            ret_data.append({
                "place_id": self.place_name_to_id(props["NAME"]),
                "num_free": props["parkingFree"],
                "status": status_mapping.get(props["status"]),
            })

        return ret_data

    def transform_meta_data(self, data):
        ret_data = super().transform_meta_data(None)

        for entry in data["features"]:
            props = entry["properties"]

            place_id = self.place_name_to_id(props["NAME"])
            ret_data["places"][place_id] = {
                "place_id": place_id,
                "place_name": props["NAME"],
                "place_url": props["URL"],
                "num_all": props["parkingTotal"],
            }

        return ret_data
