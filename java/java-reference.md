Im not going to talk about each reference class available within the java.lang.ref package as it is already very well explained here. Let us take a look at the following code snippet which I wrote to understand the basic operation of a WeakReference.

```
import java.lang.ref.WeakReference;  
import java.util.HashMap;  
import java.util.Map;  
  
public class ReferencesTest {  
  
 private WeakReference<Map<Integer, String>> myMap;  
  
 public static void main(String[] args) {  
  new ReferencesTest().doFunction();  
 }  
  
 private void doFunction() {  
  
  Map<Integer, String> map = new HashMap<Integer, String>();  
  myMap = new WeakReference<Map<Integer, String>>(map);  
  
  map = null;  
  int i = 0;  
  while (true) {  
   if (myMap != null && myMap.get() != null) {  
    myMap.get().put(i++, "test" + i);  
  
    System.out.println("im still working!!!!" + Runtime.getRuntime().freeMemory());  
   } else {  
  
    System.out  
      .println("*******im free*******" + Runtime.getRuntime().freeMemory());  
  
   }  
  
  }  
 }  
}  
```

First I have defined a weak reference instance variable to which I assign an instance of a HashMap initialized within the doFunction() method. Then data is input to the map via the weak reference instance and not directly through the concrete instance of the hashmap we created. We check for the map being null due to the fact of the way WeakReferences work.

During the execution of the program, a weak reference will be the first to be garbage collected if there are no soft or strong references binding to it. So if memory is considerably low, or when and if the garbage collector deems appropriate, the weak reference is garbage collected and this is why I have included the else statement within my code to show the occurrence of that situation. Run this by setting minimum –Xms and –Xmx to understand how it works since otherwise you will have to wait a longer period to get an out of memory exception. And then change the WeakReference implementation to a SoftReference implementation and see that the program actually crashes after a few iterations. This is due to the fact that SoftReferences only gurantee to clean up memory just before a OutOfMemory error occurs. But with the WeakReference, the program continues to function without halting because it is almost always eligible for garbage collection and we can reinitialize the cache and continue to repopulate our cache.

The good thing about weak reference is that in my opinion it is one of the best ways to implement an in-memory cache which we usually implement ourselves when we need to keep data that do not consistently change but frequently accessed in memory and when the cost of going for a fully-fledged caching implementation like the JBoss cache or EHCache is too much. Quite often I have implemented caching solutions and have also seen production code similar to the following code snippet;

```
import java.util.HashMap;  
import java.util.Map;  
  
public class CacheTest {  
  
 private Map<String, Object> myAwesomeCache = new HashMap<String, Object>(100);  
   
 public Object getData(String id){  
    
  Object objToReturn = null;  
    
  if(myAwesomeCache.containsKey(id)){  
   objToReturn = myAwesomeCache.get(id);  
  }else{  
   // retrieve from the database and populate the in memory cache map  
  }  
    
  return objToReturn;  
 }  
}  
```

This is just a very basic level implementation to put out the idea across that we sometimes do use Maps to construct in-memory caching implementations. The fact that we have to note is that though there is nothing intrinsically wrong with this implementation, in an instance where your application is running low on memory, it would be a ideal if the garbage collector could remove this from memory to free up some for the other processes that need it. But since this map is a strong reference, there is no way the garbage collector can mark this reference as eligible for collection. A better solution would be to change the caching implementation from HashMap to a WeakHashMap.

The Javadoc specifies the following about the WeakHashMap;

         “A hashtable-based Map implementation with weak keys. An entry in a WeakHashMap will   automatically be removed when its key is no longer in ordinary use. More precisely, the presence of a mapping for a given key will not prevent the key from being discarded by the garbage collector, that is, made finalizable, finalized, and then reclaimed. When a key has been discarded its entry is effectively removed from the map, so this class behaves somewhat differently from other Map implementations.”

So in retrospect, I believe whenever you are in need of an in-memory caching implementation and memory is of utmost importance to you, using a WeakHashMap would be beneficial.

That concludes my findings on the Reference package and I invite you all to share your experience in this regard which is highly appreciated.


Using a WeakHashMap as a cache is not a good idea. A FIFO data structure is usually a better idea, as you usually want items to stay in the cache for some time regardless of whether there are or not strong references to them outside the cache.

