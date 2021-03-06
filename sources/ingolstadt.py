import bs4
import json

from util import DataSource


class ParkingIngolstadt(DataSource):

    source_id = "ingolstadt-parken"
    web_url = "https://www.ingolstadt.de/Wirtschaft/parkIN/Derzeit-freie-Parkpl%C3%A4tze"
    city_name = "Ingolstadt"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []
        div = soup.find("div", {"id": "parkplatzauskunft"})
        table = div.find("table")

        for tr in table.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]

            parking_places.append({
                "place_name": row[1].split("|")[0].strip(),
                "type": row[1].split("|")[1].strip(),
                "num_free": self.int_or_none(row[0]),
            })

        return parking_places


