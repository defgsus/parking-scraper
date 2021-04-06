import bs4
import json

from util import DataSource


class ParkingKonstanz(DataSource):

    source_id = "konstanz-parken"
    web_url = "https://www.konstanz.de/leben+in+konstanz/parkleitsystem"
    city_name = "Konstanz"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for tr in soup.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if len(row) == 2 and row[0] != "Parkmöglichkeit":
                print(row)
                parking_places.append({
                    "place_name": row[0],
                    "num_free": self.int_or_none(row[1]),
                })

        return parking_places