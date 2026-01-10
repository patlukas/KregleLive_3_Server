from PyQt5.QtWidgets import QAction, QPushButton
import os
import shutil

from utils.messages import prepare_message_and_encapsulate, encapsulate_message, prepare_message


class CheckboxActionAnalyzedMessage:
    """
    Abstract base class for a checkable QAction-based menu setting.
    """
    def __init__(self, parent, label: str, default_enabled=True) -> None:
        """

        :param label <str> - Text displayed in the menu QAction
        :param default_enabled <bool=True> - Initial state of the setting
        """
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
        print(self._label, checked)
        self._is_enabled = checked
        self._after_toggled()

    def _after_toggled(self):
        pass

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


class SettingTurnOnPrinter(CheckboxActionAnalyzedMessage):
    """
   Menu setting responsible for enabling the printer
   when a 'IG' message is sent with disable printer.
   """
    def __init__(self, parent):
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Uruchom drukarkę przy meczówce",
            default_enabled=True
        )

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
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Dodaj opcję włączenia czasu w próbnych",
            default_enabled=True
        )

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

        packet_trial = encapsulate_message(message, 3, -1) # TODO: can a fixed value (e.g. 250) be used instead of the default -1?
        packet_pick_up = prepare_message_and_encapsulate(message[:4] + b"T41", 3, -1)
        packet_stop_time = prepare_message_and_encapsulate(message[:4] + b"T14", 9, 300)
        return [], [], [], [packet_trial, packet_pick_up, packet_stop_time]


class SettingStopCommunicationBeforeTrial(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible stop communication before new block.
    """
    def __init__(self, parent):
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Wstrzymuj kolejny blok",
            default_enabled=True
        )
        self._was_trial_end = False
        self._stop_communication = False
        self._btn_enable_communication = None

    def communication_to_lane_is_enabled(self) -> bool:
        return not self._stop_communication

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            0

        Activation conditions:
            In:
                b'____P_________\r'
            Out:
                None
        """
        if not self._was_trial_end:
            return
        if len(message) != 15 or message[4:5] != b"P":
            return

        self._was_trial_end = False
        if self.is_enabled():
            self._stop_communication = True
            self._btn_enable_communication.show()

        return

    def analyze_message_from_lane(self, message: bytes):
        """
        Level of interference:
            0

        Activation conditions:
            In:
                b'____p0__\r'
            Out:
                None
        """
        if len(message) != 9 or message[4:6] != b"p0":
            return
        self._was_trial_end = True
        return

    def prepare_button(self, parent):
        self._btn_enable_communication = QPushButton("ROZPOCZNIJ KOLEJNY BLOK", parent)
        self._btn_enable_communication.setMinimumSize(570, 200)
        self._btn_enable_communication.setStyleSheet("""
            QPushButton {
                font-size: 20pt;
                font-weight: bold;
                background-color: #e74c3c;
                color: white;
                border: 4px solid #c0392b;
                border-radius: 20px;
                padding: 20px;
                margin-top: 50px;
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
        self._btn_enable_communication.clicked.connect(lambda: self._on_enable_communication())
        self._btn_enable_communication.hide()

    def _on_enable_communication(self):
        self._btn_enable_communication.hide()
        self._stop_communication = False


class SettingShowResultOnMonitorFromLastGame(CheckboxActionAnalyzedMessage):
    """
    Menu setting responsible show result from last block on monitor. (replace daten.ini)
    """
    def __init__(self, parent):
        """
        :list_path_to_lane_dir: list[str] - list with path to dir where is daten.ini
        """
        CheckboxActionAnalyzedMessage.__init__(
            self,
            parent,
            "Pokaż wynik na monitorze z poprzedniej gry",
            default_enabled=True
        )
        self._file_name = "daten.ini"
        self._file_name_archive = "daten_last.ini"
        self._file_name_future = "daten_next.ini"
        self._list_path_to_lane_dir = []
        self._is_trial = False

    def set_list_path_to_lane_dir(self, list_path_to_lane_dir):
        self._list_path_to_lane_dir = list_path_to_lane_dir

    def analyze_message_to_lane(self, message: bytes):
        """
        Level of interference:
            0

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
            self.__copy_on_lanes(self._file_name, self._file_name_future)
            self.__copy_on_lanes(self._file_name_archive, self._file_name, True)

        return

    def analyze_message_from_lane(self, message: bytes):
        """
        Level of interference:
            0

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
            self.__copy_on_lanes(self._file_name, self._file_name_archive)

        if message[4:6] == b"p1":
            self.__copy_on_lanes(self._file_name_future, self._file_name, True)

        return

    def __copy_file(self, src, target, remove_src=False):
        if not os.path.exists(src):
            print("Brak pliku:", src)
            return

        try:
            shutil.copy2(src, target)
            print("Skopiowano:", src, "->", target)
            if remove_src:
                os.remove(src)
                print("Del", src)
        except Exception as e:
            print("Błąd kopiowania:", src, e)

    def __copy_on_lanes(self, src_name, target_name, remove_src=False):
        for s in self._list_path_to_lane_dir:
            src = os.path.join(s, src_name)
            target = os.path.join(s, target_name)
            self.__copy_file(src, target, remove_src)
