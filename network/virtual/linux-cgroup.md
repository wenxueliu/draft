前面，我们介绍了 Linux Namespace，但是 Namespace 解决的问题主要是环境隔离的问题，这只是虚拟化中最最基础的一步，
我们还需要解决对计算机资源使用上的隔离。也就是说，虽然你通过 Namespace 把我 Jail 到一个特定的环境中去了，但是我
在其中的进程使用用 CPU、内存、磁盘等这些计算资源其实还是可以随心所欲的。所以，我们希望对进程进行资源利用上的限制
或控制。这就是 Linux CGroup 出来了的原因。

Linux CGroup 全称 Linux Control Group， 是 Linux 内核的一个功能，用来限制，控制与分离一个进程组群的资源（如CPU、内存、
磁盘输入输出等）。这个项目最早是由 Google 的工程师在 2006 年发起（主要是 Paul Menage 和 Rohit Seth），最早的名称为进程
容器（process containers）。在2007年时，因为在 Linux 内核中，容器（container）这个名词太过广泛，为避免混乱，被重命名为
cgroup，并且被合并到 2.6.24 版的内核中去。然后，其它开始了他的发展。

Linux CGroupCgroup 可让您为系统中所运行任务（进程）的用户定义组群分配资源— 比如 CPU 时间、系统内存、网络带宽或者这些资
源的组合。您可以监控您配置的 cgroup，拒绝 cgroup 访问某些资源，甚至在运行的系统中动态配置您的 cgroup。

主要提供了如下功能：

* Resource limitation: 限制资源使用，比如内存使用上限以及文件系统的缓存限制。
* Prioritization: 优先级控制，比如：CPU利用和磁盘IO吞吐。
* Accounting: 一些审计或一些统计，主要目的是为了计费。
* Control: 挂起进程，恢复执行进程。

使用 cgroup，系统管理员可更具体地控制对系统资源 的分配、优先顺序、拒绝、管理和监
控。可更好地根据任务和用户分配硬件资源， 提高总体效率

* 隔离一个进程集合（比如：nginx的所有进程），并限制他们所消费的资源，比如绑定CPU的核。
* 为这组进程 分配其足够使用的内存
* 为这组进程分配相应的网络带宽和磁盘存储限制
* 限制访问某些设备（通过设置设备的白名单）

那么CGroup是怎么干的呢？我们先来点感性认识吧。

首先，Linux 把 CGroup 这个事实现成了一个 file system，你可以 mount。在我的 Ubuntu 14.04 下，你输入以下命令你就可以看到
cgroup 已为你 mount 好了。

    mininet@mininet-vm:~$ mount -t cgroup
    cgroup on /sys/fs/cgroup/cpuset type cgroup (rw,relatime,cpuset)
    cgroup on /sys/fs/cgroup/cpu type cgroup (rw,relatime,cpu)
    cgroup on /sys/fs/cgroup/cpuacct type cgroup (rw,relatime,cpuacct)
    cgroup on /sys/fs/cgroup/memory type cgroup (rw,relatime,memory)
    cgroup on /sys/fs/cgroup/devices type cgroup (rw,relatime,devices)
    cgroup on /sys/fs/cgroup/freezer type cgroup (rw,relatime,freezer)
    cgroup on /sys/fs/cgroup/blkio type cgroup (rw,relatime,blkio)
    cgroup on /sys/fs/cgroup/perf_event type cgroup (rw,relatime,perf_event)
    cgroup on /sys/fs/cgroup/hugetlb type cgroup (rw,relatime,hugetlb)
    systemd on /sys/fs/cgroup/systemd type cgroup (rw,noexec,nosuid,nodev,none,name=systemd)

或者使用 lssubsys命令：

    mininet@mininet-vm:~$ lssubsys -m
    cpuset /sys/fs/cgroup/cpuset
    cpu /sys/fs/cgroup/cpu
    cpuacct /sys/fs/cgroup/cpuacct
    memory /sys/fs/cgroup/memory
    devices /sys/fs/cgroup/devices
    freezer /sys/fs/cgroup/freezer
    blkio /sys/fs/cgroup/blkio
    perf_event /sys/fs/cgroup/perf_event
    hugetlb /sys/fs/cgroup/hugetlb

我们可以看到，在/sys/fs下有一个cgroup的目录，这个目录下还有很多子目录，比如： cpu，cpuset，memory，blkio……
这些，这些都是cgroup的子系统。分别用于干不同的事的。

