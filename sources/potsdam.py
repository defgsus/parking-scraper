import bs4
import json

from util import DataSource


class ParkingPotsdam(DataSource):

    source_id = "mobil-potsdam-parken"

    def get_data(self):
        text = self.get_url("https://www.mobil-potsdam.de/de/parken/parken-in-potsdam/?no_cache=1")
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        for div in soup.find_all("div", {"class": "parken_sektion"}):
            table = div.find("table")
            for tr in table.find_all("tr"):
                row = [td.text.strip() for td in tr.find_all("td")]

                if row[0] != "Füllstand":

                    parking_places.append({
                        "place_name": row[1][:len(row[1]) // 2],
                        "num_current": self.int_or_none(row[2]),
                        "percent_current": self.int_or_none(row[0].rstrip("%")),
                    })

        return parking_places

