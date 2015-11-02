fio是一个非常灵活的 IO 测试工具, 他可以通过多线程或进程模拟各种 IO 操作

随着块设备的发展, 特别是 SSD 盘的出现, 设备的并行度越来越高. 要想利用好这些设备, 有个诀窍就是提高设备的 iodepth,
一次喂给设备更多的 IO 请求, 让电梯算法和设备有机会来安排合并以及内部并行处理, 提高总体效率.

应用程序使用IO通常有二种方式: 

##准备知识

###硬盘性能指标

顺序读写 （吞吐量，常用单位为MB/s）：文件在硬盘上存储位置是连续的。

适用场景：大文件拷贝（比如视频音乐）。速度即使很高，对数据库性能也没有参考价值。

4K随机读写 （IOPS，常用单位为次）：在硬盘上随机位置读写数据，每次4KB。

适用场景：操作系统运行、软件运行、数据库。


###磁盘

每个硬盘都有一个磁头(相当于银行的柜台)，硬盘的工作方式是：

    收到IO请求，得到地址和数据大小
    移动磁头(寻址)
    找到相应的磁道(寻址)
    读取数据
    传输数据

磁盘的随机IO服务时间:

服务时间 = 寻道时间 + 旋转时间 + 传输时间

对于10000转速的SATA硬盘来说，一般寻道时间是7 ms，旋转时间是3 ms, 64KB的传输时间是 0.8 ms， 则SATA硬盘每秒可以进行随机IO操作是 1000/(7 + 3 + 0.8) = 93，所以我们估算SATA硬盘64KB随机写的IOPS是93。一般的硬盘厂商都会标明顺序读写的MBPS。

我们在列出IOPS时，需要说明IO大小，寻址空间，读写模式，顺序/随机，队列深度。我们一般常用的IO大小是4KB，这是因为文件系统常用的块大小是4KB。


###同步 IO 和异步 IO

同步的IO一次只能发出一个IO请求, 等待内核完成才返回, 这样对于单个线程 iodepth 总是小于 1, 但是可以通过多个线程并发执行来解决,
通常我们会用 16-32 个线程同时工作把 iodepth 塞满.

异步的话就是用类似 libaio 这样的 linux native aio 一次提交一批, 然后等待一批的完成, 减少交互的次数, 会更有效率.


###IO 队列深度

IO 队列深度通常对不同的设备很敏感, 那么如何用 fio 来探测出合理的值呢? 在 fio 的帮助文档里是如何解释 iodepth 相关参数的

    iodepth=int
    Number of I/O units to keep in flight against the file. Note that increasing iodepth beyond 1 will not affect synchronous ioengines
    (except for small degress when verify_async is in use). Even async engines my impose OS restrictions causing the desired depth not to be
    achieved. This may happen on Linux when using libaio and not setting direct=1, since buffered IO is not async on that OS. Keep an eye on
    the IO depth distribution in the fio output to verify that the achieved depth is as expected. Default: 1.

    iodepth_batch=int
    Number of I/Os to submit at once. Default: iodepth.

    iodepth_batch_complete=int
    This defines how many pieces of IO to retrieve at once. It defaults to 1 which
    means that we’ll ask for a minimum of 1 IO in the retrieval process from the kernel. The IO retrieval will go on until we hit the limit
    set by iodepth_low. If this variable is set to 0, then fio will always check for completed events before queuing more IO. This helps
    reduce IO latency, at the cost of more retrieval system calls.

    iodepth_low=int
    Low watermark indicating when to start filling the queue again. Default: iodepth.

    direct=bool
    If true, use non-buffered I/O (usually O_DIRECT). Default: false.

    fsync=int
    How many I/Os to perform before issuing an fsync(2) of dirty data. If 0, don’t sync. Default: 0. 

这几个参数在 libaio 的引擎下的作用, 会用 iodepth 值来调用 io_setup 准备一个可以一次提交 iodepth 个 IO 的上下文,
同时申请一个 IO 请求队列用于保持 IO.  在压测进行的时候, 系统会生成特定的 IO 请求, 往 IO 请求队列里面扔, 当队列
里面的 IO 数量达到 iodepth\_batch 值的时候, 就调用 io\_submit 批次提交请求, 然后开始调用 io_getevents 开始收割已
经完成的 IO.  每次收割多少呢? 由于收割的时候, 超时时间设置为 0, 所以有多少已完成就算多少, 最多可以收割
iodepth_batch_complete 值个. 随着收割, IO 队列里面的IO数就少了, 那么需要补充新的 IO.  什么时候补充呢? 当 IO 数目
降到 iodepth\_low 值的时候, 就重新填充, 保证 OS 可以看到至少 iodepth_low 数目的 IO 在电梯口排队着.


