"""This module read configuration from config.json"""
import json
import os


def get_configurations() -> dict:
    """
    This method get config from config.json

    :return: dict with config

    :raise:
        KeyError - if config doesn't have required fields
        FileNotFoundError - if the path to the com0com directory is incorrect
        FileNotFoundError - if config.json does not exist
    """
    try:
        file = open("config.json")
        data = json.load(file)
        for key in ["path_to_dict_com0com", "com_x", "com_y", "com_z", "com_timeout", "com_write_timeout",
                    "minimum_number_of_lines_to_write_in_log_file"]:
            if key not in data:
                raise KeyError("W pliku config.json nie ma: " + key)
        if not os.path.exists(data["path_to_dict_com0com"]+"\\setupc.exe"):
            raise FileNotFoundError("Ścieżka do katalogu com0com w config.json jest niepoprawna")
        return data
    except FileNotFoundError:
        raise FileNotFoundError("Nie znaleziono pliku config.json")