如果你没有看到上述的目录，你可以自己 mount，下面给了一个示例：

    mkdir cgroup
    mount -t tmpfs cgroup_root ./cgroup
    mkdir cgroup/cpuset
    mount -t cgroup -ocpuset cpuset ./cgroup/cpuset/
    mkdir cgroup/cpu
    mount -t cgroup -ocpu cpu ./cgroup/cpu/
    mkdir cgroup/memory
    mount -t cgroup -omemory memory ./cgroup/memory/

一旦 mount 成功，你就会看到这些目录下就有好文件了，比如，如下所示的 cpu 和 cpuset 的子系统：

    mininet@mininet-vm:~$ ls /sys/fs/cgroup/cpu /sys/fs/cgroup/cpuset/
    /sys/fs/cgroup/cpu:
    cgroup.clone_children  cgroup.sane_behavior  cpu.shares         release_agent
    cgroup.event_control   cpu.cfs_period_us     cpu.stat           tasks
    cgroup.procs           cpu.cfs_quota_us      notify_on_release  user

    /sys/fs/cgroup/cpuset/:
    cgroup.clone_children  cpuset.mem_hardwall             cpuset.sched_load_balance
    cgroup.event_control   cpuset.memory_migrate           cpuset.sched_relax_domain_level
    cgroup.procs           cpuset.memory_pressure          notify_on_release
    cgroup.sane_behavior   cpuset.memory_pressure_enabled  release_agent
    cpuset.cpu_exclusive   cpuset.memory_spread_page       tasks
    cpuset.cpus            cpuset.memory_spread_slab       user
    cpuset.mem_exclusive   cpuset.mems

你可以到/sys/fs/cgroup的各个子目录下去make个dir，你会发现，一旦你创建了一个子目录，这个子目录里又有很多文件了。

    mininet@mininet-vm:/sys/fs/cgroup/cpu$ sudo mkdir haoel
    mininet@mininet-vm:/sys/fs/cgroup/cpu$ ls ./haoel/
    cgroup.clone_children  cgroup.procs       cpu.cfs_quota_us  cpu.stat           tasks
    cgroup.event_control   cpu.cfs_period_us  cpu.shares        notify_on_release

好了，我们来看几个示例。

###CPU 限制

假设，我们有一个非常吃CPU的程序，叫deadloop，其源码如下：

    #deadloop.c
    #include <stdio.h>
    int main(void)
    {
        int i = 0;
        for(;;) i++;
        return 0;
    }

用 sudo 执行起来后，毫无疑问，CPU 被干到了 100%（下面是top命令的输出）

    PID  USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
    4150 mininet   20   0    4192    356    276 R 94.0  0.0   0:13.40 deadloop

然后，我们这前不是在 /sys/fs/cgroup/cpu 下创建了一个 haoel 的 group。我们先设置一下这个 group 的 cpu 利用的限制：

    mininet@mininet-vm:~/docker$ cat /sys/fs/cgroup/cpu/haoel/cpu.cfs_quota_us
    -1
    mininet@mininet-vm:~/docker$ su root
    Password:
    root@mininet-vm:/home/mininet/docker# echo 20000 > /sys/fs/cgroup/cpu/haoel/cpu.cfs_quota_us

我们看到，这个进程的 PID 是 4150，我们把这个进程加到这个 cgroup 中：

    root@mininet-vm:/home/mininet/docker# echo 4150 >> /sys/fs/cgroup/cpu/haoel/tasks

然后，就会在top中看到CPU的利用立马下降成20%了。（前面我们设置的20000就是20%的意思）

    PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND
    4150 mininet   20   0    4192    356    276 R 20.0  0.0   2:23.68 deadloop

下面的代码是一个线程的示例：

