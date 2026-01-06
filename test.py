# import socket
# import time
#
# with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
#     s.settimeout(0)
#     print("1")
#     while True:
#         try:
#             s.connect(("127.0.0.1", 65432))
#         except Exception:
#             print("Connect error")
#         t = b""
#         for x in range(10):
#             t += b"A"
#         while True:
#             # try:
#                 data = s.recv(240)
#                 print(len(data), data)
#                 # s.sendall(b"SSSSSSSSS")
#                 print(s.send(t))
#
#             # except Exception as e:
#             #     print("-" + str(e))
#             # time.sleep(0.5)
#
#
#
#     # for x in range(10000000):
#     #     if x % 1000000 == 0:
#     #         print(x)
from gui.setting_option import SettingTurnOnPrinter

a = SettingTurnOnPrinter()
qaction = a.create_menu_action()
print(a.analyze_message_to_lane(b'3038IG00100201E004005000010\r'))
print(a.analyze_message_to_lane(b'3038IG00100201E004005000110\r'))
print(a.analyze_message_to_lane(b'3038IG\r'))
print(a.analyze_message_to_lane(b'3038IGaaaaaaaaaaaaaaaaaaaaaaa\r'))
a.on_toggle()
print(a.analyze_message_to_lane(b'3038IG00100201E004005000010\r'))
print(a.analyze_message_to_lane(b'3038IG00100201E004005000110\r'))
print(a.analyze_message_to_lane(b'3038IG\r'))
print(a.analyze_message_to_lane(b'3038IGaaaaaaaaaaaaaaaaaaaaaaa\r'))