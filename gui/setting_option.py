from PyQt5.QtWidgets import QAction, QPushButton, QComboBox, QHBoxLayout, QLabel
import os
import shutil
import threading


from utils.messages import prepare_message_and_encapsulate, encapsulate_message, prepare_message, \
    extract_lane_id_from_incoming_message, extract_lane_id_from_outgoing_message


class CheckboxActionAnalyzedMessageBase:
    """
    Abstract base class for a checkable QAction-based menu setting.
    """
    def __init__(self, parent, label: str, default_enabled=True) -> None:
        """

        :param label <str> - Text displayed in the menu QAction
        :param default_enabled <bool=True> - Initial state of the setting
        """
        self._add_log = lambda a,b,c,d: None
        self._label = label
        self._is_enabled = default_enabled
        self._menu_action = QAction(self._label, parent)

        self._menu_action.setCheckable(True)
        self._menu_action.setChecked(self._is_enabled)
        self._menu_action.toggled.connect(lambda checked: self._on_toggled(checked))

    def _on_toggled(self, checked: bool) -> None:
        """
        This method is called whenever the QAction checked state changes,
        either due to user interaction or programmatic calls to setChecked().

        :param checked: <bool> - Current checked state of the QAction
        """
        self._is_enabled = checked
        self._after_toggled()

    def _after_toggled(self):
        pass

    def _init_action(self, new_state, on_add_message):
        self._add_log = on_add_message
        self.on_toggle(new_state)

    def on_toggle(self, new_state=None) -> None:
        """
        This method allows changing the setting state without requiring
        direct user interaction with the menu.

        :param new_state: <bool || None> - Desired state or None to toggle
        """
        if new_state is None:
            self._is_enabled = not self._is_enabled
        else:
            self._is_enabled = new_state

        if self._menu_action is not None:
            self._menu_action.setChecked(self._is_enabled)

    def get_menu_action(self):
        """
        :return: <QAction> Configured QAction instance
        """
        return self._menu_action

    def is_enabled(self) -> bool:
        """
        Return current logical state of the setting.

        :return: <bool> True if enabled, False otherwise
        """
        return self._is_enabled

    def analyze_message_to_lane(self, message: bool):
        """
        Analyze a message being sent to the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        return

    def analyze_message_from_lane(self, message: bytes):
        """
        Analyze a message received from the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        return


class CheckboxActionAnalyzedMessage(CheckboxActionAnalyzedMessageBase):
    def __init__(self, parent, label, default_enabled):
        super().__init__(parent, label, default_enabled)

    def init(self, new_state, on_add_message):
        self._init_action(new_state, on_add_message)


