from PyQt5.QtWidgets import QGroupBox, QGridLayout, QPushButton

class SectionLaneControlPanel(QGroupBox):

    def __init__(self):
        super().__init__("Sterowanie torami")
        self.__log_management = None
        self.__on_add_message = None
        self.__box_enter = None
        self.__box_time = None
        self.__layout = QGridLayout()
        self.setLayout(self.__layout)
        self.setVisible(False)

    def init(self, number_of_lane: int, log_management, on_add_message):
        self.__log_management = log_management
        self.__on_add_message = on_add_message

        button_structure = self.__get_structure(number_of_lane)
        self.__box_enter = self.__get_panel_with_buttons("", "Enter", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T24", "Enter"))
        self.__box_time = self.__get_panel_with_buttons("", "Czas stop", button_structure, number_of_lane,
                                                              lambda list_lane: self.__add_new_messages(list_lane, b"T14", "Czas stop"))
        self.__layout.addWidget(self.__box_enter)
        self.__layout.addWidget(self.__box_time)

    def __get_structure(self, number_of_lane: int) -> list:
        number_of_lane_in_row = number_of_lane
        return_list = []
        while number_of_lane_in_row >= 1:
            return_list.append(self.__get_structure_row(number_of_lane_in_row, number_of_lane))
            number_of_lane_in_row -= (2 if number_of_lane_in_row > 2 else 1)
        return return_list

    @staticmethod
    def __get_structure_row(number_of_lane_in_row: int, number_of_lane: int) -> list:
        step = 2 if number_of_lane_in_row > 1 else 1
        left_lane = 0
        result_list = []
        while left_lane + number_of_lane_in_row <= number_of_lane:
            a = [left_lane+i for i in range(number_of_lane_in_row)]
            result_list.append(a)
            left_lane += step
        return result_list

    def __add_new_messages(self, list_lane: list, body_message: bytes, what_message_means: str):
        if self.__on_add_message is None or self.__log_management is None:
            return
        list_lane_to_print = [x+1 for x in list_lane]
        self.__log_management(3, "LCP_CLICK", "", "Dodano nowe wiadomości przez 'Sterowanie torami': Adresaci {}, Wiadomość '{}'({})".format(list_lane_to_print, what_message_means, body_message))
        for lane in list_lane:
            message = b"3" + bytes(str(lane), "cp1250") + b"38" + body_message
            self.__on_add_message(message, True, 9, -1) #TODO change time_wait

    @staticmethod
    def __get_panel_with_buttons(main_label: str, option_name: str, structure: list, number_col: int, on_click):
        box = QGroupBox(main_label)
        layout = QGridLayout()
        for i, row in enumerate(structure):
            number_btn = len(row)
            cols_for_btn = number_col // number_btn
            left_col = 0
            for btn_lane in row:
                btn = QPushButton(option_name + " " + ", ".join(map(str, [x + 1 for x in btn_lane])))
                btn.clicked.connect(lambda _, list_lane=btn_lane: on_click(list_lane))
                layout.addWidget(btn, i, left_col, 1, cols_for_btn)
                left_col += cols_for_btn
        box.setLayout(layout)
        box.setVisible(False)
        return box

    def show_control_panel(self, name: str, show: bool):
        if self.__box_time is None or self.__box_enter is None:
            return

        show_main = show
        if name == "Enter":
            self.__box_enter.setVisible(show)
            show_main = show_main or self.__box_time.isVisible()
        elif name == "Time":
            self.__box_time.setVisible(show)
            show_main = show_main or self.__box_enter.isVisible()
        self.setVisible(show_main)
        if show_main:
            self.adjustSize()
