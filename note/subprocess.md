
'''

Popen.communicate(input=None)

option :
	input :[string] sent to the child process. default None

workflow: 
	Send data to stdin.  
	Read data from stdout and stderr until end-of-file is reached.  
	Wait for process to terminate. 

return : [tuple] (stdoutdata, stderrdata)

Note : 
	that if you want to send data to the process’s stdin, you need to create the Popen object with stdin=PIPE.  Similarly, to get anything other than None in the result tuple, you need to give stdout=PIPE and/or  stderr=PIPE too.
Note
	The data read is buffered in memory, so do not use this method if the data size is large or unlimited.
'''

##EXAMPLE 1 
###test.py
	#! /usr/bin python
	def test():
		print "Something to print"
		while(True):
		  input =raw_input("output what you input(y/n)")
		  if r=='n':
			print "Exiting"
			break
		  else :
			print input
	if __name__ == "__main__":
		test()


###subproc.py
	#! /usr/bin python
	def subproc():
		p=subprocess.Popen(["python","test.py"],stdin=PIPE,stdout=PIPE)
		print p.communicate()[0]

	if __name__ == "__main__":
 	subproc()

###Ouput
	Traceback (most recent call last):
	  File "./test.py", line 13, in <module>
		test()
	  File "./test.py", line 5, in test
		input =raw_input("output what you input, input 'n'exit\n")
	EOFError: EOF when reading a line
	Something to print
	output what you input, input 'n'exit

###Analysis
look at the workflow: .communicate() writes input , reads all output, and waits for the subprocess to exit.

there is no input in this case so it just closes subprocess' stdin to indicate to the subprocess that there is no more input

p.stdout.read() hangs forever because it tries to read all output from the child at the same time as the child waits for input (raw_input()) that causes a deadlock.

###Correct
To avoid the deadlock you need to read/write asynchronously (e.g., by using threads or select) or to know exactly when and how much to read/write



	from subprocess import PIPE, Popen

	p = Popen(["python", "-u", "test.py"], stdin=PIPE, stdout=PIPE, bufsize=1)
	print p.stdout.readline(), # read the first line "Something to print"
	for i in range(10): # repeat several times to show that it works
		print >>p.stdin, i # write input,  stdin=PIPE
		# the above print is equal to follow two sentence
		# p.stdin.write(str(i)+"\n")
		# p.stdin.flush()   
		print p.stdout.readline(), # read output,stdout=PIPE

	print p.communicate("n\n")[0], # signal the child to exit,
		                           # read the rest of the output, 
                               	   # wait for the child to exit

###Example2 [2]
	#!/usr/bin/python

	from subprocess import Popen, PIPE
	import threading

	p = Popen('ls', stdout=PIPE)

	class ReaderThread(threading.Thread):

		def __init__(self, stream):
		    threading.Thread.__init__(self)
		    self.stream = stream

		def run(self):
		    while True:
		        line = self.stream.readline()
		        if len(line) == 0:
		            break
		        print line,


	reader = ReaderThread(p.stdout)
	reader.start()

	# Wait until subprocess is done
	p.wait()

	# Wait until we've processed all output
	reader.join()

	print "Done!"

###Example3 [3]

