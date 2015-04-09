#!/usr/bin/python
# -*- utf-8 -*-

import os
import sys
from posixpath import curdir, sep, pardir, join, abspath, commonprefix
import locale

enc = locale.getpreferredencoding()

def unicode_abspath(path):
    global enc
    assert type(path) is unicode
    # shouldn't pass unicode to this craphead, it appends with os.getcwd() which is always a str
    return os.path.abspath(path.encode(sys.getfilesystemencoding())).decode(sys.getfilesystemencoding())


def relpath(path, start=curdir):
    """Return a relative version of a path"""

    if not path:
        raise ValueError("no path specified")

    if type(start) is unicode:
        start_list = unicode_abspath(start).split(sep)
    else:
        start_list = abspath(start).split(sep)

    if type(path) is unicode:
        path_list = unicode_abspath(path).split(sep)
    else:
        path_list = abspath(path).split(sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(commonprefix([start_list, path_list]))

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return join(*rel_list)


def console_print(st=u"", f=sys.stdout, linebreak=True):
    global enc
    assert type(st) is unicode
    f.write(st.encode(enc))
    if linebreak: f.write(os.linesep)

def console_flush(f=sys.stdout):
    f.flush()

#@parm question: you want to question which need replay yes/no; 
def yes_no_question(question):
    """a chose of y/n"""
    while True:
        console_print(question, linebreak=False)
        console_print(u" [y/n] ", linebreak=False)
        console_flush()
        text = raw_input()
        if text.lower().startswith("y"):
            return True
        elif text.lower().startswith("n"):
            return False
        else:
            console_print(u"Sorry, I didn't understand that. Please type yes or no.")


def plat():
    """get the platform x86 or x86_64"""
    if sys.platform.lower().startswith('linux'):
        arch = platform.machine()
        if (arch[0] == 'i' and
            arch[1].isdigit() and
            arch[2:4] == '86'):
            plat = "x86"
        elif arch == 'x86_64':
            plat = arch
        else:
            FatalVisibleError("Platform not supported")
        return "lnx.%s" % plat
    else:
        FatalVisibleError("Platform not supported")


def mkdirs(path, overwrite=False):
    from os import makedirs
    from errno import EEXIST
    try:
        makedirs(path)
    except OSError as err:
        if err.errno == EEXIST:
            if not overwrite:
                print "path '%s' already exists" % path
        else:
            raise

####################################################
from optparse import OptionParser, SUPPRESS_HELP
def CmdLineParse():   
    """
    命令行程序： from python-swiftclient
    """
    parser = OptionParser(version='%%prog %s' % version,
                          usage = '''
Usage: %%prog <command> [options] [args]
.....
'''.strip('\n') )
    parser.add_option('-v', '--verbose', action='count', dest='verbose',
            default=1, help='print more info')
    parser.disable_interspersed_args()
    (options, args) = parse_args(parser, argv[1:], enforce_requires=False)
    parser.enable_interspersed_args()

def encode_utf8(value):
    if isinstance(value, unicode):
        value = value.encode('utf8')
    return value


TRUE_VALUES = set(('true', '1', 'yes', 'on', 't', 'y'))
def config_true_value(value):
    """
    Returns True if the value is either True or a string in TRUE_VALUES.
    Returns False otherwise.
    This function come from swift.common.utils.config_true_value()
    """
    return value is True or \
        (isinstance(value, basestring) and value.lower() in TRUE_VALUES)


def prt_bytes(bytes, human_flag):
    """
    convert a number > 1024 to printable format, either in 4 char -h format as
    with ls -lh or return as 12 char right justified string
    """

    if human_flag:
        suffix = ''
        mods = 'KMGTPEZY'
        temp = float(bytes)
        if temp > 0:
            while (temp > 1023):
                temp /= 1024.0
                suffix = mods[0]
                mods = mods[1:]
            if suffix != '':
                if temp >= 10:
                    bytes = '%3d%s' % (temp, suffix)
                else:
                    bytes = '%.1f%s' % (temp, suffix)
        if suffix == '':    # must be < 1024
            bytes = '%4s' % bytes
    else:
        bytes = '%12s' % bytes

    return(bytes)

def _run_shell_command(cmd, throw_on_error=False, buffer=True, env=None):
    if buffer:
        out_location = subprocess.PIPE
        err_location = subprocess.PIPE
    else:
        out_location = None
        err_location = None

    newenv = os.environ.copy()
    if env:
        newenv.update(env)

    output = subprocess.Popen(cmd,
                              stdout=out_location,
                              stderr=err_location,
                              env=newenv)
    out = output.communicate()
    if output.returncode and throw_on_error:
        print "%s returned %d" % (cmd, output.returncode)
    if len(out) == 0 or not out[0] or not out[0].strip():
        return ''
    return out[0].strip().decode('utf-8')

#=======================================
import datetime
def get_datetime(date, now=False):
    if now:
        now = time.utcnow()
        current_time = time.time(now.hour, now.minute, now.second)
    else:
        current_time = time.time()
    return datetime.datetime.combine(data, current_time)

def today(self):
    return time.today()
#=======================================
