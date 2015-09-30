Concurrency

Concurrency is a property of systems in which several computations are executing simultaneously, and potentially interacting with each other，维基百科上这样定义Concurrency。多线程在同一个核内分时执行或者多核下多进程同时执行都可以被称为Concurrency。并发的数学模型已经发展的非常成熟，诸如我们常用的多进程，以及erlang用的Actor模型，golang用的CSP模型等。
Threads, Processes and Green Threads

在linux中，进程和线程的都由task_struct对象来表示，区别在于signal handler，以及线程共享了虚拟内存空间等，尽管这些区别可能会让线程在创建和context switch的时候更加轻松些，但其实看起来没有明显的区别。

当然进程并不只是task_struct对象，它是可执行代码和所操作数据的集合，是一个动态的实体，随着可执行代码的执行而动态变化。进程同时包含了程序计数器，CPU内的各个寄存器以及存放临时变量的程序栈等。所以我们大概可以想象出进程在进行context switch时要进行的操作。

kernel负责对进程（线程）进行调度，系统会把不同的进程运行在不同的CPU上来提升CPU的利用率。当一个进程阻塞时，CPU会被调度执行其他的进程。调度的目的是提高系统的在单位时间内执行的任务吞吐量，降低任务从可执行到执行结束的时间，使进程占用的资源更加合理，系统对于进程和线程的调度是无差别的。

green threads可以理解是用户态线程，它运行在用户空间中。也就是我们在程序层面实现了类似操作系统线程这样的概念，通常这个实现逻辑会简单许多。

green threads可以带来什么？最显而易见的是：在不支持线程的操作系统上，我们依旧可以在语言层面上实现green threads。其次操作系统提供的线程是一个大而全的对象，而对于用户程序来说，诸多功能是冗余的，因此green threads的构造可以更简单，调度策略也更加简单。goroutine可以理解为是一种green threads，它建立在系统线程之上，所以go程序可以并行执行成千上万个goroutine。
Goroutine

green threads的实现通常有三种模型：多个green threads运行在同一个kernel thread上，优点是context switch的速度快，但是只能运行在一个核上；一个green thread对应一个kernel thread，优点是可以利用多核，但是由于绑定关系context swtich会更耗时。

goroutine使用了第三种模型，也就是多个green threads运行在多个kernel threads上，既可以快速的进行context switch又可以很好的利用多核。显然缺点是调度策略会因此变得非常复杂。goroutine的实现使用work stealing算法，定义了MPG三个角色，分别代表kernel threads，processor和goroutine。

P也可以理解为context，我们设置的GOMAXPROCS就是指的P的数量。P负责完成对G和M的调度。P维护了一个deque来存放可执行的G，进行调度时切换当前执行的G，从deque顶部取出下一个G继续执行。当G进行syscall阻塞时，不仅需要切换G，M也需要进行切换来保证P能够继续执行后面的G，当阻塞的G-M对就绪时会被重新调度执行。同时当P维护的所有的G执行结束后，会从别的P的deque的steal一半的G放入自己的deque中执行，这也就是为什么叫做work steal算法。
Non-Blocking I/O

Go提供了同步阻塞的IO模型，但Go底层并不没有使用kernel提供的同步阻塞I/O模型。green threads通常在实现的时候会避免使用同步阻塞的syscall，原因在于当kernel threads阻塞时，需要创建新的线程来保证green threads能够继续执行，代价非常高。所以Go在底层使用非阻塞I/O的模型来避免M阻塞。

当goroutine尝试进行I/O操作而IO未就绪时，syscall返回error，当前执行的G设置为阻塞，而M可以被调度继续执行其他的G，这样就不需要再去创建新的M。当然只是Non-Blocking I/O还不够，Go实现了netpoller来进行I/O的多路复用，在linux下通过epoll实现，epoll提供了同步阻塞的多路复用I/O模型。当G阻塞到I/O时，将fd注册到epoll实例中进行epoll_wait，就绪的fd回调通知给阻塞的G，G重新设置为就绪状态等待调度继续执行，这种实现使得Go在进行高并发的网络通信时变得非常强大，相比于php-fpm的多进程模型，Go Http Server使用很少的线程运行非常多的goroutine，而尽可能的让每一个线程都忙碌起来，这样提高了CPU的利用率，减少了系统进行context switch的开销，从而hold住更大的并发量级。

Done

参考：
https://morsmachine.dk
http://www.tldp.org/LDP/tlk/kernel/processes.html http://man7.org/linux/man-pages/man7/epoll.7.html http://man7.org/tlpi/download/TLPI-04-FileIOTheUniversalIO_Model.pdf

from [Panic blog](http://blog.panic.so/share/2015/09/17/Golang%E5%A6%82%E4%BD%95%E5%B9%B6%E5%8F%91/#rd?sukey=3fed89b912c7bbb210f4f25d56c2a3b040315daef907b54c249bf7c8f5ad2c0318ff1f7669d4d66297fef603a1a39b8c)
