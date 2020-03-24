import bs4
import json

from util import DataSource


class ParkingWiesbaden(DataSource):

    source_id = "wiesbaden-parken"

    def get_data(self):
        text = self.get_url("https://wi.memo-rheinmain.de/wiesbaden/parkliste.phtml?order=carparks")
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        table = soup.find("table")
        for tr in table.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if row and row[0] == "":
                numbers = row[2].split("/")
                parking_places.append({
                    "place_name": row[1],
                    "num_all": self.int_or_none(numbers[1]),
                    "num_current": self.int_or_none(numbers[0]),
                })

        return parking_places


