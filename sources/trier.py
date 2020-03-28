import bs4
import json

from util import DataSource


class ParkingTrier(DataSource):

    source_id = "swt-trier-parken"
    web_url = "https://www.swt.de/"
    city_name = "Trier"

    def download_snapshot_data(self):
        data = self.get_xml_data(f"{self.web_url}parken-v2.xml")

        return data["parkhaus"]

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry["phname"]),
                "num_free": entry["shortfree"],
            })

        return ret_data
