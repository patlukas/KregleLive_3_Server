import socket
import select
from typing import Tuple


class SocketsManagerError(Exception):
    """
    List code:
        11-000 - TypeError - wrong type of variable
        11-001 - OSError - general error when creating server socket, e.g. port and address is occurred
        11-002 - OverflowError error when creating server socket, it is when was give port number out of range (0-65535)
        11-003 - TypeError - error when creating server socket, it is when was give variable which has wrong type
        11-004 - PortError - error when server port number is out of range, must be from range 0-65535
    """
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__()


class SocketsManager:
    """
        This class is used to manage sockets communication.

        Logs:
            SKT_ACPT_ERROR - 10 - An error occurred while connecting the new client (AkCePT new socket ERROR)
            SKT_MNGR_ERROR - 10 - Error occurred while managing socket connections 
            SKT_MNGR_ERR_2 - 10 - Unexpected error occurred while managing socket connections (error should not occur)
            SKT_RECV_ERROR - 10 - An error occurred while recv data (RECeiVed data)
            SKT_CLSC_ERROR - 10 - Error occurred while trying close socket (CLose Socket Client ERROR)
            SKT_CLSS_ERROR - 10 - Error occurred while trying close server socket (CLose Socket Server)
            SKT_CCSS_ERROR - 10 - Error occurred while trying close closed server socket (Close Closed Socket Server)
            SKT_SEND_ERROR - 10 - An error occurred while send data (SEND data ERROR)
            SKT_ATST_ERROR - 10 - Wrong data type specified for sending (Add data To Send - Type ERROR)
            SKT_ATSE_ERROR -  10 - Wrong last sign. Must be '\r' (Add data To Send - End sign ERROR)
            SKT_ATSL_ERROR -  10 - New message must has minimum one byte (Add data To Send - Length ERROR)
            SKT_CQUE - 8 - Queue with not send data has been cleared (Cleared QUEue)
            SKT_EQUE - 8 - Queue with not send data was empty (Empty QUEue)
            SKT_RECV_CLOSE - 7 - While recv, class detected that the client socket was closed.
            SKT_ACPT - 6 - New client was connect (AkCePT new socket)
            SKT_CLSE - 6 - Socket has been closed (CLose Socket Clint)
            SKT_CLSS - 6 - Server socket has been closed (CLose Socket Server)
            SKT_RECV - 5 - Data successfully received (RECeiVed data)
            SKT_SEND - 3 - Data successfully sent (SENDed data)
            SKT_SRCD - 2 - Socket server was successfully created (SerweR CreateD)
            SKT_ATSD - 1 - Added new data to send queue in socket (Add To SenD)
            SKT_ATQE - 1 - Added new data to queue not send sata  (Add To QueuE)

        :raise SocketsManagerError:
    """
    def __init__(self, ip_addr: str, port: int, on_add_log):
        """
        :param ip_addr: <str> server ip address
        :param port: <int> server port
        :param on_add_log: <func(int,str,str,str)> function to add logs

        self.__on_add_log - same like in :param on_add_log:
        self.__sockets - <dict> key is descryptor, value is dict with fields:
                                - data_to_send - <bytes> waiting queue for send data
                                - data_to_recv - <bytes> waiting queue for recv, in this var socket wait to sign '\r'
                                - number_received_bytes - <int> number of recv bytes from data_to_recv
                                - number_received_communicates - <int> number of recv communicates from data_to_recv
        self.__server_socket - <socket.socket> object with server socket, via this socket client can connect with app
        self.__queue_not_sent_data - <bytes> if aren't any client socket, then every data to send will be there storage
        """
        self.__check_types([["ip_addr", ip_addr, [str]], ["port", port, [int]]])
        self.__check_port_number(port)
        self.__on_add_log = on_add_log
        self.__sockets = {}
        self.__server_socket = self.__create_server(ip_addr, port)
        self.__queue_not_sent_data = b''

    @staticmethod
    def __check_types(controlled_variables) -> None:
        """
        This method check types of variable, if variable has wrong type then throw error

        :param controlled_variables: <List<[str, value, List]>> List of list where in nested list is name of variable,
                                                                value of variable and list of expected types
        :raise SocketsManagerError: 11-000
        :return: None
         """
        for [name, value, expected_type] in controlled_variables:
            if type(value) not in expected_type:
                raise SocketsManagerError("11-000", "TypeError - variable '{}' must be one of [{}], but is {}"
                                          .format(name, type(value).__name__, str(expected_type)))

    @staticmethod
    def __check_port_number(port: int) -> True:
        """
        This method checks if the port number is in the range 0-65535

        :param port: <int> port number
        :return: <True> True - if port number if ok
        :raise SocketsManagerError: 11-004
        """
        if port < 0 or port > 65535:
            SocketsManagerError("11-004", "PortError - Server port number is out of range, "
                                          "must be from range 0-65535 is {}".format(port))
        return True

    def __create_server(self, ip_addr: str, port: int) -> socket.socket:
        """
        This method create server socket port.

        :param ip_addr: <str> server ip address
        :param port: <int> port where server will listen (0-65535)
        :return: <socket.socket> Object with created server socket
        :raise SocketsManagerError: 11-001, 11-002, 11-003
        :logs: SKT_SRCD (2)
        """
        try:
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_address = (ip_addr, port)
            server_socket.bind(server_address)
            server_socket.listen(5)
            server_socket.settimeout(1)
            self.__on_add_log(2, "SKT_SRCD", "", "Socket server: ip addr: {} port: {}".format(ip_addr, port))
            return server_socket
        except OSError as e:
            raise SocketsManagerError("11-001", "OSError - Error while create socket server | {}".format(e))
        except OverflowError as e:
            raise SocketsManagerError("11-002", "OverflowError - Error while create socket server - "
                                                "wrong number of port | {}".format(e))
        except TypeError as e:
            raise SocketsManagerError("11-003", "TypeError - Error while create socket server - "
                                                "wrong type of argument | {}".format(e))

    def get_info(self) -> list:
        """
        This method give list with primary information about every sockets with name ip addr and number of recv bytes.

        :return: <list<list<str, str, str>>> -   list of list, in nested list is two str,
                                                    first is ip addr or name
                                                    second is number of communicates,
                                                    third is number of recv bytes
        """
        result = []
        for key in list(self.__sockets.keys()):
            result.append([
                str(key.getsockname()),
                str(self.__sockets[key]["number_received_communicates"]),
                str(self.__sockets[key]["number_received_bytes"])
            ])
        result.append(["Kolejka", str(self.__queue_not_sent_data.count(b"\r")), str(len(self.__queue_not_sent_data))])
        return result

    def communications(self) -> bytes:
        """
        Manages socket operations including accepting new connections, receiving and sending data.

        :return: <bytes> all received data
        :logs: SKT_MNGR_ERROR (10), SKT_MNGR_ERR_2 (10)
        """
        received_data = b""
        try:
            all_skt_read, all_skt_write = list(self.__sockets.keys()), list(self.__sockets.keys())
            if self.__server_socket is not None:
                all_skt_read.append(self.__server_socket)
            if len(all_skt_write) + len(all_skt_read) == 0:
                return b""
            list_ready_to_read, list_ready_to_write, _ = select.select(all_skt_read, all_skt_write, [], 0)
            for socket_el in list_ready_to_read:
                if socket_el == self.__server_socket:
                    self.__accept_new_client()
                else:
                    received_data += self.__socket_recv(socket_el)[1]
            for socket_el in list_ready_to_write:
                self.__socket_send(socket_el)

        except OSError as e:
            self.__on_add_log(10, "SKT_MNGR_ERROR", "", "Error occurred while managing sockets connections "
                                                        "| {}".format(e))
        except Exception as e:
            self.__on_add_log(10, "SKT_MNGR_ERR_2", "", "Unexpected error occurred while managing socket "
                                                        "connections | {}".format(e))
        return received_data

    def __accept_new_client(self) -> bool:
        """
        Accepts a connection from a client and performs necessary setup.

        :return: <bool> True - client socket successfully accepted, False - there was an error while accepting
        :logs: SKT_ACPT_ERROR (10), SKT_ACPT (6)
        """
        try:
            client_socket, client_address = self.__server_socket.accept()
            client_socket.setblocking(False)
        except (socket.error, OSError, socket.timeout) as e:
            self.__on_add_log(10, "SKT_ACPT_ERROR", "", "An error occurred while "
                                                        "connecting the new client | {}".format(e))
            return False

        self.__sockets[client_socket] = {
            "data_to_send": self.__queue_not_sent_data,
            "data_to_recv": b"",
            "number_received_bytes": 0,
            "number_received_communicates": 0
        }
        self.__queue_not_sent_data = b''
        self.__on_add_log(6, "SKT_ACPT", client_address, "New socket client")
        return True

    def add_bytes_to_send(self, new_bytes_to_send: bytes) -> bool:
        """
        This method add to all send queues new message or if aren't any opened socket client, then add to waiting queue.
        Message must have sign "\r" on the end.

        :param new_bytes_to_send: <bytes> Bytes which will be add to send queue
        :return: <boot> True - successfully, False - was error
        :logs: SKT_ATST_ERROR (10), SKT_ATSL_ERROR (10), SKT_ATSE_ERROR (10), SKT_ATSD (1), SKT_ATQE (1)
        """
        # TODO Add limit queue
        if type(new_bytes_to_send) != bytes:
            self.__on_add_log(10, "SKT_ATST_ERROR", "", "Wrong type of data to send: '{}' have type '{}'"
                              .format(new_bytes_to_send, type(new_bytes_to_send).__name__))
            return False
        if len(new_bytes_to_send) == 0:
            self.__on_add_log(10, "SKT_ATSL_ERROR", "", "Wrong length of data to send, must send minimum one byte: '{}'"
                              .format(new_bytes_to_send))
            return False
        if new_bytes_to_send[-1:] != b"\r":
            self.__on_add_log(10, "SKT_ATSE_ERROR", "", "Wrong last sign of data to send, last sign must be '\\r': '{}'"
                              .format(new_bytes_to_send))
            return False
        if len(self.__sockets):
            for key in self.__sockets:
                self.__sockets[key]["data_to_send"] += new_bytes_to_send
                self.__on_add_log(1, "SKT_ATSD", key.getsockname(), "{}".format(new_bytes_to_send))
        else:
            self.__queue_not_sent_data += new_bytes_to_send
            self.__on_add_log(1, "SKT_ATQE", "", "{}".format(new_bytes_to_send))
        return True

    def __socket_recv(self, socket_el: socket.socket) -> Tuple[int, bytes]:
        """
        This method try receive data from client socket port.

        :param socket_el: <socket.socket> socket port from which data will be received
        :return: <List(int, bytes)>  bytes - received data
            int:
                -2 - was error, so socket was closed
                -1 - the port was closed
                0 - port is closed now
                1 - successfully
        :logs: SKT_RECV_ERROR (10), SKT_RECV_CLOSE (7), SKT_RECV (5)
        """
        if socket_el not in self.__sockets:
            return -1, b""

        client_address = socket_el.getsockname()
        try:
            data = socket_el.recv(1024)
        except OSError as e:
            self.__on_add_log(10, "SKT_RECV_ERROR", client_address, "An error occurred while recv data | {}".format(e))
            self.__socket_close(socket_el)
            return -2, b""

        if len(data) == 0:
            self.__socket_close(socket_el)
            self.__on_add_log(7, "SKT_RECV_CLOSE", client_address, "The socket connection was closed")
            return 0, b""

        if data == b"\r":
            self.__on_add_log(1, "SKT_RCVP", client_address, "Receive ping message")
            return 1, b""

        data_to_recv = self.__sockets[socket_el]["data_to_recv"] + data
        if b"\r" not in data_to_recv:
            index = 0
        else:
            index = data_to_recv.rindex(b"\r") + 1
        data_received = data_to_recv[:index]
        self.__sockets[socket_el]["data_to_recv"] = data_to_recv[index:]
        self.__sockets[socket_el]["number_received_bytes"] += len(data_received)
        self.__sockets[socket_el]["number_received_communicates"] += data_received.count(b"\r")
        self.__on_add_log(5, "SKT_RECV", client_address, str(data_received))
        return 1, data_received

    def __socket_send(self, socket_el: socket.socket) -> int:
        """
        This method try send data to socket port.

        :param socket_el: <socket.socket> socket port to which data will be sent
        :return: <int>  -2 -  was error, so socket was closed
                        -1 - the port is closed
                        0  - there is no data to send
                        >0 - number of sent bits
        :logs: SKT_SEND_ERROR (10), SKT_SEND (3)
        """
        if socket_el not in self.__sockets:
            return -1
        if b"\r" not in self.__sockets[socket_el]["data_to_send"]:
            return 0

        position_special_sign = self.__sockets[socket_el]["data_to_send"].rfind(b"\r")
        client_address = socket_el.getsockname()
        try:
            number_sent_bits = socket_el.send(self.__sockets[socket_el]["data_to_send"][:position_special_sign+2])
        except OSError as e:
            self.__on_add_log(10, "SKT_SEND_ERROR", client_address, "An error occurred while send data | {}".format(e))
            self.__socket_close(socket_el)
            return -2

        sent_data = self.__sockets[socket_el]["data_to_send"][:number_sent_bits]
        self.__sockets[socket_el]["data_to_send"] = self.__sockets[socket_el]["data_to_send"][number_sent_bits:]

        self.__on_add_log(3, "SKT_SEND", client_address, sent_data)
        return number_sent_bits

    def __socket_close(self, socket_el: socket.socket) -> bool:
        """
        This method close socket port and remove from self.__sockets

        :param socket_el: <socket.socket> socket port witch will be closed
        :return: <bool> True - closing was successful, False - was error
        :logs: SKT_CLSC_ERROR (10), SKT_CLSC (6)
        """
        address = socket_el.getsockname()
        removed = self.__sockets.pop(socket_el, None)
        if removed is not None and len(self.__sockets) == 0:
            self.__queue_not_sent_data = removed["data_to_send"]
        try:
            socket_el.close()
            self.__on_add_log(6, "SKT_CLSC", address, "Socket has been closed")
            return True
        except OSError as e:
            self.__on_add_log(10, "SKT_CLSC_ERROR", address, "Error occurred while trying close socket | {}".format(e))
            return False

    def close(self) -> bool:
        """
        This method close every sockets.

        :return: True - closing was ended successfully, False - was error while closing server socket
        :logs: SKT_CLSS_ERROR (10), SKT_CLSS (6)
        """
        for socket_el in list(self.__sockets.keys()):
            self.__socket_close(socket_el)

        if self.__server_socket is None:
            self.__on_add_log(10, "SKT_CCSS_ERROR", "", "Error occurred while trying close closed server socket")
            return False
        try:
            self.__server_socket.close()
            self.__server_socket = None
            self.__on_add_log(6, "SKT_CLSS", "", "Socket server has been closed")
            return True
        except OSError as e:
            self.__on_add_log(10, "SKT_CLSS_ERROR", "", "Error occurred while trying close socket server"
                                                        " | {}".format(e))
        return False

    def on_clear_queue(self) -> int:
        """
        This method clear queue with unsent data has been cleared

        :return: <int> number of deleted bytes
        :logs: SKT_CQUE (8), SKT_EQUE (8)
        """

        number_of_deleted_bytes = len(self.__queue_not_sent_data)
        if number_of_deleted_bytes > 0:
            self.__queue_not_sent_data = b""
            self.__on_add_log(8, "SKT_CQUE", "", "Queue with unsent data has been cleared")
        else:
            self.__on_add_log(8, "SKT_EQUE", "", "Queue with unsent data was empty")
        return number_of_deleted_bytes
