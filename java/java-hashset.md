Problem
While you do have a ConcurrentHashMap class in Java, there is no ConcurrentHashSet.

Solution
You can easily get a ConcurrentHashSet with the following code –

Collections.newSetFromMap(new ConcurrentHashMap<Object,Boolean>())

Notes

    A Set lends itself to implementation via a Map if you think about it. So can actually just use a Map. But that may not fit in well with the context of your use.
    The HashSet class internally uses a HashMap.
    The ConcurrentHashSet obtained via the method inherits pretty much all the concurrency features of the underlying collection.


---------------------------

 Thread safety is a very hot topic for Java programmers right now. But I’ve seen quite a few folks using the rather complex collections from java.util.concurrent when they actually needed just a thread-safe implementation of a Set.

Of course, the HashSet implementation is non-thread-safe:

http://java.sun.com/javase/6/docs/api/java/util/HashSet.html

    Note that this implementation is not synchronized. If multiple threads access a hash set concurrently, and at least one of the threads modifies the set, it must be synchronized externally. This is typically accomplished by synchronizing on some object that naturally encapsulates the set. If no such object exists, the set should be “wrapped” using the Collections.synchronizedSet method. This is best done at creation time, to prevent accidental unsynchronized access to the set:

So getting a thread-safe representation of the HashSet class is pretty easy:

   Set s = Collections.synchronizedSet(new HashSet(...));

This returns a synchronized set backed by the specified set. But be careful: In order to guarantee serial access, it is critical that all access to the backing set is accomplished through the returned set.

A further pitfall is the use of the class’s iterator

    Note that the fail-fast behavior of an iterator cannot be guaranteed as it is, generally speaking, impossible to make any hard guarantees in the presence of unsynchronized concurrent modification. Fail-fast iterators throw ConcurrentModificationException on a best-effort basis. Therefore, it would be wrong to write a program that depended on this exception for its correctness: the fail-fast behavior of iterators should be used only to detect bugs.

So it is imperative that you manually synchronize on the returned set when iterating over it:

  Set s = Collections.synchronizedSet(new HashSet());
      ...
  synchronized(s) {
      Iterator i = s.iterator(); // Must be in the synchronized block
      while (i.hasNext())
          foo(i.next());
  }
 

Failure to follow this advice may result in non-deterministic behavior.

##Reference

http://possiblelossofprecision.net/?p=813
