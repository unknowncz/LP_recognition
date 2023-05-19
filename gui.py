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

        self.centralwidgets = {'main':QtWidgets.QWidget(), 'cameramanager':QtWidgets.QWidget(), 'dbmanager':QtWidgets.QWidget(), 'settings':QtWidgets.QWidget()}
        self.centralwidgets.setdefault('main', self.centralwidgets['main'])

        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # layout for the main window
        self.window = QtWidgets.QMainWindow()
        self.cw = QtWidgets.QStackedWidget()
        self.cw.addWidget(self.centralwidgets['main'])
        self.cw.addWidget(self.centralwidgets['cameramanager'])
        self.cw.addWidget(self.centralwidgets['dbmanager'])
        self.cw.addWidget(self.centralwidgets['settings'])
        self.window.setCentralWidget(self.cw)
        layout = QtWidgets.QHBoxLayout(self.cw.currentWidget())
        self.window.setMinimumSize(1250, 600)
        # make the window frameless
        #self.window.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
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
        btn_txt = ['Camera Manager', 'DB Manager', 'Manual Override']
        buttons = [QtWidgets.QPushButton(i) for i in btn_txt]
        # make the manual override button pulse green when it is clicked
        self.manualoverride_btn = buttons[2]
        anim = QtCore.QVariantAnimation()
        anim.setStartValue(255)
        anim.setEndValue(1)
        anim.setDuration(10000)
        anim.valueChanged.connect(lambda x: self.manualoverride_btn.setStyleSheet(f'background-color: rgba(0, 255, 0, {int(x)})'))
        anim.finished.connect(lambda: self.manualoverride_btn.setStyleSheet(''))
        #anim.setLoopCount(1)
        funcs = [self.cameramgr, self.dbmgr, lambda:(self.manualoverride(), anim.start())]
        # connect the functions
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
        buttons2[0].clicked.connect(self.switchtosettings)
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

        # add the back button
        back_btn = QtWidgets.QPushButton('Back')
        layout.addWidget(back_btn)
        back_btn.clicked.connect(lambda:(self.resetdbchanges(),self.resetContent()))


        # settings window
        # |--------------------------------------------------|
        # | [QLabel]: [Setting]                              |
        # | [QLabel]: [Setting]                              |
        # | [QLabel]: [Setting]                              |
        # | [QLabel]: [Setting]                              |
        # |                                                  |
        # |                                                  |
        # | [cancel]                                 [apply] |
        # | [                    back                      ] |
        # |--------------------------------------------------|

        # add a vertical layout for the buttons as the first item in the layout
        self.settingslayout = QtWidgets.QVBoxLayout()
        centerwidget = self.centralwidgets['settings']
        centerwidget.setLayout(self.settingslayout)

        # add each entry in the config file to the layout
        widgettypes = {'int':QtWidgets.QSpinBox, 'float':QtWidgets.QDoubleSpinBox, 'str':QtWidgets.QLineEdit, 'bool':QtWidgets.QCheckBox}
        self.translatetable = {'bool':lambda x:True if x=='True' else False, 'int':int, 'float':float, 'str':str}
        for row in self.config['USER']:
            value, widgettype = self.config['USER'][row].split(', ')
            self._addWidgetPair(row, widgettypes[widgettype](), self.settingslayout)
            # set the value of the widget
            self.modifyWidget(self.settingslayout, self.settingslayout.count()-1, self.translatetable[widgettype](value))
            # add a stretch so the settings aren't as wide
            self.settingslayout.itemAt(self.settingslayout.count()-1).layout().addStretch()

        self.settingslayout.addStretch()
        # add the cancel and apply buttons
        cancelbtn = QtWidgets.QPushButton('Cancel')
        applybtn = QtWidgets.QPushButton('Apply')
        cancelbtn.setMinimumWidth(100)
        applybtn.setMinimumWidth(100)

        l = QtWidgets.QHBoxLayout()
        cancelbtn.clicked.connect(self.resetsettings)
        applybtn.clicked.connect(lambda:(self.applysettings(), self.resetsettings()))
        l.addStretch(2)
        l.addWidget(cancelbtn)
        l.addStretch(3)
        l.addWidget(applybtn)
        l.addStretch(2)
        self.settingslayout.addLayout(l)

        # add the back button
        back_btn = QtWidgets.QPushButton('Back')
        self.settingslayout.addWidget(back_btn)
        back_btn.clicked.connect(lambda:(self.resetsettings(),self.resetContent()))

        self.applysettings()

        # exec and kill
        self.app.exec()
        self.kill()

