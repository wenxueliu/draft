

编写 Java 多线程程序一直以来都是一件十分困难的事，多线程程序的 bug 很难测试，DCL(Double Check Lock)就是一个典型，
因此对多线程安全的理论分析就显得十分重要，当然这决不是说对多线程程序的测试就是不必要的。传统上，对多线程程序的分析是通
过分析操作之间可能的执行先后顺序，然而程序执行顺序十分复杂，它与硬件系统架构，编译器，缓存以及虚拟机的实现都有着很大的
关系。仅仅为了分析多线程程序就需要了解这么多底层知识确实不值得，况且当年选择学 Java 就是因为不用理会烦人的硬件和操作系
统，这导致了许多 Java 程序员不愿也不能从理论上分析多线程程序的正确性。虽然 99% 的 Java 程序员都知道 DCL 不对，但是
如果让他们回答一些问题，DCL 为什么不对？有什么修正方法？这个修正方法是正确的吗？如果不正确，为什么不正确？对于此类问题，
他们一脸茫然，或者回答也许吧，或者很自信但其实并没有抓住根本。

幸好现在还有另一条路可走，我们只需要利用几个基本的 happen-before 规则就能从理论上分析 Java 多线程程序的正确性，而且
不需要涉及到硬件和编译器的知识。接下来的部分，我会首先说明一下 happen-before 规则，然后使用 happen-before 规则来分
析 DCL，最后我以我自己的例子来说明 DCL 的问题其实很常见，只是因为对 DCL 的过度关注反而忽略其问题本身，当然其忽略是有
原因的，因为很多人并不知道 DCL 的问题到底出在哪里。

##Happen-Before规则

我们一般说一个操作 happen-before 另一个操作，这到底是什么意思呢？当说操作 A happen-before 操作 B 时，我们其实是
在说在发生操作 B 之前，操作 A 对内存施加的影响能够被观测到。所谓"对内存施加的影响"就是指对变量的写入，"被观测到"指当
读取这个变量时能够得到刚才写入的值（如果中间没有发生其它的写入）。听起来很绕口？这就对了，请你保持耐心，举个例子来说明
一下。线程Ⅰ执行了操作 A：x=3，线程Ⅱ执行了操作 B：y=x。如果操作 A happen-before操作 B，线程Ⅱ在执行操作 B 之前就
确定操作 "x=3" 被执行了，它能够确定，是因为如果这两个操作之间没有任何对 x 的写入的话，它读取 x 的值将得到 3，这意味
着线程Ⅱ执行操作 B 会写入 y 的值为 3。如果两个操作之间还有对 x 的写入会怎样呢？假设线程Ⅲ在操作 A 和 B 之间执行了操
作 C: x=5，并且操作 C 和操作 B 之前并没有 happen-before 关系(后面我会说明时间上的先后并不一定导致 happen-before
关系)。这时线程Ⅱ执行操作 B 会讲到 x 的什么值呢？3 还是 5? 答案是两者皆有可能，这是因为 happen-before 关系保证一
定能够观测到前一个操作施加的内存影响，只有时间上的先后关系而并没有 happen-before 关系可能但并不保证 能观测前一个操作
施加的内存影响。如果读到了值 3，我们就说读到了"陈旧"的数据。正是多种可能性导致了多线程的不确定性和复杂性，但是要分析多
线程的安全性，我们只能分析确定性部分，这就要求找出 happen-before 关系，这又得利用 happen-before 规则。

下面是我列出的三条非常重要的happen-before规则，利用它们可以确定两个操作之间是否存在happen-before关系。

1. 同一个线程中，书写在前面的操作 happen-before 书写在后面的操作。这条规则是说，在单线程 中操作间 happen-before
关系完全是由源代码的顺序决定的，这里的前提"在同一个线程中"是很重要的，这条规则也称为单线程规则 。这个规则多少说得有些
简单了，考虑到控制结构和循环结构，书写在后面的操作可能 happen-before 书写在前面的操作，不过我想读者应该明白我的意思。
    
2. 对锁的 unlock 操作 happen-before 后续的对同一个锁的 lock 操作。这里的"后续"指的是时间上的先后关系，unlock操
作发生在退出同步块之后，lock 操作发生在进入同步块之前。这是条最关键性的规则，线程安全性主要依赖于这条规则。但是仅仅是
这条规则仍然不起任何作用，它必须和下面这条规则联合起来使用才显得意义重大。这里关键条件是必须对"同一个锁"的lock和unlock。

