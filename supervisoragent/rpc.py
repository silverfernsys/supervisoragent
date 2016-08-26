import httplib, socket, xmlrpclib

class UnixStreamHTTPConnection(httplib.HTTPConnection):
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.host)
        except socket.error as e:
            sys.exit('Supervisor not running.')


class UnixStreamTransport(xmlrpclib.Transport, object):
    def __init__(self, socket_path):
        self.socket_path = socket_path
        super(UnixStreamTransport, self).__init__()

    def make_connection(self, host):
        return UnixStreamHTTPConnection(self.socket_path)


class RPC(object):
    def __init__(self):
        self.xmlrpc = xmlrpclib.Server('http://arg_unused', transport=UnixStreamTransport('/var/run/supervisor.sock'))
        # print(self.xmlrpc.supervisor.getState())
        # print(self.xmlrpc.system.listMethods())
        
    def stopProcesses(self, args):
        ret_val = []
        if len(args) == 1 and '*' in args:
            try:
                self.xmlrpc.supervisor.stopAllProcesses()
                ret_val.append({'result': 'success', 'cmd': 'stop', 'process': '*', 'details': 'Stopped all processes'})
            except Exception as e:
                print('Exception stopping all processes')
                ret_val.append({'result': 'error', 'cmd': 'stop', 'process': '*', 'details': str(e)})
        else:
            for arg in args:
                try:
                    self.xmlrpc.supervisor.stopProcess(arg)
                    ret_val.append({'result': 'success', 'cmd': 'stop', 'process': arg, 'details': 'Stopped process {0}'.format(arg)})
                except Exception as e:
                    print('Exception stopping process %s: %s' % (arg, e))
                    ret_val.append({'result': 'error', 'cmd': 'stop', 'process': arg, 'details': str(e)})
        return ret_val

    def startProcesses(self, args):
        ret_val = []
        if len(args) == 1 and '*' in args:
            try:
                self.xmlrpc.supervisor.startAllProcesses()
                ret_val.append({'result': 'success', 'cmd': 'start', 'process': '*', 'details': 'Started all processes'})
            except Exception as e:
                print('Exception starting all processes')
                ret_val.append({'result': 'error', 'cmd': 'start', 'process': '*', 'details': str(e)})
        else:
            for arg in args:
                try:
                    self.xmlrpc.supervisor.startProcess(arg)
                    ret_val.append({'result': 'success', 'cmd': 'start', 'process': arg, 'details': 'Started process {0}'.format(arg)})
                except Exception as e:
                    print('Exception starting process %s: %s' % (arg, e))
                    ret_val.append({'result': 'error', 'cmd': 'start', 'process': arg, 'details': str(e)})
        return ret_val

    def restartProcesses(self, args):
        return self.stopProcesses(args).extend(self.startProcesses(args))