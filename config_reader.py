"""This module read configuration from config.json"""
import json
import os


class ConfigReaderError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__()


class ConfigReader:
    def get_configuration(self) -> dict:
        """
        This method get configuration from config.json

        :return: dict with config

        :raises:
            ConfigReaderError
                1 - FileNotFoundError - if config.json does not exist
                2 - KeyError - if config doesn't have required fields
                3 - FileNotFoundError - if the path to the com0com directory is incorrect
        """
        try:
            file = open("config.json")
        except FileNotFoundError as e:
            raise ConfigReaderError(1, "Nie znaleziono pliku {}".format(os.path.abspath("config.json")))
        try:
            data = json.load(file)
        except ValueError as e:
            raise ConfigReaderError(1, "Niewłaściwy format danych w pliku {}".format(os.path.abspath("config.json")))
        for key in self.__get_required_config_settings():
            if key not in data:
                raise ConfigReaderError(1, "KeyError - W pliku config.json nie ma: " + key)
        if not os.path.exists(data["path_to_dict_com0com"] + "\\setupc.exe"):
            raise ConfigReaderError(2, "Ścieżka do katalogu com0com w config.json jest niepoprawna")
        return data

    @staticmethod
    def __get_required_config_settings() -> list:
        """
        This method return list of required keys

        :return: list of required key names that must be in config.json
        """
        list_settings = [
            "path_to_dict_com0com",
            "path_to_run_kegeln_program",
            "flags_to_run_kegeln_program",
            "com_x",
            "com_y",
            "com_z",
            "com_timeout",
            "com_write_timeout",
            "minimum_number_of_lines_to_write_in_log_file",
            "ip_addr",
            "port",
            "time_interval_break",
            "min_log_priority",
        ]
        return list_settings
