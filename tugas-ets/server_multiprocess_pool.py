import socket
import threading
import logging
import signal
import sys
import os
import atexit
from concurrent.futures import ProcessPoolExecutor
from file_protocol import FileProtocol

shutdown_requested = False

def process_client(connection, client_address):
    """
    Handle a client connection in a separate process.
    This function will be executed in a worker process from the process pool.
    """
    # Each process needs its own FileProtocol instance
    process_fp = FileProtocol()
    
    pid = os.getpid()
    logging.warning(f"[PID: {pid}] Processing client {client_address}")
    
    try:
        while not shutdown_requested:
            data_received = connection.recv(52428800)
            if data_received:
                data = data_received.decode()
                result = process_fp.proses_string(data)
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
        threading.Thread.__init__(self)
        self.daemon = True  # Make thread a daemon so it exits when main thread exits
        self.ipinfo = (ipaddress, port)
        self.my_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.running = True
        # If max_workers is None, ProcessPoolExecutor will use cpu_count()
        self.max_workers = max_workers
        self.executor = None

    def run(self):
        global shutdown_requested
        
        logging.warning(f"[PID: {os.getpid()}] Server starting at {self.ipinfo}")
        try:
            self.my_socket.bind(self.ipinfo)
            self.my_socket.listen(5)  # Increased backlog for multiple clients
            self.my_socket.settimeout(1.0)
            
            # Create the process pool
            with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
                self.executor = executor
                logging.warning(f"Process pool created with max_workers={self.max_workers or 'default'}")
                
                while self.running and not shutdown_requested:
                    try:
                        connection, client_address = self.my_socket.accept()
                        logging.warning(f"Connection from {client_address}")
                        
                        # Submit client processing to the process pool
                        executor.submit(process_client, connection, client_address)
                    except socket.timeout:
                        continue
                    except socket.error as e:
                        if not self.running:
                            logging.warning(f"Socket error during shutdown: {e}")
                            break
                        else:
                            logging.warning(f"Socket error: {e}")
                    except Exception as e:
                        logging.warning(f"Unexpected error in server loop: {e}")
        except Exception as e:
            logging.warning(f"Server error: {e}")
        finally:
            logging.warning("Server run loop ended")
            self.my_socket.close()
            self.executor = None

    def shutdown(self):
        global shutdown_requested
        
        logging.warning("Shutting down server...")
        self.running = False
        shutdown_requested = True
        
        try:
            # Close socket to unblock accept() calls
            self.my_socket.close()
        except Exception as e:
            logging.warning(f"Error closing socket: {e}")
        
        logging.warning("Server shutdown complete")

def cleanup():
    global shutdown_requested
    logging.warning("Cleanup handler called")
    shutdown_requested = True
    if 'server' in globals() and server:
        server.shutdown()

def signal_handler(sig, frame):
    logging.warning(f"Signal {sig} received, shutting down...")
    cleanup()
    sys.exit(0)

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    atexit.register(cleanup)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        server = Server(ipaddress='127.0.0.1', port=3000)
        server.start()
        
        # Keep the main thread alive to handle signals
        while server.is_alive():
            server.join(1.0)

        logging.warning("Server thread has ended")
    except KeyboardInterrupt:
        logging.warning("Keyboard interrupt received")
        cleanup()
    except Exception as e:
        logging.warning(f"Error in main: {e}")
        cleanup()
    
    logging.warning("Program exited")