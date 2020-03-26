import bs4
import json

from util import DataSource


class ParkingBonn(DataSource):

    source_id = "bonn-bcp-parken"

    def get_data(self):
        data = self.get_xml_data("http://www.bcp-bonn.de/stellplatz/bcpext.xml")

        return data["parkhaus"]

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            if entry["status"] in (0, ):
                ret_data.append({
                    "place_id": self.place_name_to_id(entry["bezeichnung"]),
                    "num_free": entry["frei"],
                })

        return ret_data