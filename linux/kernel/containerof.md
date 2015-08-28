
在linux内核链表中, 有两个点我认为设计的比较巧妙.

第一个是链表项中没有数据项, 而是在要使用链表时, 定义个数据项结构体, 然后把链表项结构体定义为数据项结构体的
成员(这个将在下一篇博文中详细阐述). 如果要对数据项结构体中数据进行访问, 则通过本文要分析的函数(或者说宏)来
解决.

第二个是 container_of(ptr,  type,  member) 这个宏, 这个宏的作用是已知一个结果体的类型 type, 和一个结构体的
成员变量member, (ptr = &member). 就可以求的出结构体的首地址. 其实这是解决上一个设计巧妙的地方所带来的问题.

先来看下这个宏的用处:

假设: 有个结构体typedef  struct  test{......}T; 其结构体成员都知道的(假设里面有个成员变量为 member, 他所在
的结构体中的位置随意). 现在已知某个(未知结构体变量名)结构体变量中的成员变量 member, 求该结构体变量中的其他
成员变量.

分析: 求其他结构体变量中的成员, 其实只要求出 member 所在的结构体变量的首地址即可, 通过首地址指针一个个遍历.

答案: 用 container_of() 宏来求解. 这个宏就是用来求已知某个结构体变量中的某个成员所在的结构体变量首地址.
member 所在的结构体变量首地址 = container_of(&member, T, member);

接下来分析下container_of()宏的实现:

        #define list_entry(ptr,  type,  member) /
                ((type *)((char *)(ptr)-(unsigned long)(&((type *)0)->member)))

先来逐个分析下:

减号右边分析: (unsigned long)(&((type*)0)->member)     (type*)0:  把 0 地址强制转换成 type 结构体的地址, 表示
0 地址处存放了 type 类型的结构体变量, 为什么在 0 处强转为结构体地址, 这也是个设计巧妙点; ((type*)0)->member:
这个表示指向结构体变量中的成员 member; &(((type*)0)->member)): 这个当然是结构体变量中 member 的地址了, 但是这
里转了下弯, 这是不仅表示是结构体变量中成员 member 的地址, 还表示了结构体变量中的 member 成员到结构体变量的首
地址的距离, 也就是说 member 相对于首地址的偏移量. 偏移量本应该是这么算的: member的地址 - 首地址. 但首地址强转
在 0 处, 所以 member 的地址就是偏移量. (unsigned long)是把偏移量强转为整型.

减号左边的就很好分析了. 用实际的 member 地址减去偏移量, 就得到了变量的首地址了. 然后再强转为结构体类型. (char*)
是因为前面的偏移量是用unsigned long来表示的. 大概原理就是这样的了. 其实很简单, 关键点是在0处强转为结构体类型,
以至于得到 member 的地址就是偏移量. 


###自定义结构体

struct dataNode {
	struct hData data;
	struct hlist_node *node
}


了解内核中链表或者哈希链表结构的都知道, 里面是没有数据项的, 要我们自己使用时, 自行定义数据结构体(如文中的struct dataNode结构体),
然后包含内核中定义链表结构体(struct hlist_node *node). 而我们定义的数据结构体(dataNode)是靠内核中定义的链表结构
体节点(struct hlist_node *node)来连接的(我们对这种链表结构的操作一般都是使用内核设计好的一些操作宏或者函数, 这些
宏或者函数都是对没有数据项的链表节点进行操作的). 所以一般是已知内核链表节点(struct hlist_node *node)通过container_of()
来求出数据节点(struct dataNode)的头指针.

问题来了, 如果已知数据节点中的成员 node 是可以推导出 dataNode 指针的. 但如果仅仅是知道 node 所指向的数据, 则是不能
由 container_of() 推导出.  (为什么不能推导出来, 稍微看下就知道, 因为这样就相当于是个单链表了, 单链表是无法推出前个
节点的地址)而我们程序中操作时, 往往是传递过来的是某个链表节点也就是 node 指向的数据. 所以这种链表的结构是个误区, 要
多小心. ?????


###OpenvSwitch 中的实现

#define list_entry(ptr,  type,  member) /
        ((type *)((char *)(ptr)-(unsigned long)(&((type *)0)->member)))

#define hlist_entry_safe(ptr, type, member) \
    ({ typeof(ptr) ____ptr = (ptr); \
          ____ptr ? hlist_entry(____ptr, type, member) : NULL; \
               })

#define hlist_for_each_entry_rcu(pos, head, member)         \
        for (pos = hlist_entry_safe (rcu_dereference_raw(hlist_first_rcu(head)),\
                typeof(*(pos)), member);            \
            pos;                            \
            pos = hlist_entry_safe(rcu_dereference_raw(hlist_next_rcu(\
                 &(pos)->member)), typeof(*(pos)), member))
        )))))

###参考
http://blog.csdn.net/yuzhihui_no1/article/details/38407443
http://blog.csdn.net/yuzhihui_no1/article/details/38356393
