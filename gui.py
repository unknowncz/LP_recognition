import PyQt6.QtWidgets as QtWidgets
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as QtCore
import logging
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from sys import stdout
import configparser

import utils

class GUImgr:
    def __init__(self, guiQueue:Queue=None):
        self.app = QtWidgets.QApplication([])
        self.config = configparser.ConfigParser()
        self.config.read(f'{__file__}\\..\\config.ini')
        
        self.subwindows = {}
        self.centralwidgets = {'main':QtWidgets.QWidget(), 'cameramanager':QtWidgets.QWidget(), 'dbmanager':QtWidgets.QWidget()}
        self.centralwidgets.setdefault('main', self.centralwidgets['main'])

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # layout for the main window
        self.window = QtWidgets.QMainWindow()
        self.cw = QtWidgets.QStackedWidget()
        self.cw.addWidget(self.centralwidgets['main'])
        self.cw.addWidget(self.centralwidgets['cameramanager'])
        self.window.setCentralWidget(self.cw)
        layout = QtWidgets.QHBoxLayout(self.cw.currentWidget())
        self.window.setMinimumSize(1250, 600)
        self.centralwidgets.setdefault('main', self.cw)

# ---------------------------- MAIN LAYOUT --------------------------------
        # |---------------------|-------------------------------|
        # |       button        |                               |
        # |       button        |                               |
        # |       button        |               log             |
        # |                     |                               |
        # |                     |                               |
        # |   button   button   |                               |
        # |---------------------|-------------------------------|

        # add a vertical layout for the buttons as the first item in the layout
        button_layout = QtWidgets.QVBoxLayout()
        helperwidget = QtWidgets.QWidget()
        helperwidget.setMinimumWidth(200)
        helperwidget.setLayout(button_layout)
        layout.addWidget(helperwidget)

        # create three buttons
        buttons = [QtWidgets.QPushButton(['Camera Manager', 'DB Manager', 'Manual Override'][i]) for i in range(3)]
        buttons[0].clicked.connect(self.cameramgr)

        # add the buttons to the layout
        for i in buttons:
            button_layout.addWidget(i)
        button_layout.addStretch()
        
        # add a bottom row of buttons
        button_layout2 = QtWidgets.QHBoxLayout()
        button_layout.addLayout(button_layout2)
        buttons2 = [QtWidgets.QPushButton(['Settings', 'Exit'][i]) for i in range(2)]
        buttons2[1].clicked.connect(self.kill)
        buttons2[0].clicked.connect(self.settingswindow)
        for i in buttons2:
            button_layout2.addWidget(i)
        
        
        # create an unwriteable text box for the logger output
        self.loggerout = QtWidgets.QTextEdit()
        self.loggerout.setReadOnly(True)
        self.loggerout.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
        self.loggerout.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
        self.loggerout.setFont(QtGui.QFont("Cascadia Mono", 10))
        layout.addWidget(self.loggerout)
        self.window.show()

        # add a handler for the logger to write to the text box
        if guiQueue is not None:
            meta = self.loggerout.metaObject()
            handler = utils.LoggerOutput(guiQueue, reciever_meta=meta, reciever=self.loggerout, formatter=logging.Formatter("%(asctime)s | %(levelname)-8s | %(message)s"))
            listener = QueueListener(guiQueue, handler)
            listener.start()
            self.logger.addHandler(QueueHandler(guiQueue))

        self.logger.addHandler(logging.StreamHandler(stdout))
        self.logger.info("GUI started")

