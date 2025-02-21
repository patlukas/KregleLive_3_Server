"""This module is responsible for data transfer"""
import time
import serial
from typing import List

from com_manager import ComManager
from sockets_manager import SocketsManager


class ConnectionManager:
    """

        Logs:
            CON_ERROR_WAIT - 10 - alarmingly long wait for response
            CON_WAIT_LONG - 10 - too long to wait for a response, so another message was sent
            CON_READ_ERROR - 10 - error when reading data from the port
            CON_CLOSE - 8 - Com and socket ports have been closed
            CON_STOP - 7 - Communication has been stopped
            CON_START - 7 - Communication has been started
            CON_WAIT_END - 6 - however, a belated message has arrived
            CON_INFO - 2 - COM port number information
            CON_SCQU - 2 - Clear queue unsent data from socket objct (Socket Clear QUeue)

        :raise
            ComManagerError
            SocketsManagerError
    """
    def __init__(self, com_name_x: str, com_name_y: str, com_timeout, com_write_timeout: float, on_add_log,
                 time_interval_break: float, max_waiting_time_for_response: float, warning_response_time: float):
        """
        :param com_name_x: <str> name of COM port to get information from 9pin machine, e.g. "COM1"
        :param com_name_y: <str> name of COM port to get information from computer application, e.g. "COM2"
        :param com_timeout: <float | int> maximum waiting time for downloading information from the COM port
        :param com_write_timeout: <float | int> maximum waiting time for sending information to the COM port
        :param on_add_log: <func> a function for saving the transmitted information in a log file
        :param time_interval_break: <float> length of time to wait after the end of the communication loop
        :param max_waiting_time_for_response: <float> time in seconds, after which, if the lane does not respond, we will send another
        :param warning_response_time: <float> time in seconds after which program will inform about the alarmingly long waiting time for a response

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
        self.__max_waiting_time_for_response = max_waiting_time_for_response
        self.__warning_response_time = warning_response_time
        self.__on_add_log(2, "CON_INFO", "", "COM_X={}, COM_Y={}".format(com_name_x, com_name_y))

    def start(self) -> None:
        """
        This method starts transferring data
        :return: None
        :logs: CON_ERROR_WAIT (10), CON_WAIT_LONG (10), CON_START (7), CON_WAIT_END (6)
        """
        self.__on_add_log(7, "CON_START", "", "Communication has been started")

        time_next_sending_x = time.time() + 1.5
        time_last_sending_x = 0
        last_sent_x = b""

        self.__is_run = True
        while self.__is_run:
            if time_last_sending_x > 0 and time.time() > time_last_sending_x + self.__warning_response_time:
                self.__on_add_log(10, "CON_WAIT_LONG", "COM_X", "Długie oczekiwanie na odpowiedź na: " + str(last_sent_x))
                time_last_sending_x = -1

            recv_bytes_x, recv_msg_x = self.__com_reader(self.__com_x, self.__com_y, self.__sockets)

            if recv_bytes_x > 0:
                if time_last_sending_x == -1:
                    self.__on_add_log(6, "CON_WAIT_END", "COM_X", "Przyszła odpowiedź na: " + str(last_sent_x))
                time_next_sending_x = 0
                time_last_sending_x = 0

            self.__com_reader(self.__com_y, self.__com_x, self.__sockets)
            self.__com_y.send()

            if time.time() >= time_next_sending_x:
                if time_next_sending_x > 0 and last_sent_x != b"":
                    self.__on_add_log(10, "CON_ERROR_WAIT", "COM_X", "Oczekiwanie na tyle długie, że zostanie wysłana nowa wiadomość. Ostatnio wysłana: " + str(last_sent_x))
                    time_next_sending_x = 0
                sent_bytes_x, sent_msg_x = self.__com_x.send()

                if sent_bytes_x > 0:
                    time_next_sending_x = time.time() + self.__max_waiting_time_for_response
                    time_last_sending_x = time.time()
                    last_sent_x = sent_msg_x
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
                    str(com.get_number_received_bytes()),
                    str(com.get_number_of_waiting_messages_to_send())
                ]
            )
        return com_info + self.__sockets.get_info()

    def __com_reader(self, com_in: ComManager, com_out: ComManager, sockets: SocketsManager) -> (int, bytes):
        """
        This method reads data from the "com_in" port. It then adds the read data to the queue with data to be sent in
        'com_out' and sockets queue.

        :param com_in: <ComManager> object with a COM port from which this function will read data
        :param com_out: <ComManager> with COM port where this func will add read data to the queue with data to be sent
        :param sockets <SocketManager> obj to management socket connection

        :return: <int, bytes> The number of data bytes received or -1 if there was an error, received bytes
        :logs: CON_READ_ERROR (10)
        """
        try:
            received_bytes = com_in.read()
            if received_bytes == b"":
                return 0, b""
            com_out.add_bytes_to_send(received_bytes)
            sockets.add_bytes_to_send(received_bytes)
            return len(received_bytes), received_bytes
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            self.__on_add_log(10, "CON_READ_ERROR", com_in.get_alias(), e)
            return -1, b""

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