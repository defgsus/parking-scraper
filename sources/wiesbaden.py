from copy import deepcopy

from util import DataSource


class ParkingWiesbaden(DataSource):

    source_id = "wiesbaden-parken"
    web_url = "https://www.wiesbaden.de/leben-in-wiesbaden/verkehr/verkehrsinfos/parken.php"
    city_name = "Wiesbaden"

    def download_snapshot_data(self):
        soup = self.get_html_soup("https://wi.memo-rheinmain.de/wiesbaden/parkliste.phtml?order=carparks")

        parking_places = []

        table = soup.find("table")
        for tr in table.find_all("tr"):
            row = [td.text.strip() for td in tr.find_all("td")]
            if row and row[0] == "":
                numbers = row[2].split("/")
                if len(numbers) != 2:
                    numbers = (None, None)
                parking_places.append({
                    "place_name": self._fix_name(row[1]),
                    "num_all": self.int_or_none(numbers[1]),
                    "num_free": self.int_or_none(numbers[0]),
                })

        return parking_places

    def transform_snapshot_data(self, data):
        return super().transform_snapshot_data(self._fix_data(data))

    def transform_meta_data(self, data):
        return super().transform_meta_data(self._fix_data(data))

    def _fix_name(self, name):
        if name.startswith("Coulinstra"):
            return "Coulinstrasse"
        return name

    def _fix_data(self, data):
        data = deepcopy(data)
        for place in data:
            place["place_name"] = self._fix_name(place["place_name"])
        return data