import bs4
import json

from util import DataSource


class ParkingTrier(DataSource):

    source_id = "swt-trier-parken"

    def get_data(self):
        data = self.get_xml_data("https://www.swt.de/parken-v2.xml")

        return data["parkhaus"]

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry["phname"]),
                "num_free": entry["shortfree"],
            })

        return ret_data