3. 如果操作 A happen-before 操作 B，操作 B happen-before 操作 C，那么操作 A happen-before 操作 C。这条规则
也称为传递规则。

现在暂时放下 happen-before 规则，先探讨一下"一个操作在时间上先于另一个操作发生"和"一个操作happen-before另一个操作
之间"的关系。两者有关联却并不相同。关联部分在第2条 happen-before 规则中已经谈到了，通常我们得假定一个时间上的先后顺
序然后据此得出 happen-before 关系。不同部分体现在，首先，一个操作在时间上先于另一个操作发生，并不意味着一个操作
happen-before 另一个操作 。看下面的例子：

```java
    public void setX(int x) {
      this.x = x;               // (1)
    }

    public int getX() {
      return x;                 // (2)
    }
```

假设线程Ⅰ先执行 setX 方法，接着线程Ⅱ执行 getX 方法，在时间上线程Ⅰ的操作 A：this.x = x 先于线程Ⅱ的操作 B：return x。
但是操作 A 却并不 happen-before 操作 B，让我们逐条检查三条 happen-before 规则。第 1 条规则在这里不适用，因为这时
两个不同的线程。第 2 条规则也不适用，因为这里没有任何同步块，也就没有任何 lock 和 unlock 操作。第 3 条规则必须基于已
经存在的 happen-before 关系，现在没有得出任何 happen-before 关系，因此第三条规则对我们也任何帮助。通过检查这三条规
则，我们就可以得出，操作 A 和操作 B 之间没有 happen-before 关系。这意味着如果线程Ⅰ调用了 setX(3)，接着线程Ⅱ调用了
getX()，其返回值可能不是 3，尽管两个操作之间没有任何其它操作对 x 进行写入，它可能返回任何一个曾经存在的值或者默认值 0。
"任何曾经存在的值"需要做点解释，假设在线程Ⅰ调用 setX(3) 之前，还有别的线程或者就是线程Ⅰ还调用过 setX(5), setX(8)，
那么 x 的曾经可能值为0, 5和8(这里假设 setX 是唯一能够改变 x 的方法)，其中 0 是整型的默认值，用在这个例子中，线程Ⅱ调
用 getX() 的返回值可能为 0, 3, 5 和 8，至于到底是哪个值是不确定的。

现在将两个方法都设成同步的，也就是如下：

```java
public synchronized void setX(int x) {
  this.x = x;               // (1)
}

public synchronized int getX() {
  return x;                 // (2)
}
```

做同样的假设，线程Ⅰ先执行 setX 方法，接着线程Ⅱ执行 getX 方法，这时就可以得出来，线程Ⅰ的操作 A happen-before 线程Ⅱ
的操作 B。下面我们来看如何根据 happen-before 规则来得到这个结论。由于操作 A 处于同步块中，操作 A 之后必须定要发生对
this 锁的 unlock 操作，操作 B 也处于同步块中，操作 B 之前必须要发生对 this 锁的 lock 操作，根据假设 unlock 操作发生
lock 操作之前，根据第 2 条 happen-before 规则，就得到 unlock 操作 happen-before 于 lock 操作; 另外根据第 1 条
happen-before 规则（单线程规则），操作 A happen-before 于 unlock 操作，lock 操作 happen-before 于操作 B; 最后
根据第 3 条 happen-before 规则（传递规则），A -> unlock, unlock -> lock, lock -> B（这里我用->表示happen-before
关系），有 A -> B，也就是说操作A happen-before 操作 B。这意味着如果线程Ⅰ调用了 setX(3)，紧接着线程Ⅱ调用了 getX()，
如果中间再没有其它线程改变 x 的值，那么其返回值必定是3。

如果将两个方法的任何一个 synchronized 关键字去掉又会怎样呢？这时能不能得到线程Ⅰ的操作 A happen-before 线程Ⅱ的操作 B
呢？答案是得不到。这里因为第二条 happen-before 规则的条件已经不成立了，这时因为要么只有线程Ⅰ的 unlock 操作(如果去掉
getX 的 synchronized)，要么只有线程Ⅱ的 lock 操作(如果去掉 setX 的 synchronized 关键字)。这里也告诉我们一个原则，
**必须对同一个变量的所有读写同步，才能保证不读取到陈旧的数据，仅仅同步读或写是不够的**。
 
