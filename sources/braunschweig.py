import bs4
import json

from util import DataSource


class ParkingBraunschweig(DataSource):

    source_id = "braunschweig-parken"
    web_url = "http://www.braunschweig.de/plan/index.php#parken"
    city_name = "Braunschweig"
    
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

    def download_meta_data(self):
        text = self.get_url("http://www.braunschweig.de/apps/pulp/result/parkhaeuser.geojson")
        geojson = json.loads(text)
        return geojson

    def transform_meta_data(self, geojson):
        ret_data = super().transform_meta_data(None)

        for feature in geojson["features"]:
            props = feature["properties"]

            place_id = self.place_name_to_id(props["name"])
            ret_data["places"][place_id] = {
                "place_id": place_id,
                "place_name": props["name"],
                "num_all": props.get("capacity"),
                "coordinates": feature["geometry"]["coordinates"][::-1],
            }

        return ret_data
