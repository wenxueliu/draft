
##Writes are expensive

Datastore is transactional: writes require disk access, Disk access means disk seeks

Rule of thumb: 10ms for a disk seek

Simple math: 1s / 10ms = 100 seeks/sec maximum

Depends on:
* The size and shape of your data
* Doing work in batches (batch puts and gets)


##Reads are cheap

Reads do not need to be transactional, just consistent Data is read from disk once, then it's easily cached
All subsequent reads come straight from memory

Rule of thumb: 250usec for 1MB of data from memory

Simple math: 1s / 250usec = 4GB/sec maximum

* For a 1MB entity, that's 4000 fetches/sec


##Numbers Miscellaneous


###CPU

* L1 cache reference            0.5 ns
* Branch mispredict             5 ns
* L2 cache reference            7 ns
* Mutex lock/unlock             25 ns
* Main memory reference         100 ns
* Compress 1K bytes with Zippy  10,000 ns

* L1 cache sequential access        4 cycle
* L1 cache in Page Random access    4 cycle
* L1 cache in Full Random access    4 cycle
* L2 cache sequential access        11 cycle
* L2 cache in Page Random access    11 cycle
* L2 cache in Full Random access    11 cycle
* L3 cache sequential access        14 cycle
* L3 cache in Page Random access    18 cycle
* L2 cache in Full Random access    38 cycle
* Main Memory                       167 cycle

###network

* Send 2K bytes over 1 Gbps network     20,000 ns
* Round trip within same datacenter     500,000 ns
* Read 1 MB sequentially from network   10,000,000 ns
* Send packet CA->Netherlands->CA       150,000,000 ns
* 异地机房之间网络来回 30-100ms

##IO

* Disk seek 10,000,000 ns
* Read 1 MB sequentially from memory 250,000 ns
* Read 1 MB sequentially from disk 30,000,000 ns
* Writes are 40 times more expensive than reads.

* 从 sata 磁盘顺序读取1M数据 20ms
* SSD访问延迟 0.1-0.2ms
* 内存IOPS 千万级
* SSD盘IOPS 35000

* 7200转SATA磁盘IOPS 75-100
* 10000转SATA磁盘IOPS 125-150
* 10000转SAS磁盘IOPS 140
* 15000转SAS磁盘IOPS 175-210
* Fusion-io SSD盘 140000 Read IOPS, 135000 Write IOPS 

* SATA1.0 理论数据传输 150MB/s
* SATA2.0 理论传输速度 300MB/s
* SATA3.0 理论传输速度 750MB/s

* 金士顿SSD 读取 535MB/秒
* 金士顿SSD 写入 500MB/秒

* 磁盘平均存取时间 = 平均旋转延迟搜索时间(潜伏时间) + 平均寻道时间
* SATA磁盘平均寻道时间 10ms
* 7200转HDD的平均潜伏时间4.17ms
* 10000转HDD的平均潜伏时间3.00ms
* 15000转HDD的平均潜伏时间2.00ms

例如一个NVMe SSD的写延迟20μs，而上下文切换大约占用5μs，在延迟占比达25%，

JBOD configuration with six 7200rpm SATA RAID-5 array
linear writes : 600MB/sec
random writes : 100k/sec

##数据库

* MySQL性能评测本身需要的环境：cpu、disk、engine、表结构和大小、线程数、各参数设置：
* 参考（pc）：单线程百万级别表qps：330-370
* 参考（pc）：64线程百万级别表qps：700-900
* 参考（pc）：多线程百万级别表tps：400-800
* 淘宝双十一单机qps峰值：6.5w
* MySQL 5.7只读InnoDB Memcached plugin版单机qps：100w

##可用性

* 99.999%的可用性：每年的宕机时间不超过5分钟
* 99.99%的可用性：每年的宕机时间不超过52.5分钟
* 99.9%的可用性：每年的宕机时间不超过8.75小时
* MySQL Cluster可用性：99.999%

##The Lessons

Global shared data is expensive. This is a fundamental limitation of distributed systems. The lock contention
in shared heavily written objects kills performance as transactions become serialized and slow.

Architect for scaling writes.

Optimize for low write contention.

Optimize wide. Make writes as parallel as you can.


##Sharded Counters

The naive counter implementation is to lock-read-increment-write. This is fine if there a low number of writes.
But if there are frequent updates there's high contention. Given the the number of writes that can be made per
second is so limited, a high write load serializes and slows down the whole process.

The solution is to shard counters. This means:

* Create N counters in parallel.
* Pick a shard to increment transactionally at random for each item counted.
* To get the real current count sum up all the sharded counters.
* Contention is reduced by 1/N. Writes have been optimized because they have been spread over the different shards.
A bottleneck around shared state has been removed.

This approach seems counter-intuitive because we are used to a counter being a single incrementable variable. Reads
are cheap so we replace having a single easily read counter with having to make multiple reads to recover the actual
count. Frequently updated shared variables are expensive so we shard and parallelize those writes.

With a centralized database letting the database be the source of sequence numbers is doable. But to scale writes you
need to partition and once you partition it becomes difficult to keep any shared state like counters. You might argue
that so common a feature should be provided by GAE and I would agree 100 percent, but it's the ideas that count (pun
intended).

##Paging Through Comments

How can comments be stored such that they can be paged through in roughly the order they were entered?

Under a high write load situation this is a surprisingly hard question to answer. Obviously what you want is just a counter.
As a comment is made you get a sequence number and that's the order comments are displayed. But as we saw in the last
section shared state like a single counter won't scale in high write environments.

A sharded counter won't work in this situation either because summing the shared counters isn't transactional. There's
no way to guarantee each comment will get back the sequence number it allocated so we could have duplicates.

Searches in BigTable return data in alphabetical order. So what is needed for a key is something unique and alphabetical
so when searching through comments you can go forward and backward using only keys.

A lot of paging algorithms use counts. Give me records 1-20, 21-30, etc. SQL makes this easy, but it doesn't work for
BigTable. BigTable knows how to get things by keys so you must make keys that return data in the proper order.

In the grand old tradition of making unique keys we just keep appending stuff until it becomes unique. The suggested key
for GAE is: time stamp + user ID + user comment ID.

Ordering by date is obvious. The good thing is getting a time stamp is a local decision, it doesn't rely on writes and is
scalable. The problem is timestamps are not unique, especially with a lot of users.

So we can add the user name to the key to distinguish it from all other comments made at the same time. We already have
the user name so this too is a cheap call.

Theoretically even time stamps for a single user aren't sufficient. What we need then is a sequence number for each user's comments.

And this is where the GAE solution turns into something totally unexpected. Our goal is to remove write contention so we
want to parallelize writes. And we have a lot available storage so we don't have to worry about that.

With these forces in mind, the idea is to create a counter per user. When a user adds a comment it's added to a user's comment
list and a sequence number is allocated. Comments are added in a transactional context on a per user basis using Entity Groups.
So each comment add is guaranteed to be unique because updates in an Entity Group are serialized.

The resulting key is guaranteed unique and sorts properly in alphabetical order. When paging a query is made across entity groups
using the ID index. The results will be in the correct order. Paging is a matter of getting the previous and next keys in the query
for the current page. These keys can then be used to move through index.

I certainly would have never thought of this approach. The idea of keeping per user comment indexes is out there. But it cleverly
follows the rules of scaling in a distributed system. Writes and reads are done in parallel and that's the goal. Write contention
is removed.

##参考

[number everyone should know](http://highscalability.com/blog/2009/2/18/numbers-everyone-should-know.html)
