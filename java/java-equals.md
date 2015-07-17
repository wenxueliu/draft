在实际开发中有时候会遇到需要比较同一个类的不同实例对象的场景，一般情况下继承自 Object
父类的 equals() 和 hashCode() 可以满足需求，但却不能满足所有的场景，比如只需要使用少数
几个对象属性来判断比较是否是同一个对象，这时我们就需要自定义的 equals() 和 hashCode()
实现来进行重写覆盖 Object 中的方法。


##官方文档

###equals()

The equals method implements an equivalence relation on non-null object references:

**reflexive**

    for any non-null reference value x, x.equals(x) should return true.

**symmetric**

    for any non-null reference values x and y, x.equals(y) should
    return true if and only if y.equals(x) returns true.

**transitive**

    for any non-null reference values x, y, and z, if x.equals(y)
    returns true and y.equals(z) returns true, then x.equals(z) should return true.

**consistent**

    for any non-null reference values x and y, multiple
    invocations of x.equals(y) consistently return true or consistently return
    false, provided no information used in equals comparisons on the objects is
    modified.

**non-null**

    For any non-null reference value x, x.equals(null) should return false.

The equals method for class Object implements the most discriminating possible
equivalence relation on objects; that is, for any non-null reference values x
and y, this method returns true if and only if x and y refer to the same object
(x == y has the value true).

Note that it is generally necessary to override the hashCode method whenever
this method is overridden, so as to maintain the general contract for the
hashCode method, which states that equal objects must have equal hash codes.

##hashCode

Returns a hash code value for the object. This method is supported for the
benefit of hash tables such as those provided by HashMap.

The general contract of hashCode is:

Whenever it is invoked on the same object more than once during an execution of
a Java application, the hashCode method must consistently return the same
integer, provided no information used in equals comparisons on the object is
modified. This integer need not remain consistent from one execution of an
application to another execution of the same application.

if two objects are equal according to the equals(Object) method, then calling the
hashCode method on each of the two objects must produce the same integer result.

It is not required that if two objects are unequal according to the
equals(java.lang.Object) method, then calling the hashCode method on each of the
two objects must produce distinct integer results. However, the programmer
should be aware that producing distinct integer results for unequal objects may
improve the performance of hash tables.

As much as is reasonably practical, the hashCode method defined by class Object
does return distinct integers for distinct objects. (This is typically implemented
by converting the internal address of the object into an integer, but this implementation
technique is not required by the JavaTM programming language.)


要点:

### equals() 方法重写注意事项

必须同时满足对称性，传递性，反射性，一致性和非空

####重写equals()方法的同时一定要重写 hashcode()方法

hashcode是用于散列数据的快速存取，如利用HashSet/HashMap/Hashtable类来存储数据时，都是根据存储对象的hashcode值来进行判断是否相同的。
如果重写equals()的时候没有重写hashcode()方法，就会造成对象之间的混淆。

equals()和hashcode()方法之间要满足一下关系：

* 当 obj1.equals(obj2) 为 true 时，obj1.hashCode() == obj2.hashCode() 必须为 true
* 当 obj1.hashCode() == obj2.hashCode() 为 false 时，obj1.equals(obj2) 必须为 false
* 当 obj1.hashCode() == obj2.hashCode() 为 true 时，obj1.equals(obj2) 不一定为 false

##equals() 不需要比较所有成员变量，而是哪些可以唯一标志这个对象的成员，这与实际需求相关

##不要修改 equals 中 Object 的类似，否则不是重载，而是覆盖了.

##equals VS ==

###==

它的作用是判断两个对象的地址是不是相等。即，判断两个对象是不试同一个对象。

###equals() :

它的作用也是判断两个对象是否相等。但它一般有两种使用情况(前面第1部分已详细介绍过)：

情况1，类没有覆盖 equals() 方法。则通过 equals() 比较该类的两个对象时，等价于通过 "==" 比较这两个对象。
情况2，类覆盖了 equals() 方法。一般，我们都覆盖 equals() 方法来两个对象的内容相等; 若它们的内容相等, 则返回 true (即，认为这两个对象相等)。

###equals 与 ORM 的关系

如果你使用ORM处理一些对象的话，你要确保在hashCode()和equals()对象中使用getter和setter而不是直接引用成员变量。因为在ORM中有的时候成员变量会被延时加载，这些变量只有当getter方法被调用的时候才真正可用。

