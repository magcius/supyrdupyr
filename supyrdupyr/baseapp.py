
import sys
import os

import ogre.physics.bullet
from ogre.io import OIS
import ogre.renderer.OGRE as ogre
from supyrdupyr.messenger import Messenger

class MessengerFrameListener(ogre.FrameListener, ogre.WindowEventListener, OIS.MouseListener, OIS.KeyListener):

    buffered = True
    
    def __init__(self, app, win, cam, scman):
        ogre.FrameListener.__init__(self)
        ogre.WindowEventListener.__init__(self)
        OIS.MouseListener.__init__(self)
        OIS.KeyListener.__init__(self)
        
        self.app, self.renderWindow, self.camera, self.sceneManager = app, win, cam, scman

        self.inputManager = None
        self.keyboardInput, self.mouseInput, self.joyInput = None, None, None

        self.setupInput()
    
    def mouseMoved(self, evt):
        self.app.messenger.send("mouse-moved", self, evt)
    
    def mousePressed(self, evt, id):
        self.app.messenger.send("mouse-" + id.name[3:].lower(), self, evt)
    
    def mouseReleased(self, evt, id):
        self.app.messenger.send("mouse-" + id.name[3:].lower() + "-up", self, evt)

    def keyPressed(self, evt):
        self.app.messenger.send(evt.key.name[3:].lower(), self, evt)

    def keyReleased(self, evt):
        self.app.messenger.send(evt.key.name[3:].lower() + "-up", self, evt)
        
    def frameRenderingQueued(self, evt):
        if self.renderWindow.isClosed():
            return False

        self.keyboardInput.capture()
        self.mouseInput.capture()
        if self.joyInput:
            self.joyInput.capture()

        return True

    def windowResized(self, rw):
        width, height, depth, left, top = rw.getMetrics(0, 0, 0, 0, 0)
        state = self.mouseInput.getMouseState()
        state.width, state.height = width, height
        
    def setupInput(self):
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

class BaseApplication(object):

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
        path = os.path.join(self.configDir, filename + ".cfg")

        if os.path.exists(path):
            return path

        path += "." + os.name

        if os.path.exists(path):
            return path

        self.exit("Unable to locate a suitable %s.cfg file." % (filename,))

    def exit(self, message):
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
        
        self.root = ogre.Root(self.getConfigFilePath("plugins"), self.getConfigFilePath("ogre"))
        self.root.setFrameSmoothingPeriod(self.frameSmoothingPeriod)
        
        self.setupResources()
        self.configure()

        self.messenger = self.createMessenger()

        self.createSceneManagers()
        self.createWorld()
        self.createCameras()
        self.createViewports()

        ogre.TextureManager.getSingleton().setDefaultNumMipmaps(self.defaultNumMipmaps)

        self.createResourceListener()
        self.loadResources()

        self.createScene()
        self.createFrameListeners()

        self.createMessengerListeners()

        if self.globals:
            self.setupGlobals()
    
    def setupGlobals(self):
        import __builtin__  as builtins
        for attrname in self.globals:
            setattr(builtins, attrname, getattr(self, attrname))

    def setupResources(self):
        config = ogre.ConfigFile()
        config.load(self.getConfigFilePath("resources"))

        section = config.getSectionIterator()
        while section.hasMoreElements():
            sectionKey   = section.peekNextKey()
            sectionItems = section.getNext()
            for item in sectionItems:
                ogre.ResourceGroupManager.getSingleton().addResourceLocation(item.value, item.key, sectionKey)

    def configure(self):
        canceled = False
        if self.useSettingsDialog:
            canceled = not self.root.showConfigDialog()
        else:
            canceled = not self.root.restoreConfig()
        
        if canceled:
            sys.exit("Exiting")

        self.renderWindow = self.root.initialise(True, self.windowTitle)
    
    def createMessenger(self):
        return Messenger(self)

    def createSceneManagers(self):
        self.sceneManager = self.root.createSceneManager(ogre.ST_GENERIC, "SceneManager")

    def createWorld(self):
        pass
    
    def createCameras(self):
        self.camera = self.sceneManager.createCamera("MainCamera")

    def createViewports(self):
        try:
            self.viewport = self.renderWindow.addViewport(self.camera.getRealCamera())
        except AttributeError:
            self.viewport = self.renderWindow.addViewport(self.camera)

        self.viewport.BackgroundColor = ogre.ColourValue(0, 0, 0)

    def createResourceListener(self):
        pass

    def loadResources(self):
        ogre.ResourceGroupManager.getSingleton().initialiseAllResourceGroups()
    
    def createScene(self):
        self.sceneManager.setAmbientLight((0.5, 0.5, 0.5))
        self.sceneManager.setSkyDome(True, "CloudySky", 5, 8)

    def createRenderWindows(self):
        self.renderWindow = self.root.initialise(True, self.windowTitle)
        
    def createFrameListeners(self):
        self.frameListener = MessengerFrameListener(self, self.renderWindow, self.camera, self.sceneManager)
        self.root.addFrameListener(self.frameListener)

    def createMessengerListeners(self):
        pass
