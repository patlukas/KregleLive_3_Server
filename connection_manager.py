"""This module is responsible for data transfer"""
from typing import List

import select
import time

import serial
import socket

from com_manager import ComManager


# class ConnectionManagerError(Exception):
#     def __init__(self, code, message):
#         self.code = code
#         self.message = message
#         super().__init__()


class ConnectionManager:
    def __init__(self, com_name_x: str, com_name_y: str, com_timeout, com_write_timeout: float, on_add_log,
                 ip_addr: str, port: int, time_interval_break: float):
        """
        :param com_name_x: <str> name of COM port to get information from 9pin machine, e.g. "COM1"
        :param com_name_y: <str> name of COM port to get information from computer application, e.g. "COM2"
        :param com_timeout: <float | int> maximum waiting time for downloading information from the COM port
        :param com_write_timeout: <float | int> maximum waiting time for sending information to the COM port
        :param on_add_log: <func> a function for saving the transmitted information in a log file
        :param ip_addr: <str> the IP address of the server (this computer).
        :param port: port which be used to communication via socket
        :param time_interval_break: length of time to wait after the end of the communication loop

        :raise
            ComManagerError
        """
        self.__com_x = ComManager(com_name_x, com_timeout, com_write_timeout, "COM_X", on_add_log)
        self.__com_y = ComManager(com_name_y, com_timeout, com_write_timeout, "COM_Y", on_add_log)
        # com_port_x = serial.Serial(com_name_x, 9600, timeout=com_timeout, write_timeout=com_write_timeout)
        # com_port_y = serial.Serial(com_name_y, 9600, timeout=com_timeout, write_timeout=com_write_timeout)
        # self.__com_x = {"port": com_port_x, "data_to_send": b"", "data_to_recv": b"", "number_received_bytes": 0, "name": "COM_X"}
        # self.__com_y = {"port": com_port_y, "data_to_send": b"", "data_to_recv": b"", "number_received_bytes": 0, "name": "COM_Y"}
        self.__sockets = {}
        self.__ip_address = ip_addr
        self.__port = port
        self.__server_socket = None
        self.__not_sent_data_to_socket = b''
        self.__on_add_log = on_add_log
        self.__is_run = False
        self.__time_interval_break = time_interval_break
        self.__on_add_log(2, "COM_INFO", "", "COM_X={}, COM_Y={}".format(com_name_x, com_name_y))

    def start(self) -> None:
        """
        This method starts transferring data
        :return: None
        """
        self.__is_run = True
        while self.__is_run:
            self.__com_reader(self.__com_x, self.__com_y, self.__sockets)
            self.__com_reader(self.__com_y, self.__com_x, self.__sockets)
            self.__com_x.send()
            self.__com_y.send()
            # self.__com_sender(self.__com_x)
            # self.__com_sender(self.__com_y)
            self.__socket_manager()
            time.sleep(self.__time_interval_break)

    def stop(self) -> None:
        """
        This method stop transferring data
        :return: None
        """
        self.__is_run = False

    def close(self) -> None:
        """
        This method close every open ports and sockets
        :return: None
        """
        self.__com_x.close()
        self.__com_y.close()
        for socket_el in self.__sockets:
            self.__socket_close_connection(socket_el)

    def get_info(self) -> List[List[str]]:
        """
        This method returned info about connection
        :return: list[list[name port: str, number recv data: str]]
        """
        data = [
            [self.__com_x.get_alias(), str(self.__com_x.get_number_received_bytes())],
            [self.__com_y.get_alias(), str(self.__com_y.get_number_received_bytes())]
        ]
        for key in self.__sockets.keys():
            data.append([str(key.getsockname()), str(self.__sockets[key]["number_received_bytes"])])
        return data

    def __com_reader(self, com_in: ComManager, com_out: ComManager, sockets: dict) -> int:
        """
        This method reads data from the "com_in" port. It then adds the read data to the queue with data to be sent in
        'com_out' and adds that data to the send queue on all sockets, or if there are no open sockets at that moment,
        it adds that data to the waiting queue.

        :param com_in: <ComManager> object with a COM port from which this function will read data
        :param com_out: <ComManager> with COM port where this func will add read data to the queue with data to be sent
        :param sockets <{port: {data_to_send, number_received_bytes}, ...}>
                        port - <socket.socket> - object COM port
                        data_to_send - <str> binary text with data to send
                        number_received_bytes - <int> - number of received bytes

        :return: The number of data bytes received or -1 if there was an error
        """
        try:
            received_bytes = com_in.read()
            if received_bytes == b"":
                return 0
            com_out.add_bytes_to_send(received_bytes)
            if len(sockets):
                for key in sockets:
                    sockets[key]["data_to_send"] += received_bytes
            else:
                self.__not_sent_data_to_socket += received_bytes
            return len(received_bytes)
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            self.__on_add_log(10, "COM_READ_ERROR", com_in.get_alias(), e)
            return -1

    # def __com_sender(self, com_out: dict) -> int:
    #     """
    #     This method will try to send data to the com_out port
    #
    #     :param com_out: <{port, data_to_send, number_received_bytes}> dict with port to send data
    #                     port - <serial.Serial> - object COM port
    #                     data_to_send - <str> binary text with data to send
    #                     number_received_bytes - <int> - number of received bytes
    #     :return: Number of data bytes sent or -1 means there was an error
    #     """
    #     if com_out["data_to_send"] == b'':
    #         return 0
    #
    #     position_special_sign = com_out["data_to_send"].rfind(b"\r")
    #     if position_special_sign == -1:
    #         return 0
    #
    #     if com_out["port"].out_waiting == 0:
    #         try:
    #             bytes_sent = com_out["port"].write(com_out["data_to_send"][:position_special_sign+2])
    #             sent_data = com_out["data_to_send"][:bytes_sent]
    #             com_out["data_to_send"] = com_out["data_to_send"][bytes_sent:]
    #
    #             self.__on_add_log(4, "COM_SEND", com_out["name"], sent_data)
    #             return bytes_sent
    #         except serial.SerialTimeoutException as e:
    #             self.__on_add_log(1, "COM_SEND_TOUT", com_out["name"], str(e))
    #             return -1
    #     return 0

    def __socket_manager(self) -> bool:
        """
        Manages socket operations including accepting new connections, receiving and sending data.

        :return: True - if Ok, False if was error
        """
        try:
            if self.__server_socket is None:
                self.__socket_create_server()
            list_all_client_socket = list(self.__sockets.keys())
            if self.__server_socket is None:
                list_socket_to_recv = list(self.__sockets.keys())
            else:
                list_socket_to_recv = [self.__server_socket] + list_all_client_socket
            socket_read, socket_write, _ = select.select(list_socket_to_recv, list_all_client_socket, [], 0)
            for socket_el in socket_read:
                if socket_el == self.__server_socket:
                    self.__socket_accept()
                else:
                    self.__socket_recv(socket_el)
            for socket_el in socket_write:
                self.__socket_send(socket_el)
            return True
        except (socket.error, OSError, select.error) as e:
            self.__on_add_log(10, "SKT_MNGR_ERROR", "", e)
        except Exception as e:
            self.__on_add_log(10, "SKT_MNGR_ERR_2", "", e)
        return False

    def __socket_create_server(self) -> None:
        """
        This method create server socket port.

        :return: None
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (self.__ip_address, self.__port)
            server_socket.bind(server_address)
            server_socket.listen(5)
            self.__server_socket = server_socket
        except (socket.error, OSError) as e:
            self.__on_add_log(10, "SKT_CREA_ERROR", "", e)

    def __socket_close_connection(self, socket_el: socket.socket) -> None:
        """
        This method close socket port and remove from self.__sockets

        :param socket_el: <socket.socket> socket port witch will be closed
        :return: None
        """
        removed = self.__sockets.pop(socket_el, None)
        address = socket_el.getsockname()
        if removed is not None and len(self.__sockets) == 0:
            self.__not_sent_data_to_socket = removed["data_to_send"]
        self.__on_add_log(6, "SKT_CLSE", address, "")
        socket_el.close()

    def __socket_accept(self) -> bool:
        """
        Accepts a connection from a client and performs necessary setup.

        :return: True - client socket successfully accepted, False - there was an error while accepting
        """
        try:
            client_socket, client_address = self.__server_socket.accept()
            client_socket.setblocking(False)
        except (socket.error, OSError, socket.timeout) as e:
            self.__on_add_log(10, "SKT_ACPT_ERROR", "", e)
            return False

        self.__sockets[client_socket] = {"data_to_send": self.__not_sent_data_to_socket, "number_received_bytes": 0}
        self.__not_sent_data_to_socket = b''

        self.__on_add_log(6, "SKT_ACPT", client_address, "")
        return True

    def __socket_recv(self, socket_el: socket.socket) -> int:
        """
        This method try receive data from client socket port.

        :param socket_el: <socket.socket> socket port from which data will be received
        :return: <int>  -2 - was error, so socket was closed
                        -1 - the port was closed
                        0 - port is closed now
                        more then 0 - number of the received data
        """
        if socket_el not in self.__sockets:
            return -1

        client_address = socket_el.getsockname()
        try:
            data = socket_el.recv(1024)
        except (socket.error, OSError) as e:
            self.__on_add_log(10, "SKT_RECV_ERROR", client_address, e)
            self.__socket_close_connection(socket_el)
            return -2

        if len(data) == 0:
            self.__socket_close_connection(socket_el)
            self.__on_add_log(10, "SKT_RECV_CLOSE", client_address, "")
            return 0

        self.__com_x["data_to_send"] += data
        self.__sockets[socket_el]["number_received_bytes"] += len(data)
        self.__on_add_log(5, "SKT_RECV", client_address, str(data))
        return len(data)

    def __socket_send(self, socket_el: socket.socket) -> int:
        """
        This method try send data to socket port.

        :param socket_el: <socket.socket> socket port to which data will be sent
        :return: <int>  -2 -  was error, so socket was closed
                        -1 - the port is closed
                        0  - there is no data to send
                        >0 - number of sent bits
        """
        if socket_el not in self.__sockets:
            return -1
        if len(self.__sockets[socket_el]["data_to_send"]) == 0:
            return 0

        position_special_sign = self.__sockets[socket_el]["data_to_send"].rfind(b"\r")
        if position_special_sign == -1:
            return 0

        client_address = socket_el.getsockname()
        try:
            number_sent_bits = socket_el.send(self.__sockets[socket_el]["data_to_send"][:position_special_sign+2])
        except (socket.error, OSError) as e:
            self.__on_add_log(10, "SKT_SEND_ERROR", client_address, e)
            self.__socket_close_connection(socket_el)
            return -2

        sent_data = self.__sockets[socket_el]["data_to_send"][:number_sent_bits]
        self.__sockets[socket_el]["data_to_send"] = self.__sockets[socket_el]["data_to_send"][number_sent_bits:]

        self.__on_add_log(3, "SKT_SEND", client_address, sent_data)
        return number_sent_bits

    def on_send_message(self, message: str, addressee_is_lane: bool):
        if type(message) == str:
            message = str.encode(message)
        if addressee_is_lane:
            self.__com_x["data_to_send"] += message
        else:
            self.__com_y["data_to_send"] += message

        if len(self.__sockets):
            for key in self.__sockets:
                self.__sockets[key]["data_to_send"] += message
        else:
            self.__not_sent_data_to_socket += message
