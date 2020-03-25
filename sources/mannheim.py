import bs4
import json

from util import DataSource


class ParkingMannheim(DataSource):

    source_id = "parken-mannheim"
    web_url = "https://www.parken-mannheim.de/"

    def get_data(self):
        text = self.get_url(self.web_url)
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        div = soup.find("div", {"id": "parkhausliste-ct"})
        div = div.find("div")
        for a in div.find_all("a"):
            row = [d.text.strip() for d in a.parent.parent.find_all("div")]
            
            parking_places.append({
                "place_name": row[0],
                "num_current": self.int_or_none(row[1]),
            })

        return parking_places

    def get_meta_data_TODO(self):
        text = self.get_url(self.web_url)
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        div = soup.find("div", {"id": "parkhausliste-ct"})
        urls = [a.get("href") for a in div.find_all("a")]

        for url in urls:
            text = self.get_url(self.web_url + url)
            soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

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
                    "num_current": self.int_or_none(num_cur),
                })
            else:
                print(num_all)
            #for h3 in park_div.find_all("h3"):
            #    print(h3)
            #    print(h3.parent.)

            continue

