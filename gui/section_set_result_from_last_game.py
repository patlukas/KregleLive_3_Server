from gui.setting_option import CheckboxActionAnalyzedMessage
from utils.messages import extract_lane_id_from_outgoing_message, prepare_message, encapsulate_message, \
    prepare_message_and_encapsulate

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QHBoxLayout, QWidget, QComboBox, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIntValidator


class SectionSetResultFromLastGame(CheckboxActionAnalyzedMessage, QGroupBox):
    def __init__(self, parent):
        """
            self.__round_in_block - -1 - when is trial, 0 on first lane, 1 on second, ...
            self.__is_during_game - True after "IG" and "P", False after "p0" and "i0"
        """
        QGroupBox.__init__(self, "Wynik z elimiminacji", parent)
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Ustawianie wyniku z eliminacji",
            default_enabled=False
        )
        self.__parent = parent
        self.__number_of_lane = 0
        self.__round_in_block = -1
        self.__is_during_game = False
        self.__list_sum = []
        self.__list_sum_next = []
        self.__list_set_input_value = []
        self.__list_set_next_input_value = []
        self.__mode = 2

    def _after_toggled(self):
        self.setVisible(self._is_enabled)
        self.__parent.adjustSize()

    def init(self, number_of_lane: int):
        self.__number_of_lane = number_of_lane
        self.__list_sum = [0 for _ in range(number_of_lane)]
        self.__list_sum_next = [0 for _ in range(number_of_lane)]
        self.__list_set_input_value = [lambda value="": None for _ in range(number_of_lane)]
        self.__list_set_next_input_value = [lambda value="": None for _ in range(number_of_lane)]
        self.__prepare_section()

    def __prepare_section(self):
        self.setToolTip("Dodanie wyniku z eliminacji do aktualnej gry.\n\nWyniki będą automatycznie przepisywane na odpowiednie tory, po otrzymaniu komunikatu o kolejnym torze.\n"
                        "Ustawianie wartości odbywa się tylko i wyłącznie w pierwszej wiadomości na torze.\n\n"
                        "Po otrzymaniu wiadomości o próbnych, wyniki z rzędu 'Następny blok' zostaną przeniesione do 'Aktualny blok'.")
        old_layout = self.layout()
        if old_layout:
            QWidget().setLayout(old_layout)

        layout = QGridLayout()

        combo_modes = QComboBox()
        combo_modes.addItems([
            "Ustawienie wyniku na pierwszym torze (IG)",
            "Edycja wyniku na pierwszym torze (Z)",
            "[*] Ustawienie wyniku na każdym torze (IG)"
        ])
        combo_modes.currentIndexChanged.connect(self.__on_mode_selected)
        combo_modes.setCurrentIndex(self.__mode)
        layout.addWidget(combo_modes, 0, 0, 1, self.__number_of_lane+1)

        layout.addWidget(QLabel("Aktualny blok"), 2, 0)
        layout.addWidget(QLabel("Następny blok"), 3, 0)

        for i in range(self.__number_of_lane):
            label = QLabel("Tor " + str(i + 1))
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label, 1, 1 + i)

            line_edit = self.__create_value_editor(i, self.__list_sum, self.__list_set_input_value)
            layout.addWidget(line_edit, 2, 1 + i)

        for i in range(self.__number_of_lane):
            input_result_next = self.__create_value_editor(i, self.__list_sum_next, self.__list_set_next_input_value)
            layout.addWidget(input_result_next, 3, 1 + i)

        self.setLayout(layout)
        self.setVisible(self.is_enabled())

    def __create_value_editor(self, lane_id: int, stored_values: list, list_value_actions: list) -> QLineEdit:
        editor  = QLineEdit()
        editor.setValidator(QIntValidator(0, 4095))
        editor.setMaxLength(4)
        editor.setFixedWidth(60)
        editor.setAlignment(Qt.AlignCenter)

        editor .textEdited.connect(lambda value, lane=lane_id: self.__handle_user_value_edit(stored_values, lane, value))

        list_value_actions[lane_id] = lambda value=None, widget=editor , lane=lane_id: self.__update_editor_value(stored_values, widget, lane, value)

        return editor

    def __on_mode_selected(self, mode_index: int) -> None:
        self.__mode = mode_index

    def __handle_user_value_edit(self, stored_values: list, lane_id: int, text_value: str) -> None:
        value_int = int(text_value) if text_value else 0
        self.__set_lane_value(stored_values, lane_id, value_int)

    def __update_editor_value(self, stored_values: list, editor: QLineEdit, lane_id: int, value_int: int) -> None:
        if value_int is None:
            value_int = 0
            value_str = ""
        else:
            value_str = str(value_int)

        editor.setText(value_str)
        self.__set_lane_value(stored_values, lane_id, value_int)

    @staticmethod
    def __set_lane_value(stored_values: list, lane_id: int, value: int) -> None:
        if not 0 <= value <= 4095:
            value = 0

        stored_values[lane_id] = value

    @staticmethod
    def __int_to_hex_bytes(value_int: int) -> bytes:
        """
        <0      => b"000"
        0-4095  => b"000" - b"FFF"
        >4095   => b"000"
        """
        if not 0 <= value_int <= 4095:
            return b"000"

        return format(value_int, "03X").encode()

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            8: b'____IG_________000_________\r' and mode 1
            3: b'____IG_________000_________\r' and mode 0
            3: b'____IG_____________________\r' and mode 2
            1: b'____P_________\r'
            0: otherwise

        Activation conditions:
            In: (mode 1)
                b'____IG_________000_________\r'
            Out:
                [], [], [], [b'____IG_________xyz_________\r', Z] - 'xyz' result from last game

            In:
                b'____IG_____________________\r'
            Out:
                b'____IG_________xyz_________\r' - 'xyz' result from last game

            In:
                b'____P_________\r'
            Out:
                None
        """
        if not self.is_enabled():
            return

        if message[4:5] == b"P":
            if not self.__is_during_game:
                self.__is_during_game = True
                if self.__round_in_block != -1:
                    for i in range(self.__number_of_lane):
                        self.__list_set_input_value[i](self.__list_sum_next[i])
                        self.__list_set_next_input_value[i]()
                self.__round_in_block = -1
            return

        if message[4:6] == b"IG":
            if not self.__is_during_game:
                self.__is_during_game = True
                self.__round_in_block += 1
                self.__replace_additional_sum_between_lane()
            return self.__prepare_ig_messages(message)

    def analyze_message_from_lane(self, message: bytes):
        """
        Level of interference:
            1: b'____i0__\r'
            1: b'____p0__\r'
            0: otherwise

        Activation conditions:
            In: (mode 1)
                b'____i0__\r' || b'____p0__\r'
            Out:
                None
        """
        if message[4:6] == b"i0" or message[4:6] == b"p0":
            self.__is_during_game = False

    def __prepare_ig_messages(self, message: bytes):
        total_sum = int(message[15:18].decode(), 16)
        additional_sum = self.__get_sum_from_last_game(message)
        new_total_sum = total_sum + additional_sum
        new_total_sum_bytes = self.__int_to_hex_bytes(new_total_sum)

        if self.__mode == 0:
            if total_sum > 0:
                return

            message = message[:15] + new_total_sum_bytes + message[18:]
            message = prepare_message(message[:-2])
            return message

        if self.__mode == 1:
            if total_sum > 0:
                return

            message_z = message[:4] + b"Z000000000" + new_total_sum_bytes +  b"000000000000000"
            packet_ig = encapsulate_message(message)
            packet_z = prepare_message_and_encapsulate(message_z)
            return [], [], [], [packet_ig, packet_z]

        if self.__mode == 2:
            message = message[:15] + new_total_sum_bytes + message[18:]
            message = prepare_message(message[:-2])
            return message

    def __get_sum_from_last_game(self, message: bytes) -> int:
        lane_id = extract_lane_id_from_outgoing_message(message, self.__number_of_lane)
        if lane_id is None:
            return 0
        total_sum = self.__list_sum[lane_id]
        return total_sum

    def __replace_additional_sum_between_lane(self):
        if self.__round_in_block <= 0:
            return

        new_list = [0 for _ in range(self.__number_of_lane)]
        for i, v in enumerate(self.__list_sum):
            if self.__round_in_block % 2 == 1:
                new_i = i ^ 1
            else:
                new_i = (i + 2) % self.__number_of_lane
            if len(self.__list_sum) > new_i:
                new_list[new_i] = self.__list_sum[i]

        for i in range(self.__number_of_lane):
            self.__list_set_input_value[i](new_list[i])
