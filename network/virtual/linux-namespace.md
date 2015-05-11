Linux Namespace 是 Linux 提供的一种内核级别环境隔离的方法。不知道你是否还记得很早以前的 Unix
有一个叫 chroot 的系统调用（通过修改根目录把用户jail到一个特定目录下），chroot提供了一种简单
的隔离模式：chroot内部的文件系统无法访问外部的内容。Linux Namespace 在此基础上，提供了对 UTS、
IPC、mount、PID、network、User等的隔离机制。

举个例子，我们都知道，Linux 下的超级父亲进程的PID是1，所以，同 chroot 一样，如果我们可以把用户
的进程空间jail到某个进程分支下，并像 chroot 那样让其下面的进程 看到的那个超级父进程的 PID 为1，
于是就可以达到资源隔离的效果了（不同的PID namespace中的进程无法看到彼此）

Linux Namespace 有如下种类，官方文档在这里《[Namespace in Operation](http://lwn.net/Articles/531114/)》

		分类 				系统调用参数 	相关内核版本
		Mount namespaces 	CLONE_NEWNS 	[Linux 2.4.19](http://lwn.net/2001/0301/a/namespaces.php3)
		UTS namespaces 		CLONE_NEWUTS 	[Linux 2.6.19](http://lwn.net/Articles/179345/)
		IPC namespaces 		CLONE_NEWIPC 	[Linux 2.6.19](http://lwn.net/Articles/187274/)
		PID namespaces 		CLONE_NEWPID 	[Linux 2.6.24](http://lwn.net/Articles/259217/)
		Network namespaces 	CLONE_NEWNET 	[始于Linux 2.6.24 完成于 Linux 2.6.29](http://lwn.net/Articles/219794/)
		User namespaces 	CLONE_NEWUSER 	[始于 Linux 2.6.23 完成于 Linux 3.8)](http://lwn.net/Articles/528078/)

主要是三个系统调用

* clone() - 实现线程的系统调用，用来创建一个新的进程，并可以通过设计上述参数达到隔离。
* unshare() - 使某进程脱离某个namespace
* setns() - 把某进程加入到某个namespace

unshare() 和 setns() 都比较简单，大家可以自己 man，我这里不说了。

下面还是让我们来看一些示例（以下的测试程序最好在Linux 内核为3.8以上的版本中运行，我用的是ubuntu 14.04）。

###clone()系统调用

首先，我们来看一下一个最简单的 clone() 系统调用的示例，（后面，我们的程序都会基于这个程序做修改）：

``` //clone.c
	#define _GNU_SOURCE
	#include <sys/types.h>
	#include <sys/wait.h>
	#include <stdio.h>
	#include <sched.h>
	#include <signal.h>
	#include <unistd.h>

	/* 定义一个给 clone 用的栈，栈大小1M */
	#define STACK_SIZE (1024 * 1024)
	static char container_stack[STACK_SIZE];

	char* const container_args[] = {
		"/bin/bash",
		NULL
	};

	int container_main(void* arg)
	{
		printf("Container - inside the container!\n");
		/* 直接执行一个shell，以便我们观察这个进程空间里的资源是否被隔离了 */
		execv(container_args[0], container_args);
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		printf("Parent - start a container!\n");
		/* 调用clone函数，其中传出一个函数，还有一个栈空间的（为什么传尾指针，因为栈是反着的） */
		int container_pid = clone(container_main, container_stack+STACK_SIZE, SIGCHLD, NULL);
		/* 等待子进程结束 */
		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```

从上面的程序，我们可以看到，这和 pthread 基本上是一样的玩法。但是，对于上面的程序，父子进程的进程空间
是没有什么差别的，父进程能访问到的子进程也能。

下面， 让我们来看几个例子看看，Linux 的 Namespace 是什么样的。


###UTS Namespace

下面的代码，我略去了上面那些头文件和数据结构的定义，只有最重要的部分。

``` //clone_uts.c
	int container_main(void* arg)
	{
		printf("Container - inside the container!\n");
		sethostname("container",10); /* 设置hostname */
		execv(container_args[0], container_args);
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		printf("Parent - start a container!\n");
		int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | SIGCHLD, NULL); /*启用CLONE_NEWUTS Namespace隔离 */
		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```

运行上面的程序你会发现（需要root权限），子进程的hostname变成了 container。

    mininet@mininet-vm:~/docker$ ./clone_uts //必须是 sudo 权限
    Parent - start a container!
    clone: Operation not permitted
    mininet@mininet-vm:~/docker$ sudo ./clone_uts
    Parent - start a container!
    Container - inside the container!
    root@container:~/docker# hostname
    container
	root@container:~# uname -n
	container
    root@container:~# uname -a
    Linux container 3.13.0-24-generic #46-Ubuntu SMP Thu Apr 10 19:11:08 UTC
    2014 x86_64 x86_64 x86_64 GNU/Linux
    root@container:~/docker# exit
    exit
    Parent - container stopped!

##IPC Namespace

IPC 全称 Inter-Process Communication，是 Unix/Linux 下进程间通信的一种方式，IPC 有共享内存、
信号量、消息队列等方法。所以，为了隔离，我们也需要把 IPC 给隔离开来，这样，只有在同一个
Namespace 下的进程才能相互通信。如果你熟悉 IPC 的原理的话，你会知道，IPC 需要有一个全局的 ID，
即然是全局的，那么就意味着我们的 Namespace 需要对这个 ID 隔离，不能让别的 Namespace 的进程看到。

要启动 IPC 隔离，我们只需要在调用 clone 时加上 CLONE_NEWIPC 参数就可以了。

```
	int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | CLONE_NEWIPC | SIGCHLD, NULL);
```

首先，我们先创建一个 IPC 的 Queue（如下所示，全局的 Queue ID 是 0）

    mininet@mininet-vm:~/docker$ ipcmk -Q
    Message queue id: 0
    mininet@mininet-vm:~/docker$ ipcs -q

    ------ Message Queues --------
    key        msqid      owner      perms      used-bytes   messages
    0x00586d89 0          mininet    644        0            0

如果我们运行没有CLONE_NEWIPC的程序，我们会看到，在子进程中还是能看到这个全启的IPC Queue。

    mininet@mininet-vm:~/docker$ sudo ./clone_uts
    Parent - start a container!
    Container - inside the container!
    root@container:~/docker# ipcs -q

    ------ Message Queues --------
    key        msqid      owner      perms      used-bytes   messages
    0x00586d89 0          mininet    644        0            0

但是，如果我们运行加上了CLONE_NEWIPC的程序，我们就会下面的结果：

    mininet@mininet-vm:~/docker$ ./clone_ipc_uts
    Parent - start a container!
    Parent - container stopped!
    mininet@mininet-vm:~/docker$ sudo ./clone_ipc_uts
    Parent - start a container!
    Container - inside the container!
    root@container:~/docker# ipcs -q

    ------ Message Queues --------
    key        msqid      owner      perms      used-bytes   messages
    root@container:~/docker# exit
    exit
    Parent - container stopped!


我们可以看到IPC已经被隔离了。

###PID Namespace

我们继续修改上面的程序

``` ./clone_pid_uts.c
	int container_main(void* arg)
	{
		/* 查看子进程的PID，我们可以看到其输出子进程的 pid 为 1 */
		printf("Container [%5d] - inside the container!\n", getpid());
		sethostname("container",10);
		execv(container_args[0], container_args);
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		printf("Parent [%5d] - start a container!\n", getpid());
		/*启用PID namespace - CLONE_NEWPID*/
		int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | CLONE_NEWPID | SIGCHLD, NULL);
		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```

运行结果如下（我们可以看到，子进程的 pid 是 1 了）：

    mininet@mininet-vm:~/docker$ sudo ./clone_pid_uts
    Parent [ 4566] - start a container!
    Container [    1] - inside the container!
    root@container:~/docker# echo $$
    1
    root@container:~/docker# exit
    exit
    Parent - container stopped!

你可能会问，PID 为 1 有个毛用啊？我们知道，在传统的 UNIX 系统中，PID 为 1 的进程是init，地位非常特殊。
他作为所有进程的父进程，有很多特权（比如：屏蔽信号等），另外，其还会为检查所有进程的状态，我们知道，
如果某个子进程脱离了父进程（父进程没有 wait 它），那么 init 就会负责回收资源并结束这个子进程。所以，
要做到进程空间的隔离，首先要创建出 PID 为 1 的进程，最好就像 chroot 那样，把子进程的 PID 在容器内变成 1。

但是，我们会发现，在子进程的 shell 里输入 ps,top 等命令，我们还是可以看得到所有进程。说明并没有完全隔离。
这是因为，像 ps, top 这些命令会去读 /proc 文件系统，所以，因为 /proc 文件系统在父进程和子进程都是一样的，
所以这些命令显示的东西都是一样的。

所以，我们还需要对文件系统进行隔离。

###Mount Namespace

下面的例程中，我们在启用了mount namespace并在子进程中重新mount了/proc文件系统。

``` //clone_ns_pid_uts.c
	int container_main(void* arg)
	{
		printf("Container [%5d] - inside the container!\n", getpid());
		sethostname("container",10);
		/* 重新mount proc文件系统到 /proc下 */
		system("mount -t proc proc /proc");
		execv(container_args[0], container_args);
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		printf("Parent [%5d] - start a container!\n", getpid());
		/* 启用Mount Namespace - 增加CLONE_NEWNS参数 */
		int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | SIGCHLD, NULL);
		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```


运行结果如下：

    mininet@mininet-vm:~/docker$ sudo ./clone_ns_pid_uts
    Parent [ 5027] - start a container!
    Container [    1] - inside the container!
    root@container:~/docker# ps -elf
    F S UID        PID  PPID  C PRI  NI ADDR SZ WCHAN  STIME TTY          TIME CMD
    4 S root         1     0  0  80   0 -  5918 wait   01:02 pts/2    00:00:00 /bin/bash
    0 R root        20     1  0  80   0 -  4672 -      01:03 pts/2    00:00:00 ps -elf



上面，我们可以看到只有两个进程 ，而且 pid=1 的进程是我们的 /bin/bash。我们还可以看到 /proc 目录下也干净了很多：

    root@container:~/docker# ls /proc/
    1          cmdline    driver       ioports    kpagecount     misc
    sched_debug  swaps          uptime
    24         consoles   execdomains  ipmi       kpageflags     modules
    schedstat    sys            version
    acpi       cpuinfo    fb           irq        latency_stats  mounts        scsi
    sysrq-trigger  version_signature
    asound     crypto     filesystems  kallsyms   loadavg        mtrr          self
    sysvipc        vmallocinfo
    buddyinfo  devices    fs           kcore      locks          net
    slabinfo     timer_list     vmstat
    bus        diskstats  interrupts   key-users  mdstat         pagetypeinfo
    softirqs     timer_stats    zoneinfo
    cgroups    dma        iomem        kmsg       meminfo        partitions    stat
    tty

    root@container:~/docker# exit
    exit
    Parent - container stopped!

下图，我们也可以看到在子进程中的 top 命令只看得到两个进程了。

这里，多说一下。在通过 CLONE_NEWNS 创建 mount namespace 后，父进程会把自己的文件结构复制给子进程中。
而子进程中新的 namespace 中的所有 mount 操作都只影响自身的文件系统，而不对外界产生任何影响。这样可以
做到比较严格地隔离。

你可能会问，我们是不是还有别的一些文件系统也需要这样 mount? 是的。


###Docker的 Mount Namespace

下面我将向演示一个“山寨镜像”，其模仿了Docker的Mount Namespace。

首先，我们需要一个rootfs，也就是我们需要把我们要做的镜像中的那些命令什么的copy到一个rootfs的目录下，我们
模仿Linux构建如下的目录：

    mininet@mininet-vm:~/docker$ ls rootfs/
    bin  dev  etc  home  lib  lib64  mnt  opt  proc  root  run  sbin  sys  tmp  usr
    var

然后，我们把一些我们需要的命令 copy 到 rootfs/bin 目录中（sh 命令必需要 copy 进去，不然我们无法 chroot ）

    mininet@mininet-vm:~/docker$ ls rootfs/bin/ rootfs/usr/bin/
    rootfs/bin/:
    bash  chgrp  chown  echo  gzip      ip    less  ls    mount       mv  netstat
    ps   rm   sh     tar    which
    cat   chmod  cp     grep  hostname  kill  ln    more  mountpoint  nc  ping
    pwd  sed  sleep  touch

    rootfs/usr/bin/:
    awk  env  groups  head  id  mesg  sort  strace  tail  top  uniq  vi  wc  xargs


注：你可以使用ldd命令把这些命令相关的那些so文件copy到对应的目录：

    mininet@mininet-vm:~/docker$ cd rootfs/bin/
    mininet@mininet-vm:~/docker/rootfs/bin$ ldd bash
        linux-vdso.so.1 =>  (0x00007fff86ca3000)
        libtinfo.so.5 => /lib/x86_64-linux-gnu/libtinfo.so.5
        (0x00007f1176122000)
        libdl.so.2 => /lib/x86_64-linux-gnu/libdl.so.2 (0x00007f1175f1e000)
        libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6 (0x00007f1175b57000)
        /lib64/ld-linux-x86-64.so.2 (0x00007f1176359000)

下面是我的rootfs中的一些so文件：

    mininet@mininet-vm:~/docker/rootfs/bin$ cd ..
    mininet@mininet-vm:~/docker/rootfs$ ls ./lib64 ./lib/x86_64-linux-gnu/
    ./lib64:
    ld-linux-x86-64.so.2

    ./lib/x86_64-linux-gnu/:
    libacl.so.1      libc.so.6          libm.so.6           libnss_compat-2.19.so
    libnss_hesiod.so.2      libpthread-2.19.so  libutil-2.19.so
    libacl.so.1.1.0  libdl-2.19.so      libncurses.so.5     libnss_compat.so.2
    libnss_nis-2.19.so      libpthread.so.0     libutil.so.1
    libattr.so.1     libdl.so.2         libncurses.so.5.9   libnss_dns-2.19.so
    libnss_nisplus-2.19.so  libresolv-2.19.so   libuuid.so.1
    libblkid.so.1    libm-2.19.so       libncursesw.so.5    libnss_dns.so.2
    libnss_nisplus.so.2     libresolv.so.2      libz.so.1
    libc-2.19.so     libmemusage.so     libncursesw.so.5.9  libnss_files-2.19.so
    libnss_nis.so.2         libselinux.so.1
    libcap.so.2      libmount.so.1      libnsl-2.19.so      libnss_files.so.2
    libpcre.so.3            libtinfo.so.5
    libcap.so.2.24   libmount.so.1.1.0  libnsl.so.1         libnss_hesiod-2.19.so
    libprocps.so.3          libtinfo.so.5.9


包括这些命令依赖的一些配置文件：

    mininet@mininet-vm:~/docker/rootfs$ ls ./etc/
    bash.bashrc  conf  group  hostname  hosts  ld.so.cache  nsswitch.conf  passwd
    profile  resolv.conf  shadow

你现在会说，我靠，有些配置我希望是在容器起动时给他设置的，而不是hard code在镜像中的。比如：/etc/hosts，
/etc/hostname，还有 DNS 的 /etc/resolv.conf 文件。好的。那我们在 rootfs 外面，我们再创建一个 conf 目录，
把这些文件放到这个目录中。

    mininet@mininet-vm:~/docker/rootfs$ cd ..
    mininet@mininet-vm:~/docker$ ls conf/
    hostname  hosts  resolv.conf


这样，我们的父进程就可以动态地设置容器需要的这些文件的配置， 然后再把他们 mount 进容器，这样，容器的镜像中的配置就比较灵活了。

好了，终于到了我们的程序。

```
    //clone_docker.c
	#define _GNU_SOURCE
	#include <sys/types.h>
	#include <sys/wait.h>
	#include <sys/mount.h>
	#include <stdio.h>
	#include <sched.h>
	#include <signal.h>
	#include <unistd.h>

	#define STACK_SIZE (1024 * 1024)

	static char container_stack[STACK_SIZE];
	char* const container_args[] = {
		"/bin/bash",
		"-l",
		NULL
	};

	int container_main(void* arg)
	{
		printf("Container [%5d] - inside the container!\n", getpid());

		//set hostname
		sethostname("container",10);

		//remount "/proc" to make sure the "top" and "ps" show container's information
		if (mount("proc", "rootfs/proc", "proc", 0, NULL) !=0 ) {
		    perror("proc");
		}
		if (mount("sysfs", "rootfs/sys", "sysfs", 0, NULL)!=0) {
		    perror("sys");
		}
		if (mount("none", "rootfs/tmp", "tmpfs", 0, NULL)!=0) {
		    perror("tmp");
		}
		if (mount("udev", "rootfs/dev", "devtmpfs", 0, NULL)!=0) {
		    perror("dev");
		}
		if (mount("devpts", "rootfs/dev/pts", "devpts", 0, NULL)!=0) {
		    perror("dev/pts");
		}
		if (mount("shm", "rootfs/dev/shm", "tmpfs", 0, NULL)!=0) {
		    perror("dev/shm");
		}
		if (mount("tmpfs", "rootfs/run", "tmpfs", 0, NULL)!=0) {
		    perror("run");
		}
		/*
		 * 模仿Docker的从外向容器里mount相关的配置文件
		 * 你可以查看：/var/lib/docker/containers/<container_id>/目录，
		 * 你会看到docker的这些文件的。
		 */
		if (mount("conf/hosts", "rootfs/etc/hosts", "none", MS_BIND, NULL)!=0 ||
		      mount("conf/hostname", "rootfs/etc/hostname", "none", MS_BIND, NULL)!=0 ||
		      mount("conf/resolv.conf", "rootfs/etc/resolv.conf", "none", MS_BIND, NULL)!=0 ) {
		    perror("conf");
		}
		/* 模仿docker run命令中的 -v, --volume=[] 参数干的事 */
		if (mount("/tmp/t1", "rootfs/mnt", "none", MS_BIND, NULL)!=0) {
		    perror("mnt");
		}

		/* chroot 隔离目录 */
		if ( chdir("./rootfs") != 0 || chroot("./") != 0 ){
		    perror("chdir/chroot");
		}

		execv(container_args[0], container_args);
		perror("exec");
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		printf("Parent [%5d] - start a container!\n", getpid());
		int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWPID | CLONE_NEWNS | SIGCHLD, NULL);
		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```


sudo运行上面的程序，你会看到下面的挂载信息以及一个所谓的“镜像”：


    mininet@mininet-vm:~/docker$ sudo ./clone_docker
    Parent [ 6320] - start a container!
    Container [    1] - inside the container!
    mnt: No such file or directory

    root@container:/# mount
    proc on /proc type proc (rw,relatime)
    sysfs on /sys type sysfs (rw,relatime)
    none on /tmp type tmpfs (rw,relatime)
    udev on /dev type devtmpfs (rw,relatime,size=928744k,nr_inodes=232186,mode=755)
    devpts on /dev/pts type devpts (rw,relatime,mode=600,ptmxmode=000)
    tmpfs on /run type tmpfs (rw,relatime)
    /dev/disk/by-uuid/19968674-0d36-4a9b-96bc-b59198ea0522 on /etc/hosts type
    ext4 (rw,relatime,errors=remount-ro,data=ordered)
    /dev/disk/by-uuid/19968674-0d36-4a9b-96bc-b59198ea0522 on /etc/hostname type
    ext4 (rw,relatime,errors=remount-ro,data=ordered)
    /dev/disk/by-uuid/19968674-0d36-4a9b-96bc-b59198ea0522 on /etc/resolv.conf
    type ext4 (rw,relatime,errors=remount-ro,data=ordered)

    root@container:/# ls /bin /usr/bin
    /bin:
    bash  chgrp  chown  echo  gzip      ip    less  ls    mount   mv  netstat
    ps   rm  sh tar    which
    cat   chmod  cp     grep  hostname  kill  ln    more  mountpoint  nc  ping
    pwd  sed  sleep touch

    /usr/bin:
    awk  env  groups  head  id  mesg  sort  strace  tail  top  uniq  vi  wc
    xargs

    root@container:/# exit
    logout
    Parent - container stopped!


关于如何做一个chroot的目录，这里有个工具叫[DebootstrapChroot](https://wiki.ubuntu.com/DebootstrapChroot)，
你可以顺着链接去看看（英文的哦）

###User Namespace

User Namespace 主要是用了 CLONE_NEWUSER 的参数。使用了这个参数后，内部看到的 UID 和 GID 已经与外部不同了，
默认显示为65534。那是因为容器找不到其真正的UID所以，设置上了最大的UID（其设置定义在/proc/sys/kernel/overflowuid）。

要把容器中的 uid 和真实系统的 uid 给映射在一起，需要修改 /proc/<pid>/uid_map 和 /proc/<pid>/gid_map 这两个文件。
这两个文件的格式为：

ID-inside-ns ID-outside-ns length

其中：

* 第一个字段ID-inside-ns表示在容器显示的UID或GID，
* 第二个字段ID-outside-ns表示容器外映射的真实的UID或GID。
* 第三个字段表示映射的范围，一般填1，表示一一对应。

比如，把真实的uid=1000映射成容器内的uid=0

    $ cat /proc/2465/uid_map
            0       1000          1

再比如下面的示例：表示把namespace内部从0开始的uid映射到外部从0开始的uid，其最大范围是无符号32位整形

    $ cat /proc/$$/uid_map
            0          0          4294967295

另外，需要注意的是：

* 写这两个文件的进程需要这个 namespace 中的 CAP_SETUID (CAP_SETGID) 权限（可参看[Capabilities](http://man7.org/linux/man-pages/man7/capabilities.7.html)）
* 写入的进程必须是此 user namespace 的父或子的 user namespace 进程。
* 另外需要满如下条件之一：1）父进程将effective uid/gid映射到子进程的user namespace中，2）父进程如果有CAP_SETUID/CAP_SETGID权限，那么它将可以映射到父进程中的任一uid/gid。

这些规则看着都烦，我们来看程序吧（下面的程序有点长，但是非常简单，如果你读过《Unix网络编程》上卷，你应该可以看懂）：

```
    //clone_pid_uts_ns_user.c
	#define _GNU_SOURCE
	#include <stdio.h>
	#include <stdlib.h>
	#include <sys/types.h>
	#include <sys/wait.h>
	#include <sys/mount.h>
	#include <sys/capability.h>
	#include <stdio.h>
	#include <sched.h>
	#include <signal.h>
	#include <unistd.h>

	#define STACK_SIZE (1024 * 1024)

	static char container_stack[STACK_SIZE];
	char* const container_args[] = {
		"/bin/bash",
		NULL
	};

	int pipefd[2];

	void set_map(char* file, int inside_id, int outside_id, int len) {
		FILE* mapfd = fopen(file, "w");
		if (NULL == mapfd) {
		    perror("open file error");
		    return;
		}
		fprintf(mapfd, "%d %d %d", inside_id, outside_id, len);
		fclose(mapfd);
	}

	void set_uid_map(pid_t pid, int inside_id, int outside_id, int len) {
		char file[256];
		sprintf(file, "/proc/%d/uid_map", pid);
		set_map(file, inside_id, outside_id, len);
	}

	void set_gid_map(pid_t pid, int inside_id, int outside_id, int len) {
		char file[256];
		sprintf(file, "/proc/%d/gid_map", pid);
		set_map(file, inside_id, outside_id, len);
	}

	int container_main(void* arg)
	{

		printf("Container [%5d] - inside the container!\n", getpid());

		printf("Container: eUID = %ld;  eGID = %ld, UID=%ld, GID=%ld\n",
		        (long) geteuid(), (long) getegid(), (long) getuid(), (long) getgid());

		/* 等待父进程通知后再往下执行（进程间的同步） */
		char ch;
		close(pipefd[1]);
		read(pipefd[0], &ch, 1);

		printf("Container [%5d] - setup hostname!\n", getpid());
		//set hostname
		sethostname("container",10);

		//remount "/proc" to make sure the "top" and "ps" show container's information
		mount("proc", "/proc", "proc", 0, NULL);

		execv(container_args[0], container_args);
		printf("Something's wrong!\n");
		return 1;
	}

	int main()
	{
		const int gid=getgid(), uid=getuid();

		printf("Parent: eUID = %ld;  eGID = %ld, UID=%ld, GID=%ld\n",
		        (long) geteuid(), (long) getegid(), (long) getuid(), (long) getgid());

		pipe(pipefd);

		printf("Parent [%5d] - start a container!\n", getpid());

		int container_pid = clone(container_main, container_stack+STACK_SIZE,
		        CLONE_NEWUTS | CLONE_NEWPID | CLONE_NEWNS | CLONE_NEWUSER | SIGCHLD, NULL);


		printf("Parent [%5d] - Container [%5d]!\n", getpid(), container_pid);

		//To map the uid/gid,
		//   we need edit the /proc/PID/uid_map (or /proc/PID/gid_map) in parent
		//The file format is
		//   ID-inside-ns   ID-outside-ns   length
		//if no mapping,
		//   the uid will be taken from /proc/sys/kernel/overflowuid
		//   the gid will be taken from /proc/sys/kernel/overflowgid
		set_uid_map(container_pid, 0, uid, 1);
		set_gid_map(container_pid, 0, gid, 1);

		printf("Parent [%5d] - user/group mapping done!\n", getpid());

		/* 通知子进程 */
		close(pipefd[1]);

		waitpid(container_pid, NULL, 0);
		printf("Parent - container stopped!\n");
		return 0;
	}
```

上面的程序，我们用了一个 pipe 来对父子进程进行同步，为什么要这样做？因为子进程中有一个 execv 的系统调用，
这个系统调用会把当前子进程的进程空间给全部覆盖掉，我们希望在 execv 之前就做好 user namespace 的 uid/gid
的映射，这样，execv 运行的 /bin/bash 就会因为我们设置了 uid 为 0 的 inside-uid 而变成 #号的提示符。

整个程序的运行效果如下：

	mininet@mininet-vm:~/docker$ id
	uid=1000(mininet) gid=1000(mininet) groups=1000(mininet),4(adm),24(cdrom),27(sudo),30(dip),46(plugdev),109(lpadmin),110(sambashare)

	mininet@mininet-vm:~/docker$ ./clone_pid_uts_ns_user  #<--以 mininet 用户运行
	Parent: eUID = 1000;  eGID = 1000, UID=1000, GID=1000
	Parent [ 4551] - start a container!
	Parent [ 4551] - Container [ 4552]!
	Parent [ 4551] - user/group mapping done!
	Container [    1] - inside the container!
	Container: eUID = 0;  eGID = 0, UID=0, GID=0
	Container [    1] - setup hostname!

	root@container:/# id #<----我们可以看到容器里的用户和命令行提示符是root用户了
	uid=0(root) gid=0(root) groups=0(root),65534(nogroup)

    root@container:~/docker# exit
    exit
    Parent - container stopped!

虽然容器里是 root，但其实这个容器的 /bin/bash 进程是以一个普通用户 mininet 来运行的。这样一来，我们容器的安全性会得到提高。

我们注意到，User Namespace 是以普通用户运行，但是别的 Namespace 需要 root 权限，那么，
如果我要同时使用多个 Namespace，该怎么办呢？一般来说，我们先用一般用户创建 User
Namespace，然后把这个一般用户映射成 root，在容器内用 root 来创建其它的 Namesapce。

###Network Namespace

Network 的 Namespace 比较啰嗦。在 Linux 下，我们一般用 ip 命令创建 Network Namespace（Docker的源码中，它没有用ip命令，
而是自己实现了 ip 命令内的一些功能——是用了Raw Socket发些“奇怪”的数据，呵呵）。这里，我还是用ip命令讲解一下。

首先，我们先看个图，下面这个图基本上就是Docker在宿主机上的网络示意图（其中的物理网卡并不准确，因为docker可能会运行在
一个VM中，所以，这里所谓的“物理网卡”其实也就是一个有可以路由的IP的网卡）

![network-namespace](network-namespace.jpg)

上图中，Docker使用了一个私有网段，172.40.1.0，docker 还可能会使用 10.0.0.0 和 192.168.0.0 这两个私有网段，
关键看你的路由表中是否配置了，如果没有配置，就会使用，如果你的路由表配置了所有私有网段，那么docker启动时就会出错了。

当你启动一个 Docker 容器后，你可以使用 ip link show 或 ip addr show 来查看当前宿主机的网络情况（我们可以看到有一个
docker0，还有一个 veth22a38e6 的虚拟网卡——给容器用的）：

    mininet@mininet-vm:~/docker$ ip link show
    1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state ...
        link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc ...
        link/ether 00:0c:29:b7:67:7d brd ff:ff:ff:ff:ff:ff
    3: docker0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
        link/ether 56:84:7a:fe:97:99 brd ff:ff:ff:ff:ff:ff
    5: veth22a38e6: <BROADCAST,UP,LOWER_UP> mtu 1500 qdisc ...
        link/ether 8e:30:2a:ac:8c:d1 brd ff:ff:ff:ff:ff:ff

那么，要做成这个样子应该怎么办呢？我们来看一组命令：

    ## 首先，我们先增加一个网桥lxcbr0，模仿docker0
    brctl addbr lxcbr0
    brctl stp lxcbr0 off
    ifconfig lxcbr0 192.168.10.1/24 up #为网桥设置IP地址

    ## 接下来，我们要创建一个network namespace - ns1

    # 增加一个namesapce 命令为 ns1 （使用ip netns add命令）
    ip netns add ns1

    # 激活namespace中的loopback，即127.0.0.1（使用ip netns exec ns1来操作ns1中的命令）
    ip netns exec ns1   ip link set dev lo up

    ## 然后，我们需要增加一对虚拟网卡

    # 增加一个pair虚拟网卡，注意其中的veth类型，其中一个网卡要按进容器中
    ip link add veth-ns1 type veth peer name lxcbr0.1

    # 把 veth-ns1 按到namespace ns1中，这样容器中就会有一个新的网卡了
    ip link set veth-ns1 netns ns1

    # 把容器里的 veth-ns1改名为 eth0 （容器外会冲突，容器内就不会了）
    ip netns exec ns1  ip link set dev veth-ns1 name eth0

    # 为容器中的网卡分配一个IP地址，并激活它
    ip netns exec ns1 ifconfig eth0 192.168.10.11/24 up


    # 上面我们把 veth-ns1 这个网卡按到了容器中，然后我们要把 lxcbr0.1 添加上网桥上
    brctl addif lxcbr0 lxcbr0.1

    # 为容器增加一个路由规则，让容器可以访问外面的网络
    ip netns exec ns1     ip route add default via 192.168.10.1

    # 在/etc/netns下创建network namespce名称为ns1的目录，
    # 然后为这个namespace设置resolv.conf，这样，容器内就可以访问域名了
    mkdir -p /etc/netns/ns1
    echo "nameserver 8.8.8.8" > /etc/netns/ns1/resolv.conf

上面基本上就是docker网络的原理了，只不过，

* Docker 的 resolv.conf 没有用这样的方式，而是用了上篇中的 Mount Namesapce 的那种方式
* Docker 是用进程的 PID 来做 Network Namespace 的名称的。

了解了这些后，你甚至可以为正在运行的docker容器增加一个新的网卡：

    ip link add peerA type veth peer name peerB
    brctl addif docker0 peerA
    ip link set peerA up
    ip link set peerB netns ${container-pid}
    ip netns exec ${container-pid} ip link set dev peerB name eth1
    ip netns exec ${container-pid} ip link set eth1 up ;
    ip netns exec ${container-pid} ip addr add ${ROUTEABLE_IP} dev eth1 ;

上面的示例是我们为正在运行的docker容器，增加一个 eth1 的网卡，并给了一个静态的可被外部访问到的IP地址。

这个需要把外部的“物理网卡”配置成混杂模式，这样这个 eth1 网卡就会向外通过 ARP 协议发送自己的 Mac 地址，
然后外部的交换机就会把到这个 IP 地址的包转到“物理网卡”上，因为是混杂模式，所以 eth1 就能收到相关的数据，
一看，是自己的，那么就收到。这样，Docker 容器的网络就和外部通了。

当然，无论是 Docker 的NAT方式，还是混杂模式都会有性能上的问题，NAT 不用说了，存在一个转发的开销，混杂模
式呢，网卡上收到的负载都会完全交给所有的虚拟网卡上，于是就算一个网卡上没有数据，但也会被其它网卡上的数据
所影响。

这两种方式都不够完美，我们知道，真正解决这种网络问题需要使用 VLAN 技术，于是 Google 的同学们为 Linux 内核
实现了一个 [IPVLAN](https://lwn.net/Articles/620087/) 的驱动，这基本上就是为Docker量身定制的。

###Namespace文件

上面就是目前 Linux Namespace 的玩法。 现在，我来看一下其它的相关东西。

让我们运行一下（也就是 PID Namespace 中那个 mount proc 的程序），然后不要退出。

    mininet@mininet-vm:~/docker$ sudo ./clone_pid_uts
    Parent [ 6777] - start a container!
    Container [    1] - inside the container!
    root@container:~/docker# pstree -p 6777
    clone_pid_uts(6777)───bash(6778)───pstree(6797)

我们到另一个shell中查看一下父子进程的PID：

    mininet@mininet-vm:~$ pstree -p 6777
    clone_pid_uts(6777)───bash(6778)

我们可以到proc下（/proc//ns）查看进程的各个 namespace 的id（内核版本需要3.8以上）。

    mininet@mininet-vm:~$ sudo ls -l /proc/6777/ns/
    total 0
    lrwxrwxrwx 1 root root 0 May  6 02:45 ipc -> ipc:[4026531839]
    lrwxrwxrwx 1 root root 0 May  6 02:45 mnt -> mnt:[4026531840]
    lrwxrwxrwx 1 root root 0 May  6 02:45 net -> net:[4026531956]
    lrwxrwxrwx 1 root root 0 May  6 02:45 pid -> pid:[4026531836]
    lrwxrwxrwx 1 root root 0 May  6 02:45 user -> user:[4026531837]
    lrwxrwxrwx 1 root root 0 May  6 02:45 uts -> uts:[4026531838]

下面是子进程的：

    mininet@mininet-vm:~$ sudo ls -l /proc/6778/ns/
    total 0
    lrwxrwxrwx 1 root root 0 May  6 02:47 ipc -> ipc:[4026531839]
    lrwxrwxrwx 1 root root 0 May  6 02:47 mnt -> mnt:[4026531840]
    lrwxrwxrwx 1 root root 0 May  6 02:47 net -> net:[4026531956]
    lrwxrwxrwx 1 root root 0 May  6 02:47 pid -> pid:[4026532193]
    lrwxrwxrwx 1 root root 0 May  6 02:47 user -> user:[4026531837]
    lrwxrwxrwx 1 root root 0 May  6 02:47 uts -> uts:[4026532192]


我们可以看到，其中的 ipc，net，user 是同一个ID，而 mnt,pid,uts 都是不一样的。如果两个进程指向的
namespace 编号相同，就说明他们在同一个 namespace 下，否则则在不同 namespace 里面。

这些文件还有另一个作用，那就是，一旦这些文件被打开，只要其 fd 被占用着，那么就算 PID 所属的所有
进程都已经结束，创建的 namespace 也会一直存在。比如：我们可以通过：

    mount –bind /proc/6777/ns/uts ~/uts 来 hold 这个 namespace。

另外，我们在上篇中讲过一个 setns 的系统调用，其函数声明如下：

    int setns(int fd, int nstype);

其中第一个参数就是一个fd，也就是一个open()系统调用打开了上述文件后返回的 fd，比如：

    fd = open("/proc/4600/ns/nts", O_RDONLY);  // 获取namespace文件描述符
    setns(fd, 0); // 加入新的namespace

##参考文档

[Namespaces in operation](http://lwn.net/Articles/531114/)
[Linux Namespace Man Page](http://man7.org/linux/man-pages/man7/namespaces.7.html)
[Creat Containers – Part 1](http://crosbymichael.com/creating-containers-part-1.html)
[Introduction to Linux namespaces](https://blog.jtlebi.fr/2013/12/22/introduction-to-linux-namespaces-part-1-uts/)
