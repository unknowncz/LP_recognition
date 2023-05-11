import PyQt6.QtWidgets as QtWidgets
import PyQt6.QtGui as QtGui
import PyQt6.QtCore as QtCore
import logging
from logging.handlers import QueueHandler, QueueListener
from multiprocessing import Queue
from sys import stdout
import configparser
import time

import utils
import dbmgr

class GUImgr:
    """GUI manager class for the main window
    """
    def __init__(self, guiQueue:Queue=None, db=dbmgr.DatabaseHandler(f'{__file__}\\..\\lp.csv'), mgr=None):
        """Initialize the class and the GUI

        Args:
            guiQueue (Queue, optional): Logging queue for multiprocess communication. Defaults to None.
            db (dbmgr.DatabaseHandler, optional): Database handler for easier access to data and for easier overrides. Defaults to dbmgr.DatabaseHandler(f'{__file__}\..\lp.csv').
            mgr (manager.taskDistributor, optional): Parent class for access to its variables. Defaults to None.
        """
        self.app = QtWidgets.QApplication([])
        self.config = configparser.ConfigParser()
        self.config.read(f'{__file__}\\..\\config.ini')
        self.DBmgr = db
        self.mgr = mgr

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
        self.cw.addWidget(self.centralwidgets['dbmanager'])
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
        funcs = [self.cameramgr, self.dbmgr, self.manualoverride]
        btn_txt = ['Camera Manager', 'DB Manager', 'Manual Override']
        buttons = [QtWidgets.QPushButton(i) for i in btn_txt]
        [i.clicked.connect(funcs[j]) for j, i in enumerate(buttons)]
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
        # |    add camera    |                               |
        # |                  |                               |
        # |   back_button    |                               |
        # |------------------|-------------------------------|

        # add a vertical layout for the buttons as the first item in the layout
        layout = QtWidgets.QHBoxLayout()
        self.cambutton_layout = QtWidgets.QVBoxLayout()
        centerwidget = self.centralwidgets['cameramanager']
        centerwidget.setLayout(layout)

        # create a button for all the cameras
        # the camera names are stored in the config file
        self.cambuttons = [QtWidgets.QPushButton(f'Camera {str(i)}') for i in range(int(self.config['GENERAL']['num_cameras']))]
        for i, j in enumerate(self.cambuttons):
            self.cambutton_layout.addWidget(j)

        # add the add camera button
        self.cambuttons += [QtWidgets.QPushButton('Add Camera')]
        self.cambutton_layout.addWidget(self.cambuttons[-1])
        self.cambuttons[-1].clicked.connect(self.addcamera)
        self.cambutton_layout.addStretch()

        # add the back button
        self.cambuttons += [QtWidgets.QPushButton('Back')]
        self.cambutton_layout.addWidget(self.cambuttons[-1])
        self.cambuttons[-1].clicked.connect(self.resetContent)
        helperwidget = QtWidgets.QWidget()
        helperwidget.setMinimumWidth(200)
        helperwidget.setMaximumWidth(200)
        helperwidget.setLayout(self.cambutton_layout)
        centerwidget.layout().addWidget(helperwidget)

        # add the camera settings to the layout
        self.camerawidget = QtWidgets.QStackedWidget()

        # add the default text
        self.camerawidget.addWidget(QtWidgets.QLabel('Select a camera to view its settings'))

        self.camerawidget.setMinimumWidth(500)
        self.cameras = []
        for i in range(int(self.config['GENERAL']['num_cameras'])):
            # add a camera for each camera in the config file
            self.cameras.append(Camera(self.config, i, self, self.cambuttons[i]))
            self.camerawidget.addWidget(self.cameras[-1])
        self.camerawidget.setCurrentIndex(0)

        centerwidget.layout().addWidget(self.camerawidget)

        self.feedmgr = utils.FeedManager(self.logger)

