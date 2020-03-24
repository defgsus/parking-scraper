import bs4
import json

from util import DataSource


class ParkingUlmUni(DataSource):

    source_id = "uni-ulm-parken"

    def get_data(self):
        text = self.get_url("http://tsu-app.rrooaarr.biz/front/soap.php?counterid=10021")

        parking_places = [{
            "num_current": self.int_or_none(text)
        }]

        return parking_places
