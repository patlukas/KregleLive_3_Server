from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton, QCheckBox, QLabel, QHBoxLayout, QComboBox
from PyQt5.QtCore import Qt

class SectionClearOffTest(QGroupBox):

    def __init__(self):
        """
        TODO: describe variables
        """
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
        self.__list_actually_layout = []
        self.__list_last_layout = []
        self.__max_throw_to_layout = 3

    def init(self, number_of_lane: int, log_management):
        self.__log_management = log_management
        for i in range(number_of_lane):
            self.__list_throw_to_current_layout.append(0)
            self.__list_count_clear_off_finish.append(0)
            self.__list_count_full_throws.append(0)
            self.__list_count_all_throws.append(0)
            self.__list_actually_layout.append([0,0])
            self.__list_last_layout.append([0,0])
        self.__box = self.__get_panel(number_of_lane)
        self.__layout.addWidget(self.__box)

    def __get_panel(self, number_of_lane):
        box = QGroupBox("")
        layout = QGridLayout()

        self.__combo_modes = QComboBox()
        self.__combo_modes.addItems([
            "Tryb 43: Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",
            "Tryb 43.A: (z podniesieniem i 0ms) Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",
            "Tryb 43.B: (z podniesieniem i 200ms) Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",
            "Tryb 43.C: (z podniesieniem i 400ms) Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",
            "Tryb 43.D: (z podniesieniem i 600ms) Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",
            "Tryb 43.E: (z podniesieniem i 800ms) Stop(0)   Z_1(0)    Korekta(0)   C(0)   Enter(0)   Podnies(800) =  800",

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
        """
        Level of interference:
            8: b'____w_____________________________\r' & 3 throw to layout & enable full layout after 3 throw
            1: b'____i0__\r'
            0: otherwise

        Activation conditions:
            In:
                b'____i0__\r'
            Out:
                None
            In:
                b'____w_____________________________\r' in place 'w' can be 'g', 'h', 'k', 'f'
            Out:
                None - if the full layout is not set
                [set_full_layout], [], [], [b'____w_____________________________\r'] - otherwise

        """
        if msg[4:6] == b"i0":
            lane = int(msg[3:4])
            self.__log_management(5, "S_COF_1", "", "Odebrano wiadomość i0 a torze '{}'({})".format(lane, msg ))
            if lane >= len(self.__list_throw_to_current_layout):
                return
            self.__checkboxes[0][lane].setChecked(self.__checkboxes[1][lane].isChecked())
            self.__checkboxes[1][lane].setChecked(False)
            self.__list_throw_to_current_layout[lane] = 0
            self.__list_count_clear_off_finish[lane] = 0
            self.__list_actually_layout[lane] = [0, 100] # TODO
            self.__list_count_all_throws[lane] = 0 # then in trial after 3x 0 this function not will set full layout
            self.__actualize_label(lane)
            return
        if msg[4:5] in [b"w", b"g", b"h", b"f", b"k"]:
            lane = int(msg[3:4])
            if lane >= len(self.__list_throw_to_current_layout):
                return
            throw_number = int(msg[5:8], 16)
            self.__log_management(4, "S_COF_2", "", "Odebrano wiadomość o rzucie {} na torze '{}'({})".format(throw_number, lane, msg))
            if self.__list_count_all_throws[lane] == 0:
                self.__log_management(3, "S_COF_14", "", "Są próbne: jest rzut '{}'".format(throw_number))
                return

            if throw_number < self.__list_actually_layout[lane][0]:
                self.__list_actually_layout[lane][0] = self.__list_last_layout[lane][0]
                self.__list_actually_layout[lane][1] = self.__list_last_layout[lane][1]

            if throw_number <= self.__list_count_full_throws[lane]:
                self.__log_management(3, "S_COF_12", "", "Są jeszcze pełne: jest rzut '{}', a pełne trwają {} rzutów".format(throw_number, self.__list_count_full_throws[lane]))
                return
            if throw_number >= self.__list_count_all_throws[lane]:
                self.__log_management(3, "S_COF_13", "", "Gra na torze się zakończyła: jest rzut '{}', a pełne trwają {} rzutów".format(throw_number, self.__list_count_full_throws[lane]))
                return
            next_layout = msg[17:20]
            fallen_pins = msg[26:29]

            if next_layout == b"000" and fallen_pins != b"000":
                self.__list_last_layout[lane][0] = self.__list_actually_layout[lane][0]
                self.__list_last_layout[lane][1] = self.__list_actually_layout[lane][1]
                self.__list_actually_layout[lane] = [throw_number, throw_number + self.__max_throw_to_layout]
                self.__log_management(5, "S_COF_3", "", "Na torze {} dobito układ, więc actually_layout to [{}, {}]".format(
                    lane, self.__list_actually_layout[lane][0], self.__list_actually_layout[lane][1]))

            # if next_layout != b"000" or fallen_pins == b"000":
            #     self.__list_throw_to_current_layout[lane] += 1
            # else:
            #     self.__list_throw_to_current_layout[lane] = 0
            # self.__log_management(5, "S_COF_3", "", "Na torze {} będzie rzut numer {} do układu".format(lane, self.__list_throw_to_current_layout[lane]+1))
            self.__actualize_label(lane)
            if throw_number == self.__list_actually_layout[lane][1]:
                self.__list_last_layout[lane][0] = self.__list_actually_layout[lane][0]
                self.__list_last_layout[lane][1] = self.__list_actually_layout[lane][1]
                self.__list_actually_layout[lane] = [throw_number, throw_number + self.__max_throw_to_layout]
                self.__log_management(5, "S_COF_3", "", "Na torze {} ustawi się pełen układ, a actually_layout to [{}, {}]".format(
                    lane, self.__list_actually_layout[lane][0], self.__list_actually_layout[lane][1]))
                self.__actualize_label(lane)
                if self.__checkboxes[0][lane].isChecked():
                    return self.__analyse_max_throw_clearoff(lane, msg)
            else:
                return
        return

    def analyze_message_to_lane(self, msg):
        """
        Level of interference:
            1: b'____IG_____________________\r'
            0: Otherwise

        Activation conditions:
            In:
                b'____IG_____________________\r'
            Out:
                None
        """
        if msg[4:6] == b"IG":
            lane = int(msg[1:2])
            self.__log_management(5, "S_COF_10", "", "Odebrano wiadomość IG na torze '{}'({})".format(lane, msg ))
            if lane >= len(self.__list_throw_to_current_layout):
                return

            count_full_throw = int(msg[6:9], 16)
            count_clear_off_throw = int(msg[9:12], 16)
            self.__list_count_full_throws[lane] = count_full_throw
            self.__list_count_all_throws[lane] = count_full_throw + count_clear_off_throw
            self.__list_actually_layout[lane] = [0, count_full_throw + self.__max_throw_to_layout]
            self.__list_last_layout[lane] = [0, count_full_throw + self.__max_throw_to_layout]
            self.__log_management(5, "S_COF_11", "", "Na torze '{}' włączono meczówkę na {}+{} rzutów".format(lane, count_full_throw, count_clear_off_throw))
            self.__actualize_label(lane)
            return
        return

    def __analyse_max_throw_clearoff(self, lane, message):
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

        pins = self.__count_beaten_pins(next_layout)
        total_sum_1 = self.__add_to_hex(total_sum, pins)
        lane_sum_1 = self.__add_to_hex(lane_sum, pins)

        z_1 = lambda time_wait=-1, priority=5: self.__on_get_message(
            message_head +
            b"Z" +
            number_of_throw +
            last_throw_result +
            lane_sum_1 +
            total_sum_1 +
            next_layout +
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
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_pick_up(0, 9), b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43A
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_pick_up(0, 9), b_stop(200), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43B
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_pick_up(0, 9), b_stop(400), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43C
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_pick_up(0, 9), b_stop(600), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43D
            [
                [b_stop(0), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
                [b_pick_up(0, 9), b_stop(800), z_1(0), b_layout(0), b_clear(0), b_enter(0), b_pick_up(800)],
            ],  # Tryb 43E
        ]

        mode_index = self.__combo_modes.currentIndex()
        if mode_index >= len(modes):
            self.__log_management(10, "S_COF_6", "", "Wybrano mode o nmerze {}, a jest {}".format(mode_index, len(modes)))
            mode_index = 0
        self.__log_management(3, "S_COF_5", "", "Do ustawienia pełnego ukłądu użyto metody numer {}".format(mode_index))
        mode_of_mode = 0
        if fallen_pins == b"000":
            mode_of_mode = 1
            self.__log_management(4, "S_COF_6", "", "Do ustawienia pełnego układu zostanie użyty mode dla dziury")
        else:
            self.__log_management(4, "S_COF_6", "", "Do ustawienia pełnego układu zostanie użyty mode dla zbitych kręgli")
        return modes[mode_index][mode_of_mode], []

    def __on_get_message(self, message, priority=5, time_wait=-1):
        msg = message + self.__calculate_control_sum(message) + b"\r"
        return {"message": msg, "time_wait": time_wait, "priority": priority}

    @staticmethod
    def __add_to_hex(hex_bytes, x):
        hex_str = hex_bytes.decode('Windows-1250')
        hex_value = int(hex_str, 16)
        new_hex_value = hex_value + x

        new_hex_str = hex(new_hex_value)[2:].upper().zfill(3)
        new_hex_bytes = new_hex_str.encode('Windows-1250')

        return new_hex_bytes

    @staticmethod
    def __count_beaten_pins(layout):
        hex_str = layout.decode('Windows-1250')
        value = int(hex_str, 16)
        ones_count = bin(value).count('1')
        return ones_count

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
        self.__labels[lane].setText(str(self.__list_actually_layout[lane][1]) + " | " + str(self.__list_count_clear_off_finish[lane]))