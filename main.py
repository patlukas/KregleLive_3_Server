from PyQt5.QtGui import QBrush

from connection_manager import ConnectionManager
from gui.section_lane_control_panel import SectionLaneControlPanel
from gui.section_clearoff_fast import SectionClearOffTest
from gui.setting_option import SettingTurnOnPrinter, SettingStartTimeInTrial, SettingStopCommunicationBeforeTrial, \
    SettingShowResultOnMonitorFromLastGame
from gui.socket_section import SocketSection
from log_management import LogManagement
from config_reader import ConfigReader, ConfigReaderError
from serial_port_manager import SerialPortManager, SerialPortManagementError
import subprocess
import sys
import os
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QWidget,
    QGroupBox,
    QLabel,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QComboBox,
    QMenuBar,
    QAction,
    QHeaderView,
    QMenu
)
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, Qt
from _thread import start_new_thread

APP_NAME = "KL3S"
APP_VERSION = "1.3.0"

class GUI(QDialog):
    """
        This class is used to initialize the program and manage all elements and UI/UX

        Logs:
            KEGELN_PATH_NOTSPECIFIED - 10 - The path to the Kegelna exe file was not specified - Set 'path_to_run_kegeln_program' in 'config.json'
            KEGELN_PATH_NOTEXISTS - 10 - Kegeln exe file not exists with this path - Set correct 'path_to_run_kegeln_program' in 'config.json'
            KEGELN_ERROR - 10 - Error running kegeln exe - Check if you have set the correct 'path_to_run_kegeln_program' and 'flags_to_run_kegeln_program' in 'config.json'
            CNF_READ_ERROR - 10 - An error occurred while reading the configuration, Check if the "config.json" file is complete
            COM_MNGR_ERROR - 10 - An error occurred while checkcom port (port is busy, not exists, etc)
            MAIN_____ERROR - 10 - Unexpected error while initialize program
            COM_MNGR - 2 - Informacje o portach COM (są zajęte, czy jest połączenie, istnieje, numer portu COM)
            CNF_READ - 2 - The configuration was read from the "config.json" file.
            KEGELN_RUN - 2 - Kegeln exe file was started
            DIR_SET - 0 - Home directory was set
            START - 0 - Program was started
    """
    def __init__(self):
        """
        self.__layout - <QVBoxLayout> The main vertical layout for the window.
        self.__log_management - <None | LogManagement> Placeholder for the log management object.
        self.__connection_manager - <None | ConnectionManager> Placeholder for the connection management object.
        self.__connect_list_layout - <None | QVBoxLayout> Placeholder for object with layouts describing the connection.
        self.__config - <None | dict> dict with configuration
        self.__table_logs - <None | QTableWidget> An object with a log table
        self.__table_lane_stat - <None | QTableWidget> An object with a lane stat table
        self.__label_errors - <None | QLabel> Label with number of errors
        self.__number_errors - <int> Number of errors
        self.__min_priority - <int <0, 10>> Minimum priority of displayed errors
        self.__show_logs - <bool> Show or hide the log table
        self.__show_lane_stat - <bool> Show or hide the lane stat table
        self.__priority_dropdown - <None | QComboBox> Priority list item to set __min_priority
        self.__timer_connect_list_layout - <QTimer> Timer for updating the connection list layout.
        self.__timer_update_table_logs <QTimer> Timer for updating the logs table.
        self.__timer_update_table_lane_stat <QTimer> Timer for updating table with lane stat
        self.__kegeln_program_has_been_started <bool> kegeln program has been started
        """
        super().__init__()
        self.__init_window()
        self.__layout = QVBoxLayout()
        self.setLayout(self.__layout)
        self.__config = None
        self.__log_management = None
        self.__connection_manager = None
        self.__connect_list_layout = None
        self.__table_logs = None
        self.__table_lane_stat = None
        self.__label_errors = None
        self.__number_errors = 0
        self.__min_priority = 1
        self.__show_logs = False
        self.__show_lane_stat = False
        self.__priority_dropdown = None
        self.__kegeln_program_has_been_started = False
        self.__socket_section = None
        self.__section_lane_control_panel = SectionLaneControlPanel()
        self.__section_clearoff_fast = SectionClearOffTest()

        self.__action_setting_turn_on_printer = SettingTurnOnPrinter(self)
        self.__action_setting_start_time_in_trial = SettingStartTimeInTrial(self)
        self.__action_setting_stop_communication = SettingStopCommunicationBeforeTrial(self)
        self.__action_show_result_from_last_block = SettingShowResultOnMonitorFromLastGame(self)

        self.__set_layout()
        self.__init_program()

        self.__timer_connect_list_layout = QTimer(self)
        self.__timer_connect_list_layout.timeout.connect(self.__update_connect_list_layout)
        self.__timer_connect_list_layout.start(1000)

        self.__timer_update_table_logs = QTimer(self)
        self.__timer_update_table_logs.timeout.connect(self.__update_table_logs)
        self.__timer_update_table_logs.start(1000)

        self.__timer_update_table_lane_stat = QTimer(self)
        self.__timer_update_table_lane_stat.timeout.connect(self.__update_table_lane_stat)
        if self.__show_lane_stat:
            self.__timer_update_table_lane_stat.start(500)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        The function intercepts the close signal and asks for confirmation

        :param event: The close event that is triggered when the window is requested to be closed.
        :return: None
        """
        if self.__kegeln_program_has_been_started:
            reply = QMessageBox.question(self, 'Potwierdź zamknięcie',
                                         'Czy na pewno chcesz zamknąć aplikację?\n\nJeżeli jest uruchoiona aplikacja '
                                         '"Zentral-PC Kegeln" to po wyłączeniu tego programu przestanie działać',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def __init_window(self) -> None:
        """
        Sets up main window application, including title, icon, window flags, minimum size, initial position, and layout

        :return: None
        """
        self.setWindowTitle("Kręgle Live - Serwer")
        self.setWindowIcon(QtGui.QIcon('icon/icon.ico'))
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setMinimumWidth(570)
        self.setMinimumHeight(300)
        self.move(300, 50)
        self.layout()

    def __init_program(self) -> None:
        """
        Initializes log management,reads configuration,manages serial ports,initializes connection and handles exception

        :return: None
        :logs: CNF_READ_ERROR (10), COM_MNGR_ERROR (10), MAIN_____ERROR (10), COM_MNGR (2), CNF_READ(2), START (0)
        """
        self.__log_management = LogManagement()
        self.__log_management.add_log(0, "START", "", "Aplikacja została uruchomiona")
        try:
            self.__set_working_directory()
            self.__config = ConfigReader().get_configuration()

            self.__min_priority = self.__config["min_log_priority"]
            if self.__priority_dropdown is not None:
                self.__priority_dropdown.setCurrentText(str(self.__min_priority))
            self.__update_table_logs(self.__min_priority)
            self.__update_table_lane_stat()

            self.__log_management.add_log(2, "CNF_READ", "", "Pobrano konfigurację")
            self.__log_management.set_minimum_number_of_lines_to_write(
                self.__config["minimum_number_of_lines_to_write_in_log_file"]
            )
            self.__com_result = SerialPortManager(self.__config).ports_com_management()
            if self.__com_result[0] > 0:
                self.__run_kegeln_program(self.__config["path_to_run_kegeln_program"],
                                          self.__config["flags_to_run_kegeln_program"])
            self.__log_management.add_log(2, "COM_MNGR", str(self.__com_result[0]), self.__com_result[1])

            self.__connection_manager = ConnectionManager(
                self.__config["com_x"],
                self.__config["com_y"],
                self.__config["com_timeout"],
                self.__config["com_write_timeout"],
                self.__log_management.add_log,
                self.__config["time_interval_break"],
                self.__config["max_waiting_time_for_response"],
                self.__config["critical_response_time"],
                self.__config["warning_response_time"],
                self.__config["number_of_lane"],
                self.__action_setting_stop_communication.communication_to_lane_is_enabled
            )
            self.__socket_section.set_default_address(self.__config["default_ip"], self.__config["default_port"])
            self.__socket_section.set_func_to_get_list_ip(self.__connection_manager.on_get_list_ip)
            self.__prepare_lane_stat_table(self.__config["number_of_lane"])
            self.__section_lane_control_panel.init(self.__config["number_of_lane"], self.__config["stop_time_deadline_buffer_s"], self.__log_management.add_log, self.__connection_manager.add_message_to_x)
            self.__section_clearoff_fast.init(self.__config["number_of_lane"], self.__log_management.add_log)
            self.__launch_startup_tools(self.__config["tools_to_run_on_startup"])

            self.__action_show_result_from_last_block.set_list_path_to_lane_dir(self.__config["list_path_to_daten_files_on_lane"])

            self.__action_setting_turn_on_printer.on_toggle(self.__config["enable_action_turn_on_printer"])
            self.__action_setting_start_time_in_trial.on_toggle(self.__config["enable_action_start_time_in_trial"])
            self.__action_setting_stop_communication.on_toggle(self.__config["enable_action_stop_communication_after_block"])
            self.__action_show_result_from_last_block.on_toggle(self.__config["enable_action_show_result_from_last_block"])

            self.__connection_manager.add_func_for_analyze_msg_to_recv(lambda msg: self.__section_clearoff_fast.analyze_message_from_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_recv(lambda msg: self.__section_lane_control_panel.analyze_message_from_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_recv(lambda msg: self.__action_setting_stop_communication.analyze_message_from_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_recv(lambda msg: self.__action_show_result_from_last_block.analyze_message_from_lane(msg))

            self.__connection_manager.add_func_for_analyze_msg_to_lane(lambda msg: self.__section_clearoff_fast.analyze_message_to_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_lane(lambda msg: self.__action_setting_turn_on_printer.analyze_message_to_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_lane(lambda msg: self.__action_setting_stop_communication.analyze_message_to_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_lane(lambda msg: self.__action_show_result_from_last_block.analyze_message_to_lane(msg))
            self.__connection_manager.add_func_for_analyze_msg_to_lane(lambda msg: self.__action_setting_start_time_in_trial.analyze_message_to_lane(msg))

            start_new_thread(self.__connection_manager.start, ())
        except ConfigReaderError as e:
            self.__log_management.add_log(10, "CNF_READ_ERROR", e.code, e.message)
        except SerialPortManagementError as e:
            self.__log_management.add_log(10, "COM_MNGR_ERROR", e.code, e.message)
        except Exception as e:
            self.__log_management.add_log(10, "MAIN_____ERROR", "", str(e))
        if self.__log_management is not None:
            self.__log_management.close_log_file()

    def __set_layout(self) -> None:
        """
        This function create all UI elements (button, table, layout, dropdown).

        :return: None
        """
        self.__socket_section = SocketSection(self.__on_create_server, self.__on_close_server)

        self.__layout.setMenuBar(self.__create_menu_bar())

        connect_list = QGroupBox("Komunikacja")
        self.__connect_list_layout = QVBoxLayout()
        connect_list.setLayout(self.__connect_list_layout)

        self.__label_errors = QLabel("Liczba błędów: " + str(self.__number_errors))

        col_config = QGroupBox("Ustawienia")
        col_config_layout = QVBoxLayout()
        col_config.setLayout(col_config_layout)

        dropdown_priority = QGroupBox("Minimalny priorytet")
        dropdown_priority_label = QHBoxLayout()
        dropdown_priority.setLayout(dropdown_priority_label)

        self.__priority_dropdown = QComboBox()

        for i in range(11):
            self.__priority_dropdown.addItem(str(i))
        self.__priority_dropdown.setCurrentText(str(self.__min_priority))

        dropdown_priority_label.addWidget(self.__priority_dropdown)

        self.__priority_dropdown.currentIndexChanged.connect(self.__update_table_logs)

        col_config_layout.addWidget(self.__label_errors)
        col_config_layout.addWidget(dropdown_priority)

        row1 = QWidget()
        row1_label = QHBoxLayout()
        row1.setLayout(row1_label)
        row1_label.addWidget(connect_list)
        row1_label.addWidget(col_config)
        self.__layout.addWidget(self.__socket_section)
        self.__layout.addWidget(row1)

        self.__table_logs = QTableWidget()
        self.__table_logs.setRowCount(0)
        self.__table_logs.setColumnCount(6)
        self.__table_logs.setHorizontalHeaderLabels(["Id", "Data", "Priorytet", "Kod", "Port", "Wiadomość"])
        self.__table_logs.verticalHeader().setVisible(False)
        self.__table_logs.setVisible(self.__show_logs)

        self.__layout.addWidget(self.__table_logs)
        self.__layout.setStretchFactor(self.__table_logs, 1)

        self.__table_lane_stat = QTableWidget()
        self.__layout.addWidget(self.__table_lane_stat)

        self.__layout.addWidget(self.__section_lane_control_panel)
        self.__layout.addWidget(self.__section_clearoff_fast)

        self.__update_connect_list_layout()

        self.__action_setting_stop_communication.prepare_button(self)

    def __create_menu_bar(self):
        menu_bar = QMenuBar(self)

        settings = menu_bar.addMenu("Ustawienia")
        settings.addAction(self.__action_setting_turn_on_printer.get_menu_action())
        settings.addAction(self.__action_setting_start_time_in_trial.get_menu_action())
        settings.addAction(self.__action_setting_stop_communication.get_menu_action())
        settings.addAction(self.__action_show_result_from_last_block.get_menu_action())

        ip_menu = menu_bar.addMenu("Adresy IP")
        ip_refresh_action = QAction("Odśwież listę adresów IP", self)
        ip_refresh_action.triggered.connect(self.__socket_section.refresh_list_with_ip_address)
        ip_menu.addAction(ip_refresh_action)

        queue_menu = menu_bar.addMenu("Kolejka")
        queue_clear_action = QAction("Wyczyść kolejkę wiadomości", self)
        queue_clear_action.triggered.connect(self.__on_clear_socket_queue)
        queue_menu.addAction(queue_clear_action)

        view_menu = menu_bar.addMenu("Widok")
        log_list_table = QAction("Lista logów", self)
        log_list_table.setCheckable(True)
        log_list_table.setChecked(self.__show_logs)
        log_list_table.triggered.connect(lambda checked: self.__on_show_logs(checked))
        view_menu.addAction(log_list_table)

        lane_stat_list_table = QAction("Historia czasów odpowiedzi torów", self)
        lane_stat_list_table.setCheckable(True)
        lane_stat_list_table.setChecked(self.__show_lane_stat)
        lane_stat_list_table.triggered.connect(lambda checked: self.__on_show_table_stat(checked))
        view_menu.addAction(lane_stat_list_table)

        lane_control_enter = QAction("Sterowanie torami - Enter", self)
        lane_control_enter.setCheckable(True)
        lane_control_enter.setChecked(False)
        lane_control_enter.triggered.connect(lambda checked: self.__on_show_lane_control("Enter", checked))
        view_menu.addAction(lane_control_enter)

        lane_control_time = QAction("Sterowanie torami - Czas stop", self)
        lane_control_time.setCheckable(True)
        lane_control_time.setChecked(False)
        lane_control_time.triggered.connect(lambda checked: self.__on_show_lane_control("Time", checked))
        view_menu.addAction(lane_control_time)

        clear_off = QAction("Zbierane na 3 rzuty", self)
        clear_off.setCheckable(True)
        clear_off.setChecked(False)
        clear_off.triggered.connect(lambda checked: self.__on_show_clear_off_fast(checked))
        view_menu.addAction(clear_off)

        self.__add_menu_with_tools_to_menu_bar(menu_bar)

        help_menu = menu_bar.addMenu("Pomoc")
        about_action = QAction("O aplikacji", self)
        about_action.triggered.connect(self.__show_about)
        help_menu.addAction(about_action)

        return menu_bar

    def __show_about(self):
        about_text = (
            "<h3>Kręgle Live - Serwer</h3>"
            "<p>Wersja: {}</p>".format(APP_VERSION) +
            "<p>Aplikacja wykonana w PyQt5.</p>"
        )
        QMessageBox.information(self, "O aplikacji", about_text)

    def __on_show_logs(self, show_logs: bool) -> None:
        """
        This function show and hide table with logs and show/hide btn to show/hide table with logs

        :param show_logs: <bool> true/false - show/hide table with logs
        :return: None
        """
        self.__show_logs = show_logs
        self.__table_logs.setVisible(self.__show_logs)
        self.adjustSize()

    def __on_show_table_stat(self, show: bool) -> None:
        self.__show_lane_stat = show
        self.__table_lane_stat.setVisible(show)
        if show:
            self.__timer_update_table_lane_stat.start(500)
        else:
            self.__timer_update_table_lane_stat.stop()
        self.adjustSize()

    def __on_show_lane_control(self, name_type: str, show: bool):
        self.__section_lane_control_panel.show_control_panel(name_type, show)
        self.adjustSize()

    def __on_show_clear_off_fast(self, show: bool):
        self.__section_clearoff_fast.show_control_panel(show)
        self.adjustSize()

    def __update_connect_list_layout(self) -> int:
        """
        Update list connected devices and received bytes.
        :return:
            -1 - UI is not ready, __connection_manager or __connect_list_layout is none
            <0, +int> - number of connected devices
        """
        if self.__connection_manager is None or self.__connect_list_layout is None:
            return -1

        while self.__connect_list_layout.count() > 0:
            item = self.__connect_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                item.layout().deleteLater()

        data = self.__connection_manager.get_info()
        number_of_connected_devices = 0
        for name, rec_communicates, rec_bytes, waiting_messages, duplicates in data:
            rec = ""
            if rec_communicates != "0" or rec_bytes != "0":
                rec = " ( " + rec_communicates + " | " + rec_bytes + " B )"
            if waiting_messages != "0":
                rec += " | ( " + waiting_messages + " w kolejce )"
            if duplicates != "0":
                rec += " | ( " + duplicates + " duplikatów )"
            label = QLabel(name + rec)
            self.__connect_list_layout.addWidget(label)
            number_of_connected_devices += 1
        return number_of_connected_devices

    def __update_table_logs(self, new_min_priority=None) -> int:
        """
        Update log table and error count display, filtering logs based on priority and updating the UI accordingly.

        :param new_min_priority: <None | int> - None - min_priority doesn't was changed, int <0, 10> new min priority
        :return:
                -1 - program is not ready to show logs
                 0 - does not show new logs, because the logs are hidden, or the user scrolled through the logs
                 1 - logs list was refreshed
        """
        if self.__log_management is None or self.__table_logs is None:
            return -1

        if new_min_priority is not None:
            self.__min_priority = int(new_min_priority)

        number_errors = 0
        data = self.__log_management.get_logs(self.__min_priority, 250, 100)
        for log in data:
            if int(log[2]) == 10:
                number_errors += 1
        self.__label_errors.setText("Liczba błędów: " + str(number_errors))

        vertical_scroll_bar = self.__table_logs.verticalScrollBar()
        current_scroll_position = vertical_scroll_bar.value()
        if current_scroll_position > 3 and new_min_priority is None or not self.__show_logs:
            return 0

        self.__table_logs.setRowCount(0)

        for index, log in enumerate(data):
            self.__table_logs.insertRow(index)
            for j, val in enumerate(log):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                if j < 5:
                    item.setTextAlignment(Qt.AlignCenter)
                self.__table_logs.setItem(index, j, item)
                if int(log[2]) == 10:
                    item.setBackground(QtGui.QColor(255, 100, 100))
                elif int(log[2]) >= 5:
                    item.setBackground(QtGui.QColor(255, 255, 225))
        self.__table_logs.resizeColumnsToContents()
        self.__adjust_table_width(self.__table_logs, 1000)
        return 1

    def __update_table_lane_stat(self) -> int:
        """
        Update lane stat table

        :return:
                -1 - program is not ready to show table stat
                 0 - table is hide
                 1 - lane stat table was refreshed
        """
        if self.__table_lane_stat is None or self.__config is None or self.__connection_manager is None:
            return -1

        if not self.__show_lane_stat:
            return 0

        data = self.__connection_manager.get_lane_response_stat()

        warning_col = 7
        critical_col = 8
        timeout_col = 9
        for lane_number, lane_data in enumerate(data):
            for j, val in enumerate(lane_data):
                item = QTableWidgetItem(str(val))
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignCenter)
                self.__table_lane_stat.setItem(lane_number, j, item)
                if j == warning_col:
                    if val > 0:
                        item.setBackground(QtGui.QColor(253, 253, 150))
                    else:
                        item.setBackground(QBrush(Qt.NoBrush))
                elif j == critical_col:
                    if val > 0:
                        item.setBackground(QtGui.QColor(255, 196, 157))
                    else:
                        item.setBackground(QBrush(Qt.NoBrush))
                elif j == timeout_col:
                    if val > 0:
                        item.setBackground(QtGui.QColor(255, 105, 97))
                    else:
                        item.setBackground(QBrush(Qt.NoBrush))
        self.__table_lane_stat.resizeColumnsToContents()
        return 1

    def __prepare_lane_stat_table(self, number_of_lane: int) -> int:
        """
        This method add rows, set name columns and rows, set tooltips

        :param number_of_lane: <int> how many rows must be added
        :return: -1 - table not exists, 1 - table was prepare to show data
        """
        if self.__table_lane_stat is None:
            return -1

        self.__table_lane_stat.setColumnCount(10)
        self.__table_lane_stat.setHorizontalHeaderLabels(
            ["Σ", "μ50", "μ50-100", "μ250", "μ1000", "μAll", "Max", "Warn", "Critical", "Timeout"])
        self.__table_lane_stat.setVisible(self.__show_lane_stat)
        warning_time = int(self.__config["warning_response_time"] * 1000)
        critical_time = int(self.__config["critical_response_time"] * 1000)
        timeout_time = int(self.__config["max_waiting_time_for_response"] * 1000)
        tooltips = [
            "Ilość oebranych wiadomości",
            "Średni czas w milisekundach oczekiwania na wiadomość z 50 ostatnich razy",
            "Średni czas w milisekundach oczekiwania na wiadomość z przedostatnich 50 razy",
            "Średni czas w milisekundach oczekiwania na wiadomość z 250 ostatnich razy",
            "Średni czas w milisekundach oczekiwania na wiadomość z 1000 ostatnich razy",
            "Średni czas w milisekundach oczekiwania na wiadomość ze wszystkich razy",
            "Maksymalny czas w milisekundach oczekiwania",
            "Liczba warningów z powodu długiego czekania (ponad {}ms)".format(warning_time),
            "Liczba krytycznie długich oczekiwań (ponad {}ms)".format(critical_time),
            "Liczba niedoczekania się odpowiedzi (czekano {}ms)".format(timeout_time)
        ]

        for col, tooltip in enumerate(tooltips):
            self.__table_lane_stat.horizontalHeaderItem(col).setToolTip(tooltip)
        self.__layout.addWidget(self.__table_lane_stat)
        self.__table_lane_stat.setVisible(self.__show_lane_stat)

        self.__table_lane_stat.setContextMenuPolicy(Qt.CustomContextMenu)
        self.__table_lane_stat.customContextMenuRequested.connect(self.__show_context_menu_in_lane_stat)

        for i in range(number_of_lane):
            self.__table_lane_stat.insertRow(i)
        row_labels = ["Tor" + str(i+1) for i in range(number_of_lane)]
        self.__table_lane_stat.setVerticalHeaderLabels(row_labels)
        self.__table_lane_stat.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.__table_lane_stat.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.__table_lane_stat.resizeRowsToContents()
        QTimer.singleShot(100, lambda: (
                self.__adjust_table_height(self.__table_lane_stat, 0),
                self.__adjust_table_width(self.__table_lane_stat, 0)
            )
        )
        return 1

    def __adjust_table_width(self, table: QTableWidget, max_width: int) -> None:
        total_width = 0

        for col in range(table.columnCount()):
            total_width += table.columnWidth(col)

        total_width += table.verticalHeader().width()
        total_width += table.frameWidth() * 2

        if table.verticalScrollBar().isVisible():
            total_width += table.verticalScrollBar().width()

        if total_width > max_width > 0:
            total_width = max_width

        table.setFixedWidth(total_width)
        self.adjustSize()

    def __adjust_table_height(self, table: QTableWidget, max_height: int) -> None:
        row_count = table.rowCount()
        row_height = table.rowHeight(0)
        header_height = table.horizontalHeader().height()
        margins = table.contentsMargins()
        margins_height = margins.top() + margins.bottom()
        total_height = row_count * row_height + header_height + margins_height
        if total_height > max_height > 0:
            total_height = max_height
        table.setFixedHeight(total_height)
        self.adjustSize()

    def __show_context_menu_in_lane_stat(self, position):
        menu = QMenu(self)

        delete_max_action = QAction("Wyczyść kolumnę Max", self)
        delete_max_action.triggered.connect(lambda: self.__connection_manager.clear_lane_stat("Max"))

        delete_warn_action = QAction("Wyczyść kolumny z ostrzeżeniami", self)
        delete_warn_action.triggered.connect(lambda: self.__connection_manager.clear_lane_stat("Warn"))

        delete_all_action = QAction("Wyczyść całą tabelę", self)
        delete_all_action.triggered.connect(lambda: self.__connection_manager.clear_lane_stat("All"))

        menu.addAction(delete_max_action)
        menu.addAction(delete_warn_action)
        menu.addAction(delete_all_action)

        menu.exec_(self.__table_lane_stat.viewport().mapToGlobal(position))

    def __set_working_directory(self) -> None:
        """
        Set the working directory to the directory where the executable or script is located.
        
        :return: None
        :logs: DIR_SET (0)
        """
        if hasattr(sys, 'frozen'):
            exe_directory = os.path.dirname(sys.executable)
        else:
            exe_directory = os.path.dirname(os.path.abspath(__file__))
        os.chdir(exe_directory)
        self.__log_management.add_log(0, "DIR_SET", "", "Katalog domowy to {}".format(exe_directory))

    def __run_kegeln_program(self, path: str, flags: str) -> str:
        """
        This method check path to exe file and run this file with flags.

        :param path: <str> path to kegeln.exe file
        :param flags: <str> flags with which to run the exe file
        :return: <str> Error message or if "" this mean everything was ok
        :logs: KEGELN_PATH_NOTSPECIFIED (10), KEGELN_PATH_NOTEXISTS (10), KEGELN_ERROR (10), KEGELN_RUN (2)
        """
        if path == "":
            self.__log_management.add_log(10, "KEGELN_PATH_NOTSPECIFIED", "", "Kegeln's path file not specified")
            return "Kegeln's path file not specified"
        if not os.path.isfile(path):
            self.__log_management.add_log(10, "KEGELN_PATH_NOTEXISTS", "",
                                          "Kegeln exe file not exists with this path")
            return "Kegeln exe file not exists with this path"
        try:
            subprocess.Popen(path + " " + flags, shell=True)
        except subprocess.CalledProcessError as e:
            self.__log_management.add_log(10, "KEGELN_ERROR", "", str(e))
            return str(e)
        self.__kegeln_program_has_been_started = True
        self.__log_management.add_log(2, "KEGELN_RUN", "", "Kegeln.exe run")
        return ""

    def __add_menu_with_tools_to_menu_bar(self, menu_bar):
        tools_dir = "Tools"
        if not os.path.exists(tools_dir):
            os.makedirs(tools_dir)

        try:
            tools_files = os.listdir(tools_dir)
        except Exception as e:
            return

        if len(tools_files) == 0:
            return

        view_menu = menu_bar.addMenu("Narzędzia")
        for file in tools_files:
            file_path = os.path.join(tools_dir, file)
            option_name = file.replace(".lnk", "")
            tool_action = QAction(option_name, self)
            tool_action.triggered.connect(lambda: self.__launch_tool(file_path))
            view_menu.addAction(tool_action)

    def __launch_startup_tools(self, list_name_tools):
        for name_tool in list_name_tools:
            file_path = os.path.join("Tools", name_tool + ".lnk")
            self.__launch_tool(file_path)

    def __launch_tool(self, file_path):
        try:
            if os.name == 'nt':
                os.startfile(file_path)
        except FileNotFoundError as e:
            self.__log_management.add_log(10, "TOOL_RUN_ERROR", "NO_FILE", "Nie można uruchomić narzędzia {}, bo nie ma takiego pliku:  {}".format(file_path, e))
        except OSError as e:
            self.__log_management.add_log(10, "TOOL_RUN_ERROR", "OSError", "Nie można uruchomić narzędzia {}, bo plik prowadzi do nikąd:  {}".format(file_path, e))
        except Exception as e:
            self.__log_management.add_log(10, "TOOL_RUN_ERROR", "", "Nie można uruchomić narzędzia {}: {} {}".format(file_path, type(e).__name__, e))

    def __on_clear_socket_queue(self) -> None:
        """
        This method clear socket queue

        :return: None
        """
        if self.__connection_manager is not None:
            if self.__connection_manager.on_clear_sockets_queue() > 0:
                self.__update_connect_list_layout()

    def __on_create_server(self, ip, port):
        """
        This method create server TCP if exists self.__connection_manager.

        :param ip: <str> server ip address
        :param port: <int> port where server will listen (0-65535)
        :return: True
        :return: True
        :raise: SocketsManagerError
        """
        if self.__connection_manager is not None:
            self.__connection_manager.on_create_server(ip, port)

    def __on_close_server(self):
        """
        This method close server if exists self.__connection_manager.

        :return: True - closing was ended successfully, False - was error while closing server socket
        """
        if self.__connection_manager is not None:
            self.__connection_manager.on_close_server()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    ex.show()
    sys.exit(app.exec_())
