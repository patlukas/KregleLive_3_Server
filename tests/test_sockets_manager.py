import pytest
import socket
from sockets_manager import SocketsManager, SocketsManagerError
import threading


def test_init_ip_addr():
    a = SocketsManager(lambda a, b, c, d: print(a, b, c, d))
    with pytest.raises(SocketsManagerError) as e:
        a.create_server(None, 50000)
        a.close()
    assert str(e.value.code) == "11-000"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server(123, 50000)
        a.close()
    assert str(e.value.code) == "11-000"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("1.1.1.11.1", 50000)
        a.close()
    assert str(e.value.code) == "11-001"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("192.268.1.256", 50000)
        a.close()
    assert str(e.value.code) == "11-001"

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip_addr = s.getsockname()[0]
    s.close()

    a.create_server("localhost", 50000)
    a.close()

    a.create_server(ip_addr, 50000)
    a.close()

    ip_addr_not_exist = ip_addr.split(".")
    ip_addr_not_exist[3] = str(int(ip_addr_not_exist[3]) + 1)
    with pytest.raises(SocketsManagerError) as e:
        a.create_server(".".join(ip_addr_not_exist), 50000)
        a.close()
    assert str(e.value.code) == "11-001"


def test_init_port():
    a = SocketsManager(lambda a, b, c, d: print(a, b, c, d))

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", None)
        a.close()
    assert str(e.value.code) == "11-000"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", "12345")
        a.close()
    assert str(e.value.code) == "11-000"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", 12345.0)
        a.close()
    assert str(e.value.code) == "11-000"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", -1)
        a.close()
    assert str(e.value.code) == "11-002"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", 65536)
        a.close()
    assert str(e.value.code) == "11-002"

    with pytest.raises(SocketsManagerError) as e:
        a.create_server("localhost", 1234567890123456789)
        a.close()
    assert str(e.value.code) == "11-002"

    a.create_server("localhost", 0)

    a.close()

    a.create_server("localhost", 65535)

    a.close()


def test_busy_port_and_address():
    a = SocketsManager(lambda a, b, c, d: print(a, b, c, d))
    a.create_server("localhost", 5000)

    with pytest.raises(SocketsManagerError) as e:
        b = SocketsManager(lambda a, b, c, d: print(a, b, c, d))
        b.create_server("localhost", 5000)
        b.close()
    a.close()
    assert str(e.value.code) == "11-001"


def test_func_add_bytes_to_send():
    e = []
    a = SocketsManager(lambda a, b, c, d: e.append(b))
    a.create_server("localhost", 5000)


    assert not a.add_bytes_to_send(None)
    assert e[-1] == "SKT_ATST_ERROR"

    assert not a.add_bytes_to_send("string")
    assert e[-1] == "SKT_ATST_ERROR"

    assert not a.add_bytes_to_send(123)
    assert e[-1] == "SKT_ATST_ERROR"

    assert not a.add_bytes_to_send("")
    assert e[-1] == "SKT_ATST_ERROR"

    assert not a.add_bytes_to_send(b"bytes")
    assert e[-1] == "SKT_ATSE_ERROR"

    assert not a.add_bytes_to_send(b"")
    assert e[-1] == "SKT_ATSL_ERROR"

    assert a.add_bytes_to_send(b"test\r")
    assert e[-1] == "SKT_ATQE"

    a.close()


def test_0_client():
    e = []
    a = SocketsManager(lambda a, b, c, d: e.append(b))
    a.create_server("localhost", 65535)


    assert a.get_info() == [['Kolejka', '0', '0']]
    assert a.add_bytes_to_send(b"ABC\r")
    assert e[-1] == "SKT_ATQE"

    assert a.add_bytes_to_send(b"DEF\r")
    assert e[-1] == "SKT_ATQE"

    assert a._SocketsManager__queue_not_sent_data == b"ABC\rDEF\r"

    assert a.communications() == b""

    assert a.close()


def test_after_close():
    e = []
    a = SocketsManager(lambda a, b, c, d: e.append(b))
    a.create_server("localhost", 50000)
    assert a.close()

    assert not a.close()
    assert e[-1] == "SKT_CCSS_ERROR"

    assert a.add_bytes_to_send(b"Hej\r")
    assert a.communications() == b""
    assert a.get_info() == [['Kolejka', '1', '4']]


def test_1_client():
    e = []
    a = SocketsManager(lambda a, b, c, d: e.append(b))
    a.create_server("localhost", 12345)


    b = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    b.connect(("localhost", 12345))
    assert a.get_info() == [['Kolejka', '0', '0']]
    a.communications()
    assert a.get_info() == [["('127.0.0.1', 12345)", '0', '0'], ['Kolejka', '0', '0']]

    assert a.communications() == b""
    b.close()

    assert a.get_info() == [["('127.0.0.1', 12345)", '0', '0'], ['Kolejka', '0', '0']]
    assert a.communications() == b""
    assert a.get_info() == [['Kolejka', '0', '0']]
    assert a.add_bytes_to_send(b"D\r")
    assert a.add_bytes_to_send(b"E\r")
    a.communications()
    assert a.communications() == b""

    def c():
        bb = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bb.connect(("localhost", 12345))
        assert bb.recv(1024) == b"D\rE\r"
        bb.send(b'3\xde\xae\xde\xef\xa6\xce\xce\xce\xce~\xce\xee\xfa\xaf\xfc\r3\r4')
        bb.close()
    d = threading.Thread(target=c)
    d.start()
    while len(a.get_info()) == 1:
        assert a.communications() == b""
    assert a._SocketsManager__sockets[list(a._SocketsManager__sockets)[0]]["data_to_send"] == b"D\rE\r"
    assert a.communications() == b""
    assert a._SocketsManager__sockets[list(a._SocketsManager__sockets)[0]]["data_to_send"] == b""
    while True:
        x = a.communications()
        assert x in [b"", b'3\xde\xae\xde\xef\xa6\xce\xce\xce\xce~\xce\xee\xfa\xaf\xfc\r3\r']
        if x == b'3\xde\xae\xde\xef\xa6\xce\xce\xce\xce~\xce\xee\xfa\xaf\xfc\r3\r':
            assert e[-1] == "SKT_RECV"
            break
    d.join()
    assert a.close()


def test_clear_queue():
    e = []
    a = SocketsManager(lambda a, b, c, d: e.append(b))
    a.create_server("localhost", 50000)
    assert a.on_clear_queue() == 0
    a.add_bytes_to_send(b"Hejka\r")
    assert a.on_clear_queue() == 6
    assert a.on_clear_queue() == 0

