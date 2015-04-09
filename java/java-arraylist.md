
##ArrayList 元素删除

在这次的项目开发中遇到动态的删除ArrayList中的一些元素，假如我们有如下的一个List:

``` java

    List<Integer> list = new LinkedList<Integer>();
    list.add(4);
    list.add(2);
    list.add(1);
    list.add(1);
    list.add(2);
```

一种错误的方式：

```java

    for(int i = 0, len = list.size(); i < len; i++) {
        if(list.get(i) == 1) {
        list.remove(i);
        }
    }
```

上面这种方式会抛出如下异常：

Exception in thread "main" java.lang.IndexOutOfBoundsException: Index: 3, Size: 3
    at java.util.ArrayList.RangeCheck(Unknown Source)
    at java.util.ArrayList.get(Unknown Source)

因为你删除了元素，但是未改变迭代的下标，这样当迭代到最后一个的时候就会抛异常。

正确的做法是：

```
    for(int i = 0, len = list.size(); i < len; i++) {
        if(list.get(i) == 1){
        list.remove(i);
        len--;
        i--;
        }
    }
```

更好的一个做法

List接口内部实现了Iterator接口，提供开发者一个iterator()得到当前list对象的一个iterator对象。所以我们还有一个更好的做法是：

```java

    Iterator<Integer> iterator = list.iterator();
    while(iterator.hasNext()) {
        int i = iterator.next();
        if(i == 1) {
            iterator.remove();
        }
    }
```

##Avoid ConcurrentModificationException when using an Iterator

Java Collection classes are fail-fast which means that if the Collection will be changed while some thread is traversing over it using iterator, the iterator.next() will throw a ConcurrentModificationException.

This situation can come in case of multithreaded as well as single threaded environment.

Lets explore this scenario with the following example:

```java

	import java.util.*;
	 
	public class IteratorExample {
	 
		public static void main(String args[]){
		    List<String> myList = new ArrayList<String>();
	 
		    myList.add("1");
		    myList.add("2");
		    myList.add("3");
		    myList.add("4");
		    myList.add("5");
	 
		    Iterator<String> it = myList.iterator();
		    while(it.hasNext()){
		        String value = it.next();
		        System.out.println("List Value:"+value);
		        if(value.equals("3")) myList.remove(value);
		    }
	 
		    Map<String,String> myMap = new HashMap<String,String>();
		    myMap.put("1", "1");
		    myMap.put("2", "2");
		    myMap.put("3", "3");
	 
		    Iterator<String> it1 = myMap.keySet().iterator();
		    while(it1.hasNext()){
		        String key = it1.next();
		        System.out.println("Map Value:"+myMap.get(key));
		        if(key.equals("2")){
		            myMap.put("1","4");
		            //myMap.put("4", "4");
		        }
		    }
	 
		}
	}
```

Output is:

	List Value:1
	List Value:2
	List Value:3
	Exception in thread "main" java.util.ConcurrentModificationException
		at java.util.AbstractList$Itr.checkForComodification(AbstractList.java:372)
		at java.util.AbstractList$Itr.next(AbstractList.java:343)
		at com.journaldev.java.IteratorExample.main(IteratorExample.java:27)


From the output stack trace, its clear that the exception is coming when we call iterator next() function. If you are 
wondering how Iterator checks for the modification, its implementation is present in AbstractList class where an int 
variable modCount is defined that provides the number of times list size has been changed. This value is used in every
 next() call to check for any modifications in a function checkForComodification().


Now comment the list part and run the program again.

Output will be:

	Map Value:3
	Map Value:2
	Map Value:4

Since we are updating the existing key value in the myMap, its size has not been changed and we are not getting ConcurrentModificationException. Note that the output may differ in your system because HashMap keyset is not ordered
like list. If you will uncomment the statement where I am adding a new key-value in the HashMap, it will cause ConcurrentModificationException.

