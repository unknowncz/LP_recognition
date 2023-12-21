
# Function and class usage and examples #

## Camera.py ##

This file contains a helper class with functions related to camera connection and interfacing.

### Camera (class) ###

Helper class with functions related to camera connection and interfacing.

#### __\_\_init\_\___ ####

This function sets up class variables and logging.

```cfg``` is the camera config as a ```dict``` with the attributes:

- id (int) - Internal camera ID. Used for image transport purposes.

- ip (str) - Connection IP of the camera.

- protocol (str) - Communication protocol to use with the camera (http, rstp, etc.).

- port (int) - Connection port which the camera is listening on.

- login (str) - provided username. Used for username / password protected cameras.

- password (str) - provided password. Used for username / password protected cameras.

```output``` is the namespace to which the camera will be writing the recieved frames.

```loggerQueue``` (optional) is a ```multiprocessing.Queue``` object to which logs will be written.

```autoconnect``` (optional) automatically attempts to connect using the ```Camera.connect``` class function.
By default, this also causes the ```Camera.connect``` function to have the ```autostart=True``` argument be set.  Defaults to ```False```.

Returns: ```None```.

##### Usage #####

    ...
    cfg = {
        "id":0,
        "ip":"127.0.0.1",
        "port":554,
        "login":"admin",
        "password":"admin",
        "protocol":"rtsp"
    }
    loggingQueue = multiprocessing.Queue()
    manager = multiprocessing.Manager()
    namespace = manager.Namespace()
    camera = Camera(id=0, cfg=cfg, output=namespace, loggerQueue=loggingQueue, autoconnect=True)
    ...

#### __connect__ ####

This function initializes a connection to the camera.

```autostart``` (optional) automatically starts the frame-grabbing loop. Defaults to ```False```.

Returns: ```None```

##### Usage #####

    ...
    camera = Camera(0, cfg, namespace, loggingQueue, autoconnect=False)
    camera.connect(autostart=True)
    ...

#### __run__ ####

Starts the frame-grabbing loop. Use ```process.kill``` or equivalent to exit the loop.

```NoReturn``` function.

##### Usage #####

    ...
    camera = Camera(0, cfg, namespace, loggingQueue, autoconnect=False)
    camera.connect()
    camera.run()
    ...

The above usage works, however it is best used when in a different thread/process - see example below.

    ...
    camera = Camera(0, cfg, namespace, loggingQueue, autoconnect=False)
    camera.connect()
    thread = threading.Thread(target=camera.run)
    thread.start()
    ...

---

## dbmgr.py ##

This file contains a helper class with functions related to database interfacing.

### DatabaseHandler (class) ##

A class to manage data access and modification.

> Note: The default database interface is suboptimal, use a custom implementation.

#### __\_\_init\_\___ ####

Initializes the database class and loads the data.

```path``` Path to the database.

```logger``` (optional) Logger for database info and error logging.

Returns: ```None```

##### Usage #####

    ...
    database = DatabaseHandler(path=f'{__file__}/../db.csv')
    ...

#### __save__ ####

Writes the current state of the database to file.

Returns: ```None```

##### Usage #####

    ...
    database.save()
    ...

---

## gui.py ##

This file contains functions and classes related to the user interface.

### GUImgr (class) ###

This is the main class of the user interface. The window and its contents are created here.

#### __\_\_init\_\___ ####

```guiQueue``` Multiprocessing queue for writing logs to a gui element.

```db``` Database handler for in-GUI modifications.

```overridequeue``` (optional) Queue for recieving manual gate open events.

This function sets up the gui elements as well as starting the PyQt app.

Returns: ```None```

> Note: Start this function in a separate process / thread to avoid the blocking ```app.exec()``` call.

##### Usage #####

    ...
    logQueue = multiprocessing.Queue()
    override = multiprocessing.Queue()
    database = DatabaseHandler(f'{__file__}/../db.csv')
    gui = GUImgr(guiQueue=logQueue, db=database, overridequeue=override)
    ...

#### __\_addWidgetPair__ ####

Internal function for adding a ```QLabel```ed widget to the layout.

```label``` str. Label text for the given widget.

```widget``` ```QWidget``` which will be added to the layout.

```layout``` Target ```QLayout``` which will contain the element.

Returns: ```None```

