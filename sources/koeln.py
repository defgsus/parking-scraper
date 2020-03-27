import bs4
import json

from util import DataSource


class ParkingKoeln(DataSource):

    source_id = "koeln-apps-parken"
    web_url = "https://www.koeln.de/apps/parken/"

    def get_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for table in soup.find_all("table", {"class": "quarter"}):
            th = table.find("th")
            parking_group_name = th.text.strip()

            for tr in table.find_all("tr"):
                row = tr.find_all("td")
                if row:
                    parking_place_name = row[1].text.strip()

                    numbers = [img.get("alt") for img in row[0].find_all("img") if img.get("alt").isdigit()]
                    number = self.int_or_none("".join(numbers))

                    parking_places.append({
                        "group_name": parking_group_name,
                        "place_name": parking_place_name,
                        "num_current": number,
                    })

        return parking_places


