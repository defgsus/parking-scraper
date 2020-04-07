import argparse
import json
import datetime
import traceback
import csv
import os
from io import StringIO
from multiprocessing import Pool
from functools import partial
import numpy as np
from copy import deepcopy

import tqdm

from util import DataSources, Storage, RegexFilter, to_json, settings, to_utc, from_utc
from sources import *


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "command", type=str,
        help="""
        store: make a snapshot and store to disk
        store-meta: make a snapshot of meta data and store to disk
        dump: make a snapshot and dump as json
        dump-meta: make a snapshot of meta data and dump as json
        test: make a snapshot but print nothing except errors
        list: list all data sources
        load: load snapshots from disk and print
        load-stats: load snapshots from disk and print stats
        export: print complete json data of meta and snapshots - also tests if all timestamp places are in meta data
        export-csv: export timestamp csv file to --csv-path - export timezone is UTC
            if used with --date, export single day 
            otherwise export everything until UTC yesterday that is not already exported in --csv-path
        to-influx: load snapshots and export to influx
        """
    )
    parser.add_argument(
        "-i", "--include", type=str, nargs="+",
        help="regex to match names of data sources to include",
    )
    parser.add_argument(
        "-e", "--exclude", type=str, nargs="+",
        help="regex to match names of data sources to exclude",
    )
    parser.add_argument(
        "-id", "--include-id", type=str, nargs="+",
        help="regex to match place_ids - filters output of load, load-stats, ..",
    )
    parser.add_argument(
        "-d", "--date", type=str,
        help="'today', 'yesterday', or 'YYYY-MM-DD' - "
             "Limits the loading/export to a single day",
    )
    parser.add_argument(
        "-f", "--format", type=str, default="text",
        help="text, json, csv, influxdb",
    )
    parser.add_argument(
        "--csv-path", type=str, default="./csv-export",
        help="base directory for csv export, defaults to './csv-export'",
    )
    parser.add_argument(
        "-c", "--cache", type=bool, nargs="?", default=False, const=True,
        help="Store websites/endpoints data in cache directory and reuse if existing",
    )

    return parser.parse_args()


def download_source(use_cache, do_store, type, attributes):
    storage = Storage()
    timestamp = datetime.datetime.now()

    try:
        try:
            source = attributes["class"](use_cache=use_cache)
            if type == "meta":
                data = source.download_meta_data()
            else:
                data = source.download_snapshot_data()
                if not data:
                    raise ValueError(f"No data returned from {attributes['class'].__name__}.download_{type}_data()")

            if do_store and data:
                storage.store(attributes["source_id"], timestamp, data, type)

            return data

        except BaseException as e:
            error_str = f"{attributes['source_id']}: {e.__class__.__name__}"
            traceback_str = traceback.format_exc()
            print(f"{error_str}\n{traceback_str}")

            if do_store:
                storage.store(
                    attributes["source_id"],
                    timestamp,
                    {
                        "error": error_str,
                        "traceback": traceback_str,
                    },
                    "error"
                )

    except BaseException as e:
        print(f"{attributes['source_id']}: {e.__class__.__name__}: {e}\n{traceback.format_exc()}")


def download_sources(sources, use_cache, do_store=False, meta=False):

    pool = Pool(len(sources.sources))

    source_data_list = pool.map(
        partial(download_source, use_cache, do_store, "meta" if meta else "snapshot"),
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

    elif format == "json":
        print(to_json(filtered_data))

    elif format == "csv":
        io = StringIO()
        writer = csv.DictWriter(io, fieldnames=("place_id", "timestamp", "num_free"))
        writer.writeheader()
        for place_id in sorted(filtered_data):
            for ts in sorted(place_id_to_timestamps[place_id], key=lambda v: v["timestamp"]):
                ts = deepcopy(ts)
                ts["place_id"] = place_id
                writer.writerow(ts)
        io.seek(0)
        print(io.read())


def export_place_id_to_timestamps_csv_multiple_files(place_id_to_timestamps, place_id_filters=None):
    filtered_data = dict()
    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue
        filtered_data[place_id] = place_id_to_timestamps[place_id]

    export_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "csv-export"))
    if not os.path.exists(export_path):
        os.makedirs(export_path)

    for place_id in sorted(filtered_data):
        with open(os.path.join(export_path, f"{place_id}.csv"), "w") as fp:
            writer = csv.DictWriter(fp, fieldnames=("timestamp", "num_free"))
            writer.writeheader()
            last_value = "XYZ"
            for ts in sorted(place_id_to_timestamps[place_id], key=lambda v: v["timestamp"]):
                if ts["num_free"] != last_value:
                    writer.writerow(ts)
                last_value = ts["num_free"]