##### Usage #####

    ...
    layout = QtWidgets.QVBoxLayout()
    widget = QtWidgets.QWidget()
    self._addWidgetPair(label="Widget", widget=widget, layout=layout)
    ...

#### __modifyWidget__ ####

Modify a ```QLabel```ed widget's value based on the passed value type. ```list``` type / dropdown menu is currently not implemented.

```layout``` A ```QLayout``` with a widget pairs (```QLabel``` and ```QWidget```)

```index``` An ```int``` which indicates the index if the target element to be modified.

```value``` QWidget modified value.

Returns: ```None```

> Note: If the given element does not match the value type (eg. set value of number field as str) an exception will be raised.

##### Usage #####

    ...
    layout = QtWidgets.QVBoxLayout()
    widget = QtWidgets.QLineEdit()
    self._addWidgetPair(label="Widget", widget=widget, layout=layout)
    self.modifyWidget(layout=layout, index=0, value="new LineEdit value")
    ...

#### __getwidgetvalue__ ####

Get widget value from labeled widget pair.

```layout``` Target ```QLayout``` that contains a label / widget pair.

```index``` Index of the label / widget pair.

Returns: ```Any```

##### Usage #####

    ...
    layout = QtWidgets.QVBoxLayout()
    widget = QtWidgets.QLineEdit()
    self._addWidgetPair(label="Widget", widget=widget, layout=layout)
    self.modifyWidget(layout=layout, index=0, value="new LineEdit value")
    value = self.getwidgetvalue(layout=layout, index=0)
    ...

#### __resetcontent__ ####

Reset the current main widget to the default state.

Returns: ```None```

##### Usage #####

    ...
    self.resetcontent()
    ...

#### __moveWindow__ ####

Move window event for custom titlebar. Use through PyQt events.

```event``` PyQt mouse event.

Returns: ```None```

##### Usage #####

    ...
    titlebar = QtWidgets.QWidget()
    titlebar.mousePressEvent = self.moveWindow
    titlebar.mouseMoveEvent = self.moveWindow
    ...

#### __switchtosettings__ ####

Wrapper function to change main widget to the settings screen.

Returns: ```None```

##### Usage #####

    ...
    self.switchtosettings()
    ...

#### __resetsettings__ ####

Reset all the settings input methods to their saved values.

Returns: ```None```

##### Usage #####

    ...
    self.resetsettings()
    ...

#### __applysettings__ ####

Save the modified settings and write them to file.

Returns: ```None```

##### Usage #####

    ...
    self.applysettings()
    ...

#### __applysettingsfunc__ ####

Act on the new settings values. Should be automatically called with ```applysettings```

Returns: ```None```

#### __camdetails__ ####

Switch to settings related to individual cameras.

```camid``` Camera id of which settings should be displayed.

Returns: ```None```

##### Usage #####

    ...
    self.camdetails(camid=0)
    ...

#### __cameramgr__ ####

Set the camera management widget to be active.

Returns: ```None```

##### Usage #####

    ...
    self.cameramgr()
    ...

#### __addcamera__ ####

Add a new camera to the config and set it as the active widget.

Returns: ```None```

##### Usage #####

    ...
    self.addcamera()
    ...

#### __deletecamera__ ####

Delete the camera config and widget givent its ID and shift the ID of the remaining cameras to fill the gap.

Will raise an exception if the given id is either invalid or doesn't exist.

```id``` ID of the to-be deleted camera.

Returns: ```None```

##### Usage #####

    ...
    self.addcamera()
    ...
    self.deletecamera(0)
    ...

#### __dbmgr__ ####

Set the database manager as the current widget.

Returns: ```None```

##### Usage #####

    ...
    self.dbmgr()
    ...

#### __applydbchanges__ ####

Filter and save the database rows.

Returns: ```None```

##### Usage #####

    ...
    self.applydbchanges()
    ...

#### __resetdbchanges__ ####

Reset the LineEdits to the state of the database.

Returns: ```None```

##### Usage #####

    ...
    self.resetdbchanges()
    ...

#### __adddbrow__ ####

Add or modify a row in the database manager.

```*args``` add ```len(args)``` columns with ```args``` as values

```forceidx``` (optional) Force the index of the modified row to be ```forceidx```. Adds a new line if this argument is not specified.

