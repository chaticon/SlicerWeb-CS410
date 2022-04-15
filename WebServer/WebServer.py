# slicer imports
from __main__ import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

# python imports
try:
    from BaseHTTPServer import HTTPServer
except ImportError:
    from http.server import HTTPServer
#import json
#import logging
#import mimetypes
#import numpy
#import os
#import pydicom
#import random
#import select
#import sys
import socket
#import string
#import time

try:
    import urlparse
except ImportError:
    import urllib


    class urlparse(object):
        urlparse = urllib.parse.urlparse
        parse_qs = urllib.parse.parse_qs
#import uuid

# vtk imports
#import vtk.util.numpy_support

# WebServer imports
import glTFLib
#import dicomserver

#######################
from requesthandlers import *
#######################

#
# WebServer
#

class WebServer:
    def __init__(self, parent):
        parent.title = "Web Server"
        parent.categories = ["Servers"]
        parent.dependencies = []
        parent.contributors = ["Steve Pieper (Isomics)"]
        parent.helpText = """Provides an embedded web server for slicer that provides a web services API for interacting with slicer.
    """
        parent.acknowledgementText = """
This work was partially funded by NIH grant 3P41RR013218.
"""
        self.parent = parent


#
# WebServer widget
#

class WebServerWidget(ScriptedLoadableModuleWidget):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None):
        ScriptedLoadableModuleWidget.__init__(self, parent)
        self.guiMessages = True
        self.consoleMessages = True

    def enter(self):
        pass

    def exit(self):
        pass

    def setLogging(self):
        self.consoleMessages = self.logToConsole.checked
        self.guiMessages = self.logToGUI.checked

    def setup(self):
        ScriptedLoadableModuleWidget.setup(self)

        # reload button
        self.reloadButton = qt.QPushButton("Reload")
        self.reloadButton.name = "WebServer Reload"
        self.reloadButton.toolTip = "Reload this module."
        self.layout.addWidget(self.reloadButton)
        self.reloadButton.connect('clicked(bool)', self.onReload)

        self.log = qt.QTextEdit()
        self.log.readOnly = True
        self.layout.addWidget(self.log)
        self.logMessage('<p>Status: <i>Idle</i>\n')

        # log to console
        self.logToConsole = qt.QCheckBox('Log to Console')
        self.logToConsole.setChecked(self.consoleMessages)
        self.logToConsole.toolTip = "Copy log messages to the python console and parent terminal"
        self.layout.addWidget(self.logToConsole)
        self.logToConsole.connect('clicked()', self.setLogging)

        # log to GUI
        self.logToGUI = qt.QCheckBox('Log to GUI')
        self.logToGUI.setChecked(self.guiMessages)
        self.logToGUI.toolTip = "Copy log messages to the log widget"
        self.layout.addWidget(self.logToGUI)
        self.logToGUI.connect('clicked()', self.setLogging)

        # clear log button
        self.clearLogButton = qt.QPushButton("Clear Log")
        self.clearLogButton.toolTip = "Clear the log window."
        self.layout.addWidget(self.clearLogButton)
        self.clearLogButton.connect('clicked()', self.log.clear)

        # TODO: button to start/stop server
        # TODO: warning dialog on first connect
        # TODO: config option for port

        # open browser page
        self.localConnectionButton = qt.QPushButton("Open Browser Page")
        self.localConnectionButton.toolTip = "Open a connection to the server on the local machine with your system browser."
        self.layout.addWidget(self.localConnectionButton)
        self.localConnectionButton.connect('clicked()', self.openLocalConnection)

        # open slicer widget
        self.localQtConnectionButton = qt.QPushButton("Open SlicerWeb demo in WebWidget Page")
        self.localQtConnectionButton.toolTip = "Open a connection with Qt to the server on the local machine."
        self.layout.addWidget(self.localQtConnectionButton)
        self.localQtConnectionButton.connect('clicked()', lambda: self.openQtLocalConnection('http://localhost:2016'))

        # open step demo in widget
        self.localQtConnectionButton = qt.QPushButton("Open STEP in WebWidget")
        self.localQtConnectionButton.toolTip = "Open a connection with Qt to the server on the local machine."
        self.layout.addWidget(self.localQtConnectionButton)
        self.localQtConnectionButton.connect('clicked()',
                                             lambda: self.openQtLocalConnection('http://pieper.github.io/step'))

        # qiicr chart button
        self.qiicrChartButton = qt.QPushButton("Open QIICR Chart Demo")
        self.qiicrChartButton.toolTip = "Open the QIICR chart demo.  You need to be on the internet to access the page and you need to have the QIICR Iowa data loaded in your DICOM database in order to drill down to the image level."
        self.layout.addWidget(self.qiicrChartButton)
        self.qiicrChartButton.connect('clicked()', self.openQIICRChartDemo)

        # export scene
        self.exportSceneButton = qt.QPushButton("Export Scene")
        self.exportSceneButton.toolTip = "Export the current scene to a web site (only models and tracts supported)."
        self.layout.addWidget(self.exportSceneButton)
        self.exportSceneButton.connect('clicked()', self.exportScene)

        # slivr button
        self.slivrButton = qt.QPushButton("Open Slivr Demo")
        self.slivrButton.toolTip = "Open the Slivr demo.  Example of VR export."
        self.layout.addWidget(self.slivrButton)
        self.slivrButton.connect('clicked()', self.openSlivrDemo)

        # ohif button
        self.ohifButton = qt.QPushButton("Open OHIF Demo")
        self.ohifButton.toolTip = "Open the OHIF demo.  Example of dicomweb access."
        self.layout.addWidget(self.ohifButton)
        self.ohifButton.connect('clicked()', self.openOHIFDemo)

        self.logic = WebServerLogic(logMessage=self.logMessage)
        self.logic.start()

        # Add spacer to layout
        self.layout.addStretch(1)

    def openLocalConnection(self):
        qt.QDesktopServices.openUrl(qt.QUrl('http://localhost:2016'))

    def openQtLocalConnection(self, url='http://localhost:2016'):
        self.webWidget = slicer.qSlicerWebWidget()
        html = """
    <h1>Loading from <a href="%(url)s">%(url)s/a></h1>
    """ % {'url': url}
        # self.webWidget.html = html
        self.webWidget.url = 'http://localhost:2016/work'
        self.webWidget.url = url
        self.webWidget.show()

    def openQIICRChartDemo(self):
        self.qiicrWebWidget = slicer.qSlicerWebWidget()
        self.qiicrWebWidget.setGeometry(50, 50, 1750, 1200)
        url = "http://pieper.github.io/qiicr-chart/dcsr/qiicr-chart"
        html = """
    <h1>Loading from <a href="%(url)s">%(url)s/a></h1>
    """ % {'url': url}
        # self.qiicrWebWidget.html = html
        self.qiicrWebWidget.url = url
        self.qiicrWebWidget.show()

    def exportScene(self):
        exportDirectory = ctk.ctkFileDialog.getExistingDirectory()
        if exportDirectory.endswith('/untitled'):
            # this happens when you select inside of a directory on mac
            exportDirectory = exportDirectory[:-len('/untitled')]
        if exportDirectory != '':
            self.logic.exportScene(exportDirectory)

    def openSlivrDemo(self):
        qt.QDesktopServices.openUrl(qt.QUrl('http://localhost:2016/slivr'))

    def openOHIFDemo(self):
        qt.QDesktopServices.openUrl(qt.QUrl('http://localhost:2016/ohif'))

    def onReload(self):
        self.logic.stop()
        ScriptedLoadableModuleWidget.onReload(self)
        slicer.modules.WebServerWidget.logic.start()

    def logMessage(self, *args):
        if self.consoleMessages:
            for arg in args:
                print(arg)
        if self.guiMessages:
            if len(self.log.html) > 1024 * 256:
                self.log.clear()
                self.log.insertHtml("Log cleared\n")
            for arg in args:
                self.log.insertHtml(arg)
            self.log.insertPlainText('\n')
            self.log.ensureCursorVisible()
            self.log.repaint()
            # slicer.app.processEvents(qt.QEventLoop.ExcludeUserInputEvents)


