

在内核中 sk_buff 表示一个网络数据包, 它是一个双向链表, 而链表头就是 sk_buff_head, 而 sk_buff 的
内存布局可以分作 3 个段, 

* sk_buff 自身
* linear-data buff
* paged-data buff(也就是skb_shared_info)

如下示意图:

![skb 结构示意图](skb_buff_struct.jpg)


##skb 结构体

```
    struct sk_buff {
        /* These two members must be first. */
        struct sk_buff *next;
        struct sk_buff *prev;
        //老版本(2.6以前)应该还有个字段： sk_buff_head *list 即每个sk_buff结构都有个指针指向头节点

        struct sock *sk; //表示从属于那个socket，主要是被4层用到。

        ktime_t tstamp; //表示这个skb被接收的时间。

        //这个表示一个网络设备, 当 skb 为输出时它表示 skb 将要输出的设备, 当接收时, 它表示输入设备.
        //要注意, 这个设备有可能会是虚拟设备(在3层以上看来)
        struct net_device *dev;

        //这里其实应该是 dst_entry 类型，不知道为什么内核要改为 ul. 这个域主要用于路由子系统. 这个数
        //据结构保存了一些路由相关信息
        unsigned long _skb_dst;

        #ifdef CONFIG_XFRM
        struct sec_path *sp;
        #endif

        char cb[48]; //这个域很重要, 我们下面会详细说明. 这里只需要知道这个域是保存每层的控制信息的就够了.

        //这个长度表示当前的 skb 中的数据的长度, 这个长度既包括 buf 中的数据又包括保存在 skb_shared_info 中的数据.
        //这个值是会随着从一层到另一层而改变的, 因为分片数据长度不变, 从L2到L4时, len 要减去帧头大小和网络头大小;
        //从 L4 到 L2 则相反, 要加上帧头和网络头大小.
        unsigned int len,

        data_len; //这个长度只表示 skb_shared_info 中的长度. 所以 len = (tail - data) + data_len;

        __u16 mac_len, //这个长度表示 mac 头的长度(2层的头的长度)

        hdr_len; //这个主要用于 clone 的时候, 它表示 clone 的 skb 的头的长度。


        //接下来是校验相关的域
        union {
        __wsum csum;
            struct {
            __u16 csum_start;
            __u16 csum_offset;
            };
        };
        //优先级, 主要用于QOS
        __u32 priority;
        kmemcheck_bitfield_begin(flags1);

        //接下来是一些标志位
        __u8 local_df:1, //首先是是否可以本地分片的标志

        //为 1 说明头可能被 clone, 或者自己是个克隆的结构体; 同理被克隆时, 自身 skb 和克隆 skb 的 cloned 都要置 1
        cloned:1,

        //这个表示校验相关的一个标记,表示硬件驱动是否为我们已经进行了校验
        ip_summed:2,

        //1. 这个域如果为 1, 则说明这个 skb 的头域指针已经分配完毕, 因此这个时候计算头的长度只需要 head 和 data 的差就可以了.
        //2. 标识 payload 是否被单独引用, 不存在协议首部.
        nohdr:1,

        nfctinfo:3;         //如果被引用, 则决不能再修改协议首部, 也不能通过 skb->data 来访问协议首部.
        __u8 pkt_type:3,    //主要是表示数据包的类型, 比如多播, 单播, 回环等等.
        fclone:2,           //这个域是一个 clone 标记. 主要是在 fast clone 中被设置.

        ipvs_property:1,    //ipvs拥有的域。

        peeked:1,           //这个域应该是 udp 使用的一个域. 表示只是查看数据.

        nf_trace:1;         //netfilter使用的域. 是一个 trace 标记

        __be16 protocol:16; //这个表示 L3 层的协议. 比如 IP, IPV6 等等.

        kmemcheck_bitfield_end(flags1);

        //skb的析构函数，一般都是设置为 sock_rfree 或者 sock_wfree.
        void (*destructor)(struct sk_buff *skb);

        ///netfilter相关的域。
    #if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
        struct nf_conntrack *nfct;
        struct sk_buff *nfct_reasm;
    #endif

    #ifdef CONFIG_BRIDGE_NETFILTER
        struct nf_bridge_info *nf_bridge;
    #endif

        int iif;            //接收设备的index。

    //流量控制的相关域。
    #ifdef CONFIG_NET_SCHED
        __u16 tc_index; /* traffic control index */

    #ifdef CONFIG_NET_CLS_ACT

        __u16 tc_verd; /* traffic control verdict */
    #endif
    #endif

        kmemcheck_bitfield_begin(flags2);
        //多队列设备的映射, 也就是说映射到哪个队列.
        __u16 queue_mapping:16;
    #ifdef CONFIG_IPV6_NDISC_NODETYPE
        __u8 ndisc_nodetype:2;
    #endif
        kmemcheck_bitfield_end(flags2);

    /* 0/14 bit hole */

    #ifdef CONFIG_NET_DMA
        dma_cookie_t dma_cookie;
    #endif

    #ifdef CONFIG_NETWORK_SECMARK
        __u32 secmark;
    #endif

        __u32 mark;                         //skb的标记.

        __u16 vlan_tci;                     //vlan的控制tag.

        sk_buff_data_t transport_header;    //传输层的头
        sk_buff_data_t network_header;      //网络层的头
        sk_buff_data_t mac_header;          //链路层的头。

        /* These elements must be at the end, see alloc_skb() for details.  */
        sk_buff_data_t tail;                //指向数据区中实际数据结束的位置
        sk_buff_data_t end;                 //指向数据区中结束的位置(非实际数据区域结束位置)
        unsigned char *head,                //指向数据区中开始的位置(非实际数据区域开始位置)
        *data;                              //指向数据区中实际数据开始的位置

        unsigned int truesize;              //这个表示整个 skb 的大小,  truesize = end - head + sizeof(sk_buff)
        atomic_t users;                     //skb 的引用计数, skb 被克隆或引用的次数, 在内存申请和克隆时会用到
    };
```

NOTE:

>在老的内核里面 sk_buff 会有一个 list 域直接指向 sk_buff_head 也就是链表头, 现在在 2.6.33 里面这个域已经被删除了.

####sk_buff->len

表示当前协议数据包的长度. 它包括主缓冲区中的数据长度(data指针指向它)和分片中的数据长度. 比如, 处在网络层, len 指
的是 ip 包的长度, 如果包已经到了应用层, 则 len 是应用层头部和数据载荷的长度.

####sk_buff->data_len

data_len 只计算分片中数据的长度, 即 skb_shared_info 中有效数据总长度(包括 frag_list, frags[] 中的扩展数据),一般为 0

####sk_buff->truesize

这是缓冲区的总长度, 包括 sk_buff 结构和数据部分. 如果申请一个 len 字节的缓冲区, alloc_skb 函数会把它初始化成
len+sizeof(sk_buff). 当 skb->len 变化时, 这个变量也会变化.

####char cb[48]

这个字段是 skb 信息控制块, 也就是存储每层的一些协议信息, 当数据包在哪一层时, 存储的就是哪一层协议信息.
这个字段由数据包所在层使用和维护, 如果要访问本层协议信息, 可以通过用一些宏来操作这个成员字段. 如:

    #define TCP_SKB_CB(__skb)  ((struct tcp_skb_cb *)&((__skb)->cb[0]))
    #define FRAG_CB(skb) ((struct ipfrag_skb_cb *)((skb)->cb))

####_u8 fclone:2

这是个克隆状态标志, 到 sk_buff 结构内存申请时会使用到. 这里提前讲下:

* 若 fclone = SKB_FCLONE_UNAVAILABLE, 则表明 skb 未被克隆;
* 若 fclone = SKB_FCLONE_ORIG, 则表明是从 skbuff_fclone_cache 缓存池(这个缓存池上分配内存时, 每次都分配一对 skb 内存)中分配的父 skb, 可以被克隆;
* 若 fclone = SKB_FCLONE_CLONE, 则表明是在 skbuff_fclone_cache 分配的子 skb, 从父 skb 克隆得到的;

####atomic_t users

这是个引用计数, 表明了有多少实体引用了这个 skb. 其作用就是在销毁 skb 结构体时, 先查看下 users 是否为零, 若不为零,
则调用函数递减下引用计数 users 即可; 当某一次销毁时, users 为零才真正释放内存空间. 有两个操作函数:

* atomic_inc(): 引用计数增加 1;
* atomic_dec(): 引用计数减去 1；


##skb_share_info

这个分片结构体和 sk_buff 结构的数据区是一体的, 所以在各种操作时都把他们两个结构看做是一个来操作. 比如:
为 sk_buff 结构的数据区申请和释放空间时, 分片结构也会跟着该数据区一起分配和释放. 而克隆时, sk_buff 的
数据区和分片结构都由分片结构中的 dataref 成员字段来标识是否被引用.

```
    struct skb_shared_info {
        atomic_t    dataref;        //用于数据区的引用计数, 克隆一个 skb 结构体时, 会增加一个引用计数
        unsigned short  nr_frags;   //表示有多少个分片结构
        unsigned short  gso_size;
    #ifdef CONFIG_HAS_DMA
        dma_addr_t  dma_head;
    #endif
        /* Warning: this field is not always filled in (UFO)! */
        unsigned short  gso_segs;
        unsigned short  gso_type;           // 分片的类型
        __be32          ip6_frag_id;
        union skb_shared_tx tx_flags;
        struct sk_buff  *frag_list;         // 这也是一种类型的分配数据
        struct skb_shared_hwtstamps hwtstamps;
        skb_frag_t  frags[MAX_SKB_FRAGS];   //这是个比较重要的数组
    #ifdef CONFIG_HAS_DMA
        dma_addr_t  dma_maps[MAX_SKB_FRAGS];
    #endif
        /* Intermediate layers must ensure that destructor_arg
         * remains valid until skb destructor */
        void *      destructor_arg;
    };
```

从上图也可以看出来分片结构和 sk_buff 的数据区连在一起, end 指针的下个字节就是分片结构的开始位置. 那访问分片结构时,
可以直接用 end 指针作为这个分片结构体的开始(记得要强转成分片结构体)或者用内核定义好的宏

    #define skb_shinfo(SKB) ((struct skb_shared_info *)((SKB)->end))

其中有个成员字段非常重要: skb_frag_t  frags[MAX_SKB_FRAGS]; 其实这就和分片结构的数据区有关. 下面来讲下这个数字中
的元素结构体:

```
    /* To allow 64K frame to be packed as single skb without frag_list we
    * require 64K/PAGE_SIZE pages plus 1 additional page to allow for
    * buffers which do not start on a page boundary.
    *
    * Since GRO uses frags we allocate at least 16 regardless of page
    * size.
    */
    #if (65536/PAGE_SIZE + 1) < 16
    #define MAX_SKB_FRAGS 16UL
    #else
    #define MAX_SKB_FRAGS (65536/PAGE_SIZE + 1)
    #endif
```

```
    typedef struct skb_frag_struct skb_frag_t;
        struct skb_frag_struct {
                struct page *page;  //指向分片数据区的指针，类似于 sk_buff 中的 data 指针
                __u32 page_offset;  //偏移量, 表示从 page 指针指向的地方, 偏移 page_offset
                __u32 size;         //数据区的长度, 即: sk_buff 结构中的 data_len
            };
```


## skb_buff_head

每个 skb 必须能被整个链表头部快速找到. 为了满足这个需求, 在第一个 SKB 节点前面会插入另一个辅助的 sk_buff_head 结构的头结点,
可以认为该 sk_buff_head 结构就是 SKB 链表的头结点.

```
    struct sk_buff_head {
        /* These two members must be first. */
        struct sk_buff *next;
        struct sk_buff *prev;

        __u32 qlen;         //代表当前链表中 skb 个数
        spinlock_t lock;    //锁，防止并发访问
    };
```

![skb 列表](skb_buf_list.jpg)

## skb_buff 使用示例

在进行更为详细的介绍之前我们看看 skb 实际的使用场景

struct  sk_buff 的成员 head 指向一个已分配的空间的头部, 该空间用于承载网络数据, end 指向该空间的尾部,
这两个成员指针从空间创建之后, 就不能被修改. data 指向分配空间中数据的头部, tail 指向数据的尾部,这两个
值随着网络数据在各层之间的传递, 修改, 会被不断改动. 所以, 这四个指针指向共同的一块内存区域的不同位置,
该内存区域由 __alloc_skb 在创建缓冲区时创建. 注意: 这些都是 char * 类型的指针, 指向特定的内存块.

下面这张图表示了 buffer 从 TCP 层到链路层的过程中 len, head, data, tail 以及 end 的变化, 通过这个图我
们可以非常清晰的了解到这几个域的区别:

![skb 数据变化示例](skb_data.jpg)

可以很清楚的看到 head 指针为分配的 buffer 的起始位置, end 为结束位置, 而 data 为当前数据的起始位置,
tail 为当前数据的结束位置. len 就是数据区的长度.

然后来看 transport_header, network_header 以及 mac_header 的变化, 这几个指针都是随着数据包到达不同的
层次才会有对应的值, 我们来看下面的图, 这个图表示了当从 2 层到达 3 层对应的指针的变化.

![skb mac](skb_mac.jpg)

###skb 真实场景介绍

1. sk_buff 结构数据区刚被申请好, 此时 head 指针, data 指针, tail 指针都是指向同一个地方. 记住前面讲过的: head
指针和 end 指针指向的位置一直都不变, 而对于数据的变化和协议信息的添加都是通过 data 指针和 tail 指针的改变来表现的.

2. 开始准备存储应用层下发过来的数据, 通过调用函数 skb_reserve() 来使 data 指针和 tail 指针同时向下移动, 空出一部分
空间来为后期添加协议信息.

3. 开始存储数据了, 通过调用函数 skb_put() 来使 tail 指针向下移动空出空间来添加数据, 此时 skb->data 和 skb->tail 之
间存放的都是数据信息, 无协议信息.

4. 开始添加帧头, 这时就开始调用函数 skb_push() 来使 data 指针向上移动, 空出空间来添加各层协议信息. 直到最后到达二
层, 添加完帧头然后就开始发包了.

![skb 数据指针变化](skb_data_changing.png)

------------------------------------------------------------------------------

在内核中有许多很短简单的函数来操作 sk_buff 结构, 在 linux/skbuff.h 和 net/core/skbuff.c 源文件中,
几乎所有函数都有两个版本, 类似 do_something 和 __do_something. 通常来讲, 第一种是封装函数, 增加了
一些额外的参数合理性检查或在调用第二种函数前加入上锁机制.

## skb_init

```
	void __init skb_init(void)
	{
        skbuff_head_cache = kmem_cache_create("skbuff_head_cache",
                sizeof(struct sk_buff),
                0,
                SLAB_HWCACHE_ALIGN|SLAB_PANIC,
                NULL);
        skbuff_fclone_cache = kmem_cache_create("skbuff_fclone_cache",
                (2 * sizeof(struct sk_buff)) + sizeof(atomic_t),
                0,
                SLAB_HWCACHE_ALIGN|SLAB_PANIC,
                NULL);
	}
```


skb_init() 函数中创建了 skbuff_head_cache 高速缓存, 一般情况下, skb 都是从该高速缓存中分配的.
skbuff_fclone_cahe 高速缓存的创建是为了方便 skb 的克隆, 如果一个 skb 在分配的时候就知道可能被克隆,
那么应该从这个高速缓存中分配, 因为这个高速缓存中分配 skb 时, 会同时分配一个后备的skb, 在克隆的时候
直接使用后备的 skb 即可, 不用再次分配 skb, 很明显这样能提高效率.

## alloc_skb

alloc_skb() 用来分配 skb. 数据缓存区和 skb 描述符是两个不同的实体, 这就意味着, 在分配一个 skb 时,
需要分配两块内存, 一块是数据缓存区, 一块是 skb 描述符. __alloc_skb() 调用 kmem_cache_alloc_node()
从高速缓存中获取一个 sk_buff 结构的空间, 然后调用 kmalloc_node_track_caller() 分配数据缓存区.

参数说明如下:


```
    /*
     * size        : 待分配 SKB 的线性存储区的长度;
     * gfp_mask    : 分配内存的方式, 一般为 GFP_KERNEL
     * fclone      : 预测是否会克隆, 用于确定从哪个高速缓存中分配;
     * node        : 当支持 NUMA(非均匀质存储结构)时, 用于确定何种区域中分配 skb.
     */

	struct sk_buff *__alloc_skb(unsigned int size, gfp_t gfp_mask,
	   int fclone, int node)
	{
        struct kmem_cache *cache;
        struct skb_shared_info *shinfo;
        struct sk_buff *skb;
        u8 *data;

	    //这里通过fclone的值来判断是要从 fclone cache 还是说从 head cache 中取.
	    cache = fclone ? skbuff_fclone_cache : skbuff_head_cache;

        //从指定段中为skb分配内存, 分配的方式是去除在DMA内存中分配, 因为DMA内存比较小, 且有特定的作用, 一般不用来分配 skb.
	    skb = kmem_cache_alloc_node(cache, gfp_mask & ~__GFP_DMA, node);
	    if (!skb)
	        goto out;

	    //首先将 size 对齐, 这里是按一级缓存的大小来对齐. 长度为 len(end - head)
	    size = SKB_DATA_ALIGN(size);

	    //然后是数据区的大小, 大小为 size + sizeof(struct skb_shared_info), 这里允许有些数据可以用DMA内存来分配
	    data = kmalloc_node_track_caller(
                        size + sizeof(struct skb_shared_info),
	                    gfp_mask, node);
	    if (!data)
	        goto nodata;

	    //初始化 tail 之前(包含 tail) 为 0
        /*
         * Only clear those fields we need to clear, not those that
         * we will actually initialise below. Hence, don't put any more
         * fields after the tail pointer in struct sk_buff!
         */
	    memset(skb, 0, offsetof(struct sk_buff, tail));

	    //这里 truesize 可以看到就是我们分配的整个 skb + data 的大小
	    skb->truesize = size + sizeof(struct sk_buff);

	    atomic_set(&skb->users, 1);     //users加一.

	    //一开始 head 和 data 是一样大的.
	    skb->head = data;
	    skb->data = data;
	    skb_reset_tail_pointer(skb);    //设置tail指针

	    //一开始tail也就是和data是相同的。
	    skb->end = skb->tail + size;
	    kmemcheck_annotate_bitfield(skb, flags1);
	    kmemcheck_annotate_bitfield(skb, flags2);
	#ifdef NET_SKBUFF_DATA_USES_OFFSET
	    skb->mac_header = ~0U;
	#endif

	    //初始化 shinfo, 这个我就不介绍了
        shinfo = skb_shinfo(skb);
        atomic_set(&shinfo->dataref, 1);
        shinfo->nr_frags        = 0;
        shinfo->gso_size        = 0;
        shinfo->gso_segs        = 0;
        shinfo->gso_type        = 0;
        shinfo->ip6_frag_id     = 0;
        shinfo->tx_flags.flags  = 0;
        skb_frag_list_init(skb);
        memset(&shinfo->hwtstamps, 0, sizeof(shinfo->hwtstamps));

	    /* fclone为1,说明多分配了一块内存, 因此需要设置对应的 fclone 域.
         * 虽然是分配了两个sk_buff结构内存, 但是数据区却是只有一个的, 所以是两个 sk_buff
         * 结构中的指针都是指向这一个数据区的. 也正因为如此, 所以分配 sk_buff 结构时也顺
         * 便分配了个引用计数器
         */
	    if (fclone) {
            struct sk_buff *child = skb + 1;  //可以看到多分配的内存刚好在当前的 skb 的下方.
            atomic_t *fclone_ref = (atomic_t *) (child + 1);

	        kmemcheck_annotate_bitfield(child, flags1);
	        kmemcheck_annotate_bitfield(child, flags2);

	        //设置标记. 这里要注意, 当前的 skb 和多分配的 skb 设置的 fclone 是不同的.
	        skb->fclone = SKB_FCLONE_ORIG;
	        atomic_set(fclone_ref, 1);
	        child->fclone = SKB_FCLONE_UNAVAILABLE;
	    }
    out:
        return skb;
        nodata:
        kmem_cache_free(cache, skb);
        skb = NULL;
        goto out;
	}
```

####fclone 标志

* 若 fclone = SKB_FCLONE_UNAVAILABLE, 则表明 skb 未被克隆;
* 若 fclone = SKB_FCLONE_ORIG, 则表明是从 skbuff_fclone_cache 缓存池(这个缓存池上分配内存时, 每次都分配一对 skb 内存)中分配的父 skb, 可以被克隆;
* 若 fclone = SKB_FCLONE_CLONE, 则表明是在 skbuff_fclone_cache 分配的子 skb, 从父 skb 克隆得到的;

需要说明的是,  __alloc_skb() 一般不被直接调用, 而是被封装函数调用, 如 __netdev_alloc_skb(), alloc_skb(), alloc_skb_fclone() 等函数.

```
    //来源 linux-2.6.32.63/include/linux/sk_buff.h

    //用来分配单纯的 sk_buff 结构
    static inline struct sk_buff *alloc_skb(unsigned int size,
                                    gfp_t priority)
    {
        return __alloc_skb(size, priority, 0, -1);
    }

    //用来分配克隆 sk_buff 结构
    static inline struct sk_buff *alloc_skb_fclone(unsigned int size,
                                           gfp_t priority)
    {
                return __alloc_skb(size, priority, 1, -1);
    }


    /*
     * 它是用 GFP_ATOMIC 的内存分配方式来申请的(一般我们用GFP_KERNEL), 这是个原子操作,
     * 表示申请时不能被中断. 其实还有个申请函数: netdev_alloc_skb()
     */
    struct sk_buff *dev_alloc_skb(unsigned int length)
    {
        /*
         * There is more code here than it seems: 
         * __dev_alloc_skb is an inline 
         */
        return __dev_alloc_skb(length, GFP_ATOMIC);
    }

    static inline struct sk_buff *__dev_alloc_skb(unsigned int length,
                                          gfp_t gfp_mask)
    {
        struct sk_buff *skb = alloc_skb(length + NET_SKB_PAD, gfp_mask);
        if (likely(skb))
            skb_reserve(skb, NET_SKB_PAD);
            return skb;
        }
    }
```

调用alloc_skb()之后的套接口缓存结构:

![ alloc_skb 调用后示意图](alloc_skb.jpg)

NOTE:

    这里的 size = end - head, 而
    skb->data_len 为 tail-data
    skb->len = data_len + sizeof(skb_shared_info)
    skb->truesize = size + sizeof(skb_buff)

-----------------------------------------------------

##skb_clone


```
    /**
     *    skb_clone    -    duplicate an sk_buff
     *    @skb: buffer to clone
     *    @gfp_mask: allocation priority
     *
     *    Duplicate an &sk_buff. The new one is not owned by a socket. Both
     *    copies share the same packet data but not structure. The new
     *    buffer has a reference count of 1. If the allocation fails the
     *    function returns %NULL otherwise the new buffer is returned.
     *
     *    If this function is called from an interrupt gfp_mask() must be
     *    %GFP_ATOMIC.
     */

	struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
	{
        struct sk_buff *n;

        // n 为 skb 紧跟着那块内存, 这里如果 skb 是通过 skb_fclone 分配的, 那么 n 就是一个 skb.
        n = skb + 1;

        /* 判断原始 skb 是否是从 skbuff_fclone_cache 缓冲区中分配的, 从 skbuff_fclone_cache 分配将预先为
         * clone 的 skb 分配好内存, 同时判定该预先分配的 clone skb 是否被使用, 可以看到这里的值就是我们
         * 在 __alloc_skb 中设置的值.
         */
        if (skb->fclone == SKB_FCLONE_ORIG && n->fclone == SKB_FCLONE_UNAVAILABLE) {
            /*
             * 现在的 skb 实际上是一组 skb, 即 fclone 标志为 1.
             * 那么 n 是可用的, 不需要再次申请了, 只需要增加引用计数.
             */
            atomic_t *fclone_ref = (atomic_t *) (n + 1);
            n->fclone = SKB_FCLONE_CLONE;
            atomic_inc(fclone_ref);
        } else {

            /* 主skb并未同时分配 clone skb 的情况, 将重新独立分配 skb 结构作为 clone 的 skb */
            n = kmem_cache_alloc(skbuff_head_cache, gfp_mask);
            if (!n)
                return NULL;

            kmemcheck_annotate_bitfield(n, flags1);
            kmemcheck_annotate_bitfield(n, flags2);
            //设置新的 skb 的 fclone 域. 这里我们新建的 skb, 没有被 fclone 的都是这个标记.
            n->fclone = SKB_FCLONE_UNAVAILABLE;
        }

        /* 拷贝skb中的信息，各种指针等等，并增加数据段的引用计数 */
        return __skb_clone(n, skb);
	}

    /*
     * You should not add any new code to this function. Add it to
     * __copy_skb_header above instead.
     */
    static struct sk_buff *__skb_clone(struct sk_buff *n, struct sk_buff *skb)
    {
    #define C(x) n->x = skb->x

        //让前驱后继指针都为 NULL, 因为这是个单独的 sk_buff 结构体, 没有在 sk_buff 链表上.
        n->next = n->prev = NULL;
        n->sk = NULL;
        /* copy 头部字段，详细请参考源代码，很简单 */
        __copy_skb_header(n, skb);

        C(len);
        C(data_len);
        C(mac_len);
        n->hdr_len = skb->nohdr ? skb_headroom(skb) : skb->hdr_len;
        n->cloned = 1;
        n->nohdr = 0;
        n->destructor = NULL;
        C(tail);
        C(end);
        C(head);
        C(data);
        C(truesize);
        /* 设置 skb 描述符的 users 为 1 */
        atomic_set(&n->users, 1);

        /* 增加 shinfo 中 dataref 的引用计数, 因为 clone 的 skb 与原始 skb 指向同一数据缓冲区 */
        atomic_inc(&(skb_shinfo(skb)->dataref));
        skb->cloned = 1; /* 指明原始skb是被 clone 过的 */

        return n;
    #undef C
    }
```

下图就是 skb_clone 之后的两个skb的结构图:

![skb clone 示意图](skb_clone.jpg)

NOTE:
> 理解 users, cloned, dataref 之间的关系
* users : skb 被引用或克隆的次数
* dataref : 数据区被克隆的次数
* cloned  : skb 是否被克隆或从克隆自其他 skb

由 skb_clone() 函数克隆一个 skb, 然后共享其他数据. 虽然可以提高效率, 但是存在一个很大的缺陷, 就是
当有克隆 skb 指向共享数据区是, 那么共享数据区的数据就不能被修改了. 所以说如果只是让多个 skb 查看
共享数据区内容, 则可以用 skb_clone() 函数来克隆这几个 skb 出来, 提高效率. 但如果涉及到某个 skb 要
修改 sk_buff 结构的数据区, 则必须要用 copy 语义来解决.

## skb_copy

当一个 skb 被 clone 之后, 这个 skb 的数据区是不能被修改的, 这就意为着, 我们存取数据不需要任何锁.
可是有时我们需要修改数据区, 这个时候会有两个选择:

* 一个是我们只修改 linear 段, 也就是 head 和 end 之间的段
* 一种是我们还要修改切片数据, 也就是 skb_shared_info.

这样就有两个函数供我们选择, 第一个是 pskb_copy, 第二个是 skb_copy.

###pskb_copy

我们先来看 pskb_copy, 函数先 alloc 一个新的 skb, 然后调用
skb_copy_from_linear_data 来复制 skb_shared_info 的数据.

不仅拷贝 sk_buff 结构体, 还拷贝 sk_buff 结构体指针 data 所指向的数据区(当然这个数据区包括了分片
结构体, 因为内存分配时, 这两个结构体都是一起分配的, 现在如果要重新为数据区分配内存的话, 那自然
也是一起分配了), 但是分片结构体中所指的数据区是共享的.

```
    /**
      * pskb_copy - create copy of an sk_buff with private head.
      * Make a copy of both an &sk_buff and part of its data, located
      * in header. Fragmented data remain shared. This is used when
      * the caller wishes to modify only header of &sk_buff and needs
      * private copy of the header to alter. Returns %NULL on failure
      * or the pointer to the buffer on success.
      * The returned buffer has a reference count of 1.
      */
    struct sk_buff *pskb_copy(struct sk_buff *skb, gfp_t gfp_mask)
    {
        /*
        *     Allocate the copy buffer
        */
        struct sk_buff *n;
    #ifdef NET_SKBUFF_DATA_USES_OFFSET
        n = alloc_skb(skb->end, gfp_mask);
    #else
        n = alloc_skb(skb->end - skb->head, gfp_mask);
    #endif
        if (!n)
            goto out;

        /* n->head 定位到 skb->head */
        skb_reserve(n, skb->data - skb->head);
        /* Set the tail pointer and length */
        // n->tail 定位到 skb->tail, 并重置 n->len = skb->len
        skb_put(n, skb_headlen(skb));

        //复制线性数据段: n->len = skb->len = skb->data_len + skb->tail - skb->head
        skb_copy_from_linear_data(skb, n->data, n->len);

        //更新相关域
        n->truesize += skb->data_len;
        n->data_len  = skb->data_len;
        n->len          = skb->len;

        //下面只是复制切片数据的指针
        if (skb_shinfo(skb)->nr_frags) {
            int i;

            //skb_shinfo(skb)宏其实就是skb->end
            for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                skb_shinfo(n)->frags[i] = skb_shinfo(skb)->frags[i];
                get_page(skb_shinfo(n)->frags[i].page);
            }
            skb_shinfo(n)->nr_frags = i;
        }

        if (skb_has_frags(skb)) {
                skb_shinfo(n)->frag_list = skb_shinfo(skb)->frag_list;
                skb_clone_fraglist(n);
        }

        copy_skb_header(n, skb);
    out:
        return n;
    }
```

###skb copy

复制skb的所有数据段, 包括分片数据:


```
    struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask)
    {
        /*
        用 skb 的 data 减去 head 就是这层协议头部的大小, 也许是 L2,L3,和L4.
        */
        int headerlen = skb->data - skb->head;
        /*
        * Allocate the copy buffer
        */

        //先alloc一个新的skb
        struct sk_buff *n;
    #ifdef NET_SKBUFF_DATA_USES_OFFSET
        n = alloc_skb(skb->end + skb->data_len, gfp_mask);
    #else
        n = alloc_skb(skb->end - skb->head + skb->data_len, gfp_mask);
    #endif
        if (!n)
            return NULL;

        /* Set the data pointer */
        skb_reserve(n, headerlen);
        /* Set the tail pointer and length */
        skb_put(n, skb->len);
        ///然后复制所有的数据。
        if (skb_copy_bits(skb, -headerlen, n->head, headerlen + skb->len))
            BUG();

        copy_skb_header(n, skb);
        return n;
    }
```

下面这张图就表示了 psb_copy 和 skb_copy 调用后的内存模型, 其中 a 是 pskb_copy, b 是 skb_copy:

![skb copy 示意图](skb_copy.jpg)

##skb_free

这里主要是判断一个引用标记位 users, 将它减一, 如果大于 0 则直接返回, 否则释放 skb.

```
    void kfree_skb(struct sk_buff *skb)
    {
        if (unlikely(!skb))
            return;
        if (likely(atomic_read(&skb->users) == 1))
            smp_rmb();
        //减一，然后判断。
        else if (likely(!atomic_dec_and_test(&skb->users)))
            return;
        trace_kfree_skb(skb, __builtin_return_address(0));
        __kfree_skb(skb);
    }

    void __kfree_skb(struct sk_buff *skb)
    {
        skb_release_all(skb);
        kfree_skbmem(skb);
    }

    static void skb_release_all(struct sk_buff *skb)
    {
        skb_release_head_state(skb);
        skb_release_data(skb);
    }
```

##辅助函数

![skb 操作](skb_operation.jpeg)

###skb_reserve(len)

此函数在数据缓存区头部预留一定的空间, 通常被用来在数据缓存区中插入协议首部或者在某个边界上对齐.
它并没有把数据移出或移入数据缓存区, 而只是简单地更新了数据缓存区的两个指针--分别指向负载起始和
结尾的 data 和 tail 指针.

请注意: skb_reserve() 只能用于空的 skb, 通常会在分配 skb 之后就调用该函数, 此时 data 和 tail
指针还一同指向数据区的起始位置. 例如, 某个以太网设备驱动的接收函数, 在分配 skb 之后, 向数据缓存
区填充数据之前, 会有这样的一条语句 skb_reserve(skb, 2), 这是因为以太网头部为 14 字节长, 再加上
2 字节就正好 16 字节边界对齐, 所以大多数以太网设备都会在数据包之前保留 2 个字节.

当 skb 在协议栈中向下传递时, 每一层协议都把 skb->data 指针向上移动, 然后复制本层首部, 同时更新
skb->len.

###skb_push(len)

此函数在数据缓存区的头部加入一块数据. 修改指向数据区起始的指针 data, 使之往上移 len 字节, 使
数据区向上扩大 len 字节, 并更新数据区长度 len. 常用于向外发送数据是从协议栈由上到下填充协议头

###skb_put(len)

此函数修改指向数据区末尾的指针 tail, 使之往下移 len 字节, 即使数据区向下扩大 len 字节, 并更新
数据区长度len. 常用于接受外部数据时, 构造包时填充协议头, 与 skb_push 正好相反.

###skb_pull(len)

此函数通过将 data 指针往下移动来在数据区首部忽略 len 字节长度的数据, 通常用于接收到的数据包后
在各层间由下往上传递时, 上层忽略下层的首部.

## skb queue


###初始化函数

```
    static inline void skb_queue_head_init(struct sk_buff_head *list)
    {
        spin_lock_init(&list->lock); // 获得头结点中的自旋锁
        __skb_queue_head_init(list); // 调用函数初始化头结点
    }
    static inline void __skb_queue_head_init(struct sk_buff_head *list)
    {
        list->prev = list->next = (struct sk_buff *)list;   // 创建一个链表
        list->qlen = 0;                                     // 链表节点个数为零
    }
```

###插入函数

```
    void skb_queue_head(struct sk_buff_head *list, struct sk_buff *newsk)
    {
        unsigned long flags;

        spin_lock_irqsave(&list->lock, flags);
        __skb_queue_head(list, newsk);
        spin_unlock_irqrestore(&list->lock, flags);
    }

    static inline void __skb_queue_head(struct sk_buff_head *list,
                        struct sk_buff *newsk)
    {
        __skb_queue_after(list, (struct sk_buff *)list, newsk);
        // 第一个 list 本来表示的是一个链表指针, 第二个 list 是由第一个队列指针 list 强转为链表头部结点
    }

    static inline void __skb_queue_after(struct sk_buff_head *list,
                         struct sk_buff *prev,
                         struct sk_buff *newsk)
    {
        __skb_insert(newsk, prev, prev->next, list); // 这里的prev实则是链表头部结点
    }


    void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk)
    {
        unsigned long flags;

        spin_lock_irqsave(&list->lock, flags);
        __skb_queue_tail(list, newsk);
        spin_unlock_irqrestore(&list->lock, flags);
    }

    static inline void __skb_queue_tail(struct sk_buff_head *list,
                       struct sk_buff *newsk)
    {
        __skb_queue_before(list, (struct sk_buff *)list, newsk); // 调用函数实现参数的变化
    }

    static inline void __skb_queue_before(struct sk_buff_head *list,
                          struct sk_buff *next,
                          struct sk_buff *newsk)
    {
        __skb_insert(newsk, next->prev, next, list);    // 调用函数实现真正的插入操作
    }

    static inline void __skb_insert(struct sk_buff *newsk,
                    struct sk_buff *prev, struct sk_buff *next,
                    struct sk_buff_head *list)
    {
        newsk->next = next;
        newsk->prev = prev;
        next->prev  = prev->next = newsk;
        list->qlen++;
    }
```

###出队列函数

```
    struct sk_buff *skb_dequeue(struct sk_buff_head *list)
    {
        unsigned long flags;
        struct sk_buff *result;

        spin_lock_irqsave(&list->lock, flags);
        result = __skb_dequeue(list);
        spin_unlock_irqrestore(&list->lock, flags);
        return result;
    }

    static inline struct sk_buff *__skb_dequeue(struct sk_buff_head *list)
    {
        struct sk_buff *skb = skb_peek(list);
        if (skb)
            __skb_unlink(skb, list);
        return skb;
    }

    static inline struct sk_buff *skb_peek(struct sk_buff_head *list_)
    {
        struct sk_buff *list = ((struct sk_buff *)list_)->next;
        if (list == (struct sk_buff *)list_)
            list = NULL;
        return list;
    }

    struct sk_buff *skb_dequeue_tail(struct sk_buff_head *list)
    {
        unsigned long flags;
        struct sk_buff *result;

        spin_lock_irqsave(&list->lock, flags);
        result = __skb_dequeue_tail(list);
        spin_unlock_irqrestore(&list->lock, flags);
    }

    static inline struct sk_buff *__skb_dequeue_tail(struct sk_buff_head *list)
    {
        struct sk_buff *skb = skb_peek_tail(list);
        if (skb)
            __skb_unlink(skb, list);
        return skb;
    }

    static inline struct sk_buff *skb_peek_tail(struct sk_buff_head *list_)
    {
        struct sk_buff *list = ((struct sk_buff *)list_)->prev;
        if (list == (struct sk_buff *)list_)
            list = NULL;
        return list;
    }

    static inline void __skb_unlink(struct sk_buff *skb, struct sk_buff_head *list)
    {
        struct sk_buff *next, *prev;

        list->qlen--; // 队列元素计数器自减1
        next       = skb->next; // 下面的实现分析看图
        prev       = skb->prev;
        skb->next  = skb->prev = NULL;
        next->prev = prev;
        prev->next = next;
    }
```


###清空队列函数

```
    void skb_queue_purge(struct sk_buff_head *list)
    {
        struct sk_buff *skb;
        while ((skb = skb_dequeue(list)) != NULL)
            kfree_skb(skb);
    }
```

