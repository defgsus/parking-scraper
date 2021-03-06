import re
import json

from util import DataSource


class ParkingReutlingen(DataSource):

    source_id = "reutlingen-parken"
    web_url = "https://www.reutlingen.de/de/Rathaus-Service/Noch-mehr-Service/Anreise,-Parkplaetze-und-Fahrplaene/Parken-in-Reutlingen"
    city_name = "Reutlingen"

    def download_snapshot_data(self):
        soup = self.get_html_soup("https://www.reutlingen.de/parkinfo/list")

        parking_places = []

        match_regex = re.compile("(.*) \(frei: (\d+)\)")

        for div in soup.find_all("div", {"class": "parkInfoService_list_title"}):
            text = div.text
            match = match_regex.findall(text)

            parking_places.append({
                "place_name": match[0][0],
                "num_free": self.int_or_none(match[0][1]),
            })

        return parking_places


