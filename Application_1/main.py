from com_port_creator import ComPortCreator
from connection_manager import ConnectionManager
from log_management import LogManagement
import config_reader


class Program:
    def __init__(self):
        print("Start:")
        try:
            self.__config = config_reader.get_configurations()
            self.__com_result = self.__ports_com_management()
            if self.__com_result == 0:
                print("Jeżeli program 'Kegeln' jest uruchomiony, to jest wszystko OK")
            elif self.__com_result == 1:
                print("Wirtualne porty zostały utworzone")
            elif self.__com_result == 2:
                print("Wirtualne porty już istniały")
            self.__log_management = LogManagement(self.__config["minimum_number_of_lines_to_write_in_log_file"])
            self.__on_add_log = lambda new_log: self.__log_management.add_log(new_log)

            ConnectionManager(self.__config["com_x"], self.__config["com_y"], self.__config["com_timeout"],
                              self.__config["com_write_timeout"], self.__on_add_log)

            self.__log_management.close_log_file()
        except Exception as e:
            print(e)

        while True:
            pass

    def __ports_com_management(self):
        """
        This method checks if the ports exists and if there is a connection between those ports

        :return:
            2 if ports exist [OK]
            1 if ports com_y and com_z did not exist, but were created [OK]
            0 if not exists port com_z, but exists com_y [WARNING, maybe other program is now turn on]

        :raise:
            if not exists port com_y, but exists com_z [CRITICAL, because this program will be try connect to com_y]
            if ports exists, but not exits connection between this ports [CRITICAL]
            if not exists com_x [CRITICAL]
            error when program tried to create ports [CRITICAL]
        """
        path_to_com0com = self.__config["path_to_dict_com0com"]
        com_x, com_y, com_z = self.__config["com_x"], self.__config["com_y"], self.__config["com_z"]
        com_port_manager = ComPortCreator(com_x, com_y, com_z, path_to_com0com)
        port_exists = com_port_manager.create_ports()
        return port_exists


Program()
