fio是一个非常灵活的io测试工具，他可以通过多线程或进程模拟各种io操作

随着块设备的发展，特别是SSD盘的出现，设备的并行度越来越高。要想利用好这些设备，有个诀窍就是提高设备的iodepth, 一次喂给设备更多的IO请求，让电梯算法和设备有机会来安排合并以及内部并行处理，提高总体效率。

应用程序使用IO通常有二种方式：同步和异步。 同步的IO一次只能发出一个IO请求，等待内核完成才返回，这样对于单个线程iodepth总是小于1，但是可以通过多个线程并发执行来解决，通常我们会用16-32个线程同时工作把iodepth塞满。 异步的话就是用类似libaio这样的linux native aio一次提交一批，然后等待一批的完成，减少交互的次数，会更有效率。

io队列深度通常对不同的设备很敏感，那么如何用fio来探测出合理的值呢？在fio的帮助文档里是如何解释iodepth相关参数的

iodepth=int
iodepth_batch=int
iodepth_batch_complete=int
iodepth_low=int
fsync=int
direct=bool

这几个参数在libaio的引擎下的作用，会用iodepth值来调用io_setup准备一个可以一次提交iodepth个IO的上下文，同时申请一个io请求队列用于保持IO。 在压测进行的时候，系统会生成特定的IO请求，往io请求队列里面扔，当队列里面的IO数量达到iodepth_batch值的时候，就调用io_submit批次提交请求，然后开始调用io_getevents开始收割已经完成的IO。 每次收割多少呢？由于收割的时候，超时时间设置为0，所以有多少已完成就算多少，最多可以收割iodepth_batch_complete值个。随着收割，IO队列里面的IO数就少了，那么需要补充新的IO。 什么时候补充呢？当IO数目降到iodepth_low值的时候，就重新填充，保证OS可以看到至少iodepth_low数目的io在电梯口排队着。

 

下载
[root@vmforDB05 tmp]# wget ftp://ftp.univie.ac.at/systems/linux/dag/redhat/el5/en/x86_64/dag/RPMS/fio-2.0.6-1.el5.rf.x86_64.rpm

安装
[root@vmforDB05 tmp]# rpm -ivh fio-2.0.6-1.el5.rf.x86_64.rpm

 

测试下
[root@vmforDB05 ~]# fio -filename=/dev/mapper/cachedev  -direct=1 -rw=randread -bs=8k -size 1G -numjobs=8 -runtime=30 -group_reporting -name=file
file: (g=0): rw=randread, bs=8K-8K/8K-8K, ioengine=sync, iodepth=1
...
file: (g=0): rw=randread, bs=8K-8K/8K-8K, ioengine=sync, iodepth=1
fio 2.0.6
Starting 8 processes
Jobs: 1 (f=1): [____r___] [13.2% done] [200K/0K /s] [24 /0  iops] [eta 03m:30s]
file: (groupid=0, jobs=8): err= 0: pid=22052
  read : io=4632.0KB, bw=156907 B/s, iops=19 , runt= 30229msec
    clat (usec): min=168 , max=1585.8K, avg=409213.69, stdev=234820.76
     lat (usec): min=169 , max=1585.8K, avg=409214.35, stdev=234820.77
    clat percentiles (msec):
     |  1.00th=[   28],  5.00th=[   61], 10.00th=[  114], 20.00th=[  200],
     | 30.00th=[  273], 40.00th=[  334], 50.00th=[  392], 60.00th=[  445],
     | 70.00th=[  510], 80.00th=[  578], 90.00th=[  717], 95.00th=[  816],
     | 99.00th=[ 1057], 99.50th=[ 1221], 99.90th=[ 1582], 99.95th=[ 1582],
     | 99.99th=[ 1582]
    bw (KB/s)  : min=    4, max=  202, per=12.72%, avg=19.46, stdev=13.99
    lat (usec) : 250=0.17%
    lat (msec) : 50=4.15%, 100=4.84%, 250=16.58%, 500=42.14%, 750=24.18%
    lat (msec) : 1000=6.56%, 2000=1.38%
  cpu          : usr=0.03%, sys=0.09%, ctx=1102, majf=0, minf=244
  IO depths    : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0%
     submit    : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     complete  : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0%
     issued    : total=r=579/w=0/d=0, short=r=0/w=0/d=0

