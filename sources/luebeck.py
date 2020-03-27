import bs4
import json
import ast

from util import DataSource


class ParkingLuebeck(DataSource):

    source_id = "parken-luebeck"
    web_url = "https://www.parken-luebeck.de/parkmoeglichkeiten.html"

    def get_snapshot_data(self):
        text = self.get_url(self.web_url)

        search_str = "var parkingData = JSON.parse('"
        idx = text.index(search_str)
        if idx <= 0:
            raise AssertionError("json data not found")

        text = text[idx+len(search_str):]
        text = text[:text.index("');")]
        text = ast.literal_eval('"'+text+'"')
        full_data = json.loads(text)

        parking_places = []
        for space in full_data.values():
            parking_places.append({
                "place_name": space["title"],
                "id": space["id"],
                "num_all": self.int_or_none(space["totalSpace"]),
                "num_current": self.int_or_none(space["free"]),
                "status": space["state"],
            })

        return parking_places

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry["place_name"] + "-" + entry["id"]),
                "num_free": entry["num_current"]
            })

        return ret_data
