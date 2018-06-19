"""
SamProxyMaker

Created by: samueljklee

Last update: 6/19/2018
"""

import sys, os, time, math
from PyQt5.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QApplication, QLabel, QSplitter, QFrame, QButtonGroup, QSizePolicy, QPlainTextEdit, QSplashScreen, QDesktopWidget)
from PyQt5.QtCore import QDate, QTime, QDateTime, Qt, QThread, QTimer
from PyQt5.QtGui import *
from giganet.run import *
from netnut.run import *
import json

class displayThread(QThread):
    def __init__(self, source, dest):
        """ 
        Read from File == source
        Log / Proxy Display == dest
        """
        QThread.__init__(self)
        self.src = source
        self.des = dest

    def __del__(self):
        self.wait()

    def run(self):
        # Not recommended: Thread that writes to widget.
        text = open(self.src, 'r').read()
        self.des.appendPlainText(text)

class proxyMaker(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        self.initSplashScreen()

    def initUI(self):        
        serverNames = ['GigaNet', 'UpCloud', 'Vultr', 'NetNut']
        actionNames = ['Create', 'Info', 'Destroy', 'Quit']

        # Input Horizontal
        hbox = QVBoxLayout(self)
        splitter = QSplitter(self)
        splitter.setOrientation(Qt.Vertical)

        # Top Horizontal
        top = QFrame(splitter)
        top.setFrameShape(QFrame.StyledPanel)
        # Bottom Horizontal
        bottom = QFrame(splitter)
        bottom.setFrameShape(QFrame.StyledPanel)

        # Inputs
        # Server, NumberProxies, Location, Action
        inputBox = QHBoxLayout(top)
        serverSplitter = QSplitter(top)
        serverSplitter.setOrientation(Qt.Horizontal)
        numberSplitter = QSplitter(top)
        numberSplitter.setOrientation(Qt.Horizontal)
        locationSplitter = QSplitter(top)
        locationSplitter.setOrientation(Qt.Horizontal)
        actionSplitter = QSplitter(top)
        actionSplitter.setOrientation(Qt.Horizontal)

        # Server, NumberProxies, Location, Action Verticals
        serverBox = QFrame(serverSplitter)
        serverBox.setFrameShape(QFrame.StyledPanel)
        numberBox = QFrame(numberSplitter)
        numberBox.setFrameShape(QFrame.StyledPanel)
        locationBox = QFrame(locationSplitter)
        locationBox.setFrameShape(QFrame.StyledPanel)
        actionBox = QFrame(actionSplitter)
        actionBox.setFrameShape(QFrame.StyledPanel)

        ### Server 
        self.serverLayout = QVBoxLayout(serverBox)
        self.serverButtons = [QPushButton(x) for x in serverNames]
        [ x.setCheckable(True) for x in self.serverButtons ]
        self.serverButtonsGroup = QButtonGroup()
        [self.serverButtonsGroup.addButton(x) for x in self.serverButtons]
        self.serverButtonsGroup.setExclusive(True)

        self.serverButtons[0].clicked.connect(self.giganet)
        self.serverButtons[1].clicked.connect(self.upcloud)
        self.serverButtons[2].clicked.connect(self.vultr)
        self.serverButtons[3].clicked.connect(self.netnut)

        # Number and Location Box
        generalInfoLayout = QVBoxLayout(numberBox)
        self.numberDisplay = QPlainTextEdit()
        self.numberDisplay.setPlaceholderText("Number of proxies.")
        self.locationDisplay = QPlainTextEdit()
        self.locationDisplay.setPlaceholderText("Location of proxies.")
        
        # Server specific requirements
        specificInfoLayout = QVBoxLayout(locationBox)
        self.gigaInfo = ['APIKEY', 'APIHASH']
        self.gigaInfo[0] = QPlainTextEdit()
        self.gigaInfo[0].setPlaceholderText("GigaNet API KEY.")
        self.gigaInfo[0].setVisible(False)
        self.gigaInfo[1] = QPlainTextEdit()
        self.gigaInfo[1].setPlaceholderText("GigaNet API HASH.")
        self.gigaInfo[1].setVisible(False)

        self.ucInfo = ['ucUSR', 'ucPSWD']
        self.ucInfo[0] = QPlainTextEdit()
        self.ucInfo[0].setPlaceholderText("UpCloud Username.")
        self.ucInfo[0].setVisible(False)
        self.ucInfo[1] = QPlainTextEdit()
        self.ucInfo[1].setPlaceholderText("UpCloud Password.")
        self.ucInfo[1].setVisible(False)

        self.vInfo = ['vtoken']
        self.vInfo[0] = QPlainTextEdit()
        self.vInfo[0].setPlaceholderText("Vultr.")
        self.vInfo[0].setVisible(False)
    
        self.nnInfo = ['nnUSR', 'nnPSWD']
        self.nnInfo[0] = QPlainTextEdit()
        self.nnInfo[0].setPlaceholderText("NetNut Username.")
        self.nnInfo[0].setVisible(False)
        self.nnInfo[1] = QPlainTextEdit()
        self.nnInfo[1].setPlaceholderText("NetNut Password.")
        self.nnInfo[1].setVisible(False)

        # Action Box
        self.actionLayout = QVBoxLayout(actionBox)
        self.actionButtons = [QPushButton(x) for x in actionNames]
        [ x.setCheckable(True) for x in self.actionButtons ]
        self.actionButtonsGroup = QButtonGroup()
        [self.actionButtonsGroup.addButton(x) for x in self.actionButtons]
        self.actionButtonsGroup.setExclusive(True)

        self.actionButtons[0].clicked.connect(self.create)
        self.actionButtons[1].clicked.connect(self.info)
        self.actionButtons[2].clicked.connect(self.destroy)
        self.actionButtons[3].clicked.connect(self.quit)
        
        # Output
        # Log, Verticals
        outputBox = QHBoxLayout(bottom)
        logSplitter = QSplitter(bottom)
        logSplitter.setOrientation(Qt.Horizontal)
        proxySplitter = QSplitter(bottom)
        proxySplitter.setOrientation(Qt.Horizontal)

        # Log, Proxy Verticals
        logBox = QFrame(logSplitter)
        logBox.setFrameShape(QFrame.StyledPanel)
        proxyBox = QFrame(proxySplitter)
        proxyBox.setFrameShape(QFrame.StyledPanel)

        # Log
        logLayout = QVBoxLayout(logBox)
        self.logDisplay = QPlainTextEdit()
        self.logDisplay.setReadOnly(True)
        self.logDisplay.setPlainText("Log will display here.")
        
        # Proxy
        proxyLayout = QVBoxLayout(proxyBox)
        self.proxyDisplay = QPlainTextEdit()
        self.proxyDisplay.setPlainText("Proxies:")
        self.proxyDisplay.setReadOnly(True)
        

        # Add widgets into layout
        [self.serverLayout.addWidget(x) for x in self.serverButtons]
        [self.actionLayout.addWidget(x) for x in self.actionButtons]
        
        generalInfoLayout.addWidget(self.numberDisplay)
        generalInfoLayout.addWidget(self.locationDisplay)

        [specificInfoLayout.addWidget(self.gigaInfo[i]) for i in range(len(self.gigaInfo))]
        [specificInfoLayout.addWidget(self.ucInfo[i]) for i in range(len(self.ucInfo))]
        [specificInfoLayout.addWidget(self.vInfo[i]) for i in range(len(self.vInfo))]
        [specificInfoLayout.addWidget(self.nnInfo[i]) for i in range(len(self.nnInfo))]


        logLayout.addWidget(self.logDisplay)
        proxyLayout.addWidget(self.proxyDisplay)

        inputBox.addWidget(serverSplitter)
        inputBox.addWidget(numberSplitter)
        inputBox.addWidget(locationSplitter)
        inputBox.addWidget(actionSplitter)
        outputBox.addWidget(logSplitter)
        outputBox.addWidget(proxySplitter)
        hbox.addWidget(splitter)

        # Restore Information from data/info.txt if exists
        if os.path.isfile("data/info.txt"):
            print("Info.txt found.")
            with open("data/info.txt") as fh:
                data = json.load(fh)
                for dataHandler in data['giganet']:
                    self.gigaInfo[0].setPlainText(dataHandler['apikey'])
                    self.gigaInfo[1].setPlainText(dataHandler['apihash'])
                for dataHandler in data['upcloud']:
                    self.ucInfo[0].setPlainText(dataHandler['ucuser'])
                    self.ucInfo[1].setPlainText(dataHandler['ucpass'])
                for dataHandler in data['vultr']:
                    self.vInfo[0].setPlainText(dataHandler['vtoken'])
                for dataHandler in data['netnut']:
                    self.nnInfo[0].setPlainText(dataHandler['nnuser'])
                    self.nnInfo[1].setPlainText(dataHandler['nnpass'])

    def initSplashScreen(self):
        splash_pix = QPixmap('data/image/loading.jpg')
        self.splash = QSplashScreen(splash_pix)
        self.splash.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.splash.setEnabled(False)

    def giganet(self):
        print("Giganet")
        [ self.gigaInfo[i].setVisible(True) for i in range(len(self.gigaInfo))]
        [ self.ucInfo[i].setVisible(False) for i in range(len(self.ucInfo))]
        [ self.vInfo[i].setVisible(False) for i in range(len(self.vInfo))]
        [ self.nnInfo[i].setVisible(False) for i in range(len(self.nnInfo))]
        self.locationDisplay.setDisabled(False)
        
    def upcloud(self):
        print("UpCloud")
        [ self.gigaInfo[i].setVisible(False) for i in range(len(self.gigaInfo))]
        [ self.ucInfo[i].setVisible(True) for i in range(len(self.ucInfo))]
        [ self.vInfo[i].setVisible(False) for i in range(len(self.vInfo))]
        [ self.nnInfo[i].setVisible(False) for i in range(len(self.nnInfo))]
        self.locationDisplay.setDisabled(False)

    def vultr(self):
        print("Vultr")
        [ self.gigaInfo[i].setVisible(False) for i in range(len(self.gigaInfo))]
        [ self.ucInfo[i].setVisible(False) for i in range(len(self.ucInfo))]
        [ self.vInfo[i].setVisible(True) for i in range(len(self.vInfo))]
        [ self.nnInfo[i].setVisible(False) for i in range(len(self.nnInfo))]
        self.locationDisplay.setDisabled(False)

    def netnut(self):
        print("NetNut")
        [ self.gigaInfo[i].setVisible(False) for i in range(len(self.gigaInfo))]
        [ self.ucInfo[i].setVisible(False) for i in range(len(self.ucInfo))]
        [ self.vInfo[i].setVisible(False) for i in range(len(self.vInfo))]
        [ self.nnInfo[i].setVisible(True) for i in range(len(self.nnInfo))]
        self.locationDisplay.setDisabled(True)
    
    def enableAll(self):
        # Enable all buttons and text boxes
        [x.setDisabled(False) for x in self.serverButtons]
        [x.setDisabled(False) for x in self.actionButtons]
        self.numberDisplay.setDisabled(False)
        self.locationDisplay.setDisabled(False)
        [self.gigaInfo[i].setDisabled(False) for i in range(len(self.gigaInfo))]
        [self.ucInfo[i].setDisabled(False) for i in range(len(self.ucInfo))]
        [self.vInfo[i].setDisabled(False) for i in range(len(self.vInfo))]
        [self.nnInfo[i].setDisabled(False) for i in range(len(self.nnInfo))]
        self.logDisplay.setDisabled(False)
        self.proxyDisplay.setDisabled(False)

    def disableAll(self):
        # Disable all buttons and text boxes
        [x.setDisabled(True) for x in self.serverButtons]
        [x.setDisabled(True) for x in self.actionButtons]
        self.numberDisplay.setDisabled(True)
        self.locationDisplay.setDisabled(True)
        [self.gigaInfo[i].setDisabled(True) for i in range(len(self.gigaInfo))]
        [self.ucInfo[i].setDisabled(True) for i in range(len(self.ucInfo))]
        [self.vInfo[i].setDisabled(True) for i in range(len(self.vInfo))]
        [self.nnInfo[i].setDisabled(True) for i in range(len(self.nnInfo))]
        self.logDisplay.setDisabled(True)
        self.proxyDisplay.setDisabled(True)

    def threadHelper(self, func, args, res):
        res.append(func(*args))

    def threadHelperNoArgs(self, func):
        func()

    def create(self):
        print("Create")

        if self.serverButtons[0].isChecked() \
                and len(self.numberDisplay.toPlainText()) != 0 \
                and len(self.locationDisplay.toPlainText()) != 0:

            print("Giga create")
            numProxies = self.numberDisplay.toPlainText()
            serverLocation = self.locationDisplay.toPlainText()
            gigaKey = self.gigaInfo[0].toPlainText()
            gigaHash = self.gigaInfo[1].toPlainText()
            self.logDisplay.setPlainText("Giganet chosen. Creating ...")
            self.logDisplay.appendPlainText("Number of Proxies: {}".format(numProxies))
            self.logDisplay.appendPlainText("Server Location: {}".format(serverLocation))
            
            # Run API function in a thread and return value store in res.
            res = [] 
            gigaApiInit(serverLocation,gigaKey,gigaHash)
            thread = threading.Thread(target=self.threadHelper, 
                            args=(gigaApiCreate, (numProxies, serverLocation,), res))
            thread.start()

            # Show splash screen when thread is still running.
            stillAlive = 0
            while thread.is_alive():
                if not stillAlive:
                    self.splash.show()
                    self.disableAll()
                    # When QSplashScreen is running, there should be an event loop running
                    # processEvents forces app to process all events
                    app.processEvents()
                    stillAlive = 1
            else:
                self.splash.close()
                self.enableAll()

            logFile, infoFile = gigaApiReturnFileName()
        
        elif self.serverButtons[1].isChecked() \
                and len(self.numberDisplay.toPlainText()) != 0 \
                and len(self.locationDisplay.toPlainText()) != 0:

            print("UpCloud")
        
        elif self.serverButtons[2].isChecked() \
                and len(self.numberDisplay.toPlainText()) != 0 \
                and len(self.locationDisplay.toPlainText()) != 0:

            print("Vultr")

        elif self.serverButtons[3].isChecked() \
                and len(self.numberDisplay.toPlainText()) != 0:

            print("NetNut")
            numProxies = self.numberDisplay.toPlainText()
            self.logDisplay.setPlainText("NetNut chosen. Creating ...")
            self.logDisplay.appendPlainText("Number of Proxies: {}".format(numProxies))
            nnUsername = self.nnInfo[0].toPlainText()
            nnPassword = self.nnInfo[1].toPlainText()

            # Run API function in a thread and return value store in res.
            res = [] 
            nnApiInit()
            thread = threading.Thread(target=self.threadHelper, 
                            args=(nnApiCreate, (numProxies, nnUsername, nnPassword,), res))
            thread.start()

            # Show splash screen when thread is still running.
            stillAlive = 0
            while thread.is_alive():
                if not stillAlive:
                    self.splash.show()
                    self.disableAll()
                    # When QSplashScreen is running, there should be an event loop running
                    # processEvents forces app to process all events
                    app.processEvents()
                    stillAlive = 1
            else:
                self.splash.close()
                self.enableAll()

            logFile, infoFile = nnApiReturnFileName()

        else:
            print("Check input")

        logThread = displayThread(logFile,self.logDisplay)
        logThread.start()
        
        proxyThread = displayThread(infoFile,self.proxyDisplay)
        proxyThread.start()

    def info(self):
        print("Info")

        if self.serverButtons[0].isChecked():
            print("Giga Info")
            serverLocation = self.locationDisplay.toPlainText()
            gigaKey = self.gigaInfo[0].toPlainText()
            gigaHash = self.gigaInfo[1].toPlainText()
            self.logDisplay.setPlainText("Giganet chosen. Getting Info ...")
            gigaApiInit(serverLocation,gigaKey,gigaHash)

            # Run API function in a thread and return value store in res.
            thread = threading.Thread(target=self.threadHelperNoArgs, 
                            args=(gigaApiInfo,))
            thread.start()

            # Show splash screen when thread is still running.
            stillAlive = 0
            while thread.is_alive():
                if not stillAlive:
                    self.splash.show()
                    self.disableAll()
                    # When QSplashScreen is running, there should be an event loop running
                    # processEvents forces app to process all events
                    app.processEvents()
                    stillAlive = 1
            else:
                self.splash.close()
                self.enableAll()

        else:
            print("Check input")

        logFile, infoFile = gigaApiReturnFileName()

        logThread = displayThread(logFile,self.logDisplay)
        logThread.start()

        proxyThread = displayThread(infoFile,self.proxyDisplay)
        proxyThread.start()

        if sys.platform == 'linux':
            os.system("rm *.txt")
    
    def destroy(self):
        print("Destroy")

        if self.serverButtons[0].isChecked():
            print("Giga destroy")
            self.logDisplay.setPlainText("Giganet chosen. Destroying ...")
            serverLocation = self.locationDisplay.toPlainText()
            gigaKey = self.gigaInfo[0].toPlainText()
            gigaHash = self.gigaInfo[1].toPlainText()
            gigaApiInit(serverLocation,gigaKey,gigaHash)

            # Run API function in a thread and return value store in res.
            thread = threading.Thread(target=self.threadHelperNoArgs, 
                            args=(gigaApiDestroy,))
            thread.start()

            # Show splash screen when thread is still running.
            stillAlive = 0
            while thread.is_alive():
                if not stillAlive:
                    self.splash.show()
                    self.disableAll()
                    # When QSplashScreen is running, there should be an event loop running
                    # processEvents forces app to process all events
                    app.processEvents()
                    stillAlive = 1
            else:
                self.splash.close()
                self.enableAll()

        else:
            print("Check input")

        logFile, infoFile = gigaApiReturnFileName()

        logThread = displayThread(logFile,self.logDisplay)
        logThread.start()

        if sys.platform == 'linux':
            os.system("rm *.txt")

    def quit(self):
        data = {}
        data['giganet'] = []
        data['giganet'].append({
            'apikey' : self.gigaInfo[0].toPlainText(),
            'apihash' : self.gigaInfo[1].toPlainText()
        })
        data['upcloud'] = []
        data['upcloud'].append({
            'ucuser' : self.ucInfo[0].toPlainText(),
            'ucpass' : self.ucInfo[1].toPlainText()
        })
        data['vultr'] = []
        data['vultr'].append({
            'vtoken' : self.vInfo[0].toPlainText()
        })
        data['netnut'] = []
        data['netnut'].append({
            'nnuser' : self.nnInfo[0].toPlainText(),
            'nnpass' : self.nnInfo[1].toPlainText()
        })

        with open('data/info.txt', 'w') as fh:
            json.dump(data, fh)

        QApplication.quit()


class MainWindow(QMainWindow):
    
    
    def __init__(self, parent = None):
    
        QMainWindow.__init__(self, parent)
        self.title = 'SamProxyMaker'
        self.icon = 'data/icon.svg'
        self.width = 640
        self.height = 480
        
        # Window
        self.setWindowTitle(self.title)
        frameGm = self.frameGeometry()
        centerPoint = QApplication.desktop().availableGeometry().center()
        frameGm.moveCenter(centerPoint)
        self.move(frameGm.topLeft() * 0.7)
        self.resize(self.width, self.height)
        self.setWindowIcon(QIcon(self.icon))

        # Main Widgets
        widget = proxyMaker()
        self.setCentralWidget(widget)


if __name__ == '__main__':
    global app
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())
