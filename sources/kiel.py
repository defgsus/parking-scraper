import re
import bs4
import json

from util import DataSource


class ParkingKiel(DataSource):

    source_id = "kiel-parken"
    web_url = "https://www.kiel.de/de/umwelt_verkehr/auto/parken_innenstadt.php"

    def get_snapshot_data(self):
        markup = self.get_url(self.web_url)

        array_re = re.compile(r"<fieldset class=\"parkover\">(.*)</fieldset>")

        parking_places = []

        for match in array_re.findall(markup):
            soup = bs4.BeautifulSoup(match, parser="html.parser", features="lxml")

            num_all = None
            num_free = None

            elem = soup.find("h6")
            if elem and elem.text.strip().startswith("Parkp"):
                num_all = str(elem.next_sibling)

            elem = soup.find("strong")
            if elem:
                num_free = elem.text

            parking_places.append({
                "place_name": soup.find("legend").text.strip(),
                "num_all": self.int_or_none(num_all),
                "num_free": self.int_or_none(num_free),
            })

        return parking_places


