#import os
import socket
from __main__ import qt

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
    def __init__(self, server_address=("", 8070), docroot=b'.', logFile=None,
                 logMessage=None, certfile=None, keyfile=None, app=None):
        self.address, self.port = server_address
        self.docroot = docroot
        self.timeout = 1.
        self.logFile = logFile
        if logMessage:
            self.logMessage = logMessage

        if app is None:
            print("Serving Static Files from %s" % docroot.decode("utf-8"))
            # the StaticFileHandler only takes the path arg as a string, so we have to decode the byte string
            app = Application([(r"/websocket", SlicerWebSocketHandler),
                               (r"/(.*)", StaticFileHandler, {"path": docroot.decode("utf-8"), "default_filename": "index.html"})])

        if certfile is not None and keyfile is not None:
            print("Running in Secure Mode")
            self.server = HTTPServer(app, ssl_options={"certfile": certfile, "keyfile": keyfile})
        else:
            print("Running in Non Secure Mode")
            self.server = HTTPServer(app)

        self.running = True

    def start(self, app=None):
        if app:
            self.server = HTTPServer(app)
        self.server.listen(self.port, self.address)
        self.server.start()

        # runs the two event loops on the same thread
        while self.running:
            # stop then start runs the loop once
            IOLoop.current().stop()
            IOLoop.current().start()
            if qt.QCoreApplication.hasPendingEvents():
                qt.QCoreApplication.processEvents()
        else:
            self.server.stop()

    def stop(self):
        self.logMessage("Stopping Server")
        self.running = False

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
    test = TestServer(server_address=("", 2016), docroot=b"../docroot")
    test.start()