--------------------------------------------------------------------------


Some time ago I was interviewing candidates for a Senior Java Engineer position. Among the many questions I asked was "What can you tell me about weak references?" I wasn't expecting a detailed technical treatise on the subject. I would probably have been satisfied with "Umm... don't they have something to do with garbage collection?" I was instead surprised to find that out of twenty-odd engineers, all of whom had at least five years of Java experience and good qualifications, only two of them even knew that weak references existed, and only one of those two had actual useful knowledge about them. I even explained a bit about them, to see if I got an "Oh yeah" from anybody -- nope. I'm not sure why this knowledge is (evidently) uncommon, as weak references are a massively useful feature which have been around since Java 1.2 was released, over seven years ago.

Now, I'm not suggesting you need to be a weak reference expert to qualify as a decent Java engineer. But I humbly submit that you should at least know what they are -- otherwise how will you know when you should be using them? Since they seem to be a little-known feature, here is a brief overview of what weak references are, how to use them, and when to use them.

##Strong references

First I need to start with a refresher on strong references. A strong reference is an ordinary Java reference, the kind you use every day. For example, the code:


    StringBuffer buffer = new StringBuffer();

creates a new StringBuffer() and stores a strong reference to it in the variable buffer. Yes, yes, this is kiddie stuff, but bear with me. The important part about strong references -- the part that makes them "strong" -- is how they interact with the garbage collector. Specifically, if an object is reachable via a chain of strong references (strongly reachable), it is not eligible for garbage collection. As you don't want the garbage collector destroying objects you're working on, this is normally exactly what you want.

When strong references are too strong

It's not uncommon for an application to use classes that it can't reasonably extend. The class might simply be marked final, or it could be something more complicated, such as an interface returned by a factory method backed by an unknown (and possibly even unknowable) number of concrete implementations. Suppose you have to use a class Widget and, for whatever reason, it isn't possible or practical to extend Widget to add new functionality.

What happens when you need to keep track of extra information about the object? In this case, suppose we find ourselves needing to keep track of each Widget's serial number, but the Widget class doesn't actually have a serial number property -- and because Widget isn't extensible, we can't add one. No problem at all, that's what HashMaps are for:


    serialNumberMap.put(widget, widgetSerialNumber);

