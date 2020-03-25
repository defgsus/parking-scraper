import re
import json

from util import DataSource


# The actual data is somehow blocked
class ParkingHeidelberg_TODO:  # (DataSource):

    source_id = "heidelberg-parken"
    web_url = "http://parken.heidelberg.de/"

    def get_data(self):
        self.session.headers.update({
            "Accept": "application/json, text/javascript, */*",
            "Host": "parken.heidelberg.de",
            "Referer": "http://parken.heidelberg.de/",
            "Pragma": "no-cache",
            "Cache-Control": "no-cache",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:74.0) Gecko/20100101 Firefox/74.0",
        })
        markup = self.get_url("http://parken.heidelberg.de/v1/parking-location?key=3wU8F-5QycD-ZbaW9-R6uvj-xm1MG-X07ne")
        print(markup)


