import re
import json

from util import DataSource


class ParkingHeilbronn(DataSource):

    source_id = "heilbronn-parken"
    web_url = "https://www.heilbronn.de/umwelt-mobilitaet/mobilitaet/parken/parkhaeuser.html"

    def get_snapshot_data(self):
        soup = self.get_html_soup("https://www.heilbronn.de/allgemeine-inhalte/ajax-parkhausbelegung.html?type=1496993343")

        parking_places = []

        for a in soup.find_all("a"):
            parking_places.append({
                "place_name": a.text,
                "num_free": self.int_or_none(a.parent.parent.parent.parent.text.split()[-1]),
            })

        return parking_places


