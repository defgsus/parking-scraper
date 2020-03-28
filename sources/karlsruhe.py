import re
import json

from util import DataSource


class ParkingKarlsruhe(DataSource):

    source_id = "karlsruhe-parken"
    web_url = "https://web1.karlsruhe.de/service/Parken/"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        num_all_regex = re.compile(r".*gesamt (\d+) Park.*")

        for div in soup.find_all("div", {"class": "parkhaus"}):

            num_cur = div.find("div", {"class": "fuellstand"})
            if not num_cur:
                num_cur = None
                num_all = None
                status = "closed"
            else:
                num_cur = self.int_or_none(num_cur.text.split()[0])
                num_all = num_all_regex.findall(div.text)
                num_all = self.int_or_none(num_all[0]) if len(num_all) == 1 else None

            parking_places.append({
                "place_name": div.find("strong").text,
                "num_all": num_all,
                "num_free": num_cur,
            })

        return parking_places

