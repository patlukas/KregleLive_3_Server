from connection_manager import ConnectionManager
import serial
from _thread import start_new_thread


def test_one_message_in_one_write():
    o = ConnectionManager("COM2", "COM9", 1.5, 1, lambda a,b,c,d: print(a,b,c,d),  0.5)
    start_new_thread(o.start, ())

    com_1 = serial.Serial("COM1", 9600, timeout=1, write_timeout=1)
    com_2 = serial.Serial("COM10", 9600, timeout=1, write_timeout=1)
    com_1.write(b"Hej\r")
    r = com_2.readall()
    com_1.close()
    com_2.close()
    o.close()
    assert r == b"Hej\r"


def test_one_message_in_two_write():
    o = ConnectionManager("COM2", "COM9", 1.5, 1, lambda a,b,c,d: print(a,b,c,d),  0.5)
    start_new_thread(o.start, ())

    com_1 = serial.Serial("COM1", 9600, timeout=1, write_timeout=1)
    com_2 = serial.Serial("COM10", 9600, timeout=1, write_timeout=1)
    com_1.write(b"Hej")
    com_2.readall()
    com_1.write(b"Hej\r")
    r = com_2.readall()
    com_1.close()
    com_2.close()
    o.close()
    assert r == b"HejHej\r"


def test_two_messages_in_one_write():
    o = ConnectionManager("COM2", "COM9", 1.5, 1, lambda a,b,c,d: print(a,b,c,d), 0.5)
    start_new_thread(o.start, ())

    com_1 = serial.Serial("COM1", 9600, timeout=1, write_timeout=1)
    com_2 = serial.Serial("COM10", 9600, timeout=1, write_timeout=1)
    com_1.write(b"Hej\rHej\r")
    r = com_2.readall()
    com_1.close()
    com_2.close()
    o.close()
    assert r == b"Hej\rHej\r"


def test_two_messages_in_two_write():
    o = ConnectionManager("COM2", "COM9", 1.5, 1, lambda a,b,c,d: print(a,b,c,d), 0.5)
    start_new_thread(o.start, ())

    com_1 = serial.Serial("COM1", 9600, timeout=1, write_timeout=1)
    com_2 = serial.Serial("COM10", 9600, timeout=1, write_timeout=1)
    com_1.write(b"Hej\r")
    com_1.write(b"Hej\r")
    r = com_2.readall()
    com_1.close()
    com_2.close()
    o.close()
    assert r == b"Hej\rHej\r"


def test_no_ended_message():
    o = ConnectionManager("COM2", "COM9", 1.5, 1, lambda a,b,c,d: print(a,b,c,d),  0.5)
    start_new_thread(o.start, ())

    com_1 = serial.Serial("COM1", 9600, timeout=1, write_timeout=1)
    com_2 = serial.Serial("COM10", 9600, timeout=1, write_timeout=1)
    com_1.write(b"Hej")
    r = com_2.readall()
    com_1.close()
    com_2.close()
    o.close()
    assert r == b""
