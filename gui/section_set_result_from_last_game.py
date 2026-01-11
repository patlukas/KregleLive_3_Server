from gui.setting_option import CheckboxActionAnalyzedMessage
from utils.messages import extract_lane_id_from_outgoing_message, prepare_message, encapsulate_message, \
    prepare_message_and_encapsulate

from PyQt5.QtWidgets import QGroupBox, QGridLayout, QLabel, QHBoxLayout
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class SectionSetResultFromLastGame(CheckboxActionAnalyzedMessage, QGroupBox):
    """
    """
    def __init__(self, parent):
        """
        """
        QGroupBox.__init__(self, "Wynik z elimiminacji", parent)
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Ustawianie wyniku z eliminacji",
            default_enabled=True
        )
        self.__parent = parent
        self.__number_of_lane = 0
        self.__round_in_block = -1
        self.__is_during_game = False
        self.__list_sum = []
        self.__list_set_input_value = []
        self.__mode = 2

    def _after_toggled(self):
        self.setVisible(self._is_enabled)
        self.__parent.adjustSize()

    def init(self, number_of_lane: int):
        self.__number_of_lane = number_of_lane
        self.__list_sum = [0 for _ in range(number_of_lane)]
        self.__list_set_input_value = [lambda value="": None for _ in range(number_of_lane)]
        self.__prepare_section()

    def __prepare_section(self):
        self.setToolTip("Dodanie wyniku z eliminacji do aktualnej gry.\nWyniki będą automatycznie przepisywane na odpowiednie tory, po otrzymaniu komunikatu o nowym torze.\n"
                        "Ustawianie wartości odbywa się tylko i wyłącznie w pierwszej wiadomości na torze.\n"
                        "Po otrzymaniu wiadomości, że będą próbne, wyniki zostaną wykasowane i wtedy można wprowadzić wyniki dotyczące następnego bloku.")
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
        combo_modes.currentIndexChanged.connect(self.__selected_mode)
        combo_modes.setCurrentIndex(self.__mode)
        layout.addWidget(combo_modes, 0, 0, 1, self.__number_of_lane)

        for i in range(self.__number_of_lane):
            pair_layout = QVBoxLayout()
            pair_layout.setSpacing(0)

            label = QLabel("Tor " + str(i + 1))
            label.setAlignment(Qt.AlignCenter)

            input_result = QLineEdit()
            input_result.setValidator(QIntValidator(0, 4095))
            input_result.setMaxLength(4)
            input_result.setFixedWidth(45)
            input_result.setAlignment(Qt.AlignCenter)
            input_result.textEdited.connect(lambda value, lane=i: self.__edited_current_additional_value(lane, value))

            self.__list_set_input_value[i] = lambda value=None, el=input_result, lane_id=i: self.__change_current_additional_value(el, lane_id, value)

            pair_layout.addWidget(label)
            pair_layout.addWidget(input_result)
            pair_layout.addStretch()

            layout.addLayout(pair_layout, 1, i)

        self.setLayout(layout)

    def __selected_mode(self, index: int):
        self.__mode = index

    def __edited_current_additional_value(self, lane_id, new_value):
        if not new_value:
            value_int = 0
        else:
            value_int = int(new_value)
        self.__set_current_additional_value(lane_id, value_int)

    def __change_current_additional_value(self, el, lane_id: int, value_int):
        if value_int is None:
            value_int = 0
            value_str = ""
        else:
            value_str = str(value_int)

        el.setText(value_str)
        self.__set_current_additional_value(lane_id, value_int)

    def __set_current_additional_value(self, lane_id: int, value: int):
        if value < 0 or value > 4095:
            value = 0

        self.__list_sum[lane_id] = value

    def __int_to_bytes_hex(self, val_int: int) -> bytes:
        if val_int < 0 or val_int > 4095:
            return b"000"

        value_hex = format(val_int, "03X")
        value_bytes = value_hex.encode()
        return value_bytes

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            3: b'____IG_________000_________\r'
            0: otherwise

        Activation conditions:
            In:
                b'____IG_________000_________\r'
            Out:
                b'____IG_________xyz_________\r - 'xyz' result from last game
        """
        if not self.is_enabled():
            return

        if message[4:5] == b"P":
            if not self.__is_during_game:
                self.__is_during_game = True
                if self.__round_in_block != -1:
                    # Replace values from next block to currnet block
                    # TODO or set empty value in input
                    for i in range(self.__number_of_lane):
                        self.__list_set_input_value[i]()
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
        Analyze a message received from the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        if message[4:6] == b"i0" or message[4:6] == b"p0":
            self.__is_during_game = False

    def __prepare_ig_messages(self, message: bytes):
        # TODO
        total_sum = int(message[15:18].decode(), 16)
        additional_sum = self.__get_sum_from_last_game(message)
        new_total_sum = total_sum + additional_sum
        new_total_sum_bytes = self.__int_to_bytes_hex(new_total_sum)
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