Run status group 0 (all jobs):
   READ: io=4632KB, aggrb=153KB/s, minb=156KB/s, maxb=156KB/s, mint=30229msec, maxt=30229msec

Disk stats (read/write):
    dm-0: ios=578/0, merge=0/0, ticks=169684/0, in_queue=169733, util=98.95%, aggrios=0/0, aggrmerge=0/0, aggrticks=0/0, aggrin_queue=0, aggrutil=0.00%
  loop0: ios=0/0, merge=0/0, ticks=0/0, in_queue=0, util=0.00%
  loop1: ios=0/0, merge=0/0, ticks=0/0, in_queue=0, util=0.00%
[root@vmforDB05 ~]#

 


fio可以通过配置文件来配置压力测试的方式，可以用选项 --debug=io来检测fio是否工作

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
bsrange=512-2048  //数据块的大小范围，从512bytes到2048 bytes
ioengine=libaio        //指定io引擎
userspace_reap      //配合libaio，提高异步io的收割速度
rw=randrw                //混合随机对写io，默认读写比例5:5
rwmixwrite=20         //在混合读写的模式下，写占20%
time_based             //在runtime压力测试周期内，如果规定数据量测试完，要重复测试 
runtime=180            //在180秒，压力测试将终止
direct=1                    //设置非缓冲io
group_reporting      //如果设置了多任务参数numjobs，用每组报告代替每job报告
randrepeat=0         //设置产生的随机数是不可重复的
norandommap 
ramp_time=6 
iodepth=16 
iodepth_batch=8 
iodepth_low=8 
iodepth_batch_complete=8 
exitall                                                     //一个job完成，就停止所有的
filename=/dev/mapper/cachedev    //压力测试的文件名
numjobs=1                                         //job的默认数量，也就是并发数，默认是1
size=200G                                          //这job总共的io大小
refill_buffers                                      //每次提交后都重复填充io buffer
overwrite=1                                       //设置文件可覆盖
sync=1                                              //设置异步io
fsync=1                                             //一个io就同步数据
invalidate=1                                   //开始io之前就失效buffer-cache
directory=/your_dir                        // fielname参数值的前缀
thinktime=600                              //在发布io前等待600秒
thinktime_spin=200    //消费cpu的时间，thinktime的剩余时间sleep
thinktime_blocks=2    //在thinktime之前发布的block数量

bssplit=4k/30:8k/40:16k/30            //随机读4k文件占30%、8k占40%、16k占30%
rwmixread=70                                                         //读占70% 



FIO是测试IOPS的非常好的工具，用来对硬件进行压力测试和验证，支持13种不同的I/O引擎，
包括:sync,mmap, libaio, posixaio, SG v3, splice, null, network, syslet, guasi, solarisaio 等等。 
fio 官网地址：http://freshmeat.net/projects/fio/ 

一，FIO安装 
wget http://brick.kernel.dk/snaps/fio-2.0.7.tar.gz 
yum install libaio-devel 
tar -zxvf fio-2.0.7.tar.gz 
cd fio-2.0.7 
make 
make install 

二，随机读测试： 
随机读： 
fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=randread -ioengine=psync -bs=16k -size=200G 
-numjobs=10 -runtime=1000 -group_reporting -name=mytest 

说明： 
filename=/dev/sdb1 测试文件名称，通常选择需要测试的盘的data目录。 
direct=1 测试过程绕过机器自带的buffer。使测试结果更真实。 
rw=randwrite 测试随机写的I/O 
rw=randrw 测试随机写和读的I/O 
bs=16k 单次io的块文件大小为16k 
bsrange=512-2048 同上，提定数据块的大小范围 
size=5g 本次的测试文件大小为5g，以每次4k的io进行测试。 
numjobs=30 本次的测试线程为30. 
runtime=1000 测试时间为1000秒，如果不写则一直将5g文件分4k每次写完为止。 
ioengine=psync io引擎使用pync方式 
rwmixwrite=30 在混合读写的模式下，写占30% 
group_reporting 关于显示结果的，汇总每个进程的信息。 
此外 
lockmem=1g 只使用1g内存进行测试。 
zero_buffers 用0初始化系统buffer。 
nrfiles=8 每个进程生成文件的数量。 
顺序读： 
fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=read -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest 
随机写： 
fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=randwrite -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest 
顺序写： 
fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=write -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=1000 -group_reporting -name=mytest 
混合随机读写： 
fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=16k -size=200G -numjobs=30 -runtime=100 -group_reporting -name=mytest -ioscheduler=noop 

