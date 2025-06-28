import os.path
from datetime import datetime

bad_request = 'Bad Request'
not_found = 'Not Found'
internal_server_error = 'Internal Server Error'
text_plain = 'text/plain'


class HttpServer:
    def __init__(self):
        self.sessions = {}
        self.types = {}
        self.types['.pdf'] = 'application/pdf'
        self.types['.jpg'] = 'image/jpeg'
        self.types['.txt'] = text_plain
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
                return self.http_delete(object_address)
            else:
                return self.response(400, bad_request, '', {})
        except IndexError:
            return self.response(400, bad_request, '', {})

    def http_get(self, object_address):
        base_dir = '../'  # This is where all actual files are stored

        # Static routes
        if object_address == '/':
            return self.response(200, 'OK', 'Ini Adalah web Server percobaan', dict())
        if object_address == '/video':
            return self.response(302, 'Found', '', dict(location='https://youtu.be/katoxpnTf04'))
        if object_address == '/santai':
            return self.response(200, 'OK', 'santai saja', dict())
        if object_address.startswith('/list'):
            # Extract subdirectory name after /list/
            subdir = object_address[6:].lstrip(
                '/')  # remove '/list/' prefix safely
            target_path = os.path.normpath(os.path.join(base_dir, subdir))

            # Security check: don't allow escaping base_dir
            if not os.path.abspath(target_path).startswith(os.path.abspath(base_dir)):
                return self.response(403, 'Forbidden', 'Invalid directory path', {})

            return self.list_directory(target_path)

        # Remove leading slash
        object_address = object_address.lstrip('/')

        # Always look for files inside `files/`
        filepath = os.path.join(base_dir, 'files', object_address)

        # File doesn't exist
        if not os.path.exists(filepath):
            return self.response(404, 'Not Found', 'File tidak ditemukan', {})

        # If it's a directory, list contents
        if os.path.isdir(filepath):
            return self.list_directory(filepath)

        # Try to read and serve the file
        try:
            with open(filepath, 'rb') as fp:
                isi = fp.read()

            # Determine content type
            fext = os.path.splitext(filepath)[1]
            content_type = self.types.get(fext, 'application/octet-stream')

            headers = {
                'Content-Type': content_type,
                # download hint
                'Content-Disposition': f'attachment; filename="{object_address}"'
            }

            return self.response(200, 'OK', isi, headers)
        except Exception as e:
            return self.response(500, internal_server_error, f'Error reading file: {str(e)}', {})

    def list_directory(self, directory_path):
        """List files in directory"""
        try:
            files = os.listdir(directory_path)
            output_lines = [f"Directory listing: {directory_path}", ""]

            for file in sorted(files):
                file_path = os.path.join(directory_path, file)
                if os.path.isdir(file_path):
                    output_lines.append(f"[DIR]  {file}/")
                else:
                    file_size = os.path.getsize(file_path)
                    output_lines.append(f"[FILE] {file}  ({file_size} bytes)")

            output_text = "\n".join(output_lines)

            headers = {'Content-type': text_plain}
            return self.response(200, 'OK', output_text, headers)

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
            # Extract Content-Type and boundary
            content_type = None
            for header in headers:
                if header.lower().startswith('content-type:'):
                    content_type = header.split(':', 1)[1].strip()
                    break

            if not content_type or 'multipart/form-data' not in content_type:
                return self.response(400, bad_request, 'Content-Type must be multipart/form-data', {})

            boundary = None
            if 'boundary=' in content_type:
                boundary = content_type.split('boundary=')[1].strip()

            if not boundary:
                return self.response(400, bad_request, 'Missing boundary in multipart data', {})

            boundary_bytes = ('--' + boundary).encode()
            parts = body.encode('latin1').split(boundary_bytes)

            for part in parts:
                if b'Content-Disposition: form-data' in part and b'filename=' in part:
                    # Extract filename
                    lines = part.split(b'\r\n')
                    filename = None
                    for line in lines:
                        if b'filename=' in line:
                            line_str = line.decode(errors='ignore')
                            filename = line_str.split('filename="')[
                                1].split('"')[0]
                            break

                    if filename:
                        # Extract the file content
                        content_start = part.find(b'\r\n\r\n')
                        if content_start != -1:
                            file_content = part[content_start + 4:]
                            file_content = file_content.rstrip(b'\r\n--')

                            # Save file to files/ directory
                            os.makedirs('../files', exist_ok=True)
                            save_path = os.path.join('../files', filename)
                            with open(save_path, 'wb') as f:
                                f.write(file_content)

                            success_msg = f'File "{filename}" uploaded successfully to /files ({len(file_content)} bytes)'
                            return self.response(200, 'OK', success_msg, {'Content-Type': text_plain})

            return self.response(400, bad_request, 'No file found in upload data', {})

        except Exception as e:
            return self.response(500, internal_server_error, f'Upload error: {str(e)}', {'Content-Type': text_plain})

    def http_delete(self, object_address):
        """NEW FEATURE: Delete file via DELETE method"""
        try:
            # Handle both "/filename" and "/delete/filename"
            if object_address.startswith('/delete/'):
                filename = object_address[len('/delete/'):]
            else:
                filename = object_address.lstrip('/')

            # Security check to prevent path traversal
            if '..' in filename or filename.startswith('/') or '/' in filename:
                return self.response(403, 'Forbidden', 'Invalid filename', {})

            # Force deletion from '../files/' directory only
            file_path = os.path.join('../files', filename)

            if not os.path.exists(file_path):
                return self.response(404, not_found, f'File "{filename}" not found', {})

            if os.path.isdir(file_path):
                return self.response(403, 'Forbidden', 'Cannot delete directories', {})

            os.remove(file_path)
            success_msg = f'File "{filename}" deleted successfully'
            return self.response(200, 'OK', success_msg, {})

        except PermissionError:
            return self.response(403, 'Forbidden', 'Permission denied', {})
        except Exception as e:
            return self.response(500, internal_server_error, f'Delete error: {str(e)}', {})
