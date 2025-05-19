
import socket
import threading
import logging
import signal
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from file_protocol import FileProtocol
fp = FileProtocol()

def process_client(connection, address):
    try:
        while True:
            data_received = connection.recv(52428800)
            if data_received:
                data = data_received.decode()
                result = fp.proses_string(data)
                result += "\r\n\r\n"
                connection.sendall(result.encode())
            else:
                break
    except Exception as e:
        logging.warning(f"error: {e}")
    finally:
        connection.close()

class Server(threading.Thread):
    def __init__(self, ipaddress, port, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True
        threading.Thread.__init__(self)
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.futures = []

    def run(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(1)

        try:
            while self.running:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"connection from {client_address}")
                
                # Submit client processing to thread pool
                future  = self.executor.submit(process_client, connection, client_address)
                self.futures.append(future)
                
                # Clean up completed futures
                self.futures = [f for f in self.futures if not f.done()]
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt received, shutting down server...")
        finally:
            self.shutdown()

    def shutdown(self):
        logging.warning("Shutting down server...")
        self.running = False
        self.my_socket.close()
        
        # Shutdown the thread pool
        self.executor.shutdown(wait=True)
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
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.warning("KeyboardInterrupt received, shutting down server...")