##### Usage #####

Add a line

    ...
    row = ("cell1", "cell2")
    self.adddbrow(*row)
    ...

Modify a line

    ...
    lineindex = 0
    row = ("cell1", "cell2")
    self.adddbrow(*row, forneidx=lineindex)
    ...

#### __manualoverride__ ####

Wrapper function for putting manual gate open commands into a ```multiprocessing.Queue```. Should only be called as a result of user action (eg. press of a button).

Returns: ```None```

##### Usage #####

    ...
    self.manualoverride()
    ...

---

### Camera (class) ###

This class manages its assigned cameras UI space (the camera configuration and live feed).

#### __\_\_init\_\___ ####

Initializes the camera class and makes the UI elements in the camera manager

```config``` Configparser object. Must contain section with name "CAM_{ID}" matching ID specified in argument.

```id``` Integer ID which has a matching section in the config (name = "CAM_{ID}")

```manager``` Parent GUImgr object.

```button``` Assigned button to show this cameras configuration

Returns: ```None```

##### Usage #####

    ...
    self.cameras = []
    for i in range(int(self.config['GENERAL']['num_cameras'])):
        # add a camera for each camera in the config file
        self.cameras.append(Camera(self.config, i, self, self.cambuttons[i]))
        self.camerawidget.addWidget(self.cameras[-1])
    ...

#### __\_addWidgetPair__ ####

Internal function for adding a ```QLabel```ed widget to the layout.

```label``` str. Label text for the given widget.

```widget``` ```QWidget``` which will be added to the layout.

```layout``` Target ```QLayout``` which will contain the element.

Returns: ```None```

##### Usage #####

    ...
    layout = QtWidgets.QVBoxLayout()
    widget = QtWidgets.QWidget()
    self._addWidgetPair(label="Widget", widget=widget, layout=layout)
    ...

#### __get_lower_btns__ ####

Function to create the lower buttons for the camera details page.

Returns: ```QLayout```

##### Usage #####

    ...
    layout = self.get_lower_btns()
    ...

#### __reset__ ####

Reset the options to their saved values.

Returns: ```None```

##### Usage #####

    ...
    self.reset()
    ...

#### __apply__ ####

Save the modified camera settings.

Returns: ```None```

##### Usage #####

    ...
    self.save()
    ...

#### updateId ####

Update the internal camera ID. Used for reassignment of camera IDs during camera deletion.

Returns ```None```

##### Usage #####

    ...
    camera.updateID(camera.id-1)
    ...

---

## manager.py ##

This file contains the main connection of all the other files.

### taskDistributor (class) ###

This class manages the main control functions of the program.

#### __\_\_init\_\___ ####

Initializes and starts the task distributor.

```logger``` A ```logging.Logger``` for program logs, warnings and errors.

```outputQueue``` (optional) Output namespace for worker outputs.

```inputQueue``` (optional) Input namespace for camera frames.

> Note: If both ```inputQueue``` and ```outputQueue``` are left unspecified, a shared namespace is used.

```successCallback``` Callable. Function to be called when a detection returns a positive matching result from the database.

> Note: Certain parts of this function may be later moved to its own ```run``` function for clarity and ease of maintanance.

Returns: ```None```

##### Usage #####

    ...
    logger = mp.get_logger()
    logger.addHandler(logging.StreamHandler(stdout))
    if __name__ == "__main__":
        logger.addHandler(logging.FileHandler(f"{SELFDIR}/log", mode='w'))
        logger.setLevel(logging.INFO)
    ...
    config = ConfigParser()
    config.read(f"{SELFDIR}/config.ini")
    t = taskDistributor(logger=logger)
    ...

#### __distribute__ ####

This function checks the availability of workers and assigns them new tasks. Needs to be called in a loop.

Returns: ```None```

##### Usage #####

    ...
    t = taskDistributor(logger)
    logger.info("Main process startup complete.")
    nextcheck = 0
    try:
        while True:
            ...
            t.distribute()
            ...
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()

> Note: Both ```check``` and ```distribute``` can be called in the same loop as neither of them are a blocking function.

#### __check__ ####

This function checks if the given detection result matches any results in the database.

> Note: The database comparison is implemented with a leniency for additional characters. This is done to decrease the overall response time (time from the first frame of the licence plate to the open signal being sent).