由上分析，为了测出磁盘的性能, 就要加大硬盘队列深度, 让硬盘不断工作，减少硬盘的空闲时间即

    加大队列深度 -> 提高利用率 -> 获得IOPS和MBPS峰值 -> 注意响应时间在可接受的范围内

增加队列深度的办法有很多

* 使用异步IO，同时发起多个IO请求，相当于队列中有多个IO请求
* 多线程发起同步IO请求，相当于队列中有多个IO请求
* 增大应用IO大小，到达底层之后，会变成多个IO请求，相当于队列中有多个IO请求 队列深度增加了。


##安装

wget http://brick.kernel.dk/snaps/fio-2.2.10.tar.gz
tar -zxvf fio-2.2.10.tar.gz
cd fio-2.2.10
make; sudo make install

##使用

fio分顺序读, 随机读, 顺序写, 随机写, 混合随机读写模式.

filename=/dev/sdb1   #测试文件名称，通常选择需要测试的盘的data目录, 可以通过冒号分割同时指定多个文件，如filename=/dev/sda:/dev/sdb。
directory            #设置filename的路径前缀。在后面的基准测试中，采用这种方式来指定设备。
name                 #指定job的名字，在命令行中表示新启动一个job。
direct=1             #bool类型，如果设置成true (1)，表示不使用io buffer。
rw=randwrite         #I/O模式，随机读写，顺序读写等等。
rw=randrw            #测试随机写和读的I/O
bs=16k               #单次io的块文件大小, 在direct方式下块大小必须是512的倍数，其他方式是4096的倍数。
bsrange=512-2048     #同上，提定数据块的大小范围
size=5G              #测试文件大小为5g，以每次4k的io进行测试
numjobs=30           #测试线程为30个
runtime=1000         #测试时间1000秒，如果不写则一直将5g文件分4k每次写完为止
ioengine=psync       #I/O引擎，现在fio支持19种ioengine。默认值是sync同步阻塞I/O，libaio是Linux的native异步I/O。
rwmixwrite=30        #在混合读写的模式下，写占30%
group_reporting      #关于显示结果的，汇总每个进程的信息, 当同时指定了numjobs了时，输出结果按组显示。
time_based　　　　　　　　　　　#如果在runtime指定的时间还没到时文件就被读写完成，将继续重复知道runtime时间结束。
lockmem=1G           #只使用1g内存进行测试
zero_buffers         #用0初始化系统buffer
nrfiles=8            #每个进程生成文件的数量

##范例

//顺序读
fio -filename=/dev/sda -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest

//顺序写
fio -filename=/dev/sda -direct=1 -iodepth 1 -thread -rw=write -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest

//随机读
fio -filename=/dev/sda -direct=1 -iodepth 1 -thread -rw=randread -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest

//随机写
fio -filename=/dev/sda -direct=1 -iodepth 1 -thread -rw=randwrite -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest

//混合随机读写
fio -filename=/dev/sda -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=100 -group_reporting -name=mytest -ioscheduler=noop

//根据配置文件
fio fio.conf
#复制下面的配置内容，将directory=/path/to/test修改为你测试硬盘挂载目录的地址，并另存为fio.conf

```
	[global]
	ioengine=libaio
	direct=1
	thread=1
	norandommap=1
	randrepeat=0
	runtime=60
	ramp_time=6
	size=1g
	directory=/path/to/test

	[read4k-rand]
	stonewall
	group_reporting
	bs=4k
	rw=randread
	numjobs=8
	iodepth=32

	[read64k-seq]
	stonewall
	group_reporting
	bs=64k
	rw=read
	numjobs=4
	iodepth=8

	[write4k-rand]
	stonewall
	group_reporting
	bs=4k
	rw=randwrite
	numjobs=2
	iodepth=4

	[write64k-seq]
	stonewall
	group_reporting
	bs=64k
	rw=write
	numjobs=2
	iodepth=4
```

