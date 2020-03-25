import bs4
import json

from util import DataSource


class ParkingBadenBaden(DataSource):

    source_id = "baden-baden-parken"
    web_url = "https://www.stadtwerke-baden-baden.de/"

    def get_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        ul = soup.find("ul", {"class": "listParkleitDisplay"})

        for li in ul.find_all("li"):
            text = li.find("h3").text
            row = text.split(":")

            parking_places.append({
                "place_name": row[0],
                "num_current": self.int_or_none(row[1]),
            })

        return parking_places
