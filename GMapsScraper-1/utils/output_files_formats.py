from threading import Lock
from csv import DictWriter
from os.path import isfile

class CSVCreator:
    def __init__(self, file_lock: Lock, output_path: str = "./CSV_FILES"):
        self._output_path = output_path
        self._file_lock = file_lock

    def create_csv(self, list_of_dict_data: list[dict]):
        with self._file_lock:
            file_name = "google_maps_data.csv"
            is_header_file = not isfile(self._output_path + "/" + file_name)

            with open(self._output_path + "/" + file_name, "w" if is_header_file else "a", newline="", encoding="utf-8-sig") as file_handler:
                writer = DictWriter(file_handler, fieldnames=list_of_dict_data[0].keys(), extrasaction='ignore')
                if is_header_file:
                    writer.writeheader()

                writer.writerows(list_of_dict_data)
