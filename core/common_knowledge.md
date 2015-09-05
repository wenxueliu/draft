
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

###network

* Send 2K bytes over 1 Gbps network     20,000 ns
* Round trip within same datacenter     500,000 ns
* Read 1 MB sequentially from network   10,000,000 ns
* Send packet CA->Netherlands->CA       150,000,000 ns

##IO
* Disk seek 10,000,000 ns
* Read 1 MB sequentially from memory 250,000 ns
* Read 1 MB sequentially from disk 30,000,000 ns
* Writes are 40 times more expensive than reads.


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
