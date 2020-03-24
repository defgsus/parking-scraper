import bs4
import json

from util import DataSource


class ParkingMuenster(DataSource):

    source_id = "stadt-muenster-parken"

    def get_data(self):
        text = self.get_url("https://www.stadt-muenster.de/index.php?id=10910")
        return json.loads(text)
