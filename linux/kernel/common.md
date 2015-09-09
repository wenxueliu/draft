##前言

Linux 内核源码主要以 C 语言为主, 有一小部分涉及汇编语言,编译器使用的是Gcc. 初次看内核源码,
会遇到一些难以理解, 晦涩的代码; 而恰恰是这些晦涩的代码, 在内核源码中经常出现. 把一些晦涩,
常见的代码看懂后, 大家会发现看内核代码越来越顺利.

本文以 x86_64 架构中的 Linux 2.6.32-71.el6 (RHEL 6) 源码为例, 选择一些经常出现且晦涩的源码
进行解释, 选择的源码虽以 2.6.32-71.el6 为例, 但很多内容同样使用其他版本的源码. 主要内容包
括 gcc 中 C 语言的扩展用法, 及其他一些杂项.


##gcc 中 C 语言的扩展用法

###__attribute__

在我们看文件系统(File Sytems)或页面缓存(Page Cache)管理内容时, 会经常遇到 struct address_space
数据结构, 其定义在include/linux/fs.h中.

```
struct  address_space {

      struct inode          *host;           / * owner: inode, block_device */

      struct radix_tree_root  page_tree;   / * radix tree of all pages */

      spinlock_t              tree_lock;    / * and lock protecting it */

      unsigned int           i_mmap_writable;/ * count VM_SHARED mappings */

      struct prio_tree_root    i_mmap;

/ * tree of private and shared mappings */

      struct list_head     i_mmap_nonlinear;/ *list VM_NONLINEAR mappings */

      spinlock_t              i_mmap_lock;     / * protect tree, count, list */

      unsigned int           truncate_count;  / * Cover race condition with truncate */

      unsigned long        nrpages;       / * number of total pages */

      pgoff_t                  writeback_index;/ * writeback starts here */

      const struct address_space_operations *a_ops;/ * methods */

      unsigned long        flags;            / * error bits/ gfp mask */

      struct backing_dev_info *backing_dev_info; / * device readahead, etc */

      spinlock_t              private_lock;       / * for use by the address_space */

      struct list_head     private_list; / * ditto */

      struct address_space    *assoc_mapping;/ * ditto */

} __attribute__((aligned(sizeof(long))));
```

大家注意到, 在结构体定义结束出__attribute__((aligned(sizeof(long)))).

这句的作用是什么?对结构体的定义有什么影响?

对于关键字 __attribute__, 在标准的 C 语言中是没有的. 它是 gcc 中对 C 语言的一个扩展用法. 关键字
__attribute__ 可以用来设置一个函数或数据结构定义的属性. 对一个函数设置属性的主要目的是使编译器对
函数进行可能的优化. 对函数设置属性, 是在函数原型定义中设置, 如下面一个例子：

```
    void fatal_error() __attribute__ ((noreturn));
    ....
    void fatal_error(char *message)
    {
    fprintf(stderr,"FATAL ERROR: %s\n",message);
    exit(1);
    }
```


在这个例子中, noreturn 属性告诉编译器, 这个函数不返回给调用者, 所以编译器就可以忽略所有与执行该函
数返回值有关的代码.

可以在同一个定义中, 设置多个属性, 各个属性用逗号分开即可. 如下面的定义就是告诉编译器, 它不改变全局
变量和该函数不能扩展为内联函数.

```
int getlim() __attribute__ ((pure, noinline));
```

属性(attributes)也可以用来设置变量和结构体的成员. 如, 为了保证结构体中的一个成员变量与结构体有特殊
方式的对齐(alignment), 可以用以下形式定义：

```
    struct mong {
    char id;
    int code __attribute__ ((align(4)));
    };
```

address_space结构体中, 显然 __attribute__ 是用来设置结构体 struct address_space 的, 就是给该结构体
设置一个属性. 设置什么样的属性呢? 该结构体的属性是 aligned(sizeof(long)), 就是设置 struct address_space
结构体按 sizeof(long) 个字节对齐.

这里的属性 aligned 的含义是: 设置与内存地址对齐(alignment)的方式. 如

```
     int alivalue __attribute__ ((aligned(32)));
```

变量 alivalue 的地址就是 32 字节对齐. 对于我们内核源码的例子, 当然属性有很多中, 不仅仅是 aligned, 比如
还有 deprecated, packed, unused 等. 并且设置变量或结构体的属性, 与设置函数的属性有所不同.

