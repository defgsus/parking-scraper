import bs4
import json

from util import DataSource


class ParkingNuernberg(DataSource):

    source_id = "tiefbauamt-nuernberg-parken"

    def get_data(self):
        text = self.get_url("http://www.tiefbauamt.nuernberg.de/site/parken/parkhausbelegung/parkhaus_belegung.html")
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = dict()

        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                row = [td.text.strip() for td in tr.find_all("td")]
                if len(row) > 3 and row[1].startswith("Parkhaus\n"):

                    print(row)
                    place_name = row[1].splitlines()[-1].strip()

                    parking_places[place_name] = {
                        "place_name": place_name,
                        "num_all": self.int_or_none(row[2]),
                        "num_current": self.int_or_none(row[3]),
                    }

        return list(parking_places.values())


