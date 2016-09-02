import httplib
import socket
import xmlrpclib


class RPCError(Exception):

    def __init__(self, arg, errno):
        if errno == 2:
            self.message = 'Error when attempting to open "{0}".'.format(arg)
        elif errno == 13:
            self.message = 'Permission denied when attempting to '
            'open "{0}".'.format(arg)
        else:
            self.message = 'Unknown error when attempting to open '
            '"{0}".'.format(arg)
        self.arg = arg
        self.errno = errno


class UnixStreamHTTPConnection(httplib.HTTPConnection):

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.host)
        except socket.error as e:
            raise RPCError(self.host, e.errno)


class UnixStreamTransport(xmlrpclib.Transport, object):

    def __init__(self, socket_path):
        self.socket_path = socket_path
        super(UnixStreamTransport, self).__init__()

    def make_connection(self, host):
        return UnixStreamHTTPConnection(self.socket_path)


class RPC(object):

    def __init__(self):
        transport = UnixStreamTransport('/var/run/supervisor.sock')
        self.xmlrpc = xmlrpclib.Server('http://arg_unused',
                                       transport=transport)
        # print(self.xmlrpc.supervisor.getState())
        # print(self.xmlrpc.system.listMethods())

    def stopProcesses(self, args):
        ret_val = []
        if len(args) == 1 and '*' in args:
            try:
                self.xmlrpc.supervisor.stopAllProcesses()
                ret_val.append({'result': 'success', 'cmd': 'stop',
                                'process': '*',
                                'details': 'Stopped all processes'})
            except Exception as e:
                print('Exception stopping all processes')
                ret_val.append({'result': 'error', 'cmd': 'stop',
                                'process': '*', 'details': str(e)})
        else:
            for arg in args:
                try:
                    self.xmlrpc.supervisor.stopProcess(arg)
                    ret_val.append({'result': 'success', 'cmd': 'stop',
                                    'process': arg,
                                    'details': 'Stopped process {0}'
                                    .format(arg)})
                except Exception as e:
                    print('Exception stopping process %s: %s' % (arg, e))
                    ret_val.append({'result': 'error', 'cmd': 'stop',
                                    'process': arg, 'details': str(e)})
        return ret_val

    def startProcesses(self, args):
        ret_val = []
        if len(args) == 1 and '*' in args:
            try:
                self.xmlrpc.supervisor.startAllProcesses()
                ret_val.append({'result': 'success', 'cmd': 'start',
                                'process': '*',
                                'details': 'Started all processes'})
            except Exception as e:
                print('Exception starting all processes')
                ret_val.append({'result': 'error', 'cmd': 'start',
                                'process': '*', 'details': str(e)})
        else:
            for arg in args:
                try:
                    self.xmlrpc.supervisor.startProcess(arg)
                    ret_val.append({'result': 'success', 'cmd': 'start',
                                    'process': arg,
                                    'details': 'Started process {0}'
                                    .format(arg)})
                except Exception as e:
                    print('Exception starting process %s: %s' % (arg, e))
                    ret_val.append({'result': 'error', 'cmd': 'start',
                                    'process': arg, 'details': str(e)})
        return ret_val

    def restartProcesses(self, args):
        return self.stopProcesses(args).extend(self.startProcesses(args))
