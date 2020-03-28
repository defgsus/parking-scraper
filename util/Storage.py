import os
import json
import datetime
import traceback

import tqdm


class Storage:

    def __init__(self):
        self.directories = {
            "snapshot": os.path.join(
                os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
                "snapshots",
            ),
            "meta": os.path.join(
                os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
                "snapshots-meta",
            ),
            "error": os.path.join(
                os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
                "errors",
            )
        }

    @classmethod
    def timestamp_to_filename(cls, timestamp, ext=None):
        fn = timestamp.strftime("%Y-%m-%d-%H-%M-%S")
        if ext:
            fn += f".{ext}"
        return fn

    @classmethod
    def filename_to_timestamp(cls, fn):
        return datetime.datetime.strptime(fn[:19], "%Y-%m-%d-%H-%M-%S")

    def store(self, source_id, timestamp, data, type):
        """
        Store json data for source_id
        :param source_id: str
        :param timestamp: datetime
        :param data: dict | list
        :param type: "snapshot", "meta", "error"
        """
        file_path = os.path.join(
            self.directories[type],
            source_id,
            timestamp.strftime("%Y-%m"),
        )
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        filename = self.timestamp_to_filename(timestamp, "json")
        long_filename = os.path.join(file_path, filename)

        print("writing", long_filename)
        with open(long_filename, "w") as fp:
            json.dump(data, fp, indent=1)

    def find_files(self, source_id, min_timestamp=None, type="snapshot"):
        """
        Find all snapshot files for the given source
        :param source_id: str, id of source
        :param min_timestamp: datetime, optional lower limit on timestamps
        :param type: str, snapshot/meta/error
        :return: list of dict, sorted by timestamp
        {
            "timestamp": datetime   # timestamp of data retrieval
            "filename": str,        # absolute filename
        }
        """
        path = os.path.join(self.directories[type], source_id)
        ret_files = []
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".json"):
                    timestamp = self.filename_to_timestamp(file)
                    if not min_timestamp or timestamp >= min_timestamp:
                        ret_files.append({
                            "filename": os.path.join(root, file),
                            "timestamp": timestamp,
                        })

        ret_files.sort(key=lambda f: f["timestamp"])
        return ret_files

    def load_files(self, source_id, min_timestamp=None, type="snapshot"):
        """
        Load all snapshot files for the given source.
        Will remove snapshots that can not be loaded / json-parsed.

        :param source_id: str, id of source
        :param min_timestamp: datetime, optional lower limit on timestamps
        :return: list of dict
        {
            "timestamp": datetime   # timestamp of data retrieval
            "filename": str,        # absolute filename
            "data": list            # actual data content of snapshot
        }
        """
        files = self.find_files(source_id, min_timestamp=min_timestamp, type=type)
        out_files = []

        for file in files:
            try:
                with open(file["filename"]) as fp:
                    file["data"] = json.load(fp)
                out_files.append(file)

            except BaseException as e:
                #print(f"error: {file['filename']}: {e.__class__.__name__}: {e}")
                pass

        return out_files

    def load_meta(self, source_id):
        """
        Load latest meta snapshot
        :return: dict or None
        """
        files = self.find_files(source_id, type="meta")
        if not files:
            return None

        with open(files[-1]["filename"]) as fp:
            return json.load(fp)
        # TODO might return the latest 'valid' data here

    def load_sources(self, sources, min_timestamp=None):
        from .DataSource import DataSources

        place_id_to_timestamps = dict()

        for attributes in tqdm.tqdm(sources.sources):
            source_id = attributes["source_id"]

            files = self.load_files(source_id, min_timestamp=min_timestamp)
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

    def load_sources_meta(self, sources, min_timestamp=None):
        from .DataSource import DataSources

        source_id_to_meta = dict()

        for attributes in tqdm.tqdm(sources.sources):
            source_id = attributes["source_id"]

            data_source = DataSources.create(source_id)

            meta_data = self.load_meta(source_id)

            if meta_data:
                canonical_data = data_source.transform_meta_data(meta_data)
            else:
                snapshot_files = self.find_files(source_id, min_timestamp)
                if not snapshot_files:
                    raise AssertionError("No meta-data and no snapshot-data stored")
                with open(snapshot_files[-1]["filename"]) as fp:
                    meta_data = json.load(fp)
                    canonical_data = data_source.transform_meta_data(meta_data)

            source_id_to_meta[source_id] = canonical_data

        return source_id_to_meta

    def load_sources_arrays(self, sources, min_timestamp=None):
        place_timestamps = self.load_sources(sources, min_timestamp=min_timestamp)
        place_list = []
        for place_id in sorted(place_timestamps):
            timestamps = place_timestamps[place_id]
            place_list.append({
                "place_id": place_id,
                "x": [t["timestamp"] for t in timestamps],
                "y": [t["num_free"] for t in timestamps],
            })
        return place_list