```task``` A custom utils.Task object used for frame and detection result ease of transport.

Returns: ```None```

##### Usage #####

    ...
    t = taskDistributor(logger)
    logger.info("Main process startup complete.")
    nextcheck = 0
    try:
        while True:
            f = t.outQ.__getattr__(f"wkr_id{nextcheck}")
            if not f is None:
                t.check(f)
            else:
                sleep(0.05)
            nextcheck = (nextcheck + 1) % int(config['GENERAL']['NUM_WORKERS'])
            ...
    except KeyboardInterrupt:
        logger.info("Main process shutdown.")
        exit()

> Note: Both ```check``` and ```distribute``` can be called in the same loop as neither of them are a blocking function.

#### __kill__ ####

A helper finction to end all remaining subprocesses for a clean exit.

Returns: ```None```

##### Usage #####

    def distribute(self):

        # closes the program if the user closes the GUI application
        if self.gui.exitcode is not None:
            self.logger.info("GUI closed, exiting")
            self.kill()
            exit(0)
        ...

---

### CameraHandler (class) ###

A handler for management of a camera process.

#### __\_\_init\_\___ ####

Initializes the ```CameraHandler``` class and start the camera process.

```id``` An ID integer. Defaults to -1.

```inputQ``` Input namespace to which the camera will be inserting frames.

```loggerQueue``` (optional) is a ```multiprocessing.Queue``` object to which logs will be written.

> Note: (CRITICAL) The current implementation uses a variable outside its scope to get the current config, this should be changes ASAP.

Returns: ```None```

##### Usage #####

    ...
    self.cameras = [CameraHandler(i, self.inQ, loggerQueue=self.loggerQueue) for i in range(int(config['GENERAL']['NUM_CAMERAS']))]
    ...

#### __kill__ ####

Modularity function. Kills the process for a cleaner exit.

Returns: ```None```

##### Usage #####

    ...
    for cam in self.cameras:
        try:
            cam.kill()
        except:
            pass
    ...

---

### workerHandler (class) ###

Wrapper class for the worker process for easier management.

#### __\_\_init\_\___ ####

Initialize the worker handler and start the worker process.

```id``` An integer ID. Will be used for task output as a namespace attribute.

```output``` Output namespace for worker. The designated ID indicates the variable with data from worker.

```calllback``` Callback on successful return from task. Defaults to lambda*_:None (a useless function).

```loggerQueue``` (optional) is a ```multiprocessing.Queue``` object to which logs will be written.

```model_type``` A string signaling the used model type ("tf" or "lite")

Returns: ```None```

##### Usage #####

    ...
    self.workers = [workerHandler(i, output=self.outQ, loggerQueue=self.loggerQueue, model_type=model_type) for i in range(int(config['GENERAL']['NUM_WORKERS']))]
    ...

#### __assignTask__ ####

Assign a new task to the worker process and set this worker to be busy.

```task``` A ```utils.Task``` where the ```Task.data``` is the given camera frame.

Returns: ```None```

##### Usage #####

    ...
    if not worker.busy:
        worker.assignTask(frame)
    ...

#### __update__ ####

Check if the worker has finished the assigned task, if so, set the workers busy attribute to false and output the task. Should be called before any other function.

##### Usage #####

    ...
    for worker in self.workers:
        worker.update()
        ...
    ...

#### __kill__ ####

A function to kill the worker process for a cleaner exit.

##### Usage #####

    ...
    for worker in self.workers:
        try:
            worker.kill()
        except:
            pass
    ...

---

## output.py ##

This file contains functions related to the timing and triggering of output on successful detections.

### Outputmgr (class) ###

Class for timing events based on detection trigger, not used by default - use interrupts instead.

#### __\_\_init\_\___ ####

Initialize the class and variables.

Returns: ```None```

##### Usage #####

    ...
    out = Outputmgr()
    ...

#### __trigger__ ####

Event trigger which changes the internal state based on the current state and time since last change.

Returns: ```None```

##### Usage #####

    ...
    while True:
        try:
            time.sleep(1)
        except:
            out.trigger()
    ...

#### __check\_loop__ ####

A function with a while loop that triggers attached events when the event occurs.

Returns: ```None```

> Note: This is a No-Return function, call as a thread target.