```
    //cpu_cgroup.c
    #define _GNU_SOURCE         /* See feature_test_macros(7) */

    #include <pthread.h>
    #include <stdio.h>
    #include <stdlib.h>
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <unistd.h>
    #include <sys/syscall.h>


    const int NUM_THREADS = 5;

    void *thread_main(void *threadid)
    {
        /* 把自己加入cgroup中（syscall(SYS_gettid)为得到线程的系统tid） */
        char cmd[128];
        sprintf(cmd, "echo %ld >> /sys/fs/cgroup/cpu/haoel/tasks", syscall(SYS_gettid));
        system(cmd);
        sprintf(cmd, "echo %ld >> /sys/fs/cgroup/cpuset/haoel/tasks", syscall(SYS_gettid));
        system(cmd);

        long tid;
        tid = (long)threadid;
        printf("Hello World! It's me, thread #%ld, pid #%ld!\n", tid, syscall(SYS_gettid));

        int a=0;
        while(1) {
            a++;
        }
        pthread_exit(NULL);
    }
    int main (int argc, char *argv[])
    {
        int num_threads;
        if (argc > 1){
            num_threads = atoi(argv[1]);
        }
        if (num_threads<=0 || num_threads>=100){
            num_threads = NUM_THREADS;
        }

        /* 设置CPU利用率为50% */
        mkdir("/sys/fs/cgroup/cpu/haoel", 755);
        system("echo 50000 > /sys/fs/cgroup/cpu/haoel/cpu.cfs_quota_us");

        mkdir("/sys/fs/cgroup/cpuset/haoel", 755);
        /* 限制CPU只能使用#2核和#3核 */
        system("echo \"2,3\" > /sys/fs/cgroup/cpuset/haoel/cpuset.cpus");

        pthread_t* threads = (pthread_t*) malloc (sizeof(pthread_t)*num_threads);
        int rc;
        long t;
        for(t=0; t<num_threads; t++){
            printf("In main: creating thread %ld\n", t);
            rc = pthread_create(&threads[t], NULL, thread_main, (void *)t);
            if (rc){
                printf("ERROR; return code from pthread_create() is %d\n", rc);
                exit(-1);
            }
        }

        /* Last thing that main() should do */
        pthread_exit(NULL);
        free(threads);
    }
```

编译

    mininet@mininet-vm:~/docker$ gcc cpu_cgroup.c -lpthread -o cpu_cgroup

执行

    mininet@mininet-vm:~/docker$ su root
    Password:

    root@mininet-vm:/home/mininet/docker# ./cpu_cgroup
    sh: echo: I/O error
    In main: creating thread 0
    In main: creating thread 1
    In main: creating thread 2
    In main: creating thread 3
    In main: creating thread 4
    sh: echo: I/O error
    Hello World! It's me, thread #4, pid #4704!
    sh: sh: echo: I/O error
    Hello World! It's me, thread #2, pid #4702!
    echo: I/O error
    sh: Hello World! It's me, thread #3, pid #4703!
    sh: echo: I/O error
    Hello World! It's me, thread #1, pid #4701!
    echo: I/O error
    Hello World! It's me, thread #0, pid #4700!

    mininet@mininet-vm:~/docker$ top
    PID USER      PR  NI    VIRT    RES    SHR S %CPU %MEM     TIME+ COMMAND 
    4697 root      20   0       0      0      0 Z 50.0  0.0   0:18.53 cpu_cgroup


###内存使用限制

我们再来看一个限制内存的例子（下面的代码是个死循环，其它不断的分配内存，每次512个字节，每次休息一秒）：

```
    //memory_cgroup.c
    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <sys/types.h>
    #include <unistd.h>

    int main(void)
    {
        int size = 0;
        int chunk_size = 512;
        void *p = NULL;

        while(1) {

            if ((p = malloc(p, chunk_size)) == NULL) {
                printf("out of memory!!\n");
                break;
            }
            memset(p, 1, chunk_size);
            size += chunk_size;
            printf("[%d] - memory is allocated [%8d] bytes \n", getpid(), size);
            sleep(1);
        }
        return 0;
    }
```

然后，在我们另外一边：

    # 创建memory cgroup
    $ mkdir /sys/fs/cgroup/memory/haoel
    $ echo 64k > /sys/fs/cgroup/memory/haoel/memory.limit_in_bytes

    # 把上面的进程的pid加入这个cgroup
    $ echo [pid] > /sys/fs/cgroup/memory/haoel/tasks

你会看到，一会上面的进程就会因为内存问题被kill掉了。

###磁盘I/O限制

tmux 分屏当前窗口,

    mininet@mininet-vm:~$ tmux

之后按 Ctrl+b "

在一个窗口,我们先看一下我们的硬盘IO，我们的模拟命令如下：（从/dev/sda1上读入数据，输出到/dev/null上）

    mininet@mininet-vm:~$ sudo dd if=/dev/sda1 of=/dev/null

在另一窗口,我们通过iotop 命令我们可以看到相关的 IO 速度是55MB/s（虚拟机内）：

    TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
    6028 be/4 root       55.74 M/s    0.00 B/s  0.00 % 85.65 % dd if=/de~=/dev/null...

