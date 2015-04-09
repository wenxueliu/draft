clone from [here](http://java.dzone.com/articles/how-design-good-regular-api)


People have strong opinions on how to design a good API. Consequently, there are lots of pages and books in the web, explaining how to do it. This article will focus on a particular aspect of good APIs: Regularity. Regularity is what happens when you follow the “[Principle of Least Astonishment](http://en.wikipedia.org/wiki/Principle_of_least_astonishment)“. This principle holds true no matter what kinds of personal taste and style you would like to put into your API, otherwise. It is thus one of the most important features of a good API.

The following are a couple of things to keep in mind when designing a “regular” API:

###Rule #1: Establish strong terms

If your API grows, there will be repetitive use of the same terms, over and over again. For instance, some actions will be come in several flavours resulting in various classes / types / methods, that differ only subtly in behaviour. The fact that they’re similar should be reflected by their names. Names should use strong terms. Take JDBC for instance. No matter how you execute a Statement, you will always use the term execute to do it. For instance, you will call any of these methods:

    execute(String)
    executeBatch()
    executeQuery(String)
    executeUpdate(String)

In a similar fashion, you will always use the term close to release resources, no matter which resource you’re releasing. For instance, you will call:

    Connection.close()
    Statement.close()
    ResultSet.close()

As a matter of fact, close is such a strong and established term in the JDK, that it has lead to the interfaces java.io.Closeable (since Java 1.5), and java.lang.AutoCloseable (since Java 1.7), which generally establish a contract of releasing resources.

###Rule violation: Observable

This rule is violated a couple of times in the JDK. For instance, in the java.util.Observable class. While other “Collection-like” types established the terms

    size()
    remove()
    removeAll()

… this class declares

    countObservers()
    deleteObserver(Observer)
    deleteObservers()

There is no good reason for using other terms in this context. The same applies to Observer.update(), which should really be called notify(), an otherwise established term in JDK APIs

###Rule violation: Spring. Most of it

Spring has really gotten popular in the days when J2EE was weird, slow, and cumbersome. Think about EJB 2.0… There may be similar opinions on Spring out there, which are off-topic for this post. Here’s how Spring violates this concrete rule. A couple of random examples where Spring fails to establish strong terms, and uses long concatenations of meaningless, inconcise words instead:

    AbstractBeanFactoryBasedTargetSourceCreator
    AbstractInterceptorDrivenBeanDefinitionDecorator
    AbstractRefreshablePortletApplicationContext
    AspectJAdviceParameterNameDiscoverer
    BeanFactoryTransactionAttributeSourceAdvisor
    ClassPathScanningCandidateComponentProvider
    … this could go on indefinitely, my favourite being …
    J2eeBasedPreAuthenticatedWebAuthenticationDetailsSource. Note, I’ve blogged about conciseness before…

Apart from “feeling” like a horrible API (to me), here’s some more objective analysis:

    What’s the difference between a Creator and a Factory
    What’s the difference between a Source and a Provider?
    What’s the non-subtle difference between an Advisor and a Provider?
    What’s the non-subtle difference between a Discoverer and a Provider?
    Is an Advisor related to an AspectJAdvice?
    Is it a ScanningCandidate or a CandidateComponent?
    What’s a TargetSource? And how would it be different from a SourceTarget if not a SourceSource or my favourite: A SourceSourceTargetProviderSource?


[Gary Fleming commented on my previous blog post](http://blog.jooq.org/2012/10/08/j2eebasedpreauthenticatedwebauthenticationdetailssource-wat/#comment-917) about Spring’s funny class names:

    I’d be willing to bet that a Markov-chain generated class name (based on Spring Security) would be indistinguishable from the real thing.

Back to more seriousness…


###Rule #2: Apply symmetry to term combinations

Once you’ve established strong terms, you will start combining them. When you look at the JDK’s Collection APIs, you will notice the fact that they are symmetric in a way that they’ve established the terms add(), remove(), contains(), and all, before combining them symmetrically:

    add(E)
    addAll(Collection<? extends E>)
    remove(Object)
    removeAll(Collection<?>)
    contains(Object)
    containsAll(Collection<?>)

Now, the Collection type is a good example where an exception to this rule may be acceptable, when a method doesn’t “pull its own weight”. This is probably the case for retainAll(Collection<?>), which doesn’t have an equivalent retain(E) method. It might just as well be a regular violation of this rule, though.

###Rule violation: Map

This rule is violated all the time, mostly because of some methods not pulling their own weight (which is ultimately a matter of taste). With Java 8′s defender methods, there will no longer be any excuse of not adding default implementations for useful utility methods that should’ve been on some types. For instance: Map. It violates this rule a couple of times:

    It has keySet() and also containsKey(Object)
    It has values() and also containsValue(Object)
    It has entrySet() but no containsEntry(K, V)

Observe also, that there is no point of using the term Set in the method names. The method signature already indicates that the result has a Set type. It would’ve been more consistent and symmetric if those methods would’ve been named keys(), values(), entries(). (On a side-note, Sets and Lists are another topic that I will soon blog about, as I think those types do not pull their own weight either)

At the same time, the Map interface violates this rule by providing

    put(K, V) and also putAll(Map)
    remove(Object), but no removeAll(Collection<?>)

Besides, establishing the term clear() instead of reusing removeAll() with no arguments is unnecessary. This applies to all Collection API members. In fact, the clear() method also violates rule #1. It is not immediately obvious, if clear does anything subtly different from remove when removing collection elements.

Rule #3: Add convenience through overloading

There is mostly only one compelling reason, why you would want to overload a method: Convenience. Often you want to do precisely the same thing in different contexts, but constructing that very specific method argument type is cumbersome. So, for convenience, you offer your API users another variant of the same method, with a “friendlier” argument type set. This can be observed again in the Collection type. We have:

    toArray(), which is a convenient overload of…
    toArray(T[])

Another example is the Arrays utility class. We have:

    copyOf(T[], int), which is an incompatible overload of…
    copyOf(boolean[], int), and of…
    copyOf(int[], int)
    … and all the others

Overloading is mostly used for two reasons:

    Providing “default” argument behaviour, as in Collection.toArray()
    Supporting several incompatible, yet “similar” argument sets, as in Arrays.copyOf()

Other languages have incorporated these concepts into their language syntax. Many languages (e.g. PL/SQL) formally support named default arguments. Some languages (e.g. JavaScript) don’t even care how many arguments there really are. And another, new JVM language called Ceylon got rid of overloading by combining the support for named, default arguments with union types. As Ceylon is a statically typed language, this is probable the most powerful approach of adding convenience to your API.

Rule violation: TreeSet

It is hard to find a good example of a case where this rule is violated in the JDK. But there is one: the TreeSet and TreeMap. Their constructors are overloaded several times. Let’s have a look at these two constructors:

    TreeSet(Collection<? extends E>)
    TreeSet(SortedSet<E>)

The latter “cleverly” adds some convenience to the first in that it extracts a well-known Comparator from the argument SortedSet to preserve ordering. This behaviour is quite different from the compatible (!) first constructor, which doesn’t do an instanceof check of the argument collection. I.e. these two constructor calls result in different behaviour:

	SortedSet<Object> original = // [...]
	 
	// Preserves ordering:
	new TreeSet<Object>(original);
	 
	// Resets ordering:
	new TreeSet<Object>((Collection<Object>) original);

These constructors violate the rule in that they produce completely different behaviour. They’re not just mere convenience.
Rule #4: Consistent argument ordering

Be sure that you consistently order arguments of your methods. This is an obvious thing to do for overloaded methods, as you can immediately see how it is better to always put the array first and the int after in the previous example from the Arrays utility class:

    copyOf(T[], int), which is an incompatible overload of…
    copyOf(boolean[], int)
    copyOf(int[], int)
    … and all the others

But you will quickly notice that all methods in that class will put the array being operated on first. Some examples:

    binarySearch(Object[], Object)
    copyOfRange(T[], int, int)
    fill(Object[], Object)
    sort(T[], Comparator<? super T>)

Rule violation: Arrays

The same class also “subtly” violates this rule in that it puts optional arguments in between other arguments, when overloading methods. For instance, it declares

    fill(Object[], Object)
    fill(Object[], int, int, Object)

When the latter should’ve been fill(Object[], Object, int, int). This is a “subtle” rule violation, as you may also argue that those methods in Arrays that restrict an argument array to a range will always put the array and the range argument together. In that way, the fill() method would again follow the rule as it provides the same argument order as copyOfRange(), for instance:

    fill(Object[], int, int, Object)
    copyOfRange(T[], int, int)
    copyOfRange(T[], int, int, Class)

You will never be able to escape this problem if you heavily overload your API. Unfortunately, Java doesn’t support named parameters, which helps formally distinguishing arguments in a large argument list, as sometimes, large argument lists cannot be avoided.

Rule violation: String

Another case of a rule violation is the String class:

    regionMatches(int, String, int, int)
    regionMatches(boolean, int, String, int, int)

The problems here are:

    It is hard to immediately understand the difference between the two methods, as the optional boolean argument is inserted at the beginning of the argument list
    It is hard to immediately understand the purpose of every int argument, as there are many arguments in a single method

Rule #5: Establish return value types

This may be a bit controversial as people may have different views on this topic. No matter what your opinion is, however, you should create a consistent, regular API when it comes to defining return value types. An example rule set (on which you may disagree):

    Methods returning a single object should return null when no object was found
    Methods returning several objects should return an empty List, Set, Map, array, etc. when no object was found (never null)
    Methods should only throw exceptions in case of an … well, an exception

With such a rule set, it is not a good practice to have 1-2 methods lying around, which:

    … throw ObjectNotFoundExceptions when no object was found
    … return null instead of empty Lists

Rule violation: File

File is an example of a JDK class that violates many rules. Among them, the rule of regular return types. Its File.list() Javadoc reads:

    An array of strings naming the files and directories in the directory denoted by this abstract pathname. The array will be empty if the directory is empty. Returns null if this abstract pathname does not denote a directory, or if an I/O error occurs.

So, the correct way to iterate over file names (if you’re doing defensive programming) is:

	String[] files = file.list();
	 
	// You should never forget this null check!
	if (files != null) {
		for (String file : files) {
		    // Do things with your file
		}
	}

Of course, we could argue that the Java 5 expert group could’ve been nice with us and worked that null check into their implementation of the foreach loop. Similar to the missing null check when switching over an enum (which should lead to the default: case). They’ve probably preferred the “fail early” approach in this case.

The point here is that File already has sufficient means of checking if file is really a directory (File.isDirectory()). And it should throw an IOException if something went wrong, instead of returning null. This is a very strong violation of this rule, causing lots of pain at the call-site… Hence:

NEVER return null when returning arrays or collections!

Rule violation: JPA

An example of how JPA violates this rule is the way how entities are retrieved from the EntityManager or from a Query:

    EntityManager.find() methods return null if no entity could be found
    Query.getSingleResult() throws a NoResultException if no entity could be found

As NoResultException is a RuntimeException this flaw heavily violates the Principle of Least Astonishment, as you might stay unaware of this difference until runtime!

IF you insist on throwing NoResultExceptions, make them checked exceptions as client code MUST handle them
Conclusion and further reading

… or rather, further watching. Have a look at Josh Bloch’s presentation on API design. He agrees with most of my claims 

Another useful example of such a web page is the “Java API Design Checklist” by The Amiable API:

http://theamiableapi.com/2012/01/16/java-api-design-checklist/ 


##Reference

[1](http://programmers.stackexchange.com/questions/64926/should-a-method-validate-its-parameters)
[2](http://programmers.stackexchange.com/questions/147480/should-one-check-for-null-if-he-does-not-expect-null)
[3](http://programmers.stackexchange.com/questions/238896/should-you-throw-an-exception-if-a-methods-input-values-are-out-of-range)
