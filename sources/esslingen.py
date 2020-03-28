import bs4
import json
import re

from util import DataSource
from xml.etree.ElementTree import fromstring

import xmljson


class ParkingEsslingen(DataSource):

    source_id = "esslingen-parken"
    web_url = "https://www.esslingen.de/start/es_services/Parkhaeuser.html"
    city_name = "Esslingen"
    
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

    def XXX_download_meta_data(self):
        # TODO: IDs do not match
        markup = self.get_url("https://stadtplan.esslingen.de/parkplatzinfo/getRestData.jsp")
        main_data = json.loads(markup)
        print(main_data)

        parking_places = []

        for main_entry in main_data["PLSParkings"]:
            entry_id = main_entry["ID"] + 7100
            markup = self.get_url(f"https://stadtplan.esslingen.de/websis/controller/object/get_objects.gsp"
                                  f"?key=parkplatzinfo&style=&i18n=default&opts%5Bid%5D%5B%5D={entry_id}")#&_=1585424715265")

            markup = markup.strip()[5:-2]
            sub_data = json.loads(markup)
            print("---")
            if sub_data["objects"]:
                sub_entry = sub_data["objects"][0]
                print(json.dumps(sub_entry, indent=2))
                assert main_entry["Name"] == sub_entry["name"], (main_entry["Name"], "!=", sub_entry["name"])

                parking_places.append({
                    "place_name": main_entry["Name"],
                    "num_all": main_entry["Max"],
                    "place_url": sub_entry,
                })

        return parking_places
