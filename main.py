import argparse
import json
import datetime
import traceback
from multiprocessing import Pool
from functools import partial

from util import DataSources, Storage
from sources import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        help="store, dump, test, list, load"
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


def download_source(use_cache, do_store, attributes):
    storage = Storage()
    timestamp = datetime.datetime.now()

    try:
        try:
            source = attributes["class"](use_cache=use_cache)
            data = source.get_data()
            if not data:
                raise ValueError(f"No data returned from {attributes['class'].__name__}.get_data()")

            if do_store:
                storage.store(attributes["source_id"], timestamp, data)

            return data

        except BaseException as e:
            error_str = f"{attributes['source_id']}: {e.__class__.__name__}"
            traceback_str = traceback.format_exc()
            print(f"{error_str}\n{traceback_str}")

            if do_store:
                storage.store(attributes["source_id"], timestamp, {
                    "error": error_str,
                    "traceback": traceback_str,
                }, is_error=True)

    except BaseException as e:
        print(f"{attributes['source_id']}: {e.__class__.__name__}: {e}\n{traceback.format_exc()}")


def download_sources(sources, use_cache, do_store=False):

    pool = Pool()

    source_data_list = pool.map(
        partial(download_source, use_cache, do_store),
        sources.sources
    )

    data = dict()
    for attributes, result_data in zip(sources.sources, source_data_list):
        data[attributes["source_id"]] = result_data

    return data


def load_storage(sources):
    place_id_to_timestamps = dict()

    storage = Storage()
    for attributes in sources.sources:
        source_id = attributes["source_id"]

        files = storage.load_files(source_id)
        data_source = DataSources.create(source_id)

        for file in files:
            snapshot_data = file["data"]

            # fix previous storage bug
            if isinstance(snapshot_data, dict):
                try:
                    snapshot_data = snapshot_data[data_source.source_id]
                except KeyError:
                    pass

            try:
                file["canonical_data"] = data_source.transform_snapshot_data(snapshot_data)
            except BaseException as e:
                raise ValueError(
                    f"{data_source.__class__.__name__}.transform_snapshot_data() failed "
                    f"for timestamp {file['timestamp']}: "
                    f"{e.__class__.__name__}: {e}\n{traceback.format_exc()}")

            for data in file["canonical_data"]:
                place_id = data["place_id"]
                if place_id not in place_id_to_timestamps:
                    place_id_to_timestamps[place_id] = []
                place_id_to_timestamps[place_id].append({
                    "timestamp": file["timestamp"],
                    "num_free": data["num_free"]
                })

    for key in sorted(place_id_to_timestamps):
        print(key)
        for value in sorted(place_id_to_timestamps[key], key=lambda v: v["timestamp"]):
            print("  ", value["timestamp"].isoformat(), ":", value["num_free"])


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

    elif args.command == "dump" or args.command == "test":
        all_data = download_sources(sources, use_cache=args.cache)
        if args.command == "dump":
            print(json.dumps(all_data, indent=2))

    elif args.command == "store":
        download_sources(sources, use_cache=args.cache, do_store=True)

    elif args.command == "load":
        load_storage(sources)

    else:
        print(f"Unknown command '{args.command}'")
        exit(2)


if __name__ == "__main__":
    main()
