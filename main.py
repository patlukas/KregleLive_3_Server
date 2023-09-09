from connection_manager import ConnectionManager
from log_management import LogManagement
from config_reader import ConfigReader, ConfigReaderError
from serial_port_manager import SerialPortManager, SerialPortManagementError
import subprocess
import sys
import os


class Program:
    def __init__(self):
        print("Start:")
        self.__log_management = None
        self.__log_management = LogManagement()
        self.__log_management.add_log(0, "START", "", "Aplikacja została uruchomiona")
        try:
            self.__set_working_directory()
            self.__config = ConfigReader().get_configuration()
            self.__log_management.add_log(2, "CNF_READ", "", "Pobrano konfigurację")
            self.__log_management.set_minimum_number_of_lines_to_write(
                self.__config["minimum_number_of_lines_to_write_in_log_file"]
            )
            self.__com_result = SerialPortManager(self.__config).ports_com_management()
            if self.__com_result[0] > 0:
                self.__run_kegeln_program()
            self.__log_management.add_log(2, "COM_MNGR", str(self.__com_result[0]), self.__com_result[1])

            ConnectionManager(self.__config["com_x"], self.__config["com_y"], self.__config["com_timeout"],
                              self.__config["com_write_timeout"], self.__log_management.add_log,
                              self.__config["ip_addr"], self.__config["port"], self.__config["time_interval_break"])
        except ConfigReaderError as e:
            self.__log_management.add_log(10, "CNF_READ_ERROR", e.code, e.message)
        except SerialPortManagementError as e:
            self.__log_management.add_log(10, "COM_MNGR_ERROR", e.code, e.message)
        except Exception as e:
            self.__log_management.add_log(10, "MAIN_____ERROR", "", str(e))
        if self.__log_management is not None:
            self.__log_management.close_log_file()

        while True:
            pass

    def __run_kegeln_program(self):
        cmd = self.__config["command_to_run_kegeln_program"]
        if cmd == "":
            self.__log_management.add_log(10, "KEGELN_1_ERROR", "kegeln.exe", "Path to kegeln not exist")
            return "Path to kegeln not exist"
        try:
            subprocess.Popen(cmd, shell=True)
        except subprocess.CalledProcessError as e:
            self.__log_management.add_log(10, "KEGELN_2_ERROR", "kegeln.exe", str(e))
            return str(e)
        self.__log_management.add_log(2, "KEGELN_RUN", "kegeln.exe", "Kegeln.exe run")

    def __set_working_directory(self) -> None:
        if hasattr(sys, 'frozen'):
            exe_directory = os.path.dirname(sys.executable)
        else:
            exe_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(exe_directory)
        self.__log_management.add_log(0, "DIR_SET", "", "Katalog domowy to {}".format(exe_directory))


Program()