例如在我们的例子中，如果我们使用 e1.id == e2.id 则可能会出现这个问题，
但是我们使用 e1.getId() == e2.getId() 就不会出现这个问题。

If you are dealing with an ORM, using o instanceof Person is the only
thing that will behave correctly.

####Lazy loaded objects have null-fields

ORMs usually use the getters to force loading of lazy loaded objects. This means
that person.name will be null if person is lazy loaded, even if person.getName()
forces loading and returns "John Doe". In my experience, this crops up more
often in hashCode() and equals().

If you are dealing with an ORM, make sure to always use getters, and never
field references in hashCode() and equals().

####Saving an object will change its state

Persistent objects often use a id field to hold the key of the object. This
field will be automatically updated when an object is first saved. Do not use an
id field in hashCode(). But you can use it in equals().

A pattern I often use is

    if (this.getId() == null) {
        return this == other;
    } else {
        return this.getId() == other.getId();
    }

But: you cannot include getId() in hashCode(). If you do, when an object is
persisted, its hashCode changes. If the object is in a HashSet, you will "never"
find it again.

In my Person example, I probably would use getName() for hashCode and getId()
plus getName() (just for paranoia) for equals(). It is okay if there are some
risk of "collisions" for hashCode(), but never okay for equals().

hashCode() should use the non-changing subset of properties from equals()


##继承中 hashCode() 和 equals() 的处理

###equals()

* this and other are of the exact same type
* this is of a subtype of other

The other object is smaller than this object and only the superclass fields can
be compared for equality; the subclass-specific fields of this object must have
default values.

* this is of a supertype of other

The other object is the larger object that has subclass-specific fields that
must have default values. This can be implemented easiest if we let the other
object do the work, which gets us back to case (2) with the roles of this and
other being switched.

* this and other are from different branches of the class hierarchy.

Both objects have something in common, which must be compared for equality, and
they both have subclass-specific fields, which must checked against the default
values. This is the tricky part. First, we must identify the superclass that
this and other have in common and second we must check the subclass-specific
fields of both objects for default values.

###反例

```java
    class Point {
        private int x;
        private int y;
        // (obvious constructor omitted...)
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(o instanceof Point))
                return false;
            Point p = (Point)o;
            return (p.x == this.x && p.y == this.y);
        }
    }

    class ColorPoint extends Point {
        private Color c;
        // (obvious constructor omitted...)
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(o instanceof ColorPoint))
                return false;
            ColorPoint cp = (ColorPoint)o;
            return (super.equals(cp) && cp.color == this.color);
        }
    }
```

    ColorPoint p1 = new ColorPoint(1, 2, Color.RED);
    Point p2 = new Point(1, 2);

其中

    p1.equals(p2) FALSE;
    p2.equals(p1) TRUE;

显然违反了对称性, 解决办法是修改 ColorPoint

```java
    class ColorPoint extends Point {
        private Color c;
        // (obvious constructor omitted...)
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(o instanceof Point))
                return false;
            // if o is a normal Point, do a color-blind comparison:
            if (!(o instanceof ColorPoint))
                return o.equals(this);
            // o is a ColorPoint; do a full comparison:
            ColorPoint cp = (ColorPoint)o;
            return (super.equals(cp) && cp.color == this.color);
        }
    }
```

其中

    p1.equals(p2) TRUE;
    p2.equals(p1) TRUE;

很好，满足了对称性，但是却违反了传递性(这里假设对应ColorPoint 中 Color 参与相等性测试)

    ColorPoint p3 = new ColorPoint(1, 2, Col or.BLUE);
    p2.equals(p3) FALSE;
    p1.equals(p3) TRUE;

###解决办法

    class ColorPoint {
        private Point point;
        private Color color;
        // ...etc.
    }

通过组合而不是继承很好地解决了问题, 自行验证满足所有 equals()
要求的性质，但是，有时候我们必须通过继承, 因为继承可以很好地继承父类的方法，
而组合不行，必须重写所有的方法