其次，**一个操作 happen-before 另一个操作 也并不意味着 一个操作在时间上先于另一个操作发生** 。看下面的例子：

```java
    x = 3;      (1)
    y = 2;      (2)
```

同一个线程执行上面的两个操作，操作 A：x = 3和操作 B：y = 2。根据单线程规则，操作 A happen-before操作 B，但是操作 A
却不一定在时间上先于操作 B 发生，这是因为编译器的重新排序等原因，操作 B 可能在时间上后于操作B发生。这个例子也说明了，分
析操作上先后顺序是多么地不靠谱，它可能完全违反直观感觉。

最后，一个操作和另一个操作必定存在某个顺序，要么一个操作或者是先于或者是后于另一个操作，或者与两个操作同时发生。同时发生
是完全可能存在的，特别是在多 CPU 的情况下。而两个操作之间却可能没有 happen-before 关系，也就是说有可能发生这样的情况，
操作 A 不 happen-before 操作 B，操作 B 也不 happen-before 操作 A，用数学上的术语 happen-before 关系是个偏序关系。
两个存在 happen-before 关系的操作不可能同时发生，一个操作 A happen-before 操作 B，它们必定在时间上是完全错开的，这
实际上也是同步的语义之一（独占访问）。

在运用 happen-before 规则分析 DCL 之前，有必要对"操作"澄清一下，在前面的叙述中我一直将语句是操作的同义词，这么讲是不
严格的，严格上来说这里的操作应该是指单个虚拟机的指令，如 moniterenter, moniterexit, add, sub, store, load等。使
用语句来代表操作并不影响我们的分析，下面我仍将延续这一传统，并且将直接用语句来代替操作。唯一需要注意的是单个语句实际上可能
由多个指令组成，比如语句 x=i++ 由两条指令(inc和store)组成。现在我们已经完成了一切理论准备，你一定等不及要动手开干了。

##Happen-Before规则分析DCL

下面是一个典型的使用DCL的例子：

```java
    public class LazySingleton {
        private int someField;
        
        private static LazySingleton instance;
        
        private LazySingleton() {
            this.someField = new Random().nextInt(200)+1;         // (1)
        }
        
        public static LazySingleton getInstance() {
            if (instance == null) {                               // (2)
                synchronized(LazySingleton.class) {               // (3)
                    if (instance == null) {                       // (4)
                        instance = new LazySingleton();           // (5)
                    }
                }
            }
            return instance;                                      // (6)
        }
        
        public int getSomeField() {
            return this.someField;                                // (7)
        }
    }
```

为了分析DCL，我需要预先陈述上面程序运行时几个事实：

1. 语句(5)只会被执行一次，也就是 LazySingleton 只会存在一个实例，这是由于它和语句 (4) 被放在同步块中被执行的缘故，
如果去掉语句 (3) 处的同步块，那么这个假设便不成立了。
2. instance只有两种"曾经可能存在"的值，要么为null，也就是初始值，要么为执行语句 (5) 时构造的对象引用。这个结论由
事实 1 很容易推出来。
3. getInstance() 总是返回非空值，并且每次调用返回相同的引用。如果 getInstance() 是初次调用，它会执行语句 (5) 构
造一个 LazySingleton 实例并返回，如果 getInstance() 不是初次调用，如果不能在语句 (2) 处检测到非空值，那么必定将
在语句 (4) 处就能检测到 instance 的非空值，因为语句(4)处于同步块中，对 instance 的写入也语句(5)也处于同一个同步块中。

有读者可能要问了，既然根据第 3 条事实 getInstance() 总是返回相同的正确的引用，为什么还说 DCL 有问题呢? 这里的关键是
尽管得到了 LazySingleton 的正确引用，但是却有可能访问到其成员变量的不正确值，具体来说LazySingleton.getInstance().getSomeField() 有可能返回 someField 的默认值 0。如果程序行为正确的话，这应当是不
可能发生的事，因为在构造函数里设置的 someField 的值不可能为0。为也说明这种情况理论上有可能发生，我们只需要说明语句(1)
和语句 (7) 并不存在 happen-before 关系。

