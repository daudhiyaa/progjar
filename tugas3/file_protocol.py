import json
import logging
import shlex

from file_interface import FileInterface

class FileProtocol:
    def __init__(self):
        self.file = FileInterface()

    def proses_string(self, string_datamasuk=''):
        logging.warning(f"string diproses: {string_datamasuk}")
        c = shlex.split(string_datamasuk)
        try:
            c_request = c[0].strip().upper()
            logging.warning(f"memproses request: {c_request}")
            params = list(c[1:])
            if hasattr(self.file, c_request.lower()):
                cl = getattr(self.file, c_request.lower())(params)
                return json.dumps(cl)
            else:
                return json.dumps(dict(status='ERROR', data='request tidak dikenali'))
        except Exception as e:
            return json.dumps(dict(status='ERROR', data=str(e)))