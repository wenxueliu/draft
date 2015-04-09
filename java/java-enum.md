##Reference

http://www.deepakgaikwad.net/index.php/2009/07/08/enums-in-java-5-code-examples.html

##Java Enum

Enumerations already existed in other languages like C, C++, SmallTalk etc. Hence Java Enums are not something very
new to programmers. Enums are used primarily to handle a collection of logically grouped constants. In Java, for
ages we have been handling constants (number constants here) through separate Java files, sometimes by encapsulating
those in relevant POJOs, and even using a wrong design style of implementing an interface containing all constants.

We used these constants in conditions implemented using ‘if’ statement or switch cases also. First thing you can notice
about all these approaches is that this made the code look clumsy. Usage of interfaces made the code unnecessarily complex.
Next, though the constants had something common, the language hardly provided anything to treat them as an object.
List of drawbacks doesn’t end here. Let us take an example below and see what other drawbacks are.

	public class StatusWithoutEnums {
		public static final int STATUS_OPEN = 0;
		public static final int STATUS_STARTED = 1;
		public static final int STATUS_INPROGRESS = 2;
		public static final int STATUS_ONHOLD = 3;
		public static final int STATUS_COMPLETED = 4;
		public static final int STATUS_CLOSED = 5;
	}

###Drawbacks of This Approach:

* Type Safety
All statuses above may carry some business meaning, but in Java language context, these are just int values.
This means any int value is a status for this Java program. So the program using these statuses can break with
any int value not defined in this group.

* Compile Time Constants
All these constants are compiled and used in the program. If you want to add any new constant then you will have
to add it to the list and recompile everything.

* Uninformative
When printed, these are just numbers for a reader. E.g. if a program prints status = 3, the reader will have to
go and find out what does it actually mean. Amount of information available with the print is minimal.

* Restricted Behavior
If you want to use these values in a remote call, or compare them, then you will have to handle it explicitly.
Serializable, Comparable interfaces offered by Java for same purpose cannot be used. Also there is no room to
add any additional behavior to the statuses, e.g. attaching basic object behavior of hashCode(), toString() and
equals() methods.

* Meaningless Switch-Case Use
When you use statuses above in switch case, you cannot use the variable names; instead you will have to use the
meaningless/uninformative numbers to compare. Readability of program goes down considerably in this case.

* Non-Iterative List
This is a list of values, but you cannot iterate over it the way you can on any collection.

The solution to above problem is Enum data type in Java 5. Concept of Enum is obtained from the counterpart technologies
like C, C++, C# etc. and also considering the Typesafe Enum design pattern in Effective Java book by Joshua Bloch.
The pattern is stated as below.

Define a class representing a single element of the enumerated type and provide no public constructor.

```java

	public class RequestStatus {
		private final int status;

		private RequestStatus(int aStatus) {
		    this.status = aStatus;
		}

		public static final RequestStatus STATUS_OPEN = new RequestStatus(0);
		public static final RequestStatus STATUS_STARTED = new RequestStatus(1);
		public static final RequestStatus STATUS_INPROGRESS = new RequestStatus(2);
		public static final RequestStatus STATUS_ONHOLD = new RequestStatus(3);
		public static final RequestStatus STATUS_COMPLETED = new RequestStatus(4);
		public static final RequestStatus STATUS_CLOSED = new RequestStatus(5);
	}
```

In above code, a status is actually a RequestStatus object, and though it is internally an int value, it is always
represented by a String or an object. As the int value is transformed into an object, we can add any behavior
(Serializable, Comparable, hashCode(), toString(), equals() etc.) to it.

In Java 5, this pattern is taken further to provide a cleaner implementation to a bunch of constants. Instead of a
list of "public static final" variables, we can use Enum data type to group constants together. Let us see how Java 5
enums change the code.

```java

    public class ReqStatus {

        public enum Status {
            STATUS_OPEN,
            STATUS_STARTED,
            STATUS_INPROGRESS,
            STATUS_ONHOLD,
            STATUS_COMPLETED,
            STATUS_CLOSED;
        }
        public static void main(String[] args) {
            for (Status stat: Status.values()) {
                System.out.println(stat);
            }
        }
    }
```

The change can be seen clearly. Now you don’t need to define the constants. Instead you can use enum data type
to store them directly.

##Different Uses of Java Enums:

In following discussion, you can see different ways of using enumerations in your programs. We start with an example
of primary use and then explore little complex uses later.

###Example 1:

In this example, we have one value for the status.

``` java

	public class StatusExample1 {

		public enum Status{
		    STATUS_OPEN(0),
		    STATUS_STARTED(1),
		    STATUS_INPROGRESS(2),
		    STATUS_ONHOLD(3),
		    STATUS_COMPLETED(4),
		    STATUS_CLOSED(5);

		    private final int status;

		    Status(int aStatus) {
		        this.status = aStatus;
		    }
		    public int status() {
		        return this.status;
		    }
		}

		public static void main(String[] args) {
		    for (Status stat: Status.values()) {
		        System.out.println(stat + "value is "+ new Integer(stat.status()));
		    }
		}
	}
```

###Example 2

Here we have two attributes of a status – an int value and a String description.

