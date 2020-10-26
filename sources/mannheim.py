import bs4
import json

from util import DataSource


class ParkingMannheim(DataSource):

    source_id = "parken-mannheim"
    web_url = "https://www.parken-mannheim.de/"
    city_name = "Mannheim"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        for div in soup.find_all("div", {"id": "parkhausliste-ct"}):
            div = div.find("div")
            if not div:
                continue

            for a in div.find_all("a"):
                row = [d.text.strip() for d in a.parent.parent.find_all("div")]

                parking_places.append({
                    "place_name": row[0],
                    "num_free": self.int_or_none(row[1]),
                })

        return parking_places

    def get_meta_data_TODO(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        div = soup.find("div", {"id": "parkhausliste-ct"})
        urls = [a.get("href") for a in div.find_all("a")]

        for url in urls:
            soup = self.get_html_soup(self.web_url + url)

            park_div = soup.find("div", {"class": "parkhaus-left-ct"})
            place_name = park_div.find("h2").text.strip()

            park_text = park_div.text
            num_all = park_text[park_text.index("Stellplätze")+12:park_text.index("Aktuell freie")].strip()
            num_cur = park_text[park_text.index("Aktuell freie Parkplätze")+20:]

            print("\n")
            print(place_name)
            if self.int_or_none(num_cur) is not None:
                parking_places.append({
                    "place_name": place_name,
                    "num_all": self.int_or_none(num_all),
                    "num_free": self.int_or_none(num_cur),
                })
            else:
                print(num_all)
            #for h3 in park_div.find_all("h3"):
            #    print(h3)
            #    print(h3.parent.)

            continue