然后，新开一个 shell 窗口, 我们先创建一个blkio（块设备IO）的cgroup

    mininet@mininet-vm:~$ sudo mkdir /sys/fs/cgroup/blkio/haoel

并把读IO限制到1MB/s，并把前面那个dd命令的pid放进去（注：8:0 是设备号，你可以通过ls -l /dev/sda1获得）

    mininet@mininet-vm:~$ su root
    Password:
    root@mininet-vm:/home/mininet# echo '8:0 1048576'  > /sys/fs/cgroup/blkio/haoel/blkio.throttle.read_bps_device
    root@mininet-vm:/home/mininet# echo 6028 > /sys/fs/cgroup/blkio/haoel/tasks

再用iotop命令，你马上就能看到读速度被限制到了1MB/s左右

    TID  PRIO  USER     DISK READ  DISK WRITE  SWAPIN     IO>    COMMAND
    6028 be/4 root      973.20 K/s    0.00 B/s  0.00 % 94.41 % dd if=/de~=/dev/null...

###CGroup的子系统

好了，有了以上的感性认识我们来，我们来看看control group有哪些子系统：

* blkio     这个子系统为块设备设定输入/输出限制，比如物理设备（磁盘，固态硬盘，USB 等等）。
* cpu       这个子系统使用调度程序提供对 CPU 的 cgroup 任务访问。
* cpuacct   这个子系统自动生成 cgroup 中任务所使用的 CPU 报告。
* cpuset    这个子系统为 cgroup 中的任务分配独立 CPU（在多核系统）和内存节点。
* devices   这个子系统可允许或者拒绝 cgroup 中的任务访问设备。
* freezer   这个子系统挂起或者恢复 cgroup 中的任务。
* memory    这个子系统设定 cgroup 中任务使用的内存限制，并自动生成内存资源使用报告。
* net_cls   这个子系统使用等级识别符（classid）标记网络数据包，可允许 Linux 流量控制程序（tc）识别从具体 cgroup 中生成的数据包。
* net_prio  这个子系统用来设计网络流量的优先级
* hugetlb   这个子系统主要针对于HugeTLB系统进行限制，这是一个大页文件系统。

注意，你可能在 Ubuntu 14.04 下看不到 net_cls 和 net_prio 这两个cgroup，你需要手动mount一下：

$ sudo modprobe cls_cgroup
$ sudo mkdir /sys/fs/cgroup/net_cls
$ sudo mount -t cgroup -o net_cls none /sys/fs/cgroup/net_cls

$ sudo modprobe netprio_cgroup
$ sudo mkdir /sys/fs/cgroup/net_prio
$ sudo mount -t cgroup -o net_prio none /sys/fs/cgroup/net_prio

关于各个子系统的参数细节，以及更多的Linux CGroup的文档，你可以看看下面的文档：