##### Usage #####

    ...
    thread = threading.Thread(target=out.check_loop)
    thread.start()
    ...

#### __main\_enter__ ####

Event handler for when the state changes from ("idle" or "exit") to "enter".

Returns: ```None```

##### Usage #####

    ...
    if self.state == 'enter':
        self.main_enter()
    ...

#### __main\_trigger__ ####

Event handler for when the state changes from "enter" to "trigger".

Returns: ```None```

##### Usage #####

    ...
    if self.state == 'trigger':
        self.main_trigger()
    ...

#### __main\_exit__ ####

Event handler for when the state changes from "trigger" to "exit".

Returns: ```None```

##### Usage ######

    ...
    if self.state == 'exit':
        self.main_exit()
    ...

#### __main\_idle__ ####

Event handler for when the state changes from "exit" to "idle".

Returns: ```None```

##### Usage #####

    ...
    if self.state == 'idle':
        self.main_idle()
    ...

#### __addeventlistener__ ####

Add a function to call when an event occurs.

##### Usage #####

    ...
    out = Outputmgr()
    out.addeventlistener(ENTER_EVENT, lambda: print("enter"))
    ...

---

### Outputhelper (class) ###

Helper class for easier management of pin writing and event triggering. Class attributes are pin definitions.

#### __\_\_init\_\___ ####

Initialize the class, set all the pins to the correct modes and ensure they are in the propper state.

```gpio``` A GPIO manager for read/write/interrupts from pins.

Returns: ```None```

##### Usage #####

    ...
    pins = [output.OPiTools.Pin(**pin) for pin in output.OPiTools.PINLIST]
    gpio = output.OPiTools.GPIOmgr(pins)
    outhelper = output.Outputhelper(gpio)
    ...

#### __enter__ ####

Enter event trigger function.

```overridetrigger``` (optional) Trigger the ```gate_open``` function and change the state. Interrupt utility variable.

Returns: ```None```

##### Usage #####

    ...
    pins = [output.OPiTools.Pin(**pin) for pin in output.OPiTools.PINLIST]
    gpio = output.OPiTools.GPIOmgr(pins)
    outhelper = output.Outputhelper(gpio)
    t = taskDistributor(logger, successCallback=lambda:helperfunc(outhelper.enter))
    ...

#### __interrupt\_enter__ ####

Utility function when calling enter from an interrupt.

Returns: ```None```

##### Usage #####

    ...
    gpio.attachinterrupt(0, gpio.phys2wPi(self.INTERRUPT), self.interrupt_enter, OPiTools.FALLING)
    ...

#### __trigger\_enter__ ####

Utility function for switching states. Called 10s after ```enter``` by default.

Returns: ```None```

##### Usage #####

    ...
    self.trigger_enter()
    ...

#### __trigger\_exit__ ####

Utility function for switching states. Called 10s after ```trigger_enter``` by default.

Returns: ```None```

##### Usage #####

    ...
    self.trigger_exit()
    ...

#### __exit__ ####

Utility function for switching states. Called 10s after ```trigger_exit``` by default.

Returns: ```None```

##### Usage #####

    ...
    self.exit()
    ...

#### __gate\_open__ ####

Event trigger function which opens the gate. In the provided code, the gate opens with a 1s high pulse.

##### Usage #####

    ...
    self.gate_open()
    ...

#### __gate\_close__ ####

Event fired when the gate closes. Reset variable to allow subsequent triggers.

##### Usage #####

    ...
    self.gate_close()
    ...

---

## utils.py ##

This file contains various different utilities which don't exactly fit into other files.

### Task (class, dataclass) ###

A Utility task for ease of transport of data.

```id``` :int = Camera ID which supplied this frame.

```data``` :Any = Data to be wrapped (either camera frame or detection info)

#### Usage ####

    ...
    setattr(self._output, f"cam_id{self.cfg['id']}", utils.Task(self.cfg['id'], frame))
    ...

---

### LoggerOutput (class, logging.handlers.QueueHandler) ###

Helper class which writes appropriately formatted loggs to a ```QTextEdit element```

#### __\_\_init\_\___ ####

Initialize the class and setup variables.

```queue``` A ```multiprocessing.Queue``` object to which logs will be written.

```*args``` Consumes the rest of positional arguments, the rest are keyword only.

