"""This module is responsible for earlier ending clear off"""


class FinishingClearOffEarlier:
    def __init__(self, on_add_log, number_of_lane: int, max_number_of_throws: int, message_when_to_many_throws: str,
                 list_widget_checkbox: list, list_widget_label: list):
        """
        :param on_add_log: <func> a function for saving log
        :param number_of_lane: <int> number of ninepin lane
        :param max_number_of_throws: <int> max number of throws, when <=0 then no limit
        :param message_when_to_many_throws: <str> this message will be send when will be to many throw in clear off,
                                            when in str is '_' then this char will be replace by lane_index and will be
                                            calculate checksum, in otherwise this message without change will be send
        :param list_widget_checkbox: <list[QCheckBox]> list with widgets checkbox to select lane
        :param list_widget_label: <list[QLabel]>  list with widgets label to show how many throw is in clear off
        """
        self.__on_add_log = on_add_log
        self.__on_send_message = None
        self.__max_number_of_throws = int(max_number_of_throws)
        self.__number_of_lane = number_of_lane
        self.__messages = b""
        self.__message_when_to_many_throws = message_when_to_many_throws
        self.__lane = [[0, 0, False] for _ in range(number_of_lane)]
        self.__list_widget_checkbox = list_widget_checkbox
        self.__list_widget_label = list_widget_label

        for i, widget_checkbox in enumerate(self.__list_widget_checkbox):
            widget_checkbox.clicked.connect(lambda state, i=i: self.__on_click_checkbox(i))

    def on_set_send_message_func(self, on_send_message) -> None:
        """
        This method set func to send message to ninepin lane.

        :param on_send_message: <func> function to send message to ninepin lane
        :return: None
        """
        self.__on_send_message = on_send_message

    def on_receive_message(self, message: bytes) -> None:
        """
        This method analyze messages and when number of throw in clear off is too many,then sed message to end clear off

        :param message: <bytes> recived data
        :return: None
        """
        try:
            self.__messages += message
        except AttributeError as e:
            self.__on_add_log(10, "FCE_DECD_ERROR", "",
                                          "Nieudana zmiana typu wiadomości {} | Error: {}".format(message, e))
            return

        while b"\r" in self.__messages:
            try:
                index = self.__messages.index(b"\r")
                message, self.__messages = self.__messages[:index+1], self.__messages[index+1:]
                if len(message) != 35 or message[:2] != b"38":
                    continue
                try:
                    next_arrangement, number_throw, index_lane = message[17:20], int(message[5:8], 16), int(message[3:4])
                except ValueError as e:
                    self.__on_add_log(10, "FCE_SPLT_ERROR", "",
                                                  "Nieudany podział wiadomości {} | Error: {}".format(message, e))
                    continue
                if index_lane < self.__number_of_lane:
                    if next_arrangement == b"000":
                        self.__lane[index_lane][1] = number_throw
                    elif self.__lane[index_lane][0] > number_throw:
                        self.__lane[index_lane][1] = 0
                    self.__lane[index_lane][0] = number_throw
                    self.__list_widget_label[index_lane].setText(str(number_throw - self.__lane[index_lane][1]))
                if self.__lane[index_lane][2] \
                        and 0 < self.__max_number_of_throws <= number_throw - self.__lane[index_lane][1]:
                    if len(self.__message_when_to_many_throws) > 0 and self.__on_send_message is not None:
                        message_when_to_many_throws = self.__get_message_to_end_clear_off(index_lane)
                        self.__on_send_message(message_when_to_many_throws)
                        #### TODEL ####
                        self.__lane[index_lane][1] = self.__lane[index_lane][0] # TODEL powinna być info zwrotne jaki jest aktualnie uklad
                        self.__list_widget_label[index_lane].setText(str(self.__lane[index_lane][0] - self.__lane[index_lane][1])) #TODEL
                        #### TODEL END ####
                        self.__on_add_log(4, "FCE_SEND", "",
                                                      "Wysłanie wiadomości do {}, aby zakończyć układ ({})".format(
                                                          index_lane+1, message_when_to_many_throws))
            except Exception as e:
                self.__on_add_log(10, "FCE______ERROR", "",
                                              "Błąd przy analizie wiadomości {} | Error: {}".format(message, e))

    def __get_message_to_end_clear_off(self, index_lane: int) -> bytes:
        """
        This method create message, witch will be send to lane.

        :param index_lane: <int> index of ninepin lane
        :return: <bytes> message witch will be send to lane
        """
        messages = self.__message_when_to_many_throws.split(",")
        messages_return = ""
        for message in messages:
            if "_" not in message:
                messages_return += message + "\r"
            else:
                message = message.replace("_", str(index_lane))
                messages_return += message + self.__get_checksum(message) + "\r"
        return str.encode(messages_return)

    def __on_click_checkbox(self, lane_index):
        self.__lane[lane_index][2] = not self.__lane[lane_index][2]

    @staticmethod
    def __get_checksum(message: str) -> str:
        """
        This method calculate checksum.

        :param message: <str> message for which the checksum will be calculated
        :return: <str> checksum, witch will have two char
        """
        sum_ascii = 0
        for x in message:
            sum_ascii += ord(x)
        checksum = hex(sum_ascii).split("x")[-1].upper()[-2:]
        if len(checksum) == 1:
            checksum = "0" + checksum
        return checksum
