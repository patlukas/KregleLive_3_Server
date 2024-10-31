"""This module is responsible for data transfer"""
import time
import serial
from typing import List

from com_manager import ComManager
from sockets_manager import SocketsManager


class ConnectionManager:
    """

        Logs:
            CON_READ_ERROR - 10 - error when reading data from the port
            CON_CLOSE - 8 - Com and socket ports have been closed
            CON_STOP - 7 - Communication has been stopped
            CON_START - 7 - Communication has been started
            CON_INFO - 2 - COM port number information
            CON_SCQU - 2 - Clear queue unsent data from socket objct (Socket Clear QUeue)

        :raise
            ComManagerError
            SocketsManagerError
    """
    def __init__(self, com_name_x: str, com_name_y: str, com_timeout, com_write_timeout: float, on_add_log,
                 time_interval_break: float):
        """
        :param com_name_x: <str> name of COM port to get information from 9pin machine, e.g. "COM1"
        :param com_name_y: <str> name of COM port to get information from computer application, e.g. "COM2"
        :param com_timeout: <float | int> maximum waiting time for downloading information from the COM port
        :param com_write_timeout: <float | int> maximum waiting time for sending information to the COM port
        :param on_add_log: <func> a function for saving the transmitted information in a log file
        :param time_interval_break: length of time to wait after the end of the communication loop

        :logs: CON_INFO (2)
        :raise
            ComManagerError
            SocketsManagerError
        """
        self.__com_x = ComManager(com_name_x, com_timeout, com_write_timeout, "COM_X", on_add_log)
        self.__com_y = ComManager(com_name_y, com_timeout, com_write_timeout, "COM_Y", on_add_log)
        self.__sockets = SocketsManager(on_add_log)
        self.__on_add_log = on_add_log
        self.__is_run = False
        self.__time_interval_break = time_interval_break
        self.__on_add_log(2, "CON_INFO", "", "COM_X={}, COM_Y={}".format(com_name_x, com_name_y))

    def start(self) -> None:
        """
        This method starts transferring data
        :return: None
        :logs: CON_START (7)
        """
        self.__on_add_log(7, "CON_START", "", "Communication has been started")
        self.__is_run = True
        while self.__is_run:
            self.__com_reader(self.__com_x, self.__com_y, self.__sockets)
            self.__com_reader(self.__com_y, self.__com_x, self.__sockets)
            self.__com_x.send()
            self.__com_y.send()
            bytes_to_send_to_com_x = self.__sockets.communications()
            if bytes_to_send_to_com_x != b"":
                self.__com_x.add_bytes_to_send(bytes_to_send_to_com_x)
            time.sleep(self.__time_interval_break)

    def stop(self) -> None:
        """
        This method stop transferring data
        :return: None
        :logs: CON_STOP (7)
        """
        self.__on_add_log(7, "CON_STOP", "", "Communication has been stopped")
        self.__is_run = False

    def close(self) -> None:
        """
        This method close every open ports and sockets
        :return: None
        :logs: CON_CLOSE (8)
        """
        self.__on_add_log(8, "CON_CLOSE", "", "Com and socket ports have been closed")
        self.__com_x.close()
        self.__com_y.close()
        self.__sockets.close()

    def get_info(self) -> List[List[str]]:
        """
        This method returned info about connection
        :return: list[list[name port: str, number recv communicates: str, number recv data: str]]
        """
        com_info = []
        for com in [self.__com_x, self.__com_y]:
            com_info.append(
                [
                    com.get_alias(),
                    str(com.get_number_received_communicates()),
                    str(com.get_number_received_bytes())
                ]
            )
        return com_info + self.__sockets.get_info()

    def __com_reader(self, com_in: ComManager, com_out: ComManager, sockets: SocketsManager) -> int:
        """
        This method reads data from the "com_in" port. It then adds the read data to the queue with data to be sent in
        'com_out' and sockets queue.

        :param com_in: <ComManager> object with a COM port from which this function will read data
        :param com_out: <ComManager> with COM port where this func will add read data to the queue with data to be sent
        :param sockets <SocketManager> obj to management socket connection

        :return: The number of data bytes received or -1 if there was an error
        :logs: CON_READ_ERROR (10)
        """
        try:
            received_bytes = com_in.read()
            if received_bytes == b"":
                return 0
            com_out.add_bytes_to_send(received_bytes)
            sockets.add_bytes_to_send(received_bytes)
            return len(received_bytes)
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            self.__on_add_log(10, "CON_READ_ERROR", com_in.get_alias(), e)
            return -1

    def on_clear_sockets_queue(self) -> int:
        """
        This method clear queue with unsent data has been cleared

        :return: <int> number of deleted bytes
        :logs: CON_SCQU (2)
        """
        self.__on_add_log(2, "CON_SCQU", "", "Queue with unsent data will be cleared")
        return self.__sockets.on_clear_queue()

    def on_create_server(self, ip, port):
        """
        This method create server TCP

        :param ip_addr: <str> server ip address
        :param port: <int> port where server will listen (0-65535)
        :return: True
        :raise: SocketsManagerError
        """
        self.__sockets.create_server(ip, port)

    def on_close_server(self):
        """
        This method close server.

        :return: True - closing was ended successfully, False - was error while closing server socket
        """
        self.__sockets.close()

    def on_get_list_ip(self):
        """
        This method give list of available IP on computer

        :return: <list[str]> list of available IP on computer
        """
        return self.__sockets.get_list_ip()