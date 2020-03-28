import bs4
import json

from util import DataSource


class ParkingBonn(DataSource):

    source_id = "bonn-bcp-parken"
    web_url = "http://www.bcp-bonn.de/"
    city_name = "Bonn"

    def download_snapshot_data(self):
        data = self.get_xml_data(f"{self.web_url}stellplatz/bcpext.xml")
        return data["parkhaus"]

    def download_meta_data(self):
        data = self.get_xml_data(f"{self.web_url}stellplatz/bcpext.xml")
        return {
            "xml": data["parkhaus"]
        }

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            if entry["status"] in (0, ):
                ret_data.append({
                    "place_id": self.place_name_to_id(entry["bezeichnung"]),
                    "num_free": entry["frei"],
                })

        return ret_data

    def transform_meta_data(self, data):
        xml_entries = data
        if isinstance(data, dict):
            xml_entries = data["xml"]

        ret_data = []
        for entry in xml_entries:
            if entry["status"] in (0, ):
                ret_data.append({
                    "place_name": entry["bezeichnung"],
                    "num_all": entry["gesamt"],
                })

        ret_data = super().transform_meta_data(ret_data)

        return ret_data
