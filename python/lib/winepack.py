import os, socket
from .Variables import playonlinux_rep

winepack_home = '%s/winepack' % playonlinux_rep
os.environ["WINEPACK_HOME"] = winepack_home


class Category(object):

    name = ''
    location = ''
    meta_path = ''
    icon_path = ''

    iid = -1
    applications = []

    def __init__(self, dirname):
        self.name = os.path.basename(dirname)
        self.location = dirname
        self.meta_path = '%s/metadata.xml' % self.location
        self.icon_path = '%s/icon.png' % self.location
    def load(self, name):
        try:
            input = open(self.meta_path, 'r')
        except IOError:
            return
    def add_application(self, application):
        self.applications.append(application)
        application.category = self
        application.category_index = len(self.applications) - 1

class Application(object):

    appnme = ''
    meta_path = ''

    testing = -1
    nocd = -1
    free = -1
    category = None
    category_index = -1

    def __init__(self, meta_file_path):
        self.meta_path = meta_file_path
        self.appname = os.path.basename(self.meta_path).rsplit('.', -1)
    def load(self):
        try:
            input = open(self.meta_path, 'r')
        except IOError:
            return

def winepack_call_POL(method, *args):
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