* [Linux Kernel的官方文档](https://www.kernel.org/doc/Documentation/cgroups/)
* [Redhat的官方文档](https://access.redhat.com/documentation/zh-CN/Red_Hat_Enterprise_Linux/6/html-single/Resource_Management_Guide/index.html#ch-Subsystems_and_Tunable_Parameters)

###CGroup的术语

CGroup有下述术语：

**任务（Tasks）**

就是系统的一个进程。

**控制组（Control Group）**

一组按照某种标准划分的进程，比如官方文档中的 Professor 和 Student，或是 WWW 和 System 之类的，其表示了某进
程组。Cgroups 中的资源控制都是以控制组为单位实现。一个进程可以加入到某个控制组。而资源的限制是定义在这个组
上，就像上面示例中我用的 haoel 一样。简单点说，cgroup 的呈现就是一个目录带一系列的可配置文件。

**层级（Hierarchy）**

控制组可以组织成 hierarchical 的形式，即一颗控制组的树（目录结构）。控制组树上的子节点继承父结点的属性。简
单点说，hierarchy 就是在一个或多个子系统上的 cgroups 目录树。

**子系统（Subsystem）**

一个子系统就是一个资源控制器，比如 CPU 子系统就是控制 CPU 时间分配的一个控制器。子系统必须附加到一个层级上
才能起作用，一个子系统附加到某个层级以后，这个层级上的所有控制族群都受到这个子系统的控制。Cgroup 的子系统可
以有很多，也在不断增加中。

###下一代的CGroup

上面，我们可以看到，CGroup 的一些常用方法和相关的术语。一般来说，这样的设计在一般情况下还是没什么问题的，除
了操作上的用户体验不是很好，但基本满足我们的一般需求了。

不过，对此，有个叫Tejun Heo的同学非常不爽，他在 Linux 社区里对 cgroup 吐了一把槽，还引发了内核组的各种讨论。

对于 Tejun Heo 同学来说，cgroup 设计的相当糟糕。他给出了些例子，大意就是说，如果有多种层级关系，也就是说有多
种对进程的分类方式，比如，我们可以按用户来分，分成 Professor 和 Student，同时，也有按应用类似来分的，比如
WWW 和 NFS 等。那么，当一个进程即是 Professor 的，也是 WWW 的，那么就会出现多层级正交的情况，从而出现对进程
上管理的混乱。另外，一个 case 是，如果有一个层级 A 绑定 cpu，而层级 B 绑定 memory，还有一个层级 C 绑定 cputset，
而有一些进程有的需要 AB，有的需要 AC，有的需要 ABC，管理起来就相当不易。

层级操作起来比较麻烦，而且如果层级变多，更不易于操作和管理，虽然那种方式很好实现，但是在使用上有很多的复杂度。
你可以想像一个图书馆的图书分类问题，你可以有各种不同的分类，分类和图书就是一种多对多的关系。

所以，在Kernel 3.16后，引入了 [unified hierarchy] 的新的设计，这个东西引入了一个叫__DEVEL__sane_behavior 的特
性（这个名字很明显意味目前还在开发试验阶段），它可以把所有子系统都挂载到根层级下，只有叶子节点可以存在 tasks，
非叶子节点只进行资源控制。

我们mount一下看看：

    $ sudo mount -t cgroup -o __DEVEL__sane_behavior cgroup ./cgroup

    $ ls ./cgroup
    cgroup.controllers  cgroup.procs  cgroup.sane_behavior  cgroup.subtree_control

    $ cat ./cgroup/cgroup.controllers
    cpuset cpu cpuacct memory devices freezer net_cls blkio perf_event net_prio
    hugetlb

我们可以看到有四个文件，然后，你在这里 mkdir 一个子目录，里面也会有这四个文件。上级的 cgroup.subtree_control
控制下级的 cgroup.controllers。

举个例子：假设我们有以下的目录结构，b代表blkio，m代码memory，其中，A是root，包括所有的子系统（）。

    # A(b,m) - B(b,m) - C (b)
    #               \ - D (b) - E

    # 下面的命令中， +表示enable， -表示disable

    # 在B上的enable blkio
    # echo +blkio > A/cgroup.subtree_control

    # 在C和D上enable blkio
    # echo +blkio > A/B/cgroup.subtree_control

    # 在B上enable memory
    # echo +memory > A/cgroup.subtree_control

在上述的结构中，

* cgroup 只有上线控制下级，无法传递到下下级。所以，C 和 D 中没有 memory 的限制，E 中没有 blkio 和 memory 的限制。而本层的 cgroup.controllers 文件是个只读的，其中的内容就看上级的 subtree_control 里有什么了。
* 任何被配置过 subtree_control 的目录都不能绑定进程，根结点除外。所以，A,C,D,E可以绑上进程，但是B不行。

我们可以看到，这种方式干净的区分开了两个事，一个是进程的分组，一个是对分组的资源控制（以前这两个事完全混在一起），
在目录继承上增加了些限制，这样可以避免一些模棱两可的情况。

当然，这个事还在演化中，cgroup 的这些问题这个事目前由 cgroup 的吐槽人 Tejun Heo 和华为的 Li Zefan 同学负责解决中。
总之，这是一个系统管理上的问题，而且改变会影响很多东西，但一旦方案确定，老的cgroup方式将一去不复返。

###参考


* [Linux Kernel Cgroup Documents](https://www.kernel.org/doc/Documentation/cgroups/)
* [Reahat Resource Management Guide](https://access.redhat.com/documentation/zh-CN/Red_Hat_Enterprise_Linux/6/html-single/Resource_Management_Guide/index.html)
* [Fixing control groups](https://lwn.net/Articles/484251/)
* [The unified control group hierarchy in 3.16](http://lwn.net/Articles/601840/)
* [Cgroup v2(PDF)](http://events.linuxfoundation.org/sites/events/files/slides/2014-KLF.pdf)

