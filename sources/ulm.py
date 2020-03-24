import bs4
import json

from util import DataSource


class ParkingUlm(DataSource):

    source_id = "parken-in-ulm"

    def get_data(self):
        text = self.get_url("https://www.parken-in-ulm.de/")
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        for table in soup.find_all("table", {"width": "790"}):
            for tr in table.find_all("tr"):
                if tr.get("id"):
                    row = [td.text.strip() for td in tr.find_all("td")[:-1]]

                    parking_places.append({
                        "place_name": row[0],
                        "num_all": int(row[1]) if row[1] else None,
                        "num_current": int(row[2]) if row[2] else None,
                    })

        return parking_places


