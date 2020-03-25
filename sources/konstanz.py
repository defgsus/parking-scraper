import bs4
import json

from util import DataSource


class ParkingKonstanz(DataSource):

    source_id = "konstanz-parken"
    web_url = "https://www.konstanz.de/leben+in+konstanz/parkleitsystem"

    def get_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for tr in soup.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if len(row) == 3 and row[0] == "":

                parking_places.append({
                    "place_name": row[1],
                    "num_current": self.int_or_none(row[2]),
                })

        return parking_places