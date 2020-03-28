import requests
import re
import os
import hashlib
from xml.etree.ElementTree import fromstring

import xmljson

import bs4


class DataSources:

    _registered_sources = dict()

    def __init__(self):
        self.sources = list(self._registered_sources.values())

    def filtered(self, name_regex):
        regex = re.compile(name_regex)

        sources = self.__class__()
        sources.sources = list(
            filter(
                lambda a: regex.findall(a["source_id"]),
                self.sources
            )
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

        print("downloading", url)
        response = self.session.request(method, url, data=data)
        if encoding is None:
            text = response.text
        else:
            text = response.content.decode(encoding)

        if self.use_cache:
            if not os.path.exists(self.cache_dir):
                os.makedirs(self.cache_dir)
            with open(self.get_cache_filename(url), "w") as fp:
                fp.write(text)

        return text

    def get_html_soup(self, url):
        text = self.get_url(url)
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
            return int(str(x).lstrip("0"))
        except (ValueError, TypeError):
            return None

    @staticmethod
    def float_or_none(x):
        try:
            return float(str(x))
        except (ValueError, TypeError):
            return None

    def place_name_to_id(self, place_name):
        place_id = "".join(
            c if c.isalnum() or c in " \t" else "-"
            for c in place_name
        ).replace(" ", "-").replace("ß", "ss")

        place_id = f"{self.source_id}-{place_id}"
        place_id = self._re_double_minus.sub("-", place_id)
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
                    "city_name", str | None,
                    "address": [str,] | None,
                    "num_all": int | None,
                }
            }
        }

        The base implementation creates the whole dictionary and an initialized `places` dict
        """
        places = dict()
        if isinstance(data, list):
            for place in data:
                if isinstance(place, dict) and place.get("place_name"):
                    places.append({
                        "place_id": self.place_name_to_id(place["place_name"]),
                        "place_name": place["place_name"],
                        "city_name": place.get("city_name"),
                        "address": place.get("address"),
                        "num_all": place.get("num_all"),
                    })

        return {
            "source_id": self.source_id,
            "source_web_url": self.web_url,
            "places": places,
        }

