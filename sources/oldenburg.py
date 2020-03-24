import bs4
import json
import xmljson
from xml.etree.ElementTree import fromstring

from util import DataSource


class ParkingOldenburg(DataSource):

    source_id = "oldenburg-service-parken"

    def get_data(self):
        text = self.get_url("https://oldenburg-service.de/cros.php")

        data = xmljson.parker.data(fromstring(text))
        return data["Parkhaus"]

