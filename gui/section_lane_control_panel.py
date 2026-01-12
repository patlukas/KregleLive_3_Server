import time

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton, QAction

from utils.messages import extract_lane_id_from_incoming_message, prepare_message_to_lane_and_encapsulate, encapsulate_message


class SectionLaneControlPanel(QGroupBox):

    def __init__(self, parent):
        """
        self.__mode_on_lane: [int] - what mode is on lane
            0 - the variable has been initialized and has not been changed yet
            1 - trial is ready
            2 - trial is over
            3 - game is ready
            4 - game is over
        self.__enable_enter_on_lane: [bool] - Specify whether an Enter message can be sent on the track
        self.__enable_stop_time_on_lane: [bool] - Specify whether a time-stopping message can be sent on the track
        self.__trial_time_on_lane: [bytes] - is used to check time is running in trial runs
        self.__stop_time_deadline_on_lane [float] - until what time will be send message to stop time
        self.__stop_time_deadline_buffer_s <int> - how many seconds does it take to stop time
        """
        super().__init__("Sterowanie torami")
        self.__parent = parent
        self.__log_management = None
        self.__on_add_message = None
        self.__box_enter = None
        self.__box_time = None
        self.action_enter = self.__prepare_action_widget("Sterowanie torami - Enter", "Enter")
        self.action_stop_time = self.__prepare_action_widget("Sterowanie torami - Czas stop", "Time")
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.setVisible(False)

        self.__number_of_lane = 0
        self.__mode_on_lane = []
        self.__enable_enter_on_lane = []
        self.__enable_stop_time_on_lane = []
        self.__trial_time_on_lane = []
        self.__stop_time_deadline_on_lane = []
        self.__stop_time_deadline_buffer_s = 15

    def init(self, number_of_lane: int, stop_time_deadline_buffer_s: int, log_management, on_add_message, show_section_enter, show_section_stop_time):
        """
        :param:
            number_of_lane <int>
            stop_time_deadline_buffer_s <int> - max number of second delay between click stop time, a recv message about throw result
        """
        self.__number_of_lane = number_of_lane
        self.__stop_time_deadline_buffer_s = stop_time_deadline_buffer_s
        self.__log_management = log_management
        self.__on_add_message = on_add_message

        button_structure = self.__get_structure(number_of_lane)
        self.__box_enter = self.__get_panel_with_buttons("", "Enter", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T24", "Enter"))
        self.__box_time = self.__get_panel_with_buttons("", "Czas stop", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T14", "Czas stop"))
        self.__layout.addWidget(self.__box_enter)
        self.__layout.addWidget(self.__box_time)

        self.action_enter.setChecked(show_section_enter)
        self.action_stop_time.setChecked(show_section_stop_time)

        self.__mode_on_lane = [0 for _ in range(number_of_lane)]
        self.__enable_enter_on_lane = [False for _ in range(number_of_lane)]
        self.__enable_stop_time_on_lane = [False for _ in range(number_of_lane)]
        self.__trial_time_on_lane = [b"" for _ in range(number_of_lane)]
        self.__stop_time_deadline_on_lane = [0 for _ in range(number_of_lane)]

    def __prepare_action_widget(self, label, name_type):
        action = QAction(label, self)
        action.setCheckable(True)
        action.setChecked(False)
        action.toggled.connect(lambda checked: self.__on_show_lane_control(name_type, checked))
        return action

    def __on_show_lane_control(self, name_type: str, show: bool):
        self.__show_control_panel(name_type, show)
        self.__parent.adjustSize()

    def __get_structure(self, number_of_lane: int) -> list:
        number_of_lane_in_row = number_of_lane
        return_list = []
        while number_of_lane_in_row >= 1:
            return_list.append(self.__get_structure_row(number_of_lane_in_row, number_of_lane))
            number_of_lane_in_row -= (2 if number_of_lane_in_row > 2 else 1)
        return return_list

    @staticmethod
    def __get_structure_row(number_of_lane_in_row: int, number_of_lane: int) -> list:
        step = 2 if number_of_lane_in_row > 1 else 1
        left_lane = 0
        result_list = []
        while left_lane + number_of_lane_in_row <= number_of_lane:
            a = [left_lane+i for i in range(number_of_lane_in_row)]
            result_list.append(a)
            left_lane += step
        return result_list

    def __add_new_messages(self, list_lane: list, body_message: bytes, what_message_means: str):
        if self.__on_add_message is None or self.__log_management is None:
            return
        list_lane_to_print = [x+1 for x in list_lane]
        self.__log_management(3, "LCP_CLICK", "", "Dodano nowe wiadomości przez 'Sterowanie torami': Adresaci {}, Wiadomość '{}'({})".format(list_lane_to_print, what_message_means, body_message))
        for lane in list_lane:
            if body_message == b"T14":
                if not self.__enable_stop_time_on_lane[lane]:
                    continue
                self.__stop_time_deadline_on_lane[lane] = time.time() + self.__stop_time_deadline_buffer_s
            if body_message == b"T24":
                if not self.__enable_enter_on_lane[lane]:
                    continue
                self.__stop_time_deadline_on_lane[lane] = 0
                if self.__mode_on_lane[lane] == 1:
                    self.__enable_enter_on_lane[lane] = False
            message = b"3" + bytes(str(lane), "cp1250") + b"38" + body_message
            self.__on_add_message(message, True, 9, 0)

    @staticmethod
    def __get_panel_with_buttons(main_label: str, option_name: str, structure: list, number_col: int, on_click):
        box = QGroupBox(main_label)
        layout = QGridLayout()
        for i, row in enumerate(structure):
            number_btn = len(row)
            cols_for_btn = number_col // number_btn
            left_col = 0
            for btn_lane in row:
                btn = QPushButton(option_name + " " + ", ".join(map(str, [x + 1 for x in btn_lane])))
                btn.clicked.connect(lambda _, list_lane=btn_lane: on_click(list_lane))
                layout.addWidget(btn, i, left_col, 1, cols_for_btn)
                left_col += cols_for_btn
        box.setLayout(layout)
        box.setVisible(False)
        return box

    def __show_control_panel(self, name: str, show: bool):
        if self.__box_time is None or self.__box_enter is None:
            return

        show_main = show
        if name == "Enter":
            self.__box_enter.setVisible(show)
            show_main = show_main or self.__box_time.isVisible()
        elif name == "Time":
            self.__box_time.setVisible(show)
            show_main = show_main or self.__box_enter.isVisible()
        self.setVisible(show_main)
        if show_main:
            self.adjustSize()

    def analyze_message_from_lane(self, msg: bytes):
        """
        This function is responsible for analyzing messages received from the lanes

        Args:
            msg (bytes): Incoming message received from a lane.

        Level of interference:
            8: b'____w_____________________________\r' & was clicked "Stop time" when pins weren't standing
            1: b'____i0__\r'
            1: b'____i1__\r'
            1: b'____p0__\r'
            1: b'____p1__\r'
            0: otherwise

        Activation conditions:
            In:
                b'____i0__\r'
                b'____i1__\r'
                b'____p0__\r'
                b'____p1__\r'
            Out:
                None
            In:
                b'____w_____________________________\r' in place 'w' can be 'g', 'h', 'k', 'f'
            Out:
                None - if time no will be stop
                [T14], [], [], [b'____w_____________________________\r'] - otherwise

        Returns:
            None || [list, list, list, list]
        """
        lane_id = extract_lane_id_from_incoming_message(msg, self.__number_of_lane)
        if lane_id == -1:
            self.__log_management(10, "LCP_ERROR_1", "", "Numer toru {} jest niepoprawny".format(lane_id))
            return
        self.__update_mode_from_incoming_message(msg, lane_id)
        self.__analyze_message__moment_of_trial(msg, lane_id)
        return self.__analyze_message__throw(msg, lane_id)

    def __update_mode_from_incoming_message(self, msg: bytes, lane_id: int) -> None:
        """
        Update the current mode based on an incoming message.

        Detects start and end events of a trial or game and updates
        the internal mode state accordingly.

        Args:
            msg (bytes): Incoming message received from a lane.
            lane_id (int): Lane number from which the message was sent.

        Returns:
            None
        """
        if len(msg) < 9:
            return

        if msg[4:5] not in [b"p", b"i"]:
            return

        content = msg[4:6]
        if content == b"p1":
            self.__mode_on_lane[lane_id] = 1
            self.__trial_time_on_lane[lane_id] = b""
        elif content == b"p0":
            self.__mode_on_lane[lane_id] = 2
        elif content == b"i1":
            self.__mode_on_lane[lane_id] = 3
        elif content == b"i0":
            self.__mode_on_lane[lane_id] = 4

        if self.__mode_on_lane[lane_id] in [1, 3]:
            self.__enable_enter_on_lane[lane_id] = True
            self.__enable_stop_time_on_lane[lane_id] = True
        elif self.__mode_on_lane[lane_id] in [2, 4]:
            self.__enable_enter_on_lane[lane_id] = False
            self.__enable_stop_time_on_lane[lane_id] = False

    def __analyze_message__moment_of_trial(self, msg: bytes, lane_id: int) -> None:
        """
        This func analyze messages when is trial (mode == 1), and when time is started then disable possibility to click "enter"

        param:
            msg <bytes> - message from lane
            lane_id <int> - lane number from where message was sent

        return:
            None
        """
        if self.__mode_on_lane[lane_id] != 1:
            return
        if not self.__enable_enter_on_lane[lane_id]:
            return
        if len(msg) == 35:
            self.__enable_enter_on_lane[lane_id] = False
            return
        if len(msg) != 10:
            return

        if self.__trial_time_on_lane[lane_id] == b"":
            self.__trial_time_on_lane[lane_id] = msg[4:7]
        elif self.__trial_time_on_lane[lane_id] != msg[4:7]:
            self.__enable_enter_on_lane = False

    def __analyze_message__throw(self, msg: bytes, lane_id: int):
        """
        This function is responsible for resending the message to stop the time if a message with a new roll is received before the deadline expires

        param:
            msg <bytes> - message from lane
            lane_id <int> - lane number from where message was sent

        return:
            if the message is not required: None
            otherwise: [stop_time], [], [], [msg]
        """
        if len(msg) != 35:
            return
        if not self.__enable_stop_time_on_lane[lane_id]:
            return

        if time.time() <= self.__stop_time_deadline_on_lane[lane_id]:
            self.__stop_time_deadline_on_lane[lane_id] = 0
            packet_to_lane = prepare_message_to_lane_and_encapsulate(lane_id, b"T14", 9, 0)
            packet_from_lane = encapsulate_message(msg, 3, -1)
            return [packet_to_lane], [], [], [packet_from_lane]
        return
