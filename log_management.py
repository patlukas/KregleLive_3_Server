"""This module creates a log file and writes the logs to a log file"""
import os
from datetime import datetime


class LogManagement:
    def __init__(self, minimum_number_of_lines_to_write: int = 1):
        """
        self.__name - <str> log file name
        self.__index - <int> index of the last saved log
        self.__number_lines_to_write - <int> how many logs are waiting to be written
        self.__minimum_number_of_lines_to_write - <int> when this number of logs are waiting,
                                                        the logs are written to the file
        self.__lines_to_writ - <str> logs waiting to be saved

        :param minimum_number_of_lines_to_write: when this number of lines the program will then write them to the file
        """
        if not os.path.exists("logs") or not os.path.isdir("logs"):
            os.makedirs("logs")
        self.__name = "logs/" + self.__get_file_name()
        open(self.__name, "w").close()
        self.__index = 0
        self.__number_lines_to_write = 0
        self.__minimum_number_of_lines_to_write = minimum_number_of_lines_to_write
        self.__lines_to_write = ""
        self.__log_list = []

    def set_minimum_number_of_lines_to_write(self, minimum_number_of_lines_to_write):
        """
        This method updates value in minimum_number_of_lines_to_write

        :param minimum_number_of_lines_to_write: <int> when this number of logs are waiting,
                                                        the logs are written to the file
        """
        self.__minimum_number_of_lines_to_write = minimum_number_of_lines_to_write

    def __get_file_name(self) -> str:
        """
        :return: name of logs file, in name is datetime
        """
        filename = "logs_{}.log".format(self.__get_datetime())
        return filename

    @staticmethod
    def __get_datetime(with_ms: bool = False) -> str:
        """
        :param with_ms: if True, then str in return include milliseconds
        :return: str with datetime, without ms format: YYYY_MM_DD__gg_mm_ss, with ms: YYYY_MM_DD__gg_mm_ss_mmmm
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")
        day = now.strftime("%d")
        hour = now.strftime("%H")
        minute = now.strftime("%M")
        second = now.strftime("%S")
        datetime_str = "{}_{}_{}__{}_{}_{}".format(year, month, day, hour, minute, second)
        if with_ms:
            millisecond = now.strftime("%f")[:3]
            datetime_str += "_{}".format(millisecond)
        return datetime_str

    def add_log(self, priority: int, code: str, port: str, message: str) -> None:
        """
        This method write log messages to log file. This method save logs to file, when is
        __minimum_number_of_lines_to_write logs to save.

        :param code: log code, e.g. 'SKT_SEND'
        :param port: port name, e.g. 'COM1' or '127.0.0.1'
        :param message: log description
        :param priority: log priority level (0 - not important, ...)
        :return: None
        """
        if type(port) == tuple:
            port = str(port)
        if type(code) != str:
            code = str(code)
        if type(port) != str:
            port = str(port)
        if type(message) != str:
            message = str(message)
        self.__index += 1
        self.__number_lines_to_write += 1
        date = self.__get_datetime(True)
        self.__log_list.append([self.__index, date, priority, code, port, message])
        new_line = "{}.\t{}\t{}\t{}\t{}\t{}".format(self.__index, date, priority, code.ljust(14), port.ljust(26), message)
        self.__lines_to_write += new_line + "\n"
        if priority > 1:
           print(new_line)

        if self.__number_lines_to_write >= self.__minimum_number_of_lines_to_write:
            if not os.path.exists("logs") or not os.path.isdir("logs"):
                os.makedirs("logs")
            with open(self.__name, "a") as file:
                file.write(self.__lines_to_write)
            self.__lines_to_write = ""
            self.__number_lines_to_write = 0

    def close_log_file(self) -> None:
        """
        This method writes unsaved logs to a file.

        :return: None
        """
        with open(self.__name, "a") as file:
            if not os.path.exists("logs") or not os.path.isdir("logs"):
                os.makedirs("logs")
            file.write(self.__lines_to_write)
