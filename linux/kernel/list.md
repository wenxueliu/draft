
##双向循环列表

在Linux内核中，提供了一个用来创建双向循环链表的结构 list_head。虽然 linux 内核是用 C 语言写的, 但是 list_head 的引入,
使得内核数据结构也可以拥有面向对象的特性, 通过使用操作 list_head 的通用接口很容易实现代码的重用, 有点类似于C++的继承
机制(希望有机会写篇文章研究一下 C 语言的面向对象机制). 下面就是 kernel 中的 list_head 结构定义:

```
    struct list_head {
    　　struct list_head *next, *prev;
    };

    struct hlist_head {
        struct hlist_node *first;
    };

    struct hlist_node {
        struct hlist_node *next, **pprev;
    };

    #define LIST_HEAD_INIT(name) { &(name), &(name) }
```

需要注意的一点是, 头结点 head 是不使用的, 这点需要注意.

使用list_head组织的链表的结构如下图所示:

![head list 示意图](head_list.jpg)

list_head这个结构看起来怪怪的, 它竟没有数据域! 所以看到这个结构的人第一反应就是我们怎么访问数据?

其实 list_head 不是拿来单独用的, 它一般被嵌到其它结构中, 如:

```
    struct file_node{
    　　char c;
    　　struct list_head node;
    };
```

此时 list_head 就作为它的父结构中的一个成员了, 当我们知道 list_head 的地址(指针)时, 我们可以通过 list.c
提供的宏 list_entry 来获得它的父结构的地址. 下面我们来看看 list_entry 的实现:

```
    #define list_entry(ptr,type,member)\
    　　container_of(ptr,type,member)

    #define offsetof(TYPE,MEMBER) ((size_t)&((TYPE *)0)->MEMBER)

    #define container_of(ptr,type,member) ( {\
    　　const typeof( ((type*)0)->member ) *__mptr=(ptr);\
    　　(type*)( (char*)__mptr - offsetof(type,member) );} )
```

这里涉及到三个宏, 还是有点复杂的, 我们一个一个来看:

```
    #define offsetof(TYPE,MEMBER) ( (size_t)& ((TYPE *)0）-> MEMBER )
```

我们知道内存中 0 地址内容是不能访问的, 但 0 作为地址我们还是可以的, 这里用到一个取址运算符

