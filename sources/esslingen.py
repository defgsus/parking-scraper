import bs4
import json
import re

from util import DataSource
from xml.etree.ElementTree import fromstring

import xmljson


class ParkingEsslingen(DataSource):

    source_id = "esslingen-parken"
    web_url = "https://www.esslingen.de/start/es_services/Parkhaeuser.html"

    def download_snapshot_data(self):
        markup = self.get_url("https://stadtplan.esslingen.de/parkplatzinfo/getRestData.jsp")
        data = json.loads(markup)

        parking_places = []

        for entry in data["PLSParkings"]:

            parking_places.append({
                "place_name": entry["Name"],
                "num_all": entry["Max"],
                "num_free": entry["Free"],
            })

        return parking_places
