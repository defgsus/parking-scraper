import argparse
import json
import datetime
import traceback
import csv
from io import StringIO
from multiprocessing import Pool
from functools import partial
import numpy as np

import tqdm

from util import DataSources, Storage, RegexFilter, to_json
from sources import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        help="""
        store: make a snapshot and store to disk
        dump: make a snapshot and just dump as json
        test: make a snapshot but print nothing except errors
        list: list all data sources
        load: load snapshots from disk and print
        load-stats: load snapshots from disk and print stats
        """
    )
    parser.add_argument(
        "-i", "--include", type=str, nargs="+",
        help="regex to match names of data sources",
    )
    parser.add_argument(
        "-id", "--include-id", type=str, nargs="+",
        help="regex to match place_ids - filters output of load, load-stats, ..",
    )
    parser.add_argument(
        "-f", "--format", type=str, default="text",
        help="text, json, csv",
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


def dump_place_id_to_timestamps(place_id_to_timestamps, place_id_filters=None, format="text"):
    filtered_data = dict()
    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue
        filtered_data[place_id] = place_id_to_timestamps[place_id]

    if format == "text":
        for place_id in sorted(filtered_data):
            print(place_id)
            for value in sorted(place_id_to_timestamps[place_id], key=lambda v: v["timestamp"]):
                print("  ", value["timestamp"].isoformat(), ":", value["num_free"])
    else:
        print(to_json(filtered_data))


def dump_stats(place_arrays, place_id_filters=None, format="text"):
    max_place_id_length = max(len(place["place_id"]) for place in place_arrays)

    stats_list = []
    for place in place_arrays:
        if place_id_filters and not place_id_filters.matches(place["place_id"]):
            continue

        num_changes = 0
        last_value = "---"
        for value in place["y"]:
            if value != last_value:
                last_value = value
                num_changes += 1

        true_y = [v for v in place["y"] if v is not None]

        stats = {
            "place_id": place["place_id"],
            "num_timestamps": len(place["x"]),
            "num_changes": num_changes,
        }

        for key in ("average", "min", "max", "median", "mean", "std", "var"):
            if true_y:
                stats[key] = round(getattr(np, key)(true_y), 1)
            else:
                stats[key] = ""

        stats_list.append(stats)

    if format == "text":
        for place in stats_list:
            print(
                f"{place['place_id']:{max_place_id_length}}"
                f" {place['num_timestamps']:5} snapshots"
                f" {place['num_changes']:5} changes"
                f" {place['average']:7} average"
                f" {place['min']:7} min"
                f" {place['max']:7} max"
                f" {place['std']:7} std"
                f" {place['var']:7} var"
            )
        print(f"num places: {len(place_arrays)}")

    elif format == "json":
        print(to_json(stats_list))

    elif format == "csv":
        with StringIO() as fp:
            writer = csv.DictWriter(fp, stats_list[0].keys())
            writer.writeheader()
            writer.writerows(stats_list)
            fp.seek(0)
            print(fp.read())


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
        place_id_to_timestamps = Storage().load_sources(sources)
        dump_place_id_to_timestamps(place_id_to_timestamps, place_id_filters=place_id_filters, format=args.format)

    elif args.command == "load-stats":
        place_arrays = Storage().load_sources_arrays(sources)
        dump_stats(place_arrays, place_id_filters=place_id_filters, format=args.format)

    else:
        print(f"Unknown command '{args.command}'")
        exit(2)


if __name__ == "__main__":
    main()
