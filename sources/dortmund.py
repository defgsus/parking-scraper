import bs4
import json
import re

from util import DataSource


class ParkingDortmund(DataSource):

    source_id = "digistadt-dortmund-parken"

    def get_data(self):
        text = self.get_url("https://geoweb1.digistadtdo.de/OWSServiceProxy/client/parken.jsp")
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        for dl in soup.find_all("dl"):
            dt = dl.find("dt")
            parking_place_name = dt.text.strip()

            text = dl.find("dd").text.strip()
            match = re.match(r"(\d+) Plätze von (\d+)", text)
            if not match:
                num_all = None
                num_cur = None
            else:
                numbers = match.groups()
                num_cur = int(numbers[0])
                num_all = int(numbers[1])

            parking_places.append({
                "place_name": parking_place_name,
                "num_all": num_all,
                "num_current": num_cur,
            })

        return parking_places
