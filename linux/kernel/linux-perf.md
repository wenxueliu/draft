
有些程序慢是因为计算量太大，其多数时间都应该在使用 CPU 进行计算，这叫做 CPU
bound 型；有些程序慢是因为过多的 IO，这种时候其 CPU 利用率应该不高，这叫做 IO
bound 型；对于 CPU bound 程序的调优和 IO bound 的调优是不同的。

* strace
    time sudo strace -v  -T -r -c -p 2377
* dtrace


##perf

安装:

方法一:

    sudo apt-get install linux-tools-`uname -r`

方法二:

    # cd /usr/src/linux-headers-`uname -r`/tools/perf
    # make
    # make install

###perf的运行原理

性能调优工具如 perf，Oprofile 等的基本原理都是对被监测对象进行采样, 最简单的情形是根据 tick 中断进行采样,
即在 tick 中断内触发采样点, 在采样点里判断程序当时的上下文. 假如一个程序 90% 的时间都花费在函数 foo() 上,
那么 90% 的采样点都应该落在函数 foo() 的上下文中. 运气不可捉摸, 但我想只要采样频率足够高, 采样时间足够长,
那么以上推论就比较可靠。因此，通过 tick 触发采样，我们便可以了解程序中哪些地方最耗时间, 从而重点分析.

###采样的事件

$perf list

事件分为以下三种：

* Hardware Event 是由 PMU 硬件产生的事件, 比如 cache 命中, 当您需要了解程序对硬件特性的使用情况时, 便需要对这些事件进行采样;
* Software Event 是内核软件产生的事件, 比如进程切换, tick 数等;
* Tracepoint event 是内核中的静态 tracepoint 所触发的事件, 这些 tracepoint 用来判断程序运行期间内核的行为细节, 比如 slab 分配器的分配次数等.

###

$ perf

###确定哪个进程最消耗 CPU

    $perf top

###统计命令 COMMAND 的 CPU

    $sudo perf stat COMMAND

###统计进程 PID 的 CPU

    $perf stat -p PID -- sleep NUM_SEC

    $perf stat -p PID -a sleep NUM_SEC

###

    $perf stat -p PID -e L1-dcache-loads,L1-dcache-load-misses,L1-dcache-stores -- sleep NUM_SEC

###对 PID 进程进行采样

$sudo perf record -F 100 -e cpu_clock -g -p PID -- sleep NUM_SEC

###对 COMMAND

$sudo perf record -F 100 -e cpu_clock -g COMMAND  //COMMAND 为执行的命令

###列出 tracepoints

perf list

###perf report

　　[.] : user level
　　[k]: kernel level
　　[g]: guest kernel level (virtualization)
    [u]: guest os user space
    [H]: hypervisor

$ sudo perf stat -p 2291 -a sleep 60

 Performance counter stats for process id '2291':

     168812.111385 task-clock (msec)         #    2.814 CPUs utilized           [100.00%]
         3,262,982 context-switches          #    0.019 M/sec                   [100.00%]
            37,705 cpu-migrations            #    0.223 K/sec                   [100.00%]
                 0 page-faults               #    0.000 K/sec
   479,942,635,951 cycles                    #    2.843 GHz                     [100.00%]
   <not supported> stalled-cycles-frontend
   <not supported> stalled-cycles-backend
   468,434,830,331 instructions              #    0.98  insns per cycle         [100.00%]
    96,954,751,128 branches                  #  574.335 M/sec                   [100.00%]
       446,596,919 branch-misses             #    0.46% of all branches

      60.000612802 seconds time elapsed

task-clock CPU 利用率. 该值高, 说明程序的多数时间花费在 CPU 计算上而非 IO.

context-switches : 进程切换次数. 记录了程序运行过程中发生了多少次进程切换, 频繁的进程切换是应该避免的。

cpu-migrations：处理器迁移次数. Linux为了维持多个处理器的负载均衡, 在特定条件下会将某个任务从一个 CPU 迁移到另一个 CPU.

page-faults：缺页异常的次数。当应用程序请求的页面尚未建立、请求的页面不在内存中，或者请求的页面虽然在内
存中，但物理地址和虚拟地址的映射关系尚未建立时，都会触发一次缺页异常。另外TLB不命中，页面访问权限不匹配
等情况也会触发缺页异常。

cycles：消耗的处理器周期数. 如果把被 ls 使用的 cpu cycles 看成是一个处理器的, 那么它的主频为 2.486GHz。

instructions：记录执行程序所发费的指令数。
branches：记录程序在运行过程中的分支指令数。
branch-misses：记录程序在运行过程中的分支预测失败次数。

###参考
http://www.brendangregg.com/perf.html
https://perf.wiki.kernel.org/index.php/Tutorial
http://kernel.taobao.org/index.php?title=Documents/Perf_flame_graph

----------------------------------------------------------------------------------------------

##SystemTap

如果要支持用户空间, 编译要加 -rdynamic

##参考
https://wiki.ubuntu.com/Kernel/Systemtap
https://sourceware.org/systemtap/wiki/SystemtapOnUbuntu
http://www.ibm.com/developerworks/cn/linux/l-cn-systemtap3/#main
https://sourceware.org/systemtap/SystemTap_Beginners_Guide/userspace-probing.html
http://blog.csdn.net/zhangskd/article/details/25708441
https://sourceware.org/systemtap/langref/
http://blog.csdn.net/sailor_8318/article/details/25076745
https://sourceware.org/systemtap/SystemTap_Beginners_Guide/useful-systemtap-scripts.html
http://www.brendangregg.com/perf.html
http://www.ibm.com/developerworks/cn/linux/l-systemtap/index.html
http://www.ibm.com/developerworks/cn/linux/l-cn-systemtap3/#main

##Ktap

###安装

$ apt-get install git gcc make libelf-dev
$ git clone https://github.com/ktap/ktap
$ cd ktap
$ make
$ sudo make install
$ sudo make load

##参考
http://www.ktap.org/doc/tutorial.html
http://www.brendangregg.com/ktap.html
