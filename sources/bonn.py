import bs4
import json
import xmljson
from xml.etree.ElementTree import fromstring

from util import DataSource


class ParkingBonn(DataSource):

    source_id = "bonn-bcp-parken"

    def get_data(self):
        text = self.get_url("http://www.bcp-bonn.de/stellplatz/bcpext.xml")

        data = xmljson.parker.data(fromstring(text))
        return data["parkhaus"]
