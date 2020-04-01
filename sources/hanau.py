import re
import bs4
import json
from copy import deepcopy

from util import DataSource


class ParkingHanau(DataSource):

    source_id = "hanau-neu-erleben-parken"
    web_url = "http://www.hanau-neu-erleben.de/reise/parken/072752/index.html"
    city_name = "Hanau"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "well"}):
            span = div.find("span", {"class": "badge"})
            prog = div.find("div", {"class": "progress-bar-success"})
            if span and prog:
                num_all = self.int_or_none(span.text.split()[0])
                num_free = self.int_or_none(prog.text.split()[-1])
                place_name = div.find("b").text.strip()
                place_name = re.sub(r"\(.*\)", "", place_name)
                place_id = place_name[place_name.index("ID:")+3:]
                place_name = place_name[:place_name.index("ID:")].strip()

                parking_places.append({
                    # mixed-up num_free / occupied before v2
                    "v": 2,
                    "place_name": place_name,
                    "place_id": place_id,
                    "num_all": num_all,
                    "num_free": num_free,
                })

        return parking_places

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

                place["num_free"] = place["num_all"] - num_free
        return data

