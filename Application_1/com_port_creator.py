"""This module can check if ports com exists and create com ports"""
import serial
import subprocess


class ComPortCreator:
    """
        __init__(str, str, str, str)
        check_virtual_ports_exist() -> int
    """

    def __init__(self, com_x: str, com_y: str, com_z: str, path: str):
        """
        :param com_y: com port name (e.g. COM3) to which this application will connect
        :param com_z: com port name (e.g. COM4) to which the eavesdropped application will connect
        :param path: absolute path to directory with program com0com
        """
        self.__com_x = com_x
        self.__com_y = com_y
        self.__com_z = com_z
        self.__path = path

    def create_ports(self) -> int:
        """
        This method checks if the ports exists and if there is a connection between those ports

        :return:
            2 if ports exist [OK]
            1 if ports com_y and com_z did not exist, but were created [OK]
            0 if not exists port com_z, but exists com_y [WARNING, maybe other program is now turn on]

        :raise:
            ValueError - if not exists port com_y, but exists com_z [CRITICAL this program will be try connect to com_y]
            ConnectionError - if ports exists, but not exits connection between this ports [CRITICAL]
            ValueError - if not exists com_x [CRITICAL]
            ValueError - error when program tried to create ports [CRITICAL]
        """
        exist_x = self.__check_exist_port(self.__com_x)
        exist_y = self.__check_exist_port(self.__com_y)
        exist_z = self.__check_exist_port(self.__com_z)
        if not exist_x:
            raise ValueError("Nie istnieje port " + self.__com_x + "lub jest zajęty")
        if not exist_y and not exist_z:
            if self.__create_ports():
                return 1
            else:
                raise ValueError("Nie udało się utworzyć pary portów " + self.__com_y + "-" + self.__com_z)
        if exist_y and not exist_z:
            return 0
        if not exist_y and exist_z:
            raise ValueError("Nie istnieje port " + self.__com_y + "lub jest zajęty")
        if not self.__check_if_exist_connection_between_ports(self.__com_y, self.__com_z):
            raise ConnectionError("Nie ma połączenia między portami " + self.__com_y + " a " + self.__com_z)
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

    def __create_ports(self) -> bool:
        """
        This method tries to create virtual ports

        :return: True - when ports was created, False if was error
        """
        try:
            path = self.__path
            command = 'cd "' + path + '" && setupc install PortName=' + self.__com_y + " PortName=" + self.__com_z
            subprocess.call(command, shell=True)
            return True
        except Exception:
            return False