#
# SlicerHTTPServer
#


class SlicerHTTPServer(HTTPServer):
    """
    This web server is configured to integrate with the Qt main loop
    by listenting activity on the fileno of the servers socket.
    """

    # TODO: set header so client knows that image refreshes are needed (avoid
    # using the &time=xxx trick)
    def __init__(self, server_address=("", 8070), RequestHandlerClass=SlicerRequestHandler, docroot='.', logFile=None,
                 logMessage=None, certfile=None):
        HTTPServer.__init__(self, server_address, RequestHandlerClass)
        self.docroot = docroot
        self.timeout = 1.
        if certfile:
            # https://stackoverflow.com/questions/19705785/python-3-simple-https-server
            import ssl
            self.socket = ssl.wrap_socket(self.socket,
                                          server_side=True,
                                          certfile=certfile,
                                          ssl_version=ssl.PROTOCOL_TLS)
        self.socket.settimeout(5.)
        self.logFile = logFile
        if logMessage:
            self.logMessage = logMessage
        self.notifiers = {}
        self.connections = {}
        self.requestCommunicators = {}

    class RequestCommunicator(object):
        """Encapsulate elements for handling event driven read of request"""

        def __init__(self, connectionSocket, docroot, logMessage):
            self.connectionSocket = connectionSocket
            self.docroot = docroot
            self.logMessage = logMessage
            self.bufferSize = 1024 * 1024
            self.slicerRequestHandler = SlicerRequestHandler(logMessage)
            self.dicomRequestHandler = DICOMRequestHandler(logMessage)
            self.staticRequestHandler = StaticRequestHandler(self.docroot, logMessage)
            self.expectedRequestSize = -1
            self.requestSoFar = b""
            fileno = self.connectionSocket.fileno()
            self.readNotifier = qt.QSocketNotifier(fileno, qt.QSocketNotifier.Read)
            self.readNotifier.connect('activated(int)', self.onReadable)
            self.logMessage('Waiting on %d...' % fileno)

        def onReadableComplete(self):
            self.logMessage("reading complete, freeing notifier")
            self.readNotifier = None

        def onReadable(self, fileno):
            self.logMessage('Reading...')
            requestHeader = b""
            requestBody = b""
            requestComplete = False
            requestPart = ""
            try:
                requestPart = self.connectionSocket.recv(self.bufferSize)
                self.logMessage('Just received... %d bytes in this part' % len(requestPart))
                self.requestSoFar += requestPart
                endOfHeader = self.requestSoFar.find(b'\r\n\r\n')
                if self.expectedRequestSize > 0:
                    self.logMessage(
                        'received... %d of %d expected' % (len(self.requestSoFar), self.expectedRequestSize))
                    if len(self.requestSoFar) >= self.expectedRequestSize:
                        requestHeader = self.requestSoFar[:endOfHeader + 2]
                        requestBody = self.requestSoFar[4 + endOfHeader:]
                        requestComplete = True
                else:
                    if endOfHeader != -1:
                        self.logMessage('Looking for content in header...')
                        contentLengthTag = self.requestSoFar.find(b'Content-Length:')
                        if contentLengthTag != -1:
                            tag = self.requestSoFar[contentLengthTag:]
                            numberStartIndex = tag.find(b' ')
                            numberEndIndex = tag.find(b'\r\n')
                            contentLength = int(tag[numberStartIndex:numberEndIndex])
                            self.expectedRequestSize = 4 + endOfHeader + contentLength
                            self.logMessage(
                                'Expecting a body of %d, total size %d' % (contentLength, self.expectedRequestSize))
                            if len(requestPart) == self.expectedRequestSize:
                                requestHeader = requestPart[:endOfHeader + 2]
                                requestBody = requestPart[4 + endOfHeader:]
                                requestComplete = True
                        else:
                            self.logMessage('Found end of header with no content, so body is empty')
                            requestHeader = self.requestSoFar[:-2]
                            requestComplete = True
            except socket.error as e:
                print('Socket error: ', e)
                print('So far:\n', self.requestSoFar)
                requestComplete = True

            if len(requestPart) == 0 or requestComplete:
                self.logMessage(
                    'Got complete message of header size %d, body size %d' % (len(requestHeader), len(requestBody)))
                self.readNotifier.disconnect('activated(int)', self.onReadable)
                self.readNotifier.setEnabled(False)
                qt.QTimer.singleShot(0, self.onReadableComplete)

                if len(self.requestSoFar) == 0:
                    self.logMessage("Ignoring empty request")
                    return

                method, uri, version = [b'GET', b'/', b'HTTP/1.1']  # defaults
                requestLines = requestHeader.split(b'\r\n')
                self.logMessage(requestLines[0])
                try:
                    method, uri, version = requestLines[0].split(b' ')
                except ValueError as e:
                    self.logMessage("Could not interpret first request lines: ", requestLines)

                if requestLines == "":
                    self.logMessage("Assuming empty sting is HTTP/1.1 GET of /.")

                if version != b"HTTP/1.1":
                    self.logMessage("Warning, we don't speak %s", version)
                    return

                # TODO: methods = ["GET", "POST", "PUT", "DELETE"]
                methods = [b"GET", b"POST", b"PUT"]
                if not method in methods:
                    self.logMessage("Warning, we only handle %s" % methods)
                    return

                contentType = b'text/plain'
                responseBody = b'No body'
                parsedURL = urlparse.urlparse(uri)
                pathParts = os.path.split(parsedURL.path)  # path is like /slicer/timeimage
                request = parsedURL.path
                if parsedURL.query != b"":
                    request += b'?' + parsedURL.query
                self.logMessage('Parsing url request: ', parsedURL)
                self.logMessage(' request is: %s' % request)
                route = pathParts[0]
                if route.startswith(b'/slicer'):
                    request = request[len(b'/slicer'):]
                    self.logMessage(' request is: %s' % request)
                    contentType, responseBody = self.slicerRequestHandler.handleSlicerRequest(request, requestBody)
                elif parsedURL.path.startswith(b'/dicom'):
                    self.logMessage(' dicom request is: %s' % request)
                    contentType, responseBody = self.dicomRequestHandler.handleDICOMRequest(parsedURL, requestBody)
                elif parsedURL.path.startswith(b'/websocket'):
                    self.logMessage(' TODO: establishing websocket connection with socket %s' % fileno)
                else:
                    contentType, responseBody = self.staticRequestHandler.handleStaticRequest(uri, requestBody)

                if responseBody:
                    self.response = b"HTTP/1.1 200 OK\r\n"
                    self.response += b"Access-Control-Allow-Origin: *\r\n"
                    self.response += b"Content-Type: %s\r\n" % contentType
                    self.response += b"Content-Length: %d\r\n" % len(responseBody)
                    self.response += b"Cache-Control: no-cache\r\n"
                    self.response += b"\r\n"
                    self.response += responseBody
                else:
                    self.response = b"HTTP/1.1 404 Not Found\r\n"
                    self.response += b"\r\n"

                self.toSend = len(self.response)
                self.sentSoFar = 0
                fileno = self.connectionSocket.fileno()
                self.writeNotifier = qt.QSocketNotifier(fileno, qt.QSocketNotifier.Write)
                self.writeNotifier.connect('activated(int)', self.onWritable)

        def onWriteableComplete(self):
            self.logMessage("writing complete, freeing notifier")
            self.writeNotifier = None
            self.connectionSocket = None

        def onWritable(self, fileno):
            self.logMessage('Sending on %d...' % (fileno))
            sendError = False
            try:
                sent = self.connectionSocket.send(self.response[:500 * self.bufferSize])
                self.response = self.response[sent:]
                self.sentSoFar += sent
                self.logMessage('sent: %d (%d of %d, %f%%)' % (
                    sent, self.sentSoFar, self.toSend, 100. * self.sentSoFar / self.toSend))
            except socket.error as e:
                self.logMessage('Socket error while sending: %s' % e)
                sendError = True

            if self.sentSoFar >= self.toSend or sendError:
                self.writeNotifier.disconnect('activated(int)', self.onWritable)
                self.writeNotifier.setEnabled(False)
                qt.QTimer.singleShot(0, self.onWriteableComplete)
                self.connectionSocket.close()
                self.logMessage('closed fileno %d' % (fileno))

    def onServerSocketNotify(self, fileno):
        self.logMessage('got request on %d' % fileno)
        try:
            (connectionSocket, clientAddress) = self.socket.accept()
            fileno = connectionSocket.fileno()
            self.requestCommunicators[fileno] = self.RequestCommunicator(connectionSocket, self.docroot,
                                                                         self.logMessage)
            self.logMessage('Connected on %s fileno %d' % (connectionSocket, connectionSocket.fileno()))
        except socket.error as e:
            self.logMessage('Socket Error', socket.error, e)

    def start(self):
        """start the server
        - use one thread since we are going to communicate
        via stdin/stdout, which will get corrupted with more threads
        """
        try:
            self.logMessage('started httpserver...')
            self.notifier = qt.QSocketNotifier(self.socket.fileno(), qt.QSocketNotifier.Read)
            self.logMessage('listening on %d...' % self.socket.fileno())
            self.notifier.connect('activated(int)', self.onServerSocketNotify)

        except KeyboardInterrupt:
            self.logMessage('KeyboardInterrupt - stopping')
            self.stop()

    def stop(self):
        self.socket.close()
        if self.notifier:
            self.notifier.disconnect('activated(int)', self.onServerSocketNotify)
        self.notifier = None

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


