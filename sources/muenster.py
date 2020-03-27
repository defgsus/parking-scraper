import bs4
import json

from util import DataSource


class ParkingMuenster(DataSource):

    source_id = "stadt-muenster-parken"
    web_url = "https://www.stadt-muenster.de/index.php?id=10910"

    def get_snapshot_data(self):
        text = self.get_url(self.web_url)
        return json.loads(text)

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data["features"]:
            props = entry["properties"]
            ret_data.append({
                "place_id": self.place_name_to_id(props["NAME"]),
                "num_free": props["parkingFree"],
            })

        return ret_data