import socket
import logging
import argparse
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol

fp = FileProtocol()

def process_client(connection, address):
    buffer = ""
    try:
        connection.settimeout(1800)  # 30 minutes timeout
        while True:
            data = connection.recv(131072)  # Increased from 32 to 8192 bytes
            if not data:
                break
            buffer += data.decode()
            while "\r\n\r\n" in buffer:
                command, buffer = buffer.split("\r\n\r\n", 1)
                result = fp.proses_string(command)
                response = result + "\r\n\r\n"
                connection.sendall(response.encode())
    except Exception as e:
        logging.warning(f"Error: {str(e)}")
    finally:
        connection.close()

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=6667, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.my_socket.settimeout(1800)  # 30 minutes timeout
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    def start(self):
        logging.warning(f"server running on ip address {self.ipinfo} with process pool size {self.executor._max_workers}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5) # Increased backlog for more pending connections

        try:
            while True:
                connection, client_address = self.my_socket.accept()
                logging.warning(f"connection from {client_address}")
                self.executor.submit(process_client, connection, client_address)
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
    multiprocessing.freeze_support()
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description='Multiprocess Server')
    parser.add_argument('--port', type=int, default=6667, help='Server port (default: 6667)')
    parser.add_argument('--pool-size', type=int, default=10, help='Thread pool size (default: 10)')
    args = parser.parse_args()

    server = Server(ipaddress='0.0.0.0', port=args.port, max_workers=args.pool_size)
    server.start()