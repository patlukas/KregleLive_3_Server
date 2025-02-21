import serial
from typing import Union


class ComManagerError(Exception):
    """
    List code:
        "10-000" - wrong type of variable
        "10-001" - error during port creation, wrong parameters e.g. baud rate, data bits
        "10-002" - error during port creation, port not exists or is used
        "10-003" - trying to read data from an unopened port
        "10-004" - trying to send data to an unopened port
        "10-005" - trying to close unopened port
    """

    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__()


class ComManager:
    """
        This class is used to manage serial port communication.

        Logs:
            COM_READ_NOISE - 10 - noisy data was read
            COM_SEND_WTPE - 6 - invalid data type attempted to be added to the send queue
            COM_SEND_WEND - 6 - wrong end of data to send, should have '\r' as last sign
            COM_CLOSE - 6 - COM port have been closed
            COM_READ - 5 - read bytes from com port
            COM_SEND_inQUEUE - 5 - message is already in the queue to be sent, so it is discarded
            COM_SEND - 4 - sent bytes to com port
            COM_SEND_TOUT - 1 - timeout occurred while trying to send data
            COM_CREATE - 1 - COM port has been created

        :raise ComManagerError:
    """

    def __init__(self, port_name: str, timeout: Union[int, float, None],
                 write_timeout: Union[int, float, None], alias: str, on_add_log):
        """
        :param port_name: <str> name of port e.g. "COM1", "COM2"
        :param timeout: <int, float, None> waiting during send data
                        None -  wait forever (blocking mode)
                        0 -     non blocking mode, return immediately in any case
                        >0 -    returns immediately when the requested number of bytes are available, otherwise wait
                                until the timeout expires and return all bytes that were received until then.
        :param write_timeout: <int, float, None> waiting during received data (same options like in timeout)
        :param alias: <str> alternative port name, e.g. "COM_X", "COM_Y"
        :param on_add_log: <func(int,str,str,str)> function to add logs

        self.__port_name - same like in :param port_name:
        self.__alias - same like in :param alias:
        self.__bytes_to_send - <bytes> buffer with data witch waiting to send to com port
        self.__bytes_to_recv - <bytes> buffer with data witch waiting to recv
                                        (in this buffer is data until not recv sign '\r')
        self.__number_received_bytes - <int> number of bytes which was recv from self.__bytes_to_recv
        self.__number_received_communicates - <int> number of communicates which was recv from self.__bytes_to_recv
        self.__on_add_log - same like in :param on_add_log:
        self.__com_port - <serial.Serial, None>
                            - serial.Serial - opened com port to communicate
                            - None - closed or not open com port
        """
        self.__check_types([
            ["port_name", port_name, [str]],
            ["timeout", timeout, [int, float, None]],
            ["write_timeout", write_timeout, [int, float, None]],
            ["alias", alias, [str]]
        ])
        self.__port_name = port_name
        self.__alias = alias
        self.__bytes_to_send = b""
        self.__bytes_to_recv = b""
        self.__number_received_bytes = 0
        self.__number_received_communicates = 0
        self.__number_duplicates = 0
        self.__on_add_log = on_add_log
        self.__com_port = self.__create_port(timeout, write_timeout)

    @staticmethod
    def __check_types(controlled_variables) -> None:
        """
        This method check types of variable, if variable has wrong type then throw error
        :param controlled_variables: <List<[str, value, List]>> List of list where in nested list is name of variable,
                                                                value of variable and list of expected types

        :return: None
        :raise ComManagerError:
            10-000 - Wrong type of variable
        """
        for [name, value, expected_type] in controlled_variables:
            if type(value) not in expected_type:
                raise ComManagerError("10-000", "Error type - variable '{}' must be one of [{}], but is {}"
                                      .format(name, type(value).__name__, str(expected_type)))

    def __create_port(self, timeout: Union[float, None], write_timeout: Union[float, None]) -> serial.Serial:
        """
        This method return object created via serial.Serial, which has com port.

        :param timeout: <float, None> waiting during send data
                        None -  wait forever (blocking mode)
                        0 -     non blocking mode, return immediately in any case
                        >0 -    returns immediately when the requested number of bytes are available, otherwise wait
                                until the timeout expires and return all bytes that were received until then.
        :param write_timeout: <float, None> waiting during received data (same options like in timeout)
        :return: <serial.Serial> object with communicate port
        :logs: COM_CREATE (1)
        :raise ComManagerError: method will throw this raise, if was problem with create serial port
            10-001 - ValueError - e.g. wrong baud rate or data bits
            10-002 - SerialException - device can't be found or can't be configured
        """
        self.__on_add_log(1, "COM_CREATE", self.__alias, "COM port '{}' has been created".format(self.__alias))
        try:
            com_port = serial.Serial(self.__port_name, 9600, timeout=timeout, write_timeout=write_timeout)
            return com_port
        except ValueError as e:
            raise ComManagerError("10-001", "ValueError while create {} ({}) port: parameter are out of range, "
                                            "e.g. baud rate, data bits| {}".format(self.__port_name, self.__alias, e))
        except serial.SerialException as e:
            raise ComManagerError("10-002", "SerialException while create {} ({}) port: In case the device can not be "
                                            "found or can not be configured| {}"
                                  .format(self.__port_name, self.__alias, e))

    def get_alias(self) -> str:
        """
        This method return name alias of port, e.g. "COM_X"

        :return: <str> name alias
        """
        return self.__alias

    def read(self) -> bytes:
        """
        This method read bytes from com port.

        :return: <bytes> Received bytes form self.__bytes_to_recv with ended sign '\r'
        :logs: COM_READ_NOISE (10), COM_READ (5)
        :raise ComManagerError:
            10-003 - method will throw this raise, if port was be closed
        """
        if self.__com_port is None:
            raise ComManagerError("10-003", "Port {} ({}) is closed or not was be created, so I can't read data"
                                  .format(self.__port_name, self.__alias))

        in_waiting = self.__com_port.in_waiting
        if in_waiting == 0:
            return b""

        data_read = self.__com_port.read(in_waiting)
        self.__on_add_log(5, "COM_READ", self.__alias, data_read)
        self.__bytes_to_recv += data_read

        try:
            data_read.decode('Windows-1250')
        except UnicodeError:
            self.__on_add_log(10, "COM_READ_NOISE", self.__alias, data_read)

        if b"\r" not in self.__bytes_to_recv:
            return b""

        index = self.__bytes_to_recv.rindex(b"\r") + 1
        data_received, self.__bytes_to_recv = self.__bytes_to_recv[:index], self.__bytes_to_recv[index:]
        self.__number_received_bytes += len(data_received)
        self.__number_received_communicates += data_received.count(b"\r")
        return data_received

    def send(self) -> (int, bytes):
        """
        This method send to port bytes from self.__bytes_to_send.

        If buffer out_waiting isn't empty or in self.__bytes_to_send isn't sign '\r' then method is ending.
        This method will send only message which will be completed received, so it will send only messages witch will
        be ended with sign '\r'

        :return: <int, bytes> number of sent bytes or -1 if was error, and sent message
        :logs: COM_SEND (4), COM_SEND_TOUT (1)
        :raise ComManagerError:
            10-004 - method will throw this raise, if port was be closed
        """
        if self.__com_port is None:
            raise ComManagerError("10-004", "Port {} ({}) is closed or not was be created, so I can't send data"
                                  .format(self.__port_name, self.__alias))

        if self.__com_port.out_waiting > 0 or self.__bytes_to_send == b"" or b"\r" not in self.__bytes_to_send:
            return 0, b""

        try:
            index_first_special_sign = self.__bytes_to_send.index(b"\r") + 1
            number_sent_bytes = self.__com_port.write(self.__bytes_to_send[:index_first_special_sign])
            sent_bytes = self.__bytes_to_send[:number_sent_bytes]
            self.__bytes_to_send = self.__bytes_to_send[number_sent_bytes:]

            self.__on_add_log(4, "COM_SEND", self.__alias, sent_bytes)
            return len(sent_bytes), sent_bytes
        except serial.SerialTimeoutException as e:
            self.__on_add_log(1, "COM_SEND_TOUT", self.__alias, str(e))
            return -1, b""

    def add_bytes_to_send(self, new_bytes_to_send: bytes) -> int:
        """
        This method add to send queue new bytes.
        
        :param new_bytes_to_send: <bytes> Bytes which will be add to send queue
        :return: <int> Size of queue after add new bytes
        :logs: COM_SEND_WTPE (6), COM_SEND_WEND (6), COM_SEND_inQUEUE (5)
        """
        if type(new_bytes_to_send) != bytes:
            self.__on_add_log(6, "COM_SEND_WTPE", self.__alias, "Wrong type of data to send: '{}' have type '{}'"
                              .format(new_bytes_to_send, type(new_bytes_to_send).__name__))
        else:
            if new_bytes_to_send[-1:] != b"\r":
                self.__on_add_log(6, "COM_SEND_WEND", self.__alias,
                                  "Wrong end of data to send, should have '\r' as last sign: '{}'".format(
                                      new_bytes_to_send[-1:]))
            if new_bytes_to_send in self.__bytes_to_send:
                self.__on_add_log(5, "COM_SEND_inQUEUE", self.__alias, "Message '{}' is already in the queue to be sent, so it is discarded"
                                  .format(new_bytes_to_send))
                self.__number_duplicates += 1
            else:
                self.__bytes_to_send += new_bytes_to_send
        return len(self.__bytes_to_send)

    def get_number_received_bytes(self) -> int:
        """
        This method return number of received bytes from port.

        :return: <int> number of received bytes
        """
        return self.__number_received_bytes

    def get_number_received_communicates(self) -> int:
        """
        This method return number of received communicates from port.

        :return: <int> number of received communicates
        """
        return self.__number_received_communicates

    def get_number_of_waiting_messages_to_send(self) -> int:
        """
        This method return number of waiting messages to send

        :return: <int> number of waiting messages
        """
        return self.__bytes_to_send.count(b"\r")

    def get_number_of_duplicates(self) -> int:
        """
        This method return number of duplicate messages in queue to send

        :return: <int> number of duplicates
        """
        return self.__number_duplicates

    def close(self) -> None:
        """
        This method close serial port.

        :return: <None>
        :logs: COM_CLOSE (6)
        :raise ComManagerError:
            10-005 - method will throw this raise, if port was be closed
        """
        self.__on_add_log(6, "COM_CLOSE", self.__alias, "COM port {} have been closed".format(self.__alias))
        if self.__com_port is None:
            raise ComManagerError("10-005", "Port {} ({}) is closed or not was be created, so I can't close port"
                                  .format(self.__port_name, self.__alias))
        self.__com_port.close()
        self.__com_port = None
