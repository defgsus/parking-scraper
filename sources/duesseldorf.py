import bs4
import json
import re

from util import DataSource
from xml.etree.ElementTree import fromstring

import xmljson


class ParkingDuesseldorf(DataSource):

    source_id = "vtmanager-duesseldorf-parken"
    web_url = "https://vtmanager.duesseldorf.de/info/?parkquartier#main"

    def download_snapshot_data(self):
        markup = self.get_url(
            "https://vtmanager.duesseldorf.de/geoserverwfs",
            method="POST",
            data='<wfs:GetFeature xmlns:wfs="http://www.opengis.net/wfs" service="WFS" version="1.1.0" xsi:schemaLocation="http://www.opengis.net/wfs http://schemas.opengis.net/wfs/1.1.0/wfs.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"><wfs:Query typeName="feature:Parkhaeuser" srsName="EPSG:900913" xmlns:feature="http://vtmanager.duesseldorf.de/"/></wfs:GetFeature>',
            encoding="utf-8"
        )

        data = self.xml_to_dict(markup)

        parking_places = []

        for entry in data["{http://www.opengis.net/gml}featureMembers"]["{http://vtmanager.duesseldorf.de/}Parkhaeuser"]:
            num_all = self.int_or_none(entry.get("{http://vtmanager.duesseldorf.de/}kurzparkermax"))
            num_occupied = self.int_or_none(entry.get("{http://vtmanager.duesseldorf.de/}kurzparkerbelegt"))
            num_cur = None
            if num_all is not None and num_occupied is not None:
                num_cur = num_all - num_occupied

            place_name = entry["{http://www.opengis.net/gml}name"]

            parking_places.append({
                "place_name": place_name,
                "id": "-".join(place_name.split()[:2]),
                "num_all": num_all,
                "num_free": num_cur,
            })

        return parking_places

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            place_id = entry.get("id") or "-".join(entry["place_name"].split()[:2])
            ret_data.append({
                "place_id": self.place_name_to_id(place_id),
                "num_free": entry.get("num_free") or entry.get("num_current"),
            })

        return ret_data
