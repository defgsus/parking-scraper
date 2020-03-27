import bs4
import json

from util import DataSource


class ParkingBremen(DataSource):

    source_id = "vmz-bremen-parken"
    web_url = "https://vmz.bremen.de/parken/parkhaeuser-parkplaetze/"

    def get_snapshot_data(self):
        text = self.get_url("https://vmz.bremen.de/geojson/parking.geojson")
        geojson = json.loads(text)

        parking_places = []

        for feature in geojson["features"]:
            props = feature["properties"]

            parking_places.append({
                "place_id": props["id"],
                "place_name": props["name"],
                "num_all": props.get("capacity"),
                "num_free": props.get("free"),
            })

        return parking_places


