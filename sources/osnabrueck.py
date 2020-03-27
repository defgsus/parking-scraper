import bs4
import json

from util import DataSource


class ParkingOsnabrueck(DataSource):

    source_id = "parken-osnabrueck"
    web_url = "https://www.parken-osnabrueck.de/"

    def get_snapshot_data(self):
        text = self.get_url("https://www.parken-osnabrueck.de/index.php?type=427590&tx_tiopgparkhaeuserosnabrueck_parkingosnabruek[controller]=Parking&tx_tiopgparkhaeuserosnabrueck_parkingosnabruek[action]=ajaxCallGetUtilizationData&_=1585143795975")

        return json.loads(text)

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data.values():
            ret_data.append({
                "place_id": self.place_name_to_id(entry["identifier"]),
                "num_free": entry["available"],
            })

        return ret_data
