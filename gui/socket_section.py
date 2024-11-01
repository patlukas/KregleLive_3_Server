from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget, QPushButton, QGroupBox, QGridLayout, QLabel, QLineEdit, QStackedLayout, QComboBox

from sockets_manager import SocketsManagerError


class SocketSection(QGroupBox):
    """
        TODO: Add comment
    """
    def __init__(self, on_create_socket, on_close_sockets):
        super().__init__("Tworzenie serwera TCP")
        self.__on_create_socket = on_create_socket
        self.__on_close_sockets = on_close_sockets
        self.__get_list_ip = None

        self.__stacked_layout = QStackedLayout()

        self.__widget_connect = QWidget()
        self.__layout_connect = QGridLayout()
        self.__label_ip = QLabel("IP: ")
        self.__label_port = QLabel("Port: ")
        self.__label_info = QLabel("")
        self.__combo_ip = QComboBox()
        self.__line_port = QLineEdit()
        # self.__button_refresh = QPushButton("Odśwież listę adresów IP")
        self.__button_create = QPushButton("Stwórz serwer")

        self.__widget_connected = QWidget()
        self.__layout_connected = QGridLayout()
        self.__label_connect_ip = QLabel("")
        self.__button_disconnect = QPushButton("Usuń serwer")

        self.__set_layout()

    def __set_layout(self):
        """."""
        self.__button_create.clicked.connect(self.__create)
        self.__layout_connect.addWidget(self.__label_ip, 0, 0, Qt.AlignRight)
        self.__layout_connect.addWidget(self.__combo_ip, 0, 1)
        self.__layout_connect.addWidget(self.__label_port, 0, 3, Qt.AlignRight)
        self.__layout_connect.addWidget(self.__line_port, 0, 4)
        self.__layout_connect.addWidget(self.__label_info, 1, 0, 1, 4)
        self.__layout_connect.addWidget(self.__button_create, 1, 4)
        self.__layout_connect.setColumnMinimumWidth(2, 20)
        self.__layout_connect.setColumnStretch(1, 2)
        self.__layout_connect.setColumnStretch(4, 1)
        self.__widget_connect.setLayout(self.__layout_connect)
        self.__stacked_layout.addWidget(self.__widget_connect)

        self.__button_disconnect.clicked.connect(self.__disconnect)
        self.__layout_connected.addWidget(self.__label_connect_ip, 0, 0)
        self.__layout_connected.addWidget(self.__button_disconnect, 0, 1)
        self.__widget_connected.setLayout(self.__layout_connected)
        self.__stacked_layout.addWidget(self.__widget_connected)

        self.setLayout(self.__stacked_layout)

    def refresh_list_with_ip_address(self):
        self.__combo_ip.clear()
        if self.__get_list_ip is not None:
            list_ip = self.__get_list_ip()
            self.__combo_ip.addItems(list_ip)

    def __create(self):
        ip, port = self.__combo_ip.currentText(), self.__line_port.text()
        try:
            port = int(port)
            self.__on_create_socket(ip, port)
            self.__label_connect_ip.setText("Adres serwera {} : {}".format(ip, port))
            self.__stacked_layout.setCurrentWidget(self.__widget_connected)
        except SocketsManagerError as e:
            self.__label_info.setText(e.message)
        except ValueError:
            self.__label_info.setText("Port musi być liczbą")

    def __disconnect(self):
        self.__on_close_sockets()
        self.__stacked_layout.setCurrentWidget(self.__widget_connect)
        self.__label_info.setText("")

    def set_func_to_get_list_ip(self, on_get_list_ip):
        self.__get_list_ip = on_get_list_ip
        self.refresh_list_with_ip_address()

    def set_default_port(self, default_port):
        self.__line_port.setText(str(default_port))