#import os
import socket
#from __main__ import qt

"""
try:
    import urlparse
except ImportError:
    import urllib


    class urlparse(object):
        urlparse = urllib.parse.urlparse
        parse_qs = urllib.parse.parse_qs
"""

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from tornado.web import Application
from tornado.web import StaticFileHandler
from requesthandlers import SlicerWebSocketHandler


class TestServer:
    """
    This web server is configured to integrate with the Qt main loop
    by listenting activity on the fileno of the servers socket.
    """

    # TODO: set header so client knows that image refreshes are needed (avoid
    # using the &time=xxx trick)
    def __init__(self, server_address=("", 8070), docroot='.', logFile=None,
                 logMessage=None, certfile=None, app=Application([
                (r"/websocket", SlicerWebSocketHandler),
                (r"/(.*)", StaticFileHandler, {"path": "../docroot", "default_filename": "index.html"})])):
        self.server_address = server_address
        self.docroot = docroot
        self.timeout = 1.
        self.logFile = logFile
        if logMessage:
            self.logMessage = logMessage
        self.server = HTTPServer(app)

    def start(self, app=None):
        if app:
            self.server = HTTPServer(app)
        self.server.listen(self.server_address[1], self.server_address[0])
        self.server.start()
        IOLoop.current().start()

    def stop(self):
        self.server.stop()

    def handle_error(self, request, client_address):
        """Handle an error gracefully.  May be overridden.

        The default is to print a traceback and continue.

        """
        print('-' * 40)
        print('Exception happened during processing of request', request)
        print('From', client_address)
        import traceback
        traceback.print_exc()  # XXX But this goes to stderr!
        print('-' * 40)

    def logMessage(self, message):
        if self.logFile:
            fp = open(self.logFile, "a")
            fp.write(message + '\n')
            fp.close()

    @classmethod
    def findFreePort(self, port=2016):
        """returns a port that is not apparently in use"""
        portFree = False
        while not portFree:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind(("", port))
            except socket.error as e:
                portFree = False
                port += 1
            finally:
                s.close()
                portFree = True
        return port


if __name__ == "__main__":
    test = TestServer(server_address=("", 2016))
    test.start()