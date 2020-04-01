import bs4
import json
from copy import deepcopy

from util import DataSource


class ParkingNuernberg(DataSource):

    source_id = "tiefbauamt-nuernberg-parken"
    web_url = "http://www.tiefbauamt.nuernberg.de/site/parken/parkhausbelegung/parkhaus_belegung.html"
    city_name = "Nürnberg"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = dict()

        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                row = [td.text.strip() for td in tr.find_all("td")]
                
                if len(row) == 4:

                    place_name = row[1].splitlines()[-1].strip()

                    parking_places[place_name] = {
                        # flipped num_all/free in v2
                        "v": 2,
                        "place_name": place_name,
                        "num_all": self.int_or_none(row[3]),
                        "num_free": self.int_or_none(row[2]),
                    }

        return list(parking_places.values())

    def transform_snapshot_data(self, data):
        return super().transform_snapshot_data(self._fix_data(data))

    def transform_meta_data(self, data):
        return super().transform_meta_data(self._fix_data(data))

    def _fix_data(self, data):
        data = deepcopy(data)
        for place in data:
            if place.get("v", 0) < 2:
                num_free = place.get("num_current")
                if "num_free" in place:
                    num_free = place["num_free"]

                place["num_all"], place["num_free"] = num_free, place["num_all"]
        return data