```java
    class Point {
        private int x;
        private int y;
        protected boolean blindlyEquals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(o instanceof Point))
                return false;
            Point p = (Point)o;
            return (p.x == this.x && p.y == this.y);
        }
        public boolean equals(Object o) {
            return (this.blindlyEquals(o) && o.blindlyEquals(this));
        }
    }

    class ColorPoint extends Point {
        private Color c;
        protected boolean blindlyEquals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(o instanceof ColorPoint))
                return false;
            ColorPoint cp = (ColorPoint)o;
            return (super.blindlyEquals(cp) &&
                            cp.color == this.color);
        }
    }
```
以上可以解决继承中的问题，但是每个子类都必须重写 blindlyEquals 方法,
是否存在更合适的方法 ?

```java

    class ColorPoint extends Point {
        private Color c;
        // (obvious constructor omitted...)
        public boolean equals(Object o) {
            if (this == o) return true;
            if (o == null) return false;
            if (!(this.getClass() != o.getClass()))
                return false;
            // o is a ColorPoint; do a full comparison:
            ColorPoint cp = (ColorPoint)o;
            return (super.equals(cp) && cp.color == this.color);
        }
    }
```

    p1.equals(p2) FALSE;
    p2.equals(p1) FALSE;
    ColorPoint p3 = new ColorPoint(1, 2, Col or.BLUE);
    p2.equals(p3) FALSE;
    p3.equals(p2) FALSE;
    p1.equals(p3) FALSE;
    p3.equals(p1) FALSE;

显然这种方法更为合适且简洁．

注意:

* 对于 final 类，通过 instanceof 实现显然是没有不能满足传递性的问题
* 如果你的父类是你不可控的，或者是遗留代码通过 instanceof 来实现 equals() 那么，这里的 getClass() 的方式是不可行的,当然遇到这种情况，也许组合()或者代理(delegation)是一个不错的选择

###无法用代理和组合的情况: 类中存在protected 成员，使用某种框架，异常类

###equals() 与 实现 Comparable 接口的类

class MyClass implements Comparable<MyClass>
{

  @Override
  public boolean equals(Object obj)
  {
      /* If compareTo and equals aren't final, we should check with getClass
       * instead. */
      if (!(obj instanceof MyClass)) 
        return false;
      return compareTo((MyClass) obj) == 0;
    }

}

###equals() hashCode() 与 构造函数的关系

public class LinkInfo {

    public LinkInfo(Long firstSeenTime,
                    Long lastLldpReceivedTime,
                    Long lastBddpReceivedTime) {
        super();
        this.firstSeenTime = firstSeenTime;
        this.lastLldpReceivedTime = lastLldpReceivedTime;
        this.lastBddpReceivedTime = lastBddpReceivedTime;
    }

    /*
     * Do not use this constructor. Used primarily for JSON
     * Serialization/Deserialization
     */
    public LinkInfo() {
        this.firstSeenTime = null;
        this.lastLldpReceivedTime = null;
        this.lastBddpReceivedTime = null;
    }

    public LinkInfo(LinkInfo fromLinkInfo) {
        this.firstSeenTime = fromLinkInfo.getFirstSeenTime();
        this.lastLldpReceivedTime = fromLinkInfo.getUnicastValidTime();
        this.lastBddpReceivedTime = fromLinkInfo.getMulticastValidTime();
    }

    protected Long firstSeenTime;
    protected Long lastLldpReceivedTime; /* Standard LLLDP received time */
    protected Long lastBddpReceivedTime; /* Modified LLDP received time  */

    /** The port states stored here are topology's last knowledge of
     * the state of the port. This mostly mirrors the state
     * maintained in the port list in IOFSwitch (i.e. the one returned
     * from getPort), except that during a port status message the
     * IOFSwitch port state will already have been updated with the
     * new port state, so topology needs to keep its own copy so that
     * it can determine if the port state has changed and therefore
     * requires the new state to be written to storage.
     */

    public Long getFirstSeenTime() {
        return firstSeenTime;
    }

    public void setFirstSeenTime(Long firstSeenTime) {
        this.firstSeenTime = firstSeenTime;
    }

    public Long getUnicastValidTime() {
        return lastLldpReceivedTime;
    }

    public void setUnicastValidTime(Long unicastValidTime) {
        this.lastLldpReceivedTime = unicastValidTime;
    }

    public Long getMulticastValidTime() {
        return lastBddpReceivedTime;
    }

    public void setMulticastValidTime(Long multicastValidTime) {
        this.lastBddpReceivedTime = multicastValidTime;
    }

