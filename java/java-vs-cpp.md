
* Comparison of variables : equality vs identify

Now, in Java all classes have the method boolean equals(Object o) defined; it is
inherited from the base class of all classes, class Object . User-defined
classes can override this method in order to implement a functionality that
checks for equality . Redefining the equals() function looks like good way to
get back the value oriented comparison semantics that we know so well from C++.
However, this is treacherous.

The precise meaning of equals() always depends on the specific class and its
implementation. equals() must not mean "check for equality "; it can equally
well mean anything else. For instance, all classes that do not override the
equals() function exhibit the default behaviour inherited from class Object
which is "check for identity ". 


* Assignment

Assignment of variables comes with similar surprises, because assignment is
value assignment in C++ and reference assignment in Java. The clone() function
again looks like it would get us back value semantics, but by default it does a
shallow copy. Again, it depends on each single class what clone() actually means
and it is not used consistently.

* Reference variables

 The type system itself makes for surprises because Java reference variables
 look like C++ references, but behave like C++ pointers. For instance, in C++ a
 reference must be initialised to refer to an existing object, and only pointers
 can have a null value indicating that it does not refer to anything valid. In
 Java, reference variables are by default initialised with a null reference,
 which makes them behave pretty much like C++ pointers: you always have to check
 for the null value before any access.

* Construction/destruction
