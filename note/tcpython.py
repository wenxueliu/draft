#! /usr/bin python
def TestOpionparser():
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename",
                    help="write report to FILE", metavar="FILE")
    parser.add_option("-q", "--quiet",
                     action="store_false", dest="verbose", default=True,
                     help="don't print status messages to stdout")
    (options, args) = parser.parse_args()

    print "test"
    print _(options.__dict__)
    print (options.filename)
    print (options.verbose)
    print (args)

import subprocess

def sub(size):
    print 'start'
    cmd1 = 'find ../'
    cmd2 = "ls ./"
    cmd3 = 'echo 1'
    status = 0
    for cmd in (cmd1, cmd2, cmd3):
        p = subprocess.Popen(args=cmd, shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT, close_fds=True)
        out_put = p.stdout.read()
        if out_put:
            print out_put
            
        #p.communicate()
        #p.wait()
        if p.returncode:
            status += 1
    print status
    print 'end'


if __name__=="__main__":
    sub(64 * 1024 + 1)
