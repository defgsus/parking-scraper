import os
import json


class Storage:

    def __init__(self):
        self.storage_dir = os.path.join(
            os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
            "snapshots",
        )

    def store(self, source_id, timestamp, data):
        file_path = os.path.join(
            self.storage_dir,
            source_id,
            timestamp.strftime("%Y-%m"),
        )
        if not os.path.exists(file_path):
            os.makedirs(file_path)

        filename = timestamp.strftime("%Y-%m-%d-%H-%M-%S.json")
        long_filename = os.path.join(file_path, filename)

        print("writing", long_filename)
        with open(long_filename, "w") as fp:
            json.dump(data, fp, indent=1)