###遍历队列操作

	    #define skb_queue_walk(queue, skb) \
            for (skb = (queue)->next;                    \
                 prefetch(skb->next), (skb != (struct sk_buff *)(queue));    \
                 skb = skb->next)
    // 上面的遍历是从 queue 头结点开始遍历，直到遍历循环回到queue结束.
    // 也就是遍历整个队列操作, 但该宏不能做删除skb操作,一旦删除了skb后, skb->next 就是非法的(因为此时skb不存在).

    #define skb_queue_walk_safe(queue, skb, tmp)                    \
            for (skb = (queue)->next, tmp = skb->next;            \
                 skb != (struct sk_buff *)(queue);              \
                 skb = tmp, tmp = skb->next)

    // 这个宏也是从queue头结点开始遍历整个队列操作，唯一不同的是这个宏用了一个临时变量，就是防止遍历时要删除掉skb变量,
    // 因为删除掉了skb后，也可以从skb=tmp中再次获得，然后依次tmp = skb->next;(此时skb是存在的)所以遍历时，可以做删除操作.

    #define skb_queue_walk_from(queue, skb)                     \
            for (; prefetch(skb->next), (skb != (struct sk_buff *)(queue));  \
                 skb = skb->next)
    // 这个宏是从skb元素处开始遍历直到遇到头结点queue结束，该宏只能做查看操作，不能做删除skb操作，分析如第一个宏

    #define skb_queue_walk_from_safe(queue, skb, tmp)               \
            for (tmp = skb->next;                        \
                 skb != (struct sk_buff *)(queue);              \
                 skb = tmp, tmp = skb->next)
    // 这个宏也是从skb元素开始遍历直到遇到queue元素结束，但该宏可以做删除skb元素操作，具体分析如第一个宏

    #define skb_queue_reverse_walk(queue, skb) \
            for (skb = (queue)->prev;                    \
                 prefetch(skb->prev), (skb != (struct sk_buff *)(queue));    \
                 skb = skb->prev)
    // 这是个逆反遍历宏，就是从queue头结点的尾部开始（或者说从前驱元素开始）直到遇到 queue 元素节点.
    // 也即是从头结点尾部开始遍历了整个队列，此宏和第一、第三个宏一样，不能做删除操作.

###插入数据函数

    // skb为被添加的sk_buff类型的结构体，from为将要添加的数据源，copy为数据源的长度
    static inline int skb_add_data(struct sk_buff *skb,
                       char __user *from, int copy)
    {
        const int off = skb->len;

        if (skb->ip_summed == CHECKSUM_NONE) {// 表示检验ip包的校验
            int err = 0;
            // 数据拷贝操作，这里调用了skb_put()函数让tail往下移空出控件来存放将要拷贝的数据，并且返回tail指针
            __wsum csum = csum_and_copy_from_user(from, skb_put(skb, copy),
                                    copy, 0, &err);
            if (!err) {
                skb->csum = csum_block_add(skb->csum, csum, off); // 这个应该是IP校验计算吧
                return 0;
            }
        } else if (!copy_from_user(skb_put(skb, copy), from, copy)) // 这是最本质的数据拷贝操作宏，同样调用了skb_put()函数返回tail指针
            return 0;

        __skb_trim(skb, off); // 这个是删除数据操作，将在下一个数据删除（skb_trim()函数）分析
        return -EFAULT; 
    }

    static inline
    __wsum csum_and_copy_from_user (const void __user *src, void *dst,
                          int len, __wsum sum, int *err_ptr)
    {
        if (access_ok(VERIFY_READ, src, len)) // 判断数据长度关系
            return csum_partial_copy_from_user(src, dst, len, sum, err_ptr); // 调用拷贝函数
        if (len)
            *err_ptr = -EFAULT;
        return sum;
    }

    static __inline__
    __wsum csum_partial_copy_from_user(const void __user *src,
                                             void *dst, int len, __wsum sum,
                                             int *err_ptr)
    {
            if (copy_from_user(dst, src, len)) { // 拷贝操作
                    *err_ptr = -EFAULT;
                    return (__force __wsum)-1;
            }
            return csum_partial(dst, len, sum); // 设置校验和
    }

    // 这是调用memcpy()函数来对数据进行拷贝，to是tail指针，from是将要插入的数据源指针，n是数据源长度
    #define copy_from_user(to, from, n) (memcpy((to), (from), (n)), 0)

删除数据函数

    void skb_trim(struct sk_buff *skb, unsigned int len)  
    {
        // 这里值得注意的是len不是要删除的数据长度，而是删除后的数据长度，即是新的数据长度。
        // 所以新的数据长度不能比开始的skb的长度还大，否则就是插入增加数据函数而不是删除数据函数了
        if (skb->len > len)
            __skb_trim(skb, len);// 调用函数进行删除数据操作
    }

    static inline void __skb_trim(struct sk_buff *skb, unsigned int len)
    {
        if (unlikely(skb->data_len)) {
            WARN_ON(1);
            return;
        }
        skb->len = len; // 为新的skb赋上删除后的len值
        skb_set_tail_pointer(skb, len); // 调用函数删除操作
    }

    static inline void skb_set_tail_pointer(struct sk_buff *skb, const int offset)
    {
        skb->tail = skb->data + offset; // 实质上没有对数据进行删除，只是让tail指针偏移，改变有效数据值
    }


    static inline int pskb_trim(struct sk_buff *skb, unsigned int len)
    {
        return (len < skb->len) ? __pskb_trim(skb, len) : 0; // 这个功能和上面类似，如果新len值小于skb原有的值，则做删除操作
    }
    static inline int __pskb_trim(struct sk_buff *skb, unsigned int len)
    {
        if (skb->data_len)// 如果分片结构数据区有数据
            return ___pskb_trim(skb, len);// 则调用该函数来删除分片结构中的数据区数据
        __skb_trim(skb, len);// 这个和上面删除sk_buff结构中的数据区数据一样
        return 0;
    }

###拆分数据函数

    // skb为原来的skb结构体（将要被拆分的），skb1为拆分后得到的子skb，len为拆分后的skb的新长度
    void skb_split(struct sk_buff *skb, struct sk_buff *skb1, const u32 len)
    {
        int pos = skb_headlen(skb);// pos = skb->len - skb->data_len，pos是skb结构中数据区的有效数据长度

        if (len < pos)   // 如果拆分长度小于skb数据区中的有效长度，则调用下面函数
            skb_split_inside_header(skb, skb1, len, pos);// 该函数只拆分skb数据区中的数据
        else  // 反之，如果拆分长度不小于skb数据区中的有效长度，则调用下面函数
            skb_split_no_header(skb, skb1, len, pos);// 拆分skb结构中的分片结构中数据区数据
    }

    // 这是只拆分sk_buff结构数据区的数据，其他参数不变，参数：pos则是sk_buff结构数据区中有效数据长度
    static inline void skb_split_inside_header(struct sk_buff *skb,
                           struct sk_buff* skb1,
                           const u32 len, const int pos)
    {
        int i;
        // 这是个把sk_buff结构中有效数据拷贝到新的skb1中,pos为有效数据长度，len为剩下数据长度，得：pos-len为要拷贝的数据长度
        // skb_put(skb1,pos-len)是移动tail指针让skb1结构数据区空出空间来存放将要拷贝的数据，该函数返回tail指针
        skb_copy_from_linear_data_offset(skb, len, skb_put(skb1, pos - len),
                         pos - len);
                // 为了方便理解，把该函数实现代码注释进来
                // skb为要被拆分的sk_buff结构，offset为剩下新的skb数据长度，to为skb1结构中tail指针，len为要拷贝的数据长度
                // static inline void skb_copy_from_linear_data_offset(const struct sk_buff *skb,
            //                  const int offset, void *to,
            //                  const unsigned int len)
            // {
            // 从skb要剩下的数据位置开始（即是skb->data+offset，skb->data和skb->data+offset之间的数据是要保留的）
            // to则是tail指针移动前返回的一个位置指针（详细请看skb_put()函数实现），拷贝len长度内容
            //  <span style="white-space:pre">    </span>memcpy(to, skb->data + offset, len);
            //<span style="white-space:pre">  </span>}
            // 如果对sk_buff结构及相关结构体中成员变量了解，则这些代码就非常好理解了。
            // nr_frags为多少个分片数据区，循环把所有分片数据拷贝到skb1中
        for (i = 0; i < skb_shinfo(skb)->nr_frags; i++)
            skb_shinfo(skb1)->frags[i] = skb_shinfo(skb)->frags[i];

        //下面做的都是些成员字段拷贝赋值操作，并且设置skb的字段
        skb_shinfo(skb1)->nr_frags = skb_shinfo(skb)->nr_frags;
        skb_shinfo(skb)->nr_frags  = 0;
        skb1->data_len          = skb->data_len;
        skb1->len           += skb1->data_len;
        skb->data_len           = 0;
        skb->len        = len;
        skb_set_tail_pointer(skb, len);// 下面把实现函数代码注释进来，方便理解
            //  static inline void skb_set_tail_pointer(struct sk_buff *skb, const int offset)
            //  {
            //      // 这是把tail指针移到数据区的最后面
            //      skb->tail = skb->data + offset;
            //  }
    }

    // 这是拆分分片结构数据区数据，同理，其他参数不变，参数：pos则是sk_buff结构数据区中有效数据长度
    static inline void skb_split_no_header(struct sk_buff *skb,
                           struct sk_buff* skb1,
                           const u32 len, int pos)
    {
        int i, k = 0;
        // 开始设置sk_buff结构数据区内容
        const int nfrags = skb_shinfo(skb)->nr_frags;
        skb_shinfo(skb)->nr_frags   = 0;
        skb1->len                   = skb1->data_len = skb->len - len;
        skb->len                    = len;
        skb->data_len               = len - pos;

        // 这是循环拆分分片结构数据区数据
        for (i = 0; i < nfrags; i++) {
            int size = skb_shinfo(skb)->frags[i].size;
        // 其实拆分，数据区存储不会动，动的只是指向这些数据存储的位置指针
           //  下面都是把skb的一些指向分片结构数据区的指针赋值给skb1中的数据区相关变量
            if (pos + size > len) {
                skb_shinfo(skb1)->frags[k] = skb_shinfo(skb)->frags[i];
                if (pos < len) {
                    get_page(skb_shinfo(skb)->frags[i].page);
                    skb_shinfo(skb1)->frags[0].page_offset += len - pos;
                    skb_shinfo(skb1)->frags[0].size -= len - pos;
                    skb_shinfo(skb)->frags[i].size   = len - pos;
                    skb_shinfo(skb)->nr_frags++;
                }
                k++;
            } else
                skb_shinfo(skb)->nr_frags++;
            pos += size;
        }
        skb_shinfo(skb1)->nr_frags = k;
    }
```

##实际应用

中断环境下 SKB 的分配流程

当数据到达网卡后, 会触发网卡的中断, 从而进入 ISR 中, 系统会在 ISR
中计算出此次接收到的数据的字节数: pkt_len, 然后调用 skb 分配函数来分配 skb :

    skb = dev_alloc_skb(pkt_len+5);

我们可以看到, 实际上传入的数据区的长度还要比实际接收到的字节数多, 这实际上是一种保护机制.
实际上, 在 dev_alloc_skb 函数调用 __dev_alloc_skb 函数, 而 __dev_alloc_skb 函数又调用
alloc_skb 函数时, 其数据区的大小又增加了 128 字节, 这 128 字节就事前面我们所说的 reserve
机制预留的 header 空间.

##参考

* https://github.com/torvalds/linux/blob/master/include/linux/skbuff.h
* http://blog.chinaunix.net/uid-14518381-id-3397881.html
* http://blog.csdn.net/scottgly/article/details/6821782
* http://blog.chinaunix.net/uid-23629988-id-262233.html
* http://blog.csdn.net/column/details/linux-skb.html
* http://www.cnblogs.com/zhuyp1015/archive/2012/08/04/2623353.html
* http://blog.csdn.net/yuzhihui_no1/article/details/38666589
* http://blog.csdn.net/yuzhihui_no1/article/details/38737615
* http://blog.csdn.net/yuzhihui_no1/article/details/38827603


##附录

```
/*
* Definitions for the 'struct sk_buff' memory handlers.
*
* Authors:
* Alan Cox, <gw4pts@gw4pts.ampr.org>
* Florian La Roche, <rzsfl@rz.uni-sb.de>
*
* This program is free software; you can redistribute it and/or
* modify it under the terms of the GNU General Public License
* as published by the Free Software Foundation; either version
* 2 of the License, or (at your option) any later version.
*/
#ifndef _LINUX_SKBUFF_H
#define _LINUX_SKBUFF_H
#include <linux/kernel.h>
#include <linux/kmemcheck.h>
#include <linux/compiler.h>
#include <linux/time.h>
#include <linux/bug.h>
#include <linux/cache.h>
#include <linux/rbtree.h>
#include <linux/socket.h>
#include <linux/atomic.h>
#include <asm/types.h>
#include <linux/spinlock.h>
#include <linux/net.h>
#include <linux/textsearch.h>
#include <net/checksum.h>
#include <linux/rcupdate.h>
#include <linux/hrtimer.h>
#include <linux/dma-mapping.h>
#include <linux/netdev_features.h>
#include <linux/sched.h>
#include <net/flow_dissector.h>
#include <linux/splice.h>
#include <linux/in6.h>
/* A. Checksumming of received packets by device.
*
* CHECKSUM_NONE:
*
* Device failed to checksum this packet e.g. due to lack of capabilities.
* The packet contains full (though not verified) checksum in packet but
* not in skb->csum. Thus, skb->csum is undefined in this case.
*
* CHECKSUM_UNNECESSARY:
*
* The hardware you're dealing with doesn't calculate the full checksum
* (as in CHECKSUM_COMPLETE), but it does parse headers and verify checksums
* for specific protocols. For such packets it will set CHECKSUM_UNNECESSARY
* if their checksums are okay. skb->csum is still undefined in this case
* though. It is a bad option, but, unfortunately, nowadays most vendors do
* this. Apparently with the secret goal to sell you new devices, when you
* will add new protocol to your host, f.e. IPv6 8)
*
* CHECKSUM_UNNECESSARY is applicable to following protocols:
* TCP: IPv6 and IPv4.
* UDP: IPv4 and IPv6. A device may apply CHECKSUM_UNNECESSARY to a
* zero UDP checksum for either IPv4 or IPv6, the networking stack
* may perform further validation in this case.
* GRE: only if the checksum is present in the header.
* SCTP: indicates the CRC in SCTP header has been validated.
*
* skb->csum_level indicates the number of consecutive checksums found in
* the packet minus one that have been verified as CHECKSUM_UNNECESSARY.
* For instance if a device receives an IPv6->UDP->GRE->IPv4->TCP packet
* and a device is able to verify the checksums for UDP (possibly zero),
* GRE (checksum flag is set), and TCP-- skb->csum_level would be set to
* two. If the device were only able to verify the UDP checksum and not
* GRE, either because it doesn't support GRE checksum of because GRE
* checksum is bad, skb->csum_level would be set to zero (TCP checksum is
* not considered in this case).
*
* CHECKSUM_COMPLETE:
*
* This is the most generic way. The device supplied checksum of the _whole_
* packet as seen by netif_rx() and fills out in skb->csum. Meaning, the
* hardware doesn't need to parse L3/L4 headers to implement this.
*
* Note: Even if device supports only some protocols, but is able to produce
* skb->csum, it MUST use CHECKSUM_COMPLETE, not CHECKSUM_UNNECESSARY.
*
* CHECKSUM_PARTIAL:
*
* A checksum is set up to be offloaded to a device as described in the
* output description for CHECKSUM_PARTIAL. This may occur on a packet
* received directly from another Linux OS, e.g., a virtualized Linux kernel
* on the same host, or it may be set in the input path in GRO or remote
* checksum offload. For the purposes of checksum verification, the checksum
* referred to by skb->csum_start + skb->csum_offset and any preceding
* checksums in the packet are considered verified. Any checksums in the
* packet that are after the checksum being offloaded are not considered to
* be verified.
*
* B. Checksumming on output.
*
* CHECKSUM_NONE:
*
* The skb was already checksummed by the protocol, or a checksum is not
* required.
*
* CHECKSUM_PARTIAL:
*
* The device is required to checksum the packet as seen by hard_start_xmit()
* from skb->csum_start up to the end, and to record/write the checksum at
* offset skb->csum_start + skb->csum_offset.
*
* The device must show its capabilities in dev->features, set up at device
* setup time, e.g. netdev_features.h:
*
* NETIF_F_HW_CSUM - It's a clever device, it's able to checksum everything.
* NETIF_F_IP_CSUM - Device is dumb, it's able to checksum only TCP/UDP over
* IPv4. Sigh. Vendors like this way for an unknown reason.
* Though, see comment above about CHECKSUM_UNNECESSARY. 8)
* NETIF_F_IPV6_CSUM - About as dumb as the last one but does IPv6 instead.
* NETIF_F_... - Well, you get the picture.
*
* CHECKSUM_UNNECESSARY:
*
* Normally, the device will do per protocol specific checksumming. Protocol
* implementations that do not want the NIC to perform the checksum
* calculation should use this flag in their outgoing skbs.
*
* NETIF_F_FCOE_CRC - This indicates that the device can do FCoE FC CRC
* offload. Correspondingly, the FCoE protocol driver
* stack should use CHECKSUM_UNNECESSARY.
*
* Any questions? No questions, good. --ANK
*/
/* Don't change this without changing skb_csum_unnecessary! */
#define CHECKSUM_NONE	0
#define CHECKSUM_UNNECESSARY	1
#define CHECKSUM_COMPLETE	2
#define CHECKSUM_PARTIAL	3
/* Maximum value in skb->csum_level */
#define SKB_MAX_CSUM_LEVEL	3
#define SKB_DATA_ALIGN(X) ALIGN(X, SMP_CACHE_BYTES)
#define SKB_WITH_OVERHEAD(X) \
((X) - SKB_DATA_ALIGN(sizeof(struct skb_shared_info)))
#define SKB_MAX_ORDER(X, ORDER) \
SKB_WITH_OVERHEAD((PAGE_SIZE << (ORDER)) - (X))
#define SKB_MAX_HEAD(X) (SKB_MAX_ORDER((X), 0))
#define SKB_MAX_ALLOC	(SKB_MAX_ORDER(0, 2))
/* return minimum truesize of one skb containing X bytes of data */
#define SKB_TRUESIZE(X) ((X) + \
SKB_DATA_ALIGN(sizeof(struct sk_buff)) + \
SKB_DATA_ALIGN(sizeof(struct skb_shared_info)))
struct net_device;
struct scatterlist;
struct pipe_inode_info;
struct iov_iter;
struct napi_struct;

#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
struct nf_conntrack {
    atomic_t use;
};
#endif

#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
struct nf_bridge_info {
    atomic_t	use;
    enum {
        BRNF_PROTO_UNCHANGED,
        BRNF_PROTO_8021Q,
        BRNF_PROTO_PPPOE
    } orig_proto:8;
    bool	pkt_otherhost;
    __u16 frag_max_size;
    unsigned int	mask;
    struct net_device *physindev;
    union {
        struct net_device *physoutdev;
        char neigh_header[8];
    };
    union {
        __be32 ipv4_daddr;
        struct in6_addr ipv6_daddr;
    };
};
#endif

struct sk_buff_head {
    /* These two members must be first. */
    struct sk_buff *next;
    struct sk_buff *prev;
    __u32 qlen;
    spinlock_t	lock;
};

struct sk_buff;

/* To allow 64K frame to be packed as single skb without frag_list we
* require 64K/PAGE_SIZE pages plus 1 additional page to allow for
* buffers which do not start on a page boundary.
*
* Since GRO uses frags we allocate at least 16 regardless of page
* size.
*/
#if (65536/PAGE_SIZE + 1) < 16
#define MAX_SKB_FRAGS 16UL
#else
#define MAX_SKB_FRAGS (65536/PAGE_SIZE + 1)
#endif

typedef struct skb_frag_struct skb_frag_t;

struct skb_frag_struct {
    struct {
        struct page *p;
    } page;
#if (BITS_PER_LONG > 32) || (PAGE_SIZE >= 65536)
    __u32 page_offset;
    __u32 size;
#else
    __u16 page_offset;
    __u16 size;
#endif
};

static inline unsigned int skb_frag_size(const skb_frag_t *frag)
{
    return frag->size;
}

static inline void skb_frag_size_set(skb_frag_t *frag, unsigned int size)
{
    frag->size = size;
}

static inline void skb_frag_size_add(skb_frag_t *frag, int delta)
{
    frag->size += delta;
}

static inline void skb_frag_size_sub(skb_frag_t *frag, int delta)
{
    frag->size -= delta;
}

#define HAVE_HW_TIME_STAMP

/**
* struct skb_shared_hwtstamps - hardware time stamps
* @hwtstamp: hardware time stamp transformed into duration
* since arbitrary point in time
*
* Software time stamps generated by ktime_get_real() are stored in
* skb->tstamp.
*
* hwtstamps can only be compared against other hwtstamps from
* the same device.
*
* This structure is attached to packets as part of the
* &skb_shared_info. Use skb_hwtstamps() to get a pointer.
*/
struct skb_shared_hwtstamps {
    ktime_t	hwtstamp;
};

/* Definitions for tx_flags in struct skb_shared_info */
enum {
/* generate hardware time stamp */
SKBTX_HW_TSTAMP = 1 << 0,
/* generate software time stamp when queueing packet to NIC */
SKBTX_SW_TSTAMP = 1 << 1,
/* device driver is going to provide hardware time stamp */
SKBTX_IN_PROGRESS = 1 << 2,
/* device driver supports TX zero-copy buffers */
SKBTX_DEV_ZEROCOPY = 1 << 3,
/* generate wifi status information (where possible) */
SKBTX_WIFI_STATUS = 1 << 4,
/* This indicates at least one fragment might be overwritten
* (as in vmsplice(), sendfile() ...)
* If we need to compute a TX checksum, we'll need to copy
* all frags to avoid possible bad checksum
*/
SKBTX_SHARED_FRAG = 1 << 5,
/* generate software time stamp when entering packet scheduling */
SKBTX_SCHED_TSTAMP = 1 << 6,
/* generate software timestamp on peer data acknowledgment */
SKBTX_ACK_TSTAMP = 1 << 7,
};
#define SKBTX_ANY_SW_TSTAMP	(SKBTX_SW_TSTAMP | \
SKBTX_SCHED_TSTAMP | \
SKBTX_ACK_TSTAMP)
#define SKBTX_ANY_TSTAMP	(SKBTX_HW_TSTAMP | SKBTX_ANY_SW_TSTAMP)
/*
* The callback notifies userspace to release buffers when skb DMA is done in
* lower device, the skb last reference should be 0 when calling this.
* The zerocopy_success argument is true if zero copy transmit occurred,
* false on data copy or out of memory error caused by data copy attempt.
* The ctx field is used to track device context.
* The desc field is used to track userspace buffer index.
*/
struct ubuf_info {
void (*callback)(struct ubuf_info *, bool zerocopy_success);
void *ctx;
unsigned long desc;
};


/* This data is invariant across clones and lives at
* the end of the header data, ie. at skb->end.
*/
struct skb_shared_info {
    unsigned char	nr_frags;
    __u8 tx_flags;
    unsigned short	gso_size;
    /* Warning: this field is not always filled in (UFO)! */
    unsigned short	gso_segs;
    unsigned short gso_type;
    struct sk_buff *frag_list;
    struct skb_shared_hwtstamps hwtstamps;
    u32 tskey;
    __be32 ip6_frag_id;
    /*
    * Warning : all fields before dataref are cleared in __alloc_skb()
    */
    atomic_t	dataref;
    /* Intermediate layers must ensure that destructor_arg
    * remains valid until skb destructor */
    void * destructor_arg;
    /* must be last field, see pskb_expand_head() */
    skb_frag_t	frags[MAX_SKB_FRAGS];
};

/* We divide dataref into two halves. The higher 16 bits hold references
* to the payload part of skb->data. The lower 16 bits hold references to
* the entire skb->data. A clone of a headerless skb holds the length of
* the header in skb->hdr_len.
*
* All users must obey the rule that the skb->data reference count must be
* greater than or equal to the payload reference count.
*
* Holding a reference to the payload part means that the user does not
* care about modifications to the header part of skb->data.
*/

#define SKB_DATAREF_SHIFT 16
#define SKB_DATAREF_MASK ((1 << SKB_DATAREF_SHIFT) - 1)
enum {
    SKB_FCLONE_UNAVAILABLE, /* skb has no fclone (from head_cache) */
    SKB_FCLONE_ORIG, /* orig skb (from fclone_cache) */
    SKB_FCLONE_CLONE, /* companion fclone skb (from fclone_cache) */
};

enum {
    SKB_GSO_TCPV4 = 1 << 0,
    SKB_GSO_UDP = 1 << 1,
    /* This indicates the skb is from an untrusted source. */
    SKB_GSO_DODGY = 1 << 2,
    /* This indicates the tcp segment has CWR set. */
    SKB_GSO_TCP_ECN = 1 << 3,
    SKB_GSO_TCPV6 = 1 << 4,
    SKB_GSO_FCOE = 1 << 5,
    SKB_GSO_GRE = 1 << 6,
    SKB_GSO_GRE_CSUM = 1 << 7,
    SKB_GSO_IPIP = 1 << 8,
    SKB_GSO_SIT = 1 << 9,
    SKB_GSO_UDP_TUNNEL = 1 << 10,
    SKB_GSO_UDP_TUNNEL_CSUM = 1 << 11,
    SKB_GSO_TUNNEL_REMCSUM = 1 << 12,
};

#if BITS_PER_LONG > 32
#define NET_SKBUFF_DATA_USES_OFFSET 1
#endif
#ifdef NET_SKBUFF_DATA_USES_OFFSET
typedef unsigned int sk_buff_data_t;
#else
typedef unsigned char *sk_buff_data_t;
#endif

/**
* struct skb_mstamp - multi resolution time stamps
* @stamp_us: timestamp in us resolution
* @stamp_jiffies: timestamp in jiffies
*/
struct skb_mstamp {
    union {
        u64 v64;
        struct {
            u32 stamp_us;
            u32 stamp_jiffies;
        };
    };
};

/**
* skb_mstamp_get - get current timestamp
* @cl: place to store timestamps
*/
static inline void skb_mstamp_get(struct skb_mstamp *cl)
{
    u64 val = local_clock();
    do_div(val, NSEC_PER_USEC);
    cl->stamp_us = (u32)val;
    cl->stamp_jiffies = (u32)jiffies;
}

/**
* skb_mstamp_delta - compute the difference in usec between two skb_mstamp
* @t1: pointer to newest sample
* @t0: pointer to oldest sample
*/
static inline u32 skb_mstamp_us_delta(const struct skb_mstamp *t1,
const struct skb_mstamp *t0)
{
    s32 delta_us = t1->stamp_us - t0->stamp_us;
    u32 delta_jiffies = t1->stamp_jiffies - t0->stamp_jiffies;
    /* If delta_us is negative, this might be because interval is too big,
     * or local_clock() drift is too big : fallback using jiffies.
     */
    if (delta_us <= 0 ||
            delta_jiffies >= (INT_MAX / (USEC_PER_SEC / HZ)))
        delta_us = jiffies_to_usecs(delta_jiffies);
    return delta_us;
}

/**
 * struct sk_buff - socket buffer
 * @next: Next buffer in list
 * @prev: Previous buffer in list
 * @tstamp: Time we arrived/left
 * @rbnode: RB tree node, alternative to next/prev for netem/tcp
 * @sk: Socket we are owned by
 * @dev: Device we arrived on/are leaving by
 * @cb: Control buffer. Free for use by every layer. Put private vars here
 * @_skb_refdst: destination entry (with norefcount bit)
 * @sp: the security path, used for xfrm
 * @len: Length of actual data
 * @data_len: Data length
 * @mac_len: Length of link layer header
 * @hdr_len: writable header length of cloned skb
 * @csum: Checksum (must include start/offset pair)
 * @csum_start: Offset from skb->head where checksumming should start
 * @csum_offset: Offset from csum_start where checksum should be stored
 * @priority: Packet queueing priority
 * @ignore_df: allow local fragmentation
 * @cloned: Head may be cloned (check refcnt to be sure)
 * @ip_summed: Driver fed us an IP checksum
 * @nohdr: Payload reference only, must not modify header
 * @nfctinfo: Relationship of this skb to the connection
 * @pkt_type: Packet class
 * @fclone: skbuff clone status
 * @ipvs_property: skbuff is owned by ipvs
 * @peeked: this packet has been seen already, so stats have been
 * done for it, don't do them again
 * @nf_trace: netfilter packet trace flag
 * @protocol: Packet protocol from driver
 * @destructor: Destruct function
 * @nfct: Associated connection, if any
 * @nf_bridge: Saved data about a bridged frame - see br_netfilter.c
 * @skb_iif: ifindex of device we arrived on
 * @tc_index: Traffic control index
 * @tc_verd: traffic control verdict
 * @hash: the packet hash
 * @queue_mapping: Queue mapping for multiqueue devices
 * @xmit_more: More SKBs are pending for this queue
 * @ndisc_nodetype: router type (from link layer)
 * @ooo_okay: allow the mapping of a socket to a queue to be changed
 * @l4_hash: indicate hash is a canonical 4-tuple hash over transport
 * ports.
 * @sw_hash: indicates hash was computed in software stack
 * @wifi_acked_valid: wifi_acked was set
 * @wifi_acked: whether frame was acked on wifi or not
 * @no_fcs: Request NIC to treat last 4 bytes as Ethernet FCS
 * @napi_id: id of the NAPI struct this skb came from
 * @secmark: security marking
 * @mark: Generic packet mark
 * @vlan_proto: vlan encapsulation protocol
 * @vlan_tci: vlan tag control information
 * @inner_protocol: Protocol (encapsulation)
 * @inner_transport_header: Inner transport layer header (encapsulation)
 * @inner_network_header: Network layer header (encapsulation)
 * @inner_mac_header: Link layer header (encapsulation)
 * @transport_header: Transport layer header
 * @network_header: Network layer header
 * @mac_header: Link layer header
 * @tail: Tail pointer
 * @end: End pointer
 * @head: Head of buffer
 * @data: Data head pointer
 * @truesize: Buffer size
 * @users: User count - see {datagram,tcp}.c
 */
struct sk_buff {
    union {
        struct {
            /* These two members must be first. */
            struct sk_buff *next;
            struct sk_buff *prev;
            union {
                ktime_t	tstamp;
                struct skb_mstamp skb_mstamp;
            };
        };
        struct rb_node rbnode; /* used in netem & tcp stack */
    };
    struct sock *sk;
    struct net_device *dev;
    /*
     * This is the control buffer. It is free to use for every
     * layer. Please put your private variables there. If you
     * want to keep them across layers you have to do a skb_clone()
     * first. This is owned by whoever has the skb queued ATM.
     */
    char	cb[48] __aligned(8);
    unsigned long	_skb_refdst;
    void	(*destructor)(struct sk_buff *skb);
#ifdef CONFIG_XFRM
    struct	sec_path *sp;
#endif
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
    struct nf_conntrack *nfct;
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
    struct nf_bridge_info *nf_bridge;
#endif
    unsigned int	len,
                    data_len;
    __u16 mac_len,
          hdr_len;
    /* Following fields are _not_ copied in __copy_skb_header()
     * Note that queue_mapping is here mostly to fill a hole.
     */
    kmemcheck_bitfield_begin(flags1);
    __u16 queue_mapping;
    __u8 cloned:1,
         nohdr:1,
         fclone:2,
         peeked:1,
         head_frag:1,
         xmit_more:1;
    /* one bit hole */
    kmemcheck_bitfield_end(flags1);
    /* fields enclosed in headers_start/headers_end are copied
     * using a single memcpy() in __copy_skb_header()
     */
    /* private: */
    __u32 headers_start[0];
    /* public: */
    /* if you move pkt_type around you also must adapt those constants */
#ifdef __BIG_ENDIAN_BITFIELD
#define PKT_TYPE_MAX	(7 << 5)
#else
#define PKT_TYPE_MAX	7
#endif
#define PKT_TYPE_OFFSET() offsetof(struct sk_buff, __pkt_type_offset)
    __u8 __pkt_type_offset[0];
    __u8 pkt_type:3;
    __u8 pfmemalloc:1;
    __u8 ignore_df:1;
    __u8 nfctinfo:3;
    __u8 nf_trace:1;
    __u8 ip_summed:2;
    __u8 ooo_okay:1;
    __u8 l4_hash:1;
    __u8 sw_hash:1;
    __u8 wifi_acked_valid:1;
    __u8 wifi_acked:1;
    __u8 no_fcs:1;
    /* Indicates the inner headers are valid in the skbuff. */
    __u8 encapsulation:1;
    __u8 encap_hdr_csum:1;
    __u8 csum_valid:1;
    __u8 csum_complete_sw:1;
    __u8 csum_level:2;
    __u8 csum_bad:1;
#ifdef CONFIG_IPV6_NDISC_NODETYPE
    __u8 ndisc_nodetype:2;
#endif
    __u8 ipvs_property:1;
    __u8 inner_protocol_type:1;
    __u8 remcsum_offload:1;
    /* 3 or 5 bit hole */
#ifdef CONFIG_NET_SCHED
    __u16 tc_index; /* traffic control index */
#ifdef CONFIG_NET_CLS_ACT
    __u16 tc_verd; /* traffic control verdict */
#endif
#endif
    union {
        __wsum csum;
        struct {
            __u16 csum_start;
            __u16 csum_offset;
        };
    };
    __u32 priority;
    int	skb_iif;
    __u32 hash;
    __be16 vlan_proto;
    __u16 vlan_tci;
#if defined(CONFIG_NET_RX_BUSY_POLL) || defined(CONFIG_XPS)
    union {
        unsigned int	napi_id;
        unsigned int	sender_cpu;
    };
#endif
#ifdef CONFIG_NETWORK_SECMARK
    __u32 secmark;
#endif
    union {
        __u32 mark;
        __u32 reserved_tailroom;
    };
    union {
        __be16 inner_protocol;
        __u8 inner_ipproto;
    };
    __u16 inner_transport_header;
    __u16 inner_network_header;
    __u16 inner_mac_header;
    __be16 protocol;
    __u16 transport_header;
    __u16 network_header;
    __u16 mac_header;
    /* private: */
    __u32 headers_end[0];
    /* public: */
    /* These elements must be at the end, see alloc_skb() for details. */
    sk_buff_data_t	tail;
    sk_buff_data_t	end;
    unsigned char	*head,
                    *data;
    unsigned int	truesize;
    atomic_t	users;
};
#ifdef __KERNEL__
/*
 * Handling routines are only of interest to the kernel
 */
#include <linux/slab.h>
#define SKB_ALLOC_FCLONE	0x01
#define SKB_ALLOC_RX	0x02
#define SKB_ALLOC_NAPI	0x04
/* Returns true if the skb was allocated from PFMEMALLOC reserves */
static inline bool skb_pfmemalloc(const struct sk_buff *skb)
{
    return unlikely(skb->pfmemalloc);
}
/*
 * skb might have a dst pointer attached, refcounted or not.
 * _skb_refdst low order bit is set if refcount was _not_ taken
 */
#define SKB_DST_NOREF	1UL
#define SKB_DST_PTRMASK	~(SKB_DST_NOREF)
/**
 * skb_dst - returns skb dst_entry
 * @skb: buffer
 *
 * Returns skb dst_entry, regardless of reference taken or not.
 */
static inline struct dst_entry *skb_dst(const struct sk_buff *skb)
{
    /* If refdst was not refcounted, check we still are in a
     * rcu_read_lock section
     */
    WARN_ON((skb->_skb_refdst & SKB_DST_NOREF) &&
            !rcu_read_lock_held() &&
            !rcu_read_lock_bh_held());
    return (struct dst_entry *)(skb->_skb_refdst & SKB_DST_PTRMASK);
}
/**
 * skb_dst_set - sets skb dst
 * @skb: buffer
 * @dst: dst entry
 *
 * Sets skb dst, assuming a reference was taken on dst and should
 * be released by skb_dst_drop()
 */
static inline void skb_dst_set(struct sk_buff *skb, struct dst_entry *dst)
{
    skb->_skb_refdst = (unsigned long)dst;
}
/**
 * skb_dst_set_noref - sets skb dst, hopefully, without taking reference
 * @skb: buffer
 * @dst: dst entry
 *
 * Sets skb dst, assuming a reference was not taken on dst.
 * If dst entry is cached, we do not take reference and dst_release
 * will be avoided by refdst_drop. If dst entry is not cached, we take
 * reference, so that last dst_release can destroy the dst immediately.
 */
static inline void skb_dst_set_noref(struct sk_buff *skb, struct dst_entry *dst)
{
    WARN_ON(!rcu_read_lock_held() && !rcu_read_lock_bh_held());
    skb->_skb_refdst = (unsigned long)dst | SKB_DST_NOREF;
}
/**
 * skb_dst_is_noref - Test if skb dst isn't refcounted
 * @skb: buffer
 */
static inline bool skb_dst_is_noref(const struct sk_buff *skb)
{
    return (skb->_skb_refdst & SKB_DST_NOREF) && skb_dst(skb);
}
static inline struct rtable *skb_rtable(const struct sk_buff *skb)
{
    return (struct rtable *)skb_dst(skb);
}
void kfree_skb(struct sk_buff *skb);
void kfree_skb_list(struct sk_buff *segs);
void skb_tx_error(struct sk_buff *skb);
void consume_skb(struct sk_buff *skb);
void __kfree_skb(struct sk_buff *skb);
extern struct kmem_cache *skbuff_head_cache;
void kfree_skb_partial(struct sk_buff *skb, bool head_stolen);
bool skb_try_coalesce(struct sk_buff *to, struct sk_buff *from,
        bool *fragstolen, int *delta_truesize);
struct sk_buff *__alloc_skb(unsigned int size, gfp_t priority, int flags,
        int node);
struct sk_buff *__build_skb(void *data, unsigned int frag_size);
struct sk_buff *build_skb(void *data, unsigned int frag_size);
static inline struct sk_buff *alloc_skb(unsigned int size,
        gfp_t priority)
{
    return __alloc_skb(size, priority, 0, NUMA_NO_NODE);
}
struct sk_buff *alloc_skb_with_frags(unsigned long header_len,
        unsigned long data_len,
        int max_page_order,
        int *errcode,
        gfp_t gfp_mask);