```reciever_meta``` A QMetaObject for interraction outside the current thread / process.

```reciever``` QTextEdit for log output. The recieved logs from ```queue``` are written here.

```formatter``` A logging.Formatter

```**kwargs``` Consumes the rest of the kwargs.

> Note: ```*args``` and ```**kwargs``` are passed to the parent class (```logging.handlers.QueueHandler```)

Returns: ```None```

##### Usage #####

    ...
    self.loggerout = QtWidgets.QTextEdit()
    self.loggerout.setObjectName('log')
    self.loggerout.setReadOnly(True)
    self.loggerout.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
    self.loggerout.setWordWrapMode(QtGui.QTextOption.WrapMode.NoWrap)
    layout.addWidget(self.loggerout)

    # add a handler for the logger to write to the text box
    if guiQueue is not None:
        meta = self.loggerout.metaObject()
            handler = utils.LoggerOutput(guiQueue, reciever_meta=meta, reciever=self.loggerout, formatter=loggingFormatter("%(asctime)s | %(levelname)-8s | %(message)s"))
        listener = QueueListener(guiQueue, handler)
        listener.start()
        self.logger.addHandler(QueueHandler(guiQueue))
    ...

#### emit ####

Override function for emitting logs.

---

### Detector (class) ###

A wrapper class for the tensorflow LP detection model.

#### __\_\_init\_\___ ####

Initialize the class, load the model and compile it.

```path``` Path to the saved model.

Returns: ```None```

##### Usage #####

    ...
    if model_type == 'tf':
        self.logger.info("Using TensorFlow model")
        self.detector = utils.Detector(f"{pth}/saved_model")
    ...

#### __\_\_call\_\___ ####

Detect licence plates in a provided image.

```img``` Provided image in (height, width, 3) shaped array. Channel order is R-G-B.

Returns: ```tensor```

##### Usage #####

    ...
    if task.data is not None:
        detections = self.detector(task.data)
    ...

---

### LiteDetector (class, Detector) ###

A wrapper class for the tensorflow LP detection model. Uses the tf.lite model instead.

#### __\_\_init\_\___ ####

Initialize the class, load the model and allocate tensors.

```path``` Path to the saved model.

Returns: ```None```

##### Usage #####

    ...
    if model_type == 'lite':
        self.logger.info("Using TensorFlow Lite model")
        self.detector = utils.LiteDetector(f"{pth}/saved_model")
    ...

#### __\_\_call\_\___ ####

Detect licence plates in a provided image.

```img``` Provided image in (height, width, 3) shaped array. Channel order is R-G-B.

Returns: ```dict```

##### Usage #####

    ...
    if task.data is not None:
        detections = self.detector(task.data)
    ...

---

### FeedManager ###

A camera live feed manager. Controlled from the UI.

> Note: This function should be rewritten in the near future as openning a new connection is wasteful. Should use the namespace for getting frames - this would also eliminate the need for an entire config argument and the function would only need the camera ID.

#### __\_\_init\_\___ ####

Initialize the class and variables.

```logger``` A ```logging.Logger``` or ```multiprocessing.Logger```

Returns: ```None```

##### Usage #####

    ...
    self.feedmgr = utils.FeedManager(self.logger)
    ...

#### __start__ ####

Start the camera live feed in a separate thread. Different behaviour for windows / linux.

```camcfg``` A dict containing the configuration of the camera.

Returns: ```None```

##### Usage #####

    ...
    cfg = {"protocol":"rtsp", "port":554, "login":"admin", "password":"admin", "ip":"127.0.0.1", "id":self.id}
    cfg |= {k:v for k, v in self.config.items(f'CAM_{self.id}')}
    btn = QtWidgets.QPushButton("Live feed", clicked=lambda: self.manager.feedmgr.start(cfg) if self.manager.feedmgr.thread is None else self.manager.feedmgr.stop())
    ...

#### __stop__ ####

Stop the current camera feed

Returns: ```None```

##### Usage #####

    ...
    cfg = {"protocol":"rtsp", "port":554, "login":"admin", "password":"admin", "ip":"127.0.0.1", "id":self.id}
    cfg |= {k:v for k, v in self.config.items(f'CAM_{self.id}')}
    btn = QtWidgets.QPushButton("Live feed", clicked=lambda: self.manager.feedmgr.start(cfg) if self.manager.feedmgr.thread is None else self.manager.feedmgr.stop())
    ...

