import bs4
import json

from util import DataSource


class ParkingBraunschweig(DataSource):

    source_id = "braunschweig-parken"
    web_url = "http://www.braunschweig.de/plan/index.php#parken"

    def download_snapshot_data(self):
        text = self.get_url("http://www.braunschweig.de/apps/pulp/result/parkhaeuser.geojson")
        geojson = json.loads(text)

        parking_places = []

        for feature in geojson["features"]:
            props = feature["properties"]

            parking_places.append({
                "place_name": props["name"],
                "num_all": props.get("capacity"),
                "num_free": props.get("free"),
                "status": props.get("openingState"),
            })

        return parking_places


