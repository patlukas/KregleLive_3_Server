"""This module is responsible for data transfer"""
import serial


class ConnectionManager:
    def __init__(self, com_x: str, com_y: str, com_timeout, com_write_timeout, on_add_log):
        """

        :param com_x: <str> name of COM port to get information from 9pin machine
        :param com_y: <str> name of COM port to get information from computer application
        :param com_timeout: <float | int> maximum waiting time for downloading information from the COM port
        :param com_write_timeout: <float | int> maximum waiting time for sending information to the COM port
        :param on_add_log: <func> a function for saving the transmitted information in a log file
        """
        self.__com_port_x = serial.Serial(com_x, 9600, timeout=com_timeout, write_timeout=com_write_timeout)
        self.__com_port_y = serial.Serial(com_y, 9600, timeout=com_timeout, write_timeout=com_write_timeout)
        self.__on_add_log = on_add_log
        self.__is_run = False
        self.start()

    def start(self) -> None:
        """
        This method starts transferring data
        :return: None
        """
        self.__is_run = True
        while self.__is_run:
            self.__com_reader(self.__com_port_x, self.__com_port_y)
            self.__com_reader(self.__com_port_y, self.__com_port_x)

    def stop(self) -> None:
        """
        This method stop transferring data
        :return: None
        """
        self.__is_run = False

    def __com_reader(self, com_port_in: serial.Serial, com_port_out: serial.Serial) -> bool:
        """
        This method reads data from com_port_in adn and then displays this data in the console, writes this data to a
        log file and sends this data to com_port_out

        :param com_port_in: <serial.Serial> port from which the method will try to read data
        :param com_port_out: <serial.Serial> port where the method will try to write data
        :return: True if data has been read, False otherwise
        """
        data = com_port_in.readline()
        if data != b"":
            print(data)
            write_success = 1
            try:
                com_port_out.write(data)
            except serial.SerialTimeoutException as e:
                print(e)
                write_success = 0
            self.__on_add_log("{}->{}\t{}\t{}".format(com_port_in.name, com_port_out.name, write_success, data))
            return True
        return False
