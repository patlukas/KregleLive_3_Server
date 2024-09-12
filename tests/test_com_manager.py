
import pytest
import serial
from com_manager import ComManager, ComManagerError
"""
    Requirements:
        must exists serial port: COM1<->COM2
        cannot exist serial port: COM13
"""


def test_busy_port():
    a = serial.Serial("COM1")
    with pytest.raises(ComManagerError) as e:
        b = ComManager("COM1", 1, 1, "COM_A", lambda a,b,c,d: print(a,b,c,d))
        b.close()
    a.close()
    assert str(e.value.code) == "10-002"


def test_cannot_exist_port():
    with pytest.raises(ComManagerError) as e:
        b = ComManager("COM13", 1, 1, "COM_A", lambda a,b,c,d: print(a,b,c,d))
        b.close()
    assert e.value.code == "10-002"


def test_released_port():
    a = serial.Serial("COM1")
    a.close()
    b = ComManager("COM1", 1, 1, "COM_A", lambda a,b,c,d: print(a,b,c,d))
    b.close()


def test_close_port():
    b = ComManager("COM1", 1, 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    b.close()
    with pytest.raises(ComManagerError) as e1:
        b.read()
    with pytest.raises(ComManagerError) as e2:
        b.send()
    with pytest.raises(ComManagerError) as e3:
        b.close()
    assert e1.value.code == "10-003" and e2.value.code == "10-004" and e3.value.code == "10-005"


def test_in_communication():
    e = []
    a = serial.Serial("COM2", timeout=0.1, write_timeout=0.1)
    b = ComManager("COM1", 0.1, 0.1, "COM_A", lambda a, b, c, d: e.append(b))
    a.write(b"Hello")
    r1 = b.read()
    r2 = b.get_number_received_bytes()
    assert r1 == b'' and r2 == 0

    a.write(b" ")
    r3 = b.read()
    r4 = b.get_number_received_bytes()
    assert r3 == b'' and r4 == 0

    a.write(b"World\r_")
    r5 = b.read()
    r6 = b.get_number_received_bytes()
    assert r5 == b"Hello World\r" and r6 == 12

    a.write(b'3\xde\xae\xde\xef\xa6\xce\xce\xce\xce~\xce\xee\xfa\xaf\xfc')
    r7 = b.read()
    assert r7 == b'' and e[-1] == "COM_READ_NOISE" and e[-2] == "COM_READ"

    a.close()
    b.close()


def test_out_communication():
    a = serial.Serial("COM2", timeout=0.1, write_timeout=0.1)
    b = ComManager("COM1", 0.1, 0.1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    b.send()
    r = a.readall()
    assert r == b''

    b.add_bytes_to_send(b"Hello")
    b.send()
    r = a.readall()
    assert r == b''

    b.add_bytes_to_send(b" ")
    b.send()
    r = a.readall()
    assert r == b''

    b.add_bytes_to_send(b"World\r_")
    b.send()
    r = a.readall()
    assert r == b"Hello World\r"

    a.close()
    b.close()


def test_wrong_arguments():
    with pytest.raises(ComManagerError) as e1:
        b = ComManager("", 1, 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e2:
        b = ComManager(None, 1, 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e3:
        b = ComManager("COM1", "1", 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e4:
        b = ComManager("COM1", 1, "1", "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e5:
        b = ComManager("COM1", -1, 0.1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e6:
        b = ComManager("COM1", 1, -1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e7:
        b = ComManager("COM1", 1, -1, 1, lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(ComManagerError) as e8:
        b = ComManager("COM1", 1, -1, None, lambda a, b, c, d: print(a, b, c, d))

    assert e1.value.code == "10-002" and e2.value.code == "10-000" and e3.value.code == "10-000"
    assert e4.value.code == "10-000" and e5.value.code == "10-001" and e6.value.code == "10-001"
    assert e7.value.code == "10-000" and e8.value.code == "10-000"


def test_get_alias():
    b = ComManager("COM1", 1, 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    assert b.get_alias() == "COM_A"
    b.close()


def test_send_wrong_type_of_message():
    b = ComManager("COM1", 1, 1, "COM_A", lambda a, b, c, d: print(a, b, c, d))
    b.add_bytes_to_send("aaa")
    b.close()
