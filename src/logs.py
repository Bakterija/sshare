from colorama import Fore, Back, Style
import logging
Logger = logging.getLogger(name='bakterija_io')
Logger.setLevel(1)


class _LogHandler(logging.Handler):
    def emit(self, logrecord):
        pathname = logrecord.pathname
        exc_info = logrecord.exc_info
        created = logrecord.created
        lineno = logrecord.lineno
        name = logrecord.name
        args = logrecord.args
        msg = logrecord.msg
        levelname = logrecord.levelname
        s = msg.find(':')
        if s == -1:
            msg = '[%-12s] %s' % (levelname, msg)
        else:
            msg = '[%-12s] [%-14s]%s' % (levelname, msg[:s], msg[s+1:])
            if levelname[0] == 'E':
                msg = ''.join((Fore.RED, msg, Style.RESET_ALL))
            elif levelname[0] == 'C':
                msg = ''.join((Fore.YELLOW, msg, Style.RESET_ALL))
        print (msg)

Logger.addHandler(_LogHandler())


class GeventLoggerInfo(object):
    @staticmethod
    def write(msg):
        msg = msg.rstrip()
        Logger.info('Gevent: %s' % (msg))


class GeventLoggerError(object):
    @staticmethod
    def write(msg):
        msg = msg.rstrip()
        Logger.error('Gevent: %s' % (msg))