假设线程Ⅰ是初次调用 getInstance() 方法，紧接着线程Ⅱ也调用了 getInstance() 方法和 getSomeField() 方法，我们要
说明的是线程Ⅰ的语句 (1) 并不 happen-before 线程Ⅱ的语句 (7)。线程Ⅱ在执行 getInstance() 方法的语句 (2) 时，由
于对 instance 的访问并没有处于同步块中，因此线程 Ⅱ 可能观察到也可能观察不到线程Ⅰ在语句 (5) 时对 instance 的写入，
也就是说 instance 的值可能为空也可能为非空。我们先假设 instance 的值非空，也就观察到了线程Ⅰ对 instance 的写入，这时
线程Ⅱ就会执行语句 (6) 直接返回这个 instance 的值，然后对这个 instance 调用 getSomeField() 方法，该方法也是在没
有任何同步情况被调用，因此整个线程Ⅱ的操作都是在没有同步的情况下调用，这时我们无法利用第 1 条和第 2 条 happen-before
规则得到线程Ⅰ的操作和线程Ⅱ的操作之间的任何有效的 happen-before 关系，这说明线程Ⅰ的语句(1)和线程Ⅱ的语句(7)之间并
不存在 happen-before 关系，这就意味着线程Ⅱ在执行语句 (7) 完全有可能观测不到线程Ⅰ在语句 (1) 处对 someFiled 写入
的值，这就是 DCL 的问题所在(这里更准确的表述是线程 I 调用 (5) 初始化 instance 的过程中, 可能在 instance 已经
非空, 还没来得及初始化 someField , 线程 II 调用了 getInstance() 由于 instance 为非 NULL, 所以直接调用 
getSomeField(), 由于  someField 还没有初始化, 所以为 0. 至于 instance 的非空可能会发生在 someField 之前是
因为指令重排序)。很荒谬，是吧？ DCL 原本是为了逃避同步，它达到了这个目的，也正是因为如此，它最终受到惩罚，这样的程序存在
严重的 bug，虽然这种 bug 被发现的概率绝对比中彩票的概率还要低得多，而且是转瞬即逝，更可怕的是，即使发生了你也不会想到是
 DCL 所引起的。

