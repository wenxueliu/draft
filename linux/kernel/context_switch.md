


###什么是上下文切换

精确定义见[这里](http://www.linfo.org/context_switch.html)

多任务系统往往需要同时执行多道作业.作业数往往大于机器的CPU数, 然而一颗CPU同时只能执行一项任务,
如何让用户感觉这些任务正在同时进行呢? 操作系统的设计者巧妙地利用了时间片轮转的方式, CPU给每个
任务都服务一定的时间, 然后把当前任务的状态保存下来, 在加载下一任务的状态后, 继续服务下一任务.
任务的状态保存及再加载, 这段过程就叫做上下文切换. 时间片轮转的方式使多个任务在同一颗 CPU 上
执行变成了可能, 但同时也带来了保存现场和加载现场的直接消耗.

更精确地说, 上下文切换会带来直接和间接两种因素影响程序性能的消耗. 直接消耗包括: CPU寄存器需要
保存和加载, 系统调度器的代码需要执行, TLB实例需要重新加载, CPU 的 pipeline 需要刷掉; 间接消耗
指的是多核的cache之间得共享数据, 间接消耗对于程序的影响要看线程工作区操作数据的大小.

[上下文切换](context_switch.png)

###如何查看上下文切换

$ vmstat 1
procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
 r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
 0  0  34220 370956 186004 1114880    0    0    16    22  287  152 10  3 87  0  0
 0  0  34220 370452 186020 1115424    0    0   128   344  585 2383  5  3 91  2  0
 0  0  34220 364684 186028 1115416    0    0     0    12  568 1755  6  1 93  1  0
 0  0  34220 371212 186032 1115416    0    0     0   204  606 2339  6  3 91  0  0
 0  0  34220 371196 186032 1115424    0    0     0     0  523 1737  3  1 96  0  0
 0  0  34220 369884 186032 1115424    0    0     0    44  596 2400  5  3 93  0  0
 0  0  34220 369956 186040 1115416    0    0     0    84  495 1656  3  1 95  0  0

###引起上下文切换的原因

* 当前执行任务的时间片用完之后, 系统 CPU 正常调度下一个任务
* 当前执行任务碰到 IO 阻塞, 调度器将挂起此任务, 继续下一任务
* 多个任务抢占锁资源, 当前任务没有抢到, 被调度器挂起, 继续下一任务
* 用户代码挂起当前任务, 让出 CPU 时间


###如果测试上下文切换


1 硬件中断. 前段时间发现有人在使用 futex 的 WAIT 和 WAKE 来测试 context switch 的直接消耗(链接),



2 阻塞 IO 来测试 context switch 的消耗(链接).



###如何跟踪上下文切换

* strace
* perf

    perf stat -e cache-misses COMMAND

* systemTap
* ktap

###上下文切换与 CPU affinity 的关系


对比没有将进程绑定到 CPU 和通过 taskset 将进程绑定到具体 CPU 之后区别


###进程上下文

进程的运行环境主要包括:

1. 进程空间中的代码和数据, 各种数据结构, 进程堆栈和共享内存区等.
2. 环境变量: 提供进程运行所需的环境信息.
3. 系统数据: 进程空间中的对进程进行管理和控制所需的信息, 包括进程任务结构体以及内核堆栈等.
4. 进程访问设备或者文件时的权限.
5. 各种硬件寄存器.
6. 地址转换信息.

在 Linux 中把系统提供给进程的处于动态变化的运行环境总和称为进程上下文.

处理器总处于以下状态中的一种:

1. 内核态, 运行于进程上下文, 内核代表进程运行于内核空间;
2. 内核态, 运行于中断上下文, 内核代表硬件运行于内核空间;
3. 用户态, 运行于用户空间.

用户态到内核态, 进程需要传递进程的运行环境给内核, 这个涉及到寄存器状态的
保存, 参数传递等等数据.

上下文简单说来就是一个环境, 相对于进程而言, 就是进程执行时的环境. 具体来
说就是各个变量和数据, 包括所有的寄存器变量, 进程打开的文件, 内存信息等.

一个进程的上下文可以分为三个部分: 用户级上下文, 寄存器上下文以及系统级上下文.

用户级上下文: 正文, 数据, 用户堆栈以及共享存储区;
寄存器上下文: 通用寄存器, 程序寄存器(IP), 处理器状态寄存器(EFLAGS), 栈指针(ESP);
系统级上下文: 进程控制块 task_struct, 内存管理信息(mm_struct, vm_area_struct, pgd, pte), 内核栈;

当发生进程调度时, 进行进程切换就是上下文切换(context switch). 操作系统
必须对上面提到的全部信息进行切换, 新调度的进程才能运行. 而系统调用进行的
模式切换(mode switch). 模式切换与进程切换比较起来, 容易很多, 而且节省时间,
因为模式切换最主要的任务只是切换进程寄存器上下文.

系统中的每一个进程都有自己的上下文. 一个正在使用处理器运行的进程称为当前
进程(current). 当前进程因时间片用完或者因等待某个事件而阻塞时, 进程调度
需要把处理器的使用权从当前进程交给另一个进程, 这个过程叫做进程切换. 此时,
被调用进程成为当前进程. 在进程切换时系统要把当前进程的上下文保存在指定的
内存区域(该进程的任务状态段TSS中), 然后把下一个使用处理器运行的进程的上
下文设置成当前进程的上下文. 当一个进程经过调度再次使用 CPU 运行时, 系统要恢
复该进程保存的上下文. 所以, 进程的切换也就是上下文切换.

在系统内核为用户进程服务时, 通常是进程通过系统调用执行内核代码, 这时进程的
执行状态由用户态转换为内核态. 但是, 此时内核的运行是为用户进程服务, 也可以
说内核在代替当前进程执行某种服务功能. 在这种情况下, 内核的运行仍是进程运行
的一部分, 所以说这时内核是运行在进程上下文中. 内核运行在进程上下文中时可以
访问和修改进程的系统数据. 此外, 若内核运行在进程上下文中需要等待资源和设备
时, 系统可以阻塞当前进程.

###参考



###附录


A context switch (also sometimes referred to as a process switch or a task switch) is the switching of the CPU
 (central processing unit) from one process or thread to another.

A process (also sometimes referred to as a task) is an executing (i.e., running) instance of a program. In Linux,
threads are lightweight processes that can run in parallel and share an address space (i.e., a range of memory
 locations) and other resources with their parent processes (i.e., the processes that created them).

A context is the contents of a CPU's registers and program counter at any point in time. A register is a small amount
of very fast memory inside of a CPU (as opposed to the slower RAM main memory outside of the CPU) that is used to
speed the execution of computer programs by providing quick access to commonly used values, generally those in the
midst of a calculation. A program counter is a specialized register that indicates the position of the CPU in its
instruction sequence and which holds either the address of the instruction being executed or the address of the next
 instruction to be executed, depending on the specific system.

Context switching can be described in slightly more detail as the kernel (i.e., the core of the operating system)
performing the following activities with regard to processes (including threads) on the CPU:

(1) suspending the progression of one process and storing the CPU's state (i.e., the context) for that process somewhere in memory,
(2) retrieving the context of the next process from memory and restoring it in the CPU's registers and
(3) returning to the location indicated by the program counter (i.e., returning to the line of code at which the process was interrupted) in order to resume the process.

A context switch is sometimes described as the kernel suspending execution of one process on the CPU and resuming
execution of some other process that had previously been suspended. Although this wording can help clarify the concept,
it can be confusing in itself because a process is, by definition, an executing instance of a program. Thus the wording
suspending progression of a process might be preferable.

Context Switches and Mode Switches

Context switches can occur only in kernel mode. Kernel mode is a privileged mode of the CPU in which only the kernel runs
and which provides access to all memory locations and all other system resources. Other programs, including applications,
initially operate in user mode, but they can run portions of the kernel code via system calls. A system call is a request
in a Unix-like operating system by an active process (i.e., a process currently progressing in the CPU) for a service performed
by the kernel, such as input/output (I/O) or process creation (i.e., creation of a new process). I/O can be defined as any
movement of information to or from the combination of the CPU and main memory (i.e. RAM), that is, communication between
this combination and the computer's users (e.g., via the keyboard or mouse), its storage devices (e.g., disk or tape drives),
or other computers.

The existence of these two modes in Unix-like operating systems means that a similar, but simpler, operation is necessary when
a system call causes the CPU to shift to kernel mode. This is referred to as a mode switch rather than a context switch, because
it does not change the current process.

Context switching is an essential feature of multitasking operating systems. A multitasking operating system is one in which
multiple processes execute on a single CPU seemingly simultaneously and without interfering with each other. This illusion of
concurrency is achieved by means of context switches that are occurring in rapid succession (tens or hundreds of times per second).
These context switches occur as a result of processes voluntarily relinquishing their time in the CPU or as a result of the scheduler
making the switch when a process has used up its CPU time slice.

A context switch can also occur as a result of a hardware interrupt, which is a signal from a hardware device (such as a keyboard,
mouse, modem or system clock) to the kernel that an event (e.g., a key press, mouse movement or arrival of data from a network
connection) has occurred.

Intel 80386 and higher CPUs contain hardware support for context switches. However, most modern operating systems perform software
context switching, which can be used on any CPU, rather than hardware context switching in an attempt to obtain improved performance.
Software context switching was first implemented in Linux for Intel-compatible processors with the 2.4 kernel.

One major advantage claimed for software context switching is that, whereas the hardware mechanism saves almost all of the CPU state,
software can be more selective and save only that portion that actually needs to be saved and reloaded. However, there is some question
as to how important this really is in increasing the efficiency of context switching. Its advocates also claim that software context
switching allows for the possibility of improving the switching code, thereby further enhancing efficiency, and that it permits better
control over the validity of the data that is being loaded.

The Cost of Context Switching

Context switching is generally computationally intensive. That is, it requires considerable processor time, which can be on the order
of nanoseconds for each of the tens or hundreds of switches per second. Thus, context switching represents a substantial cost to the
system in terms of CPU time and can, in fact, be the most costly operation on an operating system.

Consequently, a major focus in the design of operating systems has been to avoid unnecessary context switching to the extent possible.
However, this has not been easy to accomplish in practice. In fact, although the cost of context switching has been declining when
measured in terms of the absolute amount of CPU time consumed, this appears to be due mainly to increases in CPU clock speeds rather
than to improvements in the efficiency of context switching itself.

One of the many advantages claimed for Linux as compared with other operating systems, including some other Unix-like systems, is its
extremely low cost of context switching and mode switching.

更多定义见 http://www.linfo.org/index.html
