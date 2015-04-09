	   HashSet<String> hashSet = new HashSet<String>();

		long start = System.currentTimeMillis();
		for (int i = 0; i < 900000; i++) {
		    hashSet.add(String.valueOf(i));
		}

		System.out.println("Insert HashSet Time: " + (System.currentTimeMillis() - start));


		ArrayList<String> arrayList = new ArrayList<String>();

		start = System.currentTimeMillis();

		for (int i = 0; i < 900000; i++) {
		    arrayList.add(String.valueOf(i));
		}
		System.out.println("Insert ArrayList Time: " + (System.currentTimeMillis() - start));

result:

	Insert HashSet Time: 978
	Insert ArrayList Time: 287




Exact performance characteristics of datastructures and algorithms are highly machine- and implementation-specific. However, it doesn't seem surprising to me that ArrayList inserts would be faster than HashSet inserts by a constant factor. To insert into an ArrayList, you just need to set a value at a particular index in an array. To insert into a hash set, you need to compute a hashcode for the inserted item and map that to an array index, check that index and possibly perform some action based on what you find, and finally insert into the array. Furthermore the HashSet will have worse memory locality so you'll get cache misses more often.

There's also the question of array resizing, which both data structures will need to do, but both data structures will need to resize at about the same rate (and hash table resizing is probably more expensive by a constant factor, too, due to rehashing).

Both algorithms are constant (expected) time, but there's a lot more stuff to do with a hash table than an array list. So it's not surprising that it would be slower by a constant factor. (Again, the exact difference is highly dependent on machine and implementation.)

HashSet will outperform ArrayList on search i.e: get().
But on insert they have comparable performance. Actually ArrayList is even faster if you are within array limits (no resize needed) and the hash function is not good

Actually, you are getting the right results. Also, as pointed out in the above answer, these are different types of data-structures. Comparing them would be like comparing the speed of a bike with a car. I think the time for inserting in a HashSet must be more than that of insertion in an ArrayList because HashSet doesn't allow duplicate keys. So I assume that before insertion there must be some sort of checking for duplicate keys before insertion and how to handle them which makes them somewhat slower as compared to ArrayList.



HashSet is backed by hashtable. If you know about hashtable, you would know that there is a hash function. also collision handling(if there was collision) when you add new element in it. Well hashSet doesn't handle collision, just overwrite the old value if hash are same. However if capacity reached, it need to resize, and possible re-hash. it would be very slow.

ArrayList just append the object to the end of the list. if size reached, it does resize.

