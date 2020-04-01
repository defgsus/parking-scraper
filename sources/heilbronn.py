import re
import json

from util import DataSource


class ParkingHeilbronn(DataSource):

    source_id = "heilbronn-parken"
    web_url = "https://www.heilbronn.de/umwelt-mobilitaet/mobilitaet/parken/parkhaeuser.html"
    city_name = "Heilbronn"

    def download_snapshot_data(self):
        soup = self.get_html_soup("https://www.heilbronn.de/allgemeine-inhalte/ajax-parkhausbelegung.html?type=1496993343")

        parking_places = []

        for div in soup.find_all("div", {"class": "carparkLocation"}):
            if div.find("a"):
                place_name = div.find("a").text.strip()
            else:
                place_name = div.text.strip()

            num_free = div.parent.parent.next_sibling.text.split()[-1]

            parking_places.append({
                "place_name": place_name,
                "num_free": self.int_or_none(num_free),
            })

        return parking_places

    def transform_snapshot_data(self, data):
        return super().transform_snapshot_data(self._fix_data(data))

    def transform_meta_data(self, data):
        return super().transform_meta_data(self._fix_data(data))

    def _fix_data(self, data):
        """Filter out a typo3 parking house !??"""
        new_data = []
        for place in data:
            if "typo3" in place["place_name"]:
                continue
            new_data.append(place)
        return new_data
