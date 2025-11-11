"""This module is responsible for data transfer"""
import time
import serial
from typing import List

from com_manager import ComManager
from sockets_manager import SocketsManager


class ConnectionManager:
    """

        Logs:
            CON_ERROR_WAIT - 10 - timeout - too long wait for response, so next message was sent
            CON_READ_ERROR - 10 - error when reading data from the port
            CON_WAIT_veryLONG - 10 - critical long wait for a response
            CON_CLOSE - 8 - Com and socket ports have been closed
            CON_REPLACE - 7 - Message was changed on fly
            CON_WAIT_LONG - 7 - long wait for a response
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
                 time_interval_break: float, max_waiting_time_for_response: float, critical_response_time: float,
                 warning_response_time: float, number_of_lane: int):
        """
        :param com_name_x: <str> name of COM port to get information from 9pin machine, e.g. "COM1"
        :param com_name_y: <str> name of COM port to get information from computer application, e.g. "COM2"
        :param com_timeout: <float | int> maximum waiting time for downloading information from the COM port
        :param com_write_timeout: <float | int> maximum waiting time for sending information to the COM port
        :param on_add_log: <func> a function for saving the transmitted information in a log file
        :param time_interval_break: <float> length of time to wait after the end of the communication loop
        :param max_waiting_time_for_response: <float> time in seconds, after which, if the lane does not respond, we will send another
        :param critical_response_time: <float>  time in seconds after which program will inform about the criticaly long waiting time for a response
        :param warning_response_time: <float> time in seconds after which program will inform about the alarmingly long waiting time for a response
        :param number_of_lane: <int>

        List of additional_options: <empty list>

        :logs: CON_INFO (2)
        :raise
            ComManagerError
            SocketsManagerError
        """
        self.__com_x = ComManager(com_name_x, com_timeout, com_write_timeout, "COM_X", on_add_log, [b"30", b"31", b"32", b"33", b"34", b"35"])
        self.__com_y = ComManager(com_name_y, com_timeout, com_write_timeout, "COM_Y", on_add_log, [b"38"])
        self.__recv_com_x_additional_options = 0
        self.__recv_com_y_additional_options = 0
        self.__sockets = SocketsManager(on_add_log)
        self.__on_add_log = on_add_log
        self.__is_run = False
        self.__time_interval_break = time_interval_break
        self.__max_waiting_time_for_response = max_waiting_time_for_response
        self.__critical_response_time = critical_response_time
        self.__warning_response_time = warning_response_time
        self.__history_of_communication_x = []
        self.__number_of_lane = number_of_lane
        self.__on_add_log(2, "CON_INFO", "", "COM_X={}, COM_Y={}".format(com_name_x, com_name_y))
        self.__list_func_for_analyze_msg_to_send = []
        self.__list_func_for_analyze_msg_to_recv = []

        for _ in range(self.__number_of_lane):
            self.__history_of_communication_x.append({
                "no_answer": 0,
                "warning_wait": 0,
                "critical_wait": 0,
                "left_max": 0,
                "response_times": []
            })

    def start(self) -> None:
        """
        This method starts transferring data

        possible value in response_waiting_mode:
            3 - if the wait is longer than this __warning_response_time then add log CON_WAIT_LONG and set mode 2
            2 - if the wait is longer than this __critical_response_time then add log CON_WAIT_veryLONG and set mode 1
            1 v 2 - the wait was long, so when received add log with a late message was received
            0 - does not wait for a response

        :return: None
        :logs: CON_ERROR_WAIT (10), CON_WAIT_veryLONG (10), CON_WAIT_LONG (7), CON_START (7), CON_WAIT_END (6)
        """
        self.__on_add_log(7, "CON_START", "", "Communication has been started")

        time_next_sending_x = time.time() + 1.5
        time_last_sending_x = 0
        last_sent_x = b""
        response_waiting_mode = 0

        self.__is_run = True
        while self.__is_run:
            if response_waiting_mode == 3 and time.time() > time_last_sending_x + self.__warning_response_time:
                self.__on_add_log(7, "CON_WAIT_LONG", "COM_X", "Ostrzegawczo długie oczekiwanie na odpowiedź na: " + str(last_sent_x))
                self.__count_anomalies_pending_response(last_sent_x, 2)
                response_waiting_mode = 2

            if response_waiting_mode == 2 and time.time() > time_last_sending_x + self.__critical_response_time:
                self.__on_add_log(10, "CON_WAIT_veryLONG", "COM_X", "Krytycznie długie oczekiwanie na odpowiedź na: " + str(last_sent_x))
                self.__count_anomalies_pending_response(last_sent_x, 1)
                response_waiting_mode = 1

            recv_bytes_x, recv_msg_x = self.__com_reader(self.__com_x, self.__com_y, self.__sockets, self.__recv_com_x_additional_options, self.__list_func_for_analyze_msg_to_recv)
            if recv_bytes_x > 0:
                if response_waiting_mode in [1, 2]:
                    self.__on_add_log(6, "CON_WAIT_END", "COM_X", "Przyszła odpowiedź na: " + str(last_sent_x))
                self.__analysis_of_responses(last_sent_x, recv_msg_x, time_last_sending_x)
                time_next_sending_x = 0
                response_waiting_mode = 0

            self.__com_reader(self.__com_y, self.__com_x, self.__sockets, self.__recv_com_y_additional_options, self.__list_func_for_analyze_msg_to_send)
            self.__com_y.send()

            if time.time() >= time_next_sending_x:
                if time_next_sending_x > 0 and last_sent_x != b"":
                    self.__on_add_log(10, "CON_ERROR_WAIT", "COM_X", "Oczekiwanie na tyle długie, że zostanie wysłana nowa wiadomość. Ostatnio wysłana: " + str(last_sent_x))
                    time_next_sending_x = 0
                    self.__count_anomalies_pending_response(last_sent_x, 0)
                sent_bytes_x, sent_msg_x = self.__com_x.send()

                if sent_bytes_x > 0:
                    time_next_sending_x = time.time() + self.__max_waiting_time_for_response
                    time_last_sending_x = time.time()
                    last_sent_x = sent_msg_x
                    response_waiting_mode = 3
            bytes_to_send_to_com_x = self.__sockets.communications()
            if bytes_to_send_to_com_x != b"":
                # TODO
                self.__on_add_log(10, "TODO_1", "", "Give msg from socket to com_x")
                # self.__com_x.add_bytes_to_send(bytes_to_send_to_com_x)
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
                    str(com.get_number_of_waiting_messages_to_send()),
                    str(com.get_number_of_duplicates())
                ]
            )
        return com_info + self.__sockets.get_info()

    def __com_reader(self, com_in: ComManager, com_out: ComManager, sockets: SocketsManager, additional_options: int, list_func_for_analyze_msg) -> (int, bytes):
        """
        This method reads data from the "com_in" port. It then adds the read data to the queue with data to be sent in
        'com_out' and sockets queue.

        :param com_in: <ComManager> object with a COM port from which this function will read data
        :param com_out: <ComManager> with COM port where this func will add read data to the queue with data to be sent
        :param sockets <SocketManager> obj to management socket connection
        :param additional_options <int> options used to edit message on fly
        :param list_func_for_analyze_msg: list[func] TODO

        :return: <int, bytes> The number of data bytes received or -1 if there was an error, received bytes
        :logs: CON_READ_ERROR (10)
        """
        try:
            received_bytes = com_in.read()
            if received_bytes == b"":
                return 0, b""

            received_bytes = self.__edit_message_on_the_fly(additional_options, received_bytes)
            socket_msg = b""
            while b"\r" in received_bytes:
                index_first_special_sign = received_bytes.index(b"\r") + 1
                msg = received_bytes[:index_first_special_sign]
                received_bytes = received_bytes[index_first_special_sign:]

                com_in_front, com_in_end, com_out_front, com_out_end = self.__analyze_msg(msg, list_func_for_analyze_msg)

                com_in.add_msg_to_send(com_in_front, com_in_end)
                com_out.add_msg_to_send(com_out_front, com_out_end)

                # TODO optymalize

                for m in com_in_front + com_out_front + com_in_end + com_out_end:
                    socket_msg += m["message"]
                sockets.add_bytes_to_send(socket_msg)
            return len(socket_msg), socket_msg
        except (serial.SerialException, serial.SerialTimeoutException) as e:
            self.__on_add_log(10, "CON_READ_ERROR", com_in.get_alias(), e)
            return -1, b""

    def __analyze_msg(self, message, list_func_to_analyze):
        """
        TODO
        """
        msg_obj = {"message": message, "time_wait": -1, "priority": 3}
        for func in list_func_to_analyze:
            print("A", func)
            com_in_front, com_in_end, com_out_front, com_out_end = func(message)
            if len(com_in_front) + len(com_in_end) + len(com_out_front) + len(com_out_end) != 0:
                return com_in_front, com_in_end, com_out_front, com_out_end
        return [], [], [], [msg_obj]

    def __edit_message_on_the_fly(self, options: int, messages: bytes) -> bytes:
        """
        NOT USED
        Method is used to swap message data on the fly if certain conditions occur

        The method was made to turn on the printer, but it turned out that messages are sent every 3s, so this way did not speed up the operation

        List options:
            <empty>

        :param options: <int> options
        :param messages: <bytes> message/messages to edit
        :return: <bytes> message/messags after edit
        :logs: CON_REPLACE (7)
        """
        if options == 0:
            return messages
        return_messages = b""
        for message in messages.split(b"\r")[:-1]:
            message_old = message
            # if options & 1 and message[4:6] == b"IG" and len(message) == 27: #PRINT_ON
            #     head = message[:-2]
            #     head_new = head[:24] + bytes([head[24] | 0b00000001]) + head[25:]
            #     if head_new != head:
            #         message_new = head_new + self.__calculate_control_sum(head_new) + b"\r"
            #         self.__on_add_log(7, "CON_REPLACE", "", "Wiadomość {} zostałą zamianiona na {}".format(message, message_new))
            #         message = message_new
            if message_old != message:
                self.__on_add_log(7, "CON_REPLACE", "", "Wiadomość {} zostałą zamianiona na {}".format(message_old, message))
            return_messages += message + b"\r"
        return return_messages

    @staticmethod
    def __calculate_control_sum(message_head: bytes) -> bytes:
        sum_ascii = 0
        for x in message_head:
            sum_ascii += x
        checksum = bytes(hex(sum_ascii).split("x")[-1].upper()[-2:], 'utf-8')
        return checksum

    def __analysis_of_responses(self, msg_to: bytes, msg_from: bytes, time_send: float) -> None:
        """
        The main task of the function is to add to history_of_communication_x the time to wait for a response

        :param msg_to: <bytes> message to lane
        :param msg_from: <bytes> message from lane
        :param time_send: <float>
        :return: None
        """
        if msg_from.count(b"\r") > 1:
            self.__on_add_log(10, "CON_ANLS_ERROR_1", "", "Przyszło kilka odpowiedzi ({}) po wiadomości {}".format(msg_from, msg_to))
            return

        if len(msg_to) < 2 or len(msg_from) < 4:
            return
        try:
            msg_to_addressee = int(msg_to[1:2])
            msg_from_sender = int(msg_from[3:4])
            if msg_to_addressee >= self.__number_of_lane or msg_from_sender >= self.__number_of_lane:
                return
            if msg_to_addressee != msg_from_sender:
                self.__on_add_log(10, "CON_ANLS_ERROR_2", "", "Odpowiedź od innego toru: po wiadomości {} przyszła odpowiedź {}".format(msg_to, msg_from))
                return
            delta_time = int((time.time() - time_send) * 1000)
            self.__history_of_communication_x[msg_to_addressee]["response_times"].append(delta_time)
        except ValueError:
            return

    def __count_anomalies_pending_response(self, msg: bytes, stage: int) -> None:
        """
        Function increments the corresponding values in anomaly statistics

        :param msg: <bytes> message for which we (are waiting) / (have finished waiting)
        :param stage: <int> 0 - time out (waiting end), 1 - critical waiting time, 2 - warning waiting time
        :return: None
        """
        if len(msg) < 2:
            return
        try:
            addressee = int(msg[1:2])
            if addressee >= self.__number_of_lane:
                return
            if stage == 0:
                self.__history_of_communication_x[addressee]["no_answer"] += 1
                if self.__history_of_communication_x[addressee]["critical_wait"] > 0:
                    self.__history_of_communication_x[addressee]["critical_wait"] -= 1
            elif stage == 1:
                self.__history_of_communication_x[addressee]["critical_wait"] += 1
                if self.__history_of_communication_x[addressee]["warning_wait"] > 0:
                    self.__history_of_communication_x[addressee]["warning_wait"] -= 1
            else:
                self.__history_of_communication_x[addressee]["warning_wait"] += 1
        except ValueError:
            return

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

    def get_lane_response_stat(self):
        data = []
        for i, lane_stat in enumerate(self.__history_of_communication_x):
            list_all = lane_stat["response_times"]
            data_lane = [len(list_all)]
            for n in [50, [100, 50], 250, 1000, len(list_all)]:
                left = n[0] if isinstance(n, list) else n
                right = n[1] if isinstance(n, list) else 0
                l = list_all[-left:-right] if right > 0 else list_all[-left:]
                if len(list_all) <= right:
                    data_lane.append("")
                elif len(l) == 0:
                    data_lane.append(0)
                else:
                    data_lane.append(int(sum(l) / len(l)))
            list_max = list_all[lane_stat["left_max"]:]
            max_wait = 0 if len(list_max) == 0 else max(list_max)
            data_lane.extend([max_wait, lane_stat["warning_wait"], lane_stat["critical_wait"], lane_stat["no_answer"]])
            data.append(data_lane)
        return data

    def add_message_to_x(self, head_message: bytes, front: bool, priority: int, time_wait: int):
        message = head_message + self.__calculate_control_sum(head_message) + b"\r"
        self.__on_add_log(5, "CON_USERMSG", "", "Wiadomość dodana przez użytkowanika {}".format(message))
        msg_obj = {"message": message, "time_wait": time_wait, "priority": priority}
        if front:
            self.__com_x.add_msg_to_send([msg_obj], [])
        else:
            self.__com_x.add_msg_to_send([], [msg_obj])
        self.__sockets.add_bytes_to_send(message)

    def clear_lane_stat(self, clear_type: str) -> None:
        """
        :param clear_type: <"Max", "Warn", "All">
        :return: None
        """
        if clear_type == "Max":
            for lane_stat in self.__history_of_communication_x:
                lane_stat["left_max"] = len(lane_stat["response_times"])
        if clear_type == "Warn":
            for lane_stat in self.__history_of_communication_x:
                lane_stat["warning_wait"] = 0
                lane_stat["critical_wait"] = 0
                lane_stat["no_answer"] = 0
        if clear_type == "All":
            for i in range(len(self.__history_of_communication_x)):
                self.__history_of_communication_x[i] = {
                    "no_answer": 0,
                    "warning_wait": 0,
                    "critical_wait": 0,
                    "left_max": 0,
                    "response_times": []
                }

    def add_func_for_analyze_msg_to_recv(self, func):
        self.__list_func_for_analyze_msg_to_recv.append(func)
