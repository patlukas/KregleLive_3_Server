import time

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton

class SectionLaneControlPanel(QGroupBox):

    def __init__(self):
        """
        self.__mode_on_lane: [int] - 0-before start first block, 1=trial started, 2=trail ended, 3=game started, 4=game ended
        self.__enable_enter_on_lane: [bool] - TODO
        self.__enable_stop_time_on_lane: [bool] - TODO
        self.__trial_time_on_lane: [bytes] - is used to check time is running in trial runs
        self.__stop_time_deadline_on_lane - TODO
        """
        super().__init__("Sterowanie torami")
        self.__log_management = None
        self.__on_add_message = None
        self.__box_enter = None
        self.__box_time = None
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.setVisible(False)

        self.__number_of_lane = 0
        self.__mode_on_lane = []
        self.__enable_enter_on_lane = []
        self.__enable_stop_time_on_lane = []
        self.__trial_time_on_lane = []
        self.__stop_time_deadline_on_lane = []

    def init(self, number_of_lane: int, log_management, on_add_message):
        self.__number_of_lane = number_of_lane
        self.__log_management = log_management
        self.__on_add_message = on_add_message

        button_structure = self.__get_structure(number_of_lane)
        self.__box_enter = self.__get_panel_with_buttons("", "Enter", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T24", "Enter"))
        self.__box_time = self.__get_panel_with_buttons("", "Czas stop", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T14", "Czas stop"))
        self.__layout.addWidget(self.__box_enter)
        self.__layout.addWidget(self.__box_time)

        self.__mode_on_lane = [0 for _ in range(number_of_lane)]
        self.__enable_enter_on_lane = [False for _ in range(number_of_lane)]
        self.__enable_stop_time_on_lane = [False for _ in range(number_of_lane)]
        self.__trial_time_on_lane = [b"" for _ in range(number_of_lane)]
        self.__stop_time_deadline_on_lane = [0 for _ in range(number_of_lane)]


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
            message = b"3" + bytes(str(lane), "cp1250") + b"38" + body_message
            self.__on_add_message(message, True, 9, 0) #TODO change time_wait

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

    def show_control_panel(self, name: str, show: bool):
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

    def analyze_message_from_lane(self, msg):
        """
        TODO
        """
        lane = self.__get_lane(msg, self.__number_of_lane)
        if lane == -1:
            self.__log_management(10, "LCP_ERROR_1", "", "Numer toru {} jest niepoprawny".format(lane))
            return
        self.__analyze_message__check_mode(msg, lane)
        self.__analyze_message__moment_of_trial(msg, lane)
        return self.self.__analyze_message__throw(msg, lane)

    def __analyze_message__check_mode(self, msg, lane):
        """
            This function change mode when trial/game is started/ended

            msg <bytes> - message from lane
            lane <int> - lane number from where message was sent

            return None
        """
        if len(msg) < 8:
            return

        if msg[4:5] not in [b"p", b"i"]:
            return

        content = msg[4:6]
        if content == b"p1":
            self.__mode_on_lane[lane] = 1
            self.__enable_enter_on_lane[lane] = True
            self.__enable_stop_time_on_lane[lane] = True
            self.__trial_time_on_lane[lane] = b""
        elif content == b"p0":
            self.__mode_on_lane[lane] = 2
            self.__enable_enter_on_lane[lane] = False
            self.__enable_stop_time_on_lane[lane] = False
        elif content == b"i1":
            self.__mode_on_lane[lane] = 3
            self.__enable_enter_on_lane[lane] = True
            self.__enable_stop_time_on_lane[lane] = True
        elif content == b"i0":
            self.__mode_on_lane[lane] = 4
            self.__enable_enter_on_lane[lane] = False
            self.__enable_stop_time_on_lane[lane] = False

    def __analyze_message__moment_of_trial(self, msg, lane):
        """
        This func analyze messages when is trial (mode == 1), and when time is started then disable possibility to click "enter"

        param:
            msg <bytes> - message from lane
            lane <int> - lane number from where message was sent

        return:
            None
        """
        if self.__mode_on_lane[lane] != 1:
            return
        if not self.__enable_enter_on_lane[lane]:
            return
        if len(msg) == 35:
            self.__enable_enter_on_lane[lane] = False
            return
        if len(msg) != 10:
            return

        if self.__trial_time_on_lane[lane] == b"":
            self.__trial_time_on_lane[lane] = msg[4:7]
        elif self.__trial_time_on_lane[lane] != msg[4:7]:
            self.__enable_enter_on_lane = False

    def __analyze_message__throw(self, msg, lane):
        """
        This function is responsible for resending the message to stop the time if a message with a new roll is received before the deadline expires

        param:
            msg <bytes> - message from lane
            lane <int> - lane number from where message was sent

        return:
            if the message is not required: [], [], [], []
            otherwise: [], [stop_time], [], [msg]
        """
        if len(msg) != 35:
            return [], [], [], []
        if not self.__enable_stop_time_on_lane[lane]:
            return [], [], [], []

        if time.time() <= self.__stop_time_deadline_on_lane[lane]:
            self.__stop_time_deadline_on_lane[lane] = 0
            return [], [], [], []
            # TODO Something like this
            # [], [{"message": 3?38T24??, "time_wait": ???, "priority": ???}], [], [{"message": msg, "time_wait": ???, "priority": ???}]

        return [], [], [], []

    @staticmethod
    def __get_lane(msg, number_of_lane):
        """
        msg: bytes - message from lane
        number_of_lane: int

        return <int>
            -1 - when message is too short or lane doesn't exist
            <0, ..> lane number
        """
        if len(msg) < 4:
            return -1
        lane = int(msg[3:4])
        if lane >= number_of_lane:
            return -1
        return lane
