import os, socket
import xml.etree.cElementTree as ET
from .Variables import playonlinux_rep
from subprocess import Popen, PIPE

winepack_home = '%s/winepack' % playonlinux_rep
os.environ["WINEPACK_HOME"] = winepack_home

LOADED_CATEGORIES = []
LOADED_APPLICATIONS = []

class Category(object):

    name = ''
    location = ''
    icon_path = ''

    applications = []

    def __init__(self, dirname):
        self.name = os.path.basename(dirname)
        self.location = dirname
        self.icon_path = '%s/icon.png' % self.location
    def __eq__(self, other):
        return self.name == other.name
    def __ne__(self, other):
        return not self.__eq__(other)
    def add_application(self, application):
        self.applications.append(application)
        application.category = self
        application.category_index = len(self.applications) - 1

class Application(object):

    appnme = ''
    location = ''
    icon_path = ''
    meta_path = ''

    includes = {
        'testing': 0,
        'nocd': 0,
        'free': 0,
    }

    category = None
    category_index = -1

    def __init__(self, dirname):
        self.appname = os.path.basename(dirname)
        self.location = dirname
        self.icon_path = '%s/icon.png' % self.location
        self.meta_path = '%s/metadata.xml' % self.location
    def __cmp__(self, other):
        if self.appname < other.appname:
            return -1;
        elif self.appname > other.appname:
            return 1
        else:
            return 0
    def __eq__(self, other):
        return self.appname == other.appname
    def __ne__(self, other):
        return not self.__eq__(other)
    def load(self):
        try:
            tree = ET.parse(self.meta_path)
            root = tree.getroot()
            includes = root.findall('include')
            for i in includes:
                a = i.attrib.get('name', '')
                if a in self.includes:
                    val = int(i.text)
                    self.includes[a] = val
            icon = root.find('icon')
            if icon is not None and 'path' in icon.attrib:
                self.icon_path = icon.attrib['path']
            appname = root.find('appname')
            if appname is not None:
                self.appname = appname.text
        except IOError:
            pass
        return

def get_toplevel_subdirs(directory):
    find = Popen(['find', directory, '-maxdepth', '1', '-mindepth', '1', '-type', 'd'], stdout=PIPE)
    stdout, stderr = find.communicate()
    subdirs = stdout.split('\n')[:-1]
    return subdirs

def load_categories():
    category_dirnames = get_toplevel_subdirs(winepack_home)
    for dirname in category_dirnames:
        c = Category(dirname)
        if c not in LOADED_CATEGORIES:
            LOADED_CATEGORIES.append(c)

def load_applications(category):
    apps_location = '%s/applications' % category.location
    application_dirnames = get_toplevel_subdirs(apps_location)
    for dirname in application_dirnames:
        a = Application(dirname)
        a.load()
        if a not in LOADED_APPLICATIONS:
            category.add_application(a)
            LOADED_APPLICATIONS.append(a)

def call_POL(method, *args):
    '''
    method to connect to POL GUI server and issue calls to POL window methods
    This method wraps an IPC mechanism which communicates with mainwindow.py.
    It and methods that call it thus cannot be called within the mainwindow.py thread
    '''
    host = os.environ.get("POL_HOST")
    if host is None:
        host = '127.0.0.1'
    cookie = os.environ["POL_COOKIE"]
    port = int(os.environ["POL_PORT"])
    chunksize = 16
    pid = os.getpid()
    connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    dest = (host, port)
    call = '%s\t%s\t%s' % (cookie, method, pid)
    for arg in args:
        call += '\t%s' % arg
    call += '\n'

    try:
        connection.connect(dest)

        connection.sendall(call)

        response = ''
        recv_chunksize = chunksize
        while recv_chunksize >= chunksize:
            chunk = connection.recv(chunksize)
            response += chunk
            recv_chunksize = len(chunk)
    finally:
        connection.close()

    return response

