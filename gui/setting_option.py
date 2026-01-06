from PyQt5.QtWidgets import QAction

from abc import ABCMeta, abstractmethod


class _BaseMenuSetting(metaclass=ABCMeta):
    """
    Abstract base class for a checkable QAction-based menu setting.
    """
    def __init__(self, label: str, default_enabled=True) -> None:
        """

        :param label <str> - Text displayed in the menu QAction
        :param default_enabled <bool=True> - Initial state of the setting
        """
        self._label = label
        self._is_enabled = default_enabled
        self._menu_action = None

    def _on_toggled(self, checked: bool) -> None:
        """
        This method is called whenever the QAction checked state changes,
        either due to user interaction or programmatic calls to setChecked().

        :param checked: <bool> - Current checked state of the QAction
        """
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

    def create_menu_action(self, parent=None):
        """
        Create and configure the QAction associated with this setting.
        The returned QAction is intended to be added to a QMenu.

        :param parent: Parent QObject (usually a QMenu or QMainWindow)
        :return: <QAction> Configured QAction instance
        """

        self._menu_action = QAction(self._label, parent)
        self._menu_action.setCheckable(True)
        self._menu_action.setChecked(self._is_enabled)
        self._menu_action.toggled.connect(lambda checked: self._on_toggled(checked))

        return self._menu_action

    def is_enabled(self) -> bool:
        """
        Return current logical state of the setting.

        :return: <bool> True if enabled, False otherwise
        """
        return self._is_enabled

    @abstractmethod
    def analyze_message_to_lane(self, message: bool):
        """
        Analyze a message being sent to the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        return [], [], [], []

    @abstractmethod
    def analyze_message_from_lane(self, message: bytes):
        """
        Analyze a message received from the lane.

        Subclasses must implement this method and decide whether
        to act based on the current enabled state.

        :param message: <bytes> Message to analyze (terminated with b"\r")
        """
        return [], [], [], []