GCC 对 C 语言的扩展, 更多内容请参考链接. http://gcc.gnu.org/onlinedocs/gcc/C-Extensions.html#C-Extensions

我们再来看一个实例代码摘自linux/include/module.h

```
#ifdef MODULE
#define MODULE_GENERIC_TABLE(gtype,name)             \
extern const struct gtype##_id     mod_##gtype##_table      \
  __attribute__ ((unused, alias(__stringify(name))))


extern struct module __this_module;
#define THIS_MODULE (&   this_module )
#else  / * ! MODULE */
#define MODULE_GENERIC_TABLE(gtype,name)
#define THIS_MODULE ((struct module *)0)
#endif
```

注意到 __attribute__ ((unused, alias(__stringify(name)))). 前面已经提到, 可以为一个变量或函数设置多个属性
(attribute), 各个属性之间用逗号隔开. 86行的宏有两个属性： unused 和 alias. unused 使该类型的数据项显示为未
被使用的, 这样编译时就不会产生任何告警信息; alias使该定义是其他符号的别名. 如

```
void __f () { /* Do something. */; }
void f () __attribute__ ((weak, alias ("__f")));
定义"f"是"__f"的一个弱别名. 
```

###关键字替代

先看一段源码, 摘自include/linux/compiler-gcc.h.

```
/ * Optimization barrier */
/ * The "volatile" is due to gcc bugs */
#define barrier() __asm              __volatile__("": : :"memory")
```

在文件arch/x86/include/asm/msr.h另外一段代码.

```
static inline unsigned long long native_read_msr_safe(unsigned int msr,
                                               int *err)
{

      DECLARE_ARGS(val, low, high);
      asm volatile("2: rdmsr ; xor %[err],%[err]\n"
                  "1:\n\t"
                  ".section .fixup,\"ax\"\n\t"
                  "3:  mov %[fault],%[err] ; jmp 1b\n\t"
                  ".previous\n\t"
                  _ASM_EXTABLE(2b, 3b)
                  : [err] "=r" (*err), EAX_EDX_RET(val, low, high)
                  : "c" (msr), [fault] "i" (- EIO));
      return EAX_EDX_VAL(val, low, high);

}

```

给出的两段代码都使用了嵌入式汇编. 但不同的是关键字的形式不一样. 一个使用的是__asm__,
另外一个是asm. 事实上, 两者的含义都一样. 也就是__asm__等同于asm, 区别在于编译时, 若
使用了选项-std和-ansi, 则关闭了关键字asm, 而其替代关键字__asm__仍然可以使用.

类似的关键字还有__typeof__和__inline__, 其等同于typeof和inline.

###typeof

在内核双链表include/linux/kernel.h中, 有以下一段代码. 该宏的具体含义, 这里不多作解释, 后面的章节会介绍. 这里我们关注一个关键字typeof. 

00669: / **

00670:  * container_of - cast a member of a structure out to the containing structure

00671:  * @ptr: the pointer to the member.

00672:  * @type:the type of the container struct this is embedded in.

00673:  * @member: the name of the member within the struct.

00674:  *

00675:  */

00676: #define container_of(ptr,  type,  member) ({             \

00677:       const typeof( ((type *)0)->member) *__mptr = (ptr);  \

00678:       (type *)( (char *)__mptr - offsetof(type,member) );})

00679:

 

从字面意思上理解, typeof就是获取其类型, 其含义也正是如此. 关键字typeof返回的是表达式的类型, 使用上类似于关键字sizeof, 但它的返回值是类型, 而不是一个大小. 下面是一些例子：

char *chptr; // A char pointer

typeof (*chptr) ch; // A char

typeof (ch) *chptr2; // A char pointer

typeof (chptr) chparray[10]; // Ten char pointers

typeof (*chptr) charray[10]; // Ten chars

typeof (ch) charray2[10]; // Ten chars

 
2.4      asmlinkage

asmlinkage在内核源码中出现的频率非常高, 它是告诉编译器在本地堆栈中传递参数, 与之对应的是fastcall; fastcall是告诉编译器在通用寄存器中传递参数. 运行时, 直接从通用寄存器中取函数参数, 要比在本地堆栈(内存)中取, 速度快很多. 

