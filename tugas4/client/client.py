import socket
import logging
import ssl
import os

server_address = ('127.0.0.1', 8080)


def make_socket(destination_address='127.0.0.1', port=8080):
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        return sock
    except Exception as ee:
        logging.warning(f"error {str(ee)}")


def make_secure_socket(destination_address='127.0.0.1', port=8080):
    try:
        # get it from https://curl.se/docs/caextract.html

        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        context.load_verify_locations(os.getcwd() + '/domain.crt')

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (destination_address, port)
        logging.warning(f"connecting to {server_address}")
        sock.connect(server_address)
        secure_socket = context.wrap_socket(
            sock, server_hostname=destination_address)
        logging.warning(secure_socket.getpeercert())
        return secure_socket
    except Exception as ee:
        logging.warning(f"error {str(ee)}")


def send_command(command_str, is_secure=False):
    ip = server_address[0]
    port = server_address[1]
    # gunakan fungsi diatas
    if is_secure == True:
        sock = make_secure_socket(ip, port)
    else:
        sock = make_socket(ip, port)

    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning("sending message ")
        sock.sendall(command_str.encode())
        logging.warning(command_str)
        # Look for the response, waiting until socket is done (no more data)
        data_received = ""
        while True:
            # socket does not receive all data at once, data comes in part, need to be concatenated at the end of process
            data = sock.recv(2048)
            if data:
                # data is not empty, concat with previous content
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                # no more data, stop the process by break
                break
        # at this point, data_received (string) will contain all data coming from the socket
        # to be able to use the data_received as a dict, need to load it using json.loads()
        hasil = data_received
        logging.warning("data received from server:")
        return hasil
    except Exception as ee:
        logging.warning(f"error during data receiving {str(ee)}")
        return False


def handle_client_upload(filename):
    file_path = os.path.join("../", filename)
    if not os.path.isfile(file_path):
        print("File does not exist.")
        return None
    filename = os.path.basename(file_path)
    with open(file_path, 'rb') as f:
        file_data = f.read()

    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()

    request = (
        f"POST /upload HTTP/1.1\r\n"
        f"Host: localhost\r\n"
        f"Content-Type: multipart/form-data; boundary={boundary}\r\n"
        f"Content-Length: {len(body)}\r\n\r\n"
    ).encode() + body

    return request.decode('latin1')


def show_menu():
    print("\n=== HTTP Client Menu ===")
    print("  1. GET    /             - Welcome message")
    print("  2. GET    /list         - List directory files")
    print("  3. GET    /filename     - Download file")
    print("  4. POST   /upload       - Upload file")
    print("  5. DELETE /filename     - Delete file")
    print("  0. Exit")
    choice = input("Enter menu number: ").strip()
    return choice


def handle_user_choice(choice):
    if choice == '1':
        return "GET / HTTP/1.1\r\nHost: localhost\r\n\r\n"

    elif choice == '2':
        dir_name = input(
            "Enter directory to list (relative to './'): ").strip()
        return f"GET /list/{dir_name} HTTP/1.1\r\nHost: localhost\r\n\r\n"

    elif choice == '3':
        filename = input(
            "Enter filename to download (e.g. test.txt): ").strip()
        return f"GET /{filename} HTTP/1.1\r\nHost: localhost\r\n\r\n"

    elif choice == '4':
        filename = input(
            "Enter filename to upload (must exist in ../): ").strip()
        return handle_client_upload(filename)

    elif choice == '5':
        filename = input(
            "Enter filename to delete (must exist in files/): ").strip()
        return f"DELETE /{filename} HTTP/1.1\r\nHost: localhost\r\n\r\n"

    elif choice == '0':
        return "EXIT"

    else:
        print("Invalid choice. Please enter a number between 0 and 5.")
        return None


if __name__ == '__main__':
    while True:
        choice = show_menu()
        request_data = handle_user_choice(choice)

        if request_data == "EXIT":
            print("Goodbye!")
            break

        if request_data:
            hasil = send_command(request_data)
            print("\nResponse:\n", hasil)
