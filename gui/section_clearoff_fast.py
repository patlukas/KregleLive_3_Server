from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton, QCheckBox, QLabel, QHBoxLayout, QComboBox
from PyQt5.QtCore import Qt

class SectionClearOffTest(QGroupBox):

    def __init__(self):
        super().__init__("Szybsze kończenie zbieranych")
        self.__log_management = None
        self.__box = None
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.setVisible(False)
        self.__checkboxes = []
        self.__labels = []
        self.__combo_modes = None
        self.__list_throw_to_current_layout = []
        self.__list_count_clear_off_finish = []

    def init(self, number_of_lane: int, log_management):
        self.__log_management = log_management
        for i in range(number_of_lane):
            self.__list_throw_to_current_layout.append(0)
            self.__list_count_clear_off_finish.append(0)
        self.__box = self.__get_panel(number_of_lane)
        self.__layout.addWidget(self.__box)

    def __get_panel(self, number_of_lane):
        box = QGroupBox("")
        layout = QGridLayout()

        self.__combo_modes = QComboBox()
        self.__combo_modes.addItems(["Tryb A", "Tryb A - szybki"])
        layout.addWidget(self.__combo_modes, 0, 0)

        box_row = QGroupBox("Status na torach")
        layout_row = QGridLayout()
        for i in range(number_of_lane):
            pair_layout = QHBoxLayout()
            label = QLabel()
            self.__labels.append(label)
            pair_layout.addWidget(label)
            self.__actualize_label(i)
            layout_row.addLayout(pair_layout, 0, i)

        box_row.setLayout(layout_row)
        layout.addWidget(box_row, 1, 0)


        for row, title in enumerate(["Aktualny tor", "Następny tor"]):
            box_row = QGroupBox(title)
            layout_row = QGridLayout()
            self.__checkboxes.append([])

            for i in range(number_of_lane):
                pair_layout = QHBoxLayout()
                pair_layout.setSpacing(0)

                label = QLabel(str(i + 1))
                checkbox = QCheckBox()

                self.__checkboxes[row].append(checkbox)

                pair_layout.addWidget(label)
                pair_layout.addWidget(checkbox)
                pair_layout.addStretch()

                layout_row.addLayout(pair_layout, 0, i)

            box_row.setLayout(layout_row)
            layout.addWidget(box_row, row+2, 0)

        box.setLayout(layout)
        box.setVisible(False)
        return box

    def analyze_message(self, msg):
        if msg[4:6] == b"i0":
            lane = int(msg[3:4])
            self.__log_management(5, "S_COF_1", "", "Odebrano wiadomość i0 a torze '{}'({})".format(lane, msg ))
            if lane >= len(self.__list_throw_to_current_layout):
                return [], [], [], []
            self.__checkboxes[0][lane].setChecked(self.__checkboxes[1][lane].isChecked())
            self.__checkboxes[1][lane].setChecked(False)
            self.__list_throw_to_current_layout[lane] = 0
            self.__list_count_clear_off_finish[lane] = 0
            self.__actualize_label(lane)
            return [], [], [], []
        if msg[4:5] in [b"w", b"g", b"h", b"f"]:
            lane = int(msg[3:4])
            if lane >= len(self.__list_throw_to_current_layout):
                return [], [], [], [] # {"message": msg, "time_wait": -1, "priority": 3}
            self.__log_management(4, "S_COF_2", "", "Odebrano wiadomość o rzucie na torze '{}'({})".format(lane, msg))
            next_layout = msg[17:20]
            fallen_pins = msg[26:29]
            if next_layout != b"000" or fallen_pins == b"000":
                self.__list_throw_to_current_layout[lane] += 1
            else:
                self.__list_throw_to_current_layout[lane] = 0
            self.__log_management(5, "S_COF_3", "", "Na torze {} będzie rzut numer {} do układu".format(lane, self.__list_throw_to_current_layout[lane]+1))
            self.__actualize_label(lane)
            if not self.__checkboxes[0][lane].isChecked():
                return [], [], [], []
            return self.__analyse_max_throw_clearoff(lane, msg)
        return [], [], [], []

    def __analyse_max_throw_clearoff(self, lane, message):
        max_throw = 3
        if self.__list_throw_to_current_layout[lane] < max_throw:
            return [], [], [], []
        self.__log_management(7, "S_COF_4", "", "Zakończenie układu i ustawienie pełnego układu na torze: {}".format(lane))
        self.__list_throw_to_current_layout[lane] = 0
        com_x_front, com_y_end =  self.__send_message_to_end_layout(
            message[2:4] + message[0:2],
            message[5:8],
            message[8:11],
            message[11:14],
            message[14:17],
            message[17:20],
            message[20:23],
            message[23:26],
            message[26:29],
            message[29:32]
        )
        self.__list_count_clear_off_finish[lane] += 1
        self.__actualize_label(lane)
        return com_x_front, com_y_end, [], [{"message": message, "time_wait": -1, "priority": 3}]

    def __send_message_to_end_layout(self, message_head, number_of_throw, last_throw_result, lane_sum, total_sum, next_layout,
                                     number_of_x, time_to_end, fallen_pins, options):
        z = lambda priority, time_wait: self.__on_get_message(
            message_head +
            b"Z" +
            number_of_throw +
            last_throw_result +
            lane_sum +
            total_sum +
            b"000" +
            number_of_x +
            time_to_end +
            fallen_pins +
            options,
            priority,
            time_wait
        )

        b_click = lambda msg, priority=3, time_wait=-1: self.__on_get_message(message_head + msg, priority, time_wait)

        b_stop_9 = b_click(b"T40", 9)
        b_layout_5 = b_click(b"T16", 5)
        b_clear_6 = b_click(b"T22", 6)
        b_enter_6 = b_click(b"T24", 6)
        z_2_5_1500 = z(5, 1500)
        b_pick_up_7 = b_click(b"T41", 7)

        b_layout_5_300 = b_click(b"T16", 5, 300)
        b_clear_6_300 = b_click(b"T22", 6, 300)
        b_pick_up_7_300 = b_click(b"T41", 7, 300)

        modes = [
            [b_stop_9, b_layout_5, b_clear_6, b_enter_6, z_2_5_1500, b_pick_up_7],
            [b_stop_9, b_layout_5_300, b_clear_6_300, b_enter_6, z_2_5_1500, b_pick_up_7_300],
        ]

        mode_index = self.__combo_modes.currentIndex()
        self.__log_management(3, "S_COF_5", "", "Do ustawienia pełnego ukłądu użyto metody numer {}".format(mode_index))
        return modes[mode_index], []

    def __on_get_message(self, message, priority=5, time_wait=-1):
        msg = message + self.__calculate_control_sum(message) + b"\r"
        return {"message": msg, "time_wait": time_wait, "priority": priority}

    @staticmethod
    def __calculate_control_sum(message):
        sum_ascii = 0
        for x in message:
            sum_ascii += x
        checksum = bytes(hex(sum_ascii).split("x")[-1].upper()[-2:], 'utf-8')
        return checksum

    def show_control_panel(self, show: bool):
        if self.__box is None:
            return
        self.__box.setVisible(show)
        self.setVisible(show)
        if show:
            self.adjustSize()

    def __actualize_label(self, lane):
        """
        TODO
        """
        self.__labels[lane].setText(str(self.__list_throw_to_current_layout[lane] + 1) + " | " + str(self.__list_count_clear_off_finish[lane]))