00492: / *

00493:  * sys_execve() executes a new program.

00494:  */

00495: asmlinkage

00496: long  sys_execve(char __user *name, char __user * __user *argv,

00497:               char __user * __user *envp, struct pt_regs *regs)

00498: {

00499:       long error;

00500:       char *filename;

00501:

00502:       filename = getname(name);

00503:       error = PTR_ERR(filename);

00504:       if (IS_ERR(filename))

00505:               return error;

00506:       error = do_execve(filename, argv, envp, regs);

00507:       putname(filename);

00508:       return error;

00509: }

 

fastcall的使用是和平台相关的, asmlinkage和fastcall的定义都在文件arch/x86/include/asm/linkage.h中. 

00009: #ifdef CONFIG_X86_32

00010: #define asmlinkage CPP_ASMLINKAGE   __attribute__((regparm(0)))

00011: / *

00012:  * For 32- bit UML - mark functions implemented in assembly that use

00013:  * regparm input parameters:

00014:  */

00015: #define asmregparm __attribute__((regparm(3)))

 
2.5      UL

UL通常用在一个常数的后面, 标记为“unsigned long”. 使用UL的必要性在于告诉编译器, 把这个常数作为长型数据对待. 这可以避免在部分平台上, 造成数据溢出. 例如, 在16位的整数可以表示的范围为-32,768 ~ +32,767; 一个无符号整型表示的范围可以达到65,535. 使用UL可以帮助当你使用大数或长的位掩码时, 写出的代码与平台无关. 下面一段代码摘自include/linux/hash.h. 

00017: #include  types.h>

00018:

00019: / * 2^31 + 2^29 - 2^25 + 2^22 - 2^19 - 2^16 + 1 */

00020: #define GOLDEN_RATIO_PRIME_32 0x9e370001UL

00021: / * 2^63 + 2^61 - 2^57 + 2^54 - 2^51 - 2^18 + 1 */

00022: #define GOLDEN_RATIO_PRIME_64 0x9e37fffffffc0001UL

00023:

 
2.6      const和volatile

关键字const的含义不能理解为常量, 而是理解为“只读”. 如int const*x是一个指针, 指向一个const整数. 这样, 指针可以改变, 但整数值却不能改变. 然而int *const x是一个const指针, 指向整数, 整数的值可以改变, 但指针不能改变. 下面代码摘自fs/ext4/inode.c. 

00347: static int ext4_block_to_path(struct inode *inode,

00348:                           ext4_lblk_t i_block,

00349:                           ext4_lblk_t offsets[4], int *boundary)

