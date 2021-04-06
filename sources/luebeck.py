import json
import re

from util import DataSource


class ParkingLuebeck(DataSource):

    source_id = "parken-luebeck"
    web_url = "https://www.parken-luebeck.de/"
    city_name = "Lübeck"

    RE_PLACE_NUM = re.compile(r"\s*([^\|]+) | .* (\d+)\s+frei\s+/\s+(\d+)")

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for elem in soup.find_all("div", {"class": "location-list--item"}):
            #match = self.RE_PLACE_NUM.match(div1.text)
            #if match:
            #    print(match.groups())
            #else:
            #    print(div1.text)

            div = elem.find("div", {"class": "location-list-inner"})
            place_name = div.text.strip().split("|")[0].strip()

            div = elem.find("div", {"class": "free-live-spots"})
            try:
                num_free = int(div.text)
            except:
                num_free = None

            div = elem.find("div", {"class": "free-spots"})
            try:
                num_all = int(div.text.split("/")[-1])
            except:
                num_all = None

            parking_places.append({
                "place_name": place_name,
                "num_free": num_free,
                "num_all": num_all,
            })

        return parking_places

        # TODO: how to match with previous JSON based data? especially the ID?
        #    parking_places.append({
        #        "place_name": space["title"],
        #        "id": space["id"],
        #        "num_all": self.int_or_none(space["totalSpace"]),
        #        "num_free": self.int_or_none(space["free"]),
        #        "status": space["state"],
        #    })

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(entry.get("id") or entry["place_name"]),
                "num_free": entry.get("num_current") or entry.get("num_free")
            })

        return ret_data

    def transform_meta_data(self, data):
        #for place in data:
        #    place["id"] = f"{place['place_name'].lower()} {place['id']}"

        return super().transform_meta_data(data)
