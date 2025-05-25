import socket
import logging
import argparse
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

class Server:
    def __init__(self, ipaddress='0.0.0.0', port=6667, max_workers=10):
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.my_socket.settimeout(1800)  # 5 minutes timeout
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

    def start(self):
        logging.warning(f"server running on ip address {self.ipinfo} with process pool size {self.executor._max_workers}")
        self.my_socket.bind(self.ipinfo)
        self.my_socket.listen(5)

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
        
        # Shutdown the thread pool executor
        self.executor.shutdown(wait=True)
        logging.warning("Server has been shut down.")

if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)
    parser = argparse.ArgumentParser(description='Multithreaded Server')
    parser.add_argument('--port', type=int, default=6667, help='Server port (default: 6667)')
    parser.add_argument('--pool-size', type=int, default=10, help='Thread pool size (default: 10)')
    args = parser.parse_args()

    server = Server(ipaddress='0.0.0.0', port=args.port, max_workers=args.pool_size)
    server.start()
