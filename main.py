from connection_manager import ConnectionManager
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
    QPushButton,
    QComboBox
)
from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import QTimer, Qt
from _thread import start_new_thread


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
        self.__table_logs - <None | QTableWidget> An object with a log table
        self.__label_errors - <None | QLabel> Label with number of errors
        self.__number_errors - <int> Number of errors
        self.__min_priority - <int <0, 10>> Minimum priority of displayed errors
        self.__show_logs - <bool> Show or hide the log table
        self.__btn_logs_show - <None | QPushButton> Button showing a table with logs
        self.__btn_logs_hide - <None | QPushButton> Button hiding a table with logs
        self.__priority_dropdown - <None | QComboBox> Priority list item to set __min_priority
        self.__timer_connect_list_layout - <QTimer> Timer for updating the connection list layout.
        self.__timer_update_table_logs <QTimer> Timer for updating the logs table.
        self.__kegeln_program_has_been_started <bool> kegeln program has been started
        """
        super().__init__()
        self.__init_window()
        self.__layout = QVBoxLayout()
        self.setLayout(self.__layout)
        self.__log_management = None
        self.__connection_manager = None
        self.__connect_list_layout = None
        self.__table_logs = None
        self.__label_errors = None
        self.__number_errors = 0
        self.__min_priority = 1
        self.__show_logs = False
        self.__btn_logs_show = None
        self.__btn_logs_hide = None
        self.__priority_dropdown = None
        self.__kegeln_program_has_been_started = False

        self.__set_layout()
        self.__init_program()

        self.__timer_connect_list_layout = QTimer(self)
        self.__timer_connect_list_layout.timeout.connect(self.__update_connect_list_layout)
        self.__timer_connect_list_layout.start(1000)

        self.__timer_update_table_logs = QTimer(self)
        self.__timer_update_table_logs.timeout.connect(self.__update_table_logs)
        self.__timer_update_table_logs.start(1000)

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
        self.setMinimumWidth(400)
        self.setMinimumHeight(225)
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

            self.__log_management.add_log(2, "CNF_READ", "", "Pobrano konfigurację")
            self.__log_management.set_minimum_number_of_lines_to_write(
                self.__config["minimum_number_of_lines_to_write_in_log_file"]
            )
            self.__com_result = SerialPortManager(self.__config).ports_com_management()
            if self.__com_result[0] > 0:
                self.__run_kegeln_program(self.__config["path_to_run_kegeln_program"],
                                          self.__config["flags_to_run_kegeln_program"])
            self.__log_management.add_log(2, "COM_MNGR", str(self.__com_result[0]), self.__com_result[1])

            self.__connection_manager = ConnectionManager(self.__config["com_x"], self.__config["com_y"],
                                                          self.__config["com_timeout"],
                                                          self.__config["com_write_timeout"],
                                                          self.__log_management.add_log,
                                                          self.__config["ip_addr"], self.__config["port"],
                                                          self.__config["time_interval_break"],
                                                          )
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

        self.__btn_logs_show = QPushButton("Pokaż logi")
        self.__btn_logs_show.setVisible(not self.__show_logs)
        self.__btn_logs_show.clicked.connect(lambda: self.__on_show_logs(True))

        self.__btn_logs_hide = QPushButton("Ukryj logi")
        self.__btn_logs_hide.setVisible(self.__show_logs)
        self.__btn_logs_hide.clicked.connect(lambda: self.__on_show_logs(False))

        dropdown_priority_label.addWidget(self.__priority_dropdown)

        self.__priority_dropdown.currentIndexChanged.connect(self.__update_table_logs)

        col_config_layout.addWidget(self.__label_errors)
        col_config_layout.addWidget(dropdown_priority)
        col_config_layout.addWidget(self.__btn_logs_show)
        col_config_layout.addWidget(self.__btn_logs_hide)

        row1 = QWidget()
        row1_label = QHBoxLayout()
        row1.setLayout(row1_label)
        row1_label.addWidget(connect_list)
        row1_label.addWidget(col_config)
        self.__layout.addWidget(row1)

        self.__table_logs = QTableWidget()
        self.__table_logs.setRowCount(0)
        self.__table_logs.setColumnCount(6)
        self.__table_logs.setHorizontalHeaderLabels(["Id", "Data", "Priorytet", "Kod", "Port", "Wiadomość"])
        self.__table_logs.verticalHeader().setVisible(False)
        self.__table_logs.setVisible(self.__show_logs)

        self.__layout.addWidget(self.__table_logs)
        self.__layout.setStretchFactor(self.__table_logs, 1)
        self.__update_connect_list_layout()

    def __on_show_logs(self, show_logs: bool) -> None:
        """
        This function show and hide table with logs and show/hide btn to show/hide table with logs

        :param show_logs: <bool> true/false - show/hide table with logs
        :return: None
        """
        self.__show_logs = show_logs
        self.__btn_logs_show.setVisible(not self.__show_logs)
        self.__btn_logs_hide.setVisible(self.__show_logs)
        self.__table_logs.setVisible(self.__show_logs)
        if show_logs:
            self.resize(980, 600)
        else:
            self.resize(400, 225)

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
        for name, rec in data:
            if rec == "0":
                rec = ""
            else:
                rec = "( " + rec + " B )"
            label = QLabel(name + " " + rec)
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
                self.__table_logs.setItem(index, j, item)
                if int(log[2]) == 10:
                    item.setBackground(QtGui.QColor(255, 100, 100))
                elif int(log[2]) >= 5:
                    item.setBackground(QtGui.QColor(255, 255, 225))
        self.__table_logs.resizeColumnsToContents()
        return 1

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


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = GUI()
    ex.show()
    sys.exit(app.exec_())
