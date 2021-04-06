import re
import json

from util import DataSource


class ParkingBielefeld(DataSource):

    source_id = "sw-bielefeld-parken"
    web_url = "https://www.bielefeld.de/de/sv/verkehr/parken/park/"
    city_name = "Bielefeld"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        num_all_re = re.compile(".* (\d+) Plätze.*")
        num_free_re = re.compile(".* (\d+) frei.*")

        parking_places = []

        for table in soup.find_all("table"):
            for tr in table.find_all("tr"):
                text = tr.text.strip().replace("\n", " ")
                if text.startswith("Kapazität"):
                    num_all = num_all_re.match(text)
                    if num_all:
                        num_all = self.int_or_none(num_all.groups()[0])

                    num_free = num_free_re.match(text)
                    if num_free:
                        num_free = self.int_or_none(num_free.groups()[0])

                    # now climb out of table to get place name
                    h3 = table.parent.find("h3")
                    place_name = h3.text.strip()

                    parking_places.append({
                        "place_name": place_name,
                        "num_all": num_all,
                        "num_free": num_free,
                    })

        return parking_places
