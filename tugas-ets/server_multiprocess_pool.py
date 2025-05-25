import socket
import logging
import os
import argparse
import multiprocessing
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol

def process_command(data: str) -> str:
    """Function to be executed in the process pool"""
    fp = FileProtocol()  # must be created inside the worker
    result = fp.proses_string(data)
    return result + "\r\n\r\n"

def process_client(connection, address, executor):
    """Handle client connection in the main thread; delegate CPU-bound task to process pool"""
    logging.warning(f"Handling connection from {address}")
    try:
        buffer = ""
        while True:
            data = connection.recv(52428800)  # 50MB max read size
            if not data:
                break
            buffer += data.decode()

            while "\r\n\r\n" in buffer:
                cmd, buffer = buffer.split("\r\n\r\n", 1)
                future = executor.submit(process_command, cmd)
                result = future.result()
                connection.sendall(result.encode())
    except Exception as e:
        logging.warning(f"Error handling {address}: {e}")
    finally:
        logging.warning(f"Closing connection from {address}")
        connection.close()

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
                logging.warning(f"connection from {client_address}")
                process_client(connection, client_address, self.executor)
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