This might look okay on the surface, but the strong reference to widget will almost certainly cause problems. We have to know (with 100% certainty) when a particular Widget's serial number is no longer needed, so we can remove its entry from the map. Otherwise we're going to have a memory leak (if we don't remove Widgets when we should) or we're going to inexplicably find ourselves missing serial numbers (if we remove Widgets that we're still using). If these problems sound familiar, they should: they are exactly the problems that users of non-garbage-collected languages face when trying to manage memory, and we're not supposed to have to worry about this in a more civilized language like Java.

Another common problem with strong references is caching, particular with very large structures like images. Suppose you have an application which has to work with user-supplied images, like the web site design tool I work on. Naturally you want to cache these images, because loading them from disk is very expensive and you want to avoid the possibility of having two copies of the (potentially gigantic) image in memory at once.

Because an image cache is supposed to prevent us from reloading images when we don't absolutely need to, you will quickly realize that the cache should always contain a reference to any image which is already in memory. With ordinary strong references, though, that reference itself will force the image to remain in memory, which requires you (just as above) to somehow determine when the image is no longer needed in memory and remove it from the cache, so that it becomes eligible for garbage collection. Once again you are forced to duplicate the behavior of the garbage collector and manually determine whether or not an object should be in memory.

##Weak references

A weak reference, simply put, is a reference that isn't strong enough to force an object to remain in memory. Weak references allow you to leverage the garbage collector's ability to determine reachability for you, so you don't have to do it yourself. You create a weak reference like this:


    WeakReference<Widget> weakWidget = new WeakReference<Widget>(widget);

and then elsewhere in the code you can use weakWidget.get() to get the actual Widget object. Of course the weak reference isn't strong enough to prevent garbage collection, so you may find (if there are no strong references to the widget) that weakWidget.get() suddenly starts returning null.

To solve the "widget serial number" problem above, the easiest thing to do is use the built-in WeakHashMap class. WeakHashMap works exactly like HashMap, except that the keys (not the values!) are referred to using weak references. If a WeakHashMap key becomes garbage, its entry is removed automatically. This avoids the pitfalls I described and requires no changes other than the switch from HashMap to a WeakHashMap. If you're following the standard convention of referring to your maps via the Map interface, no other code needs to even be aware of the change.

##Reference queues

Once a WeakReference starts returning null, the object it pointed to has become garbage and the WeakReference object is pretty much useless. This generally means that some sort of cleanup is required; WeakHashMap, for example, has to remove such defunct entries to avoid holding onto an ever-increasing number of dead WeakReferences.

The ReferenceQueue class makes it easy to keep track of dead references. If you pass a ReferenceQueue into a weak reference's constructor, the reference object will be automatically inserted into the reference queue when the object to which it pointed becomes garbage. You can then, at some regular interval, process the ReferenceQueue and perform whatever cleanup is needed for dead references.

##Different degrees of weakness

Up to this point I've just been referring to "weak references", but there are actually four different degrees of reference strength: strong, soft, weak, and phantom, in order from strongest to weakest. We've already discussed strong and weak references, so let's take a look at the other two.

###Soft references

A soft reference is exactly like a weak reference, except that it is less eager to throw away the object to which it refers. An object which is only weakly reachable (the strongest references to it are WeakReferences) will be discarded at the next garbage collection cycle, but an object which is softly reachable will generally stick around for a while.
SoftReferences aren't required to behave any differently than WeakReferences, but in practice softly reachable objects are generally retained as long as memory is in plentiful supply. This makes them an excellent foundation for a cache, such as the image cache described above, since you can let the garbage collector worry about both how reachable the objects are (a strongly reachable object will never be removed from the cache) and how badly it needs the memory they are consuming.

###Phantom references

A phantom reference is quite different than either SoftReference or WeakReference. Its grip on its object is so tenuous that you can't even retrieve the object -- its get() method always returns null. The only use for such a reference is keeping track of when it gets enqueued into a ReferenceQueue, as at that point you know the object to which it pointed is dead. How is that different from WeakReference, though?

The difference is in exactly when the enqueuing happens. WeakReferences are enqueued as soon as the object to which they point becomes weakly reachable. This is before finalization or garbage collection has actually happened; in theory the object could even be "resurrected" by an unorthodox finalize() method, but the WeakReference would remain dead. PhantomReferences are enqueued only when the object is physically removed from memory, and the get() method always returns null specifically to prevent you from being able to "resurrect" an almost-dead object.

What good are PhantomReferences? I'm only aware of two serious cases for them: first, they allow you to determine exactly when an object was removed from memory. They are in fact the only way to determine that. This isn't generally that useful, but might come in handy in certain very specific circumstances like manipulating large images: if you know for sure that an image should be garbage collected, you can wait until it actually is before attempting to load the next image, and therefore make the dreaded OutOfMemoryError less likely.

Second, PhantomReferences avoid a fundamental problem with finalization: finalize() methods can "resurrect" objects by creating new strong references to them. So what, you say? Well, the problem is that an object which overrides finalize() must now be determined to be garbage in at least two separate garbage collection cycles in order to be collected. When the first cycle determines that it is garbage, it becomes eligible for finalization. Because of the (slim, but unfortunately real) possibility that the object was "resurrected" during finalization, the garbage collector has to run again before the object can actually be removed. And because finalization might not have happened in a timely fashion, an arbitrary number of garbage collection cycles might have happened while the object was waiting for finalization. This can mean serious delays in actually cleaning up garbage objects, and is why you can get OutOfMemoryErrors even when most of the heap is garbage.

With PhantomReference, this situation is impossible -- when a PhantomReference is enqueued, there is absolutely no way to get a pointer to the now-dead object (which is good, because it isn't in memory any longer). Because PhantomReference cannot be used to resurrect an object, the object can be instantly cleaned up during the first garbage collection cycle in which it is found to be phantomly reachable. You can then dispose whatever resources you need to at your convenience.

Arguably, the finalize() method should never have been provided in the first place. PhantomReferences are definitely safer and more efficient to use, and eliminating finalize() would have made parts of the VM considerably simpler. But, they're also more work to implement, so I confess to still using finalize() most of the time. The good news is that at least you have a choice.

##Conclusion

I'm sure some of you are grumbling by now, as I'm talking about an API which is nearly a decade old and haven't said anything which hasn't been said before. While that's certainly true, in my experience many Java programmers really don't know very much (if anything) about weak references, and I felt that a refresher course was needed. Hopefully you at least learned a little something from this review.
Related Topics >>

#Example 

##Strong references

Strong references never get collected

```
    package org.neverfear.leaks;
 
    /*
     * URL: http://neverfear.org/blog/view/150/Java_References
     * Author: doug@neverfear.org
     */
    public class ClassStrong {
     
        public static class Referred {
            protected void finalize() {
                System.out.println("Good bye cruel world");
            }
        }
     
        public static void collect() throws InterruptedException {
            System.out.println("Suggesting collection");
            System.gc();
            System.out.println("Sleeping");
            Thread.sleep(5000);
        }
     
        public static void main(String args[]) throws InterruptedException {
            System.out.println("Creating strong references");
     
            // This is now a strong reference.
            // The object will only be collected if all references to it disappear.
            Referred strong = new Referred();
     
            // Attempt to claim a suggested reference.
            ClassStrong.collect();
     
            System.out.println("Removing reference");
            // The object may now be collected.
            strong = null;
            ClassStrong.collect();
     
            System.out.println("Done");
        }
     
    }
```

##Soft references

Soft references only get collected if the JVM absolutely needs the memory. This makes them excellent for implementing object cache's.


```
package org.neverfear.leaks;
 
import java.lang.ref.SoftReference;
import java.util.ArrayList;
import java.util.List;
 
/*
 * A sample for Detecting and locating memory leaks in Java
 * URL: http://neverfear.org/blog/view/150/Java_References
 * Author: doug@neverfear.org
 */
public class ClassSoft {
 
    public static class Referred {
        protected void finalize() {
            System.out.println("Good bye cruel world");
        }
    }
 
    public static void collect() throws InterruptedException {
        System.out.println("Suggesting collection");
        System.gc();
        System.out.println("Sleeping");
        Thread.sleep(5000);
    }
 
    public static void main(String args[]) throws InterruptedException {
        System.out.println("Creating soft references");
 
        // This is now a soft reference.
        // The object will be collected only if no strong references exist and the JVM really needs the memory.
        Referred strong = new Referred();
        SoftReference<Referred> soft = new SoftReference<Referred>(strong);
 
        // Attempt to claim a suggested reference.
        ClassSoft.collect();
 
        System.out.println("Removing reference");
        // The object may but highly likely wont be collected.
        strong = null;
        ClassSoft.collect();
 
        System.out.println("Consuming heap");
        try
        {
            // Create lots of objects on the heap
            List<ClassSoft> heap = new ArrayList<ClassSoft>(100000);
            while(true) {
                heap.add(new ClassSoft());
            }
        }
        catch (OutOfMemoryError e) {
            // The soft object should have been collected before this
            System.out.println("Out of memory error raised");
        }
 
        System.out.println("Done");
    }
 
}
```

##Weak references

Weak references only get collected if no other object references it except the weak references. This makes them perfect for keeping meta data about a particular object for the life time of the object.

```
package org.neverfear.leaks;
 
import java.lang.ref.WeakReference;
import java.util.ArrayList;
import java.util.List;
 
/*
 * A sample for Detecting and locating memory leaks in Java
 * URL: http://neverfear.org/blog/view/150/Java_References
 * Author: doug@neverfear.org
 */
public class ClassWeak {
 
    public static class Referred {
        protected void finalize() {
            System.out.println("Good bye cruel world");
        }
    }
 
    public static void collect() throws InterruptedException {
        System.out.println("Suggesting collection");
        System.gc();
        System.out.println("Sleeping");
        Thread.sleep(5000);
    }
 
    public static void main(String args[]) throws InterruptedException {
        System.out.println("Creating weak references");
 
        // This is now a weak reference.
        // The object will be collected only if no strong references.
        Referred strong = new Referred();
        WeakReference<Referred> weak = new WeakReference<Referred>(strong);
 
        // Attempt to claim a suggested reference.
        ClassWeak.collect();
 
        System.out.println("Removing reference");
        // The object may be collected.
        strong = null;
        ClassWeak.collect();
 
        System.out.println("Done");
    }
 
}
```

##Phantom references

Phantom references are objects that can be collected whenever the collector likes. The object reference 
is appended to a ReferenceQueue and you can use this to clean up after a collection. This is an 
alternative to the finalize() method and is slightly safer because the finalize() method may ressurect 
the object by creating new strong references. The PhantomReference however cleans up the object and 
enqueues the reference object to a ReferenceQueue that a class can use for clean up.

```
package org.neverfear.leaks;
 
import java.lang.ref.PhantomReference;
import java.lang.ref.Reference;
import java.lang.ref.ReferenceQueue;
import java.util.HashMap;
import java.util.Map;
 
/*
 * A sample for Detecting and locating memory leaks in Java
 * URL: http://neverfear.org/blog/view/150/Java_References
 * Author: doug@neverfear.org
 */
public class ClassPhantom {
 
    public static class Referred {
        // Note that if there is a finalize() method PhantomReference's don't get appended to a ReferenceQueue
    }
 
    public static void collect() throws InterruptedException {
        System.out.println("Suggesting collection");
        System.gc();
        System.out.println("Sleeping");
        Thread.sleep(5000);
    }
 
    public static void main(String args[]) throws InterruptedException {
        System.out.println("Creating phantom references");
 
        // The reference itself will be appended to the dead queue for clean up.
        ReferenceQueue dead = new ReferenceQueue(); 
 
        // This map is just a sample we might use to locate resources we need to clean up.
        Map<Reference,String> cleanUpMap = new HashMap<Reference,String>();
 
        // This is now a phantom reference.
        // The object will be collected only if no strong references.
        Referred strong = new Referred();
 
        PhantomReference<Referred> phantom = new PhantomReference(strong, dead);
        cleanUpMap.put(phantom, "You need to clean up some resources, such as me!");
 
        strong = null;
 
        // The object may now be collected
        ClassPhantom.collect();
 
        // Check for 
        Reference reference = dead.poll();
        if (reference != null) {
            System.out.println(cleanUpMap.remove(reference));
        }
        System.out.println("Done");
    }
 
}
```

##ReferenceQueue


You saw me use the reference queue class in the previous example. A ReferenceQueue instance can be supplied as an argument to SoftReference, WeakReference or PhantomReference. When an object is collected the reference instance itself will be enqueued to the supplied ReferenceQueue. This allows you to perform clean up operations on the object. This is useful if you are implementing any container classes that you want to contain a Soft, Weak or Phantom reference and some associated data because you can get notified via the ReferenceQueue which Reference was just collected.


##WeakHashMap class

There is also a convience WeakHashMap that wraps all keys by a weak reference. Allowing you to easily store meta data against an object and have the map entry including the meta data removed and collected when the original object itself is unreachable.

```
package org.neverfear.leaks;
 
import java.util.Map;
import java.util.WeakHashMap;
 
/*
 * A sample for Detecting and locating memory leaks in Java
 * URL: http://neverfear.org/blog/view/150/Java_References
 * Author: doug@neverfear.org
 */
public class ClassWeakHashMap {
 
    public static class Referred {
        protected void finalize() {
            System.out.println("Good bye cruel world");
        }
    }
 
    public static void collect() throws InterruptedException {
        System.out.println("Suggesting collection");
        System.gc();
        System.out.println("Sleeping");
        Thread.sleep(5000);
    }
 
    public static void main(String args[]) throws InterruptedException {
        System.out.println("Creating weak references");
 
        // This is now a weak reference.
        // The object will be collected only if no strong references.
        Referred strong = new Referred();
        Map<Referred,String> metadata = new WeakHashMap<Referred,String>();
        metadata.put(strong, "WeakHashMap's make my world go around");
 
        // Attempt to claim a suggested reference.
        ClassWeakHashMap.collect();
        System.out.println("Still has metadata entry? " + (metadata.size() == 1));
        System.out.println("Removing reference");
        // The object may be collected.
        strong = null;
        ClassWeakHashMap.collect();
 
        System.out.println("Still has metadata entry? " + (metadata.size() == 1));
 
        System.out.println("Done");
    }
 
}
```

https://weblogs.java.net/blog/2006/05/04/understanding-weak-references 