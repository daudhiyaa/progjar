import socket
import threading
import logging
import signal
import sys

from file_protocol import FileProtocol
fp = FileProtocol()

shutdown_event = threading.Event()

class ProcessTheClient(threading.Thread):
    def __init__(self, connection, address):
        threading.Thread.__init__(self)
        self.connection = connection
        self.address = address

    def run(self):
        data_received = ""
        try:
            while not shutdown_event.is_set():
                data = self.connection.recv(1024)
                if data:
                    data_received += data.decode()
                    if "\r\n\r\n" in data_received:
                        break
                else:
                    break
            if data_received:
                logging.warning(f"full data received: {data_received}")
                hasil = fp.proses_string(data_received.strip())
                hasil += "\r\n\r\n"
                self.connection.sendall(hasil.encode())
        except Exception as e:
            logging.warning(f"error: {e}")
        finally:
            self.connection.close()

class Server(threading.Thread):
    def __init__(self, ipaddress, port):
        threading.Thread.__init__(self)
        self.ipinfo = (ipaddress, port)
        self.the_clients = []
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)
        while self.running and not shutdown_event.is_set():
            try:
                self.my_socket.settimeout(1.0)
                self.connection, self.client_address = self.my_socket.accept()
                logging.warning(f"connection from {self.client_address}")

                clt = ProcessTheClient(self.connection, self.client_address)
                clt.start()
                self.the_clients.append(clt)
            except socket.timeout:
                continue
            except socket.error:
                if not self.running:
                    break

    def shutdown(self):
        logging.warning("Shutting down server...")
        self.running = False
        shutdown_event.set()
        self.my_socket.close()
        for clt in self.the_clients:
            clt.join()
        logging.warning("Server has been shut down.")

def signal_handler(signal, frame):
    logging.warning("Signal received, shutting down server...")
    server.shutdown()
    sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    server = Server(ipaddress='127.0.0.1', port=3000)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    server.start()
