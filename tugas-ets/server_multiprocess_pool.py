import socket
import logging
import os
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol

def process_client(ip_port_bytes):
    ip, port, data = ip_port_bytes
    fp = FileProtocol()
    result = fp.proses_string(data.decode())
    return (ip, port, result)

class Server():
    def __init__(self, ipaddress, port, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    def start(self):
        logging.warning(f"server berjalan di ip address {self.ipinfo}")
        logging.warning(f"using {self.executor._max_workers} worker processes")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)  # Increased backlog for more pending connections

        try:
            while True:
                connection, client_address = self.my_socket.accept()
                ip, port = client_address
                logging.warning(f"connection from {client_address}")

                data = connection.recv(52428800)
                future = self.executor.submit(process_client, (ip, port, data))
                result = future.result()

                response = result[2] + "\r\n\r\n"
                connection.sendall(response.encode())
                connection.close()
        except KeyboardInterrupt:
            logging.warning("KeyboardInterrupt received, shutting down server...")
        finally:
            self.shutdown()

    def shutdown(self):
        logging.warning("Shutting down server...")
        self.my_socket.close()
        
        # Shutdown the process pool executor
        self.executor.shutdown(wait=True)
        logging.warning("Server has been shut down.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    server = Server(ipaddress='127.0.0.1', port=3000)
    server.start()