#
# WebServer logic
#

class WebServerLogic:
    """Include a concrete subclass of SimpleHTTPServer
    that speaks slicer.
    """

    def __init__(self, logMessage=None):
        if logMessage:
            self.logMessage = logMessage
        self.port = 2016
        self.server = None
        self.logFile = '/tmp/WebServerLogic.log'

        moduleDirectory = os.path.dirname(slicer.modules.webserver.path.encode())
        self.docroot = moduleDirectory + b"/docroot"

    def getSceneBounds(self):
        # scene bounds
        sceneBounds = None
        for node in slicer.util.getNodes('*').values():
            if node.IsA('vtkMRMLDisplayableNode'):
                bounds = [0, ] * 6
                if sceneBounds is None:
                    sceneBounds = bounds
                node.GetRASBounds(bounds)
                for element in range(0, 6):
                    op = (min, max)[element % 2]
                    sceneBounds[element] = op(sceneBounds[element], bounds[element])
        return sceneBounds

    def exportScene(self, exportDirectory):
        """Export a simple scene that can run independent of Slicer.

        This exports the data in a standard format with the idea that other
        sites can be built externally to make the data more usable."""

        scale = 15
        sceneBounds = self.getSceneBounds()
        center = [0.5 * (sceneBounds[0] + sceneBounds[1]), 0.5 * (sceneBounds[2] + sceneBounds[3]),
                  0.5 * (sceneBounds[4] + sceneBounds[5])]
        target = [scale * center[0] / 1000., scale * center[1] / 1000., scale * center[2] / 1000.]

        cameraPosition = [target[1], target[2], target[0] + 2]

        html = """<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <script src="https://aframe.io/releases/0.6.1/aframe.min.js"></script>
    <script src="https://cdn.rawgit.com/tizzle/aframe-orbit-controls-component/v0.1.12/dist/aframe-orbit-controls-component.min.js"></script>
    <style type="text/css">
      * {font-family: sans-serif;}
    </style>
  </head>
  <body>

    <a-scene >
      <a-entity
          id="camera"
          camera="fov: 80; zoom: 1;"
          position="%CAMERA_POSITION%"
          orbit-controls="
              autoRotate: false;
              target: #target;
              enableDamping: true;
              dampingFactor: 0.125;
              rotateSpeed:0.25;
              minDistance:1;
              maxDistance:100;
              "
          >
      </a-entity>

      <a-entity id="target" position="%TARGET_POSITION%"></a-entity>
      <a-entity id="mrml" position="0 0 0" scale="%SCALE%" rotation="-90 180 0">
        <a-gltf-model src="./mrml.gltf"></a-gltf-model>
      </a-entity>
    </a-scene>

  </body>
</html>
"""
        html = html.replace("%CAMERA_POSITION%", "%g %g %g" % (cameraPosition[0], cameraPosition[1], cameraPosition[2]))
        html = html.replace("%SCALE%", "%g %g %g" % (scale, scale, scale))
        html = html.replace("%TARGET_POSITION%", "%g %g %g" % (target[1], target[2], target[0]))

        htmlPath = os.path.join(exportDirectory, "index.html")
        print('saving to', htmlPath)
        fp = open(htmlPath, "w")
        fp.write(html)
        fp.close()

        exporter = glTFLib.glTFExporter(slicer.mrmlScene)
        glTF = exporter.export(options={
            "fiberMode": "tubes",
        })
        glTFPath = os.path.join(exportDirectory, "mrml.gltf")
        print('saving to', glTFPath)
        fp = open(glTFPath, "w")
        fp.write(glTF)
        fp.close()

        for bufferFileName in exporter.buffers.keys():
            print('saving to', bufferFileName)
            fp = open(os.path.join(exportDirectory, bufferFileName), "wb")
            fp.write(exporter.buffers[bufferFileName].data)
            fp.close()

        print('done exporting')

    def logMessage(self, *args):
        for arg in args:
            print("Logic: " + arg)

    def start(self):
        """Set up the server"""
        self.stop()
        self.port = SlicerHTTPServer.findFreePort(self.port)
        self.logMessage("Starting server on port %d" % self.port)
        self.logMessage('docroot: %s' % self.docroot)
        # for testing webxr
        # e.g. certfile = '/Users/pieper/slicer/latest/SlicerWeb/localhost.pem'
        # openssl req -new -x509 -keyout localhost.pem -out localhost.pem -days 365 -nodes
        certfile = None
        self.server = SlicerHTTPServer(docroot=self.docroot, server_address=("", self.port), logFile=self.logFile,
                                       logMessage=self.logMessage, certfile=certfile)
        self.server.start()

    def stop(self):
        if self.server:
            self.server.stop()
