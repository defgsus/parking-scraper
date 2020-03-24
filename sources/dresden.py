import bs4
import json

from util import DataSource


class ParkingDresden(DataSource):

    source_id = "dresden-parken"

    def get_data(self):
        text = self.get_url("https://www.dresden.de/freie-parkplaetze")

        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")

        parking_places = []

        for table_div in soup.find_all("div", {"class": "element_table"}):
            thead = table_div.find("thead")
            columns = [
                          th.text.strip()
                          for th in thead.find_all("th")
                      ][1:]
            parking_group_name = columns[0]

            tbody = table_div.find("tbody")
            for tr in tbody.find_all("tr"):
                row = [
                          td.find("div", {"class": "content"}).text.strip()
                          for td in tr.find_all("td")
                      ][1:]
                parking_place_name = row[0]

                parking_places.append({
                    "group_name": parking_group_name,
                    "place_name": parking_place_name,
                    "num_all": int(row[1]) if row[1] else None,
                    "num_current": int(row[2]) if row[2] else None,
                })

        return parking_places
