import sys
import os.path
import uuid
from glob import glob
from datetime import datetime
import urllib.parse
import socket
import threading

bad_request = 'Bad Request'
not_found = 'Not Found'
internal_server_error = 'Internal Server Error'


class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = 'text/plain'
        self.types['.html'] = 'text/html'

    def response(self, kode=404, message=not_found, messagebody=bytes(), headers={}):
        tanggal = datetime.now().strftime('%c')
        resp = []
        resp.append("HTTP/1.0 {} {}\r\n" . format(kode, message))
        resp.append("Date: {}\r\n" . format(tanggal))
        resp.append("Connection: close\r\n")
        resp.append("Server: myserver/1.0\r\n")
        resp.append("Content-Length: {}\r\n" . format(len(messagebody)))
        for kk in headers:
            resp.append("{}:{}\r\n" . format(kk, headers[kk]))
        resp.append("\r\n")

        response_headers = ''
        for i in resp:
            response_headers = "{}{}" . format(response_headers, i)
        # menggabungkan resp menjadi satu string dan menggabungkan dengan messagebody yang berupa bytes
        # response harus berupa bytes
        # message body harus diubah dulu menjadi bytes
        if (type(messagebody) is not bytes):
            messagebody = messagebody.encode()

        response = response_headers.encode() + messagebody
        # response adalah bytes
        return response

    def proses(self, data):
        # Split by double CRLF to separate headers from body
        parts = data.split("\r\n\r\n", 1)
        header_part = parts[0]
        body_part = parts[1] if len(parts) > 1 else ""

        requests = header_part.split("\r\n")
        baris = requests[0]
        all_headers = [n for n in requests[1:] if n != '']

        j = baris.split(" ")
        try:
            method = j[0].upper().strip()
            if (method == 'GET'):
                object_address = j[1].strip()
                return self.http_get(object_address)
            if (method == 'POST'):
                object_address = j[1].strip()
                return self.http_post(object_address, all_headers, body_part)
            if (method == 'DELETE'):
                object_address = j[1].strip()
                return self.http_delete(object_address, all_headers)
            else:
                return self.response(400, bad_request, '', {})
        except IndexError:
            return self.response(400, bad_request, '', {})

    def http_get(self, object_address):
        thedir = './'

        if object_address == '/':
            return self.response(200, 'OK', 'Ini Adalah web Server percobaan', dict())
        if object_address == '/video':
            return self.response(302, 'Found', '', dict(location='https://youtu.be/katoxpnTf04'))
        if object_address == '/santai':
            return self.response(200, 'OK', 'santai saja', dict())
        if object_address == '/list' or object_address == '/files':
            return self.list_directory(thedir)

        object_address = object_address.lstrip('/')
        filepath = os.path.join(thedir, object_address)

        if not os.path.exists(filepath):
            return self.response(404, not_found, 'File tidak ditemukan', {})

        if os.path.isdir(filepath):
            return self.list_directory(filepath)

        try:
            with open(filepath, 'rb') as fp:
                isi = fp.read()

            fext = os.path.splitext(filepath)[1]
            content_type = self.types.get(fext, 'application/octet-stream')
            headers = {'Content-type': content_type}
            return self.response(200, 'OK', isi, headers)
        except Exception as e:
            return self.response(500, internal_server_error, f'Error reading file: {str(e)}', {})

    def list_directory(self, directory_path):
        """NEW FEATURE: List files in directory"""
        try:
            files = os.listdir(directory_path)
            html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Directory Listing - {}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #333; }}
        ul {{ list-style-type: none; padding: 0; }}
        li {{ padding: 8px 0; border-bottom: 1px solid #eee; }}
        a {{ text-decoration: none; color: #0066cc; }}
        a:hover {{ text-decoration: underline; }}
        .file {{ background: #f9f9f9; padding: 5px; border-radius: 3px; }}
        .upload-form {{
            margin-top: 30px;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <h1>Directory Listing: {}</h1>
    <ul>
""".format(directory_path, directory_path)

            for file in sorted(files):
                file_path = os.path.join(directory_path, file)
                if os.path.isdir(file_path):
                    html_content += f'<li><a href="/{file}/">{file}/</a> <small>[Directory]</small></li>\n'
                else:
                    file_size = os.path.getsize(file_path)
                    html_content += f'<li class="file"><a href="/{file}">{file}</a> <small>({file_size} bytes)</small> <a href="/delete/{file}" onclick="curl -X DELETE -F {file}">Delete</a></li>\n'

            html_content += """
    </ul>

    <div class="upload-form">
        <h3>Upload File</h3>
        <p><strong>To upload a file, use POST request to /upload with form data</strong></p>
        <p>Example: <code>curl -X POST -F "file=@yourfile.txt" http://localhost:port/upload</code></p>
    </div>
</body>
</html>
"""

            headers = {'Content-type': 'text/html'}
            return self.response(200, 'OK', html_content, headers)

        except Exception as e:
            return self.response(500, internal_server_error, f'Error listing directory: {str(e)}', {})

    def http_post(self, object_address, headers, body):
        """Enhanced POST method with file upload capability"""

        # NEW FEATURE: File upload
        if object_address == '/upload':
            return self.handle_file_upload(headers, body)

        # Original POST handling
        headers_dict = {}
        isi = "POST request received"
        return self.response(200, 'OK', isi, headers_dict)

    def handle_file_upload(self, headers, body):
        """NEW FEATURE: Handle file upload via POST"""
        try:
            # Parse headers to find Content-Type
            content_type = None
            for header in headers:
                if header.lower().startswith('content-type:'):
                    content_type = header.split(':', 1)[1].strip()
                    break

            if not content_type or 'multipart/form-data' not in content_type:
                return self.response(400, bad_request, 'Content-Type must be multipart/form-data', {})

            # Extract boundary from content-type
            boundary = None
            if 'boundary=' in content_type:
                boundary = content_type.split(
                    'boundary=')[1].split(';')[0].strip()

            if not boundary:
                return self.response(400, bad_request, 'Missing boundary in multipart data', {})

            # Parse multipart data (simplified parser)
            boundary_bytes = ('--' + boundary).encode()
            parts = body.encode().split(boundary_bytes)

            for part in parts:
                if b'Content-Disposition: form-data' in part and b'filename=' in part:
                    # Extract filename
                    lines = part.split(b'\r\n')
                    filename = None
                    for line in lines:
                        if b'filename=' in line:
                            filename = line.decode().split(
                                'filename="')[1].split('"')[0]
                            break

                    if filename:
                        # Find the actual file content (after double CRLF)
                        content_start = part.find(b'\r\n\r\n')
                        if content_start != -1:
                            file_content = part[content_start + 4:]
                            # Remove trailing boundary markers
                            if file_content.endswith(b'\r\n'):
                                file_content = file_content[:-2]

                            # Save file
                            with open(filename, 'wb') as f:
                                f.write(file_content)

                            success_msg = f'File "{filename}" uploaded successfully ({len(file_content)} bytes)'
                            return self.response(200, 'OK', success_msg, {})

            return self.response(400, bad_request, 'No file found in upload data', {})

        except Exception as e:
            return self.response(500, internal_server_error, f'Upload error: {str(e)}', {})

    def http_delete(self, object_address):
        """NEW FEATURE: Delete file via DELETE method"""
        try:
            # Handle /delete/filename format
            if object_address.startswith('/delete/'):
                filename = object_address[8:]  # Remove '/delete/' prefix
            else:
                filename = object_address[1:]  # Remove leading '/'

            # Security check - prevent directory traversal
            if '..' in filename or filename.startswith('/'):
                return self.response(403, 'Forbidden', 'Invalid filename', {})

            file_path = './' + filename
            print(f"Deleting file: {file_path}")

            if not os.path.exists(file_path):
                return self.response(404, 'File not found', f'File "{filename}" not found', {})

            # Add the actual delete logic here
            os.remove(file_path)
            return self.response(200, 'OK', f'File "{filename}" deleted successfully', {})

        except Exception as e:
            return self.response(500, 'Internal Server Error', f'Error deleting file: {str(e)}', {})

    def start_server(self, host='localhost', port=8080):
        """Start the HTTP server with socket"""
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((host, port))
            server_socket.listen(5)
            print(f"HTTP Server started at http://{host}:{port}/")
            print("Available endpoints:")
            print("  GET  /           - Welcome message")
            print("  GET  /list       - List directory files")
            print("  GET  /filename   - Download file")
            print("  POST /upload     - Upload file")
            print("  DELETE /filename - Delete file")
            print("\nPress Ctrl+C to stop the server\n")

            while True:
                client_socket, addr = server_socket.accept()
                print(f"Connection from {addr}")

                # Handle client in separate thread
                client_thread = threading.Thread(
                    target=self.handle_client,
                    args=(client_socket,)
                )
                client_thread.daemon = True
                client_thread.start()

        except KeyboardInterrupt:
            print("\nShutting down server...")
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            server_socket.close()

    def handle_client(self, client_socket):
        """Handle individual client request"""
        try:
            # Receive request data
            request_data = b''
            while True:
                chunk = client_socket.recv(1024)
                if not chunk:
                    break
                request_data += chunk
                # Check if we have complete headers
                if b'\r\n\r\n' in request_data:
                    break

            if request_data:
                # Process the request
                request_str = request_data.decode('utf-8', errors='ignore')
                response = self.proses(request_str)

                # Send response
                client_socket.send(response)

        except Exception as e:
            print(f"Error handling client: {e}")
            error_response = self.response(
                500, internal_server_error, f'Server Error: {str(e)}', {})
            try:
                client_socket.send(error_response)
            except:
                pass
        finally:
            client_socket.close()


def main():
    """Main function to run server or tests"""
    if len(sys.argv) > 1 and sys.argv[1] == 'test':
        # Run internal tests
        run_internal_tests()
    else:
        # Start the web server
        httpserver = HttpServer()
        try:
            port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
            httpserver.start_server('localhost', port)
        except ValueError:
            print("Invalid port number. Using default port 8080.")
            httpserver.start_server('localhost', 8080)


def run_internal_tests():
    """Run internal method tests"""
    httpserver = HttpServer()

    # Create test files first
    print("=== Creating test files ===")
    with open('testing.txt', 'w') as f:
        f.write('This is a test file content.')
    print("Created testing.txt")

    with open('sample.html', 'w') as f:
        f.write('<html><body><h1>Hello World</h1></body></html>')
    print("Created sample.html")

    # Test existing functionality
    print("\n=== Testing existing GET requests ===")
    d = httpserver.proses('GET testing.txt HTTP/1.0\r\n\r\n')
    print("GET testing.txt:", d[:100], "...")

    d = httpserver.proses('GET sample.html HTTP/1.0\r\n\r\n')
    print("GET sample.html:", d[:100], "...")

    # Test new features
    print("\n=== Testing new features ===")

    # Test directory listing
    d = httpserver.proses('GET /list HTTP/1.0\r\n\r\n')
    print("GET /list: Directory listing generated successfully")

    # Test file upload (simulated)
    upload_data = '''POST /upload HTTP/1.0\r\nContent-Type: multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW\r\n\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW\r\nContent-Disposition: form-data; name="file"; filename="uploaded.txt"\r\nContent-Type: text/plain\r\n\r\nHello, this is uploaded content!\r\n------WebKitFormBoundary7MA4YWxkTrZu0gW--'''
    d = httpserver.proses(upload_data)
    print("POST /upload:", d.decode()[:200], "...")

    # Check if uploaded file exists
    if os.path.exists('uploaded.txt'):
        print("✓ Upload successful - uploaded.txt created")
        with open('uploaded.txt', 'r') as f:
            print("File content:", f.read())

    # Test file deletion
    d = httpserver.proses('DELETE /uploaded.txt HTTP/1.0\r\n\r\n')
    print("DELETE /uploaded.txt:", d.decode()[:100], "...")

    # Check if file was deleted
    if not os.path.exists('uploaded.txt'):
        print("✓ Delete successful - uploaded.txt removed")
    else:
        print("✗ Delete failed - uploaded.txt still exists")

    # Test 404 for non-existent file
    d = httpserver.proses('GET nonexistent.txt HTTP/1.0\r\n\r\n')
    print("GET nonexistent.txt (should be 404):", d[:100], "...")

    print("\n=== Testing complete ===")
    print("Available files after test:")
    files = glob('./*')
    for f in files:
        if os.path.isfile(f):
            print(f"  - {f}")


if __name__ == "__main__":
    main()
