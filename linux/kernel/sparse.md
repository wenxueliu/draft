Sparse - a Semantic Parser for C
sparse 是用于 C 语言的语法分析器，用以对 C 代码进行静态检查，它不但可以检查 ANSI C 而且还能检查具有 gcc 扩展的 C 。在 Linux 中，不但可以检查用户端代码，还可以检查内核代码。起初它由 linus 编写，后来交给其他人维护。



##Sparse 介绍

Sparse 诞生于 2004 年, 是由linux之父开发的, 目的就是提供一个静态检查代码的工具, 从而减少linux内核的隐患.

其实在Sparse之前, 已经有了一个不错的代码静态检查工具("SWAT"), 只不过这个工具不是免费软件, 使用上有一些限制.

所以 linus 还是自己开发了一个静态检查工具.

具体可以参考这篇文章(2004年的文章了): [Finding kernel problems automatically](http://lwn.net/Articles/87538/)

内核代码中还有一个简略的关于Sparse的说明文件: Documentation/sparse.txt

##Sparse 属性

Sparse通过 gcc 的扩展属性 __attribute__ 以及sparse定义的 __context__ 来对代码进行静态检查.

	宏名称					宏定义													检查点
	__bitwise 			__attribute__((bitwise)) 					确保变量是相同的位方式(比如 bit-endian, little-endiandeng)
	__user 				__attribute__((noderef, address_space(1))) 	指针地址必须在用户地址空间
	__kernel 			__attribute__((noderef, address_space(0))) 	指针地址必须在内核地址空间
	__iomem 			__attribute__((noderef, address_space(2))) 	指针地址必须在设备地址空间
	__safe 				__attribute__((safe)) 						变量可以为空
	__force 			__attribute__((force)) 						变量可以进行强制转换
	__nocast 			__attribute__((nocast)) 					参数类型与实际参数类型必须一致
	__acquires(x) 		__attribute__((context(x, 0, 1))) 			参数 x 在执行前引用计数必须是 0,执行后,引用计数必须为1
	__releases(x) 		__attribute__((context(x, 1, 0))) 			与 __acquires(x) 相反
	__acquire(x) 		__context__(x, 1) 							参数 x 的引用计数 + 1
	__release(x) 		__context__(x, -1) 							与 __acquire(x) 相反
	__cond_lock(x,c) 	((c) ? ({ __acquire(x); 1; }) : 0) 			参数c 不为0时,引用计数 + 1, 并返回1


其中 __acquires(x) 和 __releases(x), __acquire(x) 和 __release(x) 必须配对使用, 否则 Sparse 会给出警告

修饰符 __attribute__((context(...))) 可由Sparse宏 __context__(...)替代，context(...) 原型为：context(expression,in_context,out_context)

注： 在Fedora系统中通过 rpm 安装的 sparse 存在一个小bug.即使用时会报出 error: unable to open ’stddef.h’ 的错误, 最好从自己源码编译安装 sparse.


##Sparse 在编译内核中的使用

用 Sparse 对内核进行静态分析非常简单.

//检查所有内核代码
make C=1 检查所有重新编译的代码
make C=2 检查所有代码, 不管是不是被重新编译

##Linux 内核中的定义

Linux内核在 linux/compiler.h 和 linux/types.h 文件中定义了如下简短形式的预编译宏(如果编译的时候不使用 __CHECKER__ 标记, 代码中所有的这些注记将被删除)

#ifdef __CHECKER__
# define __user     __attribute__((noderef, address_space(1)))
# define __kernel   __attribute__((address_space(0)))
# define __iomem    __attribute__((noderef, address_space(2)))
# define __safe     __attribute__((safe))
# define __force    __attribute__((force))
# define __nocast   __attribute__((nocast))
# define __must_hold(x) __attribute__((context(x,1,1)))
# define __acquires(x)  __attribute__((context(x,0,1)))
# define __releases(x)  __attribute__((context(x,1,0)))
# define __acquire(x)   __context__(x,1)
# define __release(x)   __context__(x,-1)
# define __cond_lock(x,c)   ((c) ? ({ __acquire(x); 1; }) : 0)
# define __percpu   __attribute__((noderef, address_space(3)))
#ifdef CONFIG_SPARSE_RCU_POINTER
# define __rcu      __attribute__((noderef, address_space(4)))
#else
# define __rcu
#endif
extern void __chk_user_ptr(const volatile void __user *);
extern void __chk_io_ptr(const volatile void __iomem *);
#else
# define __user
# define __kernel
# define __iomem
# define __safe
# define __force
# define __nocast
# define __chk_user_ptr(x) (void)0
# define __chk_io_ptr(x) (void)0
# define __builtin_warning(x, y...) (1)
# define __must_hold(x)
# define __acquires(x)
# define __releases(x)
# define __acquire(x) (void)0
# define __release(x) (void)0
# define __cond_lock(x,c) (c)
# define __percpu
# define __rcu
#endif

#ifdef __CHECKER__
# define __bitwise__    __attribute__((bitwise))
#else
# define __bitwise__
#endif
 
#ifdef __CHECK_ENDIAN__
# define __bitwise      __bitwise__
#else
# define __bitwise
#endif


##范例

###__bitwise 的使用

主要作用就是确保内核使用的整数是在同样的位方式下. Sparse 会检查这个变量是否一直在同一种位方式(big-endian, little-endian或其他)下被使用,
如果此变量在多个位方式下被使用了, Sparse 会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:include/sound/core.h 51行 */
	typedef int __bitwise snd_device_type_t;

此外 

	typedef __u32 __bitwise    __le32;
	typedef __u32 __bitwise    __be32;

类型 __le32 和 __be32 代表不同字节顺序的32位整数类型。然而，C 语言并未指定这些类型的变量不应混合在一起。按位(bitwise)属性是用来标记这些类型的限制，所以，如果这些类型或其他整型变量混合在一起，Sparse将给出警告信息。


###__user 的使用

如果使用了 __user 宏的指针不在用户地址空间初始化, 或者指向内核地址空间, 设备地址空间等等, Sparse会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:arch/score/kernel/signal.c 45行 */
	static int setup_sigcontext(struct pt_regs *regs, struct sigcontext __user *sc)

###__kernel 的使用

如果使用了 __kernel 宏的指针不在内核地址空间初始化, 或者指向用户地址空间, 设备地址空间等等, Sparse会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:arch/s390/lib/uaccess_pt.c 180行 */
	memcpy(to, (void __kernel __force *) from, n);

###__iomem 的使用

如果使用了 __iomem 宏的指针不在设备地址空间初始化, 或者指向用户地址空间, 内核地址空间等等, Sparse会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:arch/microblaze/include/asm/io.h 22行 */
	static inline unsigned char __raw_readb(const volatile void __iomem *addr)

###__safe 的使用

使用了 __safe修饰的变量在使用前没有判断它是否为空(null), Sparse会给出警告.

我参考的内核版本(v2.6.32.61) 中的所有内核代码都没有使用 __safe, 估计可能是由于随着gcc版本的更新,

gcc已经会对这种情况给出警告, 所以没有必要用Sparse去检查了.

###__force 的使用

使用了__force修饰的变量可以进行强制类型转换, 没有使用 __force修饰的变量进行强制类型转换时, Sparse会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:arch/s390/lib/uaccess_pt.c 180行 */
	memcpy(to, (void __kernel __force *) from, n);

###__nocast 的使用

使用了__nocast修饰的参数的类型必须和实际传入的参数类型一致才行，否则Sparse会给出警告.

内核代码中的例子:

	/* 内核版本:v2.6.32.61  file:fs/xfs/support/ktrace.c 55行 */
	ktrace_alloc(int nentries, unsigned int __nocast sleep)

###__acquires __releases __acquire __release的使用

这4个宏都是和锁有关的, __acquires 和 __releases 必须成对使用, __acquire 和 __release 必须成对使用, 否则Sparse会给出警告.


##Sparse 在普通 C 的使用
Sparse除了能够用在内核代码的静态分析上, 其实也可以用在一般的C语言程序中.


#ifdef __CHECKER__
# define __user        __attribute__((noderef, address_space(1)))
# define __kernel    /* default address space */
# define __safe        __attribute__((safe))
# define __force    __attribute__((force))
# define __nocast    __attribute__((nocast))
# define __iomem    __attribute__((noderef, address_space(2)))
# define __acquires(x)    __attribute__((context(x,0,1)))
# define __releases(x)    __attribute__((context(x,1,0)))
# define __acquire(x)    __context__(x,1)
# define __release(x)    __context__(x,-1)
# define __cond_lock(x,c)    ((c) ? ({ __acquire(x); 1; }) : 0)
extern void __chk_user_ptr(const volatile void __user *);
extern void __chk_io_ptr(const volatile void __iomem *);
#else
# define __user
# define __kernel
# define __safe
# define __force
# define __nocast
# define __iomem
# define __chk_user_ptr(x) (void)0
# define __chk_io_ptr(x) (void)0
# define __builtin_warning(x, y...) (1)
# define __acquires(x)
# define __releases(x)
# define __acquire(x) (void)0
# define __release(x) (void)0
# define __cond_lock(x,c) (c)
#endif

平常 gcc 编译时, 不定义 __CHECKER__, 所以这里的 macros 就是空定义, 当使用 sparse 时就定义 __CHECKER__, 这些宏就好进行代码的检查.

##实例

程序一：

#include <stdio.h>
int main()
{
        printf ("hello world\n");
        return 0;
}


使用 sparse 检查这个程序：

$ ./sparse /home/beyes/C/gcc/context.c 

/home/beyes/C/gcc/context.c:6:10: warning: non-ANSI function declaration of function 'main'


警告提示我们这个程序中的 main 函数不符合 ANSI 函数的声明标准。
改进方法是为 main() 函数添加上参数，即：

	main(int argc, char **argv)

这样修改后再次检查时，则不会出现此警告。


程序二

#include <stdio.h>
 
#define __acquire(x) __context__(x,1)
#define __release(x) __context__(x,-1)
 
int main(int argc, char **argv)
{
      __acquire(10);
 
        printf ("hello world\n");
        return 0;
}

上面从 linux 内核代码中直接拷贝了用以实现 spinlock 的两个宏 __acquire(x) 和 __release(x) 。在这两个宏中，出现了 __context__ 标签，这个 __context__ 是一种 sparse 支持的检查特性。这里，如果函数里单独 __acquire() 而没有使用 __release() 与之匹配的话，sparse 会发出警告。顺便说一下，像自旋锁这种锁，如果忘记释放(不匹配使用)，那么会造成整个内核死锁，这时候只能重启系统。使用 sparse 检查上面的程序会发现：

$ ./sparse /home/beyes/C/gcc/context.c
/home/beyes/C/gcc/context.c:6:5: warning: context imbalance in 'main' - wrong count at exit

如果将 __release() 加上和 __acquire() 匹配的话，则警告消除。



##参考

http://en.wikipedia.org/wiki/Sparse
http://yarchive.net/comp/linux/sparse.html
http://www.linuxjournal.com/article/7272
http://www.groad.net/bbs/thread-3388-1-1.html
http://www.cnblogs.com/wang_yb/p/3575039.html
http://rd-life.blogspot.tw/2009/12/sparse-type-checking.html