# ---------------------------- DB MANAGER LAYOUT --------------------------------
        # |--------------------------------------------------|
        # | [row 1 item 1          ][row 1 item 2          ] |
        # | [row 2 item 1          ][row 2 item 2          ] |
        # | [row 3 item 1          ][row 3 item 2          ] |
        # |                 add_row_button                   |
        # |                                                  |
        # |         cancel                      apply        |
        # |                      back                        |
        # |--------------------------------------------------|

        # add a vertical layout for the buttons as the first item in the layout
        layout = QtWidgets.QVBoxLayout()
        scroll = QtWidgets.QScrollArea()
        self.dblayout = QtWidgets.QGridLayout()
        self.dblayout.setSizeConstraint(QtWidgets.QLayout.SizeConstraint.SetNoConstraint)
        self.dblayout.setContentsMargins(0, 0, 0, 0)
        centerwidget = self.centralwidgets['dbmanager']
        centerwidget.setLayout(layout)

        # apply the above code only for the width

        helperlayout = QtWidgets.QVBoxLayout()
        helperwidget = QtWidgets.QWidget()
        helperwidget.setLayout(self.dblayout)
        helperwidget.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.MinimumExpanding)
        helperlayout.addWidget(helperwidget)

        # add each entry in the config file to the layout
        for i, row in enumerate(self.DBmgr):
            self.adddbrow(row[0], row[1])

        # add a vertical spacer to the end of the layout
        addrowbtn = QtWidgets.QPushButton('Add Row')

        addrowbtn.clicked.connect(lambda: self.adddbrow('', ''))
        helperlayout.addWidget(addrowbtn)
        helperlayout.addStretch(200)

        # add the cancel and apply buttons
        cancelbtn = QtWidgets.QPushButton('Cancel')
        applybtn = QtWidgets.QPushButton('Apply')
        cancelbtn.setMinimumWidth(100)
        applybtn.setMinimumWidth(100)

        l = QtWidgets.QHBoxLayout()
        cancelbtn.clicked.connect(self.resetdbchanges)
        applybtn.clicked.connect(lambda:(self.applydbchanges(), self.resetdbchanges()))
        l.addStretch(2)
        l.addWidget(cancelbtn)
        l.addStretch(3)
        l.addWidget(applybtn)
        l.addStretch(2)
        helperlayout.addLayout(l)

        scroll.setLayout(helperlayout)

        layout.addWidget(scroll)

        # add the add row button
        # self.dbbuttons[-1].clicked.connect(self.adddbrow)
        # self.dbbutton_layout.addStretch()

        # add the back button
        back_btn = QtWidgets.QPushButton('Back')
        layout.addWidget(back_btn)
        back_btn.clicked.connect(lambda:(self.resetdbchanges(),self.resetContent()))
        # helperwidget.setMinimumWidth(200)
        # helperwidget.setMaximumWidth(200)


        # exec and kill
        self.app.exec()
        self.kill()

    def settingswindow(self):
        """Create a new window for the settings. If the window is already open, bring it to the front. To be phased out.
        """
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

    def camdetails(self, camid:int):
        """Show the settings for the camera with the given id

        Args:
            camid (int): The id of the camera to show the settings for
        """
        self.camerawidget.setCurrentIndex(camid+1)
        # self.camsettings.setText(f"Camera {camid+1}")

    def cameramgr(self):
        """Show the camera manager widget
        """
        self.cw.setCurrentWidget(self.centralwidgets['cameramanager'])

    def dbmgr(self):
        """Show the database manager widget
        """
        self.cw.setCurrentWidget(self.centralwidgets['dbmanager'])

    def applydbchanges(self):
        """Apply the changes made to the database manager and save them to the .csv file
        """
        # get the text from each line edit and save it to the config file
        self.DBmgr.database = {}
        for i in range(self.dblayout.rowCount()):
            if self.dblayout.itemAtPosition(i, 0) is None:
                continue
            key = self.dblayout.itemAtPosition(i, 0).widget().text()
            value = self.dblayout.itemAtPosition(i, 1).widget().text()
            if key:
                self.DBmgr.database[key] = value
        self.DBmgr.save()

    def resetdbchanges(self):
        """Reset the database manager to the values in the .csv file
        """
        for i in reversed(range(self.dblayout.count())):
            # remove all the widgets from the layout
            self.dblayout.itemAt(i).widget().deleteLater()
            self.dblayout.itemAt(i).widget().setParent(None)
        # set the row height to 0 to remove the empty row(s)
        for i in reversed(range(self.dblayout.rowCount())):
            self.dblayout.setRowMinimumHeight(i, 0)
        for idx, row in enumerate(self.DBmgr):
            self.adddbrow(row[0], row[1], forceidx=idx)

    def adddbrow(self, *args, forceidx:int=None):
        """Add a new row to the database manager

        Args:
            forceidx (int, optional): Force index of row to be modified rather than add a new row. Defaults to None.
        """
        # add n new line edits to the layout
        row = self.dblayout.rowCount() if forceidx is None else forceidx
        for i, text in enumerate(args):
            le = QtWidgets.QLineEdit()
            le.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
            le.setText(str(text))
            le.setMaximumHeight(20)
            le.setMinimumHeight(20)
            # add a new row
            self.dblayout.addWidget(le, row, i)
            # set the text to the default value
        self.dblayout.setRowMinimumHeight(row, 20)

    def manualoverride(self):
        """Manually override the parent check for the next 10 seconds
        """
        self.mgr.nextautopass = (time.time() + 10, True)

    def resetContent(self):
        """Reset the content of the main window to the main widget
        """
        self.cw.setCurrentWidget(self.centralwidgets['main'])
        self.camerawidget.setCurrentIndex(0)

    def _addWidgetPair(self, label:str, widget, layout):
        """Add a label and widget pair to a layout (QLabel, widget)

        Args:
            label (str): Label to be displayed next to the widget
            widget (QWidget): Widget to be added
            layout (QLayout): Layout to hold the label and widget
        """
        l = QtWidgets.QHBoxLayout()
        l.addWidget(QtWidgets.QLabel(label))
        l.addWidget(widget)
        layout.addLayout(l)

    def addcamera(self):
        """Add a new camera to the camera manager
        """
        # add a new camera to the config file
        # this will also add a new section to the config file
        # the new section will be named CAM_{num_cameras}
        # the new section will have the following options

        # create a new section
        self.config[f'CAM_{int(self.config["GENERAL"]["num_cameras"])}'] = {'IP':'127.0.0.1', 'Port':'554', 'Login':'admin', 'Password':'admin'}
        # update the number of cameras
        self.config['GENERAL']['num_cameras'] = str(int(self.config['GENERAL']['num_cameras'])+1)

        # apply the current camera config
        if self.camerawidget.currentIndex() != 0:
            self.camerawidget.currentWidget().apply()

        # create a new camera object
        self.cambuttons.insert(-2, QtWidgets.QPushButton(f'Camera {str(int(self.config["GENERAL"]["num_cameras"])-1)}'))
        self.cambutton_layout.insertWidget(len(self.cambuttons)-3, self.cambuttons[-3])
        self.cameras.append(Camera(self.config, int(self.config["GENERAL"]["num_cameras"])-1, self, self.cambuttons[-3]))
        self.camerawidget.addWidget(self.cameras[-1])
        self.camerawidget.setCurrentIndex(len(self.cameras))
        # apply the new camera config
        self.cameras[-1].apply()

    def deletecamera(self, id):
        """Delete a camera from the camera manager given its id

        Args:
            id (int): ID of the camera to be deleted
        """
        # delete the camera with the given id

        # remove the camera from the config file
        # update the number of cameras
        self.config['GENERAL']['num_cameras'] = str(int(self.config['GENERAL']['num_cameras'])-1)
        # move all sections with a higher id down one
        for i in range(id, int(self.config['GENERAL']['num_cameras'])):
            self.config[f'CAM_{i}'] = {**self.config[f'CAM_{i+1}']}
                # self.cameras[i].updateId(i-1)
                # self.config.remove_section(f'CAM_{i+1}')

        self.config.remove_section(f'CAM_{int(self.config["GENERAL"]["num_cameras"])}')
        # remove the last camera from the camera list
        self.cameras[-1].button.deleteLater()
        self.cameras.pop()
        # apply the current camera config
        for i in range(int(self.config['GENERAL']['num_cameras'])):
            self.cameras[i].updateId(i)
            self.cameras[i].reset()

        # remove the last camera from the camera list
        # remove the camera button
        self.cambutton_layout.removeWidget(self.cambuttons.pop(-3))
        # reset the current camera
        self.camerawidget.setCurrentIndex(0)

        # write the config file
        for i in range(int(self.config['GENERAL']['num_cameras'])):
            self.cameras[i].apply()

    def kill(self):
        self.app.exit()