def export_place_id_to_timestamps_csv(place_id_to_timestamps, min_date, csv_path, place_id_filters=None):
    filtered_data = dict()
    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue
        filtered_data[place_id] = place_id_to_timestamps[place_id]

    export_path = [csv_path]
    if min_date:
        export_path += [
            min_date.strftime("%Y"),
            min_date.strftime("%Y-%m"),
        ]
        filename = min_date.strftime("%Y-%m-%d.csv")
    else:
        filename = datetime.datetime.now().strftime("complete-%Y-%m-%d-%H-%M-%S.csv")

    export_path = os.path.join(*export_path)
    filename = os.path.join(export_path, filename)

    if not os.path.exists(export_path):
        os.makedirs(export_path)

    timestamp_dict = dict()
    for place_id in sorted(filtered_data):
        last_value = "XYZ"
        for ts in place_id_to_timestamps[place_id]:
            if ts["num_free"] != last_value:
                key = to_utc(ts["timestamp"]).isoformat()
                if key not in timestamp_dict:
                    timestamp_dict[key] = {"timestamp": key}
                timestamp_dict[key][place_id] = ts["num_free"]
            last_value = ts["num_free"]

    timestamp_rows = [
        timestamp_dict[ts]
        for ts in sorted(timestamp_dict)
    ]

    if timestamp_rows:
        print(f"exporting timestamps {timestamp_rows[0]['timestamp']} - {timestamp_rows[-1]['timestamp']} to {filename}")
    else:
        print(f"exporting empty csv to {filename}")

    with open(filename, "w") as fp:
        writer = csv.DictWriter(fp, fieldnames=["timestamp"] + list(filtered_data))
        writer.writeheader()
        writer.writerows(timestamp_rows)


def dump_source_to_meta(source_id_to_meta, format="text"):
    if format == "text":
        for source_meta in source_id_to_meta.values():
            print("-"*10, source_meta["source_id"])
            for place in source_meta["places"].values():
                print(f"  {place['city_name']:25} {place['place_name']:50} {(place['num_all'] or ''):6} ({place['place_id']})")

    elif format == "json":
        print(to_json(source_id_to_meta, indent=2))

    elif format == "csv":
        keys = ["place_id", "place_name", "city_name", "num_all", "address", "latitude", "longitude",
                "place_url", "source_id", "source_web_url"]

        rows = []
        for source_meta in source_id_to_meta.values():
            for place in source_meta["places"].values():
                place = place.copy()
                if place["address"]:
                    place["address"] = "\n".join(place["address"])
                if place["coordinates"]:
                    place["latitude"] = place["coordinates"][0]
                    place["longitude"] = place["coordinates"][1]
                place.pop("coordinates", None)
                place["source_id"] = source_meta["source_id"]
                place["source_web_url"] = source_meta["source_web_url"]

                rows.append(place)

        with StringIO() as fp:
            writer = csv.DictWriter(fp, keys)
            writer.writeheader()
            writer.writerows(rows)
            fp.seek(0)
            print(fp.read())


def export_place_id_to_timestamps_influx(place_id_to_timestamps, source_id_to_meta, place_id_filters=None):
    from influxdb import InfluxDBClient
    client = InfluxDBClient(
        settings.INFLUX_DB_HOST, settings.INFLUX_DB_PORT,
        settings.INFLUX_DB_USER, settings.INFLUX_DB_PASSWORD,
        settings.INFLUX_DB_NAME
    )

    filtered_data = dict()
    for place_id in sorted(place_id_to_timestamps):
        if place_id_filters and not place_id_filters.matches(place_id):
            continue
        filtered_data[place_id] = place_id_to_timestamps[place_id]

    influx_data = convert_place_id_to_timestamps_to_influx(place_id_to_timestamps, source_id_to_meta)
    client.create_database('parking_scraper')

    client.write_points(influx_data)


def convert_place_id_to_timestamps_to_influx(place_id_to_timestamps, source_id_to_meta):
    place_id_lookup = dict()
    for source_meta in source_id_to_meta.values():
        for place in source_meta["places"].values():
            place_id_lookup[place["place_id"]] = place

    influx_data = []
    for place_id, timestamps in place_id_to_timestamps.items():
        meta = place_id_lookup[place_id]

        for timestamp in timestamps:
            if timestamp["num_free"] is not None:
                influx_data.append({
                    "measurement": "free_parking_spaces",
                    "tags": {
                        "place_id": place_id,
                        "place_name": meta["place_name"],
                        "city_name": meta["city_name"],
                    },
                    "time": timestamp["timestamp"].isoformat(),
                    "fields": {
                        "value": timestamp["num_free"]
                    }
                })
    return influx_data