NOTE:

	


##测试准备

性能测试建议直接通过写裸盘的方式进行测试, 会得到较为真实的数据. 但直接测试裸盘会破坏文件系统结构, 导致数据丢失,
请在测试前确认磁盘中数据已备份.

fio任务配置里面有几个点需要非常注意：

1. libaio工作的时候需要文件direct方式打开。
2. 块大小必须是扇区(512字节)的倍数。
3. userspace_reap提高异步IO收割的速度。
4. ramp_time的作用是减少日志对高速IO的影响。
5. 只要开了direct,fsync就不会发生。
6. 测试过程用 iostat -dx 1　关注磁盘利用率 %util
7. 当遇到问题不要忘了加参数 --debug=io


###测试案例

队列深度(iodepth) 影响
寻址空间(size) 的影响



##参考

http://blog.yufeng.info/archives/2104
http://wsgzao.github.io/post/fio/



 


fio可以通过配置文件来配置压力测试的方式, 可以用选项 --debug=io来检测fio是否工作

[root@vmforDB05 tmp]# cat fio_test
[global] 
bsrange=512-2048 
ioengine=libaio 
userspace_reap 
rw=randrw 
rwmixwrite=20 
time_based 
runtime=180 
direct=1 
group_reporting 
randrepeat=0 
norandommap 
ramp_time=6 
iodepth=16 
iodepth_batch=8 
iodepth_low=8 
iodepth_batch_complete=8 
exitall 
[test] 
filename=/dev/mapper/cachedev 
numjobs=1

常用参数说明
bsrange=512-2048  //数据块的大小范围, 从512bytes到2048 bytes
ioengine=libaio        //指定io引擎
userspace_reap      //配合libaio, 提高异步io的收割速度
rw=randrw                //混合随机对写io, 默认读写比例5:5
rwmixwrite=20         //在混合读写的模式下, 写占20%
time_based             //在runtime压力测试周期内, 如果规定数据量测试完, 要重复测试 
runtime=180            //在180秒, 压力测试将终止
direct=1                    //设置非缓冲io
group_reporting      //如果设置了多任务参数numjobs, 用每组报告代替每job报告
randrepeat=0         //设置产生的随机数是不可重复的
norandommap 
ramp_time=6 
iodepth=16 
iodepth_batch=8 
iodepth_low=8 
iodepth_batch_complete=8 
exitall                                                     //一个job完成, 就停止所有的
filename=/dev/mapper/cachedev    //压力测试的文件名
numjobs=1                                         //job的默认数量, 也就是并发数, 默认是1
size=200G                                          //这job总共的io大小
refill_buffers                                      //每次提交后都重复填充io buffer
overwrite=1                                       //设置文件可覆盖
sync=1                                              //设置异步io
fsync=1                                             //一个io就同步数据
invalidate=1                                   //开始io之前就失效buffer-cache
directory=/your_dir                        // fielname参数值的前缀
thinktime=600                              //在发布io前等待600秒
thinktime_spin=200    //消费cpu的时间, thinktime的剩余时间sleep
thinktime_blocks=2    //在thinktime之前发布的block数量

bssplit=4k/30:8k/40:16k/30            //随机读4k文件占30%、8k占40%、16k占30%
rwmixread=70                                                         //读占70% 


##附录

###磁盘阵列吞吐量与IOPS两大瓶颈分析


####吞吐量

吞吐量主要取决于阵列的构架, 光纤通道的大小(现在阵列一般都是光纤阵列, 至于 SCSI 这样的 SSA 阵列, 我们不讨论)以及硬盘的个数. 
阵列的构架与每个阵列不同而不同, 他们也都存在内部带宽(类似于pc的系统总线), 不过一般情况下, 内部带宽都设计的很充足, 不是瓶颈的所在. 

光纤通道的影响还是比较大的, 如数据仓库环境中, 对数据的流量要求很大, 而一块 2Gb 的光纤卡, 所能支撑的最大流量应当是
2Gb/8(小B) = 250MB/s(大B) 的实际流量, 当 4 块光纤卡才能达到1GB/s的实际流量, 所以数据仓库环境可以考虑换4Gb的光纤卡. 