指令重排序的解释:在[参考1](http://www.ibm.com/developerworks/java/library/j-dcl.html )中提到，out-of-order 
writes是原因，就是说 instance = new LazySingleton();这行代码并不是一定按如下伪代码顺序进行的：

1. 分配内存
2. 调用构造器
3. 赋值给INSTANCE

在有的JIT上会编译优化为：

1. 分配内存
2. 赋值给INSTANCE
3. 调用构造器 

前面我们说了，线程Ⅱ在执行语句(2)时也有可能观察空值，如果是种情况，那么它需要进入同步块，并执行语句(4)。在语句(4)处
线程Ⅱ还能够读到 instance 的空值吗？不可能。这里因为这时对 instance 的写和读都是发生在同一个锁确定的同步块中，这
时读到的数据是最新的数据。为也加深印象，我再用 happen-before 规则分析一遍。线程Ⅱ在语句(3)处会执行一个 lock 操作，
而线程Ⅰ在语句 (5) 后会执行一个 unlock 操作，这两个操作都是针对同一个锁 LazySingleton.class，因此根据第 2 条
happen-before 规则，线程Ⅰ的 unlock 操作 happen-before 线程Ⅱ的 lock 操作，再利用单线程规则，线程Ⅰ的语句
(5) -> 线程Ⅰ的unlock操作，线程Ⅱ的lock操作 -> 线程Ⅱ的语句(4)，再根据传递规则，就有线程Ⅰ的语句(5) -> 线程Ⅱ的语句(4)，也就是说线程Ⅱ在执行语句 (4) 时能够观测到线程Ⅰ在语句 (5) 时对 LazySingleton 的写入值。接着对返回的 instance 调用getSomeField() 方法时，我们也能得到线程Ⅰ的语句 (1) -> 线程Ⅱ的语句 (7)，这表明这时 getSomeField 能够得到正确的值。
但是仅仅是这种情况的正确性并不妨碍 DCL 的不正确性，一个程序的正确性必须在所有的情况下的行为都是正确的，而不能有时正确，
有时不正确。

对DCL的分析也告诉我们一条经验原则，对引用（包括对象引用和数组引用）的非同步访问，即使得到该引用的最新值，却并不能保证
也能得到其成员变量（对数组而言就是每个数组元素）的最新值。 

再稍微对DCL探讨一下，这个例子中的 LazySingleton 是一个不变类，它只有 get 方法而没有 set 方法。由对 DCL 的分析我们
知道，即使一个对象是不变的，在不同的线程中它的同一个方法也可能返回不同的值。之所以会造成这个问题，是因为 LazySingleton
实例没有被安全发布，所谓"被安全的发布"是指所有的线程应该在同步块中获得这个实例。这样我们又得到一个经验原则，即使对于不可
变对象，它也必须被安全的发布，才能被安全地共享。 所谓"安全的共享"就是说不需要同步也不会遇到数据竞争的问题。在 Java5 或
以后，将 someField 声明成 final 的，即使它不被安全的发布，也能被安全地共享，而在 Java1.4 或以前则必须被安全地发布。

##关于DCL的修正

既然理解了DCL的根本原因，或许我们就可以修正它。

既然原因是线程Ⅱ执行 getInstance() 可能根本没有在同步块中执行，那就将整个方法都同步吧。这个毫无疑问是正确的，但是这却
回到最初的起点（返朴归真了），也完全违背了 DCL 的初衷，尽可能少的减少同步。虽然这不能带任何意义，却也说明一个道理，最简
单的往往是最好的。

如果我们尝试不改动 getInstance() 方法，而是在 getSomeField() 上做文章，那么首先想到的应该是将 getSomeField 设置
成同步，如下所示：

```java
    public synchronized int getSomeField() {
        return this.someField;                                // (7)
    }
```

这种修改是不是正确的呢？答案是不正确。这是因为，第 2 条 happen-before 规则的前提条件并不成立。语句 (5) 所在同步块和
语句 (7) 所在同步块并不是使用同一个锁。像下面这样修改才是对的：

```java
	public int getSomeField() {
		synchronized(LazySingleton.class) {
			return this.someField;
		}
	}
```

但是这样的修改虽然能保证正确性却不能保证高性能。因为现在每次读访问 getSomeField() 都要同步，如果使用简单的方法，将整个
getInstance() 同步，只需要在 getInstance() 时同步一次，之后调用 getSomeField() 就不需要同步了。另外 getSomeField()
方法也显得很奇怪，明明是要返回实例变量却要使用 Class 锁。这也再次验证了一个道理，简单的才是好的。

好了，由于我的想象力有限，我能想到的修正也就仅限于此了，让我们来看看网上提供的修正吧。


###修正方案一

```java
	private static LazySingleton instance;
	private static int hasInitialized = 0;
		
	public static LazySingleton getInstance() {
		if (hasInitialized == 0) {	                    // (4)
			synchronized(LazySingleton.class) {      // (5)
				if (instance == null) {	      // (6)
					instance = new LazySingleton();	// (7)
					hasInitialized = 1;
				}
			}
		}
		return instance;						// (8)
	}
```

如果你明白我前面所讲的，那么很容易看出这里根本就是一个伪修正，线程Ⅱ仍然完全有可能在非同步状态下返回 instance。
Lucas Lee 的理由是对 int 变量的赋值是原子的，但实际上对 instance 的赋值也是原子的，Java语言规范规定对任何
引用变量和基本变量的赋值都是原子的，除了 long 和 double 以外。使用 hasInitialized==0 和 instance==null
来判断 LazySingleton 有没有初始化没有任何区别。

###修正方案二

```java
	public static LazySingleton getInstance() {
	    if (instance == null) {						    // (4)
	        synchronized(LazySingleton.class) {			    // (5)
	            if (instance == null) {				    // (6)
	                LazySingleton localRef = new LazySingleton();
	                instance = localRef;				    // (7)
		     }
	        }
            }
            return instance;				                         // (8)
	}
```

这里只是引入了一个局部变量，这也容易看出来只是一个伪修正，如果你弄明白了我前面所讲的。

既然提到 DCL，就不得不提到一个经典的而且正确的修正。就是使用一个 static holder，kilik 在回复中给出了这样的一个修正。
由于这里一种完全不同的思路，与我这里讲的内容也没有太大的关系，暂时略了吧。另外一个修正是使用是threadlocal，都可以参

##步入Java5

前面所讲的都是基于 Java1.4 及以前的版本，java 5 对内存模型作了重要的改动，其中最主要的改动就是对 volatile 和 final
语义的改变。本文使用的 happen-before 规则实际上是从Java 5 中借鉴而来，然后再移花接木到 Java1.4 中，因此也就不得不谈
下 Java 5 中的多线程了。

在java 5中多增加了一条happen-before规则：

* 对 volatile 字段的写操作 happen-before 后续的对同一个字段的读操作。

利用这条规则我们可以将instance声明为volatile，即：

```java

    private volatile static LazySingleton instance; 
```

根据这条规则，我们可以得到，线程Ⅰ的语句(5) -> 语线程Ⅱ的句(2)，根据单线程规则，线程Ⅰ的语句(1) -> 线程Ⅰ的语句(5)和
语线程Ⅱ的句(2) -> 语线程Ⅱ的句(7)，再根据传递规则就有线程Ⅰ的语句(1) -> 语线程Ⅱ的句(7)，这表示线程Ⅱ能够观察到线程Ⅰ
在语句(1)时对someFiled的写入值，程序能够得到正确的行为。

这里另一层原因是 volatile 对指令重排序的修改, volatile 强制在 instance 语句之前的语句必须先与 instance 调用, 应用
于本例即在 instance 初始化之前, 必须先初始化 someFields. 

在 java5 之前对 final 字段的同步语义和其它变量没有什么区别，在 java5 中，final 变量一旦在构造函数中设置完成（前提是
在构造函数中没有泄露 this 引用)，其它线程必定会看到在构造函数中设置的值。而 DCL 的问题正好在于看到对象的成员变量的默认
值，因此我们可以将 LazySingleton 的 someField 变量设置成 final，这样在 java5 中就能够正确运行了。