/* Layout of fast clones : [skb1][skb2][fclone_ref] */
struct sk_buff_fclones {
    struct sk_buff skb1;
    struct sk_buff skb2;
    atomic_t	fclone_ref;
};
/**
 * skb_fclone_busy - check if fclone is busy
 * @skb: buffer
 *
 * Returns true is skb is a fast clone, and its clone is not freed.
 * Some drivers call skb_orphan() in their ndo_start_xmit(),
 * so we also check that this didnt happen.
 */
static inline bool skb_fclone_busy(const struct sock *sk,
        const struct sk_buff *skb)
{
    const struct sk_buff_fclones *fclones;
    fclones = container_of(skb, struct sk_buff_fclones, skb1);
    return skb->fclone == SKB_FCLONE_ORIG &&
        atomic_read(&fclones->fclone_ref) > 1 &&
        fclones->skb2.sk == sk;
}
static inline struct sk_buff *alloc_skb_fclone(unsigned int size,
        gfp_t priority)
{
    return __alloc_skb(size, priority, SKB_ALLOC_FCLONE, NUMA_NO_NODE);
}
struct sk_buff *__alloc_skb_head(gfp_t priority, int node);
static inline struct sk_buff *alloc_skb_head(gfp_t priority)
{
    return __alloc_skb_head(priority, -1);
}
struct sk_buff *skb_morph(struct sk_buff *dst, struct sk_buff *src);
int skb_copy_ubufs(struct sk_buff *skb, gfp_t gfp_mask);
struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t priority);
struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t priority);
struct sk_buff *__pskb_copy_fclone(struct sk_buff *skb, int headroom,
        gfp_t gfp_mask, bool fclone);
static inline struct sk_buff *__pskb_copy(struct sk_buff *skb, int headroom,
        gfp_t gfp_mask)
{
    return __pskb_copy_fclone(skb, headroom, gfp_mask, false);
}
int pskb_expand_head(struct sk_buff *skb, int nhead, int ntail, gfp_t gfp_mask);
struct sk_buff *skb_realloc_headroom(struct sk_buff *skb,
        unsigned int headroom);
struct sk_buff *skb_copy_expand(const struct sk_buff *skb, int newheadroom,
        int newtailroom, gfp_t priority);
int skb_to_sgvec_nomark(struct sk_buff *skb, struct scatterlist *sg,
        int offset, int len);
int skb_to_sgvec(struct sk_buff *skb, struct scatterlist *sg, int offset,
        int len);
int skb_cow_data(struct sk_buff *skb, int tailbits, struct sk_buff **trailer);
int skb_pad(struct sk_buff *skb, int pad);
#define dev_kfree_skb(a) consume_skb(a)
int skb_append_datato_frags(struct sock *sk, struct sk_buff *skb,
        int getfrag(void *from, char *to, int offset,
            int len, int odd, struct sk_buff *skb),
        void *from, int length);
int skb_append_pagefrags(struct sk_buff *skb, struct page *page,
        int offset, size_t size);
struct skb_seq_state {
    __u32 lower_offset;
    __u32 upper_offset;
    __u32 frag_idx;
    __u32 stepped_offset;
    struct sk_buff *root_skb;
    struct sk_buff *cur_skb;
    __u8 *frag_data;
};
void skb_prepare_seq_read(struct sk_buff *skb, unsigned int from,
        unsigned int to, struct skb_seq_state *st);
unsigned int skb_seq_read(unsigned int consumed, const u8 **data,
        struct skb_seq_state *st);
void skb_abort_seq_read(struct skb_seq_state *st);
unsigned int skb_find_text(struct sk_buff *skb, unsigned int from,
        unsigned int to, struct ts_config *config);
/*
 * Packet hash types specify the type of hash in skb_set_hash.
 *
 * Hash types refer to the protocol layer addresses which are used to
 * construct a packet's hash. The hashes are used to differentiate or identify
 * flows of the protocol layer for the hash type. Hash types are either
 * layer-2 (L2), layer-3 (L3), or layer-4 (L4).
 *
 * Properties of hashes:
 *
 * 1) Two packets in different flows have different hash values
 * 2) Two packets in the same flow should have the same hash value
 *
 * A hash at a higher layer is considered to be more specific. A driver should
 * set the most specific hash possible.
 *
 * A driver cannot indicate a more specific hash than the layer at which a hash
 * was computed. For instance an L3 hash cannot be set as an L4 hash.
 *
 * A driver may indicate a hash level which is less specific than the
 * actual layer the hash was computed on. For instance, a hash computed
 * at L4 may be considered an L3 hash. This should only be done if the
 * driver can't unambiguously determine that the HW computed the hash at
 * the higher layer. Note that the "should" in the second property above
 * permits this.
 */
enum pkt_hash_types {
    PKT_HASH_TYPE_NONE, /* Undefined type */
    PKT_HASH_TYPE_L2, /* Input: src_MAC, dest_MAC */
    PKT_HASH_TYPE_L3, /* Input: src_IP, dst_IP */
    PKT_HASH_TYPE_L4, /* Input: src_IP, dst_IP, src_port, dst_port */
};
    static inline void
skb_set_hash(struct sk_buff *skb, __u32 hash, enum pkt_hash_types type)
{
    skb->l4_hash = (type == PKT_HASH_TYPE_L4);
    skb->sw_hash = 0;
    skb->hash = hash;
}
static inline __u32 skb_get_hash(struct sk_buff *skb)
{
    if (!skb->l4_hash && !skb->sw_hash)
        __skb_get_hash(skb);
    return skb->hash;
}
__u32 skb_get_hash_perturb(const struct sk_buff *skb, u32 perturb);
static inline __u32 skb_get_hash_raw(const struct sk_buff *skb)
{
    return skb->hash;
}
static inline void skb_clear_hash(struct sk_buff *skb)
{
    skb->hash = 0;
    skb->sw_hash = 0;
    skb->l4_hash = 0;
}
static inline void skb_clear_hash_if_not_l4(struct sk_buff *skb)
{
    if (!skb->l4_hash)
        skb_clear_hash(skb);
}
static inline void skb_copy_hash(struct sk_buff *to, const struct sk_buff *from)
{
    to->hash = from->hash;
    to->sw_hash = from->sw_hash;
    to->l4_hash = from->l4_hash;
};
static inline void skb_sender_cpu_clear(struct sk_buff *skb)
{
#ifdef CONFIG_XPS
    skb->sender_cpu = 0;
#endif
}
#ifdef NET_SKBUFF_DATA_USES_OFFSET
static inline unsigned char *skb_end_pointer(const struct sk_buff *skb)
{
    return skb->head + skb->end;
}
static inline unsigned int skb_end_offset(const struct sk_buff *skb)
{
    return skb->end;
}
#else
static inline unsigned char *skb_end_pointer(const struct sk_buff *skb)
{
    return skb->end;
}
static inline unsigned int skb_end_offset(const struct sk_buff *skb)
{
    return skb->end - skb->head;
}
#endif
/* Internal */
#define skb_shinfo(SKB) ((struct skb_shared_info *)(skb_end_pointer(SKB)))
static inline struct skb_shared_hwtstamps *skb_hwtstamps(struct sk_buff *skb)
{
    return &skb_shinfo(skb)->hwtstamps;
}
/**
 * skb_queue_empty - check if a queue is empty
 * @list: queue head
 *
 * Returns true if the queue is empty, false otherwise.
 */
static inline int skb_queue_empty(const struct sk_buff_head *list)
{
    return list->next == (const struct sk_buff *) list;
}
/**
 * skb_queue_is_last - check if skb is the last entry in the queue
 * @list: queue head
 * @skb: buffer
 *
 * Returns true if @skb is the last buffer on the list.
 */
static inline bool skb_queue_is_last(const struct sk_buff_head *list,
        const struct sk_buff *skb)
{
    return skb->next == (const struct sk_buff *) list;
}
/**
 * skb_queue_is_first - check if skb is the first entry in the queue
 * @list: queue head
 * @skb: buffer
 *
 * Returns true if @skb is the first buffer on the list.
 */
static inline bool skb_queue_is_first(const struct sk_buff_head *list,
        const struct sk_buff *skb)
{
    return skb->prev == (const struct sk_buff *) list;
}
/**
 * skb_queue_next - return the next packet in the queue
 * @list: queue head
 * @skb: current buffer
 *
 * Return the next packet in @list after @skb. It is only valid to
 * call this if skb_queue_is_last() evaluates to false.
 */
static inline struct sk_buff *skb_queue_next(const struct sk_buff_head *list,
        const struct sk_buff *skb)
{
    /* This BUG_ON may seem severe, but if we just return then we
     * are going to dereference garbage.
     */
    BUG_ON(skb_queue_is_last(list, skb));
    return skb->next;
}
/**
 * skb_queue_prev - return the prev packet in the queue
 * @list: queue head
 * @skb: current buffer
 *
 * Return the prev packet in @list before @skb. It is only valid to
 * call this if skb_queue_is_first() evaluates to false.
 */
static inline struct sk_buff *skb_queue_prev(const struct sk_buff_head *list,
        const struct sk_buff *skb)
{
    /* This BUG_ON may seem severe, but if we just return then we
     * are going to dereference garbage.
     */
    BUG_ON(skb_queue_is_first(list, skb));
    return skb->prev;
}
/**
 * skb_get - reference buffer
 * @skb: buffer to reference
 *
 * Makes another reference to a socket buffer and returns a pointer
 * to the buffer.
 */
static inline struct sk_buff *skb_get(struct sk_buff *skb)
{
    atomic_inc(&skb->users);
    return skb;
}
/*
 * If users == 1, we are the only owner and are can avoid redundant
 * atomic change.
 */
/**
 * skb_cloned - is the buffer a clone
 * @skb: buffer to check
 *
 * Returns true if the buffer was generated with skb_clone() and is
 * one of multiple shared copies of the buffer. Cloned buffers are
 * shared data so must not be written to under normal circumstances.
 */
static inline int skb_cloned(const struct sk_buff *skb)
{
    return skb->cloned &&
        (atomic_read(&skb_shinfo(skb)->dataref) & SKB_DATAREF_MASK) != 1;
}
static inline int skb_unclone(struct sk_buff *skb, gfp_t pri)
{
    might_sleep_if(pri & __GFP_WAIT);
    if (skb_cloned(skb))
        return pskb_expand_head(skb, 0, 0, pri);
    return 0;
}
/**
 * skb_header_cloned - is the header a clone
 * @skb: buffer to check
 *
 * Returns true if modifying the header part of the buffer requires
 * the data to be copied.
 */
static inline int skb_header_cloned(const struct sk_buff *skb)
{
    int dataref;
    if (!skb->cloned)
        return 0;
    dataref = atomic_read(&skb_shinfo(skb)->dataref);
    dataref = (dataref & SKB_DATAREF_MASK) - (dataref >> SKB_DATAREF_SHIFT);
    return dataref != 1;
}
/**
 * skb_header_release - release reference to header
 * @skb: buffer to operate on
 *
 * Drop a reference to the header part of the buffer. This is done
 * by acquiring a payload reference. You must not read from the header
 * part of skb->data after this.
 * Note : Check if you can use __skb_header_release() instead.
 */
static inline void skb_header_release(struct sk_buff *skb)
{
    BUG_ON(skb->nohdr);
    skb->nohdr = 1;
    atomic_add(1 << SKB_DATAREF_SHIFT, &skb_shinfo(skb)->dataref);
}
/**
 * __skb_header_release - release reference to header
 * @skb: buffer to operate on
 *
 * Variant of skb_header_release() assuming skb is private to caller.
 * We can avoid one atomic operation.
 */
static inline void __skb_header_release(struct sk_buff *skb)
{
    skb->nohdr = 1;
    atomic_set(&skb_shinfo(skb)->dataref, 1 + (1 << SKB_DATAREF_SHIFT));
}
/**
 * skb_shared - is the buffer shared
 * @skb: buffer to check
 *
 * Returns true if more than one person has a reference to this
 * buffer.
 */
static inline int skb_shared(const struct sk_buff *skb)
{
    return atomic_read(&skb->users) != 1;
}
/**
 * skb_share_check - check if buffer is shared and if so clone it
 * @skb: buffer to check
 * @pri: priority for memory allocation
 *
 * If the buffer is shared the buffer is cloned and the old copy
 * drops a reference. A new clone with a single reference is returned.
 * If the buffer is not shared the original buffer is returned. When
 * being called from interrupt status or with spinlocks held pri must
 * be GFP_ATOMIC.
 *
 * NULL is returned on a memory allocation failure.
 */
static inline struct sk_buff *skb_share_check(struct sk_buff *skb, gfp_t pri)
{
    might_sleep_if(pri & __GFP_WAIT);
    if (skb_shared(skb)) {
        struct sk_buff *nskb = skb_clone(skb, pri);
        if (likely(nskb))
            consume_skb(skb);
        else
            kfree_skb(skb);
        skb = nskb;
    }
    return skb;
}
/*
 * Copy shared buffers into a new sk_buff. We effectively do COW on
 * packets to handle cases where we have a local reader and forward
 * and a couple of other messy ones. The normal one is tcpdumping
 * a packet thats being forwarded.
 */
/**
 * skb_unshare - make a copy of a shared buffer
 * @skb: buffer to check
 * @pri: priority for memory allocation
 *
 * If the socket buffer is a clone then this function creates a new
 * copy of the data, drops a reference count on the old copy and returns
 * the new copy with the reference count at 1. If the buffer is not a clone
 * the original buffer is returned. When called with a spinlock held or
 * from interrupt state @pri must be %GFP_ATOMIC
 *
 * %NULL is returned on a memory allocation failure.
 */
static inline struct sk_buff *skb_unshare(struct sk_buff *skb,
        gfp_t pri)
{
    might_sleep_if(pri & __GFP_WAIT);
    if (skb_cloned(skb)) {
        struct sk_buff *nskb = skb_copy(skb, pri);
        /* Free our shared copy */
        if (likely(nskb))
            consume_skb(skb);
        else
            kfree_skb(skb);
        skb = nskb;
    }
    return skb;
}
/**
 * skb_peek - peek at the head of an &sk_buff_head
 * @list_: list to peek at
 *
 * Peek an &sk_buff. Unlike most other operations you _MUST_
 * be careful with this one. A peek leaves the buffer on the
 * list and someone else may run off with it. You must hold
 * the appropriate locks or have a private queue to do this.
 *
 * Returns %NULL for an empty list or a pointer to the head element.
 * The reference count is not incremented and the reference is therefore
 * volatile. Use with caution.
 */
static inline struct sk_buff *skb_peek(const struct sk_buff_head *list_)
{
    struct sk_buff *skb = list_->next;
    if (skb == (struct sk_buff *)list_)
        skb = NULL;
    return skb;
}
/**
 * skb_peek_next - peek skb following the given one from a queue
 * @skb: skb to start from
 * @list_: list to peek at
 *
 * Returns %NULL when the end of the list is met or a pointer to the
 * next element. The reference count is not incremented and the
 * reference is therefore volatile. Use with caution.
 */
static inline struct sk_buff *skb_peek_next(struct sk_buff *skb,
        const struct sk_buff_head *list_)
{
    struct sk_buff *next = skb->next;
    if (next == (struct sk_buff *)list_)
        next = NULL;
    return next;
}
/**
 * skb_peek_tail - peek at the tail of an &sk_buff_head
 * @list_: list to peek at
 *
 * Peek an &sk_buff. Unlike most other operations you _MUST_
 * be careful with this one. A peek leaves the buffer on the
 * list and someone else may run off with it. You must hold
 * the appropriate locks or have a private queue to do this.
 *
 * Returns %NULL for an empty list or a pointer to the tail element.
 * The reference count is not incremented and the reference is therefore
 * volatile. Use with caution.
 */
static inline struct sk_buff *skb_peek_tail(const struct sk_buff_head *list_)
{
    struct sk_buff *skb = list_->prev;
    if (skb == (struct sk_buff *)list_)
        skb = NULL;
    return skb;
}
/**
 * skb_queue_len - get queue length
 * @list_: list to measure
 *
 * Return the length of an &sk_buff queue.
 */
static inline __u32 skb_queue_len(const struct sk_buff_head *list_)
{
    return list_->qlen;
}
/**
 * __skb_queue_head_init - initialize non-spinlock portions of sk_buff_head
 * @list: queue to initialize
 *
 * This initializes only the list and queue length aspects of
 * an sk_buff_head object. This allows to initialize the list
 * aspects of an sk_buff_head without reinitializing things like
 * the spinlock. It can also be used for on-stack sk_buff_head
 * objects where the spinlock is known to not be used.
 */
static inline void __skb_queue_head_init(struct sk_buff_head *list)
{
    list->prev = list->next = (struct sk_buff *)list;
    list->qlen = 0;
}
/*
 * This function creates a split out lock class for each invocation;
 * this is needed for now since a whole lot of users of the skb-queue
 * infrastructure in drivers have different locking usage (in hardirq)
 * than the networking core (in softirq only). In the long run either the
 * network layer or drivers should need annotation to consolidate the
 * main types of usage into 3 classes.
 */
static inline void skb_queue_head_init(struct sk_buff_head *list)
{
    spin_lock_init(&list->lock);
    __skb_queue_head_init(list);
}
static inline void skb_queue_head_init_class(struct sk_buff_head *list,
        struct lock_class_key *class)
{
    skb_queue_head_init(list);
    lockdep_set_class(&list->lock, class);
}
/*
 * Insert an sk_buff on a list.
 *
 * The "__skb_xxxx()" functions are the non-atomic ones that
 * can only be called with interrupts disabled.
 */
void skb_insert(struct sk_buff *old, struct sk_buff *newsk,
        struct sk_buff_head *list);
static inline void __skb_insert(struct sk_buff *newsk,
        struct sk_buff *prev, struct sk_buff *next,
        struct sk_buff_head *list)
{
    newsk->next = next;
    newsk->prev = prev;
    next->prev = prev->next = newsk;
    list->qlen++;
}
static inline void __skb_queue_splice(const struct sk_buff_head *list,
        struct sk_buff *prev,
        struct sk_buff *next)
{
    struct sk_buff *first = list->next;
    struct sk_buff *last = list->prev;
    first->prev = prev;
    prev->next = first;
    last->next = next;
    next->prev = last;
}
/**
 * skb_queue_splice - join two skb lists, this is designed for stacks
 * @list: the new list to add
 * @head: the place to add it in the first list
 */
static inline void skb_queue_splice(const struct sk_buff_head *list,
        struct sk_buff_head *head)
{
    if (!skb_queue_empty(list)) {
        __skb_queue_splice(list, (struct sk_buff *) head, head->next);
        head->qlen += list->qlen;
    }
}
/**
 * skb_queue_splice_init - join two skb lists and reinitialise the emptied list
 * @list: the new list to add
 * @head: the place to add it in the first list
 *
 * The list at @list is reinitialised
 */
static inline void skb_queue_splice_init(struct sk_buff_head *list,
        struct sk_buff_head *head)
{
    if (!skb_queue_empty(list)) {
        __skb_queue_splice(list, (struct sk_buff *) head, head->next);
        head->qlen += list->qlen;
        __skb_queue_head_init(list);
    }
}
/**
 * skb_queue_splice_tail - join two skb lists, each list being a queue
 * @list: the new list to add
 * @head: the place to add it in the first list
 */
static inline void skb_queue_splice_tail(const struct sk_buff_head *list,
        struct sk_buff_head *head)
{
    if (!skb_queue_empty(list)) {
        __skb_queue_splice(list, head->prev, (struct sk_buff *) head);
        head->qlen += list->qlen;
    }
}
/**
 * skb_queue_splice_tail_init - join two skb lists and reinitialise the emptied list
 * @list: the new list to add
 * @head: the place to add it in the first list
 *
 * Each of the lists is a queue.
 * The list at @list is reinitialised
 */
static inline void skb_queue_splice_tail_init(struct sk_buff_head *list,
        struct sk_buff_head *head)
{
    if (!skb_queue_empty(list)) {
        __skb_queue_splice(list, head->prev, (struct sk_buff *) head);
        head->qlen += list->qlen;
        __skb_queue_head_init(list);
    }
}
/**
 * __skb_queue_after - queue a buffer at the list head
 * @list: list to use
 * @prev: place after this buffer
 * @newsk: buffer to queue
 *
 * Queue a buffer int the middle of a list. This function takes no locks
 * and you must therefore hold required locks before calling it.
 *
 * A buffer cannot be placed on two lists at the same time.
 */
static inline void __skb_queue_after(struct sk_buff_head *list,
        struct sk_buff *prev,
        struct sk_buff *newsk)
{
    __skb_insert(newsk, prev, prev->next, list);
}
void skb_append(struct sk_buff *old, struct sk_buff *newsk,
        struct sk_buff_head *list);
static inline void __skb_queue_before(struct sk_buff_head *list,
        struct sk_buff *next,
        struct sk_buff *newsk)
{
    __skb_insert(newsk, next->prev, next, list);
}
/**
 * __skb_queue_head - queue a buffer at the list head
 * @list: list to use
 * @newsk: buffer to queue
 *
 * Queue a buffer at the start of a list. This function takes no locks
 * and you must therefore hold required locks before calling it.
 *
 * A buffer cannot be placed on two lists at the same time.
 */
void skb_queue_head(struct sk_buff_head *list, struct sk_buff *newsk);
static inline void __skb_queue_head(struct sk_buff_head *list,
        struct sk_buff *newsk)
{
    __skb_queue_after(list, (struct sk_buff *)list, newsk);
}
/**
 * __skb_queue_tail - queue a buffer at the list tail
 * @list: list to use
 * @newsk: buffer to queue
 *
 * Queue a buffer at the end of a list. This function takes no locks
 * and you must therefore hold required locks before calling it.
 *
 * A buffer cannot be placed on two lists at the same time.
 */
void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk);
static inline void __skb_queue_tail(struct sk_buff_head *list,
        struct sk_buff *newsk)
{
    __skb_queue_before(list, (struct sk_buff *)list, newsk);
}
/*
 * remove sk_buff from list. _Must_ be called atomically, and with
 * the list known..
 */
void skb_unlink(struct sk_buff *skb, struct sk_buff_head *list);
static inline void __skb_unlink(struct sk_buff *skb, struct sk_buff_head *list)
{
    struct sk_buff *next, *prev;
    list->qlen--;
    next = skb->next;
    prev = skb->prev;
    skb->next = skb->prev = NULL;
    next->prev = prev;
    prev->next = next;
}
/**
 * __skb_dequeue - remove from the head of the queue
 * @list: list to dequeue from
 *
 * Remove the head of the list. This function does not take any locks
 * so must be used with appropriate locks held only. The head item is
 * returned or %NULL if the list is empty.
 */
struct sk_buff *skb_dequeue(struct sk_buff_head *list);
static inline struct sk_buff *__skb_dequeue(struct sk_buff_head *list)
{
    struct sk_buff *skb = skb_peek(list);
    if (skb)
        __skb_unlink(skb, list);
    return skb;
}
/**
 * __skb_dequeue_tail - remove from the tail of the queue
 * @list: list to dequeue from
 *
 * Remove the tail of the list. This function does not take any locks
 * so must be used with appropriate locks held only. The tail item is
 * returned or %NULL if the list is empty.
 */
struct sk_buff *skb_dequeue_tail(struct sk_buff_head *list);
static inline struct sk_buff *__skb_dequeue_tail(struct sk_buff_head *list)
{
    struct sk_buff *skb = skb_peek_tail(list);
    if (skb)
        __skb_unlink(skb, list);
    return skb;
}
static inline bool skb_is_nonlinear(const struct sk_buff *skb)
{
    return skb->data_len;
}
static inline unsigned int skb_headlen(const struct sk_buff *skb)
{
    return skb->len - skb->data_len;
}
static inline int skb_pagelen(const struct sk_buff *skb)
{
    int i, len = 0;
    for (i = (int)skb_shinfo(skb)->nr_frags - 1; i >= 0; i--)
        len += skb_frag_size(&skb_shinfo(skb)->frags[i]);
    return len + skb_headlen(skb);
}
/**
 * __skb_fill_page_desc - initialise a paged fragment in an skb
 * @skb: buffer containing fragment to be initialised
 * @i: paged fragment index to initialise
 * @page: the page to use for this fragment
 * @off: the offset to the data with @page
 * @size: the length of the data
 *
 * Initialises the @i'th fragment of @skb to point to &size bytes at
 * offset @off within @page.
 *
 * Does not take any additional reference on the fragment.
 */
static inline void __skb_fill_page_desc(struct sk_buff *skb, int i,
        struct page *page, int off, int size)
{
    skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
    /*
     * Propagate page pfmemalloc to the skb if we can. The problem is
     * that not all callers have unique ownership of the page but rely
     * on page_is_pfmemalloc doing the right thing(tm).
     */
    frag->page.p	= page;
    frag->page_offset = off;
    skb_frag_size_set(frag, size);
    page = compound_head(page);
    if (page_is_pfmemalloc(page))
        skb->pfmemalloc = true;
}
/**
 * skb_fill_page_desc - initialise a paged fragment in an skb
 * @skb: buffer containing fragment to be initialised
 * @i: paged fragment index to initialise
 * @page: the page to use for this fragment
 * @off: the offset to the data with @page
 * @size: the length of the data
 *
 * As per __skb_fill_page_desc() -- initialises the @i'th fragment of
 * @skb to point to @size bytes at offset @off within @page. In
 * addition updates @skb such that @i is the last fragment.
 *
 * Does not take any additional reference on the fragment.
 */
static inline void skb_fill_page_desc(struct sk_buff *skb, int i,
        struct page *page, int off, int size)
{
    __skb_fill_page_desc(skb, i, page, off, size);
    skb_shinfo(skb)->nr_frags = i + 1;
}
void skb_add_rx_frag(struct sk_buff *skb, int i, struct page *page, int off,
        int size, unsigned int truesize);
void skb_coalesce_rx_frag(struct sk_buff *skb, int i, int size,
        unsigned int truesize);
#define SKB_PAGE_ASSERT(skb) BUG_ON(skb_shinfo(skb)->nr_frags)
#define SKB_FRAG_ASSERT(skb) BUG_ON(skb_has_frag_list(skb))
#define SKB_LINEAR_ASSERT(skb) BUG_ON(skb_is_nonlinear(skb))
#ifdef NET_SKBUFF_DATA_USES_OFFSET
static inline unsigned char *skb_tail_pointer(const struct sk_buff *skb)
{
    return skb->head + skb->tail;
}
static inline void skb_reset_tail_pointer(struct sk_buff *skb)
{
    skb->tail = skb->data - skb->head;
}
static inline void skb_set_tail_pointer(struct sk_buff *skb, const int offset)
{
    skb_reset_tail_pointer(skb);
    skb->tail += offset;
}
#else /* NET_SKBUFF_DATA_USES_OFFSET */
static inline unsigned char *skb_tail_pointer(const struct sk_buff *skb)
{
    return skb->tail;
}
static inline void skb_reset_tail_pointer(struct sk_buff *skb)
{
    skb->tail = skb->data;
}
static inline void skb_set_tail_pointer(struct sk_buff *skb, const int offset)
{
    skb->tail = skb->data + offset;
}
#endif /* NET_SKBUFF_DATA_USES_OFFSET */
/*
 * Add data to an sk_buff
 */
unsigned char *pskb_put(struct sk_buff *skb, struct sk_buff *tail, int len);
unsigned char *skb_put(struct sk_buff *skb, unsigned int len);
static inline unsigned char *__skb_put(struct sk_buff *skb, unsigned int len)
{
    unsigned char *tmp = skb_tail_pointer(skb);
    SKB_LINEAR_ASSERT(skb);
    skb->tail += len;
    skb->len += len;
    return tmp;
}
unsigned char *skb_push(struct sk_buff *skb, unsigned int len);
static inline unsigned char *__skb_push(struct sk_buff *skb, unsigned int len)
{
    skb->data -= len;
    skb->len += len;
    return skb->data;
}
unsigned char *skb_pull(struct sk_buff *skb, unsigned int len);
static inline unsigned char *__skb_pull(struct sk_buff *skb, unsigned int len)
{
    skb->len -= len;
    BUG_ON(skb->len < skb->data_len);
    return skb->data += len;
}
static inline unsigned char *skb_pull_inline(struct sk_buff *skb, unsigned int len)
{
    return unlikely(len > skb->len) ? NULL : __skb_pull(skb, len);
}
unsigned char *__pskb_pull_tail(struct sk_buff *skb, int delta);
static inline unsigned char *__pskb_pull(struct sk_buff *skb, unsigned int len)
{
    if (len > skb_headlen(skb) &&
            !__pskb_pull_tail(skb, len - skb_headlen(skb)))
        return NULL;
    skb->len -= len;
    return skb->data += len;
}
static inline unsigned char *pskb_pull(struct sk_buff *skb, unsigned int len)
{
    return unlikely(len > skb->len) ? NULL : __pskb_pull(skb, len);
}
static inline int pskb_may_pull(struct sk_buff *skb, unsigned int len)
{
    if (likely(len <= skb_headlen(skb)))
        return 1;
    if (unlikely(len > skb->len))
        return 0;
    return __pskb_pull_tail(skb, len - skb_headlen(skb)) != NULL;
}
/**
 * skb_headroom - bytes at buffer head
 * @skb: buffer to check
 *
 * Return the number of bytes of free space at the head of an &sk_buff.
 */
static inline unsigned int skb_headroom(const struct sk_buff *skb)
{
    return skb->data - skb->head;
}
/**
 * skb_tailroom - bytes at buffer end
 * @skb: buffer to check
 *
 * Return the number of bytes of free space at the tail of an sk_buff
 */
static inline int skb_tailroom(const struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) ? 0 : skb->end - skb->tail;
}
/**
 * skb_availroom - bytes at buffer end
 * @skb: buffer to check
 *
 * Return the number of bytes of free space at the tail of an sk_buff
 * allocated by sk_stream_alloc()
 */
static inline int skb_availroom(const struct sk_buff *skb)
{
    if (skb_is_nonlinear(skb))
        return 0;
    return skb->end - skb->tail - skb->reserved_tailroom;
}
/**
 * skb_reserve - adjust headroom
 * @skb: buffer to alter
 * @len: bytes to move
 *
 * Increase the headroom of an empty &sk_buff by reducing the tail
 * room. This is only allowed for an empty buffer.
 */
static inline void skb_reserve(struct sk_buff *skb, int len)
{
    skb->data += len;
    skb->tail += len;
}
#define ENCAP_TYPE_ETHER	0
#define ENCAP_TYPE_IPPROTO	1
static inline void skb_set_inner_protocol(struct sk_buff *skb,
        __be16 protocol)
{
    skb->inner_protocol = protocol;
    skb->inner_protocol_type = ENCAP_TYPE_ETHER;
}
static inline void skb_set_inner_ipproto(struct sk_buff *skb,
        __u8 ipproto)
{
    skb->inner_ipproto = ipproto;
    skb->inner_protocol_type = ENCAP_TYPE_IPPROTO;
}
static inline void skb_reset_inner_headers(struct sk_buff *skb)
{
    skb->inner_mac_header = skb->mac_header;
    skb->inner_network_header = skb->network_header;
    skb->inner_transport_header = skb->transport_header;
}
static inline void skb_reset_mac_len(struct sk_buff *skb)
{
    skb->mac_len = skb->network_header - skb->mac_header;
}
static inline unsigned char *skb_inner_transport_header(const struct sk_buff
        *skb)
{
    return skb->head + skb->inner_transport_header;
}
static inline void skb_reset_inner_transport_header(struct sk_buff *skb)
{
    skb->inner_transport_header = skb->data - skb->head;
}
static inline void skb_set_inner_transport_header(struct sk_buff *skb,
        const int offset)
{
    skb_reset_inner_transport_header(skb);
    skb->inner_transport_header += offset;
}
static inline unsigned char *skb_inner_network_header(const struct sk_buff *skb)
{
    return skb->head + skb->inner_network_header;
}
static inline void skb_reset_inner_network_header(struct sk_buff *skb)
{
    skb->inner_network_header = skb->data - skb->head;
}
static inline void skb_set_inner_network_header(struct sk_buff *skb,
        const int offset)
{
    skb_reset_inner_network_header(skb);
    skb->inner_network_header += offset;
}
static inline unsigned char *skb_inner_mac_header(const struct sk_buff *skb)
{
    return skb->head + skb->inner_mac_header;
}
static inline void skb_reset_inner_mac_header(struct sk_buff *skb)
{
    skb->inner_mac_header = skb->data - skb->head;
}
static inline void skb_set_inner_mac_header(struct sk_buff *skb,
        const int offset)
{
    skb_reset_inner_mac_header(skb);
    skb->inner_mac_header += offset;
}
static inline bool skb_transport_header_was_set(const struct sk_buff *skb)
{
    return skb->transport_header != (typeof(skb->transport_header))~0U;
}
static inline unsigned char *skb_transport_header(const struct sk_buff *skb)
{
    return skb->head + skb->transport_header;
}
static inline void skb_reset_transport_header(struct sk_buff *skb)
{
    skb->transport_header = skb->data - skb->head;
}
static inline void skb_set_transport_header(struct sk_buff *skb,
        const int offset)
{
    skb_reset_transport_header(skb);
    skb->transport_header += offset;
}
static inline unsigned char *skb_network_header(const struct sk_buff *skb)
{
    return skb->head + skb->network_header;
}
static inline void skb_reset_network_header(struct sk_buff *skb)
{
    skb->network_header = skb->data - skb->head;
}
static inline void skb_set_network_header(struct sk_buff *skb, const int offset)
{
    skb_reset_network_header(skb);
    skb->network_header += offset;
}
static inline unsigned char *skb_mac_header(const struct sk_buff *skb)
{
    return skb->head + skb->mac_header;
}
static inline int skb_mac_header_was_set(const struct sk_buff *skb)
{
    return skb->mac_header != (typeof(skb->mac_header))~0U;
}
static inline void skb_reset_mac_header(struct sk_buff *skb)
{
    skb->mac_header = skb->data - skb->head;
}
static inline void skb_set_mac_header(struct sk_buff *skb, const int offset)
{
    skb_reset_mac_header(skb);
    skb->mac_header += offset;
}
static inline void skb_pop_mac_header(struct sk_buff *skb)
{
    skb->mac_header = skb->network_header;
}
static inline void skb_probe_transport_header(struct sk_buff *skb,
        const int offset_hint)
{
    struct flow_keys keys;
    if (skb_transport_header_was_set(skb))
        return;
    else if (skb_flow_dissect_flow_keys(skb, &keys))
        skb_set_transport_header(skb, keys.control.thoff);
    else
        skb_set_transport_header(skb, offset_hint);
}
static inline void skb_mac_header_rebuild(struct sk_buff *skb)
{
    if (skb_mac_header_was_set(skb)) {
        const unsigned char *old_mac = skb_mac_header(skb);
        skb_set_mac_header(skb, -skb->mac_len);
        memmove(skb_mac_header(skb), old_mac, skb->mac_len);
    }
}
static inline int skb_checksum_start_offset(const struct sk_buff *skb)
{
    return skb->csum_start - skb_headroom(skb);
}
static inline int skb_transport_offset(const struct sk_buff *skb)
{
    return skb_transport_header(skb) - skb->data;
}
static inline u32 skb_network_header_len(const struct sk_buff *skb)
{
    return skb->transport_header - skb->network_header;
}
static inline u32 skb_inner_network_header_len(const struct sk_buff *skb)
{
    return skb->inner_transport_header - skb->inner_network_header;
}
static inline int skb_network_offset(const struct sk_buff *skb)
{
    return skb_network_header(skb) - skb->data;
}
static inline int skb_inner_network_offset(const struct sk_buff *skb)
{
    return skb_inner_network_header(skb) - skb->data;
}
static inline int pskb_network_may_pull(struct sk_buff *skb, unsigned int len)
{
    return pskb_may_pull(skb, skb_network_offset(skb) + len);
}
/*
 * CPUs often take a performance hit when accessing unaligned memory
 * locations. The actual performance hit varies, it can be small if the
 * hardware handles it or large if we have to take an exception and fix it
 * in software.
 *
 * Since an ethernet header is 14 bytes network drivers often end up with
 * the IP header at an unaligned offset. The IP header can be aligned by
 * shifting the start of the packet by 2 bytes. Drivers should do this
 * with:
 *
 * skb_reserve(skb, NET_IP_ALIGN);
 *
 * The downside to this alignment of the IP header is that the DMA is now
 * unaligned. On some architectures the cost of an unaligned DMA is high
 * and this cost outweighs the gains made by aligning the IP header.
 *
 * Since this trade off varies between architectures, we allow NET_IP_ALIGN
 * to be overridden.
 */
#ifndef NET_IP_ALIGN
#define NET_IP_ALIGN	2
#endif
/*
 * The networking layer reserves some headroom in skb data (via
 * dev_alloc_skb). This is used to avoid having to reallocate skb data when
 * the header has to grow. In the default case, if the header has to grow
 * 32 bytes or less we avoid the reallocation.
 *
 * Unfortunately this headroom changes the DMA alignment of the resulting
 * network packet. As for NET_IP_ALIGN, this unaligned DMA is expensive
 * on some architectures. An architecture can override this value,
 * perhaps setting it to a cacheline in size (since that will maintain
 * cacheline alignment of the DMA). It must be a power of 2.
 *
 * Various parts of the networking layer expect at least 32 bytes of
 * headroom, you should not reduce this.
 *
 * Using max(32, L1_CACHE_BYTES) makes sense (especially with RPS)
 * to reduce average number of cache lines per packet.
 * get_rps_cpus() for example only access one 64 bytes aligned block :
 * NET_IP_ALIGN(2) + ethernet_header(14) + IP_header(20/40) + ports(8)
 */
