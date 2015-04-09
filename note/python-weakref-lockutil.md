[threading local](http://bioportal.weizmann.ac.il/course/python/PyMOTW/PyMOTW/docs/threading/index.html?highlight=threading#threading)





mkdtemp(suffix='', prefix='tmp', dir=None)
        User-callable function to create and return a unique temporary
        directory.  The return value is the pathname of the directory.
        
        Arguments are as for mkstemp, except that the 'text' argument is
        not accepted.
        
        The directory is readable, writable, and searchable only by the
        creating user.
        
        Caller is responsible for deleting the directory when done with it.

lockf(...)
        lockf (fd, operation, length=0, start=0, whence=0)
        
        This is essentially a wrapper around the fcntl() locking calls.  fd is the
        file descriptor of the file to lock or unlock, and operation is one of the
        following values:
        
            LOCK_UN - unlock
            LOCK_SH - acquire a shared lock
            LOCK_EX - acquire an exclusive lock
        
        When operation is LOCK_SH or LOCK_EX, it can also be bitwise ORed with
        LOCK_NB to avoid blocking on lock acquisition.  If LOCK_NB is used and the
        lock cannot be acquired, an IOError will be raised and the exception will
        have an errno attribute set to EACCES or EAGAIN (depending on the operating
        system -- for portability, check for either value).
        
        length is the number of bytes to lock, with the default meaning to lock to
        EOF.  start is the byte offset, relative to whence, to that the lock
        starts.  whence is as with fileobj.seek(), specifically:
        
            0 - relative to the start of the file (SEEK_SET)
            1 - relative to the current buffer position (SEEK_CUR)
            2 - relative to the end of the file (SEEK_END)




	class _InterProcessLock(object):
		"""Lock implementation which allows multiple locks, working around
		issues like bugs.debian.org/cgi-bin/bugreport.cgi?bug=632857 and does
		not require any cleanup. Since the lock is always held on a file
		descriptor rather than outside of the process, the lock gets dropped
		automatically if the process crashes, even if __exit__ is not executed.

		There are no guarantees regarding usage by multiple green threads in a
		single process here. This lock works only between processes. Exclusive
		access between local threads should be achieved using the semaphores
		in the @synchronized decorator.

		Note these locks are released when the descriptor is closed, so it's not
		safe to close the file descriptor while another green thread holds the
		lock. Just opening and closing the lock file can break synchronisation,
		so lock files must be accessed only using this abstraction.
		"""

		def __init__(self, name):
		    self.lockfile = None
		    self.fname = name

		def __enter__(self):
		    self.lockfile = open(self.fname, 'w')

		    while True:
		        try:
		            # Using non-blocking locks since green threads are not
		            # patched to deal with blocking locking calls.
		            # Also upon reading the MSDN docs for locking(), it seems
		            # to have a laughable 10 attempts "blocking" mechanism.
		            self.trylock()
		            return self
		        except IOError as e:
		            if e.errno in (errno.EACCES, errno.EAGAIN):
		                # external locks synchronise things like iptables
		                # updates - give it some time to prevent busy spinning
		                time.sleep(0.01)
		            else:
		                raise

		def __exit__(self, exc_type, exc_val, exc_tb):
		    try:
		        self.unlock()
		        self.lockfile.close()
		    except IOError:
		        LOG.exception(_("Could not release the acquired lock `%s`"),
		                      self.fname)

		def trylock(self):
		    raise NotImplementedError()

		def unlock(self):
		    raise NotImplementedError()


	class _WindowsLock(_InterProcessLock):
    	def trylock(self):
        	msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_NBLCK, 1)

    	def unlock(self):
        	msvcrt.locking(self.lockfile.fileno(), msvcrt.LK_UNLCK, 1)


	class _PosixLock(_InterProcessLock):
		def trylock(self):
		    fcntl.lockf(self.lockfile, fcntl.LOCK_EX | fcntl.LOCK_NB)

		def unlock(self):
		    fcntl.lockf(self.lockfile, fcntl.LOCK_UN)



	 _semaphores = weakref.WeakValueDictionary()

	if os.name == 'nt':
    	import msvcrt
    	InterProcessLock = _WindowsLock
	else:
    	import fcntl
    	InterProcessLock = _PosixLock  

