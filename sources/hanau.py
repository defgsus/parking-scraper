import re
import bs4
import json

from util import DataSource


class ParkingHanau(DataSource):

    source_id = "hanau-neu-erleben-parken"
    web_url = "http://www.hanau-neu-erleben.de/reise/parken/072752/index.html"

    def get_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "well"}):
            span = div.find("span", {"class": "badge"})
            prog = div.find("div", {"class": "progress-bar-danger"})
            if span and prog:
                num_all = self.int_or_none(span.text.split()[0])
                num_free = self.int_or_none(prog.text)
                place_name = div.find("b").text.strip()
                place_name = re.sub(r"\(.*\)", "", place_name)
                place_id = place_name[place_name.index("ID:")+3:]
                place_name = place_name[:place_name.index("ID:")].strip()

                parking_places.append({
                    "place_name": place_name,
                    "place_id": place_id,
                    "num_all": num_all,
                    "num_free": num_free,
                })

        return parking_places