    @JsonIgnore
    public LinkType getLinkType() {
        if (lastLldpReceivedTime != null) {
            return LinkType.DIRECT_LINK;
        } else if (lastBddpReceivedTime != null) {
            return LinkType.MULTIHOP_LINK;
        }
        return LinkType.INVALID_LINK;
    }

    /* (non-Javadoc)
     * @see java.lang.Object#hashCode()
     */
    @Override
    public int hashCode() {
        final int prime = 5557;
        int result = 1;
        result = prime * result + ((firstSeenTime == null) ? 0 : firstSeenTime.hashCode());
        result = prime * result + ((lastLldpReceivedTime == null) ? 0 : lastLldpReceivedTime.hashCode());
        result = prime * result + ((lastBddpReceivedTime == null) ? 0 : lastBddpReceivedTime.hashCode());
        return result;
    }

    /* (non-Javadoc)
     * @see java.lang.Object#equals(java.lang.Object)
     */
    @Override
    public boolean equals(Object obj) {
        if (this == obj)
            return true;
        if (obj == null)
            return false;
        if (!(obj instanceof LinkInfo))
            return false;
        LinkInfo other = (LinkInfo) obj;

        if (firstSeenTime == null) {
            if (other.firstSeenTime != null)
                return false;
        } else if (!firstSeenTime.equals(other.firstSeenTime))
            return false;

        if (lastLldpReceivedTime == null) {
            if (other.lastLldpReceivedTime != null)
                return false;
        } else if (!lastLldpReceivedTime.equals(other.lastLldpReceivedTime))
            return false;

        if (lastBddpReceivedTime == null) {
            if (other.lastBddpReceivedTime != null)
                return false;
        } else if (!lastBddpReceivedTime.equals(other.lastBddpReceivedTime))
            return false;

        return true;
    }


    /* (non-Javadoc)
     * @see java.lang.Object#toString()
     */
    @Override
    public String toString() {
        return "LinkInfo [unicastValidTime=" + ((lastLldpReceivedTime == null) ? "null" : lastLldpReceivedTime)
                + ", multicastValidTime=" + ((lastBddpReceivedTime == null) ? "null" : lastBddpReceivedTime)
                + "]";
    }
}

public class SwitchPort {
    @JsonSerialize(using=ToStringSerializer.class)
    public enum ErrorStatus {
        DUPLICATE_DEVICE("duplicate-device");

        private String value;
        ErrorStatus(String v) {
            value = v;
        }

        @Override
        public String toString() {
            return value;
        }

        public static ErrorStatus fromString(String str) {
            for (ErrorStatus m : ErrorStatus.values()) {
                if (m.value.equals(str)) {
                    return m;
                }
            }
            return null;
        }
    }

    private final long switchDPID;
    private final int port;
    private final ErrorStatus errorStatus;

    /**
     * Simple constructor
     * @param switchDPID the dpid
     * @param port the port
     * @param errorStatus any error status for the switch port
     */
    public SwitchPort(long switchDPID, int port, ErrorStatus errorStatus) {
        super();
        this.switchDPID = switchDPID;
        this.port = port;
        this.errorStatus = errorStatus;
    }

    /**
     * Simple constructor
     * @param switchDPID the dpid
     * @param port the port
     */
    public SwitchPort(long switchDPID, int port) {
        super();
        this.switchDPID = switchDPID;
        this.port = port;
        this.errorStatus = null;
    }

    // ***************
    // Getters/Setters
    // ***************

    @JsonSerialize(using=DPIDSerializer.class)
    public long getSwitchDPID() {
        return switchDPID;
    }

    public int getPort() {
        return port;
    }

    public ErrorStatus getErrorStatus() {
        return errorStatus;
    }

    // ******
    // Object
    // ******

    @Override
    public int hashCode() {
        final int prime = 31;
        int result = 1;
        result = prime * result
                        + ((errorStatus == null)
                                ? 0
                                : errorStatus.hashCode());
        result = prime * result + port;
        result = prime * result + (int) (switchDPID ^ (switchDPID >>> 32));
        return result;
    }