至此实现了一个简单的非阻塞锁。


	_semaphores = weakref.WeakValueDictionary()


	def synchronized(name, lock_file_prefix, external=False, lock_path=None):
		"""Synchronization decorator.

		Decorating a method like so::

		    @synchronized('mylock')
		    def foo(self, *args):
		       ...

		ensures that only one thread will execute the foo method at a time.

		Different methods can share the same lock::

		    @synchronized('mylock')
		    def foo(self, *args):
		       ...

		    @synchronized('mylock')
		    def bar(self, *args):
		       ...

		This way only one of either foo or bar can be executing at a time.

		:param lock_file_prefix: The lock_file_prefix argument is used to provide
		lock files on disk with a meaningful prefix. The prefix should end with a
		hyphen ('-') if specified.

		:param external: The external keyword argument denotes whether this lock
		should work across multiple processes. This means that if two different
		workers both run a a method decorated with @synchronized('mylock',
		external=True), only one of them will execute at a time.

		:param lock_path: The lock_path keyword argument is used to specify a
		special location for external lock files to live. If nothing is set, then
		CONF.lock_path is used as a default.
		"""

		def wrap(f):
		    @functools.wraps(f)
		    def inner(*args, **kwargs):
		        # NOTE(soren): If we ever go natively threaded, this will be racy.
		        #              See http://stackoverflow.com/questions/5390569/dyn
		        #              amically-allocating-and-destroying-mutexes
				
				#semaphore.Semaphore() 是一个非绑定的互斥量。具体见[这里](http://eventlet.net/doc/modules/semaphore.html)
		        sem = _semaphores.get(name, semaphore.Semaphore())
		        if name not in _semaphores:
		            # this check is not racy - we're already holding ref locally
		            # so GC won't remove the item and there was no IO switch
		            # (only valid in greenthreads)
		            _semaphores[name] = sem

		        with sem:
		            LOG.debug(_('Got semaphore "%(lock)s" for method '
		                        '"%(method)s"...'), {'lock': name,
		                                             'method': f.__name__})

		            # NOTE(mikal): I know this looks odd
		            if not hasattr(local.strong_store, 'locks_held'):
		                local.strong_store.locks_held = []
		            local.strong_store.locks_held.append(name)

		            try:
						#neutron 中只有 neutron/agent/linux/iptables_manager.py 用到if，其他都是执行 else
		                if external and not CONF.disable_process_locking:
		                    LOG.debug(_('Attempting to grab file lock "%(lock)s" '
		                                'for method "%(method)s"...'),
		                              {'lock': name, 'method': f.__name__})
		                    cleanup_dir = False

		                    # We need a copy of lock_path because it is non-local
		                    local_lock_path = lock_path
		                    if not local_lock_path:
		                        local_lock_path = CONF.lock_path

		                    if not local_lock_path:
		                        cleanup_dir = True
		                        local_lock_path = tempfile.mkdtemp()

		                    if not os.path.exists(local_lock_path):
		                        fileutils.ensure_tree(local_lock_path)

		                    # NOTE(mikal): the lock name cannot contain directory
		                    # separators
		                    safe_name = name.replace(os.sep, '_')
		                    lock_file_name = '%s%s' % (lock_file_prefix, safe_name)
		                    lock_file_path = os.path.join(local_lock_path,
		                                                  lock_file_name)

		                    try:
		                        lock = InterProcessLock(lock_file_path)
		                        with lock:
		                            LOG.debug(_('Got file lock "%(lock)s" at '
		                                        '%(path)s for method '
		                                        '"%(method)s"...'),
		                                      {'lock': name,
		                                       'path': lock_file_path,
		                                       'method': f.__name__})
		                            retval = f(*args, **kwargs)
		                    finally:
		                        LOG.debug(_('Released file lock "%(lock)s" at '
		                                    '%(path)s for method "%(method)s"...'),
		                                  {'lock': name,
		                                   'path': lock_file_path,
		                                   'method': f.__name__})
		                        # NOTE(vish): This removes the tempdir if we needed
		                        #             to create one. This is used to
		                        #             cleanup the locks left behind by unit
		                        #             tests.
		                        if cleanup_dir:
		                            shutil.rmtree(local_lock_path)
		                else:
		                    retval = f(*args, **kwargs)

		            finally:
		                local.strong_store.locks_held.remove(name)

		        return retval
		    return inner
		return wrap

至此，流程：
0. 从 eventlet 获取 semaphore
1. 加锁
2. local.strong_store.locks_held 增加锁文件
3. 退出
4. local.strong_store.locks_held 删除锁文件，释放锁
	
	def synchronized_with_prefix(lock_file_prefix):
		"""Partial object generator for the synchronization decorator.

		Redefine @synchronized in each project like so::

		    (in nova/utils.py)
		    from nova.openstack.common import lockutils

		    synchronized = lockutils.synchronized_with_prefix('nova-')


		    (in nova/foo.py)
		    from nova import utils

		    @utils.synchronized('mylock')
		    def bar(self, *args):
		       ...

		The lock_file_prefix argument is used to provide lock files on disk with a
		meaningful prefix. The prefix should end with a hyphen ('-') if specified.
		"""

		return functools.partial(synchronized, lock_file_prefix=lock_file_prefix)