三，实际测试范例： 
[root@localhost ~]# fio -filename=/dev/sdb1 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=16k -size=200G -numjobs=30 
-runtime=100 -group_reporting -name=mytest1 

mytest1: (g=0): rw=randrw, bs=16K-16K/16K-16K, ioengine=psync, iodepth=1 
... 
mytest1: (g=0): rw=randrw, bs=16K-16K/16K-16K, ioengine=psync, iodepth=1 
fio 2.0.7 
Starting 30 threads 
Jobs: 1 (f=1): [________________m_____________] [3.5% done] [6935K/3116K /s] [423 /190 iops] [eta 48m:20s] s] 
mytest1: (groupid=0, jobs=30): err= 0: pid=23802 
read : io=1853.4MB, bw=18967KB/s, iops=1185 , runt=100058msec 
clat (usec): min=60 , max=871116 , avg=25227.91, stdev=31653.46 
lat (usec): min=60 , max=871117 , avg=25228.08, stdev=31653.46 
clat percentiles (msec): 
| 1.00th=[ 3], 5.00th=[ 5], 10.00th=[ 6], 20.00th=[ 8], 
| 30.00th=[ 10], 40.00th=[ 12], 50.00th=[ 15], 60.00th=[ 19], 
| 70.00th=[ 26], 80.00th=[ 37], 90.00th=[ 57], 95.00th=[ 79], 
| 99.00th=[ 151], 99.50th=[ 202], 99.90th=[ 338], 99.95th=[ 383], 
| 99.99th=[ 523] 
bw (KB/s) : min= 26, max= 1944, per=3.36%, avg=636.84, stdev=189.15 
write: io=803600KB, bw=8031.4KB/s, iops=501 , runt=100058msec 
clat (usec): min=52 , max=9302 , avg=146.25, stdev=299.17 
lat (usec): min=52 , max=9303 , avg=147.19, stdev=299.17 
clat percentiles (usec): 
| 1.00th=[ 62], 5.00th=[ 65], 10.00th=[ 68], 20.00th=[ 74], 
| 30.00th=[ 84], 40.00th=[ 87], 50.00th=[ 89], 60.00th=[ 90], 
| 70.00th=[ 92], 80.00th=[ 97], 90.00th=[ 120], 95.00th=[ 370], 
| 99.00th=[ 1688], 99.50th=[ 2128], 99.90th=[ 3088], 99.95th=[ 3696], 
| 99.99th=[ 5216] 
bw (KB/s) : min= 20, max= 1117, per=3.37%, avg=270.27, stdev=133.27 
lat (usec) : 100=24.32%, 250=3.83%, 500=0.33%, 750=0.28%, 1000=0.27% 
lat (msec) : 2=0.64%, 4=3.08%, 10=20.67%, 20=19.90%, 50=17.91% 
lat (msec) : 100=6.87%, 250=1.70%, 500=0.19%, 750=0.01%, 1000=0.01% 
cpu : usr=1.70%, sys=2.41%, ctx=5237835, majf=0, minf=6344162 
IO depths : 1=100.0%, 2=0.0%, 4=0.0%, 8=0.0%, 16=0.0%, 32=0.0%, >=64=0.0% 
submit : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0% 
complete : 0=0.0%, 4=100.0%, 8=0.0%, 16=0.0%, 32=0.0%, 64=0.0%, >=64=0.0% 
issued : total=r=118612/w=50225/d=0, short=r=0/w=0/d=0 
Run status group 0 (all jobs): 
READ: io=1853.4MB, aggrb=18966KB/s, minb=18966KB/s, maxb=18966KB/s, mint=100058msec, maxt=100058msec 
WRITE: io=803600KB, aggrb=8031KB/s, minb=8031KB/s, maxb=8031KB/s, mint=100058msec, maxt=100058msec 
Disk stats (read/write): 
sdb: ios=118610/50224, merge=0/0, ticks=2991317/6860, in_queue=2998169, util=99.77% 
主要查看以上红色字体部分的iops(read/write) 



**磁盘阵列吞吐量与IOPS两大瓶颈分析**

1、吞吐量

