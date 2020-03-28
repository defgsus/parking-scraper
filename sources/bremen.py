import bs4
import json

from util import DataSource


class ParkingBremen(DataSource):

    source_id = "vmz-bremen-parken"
    web_url = "https://vmz.bremen.de/parken/parkhaeuser-parkplaetze/"
    city_name = "Bremen"

    def download_meta_data(self):
        text = self.get_url("https://vmz.bremen.de/geojson/parking.geojson")
        geojson = json.loads(text)
        return geojson

    def download_snapshot_data(self):
        geojson = self.download_meta_data()

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

    def transform_meta_data(self, data):
        places = []
        for feature in data["features"]:
            props = feature["properties"]

            geometry = feature["geometry"]
            if "coordinates" in geometry:
                coordinates = geometry["coordinates"][::-1]
            else:
                coordinates = geometry["geometries"][0]["coordinates"]

            places.append({
                "place_id": props["id"],
                "place_name": props["name"],
                "place_url": props["detailsUrl"],
                "num_all": props.get("capacity"),
                "coordinates": coordinates,
            })

        return super().transform_meta_data(places)
