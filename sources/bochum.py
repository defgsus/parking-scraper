import re
import json

from util import DataSource


class ParkingBochum(DataSource):

    source_id = "parken-in-bochum"
    web_url = "https://www.parken-in-bochum.de/"
    city_name = "Bochum"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url + "parkhaeuser/")

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
                "num_free": num_cur,
            })

        return parking_places

    def download_meta_data(self):
        soup = self.get_html_soup(self.web_url + "parkhaeuser/")

        parking_places = []

        num_all_re = re.compile(r"Stellplätze:? (\d+).*")

        for div in soup.find_all("div", {"class": "details"}):
            place_name = div.find("h3").text.strip()

            actions = div.find("div", {"class": "actions"}).find_all("a")

            address_link = actions[1].get("href")
            address = [a.strip() for a in address_link.split("//")[-1].replace("+", " ").split(",")]
            # one of them are just geo coords
            if "Bochum" not in address[-1]:
                address = None

            num_all = None

            place_url = actions[0].get("href")
            place_url = self.web_url.rstrip("/") + place_url
            soup = self.get_html_soup(place_url)

            div = soup.find(text="Stellplätze:")
            if not div:
                div = soup.find(text="Stellplätze")
            match = num_all_re.match(div.parent.parent.text.strip())
            num_all = self.int_or_none(match.groups()[0]) if match else None

            parking_places.append({
                "place_name": place_name,
                "place_url": place_url,
                "address": address,
                "num_all": num_all,
            })

        return parking_places
