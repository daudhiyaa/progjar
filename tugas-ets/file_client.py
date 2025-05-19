import socket
import json
import base64
import logging

server_address = ('127.0.0.1', 3000)

def send_command(command_str=""):
    global server_address
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(server_address)
    logging.warning(f"connecting to {server_address}")
    try:
        logging.warning(f"sending message ")
        sock.sendall((command_str + "\r\n\r\n").encode())
        data_received = ""
        while True:
            data = sock.recv(1024)
            if data:
                data_received += data.decode()
                if "\r\n\r\n" in data_received:
                    break
            else:
                break
        hasil = json.loads(data_received.strip())
        logging.warning("data received from server:")
        return hasil
    except Exception as e:
        logging.warning(f"error during data receiving: {e}")
        return None
    finally:
        sock.close()


def remote_list():
    command_str = "LIST"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        print("daftar file : ")
        for nmfile in hasil['data']:
            print(f"- {nmfile}")
        return True
    else:
        print("Gagal")
        return False

def remote_get(filename=""):
    command_str = f"GET {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        namafile = hasil['data_namafile']
        isifile = base64.b64decode(hasil['data_file'])
        with open(namafile, 'wb+') as fp:
            fp.write(isifile)
        return True
    else:
        print("Gagal")
        return False

def remote_upload(filepath=""):
    try:
        with open(filepath, 'rb') as fp:
            filedata = base64.b64encode(fp.read()).decode()
        filename = filepath.split('/')[-1]
        command_str = f"UPLOAD {filename} {filedata}"
        hasil = send_command(command_str)
        if hasil and hasil['status'] == 'OK':
            print(f"File {filename} uploaded successfully.")
            return True
        else:
            print("Gagal")
            return False
    except FileNotFoundError:
        print("File not found")
        return False

def remote_delete(filename=""):
    command_str = f"DELETE {filename}"
    hasil = send_command(command_str)
    if hasil and hasil['status'] == 'OK':
        print(f"File {filename} deleted successfully.")
        return True
    else:
        print("Gagal")
        return False

def show_menu():
    print("\nOptions:")
    print("1. List files")
    print("2. Get file")
    print("3. Upload file")
    print("4. Delete file")
    print("5. Exit")

if __name__ == '__main__':
    server_address = ('127.0.0.1', 3000)

    while True:
        show_menu()
        choice = input("Enter your choice: ")
        if choice == '1':
            remote_list()
        elif choice == '2':
            filename = input("Enter the filename to get: ")
            remote_get(filename)
        elif choice == '3':
            filepath = input("Enter the full path of the file to upload: ")
            remote_upload(filepath)
        elif choice == '4':
            filename = input("Enter the filename to delete: ")
            remote_delete(filename)
        elif choice == '5':
            break
        else:
            print("Invalid choice, please try again.")
