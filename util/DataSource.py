import requests
import re
import os
import hashlib

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


class DataSource:

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()

        attributes = dict()
        for key in ("source_id", ):
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

    def get_data(self):
        raise NotImplementedError

    def get_url(self, url):
        if self.use_cache:
            if os.path.exists(self.get_cache_filename(url)):
                with open(self.get_cache_filename(url)) as fp:
                    return fp.read()

        # print("downloading", url)
        response = self.session.get(url)
        text = response.text

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

    def get_cache_filename(self, x):
        hash = hashlib.md5(str(x).encode("utf-8")).hexdigest()
        return os.path.join(
            self.cache_dir,
            hash,
        )

    @staticmethod
    def int_or_none(x):
        try:
            return int(x)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def xml_to_dict(soup):
        def _iter(soup, obj):
            for child in soup.children:
                obj[child.name] = child

        #soup = bs4.BeautifulSoup(soup, parser="xml.parser", features="lxml")
        data = dict()

        _iter(soup, data)

        return data