# ---------------------------- CAMERA MANAGER LAYOUT --------------------------------
        # |------------------|-------------------------------|
        # |     button       |                               |
        # |     button       |                               |
        # |     button       |         cam_settings          |
        # |                  |                               |
        # |                  |                               |
        # |   back_button    |                               |
        # |------------------|-------------------------------|

        # add a vertical layout for the buttons as the first item in the layout
        layout = QtWidgets.QHBoxLayout()
        cambutton_layout = QtWidgets.QVBoxLayout()
        centerwidget = self.centralwidgets['cameramanager']
        centerwidget.setLayout(layout)
        
        # create a button for all the cameras
        # the camera names are stored in the config file
        cambuttons = [QtWidgets.QPushButton(f'Camera {str(i)}') for i in range(int(self.config['GENERAL']['num_cameras']))]
        for i, j in enumerate(cambuttons):
            cambutton_layout.addWidget(j)
            j.clicked.connect(lambda: self.camdetails(i))
        cambutton_layout.addStretch()

        # add the back button
        cambuttons += [QtWidgets.QPushButton('Back')]
        cambutton_layout.addWidget(cambuttons[-1])
        cambuttons[-1].clicked.connect(self.resetContent)
        helperwidget = QtWidgets.QWidget()
        helperwidget.setMinimumWidth(200)
        helperwidget.setMaximumWidth(200)
        helperwidget.setLayout(cambutton_layout)
        centerwidget.layout().addWidget(helperwidget)

        # add the camera settings to the layout
        self.camsettings = QtWidgets.QStackedWidget()
        self.camsettings.setMinimumWidth(500)
        self.camsettingpages:list[QtWidgets.QWidget] = []
        self.camsettings.addWidget(q:=QtWidgets.QLabel("Select a camera to view its details"))
        self.camsettingpages.append(q)
        for i in range(int(self.config['GENERAL']['num_cameras'])):
            widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout()
            widget.setLayout(layout)
            title = QtWidgets.QLabel(f"Camera {i}")
            # title.setMaximumHeight(50)
            layout.addWidget(title)
            for j in ['IP', 'Port', 'Login', 'Password']:
                self._addWidgetPair(j, QtWidgets.QLineEdit(self.config[f'CAM_{i}'][j]), layout)
            layout.addStretch()
            self.camsettings.addWidget(widget)
            self.camsettingpages.append(widget)
        
        centerwidget.layout().addWidget(self.camsettings)
        
        self.camsettings.setCurrentIndex(0)

        # add the internals of the camera settings
        # |-------------------------------------------------|
        # |   Cam id:   {id}                                |
        # |                                                 |
        # |   IP:       {ip}                                |
        # |   Port:     {port}                              |
        # |   Login:    {field}                             |
        # |   Password: {field}                             |
        # |                                                 |
        # |   [Live feed]                 [Reset] [Apply]   |
        # |                                                 |
        # |-------------------------------------------------|
        
        # add the layout to the widgets

        self.feedmgr = utils.FeedManager(self.logger)

        def get_lower_btns(id=0):
            lower_buttons = QtWidgets.QHBoxLayout()
            funcs = [lambda: self.feedmgr.add({**self.config[f'CAM_{id}']}|{'id':id}), self.resetCamSettings, self.applyCamSettings]
            for i, btn_label in enumerate(['Live Feed', 'Reset', 'Apply']):
                btn = QtWidgets.QPushButton(btn_label)
                if i == 1:
                    lower_buttons.addStretch()
                btn.clicked.connect(funcs[i])
                lower_buttons.addWidget(btn)
            return lower_buttons

        for i, j in enumerate(self.camsettingpages[1:]):
            w = QtWidgets.QWidget()
            w.setLayout(get_lower_btns())
            j.layout().addWidget(w)

        

# ---------------------------- DB MANAGER LAYOUT --------------------------------
        # idk what to do here yet

        exit(self.app.exec())
    
    def settingswindow(self):
        # make a new window if the settings button is clicked and the window is not already open
        if type(window:=self.subwindows.get('settings', None)) == utils.SubWindow:
            # window already open, bring it to the front
            window.show()
            window.setWindowState(QtCore.Qt.WindowState.WindowActive)
            window.raise_()
            return
        window = utils.SubWindow(title="Settings")
        window.setMinimumSize(500, 250)
        
        layout = QtWidgets.QVBoxLayout(window)
        layout.addWidget(QtWidgets.QLabel("Settings"))
        # window.centralWidget.setLayout(layout)
        self.subwindows |= {'settings':window}
        window.show()

    def camdetails(self, camid):
        self.camsettings.setCurrentIndex(camid+1)
        # self.camsettings.setText(f"Camera {camid+1}")

    def cameramgr(self):
        self.cw.setCurrentWidget(self.centralwidgets['cameramanager'])

    def dbmgr(self):
        self.cw.setCurrentWidget(self.centralwidgets['dbmanager'])

    def resetContent(self):
        self.cw.setCurrentWidget(self.centralwidgets['main'])
        self.camsettings.setCurrentIndex(0)


    def _addWidgetPair(self, label, widget, layout):
        l = QtWidgets.QHBoxLayout()
        l.addWidget(QtWidgets.QLabel(label))
        l.addWidget(widget)
        layout.addLayout(l)

    def resetCamSettings(self):
        # reset the camera settings to the values in the config file
        

    def applyCamSettings(self):
        # apply the camera settings to the config file
        # and to the camera manager
        # then save the config file
        for i, j in enumerate(self.camsettingpages[1:]):
            for k in j.children():
                if type(k) == QtWidgets.QLineEdit:
                    self.config[f'CAM_{i}'][k.text()] = k.text()

    def kill(self):
        self.app.exit()

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.DEBUG)
    gui = GUImgr()