    @Override
    public boolean equals(Object obj) {
        if (this == obj) return true;
        if (obj == null) return false;
        if (getClass() != obj.getClass()) return false;
        SwitchPort other = (SwitchPort) obj;
        if (errorStatus != other.errorStatus) return false;
        if (port != other.port) return false;
        if (switchDPID != other.switchDPID) return false;
        return true;
    }

    @Override
    public String toString() {
        return "SwitchPort [switchDPID=" + HexString.toHexString(switchDPID) +
               ", port=" + port + ", errorStatus=" + errorStatus + "]";
    }

}

###如何计算各个类型的 hashCode

(1) 如果是 boolean 值，则计算 f ? 1:0
(2) 如果是 byte\char\short\int, 则计算 (int)f
(3) 如果是 long 值，则计算 (int)(f ^ (f >>> 32))
(4) 如果是 float 值，则计算 Float.floatToIntBits(f)
(5) 如果是 double 值，则计算 Double.doubleToLongBits(f)，然后返回的结果是 long, 再用规则 (3) 去处理 long, 得到 int
(6) 如果是对象应用，如果 equals 方法中采取递归调用的比较方式，那么 hashCode 中同样采取递归调用hashCode的方式。否则需要为这个域计算一个范式，比如当这个域的值为 null 的时候，那么 hashCode 值为0
(7) 如果是数组，那么需要为每个元素当做单独的域来处理。如果你使用的是 1.5 及以上版本的 JDK，那么没必要自己去重新遍历一遍数组，java.util.Arrays.hashCode 方法包含了 8 种基本类型数组和引用数组的 hashCode 计算，算法同上
(8) 最后，要如同上面的代码，把每个域的散列码合并到result当中：result = 31 * result + elementHash;

注意点:

1. 为什么初始值要使用非0的整数?这个的目的主要是为了减少hash冲突，考虑这么个场景，
如果初始值为0,并且计算hash值的前几个域hash值计算都为0，那么这几个域就会被忽略掉，
但是初始值不为0,这些域就不会被忽略掉，示例代码:

```java
import java.io.Serializable;
 
public class Test implements Serializable {
 
    private static final long serialVersionUID = 1L;
 
    private final int[] array;
 
    public Test(int... a) {
            array = a;
        }
 
    @Override
    public int hashCode() {
            int result = 0; //注意，此处初始值为0
            for (int element : array) {
                        result = 31 * result + element;
                    }
            return result;
        }
 
    public static void main(String[] args) {
            Test t = new Test(0, 0, 0, 0);
            Test t2 = new Test(0, 0, 0);
            System.out.println(t.hashCode());
            System.out.println(t2.hashCode());
        }
 
}
```
如果hashCode中result的初始值为0，那么对象t和对象t2的hashCode值都会为0，尽管这两个对象不同。
但如果result的值为17,那么计算hashCode的时候就不会忽略这些为0的值，最后的结果t1是15699857，t2是506447


2. 为什么每次需要使用乘法去操作result?　主要是为了使散列值依赖于域的顺序，还是上面的那个例子，Test t = new Test(1, 0) 跟 Test t2 = new Test(0, 1),
  t和t2的最终hashCode返回值是不一样的。

3. 为什么是31? 31是个神奇的数字，因为任何数n * 31就可以被JVM优化为 (n << 5) -n, 移位和减法的操作效率
要比乘法的操作效率高的多。

另外如果对象是不可变的，那么还推荐使用缓存的方式，在对象中使用一个单独的属性来存储hashCode的值，这样对
于这个对象来说 hashCode 只需要计算一次就可以了。

```java
private volatile int hashCode = 0;

@Override
public int hashCode() {

    int result = hashCode;
    if(result == 0) {

            ...//计算过程
        }
    return result;
}
```

###equals 如何比较各个类型的


基本类型: 直接 if (value != other.value) return false;
类类型 :  if (value == null && other.value != null) return false;
          else if (value.equals(other.value)) return false;

QA: java 的设计者为啥要搞出个 hashCode() 方法，一个 equals() 不是足够了吗？

hash 散列算法,使得在 hash 表中查找一个记录速度变 O(1).
每个记录都有自己的 hashcode, 散列算法按照 hashcode 把记录放置在合适的位置.
在查找一个记录,首先先通过 hashcode 快速定位记录的位置.然后再通过 equals 来
比较是否相等. 没有 hashcode,一个一个比较过来,时间就变 O(N)了.