class SettingTurnOnPrinter(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible for enabling the printer
    when a 'IG' message is sent with disable printer.
    """
    def __init__(self, parent):
        super().__init__(parent,"Uruchom drukarkę przy meczówce", default_enabled=True)

    def analyze_message_to_lane(self, message: bytes):
        """
        Analyze an outgoing message and optionally inject
        a modified packet to enable the printer.

        Level of interference:
            2: b'____IG__________________0__\r'
            0: otherwise

        Activation conditions:
            In:
                b'____IG__________________0__\r'
            Out:
                b'____IG__________________1__\r'
        """
        if not self.is_enabled():
            return
        if len(message) < 28 or message[4:6] != b"IG":
            return
        if message[24:25] != b"0":
            return
        content_msg = message[:24] + b"1"
        return prepare_message(content_msg)


class SettingStartTimeInTrial(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible for add possibility to start time in trial.
    """
    def __init__(self, parent):
        super().__init__(parent,"Dodaj opcję włączenia czasu w próbnych", default_enabled=True)

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            9: b'____P_________\r' - every time
            0: otherwise

        Activation conditions:
            In:
                b'____P_________\r'
            Out:
                [], [], [], [b'____P_________\r', T41, T14]
        """
        if not self.is_enabled():
            return
        if len(message) != 15 or message[4:5] != b"P":
            return

        packet_trial = encapsulate_message(message, 3, -1)
        packet_pick_up = prepare_message_and_encapsulate(message[:4] + b"T41", 3, -1)
        packet_stop_time = prepare_message_and_encapsulate(message[:4] + b"T14", 9, 300)
        return [], [], [], [packet_trial, packet_pick_up, packet_stop_time]


class SettingStopCommunicationBeforeTrial(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible stop communication before new block.
    """
    def __init__(self, parent):
        super().__init__(parent,"Wstrzymuj kolejny blok", default_enabled=True)
        self._mode = 0
        self._active_lanes = set()
        self._stop_communication = False
        self._btn_temporary = None
        self._btn_main = None

    def communication_outgoing_is_enabled(self) -> bool:
        return not self._stop_communication

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            1: b'____P_________\r'
            0: Otherwise

        Activation conditions:
            In:
                b'____P_________\r'
            Out:
                None

        :logs: STOP_COM_STOP (5)
        """
        if message[4:5] == b"P":
            if self._mode == 0:
                return
            lane_id = extract_lane_id_from_outgoing_message(message)
            self._active_lanes.discard(lane_id)
            if self._mode == 1:
                if self.is_enabled():
                    self._add_log(5, "STOP_COM_STOP", "", "Zatrzymano komunikację")
                    self._stop_communication = True

                if len(self._active_lanes) > 0:
                    self._show_button(1, 2)
                    self._mode = 2
                else:
                    self._show_button(1, 3)
                    self._mode = 3

            elif self._mode == 2:
                if len(self._active_lanes) == 0:
                    self._show_button(2, 3)
                    self._mode = 3

    def analyze_message_from_lane(self, message: bytes):
        """
        Level of interference:
            1: b'____p0__\r'
            0: Otherwise

        Activation conditions:
            In:
                b'____p0__\r'
            Out:
                None
        """
        if message[4:6] == b"p0":
            if self._mode in [2, 3]:
                self._enable_communication()
            self._mode = 1
            lane_id = extract_lane_id_from_incoming_message(message)
            self._active_lanes.add(lane_id)
        return

    def prepare_button(self, parent):
        self._prepare_button_main(parent)
        self._prepare_button_temporary(parent)

    def _prepare_button_main(self, parent):
        self._btn_main = QPushButton("ROZPOCZNIJ KOLEJNY BLOK", parent)
        self._btn_main.setMinimumSize(570, 150)
        self._btn_main.move(0, 35)
        self._btn_main.setStyleSheet("""
            QPushButton {
                font-size: 20pt;
                font-weight: bold;
                background-color: #e74c3c;
                color: white;
                border: 4px solid #c0392b;
                border-radius: 20px;
                padding: 20px;
            }
            QPushButton:hover {
                background-color: #ff6e5d;
                border-color: #e74c3c;
            }
            QPushButton:pressed {
                background-color: #b0291b;
                border-style: inset;
            }
        """)
        self._btn_main.clicked.connect(lambda: self._enable_communication())
        self._btn_main.hide()

    def _prepare_button_temporary(self, parent):
        self._btn_temporary = QPushButton("\n\nROZPOCZNIJ KOLEJNY BLOK\n\n(Mogą jeszcze nie wszystkie tory być gotowe)", parent)
        self._btn_temporary.setMinimumSize(570, 150)
        self._btn_temporary.move(0, 35)
        self._btn_temporary.setStyleSheet("""
            QPushButton {
                font-size: 12pt;
                background-color: #979797;
                color: white;
                border: 4px solid #909090;
                border-radius: 10px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #afafaf;
                border-color: #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #606060;
                border-style: inset;
            }
        """)
        self._btn_temporary.clicked.connect(lambda: self._enable_communication())
        self._btn_temporary.hide()

    def _enable_communication(self):
        """
        :logs: STOP_COM_START (5)
        """
        if not self._stop_communication:
            self._add_log(5, "STOP_COM_START", "", "Wznowiono komunikację")
        self._btn_temporary.hide()
        self._btn_main.hide()
        if self._mode == 2:
            self._active_lanes.clear()
        self._mode = 0
        self._stop_communication = False

    def _show_button(self, old_mode, new_mode):
        if old_mode == 1 and new_mode == 2:
            if self.is_enabled():
                self._btn_temporary.show()
        elif old_mode == 1 and new_mode == 3:
            if self.is_enabled():
                self._btn_main.show()
        elif old_mode == 2 and new_mode == 3:
            self._btn_temporary.hide()
            if self.is_enabled():
                self._btn_main.show()


class SettingShowResultOnMonitorFromLastGame(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible show result from last block on monitor. (replace daten.ini)
    """
    def __init__(self, parent):
        """
        :list_path_to_lane_dir: list[str] - list with path to dir where is daten.ini
        """
        super().__init__(parent,"Pokaż wynik na monitorze z poprzedniej gry", default_enabled=True)
        self._file_name = "daten.ini"
        self._file_name_archive = "daten_last.ini"
        self._file_name_future = "daten_next.ini"
        self._list_path_to_lane_dir = []
        self._is_trial = False
        self._buffer_time_P = 0
        self._buffer_time_i0 = 0
        self._buffer_time_p1 = 0
        options = []
        for i in range(6):
            for j in range(0, 11, 1):
                for k in range(6):
                    options.append(["i0=" + str(i) + " P=" + str(j) + " p1=" + str(k), [i, j, k]])
        self._list_buffer_option = options
        self.layout_select_buffer = self._prepare_widget_select_buffer(parent, self._list_buffer_option)

    def _prepare_widget_select_buffer(self, parent, options):
        layout = QHBoxLayout()

        label = QLabel("Opóźnienie kopiowania plików na telewizorach (s)")
        layout.addWidget(label)

        combo = QComboBox(parent)

        for a, b in options:
            combo.addItem(a, b)

        combo.currentIndexChanged.connect(self._change_buffer_time)

        layout.addWidget(combo)

        return layout

    def _change_buffer_time(self, index):
        self._buffer_time_i0 = self._list_buffer_option[index][1][0]
        self._buffer_time_P = self._list_buffer_option[index][1][1]
        self._buffer_time_p1 = self._list_buffer_option[index][1][2]

    def set_list_path_to_lane_dir(self, list_path_to_lane_dir):
        self._list_path_to_lane_dir = list_path_to_lane_dir

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            1: b'____P_________\r'
            0: Otherwise

        Activation conditions:
            In:
                b'____P_________\r'
            Out:
                None
        """
        if not self.is_enabled():
            return

        if message[4:5] == b"P" and not self._is_trial:
            self._is_trial = True
            self.__copy_on_lanes(self._file_name, self._file_name_future, self._buffer_time_P)
            self.__copy_on_lanes(self._file_name_archive, self._file_name, self._buffer_time_P, True)

        return

    def analyze_message_from_lane(self, message: bytes):
        """
        Level of interference:
            1: b'____i0__\r'
            1: b'____p1__\r'
            0: Otherwise

        Activation conditions:
            In:
                b'____i0__\r'
                b'____p1__\r'
            Out:
                None
        """
        if not self.is_enabled():
            return

        if message[4:6] == b"i0":
            self._is_trial = False
            self.__copy_on_lanes(self._file_name, self._file_name_archive, self._buffer_time_i0)

        if message[4:6] == b"p1":
            self.__copy_on_lanes(self._file_name_future, self._file_name, self._buffer_time_p1, True)

        return

    def __copy_file(self, src, target, buffer_time, remove_src=False):
        threading.Timer(
            buffer_time,
            lambda s=src, t=target, r=remove_src: self.__copy_file_body(s, t, r)
        ).start()


    def __copy_file_body(self, src, target, remove_src=False):
        """
        :logs: ERROR_ACTION_MONITOR (10)
        """
        if not os.path.exists(src):
            return

        try:
            shutil.copy2(src, target)
            if remove_src:
                os.remove(src)
        except Exception as e:
            self._add_log(10, "ERROR_ACTION_MONITOR", "", "Błąd podczas kopiowania pliku: {} -> {} | {}".format(src, target, e))

    def __copy_on_lanes(self, src_name, target_name, buffer_time, remove_src=False):
        for s in self._list_path_to_lane_dir:
            src = os.path.join(s, src_name)
            target = os.path.join(s, target_name)
            self.__copy_file(src, target, buffer_time, remove_src)
