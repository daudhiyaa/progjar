import socket
from concurrent.futures import ProcessPoolExecutor
from http import HttpServer

httpserver = HttpServer()
default_address = ('0.0.0.0', 8080)


def process_the_client(connection, address):
    rcv = ""
    while True:
        try:
            data = connection.recv(32)
            if data:
                # merubah input dari socket (berupa bytes) ke dalam string
                # agar bisa mendeteksi \r\n
                d = data.decode()
                rcv = rcv+d
                if rcv.endswith('\r\n'):
                    # end of command, proses string
                    # logging.warning("data dari client: {}" . format(rcv))
                    hasil = httpserver.proses(rcv)
                    # hasil akan berupa bytes
                    # untuk bisa ditambahi dengan string, maka string harus di encode
                    hasil = hasil+"\r\n\r\n".encode()
                    # logging.warning("balas ke  client: {}" . format(hasil))
                    # hasil sudah dalam bentuk bytes
                    connection.sendall(hasil)
                    rcv = ""
                    connection.close()
                    return
            else:
                break
        except OSError:
            pass
    connection.close()


def run_server(max_workers=1):
    the_clients = []
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    my_socket.bind(default_address)
    my_socket.listen(1)

    with ProcessPoolExecutor(max_workers) as executor:
        while True:
            connection, client_address = my_socket.accept()
            # logging.warning("connection from {}".format(client_address))
            p = executor.submit(process_the_client, connection, client_address)
            the_clients.append(p)
            # menampilkan jumlah process yang sedang aktif
            for i, f in enumerate(the_clients):
                print(f"Task {i}: running={f.running()} done={f.done()}")
            print(f"Total active tasks: {len(the_clients)}\n")


def main():
    run_server()


if __name__ == "__main__":
    main()
