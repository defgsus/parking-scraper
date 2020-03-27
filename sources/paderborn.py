import bs4
import json

from util import DataSource


class ParkingPaderborn(DataSource):

    source_id = "paderborn-parken"
    web_url = "https://www4.paderborn.de/aspparkinfo/default.aspx"

    def get_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        table = soup.find("table")
        for tr in table.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if row:
                parking_places.append({
                    "place_name": row[0],
                    "num_all": self.int_or_none(row[2]),
                    "num_current": self.int_or_none(row[3]),
                })

        return parking_places