#ifndef NET_SKB_PAD
#define NET_SKB_PAD	max(32, L1_CACHE_BYTES)
#endif
int ___pskb_trim(struct sk_buff *skb, unsigned int len);
static inline void __skb_trim(struct sk_buff *skb, unsigned int len)
{
    if (unlikely(skb_is_nonlinear(skb))) {
        WARN_ON(1);
        return;
    }
    skb->len = len;
    skb_set_tail_pointer(skb, len);
}
void skb_trim(struct sk_buff *skb, unsigned int len);
static inline int __pskb_trim(struct sk_buff *skb, unsigned int len)
{
    if (skb->data_len)
        return ___pskb_trim(skb, len);
    __skb_trim(skb, len);
    return 0;
}
static inline int pskb_trim(struct sk_buff *skb, unsigned int len)
{
    return (len < skb->len) ? __pskb_trim(skb, len) : 0;
}
/**
 * pskb_trim_unique - remove end from a paged unique (not cloned) buffer
 * @skb: buffer to alter
 * @len: new length
 *
 * This is identical to pskb_trim except that the caller knows that
 * the skb is not cloned so we should never get an error due to out-
 * of-memory.
 */
static inline void pskb_trim_unique(struct sk_buff *skb, unsigned int len)
{
    int err = pskb_trim(skb, len);
    BUG_ON(err);
}
/**
 * skb_orphan - orphan a buffer
 * @skb: buffer to orphan
 *
 * If a buffer currently has an owner then we call the owner's
 * destructor function and make the @skb unowned. The buffer continues
 * to exist but is no longer charged to its former owner.
 */
static inline void skb_orphan(struct sk_buff *skb)
{
    if (skb->destructor) {
        skb->destructor(skb);
        skb->destructor = NULL;
        skb->sk = NULL;
    } else {
        BUG_ON(skb->sk);
    }
}
/**
 * skb_orphan_frags - orphan the frags contained in a buffer
 * @skb: buffer to orphan frags from
 * @gfp_mask: allocation mask for replacement pages
 *
 * For each frag in the SKB which needs a destructor (i.e. has an
 * owner) create a copy of that frag and release the original
 * page by calling the destructor.
 */
static inline int skb_orphan_frags(struct sk_buff *skb, gfp_t gfp_mask)
{
    if (likely(!(skb_shinfo(skb)->tx_flags & SKBTX_DEV_ZEROCOPY)))
        return 0;
    return skb_copy_ubufs(skb, gfp_mask);
}
/**
 * __skb_queue_purge - empty a list
 * @list: list to empty
 *
 * Delete all buffers on an &sk_buff list. Each buffer is removed from
 * the list and one reference dropped. This function does not take the
 * list lock and the caller must hold the relevant locks to use it.
 */
void skb_queue_purge(struct sk_buff_head *list);
static inline void __skb_queue_purge(struct sk_buff_head *list)
{
    struct sk_buff *skb;
    while ((skb = __skb_dequeue(list)) != NULL)
        kfree_skb(skb);
}
void *netdev_alloc_frag(unsigned int fragsz);
struct sk_buff *__netdev_alloc_skb(struct net_device *dev, unsigned int length,
        gfp_t gfp_mask);
/**
 * netdev_alloc_skb - allocate an skbuff for rx on a specific device
 * @dev: network device to receive on
 * @length: length to allocate
 *
 * Allocate a new &sk_buff and assign it a usage count of one. The
 * buffer has unspecified headroom built in. Users should allocate
 * the headroom they think they need without accounting for the
 * built in space. The built in space is used for optimisations.
 *
 * %NULL is returned if there is no free memory. Although this function
 * allocates memory it can be called from an interrupt.
 */
static inline struct sk_buff *netdev_alloc_skb(struct net_device *dev,
        unsigned int length)
{
    return __netdev_alloc_skb(dev, length, GFP_ATOMIC);
}
/* legacy helper around __netdev_alloc_skb() */
static inline struct sk_buff *__dev_alloc_skb(unsigned int length,
        gfp_t gfp_mask)
{
    return __netdev_alloc_skb(NULL, length, gfp_mask);
}
/* legacy helper around netdev_alloc_skb() */
static inline struct sk_buff *dev_alloc_skb(unsigned int length)
{
    return netdev_alloc_skb(NULL, length);
}
static inline struct sk_buff *__netdev_alloc_skb_ip_align(struct net_device *dev,
        unsigned int length, gfp_t gfp)
{
    struct sk_buff *skb = __netdev_alloc_skb(dev, length + NET_IP_ALIGN, gfp);
    if (NET_IP_ALIGN && skb)
        skb_reserve(skb, NET_IP_ALIGN);
    return skb;
}
static inline struct sk_buff *netdev_alloc_skb_ip_align(struct net_device *dev,
        unsigned int length)
{
    return __netdev_alloc_skb_ip_align(dev, length, GFP_ATOMIC);
}
static inline void skb_free_frag(void *addr)
{
    __free_page_frag(addr);
}
void *napi_alloc_frag(unsigned int fragsz);
struct sk_buff *__napi_alloc_skb(struct napi_struct *napi,
        unsigned int length, gfp_t gfp_mask);
static inline struct sk_buff *napi_alloc_skb(struct napi_struct *napi,
        unsigned int length)
{
    return __napi_alloc_skb(napi, length, GFP_ATOMIC);
}
/**
 * __dev_alloc_pages - allocate page for network Rx
 * @gfp_mask: allocation priority. Set __GFP_NOMEMALLOC if not for network Rx
 * @order: size of the allocation
 *
 * Allocate a new page.
 *
 * %NULL is returned if there is no free memory.
 */
static inline struct page *__dev_alloc_pages(gfp_t gfp_mask,
        unsigned int order)
{
    /* This piece of code contains several assumptions.
     * 1. This is for device Rx, therefor a cold page is preferred.
     * 2. The expectation is the user wants a compound page.
     * 3. If requesting a order 0 page it will not be compound
     * due to the check to see if order has a value in prep_new_page
     * 4. __GFP_MEMALLOC is ignored if __GFP_NOMEMALLOC is set due to
     * code in gfp_to_alloc_flags that should be enforcing this.
     */
    gfp_mask |= __GFP_COLD | __GFP_COMP | __GFP_MEMALLOC;
    return alloc_pages_node(NUMA_NO_NODE, gfp_mask, order);
}
static inline struct page *dev_alloc_pages(unsigned int order)
{
    return __dev_alloc_pages(GFP_ATOMIC, order);
}
/**
 * __dev_alloc_page - allocate a page for network Rx
 * @gfp_mask: allocation priority. Set __GFP_NOMEMALLOC if not for network Rx
 *
 * Allocate a new page.
 *
 * %NULL is returned if there is no free memory.
 */
static inline struct page *__dev_alloc_page(gfp_t gfp_mask)
{
    return __dev_alloc_pages(gfp_mask, 0);
}
static inline struct page *dev_alloc_page(void)
{
    return __dev_alloc_page(GFP_ATOMIC);
}
/**
 * skb_propagate_pfmemalloc - Propagate pfmemalloc if skb is allocated after RX page
 * @page: The page that was allocated from skb_alloc_page
 * @skb: The skb that may need pfmemalloc set
 */
static inline void skb_propagate_pfmemalloc(struct page *page,
        struct sk_buff *skb)
{
    if (page_is_pfmemalloc(page))
        skb->pfmemalloc = true;
}
/**
 * skb_frag_page - retrieve the page referred to by a paged fragment
 * @frag: the paged fragment
 *
 * Returns the &struct page associated with @frag.
 */
static inline struct page *skb_frag_page(const skb_frag_t *frag)
{
    return frag->page.p;
}
/**
 * __skb_frag_ref - take an addition reference on a paged fragment.
 * @frag: the paged fragment
 *
 * Takes an additional reference on the paged fragment @frag.
 */
static inline void __skb_frag_ref(skb_frag_t *frag)
{
    get_page(skb_frag_page(frag));
}
/**
 * skb_frag_ref - take an addition reference on a paged fragment of an skb.
 * @skb: the buffer
 * @f: the fragment offset.
 *
 * Takes an additional reference on the @f'th paged fragment of @skb.
 */
static inline void skb_frag_ref(struct sk_buff *skb, int f)
{
    __skb_frag_ref(&skb_shinfo(skb)->frags[f]);
}
/**
 * __skb_frag_unref - release a reference on a paged fragment.
 * @frag: the paged fragment
 *
 * Releases a reference on the paged fragment @frag.
 */
static inline void __skb_frag_unref(skb_frag_t *frag)
{
    put_page(skb_frag_page(frag));
}
/**
 * skb_frag_unref - release a reference on a paged fragment of an skb.
 * @skb: the buffer
 * @f: the fragment offset
 *
 * Releases a reference on the @f'th paged fragment of @skb.
 */
static inline void skb_frag_unref(struct sk_buff *skb, int f)
{
    __skb_frag_unref(&skb_shinfo(skb)->frags[f]);
}
/**
 * skb_frag_address - gets the address of the data contained in a paged fragment
 * @frag: the paged fragment buffer
 *
 * Returns the address of the data within @frag. The page must already
 * be mapped.
 */
static inline void *skb_frag_address(const skb_frag_t *frag)
{
    return page_address(skb_frag_page(frag)) + frag->page_offset;
}
/**
 * skb_frag_address_safe - gets the address of the data contained in a paged fragment
 * @frag: the paged fragment buffer
 *
 * Returns the address of the data within @frag. Checks that the page
 * is mapped and returns %NULL otherwise.
 */
static inline void *skb_frag_address_safe(const skb_frag_t *frag)
{
    void *ptr = page_address(skb_frag_page(frag));
    if (unlikely(!ptr))
        return NULL;
    return ptr + frag->page_offset;
}
/**
 * __skb_frag_set_page - sets the page contained in a paged fragment
 * @frag: the paged fragment
 * @page: the page to set
 *
 * Sets the fragment @frag to contain @page.
 */
static inline void __skb_frag_set_page(skb_frag_t *frag, struct page *page)
{
    frag->page.p = page;
}
/**
 * skb_frag_set_page - sets the page contained in a paged fragment of an skb
 * @skb: the buffer
 * @f: the fragment offset
 * @page: the page to set
 *
 * Sets the @f'th fragment of @skb to contain @page.
 */
static inline void skb_frag_set_page(struct sk_buff *skb, int f,
        struct page *page)
{
    __skb_frag_set_page(&skb_shinfo(skb)->frags[f], page);
}
bool skb_page_frag_refill(unsigned int sz, struct page_frag *pfrag, gfp_t prio);
/**
 * skb_frag_dma_map - maps a paged fragment via the DMA API
 * @dev: the device to map the fragment to
 * @frag: the paged fragment to map
 * @offset: the offset within the fragment (starting at the
 * fragment's own offset)
 * @size: the number of bytes to map
 * @dir: the direction of the mapping (%PCI_DMA_*)
 *
 * Maps the page associated with @frag to @device.
 */
static inline dma_addr_t skb_frag_dma_map(struct device *dev,
        const skb_frag_t *frag,
        size_t offset, size_t size,
        enum dma_data_direction dir)
{
    return dma_map_page(dev, skb_frag_page(frag),
            frag->page_offset + offset, size, dir);
}
static inline struct sk_buff *pskb_copy(struct sk_buff *skb,
        gfp_t gfp_mask)
{
    return __pskb_copy(skb, skb_headroom(skb), gfp_mask);
}
static inline struct sk_buff *pskb_copy_for_clone(struct sk_buff *skb,
        gfp_t gfp_mask)
{
    return __pskb_copy_fclone(skb, skb_headroom(skb), gfp_mask, true);
}
/**
 * skb_clone_writable - is the header of a clone writable
 * @skb: buffer to check
 * @len: length up to which to write
 *
 * Returns true if modifying the header part of the cloned buffer
 * does not requires the data to be copied.
 */
static inline int skb_clone_writable(const struct sk_buff *skb, unsigned int len)
{
    return !skb_header_cloned(skb) &&
        skb_headroom(skb) + len <= skb->hdr_len;
}
static inline int __skb_cow(struct sk_buff *skb, unsigned int headroom,
        int cloned)
{
    int delta = 0;
    if (headroom > skb_headroom(skb))
        delta = headroom - skb_headroom(skb);
    if (delta || cloned)
        return pskb_expand_head(skb, ALIGN(delta, NET_SKB_PAD), 0,
                GFP_ATOMIC);
    return 0;
}
/**
 * skb_cow - copy header of skb when it is required
 * @skb: buffer to cow
 * @headroom: needed headroom
 *
 * If the skb passed lacks sufficient headroom or its data part
 * is shared, data is reallocated. If reallocation fails, an error
 * is returned and original skb is not changed.
 *
 * The result is skb with writable area skb->head...skb->tail
 * and at least @headroom of space at head.
 */
static inline int skb_cow(struct sk_buff *skb, unsigned int headroom)
{
    return __skb_cow(skb, headroom, skb_cloned(skb));
}
/**
 * skb_cow_head - skb_cow but only making the head writable
 * @skb: buffer to cow
 * @headroom: needed headroom
 *
 * This function is identical to skb_cow except that we replace the
 * skb_cloned check by skb_header_cloned. It should be used when
 * you only need to push on some header and do not need to modify
 * the data.
 */
static inline int skb_cow_head(struct sk_buff *skb, unsigned int headroom)
{
    return __skb_cow(skb, headroom, skb_header_cloned(skb));
}
/**
 * skb_padto - pad an skbuff up to a minimal size
 * @skb: buffer to pad
 * @len: minimal length
 *
 * Pads up a buffer to ensure the trailing bytes exist and are
 * blanked. If the buffer already contains sufficient data it
 * is untouched. Otherwise it is extended. Returns zero on
 * success. The skb is freed on error.
 */
static inline int skb_padto(struct sk_buff *skb, unsigned int len)
{
    unsigned int size = skb->len;
    if (likely(size >= len))
        return 0;
    return skb_pad(skb, len - size);
}
/**
 * skb_put_padto - increase size and pad an skbuff up to a minimal size
 * @skb: buffer to pad
 * @len: minimal length
 *
 * Pads up a buffer to ensure the trailing bytes exist and are
 * blanked. If the buffer already contains sufficient data it
 * is untouched. Otherwise it is extended. Returns zero on
 * success. The skb is freed on error.
 */
static inline int skb_put_padto(struct sk_buff *skb, unsigned int len)
{
    unsigned int size = skb->len;
    if (unlikely(size < len)) {
        len -= size;
        if (skb_pad(skb, len))
            return -ENOMEM;
        __skb_put(skb, len);
    }
    return 0;
}
static inline int skb_add_data(struct sk_buff *skb,
        struct iov_iter *from, int copy)
{
    const int off = skb->len;
    if (skb->ip_summed == CHECKSUM_NONE) {
        __wsum csum = 0;
        if (csum_and_copy_from_iter(skb_put(skb, copy), copy,
                    &csum, from) == copy) {
            skb->csum = csum_block_add(skb->csum, csum, off);
            return 0;
        }
    } else if (copy_from_iter(skb_put(skb, copy), copy, from) == copy)
        return 0;
    __skb_trim(skb, off);
    return -EFAULT;
}
static inline bool skb_can_coalesce(struct sk_buff *skb, int i,
        const struct page *page, int off)
{
    if (i) {
        const struct skb_frag_struct *frag = &skb_shinfo(skb)->frags[i - 1];
        return page == skb_frag_page(frag) &&
            off == frag->page_offset + skb_frag_size(frag);
    }
    return false;
}
static inline int __skb_linearize(struct sk_buff *skb)
{
    return __pskb_pull_tail(skb, skb->data_len) ? 0 : -ENOMEM;
}
/**
 * skb_linearize - convert paged skb to linear one
 * @skb: buffer to linarize
 *
 * If there is no free memory -ENOMEM is returned, otherwise zero
 * is returned and the old skb data released.
 */
static inline int skb_linearize(struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) ? __skb_linearize(skb) : 0;
}
/**
 * skb_has_shared_frag - can any frag be overwritten
 * @skb: buffer to test
 *
 * Return true if the skb has at least one frag that might be modified
 * by an external entity (as in vmsplice()/sendfile())
 */
static inline bool skb_has_shared_frag(const struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) &&
        skb_shinfo(skb)->tx_flags & SKBTX_SHARED_FRAG;
}
/**
 * skb_linearize_cow - make sure skb is linear and writable
 * @skb: buffer to process
 *
 * If there is no free memory -ENOMEM is returned, otherwise zero
 * is returned and the old skb data released.
 */
static inline int skb_linearize_cow(struct sk_buff *skb)
{
    return skb_is_nonlinear(skb) || skb_cloned(skb) ?
        __skb_linearize(skb) : 0;
}
/**
 * skb_postpull_rcsum - update checksum for received skb after pull
 * @skb: buffer to update
 * @start: start of data before pull
 * @len: length of data pulled
 *
 * After doing a pull on a received packet, you need to call this to
 * update the CHECKSUM_COMPLETE checksum, or set ip_summed to
 * CHECKSUM_NONE so that it can be recomputed from scratch.
 */
static inline void skb_postpull_rcsum(struct sk_buff *skb,
        const void *start, unsigned int len)
{
    if (skb->ip_summed == CHECKSUM_COMPLETE)
        skb->csum = csum_sub(skb->csum, csum_partial(start, len, 0));
}
unsigned char *skb_pull_rcsum(struct sk_buff *skb, unsigned int len);
/**
 * pskb_trim_rcsum - trim received skb and update checksum
 * @skb: buffer to trim
 * @len: new length
 *
 * This is exactly the same as pskb_trim except that it ensures the
 * checksum of received packets are still valid after the operation.
 */
static inline int pskb_trim_rcsum(struct sk_buff *skb, unsigned int len)
{
    if (likely(len >= skb->len))
        return 0;
    if (skb->ip_summed == CHECKSUM_COMPLETE)
        skb->ip_summed = CHECKSUM_NONE;
    return __pskb_trim(skb, len);
}
#define skb_queue_walk(queue, skb) \
    for (skb = (queue)->next; \
            skb != (struct sk_buff *)(queue); \
            skb = skb->next)
#define skb_queue_walk_safe(queue, skb, tmp) \
    for (skb = (queue)->next, tmp = skb->next; \
            skb != (struct sk_buff *)(queue); \
            skb = tmp, tmp = skb->next)
#define skb_queue_walk_from(queue, skb) \
    for (; skb != (struct sk_buff *)(queue); \
            skb = skb->next)
#define skb_queue_walk_from_safe(queue, skb, tmp) \
    for (tmp = skb->next; \
            skb != (struct sk_buff *)(queue); \
            skb = tmp, tmp = skb->next)
#define skb_queue_reverse_walk(queue, skb) \
    for (skb = (queue)->prev; \
            skb != (struct sk_buff *)(queue); \
            skb = skb->prev)
#define skb_queue_reverse_walk_safe(queue, skb, tmp) \
    for (skb = (queue)->prev, tmp = skb->prev; \
            skb != (struct sk_buff *)(queue); \
            skb = tmp, tmp = skb->prev)
#define skb_queue_reverse_walk_from_safe(queue, skb, tmp) \
    for (tmp = skb->prev; \
            skb != (struct sk_buff *)(queue); \
            skb = tmp, tmp = skb->prev)
static inline bool skb_has_frag_list(const struct sk_buff *skb)
{
    return skb_shinfo(skb)->frag_list != NULL;
}
static inline void skb_frag_list_init(struct sk_buff *skb)
{
    skb_shinfo(skb)->frag_list = NULL;
}
static inline void skb_frag_add_head(struct sk_buff *skb, struct sk_buff *frag)
{
    frag->next = skb_shinfo(skb)->frag_list;
    skb_shinfo(skb)->frag_list = frag;
}
#define skb_walk_frags(skb, iter) \
    for (iter = skb_shinfo(skb)->frag_list; iter; iter = iter->next)
struct sk_buff *__skb_recv_datagram(struct sock *sk, unsigned flags,
        int *peeked, int *off, int *err);
struct sk_buff *skb_recv_datagram(struct sock *sk, unsigned flags, int noblock,
        int *err);
unsigned int datagram_poll(struct file *file, struct socket *sock,
        struct poll_table_struct *wait);
int skb_copy_datagram_iter(const struct sk_buff *from, int offset,
        struct iov_iter *to, int size);
static inline int skb_copy_datagram_msg(const struct sk_buff *from, int offset,
        struct msghdr *msg, int size)
{
    return skb_copy_datagram_iter(from, offset, &msg->msg_iter, size);
}
int skb_copy_and_csum_datagram_msg(struct sk_buff *skb, int hlen,
        struct msghdr *msg);
int skb_copy_datagram_from_iter(struct sk_buff *skb, int offset,
        struct iov_iter *from, int len);
int zerocopy_sg_from_iter(struct sk_buff *skb, struct iov_iter *frm);
void skb_free_datagram(struct sock *sk, struct sk_buff *skb);
void skb_free_datagram_locked(struct sock *sk, struct sk_buff *skb);
int skb_kill_datagram(struct sock *sk, struct sk_buff *skb, unsigned int flags);
int skb_copy_bits(const struct sk_buff *skb, int offset, void *to, int len);
int skb_store_bits(struct sk_buff *skb, int offset, const void *from, int len);
__wsum skb_copy_and_csum_bits(const struct sk_buff *skb, int offset, u8 *to,
        int len, __wsum csum);
ssize_t skb_socket_splice(struct sock *sk,
        struct pipe_inode_info *pipe,
        struct splice_pipe_desc *spd);
int skb_splice_bits(struct sk_buff *skb, struct sock *sk, unsigned int offset,
        struct pipe_inode_info *pipe, unsigned int len,
        unsigned int flags,
        ssize_t (*splice_cb)(struct sock *,
            struct pipe_inode_info *,
            struct splice_pipe_desc *));
void skb_copy_and_csum_dev(const struct sk_buff *skb, u8 *to);
unsigned int skb_zerocopy_headlen(const struct sk_buff *from);
int skb_zerocopy(struct sk_buff *to, struct sk_buff *from,
        int len, int hlen);
void skb_split(struct sk_buff *skb, struct sk_buff *skb1, const u32 len);
int skb_shift(struct sk_buff *tgt, struct sk_buff *skb, int shiftlen);
void skb_scrub_packet(struct sk_buff *skb, bool xnet);
unsigned int skb_gso_transport_seglen(const struct sk_buff *skb);
struct sk_buff *skb_segment(struct sk_buff *skb, netdev_features_t features);
struct sk_buff *skb_vlan_untag(struct sk_buff *skb);
int skb_ensure_writable(struct sk_buff *skb, int write_len);
int skb_vlan_pop(struct sk_buff *skb);
int skb_vlan_push(struct sk_buff *skb, __be16 vlan_proto, u16 vlan_tci);
static inline int memcpy_from_msg(void *data, struct msghdr *msg, int len)
{
    return copy_from_iter(data, len, &msg->msg_iter) == len ? 0 : -EFAULT;
}
static inline int memcpy_to_msg(struct msghdr *msg, void *data, int len)
{
    return copy_to_iter(data, len, &msg->msg_iter) == len ? 0 : -EFAULT;
}
struct skb_checksum_ops {
    __wsum (*update)(const void *mem, int len, __wsum wsum);
    __wsum (*combine)(__wsum csum, __wsum csum2, int offset, int len);
};
__wsum __skb_checksum(const struct sk_buff *skb, int offset, int len,
        __wsum csum, const struct skb_checksum_ops *ops);
__wsum skb_checksum(const struct sk_buff *skb, int offset, int len,
        __wsum csum);
    static inline void * __must_check
__skb_header_pointer(const struct sk_buff *skb, int offset,
        int len, void *data, int hlen, void *buffer)
{
    if (hlen - offset >= len)
        return data + offset;
    if (!skb ||
            skb_copy_bits(skb, offset, buffer, len) < 0)
        return NULL;
    return buffer;
}
    static inline void * __must_check
skb_header_pointer(const struct sk_buff *skb, int offset, int len, void *buffer)
{
    return __skb_header_pointer(skb, offset, len, skb->data,
            skb_headlen(skb), buffer);
}
/**
 * skb_needs_linearize - check if we need to linearize a given skb
 * depending on the given device features.
 * @skb: socket buffer to check
 * @features: net device features
 *
 * Returns true if either:
 * 1. skb has frag_list and the device doesn't support FRAGLIST, or
 * 2. skb is fragmented and the device does not support SG.
 */
static inline bool skb_needs_linearize(struct sk_buff *skb,
        netdev_features_t features)
{
    return skb_is_nonlinear(skb) &&
        ((skb_has_frag_list(skb) && !(features & NETIF_F_FRAGLIST)) ||
         (skb_shinfo(skb)->nr_frags && !(features & NETIF_F_SG)));
}
static inline void skb_copy_from_linear_data(const struct sk_buff *skb,
        void *to,
        const unsigned int len)
{
    memcpy(to, skb->data, len);
}
static inline void skb_copy_from_linear_data_offset(const struct sk_buff *skb,
        const int offset, void *to,
        const unsigned int len)
{
    memcpy(to, skb->data + offset, len);
}
static inline void skb_copy_to_linear_data(struct sk_buff *skb,
        const void *from,
        const unsigned int len)
{
    memcpy(skb->data, from, len);
}
static inline void skb_copy_to_linear_data_offset(struct sk_buff *skb,
        const int offset,
        const void *from,
        const unsigned int len)
{
    memcpy(skb->data + offset, from, len);
}
void skb_init(void);
static inline ktime_t skb_get_ktime(const struct sk_buff *skb)
{
    return skb->tstamp;
}
/**
 * skb_get_timestamp - get timestamp from a skb
 * @skb: skb to get stamp from
 * @stamp: pointer to struct timeval to store stamp in
 *
 * Timestamps are stored in the skb as offsets to a base timestamp.
 * This function converts the offset back to a struct timeval and stores
 * it in stamp.
 */
static inline void skb_get_timestamp(const struct sk_buff *skb,
        struct timeval *stamp)
{
    *stamp = ktime_to_timeval(skb->tstamp);
}
static inline void skb_get_timestampns(const struct sk_buff *skb,
        struct timespec *stamp)
{
    *stamp = ktime_to_timespec(skb->tstamp);
}
static inline void __net_timestamp(struct sk_buff *skb)
{
    skb->tstamp = ktime_get_real();
}
static inline ktime_t net_timedelta(ktime_t t)
{
    return ktime_sub(ktime_get_real(), t);
}
static inline ktime_t net_invalid_timestamp(void)
{
    return ktime_set(0, 0);
}
struct sk_buff *skb_clone_sk(struct sk_buff *skb);
#ifdef CONFIG_NETWORK_PHY_TIMESTAMPING
void skb_clone_tx_timestamp(struct sk_buff *skb);
bool skb_defer_rx_timestamp(struct sk_buff *skb);
#else /* CONFIG_NETWORK_PHY_TIMESTAMPING */
static inline void skb_clone_tx_timestamp(struct sk_buff *skb)
{
}
static inline bool skb_defer_rx_timestamp(struct sk_buff *skb)
{
    return false;
}
#endif /* !CONFIG_NETWORK_PHY_TIMESTAMPING */
/**
 * skb_complete_tx_timestamp() - deliver cloned skb with tx timestamps
 *
 * PHY drivers may accept clones of transmitted packets for
 * timestamping via their phy_driver.txtstamp method. These drivers
 * must call this function to return the skb back to the stack with a
 * timestamp.
 *
 * @skb: clone of the the original outgoing packet
 * @hwtstamps: hardware time stamps
 *
 */
void skb_complete_tx_timestamp(struct sk_buff *skb,
        struct skb_shared_hwtstamps *hwtstamps);
void __skb_tstamp_tx(struct sk_buff *orig_skb,
        struct skb_shared_hwtstamps *hwtstamps,
        struct sock *sk, int tstype);
/**
 * skb_tstamp_tx - queue clone of skb with send time stamps
 * @orig_skb: the original outgoing packet
 * @hwtstamps: hardware time stamps, may be NULL if not available
 *
 * If the skb has a socket associated, then this function clones the
 * skb (thus sharing the actual data and optional structures), stores
 * the optional hardware time stamping information (if non NULL) or
 * generates a software time stamp (otherwise), then queues the clone
 * to the error queue of the socket. Errors are silently ignored.
 */
void skb_tstamp_tx(struct sk_buff *orig_skb,
        struct skb_shared_hwtstamps *hwtstamps);
static inline void sw_tx_timestamp(struct sk_buff *skb)
{
    if (skb_shinfo(skb)->tx_flags & SKBTX_SW_TSTAMP &&
            !(skb_shinfo(skb)->tx_flags & SKBTX_IN_PROGRESS))
        skb_tstamp_tx(skb, NULL);
}
/**
 * skb_tx_timestamp() - Driver hook for transmit timestamping
 *
 * Ethernet MAC Drivers should call this function in their hard_xmit()
 * function immediately before giving the sk_buff to the MAC hardware.
 *
 * Specifically, one should make absolutely sure that this function is
 * called before TX completion of this packet can trigger. Otherwise
 * the packet could potentially already be freed.
 *
 * @skb: A socket buffer.
 */
static inline void skb_tx_timestamp(struct sk_buff *skb)
{
    skb_clone_tx_timestamp(skb);
    sw_tx_timestamp(skb);
}
/**
 * skb_complete_wifi_ack - deliver skb with wifi status
 *
 * @skb: the original outgoing packet
 * @acked: ack status
 *
 */
void skb_complete_wifi_ack(struct sk_buff *skb, bool acked);
__sum16 __skb_checksum_complete_head(struct sk_buff *skb, int len);
__sum16 __skb_checksum_complete(struct sk_buff *skb);
static inline int skb_csum_unnecessary(const struct sk_buff *skb)
{
    return ((skb->ip_summed == CHECKSUM_UNNECESSARY) ||
            skb->csum_valid ||
            (skb->ip_summed == CHECKSUM_PARTIAL &&
             skb_checksum_start_offset(skb) >= 0));
}
/**
 * skb_checksum_complete - Calculate checksum of an entire packet
 * @skb: packet to process
 *
 * This function calculates the checksum over the entire packet plus
 * the value of skb->csum. The latter can be used to supply the
 * checksum of a pseudo header as used by TCP/UDP. It returns the
 * checksum.
 *
 * For protocols that contain complete checksums such as ICMP/TCP/UDP,
 * this function can be used to verify that checksum on received
 * packets. In that case the function should return zero if the
 * checksum is correct. In particular, this function will return zero
 * if skb->ip_summed is CHECKSUM_UNNECESSARY which indicates that the
 * hardware has already verified the correctness of the checksum.
 */
static inline __sum16 skb_checksum_complete(struct sk_buff *skb)
{
    return skb_csum_unnecessary(skb) ?
        0 : __skb_checksum_complete(skb);
}
static inline void __skb_decr_checksum_unnecessary(struct sk_buff *skb)
{
    if (skb->ip_summed == CHECKSUM_UNNECESSARY) {
        if (skb->csum_level == 0)
            skb->ip_summed = CHECKSUM_NONE;
        else
            skb->csum_level--;
    }
}
static inline void __skb_incr_checksum_unnecessary(struct sk_buff *skb)
{
    if (skb->ip_summed == CHECKSUM_UNNECESSARY) {
        if (skb->csum_level < SKB_MAX_CSUM_LEVEL)
            skb->csum_level++;
    } else if (skb->ip_summed == CHECKSUM_NONE) {
        skb->ip_summed = CHECKSUM_UNNECESSARY;
        skb->csum_level = 0;
    }
}
static inline void __skb_mark_checksum_bad(struct sk_buff *skb)
{
    /* Mark current checksum as bad (typically called from GRO
     * path). In the case that ip_summed is CHECKSUM_NONE
     * this must be the first checksum encountered in the packet.
     * When ip_summed is CHECKSUM_UNNECESSARY, this is the first
     * checksum after the last one validated. For UDP, a zero
     * checksum can not be marked as bad.
     */
    if (skb->ip_summed == CHECKSUM_NONE ||
            skb->ip_summed == CHECKSUM_UNNECESSARY)
        skb->csum_bad = 1;
}
/* Check if we need to perform checksum complete validation.
 *
 * Returns true if checksum complete is needed, false otherwise
 * (either checksum is unnecessary or zero checksum is allowed).
 */
static inline bool __skb_checksum_validate_needed(struct sk_buff *skb,
        bool zero_okay,
        __sum16 check)
{
    if (skb_csum_unnecessary(skb) || (zero_okay && !check)) {
        skb->csum_valid = 1;
        __skb_decr_checksum_unnecessary(skb);
        return false;
    }
    return true;
}
/* For small packets <= CHECKSUM_BREAK peform checksum complete directly
 * in checksum_init.
 */
#define CHECKSUM_BREAK 76
/* Unset checksum-complete
 *
 * Unset checksum complete can be done when packet is being modified
 * (uncompressed for instance) and checksum-complete value is
 * invalidated.
 */
static inline void skb_checksum_complete_unset(struct sk_buff *skb)
{
    if (skb->ip_summed == CHECKSUM_COMPLETE)
        skb->ip_summed = CHECKSUM_NONE;
}
/* Validate (init) checksum based on checksum complete.
 *
 * Return values:
 * 0: checksum is validated or try to in skb_checksum_complete. In the latter
 * case the ip_summed will not be CHECKSUM_UNNECESSARY and the pseudo
 * checksum is stored in skb->csum for use in __skb_checksum_complete
 * non-zero: value of invalid checksum
 *
 */
static inline __sum16 __skb_checksum_validate_complete(struct sk_buff *skb,
        bool complete,
        __wsum psum)
{
    if (skb->ip_summed == CHECKSUM_COMPLETE) {
        if (!csum_fold(csum_add(psum, skb->csum))) {
            skb->csum_valid = 1;
            return 0;
        }
    } else if (skb->csum_bad) {
        /* ip_summed == CHECKSUM_NONE in this case */
        return (__force __sum16)1;
    }
    skb->csum = psum;
    if (complete || skb->len <= CHECKSUM_BREAK) {
        __sum16 csum;
        csum = __skb_checksum_complete(skb);
        skb->csum_valid = !csum;
        return csum;
    }
    return 0;
}
static inline __wsum null_compute_pseudo(struct sk_buff *skb, int proto)
{
    return 0;
}
/* Perform checksum validate (init). Note that this is a macro since we only
 * want to calculate the pseudo header which is an input function if necessary.
 * First we try to validate without any computation (checksum unnecessary) and
 * then calculate based on checksum complete calling the function to compute
 * pseudo header.
 *
 * Return values:
 * 0: checksum is validated or try to in skb_checksum_complete
 * non-zero: value of invalid checksum
 */
#define __skb_checksum_validate(skb, proto, complete, \
        zero_okay, check, compute_pseudo) \
({ \
 __sum16 __ret = 0; \
 skb->csum_valid = 0; \
 if (__skb_checksum_validate_needed(skb, zero_okay, check)) \
 __ret = __skb_checksum_validate_complete(skb, \
     complete, compute_pseudo(skb, proto)); \
 __ret; \
 })
#define skb_checksum_init(skb, proto, compute_pseudo) \
    __skb_checksum_validate(skb, proto, false, false, 0, compute_pseudo)
#define skb_checksum_init_zero_check(skb, proto, check, compute_pseudo) \
    __skb_checksum_validate(skb, proto, false, true, check, compute_pseudo)
#define skb_checksum_validate(skb, proto, compute_pseudo) \
    __skb_checksum_validate(skb, proto, true, false, 0, compute_pseudo)
#define skb_checksum_validate_zero_check(skb, proto, check, \
        compute_pseudo) \
__skb_checksum_validate(skb, proto, true, true, check, compute_pseudo)
#define skb_checksum_simple_validate(skb) \
    __skb_checksum_validate(skb, 0, true, false, 0, null_compute_pseudo)
static inline bool __skb_checksum_convert_check(struct sk_buff *skb)
{
    return (skb->ip_summed == CHECKSUM_NONE &&
            skb->csum_valid && !skb->csum_bad);
}
static inline void __skb_checksum_convert(struct sk_buff *skb,
        __sum16 check, __wsum pseudo)
{
    skb->csum = ~pseudo;
    skb->ip_summed = CHECKSUM_COMPLETE;
}
#define skb_checksum_try_convert(skb, proto, check, compute_pseudo) \
    do { \
        if (__skb_checksum_convert_check(skb)) \
        __skb_checksum_convert(skb, check, \
                compute_pseudo(skb, proto)); \
    } while (0)
static inline void skb_remcsum_adjust_partial(struct sk_buff *skb, void *ptr,
        u16 start, u16 offset)
{
    skb->ip_summed = CHECKSUM_PARTIAL;
    skb->csum_start = ((unsigned char *)ptr + start) - skb->head;
    skb->csum_offset = offset - start;
}
/* Update skbuf and packet to reflect the remote checksum offload operation.
 * When called, ptr indicates the starting point for skb->csum when
 * ip_summed is CHECKSUM_COMPLETE. If we need create checksum complete
 * here, skb_postpull_rcsum is done so skb->csum start is ptr.
 */
