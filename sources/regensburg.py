import bs4
import json

from util import DataSource


class ParkingRegensburg(DataSource):

    source_id = "regensburg-parken"

    def get_data(self):
        soup = self.get_html_soup("https://www.einkaufen-regensburg.de/service/parken-amp-anfahrt.html")

        parking_places = []

        for div in soup.find_all("div", {"class": "belegung"}):
            info = div.parent.find("div", {"class": "a-info"})

            parking_places.append({
                "place_name": info.find("h3").text,
                "num_current": self.int_or_none(div.find("p").text.split()[-1]),
            })

        return parking_places


