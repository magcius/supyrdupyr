
import sys
import os

import ogre.physics.bullet
from ogre.io import OIS
import ogre.renderer.OGRE as ogre
from supyrdupyr.messenger import Messenger

class BaseApplication(object):

    """
    Our base framework application.
    """
    
    windowTitle          = "SupyrDupyr BaseApplication"
    configDir            = "config"
    frameSmoothingPeriod = 5.0
    defaultNumMipmaps    = 5
    debugLogging         = False
    useSettingsDialog    = True
    activatePsyco        = False
    globals              = None
    # globals              = ['app', 'messenger', 'sceneManager', 'renderWindow', 'root', 'camera']

    def __init__(self):
        self.frameListener, self.root, self.camera = None, None, None
        self.renderWindow, self.viewport, self.sceneManager = None, None, None
        self.messenger = None
    
    def getConfigFilePath(self, filename):
        """
        Get a .cfg file with an optional .(posix|mac|win) extension, if it exists.
        """
        path = os.path.join(self.configDir, filename + ".cfg")

        if os.path.exists(path):
            return path

        path += "." + os.name

        if os.path.exists(path):
            return path

        self.exit("Unable to locate a suitable %s.cfg file." % (filename,))

    def exit(self, message):
        """
        Exit with a message
        """
        sys.exit("Fatal Error: %s" % (message,))
    
    def go(self):
        self.setup()
        
        if self.activatePsyco:
            try:
                import psyco
                psyco.full()
            except ImportError:
                pass
        
        self.root.startRendering()
        
    def setup(self):
        """
        Set up the game.
        """
        self.root = ogre.Root(self.getConfigFilePath("plugins"), self.getConfigFilePath("ogre"))
        self.root.setFrameSmoothingPeriod(self.frameSmoothingPeriod)
        
        self.setupResources()
        self.configure()

        self.messenger = self.createMessenger()

        self.createSceneManagers()
        self.createCameras()
        self.createViewports()

        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(self.defaultNumMipmaps)

        self.createResourceListener()
        self.loadResources()

        self.createScene()
        self.createWorld()
        self.createFrameListeners()

        self.createMessengerListeners()

        if self.globals:
            self.setupGlobals()
    
    def setupGlobals(self):
        """
        Add an interface like Panda3D where everything is global, meaning
        it's stuffed in __builtin__
        
        Uses self.globals to determine which globals should be added.
        """
        import __builtin__  as builtins
        for attrname in self.globals:
            setattr(builtins, attrname, getattr(self, attrname))

    def setupResources(self):
        """
        Read the resources.cfg file.
        """
        config = ogre.ConfigFile()
        config.load(self.getConfigFilePath("resources"))

        section = config.getSectionIterator()
        while section.hasMoreElements():
            sectionKey   = section.peekNextKey()
            sectionItems = section.getNext()
            for item in sectionItems:
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(item.value, item.key, sectionKey)

    def configure(self):
        """
        Show the configuration dialog, if wanted.
        """
        canceled = False
        if self.useSettingsDialog:
            canceled = not self.root.showConfigDialog()
        else:
            canceled = not self.root.restoreConfig()
        
        if canceled:
            sys.exit("Exiting")

        self.renderWindow = self.root.initialise(True, self.windowTitle)
    
    def createMessenger(self):
        """
        Should return a suitable Messenger instance.
        """
        return Messenger(self)

    def createSceneManagers(self):
        """
        Create our sceneManager(s).
        """
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "SceneManager")

    def createWorld(self):
        """
        Create our world.
        """
        pass
    
    def createCameras(self):
        """
        Create our camera(s).
        """
        self.camera = self.sceneManager.createCamera("MainCamera")

    def createViewports(self):
        """
        Create our viewport(s).
        """
        try:
            self.viewport = self.renderWindow.addViewport(self.camera.getRealCamera())
        except AttributeError:
            self.viewport = self.renderWindow.addViewport(self.camera)

        self.viewport.BackgroundColor = ogre.ColourValue(0, 0, 0)

    def createResourceListener(self):
        """
        Create our resource listener (optional).
        """
        pass

    def loadResources(self):
        """
        Load our resources.
        """
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()
    
    def createScene(self):
        """
        Create our default scene.
        """
        self.sceneManager.setAmbientLight((0.5, 0.5, 0.5))
        self.sceneManager.setSkyDome(True, "CloudySky", 5, 8)

    def createRenderWindows(self):
        """
        Create our render window by initializing the Root.
        """
        self.renderWindow = self.root.initialise(True, self.windowTitle)
        
    def createFrameListeners(self):
        """
        Create our default frame listeners.
        """
        self.frameListener = MessengerFrameListener(self, self.renderWindow, self.camera, self.sceneManager)
        self.root.addFrameListener(self.frameListener)
        
    def createMessengerListeners(self):
        """
        And create our messenger listeners.
        """
        pass

