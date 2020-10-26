import bs4
import json

from util import DataSource


class ParkingUlmUni(DataSource):

    source_id = "uni-ulm-parken"
    web_url = "https://www.uni-ulm.de/einrichtungen/kiz/weiteres/campus-navigation/anreise/parkplaetze/"
    city_name = "Ulm"

    STREET_NAME_FIX = {
        'KLINIKEN': "Kliniken",
        'UNIVERSITÃ\x84T OST': "Universität Ost",
        'UNIVERSITÃ\x84T WEST': "Universität West",
        'HELMHOLTZSTRAÃ\x9fE': "Helmholtzstraße",
        'KLINIKEN MICHELSBERG': "Kliniken Michelsberg",
    }
    # TODO
    #   actually we could make pre-designed meta data by hand
    #   using above information and the geocoords from the javascript at /front/script.js

    def download_snapshot_data(self):
        # soap.php?counterid=10021
        place_dict = dict()
        self._parse_page(place_dict, "index")
        self._parse_page(place_dict, "mitarbeiter")

        return list(place_dict.values())

    def _parse_page(self, place_dict, url_part):
        soap = self.get_html_soup(f"http://tsu-app.rrooaarr.biz/front/{url_part}.html")

        for h2 in soap.find("section").find_all("h2"):
            ul = h2.find_next_sibling("ul")
            assert ul, f"Expected ul in siblings of {h2}"

            street_name = h2.text.strip()
            street_name = self.STREET_NAME_FIX.get(street_name, street_name)

            for a in ul.find_all("a"):
                place_name = a.find("span", {"class": "p-text"}).text.strip()
                place_number = a.find("span", {"class": "p-number"}).text.strip()
                div = a.find("div", {"class": "free-number"})

                if place_name == "Parkplatz":
                    place_name = street_name
                else:
                    place_name = f"{street_name} {place_name}"

                if "cid" in div.attrs:
                    cid = div.attrs["cid"]
                    num_all = self.int_or_none(div.attrs["max"])
                    num_occupied = self._get_num_occupied(div.attrs["cid"])
                    num_free = None
                    if num_all is not None and num_occupied is not None:
                        num_free = num_all - num_occupied

                    if cid not in place_dict:
                        place_dict[cid] = {
                            "v": 2,
                            "place_id": cid,
                            "place_name": f"{place_name} ({place_number})",
                            "num_free": num_free,
                            "num_all": num_all,
                        }

    def _get_num_occupied(self, cid):
        text = self.get_url(f"http://tsu-app.rrooaarr.biz/front/soap.php?counterid={cid}")
        return self.int_or_none(text)

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            version = entry.get("v") or 1

            if version == 1:
                # previously i just scraped 'counterid=10021' because i read it in a blog somewhere
                num_occupied = entry.get("num_current") or entry.get("num_free")
                num_all = 545
                if num_occupied is not None:
                    num_free = num_all - num_occupied
                else:
                    num_free = None

                ret_data.append({
                    "place_id": "10021",
                    "place_name": "Kliniken Michelsberg HNO Klinik (M 1)",
                    "num_free": num_free,
                    "num_all": num_all,
                })
            else:
                ret_data.append(entry)

            ret_data[-1]["place_id"] = self.place_name_to_id(ret_data[-1]["place_id"])

        return ret_data

    def transform_meta_data(self, data):
        ret_data = super().transform_meta_data(None)

        data = self.transform_snapshot_data(data)
        for place in data:
            place_data = place.copy()
            place_data.pop("num_free")
            ret_data["places"][place["place_id"]] = place

        return ret_data
