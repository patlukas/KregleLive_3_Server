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
        self.__list_count_full_throws = []
        self.__list_count_all_throws = []

    def init(self, number_of_lane: int, log_management):
        self.__log_management = log_management
        for i in range(number_of_lane):
            self.__list_throw_to_current_layout.append(0)
            self.__list_count_clear_off_finish.append(0)
            self.__list_count_full_throws.append(0)
            self.__list_count_all_throws.append(0)
        self.__box = self.__get_panel(number_of_lane)
        self.__layout.addWidget(self.__box)

    def __get_panel(self, number_of_lane):
        box = QGroupBox("")
        layout = QGridLayout()

        self.__combo_modes = QComboBox()
        self.__combo_modes.addItems([
            "Tryb  1: Stop(700) Korekta(700) C(700) Enter(700)  Z(1500) Podnies(700)  = 5000",
            "Tryb  2: Stop(700) Korekta(300) C(300) Enter(700)  Z(1500) Podnies(300)  = 3800",
            "Tryb  3: Stop(0)   Korekta(300) C(300) Enter(700)  Z(1500) Podnies(300)  = 3100",
            "Tryb  4: Stop(0)   Korekta(200) C(200) Enter(700)  Z(1000) Podnies(200)  = 2300",
            "Tryb  5: Stop(0)   Korekta(200) C(200) Enter(1000) Z(1000) Podnies(200)  = 2600",
            "Tryb  6: Stop(0)   Korekta(200) C(200) Enter(1000) Z(200)  Podnies(200)  = 1800",
            "Tryb  7: Stop(0)   Korekta(200) C(200) Enter(200)  Z(1000) Podnies(200)  = 1800",
            "Tryb  8: Stop(0)   Korekta(200) C(200) Enter(200)  Z(200)  Podnies(1000) = 1800",
            "Tryb  9: Stop(0)   Korekta(50)  C(50)  Enter(1000) Z(1000) Podnies(50)   = 2150",
            "Tryb 10: Stop(0)   Korekta(50)  C(50)  Enter(1000) Z(50)   Podnies(50)   = 1200",
            "Tryb 11: Stop(0)   Korekta(50)  C(50)  Enter(50)   Z(1000) Podnies(50)   = 1200",
            "Tryb 12: Stop(0)   Korekta(50)  C(50)  Enter(50)   Z(50)   Podnies(1000) = 1200",
            "Tryb 13: Stop(0)   Korekta(0)   C(0)   Enter(1000) Z(0)    Podnies(0)    = 1000",
            "Tryb 14: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(1000) Podnies(0)    = 1000",
            "Tryb 15: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(0)    Podnies(1000) = 1000",
            "Tryb 16: Stop(0)   Korekta(0)   C(0)   Enter(800)  Z(0)    Podnies(0)    =  800",
            "Tryb 17: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(800)  Podnies(0)    =  800",
            "Tryb 18: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(0)    Podnies(800)  =  800",
            "Tryb 19: Stop(0)   Korekta(0)   C(0)   Enter(700)  Z(0)    Podnies(0)    =  700",
            "Tryb 20: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(700)  Podnies(0)    =  700",
            "Tryb 21: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(0)    Podnies(700)  =  700",
            "Tryb 22: Stop(0)   Korekta(0)   C(0)   Enter(600)  Z(0)    Podnies(0)    =  600",
            "Tryb 23: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(600)  Podnies(0)    =  600",
            "Tryb 24: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(0)    Podnies(600)  =  600",
            "Tryb 25: Stop(0)   Korekta(0)   C(0)   Enter(500)  Z(0)    Podnies(0)    =  500",
            "Tryb 26: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(500)  Podnies(0)    =  500",
            "Tryb 27: Stop(0)   Korekta(0)   C(0)   Enter(0)    Z(0)    Podnies(500)  =  500"
        ])
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

    def analyze_message_from_lane(self, msg):
        if msg[4:6] == b"i0":
            lane = int(msg[3:4])
            self.__log_management(5, "S_COF_1", "", "Odebrano wiadomość i0 a torze '{}'({})".format(lane, msg ))
            if lane >= len(self.__list_throw_to_current_layout):
                return [], [], [], []
            self.__checkboxes[0][lane].setChecked(self.__checkboxes[1][lane].isChecked())
            self.__checkboxes[1][lane].setChecked(False)
            self.__list_throw_to_current_layout[lane] = 0
            self.__list_count_clear_off_finish[lane] = 0
            self.__list_count_all_throws[lane] = 0 # then in trial after 3x 0 this function not will set full layout
            self.__actualize_label(lane)
            return [], [], [], []
        if msg[4:5] in [b"w", b"g", b"h", b"f"]:
            lane = int(msg[3:4])
            if lane >= len(self.__list_throw_to_current_layout):
                return [], [], [], [] # {"message": msg, "time_wait": -1, "priority": 3}s
            throw_number = int(msg[5:8])
            self.__log_management(4, "S_COF_2", "", "Odebrano wiadomość o rzucie {} na torze '{}'({})".format(throw_number, lane, msg))
            if self.__list_count_all_throws[lane] == 0:
                self.__log_management(3, "S_COF_14", "", "Są próbne: jest rzut '{}'".format(throw_number))
                return [], [], [], []
            if throw_number <= self.__list_count_full_throws[lane]:
                self.__log_management(3, "S_COF_12", "", "Są jeszcze pełne: jest rzut '{}', a pełne trwają {} rzutów".format(throw_number, self.__list_count_full_throws[lane]))
                return [], [], [], []
            if throw_number >= self.__list_count_all_throws[lane]:
                self.__log_management(3, "S_COF_13", "", "Gra na torze się zakończyła: jest rzut '{}', a pełne trwają {} rzutów".format(throw_number, self.__list_count_full_throws[lane]))
                return [], [], [], []
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

    def analyze_message_to_lane(self, msg):
        if msg[4:6] == b"IG":
            lane = int(msg[1:2])
            self.__log_management(5, "S_COF_10", "", "Odebrano wiadomość IG na torze '{}'({})".format(lane, msg ))
            if lane >= len(self.__list_throw_to_current_layout):
                return [], [], [], []

            count_full_throw = int(msg[6:9])
            count_clear_off_throw = int(msg[9:12])
            self.__list_count_full_throws[lane] = count_full_throw
            self.__list_count_all_throws[lane] = count_full_throw + count_clear_off_throw
            self.__log_management(5, "S_COF_11", "", "Na torze '{}' włączono meczówkę na {}+{} rzutów".format(lane, count_full_throw, count_clear_off_throw))
            return [], [], [], []
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
        z = lambda time_wait=-1, priority=5: self.__on_get_message(
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

        b_stop = lambda time_wait=-1, priority=9: b_click(b"T40", priority, time_wait)
        b_layout = lambda time_wait=-1, priority=5: b_click(b"T16", priority, time_wait)
        b_clear = lambda time_wait=-1, priority=6: b_click(b"T22", priority, time_wait)
        b_enter = lambda time_wait=-1, priority=6: b_click(b"T24", priority, time_wait)
        b_pick_up = lambda time_wait=-1, priority=7: b_click(b"T41", priority, time_wait)

        modes = [
            [b_stop(), b_layout(), b_clear(), b_enter(), z(1500), b_pick_up()],  # A,5000
            [b_stop(), b_layout(300), b_clear(300), b_enter(), z(1500), b_pick_up(300)],  # B,3800
            [b_stop(0), b_layout(300), b_clear(300), b_enter(), z(1500), b_pick_up(300)],  # C,3100
            [b_stop(0), b_layout(200), b_clear(200), b_enter(), z(1000), b_pick_up(200)],  # D,2300
            [b_stop(0), b_layout(200), b_clear(200), b_enter(1000), z(1000), b_pick_up(200)],  # E,2600
            [b_stop(0), b_layout(200), b_clear(200), b_enter(1000), z(200), b_pick_up(200)],  # F,1800
            [b_stop(0), b_layout(200), b_clear(200), b_enter(200), z(1000), b_pick_up(200)],  # G,1800
            [b_stop(0), b_layout(200), b_clear(200), b_enter(200), z(200), b_pick_up(1000)],  # H,1800
            [b_stop(0), b_layout(50), b_clear(50), b_enter(1000), z(1000), b_pick_up(50)],  # I,2150
            [b_stop(0), b_layout(50), b_clear(50), b_enter(1000), z(50), b_pick_up(50)],  # J,1200
            [b_stop(0), b_layout(50), b_clear(50), b_enter(50), z(1000), b_pick_up(50)],  # K,1200
            [b_stop(0), b_layout(50), b_clear(50), b_enter(50), z(50), b_pick_up(1000)],  # L,1200
            [b_stop(0), b_layout(0), b_clear(0), b_enter(1000), z(0), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(1000), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(0), b_pick_up(1000)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(800), z(0), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(800), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(0), b_pick_up(800)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(700), z(0), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(700), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(0), b_pick_up(700)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(600), z(0), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(600), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(0), b_pick_up(600)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(500), z(0), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(500), b_pick_up(0)],  #
            [b_stop(0), b_layout(0), b_clear(0), b_enter(0), z(0), b_pick_up(500)]  #
        ]

        mode_index = self.__combo_modes.currentIndex()
        if mode_index >= len(modes):
            self.__log_management(10, "S_COF_6", "", "Wybrano mode o nmerze {}, a jest {}".format(mode_index, len(modes)))
            mode_index = 0
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