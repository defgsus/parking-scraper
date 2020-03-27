import bs4
import json

from util import DataSource


class ParkingBochum(DataSource):

    source_id = "parken-in-bochum"
    web_url = "https://www.parken-in-bochum.de/parkhaeuser/"

    def get_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "details"}):

            num_cur = None
            spaces = div.find("div", {"class": "spaces"})
            if spaces:
                spaces = spaces.text.strip().split()
                if spaces:
                    num_cur = self.int_or_none(spaces[0])

            parking_places.append({
                "place_name": div.find("h3").text.strip(),
                "num_current": num_cur,
            })

        return parking_places
