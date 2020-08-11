import bs4
import json

from util import DataSource


class ParkingJena(DataSource):

    source_id = "mobilitaet-jena"
    web_url = "https://mobilitaet.jena.de/de/parken"
    city_name = "Jena"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        div = soup.find("div", {"class": "view-parking-areas"})
        if not div:
            div = soup.find("div", {"class": "view-list-parkplaetze"})
        for tr in div.find("table").find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]

            if row:
                parking_places.append({
                    "place_name": row[0],
                    "num_free": self.int_or_none(row[1]),
                    "num_all": self.int_or_none(row[2]),
                })
        print("HALLO", parking_places)
        return parking_places

