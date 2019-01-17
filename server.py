#  coding: utf-8

# Copyright 2013 Abram Hindle, Eddie Antonio Santos, Michael Lin
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
# Furthermore it is derived from the Python documentation examples thus
# some of the code is Copyright © 2001-2013 Python Software
# Foundation; All Rights Reserved
#
# http://docs.python.org/2/library/socketserver.html
#
# run: python freetests.py

# try: curl -v -X GET http://127.0.0.1:8080/

from socketserver import BaseRequestHandler, TCPServer
from os import path, chdir, getcwd


STATUS_MSG = {
    200: 'OK',
    301: '301 Moved Permanently',
    405: '405 Method Not Allowed',
    404: '404 Not Found'
}

ERR_MSG = {
    405: '''
        <!DOCTYPE html>
        <html>
            <body>HTTP/1.1 405 Method Not Allowed</body>
        </html>
    ''',
    404: '''
        <!DOCTYPE html>
        <html>
            <body>HTTP/1.1 404 Not Found</body>
        </html>
    '''
}

FILE_MIME_TYPE = {
    '.css': 'text/css',
    '.html': 'text/html'
}

HOST, PORT = "localhost", 8080

WEB_ROOT = '/www'


class MyWebServer(BaseRequestHandler):

    # https://github.com/python/cpython/blob/master/Lib/http/server.py#L147
    def handle(self):
        self.data = self.request.recv(1024).strip().decode('utf-8')
        request_method, request_path, request_http_version = self._parse_raw_request_line(self.data)

        # only support GET
        if request_method != 'GET':
            response = self._build_response(ERR_MSG.get(405, ''), 405, {'Content-Type': 'text/html'})
            self.request.sendall(response)
            return

        response = ''
        request_realpath = getcwd() + WEB_ROOT + request_path
        if path.isfile(request_realpath) and self._is_safe_path(getcwd(), request_realpath):
            # serve file https://stackoverflow.com/questions/541390/extracting-extension-from-filename-in-python
            filename, file_extension = path.splitext(request_realpath)
            if file_extension in ['.css', '.html']:
                body = open(request_realpath).read()
                response = self._build_response(body, headers={'Content-Type': FILE_MIME_TYPE[file_extension]})
        elif path.isdir(request_realpath) and self._is_safe_path(getcwd(), request_realpath):
            # check if index.html exist in the directory
            if path.isfile('{}/index.html'.format(request_realpath)):
                if request_path.endswith('/'):
                    body = open('{}/index.html'.format(request_realpath)).read()
                    response = self._build_response(body, headers={'Content-Type': 'text/html'})
                else:
                    redirect_url = 'http://{}:{}{}/'.format(HOST, PORT, request_path)
                    response = self._build_response(None, status_code=301, headers={'Location': redirect_url})
        else:
            response = self._build_response(ERR_MSG.get(404, ''), 404, {'Content-Type': 'text/html'})

        self.request.sendall(response)

    def _parse_raw_request_line(self, raw_request):
        request_lines = raw_request.splitlines()
        words = request_lines[0].split()

        if len(words) == 0:
            raise ValueError('Invalid HTTP Request')

        if len(words) >= 3:
            request_method, request_path, request_http_version = words

            return request_method, request_path, request_http_version

    def _build_response(self, body, status_code=200, headers={}):
        # first line of a HTTP response
        response = 'HTTP/1.1 {} {}\n'.format(status_code, STATUS_MSG.get(status_code, ''))

        # append headers
        for key, value in headers.items():
            response += '{}: {}\n\n'.format(key, value)

        # append body
        if body:
            response += body

        return response.encode()

    # https://security.openstack.org/guidelines/dg_using-file-paths.html
    def _is_safe_path(self, basedir, file_path, follow_symlinks=True):
        # resolves symbolic links
        if follow_symlinks:
            return path.realpath(file_path).startswith(basedir)

        return path.abspath(file_path).startswith(basedir)


if __name__ == "__main__":
    TCPServer.allow_reuse_address = True

    # Create the server, binding to localhost on port 8080
    server = TCPServer((HOST, PORT), MyWebServer)

    # Activate the server; this will keep running until you
    # interrupt the program with Ctrl-C
    server.serve_forever()
