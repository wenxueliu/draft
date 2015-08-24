1. 优雅地使用链表
        链表是编程中经常要用到的数据结构，结构体描述时分为数据域和指针域，本没有什么好讲。但有没有想过教科书上的这种方式有什么问题？通过这种方式定义和使 用链表，对于不同的链表类型，都要定义各自的链表结构，繁琐的很。linux kernel中链表的用法才应该是教科书中出现的。
        基本思想：在Linux内核链表中，不是在链表结构中包含数据，而是在数据结构中包含链表节点。
1） 链表定义：
struct list_head {
    struct list_head *next, *prev;
};
#define LIST_HEAD_INIT(name) { &(name), &(name) }
2） 链表使用者定义：
struct user_t {
    data domain;
    struct list_head node;
};
struct list_head g_user_list = LIST_HEAD_INIT(g_user_list);
3） 通过node定位user_t:
#define offsetof(TYPE, MEMBER) ((size_t) &((TYPE *)0)->MEMBER)
#define container_of(ptr, type, member) ({          
    const typeof(((type *)0)->member) * __mptr = (ptr); 
(type *)((char *)__mptr - offsetof(type, member)); })
struct user_t* next = container_of(&(g_user_list.next->node), struct user_t, node);
这里用到了container_of，container_of又用到了offsetof。offsetof是通过将结构体起始地址强制对齐到0来 计算出node和起始地址的偏移offset；而container_of在node地址基础上减去offset得到user_t结构体的地址并返回 user_t。
2. 高效地分支判断
        写程序不可避免的需要使用if/else，如何高效地进行分支判断呢？使用likely/unlikely。
#define likely(x)       __builtin_expect(!!(x), 1)
#define unlikely(x)     __builtin_expect(!!(x), 0)
long __builtin_expect (long EXP, long C)
        __builtin_expect是一个GCC内置的函数，语义是表示EXP == C，返回值是表达式的值。这两个宏定义是为了提示编译器正确地进行分支判断的优化。
        优化的原理是：通过调整生成汇编代码的顺序，将经常发生的分支代码放在cmp指令之后顺序执行，将不经常发生的分支代码通过jump指令跳过去，从而降低jump指令清空处理器流水线的影响。
3. 汇编实现的原子操作
__asm__ __volatile__(
                       "   lock       ;n"
                       "   addl %1,%0 ;n"
                       : "=m"  (my_var)   //output
                      : "ir"  (my_int), "m" (my_var)  //input
                      :       //modify  /* no clobber-list */
                      );
        这条汇编表示给my_var原子加my_int，lock前缀就是用来保证原子性的。
        Intel CPU有3种保证原子性的方式，lock前缀是其中之一，原理是通过锁总线来阻止其它处理器操作相应的地址。
4. 0长度数组
        定义数组时，长度必须是一个编译时确定的值，如果想使用运行时的值来确定数组的长度，可以使用0长度数组。
struct line {
       int length;
       char contents[0];
     };
struct line *thisline = (struct line *)malloc (sizeof (struct line) + this_length);
thisline->length = this_length;
只有GNU C才支持的特性，对于定义不确定长度的数组非常有用。
5. 三目运算的另类表达
        GNU 允许C 语言省略条件表达式中的表达式2省略, 此时表示表达式2与表达式1相同.例如
a = x ? : y;
等价于
a = x ? x : y;
但是如果 x 是一个表达式, 仅求值一次.
        也来分享一下你正在使用的tips吧！
参考文章：
http://www.ibm.com/developerworks/cn/linux/kernel/l-chain/index.html
http://kernelnewbies.org/FAQ/LikelyUnlikely
http://www.ibiblio.org/gferg/ldp/GCC-Inline-Assembly-HOWTO.html
http://gcc.gnu.org/onlinedocs/gcc/Zero-Length.html
http://zh.wikipedia.org/wiki/%E6%9D%A1%E4%BB%B6%E8%BF%90%E7%AE%97%E7%AC%A6

1.#define中使用do｛statement｝while（0）
保证statement无论在何处都能正确执行一次
2.将链表操作抽象出来，与宿主结果相互独立。所有的链表操作都作用与list_head,然后通过宏
#define list_entry(ptr, type, member) 
container_of(ptr, type, member)
获取宿主结构的地址.
container_of定义：
#define container_of(ptr, type, member) ({ \
const typeof(((type *)0)->member) *__mptr = (ptr); \
(type *)((char *)__mptr - offsetof(type, member)); })
很精辟，效率也很高，比后来的C++的面向对象的ADT效率高。
3.当一个数据结构被多个“用户”（此处用户指使用数据结构的一切对象）使用时，在内核中实际上只需要分配一个就行了，每个用户只需将指针指这个数 据结构就行了。分配函数中，如果此结构还不存在就分配一个，初始化其引用计数器为1，如果存在的话，只需简单地将引用计数器加1就行了。析构函数中，只需 将引用计数器减1，如果减到0再释放内存空间。这种技巧的核心在于利用指针实现内存的共享，而内存本身采用引用计数器来记录引用次数。这样可以极大节省空 间。 这个技巧貌似在Windows内核中也有使用。
4.使用likely和unlikely来指导gcc对代码进行分支预测的优化。二者的定义为：
#define likely(x) __builtin_expect((x),1)
#define unlikely(x) __builtin_expect((x),0)

http://www.cnblogs.com/lisperl/archive/2011/11/20/2255832.html    
http://rdc.taobao.com/blog/cs/?p=1675



If you are writing some really high performance C code. Or if you just like to do some premature C optimizations. Here’s a gcc compiler buildin you can use:
integer__builtin_expect((integervariable),(expectedvalue))
Since CPU’s prefetch instructions in a sequential way, jumps to other instructions will flush all prefetched instructions. Because of this it is better to only jump in the least expected case so the expected case can keep using the prefetched instructions.
This buildin allows you to hint the compiler about which case is more likely to happen. The return value of __builtin_expect is the first argument passed to it. The expected value needs to be a compile-time constant.
Example usage:
intexample(intalmostalwaysone){ if(__builtin_expect(almostalwaysone,1)){   // most likely path }else{   // least likely path }}
This code will result in the assambly looking something like this:
; almostalwaysone is placed in eax test eax,eax je   .else ; if case ret.else ; else case ret
As you can see the if case is execute sequentially while the else case requires a jump.
Update2012-05-05

Here is another gcc compiler buildin that can be useful from time to time:
void__builtin_unreachable(void)
This function will tell the compiler that a point in your code is never reached. It is useful in situations where the compiler cannot deduce the unreachability of the code.
Example usage:
intexample(){ function_that_never_returns(); __builtin_unreachable();}
