import bs4
import json
import ast

from util import DataSource


class ParkingLuebeck(DataSource):

    source_id = "parken-luebeck"

    def get_data(self):
        text = self.get_url("https://www.parken-luebeck.de/parkmoeglichkeiten.html")

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
