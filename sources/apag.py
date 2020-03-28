import bs4
import json

from util import DataSource


class ParkingApag(DataSource):

    source_id = "apag-parken"
    web_url = "https://www.apag.de/"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "houses"}):
            city_name = div.previous_sibling.previous_sibling
            assert city_name.name == "h2", "markup changed"
            city_name = city_name.text.split()[-1]

            for li in div.find_all("li"):
                parking_places.append({
                    "place_name": "%s %s" % (city_name, li.find("span").find("a").text.strip()),
                    "num_free": self.int_or_none(li.find("span", {"class": "counter"}).text.split()[0]),
                })

        return parking_places

    def download_meta_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"class": "houses"}):
            city_name = div.previous_sibling.previous_sibling
            assert city_name.name == "h2", "markup changed"
            city_name = city_name.text.split()[-1]

            for li in div.find_all("li"):
                place_link = li.find("span").find("a")
                place_url = self.web_url.rstrip("/") + place_link.get("href")
                soup = self.get_html_soup(place_url)

                elem_total = soup.find("span", {"class": "total"})
                elem_address = soup.find("div", {"class": "address"})

                elem_lat = soup.find("meta", {"itemprop": "latitude"})
                elem_long = soup.find("meta", {"itemprop": "longitude"})
                coords = None
                if elem_lat and elem_long:
                    coords = [self.float_or_none(elem_lat.get("content")), self.float_or_none(elem_long.get("content"))]

                parking_places.append({
                    "city_name": city_name,
                    "place_name": place_link.text.strip(),
                    "place_url": place_url,
                    "num_all": self.int_or_none(elem_total.text.split()[-1]) if elem_total else None,
                    "address": [i for i in elem_address.text.strip().split("\n") if i],
                    "coordinates": coords,
                })

        return parking_places
