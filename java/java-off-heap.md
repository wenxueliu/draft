The on-heap store refers to objects that will be present in the Java heap (and also subject to GC). On the other hand, the off-heap store refers to (serialized) objects that are managed by EHCache, but stored outside the heap (and also not subject to GC). As the off-heap store continues to be managed in memory, it is slightly slower than the on-heap store, but still faster than the disk store.

EHCache's off-heap storage takes your regular object off the heap, serializes it, and stores it as bytes in a chunk of memory that EHCache manages. It's like storing it to disk but it's still in RAM. The objects are not directly usable in this state, they have to be deserialized first. Also not subject to garbage collection.


BigMemory (the off-heap store) is to be used to avoid the overhead of GC on a heap that is several Megabytes or Gigabytes large. BigMemory uses the memory address space of the JVM process, via direct ByteBuffers that are not subject to GC unlike other native Java objects.

###What is Heap-Offloading ?

Usually all non-temporary objects you allocate are managed by java's garbage collector. Although the VM does a decent job doing garbage collection, at a certain point the VM has to do a so called 'Full GC'. A full GC involves scanning the complete allocated Heap, which means GC pauses/slowdowns are proportional to an applications heap size. So don't trust any person telling you 'Memory is Cheap'. In java memory consumtion hurts performance. Additionally you may get notable pauses using heap sizes > 1 Gb. This can be nasty if you have any near-real-time stuff going on, in a cluster or grid a java process might get unresponsive and get dropped from the cluster.

However todays server applications (frequently built on top of bloaty frameworks ;-) ) easily require heaps far beyond 4Gb.

One solution to these memory requirements, is to 'offload' parts of the objects to the non-java heap (directly allocated from the OS). Fortunately java.nio provides classes to directly allocate/read and write 'unmanaged' chunks of memory (even memory mapped files).

So one can allocate large amounts of 'unmanaged' memory and use this to save objects there. In order to save arbitrary objects into unmanaged memory, the most viable solution is the use of Serialization. This means the application serializes objects into the offheap memory, later on the object can be read using deserialization.

The heap size managed by the java VM can be kept small, so GC pauses are in the millis, everybody is happy, job done.

It is clear, that the performance of such an off heap buffer depends mostly on the performance of the serialization implementation. Good news: for some reason FST-serialization is pretty fast :-).

####Sample usage scenarios:

    Session cache in a server application. Use a memory mapped file to store gigabytes of (inactive) user sessions. Once the user logs into your application, you can quickly access user-related data without having to deal with a database.
    Caching of computational results (queries, html pages, ..) (only applicable if computation is slower than deserializing the result object ofc).
    very simple and fast persistance using memory mapped files


Edit: For some scenarios one might choose more sophisticated Garbage Collection algorithms such as ConcurrentMarkAndSweep or G1 to support larger heaps (but this also has its limits beyond 16GB hepas). There is also a commercial java virtual machine with improved 'pasueless' GC (Azul) available.


###Off heap memory usage

Using off heap memory and using object pools both help reduce GC pauses, this is their only similarity.  Object pools are good for short lived mutable objects, expensive to create objects and long live immutable objects where there is a lot of duplication.  Medium lived mutable objects, or complex objects are more likely to be better left to the GC to handle.  However, medium to long lived mutable objects suffer in a number of ways which off heap memory solves.

###Off heap memory provides;

    Scalability to large memory sizes e.g. over 1 TB and larger than main memory.
    Notional impact on GC pause times.
    Sharing between processes, reducing duplication between JVMs, and making it easier to split JVMs.
    Persistence for faster restarts or replying of production data in test.

The use of off heap memory gives you more options in terms of how you design your system.  The most important improvement is not performance, but determinism. Off heap and testing

Off heap memory can have challenges but also come with a lot of benefits.  Where you see the biggest gain and compares with other solutions introduced to achieve scalability.  Off heap is likely to be simpler and much faster than using partitioned/sharded on heap caches, messaging solutions, or out of process databases.  By being faster, you may find that some of the tricks you need to do to give you the performance you need are no longer required. e.g. off heap solutions can support synchronous writes to the OS, instead of having to perform them asynchronously with the risk of data loss. The biggest gain however, can be your startup time, giving you a production system which restarts much faster. e.g. mapping in a 1 TB data set can take 10 milli-seconds, and ease of reproducibility in test by replaying every event in order you get the same behaviour every time.  This allows you to produce quality systems you can rely on.

###cassandra 




###Reference

http://stackoverflow.com/questions/6091615/difference-between-on-heap-and-off-heap
