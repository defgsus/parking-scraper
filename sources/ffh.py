import bs4
import json

from util import DataSource


CITIES = [
    "frankfurt",
    "wiesbaden",
    "mannheim",
    "kassel",
    "bad-homburg",
]

URLS = [
    f"https://www.ffh.de/verkehr/parkhaeuser/parkhaus-info-{city}.html"
    for city in CITIES
]


class ParkingFFH(DataSource):

    source_id = "ffh-parken"
    web_url = "https://www.ffh.de/verkehr/parkhaeuser/"
    def download_snapshot_data(self):

        parking_places = []

        for city, url in zip(CITIES, URLS):
            soup = self.get_html_soup(f"{self.web_url}parkhaus-info-{city}.html")

            table = soup.find("table", {"id": "trafficParkingList"})
            for tr in table.find_all("tr"):
                if tr.get("data-facilityid"):
                    tds = list(filter(
                        lambda tag: tag.name == "td",
                        tr.children
                    ))

                    parking_place_name = tds[0].find("a").text.strip()
                    facility_id = tr.get("data-facilityid")

                    free_places = tds[1].text.strip()
                    try:
                        num_free = int(free_places)
                        status = "open"
                    except (TypeError, ValueError):
                        num_free = None
                        status = "closed" if "geschlossen" in free_places else None

                    sub_table = tds[0].find("table")
                    sub_tr = sub_table.find("tr")
                    tds = sub_tr.find_all("td")

                    num_all = None
                    if "Plätze insgesamt" in tds[0].text:
                        num_all = int(tds[1].text)

                    parking_places.append({
                        "city_name": city,
                        "place_name": parking_place_name,
                        "facility_id": facility_id,
                        "num_all": num_all,
                        "num_free": num_free,
                        "status": status,
                    })

        return parking_places

    def transform_snapshot_data(self, data):
        ret_data = []
        for entry in data:
            ret_data.append({
                "place_id": self.place_name_to_id(
                    entry["city_name"] + "-" + entry["place_name"]
                ),
                "num_free": entry.get("num_current") or entry.get("num_free")
            })

        return ret_data
