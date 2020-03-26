import os
import json
import datetime

import tqdm


class Storage:

    def __init__(self):
        self.storage_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "snapshots",
        )
        self.error_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "errors",
        )

    @classmethod
    def timestamp_to_filename(cls, timestamp, ext=None):
        fn = timestamp.strftime("%Y-%m-%d-%H-%M-%S")
        if ext:
            fn += f".{ext}"
        return fn

    @classmethod
    def filename_to_timestamp(cls, fn):
        return datetime.datetime.strptime(fn[:19], "%Y-%m-%d-%H-%M-%S")

    def store(self, source_id, timestamp, data, is_error=False):
        file_path = os.path.join(
            self.storage_dir if not is_error else self.error_dir,
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

    def find_files(self, source_id, min_timestamp=None):
        """
        Find all snapshot files for the given source
        :param source_id: str, id of source
        :param min_timestamp: datetime, optional lower limit on timestamps
        :return: list of dict
        {
            "timestamp": datetime   # timestamp of data retrieval
            "filename": str,        # absolute filename
        }
        """
        path = os.path.join(self.storage_dir, source_id)
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

    def load_files(self, source_id, min_timestamp=None):
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
        files = self.find_files(source_id, min_timestamp=min_timestamp)
        out_files = []

        for file in tqdm.tqdm(files):
            try:
                with open(file["filename"]) as fp:
                    file["data"] = json.load(fp)
                out_files.append(file)
            except BaseException as e:
                print(f"error: {file['filename']}: {e.__class__.__name__}: {e}")

        return out_files