#### __livefeed\_thread__ ####

Opens a connection to the camera and show the feed using ```cv2.imshow```.

Returns: ```None```

> Note: This is a No-Return function, call as a thread target.

##### Usage #####

    ...
    self.cam = camcfg
    self.stop_feed = False
    if 'linux' in sys.platform:
        self.thread = Thread(target=self.livefeed_thread_linux, args=(camcfg,), daemon=True)
    else:
        self.thread = Thread(target=self.livefeed_thread, args=(camcfg,), daemon=True)
    self.logger.info(f'Camera {camcfg["id"]} feed started')
    self.thread.start()
    ...

#### __livefeed\_thread\_linux__ ####

Opens a connection to the camera and show the feed using a ```QWidget```.

Returns: ```None```

> Note: This is a No-Return function, call as a thread target.

##### Usage #####

    ...
    self.cam = camcfg
    self.stop_feed = False
    if 'linux' in sys.platform:
        self.thread = Thread(target=self.livefeed_thread_linux, args=(camcfg,), daemon=True)
    else:
        self.thread = Thread(target=self.livefeed_thread, args=(camcfg,), daemon=True)
    self.logger.info(f'Camera {camcfg["id"]} feed started')
    self.thread.start()
    ...

---

### __crop\_image__ (function) ###

Crop the provided image to the bounding box of the highest confidence detection if it is above the threshold.

```img``` Supplied image to be cropped. Bounding box will be pulled from the ```detections``` argument.

```detections``` Tensor with licence plate detections.

```threshold``` A ```float``` between 0 and 1. Detections with lower confidence will be discarded. If no detections remain after the filter, the function will return ```None```

Returns: ```list``` or ```None```

#### Usage ####

    ...
    detections = self.detector(task.data)
    img = utils.crop_image(task.data, detections, threshold=0.2)
    ...

---

### __joinpredictions__ (function) ###

Join the provided text predictions into one. 

> Note: This is done to prevent split predictions not passing the check (eg. "XYZ1234" may be detected as "XYZ" and "1234" under certain conditions).

#### Usage ####

    ...
    if len(task.data) == 0: return
    if len(task.data) >= 2:
        joinedtask = utils.joinpredictions(task)
    else:
        joinedtask = utils.Task(task.id, task.data[0])
    ...

---

## worker.py ##

This file contains the main licence plate detection and recognition part of the program.

### Worker (class) ###

This class manages the connection to the mamager. The detection and recognition of licence plates is also located inside the main loop.

#### __\_\_init\_\___ ####

Initialize the class and load the detection model.

```qrecv``` A ```multiprocessing.Queue``` for inbound communication.

```qsend``` A ```multiprocessing.Queue``` for inbound communication.

```loggerQueue``` (optional) is a ```multiprocessing.Queue``` object to which logs will be written.

```*_``` This is an argument to consume positional arguments. The following args are keyword only.

```model_type``` The type of tensorflow model to use as a string ("tf" or "lite"). Lite models are only appropriate in certain situations (eg. a single board computer). Defaults to ```"lite"```

```model_pth``` Path to the saved model. Defaults to the worker.py directory /saved_model

```autostart``` Automatically call ```self.run``` and start the main loop. Defaults to ```False```.

Returns: ```None```

##### Usage #####

    ...
    self._Qsend, self._Qrecv = mp.Queue(), mp.Queue()
    # start the worker process
    self._process = mp.Process(target=worker.Worker, args=(self._Qsend, self._Qrecv, loggerQueue), kwargs={"autostart":True, "model_type":model_type}, name=f"Worker_{id}_process")
    self._process.start()
    ...

#### __run__ ####

Main detection / recognition loop of the program.

Returns: ```None```

> Note: This is a No-Return function, call as a thread or process target.

##### Usage #####

    ...
    if autostart: self.run()
    ...

---

### get\_text (function) ###

Get the text from a cropped image using PaddleOCR

```img``` Image to have text extracted from.

```ocr``` The ocr class to use. Defaults to one created on module import.

#### Usage ####

    ...
    if img is not None and len(img) > 0:
        text = get_text(img)
    ...
