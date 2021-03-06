import requests
import re
import os
import hashlib
import unicodedata
from xml.etree.ElementTree import fromstring

import xmljson

import bs4

from util import RegexFilter


class DataSources:

    _registered_sources = dict()

    def __init__(self):
        self.sources = list(self._registered_sources.values())

    def filtered(self, *expressions):
        exp_filter = RegexFilter(*expressions)
        return self.filtered_func(
            lambda s: exp_filter.matches(s["source_id"])
        )

    def excluded(self, *expressions):
        exp_filter = RegexFilter(*expressions)
        return self.filtered_func(
            lambda s: not exp_filter.matches(s["source_id"])
        )

    def filtered_func(self, func):
        sources = self.__class__()
        sources.sources = list(
            filter(func, self.sources)
        )
        return sources

    @classmethod
    def create(cls, source_id):
        """Create a new instance of the derived DataSource class"""
        return cls._registered_sources[source_id]["class"]()


class DataSource:
    """
    Base class for all data sources.

    Subclass this class and implement `download_snapshot_data()`.

        The result of get_snapshot_data will be stored to json files.
        It can return any object, but it must be json compatible
        and typically the minimal amount of necessary information is enough.

        A generic format is:
        [
            {
                "place_name": str,
                "num_free": int | None,
                "status": "open" | "closed",
                "num_all": int | None,
            }
        ]

        `place_name` and `num_free` are required, everything else is optional.

        You can also return unconverted API results, if they are small.

        Also add following class-attributes:
            source_id: str, the unique identifier for this data source
            web_url: str, some human-friendly url of the web service, e.g. `https://parken-in-dorf-xy.de/`

    For canonical data export you can override `transform_snapshot_data()` to
    convert your snapshot data into a generic format

    """

    _re_double_minus = re.compile(r"--+")

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

        attributes = dict()
        for key in ("source_id", "web_url"):
            value = getattr(cls, key, None)
            if not value:
                raise AssertionError(f"Must define class attribute {cls.__name__}.{key}")
            attributes[key] = value

        source_id = attributes["source_id"]
        if source_id in DataSources._registered_sources:
            other_class = DataSources._registered_sources[source_id]["class"]
            raise AssertionError(f"source_id '{source_id}' already used by class {other_class.__name__}")

        attributes["class"] = cls
        DataSources._registered_sources[source_id] = attributes

    def __init__(self, use_cache=False):
        self.session = requests.Session()
        self.cache_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "cache",
            self.source_id,
        )
        self.use_cache = use_cache

        self.session.headers = {
            "User-Agent": "Mozilla/5.0 Gecko/20100101 Firefox/74.0"
        }

    def download_snapshot_data(self):
        raise NotImplementedError

    def download_meta_data(self):
        pass

    def get_url(self, url, method="GET", data=None, encoding=None):
        if self.use_cache:
            if os.path.exists(self.get_cache_filename(url)):
                with open(self.get_cache_filename(url)) as fp:
                    return fp.read()

        for try_num in range(3):
            try:
                print("downloading", url)
                response = self.session.request(method, url, data=data, timeout=10)
                if encoding is None:
                    text = response.text
                else:
                    text = response.content.decode(encoding)
                break
            except requests.ConnectionError:
                if try_num == 2:
                    raise

        if self.use_cache:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            with open(self.get_cache_filename(url), "w") as fp:
                fp.write(text)

        return text

    def get_html_soup(self, url, encoding=None):
        text = self.get_url(url, encoding=encoding)
        soup = bs4.BeautifulSoup(text, parser="html.parser", features="lxml")
        return soup

    def get_xml_data(self, url):
        markup = self.get_url(url)
        return xmljson.parker.data(fromstring(markup))

    def get_cache_filename(self, x):
        hash = hashlib.md5(str(x).encode("utf-8")).hexdigest()
        return os.path.join(
            self.cache_dir,
            hash,
        )

    @staticmethod
    def xml_to_dict(markup):
        return xmljson.parker.data(fromstring(markup))

    @staticmethod
    def int_or_none(x):
        try:
            x = str(x)
            if len(x) > 1:
                x = x.lstrip("0")
            return int(x)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def float_or_none(x):
        try:
            return float(str(x))
        except (ValueError, TypeError):
            return None

    def place_name_to_id(self, place_name):
        place_name = str(place_name)
        place_name = place_name.replace("ß", "ss")
        place_name = unicodedata.normalize('NFKD', place_name).encode("ascii", "ignore").decode("ascii")

        place_id = "".join(
            c if c.isalnum() or c in " \t" else "-"
            for c in place_name
        ).replace(" ", "-")

        place_id = f"{self.source_id}-{place_id}"
        place_id = self._re_double_minus.sub("-", place_id).strip("-")
        return place_id

    def transform_snapshot_data(self, data):
        """
        Return canonical data for previously stored snapshot data retrieved from `download_snapshot_data`
        :param data: list | dict
        :return: list of dict
        {
            "place_id": str,            # unique id of parking-place
            "num_free": int | None,
        }
        """
        ret_data = []
        for entry in data:
            if "place_name" not in entry and "id" not in entry:
                raise KeyError(f"Expecting 'place_name' or 'id' in {self.__class__.__name__}.transform_snapshot_data() "
                               f"for entry {entry}")
            if "num_free" not in entry and "num_current" not in entry:
                raise KeyError(f"Expecting 'num_free' in {self.__class__.__name__}.transform_snapshot_data() "
                               f"for entry {entry}")

            num_free = entry.get("num_current")
            if "num_free" in entry:
                num_free = entry["num_free"]

            ret_data.append({
                "place_id": self.place_name_to_id(entry.get("id") or entry["place_name"]),
                "num_free": num_free
            })

        return ret_data

    def transform_meta_data(self, data):
        """
        Return canonical data for previously stored meta data retrieved from `download_meta_data`
        :param data: list
        :return: dict
        {
            "source_id": str,
            "source_web_url": str,
            "places": {
                str: {                          # mapping key is unique id of parking-place
                    "place_id": str,
                    "place_name": str,
                    "place_url": str,
                    "city_name", str | None,
                    "address": [str,] | None,
                    "coordinates": [float, float] | None,
                    "num_all": int | None,
                }
            }
        }

        The base implementation creates the whole dictionary and an initialized `places` dict
        """
        places = dict()
        if data and isinstance(data, list):
            for place in data:
                if isinstance(place, dict) and place.get("place_name"):
                    if place.get("id"):
                        place_id = self.place_name_to_id(place["id"])
                    else:
                        place_id = self.place_name_to_id(place["place_name"])
                    places[place_id] = {
                        "place_id": place_id,
                        "place_name": place["place_name"],
                        "place_url": place.get("place_url"),
                        "city_name": place.get("city_name") or getattr(self, "city_name", None),
                        "address": place.get("address"),
                        "coordinates": place.get("coordinates"),
                        "num_all": place.get("num_all"),
                    }

        return {
            "source_id": self.source_id,
            "source_web_url": self.web_url,
            "places": places,
        }

    def _make_places_complete(self, places):
        for place in places:
            if not place.get("city_name"):
                if not getattr(self, "city_name", None):
                    raise ValueError(f"Need to define class attribute {self.__class__.__name__}.city_name")
                place["city_name"] = getattr(self, "city_name")

            for key in ("place_url", "address", "coordinates", "num_all"):
                if not place.get(key):
                    place[key] = None