static inline void skb_remcsum_process(struct sk_buff *skb, void *ptr,
        int start, int offset, bool nopartial)
{
    __wsum delta;
    if (!nopartial) {
        skb_remcsum_adjust_partial(skb, ptr, start, offset);
        return;
    }
    if (unlikely(skb->ip_summed != CHECKSUM_COMPLETE)) {
        __skb_checksum_complete(skb);
        skb_postpull_rcsum(skb, skb->data, ptr - (void *)skb->data);
    }
    delta = remcsum_adjust(ptr, skb->csum, start, offset);
    /* Adjust skb->csum since we changed the packet */
    skb->csum = csum_add(skb->csum, delta);
}
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
void nf_conntrack_destroy(struct nf_conntrack *nfct);
static inline void nf_conntrack_put(struct nf_conntrack *nfct)
{
    if (nfct && atomic_dec_and_test(&nfct->use))
        nf_conntrack_destroy(nfct);
}
static inline void nf_conntrack_get(struct nf_conntrack *nfct)
{
    if (nfct)
        atomic_inc(&nfct->use);
}
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
static inline void nf_bridge_put(struct nf_bridge_info *nf_bridge)
{
    if (nf_bridge && atomic_dec_and_test(&nf_bridge->use))
        kfree(nf_bridge);
}
static inline void nf_bridge_get(struct nf_bridge_info *nf_bridge)
{
    if (nf_bridge)
        atomic_inc(&nf_bridge->use);
}
#endif /* CONFIG_BRIDGE_NETFILTER */
static inline void nf_reset(struct sk_buff *skb)
{
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
    nf_conntrack_put(skb->nfct);
    skb->nfct = NULL;
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
    nf_bridge_put(skb->nf_bridge);
    skb->nf_bridge = NULL;
#endif
}
static inline void nf_reset_trace(struct sk_buff *skb)
{
#if IS_ENABLED(CONFIG_NETFILTER_XT_TARGET_TRACE) || defined(CONFIG_NF_TABLES)
    skb->nf_trace = 0;
#endif
}
/* Note: This doesn't put any conntrack and bridge info in dst. */
static inline void __nf_copy(struct sk_buff *dst, const struct sk_buff *src,
        bool copy)
{
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
    dst->nfct = src->nfct;
    nf_conntrack_get(src->nfct);
    if (copy)
        dst->nfctinfo = src->nfctinfo;
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
    dst->nf_bridge = src->nf_bridge;
    nf_bridge_get(src->nf_bridge);
#endif
#if IS_ENABLED(CONFIG_NETFILTER_XT_TARGET_TRACE) || defined(CONFIG_NF_TABLES)
    if (copy)
        dst->nf_trace = src->nf_trace;
#endif
}
static inline void nf_copy(struct sk_buff *dst, const struct sk_buff *src)
{
#if defined(CONFIG_NF_CONNTRACK) || defined(CONFIG_NF_CONNTRACK_MODULE)
    nf_conntrack_put(dst->nfct);
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
    nf_bridge_put(dst->nf_bridge);
#endif
    __nf_copy(dst, src, true);
}
#ifdef CONFIG_NETWORK_SECMARK
static inline void skb_copy_secmark(struct sk_buff *to, const struct sk_buff *from)
{
    to->secmark = from->secmark;
}
static inline void skb_init_secmark(struct sk_buff *skb)
{
    skb->secmark = 0;
}
#else
static inline void skb_copy_secmark(struct sk_buff *to, const struct sk_buff *from)
{ }
static inline void skb_init_secmark(struct sk_buff *skb)
{ }
#endif
static inline bool skb_irq_freeable(const struct sk_buff *skb)
{
    return !skb->destructor &&
#if IS_ENABLED(CONFIG_XFRM)
        !skb->sp &&
#endif
#if IS_ENABLED(CONFIG_NF_CONNTRACK)
        !skb->nfct &&
#endif
        !skb->_skb_refdst &&
        !skb_has_frag_list(skb);
}
static inline void skb_set_queue_mapping(struct sk_buff *skb, u16 queue_mapping)
{
    skb->queue_mapping = queue_mapping;
}
static inline u16 skb_get_queue_mapping(const struct sk_buff *skb)
{
    return skb->queue_mapping;
}
static inline void skb_copy_queue_mapping(struct sk_buff *to, const struct sk_buff *from)
{
    to->queue_mapping = from->queue_mapping;
}
static inline void skb_record_rx_queue(struct sk_buff *skb, u16 rx_queue)
{
    skb->queue_mapping = rx_queue + 1;
}
static inline u16 skb_get_rx_queue(const struct sk_buff *skb)
{
    return skb->queue_mapping - 1;
}
static inline bool skb_rx_queue_recorded(const struct sk_buff *skb)
{
    return skb->queue_mapping != 0;
}
static inline struct sec_path *skb_sec_path(struct sk_buff *skb)
{
#ifdef CONFIG_XFRM
    return skb->sp;
#else
    return NULL;
#endif
}
/* Keeps track of mac header offset relative to skb->head.
 * It is useful for TSO of Tunneling protocol. e.g. GRE.
 * For non-tunnel skb it points to skb_mac_header() and for
 * tunnel skb it points to outer mac header.
 * Keeps track of level of encapsulation of network headers.
 */
struct skb_gso_cb {
    int	mac_offset;
    int	encap_level;
    __u16 csum_start;
};
#define SKB_GSO_CB(skb) ((struct skb_gso_cb *)(skb)->cb)
static inline int skb_tnl_header_len(const struct sk_buff *inner_skb)
{
    return (skb_mac_header(inner_skb) - inner_skb->head) -
        SKB_GSO_CB(inner_skb)->mac_offset;
}
static inline int gso_pskb_expand_head(struct sk_buff *skb, int extra)
{
    int new_headroom, headroom;
    int ret;
    headroom = skb_headroom(skb);
    ret = pskb_expand_head(skb, extra, 0, GFP_ATOMIC);
    if (ret)
        return ret;
    new_headroom = skb_headroom(skb);
    SKB_GSO_CB(skb)->mac_offset += (new_headroom - headroom);
    return 0;
}
/* Compute the checksum for a gso segment. First compute the checksum value
 * from the start of transport header to SKB_GSO_CB(skb)->csum_start, and
 * then add in skb->csum (checksum from csum_start to end of packet).
 * skb->csum and csum_start are then updated to reflect the checksum of the
 * resultant packet starting from the transport header-- the resultant checksum
 * is in the res argument (i.e. normally zero or ~ of checksum of a pseudo
 * header.
 */
static inline __sum16 gso_make_checksum(struct sk_buff *skb, __wsum res)
{
    int plen = SKB_GSO_CB(skb)->csum_start - skb_headroom(skb) -
        skb_transport_offset(skb);
    __wsum partial;
    partial = csum_partial(skb_transport_header(skb), plen, skb->csum);
    skb->csum = res;
    SKB_GSO_CB(skb)->csum_start -= plen;
    return csum_fold(partial);
}
static inline bool skb_is_gso(const struct sk_buff *skb)
{
    return skb_shinfo(skb)->gso_size;
}
/* Note: Should be called only if skb_is_gso(skb) is true */
static inline bool skb_is_gso_v6(const struct sk_buff *skb)
{
    return skb_shinfo(skb)->gso_type & SKB_GSO_TCPV6;
}
void __skb_warn_lro_forwarding(const struct sk_buff *skb);
static inline bool skb_warn_if_lro(const struct sk_buff *skb)
{
    /* LRO sets gso_size but not gso_type, whereas if GSO is really
     * wanted then gso_type will be set. */
    const struct skb_shared_info *shinfo = skb_shinfo(skb);
    if (skb_is_nonlinear(skb) && shinfo->gso_size != 0 &&
            unlikely(shinfo->gso_type == 0)) {
        __skb_warn_lro_forwarding(skb);
        return true;
    }
    return false;
}
static inline void skb_forward_csum(struct sk_buff *skb)
{
    /* Unfortunately we don't support this one. Any brave souls? */
    if (skb->ip_summed == CHECKSUM_COMPLETE)
        skb->ip_summed = CHECKSUM_NONE;
}
/**
 * skb_checksum_none_assert - make sure skb ip_summed is CHECKSUM_NONE
 * @skb: skb to check
 *
 * fresh skbs have their ip_summed set to CHECKSUM_NONE.
 * Instead of forcing ip_summed to CHECKSUM_NONE, we can
 * use this helper, to document places where we make this assertion.
 */
static inline void skb_checksum_none_assert(const struct sk_buff *skb)
{
#ifdef DEBUG
    BUG_ON(skb->ip_summed != CHECKSUM_NONE);
#endif
}
bool skb_partial_csum_set(struct sk_buff *skb, u16 start, u16 off);
int skb_checksum_setup(struct sk_buff *skb, bool recalculate);
struct sk_buff *skb_checksum_trimmed(struct sk_buff *skb,
        unsigned int transport_len,
        __sum16(*skb_chkf)(struct sk_buff *skb));
/**
 * skb_head_is_locked - Determine if the skb->head is locked down
 * @skb: skb to check
 *
 * The head on skbs build around a head frag can be removed if they are
 * not cloned. This function returns true if the skb head is locked down
 * due to either being allocated via kmalloc, or by being a clone with
 * multiple references to the head.
 */
static inline bool skb_head_is_locked(const struct sk_buff *skb)
{
    return !skb->head_frag || skb_cloned(skb);
}
/**
 * skb_gso_network_seglen - Return length of individual segments of a gso packet
 *
 * @skb: GSO skb
 *
 * skb_gso_network_seglen is used to determine the real size of the
 * individual segments, including Layer3 (IP, IPv6) and L4 headers (TCP/UDP).
 *
 * The MAC/L2 header is not accounted for.
 */
static inline unsigned int skb_gso_network_seglen(const struct sk_buff *skb)
{
    unsigned int hdr_len = skb_transport_header(skb) -
        skb_network_header(skb);
    return hdr_len + skb_gso_transport_seglen(skb);
}
#endif /* __KERNEL__ */
#endif /* _LINUX_SKBUFF_H */
```

```
/*linux/net/core/skbuff.c */

/*
 *      Routines having to do with the 'struct sk_buff' memory handlers.
 *
 *      Authors:        Alan Cox <alan@lxorguk.ukuu.org.uk>
 *                      Florian La Roche <rzsfl@rz.uni-sb.de>
 *
 *      Fixes:
 *              Alan Cox        :       Fixed the worst of the load
 *                                      balancer bugs.
 *              Dave Platt      :       Interrupt stacking fix.
 *      Richard Kooijman        :       Timestamp fixes.
 *              Alan Cox        :       Changed buffer format.
 *              Alan Cox        :       destructor hook for AF_UNIX etc.
 *              Linus Torvalds  :       Better skb_clone.
 *              Alan Cox        :       Added skb_copy.
 *              Alan Cox        :       Added all the changed routines Linus
 *                                      only put in the headers
 *              Ray VanTassle   :       Fixed --skb->lock in free
 *              Alan Cox        :       skb_copy copy arp field
 *              Andi Kleen      :       slabified it.
 *              Robert Olsson   :       Removed skb_head_pool
 *
 *      NOTE:
 *              The __skb_ routines should be called with interrupts
 *      disabled, or you better be *real* sure that the operation is atomic
 *      with respect to whatever list is being frobbed (e.g. via lock_sock()
 *      or via disabling bottom half handlers, etc).
 *
 *      This program is free software; you can redistribute it and/or
 *      modify it under the terms of the GNU General Public License
 *      as published by the Free Software Foundation; either version
 *      2 of the License, or (at your option) any later version.
 */

/*
 *      The functions in this file will not compile correctly with gcc 2.4.x
 */

#define pr_fmt(fmt) KBUILD_MODNAME ": " fmt

#include <linux/module.h>
#include <linux/types.h>
#include <linux/kernel.h>
#include <linux/kmemcheck.h>
#include <linux/mm.h>
#include <linux/interrupt.h>
#include <linux/in.h>
#include <linux/inet.h>
#include <linux/slab.h>
#include <linux/tcp.h>
#include <linux/udp.h>
#include <linux/netdevice.h>
#ifdef CONFIG_NET_CLS_ACT
#include <net/pkt_sched.h>
#endif
#include <linux/string.h>
#include <linux/skbuff.h>
#include <linux/splice.h>
#include <linux/cache.h>
#include <linux/rtnetlink.h>
#include <linux/init.h>
#include <linux/scatterlist.h>
#include <linux/errqueue.h>
#include <linux/prefetch.h>
#include <linux/if_vlan.h>

#include <net/protocol.h>
#include <net/dst.h>
#include <net/sock.h>
#include <net/checksum.h>
#include <net/ip6_checksum.h>
#include <net/xfrm.h>

#include <asm/uaccess.h>
#include <trace/events/skb.h>
#include <linux/highmem.h>
#include <linux/capability.h>
#include <linux/user_namespace.h>

struct kmem_cache *skbuff_head_cache __read_mostly;
static struct kmem_cache *skbuff_fclone_cache __read_mostly;

/**
 *      skb_panic - private function for out-of-line support
 *      @skb:   buffer
 *      @sz:    size
 *      @addr:  address
 *      @msg:   skb_over_panic or skb_under_panic
 *
 *      Out-of-line support for skb_put() and skb_push().
 *      Called via the wrapper skb_over_panic() or skb_under_panic().
 *      Keep out of line to prevent kernel bloat.
 *      __builtin_return_address is not used because it is not always reliable.
 */
static void skb_panic(struct sk_buff *skb, unsigned int sz, void *addr,
                      const char msg[])
{
        pr_emerg("%s: text:%p len:%d put:%d head:%p data:%p tail:%#lx end:%#lx dev:%s\n",
                 msg, addr, skb->len, sz, skb->head, skb->data,
                 (unsigned long)skb->tail, (unsigned long)skb->end,
                 skb->dev ? skb->dev->name : "<NULL>");
        BUG();
}

static void skb_over_panic(struct sk_buff *skb, unsigned int sz, void *addr)
{
        skb_panic(skb, sz, addr, __func__);
}

static void skb_under_panic(struct sk_buff *skb, unsigned int sz, void *addr)
{
        skb_panic(skb, sz, addr, __func__);
}

/*
 * kmalloc_reserve is a wrapper around kmalloc_node_track_caller that tells
 * the caller if emergency pfmemalloc reserves are being used. If it is and
 * the socket is later found to be SOCK_MEMALLOC then PFMEMALLOC reserves
 * may be used. Otherwise, the packet data may be discarded until enough
 * memory is free
 */
#define kmalloc_reserve(size, gfp, node, pfmemalloc) \
         __kmalloc_reserve(size, gfp, node, _RET_IP_, pfmemalloc)

static void *__kmalloc_reserve(size_t size, gfp_t flags, int node,
                               unsigned long ip, bool *pfmemalloc)
{
        void *obj;
        bool ret_pfmemalloc = false;

        /*
         * Try a regular allocation, when that fails and we're not entitled
         * to the reserves, fail.
         */
        obj = kmalloc_node_track_caller(size,
                                        flags | __GFP_NOMEMALLOC | __GFP_NOWARN,
                                        node);
        if (obj || !(gfp_pfmemalloc_allowed(flags)))
                goto out;

        /* Try again but now we are using pfmemalloc reserves */
        ret_pfmemalloc = true;
        obj = kmalloc_node_track_caller(size, flags, node);

out:
        if (pfmemalloc)
                *pfmemalloc = ret_pfmemalloc;

        return obj;
}

/*      Allocate a new skbuff. We do this ourselves so we can fill in a few
 *      'private' fields and also do memory statistics to find all the
 *      [BEEP] leaks.
 *
 */

struct sk_buff *__alloc_skb_head(gfp_t gfp_mask, int node)
{
        struct sk_buff *skb;

        /* Get the HEAD */
        skb = kmem_cache_alloc_node(skbuff_head_cache,
                                    gfp_mask & ~__GFP_DMA, node);
        if (!skb)
                goto out;

        /*
         * Only clear those fields we need to clear, not those that we will
         * actually initialise below. Hence, don't put any more fields after
         * the tail pointer in struct sk_buff!
         */
        memset(skb, 0, offsetof(struct sk_buff, tail));
        skb->head = NULL;
        skb->truesize = sizeof(struct sk_buff);
        atomic_set(&skb->users, 1);

        skb->mac_header = (typeof(skb->mac_header))~0U;
out:
        return skb;
}

/**
 *      __alloc_skb     -       allocate a network buffer
 *      @size: size to allocate
 *      @gfp_mask: allocation mask
 *      @flags: If SKB_ALLOC_FCLONE is set, allocate from fclone cache
 *              instead of head cache and allocate a cloned (child) skb.
 *              If SKB_ALLOC_RX is set, __GFP_MEMALLOC will be used for
 *              allocations in case the data is required for writeback
 *      @node: numa node to allocate memory on
 *
 *      Allocate a new &sk_buff. The returned buffer has no headroom and a
 *      tail room of at least size bytes. The object has a reference count
 *      of one. The return is the buffer. On a failure the return is %NULL.
 *
 *      Buffers may only be allocated from interrupts using a @gfp_mask of
 *      %GFP_ATOMIC.
 */
struct sk_buff *__alloc_skb(unsigned int size, gfp_t gfp_mask,
                            int flags, int node)
{
        struct kmem_cache *cache;
        struct skb_shared_info *shinfo;
        struct sk_buff *skb;
        u8 *data;
        bool pfmemalloc;

        cache = (flags & SKB_ALLOC_FCLONE)
                ? skbuff_fclone_cache : skbuff_head_cache;

        if (sk_memalloc_socks() && (flags & SKB_ALLOC_RX))
                gfp_mask |= __GFP_MEMALLOC;

        /* Get the HEAD */
        skb = kmem_cache_alloc_node(cache, gfp_mask & ~__GFP_DMA, node);
        if (!skb)
                goto out;
        prefetchw(skb);

        /* We do our best to align skb_shared_info on a separate cache
         * line. It usually works because kmalloc(X > SMP_CACHE_BYTES) gives
         * aligned memory blocks, unless SLUB/SLAB debug is enabled.
         * Both skb->head and skb_shared_info are cache line aligned.
         */
        size = SKB_DATA_ALIGN(size);
        size += SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
        data = kmalloc_reserve(size, gfp_mask, node, &pfmemalloc);
        if (!data)
                goto nodata;
        /* kmalloc(size) might give us more room than requested.
         * Put skb_shared_info exactly at the end of allocated zone,
         * to allow max possible filling before reallocation.
         */
        size = SKB_WITH_OVERHEAD(ksize(data));
        prefetchw(data + size);

        /*
         * Only clear those fields we need to clear, not those that we will
         * actually initialise below. Hence, don't put any more fields after
         * the tail pointer in struct sk_buff!
         */
        memset(skb, 0, offsetof(struct sk_buff, tail));
        /* Account for allocated memory : skb + skb->head */
        skb->truesize = SKB_TRUESIZE(size);
        skb->pfmemalloc = pfmemalloc;
        atomic_set(&skb->users, 1);
        skb->head = data;
        skb->data = data;
        skb_reset_tail_pointer(skb);
        skb->end = skb->tail + size;
        skb->mac_header = (typeof(skb->mac_header))~0U;
        skb->transport_header = (typeof(skb->transport_header))~0U;

        /* make sure we initialize shinfo sequentially */
        shinfo = skb_shinfo(skb);
        memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
        atomic_set(&shinfo->dataref, 1);
        kmemcheck_annotate_variable(shinfo->destructor_arg);

        if (flags & SKB_ALLOC_FCLONE) {
                struct sk_buff_fclones *fclones;

                fclones = container_of(skb, struct sk_buff_fclones, skb1);

                kmemcheck_annotate_bitfield(&fclones->skb2, flags1);
                skb->fclone = SKB_FCLONE_ORIG;
                atomic_set(&fclones->fclone_ref, 1);

                fclones->skb2.fclone = SKB_FCLONE_CLONE;
                fclones->skb2.pfmemalloc = pfmemalloc;
        }
out:
        return skb;
nodata:
        kmem_cache_free(cache, skb);
        skb = NULL;
        goto out;
}
EXPORT_SYMBOL(__alloc_skb);

/**
 * __build_skb - build a network buffer
 * @data: data buffer provided by caller
 * @frag_size: size of data, or 0 if head was kmalloced
 *
 * Allocate a new &sk_buff. Caller provides space holding head and
 * skb_shared_info. @data must have been allocated by kmalloc() only if
 * @frag_size is 0, otherwise data should come from the page allocator
 *  or vmalloc()
 * The return is the new skb buffer.
 * On a failure the return is %NULL, and @data is not freed.
 * Notes :
 *  Before IO, driver allocates only data buffer where NIC put incoming frame
 *  Driver should add room at head (NET_SKB_PAD) and
 *  MUST add room at tail (SKB_DATA_ALIGN(skb_shared_info))
 *  After IO, driver calls build_skb(), to allocate sk_buff and populate it
 *  before giving packet to stack.
 *  RX rings only contains data buffers, not full skbs.
 */
struct sk_buff *__build_skb(void *data, unsigned int frag_size)
{
        struct skb_shared_info *shinfo;
        struct sk_buff *skb;
        unsigned int size = frag_size ? : ksize(data);

        skb = kmem_cache_alloc(skbuff_head_cache, GFP_ATOMIC);
        if (!skb)
                return NULL;

        size -= SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

        memset(skb, 0, offsetof(struct sk_buff, tail));
        skb->truesize = SKB_TRUESIZE(size);
        atomic_set(&skb->users, 1);
        skb->head = data;
        skb->data = data;
        skb_reset_tail_pointer(skb);
        skb->end = skb->tail + size;
        skb->mac_header = (typeof(skb->mac_header))~0U;
        skb->transport_header = (typeof(skb->transport_header))~0U;

        /* make sure we initialize shinfo sequentially */
        shinfo = skb_shinfo(skb);
        memset(shinfo, 0, offsetof(struct skb_shared_info, dataref));
        atomic_set(&shinfo->dataref, 1);
        kmemcheck_annotate_variable(shinfo->destructor_arg);

        return skb;
}

/* build_skb() is wrapper over __build_skb(), that specifically
 * takes care of skb->head and skb->pfmemalloc
 * This means that if @frag_size is not zero, then @data must be backed
 * by a page fragment, not kmalloc() or vmalloc()
 */
struct sk_buff *build_skb(void *data, unsigned int frag_size)
{
        struct sk_buff *skb = __build_skb(data, frag_size);

        if (skb && frag_size) {
                skb->head_frag = 1;
                if (virt_to_head_page(data)->pfmemalloc)
                        skb->pfmemalloc = 1;
        }
        return skb;
}
EXPORT_SYMBOL(build_skb);

struct netdev_alloc_cache {
        struct page_frag        frag;
        /* we maintain a pagecount bias, so that we dont dirty cache line
         * containing page->_count every time we allocate a fragment.
         */
        unsigned int            pagecnt_bias;
};
static DEFINE_PER_CPU(struct netdev_alloc_cache, netdev_alloc_cache);
static DEFINE_PER_CPU(struct netdev_alloc_cache, napi_alloc_cache);

static struct page *__page_frag_refill(struct netdev_alloc_cache *nc,
                                       gfp_t gfp_mask)
{
        const unsigned int order = NETDEV_FRAG_PAGE_MAX_ORDER;
        struct page *page = NULL;
        gfp_t gfp = gfp_mask;

        if (order) {
                gfp_mask |= __GFP_COMP | __GFP_NOWARN | __GFP_NORETRY |
                            __GFP_NOMEMALLOC;
                page = alloc_pages_node(NUMA_NO_NODE, gfp_mask, order);
                nc->frag.size = PAGE_SIZE << (page ? order : 0);
        }

        if (unlikely(!page))
                page = alloc_pages_node(NUMA_NO_NODE, gfp, 0);

        nc->frag.page = page;

        return page;
}

static void *__alloc_page_frag(struct netdev_alloc_cache __percpu *cache,
                               unsigned int fragsz, gfp_t gfp_mask)
{
        struct netdev_alloc_cache *nc = this_cpu_ptr(cache);
        struct page *page = nc->frag.page;
        unsigned int size;
        int offset;

        if (unlikely(!page)) {
refill:
                page = __page_frag_refill(nc, gfp_mask);
                if (!page)
                        return NULL;

                /* if size can vary use frag.size else just use PAGE_SIZE */
                size = NETDEV_FRAG_PAGE_MAX_ORDER ? nc->frag.size : PAGE_SIZE;

                /* Even if we own the page, we do not use atomic_set().
                 * This would break get_page_unless_zero() users.
                 */
                atomic_add(size - 1, &page->_count);

                /* reset page count bias and offset to start of new frag */
                nc->pagecnt_bias = size;
                nc->frag.offset = size;
        }

        offset = nc->frag.offset - fragsz;
        if (unlikely(offset < 0)) {
                if (!atomic_sub_and_test(nc->pagecnt_bias, &page->_count))
                        goto refill;

                /* if size can vary use frag.size else just use PAGE_SIZE */
                size = NETDEV_FRAG_PAGE_MAX_ORDER ? nc->frag.size : PAGE_SIZE;

                /* OK, page count is 0, we can safely set it */
                atomic_set(&page->_count, size);

                /* reset page count bias and offset to start of new frag */
                nc->pagecnt_bias = size;
                offset = size - fragsz;
        }

        nc->pagecnt_bias--;
        nc->frag.offset = offset;

        return page_address(page) + offset;
}

static void *__netdev_alloc_frag(unsigned int fragsz, gfp_t gfp_mask)
{
        unsigned long flags;
        void *data;

        local_irq_save(flags);
        data = __alloc_page_frag(&netdev_alloc_cache, fragsz, gfp_mask);
        local_irq_restore(flags);
        return data;
}

/**
 * netdev_alloc_frag - allocate a page fragment
 * @fragsz: fragment size
 *
 * Allocates a frag from a page for receive buffer.
 * Uses GFP_ATOMIC allocations.
 */
void *netdev_alloc_frag(unsigned int fragsz)
{
        return __netdev_alloc_frag(fragsz, GFP_ATOMIC | __GFP_COLD);
}
EXPORT_SYMBOL(netdev_alloc_frag);

static void *__napi_alloc_frag(unsigned int fragsz, gfp_t gfp_mask)
{
        return __alloc_page_frag(&napi_alloc_cache, fragsz, gfp_mask);
}

void *napi_alloc_frag(unsigned int fragsz)
{
        return __napi_alloc_frag(fragsz, GFP_ATOMIC | __GFP_COLD);
}
EXPORT_SYMBOL(napi_alloc_frag);

/**
 *      __alloc_rx_skb - allocate an skbuff for rx
 *      @length: length to allocate
 *      @gfp_mask: get_free_pages mask, passed to alloc_skb
 *      @flags: If SKB_ALLOC_RX is set, __GFP_MEMALLOC will be used for
 *              allocations in case we have to fallback to __alloc_skb()
 *              If SKB_ALLOC_NAPI is set, page fragment will be allocated
 *              from napi_cache instead of netdev_cache.
 *
 *      Allocate a new &sk_buff and assign it a usage count of one. The
 *      buffer has unspecified headroom built in. Users should allocate
 *      the headroom they think they need without accounting for the
 *      built in space. The built in space is used for optimisations.
 *
 *      %NULL is returned if there is no free memory.
 */
static struct sk_buff *__alloc_rx_skb(unsigned int length, gfp_t gfp_mask,
                                      int flags)
{
        struct sk_buff *skb = NULL;
        unsigned int fragsz = SKB_DATA_ALIGN(length) +
                              SKB_DATA_ALIGN(sizeof(struct skb_shared_info));

        if (fragsz <= PAGE_SIZE && !(gfp_mask & (__GFP_WAIT | GFP_DMA))) {
                void *data;

                if (sk_memalloc_socks())
                        gfp_mask |= __GFP_MEMALLOC;

                data = (flags & SKB_ALLOC_NAPI) ?
                        __napi_alloc_frag(fragsz, gfp_mask) :
                        __netdev_alloc_frag(fragsz, gfp_mask);

                if (likely(data)) {
                        skb = build_skb(data, fragsz);
                        if (unlikely(!skb))
                                put_page(virt_to_head_page(data));
                }
        } else {
                skb = __alloc_skb(length, gfp_mask,
                                  SKB_ALLOC_RX, NUMA_NO_NODE);
        }
        return skb;
}

/**
 *      __netdev_alloc_skb - allocate an skbuff for rx on a specific device
 *      @dev: network device to receive on
 *      @length: length to allocate
 *      @gfp_mask: get_free_pages mask, passed to alloc_skb
 *
 *      Allocate a new &sk_buff and assign it a usage count of one. The
 *      buffer has NET_SKB_PAD headroom built in. Users should allocate
 *      the headroom they think they need without accounting for the
 *      built in space. The built in space is used for optimisations.
 *
 *      %NULL is returned if there is no free memory.
 */
struct sk_buff *__netdev_alloc_skb(struct net_device *dev,
                                   unsigned int length, gfp_t gfp_mask)
{
        struct sk_buff *skb;

        length += NET_SKB_PAD;
        skb = __alloc_rx_skb(length, gfp_mask, 0);

        if (likely(skb)) {
                skb_reserve(skb, NET_SKB_PAD);
                skb->dev = dev;
        }

        return skb;
}
EXPORT_SYMBOL(__netdev_alloc_skb);

/**
 *      __napi_alloc_skb - allocate skbuff for rx in a specific NAPI instance
 *      @napi: napi instance this buffer was allocated for
 *      @length: length to allocate
 *      @gfp_mask: get_free_pages mask, passed to alloc_skb and alloc_pages
 *
 *      Allocate a new sk_buff for use in NAPI receive.  This buffer will
 *      attempt to allocate the head from a special reserved region used
 *      only for NAPI Rx allocation.  By doing this we can save several
 *      CPU cycles by avoiding having to disable and re-enable IRQs.
 *
 *      %NULL is returned if there is no free memory.
 */
struct sk_buff *__napi_alloc_skb(struct napi_struct *napi,
                                 unsigned int length, gfp_t gfp_mask)
{
        struct sk_buff *skb;

        length += NET_SKB_PAD + NET_IP_ALIGN;
        skb = __alloc_rx_skb(length, gfp_mask, SKB_ALLOC_NAPI);

        if (likely(skb)) {
                skb_reserve(skb, NET_SKB_PAD + NET_IP_ALIGN);
                skb->dev = napi->dev;
        }

        return skb;
}
EXPORT_SYMBOL(__napi_alloc_skb);

void skb_add_rx_frag(struct sk_buff *skb, int i, struct page *page, int off,
                     int size, unsigned int truesize)
{
        skb_fill_page_desc(skb, i, page, off, size);
        skb->len += size;
        skb->data_len += size;
        skb->truesize += truesize;
}
EXPORT_SYMBOL(skb_add_rx_frag);

void skb_coalesce_rx_frag(struct sk_buff *skb, int i, int size,
                          unsigned int truesize)
{
        skb_frag_t *frag = &skb_shinfo(skb)->frags[i];

        skb_frag_size_add(frag, size);
        skb->len += size;
        skb->data_len += size;
        skb->truesize += truesize;
}
EXPORT_SYMBOL(skb_coalesce_rx_frag);

static void skb_drop_list(struct sk_buff **listp)
{
        kfree_skb_list(*listp);
        *listp = NULL;
}

static inline void skb_drop_fraglist(struct sk_buff *skb)
{
        skb_drop_list(&skb_shinfo(skb)->frag_list);
}

static void skb_clone_fraglist(struct sk_buff *skb)
{
        struct sk_buff *list;

        skb_walk_frags(skb, list)
                skb_get(list);
}

static void skb_free_head(struct sk_buff *skb)
{
        if (skb->head_frag)
                put_page(virt_to_head_page(skb->head));
        else
                kfree(skb->head);
}

static void skb_release_data(struct sk_buff *skb)
{
        struct skb_shared_info *shinfo = skb_shinfo(skb);
        int i;

        if (skb->cloned &&
            atomic_sub_return(skb->nohdr ? (1 << SKB_DATAREF_SHIFT) + 1 : 1,
                              &shinfo->dataref))
                return;

        for (i = 0; i < shinfo->nr_frags; i++)
                __skb_frag_unref(&shinfo->frags[i]);

        /*
         * If skb buf is from userspace, we need to notify the caller
         * the lower device DMA has done;
         */
        if (shinfo->tx_flags & SKBTX_DEV_ZEROCOPY) {
                struct ubuf_info *uarg;

                uarg = shinfo->destructor_arg;
                if (uarg->callback)
                        uarg->callback(uarg, true);
        }

        if (shinfo->frag_list)
                kfree_skb_list(shinfo->frag_list);

        skb_free_head(skb);
}

/*
 *      Free an skbuff by memory without cleaning the state.
 */
static void kfree_skbmem(struct sk_buff *skb)
{
        struct sk_buff_fclones *fclones;

        switch (skb->fclone) {
        case SKB_FCLONE_UNAVAILABLE:
                kmem_cache_free(skbuff_head_cache, skb);
                return;

        case SKB_FCLONE_ORIG:
                fclones = container_of(skb, struct sk_buff_fclones, skb1);

                /* We usually free the clone (TX completion) before original skb
                 * This test would have no chance to be true for the clone,
                 * while here, branch prediction will be good.
                 */
                if (atomic_read(&fclones->fclone_ref) == 1)
                        goto fastpath;
                break;

        default: /* SKB_FCLONE_CLONE */
                fclones = container_of(skb, struct sk_buff_fclones, skb2);
                break;
        }
        if (!atomic_dec_and_test(&fclones->fclone_ref))
                return;
fastpath:
        kmem_cache_free(skbuff_fclone_cache, fclones);
}

static void skb_release_head_state(struct sk_buff *skb)
{
        skb_dst_drop(skb);
#ifdef CONFIG_XFRM
        secpath_put(skb->sp);
#endif
        if (skb->destructor) {
                WARN_ON(in_irq());
                skb->destructor(skb);
        }
#if IS_ENABLED(CONFIG_NF_CONNTRACK)
        nf_conntrack_put(skb->nfct);
#endif
#if IS_ENABLED(CONFIG_BRIDGE_NETFILTER)
        nf_bridge_put(skb->nf_bridge);
#endif
}

/* Free everything but the sk_buff shell. */
static void skb_release_all(struct sk_buff *skb)
{
        skb_release_head_state(skb);
        if (likely(skb->head))
                skb_release_data(skb);
}

/**
 *      __kfree_skb - private function
 *      @skb: buffer
 *
 *      Free an sk_buff. Release anything attached to the buffer.
 *      Clean the state. This is an internal helper function. Users should
 *      always call kfree_skb
 */

void __kfree_skb(struct sk_buff *skb)
{
        skb_release_all(skb);
        kfree_skbmem(skb);
}
EXPORT_SYMBOL(__kfree_skb);

/**
 *      kfree_skb - free an sk_buff
 *      @skb: buffer to free
 *
 *      Drop a reference to the buffer and free it if the usage count has
 *      hit zero.
 */
void kfree_skb(struct sk_buff *skb)
{
        if (unlikely(!skb))
                return;
        if (likely(atomic_read(&skb->users) == 1))
                smp_rmb();
        else if (likely(!atomic_dec_and_test(&skb->users)))
                return;
        trace_kfree_skb(skb, __builtin_return_address(0));
        __kfree_skb(skb);
}
EXPORT_SYMBOL(kfree_skb);

void kfree_skb_list(struct sk_buff *segs)
{
        while (segs) {
                struct sk_buff *next = segs->next;

                kfree_skb(segs);
                segs = next;
        }
}
EXPORT_SYMBOL(kfree_skb_list);

/**
 *      skb_tx_error - report an sk_buff xmit error
 *      @skb: buffer that triggered an error
 *
 *      Report xmit error if a device callback is tracking this skb.
 *      skb must be freed afterwards.
 */
void skb_tx_error(struct sk_buff *skb)
{
        if (skb_shinfo(skb)->tx_flags & SKBTX_DEV_ZEROCOPY) {
                struct ubuf_info *uarg;

                uarg = skb_shinfo(skb)->destructor_arg;
                if (uarg->callback)
                        uarg->callback(uarg, false);
                skb_shinfo(skb)->tx_flags &= ~SKBTX_DEV_ZEROCOPY;
        }
}
EXPORT_SYMBOL(skb_tx_error);

/**
 *      consume_skb - free an skbuff
 *      @skb: buffer to free
 *
 *      Drop a ref to the buffer and free it if the usage count has hit zero
 *      Functions identically to kfree_skb, but kfree_skb assumes that the frame
 *      is being dropped after a failure and notes that
 */
void consume_skb(struct sk_buff *skb)
{
        if (unlikely(!skb))
                return;
        if (likely(atomic_read(&skb->users) == 1))
                smp_rmb();
        else if (likely(!atomic_dec_and_test(&skb->users)))
                return;
        trace_consume_skb(skb);
        __kfree_skb(skb);
}
EXPORT_SYMBOL(consume_skb);

/* Make sure a field is enclosed inside headers_start/headers_end section */
#define CHECK_SKB_FIELD(field) \
        BUILD_BUG_ON(offsetof(struct sk_buff, field) <          \
                     offsetof(struct sk_buff, headers_start));  \
        BUILD_BUG_ON(offsetof(struct sk_buff, field) >          \
                     offsetof(struct sk_buff, headers_end));    \

static void __copy_skb_header(struct sk_buff *new, const struct sk_buff *old)
{
        new->tstamp             = old->tstamp;
        /* We do not copy old->sk */
        new->dev                = old->dev;
        memcpy(new->cb, old->cb, sizeof(old->cb));
        skb_dst_copy(new, old);
#ifdef CONFIG_XFRM
        new->sp                 = secpath_get(old->sp);
#endif
        __nf_copy(new, old, false);

        /* Note : this field could be in headers_start/headers_end section
         * It is not yet because we do not want to have a 16 bit hole
         */
        new->queue_mapping = old->queue_mapping;

        memcpy(&new->headers_start, &old->headers_start,
               offsetof(struct sk_buff, headers_end) -
               offsetof(struct sk_buff, headers_start));
        CHECK_SKB_FIELD(protocol);
        CHECK_SKB_FIELD(csum);
        CHECK_SKB_FIELD(hash);
        CHECK_SKB_FIELD(priority);
        CHECK_SKB_FIELD(skb_iif);
        CHECK_SKB_FIELD(vlan_proto);
        CHECK_SKB_FIELD(vlan_tci);
        CHECK_SKB_FIELD(transport_header);
        CHECK_SKB_FIELD(network_header);
        CHECK_SKB_FIELD(mac_header);
        CHECK_SKB_FIELD(inner_protocol);
        CHECK_SKB_FIELD(inner_transport_header);
        CHECK_SKB_FIELD(inner_network_header);
        CHECK_SKB_FIELD(inner_mac_header);
        CHECK_SKB_FIELD(mark);
#ifdef CONFIG_NETWORK_SECMARK
        CHECK_SKB_FIELD(secmark);
#endif
#ifdef CONFIG_NET_RX_BUSY_POLL
        CHECK_SKB_FIELD(napi_id);
#endif
#ifdef CONFIG_XPS
        CHECK_SKB_FIELD(sender_cpu);
#endif
#ifdef CONFIG_NET_SCHED
        CHECK_SKB_FIELD(tc_index);
#ifdef CONFIG_NET_CLS_ACT
        CHECK_SKB_FIELD(tc_verd);
#endif
#endif

}

/*
 * You should not add any new code to this function.  Add it to
 * __copy_skb_header above instead.
 */
static struct sk_buff *__skb_clone(struct sk_buff *n, struct sk_buff *skb)
{
#define C(x) n->x = skb->x

        n->next = n->prev = NULL;
        n->sk = NULL;
        __copy_skb_header(n, skb);

