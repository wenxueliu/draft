
free命令可以查看系统的内存状况，包括服务器的总内存，已经使用的内存和剩下未被使用的内存，以及缓冲和缓存各自占用的内存情况。

free -m
             total       used       free     shared    buffers     cached
Mem:           994        787        207          0        121        227
-/+ buffers/cache:        437        557
Swap:            0          0          0

要完全理解上面3行数据，先搞明白buffer和cache是什么。

    buffer：缓冲区，将数据缓冲下来，解决速度慢和快的交接问题；速度快的需要通过缓冲区将数据一点一点传给速度慢的区域。例如：从内存中将数据往硬盘中写入，并不是直接写入，而是缓冲到一定大小之后刷入硬盘中。

            A buffer is something that has yet to be "written" to disk.

    cache：缓存，实现数据的重复使用，速度慢的设备需要通过缓存将经常要用到的数据缓存起来，缓存下来的数据可以提供高速的传输速度给速度快的设备。例如：将硬盘中的数据读取出来放在内存的缓存区中，这样以后再次访问同一个资源，速度会快很多。

            A cache is something that has been "read" from the disk and stored for later use.

buffer是用于存放将要输出到disk（块设备）的数据，而cache是存放从disk上读出的数据。二者都是为提高IO性能而设计的。

现在开始分析free命令输出的每一行代表的含义：

第一行：Mem

总共的内存994(total) = 787(used)+207(free)，used表示系统已经被使用的内存，它包括应用程序使用的内存，以及用于缓冲和缓存的内存总和。

第二行：-/+ buffers/cache，分两步理解

    -buffers/cache：437(used) = 787(used) - 121(buffers) - 227(cached)，437表示除去缓冲和缓存消耗的内存外，应用程序实际消耗的内存是437M。
    +buffers/cache：557(free) = 207(free)+121(buffers)+cached(227)，557表示系统可用的内存有557M，因为如果遇到内存告急的情况时，buffer和cache所占的内存还是可以用来给应用程序使用。

第三行：Swap

看到很多文章直接说不解释了，但这里我要解释一下，Swap表示交换分区，也就是我们通常所说的虚拟内存。就可以把一部分磁盘空间当做内存使用，这部分空间叫做虚拟内存，当系统内存不足时，系统会把那些还驻留在内存中但是当前没有运行的程序暂时放到虚拟内存中去。


##参考

http://foofish.net/blog/98/linux-command-free
