import re
import argparse
import json
import datetime
import traceback
from multiprocessing import Pool
from functools import partial

from util import DataSources, Storage, RegexFilter
from sources import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        help="store, dump, test, list, load, list-spaces"
    )
    parser.add_argument(
        "-i", "--include", type=str, nargs="+",
        help="regex to match names of data sources",
    )
    parser.add_argument(
        "-id", "--include-id", type=str, nargs="+",
        help="regex to match place_ids - filters output of load, list-spaces, ..",
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


def dump_raw_data(data, place_id_filters=None):
    data_copy = dict()
    for source_id, source_data in data.items():
        # ds = DataSources.create(source_id)
        # ds.transform_snapshot_data()
        source_data_copy = []
        if isinstance(source_data, list):
            for place in source_data:
                if place_id_filters and place.get("place_name") and not place_id_filters.matches(place["place_name"]):
                    continue
                source_data_copy.append(place)
        else:
            source_data_copy = source_data

        if source_data_copy:
            data_copy[source_id] = source_data_copy

    print(json.dumps(data_copy, indent=2))


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

    return place_id_to_timestamps


def dump_place_id_to_timestamps(place_id_to_timestamps, place_id_filters=None):
    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue
        print(place_id)
        for value in sorted(place_id_to_timestamps[place_id], key=lambda v: v["timestamp"]):
            print("  ", value["timestamp"].isoformat(), ":", value["num_free"])


def dump_places(place_id_to_timestamps, place_id_filters=None):
    max_place_id_length = max(len(place_id) for place_id in place_id_to_timestamps)

    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue

        timestamps = place_id_to_timestamps[place_id]

        num_changes = 0
        last_num_free = "---"
        for timestamp in timestamps:
            if timestamp["num_free"] != last_num_free:
                last_num_free = timestamp["num_free"]
                num_changes += 1

        print(f"{place_id:{max_place_id_length}} {len(timestamps):5} snapshots / {num_changes:5} changes")
    print(f"num places: {len(place_id_to_timestamps)}")


def main():

    args = parse_args()

    sources = DataSources()

    if args.include:
        # TODO: should be ORed / use RegexFilter
        for regex in args.include:
            sources = sources.filtered(regex)

    if not sources.sources:
        print("No data sources matching the filter")
        exit(1)

    place_id_filters = args.include_id
    if place_id_filters:
        place_id_filters = RegexFilter(*place_id_filters)

    if args.command == "list":
        for source in sources.sources:
            print(source)

    elif args.command == "dump" or args.command == "test":
        all_data = download_sources(sources, use_cache=args.cache)
        if args.command == "dump":
            dump_raw_data(all_data, place_id_filters=place_id_filters)

    elif args.command == "store":
        download_sources(sources, use_cache=args.cache, do_store=True)

    elif args.command == "load":
        place_id_to_timestamps = load_storage(sources)
        dump_place_id_to_timestamps(place_id_to_timestamps, place_id_filters=place_id_filters)

    elif args.command == "list-places":
        place_id_to_timestamps = load_storage(sources)
        dump_places(place_id_to_timestamps, place_id_filters=place_id_filters)

    else:
        print(f"Unknown command '{args.command}'")
        exit(2)


if __name__ == "__main__":
    main()