        C(len);
        C(data_len);
        C(mac_len);
        n->hdr_len = skb->nohdr ? skb_headroom(skb) : skb->hdr_len;
        n->cloned = 1;
        n->nohdr = 0;
        n->destructor = NULL;
        C(tail);
        C(end);
        C(head);
        C(head_frag);
        C(data);
        C(truesize);
        atomic_set(&n->users, 1);

        atomic_inc(&(skb_shinfo(skb)->dataref));
        skb->cloned = 1;

        return n;
#undef C
}

/**
 *      skb_morph       -       morph one skb into another
 *      @dst: the skb to receive the contents
 *      @src: the skb to supply the contents
 *
 *      This is identical to skb_clone except that the target skb is
 *      supplied by the user.
 *
 *      The target skb is returned upon exit.
 */
struct sk_buff *skb_morph(struct sk_buff *dst, struct sk_buff *src)
{
        skb_release_all(dst);
        return __skb_clone(dst, src);
}
EXPORT_SYMBOL_GPL(skb_morph);

/**
 *      skb_copy_ubufs  -       copy userspace skb frags buffers to kernel
 *      @skb: the skb to modify
 *      @gfp_mask: allocation priority
 *
 *      This must be called on SKBTX_DEV_ZEROCOPY skb.
 *      It will copy all frags into kernel and drop the reference
 *      to userspace pages.
 *
 *      If this function is called from an interrupt gfp_mask() must be
 *      %GFP_ATOMIC.
 *
 *      Returns 0 on success or a negative error code on failure
 *      to allocate kernel memory to copy to.
 */
int skb_copy_ubufs(struct sk_buff *skb, gfp_t gfp_mask)
{
        int i;
        int num_frags = skb_shinfo(skb)->nr_frags;
        struct page *page, *head = NULL;
        struct ubuf_info *uarg = skb_shinfo(skb)->destructor_arg;

        for (i = 0; i < num_frags; i++) {
                u8 *vaddr;
                skb_frag_t *f = &skb_shinfo(skb)->frags[i];

                page = alloc_page(gfp_mask);
                if (!page) {
                        while (head) {
                                struct page *next = (struct page *)page_private(head);
                                put_page(head);
                                head = next;
                        }
                        return -ENOMEM;
                }
                vaddr = kmap_atomic(skb_frag_page(f));
                memcpy(page_address(page),
                       vaddr + f->page_offset, skb_frag_size(f));
                kunmap_atomic(vaddr);
                set_page_private(page, (unsigned long)head);
                head = page;
        }

        /* skb frags release userspace buffers */
        for (i = 0; i < num_frags; i++)
                skb_frag_unref(skb, i);

        uarg->callback(uarg, false);

        /* skb frags point to kernel buffers */
        for (i = num_frags - 1; i >= 0; i--) {
                __skb_fill_page_desc(skb, i, head, 0,
                                     skb_shinfo(skb)->frags[i].size);
                head = (struct page *)page_private(head);
        }

        skb_shinfo(skb)->tx_flags &= ~SKBTX_DEV_ZEROCOPY;
        return 0;
}
EXPORT_SYMBOL_GPL(skb_copy_ubufs);

/**
 *      skb_clone       -       duplicate an sk_buff
 *      @skb: buffer to clone
 *      @gfp_mask: allocation priority
 *
 *      Duplicate an &sk_buff. The new one is not owned by a socket. Both
 *      copies share the same packet data but not structure. The new
 *      buffer has a reference count of 1. If the allocation fails the
 *      function returns %NULL otherwise the new buffer is returned.
 *
 *      If this function is called from an interrupt gfp_mask() must be
 *      %GFP_ATOMIC.
 */

struct sk_buff *skb_clone(struct sk_buff *skb, gfp_t gfp_mask)
{
        struct sk_buff_fclones *fclones = container_of(skb,
                                                       struct sk_buff_fclones,
                                                       skb1);
        struct sk_buff *n;

        if (skb_orphan_frags(skb, gfp_mask))
                return NULL;

        if (skb->fclone == SKB_FCLONE_ORIG &&
            atomic_read(&fclones->fclone_ref) == 1) {
                n = &fclones->skb2;
                atomic_set(&fclones->fclone_ref, 2);
        } else {
                if (skb_pfmemalloc(skb))
                         gfp_mask |= __GFP_MEMALLOC;
 
                 n = kmem_cache_alloc(skbuff_head_cache, gfp_mask);
                 if (!n)
                         return NULL;
 
                 kmemcheck_annotate_bitfield(n, flags1);
                 n->fclone = SKB_FCLONE_UNAVAILABLE;
         }
 