# ---------------------------- GENERIC FUNCTIONS --------------------------------
    def _addWidgetPair(self, label:str, widget:QtWidgets.QWidget, layout:QtWidgets.QLayout):
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

    def modifyWidget(self, layout:QtWidgets.QLayout, index:int, value):
        """Modify the passed widgets contents.

        Args:
            layout (QLayout): QLayout holding the widget.
            index (int): Index of the widget in the layout.
            value (Any): The QWidget will be set to this value.
        """
        w = layout.itemAt(index).layout().itemAt(1).widget()
        # you cannot directly access the object methods, so we need a match-case
        match (value.__class__.__name__):
            case ['int', 'float']:
                w.setValue(value)
            case 'str':
                w.setText(value)
            case 'bool':
                w.setChecked(value)

    def getwidgetvalue(self, layout:QtWidgets.QLayout, index:int):
        """Get the value of a widget in a layout

        Args:
            layout (QLayout): QLayout holding the widget.
            index (int): Index of the widget in the layout.

        Returns:
            Any: The value of the widget
        """
        w = layout.itemAt(index).layout().itemAt(1).widget()
        match (w.__class__.__name__):
            case ['QSpinBox', 'QDoubleSpinBox']:
                return w.value()
            case 'QLineEdit':
                return w.text()
            case 'QCheckBox':
                return w.isChecked()

    def resetContent(self):
        """Reset the content of the main window to the main widget
        """
        self.cw.setCurrentWidget(self.centralwidgets['main'])
        self.camerawidget.setCurrentIndex(0)

    def kill(self):
        self.app.exit()

# ---------------------------- SETTINGS FUNCTIONS --------------------------------
    def switchtosettings(self):
        """Show the settings widget
        """
        self.cw.setCurrentWidget(self.centralwidgets['settings'])

    def resetsettings(self):
        """Reset the settings to the values written in the config
        """
        for idx in range(self.settingslayout.count()-3):
            value, widgettype = self.config['USER'][self.settingslayout.itemAt(idx).layout().itemAt(0).widget().text()].split(', ')
            self.modifyWidget(self.settingslayout, idx, self.translatetable[widgettype](value))

    def applysettings(self):
        """Apply the settings and write them to the config file
        """
        # write the settings to the config file
        for idx in range(self.settingslayout.count()-3):
            key = self.settingslayout.itemAt(idx).layout().itemAt(0).widget().text()
            value = self.getwidgetvalue(self.settingslayout, idx)
            self.config['USER'][key] = f'{value}, {value.__class__.__name__}'
        # write the config file
        with open('config.ini', 'w') as f:
            self.config.write(f)
        # apply the settings
        self.applysettingsfunc()

    def applysettingsfunc(self):
        """Apply the settings to the program
        """
        # apply the settings to the program
        if self.config['USER']['darkmode'] == 'True, bool':
            with open(f'{__file__}\\..\\style.qss', 'r') as f:
                self.app.setStyleSheet(f.read())
        else:
            self.app.setStyleSheet('')

# ---------------------------- CAMERA FUNCTIONS --------------------------------
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

    def addcamera(self):
        """Add a new camera to the camera manager
        """
        # add a new camera to the config file
        # this will also add a new section to the config file
        # the new section will be named CAM_{num_cameras}
        # the new section will have the following options

        # create a new section
        self.config[f'CAM_{int(self.config["GENERAL"]["num_cameras"])}'] = {'IP':'127.0.0.1', 'Port':'554', 'Login':'admin', 'Password':'admin', 'Protocol':'rtsp'}
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

    def deletecamera(self, id:int):
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


# ---------------------------- DATABASE FUNCTIONS --------------------------------
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


# ---------------------------- MANUAL OVERRIDE FUNCTION --------------------------------
    def manualoverride(self):
        """Manually override the parent check for the next 10 seconds
        """
        self.mgr.nextautopass = (time.time() + 10, True)


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
        # # |   Protocol: {field}                             |
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
        for i in ['IP', 'Port', 'Login', 'Password', 'Protocol']:
            w = QtWidgets.QLineEdit()
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
        btn = QtWidgets.QPushButton("Live feed", clicked=lambda: self.manager.feedmgr.start(cfg) if self.manager.feedmgr.thread is None else self.manager.feedmgr.stop())
        btn.setMinimumWidth(75)
        layout.addWidget(btn)
        layout.addStretch()
        btn2 = QtWidgets.QPushButton("Reset", clicked=self.reset)
        btn2.setMinimumWidth(75)
        layout.addWidget(btn2)
        btn3 = QtWidgets.QPushButton("Apply", clicked=self.apply)
        btn3.setMinimumWidth(75)
        layout.addWidget(btn3)
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
