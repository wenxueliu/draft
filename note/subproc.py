#! /usr/bin python

from subprocess import PIPE, Popen

def subproc():
    p = Popen(["python", "-u", "test.py"], stdin=PIPE, stdout=PIPE, bufsize=1)
    print p.stdout.readline(), # read the first line
    for i in range(10): # repeat several times to show that it works
        #print >>p.stdin, i # write input
        p.stdin.write('test\n')
        #p.stdin.flush() # not necessary in this case
        print p.stdout.readline(), # read output

    print p.communicate("n\n")[0], # signal the child to exit,
                                   # read the rest of the output, 
                                   # wait for the child to exit


if __name__ == "__main__":
    subproc()
