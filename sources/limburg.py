import bs4
import json
import re

from util import DataSource


class ParkingLimburg(DataSource):

    source_id = "limburg-parken"
    web_url = "https://p127393.mittwaldserver.info/LM/_pls/pls.php"
    city_name = "Limburg"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        table = soup.find("table")
        for tr in table.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if len(row) == 6 and self.int_or_none(row[1]) is not None:

                parking_places.append({
                    "place_name": row[0],
                    "num_all": self.int_or_none(row[1]),
                    "num_free": self.int_or_none(row[3]),
                    "status": {"Offen": "open", "Geschlossen": "closed"}.get(row[5]) or row[5],
                })

        return parking_places
