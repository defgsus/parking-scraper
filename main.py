import argparse
import json
import datetime
import traceback

from util import DataSources, Storage
from sources import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        help="store, dump, list"
    )
    parser.add_argument(
        "-i", "--include", type=str, nargs="+",
        help="regex to match names of data sources",
    )
    parser.add_argument(
        "-c", "--cache", type=bool, nargs="?", default=False, const=True,
        help="Store websites/endpoints data in cache directory and reuse if existing",
    )

    return parser.parse_args()


def download_source(attributes, use_cache):
    source = attributes["class"](use_cache=use_cache)
    return source.get_data()


def download_sources(sources, use_cache, do_store=False):
    storage = Storage()
    data = dict()
    for attributes in sources.sources:
        try:
            timestamp = datetime.datetime.now()

            source_data = download_source(attributes, use_cache=use_cache)
            data[attributes["source_id"]] = source_data

            if do_store:
                storage.store(attributes["source_id"], timestamp, data)

        except BaseException as e:
            print(f"{attributes['source_id']}: {e.__class__.__name__}: {e}\n{traceback.format_exc()}")

    return data


def main():

    args = parse_args()

    sources = DataSources()

    if args.include:
        for regex in args.include:
            sources = sources.filtered(regex)

    if not sources.sources:
        print("No data sources matching the filter")
        exit(1)

    if args.command == "list":
        for source in sources.sources:
            print(source)

    elif args.command == "dump":
        all_data = download_sources(sources, use_cache=args.cache)
        print(json.dumps(all_data, indent=2))

    elif args.command == "store":
        download_sources(sources, use_cache=args.cache, do_store=True)

    else:
        print(f"Unknown command '{args.command}'")
        exit(2)


if __name__ == "__main__":
    main()