class MessengerFrameListener(ogre.FrameListener, ogre.WindowEventListener, OIS.MouseListener, OIS.KeyListener):

    """
    A FrameListener that uses the app's messenger instance to provide
    global events, in the style of Panda3D.
    """
    
    buffered = True

    KEY_REPLACE_MAP = {"lmenu": "lwin", "rmenu": "rwin", "apps": "menu"}
    
    def __init__(self, app, win, cam, scman):
        # super doesn't work for some reason.
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        OIS.MouseListener.__init__(self)
        OIS.KeyListener.__init__(self)
        
        self.app, self.renderWindow, self.camera, self.sceneManager = app, win, cam, scman

        self.inputManager = None
        self.keyboardInput, self.mouseInput, self.joyInput = None, None, None

        self.setupInput()
    
    def mouseMoved(self, evt):
        """
        Emits a "mouse-moved" event when the mouse is pressed.
        This also happens on mouse scroll, using the "Z" component of the mouse state.
        """
        self.app.messenger.send("mouse-moved", [self, evt])
    
    def mousePressed(self, evt, id):
        """
        Emits "mouse-left", "mouse-right", etc.
        """
        self.app.messenger.send("mouse-" + id.name[3:].lower(), [self, evt])
    
    def mouseReleased(self, evt, id):
        """
        Emits "mouse-left-up", "mouse-right-up", etc.
        """
        self.app.messenger.send("mouse-" + id.name[3:].lower() + "-up", [self, evt])

    def keyPressed(self, evt):
        """
        Emits key events when a key is pressed.
        """
        key = evt.key.name[3:].lower()
        self.app.messenger.send(self.KEY_REPLACE_MAP.get(key, key), [self, evt])

    def keyReleased(self, evt):
        """
        Emits key events when a key is released.
        """
        key = evt.key.name[3:].lower()
        self.app.messenger.send(self.KEY_REPLACE_MAP.get(key, key) + "-up", [self, evt])
        
    def frameRenderingQueued(self, evt):
        """
        Called when the frame is rendered.
        Must return True for the window to stay open.
        """
        if self.renderWindow.isClosed():
            return False

        self.keyboardInput.capture()
        self.mouseInput.capture()
        if self.joyInput:
            self.joyInput.capture()

        return True

    def windowResized(self, rw):
        """
        Called when the window is resized.
        """
        width, height, depth, left, top = rw.getMetrics(0, 0, 0, 0, 0)
        state = self.mouseInput.getMouseState()
        state.width, state.height = width, height
        
    def setupInput(self):
        """
        Sets up our input.
        """
        if sys.maxint == 2**63 - 1:
            windowHnd = self.renderWindow.getCustomAttributeUnsignedLong("WINDOW")
        else:
            windowHnd = self.renderWindow.getCustomAttributeInt("WINDOW")
        
        pl = ogre.SettingsMultiMap()
        windowHndStr = str(windowHnd)
        pl.insert("WINDOW", windowHndStr)
        
        self.inputManager = OIS.InputManager.createInputSystem(pl)
        self.keyboardInput = self.inputManager.createInputObjectKeyboard(OIS.OISKeyboard, self.buffered)
        self.mouseInput = self.inputManager.createInputObjectMouse(OIS.OISMouse, self.buffered)
        try:
            self.joyInput = self.inputManager.createInputObjectJoyStick(OIS.OISJoyStick, self.buffered)
        except:
            pass
        
        self.windowResized(self.renderWindow)
        
        ogre.WindowEventUtilities.addWindowEventListener(self.renderWindow, self)
        
        self.mouseInput.setEventCallback(self)
        self.keyboardInput.setEventCallback(self)
