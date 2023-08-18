"""This module can check if ports com exists and create com ports"""
import serial
import subprocess
from typing import Tuple


class SerialPortManagementError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__()


class SerialPortManager:
    """
    This class checks if com_x, com_y and com_z exist, if com_y and com_z don't exist it tries to create them.
    The class checks if the ports are free and if there is a connection between com_y and com_z.

    functions:
        port_com_management() -> Tuple[int, str]
    """
    def __init__(self, config: dict):
        """
        :param config: dict with configuration from config.json
        """
        self.__config = config

    def ports_com_management(self) -> Tuple[int, str]:
        """
        This method checks if the ports exists and if there is a connection between those ports

        :return:
            [int, str] - int is code, str is message
            code list:
                2 if ports exist [OK]
                1 if ports com_y and com_z did not exist, but were created [OK]
                0 if not exists port com_z, but exists com_y [WARNING, maybe other program is now turn on]

        :raises:
            SerialPortManagementError:
                1 - Not exist COM_X or is busy
                2 - Failed to create ports COM_Y COM_Z
                3 - Not exist COM_Y or is busy
                4 - Not exist connection between COM_Y and COM_Z
                5 - Other Exception
        """
        try:
            path_to_com0com = self.__config["path_to_dict_com0com"]
            com_x, com_y, com_z = self.__config["com_x"], self.__config["com_y"], self.__config["com_z"]
            port_exists = self.__check_and_prepare_ports(com_x, com_y, com_z, path_to_com0com)
            if port_exists == 0:
                return 0, "Porty COM_X={}, COM_Y={}, COM_Z={} istnieją, COM_Z jest zajęty, ale jeżeli " \
                          "program 'Kegeln' jest uruchomiony, to jest wszystko OK".format(com_x, com_y, com_z)
            if port_exists == 1:
                return 1, "Porty COM_X={}, COM_Y={}, COM_Z={} są dostępne, para COM_Y<->COM_Z została utworzona".format(
                                                                                                    com_x, com_y, com_z)
            return port_exists, "Porty COM_X={}, COM_Y={}, COM_Z={} są dostępne".format(com_x, com_y, com_z)
        except SerialPortManagementError:
            raise
        except Exception as e:
            raise SerialPortManagementError(5, e)

    def __check_and_prepare_ports(self, com_x: str, com_y: str, com_z: str, path_to_com0com: str) -> int:
        """
        This method checks if the ports exists and if there is a connection between those ports

        :param com_x: <str> - name computer port
        :param com_y: <str> - name virtual port to connect with Kegeln
        :param com_z: <str> - the name of the virtual port to which Kegeln will connect
        :param path_to_com0com: <str> path to folder with com0com program

        :return:
            2 if ports exist [OK]
            1 if ports com_y and com_z did not exist, but were created [OK]
            0 if not exists port com_z, but exists com_y [WARNING, maybe other program is now turn on]

        :raises:
            SerialPortManagementError:
                1 - if not exists port com_y, but exists com_z [CRITICAL this program will be try connect to com_y]
                2 - if ports exists, but not exits connection between this ports [CRITICAL]
                3 - if not exists com_x [CRITICAL]
                4 - error when program tried to create ports [CRITICAL]
        """
        exist_x = self.__check_exist_port(com_x)
        exist_y = self.__check_exist_port(com_y)
        exist_z = self.__check_exist_port(com_z)
        if not exist_x:
            raise SerialPortManagementError(1, "Nie istnieje port " + com_x + "lub jest zajęty")
        if not exist_y and not exist_z:
            if self.__create_virtual_ports(com_y, com_z, path_to_com0com):
                return 1
            else:
                raise SerialPortManagementError(2, "Nie udało się utworzyć pary portów " + com_y + "-" + com_z)
        if exist_y and not exist_z:
            return 0
        if not exist_y and exist_z:
            raise SerialPortManagementError(3, "Nie istnieje port " + com_y + "lub jest zajęty")
        if not self.__check_if_exist_connection_between_ports(com_y, com_z):
            raise SerialPortManagementError(4, "Nie ma połączenia między portami " + com_y + " a " + com_z)
        return 2

    @staticmethod
    def __check_exist_port(com_name: str) -> bool:
        """
        This method checks if there is a com port named 'com_name'

        :param com_name: the name of the checked port
        :return: True if port exists, otherwise False
        """
        try:
            ser = serial.Serial(com_name)
            ser.close()
            return True
        except serial.SerialException:
            return False

    @staticmethod
    def __create_virtual_ports(com_y: str, com_z: str, path: str) -> bool:
        """
        This method tries to create virtual ports

        :param com_y: <str> - name first virtual port
        :param com_z: <str> - name second virtual port
        :param path: <str> path to folder with com0com program

        :return: True - when ports was created, False if was error
        """
        try:
            command = 'cd "' + path + '" && setupc install PortName=' + com_y + " PortName=" + com_z
            subprocess.call(command, shell=True)
            return True
        except Exception:
            return False

    @staticmethod
    def __check_if_exist_connection_between_ports(com_y: str, com_z: str) -> bool:
        """
        This method checks if there is connection between the com_y port and com_z port

        :param com_y: name com port
        :param com_z: name com port

        :return: True if port-to-port connection exists, False otherwise
        """
        try:
            ser1 = serial.Serial(com_y, write_timeout=1)
            ser2 = serial.Serial(com_z, timeout=1)

            message = "The only right bowling have nine-pins not ten-pins!"
            ser1.write(message.encode('utf-8'))

            received_data = ser2.read(len(message))
            received_message = received_data.decode('utf-8')

            ser1.close()
            ser2.close()

            return message == received_message
        except serial.SerialException:
            return False