00350: {

00351:       int ptrs = EXT4_ADDR_PER_BLOCK(inode- >i_sb);

00352:       int ptrs_bits = EXT4_ADDR_PER_BLOCK_BITS(inode- >i_sb);

00353:       const long direct_blocks = EXT4_NDIR_BLOCKS,

00354:               indirect_blocks = ptrs,

00355:               double_blocks = (1 << (ptrs_bits * 2));

 

关键字volatile标记变量可以改变, 而没有告警信息. volatile告诉编译器每次访问时, 该变量必须重新加载, 而不是从拷贝或缓存中读取. 需要使用volatile的场合有, 当我们处理中断寄存器时, 或者并发进程之间共享的变量. 

task_struct结构体如下, 包含volatile和const两个特殊关键字. 

01231: struct  task_struct {

01232:       volatile long state; / * - 1 unrunnable, 0 runnable, >0 stopped */

01233:       void *stack;

01234:       atomic_t usage;

01235:       unsigned int flags; / * per process flags, defined below */

01236:       unsigned int ptrace;

01237:

01238:       int lock_depth;           / * BKL lock depth */

01239:

01240: #ifdef CONFIG_SMP

01241: #ifdef __ARCH_WANT_UNLOCKED_CTXSW

01242:       int oncpu;

01243: #endif

01244: #endif

01245:

01246:       int prio, static_prio, normal_prio;

01247:       unsigned int rt_priority;

01248:       const struct sched_class *sched_class;

 

 
3      杂项3.1      __volatile__

在嵌入式汇编代码中, 经常看到__volatile__修饰符, 我们提到__volatile__和volatile实际上是等同的, 这里不多作强调. __volatile__修饰符对汇编代码非常重要. 它告诉编译器不要优化内联的汇编代码. 通常, 编译器认为一些代码是冗余和浪费的, 于是就试图尽可能优化这些汇编代码. 


3.2      likely() 和 unlikely()

unlikely() 和 likely() 这两个语句也很常见. 先看 mm/page_alloc.c 中的函数 __alloc_pages(), 这个函数是内存管理中分配物理页面的核心函数.

02100: / *
02101:  * This is the 'heart' of the zoned buddy allocator.
02102:  */
02103: struct page *
02104: __alloc_pages_nodemask(gfp_t  gfp_mask, unsigned int order,
02105:                     struct zonelist *zonelist, nodemask_t *nodemask)
02106: {
02107:       enum zone_type high_zoneidx = gfp_zone(gfp_mask);
02108:       struct zone *preferred_zone;
02109:       struct page *page;
02110:       int migratetype = allocflags_to_migratetype(gfp_mask);
02111:
02112:       gfp_mask &= gfp_allowed_mask ;
02113:
02114:       lockdep_trace_alloc(gfp_mask);
02115:
02116:       might_sleep_if(gfp_mask & __GFP_WAIT);
02117:
02118:       if (should_fail_alloc_page(gfp_mask, order))
02119:               return NULL;
02120:
02121:       / *
02122:        * Check the zones suitable for the gfp_mask contain at least one
02123:        * valid zone. It's possible to have an empty zonelist as a result
02124:        * of GFP_THISNODE and a memoryless node
02125:        */
02126:       if (unlikely(! zonelist- >_zonerefs- >zone))
02127:               return NULL;
02128:

 

注意到2126行的 unlikely() 语句. 那么 unlikely() 和 likely() 的含义是什么?

在 linux 内核源码中, unlikely() 和 likely() 是两个宏, 它告诉编译器一个暗示. 现代的 CPU 都有提前预测语句执行分支
(branch-prediction heuristics) 的功能, 预测将要执行的指令, 以优化执行速度. unlikely() 和 likely() 通过编译器告诉
CPU, 某段代码是 likely, 应被预测; 某段代码是 unlikely, 不应被预测. likely() 和 unlikely() 定义在 include/linux/compiler.h.

00106: # ifndef likely
00107: #  define likely(x) (__builtin_constant_p(x) ? ! ! (x) : __branch_check__(x, 1))
00108: # endif
00109: # ifndef unlikely
00110: #  define unlikely(x)  (__builtin_constant_p(x) ? ! ! (x) : __branch_check__(x, 0))
00111: # endif

###IS_ERR和PTR_ERR

许多内部的内核函数返回一个指针值给调用者, 而这些函数中很多可能会失败. 在大部分情况下, 失败是通过返回一个NULL指针值来表示的. 这种技巧有作用, 但是它不能传递问题的确切性质. 某些接口确实需要返回一个实际的错误编码, 以使调用者可以根据实际出错的情况做出正确的决策. 

许多内核接口通过把错误值编码到一个指针值中来返回错误信息. 这种函数必须小心使用, 因为他们的返回值不能简单地和NULL比较. 为了帮助创建和使用这种类型的接口, 中提供了一小组函数. 

void *ERR_PTR(long error);

这里error是通常的负的错误编码. 调用者可以使用IS_ERR来检查所返回的指针是否是一个错误编码：

long IS_ERR(const void* ptr);

如果需要实际的错误编码, 可以通过以下函数把它提取出来：

long PTR_ERR(const void* ptr);

 

应该只有在IS_ERR对某值返回真值时才对该值使用PTR_ERR, 因为任何其他值都是有效的指针. 

 
3.4      __init,__initdata,__exit,__exitdata

先看linux内核启动时的一段代码, 摘自init/main.c. 

00541: asmlinkage void __init  start_kernel(void)

00542: {

00543:       char * command_line;

00544:       extern struct kernel_param __start      param[],

  __stop   param[];

00545:

00546:       smp_setup_processor_id();

00547:

00548:       / *

00549:        * Need to run as early as possible, to initialize the

00550:        * lockdep hash:

00551:        */

00552:       lockdep_init();

00553:       debug_objects_early_init();

00554:

00555:       / *

00556:        * Set up the the initial canary ASAP:

00557:        */

00558:       boot_init_stack_canary();

00559:

00560:       cgroup_init_early();

00561:

00562:       local_irq_disable();

00563:       early_boot_irqs_off();

00564:       early_init_irq_lock_class();

00565:

00566: / *

00567:  * Interrupts are still disabled. Do necessary setups, then

00568:  * enable them

00569:  */

 

函数start_kernel()有个修饰符__init. __init实际上是一个宏, 只有在linux内核初始化是执行的函数或变量前才使用__init. 编译器将标记为__init的代码段存放在一个特别的内存区域里, 这个区域在系统初始化后, 就会释放. 

同理, __initdata用来标记只在内核初始化使用的数据, __exit和__exitdata用来标记结束或关机的例程. 这些通常在设备驱动卸载时使用. 

 
3.5      内核源码语法检查

看进程管理内容时, do_fork()的源码是必读的. 我们注意到do_fork()最后两个参数前, 都有__user修饰符. 那么这么修饰符的含义和用处是怎样的?摘自kernel/fork.c. 

01397: long  do_fork(unsigned long clone_flags,

01398:             unsigned long  stack_start,

01399:             struct pt_regs *regs,

01400:             unsigned long  stack_size,

01401:             int __user *parent_tidptr,

01402:             int __user *child_tidptr)

01403: {

01404:       struct task_struct *p;

01405:       int trace = 0;

01406:       long nr;

01407:

01408:       / *

01409:        * Do some preliminary argument and permissions checking before we

01410:        * actually start allocating stuff

01411:        */

01412:       if (clone_flags & CLONE_NEWUSER) {

01413:               if (clone_flags & CLONE_THREAD)

01414:                     return - EINVAL;

01415:               / * hopefully this check will go away when userns support is

01416:               * complete

01417:               */

01418:               if (! capable(CAP_SYS_ADMIN) ||  ! capable(CAP_SETUID) ||

01419:                            ! capable(CAP_SETGID))

01420:                     return - EPERM;

01421:       }

 

先来看__user的在include/linux/compiler.h中的定义：

00006: #ifdef     CHECKER     

00007: # define __user          __attribute__((noderef, address_space(1)))

00008: # define __kernel / * default address space */

00009: # define __safe           __attribute__((safe))

00010: # define __force  __attribute__((force))

00011: # define __nocast__attribute__((nocast))

00012: # define __iomem      __attribute__((noderef, address_space(2)))

00013: # define __acquires(x)      __attribute__((context(x,0,1)))

00014: # define __releases(x)__attribute__((context(x,1,0)))

00015: # define __acquire(x) __context__(x,1)

00016: # define __release(x) __context__(x,- 1)

00017: # define __cond_lock(x,c) ((c) ? ({ __acquire(x); 1; }) : 0)

00018: extern void __chk_user_ptr(const volatile void __user *);

00019: extern void __chk_io_ptr(const volatile void __iomem *);

00020: #else

00021: # define __user

00022: # define __kernel

00023: # define __safe

00024: # define __force

00025: # define __nocast

00026: # define __iomem

00027: # define __chk_user_ptr(x) (void)0

00028: # define __chk_io_ptr(x) (void)0

00029: # define __builtin_warning(x,  y...) (1)

00030: # define __acquires(x)

00031: # define __releases(x)

00032: # define __acquire(x) (void)0

00033: # define __release(x) (void)0

00034: # define __cond_lock(x,c) (c)

00035: #endif

 

通过其定义, 似乎Gcc中现在还没有支持这个用法. 通过字面意思理解, __user很显然是告诉它是一个用户数据. 虽然Gcc还不支持这种用法, 但借助适当的工具, 就可以在内核编译时就可以发现内核源码中的一些错误; 如前面的__user, 若编译时发现传递进来的不是用户数据, 那么就产生告警. 

在__user定义中, 我们发现还有__kernel, __safe, __force, __iomem, 这些都是用来做内核源码语法检查的; 其中__iomem在驱动代码中很常见. 

目前内核社区使用SPARSE工具来做内核源码的检查. SPARSE是语法分析器, 能在编译器前端发现源码的语法. 它能检查ANSI C以及很多Gcc的扩展. SPASE提供一系列标记来传递语法信息, 如地址空间的类型, 函数所需获取或释放的锁等. 

 