``` java

	public class StatusExample2 {

		public enum Status {
		    STATUS_OPEN(0, "open"),
		    STATUS_STARTED(1, "started"),
		    STATUS_INPROGRESS(2, "inprogress"),
		    STATUS_ONHOLD(3, "onhold"),
		    STATUS_COMPLETED(4, "completed"),
		    STATUS_CLOSED(5, "closed");

		    private final int status;
		    private final String description;

		    Status(int aStatus, String desc) {
		        this.status = aStatus;
		        this.description = desc;
		    }

		    public int status() {
		        return this.status;
		    }

		    public String description() {
		        return this.description;
		    }
		}

		public static void main(String[] args) {
		    for (Status stat: Status.values()) {
		        System.out.println(stat + "value is "+ new Integer(stat.status()) + " desc is " + stat.description());
		    }
		}
	}
```

###Example 3

Here we make the enumeration serializable. (It is possible that we lose information in marshaling and
un-marshaling operations. Hence there should be an explicit implementation to reconstruct any enumerated type value.)

```java

	import java.io.Serializable;

	public class StatusExample3 {

		public enum Status implements Serializable{
		    STATUS_OPEN         (0, "open"),
		    STATUS_STARTED      (1, "started"),
		    STATUS_INPROGRESS   (2, "inprogress"),
		    STATUS_ONHOLD       (3, "onhold"),
		    STATUS_COMPLETED    (4, "completed"),
		    STATUS_CLOSED       (5, "closed");

		    private final int status;
		    private final String description;

		    Status(int aStatus, String desc) {
		        this.status = aStatus;
		        this.description = desc;
		    }

		    public int status() {
		        return this.status;
		    }
		    public String description() {
		        return this.description;
		    }
		}
	}
```

###Example 4

This example checks for comparable interface implementation. Override compareTo method to provide your own implementation.

```java

	public class StatusExample4 {

		public enum Status{
		    STATUS_OPEN         (0, "open"),
		    STATUS_STARTED      (1, "started"),
		    STATUS_INPROGRESS   (2, "inprogress"),
		    STATUS_ONHOLD       (3, "onhold"),
		    STATUS_COMPLETED    (4, "completed"),
		    STATUS_CLOSED       (5, "closed");

		    private final int status;
		    private final String description;

		    Status(int aStatus, String desc) {
		        this.status = aStatus;
		        this.description = desc;
		    }

		    public int status() {
		        return this.status;
		    }

		    public String description() {
		        return this.description;
		    }

		    public int compareTo(Status obj) {
		        return 0;
		    }
		}
	}
```

###Example 5:

Enumeration type and its values behave like parent and child. In Status enumeration definition, we define an abstract
method to get description. Each value of the enum will implement this method to provide specific behavior (description
in this case).

``` java

	public class StatusExample5 {

		public enum Status {
		    STATUS_OPEN {
		        public String description(){
		            return "open";
		        }
		    },
		    STATUS_STARTED {
		        public String description(){
		            return "started";
		        }
		    },
		    STATUS_INPROGRESS {
		        public String description(){
		            return "inprogress";
		        }
		    },
		    STATUS_ONHOLD {
		        public String description(){
		            return "onhold";
		        }
		    },
		    STATUS_COMPLETED {
		        public String description(){
		            return "completed";
		        }
		    },
		    STATUS_CLOSED {
		        public String description(){
		            return "closed";
		        }
		    };

		    Status() {
		    }

		    public abstract String description();
		}

		public static void main(String[] args){
		    for (Status stat: Status.values()){
		        System.out.println(stat + " desc is " + stat.description());
		    }
		}
	}
```

###Example 6

In this code snippet, we go back to the problem from where we started. We write a switch-case example using enumerations.

```java

	public class StatusExample6 {

		public enum Status{
		    STATUS_OPEN         (0, "open"),
		    STATUS_STARTED      (1, "started"),
		    STATUS_INPROGRESS   (2, "inprogress"),
		    STATUS_ONHOLD       (3, "onhold"),
		    STATUS_COMPLETED    (4, "completed"),
		    STATUS_CLOSED       (5, "closed");

		    private final int status;
		    private final String description;

		    Status(int aStatus, String desc){
		        this.status = aStatus;
		        this.description = desc;
		    }

		    public int status(){
		        return this.status;
		    }

		    public String description(){
		        return this.description;
		    }
		}

		private static void checkStatus(Status status){
		    switch(status) {
		        case STATUS_OPEN:
		            System.out.println("This is open status");
		        case STATUS_STARTED:
		            System.out.println("This is started status");
		        case STATUS_INPROGRESS:
		            System.out.println("This is inprogress status");
		        case STATUS_ONHOLD:
		            System.out.println("This is onhold status");
		        case STATUS_COMPLETED:
		            System.out.println("This is completed status");
		        case STATUS_CLOSED:
		            System.out.println("This is closed status");
		    }
		}

		public static void main(String[] args){
		    checkStatus(Status.STATUS_CLOSED);
		}
	}
```

##Summary:

Enum type bring a good feature of other languages in Java. Using it, we can better group and manage related
constant values. Many problems with the constant handling are solved using Enums, still Java continues to
handle Enums in ‘static’ way to ensure same performance.