###To Avoid ConcurrentModificationException in multi-threaded environment:

* You can convert the list to an array and then iterate on the array. This approach works well for small or medium size 
list but if the list is large then it will affect the performance a lot.
* You can lock the list while iterating by putting it in a synchronized block. This approach is not recommended because 
it will cease the benefits of multithreading.
* If you are using JDK1.5 or higher then you can use ConcurrentHashMap and CopyOnWriteArrayList classes. It is the 
recommended approach.

###To Avoid ConcurrentModificationException in single-threaded environment:

You can use the iterator remove() function to remove the object from underlying collection object. But in this case you can remove the same object and not any other object from the list.

Let us run an example using Concurrent Collection classes:

```java
	package com.journaldev.java;
	 
	import java.util.Iterator;
	import java.util.List;
	import java.util.Map;
	import java.util.concurrent.ConcurrentHashMap;
	import java.util.concurrent.CopyOnWriteArrayList;
	 
	public class ThreadSafeIteratorExample {
	 
		public static void main(String[] args) {
	 
		    List<String> myList = new CopyOnWriteArrayList<String>();
	 
		    myList.add("1");
		    myList.add("2");
		    myList.add("3");
		    myList.add("4");
		    myList.add("5");
	 
		    Iterator<String> it = myList.iterator();
		    while(it.hasNext()){
		        String value = it.next();
		        System.out.println("List Value:"+value);
		        if(value.equals("3")){
		            myList.remove("4");
		            myList.add("6");
		            myList.add("7");
		        }
		    }
		    System.out.println("List Size:"+myList.size());
	 
		    Map<String,String> myMap = 
		         new ConcurrentHashMap<String,String>();
		    myMap.put("1", "1");
		    myMap.put("2", "2");
		    myMap.put("3", "3");
	 
		    Iterator<String> it1 = myMap.keySet().iterator();
		    while(it1.hasNext()){
		        String key = it1.next();
		        System.out.println("Map Value:"+myMap.get(key));
		        if(key.equals("1")){
		            myMap.remove("3");
		            myMap.put("4", "4");
		            myMap.put("5", "5");
		        }
		    }
	 
		    System.out.println("Map Size:"+myMap.size());
		}
	 
	}
```

Output is:

	List Value:1
	List Value:2
	List Value:3
	List Value:4
	List Value:5
	List Size:6
	Map Value:1
	Map Value:null
	Map Value:4
	Map Value:2
	Map Size:4

From the above example its clear that:

1. Concurrent Collection classes can be modified avoiding ConcurrentModificationException.
2. In case of CopyOnWriteArrayList, iterator doesn’t accomodate the changes in the list and works on the original list.
3. In case of ConcurrentHashMap, the behavior is not always the same.

For condition:

```
	if(key.equals("1")){
	    myMap.remove("3");
```

Output is:

	Map Value:1
	Map Value:null
	Map Value:4
	Map Value:2
	Map Size:4

It is taking the new object added with key “4? but not the next added object with key “5?.

Now if I change the condition to

	if(key.equals("3")){
	    myMap.remove("2");

Output is:

	Map Value:1
	Map Value:3
	Map Value:null
	Map Size:4

In this case its not considering the new added objects.

So if you are using ConcurrentHashMap then avoid adding new objects as it can be processed depending on the keyset. 
Note that the same program can print different values in your system because HashMap keyset is not in any order.

Extra Toppings:

```java

	for(int i = 0; i<myList.size(); i++){
		System.out.println(myList.get(i));
		if(myList.get(i).equals("3")){
		    myList.remove(i);
		    i--;
		    myList.add("6");
		}
	}
```

If you are working on single-threaded environment and want your code to take care of the extra added objects in the 
list then you can do so using following code and avoiding iterator.

Note that I am decreasing the counter because I am removing the same object, if you have to remove the next or further
 far object then you don’t need to decrease the counter.

Try it yourself.