class Camera(QtWidgets.QWidget):
    """Helper class to manage the camera settings and controls
    """
    def __init__(self, config:configparser.ConfigParser, id:int, manager:GUImgr, button:QtWidgets.QPushButton):
        """Create a new camera object

        Args:
            config (configparser.ConfigParser): Config to be used
            id (int): ID of the camera
            manager (GUImgr): parent GUI manager
            button (QtWidgets.QPushButton): Button to be used to switch to this camera
        """
        super().__init__()
        self.config = config
        self.id = id
        self.manager = manager
        self.button = button
        self.button.clicked.connect(lambda: self.manager.camdetails(self.id))
        # create the layout according to this
        # # add the internals of the camera settings
        # # |-------------------------------------------------|
        # # |   Cam id:   {id}                                |
        # # |                                                 |
        # # |   IP:       {ip}                                |
        # # |   Port:     {port}                              |
        # # |   Login:    {field}                             |
        # # |   Password: {field}                             |
        # # |                                                 |
        # # |   [Delete camera]                               |
        # # |   empty line                                    |
        # # |   [Live feed]                 [Reset] [Apply]   |
        # # |                                                 |
        # # |-------------------------------------------------|

        # add the title
        self.layout = QtWidgets.QVBoxLayout(self)
        self.title = QtWidgets.QLabel(f"Camera {id}")
        self.layout.addWidget(self.title)
        # add the inputs
        self.inputs = {}
        for i in ['IP', 'Port', 'Login', 'Password']:
            w = QtWidgets.QLineEdit()
            self.inputs |= {i:w}
            l = QtWidgets.QHBoxLayout()
            self._addWidgetPair(i, w, l)
            self.layout.addLayout(l)
            self.inputs |= {i:w}
        self.reset()
        # add the delete button
        deletebutton = QtWidgets.QPushButton("Delete camera", clicked=lambda: self.manager.deletecamera(id))
        self.layout.addStretch()
        self.layout.addWidget(deletebutton)
        # add the empty line
        self.layout.addWidget(QtWidgets.QLabel(''))
        # add the live feed button
        self.layout.addLayout(self.get_lower_btns())
        self.setLayout(self.layout)

    def _addWidgetPair(self, label:str, widget:QtWidgets.QWidget, layout:QtWidgets.QLayout):
        """Add a label and a widget to a layout

        Args:
            label (str): Label to be used
            widget (QWidget): Widget to be added to the layout
            layout (QLayout): Layout to hold the label and the widget
        """
        # add a label and a widget to the layout
        l = QtWidgets.QLabel(label)
        l.setFixedWidth(100)
        layout.addWidget(l)
        layout.addWidget(widget)

    def get_lower_btns(self):
        """Create the lower buttons for the camera details page.

        Returns:
            QLayout: Layout containing the lower buttons
        """
        # get the lower buttons
        layout = QtWidgets.QHBoxLayout()
        cfg = {'id':self.id}|{k:v for k, v in self.config.items(f'CAM_{self.id}')}
        layout.addWidget(QtWidgets.QPushButton("Live feed", clicked=lambda: self.manager.feedmgr.start(cfg) if self.manager.feedmgr.thread is None else self.manager.feedmgr.stop()))
        layout.addStretch()
        layout.addWidget(QtWidgets.QPushButton("Reset", clicked=self.reset))
        layout.addWidget(QtWidgets.QPushButton("Apply", clicked=self.apply))
        return layout

    def reset(self):
        """Reset the details of the camera to the values contained in the config file
        """
        # reset the inputs to the config file
        for k, v in self.inputs.items():
            v.setText(self.config[f'CAM_{self.id}'][k])

    def apply(self):
        """Write the details of the camera to the config file.
        """
        # apply the inputs to the config file
        for i in self.inputs:
            self.config[f'CAM_{self.id}'][i] = self.inputs[i].text()
        self.config.write(open(f'{__file__}\\..\\config.ini', 'w'), True)
        self.reset()

    def updateId(self, id:int):
        """Update the id of the camera.

        Args:
            id (int): New id of the camera
        """
        # change the id of the camera in all the necessary places
        self.id = id
        self.title.setText(f"Camera {id}")
        self.button.clicked.connect(lambda: self.manager.camdetails(self.id))


if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s — %(levelname)s — %(message)s", level=logging.DEBUG)
    gui = GUImgr()