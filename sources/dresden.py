import re
import json

from util import DataSource


class ParkingDresden(DataSource):

    source_id = "dresden-parken"
    web_url = "https://www.dresden.de/freie-parkplaetze"
    city_name = "Dresden"

    def download_snapshot_data(self):
        soup = self.get_html_soup(self.web_url)

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
                    "num_all": self.int_or_none(row[1]),
                    "num_free": self.int_or_none(row[2]),
                })

        return parking_places

    def download_meta_data(self):
        soup = self.get_html_soup(self.web_url)

        parking_places = []

        remove_jsession_re = re.compile(r";jsessionid=[0-9A-Z]+")

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
                    td.find("div", {"class": "content"})
                    for td in tr.find_all("td")
                ][1:]
                row_text = [td.text.strip() for td in row]
                parking_place_name = row_text[0]

                place_url = "https://www.dresden.de/apps_ext/ParkplatzApp" + row[0].find("a").get("href").lstrip(".")
                place_url = remove_jsession_re.sub("", place_url)
                soup = self.get_html_soup(place_url)

                address = soup.find("h3", text="Adresse")
                if address:
                    address = address.next_sibling.next_sibling
                    br = address.find("br")
                    address = [s.strip() for s in br.previous_sibling.split(",")]

                coordinates = None
                gps_lon = soup.find("div", text="GPS-Lon:")
                gps_lat = soup.find("div", text="GPS-Lat:")
                if gps_lon and gps_lat:
                    coordinates = [gps_lat.next_sibling.text, gps_lon.next_sibling.text]

                parking_places.append({
                    "group_name": parking_group_name,
                    "place_name": parking_place_name,
                    "place_url": place_url,
                    "num_all": self.int_or_none(row_text[1]),
                    "address": address,
                    "coordinates": coordinates,
                })

        return parking_places
