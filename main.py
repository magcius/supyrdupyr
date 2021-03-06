
from optparse import OptionParser
import os
import os.path
import sys

class configuration(type(sys)):
    __file__ = __file__
    def __init__(self, options, args):
        for name, value in options.__dict__.iteritems():
            setattr(self, name, value)
        self.args = args

def run_app_file(filename, configuration):
    sys.modules['configuration'] = configuration
    execfile(filename, dict(__name__="__supyrdupyr__", __builtins__=__builtins__))

def run_app(appname, configuration):
    if os.path.isdir(appname) and os.path.isfile(os.path.join(appname, "app.py")):
        sys.path.append(os.getcwd())
        os.chdir(appname)
        run_app_file("app.py", configuration)
    elif os.path.isfile(appname+".py"):
        run_app_file(appname+".py", configuration)
    else:
        print 'The application "%s" does not exist.' % (appname,)
        return

def main():
    default_app = None
    
    try:
        default_app = open("default_app", "r").read().strip()
    except IOError:
        pass
    

    parser = OptionParser()
    parser.add_option("-g", "--game", dest="game", help="name of the game to run")
    parser.add_option("-w", "--window", dest="fullscreen", action="store_false", default=True, help="run the game in a window instead of in fullscreen")

    options, args = parser.parse_args()

    config = configuration(options, args)
    
    if options.game:
        return run_app(options.game, config)
    elif default_app:
        return run_app(default_app, config)

    print "You did not enter a game to run, nor is there a default_app file to specify one"

if __name__ == "__main__":
    main()