def convert_place_id_to_timestamps_to_export(place_id_to_timestamps, source_id_to_meta, place_id_filters):
    place_id_lookup = dict()
    for source_meta in source_id_to_meta.values():
        for place in source_meta["places"].values():
            place_id_lookup[place["place_id"]] = place

    ret_places = []
    for place_id, timestamps in place_id_to_timestamps.items():
        if place_id_filters and not place_id_filters.matches(place_id):
            continue

        place_export = deepcopy(place_id_lookup[place_id])
        ret_places.append(place_export)
        place_export["timestamps"] = []

        for timestamp in timestamps:
            if timestamp["num_free"] is not None:
                place_export["timestamps"].append(timestamp)

    return ret_places


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

        abs_change = 0
        if true_y:
            last_v = true_y[0]
            for v in true_y[1:]:
                abs_change += abs(v - last_v)
                last_v = v
            abs_change / len(true_y)

        stats = {
            "place_id": place["place_id"],
            "num_timestamps": len(place["x"]),
            "num_changes": num_changes,
            "abs_changes": abs_change,
            "min_timestamp": place["x"][0],
            "max_timestamp": place["x"][-1],
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
                f" {place['min_timestamp']} first ts"
                f" {place['num_timestamps']:5} snapshots"
                f" {place['num_changes']:5} changes"
                f" {place['average']:7} average"
                f" {place['min']:7} min"
                f" {place['max']:7} max"
                f" {place['std']:7} std"
                f" {place['var']:7} var"
                f" {place['abs_changes']:7} abs-changes"
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


def export_csv(sources, min_date, max_date, place_id_filters, csv_path):
    if min_date:
        min_date = from_utc(min_date)
        max_date = from_utc(max_date)

        place_id_to_timestamps = Storage().load_sources(sources, min_timestamp=min_date, max_timestamp=max_date)
        export_place_id_to_timestamps_csv(place_id_to_timestamps, min_date, csv_path, place_id_filters=place_id_filters)

    else:
        existing_dates = set()
        for root, dirs, files in os.walk(csv_path):
            for fn in files:
                if fn.endswith(".csv"):
                    try:
                        existing_dates.add(
                            datetime.datetime.strptime(fn[:10], "%Y-%m-%d").date()
                        )
                    except ValueError:
                        pass

        yesterday = to_utc(datetime.datetime.now() - datetime.timedelta(days=1)).date()
        current_date = datetime.date(2020, 3, 24)  # my earliest records
        print(f"exporting {current_date} - {yesterday}")
        print(f"already existing: {existing_dates}")

        while current_date <= yesterday:
            if current_date not in existing_dates:
                min_date = datetime.datetime(current_date.year, current_date.month, current_date.day)
                max_date = min_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

                place_id_to_timestamps = Storage().load_sources(sources, min_timestamp=min_date, max_timestamp=max_date)
                export_place_id_to_timestamps_csv(
                    place_id_to_timestamps, min_date, csv_path, place_id_filters=place_id_filters
                )
            current_date += datetime.timedelta(days=1)


def main():

    args = parse_args()

    sources = DataSources()

    if args.include:
        sources = sources.filtered(*args.include)

    if args.exclude:
        sources = sources.excluded(*args.exclude)

    if not sources.sources:
        print("No data sources matching the filter")
        exit(1)

    min_date, max_date = None, None

    try:
        min_date = datetime.datetime.strptime(args.date, "%Y-%m-%d")
    except (ValueError, TypeError):
        if args.date is None:
            pass
        elif args.date == "today":
            min_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        elif args.date == "yesterday":
            min_date = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            min_date -= datetime.timedelta(days=1)
        else:
            print(f"Invalid date '{args.date}'")
            exit(2)

    if min_date:
        max_date = min_date + datetime.timedelta(days=1) - datetime.timedelta(seconds=1)

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

    elif args.command == "dump-meta" or args.command == "test-meta":
        all_data = download_sources(sources, use_cache=args.cache, meta=True)
        if args.command == "dump-meta":
            dump_raw_data(all_data, place_id_filters=place_id_filters)

    elif args.command == "store":
        download_sources(sources, use_cache=args.cache, do_store=True)

    elif args.command == "store-meta":
        download_sources(sources, use_cache=args.cache, do_store=True, meta=True)

    elif args.command == "load":
        place_id_to_timestamps = Storage().load_sources(sources, min_timestamp=min_date, max_timestamp=max_date)
        dump_place_id_to_timestamps(place_id_to_timestamps, place_id_filters=place_id_filters, format=args.format)

    elif args.command == "load-meta":
        source_id_to_meta = Storage().load_sources_meta(sources, min_timestamp=min_date, max_timestamp=max_date)
        dump_source_to_meta(source_id_to_meta, format=args.format)

    elif args.command == "load-stats":
        place_arrays = Storage().load_sources_arrays(sources, min_timestamp=min_date, max_timestamp=max_date)
        dump_stats(place_arrays, place_id_filters=place_id_filters, format=args.format)

    elif args.command == "export-csv":
        export_csv(sources, min_date, max_date, place_id_filters, args.csv_path)

    elif args.command == "export":
        place_id_to_timestamps = Storage().load_sources(sources, min_timestamp=min_date, max_timestamp=max_date)
        source_id_to_meta = Storage().load_sources_meta(sources)
        data = convert_place_id_to_timestamps_to_export(place_id_to_timestamps, source_id_to_meta, place_id_filters=place_id_filters)
        print(to_json(data, indent=2))

    elif args.command == "to-influxdb":
        place_id_to_timestamps = Storage().load_sources(sources, min_timestamp=min_date)
        source_id_to_meta = Storage().load_sources_meta(sources)
        export_place_id_to_timestamps_influx(place_id_to_timestamps, source_id_to_meta, place_id_filters=place_id_filters)

    else:
        print(f"Unknown command '{args.command}'")
        exit(2)


if __name__ == "__main__":
    main()