The task I try to accomplish is to stream a ruby file and print out the output. (NOTE: I don't want to print out everything at once)

	main.py

	from subprocess import Popen, PIPE, STDOUT

	import pty
	import os

	file_path = '/Users/luciano/Desktop/ruby_sleep.rb'

	command = ' '.join(["ruby", file_path])

	master, slave = pty.openpty()
	proc = Popen(command, bufsize=0, shell=True, stdout=slave, stderr=slave, close_fds=True)     
	stdout = os.fdopen(master, 'r', 0)

	while proc.poll() is None:
		data = stdout.readline()
		if data != "":
		    print(data)
		else:
		    break

	print("This is never reached!")

	ruby_sleep.rb

	puts "hello"

	sleep 2

	puts "goodbye!"

**Problem**

Streaming the file works fine. The hello/goodbye output is printed with the 2 seconds delay. Exactly as the script should work. The problem is that readline() hangs in the end and never quits. I never reach the last print.

I know there is a lot of questions like this here a stackoverflow but non of them made me solve the problem. I'm not that into the whole subprocess thing so please give me a more hands-on/concrete answer.
	pty is Linux only as said in the docs:


**solution**	
Because pseudo-terminal handling is highly platform dependent, there is code to do it only for Linux. (The Linux code is supposed to work on other platforms, but hasn’t been tested yet.)

It is unclear how well it works on other OSes.You could try pexpect:

	import sys
	import pexpect

	pexpect.run("ruby ruby_sleep.rb", logfile=sys.stdout)

	Or stdbuf to enable line-buffering in non-interactive mode:

	from subprocess import Popen, PIPE, STDOUT

	proc = Popen(['stdbuf', '-oL', 'ruby', 'ruby_sleep.rb'],
		         bufsize=1, stdout=PIPE, stderr=STDOUT, close_fds=True)
	for line in iter(proc.stdout.readline, b''):
		print line,
	proc.stdout.close()
	proc.wait()

	Or using pty based on @Antti Haapala's answer:

	import os
	import pty
	import select
	from subprocess import Popen, STDOUT

	master_fd, slave_fd = pty.openpty()  # provide tty to enable
		                                 # line-buffering on ruby's side
	proc = Popen(['ruby', 'ruby_sleep.rb'],
		         bufsize=1, stdout=slave_fd, stderr=STDOUT, close_fds=True)
	timeout = .04 # seconds
	while 1:
		ready, _, _ = select.select([master_fd], [], [], timeout)
		if ready:
		    data = os.read(master_fd, 512)
		    if not data:
		        break
		    print("got " + repr(data))
		elif proc.poll() is not None: # select timeout
		    break # proc exited
	os.close(slave_fd) # can't do it sooner: it leads to errno.EIO error
	os.close(master_fd)
	proc.wait()

	print("This is reached!")

	All three code examples print 'hello' immediately (as soon as the first EOL is seen).

###Example4 [4]
The process I'm using right now is this:

    Attach a pty to the subprocess's stdout
    Loop until the subprocess exits by checking subprocess.poll
        When there is data available in the stdout write that data immediately to the current stdout.
    Finish!

After the child process has completed, the parent process hangs if I do not specify a timeout when using select.select. I would really prefer not to set a timeout. It just seems a bit dirty. However, all the other ways I've tried to get around the issue don't seem to work. Pexpect seems to get around it by using os.execv and pty.fork instead of subprocess.Popen and pty.openpty a solution I do not prefer. Am I doing something wrong with how I check for the life of the subprocess? Is my approach incorrect?

The code I'm using is below. I'm using this on a Mac OS X 10.6.8, but I need it to work on Ubuntu 12.04 as well.

This is the subprocess runner runner.py:

	import subprocess
	import select
	import pty
	import os
	import sys

	def main():
		master, slave = pty.openpty()

		process = subprocess.Popen(['python', 'outputter.py'], 
		        stdin=subprocess.PIPE, 
		        stdout=slave, stderr=slave, close_fds=True)

		while process.poll() is None:
		    # Just FYI timeout is the last argument to select.select
		    rlist, wlist, xlist = select.select([master], [], [])
		    for f in rlist:
		        output = os.read(f, 1000) # This is used because it doesn't block
		        sys.stdout.write(output)
		        sys.stdout.flush()
		print "**ALL COMPLETED**"

	if __name__ == '__main__':
		main()

This is the subprocess code outputter.py. The strange random parts are just to simulate a program outputting data at random intervals. You can remove it if you wish. It shouldn't matter:

	import time
	import sys
	import random

	def main():
		lines = ['hello', 'there', 'what', 'are', 'you', 'doing']
		for line in lines:
		    sys.stdout.write(line + random.choice(['', '\n']))
		    sys.stdout.flush()
		    time.sleep(random.choice([1,2,3,4,5])/20.0)
		sys.stdout.write("\ndone\n")
		sys.stdout.flush()

	if __name__ == '__main__':
		main()

###Example 4 [4]
Non-blocking read on a subprocess.PIPE in python

	#!/usr/bin/python
	# Runner with stdout/stderr catcher

	from sys import argv
	from subprocess import Popen, PIPE
	import os, io
	from threading import Thread
	import Queue
	def __main__():
		if (len(argv) > 1) and (argv[-1] == "-sub-"):
		    import time, sys
		    print "Application runned!"
		    time.sleep(2)
		    print "Slept 2 second"
		    time.sleep(1)
		    print "Slept 1 additional second",
		    time.sleep(2)
		    sys.stderr.write("Stderr output after 5 seconds")
		    print "Eol on stdin"
		    sys.stderr.write("Eol on stderr\n")
		    time.sleep(1)
		    print "Wow, we have end of work!",
		else:
		    os.environ["PYTHONUNBUFFERED"]="1"
		    try:
		        p = Popen( argv + ["-sub-"],
		                   bufsize=0, # line-buffered
		                   stdin=PIPE, stdout=PIPE, stderr=PIPE )
		    except WindowsError, W:
		        if W.winerror==193:
		            p = Popen( argv + ["-sub-"],
		                       shell=True, # Try to run via shell
		                       bufsize=0, # line-buffered
		                       stdin=PIPE, stdout=PIPE, stderr=PIPE )
		        else:
		            raise
		    inp = Queue.Queue()
		    sout = io.open(p.stdout.fileno(), 'rb', closefd=False)
		    serr = io.open(p.stderr.fileno(), 'rb', closefd=False)
		    def Pump(stream, category):
		        queue = Queue.Queue()
		        def rdr():
		            while True:
		                buf = stream.read1(8192)
		                if len(buf)>0:
		                    queue.put( buf )
		                else:
		                    queue.put( None )
		                    return
		        def clct():
		            active = True
		            while active:
		                r = queue.get()
		                try:
		                    while True:
		                        r1 = queue.get(timeout=0.005)
		                        if r1 is None:
		                            active = False
		                            break
		                        else:
		                            r += r1
		                except Queue.Empty:
		                    pass
		                inp.put( (category, r) )
		        for tgt in [rdr, clct]:
		            th = Thread(target=tgt)
		            th.setDaemon(True)
		            th.start()
		    Pump(sout, 'stdout')
		    Pump(serr, 'stderr')

		    while p.poll() is None:
		        # App still working
		        try:
		            chan,line = inp.get(timeout = 1.0)
		            if chan=='stdout':
		                print "STDOUT>>", line, "<?<"
		            elif chan=='stderr':
		                print " ERROR==", line, "=?="
		        except Queue.Empty:
		            pass
		    print "Finish"

	if __name__ == '__main__':
		__main__()



fcntl, select, asyncproc won't help in this case.
no good, uses select, unavailable in windows to file descriptors.
Reliable way to read a stream without blocking on both Windows and Linux is to use Queue.get_nowait():

	import sys
	from subprocess import PIPE, Popen
	from threading  import Thread

	try:
		from Queue import Queue, Empty
	except ImportError:
		from queue import Queue, Empty  # python 3.x

	ON_POSIX = 'posix' in sys.builtin_module_names

	def enqueue_output(out, queue):
		for line in iter(out.readline, b''):
		    queue.put(line)
		out.close()

	p = Popen(['myprogram.exe'], stdout=PIPE, bufsize=1, close_fds=ON_POSIX)
	q = Queue()
	t = Thread(target=enqueue_output, args=(p.stdout, q))
	t.daemon = True # thread dies with the program
	t.start()

	# ... do other things here

	# read line without blocking
	try:  line = q.get_nowait() # or q.get(timeout=.1)
	except Empty:
		print('no output yet')
	else: # got line
		# ... do something with line

Try the asyncproc module.which work on linux，not windows For example:

	import os
	from asyncproc import Process
	myProc = Process("myprogram.app")

	while True:
		# check to see if process has ended
		poll = myProc.wait(os.WNOHANG)
		if poll != None:
		    break
		# print any new output
		out = myProc.read()
		if out != "":
		    print out

###Example 5 [5]

	import subprocess

	some_string = 'input_data'

	sort_out = file('outfile.txt','w')
	sort_in = subprocess.Popen('sort', stdin=subprocess.PIPE, stdout=sort_out).stdin
	subprocess.Popen(['awk', '-f', 'script.awk'], stdout=sort_in, \
		                           stdin=subprocess.PIPE).communicate(some_string)

	#!/usr/bin/env python
	from subprocess import Popen, PIPE

	a = Popen(["a"], stdin=PIPE, stdout=PIPE)
	with open("outfile.txt", "wb") as outfile:
		b = Popen(["b"], stdin=a.stdout, stdout=outfile)
	a.stdout.close() # notify `a` if `b` exits (doesn't accept input anymore)
	a.stdin.write(b"input data")
	a.stdin.close() # no more input
	b.wait()
	a.wait() # should return on EOF in stdin or after an attempt to write to stdout

###Example 5 [5]
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

[1] http://stackoverflow.com/questions/16768290/working-of-popen-communicate?answertab=active#tab-top
[2] http://stackoverflow.com/questions/12419198/python-subprocess-readlines-hangs/12471855#12471855
[3] http://stackoverflow.com/questions/12419198/python-subprocess-readlines-hangs/12471855#12471855
[4] http://stackoverflow.com/questions/375427/non-blocking-read-on-a-subprocess-pipe-in-python	
[5] http://stackoverflow.com/questions/295459/how-do-i-use-subprocess-popen-to-connect-multiple-processes-by-pipes
[封装包](http://twistedmatrix.com/documents/current/core/howto/process.html)
[5] http://code.activestate.com/recipes/440554-module-to-allow-asynchronous-subprocess-use-on-win/ 