　　吞吐量主要取决于阵列的构架，光纤通道的大小(现在阵列一般都是光纤阵列，至于SCSI这样的SSA阵列，我们不讨论)以及硬盘的个数。阵列的构架与每个阵列不同而不同，他们也都存在内部带宽(类似于pc的系统总线)，不过一般情况下，内部带宽都设计的很充足，不是瓶颈的所在。

　　光纤通道的影响还是比较大的，如数据仓库环境中，对数据的流量要求很大，而一块2Gb的光纤卡，所77能支撑的最大流量应当是2Gb/8(小B)=250MB/s(大B)的实际流量，当4块光纤卡才能达到1GB/s的实际流量，所以数据仓库环境可以考虑换4Gb的光纤卡。

　　最后说一下硬盘的限制，这里是最重要的，当前面的瓶颈不再存在的时候，就要看硬盘的个数了，我下面列一下不同的硬盘所能支撑的流量大小：

　　10 K rpm 15 K rpm ATA

　　——— ——— ———

　　10M/s 13M/s 8M/s

　　那么，假定一个阵列有120块15K rpm的光纤硬盘，那么硬盘上最大的可以支撑的流量为120*13=1560MB/s，如果是2Gb的光纤卡，可能需要6块才能够，而4Gb的光纤卡，3-4块就够了。

2、IOPS

　　决定IOPS的主要取决与阵列的算法，cache命中率，以及磁盘个数。阵列的算法因为不同的阵列不同而不同，如我们最近遇到在hds usp上面，可能因为ldev(lun)存在队列或者资源限制，而单个ldev的iops就上不去，所以，在使用这个存储之前，有必要了解这个存储的一些算法规则与限制。

　　cache的命中率取决于数据的分布，cache size的大小，数据访问的规则，以及cache的算法，如果完整的讨论下来，这里将变得很复杂，可以有一天好讨论了。我这里只强调一个cache的命中率，如果一个阵列，读cache的命中率越高越好，一般表示它可以支持更多的IOPS，为什么这么说呢?这个就与我们下面要讨论的硬盘IOPS有关系了。

　　硬盘的限制，每个物理硬盘能处理的IOPS是有限制的，如

　　10 K rpm 15 K rpm ATA

　　——— ——— ———

　　100 150 50

　　同样，如果一个阵列有120块15K rpm的光纤硬盘，那么，它能撑的最大IOPS为120*150=18000，这个为硬件限制的理论值，如果超过这个值，硬盘的响应可能会变的非常缓慢而不能正常提供业务。

　　在raid5与raid10上，读iops没有差别，但是，相同的业务写iops，最终落在磁盘上的iops是有差别的，而我们评估的却正是磁盘的IOPS，如果达到了磁盘的限制，性能肯定是上不去了。

　　那我们假定一个case，业务的iops是10000，读cache命中率是30%，读iops为60%，写iops为40%，磁盘个数为120，那么分别计算在raid5与raid10的情况下，每个磁盘的iops为多少。

　　raid5:

　　单块盘的iops = (10000*(1-0.3)*0.6 + 4 * (10000*0.4))/120

　　= (4200 + 16000)/120

　　= 168

　　这里的10000*(1-0.3)*0.6表示是读的iops，比例是0.6，除掉cache命中，实际只有4200个iops

　　而4 * (10000*0.4) 表示写的iops，因为每一个写，在raid5中，实际发生了4个io，所以写的iops为16000个

　　为了考虑raid5在写操作的时候，那2个读操作也可能发生命中，所以更精确的计算为：

　　单块盘的iops = (10000*(1-0.3)*0.6 + 2 * (10000*0.4)*(1-0.3) + 2 * (10000*0.4))/120

　　= (4200 + 5600 + 8000)/120

　　= 148

　　计算出来单个盘的iops为148个，基本达到磁盘极限

　　raid10

　　单块盘的iops = (10000*(1-0.3)*0.6 + 2 * (10000*0.4))/120

　　= (4200 + 8000)/120

　　= 102

　　可以看到，因为raid10对于一个写操作，只发生2次io，所以，同样的压力，同样的磁盘，每个盘的iops只有102个，还远远低于磁盘的极限iops。

　　在一个实际的case中，一个恢复压力很大的standby(这里主要是写，而且是小io的写)，采用了raid5的方案，发现性能很差，通过分析，每个磁盘的iops在高峰时期，快达到200了，导致响应速度巨慢无比。后来改造成raid10，就避免了这个性能问题，每个磁盘的iops降到100左右。