最后说一下硬盘的限制, 这里是最重要的, 当前面的瓶颈不再存在的时候, 就要看硬盘的个数了, 我下面列一下不同的硬盘所能支撑的流量大小: 

	　　10 K rpm    15 K rpm     ATA
	　　10MB/s       13MB/s      8MB/s

那么, 假定一个阵列有 120 块 15K rpm 的光纤硬盘, 那么硬盘上最大的可以支撑的流量为 120*13=1560MB/s, 如果是2Gb的光纤卡, 可能需要
6 块才能够, 而 4Gb 的光纤卡, 3-4块就够了. 

####IOPS

决定IOPS的主要取决与阵列的算法, cache命中率, 以及磁盘个数. 阵列的算法因为不同的阵列不同而不同, 如我们最近遇到在 hds usp上面, 
可能因为ldev(lun)存在队列或者资源限制, 而单个 ldev 的 iops 就上不去, 所以, 在使用这个存储之前, 有必要了解这个存储的一些算法规
则与限制.

cache 的命中率取决于数据的分布, cache size 的大小, 数据访问的规则, 以及 cache 的算法, 如果完整的讨论下来, 这里将变得很复杂, 可
以有一天好讨论了. 我这里只强调一个 cache 的命中率, 如果一个阵列, 读 cache 的命中率越高越好, 一般表示它可以支持更多的 IOPS, 为什
么这么说呢? 这个就与我们下面要讨论的硬盘 IOPS 有关系了.

硬盘的限制, 每个物理硬盘能处理的 IOPS 是有限制的, 如

	　　10 K rpm 	15 K rpm 	ATA
	　　100 		150 		50

同样, 如果一个阵列有 120 块 15K rpm 的光纤硬盘, 那么, 它能撑的最大 IOPS 为 120*150=18000, 这个为硬件限制的理论值, 如果超过这个值,
硬盘的响应可能会变的非常缓慢而不能正常提供业务.

在 RAID5 与 RAID10 上, 读 IOPS 没有差别, 但是, 相同的业务写 IOPS, 最终落在磁盘上的 iops 是有差别的, 而我们评估的却正是磁盘的 IOPS,
如果达到了磁盘的限制, 性能肯定是上不去了.

那我们假定一个 case, 业务的 IOPS 是 10000, 读 cache 命中率是 30%, 读 IOPS 为 60%, 写 IOPS 为 40%, 磁盘个数为 120, 那么分别计算在
RAID5 与 RAID10 的情况下, 每个磁盘的 IOPS 为多少.

raid5:

单块盘

    IOPS = (10000*(1-0.3)*0.6 + 4 * (10000*0.4))/120 = (4200 + 16000)/120 = 168 

这里的 10000*(1-0.3)*0.6 表示是读的 IOPS,
比例是 0.6, 除掉 cache 命中, 实际只有 4200 个 IOPS

而 4 * (10000*0.4) 表示写的 IOPS, 因为每一个写, 在 RAID5 中, 实际发生了 4 个 IO, 所以写的 IOPS 为 16000 个

为了考虑 RAID5 在写操作的时候, 那2个读操作也可能发生命中, 所以更精确的计算为:

单块盘

    IOPS = (10000*(1-0.3)*0.6 + 2 * (10000*0.4)*(1-0.3) + 2 * (10000*0.4))/120 = (4200 + 5600 + 8000)/120 = 148

计算出来单个盘的iops为148个, 基本达到磁盘极限

raid10

单块盘的

    IOPS = (10000*(1-0.3)*0.6 + 2 * (10000*0.4))/120 = (4200 + 8000)/120 = 102

可以看到, 因为 RAID10 对于一个写操作, 只发生 2 次 IO, 所以, 同样的压力, 同样的磁盘, 每个盘的 IOPS 只有 102 个,
还远远低于磁盘的极限 IOPS.

在一个实际的 case 中, 一个恢复压力很大的 standby(这里主要是写, 而且是小io的写), 采用了 RAID5 的方案, 发现性能很差,
通过分析, 每个磁盘的 IOPS 在高峰时期, 快达到 200 了, 导致响应速度巨慢无比. 后来改造成 RAID10, 就避免了这个性能问题,
每个磁盘的 IOPS 降到100左右.