举例, 如果没有 HashCode, 一个 set 有一万个元素，再加入一个不同的新元素，则需要执行一万次的 equal 方法，这个效率太低了。
所以采用先比较 hashcode， 由于是 64 位整数，可以建立索引查找。如果 hashcode 没找到，则必定不 equal，加入 set 当中；
即使找到了，也只需执行 hashcode 相同的几个元素的 equal。这是一种性能设计。

QA: 内存地址, hashCode 的关系

hash code 跟内存没有关系，只不过是 Object 的默认 hashCode() 方法会返回一个内存编号，因为这样一定满足 hashCode() 方法的要求。

QA: hashCode 与 HashSet HashMap 的关系

如果没有hashCode, 默认是内存地址, 这样,从业务上,本应该是相等的对象(比如 Person("Ann") 和 Person("Ann")), 
由于 hashCode 不一样, 导致存储的两份, 这也许是不期望的, 因此, 通过重新定义自己的 hashCode 来解决业务需要相等的需求.

##equals() and its impact on the rest of your program

equals() is used by various other classes and its semantics, mixed-type
comparison or same-type-comparison-only, influences the behavior of other
components that you or others use in conjunction with your classes. 

For instance, equals() is closely related to the HashSet collection of the JDK,
because its implementation relies on the elements' equals() methods for its
internal organization. 

Same-type-comparison-only implementation of equals() . With such an
implementation of equals() you can store an Employee("Hanni Hanuta") and
a Student("Hanni Hanuta") into the same HashSet , but retrieval from the
collection will not work as expected. You will not find any of these two
contained objects when you ask the HashSet whether it contains a
Person("Hanni Hanuta") , because all three object are unequal to each
other. 

Mixed-type-comparison implementation of equals() . Conversely, with
this type of equals() implementation you will have problems storing
an Employee("Hanni Hanuta") and a Student("Hanni Hanuta") in the
same HashSet . The HashSet will reject the second add() operation,
because the collection already contains an element that compares
equal to the new element.

Both effects might be surprising and this is not to say that any of
them is incorrect or weird. It's just that the semantics of your
equals() implementation has an impact on the behavior of other
components that rely on the equals() method of your classes.

##参考

[1](http://www.oschina.net/question/82993_75533)
[2](http://www.cnblogs.com/skywang12345/p/3324958.html)
[3](http://stackoverflow.com/questions/27581/what-issues-should-be-considered-when-overriding-equals-and-hashcode-in-java)
[4](http://www.drdobbs.com/jvm/java-qa-how-do-i-correctly-implement-th/184405053#rl4)

##附录

```java
import java.util.Arrays;
/**
 * 一个链式调用的通用hashCode生成器
 *
 * <a href="http://my.oschina.net/arthor" target="_blank"
 * rel="nofollow">@author</a>  hongze.chi@gmail.com
 *
 */
public final class HashCodeHelper {

    private static final int multiplierNum = 31;
    private int hashCode;

    private HashCodeHelper() {
            this(17);
        }

    private HashCodeHelper(int hashCode) {
            this.hashCode = hashCode;
        }

    public static HashCodeHelper getInstance() {
            return new HashCodeHelper();
        }

    public static HashCodeHelper getInstance(int hashCode) {
            return new HashCodeHelper(hashCode);
        }

    public HashCodeHelper appendByte(byte val) {
            return appendInt(val);
        }

    public HashCodeHelper appendShort(short val) {
            return appendInt(val);
        }

    public HashCodeHelper appendChar(char val) {
            return appendInt(val);
        }

    public HashCodeHelper appendLong(long val) {
            return appendInt((int) (val ^ (val >>> 32)));
        }

    public HashCodeHelper appendFloat(float val) {
            return appendInt(Float.floatToIntBits(val));
        }

    public HashCodeHelper appendDouble(double val) {
            return appendLong(Double.doubleToLongBits(val));
        }

    public HashCodeHelper appendBoolean(boolean val) {
            return appendInt(val ? 1 : 0);
        }

    public HashCodeHelper appendObj(Object... val) {
            return appendInt(Arrays.deepHashCode(val));
        }

    public HashCodeHelper appendInt(int val) {
            hashCode = hashCode * multiplierNum + val;
            return this;
        }

    public int getHashCode() {
            return this.hashCode;
        }
}
```