##遭遇同样错误 

在Java世界里，框架似乎做了很多事情来隐藏多线程，以至于很多程序员认为不再需要关注多线程了。 这实际上是个陷阱，这它只会使
我们对多线程程序的 bug 反应迟钝。大部分程序员（包括我）都不 会特别留意类文档中的线程不安全警告，自己写程序时也不会考虑
将该类是否线程安全写入文档中。做个测试，你知道 java.text.SimpleDateFormat 不是线程安全的吗？如果你不知道，也不要感
到奇怪，我也是在《Java Concurrent In Practice 》这书中才看到的。

现在我们已经明白了DCL中的问题，很多人都只认为这只不过是不切实际的理论者整天谈论的话题，殊不知这样的错误其实很常见。我就
犯过，下面是从我同一个项目中所写的代码中摘录出来的，读者也不妨拿此来检验一下自己，你自己犯过吗？即使没有，你会毫不犹豫的
这样写吗？

第一个例子：

```java
public class TableConfig {
	//....
	private FieldConfig[] allFields;
	
	private transient FieldConfig[] _editFields;

	//....
	
	public FieldConfig[] getEditFields() {
		if (_editFields == null) {
			List<FieldConfig> editFields = new ArrayList<FieldConfig>();
			for (int i = 0; i < allFields.length; i++) {
				if (allFields[i].editable) editFields.add(allFields[i]);
			}
			_editFields = editFields.toArray(new FieldConfig[editFields.size()]);
		}
		return _editFields;
	}
}
```

这里缓存了 TableConfig 的 _editFields，免得以后再取要重新遍历 allFields。这里存在和 DCL 同样的问题，
_editFields 数组的引用可能是正确的值，但是数组成员却可能 null！ 与DCL不同的是 ，由于对 _editFields 的
赋值没有同步，它可能被赋值多次，但是在这里没有问题，因为每次赋值虽然其引用值不同，但是其数组成员是相同的，对于我的业务来说，它们都等价的。由于我的代码是要用在 java1.4 中，因此唯一的修复方法就是将整个方法声明为同步。

第二个例子：

```java
	private Map selectSqls = new HashMap();

	public Map executeSelect(final TableConfig tableConfig, Map keys) {
    	if (selectSqls.get(tableConfig.getId()) == null) {
    		selectSqls.put(tableConfig.getId(), constructSelectSql(tableConfig));
    	}
    	PreparedSql psql = (PreparedSql) selectSqls.get(tableConfig.getId());

    	List result = executeSql(...);
        
        return result.isEmpty() ? null : (Map) result.get(0);
    }
```

