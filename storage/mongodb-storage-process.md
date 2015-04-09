##数据存到哪儿了？

在启动 mongod 命令的时候，会去mongodb的配置文件中读取 dbpath参数。然后执行 mongod daemon，将数据存入指定的文件夹。

也可以指定在运行 mongod 的时候指定
    
    mongd --dbpath /you_path

mongod 这个命令还有很多重要的参数，参考[这里](http://docs.mongodb.org/manual/tutorial/manage-mongodb-processes/)及相关链接




##数据流


<img src="{{ IMAGE_PATH }}/mongdb/mongodb-storage-map.png" alt="mmap" title="map" width=600/>

这幅图不仅仅适用于 NoSQL 数据库，适用于绝大数操作系统和数据库交互过程

### Memory-mapped Files

mongodb 存储数据的文件叫 extents , 标准大小是 2G。按照要求创建这样的文件，随着数据库内容的增加，为了效率的考虑，会预分配整个文件。这个文件与硬盘上的几个连续的块相对应。通过预分配，可以减少磁盘碎片，提高存取效率。

### 数据到虚拟内存

对 mongodb 性能非常大影响的因素是它将内存管理的任务委托给底层的操作系统。全部的 extents 通过 mmap原语映射到内存。如上图中文件映射到virtual memory 的红线部分。

虚拟内存可以认为是一个真实内存的进程私有（process-private）。它使得进程与一个抽象的内存进行交互，而不必纠结于 RAM 中具体的地址。从进程的角度来说，内存就是一个以 bytes 为单位的数组，从0开始一直到 2^64（64为机器）。

mmap 取其中的一段内存分配了 mongod 的 extents。这样，mongod 执行读写的时候就好像在内存中一样。

### 虚拟内存到物理内存

虚拟内存到物理内存的映射是由操作系统来做。关于这其中的机理大意是虚拟内存会尽可能找到对应的物理内存，如果没有足够的物理内存，就会将暂时不用的数据先放到交互分区，留出空间给新的内存请求，具体参考<<深入理解计算机系统>>第10章。

##数据到磁盘过程分析

知道了数据存在哪里，那么是怎么存的呢？

//TODO：阅读源码
1. 客户端请求
2. 服务端解析
3. mmap 将请求的数据写入内存
4. flush 时机




##监控工具

vmstat
mongostat
mongotop
htop
参考 [这里](http://docs.mongodb.org/manual/administration/monitoring/)




##参考
[这里](http://www.polyspot.com/en/blog/2012/understanding-mongodb-storage/)


  [1]: http://www.polyspot.com/en/blog/wp-content/uploads/2012/07/mongodb-memory.png
