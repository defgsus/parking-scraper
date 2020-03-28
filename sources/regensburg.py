import bs4
import json

from util import DataSource


class ParkingRegensburg(DataSource):

    source_id = "regensburg-parken"
    web_url = "https://www.einkaufen-regensburg.de/service/parken-amp-anfahrt.html"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "belegung"}):
            info = div.parent.find("div", {"class": "a-info"})

            parking_places.append({
                "place_name": info.find("h3").text,
                "num_free": self.int_or_none(div.find("p").text.split()[-1]),
            })

        return parking_places


