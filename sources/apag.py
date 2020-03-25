import bs4
import json

from util import DataSource


class ParkingApag(DataSource):

    source_id = "apag-parken"
    web_url = "https://www.apag.de/"

    def get_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "houses"}):
            city_name = div.previous_sibling.previous_sibling
            assert city_name.name == "h2", "markup changed"
            city_name = city_name.text.split()[-1]

            for li in div.find_all("li"):
                parking_places.append({
                    "place_name": "%s %s" % (city_name, li.find("span").find("a").text.strip()),
                    "num_current": self.int_or_none(li.find("span", {"class": "counter"}).text.split()[0]),
                })

        return parking_places
