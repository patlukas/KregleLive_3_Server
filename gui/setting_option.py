from PyQt5.QtWidgets import QAction

from abc import ABCMeta, abstractmethod

from utils.messages import prepare_message_and_encapsulate, encapsulate_message


class _BaseMenuSetting(metaclass=ABCMeta):
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
        return [], [], [], []

    def analyze_message_from_lane(self, message: bytes):
        """
        Analyze a message received from the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        return [], [], [], []


class SettingTurnOnPrinter(_BaseMenuSetting):
    """
   Menu setting responsible for enabling the printer
   when a 'IG' message is sent with disable printer.
   """
    def __init__(self, parent):
        _BaseMenuSetting.__init__(
            self,
            parent,
            "Uruchom drukarkę przy meczówce",
            default_enabled=True
        )

    def analyze_message_to_lane(self, message: bytes):
        """
        Analyze an outgoing message and optionally inject
        a modified packet to enable the printer.

        Activation conditions:
            In:
                b'____IG__________________0__\r'
            Out:
                [], [], [], [b'____IG__________________1__\r']
        """
        if not self.is_enabled():
            return [], [], [], []
        if len(message) < 28 or message[4:6] != b"IG":
            return [], [], [], []
        if message[24:25] != b"0":
            return [], [], [], []
        content_msg = message[:24] + b"1"
        packet = prepare_message_and_encapsulate(content_msg, 3, -1) # TODO: can a fixed value (e.g. 250) be used instead of the default -1?
        return [], [], [], [packet]


class SettingStartTimeInTrial(_BaseMenuSetting):
    """
    Menu setting responsible for add possibility to start time in trial.
    """
    def __init__(self, parent):
        _BaseMenuSetting.__init__(
            self,
            parent,
            "Dodaj opcję włączenia czasu w próbnych",
            default_enabled=True
        )

    def analyze_message_to_lane(self, message: bytes):
        """
        Activation conditions:
            In:
                b'____P_________\r'
            Out:
                [], [], [], [b'____P_________\r', T41, T14]
        """
        if not self.is_enabled():
            return [], [], [], []
        if len(message) != 15 or message[4:5] != b"P":
            return [], [], [], []

        packet_trial = encapsulate_message(message, 3, -1) # TODO: can a fixed value (e.g. 250) be used instead of the default -1?
        packet_pick_up = prepare_message_and_encapsulate(message[:4] + b"T41", 3, -1)
        packet_stop_time = prepare_message_and_encapsulate(message[:4] + b"T14", 9, 300)
        return [], [], [], [packet_trial, packet_pick_up, packet_stop_time]