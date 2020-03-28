import bs4
import json

from util import DataSource


class ParkingBielefeld(DataSource):

    source_id = "sw-bielefeld-parken"
    web_url = "https://www.bielefeld.de/de/sv/verkehr/parken/park/"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for table in soup.find_all("table"):
            for tr in table.find_all("tr", {"class": "bghblau"}):
                row = [td for td in tr.find_all("td")]
                next_row = [td for td in tr.next_sibling.find_all("td")]
                
                place_name = list(row[1].find("b").children)[0].strip()
                if "(" in place_name:
                    place_name = place_name[:place_name.index("(")]

                parking_places.append({
                    "place_name": place_name,
                    "num_free": self.int_or_none(next_row[1].text.split()[0]),
                })

        return parking_places