         return __skb_clone(n, skb);
 }
 EXPORT_SYMBOL(skb_clone);
 
 static void skb_headers_offset_update(struct sk_buff *skb, int off)
 {
         /* Only adjust this if it actually is csum_start rather than csum */
         if (skb->ip_summed == CHECKSUM_PARTIAL)
                 skb->csum_start += off;
         /* {transport,network,mac}_header and tail are relative to skb->head */
         skb->transport_header += off;
         skb->network_header   += off;
         if (skb_mac_header_was_set(skb))
                 skb->mac_header += off;
         skb->inner_transport_header += off;
         skb->inner_network_header += off;
         skb->inner_mac_header += off;
 }
 
 static void copy_skb_header(struct sk_buff *new, const struct sk_buff *old)
 {
         __copy_skb_header(new, old);
 
         skb_shinfo(new)->gso_size = skb_shinfo(old)->gso_size;
         skb_shinfo(new)->gso_segs = skb_shinfo(old)->gso_segs;
         skb_shinfo(new)->gso_type = skb_shinfo(old)->gso_type;
 }
 
 static inline int skb_alloc_rx_flag(const struct sk_buff *skb)
 {
         if (skb_pfmemalloc(skb))
                 return SKB_ALLOC_RX;
         return 0;
 }
 
 /**
  *      skb_copy        -       create private copy of an sk_buff
  *      @skb: buffer to copy
  *      @gfp_mask: allocation priority
  *
  *      Make a copy of both an &sk_buff and its data. This is used when the
  *      caller wishes to modify the data and needs a private copy of the
  *      data to alter. Returns %NULL on failure or the pointer to the buffer
  *      on success. The returned buffer has a reference count of 1.
  *
  *      As by-product this function converts non-linear &sk_buff to linear
  *      one, so that &sk_buff becomes completely private and caller is allowed
  *      to modify all the data of returned buffer. This means that this
  *      function is not recommended for use in circumstances when only
  *      header is going to be modified. Use pskb_copy() instead.
  */
 
 struct sk_buff *skb_copy(const struct sk_buff *skb, gfp_t gfp_mask)
 {
         int headerlen = skb_headroom(skb);
         unsigned int size = skb_end_offset(skb) + skb->data_len;
         struct sk_buff *n = __alloc_skb(size, gfp_mask,
                                         skb_alloc_rx_flag(skb), NUMA_NO_NODE);
 
         if (!n)
                 return NULL;
 
         /* Set the data pointer */
         skb_reserve(n, headerlen);
         /* Set the tail pointer and length */
         skb_put(n, skb->len);
 
         if (skb_copy_bits(skb, -headerlen, n->head, headerlen + skb->len))
                 BUG();
 
         copy_skb_header(n, skb);
         return n;
 }
 EXPORT_SYMBOL(skb_copy);
 
 /**
  *      __pskb_copy_fclone      -  create copy of an sk_buff with private head.
  *      @skb: buffer to copy
  *      @headroom: headroom of new skb
  *      @gfp_mask: allocation priority
  *      @fclone: if true allocate the copy of the skb from the fclone
  *      cache instead of the head cache; it is recommended to set this
  *      to true for the cases where the copy will likely be cloned
  *
  *      Make a copy of both an &sk_buff and part of its data, located
  *      in header. Fragmented data remain shared. This is used when
  *      the caller wishes to modify only header of &sk_buff and needs
  *      private copy of the header to alter. Returns %NULL on failure
  *      or the pointer to the buffer on success.
  *      The returned buffer has a reference count of 1.
  */
 
 struct sk_buff *__pskb_copy_fclone(struct sk_buff *skb, int headroom,
                                    gfp_t gfp_mask, bool fclone)
 {
         unsigned int size = skb_headlen(skb) + headroom;
         int flags = skb_alloc_rx_flag(skb) | (fclone ? SKB_ALLOC_FCLONE : 0);
         struct sk_buff *n = __alloc_skb(size, gfp_mask, flags, NUMA_NO_NODE);
 
         if (!n)
                 goto out;
 
         /* Set the data pointer */
         skb_reserve(n, headroom);
         /* Set the tail pointer and length */
         skb_put(n, skb_headlen(skb));
         /* Copy the bytes */
         skb_copy_from_linear_data(skb, n->data, n->len);
 
         n->truesize += skb->data_len;
         n->data_len  = skb->data_len;
         n->len       = skb->len;
 
         if (skb_shinfo(skb)->nr_frags) {
                 int i;
 
                 if (skb_orphan_frags(skb, gfp_mask)) {
                         kfree_skb(n);
                         n = NULL;
                         goto out;
                 }
                 for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                         skb_shinfo(n)->frags[i] = skb_shinfo(skb)->frags[i];
                         skb_frag_ref(skb, i);
                 }
                 skb_shinfo(n)->nr_frags = i;
         }
 
         if (skb_has_frag_list(skb)) {
                 skb_shinfo(n)->frag_list = skb_shinfo(skb)->frag_list;
                 skb_clone_fraglist(n);
         }
 
         copy_skb_header(n, skb);
 out:
         return n;
 }
 EXPORT_SYMBOL(__pskb_copy_fclone);
 
 /**
  *      pskb_expand_head - reallocate header of &sk_buff
  *      @skb: buffer to reallocate
  *      @nhead: room to add at head
  *      @ntail: room to add at tail
  *      @gfp_mask: allocation priority
  *
  *      Expands (or creates identical copy, if @nhead and @ntail are zero)
  *      header of @skb. &sk_buff itself is not changed. &sk_buff MUST have
  *      reference count of 1. Returns zero in the case of success or error,
  *      if expansion failed. In the last case, &sk_buff is not changed.
  *
  *      All the pointers pointing into skb header may change and must be
  *      reloaded after call to this function.
  */
 
 int pskb_expand_head(struct sk_buff *skb, int nhead, int ntail,
                      gfp_t gfp_mask)
 {
         int i;
         u8 *data;
         int size = nhead + skb_end_offset(skb) + ntail;
         long off;
 
         BUG_ON(nhead < 0);
 
         if (skb_shared(skb))
                 BUG();
 
         size = SKB_DATA_ALIGN(size);
 
         if (skb_pfmemalloc(skb))
                 gfp_mask |= __GFP_MEMALLOC;
         data = kmalloc_reserve(size + SKB_DATA_ALIGN(sizeof(struct skb_shared_info)),
                                gfp_mask, NUMA_NO_NODE, NULL);
         if (!data)
                 goto nodata;
         size = SKB_WITH_OVERHEAD(ksize(data));
 
         /* Copy only real data... and, alas, header. This should be
          * optimized for the cases when header is void.
          */
         memcpy(data + nhead, skb->head, skb_tail_pointer(skb) - skb->head);
 
         memcpy((struct skb_shared_info *)(data + size),
                skb_shinfo(skb),
                offsetof(struct skb_shared_info, frags[skb_shinfo(skb)->nr_frags]));
 
         /*
          * if shinfo is shared we must drop the old head gracefully, but if it
          * is not we can just drop the old head and let the existing refcount
          * be since all we did is relocate the values
          */
         if (skb_cloned(skb)) {
                 /* copy this zero copy skb frags */
                 if (skb_orphan_frags(skb, gfp_mask))
                         goto nofrags;
                 for (i = 0; i < skb_shinfo(skb)->nr_frags; i++)
                         skb_frag_ref(skb, i);
 
                 if (skb_has_frag_list(skb))
                         skb_clone_fraglist(skb);
 
                 skb_release_data(skb);
         } else {
                 skb_free_head(skb);
         }
         off = (data + nhead) - skb->head;
 
         skb->head     = data;
         skb->head_frag = 0;
         skb->data    += off;
 #ifdef NET_SKBUFF_DATA_USES_OFFSET
         skb->end      = size;
         off           = nhead;
 #else
         skb->end      = skb->head + size;
 #endif
         skb->tail             += off;
         skb_headers_offset_update(skb, nhead);
         skb->cloned   = 0;
         skb->hdr_len  = 0;
         skb->nohdr    = 0;
         atomic_set(&skb_shinfo(skb)->dataref, 1);
         return 0;
 
 nofrags:
         kfree(data);
 nodata:
         return -ENOMEM;
 }
 EXPORT_SYMBOL(pskb_expand_head);
 
 /* Make private copy of skb with writable head and some headroom */
 
 struct sk_buff *skb_realloc_headroom(struct sk_buff *skb, unsigned int headroom)
 {
         struct sk_buff *skb2;
         int delta = headroom - skb_headroom(skb);
 
         if (delta <= 0)
                 skb2 = pskb_copy(skb, GFP_ATOMIC);
         else {
                 skb2 = skb_clone(skb, GFP_ATOMIC);
                 if (skb2 && pskb_expand_head(skb2, SKB_DATA_ALIGN(delta), 0,
                                              GFP_ATOMIC)) {
                         kfree_skb(skb2);
                         skb2 = NULL;
                 }
         }
         return skb2;
 }
 EXPORT_SYMBOL(skb_realloc_headroom);
 
 /**
  *      skb_copy_expand -       copy and expand sk_buff
  *      @skb: buffer to copy
  *      @newheadroom: new free bytes at head
  *      @newtailroom: new free bytes at tail
  *      @gfp_mask: allocation priority
  *
  *      Make a copy of both an &sk_buff and its data and while doing so
  *      allocate additional space.
  *
  *      This is used when the caller wishes to modify the data and needs a
  *      private copy of the data to alter as well as more space for new fields.
  *      Returns %NULL on failure or the pointer to the buffer
  *      on success. The returned buffer has a reference count of 1.
  *
  *      You must pass %GFP_ATOMIC as the allocation priority if this function
  *      is called from an interrupt.
  */
 struct sk_buff *skb_copy_expand(const struct sk_buff *skb,
                                 int newheadroom, int newtailroom,
                                 gfp_t gfp_mask)
 {
         /*
          *      Allocate the copy buffer
          */
         struct sk_buff *n = __alloc_skb(newheadroom + skb->len + newtailroom,
                                         gfp_mask, skb_alloc_rx_flag(skb),
                                         NUMA_NO_NODE);
         int oldheadroom = skb_headroom(skb);
         int head_copy_len, head_copy_off;
 
         if (!n)
                 return NULL;
 
         skb_reserve(n, newheadroom);
 
         /* Set the tail pointer and length */
         skb_put(n, skb->len);
 
         head_copy_len = oldheadroom;
         head_copy_off = 0;
         if (newheadroom <= head_copy_len)
                 head_copy_len = newheadroom;
         else
                 head_copy_off = newheadroom - head_copy_len;
 
         /* Copy the linear header and data. */
         if (skb_copy_bits(skb, -head_copy_len, n->head + head_copy_off,
                           skb->len + head_copy_len))
                 BUG();
 
         copy_skb_header(n, skb);
 
         skb_headers_offset_update(n, newheadroom - oldheadroom);
 
         return n;
 }
 EXPORT_SYMBOL(skb_copy_expand);
 
 /**
  *      skb_pad                 -       zero pad the tail of an skb
  *      @skb: buffer to pad
  *      @pad: space to pad
  *
  *      Ensure that a buffer is followed by a padding area that is zero
  *      filled. Used by network drivers which may DMA or transfer data
  *      beyond the buffer end onto the wire.
  *
  *      May return error in out of memory cases. The skb is freed on error.
  */
 
 int skb_pad(struct sk_buff *skb, int pad)
 {
         int err;
         int ntail;
 
         /* If the skbuff is non linear tailroom is always zero.. */
         if (!skb_cloned(skb) && skb_tailroom(skb) >= pad) {
                 memset(skb->data+skb->len, 0, pad);
                 return 0;
         }
 
         ntail = skb->data_len + pad - (skb->end - skb->tail);
         if (likely(skb_cloned(skb) || ntail > 0)) {
                 err = pskb_expand_head(skb, 0, ntail, GFP_ATOMIC);
                 if (unlikely(err))
                         goto free_skb;
         }
 
         /* FIXME: The use of this function with non-linear skb's really needs
          * to be audited.
          */
         err = skb_linearize(skb);
         if (unlikely(err))
                 goto free_skb;
 
         memset(skb->data + skb->len, 0, pad);
         return 0;
 
 free_skb:
         kfree_skb(skb);
         return err;
 }
 EXPORT_SYMBOL(skb_pad);
 
 /**
  *      pskb_put - add data to the tail of a potentially fragmented buffer
  *      @skb: start of the buffer to use
  *      @tail: tail fragment of the buffer to use
  *      @len: amount of data to add
  *
  *      This function extends the used data area of the potentially
  *      fragmented buffer. @tail must be the last fragment of @skb -- or
  *      @skb itself. If this would exceed the total buffer size the kernel
  *      will panic. A pointer to the first byte of the extra data is
  *      returned.
  */
 
 unsigned char *pskb_put(struct sk_buff *skb, struct sk_buff *tail, int len)
 {
         if (tail != skb) {
                 skb->data_len += len;
                 skb->len += len;
         }
         return skb_put(tail, len);
 }
 EXPORT_SYMBOL_GPL(pskb_put);
 
 /**
  *      skb_put - add data to a buffer
  *      @skb: buffer to use
  *      @len: amount of data to add
  *
  *      This function extends the used data area of the buffer. If this would
  *      exceed the total buffer size the kernel will panic. A pointer to the
  *      first byte of the extra data is returned.
  */
 unsigned char *skb_put(struct sk_buff *skb, unsigned int len)
 {
         unsigned char *tmp = skb_tail_pointer(skb);
         SKB_LINEAR_ASSERT(skb);
         skb->tail += len;
         skb->len  += len;
         if (unlikely(skb->tail > skb->end))
                 skb_over_panic(skb, len, __builtin_return_address(0));
         return tmp;
 }
 EXPORT_SYMBOL(skb_put);
 
 /**
  *      skb_push - add data to the start of a buffer
  *      @skb: buffer to use
  *      @len: amount of data to add
  *
  *      This function extends the used data area of the buffer at the buffer
  *      start. If this would exceed the total buffer headroom the kernel will
  *      panic. A pointer to the first byte of the extra data is returned.
  */
 unsigned char *skb_push(struct sk_buff *skb, unsigned int len)
 {
         skb->data -= len;
         skb->len  += len;
         if (unlikely(skb->data<skb->head))
                 skb_under_panic(skb, len, __builtin_return_address(0));
         return skb->data;
 }
 EXPORT_SYMBOL(skb_push);
 
 /**
  *      skb_pull - remove data from the start of a buffer
  *      @skb: buffer to use
  *      @len: amount of data to remove
  *
  *      This function removes data from the start of a buffer, returning
  *      the memory to the headroom. A pointer to the next data in the buffer
  *      is returned. Once the data has been pulled future pushes will overwrite
  *      the old data.
  */
 unsigned char *skb_pull(struct sk_buff *skb, unsigned int len)
 {
         return skb_pull_inline(skb, len);
 }
 EXPORT_SYMBOL(skb_pull);
 
 /**
  *      skb_trim - remove end from a buffer
  *      @skb: buffer to alter
  *      @len: new length
  *
  *      Cut the length of a buffer down by removing data from the tail. If
  *      the buffer is already under the length specified it is not modified.
  *      The skb must be linear.
  */
 void skb_trim(struct sk_buff *skb, unsigned int len)
 {
         if (skb->len > len)
                 __skb_trim(skb, len);
 }
 EXPORT_SYMBOL(skb_trim);
 
 /* Trims skb to length len. It can change skb pointers.
  */
 
 int ___pskb_trim(struct sk_buff *skb, unsigned int len)
 {
         struct sk_buff **fragp;
         struct sk_buff *frag;
         int offset = skb_headlen(skb);
         int nfrags = skb_shinfo(skb)->nr_frags;
         int i;
         int err;
 
         if (skb_cloned(skb) &&
             unlikely((err = pskb_expand_head(skb, 0, 0, GFP_ATOMIC))))
                 return err;
 
         i = 0;
         if (offset >= len)
                 goto drop_pages;
 
         for (; i < nfrags; i++) {
                 int end = offset + skb_frag_size(&skb_shinfo(skb)->frags[i]);
 
                 if (end < len) {
                         offset = end;
                         continue;
                 }
 
                 skb_frag_size_set(&skb_shinfo(skb)->frags[i++], len - offset);
 
 drop_pages:
                 skb_shinfo(skb)->nr_frags = i;
 
                 for (; i < nfrags; i++)
                         skb_frag_unref(skb, i);
 
                 if (skb_has_frag_list(skb))
                         skb_drop_fraglist(skb);
                 goto done;
         }
 
         for (fragp = &skb_shinfo(skb)->frag_list; (frag = *fragp);
              fragp = &frag->next) {
                 int end = offset + frag->len;
 
                 if (skb_shared(frag)) {
                         struct sk_buff *nfrag;
 
                         nfrag = skb_clone(frag, GFP_ATOMIC);
                         if (unlikely(!nfrag))
                                 return -ENOMEM;
 
                         nfrag->next = frag->next;
                         consume_skb(frag);
                         frag = nfrag;
                         *fragp = frag;
                 }
 
                 if (end < len) {
                         offset = end;
                         continue;
                 }
 
                 if (end > len &&
                     unlikely((err = pskb_trim(frag, len - offset))))
                         return err;
 
                 if (frag->next)
                         skb_drop_list(&frag->next);
                 break;
         }
 
 done:
         if (len > skb_headlen(skb)) {
                 skb->data_len -= skb->len - len;
                 skb->len       = len;
         } else {
                 skb->len       = len;
                 skb->data_len  = 0;
                 skb_set_tail_pointer(skb, len);
         }
 
         return 0;
 }
 EXPORT_SYMBOL(___pskb_trim);
 
 /**
  *      __pskb_pull_tail - advance tail of skb header
  *      @skb: buffer to reallocate
  *      @delta: number of bytes to advance tail
  *
  *      The function makes a sense only on a fragmented &sk_buff,
  *      it expands header moving its tail forward and copying necessary
  *      data from fragmented part.
  *
  *      &sk_buff MUST have reference count of 1.
  *
  *      Returns %NULL (and &sk_buff does not change) if pull failed
  *      or value of new tail of skb in the case of success.
  *
  *      All the pointers pointing into skb header may change and must be
  *      reloaded after call to this function.
  */
 
 /* Moves tail of skb head forward, copying data from fragmented part,
  * when it is necessary.
  * 1. It may fail due to malloc failure.
  * 2. It may change skb pointers.
  *
  * It is pretty complicated. Luckily, it is called only in exceptional cases.
  */
 unsigned char *__pskb_pull_tail(struct sk_buff *skb, int delta)
 {
         /* If skb has not enough free space at tail, get new one
          * plus 128 bytes for future expansions. If we have enough
          * room at tail, reallocate without expansion only if skb is cloned.
          */
         int i, k, eat = (skb->tail + delta) - skb->end;
 
         if (eat > 0 || skb_cloned(skb)) {
                 if (pskb_expand_head(skb, 0, eat > 0 ? eat + 128 : 0,
                                      GFP_ATOMIC))
                         return NULL;
         }
 
         if (skb_copy_bits(skb, skb_headlen(skb), skb_tail_pointer(skb), delta))
                 BUG();
 
         /* Optimization: no fragments, no reasons to preestimate
          * size of pulled pages. Superb.
          */
         if (!skb_has_frag_list(skb))
                 goto pull_pages;
 
         /* Estimate size of pulled pages. */
         eat = delta;
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int size = skb_frag_size(&skb_shinfo(skb)->frags[i]);
 
                 if (size >= eat)
                         goto pull_pages;
                 eat -= size;
         }
 
         /* If we need update frag list, we are in troubles.
          * Certainly, it possible to add an offset to skb data,
          * but taking into account that pulling is expected to
          * be very rare operation, it is worth to fight against
          * further bloating skb head and crucify ourselves here instead.
          * Pure masohism, indeed. 8)8)
          */
         if (eat) {
                 struct sk_buff *list = skb_shinfo(skb)->frag_list;
                 struct sk_buff *clone = NULL;
                 struct sk_buff *insp = NULL;
 
                 do {
                         BUG_ON(!list);
 
                         if (list->len <= eat) {
                                 /* Eaten as whole. */
                                 eat -= list->len;
                                 list = list->next;
                                 insp = list;
                         } else {
                                 /* Eaten partially. */
 
                                 if (skb_shared(list)) {
                                         /* Sucks! We need to fork list. :-( */
                                         clone = skb_clone(list, GFP_ATOMIC);
                                         if (!clone)
                                                 return NULL;
                                         insp = list->next;
                                         list = clone;
                                 } else {
                                         /* This may be pulled without
                                          * problems. */
                                         insp = list;
                                 }
                                 if (!pskb_pull(list, eat)) {
                                         kfree_skb(clone);
                                         return NULL;
                                 }
                                 break;
                         }
                 } while (eat);
 
                 /* Free pulled out fragments. */
                 while ((list = skb_shinfo(skb)->frag_list) != insp) {
                         skb_shinfo(skb)->frag_list = list->next;
                         kfree_skb(list);
                 }
                 /* And insert new clone at head. */
                 if (clone) {
                         clone->next = list;
                         skb_shinfo(skb)->frag_list = clone;
                 }
         }
         /* Success! Now we may commit changes to skb data. */
 
 pull_pages:
         eat = delta;
         k = 0;
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int size = skb_frag_size(&skb_shinfo(skb)->frags[i]);
 
                 if (size <= eat) {
                         skb_frag_unref(skb, i);
                         eat -= size;
                 } else {
                         skb_shinfo(skb)->frags[k] = skb_shinfo(skb)->frags[i];
                         if (eat) {
                                 skb_shinfo(skb)->frags[k].page_offset += eat;
                                 skb_frag_size_sub(&skb_shinfo(skb)->frags[k], eat);
                                 eat = 0;
                         }
                         k++;
                 }
         }
         skb_shinfo(skb)->nr_frags = k;
 
         skb->tail     += delta;
         skb->data_len -= delta;
 
         return skb_tail_pointer(skb);
 }
 EXPORT_SYMBOL(__pskb_pull_tail);
 
 /**
  *      skb_copy_bits - copy bits from skb to kernel buffer
  *      @skb: source skb
  *      @offset: offset in source
  *      @to: destination buffer
  *      @len: number of bytes to copy
  *
  *      Copy the specified number of bytes from the source skb to the
  *      destination buffer.
  *
  *      CAUTION ! :
  *              If its prototype is ever changed,
  *              check arch/{*}/net/{*}.S files,
  *              since it is called from BPF assembly code.
  */
 int skb_copy_bits(const struct sk_buff *skb, int offset, void *to, int len)
 {
         int start = skb_headlen(skb);
         struct sk_buff *frag_iter;
         int i, copy;
 
         if (offset > (int)skb->len - len)
                 goto fault;
 
         /* Copy header. */
         if ((copy = start - offset) > 0) {
                 if (copy > len)
                         copy = len;
                 skb_copy_from_linear_data_offset(skb, offset, to, copy);
                 if ((len -= copy) == 0)
                         return 0;
                 offset += copy;
                 to     += copy;
         }
 
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int end;
                 skb_frag_t *f = &skb_shinfo(skb)->frags[i];
 
                 WARN_ON(start > offset + len);
 
                 end = start + skb_frag_size(f);
                 if ((copy = end - offset) > 0) {
                         u8 *vaddr;
 
                         if (copy > len)
                                 copy = len;
 
                         vaddr = kmap_atomic(skb_frag_page(f));
                         memcpy(to,
                                vaddr + f->page_offset + offset - start,
                                copy);
                         kunmap_atomic(vaddr);
 
                         if ((len -= copy) == 0)
                                 return 0;
                         offset += copy;
                         to     += copy;
                 }
                 start = end;
         }
 
         skb_walk_frags(skb, frag_iter) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + frag_iter->len;
                 if ((copy = end - offset) > 0) {
                         if (copy > len)
                                 copy = len;
                         if (skb_copy_bits(frag_iter, offset - start, to, copy))
                                 goto fault;
                         if ((len -= copy) == 0)
                                 return 0;
                         offset += copy;
                         to     += copy;
                 }
                 start = end;
         }
 
         if (!len)
                 return 0;
 
 fault:
         return -EFAULT;
 }
 EXPORT_SYMBOL(skb_copy_bits);
 
 /*
  * Callback from splice_to_pipe(), if we need to release some pages
  * at the end of the spd in case we error'ed out in filling the pipe.
  */
 static void sock_spd_release(struct splice_pipe_desc *spd, unsigned int i)
 {
         put_page(spd->pages[i]);
 }
 
 static struct page *linear_to_page(struct page *page, unsigned int *len,
                                    unsigned int *offset,
                                    struct sock *sk)
 {
         struct page_frag *pfrag = sk_page_frag(sk);
 
         if (!sk_page_frag_refill(sk, pfrag))
                 return NULL;
 
         *len = min_t(unsigned int, *len, pfrag->size - pfrag->offset);
 
         memcpy(page_address(pfrag->page) + pfrag->offset,
                page_address(page) + *offset, *len);
         *offset = pfrag->offset;
         pfrag->offset += *len;
 
         return pfrag->page;
 }
 
 static bool spd_can_coalesce(const struct splice_pipe_desc *spd,
                              struct page *page,
                              unsigned int offset)
 {
         return  spd->nr_pages &&
                 spd->pages[spd->nr_pages - 1] == page &&
                 (spd->partial[spd->nr_pages - 1].offset +
                  spd->partial[spd->nr_pages - 1].len == offset);
 }
 
 /*
  * Fill page/offset/length into spd, if it can hold more pages.
  */
 static bool spd_fill_page(struct splice_pipe_desc *spd,
                           struct pipe_inode_info *pipe, struct page *page,
                           unsigned int *len, unsigned int offset,
                           bool linear,
                           struct sock *sk)
 {
         if (unlikely(spd->nr_pages == MAX_SKB_FRAGS))
                 return true;
 
         if (linear) {
                 page = linear_to_page(page, len, &offset, sk);
                 if (!page)
                         return true;
         }
         if (spd_can_coalesce(spd, page, offset)) {
                 spd->partial[spd->nr_pages - 1].len += *len;
                 return false;
         }
         get_page(page);
         spd->pages[spd->nr_pages] = page;
         spd->partial[spd->nr_pages].len = *len;
         spd->partial[spd->nr_pages].offset = offset;
         spd->nr_pages++;
 
         return false;
 }
 
 static bool __splice_segment(struct page *page, unsigned int poff,
                              unsigned int plen, unsigned int *off,
                              unsigned int *len,
                              struct splice_pipe_desc *spd, bool linear,
                              struct sock *sk,
                              struct pipe_inode_info *pipe)
 {
         if (!*len)
                 return true;
 
         /* skip this segment if already processed */
         if (*off >= plen) {
                 *off -= plen;
                 return false;
         }
 
         /* ignore any bits we already processed */
         poff += *off;
         plen -= *off;
         *off = 0;
 
         do {
                 unsigned int flen = min(*len, plen);
 
                 if (spd_fill_page(spd, pipe, page, &flen, poff,
                                   linear, sk))
                         return true;
                 poff += flen;
                 plen -= flen;
                 *len -= flen;
         } while (*len && plen);
 
         return false;
 }
 
 /*
  * Map linear and fragment data from the skb to spd. It reports true if the
  * pipe is full or if we already spliced the requested length.
  */
 static bool __skb_splice_bits(struct sk_buff *skb, struct pipe_inode_info *pipe,
                               unsigned int *offset, unsigned int *len,
                               struct splice_pipe_desc *spd, struct sock *sk)
 {
         int seg;
 
         /* map the linear part :
          * If skb->head_frag is set, this 'linear' part is backed by a
          * fragment, and if the head is not shared with any clones then
          * we can avoid a copy since we own the head portion of this page.
          */
         if (__splice_segment(virt_to_page(skb->data),
                              (unsigned long) skb->data & (PAGE_SIZE - 1),
                              skb_headlen(skb),
                              offset, len, spd,
                              skb_head_is_locked(skb),
                              sk, pipe))
                 return true;
 
         /*
          * then map the fragments
          */
         for (seg = 0; seg < skb_shinfo(skb)->nr_frags; seg++) {
                 const skb_frag_t *f = &skb_shinfo(skb)->frags[seg];
 
                 if (__splice_segment(skb_frag_page(f),
                                      f->page_offset, skb_frag_size(f),
                                      offset, len, spd, false, sk, pipe))
                         return true;
         }
 
         return false;
 }
 
 /*
  * Map data from the skb to a pipe. Should handle both the linear part,
  * the fragments, and the frag list. It does NOT handle frag lists within
  * the frag list, if such a thing exists. We'd probably need to recurse to
  * handle that cleanly.
  */
 int skb_splice_bits(struct sk_buff *skb, unsigned int offset,
                     struct pipe_inode_info *pipe, unsigned int tlen,
                     unsigned int flags)
 {
         struct partial_page partial[MAX_SKB_FRAGS];
         struct page *pages[MAX_SKB_FRAGS];
         struct splice_pipe_desc spd = {
                 .pages = pages,
                 .partial = partial,
                 .nr_pages_max = MAX_SKB_FRAGS,
                 .flags = flags,
                 .ops = &nosteal_pipe_buf_ops,
                 .spd_release = sock_spd_release,
         };
         struct sk_buff *frag_iter;
         struct sock *sk = skb->sk;
         int ret = 0;
 
         /*
          * __skb_splice_bits() only fails if the output has no room left,
          * so no point in going over the frag_list for the error case.
          */
         if (__skb_splice_bits(skb, pipe, &offset, &tlen, &spd, sk))
                 goto done;
         else if (!tlen)
                 goto done;
 
         /*
          * now see if we have a frag_list to map
          */
         skb_walk_frags(skb, frag_iter) {
                 if (!tlen)
                         break;
                 if (__skb_splice_bits(frag_iter, pipe, &offset, &tlen, &spd, sk))
                         break;
         }
 
 done:
         if (spd.nr_pages) {
                 /*
                  * Drop the socket lock, otherwise we have reverse
                  * locking dependencies between sk_lock and i_mutex
                  * here as compared to sendfile(). We enter here
                  * with the socket lock held, and splice_to_pipe() will
                  * grab the pipe inode lock. For sendfile() emulation,
                  * we call into ->sendpage() with the i_mutex lock held
                  * and networking will grab the socket lock.
                  */
                 release_sock(sk);
                 ret = splice_to_pipe(pipe, &spd);
                 lock_sock(sk);
         }
 
         return ret;
 }
 
 /**
  *      skb_store_bits - store bits from kernel buffer to skb
  *      @skb: destination buffer
  *      @offset: offset in destination
  *      @from: source buffer
  *      @len: number of bytes to copy
  *
  *      Copy the specified number of bytes from the source buffer to the
  *      destination skb.  This function handles all the messy bits of
  *      traversing fragment lists and such.
  */
 
 int skb_store_bits(struct sk_buff *skb, int offset, const void *from, int len)
 {
         int start = skb_headlen(skb);
         struct sk_buff *frag_iter;
         int i, copy;
 
         if (offset > (int)skb->len - len)
                 goto fault;
 
         if ((copy = start - offset) > 0) {
                 if (copy > len)
                         copy = len;
                 skb_copy_to_linear_data_offset(skb, offset, from, copy);
                 if ((len -= copy) == 0)
                         return 0;
                 offset += copy;
                 from += copy;
         }
 
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + skb_frag_size(frag);
                 if ((copy = end - offset) > 0) {
                         u8 *vaddr;
 
                         if (copy > len)
                                 copy = len;
 
                         vaddr = kmap_atomic(skb_frag_page(frag));
                         memcpy(vaddr + frag->page_offset + offset - start,
                                from, copy);
                         kunmap_atomic(vaddr);
 
                         if ((len -= copy) == 0)
                                 return 0;
                         offset += copy;
                         from += copy;
                 }
                 start = end;
         }
 
         skb_walk_frags(skb, frag_iter) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + frag_iter->len;
                 if ((copy = end - offset) > 0) {
                         if (copy > len)
                                 copy = len;
                         if (skb_store_bits(frag_iter, offset - start,
                                            from, copy))
                                 goto fault;
                         if ((len -= copy) == 0)
                                 return 0;
                         offset += copy;
                         from += copy;
                 }
                 start = end;
         }
         if (!len)
                 return 0;
 
 fault:
         return -EFAULT;
 }
 EXPORT_SYMBOL(skb_store_bits);
 
 /* Checksum skb data. */
 __wsum __skb_checksum(const struct sk_buff *skb, int offset, int len,
                       __wsum csum, const struct skb_checksum_ops *ops)
 {
         int start = skb_headlen(skb);
         int i, copy = start - offset;
         struct sk_buff *frag_iter;
         int pos = 0;
 
         /* Checksum header. */
         if (copy > 0) {
                 if (copy > len)
                         copy = len;
                 csum = ops->update(skb->data + offset, copy, csum);
                 if ((len -= copy) == 0)
                         return csum;
                 offset += copy;
                 pos     = copy;
         }
 
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int end;
                 skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
 
                 WARN_ON(start > offset + len);
 
                 end = start + skb_frag_size(frag);
                 if ((copy = end - offset) > 0) {
                         __wsum csum2;
                         u8 *vaddr;
 
                         if (copy > len)
                                 copy = len;
                         vaddr = kmap_atomic(skb_frag_page(frag));
                         csum2 = ops->update(vaddr + frag->page_offset +
                                             offset - start, copy, 0);
                         kunmap_atomic(vaddr);
                         csum = ops->combine(csum, csum2, pos, copy);
                         if (!(len -= copy))
                                 return csum;
                         offset += copy;
                         pos    += copy;
                 }
                 start = end;
         }
 
         skb_walk_frags(skb, frag_iter) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + frag_iter->len;
                 if ((copy = end - offset) > 0) {
                         __wsum csum2;
                         if (copy > len)
                                 copy = len;
                         csum2 = __skb_checksum(frag_iter, offset - start,
                                                copy, 0, ops);
                         csum = ops->combine(csum, csum2, pos, copy);
                         if ((len -= copy) == 0)
                                 return csum;
                         offset += copy;
                         pos    += copy;
                 }
                 start = end;
         }
         BUG_ON(len);
 
         return csum;
 }
 EXPORT_SYMBOL(__skb_checksum);
 
 __wsum skb_checksum(const struct sk_buff *skb, int offset,
                     int len, __wsum csum)
 {
         const struct skb_checksum_ops ops = {
                 .update  = csum_partial_ext,
                 .combine = csum_block_add_ext,
         };
 
         return __skb_checksum(skb, offset, len, csum, &ops);
 }
 EXPORT_SYMBOL(skb_checksum);
 
 /* Both of above in one bottle. */
 
 __wsum skb_copy_and_csum_bits(const struct sk_buff *skb, int offset,
                                     u8 *to, int len, __wsum csum)
 {
         int start = skb_headlen(skb);
         int i, copy = start - offset;
         struct sk_buff *frag_iter;
         int pos = 0;
 
         /* Copy header. */
         if (copy > 0) {
                 if (copy > len)
                         copy = len;
                 csum = csum_partial_copy_nocheck(skb->data + offset, to,
                                                  copy, csum);
                 if ((len -= copy) == 0)
                         return csum;
                 offset += copy;
                 to     += copy;
                 pos     = copy;
         }
 
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + skb_frag_size(&skb_shinfo(skb)->frags[i]);
                 if ((copy = end - offset) > 0) {
                         __wsum csum2;
                         u8 *vaddr;
                         skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
 
                         if (copy > len)
                                 copy = len;
                         vaddr = kmap_atomic(skb_frag_page(frag));
                         csum2 = csum_partial_copy_nocheck(vaddr +
                                                           frag->page_offset +
                                                           offset - start, to,
                                                           copy, 0);
                         kunmap_atomic(vaddr);
                         csum = csum_block_add(csum, csum2, pos);
                         if (!(len -= copy))
                                 return csum;
                         offset += copy;
                         to     += copy;
                         pos    += copy;
                 }
                 start = end;
         }
 
         skb_walk_frags(skb, frag_iter) {
                 __wsum csum2;
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + frag_iter->len;
                 if ((copy = end - offset) > 0) {
                         if (copy > len)
                                 copy = len;
                         csum2 = skb_copy_and_csum_bits(frag_iter,
                                                        offset - start,
                                                        to, copy, 0);
                         csum = csum_block_add(csum, csum2, pos);
                         if ((len -= copy) == 0)
                                 return csum;
                         offset += copy;
                         to     += copy;
                         pos    += copy;
                 }
                 start = end;
         }
         BUG_ON(len);
         return csum;
 }
 EXPORT_SYMBOL(skb_copy_and_csum_bits);
 
  /**
  *      skb_zerocopy_headlen - Calculate headroom needed for skb_zerocopy()
  *      @from: source buffer
  *
  *      Calculates the amount of linear headroom needed in the 'to' skb passed
  *      into skb_zerocopy().
  */
 unsigned int
 skb_zerocopy_headlen(const struct sk_buff *from)
 {
         unsigned int hlen = 0;
 
         if (!from->head_frag ||
             skb_headlen(from) < L1_CACHE_BYTES ||
             skb_shinfo(from)->nr_frags >= MAX_SKB_FRAGS)
                 hlen = skb_headlen(from);
 
         if (skb_has_frag_list(from))
                 hlen = from->len;
 
         return hlen;
 }
 EXPORT_SYMBOL_GPL(skb_zerocopy_headlen);
 
 /**
  *      skb_zerocopy - Zero copy skb to skb
  *      @to: destination buffer
  *      @from: source buffer
  *      @len: number of bytes to copy from source buffer
  *      @hlen: size of linear headroom in destination buffer
  *
  *      Copies up to `len` bytes from `from` to `to` by creating references
  *      to the frags in the source buffer.
  *
  *      The `hlen` as calculated by skb_zerocopy_headlen() specifies the
  *      headroom in the `to` buffer.
  *
  *      Return value:
  *      0: everything is OK
  *      -ENOMEM: couldn't orphan frags of @from due to lack of memory
  *      -EFAULT: skb_copy_bits() found some problem with skb geometry
  */
 int
 skb_zerocopy(struct sk_buff *to, struct sk_buff *from, int len, int hlen)
 {
         int i, j = 0;
         int plen = 0; /* length of skb->head fragment */
         int ret;
         struct page *page;
         unsigned int offset;
 
         BUG_ON(!from->head_frag && !hlen);
 
         /* dont bother with small payloads */
         if (len <= skb_tailroom(to))
                 return skb_copy_bits(from, 0, skb_put(to, len), len);
 
         if (hlen) {
                 ret = skb_copy_bits(from, 0, skb_put(to, hlen), hlen);
                 if (unlikely(ret))
                         return ret;
                 len -= hlen;
         } else {
                 plen = min_t(int, skb_headlen(from), len);
                 if (plen) {
                         page = virt_to_head_page(from->head);
                         offset = from->data - (unsigned char *)page_address(page);
                         __skb_fill_page_desc(to, 0, page, offset, plen);
                         get_page(page);
                         j = 1;
                         len -= plen;
                 }
         }
 
         to->truesize += len + plen;
         to->len += len + plen;
         to->data_len += len + plen;
 
         if (unlikely(skb_orphan_frags(from, GFP_ATOMIC))) {
                 skb_tx_error(from);
                 return -ENOMEM;
         }
 
         for (i = 0; i < skb_shinfo(from)->nr_frags; i++) {
                 if (!len)
                         break;
                 skb_shinfo(to)->frags[j] = skb_shinfo(from)->frags[i];
                 skb_shinfo(to)->frags[j].size = min_t(int, skb_shinfo(to)->frags[j].size, len);
                 len -= skb_shinfo(to)->frags[j].size;
                 skb_frag_ref(to, j);
                 j++;
         }
         skb_shinfo(to)->nr_frags = j;
 
         return 0;
 }
 EXPORT_SYMBOL_GPL(skb_zerocopy);
 
 void skb_copy_and_csum_dev(const struct sk_buff *skb, u8 *to)
 {
         __wsum csum;
         long csstart;
 
         if (skb->ip_summed == CHECKSUM_PARTIAL)
                 csstart = skb_checksum_start_offset(skb);
         else
                 csstart = skb_headlen(skb);
 
         BUG_ON(csstart > skb_headlen(skb));
 
         skb_copy_from_linear_data(skb, to, csstart);
 
         csum = 0;
         if (csstart != skb->len)
                 csum = skb_copy_and_csum_bits(skb, csstart, to + csstart,
                                               skb->len - csstart, 0);
 
         if (skb->ip_summed == CHECKSUM_PARTIAL) {
                 long csstuff = csstart + skb->csum_offset;
 
                 *((__sum16 *)(to + csstuff)) = csum_fold(csum);
         }
 }
 EXPORT_SYMBOL(skb_copy_and_csum_dev);
 
 /**
  *      skb_dequeue - remove from the head of the queue
  *      @list: list to dequeue from
  *
  *      Remove the head of the list. The list lock is taken so the function
  *      may be used safely with other locking list functions. The head item is
  *      returned or %NULL if the list is empty.
  */
 
 struct sk_buff *skb_dequeue(struct sk_buff_head *list)
 {
         unsigned long flags;
         struct sk_buff *result;
 
         spin_lock_irqsave(&list->lock, flags);
         result = __skb_dequeue(list);
         spin_unlock_irqrestore(&list->lock, flags);
         return result;
 }
 EXPORT_SYMBOL(skb_dequeue);
 
 /**
  *      skb_dequeue_tail - remove from the tail of the queue
  *      @list: list to dequeue from
  *
  *      Remove the tail of the list. The list lock is taken so the function
  *      may be used safely with other locking list functions. The tail item is
  *      returned or %NULL if the list is empty.
  */
 struct sk_buff *skb_dequeue_tail(struct sk_buff_head *list)
 {
         unsigned long flags;
         struct sk_buff *result;
 
         spin_lock_irqsave(&list->lock, flags);
         result = __skb_dequeue_tail(list);
         spin_unlock_irqrestore(&list->lock, flags);
         return result;
 }
 EXPORT_SYMBOL(skb_dequeue_tail);
 
 /**
  *      skb_queue_purge - empty a list
  *      @list: list to empty
  *
  *      Delete all buffers on an &sk_buff list. Each buffer is removed from
  *      the list and one reference dropped. This function takes the list
  *      lock and is atomic with respect to other list locking functions.
  */
 void skb_queue_purge(struct sk_buff_head *list)
 {
         struct sk_buff *skb;
         while ((skb = skb_dequeue(list)) != NULL)
                 kfree_skb(skb);
 }
 EXPORT_SYMBOL(skb_queue_purge);
 
 /**
  *      skb_queue_head - queue a buffer at the list head
  *      @list: list to use
  *      @newsk: buffer to queue
  *
  *      Queue a buffer at the start of the list. This function takes the
  *      list lock and can be used safely with other locking &sk_buff functions
  *      safely.
  *
  *      A buffer cannot be placed on two lists at the same time.
  */
 void skb_queue_head(struct sk_buff_head *list, struct sk_buff *newsk)
 {
         unsigned long flags;
 
         spin_lock_irqsave(&list->lock, flags);
         __skb_queue_head(list, newsk);
         spin_unlock_irqrestore(&list->lock, flags);
 }
 EXPORT_SYMBOL(skb_queue_head);
 
 /**
  *      skb_queue_tail - queue a buffer at the list tail
  *      @list: list to use
  *      @newsk: buffer to queue
  *
  *      Queue a buffer at the tail of the list. This function takes the
  *      list lock and can be used safely with other locking &sk_buff functions
  *      safely.
  *
  *      A buffer cannot be placed on two lists at the same time.
  */
 void skb_queue_tail(struct sk_buff_head *list, struct sk_buff *newsk)
 {
         unsigned long flags;
 
         spin_lock_irqsave(&list->lock, flags);
         __skb_queue_tail(list, newsk);
         spin_unlock_irqrestore(&list->lock, flags);
 }
 EXPORT_SYMBOL(skb_queue_tail);
 
 /**
  *      skb_unlink      -       remove a buffer from a list
  *      @skb: buffer to remove
  *      @list: list to use
  *
  *      Remove a packet from a list. The list locks are taken and this
  *      function is atomic with respect to other list locked calls
  *
  *      You must know what list the SKB is on.
  */
 void skb_unlink(struct sk_buff *skb, struct sk_buff_head *list)
 {
         unsigned long flags;
 
         spin_lock_irqsave(&list->lock, flags);
         __skb_unlink(skb, list);
         spin_unlock_irqrestore(&list->lock, flags);
 }
 EXPORT_SYMBOL(skb_unlink);
 
 /**
  *      skb_append      -       append a buffer
  *      @old: buffer to insert after
  *      @newsk: buffer to insert
  *      @list: list to use
  *
  *      Place a packet after a given packet in a list. The list locks are taken
  *      and this function is atomic with respect to other list locked calls.
  *      A buffer cannot be placed on two lists at the same time.
  */
 void skb_append(struct sk_buff *old, struct sk_buff *newsk, struct sk_buff_head *list)
 {
         unsigned long flags;
 
         spin_lock_irqsave(&list->lock, flags);
         __skb_queue_after(list, old, newsk);
         spin_unlock_irqrestore(&list->lock, flags);
 }
 EXPORT_SYMBOL(skb_append);
 
 /**
  *      skb_insert      -       insert a buffer
  *      @old: buffer to insert before
  *      @newsk: buffer to insert
  *      @list: list to use
  *
  *      Place a packet before a given packet in a list. The list locks are
  *      taken and this function is atomic with respect to other list locked
  *      calls.
  *
  *      A buffer cannot be placed on two lists at the same time.
  */
 void skb_insert(struct sk_buff *old, struct sk_buff *newsk, struct sk_buff_head *list)
 {
         unsigned long flags;
 
         spin_lock_irqsave(&list->lock, flags);
         __skb_insert(newsk, old->prev, old, list);
         spin_unlock_irqrestore(&list->lock, flags);
 }
 EXPORT_SYMBOL(skb_insert);
 
 static inline void skb_split_inside_header(struct sk_buff *skb,
                                            struct sk_buff* skb1,
                                            const u32 len, const int pos)
 {
         int i;
 
         skb_copy_from_linear_data_offset(skb, len, skb_put(skb1, pos - len),
                                          pos - len);
         /* And move data appendix as is. */
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++)
                 skb_shinfo(skb1)->frags[i] = skb_shinfo(skb)->frags[i];
 
         skb_shinfo(skb1)->nr_frags = skb_shinfo(skb)->nr_frags;
         skb_shinfo(skb)->nr_frags  = 0;
         skb1->data_len             = skb->data_len;
         skb1->len                  += skb1->data_len;
         skb->data_len              = 0;
         skb->len                   = len;
         skb_set_tail_pointer(skb, len);
 }
 
 static inline void skb_split_no_header(struct sk_buff *skb,
                                        struct sk_buff* skb1,
                                        const u32 len, int pos)
 {
         int i, k = 0;
         const int nfrags = skb_shinfo(skb)->nr_frags;
 
         skb_shinfo(skb)->nr_frags = 0;
         skb1->len                 = skb1->data_len = skb->len - len;
         skb->len                  = len;
         skb->data_len             = len - pos;
 
         for (i = 0; i < nfrags; i++) {
                 int size = skb_frag_size(&skb_shinfo(skb)->frags[i]);
 
                 if (pos + size > len) {
                         skb_shinfo(skb1)->frags[k] = skb_shinfo(skb)->frags[i];
 
                         if (pos < len) {
                                 /* Split frag.
                                  * We have two variants in this case:
                                  * 1. Move all the frag to the second
                                  *    part, if it is possible. F.e.
                                  *    this approach is mandatory for TUX,
                                  *    where splitting is expensive.
                                  * 2. Split is accurately. We make this.
                                  */
                                 skb_frag_ref(skb, i);
                                 skb_shinfo(skb1)->frags[0].page_offset += len - pos;
                                 skb_frag_size_sub(&skb_shinfo(skb1)->frags[0], len - pos);
                                 skb_frag_size_set(&skb_shinfo(skb)->frags[i], len - pos);
                                 skb_shinfo(skb)->nr_frags++;
                         }
                         k++;
                 } else
                         skb_shinfo(skb)->nr_frags++;
                 pos += size;
         }
         skb_shinfo(skb1)->nr_frags = k;
 }
 
 /**
  * skb_split - Split fragmented skb to two parts at length len.
  * @skb: the buffer to split
  * @skb1: the buffer to receive the second part
  * @len: new length for skb
  */
 void skb_split(struct sk_buff *skb, struct sk_buff *skb1, const u32 len)
 {
         int pos = skb_headlen(skb);
 
         skb_shinfo(skb1)->tx_flags = skb_shinfo(skb)->tx_flags & SKBTX_SHARED_FRAG;
         if (len < pos)  /* Split line is inside header. */
                 skb_split_inside_header(skb, skb1, len, pos);
         else            /* Second chunk has no header, nothing to copy. */
                 skb_split_no_header(skb, skb1, len, pos);
 }
 EXPORT_SYMBOL(skb_split);
 
 /* Shifting from/to a cloned skb is a no-go.
  *
  * Caller cannot keep skb_shinfo related pointers past calling here!
  */
 static int skb_prepare_for_shift(struct sk_buff *skb)
 {
         return skb_cloned(skb) && pskb_expand_head(skb, 0, 0, GFP_ATOMIC);
 }
 
 /**
  * skb_shift - Shifts paged data partially from skb to another
  * @tgt: buffer into which tail data gets added
  * @skb: buffer from which the paged data comes from
  * @shiftlen: shift up to this many bytes
  *
  * Attempts to shift up to shiftlen worth of bytes, which may be less than
  * the length of the skb, from skb to tgt. Returns number bytes shifted.
  * It's up to caller to free skb if everything was shifted.
  *
  * If @tgt runs out of frags, the whole operation is aborted.
  *
  * Skb cannot include anything else but paged data while tgt is allowed
  * to have non-paged data as well.
  *
  * TODO: full sized shift could be optimized but that would need
  * specialized skb free'er to handle frags without up-to-date nr_frags.
  */
 int skb_shift(struct sk_buff *tgt, struct sk_buff *skb, int shiftlen)
 {
         int from, to, merge, todo;
         struct skb_frag_struct *fragfrom, *fragto;
 
         BUG_ON(shiftlen > skb->len);
         BUG_ON(skb_headlen(skb));       /* Would corrupt stream */
 
         todo = shiftlen;
         from = 0;
         to = skb_shinfo(tgt)->nr_frags;
         fragfrom = &skb_shinfo(skb)->frags[from];
 
         /* Actual merge is delayed until the point when we know we can
          * commit all, so that we don't have to undo partial changes
          */
         if (!to ||
             !skb_can_coalesce(tgt, to, skb_frag_page(fragfrom),
                               fragfrom->page_offset)) {
                 merge = -1;
         } else {
                 merge = to - 1;
 
                 todo -= skb_frag_size(fragfrom);
                 if (todo < 0) {
                         if (skb_prepare_for_shift(skb) ||
                             skb_prepare_for_shift(tgt))
                                 return 0;
 
                         /* All previous frag pointers might be stale! */
                         fragfrom = &skb_shinfo(skb)->frags[from];
                         fragto = &skb_shinfo(tgt)->frags[merge];
 
                         skb_frag_size_add(fragto, shiftlen);
                         skb_frag_size_sub(fragfrom, shiftlen);
                         fragfrom->page_offset += shiftlen;
 
                         goto onlymerged;
                 }
 
                 from++;
         }
 
         /* Skip full, not-fitting skb to avoid expensive operations */
         if ((shiftlen == skb->len) &&
             (skb_shinfo(skb)->nr_frags - from) > (MAX_SKB_FRAGS - to))
                 return 0;
 
         if (skb_prepare_for_shift(skb) || skb_prepare_for_shift(tgt))
                 return 0;
 
         while ((todo > 0) && (from < skb_shinfo(skb)->nr_frags)) {
                 if (to == MAX_SKB_FRAGS)
                         return 0;
 
                 fragfrom = &skb_shinfo(skb)->frags[from];
                 fragto = &skb_shinfo(tgt)->frags[to];
 
                 if (todo >= skb_frag_size(fragfrom)) {
                         *fragto = *fragfrom;
                         todo -= skb_frag_size(fragfrom);
                         from++;
                         to++;
 
                 } else {
                         __skb_frag_ref(fragfrom);
                         fragto->page = fragfrom->page;
                         fragto->page_offset = fragfrom->page_offset;
                         skb_frag_size_set(fragto, todo);
 
                         fragfrom->page_offset += todo;
                         skb_frag_size_sub(fragfrom, todo);
                         todo = 0;
 
                         to++;
                         break;
                 }
         }
 
         /* Ready to "commit" this state change to tgt */
         skb_shinfo(tgt)->nr_frags = to;
 
         if (merge >= 0) {
                 fragfrom = &skb_shinfo(skb)->frags[0];
                 fragto = &skb_shinfo(tgt)->frags[merge];
 
                 skb_frag_size_add(fragto, skb_frag_size(fragfrom));
                 __skb_frag_unref(fragfrom);
         }
 
         /* Reposition in the original skb */
         to = 0;
         while (from < skb_shinfo(skb)->nr_frags)
                 skb_shinfo(skb)->frags[to++] = skb_shinfo(skb)->frags[from++];
         skb_shinfo(skb)->nr_frags = to;
 
         BUG_ON(todo > 0 && !skb_shinfo(skb)->nr_frags);
 
 onlymerged:
         /* Most likely the tgt won't ever need its checksum anymore, skb on
          * the other hand might need it if it needs to be resent
          */
         tgt->ip_summed = CHECKSUM_PARTIAL;
         skb->ip_summed = CHECKSUM_PARTIAL;
 
         /* Yak, is it really working this way? Some helper please? */
         skb->len -= shiftlen;
         skb->data_len -= shiftlen;
         skb->truesize -= shiftlen;
         tgt->len += shiftlen;
         tgt->data_len += shiftlen;
         tgt->truesize += shiftlen;
 
         return shiftlen;
 }
 
 /**
  * skb_prepare_seq_read - Prepare a sequential read of skb data
  * @skb: the buffer to read
  * @from: lower offset of data to be read
  * @to: upper offset of data to be read
  * @st: state variable
  *
  * Initializes the specified state variable. Must be called before
  * invoking skb_seq_read() for the first time.
  */
 void skb_prepare_seq_read(struct sk_buff *skb, unsigned int from,
                           unsigned int to, struct skb_seq_state *st)
 {
         st->lower_offset = from;
         st->upper_offset = to;
         st->root_skb = st->cur_skb = skb;
         st->frag_idx = st->stepped_offset = 0;
         st->frag_data = NULL;
 }
 EXPORT_SYMBOL(skb_prepare_seq_read);
 
 /**
  * skb_seq_read - Sequentially read skb data
  * @consumed: number of bytes consumed by the caller so far
  * @data: destination pointer for data to be returned
  * @st: state variable
  *
  * Reads a block of skb data at @consumed relative to the
  * lower offset specified to skb_prepare_seq_read(). Assigns
  * the head of the data block to @data and returns the length
  * of the block or 0 if the end of the skb data or the upper
  * offset has been reached.
  *
  * The caller is not required to consume all of the data
  * returned, i.e. @consumed is typically set to the number
  * of bytes already consumed and the next call to
  * skb_seq_read() will return the remaining part of the block.
  *
  * Note 1: The size of each block of data returned can be arbitrary,
  *       this limitation is the cost for zerocopy sequential
  *       reads of potentially non linear data.
  *
  * Note 2: Fragment lists within fragments are not implemented
  *       at the moment, state->root_skb could be replaced with
  *       a stack for this purpose.
  */
 unsigned int skb_seq_read(unsigned int consumed, const u8 **data,
                           struct skb_seq_state *st)
 {
         unsigned int block_limit, abs_offset = consumed + st->lower_offset;
         skb_frag_t *frag;
 
         if (unlikely(abs_offset >= st->upper_offset)) {
                 if (st->frag_data) {
                         kunmap_atomic(st->frag_data);
                         st->frag_data = NULL;
                 }
                 return 0;
         }
 
 next_skb:
         block_limit = skb_headlen(st->cur_skb) + st->stepped_offset;
 
         if (abs_offset < block_limit && !st->frag_data) {
                 *data = st->cur_skb->data + (abs_offset - st->stepped_offset);
                 return block_limit - abs_offset;
         }
 
         if (st->frag_idx == 0 && !st->frag_data)
                 st->stepped_offset += skb_headlen(st->cur_skb);
 
         while (st->frag_idx < skb_shinfo(st->cur_skb)->nr_frags) {
                 frag = &skb_shinfo(st->cur_skb)->frags[st->frag_idx];
                 block_limit = skb_frag_size(frag) + st->stepped_offset;
 
                 if (abs_offset < block_limit) {
                         if (!st->frag_data)
                                 st->frag_data = kmap_atomic(skb_frag_page(frag));
 
                         *data = (u8 *) st->frag_data + frag->page_offset +
                                 (abs_offset - st->stepped_offset);
 
                         return block_limit - abs_offset;
                 }
 
                 if (st->frag_data) {
                         kunmap_atomic(st->frag_data);
                         st->frag_data = NULL;
                 }
 
                 st->frag_idx++;
                 st->stepped_offset += skb_frag_size(frag);
         }
 
         if (st->frag_data) {
                 kunmap_atomic(st->frag_data);
                 st->frag_data = NULL;
         }
 
         if (st->root_skb == st->cur_skb && skb_has_frag_list(st->root_skb)) {
                 st->cur_skb = skb_shinfo(st->root_skb)->frag_list;
                 st->frag_idx = 0;
                 goto next_skb;
         } else if (st->cur_skb->next) {
                 st->cur_skb = st->cur_skb->next;
                 st->frag_idx = 0;
                 goto next_skb;
         }
 
         return 0;
 }
 EXPORT_SYMBOL(skb_seq_read);
 
 /**
  * skb_abort_seq_read - Abort a sequential read of skb data
  * @st: state variable
  *
  * Must be called if skb_seq_read() was not called until it
  * returned 0.
  */
 void skb_abort_seq_read(struct skb_seq_state *st)
 {
         if (st->frag_data)
                 kunmap_atomic(st->frag_data);
 }
 EXPORT_SYMBOL(skb_abort_seq_read);
 
 #define TS_SKB_CB(state)        ((struct skb_seq_state *) &((state)->cb))
 
 static unsigned int skb_ts_get_next_block(unsigned int offset, const u8 **text,
                                           struct ts_config *conf,
                                           struct ts_state *state)
 {
         return skb_seq_read(offset, text, TS_SKB_CB(state));
 }
 
 static void skb_ts_finish(struct ts_config *conf, struct ts_state *state)
 {
         skb_abort_seq_read(TS_SKB_CB(state));
 }
 
 /**
  * skb_find_text - Find a text pattern in skb data
  * @skb: the buffer to look in
  * @from: search offset
  * @to: search limit
  * @config: textsearch configuration
  *
  * Finds a pattern in the skb data according to the specified
  * textsearch configuration. Use textsearch_next() to retrieve
  * subsequent occurrences of the pattern. Returns the offset
  * to the first occurrence or UINT_MAX if no match was found.
  */
 unsigned int skb_find_text(struct sk_buff *skb, unsigned int from,
                            unsigned int to, struct ts_config *config)
 {
         struct ts_state state;
         unsigned int ret;
 
         config->get_next_block = skb_ts_get_next_block;
         config->finish = skb_ts_finish;
 
         skb_prepare_seq_read(skb, from, to, TS_SKB_CB(&state));
 
         ret = textsearch_find(config, &state);
         return (ret <= to - from ? ret : UINT_MAX);
 }
 EXPORT_SYMBOL(skb_find_text);
 
 /**
  * skb_append_datato_frags - append the user data to a skb
  * @sk: sock  structure
  * @skb: skb structure to be appended with user data.
  * @getfrag: call back function to be used for getting the user data
  * @from: pointer to user message iov
  * @length: length of the iov message
  *
  * Description: This procedure append the user data in the fragment part
  * of the skb if any page alloc fails user this procedure returns  -ENOMEM
  */
 int skb_append_datato_frags(struct sock *sk, struct sk_buff *skb,
                         int (*getfrag)(void *from, char *to, int offset,
                                         int len, int odd, struct sk_buff *skb),
                         void *from, int length)
 {
         int frg_cnt = skb_shinfo(skb)->nr_frags;
         int copy;
         int offset = 0;
         int ret;
         struct page_frag *pfrag = &current->task_frag;
 
         do {
                 /* Return error if we don't have space for new frag */
                 if (frg_cnt >= MAX_SKB_FRAGS)
                         return -EMSGSIZE;
 
                 if (!sk_page_frag_refill(sk, pfrag))
                         return -ENOMEM;
 
                 /* copy the user data to page */
                 copy = min_t(int, length, pfrag->size - pfrag->offset);
 
                 ret = getfrag(from, page_address(pfrag->page) + pfrag->offset,
                               offset, copy, 0, skb);
                 if (ret < 0)
                         return -EFAULT;
 
                 /* copy was successful so update the size parameters */
                 skb_fill_page_desc(skb, frg_cnt, pfrag->page, pfrag->offset,
                                    copy);
                 frg_cnt++;
                 pfrag->offset += copy;
                 get_page(pfrag->page);
 
                 skb->truesize += copy;
                 atomic_add(copy, &sk->sk_wmem_alloc);
                 skb->len += copy;
                 skb->data_len += copy;
                 offset += copy;
                 length -= copy;
 
         } while (length > 0);
 
         return 0;
 }
 EXPORT_SYMBOL(skb_append_datato_frags);
 
 /**
  *      skb_pull_rcsum - pull skb and update receive checksum
  *      @skb: buffer to update
  *      @len: length of data pulled
  *
  *      This function performs an skb_pull on the packet and updates
  *      the CHECKSUM_COMPLETE checksum.  It should be used on
  *      receive path processing instead of skb_pull unless you know
  *      that the checksum difference is zero (e.g., a valid IP header)
  *      or you are setting ip_summed to CHECKSUM_NONE.
  */
 unsigned char *skb_pull_rcsum(struct sk_buff *skb, unsigned int len)
 {
         BUG_ON(len > skb->len);
         skb->len -= len;
         BUG_ON(skb->len < skb->data_len);
         skb_postpull_rcsum(skb, skb->data, len);
         return skb->data += len;
 }
 EXPORT_SYMBOL_GPL(skb_pull_rcsum);
 
 /**
  *      skb_segment - Perform protocol segmentation on skb.
  *      @head_skb: buffer to segment
  *      @features: features for the output path (see dev->features)
  *
  *      This function performs segmentation on the given skb.  It returns
  *      a pointer to the first in a list of new skbs for the segments.
  *      In case of error it returns ERR_PTR(err).
  */
 struct sk_buff *skb_segment(struct sk_buff *head_skb,
                             netdev_features_t features)
 {
         struct sk_buff *segs = NULL;
         struct sk_buff *tail = NULL;
         struct sk_buff *list_skb = skb_shinfo(head_skb)->frag_list;
         skb_frag_t *frag = skb_shinfo(head_skb)->frags;
         unsigned int mss = skb_shinfo(head_skb)->gso_size;
         unsigned int doffset = head_skb->data - skb_mac_header(head_skb);
         struct sk_buff *frag_skb = head_skb;
         unsigned int offset = doffset;
         unsigned int tnl_hlen = skb_tnl_header_len(head_skb);
         unsigned int headroom;
         unsigned int len;
         __be16 proto;
         bool csum;
         int sg = !!(features & NETIF_F_SG);
         int nfrags = skb_shinfo(head_skb)->nr_frags;
         int err = -ENOMEM;
         int i = 0;
         int pos;
         int dummy;
 
         __skb_push(head_skb, doffset);
         proto = skb_network_protocol(head_skb, &dummy);
         if (unlikely(!proto))
                 return ERR_PTR(-EINVAL);
 
         csum = !head_skb->encap_hdr_csum &&
             !!can_checksum_protocol(features, proto);
 
         headroom = skb_headroom(head_skb);
         pos = skb_headlen(head_skb);
 
         do {
                 struct sk_buff *nskb;
                 skb_frag_t *nskb_frag;
                 int hsize;
                 int size;
 
                 len = head_skb->len - offset;
                 if (len > mss)
                         len = mss;
 
                 hsize = skb_headlen(head_skb) - offset;
                 if (hsize < 0)
                         hsize = 0;
                 if (hsize > len || !sg)
                         hsize = len;
 
                 if (!hsize && i >= nfrags && skb_headlen(list_skb) &&
                     (skb_headlen(list_skb) == len || sg)) {
                         BUG_ON(skb_headlen(list_skb) > len);
 
                         i = 0;
                         nfrags = skb_shinfo(list_skb)->nr_frags;
                         frag = skb_shinfo(list_skb)->frags;
                         frag_skb = list_skb;
                         pos += skb_headlen(list_skb);
 
                         while (pos < offset + len) {
                                 BUG_ON(i >= nfrags);
 
                                 size = skb_frag_size(frag);
                                 if (pos + size > offset + len)
                                         break;
 
                                 i++;
                                 pos += size;
                                 frag++;
                         }
 
                         nskb = skb_clone(list_skb, GFP_ATOMIC);
                         list_skb = list_skb->next;
 
                         if (unlikely(!nskb))
                                 goto err;
 
                         if (unlikely(pskb_trim(nskb, len))) {
                                 kfree_skb(nskb);
                                 goto err;
                         }
 
                         hsize = skb_end_offset(nskb);
                         if (skb_cow_head(nskb, doffset + headroom)) {
                                 kfree_skb(nskb);
                                 goto err;
                         }
 
                         nskb->truesize += skb_end_offset(nskb) - hsize;
                         skb_release_head_state(nskb);
                         __skb_push(nskb, doffset);
                 } else {
                         nskb = __alloc_skb(hsize + doffset + headroom,
                                            GFP_ATOMIC, skb_alloc_rx_flag(head_skb),
                                            NUMA_NO_NODE);
 
                         if (unlikely(!nskb))
                                 goto err;
 
                         skb_reserve(nskb, headroom);
                         __skb_put(nskb, doffset);
                 }
 
                 if (segs)
                         tail->next = nskb;
                 else
                         segs = nskb;
                 tail = nskb;
 
                 __copy_skb_header(nskb, head_skb);
 
                 skb_headers_offset_update(nskb, skb_headroom(nskb) - headroom);
                 skb_reset_mac_len(nskb);
 
                 skb_copy_from_linear_data_offset(head_skb, -tnl_hlen,
                                                  nskb->data - tnl_hlen,
                                                  doffset + tnl_hlen);
 
                 if (nskb->len == len + doffset)
                         goto perform_csum_check;
 
                 if (!sg && !nskb->remcsum_offload) {
                         nskb->ip_summed = CHECKSUM_NONE;
                         nskb->csum = skb_copy_and_csum_bits(head_skb, offset,
                                                             skb_put(nskb, len),
                                                             len, 0);
                         SKB_GSO_CB(nskb)->csum_start =
                             skb_headroom(nskb) + doffset;
                         continue;
                 }
 
                 nskb_frag = skb_shinfo(nskb)->frags;
 
                 skb_copy_from_linear_data_offset(head_skb, offset,
                                                  skb_put(nskb, hsize), hsize);
 
                 skb_shinfo(nskb)->tx_flags = skb_shinfo(head_skb)->tx_flags &
                         SKBTX_SHARED_FRAG;
 
                 while (pos < offset + len) {
                         if (i >= nfrags) {
                                 BUG_ON(skb_headlen(list_skb));
 
                                 i = 0;
                                 nfrags = skb_shinfo(list_skb)->nr_frags;
                                 frag = skb_shinfo(list_skb)->frags;
                                 frag_skb = list_skb;
 
                                 BUG_ON(!nfrags);
 
                                 list_skb = list_skb->next;
                         }
 
                         if (unlikely(skb_shinfo(nskb)->nr_frags >=
                                      MAX_SKB_FRAGS)) {
                                 net_warn_ratelimited(
                                         "skb_segment: too many frags: %u %u\n",
                                         pos, mss);
                                 goto err;
                         }
 
                         if (unlikely(skb_orphan_frags(frag_skb, GFP_ATOMIC)))
                                 goto err;
 
                         *nskb_frag = *frag;
                         __skb_frag_ref(nskb_frag);
                         size = skb_frag_size(nskb_frag);
 
                         if (pos < offset) {
                                 nskb_frag->page_offset += offset - pos;
                                 skb_frag_size_sub(nskb_frag, offset - pos);
                         }
 
                         skb_shinfo(nskb)->nr_frags++;
 
                         if (pos + size <= offset + len) {
                                 i++;
                                 frag++;
                                 pos += size;
                         } else {
                                 skb_frag_size_sub(nskb_frag, pos + size - (offset + len));
                                 goto skip_fraglist;
                         }
 
                         nskb_frag++;
                 }
 
 skip_fraglist:
                 nskb->data_len = len - hsize;
                 nskb->len += nskb->data_len;
                 nskb->truesize += nskb->data_len;
 
 perform_csum_check:
                 if (!csum && !nskb->remcsum_offload) {
                         nskb->csum = skb_checksum(nskb, doffset,
                                                   nskb->len - doffset, 0);
                         nskb->ip_summed = CHECKSUM_NONE;
                         SKB_GSO_CB(nskb)->csum_start =
                             skb_headroom(nskb) + doffset;
                 }
         } while ((offset += len) < head_skb->len);
 
         /* Some callers want to get the end of the list.
          * Put it in segs->prev to avoid walking the list.
          * (see validate_xmit_skb_list() for example)
          */
         segs->prev = tail;
 
         /* Following permits correct backpressure, for protocols
          * using skb_set_owner_w().
          * Idea is to tranfert ownership from head_skb to last segment.
          */
         if (head_skb->destructor == sock_wfree) {
                 swap(tail->truesize, head_skb->truesize);
                 swap(tail->destructor, head_skb->destructor);
                 swap(tail->sk, head_skb->sk);
         }
         return segs;
 
 err:
         kfree_skb_list(segs);
         return ERR_PTR(err);
 }
 EXPORT_SYMBOL_GPL(skb_segment);
 
 int skb_gro_receive(struct sk_buff **head, struct sk_buff *skb)
 {
         struct skb_shared_info *pinfo, *skbinfo = skb_shinfo(skb);
         unsigned int offset = skb_gro_offset(skb);
         unsigned int headlen = skb_headlen(skb);
         unsigned int len = skb_gro_len(skb);
         struct sk_buff *lp, *p = *head;
         unsigned int delta_truesize;
 
         if (unlikely(p->len + len >= 65536))
                 return -E2BIG;
 
         lp = NAPI_GRO_CB(p)->last;
         pinfo = skb_shinfo(lp);
 
         if (headlen <= offset) {
                 skb_frag_t *frag;
                 skb_frag_t *frag2;
                 int i = skbinfo->nr_frags;
                 int nr_frags = pinfo->nr_frags + i;
 
                 if (nr_frags > MAX_SKB_FRAGS)
                         goto merge;
 
                 offset -= headlen;
                 pinfo->nr_frags = nr_frags;
                 skbinfo->nr_frags = 0;
 
                 frag = pinfo->frags + nr_frags;
                 frag2 = skbinfo->frags + i;
                 do {
                         *--frag = *--frag2;
                 } while (--i);
 
                 frag->page_offset += offset;
                 skb_frag_size_sub(frag, offset);
 
                 /* all fragments truesize : remove (head size + sk_buff) */
                 delta_truesize = skb->truesize -
                                  SKB_TRUESIZE(skb_end_offset(skb));
 
                 skb->truesize -= skb->data_len;
                 skb->len -= skb->data_len;
                 skb->data_len = 0;
 
                 NAPI_GRO_CB(skb)->free = NAPI_GRO_FREE;
                 goto done;
         } else if (skb->head_frag) {
                 int nr_frags = pinfo->nr_frags;
                 skb_frag_t *frag = pinfo->frags + nr_frags;
                 struct page *page = virt_to_head_page(skb->head);
                 unsigned int first_size = headlen - offset;
                 unsigned int first_offset;
 
                 if (nr_frags + 1 + skbinfo->nr_frags > MAX_SKB_FRAGS)
                         goto merge;
 
                 first_offset = skb->data -
                                (unsigned char *)page_address(page) +
                                offset;
 
                 pinfo->nr_frags = nr_frags + 1 + skbinfo->nr_frags;
 
                 frag->page.p      = page;
                 frag->page_offset = first_offset;
                 skb_frag_size_set(frag, first_size);
 
                 memcpy(frag + 1, skbinfo->frags, sizeof(*frag) * skbinfo->nr_frags);
                 /* We dont need to clear skbinfo->nr_frags here */
 
                 delta_truesize = skb->truesize - SKB_DATA_ALIGN(sizeof(struct sk_buff));
                 NAPI_GRO_CB(skb)->free = NAPI_GRO_FREE_STOLEN_HEAD;
                 goto done;
         }
 
 merge:
         delta_truesize = skb->truesize;
         if (offset > headlen) {
                 unsigned int eat = offset - headlen;
 
                 skbinfo->frags[0].page_offset += eat;
                 skb_frag_size_sub(&skbinfo->frags[0], eat);
                 skb->data_len -= eat;
                 skb->len -= eat;
                 offset = headlen;
         }
 
         __skb_pull(skb, offset);
 
         if (NAPI_GRO_CB(p)->last == p)
                 skb_shinfo(p)->frag_list = skb;
         else
                 NAPI_GRO_CB(p)->last->next = skb;
         NAPI_GRO_CB(p)->last = skb;
         __skb_header_release(skb);
         lp = p;
 
 done:
         NAPI_GRO_CB(p)->count++;
         p->data_len += len;
         p->truesize += delta_truesize;
         p->len += len;
         if (lp != p) {
                 lp->data_len += len;
                 lp->truesize += delta_truesize;
                 lp->len += len;
         }
         NAPI_GRO_CB(skb)->same_flow = 1;
         return 0;
 }
 
 void __init skb_init(void)
 {
         skbuff_head_cache = kmem_cache_create("skbuff_head_cache",
                                               sizeof(struct sk_buff),
                                               0,
                                               SLAB_HWCACHE_ALIGN|SLAB_PANIC,
                                               NULL);
         skbuff_fclone_cache = kmem_cache_create("skbuff_fclone_cache",
                                                 sizeof(struct sk_buff_fclones),
                                                 0,
                                                 SLAB_HWCACHE_ALIGN|SLAB_PANIC,
                                                 NULL);
 }
 
 /**
  *      skb_to_sgvec - Fill a scatter-gather list from a socket buffer
  *      @skb: Socket buffer containing the buffers to be mapped
  *      @sg: The scatter-gather list to map into
  *      @offset: The offset into the buffer's contents to start mapping
  *      @len: Length of buffer space to be mapped
  *
  *      Fill the specified scatter-gather list with mappings/pointers into a
  *      region of the buffer space attached to a socket buffer.
  */
 static int
 __skb_to_sgvec(struct sk_buff *skb, struct scatterlist *sg, int offset, int len)
 {
         int start = skb_headlen(skb);
         int i, copy = start - offset;
         struct sk_buff *frag_iter;
         int elt = 0;
 
         if (copy > 0) {
                 if (copy > len)
                         copy = len;
                 sg_set_buf(sg, skb->data + offset, copy);
                 elt++;
                 if ((len -= copy) == 0)
                         return elt;
                 offset += copy;
         }
 
         for (i = 0; i < skb_shinfo(skb)->nr_frags; i++) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + skb_frag_size(&skb_shinfo(skb)->frags[i]);
                 if ((copy = end - offset) > 0) {
                         skb_frag_t *frag = &skb_shinfo(skb)->frags[i];
 
                         if (copy > len)
                                 copy = len;
                         sg_set_page(&sg[elt], skb_frag_page(frag), copy,
                                         frag->page_offset+offset-start);
                         elt++;
                         if (!(len -= copy))
                                 return elt;
                         offset += copy;
                 }
                 start = end;
         }
 
         skb_walk_frags(skb, frag_iter) {
                 int end;
 
                 WARN_ON(start > offset + len);
 
                 end = start + frag_iter->len;
                 if ((copy = end - offset) > 0) {
                         if (copy > len)
                                 copy = len;
                         elt += __skb_to_sgvec(frag_iter, sg+elt, offset - start,
                                               copy);
                         if ((len -= copy) == 0)
                                 return elt;
                         offset += copy;
                 }
                 start = end;
         }
         BUG_ON(len);
         return elt;
 }
 
 /* As compared with skb_to_sgvec, skb_to_sgvec_nomark only map skb to given
  * sglist without mark the sg which contain last skb data as the end.
  * So the caller can mannipulate sg list as will when padding new data after
  * the first call without calling sg_unmark_end to expend sg list.
  *
  * Scenario to use skb_to_sgvec_nomark:
  * 1. sg_init_table
  * 2. skb_to_sgvec_nomark(payload1)
  * 3. skb_to_sgvec_nomark(payload2)
  *
  * This is equivalent to:
  * 1. sg_init_table
  * 2. skb_to_sgvec(payload1)
  * 3. sg_unmark_end
  * 4. skb_to_sgvec(payload2)
  *
  * When mapping mutilple payload conditionally, skb_to_sgvec_nomark
  * is more preferable.
  */
 int skb_to_sgvec_nomark(struct sk_buff *skb, struct scatterlist *sg,
                         int offset, int len)
 {
         return __skb_to_sgvec(skb, sg, offset, len);
 }
 EXPORT_SYMBOL_GPL(skb_to_sgvec_nomark);
 
 int skb_to_sgvec(struct sk_buff *skb, struct scatterlist *sg, int offset, int len)
 {
         int nsg = __skb_to_sgvec(skb, sg, offset, len);
 
         sg_mark_end(&sg[nsg - 1]);
 
         return nsg;
 }
 EXPORT_SYMBOL_GPL(skb_to_sgvec);
 
 /**
  *      skb_cow_data - Check that a socket buffer's data buffers are writable
  *      @skb: The socket buffer to check.
  *      @tailbits: Amount of trailing space to be added
  *      @trailer: Returned pointer to the skb where the @tailbits space begins
  *
  *      Make sure that the data buffers attached to a socket buffer are
  *      writable. If they are not, private copies are made of the data buffers
  *      and the socket buffer is set to use these instead.
  *
  *      If @tailbits is given, make sure that there is space to write @tailbits
  *      bytes of data beyond current end of socket buffer.  @trailer will be
  *      set to point to the skb in which this space begins.
  *
  *      The number of scatterlist elements required to completely map the
  *      COW'd and extended socket buffer will be returned.
  */
 int skb_cow_data(struct sk_buff *skb, int tailbits, struct sk_buff **trailer)
 {
         int copyflag;
         int elt;
         struct sk_buff *skb1, **skb_p;
 
         /* If skb is cloned or its head is paged, reallocate
          * head pulling out all the pages (pages are considered not writable
          * at the moment even if they are anonymous).
          */
         if ((skb_cloned(skb) || skb_shinfo(skb)->nr_frags) &&
             __pskb_pull_tail(skb, skb_pagelen(skb)-skb_headlen(skb)) == NULL)
                 return -ENOMEM;
 
         /* Easy case. Most of packets will go this way. */
         if (!skb_has_frag_list(skb)) {
                 /* A little of trouble, not enough of space for trailer.
                  * This should not happen, when stack is tuned to generate
                  * good frames. OK, on miss we reallocate and reserve even more
                  * space, 128 bytes is fair. */
 
                 if (skb_tailroom(skb) < tailbits &&
                     pskb_expand_head(skb, 0, tailbits-skb_tailroom(skb)+128, GFP_ATOMIC))
                         return -ENOMEM;
 
                 /* Voila! */
                 *trailer = skb;
                 return 1;
         }
 
         /* Misery. We are in troubles, going to mincer fragments... */
 
         elt = 1;
         skb_p = &skb_shinfo(skb)->frag_list;
         copyflag = 0;
 
         while ((skb1 = *skb_p) != NULL) {
                 int ntail = 0;
 
                 /* The fragment is partially pulled by someone,
                  * this can happen on input. Copy it and everything
                  * after it. */
 
                 if (skb_shared(skb1))
                         copyflag = 1;
 
                 /* If the skb is the last, worry about trailer. */
 
                 if (skb1->next == NULL && tailbits) {
                         if (skb_shinfo(skb1)->nr_frags ||
                             skb_has_frag_list(skb1) ||
                             skb_tailroom(skb1) < tailbits)
                                 ntail = tailbits + 128;
                 }
 
                 if (copyflag ||
                     skb_cloned(skb1) ||
                     ntail ||
                     skb_shinfo(skb1)->nr_frags ||
                     skb_has_frag_list(skb1)) {
                         struct sk_buff *skb2;
 
                         /* Fuck, we are miserable poor guys... */
                         if (ntail == 0)
                                 skb2 = skb_copy(skb1, GFP_ATOMIC);
                         else
                                 skb2 = skb_copy_expand(skb1,
                                                        skb_headroom(skb1),
                                                        ntail,
                                                        GFP_ATOMIC);
                         if (unlikely(skb2 == NULL))
                                 return -ENOMEM;
 
                         if (skb1->sk)
                                 skb_set_owner_w(skb2, skb1->sk);
 
                         /* Looking around. Are we still alive?
                          * OK, link new skb, drop old one */
 
                         skb2->next = skb1->next;
                         *skb_p = skb2;
                         kfree_skb(skb1);
                         skb1 = skb2;
                 }
                 elt++;
                 *trailer = skb1;
                 skb_p = &skb1->next;
         }
 
         return elt;
 }
 EXPORT_SYMBOL_GPL(skb_cow_data);
 
 static void sock_rmem_free(struct sk_buff *skb)
 {
         struct sock *sk = skb->sk;
 
         atomic_sub(skb->truesize, &sk->sk_rmem_alloc);
 }
 
 /*
  * Note: We dont mem charge error packets (no sk_forward_alloc changes)
  */
 int sock_queue_err_skb(struct sock *sk, struct sk_buff *skb)
 {
         if (atomic_read(&sk->sk_rmem_alloc) + skb->truesize >=
             (unsigned int)sk->sk_rcvbuf)
                 return -ENOMEM;
 
         skb_orphan(skb);
         skb->sk = sk;
         skb->destructor = sock_rmem_free;
         atomic_add(skb->truesize, &sk->sk_rmem_alloc);
 
         /* before exiting rcu section, make sure dst is refcounted */
         skb_dst_force(skb);
 
         skb_queue_tail(&sk->sk_error_queue, skb);
         if (!sock_flag(sk, SOCK_DEAD))
                 sk->sk_data_ready(sk);
         return 0;
 }
 EXPORT_SYMBOL(sock_queue_err_skb);
 
 struct sk_buff *sock_dequeue_err_skb(struct sock *sk)
 {
         struct sk_buff_head *q = &sk->sk_error_queue;
         struct sk_buff *skb, *skb_next;
         unsigned long flags;
         int err = 0;
 
         spin_lock_irqsave(&q->lock, flags);
         skb = __skb_dequeue(q);
         if (skb && (skb_next = skb_peek(q)))
                 err = SKB_EXT_ERR(skb_next)->ee.ee_errno;
         spin_unlock_irqrestore(&q->lock, flags);
 
         sk->sk_err = err;
         if (err)
                 sk->sk_error_report(sk);
 
         return skb;
 }
 EXPORT_SYMBOL(sock_dequeue_err_skb);
 
 /**
  * skb_clone_sk - create clone of skb, and take reference to socket
  * @skb: the skb to clone
  *
  * This function creates a clone of a buffer that holds a reference on
  * sk_refcnt.  Buffers created via this function are meant to be
  * returned using sock_queue_err_skb, or free via kfree_skb.
  *
  * When passing buffers allocated with this function to sock_queue_err_skb
  * it is necessary to wrap the call with sock_hold/sock_put in order to
  * prevent the socket from being released prior to being enqueued on
  * the sk_error_queue.
  */
 struct sk_buff *skb_clone_sk(struct sk_buff *skb)
 {
         struct sock *sk = skb->sk;
         struct sk_buff *clone;
 
         if (!sk || !atomic_inc_not_zero(&sk->sk_refcnt))
                 return NULL;
 
         clone = skb_clone(skb, GFP_ATOMIC);
         if (!clone) {
                 sock_put(sk);
                 return NULL;
         }
 
         clone->sk = sk;
         clone->destructor = sock_efree;
 
         return clone;
 }
 EXPORT_SYMBOL(skb_clone_sk);
 
 static void __skb_complete_tx_timestamp(struct sk_buff *skb,
                                         struct sock *sk,
                                         int tstype)
 {
         struct sock_exterr_skb *serr;
         int err;
 
         serr = SKB_EXT_ERR(skb);
         memset(serr, 0, sizeof(*serr));
         serr->ee.ee_errno = ENOMSG;
         serr->ee.ee_origin = SO_EE_ORIGIN_TIMESTAMPING;
         serr->ee.ee_info = tstype;
         if (sk->sk_tsflags & SOF_TIMESTAMPING_OPT_ID) {
                 serr->ee.ee_data = skb_shinfo(skb)->tskey;
                 if (sk->sk_protocol == IPPROTO_TCP)
                         serr->ee.ee_data -= sk->sk_tskey;
         }
 
         err = sock_queue_err_skb(sk, skb);
 
         if (err)
                 kfree_skb(skb);
 }
 
 static bool skb_may_tx_timestamp(struct sock *sk, bool tsonly)
 {
         bool ret;
 
         if (likely(sysctl_tstamp_allow_data || tsonly))
                 return true;
 
         read_lock_bh(&sk->sk_callback_lock);
         ret = sk->sk_socket && sk->sk_socket->file &&
               file_ns_capable(sk->sk_socket->file, &init_user_ns, CAP_NET_RAW);
         read_unlock_bh(&sk->sk_callback_lock);
         return ret;
 }
 
 void skb_complete_tx_timestamp(struct sk_buff *skb,
                                struct skb_shared_hwtstamps *hwtstamps)
 {
         struct sock *sk = skb->sk;
 
         if (!skb_may_tx_timestamp(sk, false))
                 return;
 
         /* take a reference to prevent skb_orphan() from freeing the socket */
         sock_hold(sk);
 
         *skb_hwtstamps(skb) = *hwtstamps;
         __skb_complete_tx_timestamp(skb, sk, SCM_TSTAMP_SND);
 
         sock_put(sk);
 }
 EXPORT_SYMBOL_GPL(skb_complete_tx_timestamp);
 
 void __skb_tstamp_tx(struct sk_buff *orig_skb,
                      struct skb_shared_hwtstamps *hwtstamps,
                      struct sock *sk, int tstype)
 {
         struct sk_buff *skb;
         bool tsonly;
 
         if (!sk)
                 return;
 
         tsonly = sk->sk_tsflags & SOF_TIMESTAMPING_OPT_TSONLY;
         if (!skb_may_tx_timestamp(sk, tsonly))
                 return;
 
         if (tsonly)
                 skb = alloc_skb(0, GFP_ATOMIC);
         else
                 skb = skb_clone(orig_skb, GFP_ATOMIC);
         if (!skb)
                 return;
 
         if (tsonly) {
                 skb_shinfo(skb)->tx_flags = skb_shinfo(orig_skb)->tx_flags;
                 skb_shinfo(skb)->tskey = skb_shinfo(orig_skb)->tskey;
         }
 
         if (hwtstamps)
                 *skb_hwtstamps(skb) = *hwtstamps;
         else
                 skb->tstamp = ktime_get_real();
 
         __skb_complete_tx_timestamp(skb, sk, tstype);
 }
 EXPORT_SYMBOL_GPL(__skb_tstamp_tx);
 
 void skb_tstamp_tx(struct sk_buff *orig_skb,
                    struct skb_shared_hwtstamps *hwtstamps)
 {
         return __skb_tstamp_tx(orig_skb, hwtstamps, orig_skb->sk,
                                SCM_TSTAMP_SND);
 }
 EXPORT_SYMBOL_GPL(skb_tstamp_tx);
 
 void skb_complete_wifi_ack(struct sk_buff *skb, bool acked)
 {
         struct sock *sk = skb->sk;
         struct sock_exterr_skb *serr;
         int err;
 
         skb->wifi_acked_valid = 1;
         skb->wifi_acked = acked;
 
         serr = SKB_EXT_ERR(skb);
         memset(serr, 0, sizeof(*serr));
         serr->ee.ee_errno = ENOMSG;
         serr->ee.ee_origin = SO_EE_ORIGIN_TXSTATUS;
 
         /* take a reference to prevent skb_orphan() from freeing the socket */
         sock_hold(sk);
 
         err = sock_queue_err_skb(sk, skb);
         if (err)
                 kfree_skb(skb);
 
         sock_put(sk);
 }
 EXPORT_SYMBOL_GPL(skb_complete_wifi_ack);
 
 /**
  * skb_partial_csum_set - set up and verify partial csum values for packet
  * @skb: the skb to set
  * @start: the number of bytes after skb->data to start checksumming.
  * @off: the offset from start to place the checksum.
  *
  * For untrusted partially-checksummed packets, we need to make sure the values
  * for skb->csum_start and skb->csum_offset are valid so we don't oops.
  *
  * This function checks and sets those values and skb->ip_summed: if this
  * returns false you should drop the packet.
  */
 bool skb_partial_csum_set(struct sk_buff *skb, u16 start, u16 off)
 {
         if (unlikely(start > skb_headlen(skb)) ||
             unlikely((int)start + off > skb_headlen(skb) - 2)) {
                 net_warn_ratelimited("bad partial csum: csum=%u/%u len=%u\n",
                                      start, off, skb_headlen(skb));
                 return false;
         }
         skb->ip_summed = CHECKSUM_PARTIAL;
         skb->csum_start = skb_headroom(skb) + start;
         skb->csum_offset = off;
         skb_set_transport_header(skb, start);
         return true;
 }
 EXPORT_SYMBOL_GPL(skb_partial_csum_set);
 
 static int skb_maybe_pull_tail(struct sk_buff *skb, unsigned int len,
                                unsigned int max)
 {
         if (skb_headlen(skb) >= len)
                 return 0;
 
         /* If we need to pullup then pullup to the max, so we
          * won't need to do it again.
          */
         if (max > skb->len)
                 max = skb->len;
 
         if (__pskb_pull_tail(skb, max - skb_headlen(skb)) == NULL)
                 return -ENOMEM;
 
         if (skb_headlen(skb) < len)
                 return -EPROTO;
 
         return 0;
 }
 
 #define MAX_TCP_HDR_LEN (15 * 4)
 
 static __sum16 *skb_checksum_setup_ip(struct sk_buff *skb,
                                       typeof(IPPROTO_IP) proto,
                                       unsigned int off)
 {
         switch (proto) {
                 int err;
 
         case IPPROTO_TCP:
                 err = skb_maybe_pull_tail(skb, off + sizeof(struct tcphdr),
                                           off + MAX_TCP_HDR_LEN);
                 if (!err && !skb_partial_csum_set(skb, off,
                                                   offsetof(struct tcphdr,
                                                            check)))
                         err = -EPROTO;
                 return err ? ERR_PTR(err) : &tcp_hdr(skb)->check;
 
         case IPPROTO_UDP:
                 err = skb_maybe_pull_tail(skb, off + sizeof(struct udphdr),
                                           off + sizeof(struct udphdr));
                 if (!err && !skb_partial_csum_set(skb, off,
                                                   offsetof(struct udphdr,
                                                            check)))
                         err = -EPROTO;
                 return err ? ERR_PTR(err) : &udp_hdr(skb)->check;
         }
 
         return ERR_PTR(-EPROTO);
 }
 
 /* This value should be large enough to cover a tagged ethernet header plus
  * maximally sized IP and TCP or UDP headers.
  */
 #define MAX_IP_HDR_LEN 128
 
 static int skb_checksum_setup_ipv4(struct sk_buff *skb, bool recalculate)
 {
         unsigned int off;
         bool fragment;
         __sum16 *csum;
         int err;
 
         fragment = false;
 
         err = skb_maybe_pull_tail(skb,
                                   sizeof(struct iphdr),
                                   MAX_IP_HDR_LEN);
         if (err < 0)
                 goto out;
 
         if (ip_hdr(skb)->frag_off & htons(IP_OFFSET | IP_MF))
                 fragment = true;
 
         off = ip_hdrlen(skb);
 
         err = -EPROTO;
 
         if (fragment)
                 goto out;
 
         csum = skb_checksum_setup_ip(skb, ip_hdr(skb)->protocol, off);
         if (IS_ERR(csum))
                 return PTR_ERR(csum);
 
         if (recalculate)
                 *csum = ~csum_tcpudp_magic(ip_hdr(skb)->saddr,
                                            ip_hdr(skb)->daddr,
                                            skb->len - off,
                                            ip_hdr(skb)->protocol, 0);
         err = 0;
 
 out:
         return err;
 }
 
 /* This value should be large enough to cover a tagged ethernet header plus
  * an IPv6 header, all options, and a maximal TCP or UDP header.
  */
 #define MAX_IPV6_HDR_LEN 256
 
 #define OPT_HDR(type, skb, off) \
         (type *)(skb_network_header(skb) + (off))
 
 static int skb_checksum_setup_ipv6(struct sk_buff *skb, bool recalculate)
 {
         int err;
         u8 nexthdr;
         unsigned int off;
         unsigned int len;
         bool fragment;
         bool done;
         __sum16 *csum;
 
         fragment = false;
         done = false;
 
         off = sizeof(struct ipv6hdr);
 
         err = skb_maybe_pull_tail(skb, off, MAX_IPV6_HDR_LEN);
         if (err < 0)
                 goto out;
 
         nexthdr = ipv6_hdr(skb)->nexthdr;
 
         len = sizeof(struct ipv6hdr) + ntohs(ipv6_hdr(skb)->payload_len);
         while (off <= len && !done) {
                 switch (nexthdr) {
                 case IPPROTO_DSTOPTS:
                 case IPPROTO_HOPOPTS:
                 case IPPROTO_ROUTING: {
                         struct ipv6_opt_hdr *hp;
 
                         err = skb_maybe_pull_tail(skb,
                                                   off +
                                                   sizeof(struct ipv6_opt_hdr),
                                                   MAX_IPV6_HDR_LEN);
                         if (err < 0)
                                 goto out;
 
                         hp = OPT_HDR(struct ipv6_opt_hdr, skb, off);
                         nexthdr = hp->nexthdr;
                         off += ipv6_optlen(hp);
                         break;
                 }
                 case IPPROTO_AH: {
                         struct ip_auth_hdr *hp;
 
                         err = skb_maybe_pull_tail(skb,
                                                   off +
                                                   sizeof(struct ip_auth_hdr),
                                                   MAX_IPV6_HDR_LEN);
                         if (err < 0)
                                 goto out;
 
                         hp = OPT_HDR(struct ip_auth_hdr, skb, off);
                         nexthdr = hp->nexthdr;
                         off += ipv6_authlen(hp);
                         break;
                 }
                 case IPPROTO_FRAGMENT: {
                         struct frag_hdr *hp;
 
                         err = skb_maybe_pull_tail(skb,
                                                   off +
                                                   sizeof(struct frag_hdr),
                                                   MAX_IPV6_HDR_LEN);
                         if (err < 0)
                                 goto out;
 
                         hp = OPT_HDR(struct frag_hdr, skb, off);
 
                         if (hp->frag_off & htons(IP6_OFFSET | IP6_MF))
                                 fragment = true;
 
                         nexthdr = hp->nexthdr;
                         off += sizeof(struct frag_hdr);
                         break;
                 }
                 default:
                         done = true;
                         break;
                 }
         }
 
         err = -EPROTO;
 
         if (!done || fragment)
                 goto out;
 
         csum = skb_checksum_setup_ip(skb, nexthdr, off);
         if (IS_ERR(csum))
                 return PTR_ERR(csum);
 
         if (recalculate)
                 *csum = ~csum_ipv6_magic(&ipv6_hdr(skb)->saddr,
                                          &ipv6_hdr(skb)->daddr,
                                          skb->len - off, nexthdr, 0);
         err = 0;
 
 out:
         return err;
 }
 
 /**
  * skb_checksum_setup - set up partial checksum offset
  * @skb: the skb to set up
  * @recalculate: if true the pseudo-header checksum will be recalculated
  */
 int skb_checksum_setup(struct sk_buff *skb, bool recalculate)
 {
         int err;
 
         switch (skb->protocol) {
         case htons(ETH_P_IP):
                 err = skb_checksum_setup_ipv4(skb, recalculate);
                 break;
 
         case htons(ETH_P_IPV6):
                 err = skb_checksum_setup_ipv6(skb, recalculate);
                 break;
 
         default:
                 err = -EPROTO;
                 break;
         }
 
         return err;
 }
 EXPORT_SYMBOL(skb_checksum_setup);
 
 void __skb_warn_lro_forwarding(const struct sk_buff *skb)
 {
         net_warn_ratelimited("%s: received packets cannot be forwarded while LRO is enabled\n",
                              skb->dev->name);
 }
 EXPORT_SYMBOL(__skb_warn_lro_forwarding);
 
 void kfree_skb_partial(struct sk_buff *skb, bool head_stolen)
 {
         if (head_stolen) {
                 skb_release_head_state(skb);
                 kmem_cache_free(skbuff_head_cache, skb);
         } else {
                 __kfree_skb(skb);
         }
 }
 EXPORT_SYMBOL(kfree_skb_partial);
 
 /**
  * skb_try_coalesce - try to merge skb to prior one
  * @to: prior buffer
  * @from: buffer to add
  * @fragstolen: pointer to boolean
  * @delta_truesize: how much more was allocated than was requested
  */
 bool skb_try_coalesce(struct sk_buff *to, struct sk_buff *from,
                       bool *fragstolen, int *delta_truesize)
 {
         int i, delta, len = from->len;
 
         *fragstolen = false;
 
         if (skb_cloned(to))
                 return false;
 
         if (len <= skb_tailroom(to)) {
                 if (len)
                         BUG_ON(skb_copy_bits(from, 0, skb_put(to, len), len));
                 *delta_truesize = 0;
                 return true;
         }
 
         if (skb_has_frag_list(to) || skb_has_frag_list(from))
                 return false;
 
         if (skb_headlen(from) != 0) {
                 struct page *page;
                 unsigned int offset;
 
                 if (skb_shinfo(to)->nr_frags +
                     skb_shinfo(from)->nr_frags >= MAX_SKB_FRAGS)
                         return false;
 
                 if (skb_head_is_locked(from))
                         return false;
 
                 delta = from->truesize - SKB_DATA_ALIGN(sizeof(struct sk_buff));
 
                 page = virt_to_head_page(from->head);
                 offset = from->data - (unsigned char *)page_address(page);
 
                 skb_fill_page_desc(to, skb_shinfo(to)->nr_frags,
                                    page, offset, skb_headlen(from));
                 *fragstolen = true;
         } else {
                 if (skb_shinfo(to)->nr_frags +
                     skb_shinfo(from)->nr_frags > MAX_SKB_FRAGS)
                         return false;
 
                 delta = from->truesize - SKB_TRUESIZE(skb_end_offset(from));
         }
 
         WARN_ON_ONCE(delta < len);
 
         memcpy(skb_shinfo(to)->frags + skb_shinfo(to)->nr_frags,
                skb_shinfo(from)->frags,
                skb_shinfo(from)->nr_frags * sizeof(skb_frag_t));
         skb_shinfo(to)->nr_frags += skb_shinfo(from)->nr_frags;
 
         if (!skb_cloned(from))
                 skb_shinfo(from)->nr_frags = 0;
 
         /* if the skb is not cloned this does nothing
          * since we set nr_frags to 0.
          */
         for (i = 0; i < skb_shinfo(from)->nr_frags; i++)
                 skb_frag_ref(from, i);
 
         to->truesize += delta;
         to->len += len;
         to->data_len += len;
 
         *delta_truesize = delta;
         return true;
 }
 EXPORT_SYMBOL(skb_try_coalesce);
 
 /**
  * skb_scrub_packet - scrub an skb
  *
  * @skb: buffer to clean
  * @xnet: packet is crossing netns
  *
  * skb_scrub_packet can be used after encapsulating or decapsulting a packet
  * into/from a tunnel. Some information have to be cleared during these
  * operations.
  * skb_scrub_packet can also be used to clean a skb before injecting it in
  * another namespace (@xnet == true). We have to clear all information in the
  * skb that could impact namespace isolation.
  */
 void skb_scrub_packet(struct sk_buff *skb, bool xnet)
 {
         skb->tstamp.tv64 = 0;
         skb->pkt_type = PACKET_HOST;
         skb->skb_iif = 0;
         skb->ignore_df = 0;
         skb_dst_drop(skb);
         skb_sender_cpu_clear(skb);
         secpath_reset(skb);
         nf_reset(skb);
         nf_reset_trace(skb);
 
         if (!xnet)
                 return;
 
         skb_orphan(skb);
         skb->mark = 0;
 }
 EXPORT_SYMBOL_GPL(skb_scrub_packet);
 
 /**
  * skb_gso_transport_seglen - Return length of individual segments of a gso packet
  *
  * @skb: GSO skb
  *
  * skb_gso_transport_seglen is used to determine the real size of the
  * individual segments, including Layer4 headers (TCP/UDP).
  *
  * The MAC/L2 or network (IP, IPv6) headers are not accounted for.
  */
 unsigned int skb_gso_transport_seglen(const struct sk_buff *skb)
 {
         const struct skb_shared_info *shinfo = skb_shinfo(skb);
         unsigned int thlen = 0;
 
         if (skb->encapsulation) {
                 thlen = skb_inner_transport_header(skb) -
                         skb_transport_header(skb);
 
                 if (likely(shinfo->gso_type & (SKB_GSO_TCPV4 | SKB_GSO_TCPV6)))
                         thlen += inner_tcp_hdrlen(skb);
         } else if (likely(shinfo->gso_type & (SKB_GSO_TCPV4 | SKB_GSO_TCPV6))) {
                 thlen = tcp_hdrlen(skb);
         }
         /* UFO sets gso_size to the size of the fragmentation
          * payload, i.e. the size of the L4 (UDP) header is already
          * accounted for.
          */
         return thlen + shinfo->gso_size;
 }
 EXPORT_SYMBOL_GPL(skb_gso_transport_seglen);
 
 static struct sk_buff *skb_reorder_vlan_header(struct sk_buff *skb)
 {
         if (skb_cow(skb, skb_headroom(skb)) < 0) {
                 kfree_skb(skb);
                 return NULL;
         }
 
         memmove(skb->data - ETH_HLEN, skb->data - VLAN_ETH_HLEN, 2 * ETH_ALEN);
         skb->mac_header += VLAN_HLEN;
         return skb;
 }
 
 struct sk_buff *skb_vlan_untag(struct sk_buff *skb)
 {
         struct vlan_hdr *vhdr;
         u16 vlan_tci;
 
         if (unlikely(skb_vlan_tag_present(skb))) {
                 /* vlan_tci is already set-up so leave this for another time */
                 return skb;
         }
 
         skb = skb_share_check(skb, GFP_ATOMIC);
         if (unlikely(!skb))
                 goto err_free;
 
         if (unlikely(!pskb_may_pull(skb, VLAN_HLEN)))
                 goto err_free;
 
         vhdr = (struct vlan_hdr *)skb->data;
         vlan_tci = ntohs(vhdr->h_vlan_TCI);
         __vlan_hwaccel_put_tag(skb, skb->protocol, vlan_tci);
 
         skb_pull_rcsum(skb, VLAN_HLEN);
         vlan_set_encap_proto(skb, vhdr);
 
         skb = skb_reorder_vlan_header(skb);
         if (unlikely(!skb))
                 goto err_free;
 
         skb_reset_network_header(skb);
         skb_reset_transport_header(skb);
         skb_reset_mac_len(skb);
 
         return skb;
 
 err_free:
         kfree_skb(skb);
         return NULL;
 }
 EXPORT_SYMBOL(skb_vlan_untag);
 
 int skb_ensure_writable(struct sk_buff *skb, int write_len)
 {
         if (!pskb_may_pull(skb, write_len))
                 return -ENOMEM;
 
         if (!skb_cloned(skb) || skb_clone_writable(skb, write_len))
                 return 0;
 
         return pskb_expand_head(skb, 0, 0, GFP_ATOMIC);
 }
 EXPORT_SYMBOL(skb_ensure_writable);
 
 /* remove VLAN header from packet and update csum accordingly. */
 static int __skb_vlan_pop(struct sk_buff *skb, u16 *vlan_tci)
 {
         struct vlan_hdr *vhdr;
         unsigned int offset = skb->data - skb_mac_header(skb);
         int err;
 
         __skb_push(skb, offset);
         err = skb_ensure_writable(skb, VLAN_ETH_HLEN);
         if (unlikely(err))
                 goto pull;
 
         skb_postpull_rcsum(skb, skb->data + (2 * ETH_ALEN), VLAN_HLEN);
 
         vhdr = (struct vlan_hdr *)(skb->data + ETH_HLEN);
         *vlan_tci = ntohs(vhdr->h_vlan_TCI);
 
         memmove(skb->data + VLAN_HLEN, skb->data, 2 * ETH_ALEN);
         __skb_pull(skb, VLAN_HLEN);
 
         vlan_set_encap_proto(skb, vhdr);
         skb->mac_header += VLAN_HLEN;
 
         if (skb_network_offset(skb) < ETH_HLEN)
                 skb_set_network_header(skb, ETH_HLEN);
 
         skb_reset_mac_len(skb);
 pull:
         __skb_pull(skb, offset);
 
         return err;
 }
 
 int skb_vlan_pop(struct sk_buff *skb)
 {
         u16 vlan_tci;
         __be16 vlan_proto;
         int err;
 
         if (likely(skb_vlan_tag_present(skb))) {
                 skb->vlan_tci = 0;
         } else {
                 if (unlikely((skb->protocol != htons(ETH_P_8021Q) &&
                               skb->protocol != htons(ETH_P_8021AD)) ||
                              skb->len < VLAN_ETH_HLEN))
                         return 0;
 
                 err = __skb_vlan_pop(skb, &vlan_tci);
                 if (err)
                         return err;
         }
         /* move next vlan tag to hw accel tag */
         if (likely((skb->protocol != htons(ETH_P_8021Q) &&
                     skb->protocol != htons(ETH_P_8021AD)) ||
                    skb->len < VLAN_ETH_HLEN))
                 return 0;
 
         vlan_proto = skb->protocol;
         err = __skb_vlan_pop(skb, &vlan_tci);
         if (unlikely(err))
                 return err;
 
         __vlan_hwaccel_put_tag(skb, vlan_proto, vlan_tci);
         return 0;
 }
 EXPORT_SYMBOL(skb_vlan_pop);
 
 int skb_vlan_push(struct sk_buff *skb, __be16 vlan_proto, u16 vlan_tci)
 {
         if (skb_vlan_tag_present(skb)) {
                 unsigned int offset = skb->data - skb_mac_header(skb);
                 int err;
 
                 /* __vlan_insert_tag expect skb->data pointing to mac header.
                  * So change skb->data before calling it and change back to
                  * original position later
                  */
                 __skb_push(skb, offset);
                 err = __vlan_insert_tag(skb, skb->vlan_proto,
                                         skb_vlan_tag_get(skb));
                 if (err)
                         return err;
                 skb->protocol = skb->vlan_proto;
                 skb->mac_len += VLAN_HLEN;
                 __skb_pull(skb, offset);
 
                 if (skb->ip_summed == CHECKSUM_COMPLETE)
                         skb->csum = csum_add(skb->csum, csum_partial(skb->data
                                         + (2 * ETH_ALEN), VLAN_HLEN, 0));
         }
         __vlan_hwaccel_put_tag(skb, vlan_proto, vlan_tci);
         return 0;
 }
 EXPORT_SYMBOL(skb_vlan_push);
 
 /**
  * alloc_skb_with_frags - allocate skb with page frags
  *
  * @header_len: size of linear part
  * @data_len: needed length in frags
  * @max_page_order: max page order desired.
  * @errcode: pointer to error code if any
  * @gfp_mask: allocation mask
  *
  * This can be used to allocate a paged skb, given a maximal order for frags.
  */
 struct sk_buff *alloc_skb_with_frags(unsigned long header_len,
                                      unsigned long data_len,
                                      int max_page_order,
                                      int *errcode,
                                      gfp_t gfp_mask)
 {
         int npages = (data_len + (PAGE_SIZE - 1)) >> PAGE_SHIFT;
         unsigned long chunk;
         struct sk_buff *skb;
         struct page *page;
         gfp_t gfp_head;
         int i;
 
         *errcode = -EMSGSIZE;
         /* Note this test could be relaxed, if we succeed to allocate
          * high order pages...
          */
         if (npages > MAX_SKB_FRAGS)
                 return NULL;
 
         gfp_head = gfp_mask;
         if (gfp_head & __GFP_WAIT)
                 gfp_head |= __GFP_REPEAT;
 
         *errcode = -ENOBUFS;
         skb = alloc_skb(header_len, gfp_head);
         if (!skb)
                 return NULL;
 
         skb->truesize += npages << PAGE_SHIFT;
 
         for (i = 0; npages > 0; i++) {
                 int order = max_page_order;
 
                 while (order) {
                         if (npages >= 1 << order) {
                                 page = alloc_pages((gfp_mask & ~__GFP_WAIT) |
                                                    __GFP_COMP |
                                                    __GFP_NOWARN |
                                                    __GFP_NORETRY,
                                                    order);
                                 if (page)
                                         goto fill_page;
                                 /* Do not retry other high order allocations */
                                 order = 1;
                                 max_page_order = 0;
                         }
                         order--;
                 }
                 page = alloc_page(gfp_mask);
                 if (!page)
                         goto failure;
 fill_page:
                 chunk = min_t(unsigned long, data_len,
                               PAGE_SIZE << order);
                 skb_fill_page_desc(skb, i, page, 0, chunk);
                 data_len -= chunk;
                 npages -= 1 << order;
         }
         return skb;
 
 failure:
         kfree_skb(skb);
         return NULL;
 }
 EXPORT_SYMBOL(alloc_skb_with_frags);
 
```
