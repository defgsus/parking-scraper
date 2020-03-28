import re
import json

from util import DataSource


class ParkingBielefeld(DataSource):

    source_id = "sw-bielefeld-parken"
    web_url = "https://www.bielefeld.de/de/sv/verkehr/parken/park/"
    city_name = "Bielefeld"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []
        
        num_all_re = re.compile("(\d+) Plätze.*")
        num_free_re = re.compile(".* (\d+) frei")

        for table in soup.find_all("table"):
            for tr in table.find_all("tr", {"class": "bghblau"}):
                row = [td for td in tr.find_all("td")]
                next_row = [td.text for td in tr.next_sibling.find_all("td")]

                place_name = list(row[1].find("b").children)[0].strip()
                if "(" in place_name:
                    place_name = place_name[:place_name.index("(")]

                places_str = next_row[1]
                num_all = num_all_re.match(places_str)
                if num_all:
                    num_all = self.int_or_none(num_all.groups()[0])

                num_free = num_free_re.match(places_str)
                if num_free:
                    num_free = self.int_or_none(num_free.groups()[0])

                parking_places.append({
                    "place_name": place_name,
                    "num_all": num_all,
                    "num_free": num_free,
                })

        return parking_places