(TYPE *)0 它表示将 0 地址强制转换为 TYPE 类型, ((TYPE *)0）->MEMBER 也就是从 0 址址找到 TYPE 的成员 MEMBER.

我们结合上面的结构来看

```
    struct file_node{
    　　char c;
    　　struct list_head node;
    };
```

将实参代入 offset(struct file_node, node); 最终将变成这样:

```
    ( (size_t) & ((struct file_node*)0）-> node );
```

这样看的还是不很清楚，我们再变变：

```
    struct file_node *p = NULL;
    (size_t)&p->node;
```

这样应该比较清楚了, 即求 p 的成员 node 的地址, 只不过 p 为 0 地址, 从 0 地址开始算成员 node 的地址, 也就是成员
node 在结构体 struct file_node 中的偏移量. offset 宏就是算 MEMBER 在 TYPE 中的偏移量的.

我们再看第二个宏

```
    #define container_of(ptr,type,member) ( {\
    　　const typeof( ((type*)0)->member ) *__mptr=(ptr);\
    　　(type*)( (char*)__mptr - offsetof(type,member) );} )
```

这个宏是由两个语句组成, 最后 container_of 返回的结果就是第二个表达式的值. 这里 __mptr 为中间变量, 类型为 type->member
的类型, 这里是 list_head 指针类型, 它被初始化为 ptr 的值，而 ptr 就是当前所求的结构体中 list_head 节点的地址.
为什么要用中间变量，这是考虑到安全性因素, 如果传进来一个 ptr++, 所有 ptr++ 放在一个表达式中会有副作用, 像 (p++)+(p++) 之类.

(char*)__mptr 之所以要强制类型转化为 char 是因为地址是以字节为单位的, 而 char 的长度就是一个字节.container_of 的值是两个地址相减,

刚说了 __mptr 是结构体中 list_head 节点的地址, offset 宏求的是 list_head 节点 MEMBER 在结构体 TYPE 中的偏移量, 那么 __mptr
减去它所在结构体中的偏移量, 就是结构体的首地址.

我们再总结下: 首先 member 是 type 类型中的 head_list 类型变量, 而 ptr 是某一个 type 类型变量中 member 成员所在的地址,
返回 ptr 所在结构体的首地址.

所以 list_entry(ptr, type, member) 宏的功能就是: 由结构体成员地址求结构体地址. 其中 ptr  是所求结构体中 list_head 成员指针,
type 是所求结构体类型, member 是结构体 list_head 成员名. 通过下图来总结一下:

![container_of](container_of.jpg)

继续列举一些双链表的常用操作：

###双向链表的遍历--list_for_each

//注:这里 prefetch 是 gcc 的一个优化选项, 也可以不要

```
    #define list_for_each(pos, head) \
         for (pos = (head)->next; prefetch(pos->next), pos != (head); \
                 pos = pos->next)
```


###生成双向链表的头结点——LIST_HEAD()

LIST_HEAD() -- 生成一个名为 name 的双向链表头节点

```
    #define LIST_HEAD(name) \
        struct list_head name = LIST_HEAD_INIT(name)

    #define LIST_HEAD_INIT(name) = { &(name), &(name) }

    static inline void INIT_LIST_HEAD(struct list_head *list)
    {
    　　list->next = list;
    　　list->prev = list;
    }
```

###插入操作 -- list_add()

将 new 所代表的结构体插入 head 所管理的双向链表的头节点 head 之后: (即插入表头)

```
    static inline void list_add(struct list_head *new, struct list_head *head)
    {
    　　__list_add(new, head, head->next);
    }

    static inline void __list_add( struct list_head *new, struct list_head *prev, struct list_head *next)
    {
    　　next->prev = new;
    　　new->next = next;
    　　new->prev = prev;
    　　prev->next = new;
    }
```

###删除结点

```
    static inline void list_del(struct list_head *entry)
    {
    　　__list_del(entry->prev, entry->next);
    　　entry->next = LIST_POISON1;
    　　entry->prev = LIST_POISON2;
    }

    static inline void __list_del(struct list_head * prev, struct list_head * next)
    {
    　　next->prev = prev;
    　　prev->next = next;
    }
```

判断链表是否为空（如果双向链表head为空则返回真，否则为假）——list_empty()

```
    static inline int list_empty(const struct list_head *head)
    {
    　　return head->next == head;
    }
```


##示例

```
/*
注：这个list.h 是为了配合示例程序而建的，内容来自：linux/include/linux/list.h 和相关文件
*/
#ifndef _LINUX_LIST_H
#define _LINUX_LIST_H

struct list_head {
         struct list_head *next, *prev;
};

#define LIST_HEAD_INIT(name) { &(name), &(name) }

#define offsetof(TYPE, MEMBER) ((size_t) &((TYPE *)0)->MEMBER)

#define container_of(ptr, type, member) ({                      \
        const typeof( ((type *)0)->member ) *__mptr = (ptr);    \
        (type *)( (char *)__mptr - offsetof(type,member) );})


static inline void INIT_LIST_HEAD(struct list_head *list)
{
        list->next = list;
        list->prev = list;
}

static inline void __list_add(struct list_head *new, struct list_head *prev,struct list_head *next)
{
        next->prev = new;
        new->next = next;
        new->prev = prev;
        prev->next = new;
}


static inline void list_add(struct list_head *new, struct list_head *head)
{
        __list_add(new, head, head->next);
}

static inline void __list_del(struct list_head * prev, struct list_head * next)
{
        next->prev = prev;
        prev->next = next;
}

static inline void list_del(struct list_head *entry)
{
        __list_del(entry->prev, entry->next);
        entry->next = NULL;
        entry->prev = NULL;
}


#define prefetch(x) __builtin_prefetch(x)

//注：这里prefetch 是gcc的一个优化，也可以不要
#define list_for_each(pos, head) \
         for (pos = (head)->next; prefetch(pos->next), pos != (head); \
                 pos = pos->next)

#define list_entry(ptr, type, member) \
         container_of(ptr, type, member)

#endif
```

在Linux内核中可以使用这个以类似驱动模块的形式加载到内核:(这里就不用使用自定义的 list.h 了)


```
    #include <linux/list.h>
    #include <linux/init.h>
    #include <linux/module.h>

    MODULE_LICENSE("GPL");

    #define MAX_NAME_LEN 32
    #define MAX_ID_LEN 10


    typedef struct stud
    {
        struct list_head list;
        char name[MAX_NAME_LEN];
        char stu_number[MAX_ID_LEN];
    }num_n_stu;

    static int my_main(void)
    {

        struct list_head head;
        num_n_stu stu_1;
        num_n_stu stu_2;
        num_n_stu *entry;

        struct list_head *p;
        INIT_LIST_HEAD(&head);

        strcpy(stu_1.name,"lisi");
        strcpy(stu_1.stu_number,"10000000");

        strcpy(stu_2.name,"zhangsan");
        strcpy(stu_2.stu_number,"10000001");

        list_add(&stu_1.list,&head);
        list_add(&stu_2.list,&head);

        list_del(&stu_2.list);

        list_for_each(p,&head)
        {
            entry=list_entry(p,struct stud,list);
            printk("name: %s\n",entry->name);
            printk("stu_number: %s\n",entry->stu_number);
        }
        list_del(&stu_1.list);
        return 0;

    }

    static void my_exit(void)
    {
        printk("my_exit ! \n");
    }

    module_init(my_main);
    module_exit(my_exit);
```

##哈希列表

由上图可以知道 hash 链表中存在两种结构体, 一种是hash表头, 一种是hash节点.

###组成

####表头

```
    struct hlist_head
    {
        struct hlist_node *first;
    };
```

表头里面只存放一个hlist_node的指针，指向链表。

####节点

    struct hlist_node
    {
        struct hlist_node *next;
        struct hlist_node **pprev;
    };

有两个指针, 所以链表是双链表. 但和一般的双链表又有点不一样, next 自然是指向链表的下一个节点, 但 pprev 则
不是指向当前节点的前一个节点, 而是指向当前节点的前一个节点的 next 指针. 所以 ppre 是二级指针. 

###为什么要设计成这样呢?

因为为了统一操作, 如果设计的和我们平时使用的双链表的话(prev 指向的是前一个节点),
那头节点和链表节点之间的操作就要重新定义一套(因为头结点结构体和链表节点结构体是不一样的). 所以干脆直接
指向前一个节点的 next 指针, next 的类型是 hlist_node*, first 的类型也是 hlist_node*. 这样就统一了链表
操作函数了.

###为什么头结点要设计的和链表节点不一样呢?

官方解释是为了节约空间, 因为一般来说哈希表中有非常多的表项, 即可能有上千个表项, 也即是有上千个 hlist_head.
如果头结点不用 pprev 则可以节约非常大的空间. 我个人认为还有种解释是头结点的pprev(如果有这个指针)用处不大.
因为所有的操作都是要通过哈希函数来算出值在哈希表中的位置, 然后再有链表中查找. 哈希链表本来就是个处理碰撞现
象的, 说明链表中的关键字通过哈希函数后能得到一样的值. 所以你不知道在链表中的哪个位置, 那头结点有 pprev 的话
你也没必要从后面开始查找(也许从前面查找开些, 也许是从后面). 也就是说对于头节点来说这个指针可有可无.

###添加

/*
 * 需要修改的元素地址:
 * 1. n->next, n->pprev
 * 2. next->prev
 * 3. 此操作之前, next 前一元素的 next
 */
static inline void hlist_add_before(struct hlist_node *n,
                                        struct hlist_node *next)
{
    //修正 n->pprev : 根据定义 pprev, n->pprev 为 next 之前元素->next 的地址, 而 next->pprev 正好是这个值
    n->pprev = next->pprev;
    //修正 n->next  : 根据 next 的定义 n->next 指向 next
    n->next = next;
    //修正 next->pprev : 根据 pprev 定义 &n->next
    next->pprev = &n->next;
    //修正 next 之前元素的 next : *(n->prev) 表示 next 前一元素的 next, 由之前的 next 更改为现在的 n
    //n 的前一指针的 next 指向 n
    *(n->pprev) = n;
}

/*
 * 需要修改的元素的地址:
 * 1. n->next, n->pprev
 * 2. prev->next
 * 3. 此操作之前, prev 下一个元素的 pprev
 */
static inline void hlist_add_behind(struct hlist_node *n,
                                    struct hlist_node *prev)
{
    n->next = prev->next;
    prev->next = n;
    n->pprev = &prev->next;

    if (n->next)
            n->next->pprev  = &n->next;
}

##参考

http://blog.csdn.net/yuzhihui_no1/article/details/38357737
http://blog.csdn.net/yuzhihui_no1/article/details/38357899

##附录

```
/* linux/list.h  循环双向链表*/
#ifndef _LINUX_LIST_H
#define _LINUX_LIST_H

#include <linux/types.h>
#include <linux/stddef.h>
#include <linux/poison.h>
#include <linux/const.h>
#include <linux/kernel.h>


#define CONFIG_ILLEGAL_POINTER_VALUE 0

#ifdef __ASSEMBLY__
#define _AC(X,Y)        X
#define _AT(T,X)        X
#else
#define __AC(X,Y)       (X##Y)
#define _AC(X,Y)        __AC(X,Y)
#define _AT(T,X)        ((T)(X))
#endif

/*
 * Architectures might want to move the poison pointer offset
 * into some well-recognized area such as 0xdead000000000000,
 * that is also not mappable by user-space exploits:
 */
#ifdef CONFIG_ILLEGAL_POINTER_VALUE
# define POISON_POINTER_DELTA _AC(CONFIG_ILLEGAL_POINTER_VALUE, UL)
#else
# define POISON_POINTER_DELTA 0
#endif
/*
 * These are non-NULL pointers that will result in page faults
 * under normal circumstances, used to verify that nobody uses
 * non-initialized list entries.
 *
 * #define LIST_POISON1  ((void *) 0x00100100)
 * #define LIST_POISON2  ((void *) 0x00200200)
 */
#define LIST_POISON1  ((void *) 0x00100100 + POISON_POINTER_DELTA)
#define LIST_POISON2  ((void *) 0x00200200 + POISON_POINTER_DELTA)

/*
 * Simple doubly linked list implementation.
 *
 * Some of the internal functions ("__xxx") are useful when
 * manipulating whole lists rather than single entries, as
 * sometimes we already know the next/prev entries and we can
 * generate better code by using them directly rather than
 * using the generic single-entry routines.
 */

#define LIST_HEAD_INIT(name) { &(name), &(name) }

#define LIST_HEAD(name) \
        struct list_head name = LIST_HEAD_INIT(name)

static inline void INIT_LIST_HEAD(struct list_head *list)
{
        list->next = list;
        list->prev = list;
}

/*
 * Insert a new entry between two known consecutive entries.
 *
 * This is only for internal list manipulation where we know
 * the prev/next entries already!
 */
#ifndef CONFIG_DEBUG_LIST
static inline void __list_add(struct list_head *new,
                              struct list_head *prev,
                              struct list_head *next)
{
        next->prev = new;
        new->next = next;
        new->prev = prev;
        prev->next = new;
}
#else
extern void __list_add(struct list_head *new,
                              struct list_head *prev,
                              struct list_head *next);
#endif

/**
 * list_add - add a new entry
 * @new: new entry to be added
 * @head: list head to add it after
 *
 * Insert a new entry after the specified head.
 * This is good for implementing stacks.
 */
static inline void list_add(struct list_head *new, struct list_head *head)
{
        __list_add(new, head, head->next);
}


/**
 * list_add_tail - add a new entry
 * @new: new entry to be added
 * @head: list head to add it before
 *
 * Insert a new entry before the specified head.
 * This is useful for implementing queues.
 */
static inline void list_add_tail(struct list_head *new, struct list_head *head)
{
        __list_add(new, head->prev, head);
}

/*
 * Delete a list entry by making the prev/next entries
 * point to each other.
 *
 * This is only for internal list manipulation where we know
 * the prev/next entries already!
 */
static inline void __list_del(struct list_head * prev, struct list_head * next)
{
        next->prev = prev;
        prev->next = next;
}

/**
 * list_del - deletes entry from list.
 * @entry: the element to delete from the list.
 * Note: list_empty() on entry does not return true after this, the entry is
 * in an undefined state.
 */
#ifndef CONFIG_DEBUG_LIST
static inline void __list_del_entry(struct list_head *entry)
{
        __list_del(entry->prev, entry->next);
}

static inline void list_del(struct list_head *entry)
{
        __list_del(entry->prev, entry->next);
        entry->next = LIST_POISON1;
        entry->prev = LIST_POISON2;
}
#else
extern void __list_del_entry(struct list_head *entry);
extern void list_del(struct list_head *entry);
#endif

/**
 * list_replace - replace old entry by new one
 * @old : the element to be replaced
 * @new : the new element to insert
 *
 * If @old was empty, it will be overwritten.
 * 让　new 接管 old->prev, old->next, old->prev=new, old->next=new;
 * 因此在此处 old 成为一个环
 */
static inline void list_replace(struct list_head *old,
                                struct list_head *new)
{
        new->next = old->next;
        new->next->prev = new;
        new->prev = old->prev;
        new->prev->next = new;
}

static inline void list_replace_init(struct list_head *old,
                                        struct list_head *new)
{
        list_replace(old, new);
        INIT_LIST_HEAD(old);
}

/**
 * list_del_init - deletes entry from list and reinitialize it.
 * @entry: the element to delete from the list.
 */
static inline void list_del_init(struct list_head *entry)
{
        __list_del_entry(entry);
        INIT_LIST_HEAD(entry);
}

/**
 * list_move - delete from one list and add as another's head
 * @list: the entry to move
 * @head: the head that will precede our entry
 */
static inline void list_move(struct list_head *list, struct list_head *head)
{
        __list_del_entry(list);
        list_add(list, head);
}

/**
 * list_move_tail - delete from one list and add as another's tail
 * @list: the entry to move
 * @head: the head that will follow our entry
 */
static inline void list_move_tail(struct list_head *list,
                                  struct list_head *head)
{
        __list_del_entry(list);
        list_add_tail(list, head);
}

/**
 * list_is_last - tests whether @list is the last entry in list @head
 * @list: the entry to test
 * @head: the head of the list
 */
static inline int list_is_last(const struct list_head *list,
                                const struct list_head *head)
{
        return list->next == head;
}

/**
 * list_empty - tests whether a list is empty
 * @head: the list to test.
 */
static inline int list_empty(const struct list_head *head)
{
        return head->next == head;
}

/**
 * list_empty_careful - tests whether a list is empty and not being modified
 * @head: the list to test
 *
 * Description:
 * tests whether a list is empty _and_ checks that no other CPU might be
 * in the process of modifying either member (next or prev)
 *
 * NOTE: using list_empty_careful() without synchronization
 * can only be safe if the only activity that can happen
 * to the list entry is list_del_init(). Eg. it cannot be used
 * if another CPU could re-list_add() it.
 */
static inline int list_empty_careful(const struct list_head *head)
{
        struct list_head *next = head->next;
        return (next == head) && (next == head->prev);
}

/**
 * list_rotate_left - rotate the list to the left
 * @head: the head of the list
 */
static inline void list_rotate_left(struct list_head *head)
{
        struct list_head *first;

        if (!list_empty(head)) {
                first = head->next;
                list_move_tail(first, head);
        }
}

/**
 * list_is_singular - tests whether a list has just one entry.
 * @head: the list to test.
 */
static inline int list_is_singular(const struct list_head *head)
{
        return !list_empty(head) && (head->next == head->prev);
}

static inline void __list_cut_position(struct list_head *list,
                struct list_head *head, struct list_head *entry)
{
        struct list_head *new_first = entry->next;
        list->next = head->next;
        list->next->prev = list;
        list->prev = entry;
        entry->next = list;
        head->next = new_first;
        new_first->prev = head;
}

/**
 * list_cut_position - cut a list into two
 * @list: a new list to add all removed entries
 * @head: a list with entries
 * @entry: an entry within head, could be the head itself
 *      and if so we won't cut the list
 *
 * This helper moves the initial part of @head, up to and
 * including @entry, from @head to @list. You should
 * pass on @entry an element you know is on @head. @list
 * should be an empty list or a list you do not care about
 * losing its data.
 *
 */
static inline void list_cut_position(struct list_head *list,
                struct list_head *head, struct list_head *entry)
{
        if (list_empty(head))
                return;
        if (list_is_singular(head) &&
                (head->next != entry && head != entry))
                return;
        if (entry == head)
                INIT_LIST_HEAD(list);
        else
                __list_cut_position(list, head, entry);
}

static inline void __list_splice(const struct list_head *list,
                                 struct list_head *prev,
                                 struct list_head *next)
{
        struct list_head *first = list->next;
        struct list_head *last = list->prev;

        first->prev = prev;
        prev->next = first;

        last->next = next;
        next->prev = last;
}

/**
 * list_splice - join two lists, this is designed for stacks
 * @list: the new list to add.
 * @head: the place to add it in the first list.
 */
static inline void list_splice(const struct list_head *list,
                                struct list_head *head)
{
        if (!list_empty(list))
                __list_splice(list, head, head->next);
}

/**
 * list_splice_tail - join two lists, each list being a queue
 * @list: the new list to add.
 * @head: the place to add it in the first list.
 */
static inline void list_splice_tail(struct list_head *list,
                                struct list_head *head)
{
        if (!list_empty(list))
                __list_splice(list, head->prev, head);
}

/**
 * list_splice_init - join two lists and reinitialise the emptied list.
 * @list: the new list to add.
 * @head: the place to add it in the first list.
 *
 * The list at @list is reinitialised
 */
static inline void list_splice_init(struct list_head *list,
                                    struct list_head *head)
{
        if (!list_empty(list)) {
                __list_splice(list, head, head->next);
                INIT_LIST_HEAD(list);
        }
}

/**
 * list_splice_tail_init - join two lists and reinitialise the emptied list
 * @list: the new list to add.
 * @head: the place to add it in the first list.
 *
 * Each of the lists is a queue.
 * The list at @list is reinitialised
 */
static inline void list_splice_tail_init(struct list_head *list,
                                         struct list_head *head)
{
        if (!list_empty(list)) {
                __list_splice(list, head->prev, head);
                INIT_LIST_HEAD(list);
        }
}

/**
 * list_entry - get the struct for this entry
 * @ptr:        the &struct list_head pointer.
 * @type:       the type of the struct this is embedded in.
 * @member:     the name of the list_head within the struct.
 */
#define list_entry(ptr, type, member) \
        container_of(ptr, type, member)

/**
 * list_first_entry - get the first element from a list
 * @ptr:        the list head to take the element from.
 * @type:       the type of the struct this is embedded in.
 * @member:     the name of the list_head within the struct.
 *
 * Note, that list is expected to be not empty.
 */
#define list_first_entry(ptr, type, member) \
        list_entry((ptr)->next, type, member)

/**
 * list_last_entry - get the last element from a list
 * @ptr:        the list head to take the element from.
 * @type:       the type of the struct this is embedded in.
 * @member:     the name of the list_head within the struct.
 *
 * Note, that list is expected to be not empty.
 */
#define list_last_entry(ptr, type, member) \
        list_entry((ptr)->prev, type, member)

/**
 * list_first_entry_or_null - get the first element from a list
 * @ptr:        the list head to take the element from.
 * @type:       the type of the struct this is embedded in.
 * @member:     the name of the list_head within the struct.
 *
 * Note that if the list is empty, it returns NULL.
 */
#define list_first_entry_or_null(ptr, type, member) \
        (!list_empty(ptr) ? list_first_entry(ptr, type, member) : NULL)

/**
 * list_next_entry - get the next element in list
 * @pos:        the type * to cursor
 * @member:     the name of the list_head within the struct.
 */
#define list_next_entry(pos, member) \
        list_entry((pos)->member.next, typeof(*(pos)), member)

/**
 * list_prev_entry - get the prev element in list
 * @pos:        the type * to cursor
 * @member:     the name of the list_head within the struct.
 */
#define list_prev_entry(pos, member) \
        list_entry((pos)->member.prev, typeof(*(pos)), member)

/**
 * list_for_each        -       iterate over a list
 * @pos:        the &struct list_head to use as a loop cursor.
 * @head:       the head for your list.
 */
#define list_for_each(pos, head) \
        for (pos = (head)->next; pos != (head); pos = pos->next)

/**
 * list_for_each_prev   -       iterate over a list backwards
 * @pos:        the &struct list_head to use as a loop cursor.
 * @head:       the head for your list.
 */
#define list_for_each_prev(pos, head) \
        for (pos = (head)->prev; pos != (head); pos = pos->prev)

/**
 * list_for_each_safe - iterate over a list safe against removal of list entry
 * @pos:        the &struct list_head to use as a loop cursor.
 * @n:          another &struct list_head to use as temporary storage
 * @head:       the head for your list.
 */
#define list_for_each_safe(pos, n, head) \
        for (pos = (head)->next, n = pos->next; pos != (head); \
                pos = n, n = pos->next)

/**
 * list_for_each_prev_safe - iterate over a list backwards safe against removal of list entry
 * @pos:        the &struct list_head to use as a loop cursor.
 * @n:          another &struct list_head to use as temporary storage
 * @head:       the head for your list.
 */
#define list_for_each_prev_safe(pos, n, head) \
        for (pos = (head)->prev, n = pos->prev; \
             pos != (head); \
             pos = n, n = pos->prev)

/**
 * list_for_each_entry  -       iterate over list of given type
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 */
#define list_for_each_entry(pos, head, member)                          \
        for (pos = list_first_entry(head, typeof(*pos), member);        \
             &pos->member != (head);                                    \
             pos = list_next_entry(pos, member))

/**
 * list_for_each_entry_reverse - iterate backwards over list of given type.
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 */
#define list_for_each_entry_reverse(pos, head, member)                  \
        for (pos = list_last_entry(head, typeof(*pos), member);         \
             &pos->member != (head);                                    \
             pos = list_prev_entry(pos, member))

/**
 * list_prepare_entry - prepare a pos entry for use in list_for_each_entry_continue()
 * @pos:        the type * to use as a start point
 * @head:       the head of the list
 * @member:     the name of the list_head within the struct.
 *
 * Prepares a pos entry for use as a start point in list_for_each_entry_continue().
 */
#define list_prepare_entry(pos, head, member) \
        ((pos) ? : list_entry(head, typeof(*pos), member))

/**
 * list_for_each_entry_continue - continue iteration over list of given type
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Continue to iterate over list of given type, continuing after
 * the current position.
 */
#define list_for_each_entry_continue(pos, head, member)                 \
        for (pos = list_next_entry(pos, member);                        \
             &pos->member != (head);                                    \
             pos = list_next_entry(pos, member))

/**
 * list_for_each_entry_continue_reverse - iterate backwards from the given point
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Start to iterate over list of given type backwards, continuing after
 * the current position.
 */
#define list_for_each_entry_continue_reverse(pos, head, member)         \
        for (pos = list_prev_entry(pos, member);                        \
             &pos->member != (head);                                    \
             pos = list_prev_entry(pos, member))

/**
 * list_for_each_entry_from - iterate over list of given type from the current point
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Iterate over list of given type, continuing from current position.
 */
#define list_for_each_entry_from(pos, head, member)                     \
        for (; &pos->member != (head);                                  \
             pos = list_next_entry(pos, member))

/**
 * list_for_each_entry_safe - iterate over list of given type safe against removal of list entry
 * @pos:        the type * to use as a loop cursor.
 * @n:          another type * to use as temporary storage
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 */
#define list_for_each_entry_safe(pos, n, head, member)                  \
        for (pos = list_first_entry(head, typeof(*pos), member),        \
                n = list_next_entry(pos, member);                       \
             &pos->member != (head);                                    \
             pos = n, n = list_next_entry(n, member))

/**
 * list_for_each_entry_safe_continue - continue list iteration safe against removal
 * @pos:        the type * to use as a loop cursor.
 * @n:          another type * to use as temporary storage
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Iterate over list of given type, continuing after current point,
 * safe against removal of list entry.
 */
#define list_for_each_entry_safe_continue(pos, n, head, member)                 \
        for (pos = list_next_entry(pos, member),                                \
                n = list_next_entry(pos, member);                               \
             &pos->member != (head);                                            \
             pos = n, n = list_next_entry(n, member))

/**
 * list_for_each_entry_safe_from - iterate over list from current point safe against removal
 * @pos:        the type * to use as a loop cursor.
 * @n:          another type * to use as temporary storage
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Iterate over list of given type from current point, safe against
 * removal of list entry.
 */
#define list_for_each_entry_safe_from(pos, n, head, member)                     \
        for (n = list_next_entry(pos, member);                                  \
             &pos->member != (head);                                            \
             pos = n, n = list_next_entry(n, member))

/**
 * list_for_each_entry_safe_reverse - iterate backwards over list safe against removal
 * @pos:        the type * to use as a loop cursor.
 * @n:          another type * to use as temporary storage
 * @head:       the head for your list.
 * @member:     the name of the list_head within the struct.
 *
 * Iterate backwards over list of given type, safe against removal
 * of list entry.
 */
#define list_for_each_entry_safe_reverse(pos, n, head, member)          \
        for (pos = list_last_entry(head, typeof(*pos), member),         \
                n = list_prev_entry(pos, member);                       \
             &pos->member != (head);                                    \
             pos = n, n = list_prev_entry(n, member))

/**
 * list_safe_reset_next - reset a stale list_for_each_entry_safe loop
 * @pos:        the loop cursor used in the list_for_each_entry_safe loop
 * @n:          temporary storage used in list_for_each_entry_safe
 * @member:     the name of the list_head within the struct.
 *
 * list_safe_reset_next is not safe to use in general if the list may be
 * modified concurrently (eg. the lock is dropped in the loop body). An
 * exception to this is if the cursor element (pos) is pinned in the list,
 * and list_safe_reset_next is called after re-taking the lock and before
 * completing the current iteration of the loop body.
 */
#define list_safe_reset_next(pos, n, member)                            \
        n = list_next_entry(pos, member)

/*
 * Double linked lists with a single pointer list head.
 * Mostly useful for hash tables where the two pointer list head is
 * too wasteful.
 * You lose the ability to access the tail in O(1).
 */

#define HLIST_HEAD_INIT { .first = NULL }
#define HLIST_HEAD(name) struct hlist_head name = {  .first = NULL }
#define INIT_HLIST_HEAD(ptr) ((ptr)->first = NULL)
static inline void INIT_HLIST_NODE(struct hlist_node *h)
{
        h->next = NULL;
        h->pprev = NULL;
}

static inline int hlist_unhashed(const struct hlist_node *h)
{
        return !h->pprev;
}

static inline int hlist_empty(const struct hlist_head *h)
{
        return !h->first;
}

static inline void __hlist_del(struct hlist_node *n)
{
        struct hlist_node *next = n->next;
        struct hlist_node **pprev = n->pprev;
        *pprev = next;
        if (next)
                next->pprev = pprev;
}

static inline void hlist_del(struct hlist_node *n)
{
        __hlist_del(n);
        n->next = LIST_POISON1;
        n->pprev = LIST_POISON2;
}

static inline void hlist_del_init(struct hlist_node *n)
{
        if (!hlist_unhashed(n)) {
                __hlist_del(n);
                INIT_HLIST_NODE(n);
        }
}

//头前插入
static inline void hlist_add_head(struct hlist_node *n, struct hlist_head *h)
{
        struct hlist_node *first = h->first;
        n->next = first;
        if (first)
                first->pprev = &n->next;
        h->first = n;
        n->pprev = &h->first;
}

/* next must be != NULL */
//要让 next 之前的元素, n 及 next 的 prev, next 都指向正确的地址
static inline void hlist_add_before(struct hlist_node *n,
                                        struct hlist_node *next)
{
        n->pprev = next->pprev;
        n->next = next;
        next->pprev = &n->next;
        //n 的前一指针的 next 指向 n
        *(n->pprev) = n;
}

//要让 n, prev, prev 之后的元素指向正确的元素
static inline void hlist_add_behind(struct hlist_node *n,
                                    struct hlist_node *prev)
{
        n->next = prev->next;
        prev->next = n;
        n->pprev = &prev->next;

        if (n->next)
                n->next->pprev  = &n->next;
}

/* after that we'll appear to be on some hlist and hlist_del will work */
static inline void hlist_add_fake(struct hlist_node *n)
{
        n->pprev = &n->next;
}

/*
 * Move a list from one list head to another. Fixup the pprev
 * reference of the first entry if it exists.
 */
static inline void hlist_move_list(struct hlist_head *old,
                                   struct hlist_head *new)
{
        new->first = old->first;
        if (new->first)
                new->first->pprev = &new->first;
        old->first = NULL;
}

#define hlist_entry(ptr, type, member) container_of(ptr,type,member)

#define hlist_for_each(pos, head) \
        for (pos = (head)->first; pos ; pos = pos->next)

#define hlist_for_each_safe(pos, n, head) \
        for (pos = (head)->first; pos && ({ n = pos->next; 1; }); \
             pos = n)

#define hlist_entry_safe(ptr, type, member) \
        ({ typeof(ptr) ____ptr = (ptr); \
           ____ptr ? hlist_entry(____ptr, type, member) : NULL; \
        })

/**
 * hlist_for_each_entry - iterate over list of given type
 * @pos:        the type * to use as a loop cursor.
 * @head:       the head for your list.
 * @member:     the name of the hlist_node within the struct.
 */
#define hlist_for_each_entry(pos, head, member)                         \
        for (pos = hlist_entry_safe((head)->first, typeof(*(pos)), member);\
             pos;                                                       \
             pos = hlist_entry_safe((pos)->member.next, typeof(*(pos)), member))

/**
 * hlist_for_each_entry_continue - iterate over a hlist continuing after current point
 * @pos:        the type * to use as a loop cursor.
 * @member:     the name of the hlist_node within the struct.
 */
#define hlist_for_each_entry_continue(pos, member)                      \
        for (pos = hlist_entry_safe((pos)->member.next, typeof(*(pos)), member);\
             pos;                                                       \
             pos = hlist_entry_safe((pos)->member.next, typeof(*(pos)), member))

/**
 * hlist_for_each_entry_from - iterate over a hlist continuing from current point
 * @pos:        the type * to use as a loop cursor.
 * @member:     the name of the hlist_node within the struct.
 */
#define hlist_for_each_entry_from(pos, member)                          \
        for (; pos;                                                     \
             pos = hlist_entry_safe((pos)->member.next, typeof(*(pos)), member))

/**
 * hlist_for_each_entry_safe - iterate over list of given type safe against removal of list entry
 * @pos:        the type * to use as a loop cursor.
 * @n:          another &struct hlist_node to use as temporary storage
 * @head:       the head for your list.
 * @member:     the name of the hlist_node within the struct.
 */
#define hlist_for_each_entry_safe(pos, n, head, member)                 \
        for (pos = hlist_entry_safe((head)->first, typeof(*pos), member);\
             pos && ({ n = pos->member.next; 1; });                     \
             pos = hlist_entry_safe(n, typeof(*pos), member))

#endif

```


