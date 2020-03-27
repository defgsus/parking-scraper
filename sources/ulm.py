import bs4
import json

from util import DataSource


class ParkingUlm(DataSource):

    source_id = "parken-in-ulm"
    web_url = "https://www.parken-in-ulm.de/"

    def get_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for table in soup.find_all("table", {"width": "790"}):
            for tr in table.find_all("tr"):
                if tr.get("id"):
                    row = [td.text.strip() for td in tr.find_all("td")[:-1]]

                    parking_places.append({
                        "place_name": row[0],
                        "num_all": self.int_or_none(row[1]),
                        "num_current": self.int_or_none(row[2]),
                    })

        return parking_places