上面的代码用 constructSelectSql() 方法来动态构造 SQL 语句，为了避免构造的开销，将先前构造的结果缓存在 selectSqls
这个 Map 中，下次直接从缓存取就可以了。显然由于没有同步，这段代码会遭遇和 DCL 同样的问题，虽然 selectSqls.get(...)
可能能够返回正确的引用，但是却有可能返回该引用成员变量的非法值。另外 selectSqls 使用了非同步的 Map，并发调用时可能会
破坏它的内部状态，这会造成严重的后果，甚至程序崩溃。可能的修复就是将整个方法声明为同步：

```java
	public synchronized Map executeSelect(final TableConfig tableConfig, Map keys)  {
		// ....
    }
```

但是这样马上会遭遇吞吐量的问题，这里在同步块执行了数据库查询，执行数据库查询是是个很慢的操作，这会导致其它线程执行同样的
操作时造成不必要的等待，因此较好的方法是减少同步块的作用域，将数据库查询操作排除在同步块之外：

```
    public Map executeSelect(final TableConfig tableConfig, Map keys)  {
    	PreparedSql psql = null;
    	synchronized(this) {
	    	if (selectSqls.get(tableConfig.getId()) == null) {
	    		selectSqls.put(tableConfig.getId(), constructSelectSql(tableConfig));
	    	}
	    	psql = (PreparedSql) selectSqls.get(tableConfig.getId());
    	}

    	List result = executeSql(...);
        
        return result.isEmpty() ? null : (Map) result.get(0);
    }
```

现在情况已经改善了很多，毕竟我们将数据库查询操作拿到同步块外面来了。但是仔细观察会发现将 this 作为同步锁并不是一个好主意，
同步块的目的是保证从 selectSqls 这个 Map 中取到的是一致的对象，因此用 selectSqls 作为同步锁会更好，这能够提高性能。
这个类中还存在很多类似的方法 executeUpdate,executeInsert 时，它们都有自己的 sql 缓存，如果它们都采用 this 作为同步
锁，那么在执行 executeSelect 方法时需要等待 executeUpdate 方法，而这种等待原本是不必要的。使用细粒度的锁，可以消除这
种等待，最后得到修改后的代码：

```java
    private Map selectSqls = Collections.synchronizedMap(new HashMap())
    public Map executeSelect(final TableConfig tableConfig, Map keys)  {
    	PreparedSql psql = null;
    	synchronized(selectSqls) {
	    	if (selectSqls.get(tableConfig.getId()) == null) {
	    		selectSqls.put(tableConfig.getId(), constructSelectSql(tableConfig));
	    	}
	    	psql = (PreparedSql) selectSqls.get(tableConfig.getId());
    	}

    	List result = executeSql(...);
        
        return result.isEmpty() ? null : (Map) result.get(0);
    }
```

我对 selectSqls 使用了同步 Map，如果它只被这个方法使用，这就不是必须的。作为一种防范措施，虽然这会稍微降低性能，即便当它
被其它方法使用了也能够保护它的内部结构不被破坏。并且由于 Map 的内部锁是非竞争性锁，根据官方说法，这对性能影响很小，可以忽略
不计。这里我有意无意地提到了编写高性能的两个原则，尽量**减少同步块的作用域**，以及使用**细粒度的锁**，关于细粒度锁的最经典
例子莫过于读写锁了。这两个原则要慎用，除非你能保证你的程序是正确的。

##结束语

在这篇文章中我主要讲到 happen-before 规则，并运用它来分析 DCL 问题，最后我用例子来说明 DCL 问题并不只是理论上的讨论，在
实际程序中其实很常见。我希望读者能够明白用 happen-before 规则比使用时间的先后顺序来分析线程安全性要有效得多，作为对比，你
可以看看这篇经典的文章 中是如何分析 DCL 的线程安全性的。它是否讲明白了呢？如果它讲明白了，你是否又能理解？我想答案很可能是否
定的，不然的话就不会出现这么多对 DCL 的误解了。当然我也并不是说要用 happen-before 规则来分析所有程序的线程安全性，如果你试
着分析几个程序就会发现这是件很困难的事，因为这个规则实在是太底层了，要想更高效的分析程序的线程安全性，还得总结和利用了一些高层
的经验规则。关于这些经验规则，我在文中也谈到了一些，很零碎也不完全。 

##参考

http://www.cs.umd.edu/~pugh/java/memoryModel/DoubleCheckedLocking.html