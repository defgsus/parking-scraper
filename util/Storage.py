import os
import json
import datetime


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
