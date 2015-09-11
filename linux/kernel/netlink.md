
netlink是linux内核提供的一种用户空间与内核通讯基础组件, 基于网络实现, 可实现多播、单播、组播复杂的通讯功能. 内核驱动建立服务端, 用户程序通过socket绑定服务端, 可发送消息与接收消息, 实现监听、系统调用等功能. 其中generic netlink(genetlink)是基于netlink机制实现的一种通用协议, 可直接使用到一般用户程序环境中. 

##Netlink

Netlink 是一种特殊的 socket, 它是 Linux 所特有的, 类似于 BSD 中的 AF_ROUTE 但又远比它的功能强大,
目前在最新的 Linux 内核(2.6.14)中使用 netlink 进行应用与内核通信的应用很多, 包括: 

* 路由 daemon(NETLINK_ROUTE)
* 1-wire 子系统(NETLINK_W1)
* 用户态 socket 协议(NETLINK_USERSOCK),
* 防火墙(NETLINK_FIREWALL)
* socket 监视(NETLINK_INET_DIAG)
* netfilter
* 日志(NETLINK_NFLOG)
* ipsec 安全策略(NETLINK_XFRM)
* SELinux 事件通知(NETLINK_SELINUX)
* iSCSI 子系统(NETLINK_ISCSI)
* 进程审计(NETLINK_AUDIT)
* 转发信息表查询 (NETLINK_FIB_LOOKUP)
* netlink connector(NETLINK_CONNECTOR)
* netfilter 子系统(NETLINK_NETFILTER)
* IPv6 防火墙(NETLINK_IP6_FW)
* DECnet 路由信息(NETLINK_DNRTMSG)
* 内核事件向用户态通知(NETLINK_KOBJECT_UEVENT)
* 通用 netlink(NETLINK_GENERIC).

Netlink 是一种在内核与用户应用间进行双向数据传输的非常好的方式, 用户态应用使用标准的 socket API 就可以
使用 netlink 提供的强大功能, 内核态需要使用专门的内核 API 来使用 netlink.

Netlink 相对于系统调用, ioctl 以及 /proc 文件系统而言具有以下优点:

为了使用 netlink, 用户仅需要在 include/linux/netlink.h 中增加一个新类型的 netlink 协议定义即可,  如

    #define NETLINK_MYTEST 17

然后, 内核和用户态应用就可以立即通过 socket API 使用该 netlink 协议类型进行数据交换. 但系统调用需要增加
新的系统调用, ioctl 则需要增加设备或文件,  那需要不少代码, proc 文件系统则需要在 /proc 下添加新的文件或
目录, 那将使本来就混乱的 /proc 更加混乱.

netlink 是一种异步通信机制, 在内核与用户态应用之间传递的消息保存在 socket 缓存队列中, 发送消息只是把消息
保存在接收者的 socket 的接收队列, 而不需要等待接收者收到消息, 但系统调用与 ioctl 则是同步通信机制, 如果传
递的数据太长, 将影响调度粒度.

使用 netlink 的内核部分可以采用模块的方式实现, 使用 netlink 的应用部分和内核部分没有编译时依赖, 但系统调
用就有依赖, 而且新的系统调用的实现必须静态地连接到内核中, 它无法在模块中实现, 使用新系统调用的应用在编译
时需要依赖内核.

netlink 支持多播, 内核模块或应用可以把消息多播给一个 netlink 组, 属于该 neilink 组的任何内核模块或应用都
能接收到该消息, 内核事件向用户态的通知机制就使用了这一特性, 任何对内核事件感兴趣的应用都能收到该子系统发
送的内核事件, 在后面的文章中将介绍这一机制的使用.

内核可以使用 netlink 首先发起会话, 但系统调用和 ioctl 只能由用户应用发起调用.

netlink 使用标准的 socket API, 因此很容易使用, 但系统调用和 ioctl则需要专门的培训才能使用.

##用户态使用 netlink

用户态应用使用标准的 socket APIs,  socket(), bind(), sendmsg(), recvmsg() 和 close() 就能很容易地使用
netlink socket, 查询手册页可以了解这些函数的使用细节, 本文只是讲解使用 netlink 的用户应该如何使用这些
函数. 注意, 使用 netlink 的应用必须包含头文件 linux/netlink.h. 当然 socket 需要的头文件也必不可少, sys/socket.h.

为了创建一个 netlink socket, 用户需要使用如下参数调用 socket():

```
    socket(AF_NETLINK, SOCK_RAW, netlink_type)
```

第一个参数必须是 AF_NETLINK 或 PF_NETLINK, 在 Linux 中, 它们俩实际为一个东西, 它表示要使用 netlink;
第二个参数必须是 SOCK_RAW 或 SOCK_DGRAM;
第三个参数指定 netlink 协议类型, 如前面讲的用户自定义协议类型 NETLINK_MYTEST;

NETLINK_GENERIC 是一个通用的协议类型, 它是专门为用户使用的, 因此, 用户可以直接使用它, 而不必再添加新的协议类型.
内核预定义的协议类 型有:

```
    #define NETLINK_ROUTE 0 /* Routing/device hook */
    #define NETLINK_W1 1 /* 1-wire subsystem */
    #define NETLINK_USERSOCK 2 /* Reserved for user mode socket protocols */
    #define NETLINK_FIREWALL 3 /* Firewalling hook */
    #define NETLINK_INET_DIAG 4 /* INET socket monitoring */
    #define NETLINK_NFLOG 5 /* netfilter/iptables ULOG */
    #define NETLINK_XFRM 6 /* ipsec */
    #define NETLINK_SELINUX 7 /* SELinux event notifications */
    #define NETLINK_ISCSI 8 /* Open-iSCSI */
    #define NETLINK_AUDIT 9 /* auditing */
    #define NETLINK_FIB_LOOKUP 10
    #define NETLINK_CONNECTOR 11
    #define NETLINK_NETFILTER 12 /* netfilter subsystem */
    #define NETLINK_IP6_FW 13
    #define NETLINK_DNRTMSG 14 /* DECnet routing messages */
    #define NETLINK_KOBJECT_UEVENT 15 /* Kernel messages to userspace */
    #define NETLINK_GENERIC 16
```

对于每一个 netlink 协议类型, 可以有多达 32 多播组, 每一个多播组用一个位表示, netlink 的多播特性使得发送消息给同一个
组仅需要一次系统调用, 因而对于需要多拨消息的应用而言, 大大地降低了系统调用的次数.

函数 bind()用于把一个打开的 netlink socket 与 netlink 源 socket 地址绑定在一起. netlink socket 的地址结构如下:

```
    struct sockaddr_nl
    {
        sa_family_t nl_family;
        unsigned short nl_pad;
        __u32 nl_pid;
        __u32 nl_groups;
    };
```

* nl_family : 必须设置为 AF_NETLINK 或着 PF_NETLINK;
* nl_pad    : 当前没有使用, 因此要总是设置为 0;
* nl_pid    : 为接收或发送消息的进程的 ID, 如果希望内核处理消息或多播消息, 就把该字段设置为 0, 否则设置为处理消息的进程 ID.
* nl_groups : 用于指定多播组, bind 函数用于把调用进程加入到该字段指定的多播组, 如果设置为 0, 表示调用者不加入任何多播组.

传递给 bind 函数的地址的 nl_pid 字段应当设置为本进程的进程 ID, 这相当于 netlink socket 的本地地址. 但是, 对于一个进程的多个
线程使用 netlink socket 的情况, 字段 nl_pid 则可以设置为其它的值, 如:

```
    pthread_self()<< 16 | getpid();
```

因此字段 nl_pid 实际上未必是进程 ID, 它只是用于区分不同的接收者或发送者的一个标识, 用户可以根据自己需要设置该字段. 函数
bind 的调用方式如下:

```
    bind(fd, (struct sockaddr*)&nladdr, sizeof(struct sockaddr_nl));
```

fd      : 前面的 socket 调用返回的文件描述符;
nladdr  : struct sockaddr_nl 类型的地址.;

为了发送一个 netlink 消息给内核或其他用户态应用, 需要填充目标 netlink socket 地址, 此时, 字段 nl_pid 和 nl_groups 分别表
示接收消息者的进程 ID 与多播组. 如果字段 nl_pid 设置为 0, 表示消息接收者为内核或多播组, 如果 nl_groups为 0, 表示该消息为
单播消息, 否则表示多播消息.

使用函数 sendmsg 发送 netlink 消息时还需要引用结构 struct msghdr, struct nlmsghdr 和 struct iovec, 结构 struct msghdr 需如下设置:

```
    struct msghdr msg;
    memset(&msg, 0, sizeof(msg));
    msg.msg_name = (void *)&(nladdr);
    msg.msg_namelen = sizeof(nladdr);
```

其中 nladdr 为消息接收者的 netlink 地址.

struct nlmsghdr 为 netlink socket 自己的消息头, 这用于多路复用和多路分解 netlink 定义的所有协议类型以及其它一些控制, netlink
的内核实现将利用这个消息头来多路复用和多路分解已经其它的一些控制, 因此它也被称为 netlink 控制块. 因此, 应用在发送 netlink 消息
时必须提供该消息头.

```
    struct nlmsghdr
    {
        __u32 nlmsg_len; /* Length of message */
        __u16 nlmsg_type; /* Message type*/
        __u16 nlmsg_flags; /* Additional flags */
        __u32 nlmsg_seq; /* Sequence number */
        __u32 nlmsg_pid; /* Sending process PID */
    };
```

nlmsg_len  : 指定消息的总长度, 包括紧跟该结构的数据部分长度以及该结构的大小;
nlmsg_type : 用于应用内部定义消息的类型, 它对 netlink 内核实现是透明的, 因此大部分情况下设置为 0;
nlmsg_flags: 用于设置消息标志, 可用的标志包括:

```
    /* Flags values */
    #define NLM_F_REQUEST 1 /* It is request message. */
    #define NLM_F_MULTI 2 /* Multipart message, terminated by NLMSG_DONE */
    #define NLM_F_ACK 4 /* Reply with ack, with zero or error code */
    #define NLM_F_ECHO 8 /* Echo this request */
    /* Modifiers to GET request */
    #define NLM_F_ROOT 0x100 /* specify tree root */
    #define NLM_F_MATCH 0x200 /* return all matching */
    #define NLM_F_ATOMIC 0x400 /* atomic GET */
    #define NLM_F_DUMP (NLM_F_ROOT|NLM_F_MATCH)
    /* Modifiers to NEW request */
    #define NLM_F_REPLACE 0x100 /* Override existing */
    #define NLM_F_EXCL 0x200 /* Do not touch, if it exists */
    #define NLM_F_CREATE 0x400 /* Create, if it does not exist */
    #define NLM_F_APPEND 0x800 /* Add to end of list */


    NLM_F_REQUEST   用于表示消息是一个请求, 所有应用首先发起的消息都应设置该标志.
    NLM_F_MULTI     用于指示该消息是一个多部分消息的一部分, 后续的消息可以通过宏 NLMSG_NEXT 来获得.
    NLM_F_ACK       表示该消息是前一个请求消息的响应, 顺序号与进程ID可以把请求与响应关联起来.
    NLM_F_ECHO      表示该消息是相关的一个包的回传.
    NLM_F_ROOT      被许多 netlink 协议的各种数据获取操作使用, 该标志指示被请求的数据表应当整体返回用户应用,
                    而不是一个条目一个条目地返回. 有该标志的请求通常导致响应消息设置 NLM_F_MULTI 标志. 注意,
                    当设置了该标志时, 请求是协议特定的, 因此, 需要在字段 nlmsg_type 中指定协议类型.

    NLM_F_MATCH     表示该协议特定的请求只需要一个数据子集, 数据子集由指定的协议特定的过滤器来匹配.
    NLM_F_ATOMIC    指示请求返回的数据应当原子地收集, 这预防数据在获取期间被修改.
    NLM_F_DUMP      未实现.
    NLM_F_REPLACE   用于取代在数据表中的现有条目.
    NLM_F_EXCL_     用于和 CREATE 和 APPEND 配合使用, 如果条目已经存在, 将失败.
    NLM_F_CREATE    指示应当在指定的表中创建一个条目.
    NLM_F_APPEND    指示在表末尾添加新的条目.
```

内核需要读取和修改这些标志, 对于一般的使用, 用户把它设置为 0 就可以, 只是一些高级应用(如 netfilter 和路由 daemon
需要它进行一些复杂的操作), 字段 nlmsg_seq 和 nlmsg_pid 用于应用追踪消息, 前者表示顺序号, 后者为消息来源进程 ID.

下面是一个示例:

```
    #define MAX_MSGSIZE 1024
    char buffer[] = "An example message";
    struct nlmsghdr nlhdr;
    nlhdr = (struct nlmsghdr *)malloc(NLMSG_SPACE(MAX_MSGSIZE));
    strcpy(NLMSG_DATA(nlhdr), buffer);
    nlhdr->nlmsg_len = NLMSG_LENGTH(strlen(buffer));
    nlhdr->nlmsg_pid = getpid(); /* self pid */
    nlhdr->nlmsg_flags = 0;
```

结构 struct iovec 用于把多个消息通过一次系统调用来发送, 下面是该结构使用示例:

```
    struct iovec iov;
    iov.iov_base = (void *)nlhdr;
    iov.iov_len = nlh->nlmsg_len;
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
```

在完成以上步骤后, 消息就可以通过下面语句直接发送:

```
    sendmsg(fd, &msg, 0);
```

应用接收消息时需要首先分配一个足够大的缓存来保存消息头以及消息的数据部分, 然后填充消息头, 添完后就可以直接调用函数 recvmsg()来接收.

```
    #define MAX_NL_MSG_LEN 1024
    struct sockaddr_nl nladdr;
    struct msghdr msg;
    struct iovec iov;
    struct nlmsghdr * nlhdr;
    nlhdr = (struct nlmsghdr *)malloc(MAX_NL_MSG_LEN);
    iov.iov_base = (void *)nlhdr;
    iov.iov_len = MAX_NL_MSG_LEN;
    msg.msg_name = (void *)&(nladdr);
    msg.msg_namelen = sizeof(nladdr);
    msg.msg_iov = &iov;
    msg.msg_iovlen = 1;
    recvmsg(fd, &msg, 0);
```

注意: fd 为 socket 调用打开的 netlink socket 描述符.

在消息接收后, nlhdr 指向接收到的消息的消息头, nladdr 保存了接收到的消息的目标地址, 宏 NLMSG_DATA(nlhdr) 返回指向消息的数据部分的指针.

在 linux/netlink.h 中定义了一些方便对消息进行处理的宏, 这些宏包括:

```
    #define NLMSG_ALIGNTO 4
    #define NLMSG_ALIGN(len)    (((len)+NLMSG_ALIGNTO-1)& ~(NLMSG_ALIGNTO-1))
```

宏 NLMSG_ALIGN(len) 用于得到不小于 len 且字节对齐的最小数值.

```
    #define NLMSG_LENGTH(len)   ((len)+NLMSG_ALIGN(sizeof(struct nlmsghdr)))
```

宏 NLMSG_LENGTH(len) 用于计算数据部分长度为 len 时实际的消息长度. 它一般用于分配消息缓存.

```
    #define NLMSG_SPACE(len)    NLMSG_ALIGN(NLMSG_LENGTH(len))
```

宏 NLMSG_SPACE(len) 返回不小于 NLMSG_LENGTH(len) 且字节对齐的最小数值, 它也用于分配消息缓存.


```
    #define NLMSG_DATA(nlh)((void*)(((char*)nlh)+ NLMSG_LENGTH(0)))
```

宏 NLMSG_DATA(nlh) 用于取得消息的数据部分的首地址, 设置和读取消息数据部分时需要使用该宏.

```
    #define NLMSG_NEXT(nlh,len) ((len)-= NLMSG_ALIGN((nlh)->nlmsg_len), \
        (struct nlmsghdr*)(((char*)(nlh))+ NLMSG_ALIGN((nlh)->nlmsg_len)))
```

宏 NLMSG_NEXT(nlh,len) 用于得到下一个消息的首地址, 同时 len 也减少为剩余消息的总长度, 该宏
一般在一个消息被分成几个部分发送或接收时使用.

```
    #define NLMSG_OK(nlh,len)((len)>= (int)sizeof(struct nlmsghdr)&& \
        (nlh)->nlmsg_len >= sizeof(struct nlmsghdr)&& \
        (nlh)->nlmsg_len <= (len))
```

宏 NLMSG_OK(nlh,len) 用于判断消息是否有len这么长.


```
    #define NLMSG_PAYLOAD(nlh,len)((nlh)->nlmsg_len - NLMSG_SPACE((len)))
```

宏 NLMSG_PAYLOAD(nlh,len) 用于返回 payload 的长度.

函数 close 用于关闭打开的 netlink socket.

##netlink 内核 API

netlink 的内核实现在文件 net/core/af_netlink.c 中, 内核模块要想使用 netlink, 也必须包含头文件 linux/netlink.h.
内核使用 netlink 需要专门的 API, 这完全不同于用户态应用对 netlink 的使用. 如果用户需要增加新的 netlink协议类型,
必须通过修改linux/netlink.h 来实现, 当然, 目前的 netlink 实现已经包含了一个通用的协议类型 NETLINK_GENERIC 以方
便用户使用, 用户可以直接使用它而不必增加新的协议类型. 前面讲到, 为了增加新的 netlink 协议类型, 用户仅需增加如下
定义到 linux/netlink.h 就可以:

```
    #define NETLINK_MYTEST 17
```

只要增加这个定义之后, 用户就可以在内核的任何地方引用该协议.

在内核中, 为了创建一个 netlink socket 用户需要调用如下函数:

```
struct sock * netlink_kernel_create(int unit, void (*input)(struct sock *sk, int len));
```

* unit    表示netlink协议类型, 如 NETLINK_MYTEST;
* input   为内核模块定义的 netlink 消息处理函数, 当有消息到达这个 netlink socket 时, 该 input 函数指针就会被引用.
        函数指针 input 的参数 sk 实际上就是函数 netlink_kernel_create 返回的 struct sock 指针, sock 实际是 socket
        的一个内核表示数据结构, 用户态应用创建的 socket 在内核中也会有一个 struct sock 结构来表示.

下面是一个 input 函数的示例:


```
    void input (struct sock *sk, int len)
    {
        struct sk_buff *skb;
        struct nlmsghdr *nlh = NULL;
        u8 *data = NULL;
        while ((skb = skb_dequeue(&sk->receive_queue)) != NULL) {
            /* process netlink message pointed by skb->data */
            nlh = (struct nlmsghdr *)skb->data;
            data = NLMSG_DATA(nlh);
            /* process netlink message with header pointed by
            * nlh and data pointed by data
            */
        }
    }
```

函数 input() 会在发送进程执行 sendmsg() 时被调用, 这样处理消息比较及时, 但是, 如果消息特别长时, 这样处理将增加系统调用
sendmsg()的执行时间, 对于这种情况, 可以定义一个内核线程专门负责消息接收, 而函数 input 的工作只是唤醒该内核线程, 这样
sendmsg 将很快返回.

函数 skb = skb_dequeue(&sk->receive_queue) 用于取得 socket sk 的接收队列上的消息, 返回为一个 struct sk_buff 的结构,
skb->data 指向实际的 netlink 消息.

函数 skb_recv_datagram(nl_sk) 也用于在 netlink socket nl_sk 上接收消息, 与 skb_dequeue 的不同指出是, 如果 socket 的接收
队列上没有消息, 它将导致调用进程睡眠在等待队列 nl_sk->sk_sleep, 因此它必须在进程上下文使用, 刚才讲的内核线程就可以采用
这种方式来接收消息.

下面的函数 input 就是这种使用的示例:

```
    void input (struct sock *sk, int len)
    {
        wake_up_interruptible(sk->sk_sleep);
    }
```

当内核中发送 netlink 消息时, 也需要设置目标地址与源地址, 而且内核中消息是通过 struct sk_buff 来管理的,  linux/netlink.h
中定义了一个宏:

```
    #define NETLINK_CB(skb)     (*(struct netlink_skb_parms*)&((skb)->cb))
```

来方便消息的地址设置. 下面是一个消息地址设置的例子: 

```
    NETLINK_CB(skb).pid = 0;
    NETLINK_CB(skb).dst_pid = 0;
    NETLINK_CB(skb).dst_group = 1;
```

pid     : 表示消息发送者进程ID, 也即源地址, 对于内核, 它为 0;
dst_pid : 表示消息接收者进程ID, 也即目标地址, 如果目标为组或内核, 它设置为 0, 否则 dst_group 表示目标组地址, 如果它目标为
          某一进程或内核, dst_group 应当设置为 0.

在内核中, 模块调用函数 netlink_unicast 来发送单播消息:

```
    int netlink_unicast(struct sock *sk, struct sk_buff *skb, u32 pid, int nonblock);
```

* sk       : 为函数 netlink_kernel_create() 返回的 socket;
* skb      : 存放消息, 它的 data 字段指向要发送的 netlink 消息结构, 而 skb 的控制块保存了消息的地址信息, 前面的宏 NETLINK_CB(skb)
*            就用于方便设置该控制块;
* pid      : 为接收消息进程的pid;
* nonblock : 表示该函数是否为非阻塞, 如果为1, 该函数将在没有接收缓存可利用时立即返回, 而如果为0, 该函数在没有接收缓存可利用时睡眠.

内核模块或子系统也可以使用函数 netlink_broadcast 来发送广播消息:

```
    void netlink_broadcast(struct sock *sk, struct sk_buff *skb, u32 pid, u32 group, int allocation);
```

前面的三个参数与netlink_unicast相同, 

* group       为接收消息的多播组, 该参数的每一个代表一个多播组, 因此如果发送给多个多播组, 就把该参数设置为多个多播组组 ID 的位或.
* allocation  为内核内存分配类型, 一般地为 GFP_ATOMIC 或 GFP_KERNEL, GFP_ATOMIC 用于原子的上下文(即不可以睡眠), 而 GFP_KERNEL 用于非原子上下文.

在内核中使用函数 sock_release 来释放函数 netlink_kernel_create() 创建的netlink socket:

```
    void sock_release(struct socket * sock);
```

注意函数 netlink_kernel_create() 返回的类型为struct sock, 因此函数 sock_release 应该这种调用:

```
    sock_release(sk->sk_socket);
```

sk  为函数 netlink_kernel_create() 的返回值.




##通用协议

###内核

注册接口: 用于通知内核有一个 family 添加, 可提供服务

```
    ret = genl_register_family(&detect_family);     //注册family
    if (ret != 0)
            return ret;

    ret = genl_register_ops(&detect_family, &user_pid_ops); //family 相关的操作函数
    if (ret != 0)
            goto unreg_fam;
```

接口数据结构定义: family类型对应的操作接口, 可定义多个, 但cmd字段不同

```
    static struct genl_ops user_pid_ops = {
            .cmd = 0x01,
            .flags = 0,
            .policy = user_msg_policy,
            .doit = set_user_pid,
            .dumpit = NULL,
    };
```

操作接口用于响应消息, 用户给内核发送命令时需指定命令号 cmd, 发送的内容格式为 policy 指定, 其他字段程序中没用到.
同一 family 可注册多个命令, 不同命令对应各自的处理函数 doit.

```
    static struct genl_family detect_family = {
            .id = GENL_ID_GENERATE,
            .hdrsize = 0,
            .name = "DETECT_USB",
            .version = 0x01,
            .maxattr = DETECT_A_MAX,
    };
```

协议结构, 使用 genl 接口的 id 统一为 GENL_ID_GENERATE, name 字段用于标识特定的 family, 用户程序通过比较该字段连接到
family.  此处用于响应用户消息的接口只接收用户进程的 pid, 之后内核会将消息发送到该 pid 进程

内核消息发送接口: 将指定消息发送到用户进程, 消息是一个 32 位整数, 消息的定义内核与用户程序要一致

```
    skb = genlmsg_new(size, GFP_KERNEL);    //申请发送数据缓冲
    if (skb == NULL)
            goto end;

    //使用family协议发送数据, 填充协议头
    msg_head = genlmsg_put(skb, 0, 0, &detect_family, 0x01);
    if (msg_head == NULL) {
            nlmsg_free(skb);
            goto end;
    }

    if (nla_put_u32(skb, DETECT_A_UINT32, event->event) < 0) {
            nlmsg_free(skb);
            goto end;
    }

    if (genlmsg_end(skb, msg_head) < 0) {
            nlmsg_free(skb);
            goto end;
    }

    genlmsg_unicast(&init_net, skb, g_detect->user_pid);

```

在建立 socket 连接后内核可随时向用户空间发送消息, 用户程序调用 recv 接收.

###用户

基于 netlink 通讯的用户程序类似 socket 程序, 都是创建 socket, 绑定端口号, 发送和接收数据等操作.
用户守护进程阻塞接收内核消息, 再调用消息处理函数分发消息.

创建socket并绑定:  创建一个 netlink 类型的socket

```
    struct sockaddr_nl local;

    fd = socket(AF_NETLINK, SOCK_RAW, NETLINK_GENERIC);
    if (fd < 0)
        return -1;

    memset(&local, 0, sizeof(local));
    local.nl_family = AF_NETLINK;
    local.nl_groups = 0;
    if (bind(fd, (struct sockaddr *)&local, sizeof(local)) < 0)
         goto error;

    return fd;
```

创建 NETLINK_GENERIC 类型 socket, 绑定端口.

查找 DETECT_USB 服务端, 这部分属于 genetlink 公用部分.

```
    family_req.n.nlmsg_type = GENL_ID_CTRL;
    family_req.n.nlmsg_flags = NLM_F_REQUEST;
    family_req.n.nlmsg_seq = 0;
    family_req.n.nlmsg_pid = getpid();
    family_req.n.nlmsg_len = NLMSG_LENGTH(GENL_HDRLEN);
    family_req.g.cmd = CTRL_CMD_GETFAMILY;
    family_req.g.version = 0x1;

    na = (struct nlattr *)GENLMSG_DATA(&family_req);
    na->nla_type = CTRL_ATTR_FAMILY_NAME;
    na->nla_len = strlen("DETECT_USB") + 1 + NLA_HDRLEN;
    strcpy(NLA_DATA(na), "DETECT_USB");

    family_req.n.nlmsg_len += NLMSG_ALIGN(na->nla_len);

    if (sendto_fd(sd, (char *)&family_req, family_req.n.nlmsg_len) < 0)
            return -1;

    rep_len = recv(sd, &ans, sizeof(ans), 0);
    if (rep_len < 0)
            return -1;

    na = (struct nlattr *)GENLMSG_DATA(&ans);

    na = (struct nlattr *)((char *)na + NLA_ALIGN(na->nla_len));
    if (na->nla_type == CTRL_ATTR_FAMILY_ID)
            id = *(__u16 *) NLA_DATA(na);
```

这里查找使用的字符串必须与内核中注册接口结构中定义的字符串相同, 用于绑定到我们注册的接口.

发送消息相关程序: 用户程序初始化时运行一次, 用于将自己的 pid 通知到内核

```
    req.n.nlmsg_len = NLMSG_LENGTH(GENL_HDRLEN);
    req.n.nlmsg_type = id;
    req.n.nlmsg_flags = NLM_F_REQUEST;
    req.n.nlmsg_seq = 0;
    req.n.nlmsg_pid = getpid();
    req.g.cmd = 1;

    na = (struct nlattr *)GENLMSG_DATA(&req);
    na->nla_type = 1;                        //DETECT_A_MSG, 消息格式类型
    snprintf(message, 63, "usb detect deamon setup with pid %d", getpid());
    na->nla_len = 64 + NLA_HDRLEN;
    memcpy(NLA_DATA(na), message, 64);
    req.n.nlmsg_len += NLMSG_ALIGN(na->nla_len);

    memset(&nladdr, 0, sizeof(nladdr));
    nladdr.nl_family = AF_NETLINK;

    sendto(sd, (char *)&req, req.n.nlmsg_len, 0, (struct sockaddr *)&nladdr, sizeof(nladdr));
```

接收消息相关接口: 这里放在一个循环里来做, 也可以用poll实现

```
    rep_len = recv(sd, &ans, sizeof(ans), 0);  //阻塞接收内核消息
    if (ans.n.nlmsg_type == NLMSG_ERROR)
            return -1;

    if (rep_len < 0)
            return -1;

    if (!NLMSG_OK((&ans.n), rep_len))
            return -1;

    na = (struct nlattr *)GENLMSG_DATA(&ans);   //验证正确后做消息解析. 
```

##参考

https://en.wikipedia.org/wiki/Netlink
http://www.tuicool.com/articles/7fmYFb
http://www.linuxjournal.com/article/7356?page=0,0

附录

```
  /* netlink.c */
#ifndef _UAPI__LINUX_NETLINK_H
#define _UAPI__LINUX_NETLINK_H

#include <linux/kernel.h>
#include <linux/socket.h> /* for __kernel_sa_family_t */
#include <linux/types.h>

#define NETLINK_ROUTE           0       /* Routing/device hook                          */
#define NETLINK_UNUSED          1       /* Unused number                                */
#define NETLINK_USERSOCK        2       /* Reserved for user mode socket protocols      */
#define NETLINK_FIREWALL        3       /* Unused number, formerly ip_queue             */
#define NETLINK_SOCK_DIAG       4       /* socket monitoring                            */
#define NETLINK_NFLOG           5       /* netfilter/iptables ULOG */
#define NETLINK_XFRM            6       /* ipsec */
#define NETLINK_SELINUX         7       /* SELinux event notifications */
#define NETLINK_ISCSI           8       /* Open-iSCSI */
#define NETLINK_AUDIT           9       /* auditing */
#define NETLINK_FIB_LOOKUP      10
#define NETLINK_CONNECTOR       11
#define NETLINK_NETFILTER       12      /* netfilter subsystem */
#define NETLINK_IP6_FW          13
#define NETLINK_DNRTMSG         14      /* DECnet routing messages */
#define NETLINK_KOBJECT_UEVENT  15      /* Kernel messages to userspace */
#define NETLINK_GENERIC         16
/* leave room for NETLINK_DM (DM Events) */
#define NETLINK_SCSITRANSPORT   18      /* SCSI Transports */
#define NETLINK_ECRYPTFS        19
#define NETLINK_RDMA            20
#define NETLINK_CRYPTO          21      /* Crypto layer */

#define NETLINK_INET_DIAG       NETLINK_SOCK_DIAG

#define MAX_LINKS 32

struct sockaddr_nl {
        __kernel_sa_family_t    nl_family;      /* AF_NETLINK   */
        unsigned short  nl_pad;         /* zero         */
        __u32           nl_pid;         /* port ID      */
        __u32           nl_groups;      /* multicast groups mask */
};

struct nlmsghdr {
        __u32           nlmsg_len;      /* Length of message including header */
        __u16           nlmsg_type;     /* Message content */
        __u16           nlmsg_flags;    /* Additional flags */
        __u32           nlmsg_seq;      /* Sequence number */
        __u32           nlmsg_pid;      /* Sending process port ID */
};

/* Flags values */

#define NLM_F_REQUEST           1       /* It is request message.       */
#define NLM_F_MULTI             2       /* Multipart message, terminated by NLMSG_DONE */
#define NLM_F_ACK               4       /* Reply with ack, with zero or error code */
#define NLM_F_ECHO              8       /* Echo this request            */
#define NLM_F_DUMP_INTR         16      /* Dump was inconsistent due to sequence change */

/* Modifiers to GET request */
#define NLM_F_ROOT      0x100   /* specify tree root    */
#define NLM_F_MATCH     0x200   /* return all matching  */
#define NLM_F_ATOMIC    0x400   /* atomic GET           */
#define NLM_F_DUMP      (NLM_F_ROOT|NLM_F_MATCH)

/* Modifiers to NEW request */
#define NLM_F_REPLACE   0x100   /* Override existing            */
#define NLM_F_EXCL      0x200   /* Do not touch, if it exists   */
#define NLM_F_CREATE    0x400   /* Create, if it does not exist */
#define NLM_F_APPEND    0x800   /* Add to end of list           */

/*
   4.4BSD ADD           NLM_F_CREATE|NLM_F_EXCL
   4.4BSD CHANGE        NLM_F_REPLACE

   True CHANGE          NLM_F_CREATE|NLM_F_REPLACE
   Append               NLM_F_CREATE
   Check                NLM_F_EXCL
 */

#define NLMSG_ALIGNTO   4U
#define NLMSG_ALIGN(len) ( ((len)+NLMSG_ALIGNTO-1) & ~(NLMSG_ALIGNTO-1) )
#define NLMSG_HDRLEN     ((int) NLMSG_ALIGN(sizeof(struct nlmsghdr)))
#define NLMSG_LENGTH(len) ((len) + NLMSG_HDRLEN)
#define NLMSG_SPACE(len) NLMSG_ALIGN(NLMSG_LENGTH(len))
#define NLMSG_DATA(nlh)  ((void*)(((char*)nlh) + NLMSG_LENGTH(0)))
#define NLMSG_NEXT(nlh,len)      ((len) -= NLMSG_ALIGN((nlh)->nlmsg_len), \
                                  (struct nlmsghdr*)(((char*)(nlh)) + NLMSG_ALIGN((nlh)->nlmsg_len)))
#define NLMSG_OK(nlh,len) ((len) >= (int)sizeof(struct nlmsghdr) && \
                           (nlh)->nlmsg_len >= sizeof(struct nlmsghdr) && \
                           (nlh)->nlmsg_len <= (len))
#define NLMSG_PAYLOAD(nlh,len) ((nlh)->nlmsg_len - NLMSG_SPACE((len)))

#define NLMSG_NOOP              0x1     /* Nothing.             */
#define NLMSG_ERROR             0x2     /* Error                */
#define NLMSG_DONE              0x3     /* End of a dump        */
#define NLMSG_OVERRUN           0x4     /* Data lost            */

#define NLMSG_MIN_TYPE          0x10    /* < 0x10: reserved control messages */

struct nlmsgerr {
        int             error;
        struct nlmsghdr msg;
};

#define NETLINK_ADD_MEMBERSHIP  1
#define NETLINK_DROP_MEMBERSHIP 2
#define NETLINK_PKTINFO         3
#define NETLINK_BROADCAST_ERROR 4
#define NETLINK_NO_ENOBUFS      5
#define NETLINK_RX_RING         6
#define NETLINK_TX_RING         7

struct nl_pktinfo {
        __u32   group;
};

struct nl_mmap_req {
        unsigned int    nm_block_size;
        unsigned int    nm_block_nr;
        unsigned int    nm_frame_size;
        unsigned int    nm_frame_nr;
};

struct nl_mmap_hdr {
        unsigned int    nm_status;
        unsigned int    nm_len;
        __u32           nm_group;
        /* credentials */
        __u32           nm_pid;
        __u32           nm_uid;
        __u32           nm_gid;
};

enum nl_mmap_status {
        NL_MMAP_STATUS_UNUSED,
        NL_MMAP_STATUS_RESERVED,
        NL_MMAP_STATUS_VALID,
        NL_MMAP_STATUS_COPY,
        NL_MMAP_STATUS_SKIP,
};

#define NL_MMAP_MSG_ALIGNMENT           NLMSG_ALIGNTO
#define NL_MMAP_MSG_ALIGN(sz)           __ALIGN_KERNEL(sz, NL_MMAP_MSG_ALIGNMENT)
#define NL_MMAP_HDRLEN                  NL_MMAP_MSG_ALIGN(sizeof(struct nl_mmap_hdr))

#define NET_MAJOR 36            /* Major 36 is reserved for networking                                          */

enum {
        NETLINK_UNCONNECTED = 0,
        NETLINK_CONNECTED,
};

/*
 *  <------- NLA_HDRLEN ------> <-- NLA_ALIGN(payload)-->
 * +---------------------+- - -+- - - - - - - - - -+- - -+
 * |        Header       | Pad |     Payload       | Pad |
 * |   (struct nlattr)   | ing |                   | ing |
 * +---------------------+- - -+- - - - - - - - - -+- - -+
 *  <-------------- nlattr->nla_len -------------->
 */

struct nlattr {
        __u16           nla_len;
        __u16           nla_type;
};

/*
 * nla_type (16 bits)
 * +---+---+-------------------------------+
 * | N | O | Attribute Type                |
 * +---+---+-------------------------------+
 * N := Carries nested attributes
 * O := Payload stored in network byte order
 *
 * Note: The N and O flag are mutually exclusive.
 *
 * 最高位为是否有内嵌, 次低位为是否是网络字节顺序, 低 14 位为真正的属性
 */
#define NLA_F_NESTED            (1 << 15)
#define NLA_F_NET_BYTEORDER     (1 << 14)
#define NLA_TYPE_MASK           ~(NLA_F_NESTED | NLA_F_NET_BYTEORDER)

#define NLA_ALIGNTO             4
#define NLA_ALIGN(len)          (((len) + NLA_ALIGNTO - 1) & ~(NLA_ALIGNTO - 1))
#define NLA_HDRLEN              ((int) NLA_ALIGN(sizeof(struct nlattr)))


#endif /* _UAPI__LINUX_NETLINK_H */

```


```
  /* netlink.c */
#ifndef __NET_NETLINK_H
#define __NET_NETLINK_H

#include <linux/types.h>
#include <linux/netlink.h>
#include <linux/jiffies.h>
#include <linux/in6.h>

/* ========================================================================
 *         Netlink Messages and Attributes Interface (As Seen On TV)
 * ------------------------------------------------------------------------
 *                          Messages Interface
 * ------------------------------------------------------------------------
 *
 * Message Format:
 *    <--- nlmsg_total_size(payload)  --->
 *    <-- nlmsg_msg_size(payload) ->
 *   +----------+- - -+-------------+- - -+-------- - -
 *   | nlmsghdr | Pad |   Payload   | Pad | nlmsghdr
 *   +----------+- - -+-------------+- - -+-------- - -
 *   nlmsg_data(nlh)---^                   ^
 *   nlmsg_next(nlh)-----------------------+
 *
 * Payload Format:
 *    <---------------------- nlmsg_len(nlh) --------------------->
 *    <------ hdrlen ------>       <- nlmsg_attrlen(nlh, hdrlen) ->
 *   +----------------------+- - -+--------------------------------+
 *   |     Family Header    | Pad |           Attributes           |
 *   +----------------------+- - -+--------------------------------+
 *   nlmsg_attrdata(nlh, hdrlen)---^
 *
 * Data Structures:
 *   struct nlmsghdr                    netlink message header
 *
 * Message Construction:
 *   nlmsg_new()                        create a new netlink message
 *   nlmsg_put()                        add a netlink message to an skb
 *   nlmsg_put_answer()                 callback based nlmsg_put()
 *   nlmsg_end()                        finalize netlink message
 *   nlmsg_get_pos()                    return current position in message
 *   nlmsg_trim()                       trim part of message
 *   nlmsg_cancel()                     cancel message construction
 *   nlmsg_free()                       free a netlink message
 *
 * Message Sending:
 *   nlmsg_multicast()                  multicast message to several groups
 *   nlmsg_unicast()                    unicast a message to a single socket
 *   nlmsg_notify()                     send notification message
 *
 * Message Length Calculations:
 *   nlmsg_msg_size(payload)            length of message w/o padding
 *   nlmsg_total_size(payload)          length of message w/ padding
 *   nlmsg_padlen(payload)              length of padding at tail
 *
 * Message Payload Access:
 *   nlmsg_data(nlh)                    head of message payload
 *   nlmsg_len(nlh)                     length of message payload
 *   nlmsg_attrdata(nlh, hdrlen)        head of attributes data
 *   nlmsg_attrlen(nlh, hdrlen)         length of attributes data
 *
 * Message Parsing:
 *   nlmsg_ok(nlh, remaining)           does nlh fit into remaining bytes?
 *   nlmsg_next(nlh, remaining)         get next netlink message
 *   nlmsg_parse()                      parse attributes of a message
 *   nlmsg_find_attr()                  find an attribute in a message
 *   nlmsg_for_each_msg()               loop over all messages
 *   nlmsg_validate()                   validate netlink message incl. attrs
 *   nlmsg_for_each_attr()              loop over all attributes
 *
 * Misc:
 *   nlmsg_report()                     report back to application?
 *
 * ------------------------------------------------------------------------
 *                          Attributes Interface
 * ------------------------------------------------------------------------
 *
 * Attribute Format:
 *    <------- nla_total_size(payload) ------->
 *    <---- nla_attr_size(payload) ----->
 *   +----------+- - -+- - - - - - - - - +- - -+-------- - -
 *   |  Header  | Pad |     Payload      | Pad |  Header
 *   +----------+- - -+- - - - - - - - - +- - -+-------- - -
 *                     <- nla_len(nla) ->      ^
 *   nla_data(nla)----^                        |
 *   nla_next(nla)-----------------------------'
 *
 * Data Structures:
 *   struct nlattr                      netlink attribute header
 *
 * Attribute Construction:
 *   nla_reserve(skb, type, len)        reserve room for an attribute
 *   nla_reserve_nohdr(skb, len)        reserve room for an attribute w/o hdr
 *   nla_put(skb, type, len, data)      add attribute to skb
 *   nla_put_nohdr(skb, len, data)      add attribute w/o hdr
 *   nla_append(skb, len, data)         append data to skb
 *
 * Attribute Construction for Basic Types:
 *   nla_put_u8(skb, type, value)       add u8 attribute to skb
 *   nla_put_u16(skb, type, value)      add u16 attribute to skb
 *   nla_put_u32(skb, type, value)      add u32 attribute to skb
 *   nla_put_u64(skb, type, value)      add u64 attribute to skb
 *   nla_put_s8(skb, type, value)       add s8 attribute to skb
 *   nla_put_s16(skb, type, value)      add s16 attribute to skb
 *   nla_put_s32(skb, type, value)      add s32 attribute to skb
 *   nla_put_s64(skb, type, value)      add s64 attribute to skb
 *   nla_put_string(skb, type, str)     add string attribute to skb
 *   nla_put_flag(skb, type)            add flag attribute to skb
 *   nla_put_msecs(skb, type, jiffies)  add msecs attribute to skb
 *   nla_put_in_addr(skb, type, addr)   add IPv4 address attribute to skb
 *   nla_put_in6_addr(skb, type, addr)  add IPv6 address attribute to skb
 *
 * Nested Attributes Construction:
 *   nla_nest_start(skb, type)          start a nested attribute
 *   nla_nest_end(skb, nla)             finalize a nested attribute
 *   nla_nest_cancel(skb, nla)          cancel nested attribute construction
 *
 * Attribute Length Calculations:
 *   nla_attr_size(payload)             length of attribute w/o padding
 *   nla_total_size(payload)            length of attribute w/ padding
 *   nla_padlen(payload)                length of padding
 *
 * Attribute Payload Access:
 *   nla_data(nla)                      head of attribute payload
 *   nla_len(nla)                       length of attribute payload
 *
 * Attribute Payload Access for Basic Types:
 *   nla_get_u8(nla)                    get payload for a u8 attribute
 *   nla_get_u16(nla)                   get payload for a u16 attribute
 *   nla_get_u32(nla)                   get payload for a u32 attribute
 *   nla_get_u64(nla)                   get payload for a u64 attribute
 *   nla_get_s8(nla)                    get payload for a s8 attribute
 *   nla_get_s16(nla)                   get payload for a s16 attribute
 *   nla_get_s32(nla)                   get payload for a s32 attribute
 *   nla_get_s64(nla)                   get payload for a s64 attribute
 *   nla_get_flag(nla)                  return 1 if flag is true
 *   nla_get_msecs(nla)                 get payload for a msecs attribute
 *
 * Attribute Misc:
 *   nla_memcpy(dest, nla, count)       copy attribute into memory
 *   nla_memcmp(nla, data, size)        compare attribute with memory area
 *   nla_strlcpy(dst, nla, size)        copy attribute to a sized string
 *   nla_strcmp(nla, str)               compare attribute with string
 *
 * Attribute Parsing:
 *   nla_ok(nla, remaining)             does nla fit into remaining bytes?
 *   nla_next(nla, remaining)           get next netlink attribute
 *   nla_validate()                     validate a stream of attributes
 *   nla_validate_nested()              validate a stream of nested attributes
 *   nla_find()                         find attribute in stream of attributes
 *   nla_find_nested()                  find attribute in nested attributes
 *   nla_parse()                        parse and validate stream of attrs
 *   nla_parse_nested()                 parse nested attribuets
 *   nla_for_each_attr()                loop over all attributes
 *   nla_for_each_nested()              loop over the nested attributes
 *=========================================================================
 */

 /**
  * Standard attribute types to specify validation policy
  */
enum {
        NLA_UNSPEC,
        NLA_U8,
        NLA_U16,
        NLA_U32,
        NLA_U64,
        NLA_STRING,
        NLA_FLAG,
        NLA_MSECS,
        NLA_NESTED,
        NLA_NESTED_COMPAT,
        NLA_NUL_STRING,
        NLA_BINARY,
        NLA_S8,
        NLA_S16,
        NLA_S32,
        NLA_S64,
        __NLA_TYPE_MAX,
};

#define NLA_TYPE_MAX (__NLA_TYPE_MAX - 1)

/**
 * struct nla_policy - attribute validation policy
 * @type: Type of attribute or NLA_UNSPEC
 * @len: Type specific length of payload
 *
 * Policies are defined as arrays of this struct, the array must be
 * accessible by attribute type up to the highest identifier to be expected.
 *
 * Meaning of `len' field:
 *    NLA_STRING           Maximum length of string
 *    NLA_NUL_STRING       Maximum length of string (excluding NUL)
 *    NLA_FLAG             Unused
 *    NLA_BINARY           Maximum length of attribute payload
 *    NLA_NESTED           Don't use `len' field -- length verification is
 *                         done by checking len of nested header (or empty)
 *    NLA_NESTED_COMPAT    Minimum length of structure payload
 *    NLA_U8, NLA_U16,
 *    NLA_U32, NLA_U64,
 *    NLA_S8, NLA_S16,
 *    NLA_S32, NLA_S64,
 *    NLA_MSECS            Leaving the length field zero will verify the
 *                         given type fits, using it verifies minimum length
 *                         just like "All other"
 *    All other            Minimum length of attribute payload
 *
 * Example:
 * static const struct nla_policy my_policy[ATTR_MAX+1] = {
 *      [ATTR_FOO] = { .type = NLA_U16 },
 *      [ATTR_BAR] = { .type = NLA_STRING, .len = BARSIZ },
 *      [ATTR_BAZ] = { .len = sizeof(struct mystruct) },
 * };
 */
struct nla_policy {
        u16             type;
        u16             len;
};

/**
 * struct nl_info - netlink source information
 * @nlh: Netlink message header of original request
 * @portid: Netlink PORTID of requesting application
 */
struct nl_info {
        struct nlmsghdr         *nlh;
        struct net              *nl_net;
        u32                     portid;
};

int netlink_rcv_skb(struct sk_buff *skb,
                    int (*cb)(struct sk_buff *, struct nlmsghdr *));
int nlmsg_notify(struct sock *sk, struct sk_buff *skb, u32 portid,
                 unsigned int group, int report, gfp_t flags);

int nla_validate(const struct nlattr *head, int len, int maxtype,
                 const struct nla_policy *policy);
int nla_parse(struct nlattr **tb, int maxtype, const struct nlattr *head,
              int len, const struct nla_policy *policy);
int nla_policy_len(const struct nla_policy *, int);
struct nlattr *nla_find(const struct nlattr *head, int len, int attrtype);
size_t nla_strlcpy(char *dst, const struct nlattr *nla, size_t dstsize);
int nla_memcpy(void *dest, const struct nlattr *src, int count);
int nla_memcmp(const struct nlattr *nla, const void *data, size_t size);
int nla_strcmp(const struct nlattr *nla, const char *str);
struct nlattr *__nla_reserve(struct sk_buff *skb, int attrtype, int attrlen);
void *__nla_reserve_nohdr(struct sk_buff *skb, int attrlen);
struct nlattr *nla_reserve(struct sk_buff *skb, int attrtype, int attrlen);
void *nla_reserve_nohdr(struct sk_buff *skb, int attrlen);
void __nla_put(struct sk_buff *skb, int attrtype, int attrlen,
               const void *data);
void __nla_put_nohdr(struct sk_buff *skb, int attrlen, const void *data);
int nla_put(struct sk_buff *skb, int attrtype, int attrlen, const void *data);
int nla_put_nohdr(struct sk_buff *skb, int attrlen, const void *data);
int nla_append(struct sk_buff *skb, int attrlen, const void *data);

/**************************************************************************
 * Netlink Messages
 **************************************************************************/

/**
 * nlmsg_msg_size - length of netlink message not including padding
 * @payload: length of message payload
 */
static inline int nlmsg_msg_size(int payload)
{
        return NLMSG_HDRLEN + payload;
}

/**
 * nlmsg_total_size - length of netlink message including padding
 * @payload: length of message payload
 */
static inline int nlmsg_total_size(int payload)
{
        return NLMSG_ALIGN(nlmsg_msg_size(payload));
}

/**
 * nlmsg_padlen - length of padding at the message's tail
 * @payload: length of message payload
 */
static inline int nlmsg_padlen(int payload)
{
        return nlmsg_total_size(payload) - nlmsg_msg_size(payload);
}

/**
 * nlmsg_data - head of message payload
 * @nlh: netlink message header
 */
static inline void *nlmsg_data(const struct nlmsghdr *nlh)
{
        return (unsigned char *) nlh + NLMSG_HDRLEN;
}

/**
 * nlmsg_len - length of message payload
 * @nlh: netlink message header
 */
static inline int nlmsg_len(const struct nlmsghdr *nlh)
{
        return nlh->nlmsg_len - NLMSG_HDRLEN;
}

/**
 * nlmsg_attrdata - head of attributes data
 * @nlh: netlink message header
 * @hdrlen: length of family specific header
 */
static inline struct nlattr *nlmsg_attrdata(const struct nlmsghdr *nlh,
                                            int hdrlen)
{
        unsigned char *data = nlmsg_data(nlh);
        return (struct nlattr *) (data + NLMSG_ALIGN(hdrlen));
}

/**
 * nlmsg_attrlen - length of attributes data
 * @nlh: netlink message header
 * @hdrlen: length of family specific header
 */
static inline int nlmsg_attrlen(const struct nlmsghdr *nlh, int hdrlen)
{
        return nlmsg_len(nlh) - NLMSG_ALIGN(hdrlen);
}

/**
 * nlmsg_ok - check if the netlink message fits into the remaining bytes
 * @nlh: netlink message header
 * @remaining: number of bytes remaining in message stream
 */
static inline int nlmsg_ok(const struct nlmsghdr *nlh, int remaining)
{
        return (remaining >= (int) sizeof(struct nlmsghdr) &&
                nlh->nlmsg_len >= sizeof(struct nlmsghdr) &&
                nlh->nlmsg_len <= remaining);
}

/**
 * nlmsg_next - next netlink message in message stream
 * @nlh: netlink message header
 * @remaining: number of bytes remaining in message stream
 *
 * Returns the next netlink message in the message stream and
 * decrements remaining by the size of the current message.
 */
static inline struct nlmsghdr *
nlmsg_next(const struct nlmsghdr *nlh, int *remaining)
{
        int totlen = NLMSG_ALIGN(nlh->nlmsg_len);

        *remaining -= totlen;

        return (struct nlmsghdr *) ((unsigned char *) nlh + totlen);
}

/**
 * nlmsg_parse - parse attributes of a netlink message
 * @nlh: netlink message header
 * @hdrlen: length of family specific header
 * @tb: destination array with maxtype+1 elements
 * @maxtype: maximum attribute type to be expected
 * @policy: validation policy
 *
 * See nla_parse()
 */
static inline int nlmsg_parse(const struct nlmsghdr *nlh, int hdrlen,
                              struct nlattr *tb[], int maxtype,
                              const struct nla_policy *policy)
{
        if (nlh->nlmsg_len < nlmsg_msg_size(hdrlen))
                return -EINVAL;

        return nla_parse(tb, maxtype, nlmsg_attrdata(nlh, hdrlen),
                         nlmsg_attrlen(nlh, hdrlen), policy);
}

/**
 * nlmsg_find_attr - find a specific attribute in a netlink message
 * @nlh: netlink message header
 * @hdrlen: length of familiy specific header
 * @attrtype: type of attribute to look for
 *
 * Returns the first attribute which matches the specified type.
 */
static inline struct nlattr *nlmsg_find_attr(const struct nlmsghdr *nlh,
                                             int hdrlen, int attrtype)
{
        return nla_find(nlmsg_attrdata(nlh, hdrlen),
                        nlmsg_attrlen(nlh, hdrlen), attrtype);
}

/**
 * nlmsg_validate - validate a netlink message including attributes
 * @nlh: netlinket message header
 * @hdrlen: length of familiy specific header
 * @maxtype: maximum attribute type to be expected
 * @policy: validation policy
 */
static inline int nlmsg_validate(const struct nlmsghdr *nlh,
                                 int hdrlen, int maxtype,
                                 const struct nla_policy *policy)
{
        if (nlh->nlmsg_len < nlmsg_msg_size(hdrlen))
                return -EINVAL;

        return nla_validate(nlmsg_attrdata(nlh, hdrlen),
                            nlmsg_attrlen(nlh, hdrlen), maxtype, policy);
}

/**
 * nlmsg_report - need to report back to application?
 * @nlh: netlink message header
 *
 * Returns 1 if a report back to the application is requested.
 */
static inline int nlmsg_report(const struct nlmsghdr *nlh)
{
        return !!(nlh->nlmsg_flags & NLM_F_ECHO);
}

/**
 * nlmsg_for_each_attr - iterate over a stream of attributes
 * @pos: loop counter, set to current attribute
 * @nlh: netlink message header
 * @hdrlen: length of familiy specific header
 * @rem: initialized to len, holds bytes currently remaining in stream
 */
#define nlmsg_for_each_attr(pos, nlh, hdrlen, rem) \
        nla_for_each_attr(pos, nlmsg_attrdata(nlh, hdrlen), \
                          nlmsg_attrlen(nlh, hdrlen), rem)

/**
 * nlmsg_put - Add a new netlink message to an skb
 * @skb: socket buffer to store message in
 * @portid: netlink PORTID of requesting application
 * @seq: sequence number of message
 * @type: message type
 * @payload: length of message payload
 * @flags: message flags
 *
 * Returns NULL if the tailroom of the skb is insufficient to store
 * the message header and payload.
 */
static inline struct nlmsghdr *nlmsg_put(struct sk_buff *skb, u32 portid, u32 seq,
                                         int type, int payload, int flags)
{
        if (unlikely(skb_tailroom(skb) < nlmsg_total_size(payload)))
                return NULL;

        return __nlmsg_put(skb, portid, seq, type, payload, flags);
}

/**
 * nlmsg_put_answer - Add a new callback based netlink message to an skb
 * @skb: socket buffer to store message in
 * @cb: netlink callback
 * @type: message type
 * @payload: length of message payload
 * @flags: message flags
 *
 * Returns NULL if the tailroom of the skb is insufficient to store
 * the message header and payload.
 */
static inline struct nlmsghdr *nlmsg_put_answer(struct sk_buff *skb,
                                                struct netlink_callback *cb,
                                                int type, int payload,
                                                int flags)
{
        return nlmsg_put(skb, NETLINK_CB(cb->skb).portid, cb->nlh->nlmsg_seq,
                         type, payload, flags);
}

/**
 * nlmsg_new - Allocate a new netlink message
 * @payload: size of the message payload
 * @flags: the type of memory to allocate.
 *
 * Use NLMSG_DEFAULT_SIZE if the size of the payload isn't known
 * and a good default is needed.
 */
static inline struct sk_buff *nlmsg_new(size_t payload, gfp_t flags)
{
        return alloc_skb(nlmsg_total_size(payload), flags);
}

/**
 * nlmsg_end - Finalize a netlink message
 * @skb: socket buffer the message is stored in
 * @nlh: netlink message header
 *
 * Corrects the netlink message header to include the appeneded
 * attributes. Only necessary if attributes have been added to
 * the message.
 */
static inline void nlmsg_end(struct sk_buff *skb, struct nlmsghdr *nlh)
{
        nlh->nlmsg_len = skb_tail_pointer(skb) - (unsigned char *)nlh;
}

/**
 * nlmsg_get_pos - return current position in netlink message
 * @skb: socket buffer the message is stored in
 *
 * Returns a pointer to the current tail of the message.
 */
static inline void *nlmsg_get_pos(struct sk_buff *skb)
{
        return skb_tail_pointer(skb);
}

/**
 * nlmsg_trim - Trim message to a mark
 * @skb: socket buffer the message is stored in
 * @mark: mark to trim to
 *
 * Trims the message to the provided mark.
 */
static inline void nlmsg_trim(struct sk_buff *skb, const void *mark)
{
        if (mark) {
                WARN_ON((unsigned char *) mark < skb->data);
                skb_trim(skb, (unsigned char *) mark - skb->data);
        }
}

/**
 * nlmsg_cancel - Cancel construction of a netlink message
 * @skb: socket buffer the message is stored in
 * @nlh: netlink message header
 *
 * Removes the complete netlink message including all
 * attributes from the socket buffer again.
 */
static inline void nlmsg_cancel(struct sk_buff *skb, struct nlmsghdr *nlh)
{
        nlmsg_trim(skb, nlh);
}

/**
 * nlmsg_free - free a netlink message
 * @skb: socket buffer of netlink message
 */
static inline void nlmsg_free(struct sk_buff *skb)
{
        kfree_skb(skb);
}

/**
 * nlmsg_multicast - multicast a netlink message
 * @sk: netlink socket to spread messages to
 * @skb: netlink message as socket buffer
 * @portid: own netlink portid to avoid sending to yourself
 * @group: multicast group id
 * @flags: allocation flags
 */
static inline int nlmsg_multicast(struct sock *sk, struct sk_buff *skb,
                                  u32 portid, unsigned int group, gfp_t flags)
{
        int err;

        NETLINK_CB(skb).dst_group = group;

        err = netlink_broadcast(sk, skb, portid, group, flags);
        if (err > 0)
                err = 0;

        return err;
}

/**
 * nlmsg_unicast - unicast a netlink message
 * @sk: netlink socket to spread message to
 * @skb: netlink message as socket buffer
 * @portid: netlink portid of the destination socket
 */
static inline int nlmsg_unicast(struct sock *sk, struct sk_buff *skb, u32 portid)
{
        int err;

        err = netlink_unicast(sk, skb, portid, MSG_DONTWAIT);
        if (err > 0)
                err = 0;

        return err;
}

/**
 * nlmsg_for_each_msg - iterate over a stream of messages
 * @pos: loop counter, set to current message
 * @head: head of message stream
 * @len: length of message stream
 * @rem: initialized to len, holds bytes currently remaining in stream
 */
#define nlmsg_for_each_msg(pos, head, len, rem) \
        for (pos = head, rem = len; \
             nlmsg_ok(pos, rem); \
             pos = nlmsg_next(pos, &(rem)))

/**
 * nl_dump_check_consistent - check if sequence is consistent and advertise if not
 * @cb: netlink callback structure that stores the sequence number
 * @nlh: netlink message header to write the flag to
 *
 * This function checks if the sequence (generation) number changed during dump
 * and if it did, advertises it in the netlink message header.
 *
 * The correct way to use it is to set cb->seq to the generation counter when
 * all locks for dumping have been acquired, and then call this function for
 * each message that is generated.
 *
 * Note that due to initialisation concerns, 0 is an invalid sequence number
 * and must not be used by code that uses this functionality.
 */
static inline void
nl_dump_check_consistent(struct netlink_callback *cb,
                         struct nlmsghdr *nlh)
{
        if (cb->prev_seq && cb->seq != cb->prev_seq)
                nlh->nlmsg_flags |= NLM_F_DUMP_INTR;
        cb->prev_seq = cb->seq;
}

/**************************************************************************
 * Netlink Attributes
 **************************************************************************/

/**
 * nla_attr_size - length of attribute not including padding
 * @payload: length of payload
 */
static inline int nla_attr_size(int payload)
{
        return NLA_HDRLEN + payload;
}

/**
 * nla_total_size - total length of attribute including padding
 * @payload: length of payload
 */
static inline int nla_total_size(int payload)
{
        return NLA_ALIGN(nla_attr_size(payload));
}

/**
 * nla_padlen - length of padding at the tail of attribute
 * @payload: length of payload
 */
static inline int nla_padlen(int payload)
{
        return nla_total_size(payload) - nla_attr_size(payload);
}

/**
 * nla_type - attribute type
 * @nla: netlink attribute
 */
static inline int nla_type(const struct nlattr *nla)
{
        return nla->nla_type & NLA_TYPE_MASK;
}

/**
 * nla_data - head of payload
 * @nla: netlink attribute
 */
static inline void *nla_data(const struct nlattr *nla)
{
        return (char *) nla + NLA_HDRLEN;
}

/**
 * nla_len - length of payload
 * @nla: netlink attribute
 */
static inline int nla_len(const struct nlattr *nla)
{
        return nla->nla_len - NLA_HDRLEN;
}

/**
 * nla_ok - check if the netlink attribute fits into the remaining bytes
 * @nla: netlink attribute
 * @remaining: number of bytes remaining in attribute stream
 */
static inline int nla_ok(const struct nlattr *nla, int remaining)
{
        return remaining >= (int) sizeof(*nla) &&
               nla->nla_len >= sizeof(*nla) &&
               nla->nla_len <= remaining;
}

/**
 * nla_next - next netlink attribute in attribute stream
 * @nla: netlink attribute
 * @remaining: number of bytes remaining in attribute stream
 *
 * Returns the next netlink attribute in the attribute stream and
 * decrements remaining by the size of the current attribute.
 */
static inline struct nlattr *nla_next(const struct nlattr *nla, int *remaining)
{
        int totlen = NLA_ALIGN(nla->nla_len);

        *remaining -= totlen;
        return (struct nlattr *) ((char *) nla + totlen);
}

/**
 * nla_find_nested - find attribute in a set of nested attributes
 * @nla: attribute containing the nested attributes
 * @attrtype: type of attribute to look for
 *
 * Returns the first attribute which matches the specified type.
 */
static inline struct nlattr *
nla_find_nested(const struct nlattr *nla, int attrtype)
{
        return nla_find(nla_data(nla), nla_len(nla), attrtype);
}

/**
 * nla_parse_nested - parse nested attributes
 * @tb: destination array with maxtype+1 elements
 * @maxtype: maximum attribute type to be expected
 * @nla: attribute containing the nested attributes
 * @policy: validation policy
 *
 * See nla_parse()
 */
static inline int nla_parse_nested(struct nlattr *tb[], int maxtype,
                                   const struct nlattr *nla,
                                   const struct nla_policy *policy)
{
        return nla_parse(tb, maxtype, nla_data(nla), nla_len(nla), policy);
}

/**
 * nla_put_u8 - Add a u8 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_u8(struct sk_buff *skb, int attrtype, u8 value)
{
        return nla_put(skb, attrtype, sizeof(u8), &value);
}

/**
 * nla_put_u16 - Add a u16 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_u16(struct sk_buff *skb, int attrtype, u16 value)
{
        return nla_put(skb, attrtype, sizeof(u16), &value);
}

/**
 * nla_put_be16 - Add a __be16 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_be16(struct sk_buff *skb, int attrtype, __be16 value)
{
        return nla_put(skb, attrtype, sizeof(__be16), &value);
}

/**
 * nla_put_net16 - Add 16-bit network byte order netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_net16(struct sk_buff *skb, int attrtype, __be16 value)
{
        return nla_put_be16(skb, attrtype | NLA_F_NET_BYTEORDER, value);
}

/**
 * nla_put_le16 - Add a __le16 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_le16(struct sk_buff *skb, int attrtype, __le16 value)
{
        return nla_put(skb, attrtype, sizeof(__le16), &value);
}

/**
 * nla_put_u32 - Add a u32 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_u32(struct sk_buff *skb, int attrtype, u32 value)
{
        return nla_put(skb, attrtype, sizeof(u32), &value);
}

/**
 * nla_put_be32 - Add a __be32 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_be32(struct sk_buff *skb, int attrtype, __be32 value)
{
        return nla_put(skb, attrtype, sizeof(__be32), &value);
}

/**
 * nla_put_net32 - Add 32-bit network byte order netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_net32(struct sk_buff *skb, int attrtype, __be32 value)
{
        return nla_put_be32(skb, attrtype | NLA_F_NET_BYTEORDER, value);
}

/**
 * nla_put_le32 - Add a __le32 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_le32(struct sk_buff *skb, int attrtype, __le32 value)
{
        return nla_put(skb, attrtype, sizeof(__le32), &value);
}

/**
 * nla_put_u64 - Add a u64 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_u64(struct sk_buff *skb, int attrtype, u64 value)
{
        return nla_put(skb, attrtype, sizeof(u64), &value);
}

/**
 * nla_put_be64 - Add a __be64 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_be64(struct sk_buff *skb, int attrtype, __be64 value)
{
        return nla_put(skb, attrtype, sizeof(__be64), &value);
}

/**
 * nla_put_net64 - Add 64-bit network byte order netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_net64(struct sk_buff *skb, int attrtype, __be64 value)
{
        return nla_put_be64(skb, attrtype | NLA_F_NET_BYTEORDER, value);
}

/**
 * nla_put_le64 - Add a __le64 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_le64(struct sk_buff *skb, int attrtype, __le64 value)
{
        return nla_put(skb, attrtype, sizeof(__le64), &value);
}

/**
 * nla_put_s8 - Add a s8 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_s8(struct sk_buff *skb, int attrtype, s8 value)
{
        return nla_put(skb, attrtype, sizeof(s8), &value);
}

/**
 * nla_put_s16 - Add a s16 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_s16(struct sk_buff *skb, int attrtype, s16 value)
{
        return nla_put(skb, attrtype, sizeof(s16), &value);
}

/**
 * nla_put_s32 - Add a s32 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_s32(struct sk_buff *skb, int attrtype, s32 value)
{
        return nla_put(skb, attrtype, sizeof(s32), &value);
}

/**
 * nla_put_s64 - Add a s64 netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @value: numeric value
 */
static inline int nla_put_s64(struct sk_buff *skb, int attrtype, s64 value)
{
        return nla_put(skb, attrtype, sizeof(s64), &value);
}

/**
 * nla_put_string - Add a string netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @str: NUL terminated string
 */
static inline int nla_put_string(struct sk_buff *skb, int attrtype,
                                 const char *str)
{
        return nla_put(skb, attrtype, strlen(str) + 1, str);
}

/**
 * nla_put_flag - Add a flag netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 */
static inline int nla_put_flag(struct sk_buff *skb, int attrtype)
{
        return nla_put(skb, attrtype, 0, NULL);
}

/**
 * nla_put_msecs - Add a msecs netlink attribute to a socket buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @njiffies: number of jiffies to convert to msecs
 */
static inline int nla_put_msecs(struct sk_buff *skb, int attrtype,
                                unsigned long njiffies)
{
        u64 tmp = jiffies_to_msecs(njiffies);
        return nla_put(skb, attrtype, sizeof(u64), &tmp);
}

/**
 * nla_put_in_addr - Add an IPv4 address netlink attribute to a socket
 * buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @addr: IPv4 address
 */
static inline int nla_put_in_addr(struct sk_buff *skb, int attrtype,
                                  __be32 addr)
{
        return nla_put_be32(skb, attrtype, addr);
}

/**
 * nla_put_in6_addr - Add an IPv6 address netlink attribute to a socket
 * buffer
 * @skb: socket buffer to add attribute to
 * @attrtype: attribute type
 * @addr: IPv6 address
 */
static inline int nla_put_in6_addr(struct sk_buff *skb, int attrtype,
                                   const struct in6_addr *addr)
{
        return nla_put(skb, attrtype, sizeof(*addr), addr);
}

/**
 * nla_get_u32 - return payload of u32 attribute
 * @nla: u32 netlink attribute
 */
static inline u32 nla_get_u32(const struct nlattr *nla)
{
        return *(u32 *) nla_data(nla);
}

/**
 * nla_get_be32 - return payload of __be32 attribute
 * @nla: __be32 netlink attribute
  */
 static inline __be32 nla_get_be32(const struct nlattr *nla)
 {
         return *(__be32 *) nla_data(nla);
 }
 
 /**
  * nla_get_u16 - return payload of u16 attribute
  * @nla: u16 netlink attribute
  */
 static inline u16 nla_get_u16(const struct nlattr *nla)
 {
         return *(u16 *) nla_data(nla);
 }
 
 /**
  * nla_get_be16 - return payload of __be16 attribute
  * @nla: __be16 netlink attribute
  */
 static inline __be16 nla_get_be16(const struct nlattr *nla)
 {
         return *(__be16 *) nla_data(nla);
 }
 
 /**
  * nla_get_le16 - return payload of __le16 attribute
  * @nla: __le16 netlink attribute
  */
 static inline __le16 nla_get_le16(const struct nlattr *nla)
 {
         return *(__le16 *) nla_data(nla);
 }
 
 /**
  * nla_get_u8 - return payload of u8 attribute
  * @nla: u8 netlink attribute
  */
 static inline u8 nla_get_u8(const struct nlattr *nla)
 {
         return *(u8 *) nla_data(nla);
 }
 
 /**
  * nla_get_u64 - return payload of u64 attribute
  * @nla: u64 netlink attribute
  */
 static inline u64 nla_get_u64(const struct nlattr *nla)
 {
         u64 tmp;
 
         nla_memcpy(&tmp, nla, sizeof(tmp));
 
         return tmp;
 }
 
 /**
  * nla_get_be64 - return payload of __be64 attribute
  * @nla: __be64 netlink attribute
  */
 static inline __be64 nla_get_be64(const struct nlattr *nla)
 {
         __be64 tmp;
 
         nla_memcpy(&tmp, nla, sizeof(tmp));
 
         return tmp;
 }
 
 /**
  * nla_get_s32 - return payload of s32 attribute
  * @nla: s32 netlink attribute
  */
 static inline s32 nla_get_s32(const struct nlattr *nla)
 {
         return *(s32 *) nla_data(nla);
 }
 
 /**
  * nla_get_s16 - return payload of s16 attribute
  * @nla: s16 netlink attribute
  */
 static inline s16 nla_get_s16(const struct nlattr *nla)
 {
         return *(s16 *) nla_data(nla);
 }
 
 /**
  * nla_get_s8 - return payload of s8 attribute
  * @nla: s8 netlink attribute
  */
 static inline s8 nla_get_s8(const struct nlattr *nla)
 {
         return *(s8 *) nla_data(nla);
 }
 
 /**
  * nla_get_s64 - return payload of s64 attribute
  * @nla: s64 netlink attribute
  */
 static inline s64 nla_get_s64(const struct nlattr *nla)
 {
         s64 tmp;
 
         nla_memcpy(&tmp, nla, sizeof(tmp));
 
         return tmp;
 }
 
 /**
  * nla_get_flag - return payload of flag attribute
  * @nla: flag netlink attribute
  */
 static inline int nla_get_flag(const struct nlattr *nla)
 {
         return !!nla;
 }
 
 /**
  * nla_get_msecs - return payload of msecs attribute
  * @nla: msecs netlink attribute
  *
  * Returns the number of milliseconds in jiffies.
  */
 static inline unsigned long nla_get_msecs(const struct nlattr *nla)
 {
         u64 msecs = nla_get_u64(nla);
 
         return msecs_to_jiffies((unsigned long) msecs);
 }
 
 /**
  * nla_get_in_addr - return payload of IPv4 address attribute
  * @nla: IPv4 address netlink attribute
  */
 static inline __be32 nla_get_in_addr(const struct nlattr *nla)
 {
         return *(__be32 *) nla_data(nla);
 }
 
 /**
  * nla_get_in6_addr - return payload of IPv6 address attribute
  * @nla: IPv6 address netlink attribute
  */
 static inline struct in6_addr nla_get_in6_addr(const struct nlattr *nla)
 {
         struct in6_addr tmp;
 
         nla_memcpy(&tmp, nla, sizeof(tmp));
         return tmp;
 }
 
 /**
  * nla_nest_start - Start a new level of nested attributes
  * @skb: socket buffer to add attributes to
  * @attrtype: attribute type of container
  *
  * Returns the container attribute
  */
 static inline struct nlattr *nla_nest_start(struct sk_buff *skb, int attrtype)
 {
         struct nlattr *start = (struct nlattr *)skb_tail_pointer(skb);
 
         if (nla_put(skb, attrtype, 0, NULL) < 0)
                 return NULL;
 
         return start;
 }
 
 /**
  * nla_nest_end - Finalize nesting of attributes
  * @skb: socket buffer the attributes are stored in
  * @start: container attribute
  *
  * Corrects the container attribute header to include the all
  * appeneded attributes.
  *
  * Returns the total data length of the skb.
  */
 static inline int nla_nest_end(struct sk_buff *skb, struct nlattr *start)
 {
         start->nla_len = skb_tail_pointer(skb) - (unsigned char *)start;
         return skb->len;
 }
 
 /**
  * nla_nest_cancel - Cancel nesting of attributes
  * @skb: socket buffer the message is stored in
  * @start: container attribute
  *
  * Removes the container attribute and including all nested
  * attributes. Returns -EMSGSIZE
  */
 static inline void nla_nest_cancel(struct sk_buff *skb, struct nlattr *start)
 {
         nlmsg_trim(skb, start);
 }
 
 /**
  * nla_validate_nested - Validate a stream of nested attributes
  * @start: container attribute
  * @maxtype: maximum attribute type to be expected
  * @policy: validation policy
  *
  * Validates all attributes in the nested attribute stream against the
  * specified policy. Attributes with a type exceeding maxtype will be
  * ignored. See documenation of struct nla_policy for more details.
  *
  * Returns 0 on success or a negative error code.
  */
 static inline int nla_validate_nested(const struct nlattr *start, int maxtype,
                                       const struct nla_policy *policy)
 {
         return nla_validate(nla_data(start), nla_len(start), maxtype, policy);
 }
 
 /**
  * nla_for_each_attr - iterate over a stream of attributes
  * @pos: loop counter, set to current attribute
  * @head: head of attribute stream
  * @len: length of attribute stream
  * @rem: initialized to len, holds bytes currently remaining in stream
  */
 #define nla_for_each_attr(pos, head, len, rem) \
         for (pos = head, rem = len; \
              nla_ok(pos, rem); \
              pos = nla_next(pos, &(rem)))
 
 /**
  * nla_for_each_nested - iterate over nested attributes
  * @pos: loop counter, set to current attribute
  * @nla: attribute containing the nested attributes
  * @rem: initialized to len, holds bytes currently remaining in stream
  */
 #define nla_for_each_nested(pos, nla, rem) \
         nla_for_each_attr(pos, nla_data(nla), nla_len(nla), rem)
 
 /**
  * nla_is_last - Test if attribute is last in stream
  * @nla: attribute to test
  * @rem: bytes remaining in stream
  */
 static inline bool nla_is_last(const struct nlattr *nla, int rem)
 {
         return nla->nla_len == rem;
 }
 
 #endif
 
```

```
/* uapi/linux/genetlink.h */

#ifndef _UAPI__LINUX_GENERIC_NETLINK_H
#define _UAPI__LINUX_GENERIC_NETLINK_H

#include <linux/types.h>
#include <linux/netlink.h>

#define GENL_NAMSIZ     16      /* length of family name */

#define GENL_MIN_ID     NLMSG_MIN_TYPE
#define GENL_MAX_ID     1023

struct genlmsghdr {
        __u8    cmd;
        __u8    version;
        __u16   reserved;
};

#define GENL_HDRLEN     NLMSG_ALIGN(sizeof(struct genlmsghdr))

#define GENL_ADMIN_PERM         0x01
#define GENL_CMD_CAP_DO         0x02
#define GENL_CMD_CAP_DUMP       0x04
#define GENL_CMD_CAP_HASPOL     0x08

/*
 * List of reserved static generic netlink identifiers:
 */
#define GENL_ID_GENERATE        0
#define GENL_ID_CTRL            NLMSG_MIN_TYPE
#define GENL_ID_VFS_DQUOT       (NLMSG_MIN_TYPE + 1)
#define GENL_ID_PMCRAID         (NLMSG_MIN_TYPE + 2)

/**************************************************************************
 * Controller
 **************************************************************************/

enum {
        CTRL_CMD_UNSPEC,
        CTRL_CMD_NEWFAMILY,
        CTRL_CMD_DELFAMILY,
        CTRL_CMD_GETFAMILY,
        CTRL_CMD_NEWOPS,
        CTRL_CMD_DELOPS,
        CTRL_CMD_GETOPS,
        CTRL_CMD_NEWMCAST_GRP,
        CTRL_CMD_DELMCAST_GRP,
        CTRL_CMD_GETMCAST_GRP, /* unused */
        __CTRL_CMD_MAX,
};

#define CTRL_CMD_MAX (__CTRL_CMD_MAX - 1)

enum {
        CTRL_ATTR_UNSPEC,
        CTRL_ATTR_FAMILY_ID,
        CTRL_ATTR_FAMILY_NAME,
        CTRL_ATTR_VERSION,
        CTRL_ATTR_HDRSIZE,
        CTRL_ATTR_MAXATTR,
        CTRL_ATTR_OPS,
        CTRL_ATTR_MCAST_GROUPS,
        __CTRL_ATTR_MAX,
};

#define CTRL_ATTR_MAX (__CTRL_ATTR_MAX - 1)

enum {
        CTRL_ATTR_OP_UNSPEC,
        CTRL_ATTR_OP_ID,
        CTRL_ATTR_OP_FLAGS,
        __CTRL_ATTR_OP_MAX,
};

#define CTRL_ATTR_OP_MAX (__CTRL_ATTR_OP_MAX - 1)

enum {
        CTRL_ATTR_MCAST_GRP_UNSPEC,
        CTRL_ATTR_MCAST_GRP_NAME,
        CTRL_ATTR_MCAST_GRP_ID,
        __CTRL_ATTR_MCAST_GRP_MAX,
};

#define CTRL_ATTR_MCAST_GRP_MAX (__CTRL_ATTR_MCAST_GRP_MAX - 1)


#endif /* _UAPI__LINUX_GENERIC_NETLINK_H */

```


```
/* genetlink.h */
 #ifndef __NET_GENERIC_NETLINK_H
 #define __NET_GENERIC_NETLINK_H
 
 #include <linux/genetlink.h>
 #include <net/netlink.h>
 #include <net/net_namespace.h>
 
 #define GENLMSG_DEFAULT_SIZE (NLMSG_DEFAULT_SIZE - GENL_HDRLEN)
 
 /**
  * struct genl_multicast_group - generic netlink multicast group
  * @name: name of the multicast group, names are per-family
  */
 struct genl_multicast_group {
         char                    name[GENL_NAMSIZ];
 };
 
 struct genl_ops;
 struct genl_info;
 
 /**
  * struct genl_family - generic netlink family
  * @id: protocol family idenfitier
  * @hdrsize: length of user specific header in bytes
  * @name: name of family
  * @version: protocol version
  * @maxattr: maximum number of attributes supported
  * @netnsok: set to true if the family can handle network
  *      namespaces and should be presented in all of them
  * @parallel_ops: operations can be called in parallel and aren't
  *      synchronized by the core genetlink code
  * @pre_doit: called before an operation's doit callback, it may
  *      do additional, common, filtering and return an error
  * @post_doit: called after an operation's doit callback, it may
  *      undo operations done by pre_doit, for example release locks
  * @mcast_bind: a socket bound to the given multicast group (which
  *      is given as the offset into the groups array)
  * @mcast_unbind: a socket was unbound from the given multicast group.
  *      Note that unbind() will not be called symmetrically if the
  *      generic netlink family is removed while there are still open
  *      sockets.
  * @attrbuf: buffer to store parsed attributes, 当 maxattr != NULL &&
  * parallel_ops = true 时, kmalloc 分配空间, 否则为 null
  * @family_list: family list
  * @mcgrps: multicast groups used by this family (private)
  * @n_mcgrps: number of multicast groups (private)
  * @mcgrp_offset: starting number of multicast group IDs in this family
  * @ops: the operations supported by this family (private)
  * @n_ops: number of operations supported by this family (private)
  */
 struct genl_family {
         unsigned int            id;
         unsigned int            hdrsize;
         char                    name[GENL_NAMSIZ];
         unsigned int            version;
         unsigned int            maxattr;
         bool                    netnsok;
         bool                    parallel_ops;
         int                     (*pre_doit)(const struct genl_ops *ops,
                                             struct sk_buff *skb,
                                             struct genl_info *info);
         void                    (*post_doit)(const struct genl_ops *ops,
                                              struct sk_buff *skb,
                                              struct genl_info *info);
         int                     (*mcast_bind)(struct net *net, int group);
         void                    (*mcast_unbind)(struct net *net, int group);
         struct nlattr **        attrbuf;        /* private */
         const struct genl_ops * ops;            /* private */
         const struct genl_multicast_group *mcgrps; /* private */
         unsigned int            n_ops;          /* private */
         unsigned int            n_mcgrps;       /* private */
         unsigned int            mcgrp_offset;   /* private */
         struct list_head        family_list;    /* private */
         struct module           *module;
 };
 
 /**
  * struct genl_info - receiving information
  * @snd_seq: sending sequence number
  * @snd_portid: netlink portid of sender
  * @nlhdr: netlink message header
  * @genlhdr: generic netlink message header
  * @userhdr: user specific header
  * @attrs: netlink attributes
  * @_net: network namespace
  * @user_ptr: user pointers
  * @dst_sk: destination socket
  */
 struct genl_info {
         u32                     snd_seq;
         u32                     snd_portid;
         struct nlmsghdr *       nlhdr;
         struct genlmsghdr *     genlhdr;
         void *                  userhdr;
         struct nlattr **        attrs;
         possible_net_t          _net;
         void *                  user_ptr[2];
         struct sock *           dst_sk;
 };
 
 static inline struct net *genl_info_net(struct genl_info *info)
 {
         return read_pnet(&info->_net);
 }
 
 static inline void genl_info_net_set(struct genl_info *info, struct net *net)
 {
         write_pnet(&info->_net, net);
 }
 
 /**
  * struct genl_ops - generic netlink operations
  * @cmd: command identifier
  * @internal_flags: flags used by the family
  * @flags: flags
  * @policy: attribute validation policy
  * @doit: standard command callback
  * @dumpit: callback for dumpers
  * @done: completion callback for dumps
  * @ops_list: operations list
  */
 struct genl_ops {
         const struct nla_policy *policy;
         int                    (*doit)(struct sk_buff *skb,
                                        struct genl_info *info);
         int                    (*dumpit)(struct sk_buff *skb,
                                          struct netlink_callback *cb);
         int                    (*done)(struct netlink_callback *cb);
         u8                      cmd;
         u8                      internal_flags;
         u8                      flags;
 };
 
 int __genl_register_family(struct genl_family *family);
 
 static inline int genl_register_family(struct genl_family *family)
 {
         family->module = THIS_MODULE;
         return __genl_register_family(family);
 }
 
 /**
  * genl_register_family_with_ops - register a generic netlink family with ops
  * @family: generic netlink family
  * @ops: operations to be registered
  * @n_ops: number of elements to register
  *
  * Registers the specified family and operations from the specified table.
  * Only one family may be registered with the same family name or identifier.
  *
  * The family id may equal GENL_ID_GENERATE causing an unique id to
  * be automatically generated and assigned.
  *
  * Either a doit or dumpit callback must be specified for every registered
  * operation or the function will fail. Only one operation structure per
  * command identifier may be registered.
  *
  * See include/net/genetlink.h for more documenation on the operations
  * structure.
  *
  * Return 0 on success or a negative error code.
  */
 static inline int
 _genl_register_family_with_ops_grps(struct genl_family *family,
                                     const struct genl_ops *ops, size_t n_ops,
                                     const struct genl_multicast_group *mcgrps,
                                     size_t n_mcgrps)
 {
         family->module = THIS_MODULE;
         family->ops = ops;
         family->n_ops = n_ops;
         family->mcgrps = mcgrps;
         family->n_mcgrps = n_mcgrps;
         return __genl_register_family(family);
 }
 
 #define genl_register_family_with_ops(family, ops)                      \
         _genl_register_family_with_ops_grps((family),                   \
                                             (ops), ARRAY_SIZE(ops),     \
                                             NULL, 0)
 #define genl_register_family_with_ops_groups(family, ops, grps) \
         _genl_register_family_with_ops_grps((family),                   \
                                             (ops), ARRAY_SIZE(ops),     \
                                             (grps), ARRAY_SIZE(grps))
 
 int genl_unregister_family(struct genl_family *family);
 void genl_notify(struct genl_family *family,
                  struct sk_buff *skb, struct net *net, u32 portid,
                  u32 group, struct nlmsghdr *nlh, gfp_t flags);
 
 struct sk_buff *genlmsg_new_unicast(size_t payload, struct genl_info *info,
                                     gfp_t flags);
 void *genlmsg_put(struct sk_buff *skb, u32 portid, u32 seq,
                   struct genl_family *family, int flags, u8 cmd);
 
 /**
  * genlmsg_nlhdr - Obtain netlink header from user specified header
  * @user_hdr: user header as returned from genlmsg_put()
  * @family: generic netlink family
  *
  * Returns pointer to netlink header.
  */
 static inline struct nlmsghdr *genlmsg_nlhdr(void *user_hdr,
                                              struct genl_family *family)
 {
         return (struct nlmsghdr *)((char *)user_hdr -
                                    family->hdrsize -
                                    GENL_HDRLEN -
                                    NLMSG_HDRLEN);
 }
 
 /**
  * genlmsg_parse - parse attributes of a genetlink message
  * @nlh: netlink message header
  * @family: genetlink message family
  * @tb: destination array with maxtype+1 elements
  * @maxtype: maximum attribute type to be expected
  * @policy: validation policy
  * */
 static inline int genlmsg_parse(const struct nlmsghdr *nlh,
                                 const struct genl_family *family,
                                 struct nlattr *tb[], int maxtype,
                                 const struct nla_policy *policy)
 {
         return nlmsg_parse(nlh, family->hdrsize + GENL_HDRLEN, tb, maxtype,
                            policy);
 }
 
 /**
  * genl_dump_check_consistent - check if sequence is consistent and advertise if not
  * @cb: netlink callback structure that stores the sequence number
  * @user_hdr: user header as returned from genlmsg_put()
  * @family: generic netlink family
  *
  * Cf. nl_dump_check_consistent(), this just provides a wrapper to make it
  * simpler to use with generic netlink.
  */
 static inline void genl_dump_check_consistent(struct netlink_callback *cb,
                                               void *user_hdr,
                                               struct genl_family *family)
 {
         nl_dump_check_consistent(cb, genlmsg_nlhdr(user_hdr, family));
 }
 
 /**
  * genlmsg_put_reply - Add generic netlink header to a reply message
  * @skb: socket buffer holding the message
  * @info: receiver info
  * @family: generic netlink family
  * @flags: netlink message flags
  * @cmd: generic netlink command
  *
  * Returns pointer to user specific header
  */
 static inline void *genlmsg_put_reply(struct sk_buff *skb,
                                       struct genl_info *info,
                                       struct genl_family *family,
                                       int flags, u8 cmd)
 {
         return genlmsg_put(skb, info->snd_portid, info->snd_seq, family,
                            flags, cmd);
 }
 
 /**
  * genlmsg_end - Finalize a generic netlink message
  * @skb: socket buffer the message is stored in
  * @hdr: user specific header
  */
 static inline void genlmsg_end(struct sk_buff *skb, void *hdr)
 {
         nlmsg_end(skb, hdr - GENL_HDRLEN - NLMSG_HDRLEN);
 }
 
 /**
  * genlmsg_cancel - Cancel construction of a generic netlink message
  * @skb: socket buffer the message is stored in
  * @hdr: generic netlink message header
  */
 static inline void genlmsg_cancel(struct sk_buff *skb, void *hdr)
 {
         if (hdr)
                 nlmsg_cancel(skb, hdr - GENL_HDRLEN - NLMSG_HDRLEN);
 }
 
 /**
  * genlmsg_multicast_netns - multicast a netlink message to a specific netns
  * @family: the generic netlink family
  * @net: the net namespace
  * @skb: netlink message as socket buffer
  * @portid: own netlink portid to avoid sending to yourself
  * @group: offset of multicast group in groups array
  * @flags: allocation flags
  */
 static inline int genlmsg_multicast_netns(struct genl_family *family,
                                           struct net *net, struct sk_buff *skb,
                                           u32 portid, unsigned int group, gfp_t flags)
 {
         if (WARN_ON_ONCE(group >= family->n_mcgrps))
                 return -EINVAL;
         group = family->mcgrp_offset + group;
         return nlmsg_multicast(net->genl_sock, skb, portid, group, flags);
 }
 
 /**
  * genlmsg_multicast - multicast a netlink message to the default netns
  * @family: the generic netlink family
  * @skb: netlink message as socket buffer
  * @portid: own netlink portid to avoid sending to yourself
  * @group: offset of multicast group in groups array
  * @flags: allocation flags
  */
 static inline int genlmsg_multicast(struct genl_family *family,
                                     struct sk_buff *skb, u32 portid,
                                     unsigned int group, gfp_t flags)
 {
         return genlmsg_multicast_netns(family, &init_net, skb,
                                        portid, group, flags);
 }
 
 /**
  * genlmsg_multicast_allns - multicast a netlink message to all net namespaces
  * @family: the generic netlink family
  * @skb: netlink message as socket buffer
  * @portid: own netlink portid to avoid sending to yourself
  * @group: offset of multicast group in groups array
  * @flags: allocation flags
  *
  * This function must hold the RTNL or rcu_read_lock().
  */
 int genlmsg_multicast_allns(struct genl_family *family,
                             struct sk_buff *skb, u32 portid,
                             unsigned int group, gfp_t flags);
 
 /**
  * genlmsg_unicast - unicast a netlink message
  * @skb: netlink message as socket buffer
  * @portid: netlink portid of the destination socket
  */
 static inline int genlmsg_unicast(struct net *net, struct sk_buff *skb, u32 portid)
 {
         return nlmsg_unicast(net->genl_sock, skb, portid);
 }
 
 /**
  * genlmsg_reply - reply to a request
  * @skb: netlink message to be sent back
  * @info: receiver information
  */
 static inline int genlmsg_reply(struct sk_buff *skb, struct genl_info *info)
 {
         return genlmsg_unicast(genl_info_net(info), skb, info->snd_portid);
 }
 
 /**
  * gennlmsg_data - head of message payload
  * @gnlh: genetlink message header
  */
 static inline void *genlmsg_data(const struct genlmsghdr *gnlh)
 {
         return ((unsigned char *) gnlh + GENL_HDRLEN);
 }
 
 /**
  * genlmsg_len - length of message payload
  * @gnlh: genetlink message header
  */
 static inline int genlmsg_len(const struct genlmsghdr *gnlh)
 {
         struct nlmsghdr *nlh = (struct nlmsghdr *)((unsigned char *)gnlh -
                                                         NLMSG_HDRLEN);
         return (nlh->nlmsg_len - GENL_HDRLEN - NLMSG_HDRLEN);
 }
 
 /**
  * genlmsg_msg_size - length of genetlink message not including padding
  * @payload: length of message payload
  */
 static inline int genlmsg_msg_size(int payload)
 {
         return GENL_HDRLEN + payload;
 }
 
 /**
  * genlmsg_total_size - length of genetlink message including padding
  * @payload: length of message payload
  */
 static inline int genlmsg_total_size(int payload)
 {
         return NLMSG_ALIGN(genlmsg_msg_size(payload));
 }
 
 /**
  * genlmsg_new - Allocate a new generic netlink message
  * @payload: size of the message payload
  * @flags: the type of memory to allocate.
  */
 static inline struct sk_buff *genlmsg_new(size_t payload, gfp_t flags)
 {
         return nlmsg_new(genlmsg_total_size(payload), flags);
 }
 
 /**
  * genl_set_err - report error to genetlink broadcast listeners
  * @family: the generic netlink family
  * @net: the network namespace to report the error to
  * @portid: the PORTID of a process that we want to skip (if any)
  * @group: the broadcast group that will notice the error
  *      (this is the offset of the multicast group in the groups array)
  * @code: error code, must be negative (as usual in kernelspace)
  *
  * This function returns the number of broadcast listeners that have set the
  * NETLINK_RECV_NO_ENOBUFS socket option.
  */
 static inline int genl_set_err(struct genl_family *family, struct net *net,
                                u32 portid, u32 group, int code)
 {
         if (WARN_ON_ONCE(group >= family->n_mcgrps))
                 return -EINVAL;
         group = family->mcgrp_offset + group;
         return netlink_set_err(net->genl_sock, portid, group, code);
 }
 
 static inline int genl_has_listeners(struct genl_family *family,
                                      struct net *net, unsigned int group)
 {
         if (WARN_ON_ONCE(group >= family->n_mcgrps))
                 return -EINVAL;
         group = family->mcgrp_offset + group;
         return netlink_has_listeners(net->genl_sock, group);
 }
 #endif  /* __NET_GENERIC_NETLINK_H */
 
```

```
/* genetlink.c */
/*
 * NETLINK      Generic Netlink Family
 *
 *              Authors:        Jamal Hadi Salim
 *                              Thomas Graf <tgraf@suug.ch>
 *                              Johannes Berg <johannes@sipsolutions.net>
 *
 * 所有 genl_family 都存在一个 GENL_FAM_TAB_SIZE 大小的数组 list_head family_ht 中
 * 每个元素是 list_head, 即每个元素是一个双向的链表
 *
 *
 *
 *
 *
 */

#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/slab.h>
#include <linux/errno.h>
#include <linux/types.h>
#include <linux/socket.h>
#include <linux/string.h>
#include <linux/skbuff.h>
#include <linux/mutex.h>
#include <linux/bitmap.h>
#include <linux/rwsem.h>
#include <net/sock.h>
#include <net/genetlink.h>

static DEFINE_MUTEX(genl_mutex); /* serialization of message processing */
static DECLARE_RWSEM(cb_lock);

atomic_t genl_sk_destructing_cnt = ATOMIC_INIT(0);
DECLARE_WAIT_QUEUE_HEAD(genl_sk_destructing_waitq);

void genl_lock(void)
{
        mutex_lock(&genl_mutex);
}
EXPORT_SYMBOL(genl_lock);

void genl_unlock(void)
{
        mutex_unlock(&genl_mutex);
}
EXPORT_SYMBOL(genl_unlock);

#ifdef CONFIG_LOCKDEP
int lockdep_genl_is_held(void)
{
        return lockdep_is_held(&genl_mutex);
}
EXPORT_SYMBOL(lockdep_genl_is_held);
#endif

static void genl_lock_all(void)
{
        down_write(&cb_lock);
        genl_lock();
}

static void genl_unlock_all(void)
{
        genl_unlock();
        up_write(&cb_lock);
}

#define GENL_FAM_TAB_SIZE       16
#define GENL_FAM_TAB_MASK       (GENL_FAM_TAB_SIZE - 1)

static struct list_head family_ht[GENL_FAM_TAB_SIZE];
/*
 * Bitmap of multicast groups that are currently in use.
 *
 * To avoid an allocation at boot of just one unsigned long,
 * declare it global instead.
 * Bit 0 is marked as already used since group 0 is invalid.
 * Bit 1 is marked as already used since the drop-monitor code
 * abuses the API and thinks it can statically use group 1.
 * That group will typically conflict with other groups that
 * any proper users use.
 * Bit 16 is marked as used since it's used for generic netlink
 * and the code no longer marks pre-reserved IDs as used.
 * Bit 17 is marked as already used since the VFS quota code
 * also abused this API and relied on family == group ID, we
 * cater to that by giving it a static family and group ID.
 * Bit 18 is marked as already used since the PMCRAID driver
 * did the same thing as the VFS quota code (maybe copied?)
 */
static unsigned long mc_group_start = 0x3 | BIT(GENL_ID_CTRL) |
                                      BIT(GENL_ID_VFS_DQUOT) |
                                      BIT(GENL_ID_PMCRAID);
static unsigned long *mc_groups = &mc_group_start;
static unsigned long mc_groups_longs = 1;

static int genl_ctrl_event(int event, struct genl_family *family,
                           const struct genl_multicast_group *grp,
                           int grp_id);

//相当与 对 id / GENL_FAM_TAB_MASK(15) 取余
static inline unsigned int genl_family_hash(unsigned int id)
{
        return id & GENL_FAM_TAB_MASK;
}

static inline struct list_head *genl_family_chain(unsigned int id)
{
        return &family_ht[genl_family_hash(id)];
}

/*
 * 如果从 family_ht 所有列表中找到 genl_family->id 为 id 的 genl_family, 返回对应 id
 * 否则返回 NULL
 */
static struct genl_family *genl_family_find_byid(unsigned int id)
{
        struct genl_family *f;

        list_for_each_entry(f, genl_family_chain(id), family_list)
                if (f->id == id)
                        return f;

        return NULL;
}

/*
 * 遍历 family_ht 所有列表, 找出 genl_family->name 为 name 的元素
 /
static struct genl_family *genl_family_find_byname(char *name)
{
        struct genl_family *f;
        int i;

        for (i = 0; i < GENL_FAM_TAB_SIZE; i++)
                list_for_each_entry(f, genl_family_chain(i), family_list)
                        if (strcmp(f->name, name) == 0)
                                return f;

        return NULL;
}

static const struct genl_ops *genl_get_cmd(u8 cmd, struct genl_family *family)
{
        int i;

        for (i = 0; i < family->n_ops; i++)
                if (family->ops[i].cmd == cmd)
                        return &family->ops[i];

        return NULL;
}

/* Of course we are going to have problems once we hit
 * 2^16 alive types, but that can only happen by year 2K
 *
 * 分配 id 为 GENL_MIN_ID(19) ~ 1023 之间的值, 从 16 开始递增, 直到没有被使用, 返回该 id
 * 如果 18 ~ 1023 都被使用返回 0
*/
static u16 genl_generate_id(void)
{
        static u16 id_gen_idx = GENL_MIN_ID;
        int i;

        for (i = 0; i <= GENL_MAX_ID - GENL_MIN_ID; i++) {
                if (id_gen_idx != GENL_ID_VFS_DQUOT &&
                    id_gen_idx != GENL_ID_PMCRAID &&
                    !genl_family_find_byid(id_gen_idx))
                        return id_gen_idx;
                if (++id_gen_idx > GENL_MAX_ID)
                        id_gen_idx = GENL_MIN_ID;
        }

        return 0;
}

static int genl_allocate_reserve_groups(int n_groups, int *first_id)
{
        unsigned long *new_groups;
        int start = 0;
        int i;
        int id;
        bool fits;

        do {
                if (start == 0)
                        id = find_first_zero_bit(mc_groups,
                                                 mc_groups_longs *
                                                 BITS_PER_LONG);
                else
                        id = find_next_zero_bit(mc_groups,
                                                mc_groups_longs * BITS_PER_LONG,
                                                start);

                fits = true;
                for (i = id;
                     i < min_t(int, id + n_groups,
                               mc_groups_longs * BITS_PER_LONG);
                     i++) {
                        if (test_bit(i, mc_groups)) {
                                start = i;
                                fits = false;
                                break;
                        }
                }

                if (id >= mc_groups_longs * BITS_PER_LONG) {
                        unsigned long new_longs = mc_groups_longs +
                                                  BITS_TO_LONGS(n_groups);
                        size_t nlen = new_longs * sizeof(unsigned long);

                        if (mc_groups == &mc_group_start) {
                                new_groups = kzalloc(nlen, GFP_KERNEL);
                                if (!new_groups)
                                        return -ENOMEM;
                                mc_groups = new_groups;
                                *mc_groups = mc_group_start;
                        } else {
                                new_groups = krealloc(mc_groups, nlen,
                                                      GFP_KERNEL);
                                if (!new_groups)
                                        return -ENOMEM;
                                mc_groups = new_groups;
                                for (i = 0; i < BITS_TO_LONGS(n_groups); i++)
                                        mc_groups[mc_groups_longs + i] = 0;
                        }
                        mc_groups_longs = new_longs;
                }
        } while (!fits);

        for (i = id; i < id + n_groups; i++)
                set_bit(i, mc_groups);
        *first_id = id;
        return 0;
}

static struct genl_family genl_ctrl;

/*
 * family->mcgrps 每个元素的 name 必须不能仅包含 '\0' 但以 '\0' 结束
 * 如果 family = &genl_ctrl, family->mcgrp_offset = GENL_ID_CTRL
 *      family->name = NET_DM, family->mcgrp_offset = 1
 *      family->id = GENL_ID_VFS_DQUOT, family->mcgrp_offset = GENL_ID_VFS_DQUOT
 * 否则 分配 family->n_mcgrps 个
 */
static int genl_validate_assign_mc_groups(struct genl_family *family)
{
        int first_id;
        int n_groups = family->n_mcgrps;
        int err = 0, i;
        bool groups_allocated = false;

        if (!n_groups)
                return 0;

        for (i = 0; i < n_groups; i++) {
                const struct genl_multicast_group *grp = &family->mcgrps[i];

                if (WARN_ON(grp->name[0] == '\0'))
                        return -EINVAL;
                if (WARN_ON(memchr(grp->name, '\0', GENL_NAMSIZ) == NULL))
                        return -EINVAL;
        }

        /* special-case our own group and hacks */
        if (family == &genl_ctrl) {
                first_id = GENL_ID_CTRL;
                BUG_ON(n_groups != 1);
        } else if (strcmp(family->name, "NET_DM") == 0) {
                first_id = 1;
                BUG_ON(n_groups != 1);
        } else if (family->id == GENL_ID_VFS_DQUOT) {
                first_id = GENL_ID_VFS_DQUOT;
                BUG_ON(n_groups != 1);
        } else if (family->id == GENL_ID_PMCRAID) {
                first_id = GENL_ID_PMCRAID;
                BUG_ON(n_groups != 1);
        } else {
                groups_allocated = true;
                err = genl_allocate_reserve_groups(n_groups, &first_id);
                if (err)
                        return err;
        }

        family->mcgrp_offset = first_id;

        /* if still initializing, can't and don't need to to realloc bitmaps */
        if (!init_net.genl_sock)
                return 0;

        if (family->netnsok) {
                struct net *net;

                netlink_table_grab();
                rcu_read_lock();
                for_each_net_rcu(net) {
                        err = __netlink_change_ngroups(net->genl_sock,
                                        mc_groups_longs * BITS_PER_LONG);
                        if (err) {
                                /*
                                 * No need to roll back, can only fail if
                                 * memory allocation fails and then the
                                 * number of _possible_ groups has been
                                 * increased on some sockets which is ok.
                                 */
                                break;
                        }
                }
                rcu_read_unlock();
                netlink_table_ungrab();
        } else {
                err = netlink_change_ngroups(init_net.genl_sock,
                                             mc_groups_longs * BITS_PER_LONG);
        }

        if (groups_allocated && err) {
                for (i = 0; i < family->n_mcgrps; i++)
                        clear_bit(family->mcgrp_offset + i, mc_groups);
        }

        return err;
}

static void genl_unregister_mc_groups(struct genl_family *family)
{
        struct net *net;
        int i;

        netlink_table_grab();
        rcu_read_lock();
        for_each_net_rcu(net) {
                for (i = 0; i < family->n_mcgrps; i++)
                        __netlink_clear_multicast_users(
                                net->genl_sock, family->mcgrp_offset + i);
        }
        rcu_read_unlock();
        netlink_table_ungrab();

        for (i = 0; i < family->n_mcgrps; i++) {
                int grp_id = family->mcgrp_offset + i;

                if (grp_id != 1)
                        clear_bit(grp_id, mc_groups);
                genl_ctrl_event(CTRL_CMD_DELMCAST_GRP, family,
                                &family->mcgrps[i], grp_id);
        }
}

/*
 * 满足以下条件:
 * family->ops 数组每个元素的 dumpit 和 doit 不同时为 NULL
 * family->ops 数组元素之间的 cmd 没有重复
 * 如果 family->n_ops = 0 则 family->ops 必须为 NULL
 */
static int genl_validate_ops(const struct genl_family *family)
{
        const struct genl_ops *ops = family->ops;
        unsigned int n_ops = family->n_ops;
        int i, j;

        if (WARN_ON(n_ops && !ops))
                return -EINVAL;

        if (!n_ops)
                return 0;

        for (i = 0; i < n_ops; i++) {
                if (ops[i].dumpit == NULL && ops[i].doit == NULL)
                        return -EINVAL;
                for (j = i + 1; j < n_ops; j++)
                        if (ops[i].cmd == ops[j].cmd)
                                return -EINVAL;
        }

        return 0;
}

/**
 * __genl_register_family - register a generic netlink family
 * @family: generic netlink family
 *
 * Registers the specified family after validating it first. Only one
 * family may be registered with the same family name or identifier.
 * The family id may equal GENL_ID_GENERATE causing an unique id to
 * be automatically generated and assigned.
 *
 * The family's ops array must already be assigned, you can use the
 * genl_register_family_with_ops() helper function.
 *
 * Return 0 on success or a negative error code.
 *
 * 满足以下条件:
 * family->ops 数组每个元素的 dumpit 和 doit 不同时为 NULL
 * family->ops 数组元素之间的 cmd 没有重复
 * 如果 family->n_ops = 0 则 family->ops 必须为 NULL
 * family_ht 中不存在与 family->name 同名的 family
 * family->id 为 GENL_ID_GENERATE 或 family->id 与已经存在的 id 不重复
 *
 * 将 family_list 加入 family_ht 中
 *
 *
 */
int __genl_register_family(struct genl_family *family)
{
        int err = -EINVAL, i;

        if (family->id && family->id < GENL_MIN_ID)
                goto errout;

        if (family->id > GENL_MAX_ID)
                goto errout;

        err = genl_validate_ops(family);
        if (err)
                return err;

        genl_lock_all();

        if (genl_family_find_byname(family->name)) {
                err = -EEXIST;
                goto errout_locked;
        }

        if (family->id == GENL_ID_GENERATE) {
                u16 newid = genl_generate_id();

                if (!newid) {
                        err = -ENOMEM;
                        goto errout_locked;
                }

                family->id = newid;
        } else if (genl_family_find_byid(family->id)) {
                err = -EEXIST;
                goto errout_locked;
        }

        if (family->maxattr && !family->parallel_ops) {
                family->attrbuf = kmalloc((family->maxattr+1) *
                                        sizeof(struct nlattr *), GFP_KERNEL);
                if (family->attrbuf == NULL) {
                        err = -ENOMEM;
                        goto errout_locked;
                }
        } else
                family->attrbuf = NULL;

        err = genl_validate_assign_mc_groups(family);
        if (err)
                goto errout_locked;

        list_add_tail(&family->family_list, genl_family_chain(family->id));
        genl_unlock_all();

        /* send all events */
        genl_ctrl_event(CTRL_CMD_NEWFAMILY, family, NULL, 0);
        for (i = 0; i < family->n_mcgrps; i++)
                genl_ctrl_event(CTRL_CMD_NEWMCAST_GRP, family,
                                &family->mcgrps[i], family->mcgrp_offset + i);

        return 0;

errout_locked:
        genl_unlock_all();
errout:
        return err;
}
EXPORT_SYMBOL(__genl_register_family);

/**
 * genl_unregister_family - unregister generic netlink family
 * @family: generic netlink family
 *
 * Unregisters the specified family.
 *
 * Returns 0 on success or a negative error code.
 */
int genl_unregister_family(struct genl_family *family)
{
        struct genl_family *rc;

        genl_lock_all();

        list_for_each_entry(rc, genl_family_chain(family->id), family_list) {
                if (family->id != rc->id || strcmp(rc->name, family->name))
                        continue;

                genl_unregister_mc_groups(family);

                list_del(&rc->family_list);
                family->n_ops = 0;
                up_write(&cb_lock);
                wait_event(genl_sk_destructing_waitq,
                           atomic_read(&genl_sk_destructing_cnt) == 0);
                genl_unlock();

                kfree(family->attrbuf);
                genl_ctrl_event(CTRL_CMD_DELFAMILY, family, NULL, 0);
                return 0;
        }

        genl_unlock_all();

        return -ENOENT;
}
EXPORT_SYMBOL(genl_unregister_family);

/**
 * genlmsg_new_unicast - Allocate generic netlink message for unicast
 * @payload: size of the message payload
 * @info: information on destination
 * @flags: the type of memory to allocate
 *
 * Allocates a new sk_buff large enough to cover the specified payload
 * plus required Netlink headers. Will check receiving socket for
 * memory mapped i/o capability and use it if enabled. Will fall back
 * to non-mapped skb if message size exceeds the frame size of the ring.
 */
struct sk_buff *genlmsg_new_unicast(size_t payload, struct genl_info *info,
                                    gfp_t flags)
{
        size_t len = nlmsg_total_size(genlmsg_total_size(payload));

        return netlink_alloc_skb(info->dst_sk, len, info->snd_portid, flags);
}
EXPORT_SYMBOL_GPL(genlmsg_new_unicast);

/**
 * genlmsg_put - Add generic netlink header to netlink message
 * @skb: socket buffer holding the message
 * @portid: netlink portid the message is addressed to
 * @seq: sequence number (usually the one of the sender)
 * @family: generic netlink family
 * @flags: netlink message flags
 * @cmd: generic netlink command
 *
 * Returns pointer to user specific header
 */
void *genlmsg_put(struct sk_buff *skb, u32 portid, u32 seq,
                                struct genl_family *family, int flags, u8 cmd)
{
        struct nlmsghdr *nlh;
        struct genlmsghdr *hdr;

        nlh = nlmsg_put(skb, portid, seq, family->id, GENL_HDRLEN +
                        family->hdrsize, flags);
        if (nlh == NULL)
                return NULL;

        hdr = nlmsg_data(nlh);
        hdr->cmd = cmd;
        hdr->version = family->version;
        hdr->reserved = 0;

        return (char *) hdr + GENL_HDRLEN;
}
EXPORT_SYMBOL(genlmsg_put);

static int genl_lock_dumpit(struct sk_buff *skb, struct netlink_callback *cb)
{
        /* our ops are always const - netlink API doesn't propagate that */
        const struct genl_ops *ops = cb->data;
        int rc;

        genl_lock();
        rc = ops->dumpit(skb, cb);
        genl_unlock();
        return rc;
}

static int genl_lock_done(struct netlink_callback *cb)
{
        /* our ops are always const - netlink API doesn't propagate that */
        const struct genl_ops *ops = cb->data;
        int rc = 0;

        if (ops->done) {
                genl_lock();
                rc = ops->done(cb);
                genl_unlock();
        }
        return rc;
}

static int genl_family_rcv_msg(struct genl_family *family,
                               struct sk_buff *skb,
                               struct nlmsghdr *nlh)
{
        const struct genl_ops *ops;
        struct net *net = sock_net(skb->sk);
        struct genl_info info;
        struct genlmsghdr *hdr = nlmsg_data(nlh);
        struct nlattr **attrbuf;
        int hdrlen, err;

        /* this family doesn't exist in this netns */
        if (!family->netnsok && !net_eq(net, &init_net))
                return -ENOENT;

        hdrlen = GENL_HDRLEN + family->hdrsize;
        if (nlh->nlmsg_len < nlmsg_msg_size(hdrlen))
                return -EINVAL;

        ops = genl_get_cmd(hdr->cmd, family);
        if (ops == NULL)
                return -EOPNOTSUPP;

        if ((ops->flags & GENL_ADMIN_PERM) &&
            !netlink_capable(skb, CAP_NET_ADMIN))
                return -EPERM;

        if ((nlh->nlmsg_flags & NLM_F_DUMP) == NLM_F_DUMP) {
                int rc;

                if (ops->dumpit == NULL)
                        return -EOPNOTSUPP;

                if (!family->parallel_ops) {
                        struct netlink_dump_control c = {
                                .module = family->module,
                                /* we have const, but the netlink API doesn't */
                                .data = (void *)ops,
                                .dump = genl_lock_dumpit,
                                .done = genl_lock_done,
                        };

                        genl_unlock();
                        rc = __netlink_dump_start(net->genl_sock, skb, nlh, &c);
                        genl_lock();

                } else {
                        struct netlink_dump_control c = {
                                .module = family->module,
                                .dump = ops->dumpit,
                                .done = ops->done,
                        };

                        rc = __netlink_dump_start(net->genl_sock, skb, nlh, &c);
                }

                return rc;
        }

        if (ops->doit == NULL)
                return -EOPNOTSUPP;

        if (family->maxattr && family->parallel_ops) {
                attrbuf = kmalloc((family->maxattr+1) *
                                        sizeof(struct nlattr *), GFP_KERNEL);
                if (attrbuf == NULL)
                        return -ENOMEM;
        } else
                attrbuf = family->attrbuf;

        if (attrbuf) {
                err = nlmsg_parse(nlh, hdrlen, attrbuf, family->maxattr,
                                  ops->policy);
                if (err < 0)
                        goto out;
        }

        info.snd_seq = nlh->nlmsg_seq;
        info.snd_portid = NETLINK_CB(skb).portid;
        info.nlhdr = nlh;
        info.genlhdr = nlmsg_data(nlh);
        info.userhdr = nlmsg_data(nlh) + GENL_HDRLEN;
        info.attrs = attrbuf;
        info.dst_sk = skb->sk;
        genl_info_net_set(&info, net);
        memset(&info.user_ptr, 0, sizeof(info.user_ptr));

        if (family->pre_doit) {
                err = family->pre_doit(ops, skb, &info);
                if (err)
                        goto out;
        }

        err = ops->doit(skb, &info);

        if (family->post_doit)
                family->post_doit(ops, skb, &info);

out:
        if (family->parallel_ops)
                kfree(attrbuf);

        return err;
}

static int genl_rcv_msg(struct sk_buff *skb, struct nlmsghdr *nlh)
{
        struct genl_family *family;
        int err;

        family = genl_family_find_byid(nlh->nlmsg_type);
        if (family == NULL)
                return -ENOENT;

        if (!family->parallel_ops)
                genl_lock();

        err = genl_family_rcv_msg(family, skb, nlh);

        if (!family->parallel_ops)
                genl_unlock();

        return err;
}

static void genl_rcv(struct sk_buff *skb)
{
        down_read(&cb_lock);
        netlink_rcv_skb(skb, &genl_rcv_msg);
        up_read(&cb_lock);
}

/**************************************************************************
 * Controller
 **************************************************************************/

static struct genl_family genl_ctrl = {
        .id = GENL_ID_CTRL,
        .name = "nlctrl",
        .version = 0x2,
        .maxattr = CTRL_ATTR_MAX,
        .netnsok = true,
};

static int ctrl_fill_info(struct genl_family *family, u32 portid, u32 seq,
                          u32 flags, struct sk_buff *skb, u8 cmd)
{
        void *hdr;

        hdr = genlmsg_put(skb, portid, seq, &genl_ctrl, flags, cmd);
        if (hdr == NULL)
                return -1;

        if (nla_put_string(skb, CTRL_ATTR_FAMILY_NAME, family->name) ||
            nla_put_u16(skb, CTRL_ATTR_FAMILY_ID, family->id) ||
            nla_put_u32(skb, CTRL_ATTR_VERSION, family->version) ||
            nla_put_u32(skb, CTRL_ATTR_HDRSIZE, family->hdrsize) ||
            nla_put_u32(skb, CTRL_ATTR_MAXATTR, family->maxattr))
                goto nla_put_failure;

        if (family->n_ops) {
                struct nlattr *nla_ops;
                int i;

                nla_ops = nla_nest_start(skb, CTRL_ATTR_OPS);
                if (nla_ops == NULL)
                        goto nla_put_failure;

                for (i = 0; i < family->n_ops; i++) {
                        struct nlattr *nest;
                        const struct genl_ops *ops = &family->ops[i];
                        u32 op_flags = ops->flags;

                        if (ops->dumpit)
                                op_flags |= GENL_CMD_CAP_DUMP;
                        if (ops->doit)
                                op_flags |= GENL_CMD_CAP_DO;
                        if (ops->policy)
                                op_flags |= GENL_CMD_CAP_HASPOL;

                        nest = nla_nest_start(skb, i + 1);
                        if (nest == NULL)
                                goto nla_put_failure;

                        if (nla_put_u32(skb, CTRL_ATTR_OP_ID, ops->cmd) ||
                            nla_put_u32(skb, CTRL_ATTR_OP_FLAGS, op_flags))
                                goto nla_put_failure;

                        nla_nest_end(skb, nest);
                }

                nla_nest_end(skb, nla_ops);
        }

        if (family->n_mcgrps) {
                struct nlattr *nla_grps;
                int i;

                nla_grps = nla_nest_start(skb, CTRL_ATTR_MCAST_GROUPS);
                if (nla_grps == NULL)
                        goto nla_put_failure;

                for (i = 0; i < family->n_mcgrps; i++) {
                        struct nlattr *nest;
                        const struct genl_multicast_group *grp;

                        grp = &family->mcgrps[i];

                        nest = nla_nest_start(skb, i + 1);
                        if (nest == NULL)
                                goto nla_put_failure;

                        if (nla_put_u32(skb, CTRL_ATTR_MCAST_GRP_ID,
                                        family->mcgrp_offset + i) ||
                            nla_put_string(skb, CTRL_ATTR_MCAST_GRP_NAME,
                                           grp->name))
                                goto nla_put_failure;

                        nla_nest_end(skb, nest);
                }
                nla_nest_end(skb, nla_grps);
        }

        genlmsg_end(skb, hdr);
        return 0;

nla_put_failure:
        genlmsg_cancel(skb, hdr);
        return -EMSGSIZE;
}

static int ctrl_fill_mcgrp_info(struct genl_family *family,
                                const struct genl_multicast_group *grp,
                                int grp_id, u32 portid, u32 seq, u32 flags,
                                struct sk_buff *skb, u8 cmd)
{
        void *hdr;
        struct nlattr *nla_grps;
        struct nlattr *nest;

        hdr = genlmsg_put(skb, portid, seq, &genl_ctrl, flags, cmd);
        if (hdr == NULL)
                return -1;

        if (nla_put_string(skb, CTRL_ATTR_FAMILY_NAME, family->name) ||
            nla_put_u16(skb, CTRL_ATTR_FAMILY_ID, family->id))
                goto nla_put_failure;

        nla_grps = nla_nest_start(skb, CTRL_ATTR_MCAST_GROUPS);
        if (nla_grps == NULL)
                goto nla_put_failure;

        nest = nla_nest_start(skb, 1);
        if (nest == NULL)
                goto nla_put_failure;

        if (nla_put_u32(skb, CTRL_ATTR_MCAST_GRP_ID, grp_id) ||
            nla_put_string(skb, CTRL_ATTR_MCAST_GRP_NAME,
                           grp->name))
                goto nla_put_failure;

        nla_nest_end(skb, nest);
        nla_nest_end(skb, nla_grps);

        genlmsg_end(skb, hdr);
        return 0;

nla_put_failure:
        genlmsg_cancel(skb, hdr);
        return -EMSGSIZE;
}

static int ctrl_dumpfamily(struct sk_buff *skb, struct netlink_callback *cb)
{

        int i, n = 0;
        struct genl_family *rt;
        struct net *net = sock_net(skb->sk);
        int chains_to_skip = cb->args[0];
        int fams_to_skip = cb->args[1];

        for (i = chains_to_skip; i < GENL_FAM_TAB_SIZE; i++) {
                n = 0;
                list_for_each_entry(rt, genl_family_chain(i), family_list) {
                        if (!rt->netnsok && !net_eq(net, &init_net))
                                continue;
                        if (++n < fams_to_skip)
                                continue;
                        if (ctrl_fill_info(rt, NETLINK_CB(cb->skb).portid,
                                           cb->nlh->nlmsg_seq, NLM_F_MULTI,
                                           skb, CTRL_CMD_NEWFAMILY) < 0)
                                goto errout;
                }

                fams_to_skip = 0;
        }

errout:
        cb->args[0] = i;
        cb->args[1] = n;

        return skb->len;
}

static struct sk_buff *ctrl_build_family_msg(struct genl_family *family,
                                             u32 portid, int seq, u8 cmd)
{
        struct sk_buff *skb;
        int err;

        skb = nlmsg_new(NLMSG_DEFAULT_SIZE, GFP_KERNEL);
        if (skb == NULL)
                return ERR_PTR(-ENOBUFS);

        err = ctrl_fill_info(family, portid, seq, 0, skb, cmd);
        if (err < 0) {
                nlmsg_free(skb);
                return ERR_PTR(err);
        }

        return skb;
}

static struct sk_buff *
ctrl_build_mcgrp_msg(struct genl_family *family,
                     const struct genl_multicast_group *grp,
                     int grp_id, u32 portid, int seq, u8 cmd)
{
        struct sk_buff *skb;
        int err;

        skb = nlmsg_new(NLMSG_DEFAULT_SIZE, GFP_KERNEL);
        if (skb == NULL)
                return ERR_PTR(-ENOBUFS);

        err = ctrl_fill_mcgrp_info(family, grp, grp_id, portid,
                                   seq, 0, skb, cmd);
        if (err < 0) {
                nlmsg_free(skb);
                return ERR_PTR(err);
        }

        return skb;
}

static const struct nla_policy ctrl_policy[CTRL_ATTR_MAX+1] = {
        [CTRL_ATTR_FAMILY_ID]   = { .type = NLA_U16 },
        [CTRL_ATTR_FAMILY_NAME] = { .type = NLA_NUL_STRING,
                                    .len = GENL_NAMSIZ - 1 },
};

static int ctrl_getfamily(struct sk_buff *skb, struct genl_info *info)
{
        struct sk_buff *msg;
        struct genl_family *res = NULL;
        int err = -EINVAL;

        if (info->attrs[CTRL_ATTR_FAMILY_ID]) {
                u16 id = nla_get_u16(info->attrs[CTRL_ATTR_FAMILY_ID]);
                res = genl_family_find_byid(id);
                err = -ENOENT;
        }

        if (info->attrs[CTRL_ATTR_FAMILY_NAME]) {
                char *name;

                name = nla_data(info->attrs[CTRL_ATTR_FAMILY_NAME]);
                res = genl_family_find_byname(name);
#ifdef CONFIG_MODULES
                if (res == NULL) {
                        genl_unlock();
                        up_read(&cb_lock);
                        request_module("net-pf-%d-proto-%d-family-%s",
                                       PF_NETLINK, NETLINK_GENERIC, name);
                        down_read(&cb_lock);
                        genl_lock();
                        res = genl_family_find_byname(name);
                }
#endif
                err = -ENOENT;
        }

        if (res == NULL)
                return err;

        if (!res->netnsok && !net_eq(genl_info_net(info), &init_net)) {
                /* family doesn't exist here */
                return -ENOENT;
        }

        msg = ctrl_build_family_msg(res, info->snd_portid, info->snd_seq,
                                    CTRL_CMD_NEWFAMILY);
        if (IS_ERR(msg))
                return PTR_ERR(msg);

        return genlmsg_reply(msg, info);
}

static int genl_ctrl_event(int event, struct genl_family *family,
                           const struct genl_multicast_group *grp,
                           int grp_id)
{
        struct sk_buff *msg;

        /* genl is still initialising */
        if (!init_net.genl_sock)
                return 0;

        switch (event) {
        case CTRL_CMD_NEWFAMILY:
        case CTRL_CMD_DELFAMILY:
                WARN_ON(grp);
                msg = ctrl_build_family_msg(family, 0, 0, event);
                break;
        case CTRL_CMD_NEWMCAST_GRP:
        case CTRL_CMD_DELMCAST_GRP:
                BUG_ON(!grp);
                msg = ctrl_build_mcgrp_msg(family, grp, grp_id, 0, 0, event);
                break;
        default:
                return -EINVAL;
        }

        if (IS_ERR(msg))
                return PTR_ERR(msg);

        if (!family->netnsok) {
                genlmsg_multicast_netns(&genl_ctrl, &init_net, msg, 0,
                                        0, GFP_KERNEL);
        } else {
                rcu_read_lock();
                genlmsg_multicast_allns(&genl_ctrl, msg, 0,
                                        0, GFP_ATOMIC);
                rcu_read_unlock();
        }

        return 0;
}

static struct genl_ops genl_ctrl_ops[] = {
        {
                .cmd            = CTRL_CMD_GETFAMILY,
                .doit           = ctrl_getfamily,
                .dumpit         = ctrl_dumpfamily,
                .policy         = ctrl_policy,
        },
};

static struct genl_multicast_group genl_ctrl_groups[] = {
        { .name = "notify", },
};

static int genl_bind(struct net *net, int group)
{
        int i, err = -ENOENT;

        down_read(&cb_lock);
        for (i = 0; i < GENL_FAM_TAB_SIZE; i++) {
                 struct genl_family *f;
 
                 list_for_each_entry(f, genl_family_chain(i), family_list) {
                         if (group >= f->mcgrp_offset &&
                             group < f->mcgrp_offset + f->n_mcgrps) {
                                 int fam_grp = group - f->mcgrp_offset;
 
                                 if (!f->netnsok && net != &init_net)
                                         err = -ENOENT;
                                 else if (f->mcast_bind)
                                         err = f->mcast_bind(net, fam_grp);
                                 else
                                         err = 0;
                                 break;
                         }
                 }
         }
         up_read(&cb_lock);
 
         return err;
 }
 
 static void genl_unbind(struct net *net, int group)
 {
         int i;
 
         down_read(&cb_lock);
         for (i = 0; i < GENL_FAM_TAB_SIZE; i++) {
                 struct genl_family *f;
 
                 list_for_each_entry(f, genl_family_chain(i), family_list) {
                         if (group >= f->mcgrp_offset &&
                             group < f->mcgrp_offset + f->n_mcgrps) {
                                 int fam_grp = group - f->mcgrp_offset;
 
                                 if (f->mcast_unbind)
                                         f->mcast_unbind(net, fam_grp);
                                 break;
                         }
                 }
         }
         up_read(&cb_lock);
 }
 
 static int __net_init genl_pernet_init(struct net *net)
 {
         struct netlink_kernel_cfg cfg = {
                 .input          = genl_rcv,
                 .flags          = NL_CFG_F_NONROOT_RECV,
                 .bind           = genl_bind,
                 .unbind         = genl_unbind,
         };
 
         /* we'll bump the group number right afterwards */
         net->genl_sock = netlink_kernel_create(net, NETLINK_GENERIC, &cfg);
 
         if (!net->genl_sock && net_eq(net, &init_net))
                 panic("GENL: Cannot initialize generic netlink\n");
 
         if (!net->genl_sock)
                 return -ENOMEM;
 
         return 0;
 }
 
 static void __net_exit genl_pernet_exit(struct net *net)
 {
         netlink_kernel_release(net->genl_sock);
         net->genl_sock = NULL;
 }
 
 static struct pernet_operations genl_pernet_ops = {
         .init = genl_pernet_init,
         .exit = genl_pernet_exit,
 };
 
 static int __init genl_init(void)
 {
         int i, err;
 
         for (i = 0; i < GENL_FAM_TAB_SIZE; i++)
                 INIT_LIST_HEAD(&family_ht[i]);
 
         err = genl_register_family_with_ops_groups(&genl_ctrl, genl_ctrl_ops,
                                                    genl_ctrl_groups);
         if (err < 0)
                 goto problem;
 
         err = register_pernet_subsys(&genl_pernet_ops);
         if (err)
                 goto problem;
 
         return 0;
 
 problem:
         panic("GENL: Cannot register controller: %d\n", err);
 }
 
 subsys_initcall(genl_init);
 
 static int genlmsg_mcast(struct sk_buff *skb, u32 portid, unsigned long group,
                          gfp_t flags)
 {
         struct sk_buff *tmp;
         struct net *net, *prev = NULL;
         int err;
 
         for_each_net_rcu(net) {
                 if (prev) {
                         tmp = skb_clone(skb, flags);
                         if (!tmp) {
                                 err = -ENOMEM;
                                 goto error;
                         }
                         err = nlmsg_multicast(prev->genl_sock, tmp,
                                               portid, group, flags);
                         if (err)
                                 goto error;
                 }
 
                 prev = net;
         }
 
         return nlmsg_multicast(prev->genl_sock, skb, portid, group, flags);
  error:
         kfree_skb(skb);
         return err;
 }
 
 int genlmsg_multicast_allns(struct genl_family *family, struct sk_buff *skb,
                             u32 portid, unsigned int group, gfp_t flags)
 {
         if (WARN_ON_ONCE(group >= family->n_mcgrps))
                 return -EINVAL;
         group = family->mcgrp_offset + group;
         return genlmsg_mcast(skb, portid, group, flags);
 }
 EXPORT_SYMBOL(genlmsg_multicast_allns);
 
 void genl_notify(struct genl_family *family,
                  struct sk_buff *skb, struct net *net, u32 portid, u32 group,
                  struct nlmsghdr *nlh, gfp_t flags)
 {
         struct sock *sk = net->genl_sock;
         int report = 0;
 
         if (nlh)
                 report = nlmsg_report(nlh);
 
         if (WARN_ON_ONCE(group >= family->n_mcgrps))
                 return;
         group = family->mcgrp_offset + group;
         nlmsg_notify(sk, skb, portid, group, report, flags);
 }
 EXPORT_SYMBOL(genl_notify);
 
```

```
/* af_netlink.c */
/*
 * NETLINK      Kernel-user communication protocol.
 *
 *              Authors:        Alan Cox <alan@lxorguk.ukuu.org.uk>
 *                              Alexey Kuznetsov <kuznet@ms2.inr.ac.ru>
 *                              Patrick McHardy <kaber@trash.net>
 *
 *              This program is free software; you can redistribute it and/or
 *              modify it under the terms of the GNU General Public License
 *              as published by the Free Software Foundation; either version
 *              2 of the License, or (at your option) any later version.
 *
 * Tue Jun 26 14:36:48 MEST 2001 Herbert "herp" Rosmanith
 *                               added netlink_proto_exit
 * Tue Jan 22 18:32:44 BRST 2002 Arnaldo C. de Melo <acme@conectiva.com.br>
 *                               use nlk_sk, as sk->protinfo is on a diet 8)
 * Fri Jul 22 19:51:12 MEST 2005 Harald Welte <laforge@gnumonks.org>
 *                               - inc module use count of module that owns
 *                                 the kernel socket in case userspace opens
 *                                 socket of same protocol
 *                               - remove all module support, since netlink is
 *                                 mandatory if CONFIG_NET=y these days
 */

#include <linux/module.h>

#include <linux/capability.h>
#include <linux/kernel.h>
#include <linux/init.h>
#include <linux/signal.h>
#include <linux/sched.h>
#include <linux/errno.h>
#include <linux/string.h>
#include <linux/stat.h>
#include <linux/socket.h>
#include <linux/un.h>
#include <linux/fcntl.h>
#include <linux/termios.h>
#include <linux/sockios.h>
#include <linux/net.h>
#include <linux/fs.h>
#include <linux/slab.h>
#include <asm/uaccess.h>
#include <linux/skbuff.h>
#include <linux/netdevice.h>
#include <linux/rtnetlink.h>
#include <linux/proc_fs.h>
#include <linux/seq_file.h>
#include <linux/notifier.h>
#include <linux/security.h>
#include <linux/jhash.h>
#include <linux/jiffies.h>
#include <linux/random.h>
#include <linux/bitops.h>
#include <linux/mm.h>
#include <linux/types.h>
#include <linux/audit.h>
#include <linux/mutex.h>
#include <linux/vmalloc.h>
#include <linux/if_arp.h>
#include <linux/rhashtable.h>
#include <asm/cacheflush.h>
#include <linux/hash.h>
#include <linux/genetlink.h>

#include <net/net_namespace.h>
#include <net/sock.h>
#include <net/scm.h>
#include <net/netlink.h>

#include "af_netlink.h"

struct listeners {
        struct rcu_head         rcu;
        unsigned long           masks[0];
};

/* state bits */
#define NETLINK_CONGESTED       0x0

/* flags */
#define NETLINK_KERNEL_SOCKET   0x1
#define NETLINK_RECV_PKTINFO    0x2
#define NETLINK_BROADCAST_SEND_ERROR    0x4
#define NETLINK_RECV_NO_ENOBUFS 0x8

static inline int netlink_is_kernel(struct sock *sk)
{
        return nlk_sk(sk)->flags & NETLINK_KERNEL_SOCKET;
}

struct netlink_table *nl_table __read_mostly;
EXPORT_SYMBOL_GPL(nl_table);

static DECLARE_WAIT_QUEUE_HEAD(nl_table_wait);

static int netlink_dump(struct sock *sk);
static void netlink_skb_destructor(struct sk_buff *skb);

/* nl_table locking explained:
 * Lookup and traversal are protected with an RCU read-side lock. Insertion
 * and removal are protected with per bucket lock while using RCU list
 * modification primitives and may run in parallel to RCU protected lookups.
 * Destruction of the Netlink socket may only occur *after* nl_table_lock has
 * been acquired * either during or after the socket has been removed from
 * the list and after an RCU grace period.
 */
DEFINE_RWLOCK(nl_table_lock);
EXPORT_SYMBOL_GPL(nl_table_lock);
static atomic_t nl_table_users = ATOMIC_INIT(0);

#define nl_deref_protected(X) rcu_dereference_protected(X, lockdep_is_held(&nl_table_lock));

static ATOMIC_NOTIFIER_HEAD(netlink_chain);

static DEFINE_SPINLOCK(netlink_tap_lock);
static struct list_head netlink_tap_all __read_mostly;

static const struct rhashtable_params netlink_rhashtable_params;

static inline u32 netlink_group_mask(u32 group)
{
        return group ? 1 << (group - 1) : 0;
}

int netlink_add_tap(struct netlink_tap *nt)
{
        if (unlikely(nt->dev->type != ARPHRD_NETLINK))
                return -EINVAL;

        spin_lock(&netlink_tap_lock);
        list_add_rcu(&nt->list, &netlink_tap_all);
        spin_unlock(&netlink_tap_lock);

        __module_get(nt->module);

        return 0;
}
EXPORT_SYMBOL_GPL(netlink_add_tap);

static int __netlink_remove_tap(struct netlink_tap *nt)
{
        bool found = false;
        struct netlink_tap *tmp;

        spin_lock(&netlink_tap_lock);

        list_for_each_entry(tmp, &netlink_tap_all, list) {
                if (nt == tmp) {
                        list_del_rcu(&nt->list);
                        found = true;
                        goto out;
                }
        }

        pr_warn("__netlink_remove_tap: %p not found\n", nt);
out:
        spin_unlock(&netlink_tap_lock);

        if (found && nt->module)
                module_put(nt->module);

        return found ? 0 : -ENODEV;
}

int netlink_remove_tap(struct netlink_tap *nt)
{
        int ret;

        ret = __netlink_remove_tap(nt);
        synchronize_net();

        return ret;
}
EXPORT_SYMBOL_GPL(netlink_remove_tap);

static bool netlink_filter_tap(const struct sk_buff *skb)
{
        struct sock *sk = skb->sk;

        /* We take the more conservative approach and
         * whitelist socket protocols that may pass.
         */
        switch (sk->sk_protocol) {
        case NETLINK_ROUTE:
        case NETLINK_USERSOCK:
        case NETLINK_SOCK_DIAG:
        case NETLINK_NFLOG:
        case NETLINK_XFRM:
        case NETLINK_FIB_LOOKUP:
        case NETLINK_NETFILTER:
        case NETLINK_GENERIC:
                return true;
        }

        return false;
}

static int __netlink_deliver_tap_skb(struct sk_buff *skb,
                                     struct net_device *dev)
{
        struct sk_buff *nskb;
        struct sock *sk = skb->sk;
        int ret = -ENOMEM;

        dev_hold(dev);
        nskb = skb_clone(skb, GFP_ATOMIC);
        if (nskb) {
                nskb->dev = dev;
                nskb->protocol = htons((u16) sk->sk_protocol);
                nskb->pkt_type = netlink_is_kernel(sk) ?
                                 PACKET_KERNEL : PACKET_USER;
                skb_reset_network_header(nskb);
                ret = dev_queue_xmit(nskb);
                if (unlikely(ret > 0))
                        ret = net_xmit_errno(ret);
        }

        dev_put(dev);
        return ret;
}

static void __netlink_deliver_tap(struct sk_buff *skb)
{
        int ret;
        struct netlink_tap *tmp;

        if (!netlink_filter_tap(skb))
                return;

        list_for_each_entry_rcu(tmp, &netlink_tap_all, list) {
                ret = __netlink_deliver_tap_skb(skb, tmp->dev);
                if (unlikely(ret))
                        break;
        }
}

static void netlink_deliver_tap(struct sk_buff *skb)
{
        rcu_read_lock();

        if (unlikely(!list_empty(&netlink_tap_all)))
                __netlink_deliver_tap(skb);

        rcu_read_unlock();
}

static void netlink_deliver_tap_kernel(struct sock *dst, struct sock *src,
                                       struct sk_buff *skb)
{
        if (!(netlink_is_kernel(dst) && netlink_is_kernel(src)))
                netlink_deliver_tap(skb);
}

static void netlink_overrun(struct sock *sk)
{
        struct netlink_sock *nlk = nlk_sk(sk);

        if (!(nlk->flags & NETLINK_RECV_NO_ENOBUFS)) {
                if (!test_and_set_bit(NETLINK_CONGESTED, &nlk_sk(sk)->state)) {
                        sk->sk_err = ENOBUFS;
                        sk->sk_error_report(sk);
                }
        }
        atomic_inc(&sk->sk_drops);
}

static void netlink_rcv_wake(struct sock *sk)
{
        struct netlink_sock *nlk = nlk_sk(sk);

        if (skb_queue_empty(&sk->sk_receive_queue))
                clear_bit(NETLINK_CONGESTED, &nlk->state);
        if (!test_bit(NETLINK_CONGESTED, &nlk->state))
                wake_up_interruptible(&nlk->wait);
}

#ifdef CONFIG_NETLINK_MMAP
static bool netlink_skb_is_mmaped(const struct sk_buff *skb)
{
        return NETLINK_CB(skb).flags & NETLINK_SKB_MMAPED;
}

static bool netlink_rx_is_mmaped(struct sock *sk)
{
        return nlk_sk(sk)->rx_ring.pg_vec != NULL;
}

static bool netlink_tx_is_mmaped(struct sock *sk)
{
        return nlk_sk(sk)->tx_ring.pg_vec != NULL;
}

static __pure struct page *pgvec_to_page(const void *addr)
{
        if (is_vmalloc_addr(addr))
                return vmalloc_to_page(addr);
        else
                return virt_to_page(addr);
}

static void free_pg_vec(void **pg_vec, unsigned int order, unsigned int len)
{
        unsigned int i;

        for (i = 0; i < len; i++) {
                if (pg_vec[i] != NULL) {
                        if (is_vmalloc_addr(pg_vec[i]))
                                vfree(pg_vec[i]);
                        else
                                free_pages((unsigned long)pg_vec[i], order);
                }
        }
        kfree(pg_vec);
}

static void *alloc_one_pg_vec_page(unsigned long order)
{
        void *buffer;
        gfp_t gfp_flags = GFP_KERNEL | __GFP_COMP | __GFP_ZERO |
                          __GFP_NOWARN | __GFP_NORETRY;

        buffer = (void *)__get_free_pages(gfp_flags, order);
        if (buffer != NULL)
                return buffer;

        buffer = vzalloc((1 << order) * PAGE_SIZE);
        if (buffer != NULL)
                return buffer;

        gfp_flags &= ~__GFP_NORETRY;
        return (void *)__get_free_pages(gfp_flags, order);
}

static void **alloc_pg_vec(struct netlink_sock *nlk,
                           struct nl_mmap_req *req, unsigned int order)
{
        unsigned int block_nr = req->nm_block_nr;
        unsigned int i;
        void **pg_vec;

        pg_vec = kcalloc(block_nr, sizeof(void *), GFP_KERNEL);
        if (pg_vec == NULL)
                return NULL;

        for (i = 0; i < block_nr; i++) {
                pg_vec[i] = alloc_one_pg_vec_page(order);
                if (pg_vec[i] == NULL)
                        goto err1;
        }

        return pg_vec;
err1:
        free_pg_vec(pg_vec, order, block_nr);
        return NULL;
}

static int netlink_set_ring(struct sock *sk, struct nl_mmap_req *req,
                            bool closing, bool tx_ring)
{
        struct netlink_sock *nlk = nlk_sk(sk);
        struct netlink_ring *ring;
        struct sk_buff_head *queue;
        void **pg_vec = NULL;
        unsigned int order = 0;
        int err;

        ring  = tx_ring ? &nlk->tx_ring : &nlk->rx_ring;
        queue = tx_ring ? &sk->sk_write_queue : &sk->sk_receive_queue;

        if (!closing) {
                if (atomic_read(&nlk->mapped))
                        return -EBUSY;
                if (atomic_read(&ring->pending))
                        return -EBUSY;
        }

        if (req->nm_block_nr) {
                if (ring->pg_vec != NULL)
                        return -EBUSY;

                if ((int)req->nm_block_size <= 0)
                        return -EINVAL;
                if (!PAGE_ALIGNED(req->nm_block_size))
                        return -EINVAL;
                if (req->nm_frame_size < NL_MMAP_HDRLEN)
                        return -EINVAL;
                if (!IS_ALIGNED(req->nm_frame_size, NL_MMAP_MSG_ALIGNMENT))
                        return -EINVAL;

                ring->frames_per_block = req->nm_block_size /
                                         req->nm_frame_size;
                if (ring->frames_per_block == 0)
                        return -EINVAL;
                if (ring->frames_per_block * req->nm_block_nr !=
                    req->nm_frame_nr)
                        return -EINVAL;

                order = get_order(req->nm_block_size);
                pg_vec = alloc_pg_vec(nlk, req, order);
                if (pg_vec == NULL)
                        return -ENOMEM;
        } else {
                if (req->nm_frame_nr)
                        return -EINVAL;
        }

        err = -EBUSY;
        mutex_lock(&nlk->pg_vec_lock);
        if (closing || atomic_read(&nlk->mapped) == 0) {
                err = 0;
                spin_lock_bh(&queue->lock);

                ring->frame_max         = req->nm_frame_nr - 1;
                ring->head              = 0;
                ring->frame_size        = req->nm_frame_size;
                ring->pg_vec_pages      = req->nm_block_size / PAGE_SIZE;

                swap(ring->pg_vec_len, req->nm_block_nr);
                swap(ring->pg_vec_order, order);
                swap(ring->pg_vec, pg_vec);

                __skb_queue_purge(queue);
                spin_unlock_bh(&queue->lock);

                WARN_ON(atomic_read(&nlk->mapped));
        }
        mutex_unlock(&nlk->pg_vec_lock);

        if (pg_vec)
                free_pg_vec(pg_vec, order, req->nm_block_nr);
        return err;
}

static void netlink_mm_open(struct vm_area_struct *vma)
{
        struct file *file = vma->vm_file;
        struct socket *sock = file->private_data;
        struct sock *sk = sock->sk;

        if (sk)
                atomic_inc(&nlk_sk(sk)->mapped);
}

static void netlink_mm_close(struct vm_area_struct *vma)
{
        struct file *file = vma->vm_file;
        struct socket *sock = file->private_data;
        struct sock *sk = sock->sk;

        if (sk)
                atomic_dec(&nlk_sk(sk)->mapped);
}

static const struct vm_operations_struct netlink_mmap_ops = {
        .open   = netlink_mm_open,
        .close  = netlink_mm_close,
};

static int netlink_mmap(struct file *file, struct socket *sock,
                        struct vm_area_struct *vma)
{
        struct sock *sk = sock->sk;
        struct netlink_sock *nlk = nlk_sk(sk);
        struct netlink_ring *ring;
        unsigned long start, size, expected;
        unsigned int i;
        int err = -EINVAL;

        if (vma->vm_pgoff)
                return -EINVAL;

        mutex_lock(&nlk->pg_vec_lock);

        expected = 0;
        for (ring = &nlk->rx_ring; ring <= &nlk->tx_ring; ring++) {
                if (ring->pg_vec == NULL)
                        continue;
                expected += ring->pg_vec_len * ring->pg_vec_pages * PAGE_SIZE;
        }

        if (expected == 0)
                goto out;

        size = vma->vm_end - vma->vm_start;
        if (size != expected)
                goto out;

        start = vma->vm_start;
        for (ring = &nlk->rx_ring; ring <= &nlk->tx_ring; ring++) {
                if (ring->pg_vec == NULL)
                        continue;

                for (i = 0; i < ring->pg_vec_len; i++) {
                        struct page *page;
                        void *kaddr = ring->pg_vec[i];
                        unsigned int pg_num;

                        for (pg_num = 0; pg_num < ring->pg_vec_pages; pg_num++) {
                                page = pgvec_to_page(kaddr);
                                err = vm_insert_page(vma, start, page);
                                if (err < 0)
                                        goto out;
                                start += PAGE_SIZE;
                                kaddr += PAGE_SIZE;
                        }
                }
        }

        atomic_inc(&nlk->mapped);
        vma->vm_ops = &netlink_mmap_ops;
        err = 0;
out:
        mutex_unlock(&nlk->pg_vec_lock);
        return err;
}

static void netlink_frame_flush_dcache(const struct nl_mmap_hdr *hdr, unsigned int nm_len)
{
#if ARCH_IMPLEMENTS_FLUSH_DCACHE_PAGE == 1
        struct page *p_start, *p_end;

        /* First page is flushed through netlink_{get,set}_status */
        p_start = pgvec_to_page(hdr + PAGE_SIZE);
        p_end   = pgvec_to_page((void *)hdr + NL_MMAP_HDRLEN + nm_len - 1);
        while (p_start <= p_end) {
                flush_dcache_page(p_start);
                p_start++;
        }
#endif
}

static enum nl_mmap_status netlink_get_status(const struct nl_mmap_hdr *hdr)
{
        smp_rmb();
        flush_dcache_page(pgvec_to_page(hdr));
        return hdr->nm_status;
}

static void netlink_set_status(struct nl_mmap_hdr *hdr,
                               enum nl_mmap_status status)
{
        smp_mb();
        hdr->nm_status = status;
        flush_dcache_page(pgvec_to_page(hdr));
}

static struct nl_mmap_hdr *
__netlink_lookup_frame(const struct netlink_ring *ring, unsigned int pos)
{
        unsigned int pg_vec_pos, frame_off;

        pg_vec_pos = pos / ring->frames_per_block;
        frame_off  = pos % ring->frames_per_block;

        return ring->pg_vec[pg_vec_pos] + (frame_off * ring->frame_size);
}

static struct nl_mmap_hdr *
netlink_lookup_frame(const struct netlink_ring *ring, unsigned int pos,
                     enum nl_mmap_status status)
{
        struct nl_mmap_hdr *hdr;

        hdr = __netlink_lookup_frame(ring, pos);
        if (netlink_get_status(hdr) != status)
                return NULL;

        return hdr;
}

static struct nl_mmap_hdr *
netlink_current_frame(const struct netlink_ring *ring,
                      enum nl_mmap_status status)
{
        return netlink_lookup_frame(ring, ring->head, status);
}

static struct nl_mmap_hdr *
netlink_previous_frame(const struct netlink_ring *ring,
                       enum nl_mmap_status status)
{
        unsigned int prev;

        prev = ring->head ? ring->head - 1 : ring->frame_max;
        return netlink_lookup_frame(ring, prev, status);
}

static void netlink_increment_head(struct netlink_ring *ring)
{
        ring->head = ring->head != ring->frame_max ? ring->head + 1 : 0;
}

static void netlink_forward_ring(struct netlink_ring *ring)
{
        unsigned int head = ring->head, pos = head;
        const struct nl_mmap_hdr *hdr;

        do {
                hdr = __netlink_lookup_frame(ring, pos);
                if (hdr->nm_status == NL_MMAP_STATUS_UNUSED)
                        break;
                if (hdr->nm_status != NL_MMAP_STATUS_SKIP)
                        break;
                netlink_increment_head(ring);
        } while (ring->head != head);
}

static bool netlink_dump_space(struct netlink_sock *nlk)
{
        struct netlink_ring *ring = &nlk->rx_ring;
        struct nl_mmap_hdr *hdr;
        unsigned int n;

        hdr = netlink_current_frame(ring, NL_MMAP_STATUS_UNUSED);
        if (hdr == NULL)
                return false;

        n = ring->head + ring->frame_max / 2;
        if (n > ring->frame_max)
                n -= ring->frame_max;

        hdr = __netlink_lookup_frame(ring, n);

        return hdr->nm_status == NL_MMAP_STATUS_UNUSED;
}

static unsigned int netlink_poll(struct file *file, struct socket *sock,
                                 poll_table *wait)
{
        struct sock *sk = sock->sk;
        struct netlink_sock *nlk = nlk_sk(sk);
        unsigned int mask;
        int err;

        if (nlk->rx_ring.pg_vec != NULL) {
                /* Memory mapped sockets don't call recvmsg(), so flow control
                 * for dumps is performed here. A dump is allowed to continue
                 * if at least half the ring is unused.
                 */
                while (nlk->cb_running && netlink_dump_space(nlk)) {
                        err = netlink_dump(sk);
                        if (err < 0) {
                                sk->sk_err = -err;
                                sk->sk_error_report(sk);
                                break;
                        }
                }
                netlink_rcv_wake(sk);
        }

        mask = datagram_poll(file, sock, wait);

        spin_lock_bh(&sk->sk_receive_queue.lock);
        if (nlk->rx_ring.pg_vec) {
                netlink_forward_ring(&nlk->rx_ring);
                if (!netlink_previous_frame(&nlk->rx_ring, NL_MMAP_STATUS_UNUSED))
                        mask |= POLLIN | POLLRDNORM;
        }
        spin_unlock_bh(&sk->sk_receive_queue.lock);

        spin_lock_bh(&sk->sk_write_queue.lock);
        if (nlk->tx_ring.pg_vec) {
                if (netlink_current_frame(&nlk->tx_ring, NL_MMAP_STATUS_UNUSED))
                        mask |= POLLOUT | POLLWRNORM;
        }
        spin_unlock_bh(&sk->sk_write_queue.lock);

        return mask;
}

static struct nl_mmap_hdr *netlink_mmap_hdr(struct sk_buff *skb)
{
        return (struct nl_mmap_hdr *)(skb->head - NL_MMAP_HDRLEN);
}

static void netlink_ring_setup_skb(struct sk_buff *skb, struct sock *sk,
                                   struct netlink_ring *ring,
                                   struct nl_mmap_hdr *hdr)
{
        unsigned int size;
        void *data;

        size = ring->frame_size - NL_MMAP_HDRLEN;
        data = (void *)hdr + NL_MMAP_HDRLEN;

        skb->head       = data;
        skb->data       = data;
        skb_reset_tail_pointer(skb);
        skb->end        = skb->tail + size;
        skb->len        = 0;

        skb->destructor = netlink_skb_destructor;
        NETLINK_CB(skb).flags |= NETLINK_SKB_MMAPED;
        NETLINK_CB(skb).sk = sk;
}

static int netlink_mmap_sendmsg(struct sock *sk, struct msghdr *msg,
                                u32 dst_portid, u32 dst_group,
                                struct scm_cookie *scm)
{
        struct netlink_sock *nlk = nlk_sk(sk);
        struct netlink_ring *ring;
        struct nl_mmap_hdr *hdr;
        struct sk_buff *skb;
        unsigned int maxlen;
        int err = 0, len = 0;

        mutex_lock(&nlk->pg_vec_lock);

        ring   = &nlk->tx_ring;
        maxlen = ring->frame_size - NL_MMAP_HDRLEN;

        do {
                unsigned int nm_len;

                hdr = netlink_current_frame(ring, NL_MMAP_STATUS_VALID);
                if (hdr == NULL) {
                        if (!(msg->msg_flags & MSG_DONTWAIT) &&
                            atomic_read(&nlk->tx_ring.pending))
                                schedule();
                        continue;
                }

                nm_len = ACCESS_ONCE(hdr->nm_len);
                if (nm_len > maxlen) {
                        err = -EINVAL;
                        goto out;
                }

                netlink_frame_flush_dcache(hdr, nm_len);

                skb = alloc_skb(nm_len, GFP_KERNEL);
                if (skb == NULL) {
                        err = -ENOBUFS;
                        goto out;
                }
                __skb_put(skb, nm_len);
                memcpy(skb->data, (void *)hdr + NL_MMAP_HDRLEN, nm_len);
                netlink_set_status(hdr, NL_MMAP_STATUS_UNUSED);

                netlink_increment_head(ring);

                NETLINK_CB(skb).portid    = nlk->portid;
                NETLINK_CB(skb).dst_group = dst_group;
                NETLINK_CB(skb).creds     = scm->creds;

                err = security_netlink_send(sk, skb);
                if (err) {
                        kfree_skb(skb);
                        goto out;
                }

                if (unlikely(dst_group)) {
                        atomic_inc(&skb->users);
                        netlink_broadcast(sk, skb, dst_portid, dst_group,
                                          GFP_KERNEL);
                }
                err = netlink_unicast(sk, skb, dst_portid,
                                      msg->msg_flags & MSG_DONTWAIT);
                if (err < 0)
                        goto out;
                len += err;

        } while (hdr != NULL ||
                 (!(msg->msg_flags & MSG_DONTWAIT) &&
                  atomic_read(&nlk->tx_ring.pending)));

        if (len > 0)
                err = len;
out:
        mutex_unlock(&nlk->pg_vec_lock);
        return err;
}

static void netlink_queue_mmaped_skb(struct sock *sk, struct sk_buff *skb)
{
        struct nl_mmap_hdr *hdr;

        hdr = netlink_mmap_hdr(skb);
        hdr->nm_len     = skb->len;
        hdr->nm_group   = NETLINK_CB(skb).dst_group;
        hdr->nm_pid     = NETLINK_CB(skb).creds.pid;
        hdr->nm_uid     = from_kuid(sk_user_ns(sk), NETLINK_CB(skb).creds.uid);
        hdr->nm_gid     = from_kgid(sk_user_ns(sk), NETLINK_CB(skb).creds.gid);
        netlink_frame_flush_dcache(hdr, hdr->nm_len);
        netlink_set_status(hdr, NL_MMAP_STATUS_VALID);

        NETLINK_CB(skb).flags |= NETLINK_SKB_DELIVERED;
        kfree_skb(skb);
}

static void netlink_ring_set_copied(struct sock *sk, struct sk_buff *skb)
{
        struct netlink_sock *nlk = nlk_sk(sk);
        struct netlink_ring *ring = &nlk->rx_ring;
        struct nl_mmap_hdr *hdr;

        spin_lock_bh(&sk->sk_receive_queue.lock);
        hdr = netlink_current_frame(ring, NL_MMAP_STATUS_UNUSED);
        if (hdr == NULL) {
                spin_unlock_bh(&sk->sk_receive_queue.lock);
                kfree_skb(skb);
                netlink_overrun(sk);
                return;
        }
        netlink_increment_head(ring);
        __skb_queue_tail(&sk->sk_receive_queue, skb);
        spin_unlock_bh(&sk->sk_receive_queue.lock);

        hdr->nm_len     = skb->len;
        hdr->nm_group   = NETLINK_CB(skb).dst_group;
        hdr->nm_pid     = NETLINK_CB(skb).creds.pid;
        hdr->nm_uid     = from_kuid(sk_user_ns(sk), NETLINK_CB(skb).creds.uid);
        hdr->nm_gid     = from_kgid(sk_user_ns(sk), NETLINK_CB(skb).creds.gid);
        netlink_set_status(hdr, NL_MMAP_STATUS_COPY);
}

#else /* CONFIG_NETLINK_MMAP */
#define netlink_skb_is_mmaped(skb)      false
#define netlink_rx_is_mmaped(sk)        false
#define netlink_tx_is_mmaped(sk)        false
#define netlink_mmap                    sock_no_mmap
#define netlink_poll                    datagram_poll
#define netlink_mmap_sendmsg(sk, msg, dst_portid, dst_group, scm)       0
#endif /* CONFIG_NETLINK_MMAP */

static void netlink_skb_destructor(struct sk_buff *skb)
{
#ifdef CONFIG_NETLINK_MMAP
        struct nl_mmap_hdr *hdr;
        struct netlink_ring *ring;
        struct sock *sk;

        /* If a packet from the kernel to userspace was freed because of an
         * error without being delivered to userspace, the kernel must reset
         * the status. In the direction userspace to kernel, the status is
         * always reset here after the packet was processed and freed.
         */
        if (netlink_skb_is_mmaped(skb)) {
                hdr = netlink_mmap_hdr(skb);
                sk = NETLINK_CB(skb).sk;

                if (NETLINK_CB(skb).flags & NETLINK_SKB_TX) {
                        netlink_set_status(hdr, NL_MMAP_STATUS_UNUSED);
                        ring = &nlk_sk(sk)->tx_ring;
                } else {
                        if (!(NETLINK_CB(skb).flags & NETLINK_SKB_DELIVERED)) {
                                hdr->nm_len = 0;
                                netlink_set_status(hdr, NL_MMAP_STATUS_VALID);
                        }
                        ring = &nlk_sk(sk)->rx_ring;
                }

                WARN_ON(atomic_read(&ring->pending) == 0);
                atomic_dec(&ring->pending);
                sock_put(sk);

                skb->head = NULL;
        }
#endif
        if (is_vmalloc_addr(skb->head)) {
                if (!skb->cloned ||
                    !atomic_dec_return(&(skb_shinfo(skb)->dataref)))
                        vfree(skb->head);

                skb->head = NULL;
        }
        if (skb->sk != NULL)
                sock_rfree(skb);
}

static void netlink_skb_set_owner_r(struct sk_buff *skb, struct sock *sk)
{
        WARN_ON(skb->sk != NULL);
        skb->sk = sk;
        skb->destructor = netlink_skb_destructor;
        atomic_add(skb->truesize, &sk->sk_rmem_alloc);
        sk_mem_charge(sk, skb->truesize);
}

static void netlink_sock_destruct(struct sock *sk)
{
        struct netlink_sock *nlk = nlk_sk(sk);

        if (nlk->cb_running) {
                if (nlk->cb.done)
                        nlk->cb.done(&nlk->cb);

                module_put(nlk->cb.module);
                kfree_skb(nlk->cb.skb);
        }

        skb_queue_purge(&sk->sk_receive_queue);
#ifdef CONFIG_NETLINK_MMAP
        if (1) {
                struct nl_mmap_req req;

                memset(&req, 0, sizeof(req));
                if (nlk->rx_ring.pg_vec)
                        netlink_set_ring(sk, &req, true, false);
                memset(&req, 0, sizeof(req));
                if (nlk->tx_ring.pg_vec)
                        netlink_set_ring(sk, &req, true, true);
        }
#endif /* CONFIG_NETLINK_MMAP */

        if (!sock_flag(sk, SOCK_DEAD)) {
                printk(KERN_ERR "Freeing alive netlink socket %p\n", sk);
                return;
        }

        WARN_ON(atomic_read(&sk->sk_rmem_alloc));
        WARN_ON(atomic_read(&sk->sk_wmem_alloc));
        WARN_ON(nlk_sk(sk)->groups);
}

/* This lock without WQ_FLAG_EXCLUSIVE is good on UP and it is _very_ bad on
 * SMP. Look, when several writers sleep and reader wakes them up, all but one
 * immediately hit write lock and grab all the cpus. Exclusive sleep solves
 * this, _but_ remember, it adds useless work on UP machines.
 */

void netlink_table_grab(void)
        __acquires(nl_table_lock)
{
        might_sleep();

        write_lock_irq(&nl_table_lock);

        if (atomic_read(&nl_table_users)) {
                DECLARE_WAITQUEUE(wait, current);

                add_wait_queue_exclusive(&nl_table_wait, &wait);
                for (;;) {
                        set_current_state(TASK_UNINTERRUPTIBLE);
                        if (atomic_read(&nl_table_users) == 0)
                                break;
                        write_unlock_irq(&nl_table_lock);
                        schedule();
                        write_lock_irq(&nl_table_lock);
                }

                __set_current_state(TASK_RUNNING);
                remove_wait_queue(&nl_table_wait, &wait);
        }
}

void netlink_table_ungrab(void)
        __releases(nl_table_lock)
{
        write_unlock_irq(&nl_table_lock);
        wake_up(&nl_table_wait);
}

static inline void
netlink_lock_table(void)
{
        /* read_lock() synchronizes us to netlink_table_grab */

        read_lock(&nl_table_lock);
        atomic_inc(&nl_table_users);
        read_unlock(&nl_table_lock);
}

static inline void
netlink_unlock_table(void)
{
        if (atomic_dec_and_test(&nl_table_users))
                wake_up(&nl_table_wait);
}

struct netlink_compare_arg
{
        possible_net_t pnet;
        u32 portid;
};

/* Doing sizeof directly may yield 4 extra bytes on 64-bit. */
#define netlink_compare_arg_len \
        (offsetof(struct netlink_compare_arg, portid) + sizeof(u32))

static inline int netlink_compare(struct rhashtable_compare_arg *arg,
                                  const void *ptr)
{
        const struct netlink_compare_arg *x = arg->key;
        const struct netlink_sock *nlk = ptr;

        return nlk->portid != x->portid ||
               !net_eq(sock_net(&nlk->sk), read_pnet(&x->pnet));
}

static void netlink_compare_arg_init(struct netlink_compare_arg *arg,
                                     struct net *net, u32 portid)
{
        memset(arg, 0, sizeof(*arg));
        write_pnet(&arg->pnet, net);
        arg->portid = portid;
}
 
 static struct sock *__netlink_lookup(struct netlink_table *table, u32 portid,
                                      struct net *net)
 {
         struct netlink_compare_arg arg;
 
         netlink_compare_arg_init(&arg, net, portid);
         return rhashtable_lookup_fast(&table->hash, &arg,
                                       netlink_rhashtable_params);
 }
 
 static int __netlink_insert(struct netlink_table *table, struct sock *sk)
 {
         struct netlink_compare_arg arg;
 
         netlink_compare_arg_init(&arg, sock_net(sk), nlk_sk(sk)->portid);
         return rhashtable_lookup_insert_key(&table->hash, &arg,
                                             &nlk_sk(sk)->node,
                                             netlink_rhashtable_params);
 }
 
 static struct sock *netlink_lookup(struct net *net, int protocol, u32 portid)
 {
         struct netlink_table *table = &nl_table[protocol];
         struct sock *sk;
 
         rcu_read_lock();
         sk = __netlink_lookup(table, portid, net);
         if (sk)
                 sock_hold(sk);
         rcu_read_unlock();
 
         return sk;
 }
 
 static const struct proto_ops netlink_ops;
 
 static void
 netlink_update_listeners(struct sock *sk)
 {
         struct netlink_table *tbl = &nl_table[sk->sk_protocol];
         unsigned long mask;
         unsigned int i;
         struct listeners *listeners;
 
         listeners = nl_deref_protected(tbl->listeners);
         if (!listeners)
                 return;
 
         for (i = 0; i < NLGRPLONGS(tbl->groups); i++) {
                 mask = 0;
                 sk_for_each_bound(sk, &tbl->mc_list) {
                         if (i < NLGRPLONGS(nlk_sk(sk)->ngroups))
                                 mask |= nlk_sk(sk)->groups[i];
                 }
                 listeners->masks[i] = mask;
         }
         /* this function is only called with the netlink table "grabbed", which
          * makes sure updates are visible before bind or setsockopt return. */
 }
 
 static int netlink_insert(struct sock *sk, u32 portid)
 {
         struct netlink_table *table = &nl_table[sk->sk_protocol];
         int err;
 
         lock_sock(sk);
 
         err = -EBUSY;
         if (nlk_sk(sk)->portid)
                 goto err;
 
         err = -ENOMEM;
         if (BITS_PER_LONG > 32 &&
             unlikely(atomic_read(&table->hash.nelems) >= UINT_MAX))
                 goto err;
 
         nlk_sk(sk)->portid = portid;
         sock_hold(sk);
 
         err = __netlink_insert(table, sk);
         if (err) {
                 if (err == -EEXIST)
                         err = -EADDRINUSE;
                 nlk_sk(sk)->portid = 0;
                 sock_put(sk);
         }
 
 err:
         release_sock(sk);
         return err;
 }
 
 static void netlink_remove(struct sock *sk)
 {
         struct netlink_table *table;
 
         table = &nl_table[sk->sk_protocol];
         if (!rhashtable_remove_fast(&table->hash, &nlk_sk(sk)->node,
                                     netlink_rhashtable_params)) {
                 WARN_ON(atomic_read(&sk->sk_refcnt) == 1);
                 __sock_put(sk);
         }
 
         netlink_table_grab();
         if (nlk_sk(sk)->subscriptions) {
                 __sk_del_bind_node(sk);
                 netlink_update_listeners(sk);
         }
         if (sk->sk_protocol == NETLINK_GENERIC)
                 atomic_inc(&genl_sk_destructing_cnt);
         netlink_table_ungrab();
 }
 
 static struct proto netlink_proto = {
         .name     = "NETLINK",
         .owner    = THIS_MODULE,
         .obj_size = sizeof(struct netlink_sock),
 };
 
 static int __netlink_create(struct net *net, struct socket *sock,
                             struct mutex *cb_mutex, int protocol)
 {
         struct sock *sk;
         struct netlink_sock *nlk;
 
         sock->ops = &netlink_ops;
 
         sk = sk_alloc(net, PF_NETLINK, GFP_KERNEL, &netlink_proto);
         if (!sk)
                 return -ENOMEM;
 
         sock_init_data(sock, sk);
 
         nlk = nlk_sk(sk);
         if (cb_mutex) {
                 nlk->cb_mutex = cb_mutex;
         } else {
                 nlk->cb_mutex = &nlk->cb_def_mutex;
                 mutex_init(nlk->cb_mutex);
         }
         init_waitqueue_head(&nlk->wait);
 #ifdef CONFIG_NETLINK_MMAP
         mutex_init(&nlk->pg_vec_lock);
 #endif
 
         sk->sk_destruct = netlink_sock_destruct;
         sk->sk_protocol = protocol;
         return 0;
 }
 
 static int netlink_create(struct net *net, struct socket *sock, int protocol,
                           int kern)
 {
         struct module *module = NULL;
         struct mutex *cb_mutex;
         struct netlink_sock *nlk;
         int (*bind)(struct net *net, int group);
         void (*unbind)(struct net *net, int group);
         int err = 0;
 
         sock->state = SS_UNCONNECTED;
 
         if (sock->type != SOCK_RAW && sock->type != SOCK_DGRAM)
                 return -ESOCKTNOSUPPORT;
 
         if (protocol < 0 || protocol >= MAX_LINKS)
                 return -EPROTONOSUPPORT;
 
         netlink_lock_table();
 #ifdef CONFIG_MODULES
         if (!nl_table[protocol].registered) {
                 netlink_unlock_table();
                 request_module("net-pf-%d-proto-%d", PF_NETLINK, protocol);
                 netlink_lock_table();
         }
 #endif
         if (nl_table[protocol].registered &&
             try_module_get(nl_table[protocol].module))
                 module = nl_table[protocol].module;
         else
                 err = -EPROTONOSUPPORT;
         cb_mutex = nl_table[protocol].cb_mutex;
         bind = nl_table[protocol].bind;
         unbind = nl_table[protocol].unbind;
         netlink_unlock_table();
 
         if (err < 0)
                 goto out;
 
         err = __netlink_create(net, sock, cb_mutex, protocol);
         if (err < 0)
                 goto out_module;
 
         local_bh_disable();
         sock_prot_inuse_add(net, &netlink_proto, 1);
         local_bh_enable();
 
         nlk = nlk_sk(sock->sk);
         nlk->module = module;
         nlk->netlink_bind = bind;
         nlk->netlink_unbind = unbind;
 out:
         return err;
 
 out_module:
         module_put(module);
         goto out;
 }
 
 static void deferred_put_nlk_sk(struct rcu_head *head)
 {
         struct netlink_sock *nlk = container_of(head, struct netlink_sock, rcu);
 
         sock_put(&nlk->sk);
 }
 
 static int netlink_release(struct socket *sock)
 {
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk;
 
         if (!sk)
                 return 0;
 
         netlink_remove(sk);
         sock_orphan(sk);
         nlk = nlk_sk(sk);
 
         /*
          * OK. Socket is unlinked, any packets that arrive now
          * will be purged.
          */
 
         /* must not acquire netlink_table_lock in any way again before unbind
          * and notifying genetlink is done as otherwise it might deadlock
          */
         if (nlk->netlink_unbind) {
                 int i;
 
                 for (i = 0; i < nlk->ngroups; i++)
                         if (test_bit(i, nlk->groups))
                                 nlk->netlink_unbind(sock_net(sk), i + 1);
         }
         if (sk->sk_protocol == NETLINK_GENERIC &&
             atomic_dec_return(&genl_sk_destructing_cnt) == 0)
                 wake_up(&genl_sk_destructing_waitq);
 
         sock->sk = NULL;
         wake_up_interruptible_all(&nlk->wait);
 
         skb_queue_purge(&sk->sk_write_queue);
 
         if (nlk->portid) {
                 struct netlink_notify n = {
                                                 .net = sock_net(sk),
                                                 .protocol = sk->sk_protocol,
                                                 .portid = nlk->portid,
                                           };
                 atomic_notifier_call_chain(&netlink_chain,
                                 NETLINK_URELEASE, &n);
         }
 
         module_put(nlk->module);
 
         if (netlink_is_kernel(sk)) {
                 netlink_table_grab();
                 BUG_ON(nl_table[sk->sk_protocol].registered == 0);
                 if (--nl_table[sk->sk_protocol].registered == 0) {
                         struct listeners *old;
 
                         old = nl_deref_protected(nl_table[sk->sk_protocol].listeners);
                         RCU_INIT_POINTER(nl_table[sk->sk_protocol].listeners, NULL);
                         kfree_rcu(old, rcu);
                         nl_table[sk->sk_protocol].module = NULL;
                         nl_table[sk->sk_protocol].bind = NULL;
                         nl_table[sk->sk_protocol].unbind = NULL;
                         nl_table[sk->sk_protocol].flags = 0;
                         nl_table[sk->sk_protocol].registered = 0;
                 }
                 netlink_table_ungrab();
         }
 
         kfree(nlk->groups);
         nlk->groups = NULL;
 
         local_bh_disable();
         sock_prot_inuse_add(sock_net(sk), &netlink_proto, -1);
         local_bh_enable();
         call_rcu(&nlk->rcu, deferred_put_nlk_sk);
         return 0;
 }
 
 static int netlink_autobind(struct socket *sock)
 {
         struct sock *sk = sock->sk;
         struct net *net = sock_net(sk);
         struct netlink_table *table = &nl_table[sk->sk_protocol];
         s32 portid = task_tgid_vnr(current);
         int err;
         static s32 rover = -4097;
 
 retry:
         cond_resched();
         rcu_read_lock();
         if (__netlink_lookup(table, portid, net)) {
                 /* Bind collision, search negative portid values. */
                 portid = rover--;
                 if (rover > -4097)
                         rover = -4097;
                 rcu_read_unlock();
                 goto retry;
         }
         rcu_read_unlock();
 
         err = netlink_insert(sk, portid);
         if (err == -EADDRINUSE)
                 goto retry;
 
         /* If 2 threads race to autobind, that is fine.  */
         if (err == -EBUSY)
                 err = 0;
 
         return err;
 }
 
 /**
  * __netlink_ns_capable - General netlink message capability test
  * @nsp: NETLINK_CB of the socket buffer holding a netlink command from userspace.
  * @user_ns: The user namespace of the capability to use
  * @cap: The capability to use
  *
  * Test to see if the opener of the socket we received the message
  * from had when the netlink socket was created and the sender of the
  * message has has the capability @cap in the user namespace @user_ns.
  */
 bool __netlink_ns_capable(const struct netlink_skb_parms *nsp,
                         struct user_namespace *user_ns, int cap)
 {
         return ((nsp->flags & NETLINK_SKB_DST) ||
                 file_ns_capable(nsp->sk->sk_socket->file, user_ns, cap)) &&
                 ns_capable(user_ns, cap);
 }
 EXPORT_SYMBOL(__netlink_ns_capable);
 
 /**
  * netlink_ns_capable - General netlink message capability test
  * @skb: socket buffer holding a netlink command from userspace
  * @user_ns: The user namespace of the capability to use
  * @cap: The capability to use
  *
  * Test to see if the opener of the socket we received the message
  * from had when the netlink socket was created and the sender of the
  * message has has the capability @cap in the user namespace @user_ns.
  */
 bool netlink_ns_capable(const struct sk_buff *skb,
                         struct user_namespace *user_ns, int cap)
 {
         return __netlink_ns_capable(&NETLINK_CB(skb), user_ns, cap);
 }
 EXPORT_SYMBOL(netlink_ns_capable);
 
 /**
  * netlink_capable - Netlink global message capability test
  * @skb: socket buffer holding a netlink command from userspace
  * @cap: The capability to use
  *
  * Test to see if the opener of the socket we received the message
  * from had when the netlink socket was created and the sender of the
  * message has has the capability @cap in all user namespaces.
  */
 bool netlink_capable(const struct sk_buff *skb, int cap)
 {
         return netlink_ns_capable(skb, &init_user_ns, cap);
 }
 EXPORT_SYMBOL(netlink_capable);
 
 /**
  * netlink_net_capable - Netlink network namespace message capability test
  * @skb: socket buffer holding a netlink command from userspace
  * @cap: The capability to use
  *
  * Test to see if the opener of the socket we received the message
  * from had when the netlink socket was created and the sender of the
  * message has has the capability @cap over the network namespace of
  * the socket we received the message from.
  */
 bool netlink_net_capable(const struct sk_buff *skb, int cap)
 {
         return netlink_ns_capable(skb, sock_net(skb->sk)->user_ns, cap);
 }
 EXPORT_SYMBOL(netlink_net_capable);
 
 static inline int netlink_allowed(const struct socket *sock, unsigned int flag)
 {
         return (nl_table[sock->sk->sk_protocol].flags & flag) ||
                 ns_capable(sock_net(sock->sk)->user_ns, CAP_NET_ADMIN);
 }
 
 static void
 netlink_update_subscriptions(struct sock *sk, unsigned int subscriptions)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
 
         if (nlk->subscriptions && !subscriptions)
                 __sk_del_bind_node(sk);
         else if (!nlk->subscriptions && subscriptions)
                 sk_add_bind_node(sk, &nl_table[sk->sk_protocol].mc_list);
         nlk->subscriptions = subscriptions;
 }
 
 static int netlink_realloc_groups(struct sock *sk)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
         unsigned int groups;
         unsigned long *new_groups;
         int err = 0;
 
         netlink_table_grab();
 
         groups = nl_table[sk->sk_protocol].groups;
         if (!nl_table[sk->sk_protocol].registered) {
                 err = -ENOENT;
                 goto out_unlock;
         }
 
         if (nlk->ngroups >= groups)
                 goto out_unlock;
 
         new_groups = krealloc(nlk->groups, NLGRPSZ(groups), GFP_ATOMIC);
         if (new_groups == NULL) {
                 err = -ENOMEM;
                 goto out_unlock;
         }
         memset((char *)new_groups + NLGRPSZ(nlk->ngroups), 0,
                NLGRPSZ(groups) - NLGRPSZ(nlk->ngroups));
 
         nlk->groups = new_groups;
         nlk->ngroups = groups;
  out_unlock:
         netlink_table_ungrab();
         return err;
 }
 
 static void netlink_undo_bind(int group, long unsigned int groups,
                               struct sock *sk)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
         int undo;
 
         if (!nlk->netlink_unbind)
                 return;
 
         for (undo = 0; undo < group; undo++)
                 if (test_bit(undo, &groups))
                         nlk->netlink_unbind(sock_net(sk), undo + 1);
 }
 
 static int netlink_bind(struct socket *sock, struct sockaddr *addr,
                         int addr_len)
 {
         struct sock *sk = sock->sk;
         struct net *net = sock_net(sk);
         struct netlink_sock *nlk = nlk_sk(sk);
         struct sockaddr_nl *nladdr = (struct sockaddr_nl *)addr;
         int err;
         long unsigned int groups = nladdr->nl_groups;
 
         if (addr_len < sizeof(struct sockaddr_nl))
                 return -EINVAL;
 
         if (nladdr->nl_family != AF_NETLINK)
                 return -EINVAL;
 
         /* Only superuser is allowed to listen multicasts */
         if (groups) {
                 if (!netlink_allowed(sock, NL_CFG_F_NONROOT_RECV))
                         return -EPERM;
                 err = netlink_realloc_groups(sk);
                 if (err)
                         return err;
         }
 
         if (nlk->portid)
                 if (nladdr->nl_pid != nlk->portid)
                         return -EINVAL;
 
         if (nlk->netlink_bind && groups) {
                 int group;
 
                 for (group = 0; group < nlk->ngroups; group++) {
                         if (!test_bit(group, &groups))
                                 continue;
                         err = nlk->netlink_bind(net, group + 1);
                         if (!err)
                                 continue;
                         netlink_undo_bind(group, groups, sk);
                         return err;
                 }
         }
 
         if (!nlk->portid) {
                 err = nladdr->nl_pid ?
                         netlink_insert(sk, nladdr->nl_pid) :
                         netlink_autobind(sock);
                 if (err) {
                         netlink_undo_bind(nlk->ngroups, groups, sk);
                         return err;
                 }
         }
 
         if (!groups && (nlk->groups == NULL || !(u32)nlk->groups[0]))
                 return 0;
 
         netlink_table_grab();
         netlink_update_subscriptions(sk, nlk->subscriptions +
                                          hweight32(groups) -
                                          hweight32(nlk->groups[0]));
         nlk->groups[0] = (nlk->groups[0] & ~0xffffffffUL) | groups;
         netlink_update_listeners(sk);
         netlink_table_ungrab();
 
         return 0;
 }
 
 static int netlink_connect(struct socket *sock, struct sockaddr *addr,
                            int alen, int flags)
 {
         int err = 0;
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         struct sockaddr_nl *nladdr = (struct sockaddr_nl *)addr;
 
         if (alen < sizeof(addr->sa_family))
                 return -EINVAL;
 
         if (addr->sa_family == AF_UNSPEC) {
                 sk->sk_state    = NETLINK_UNCONNECTED;
                 nlk->dst_portid = 0;
                 nlk->dst_group  = 0;
                 return 0;
         }
         if (addr->sa_family != AF_NETLINK)
                 return -EINVAL;
 
         if ((nladdr->nl_groups || nladdr->nl_pid) &&
             !netlink_allowed(sock, NL_CFG_F_NONROOT_SEND))
                 return -EPERM;
 
         if (!nlk->portid)
                 err = netlink_autobind(sock);
 
         if (err == 0) {
                 sk->sk_state    = NETLINK_CONNECTED;
                 nlk->dst_portid = nladdr->nl_pid;
                 nlk->dst_group  = ffs(nladdr->nl_groups);
         }
 
         return err;
 }
 
 static int netlink_getname(struct socket *sock, struct sockaddr *addr,
                            int *addr_len, int peer)
 {
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         DECLARE_SOCKADDR(struct sockaddr_nl *, nladdr, addr);
 
         nladdr->nl_family = AF_NETLINK;
         nladdr->nl_pad = 0;
         *addr_len = sizeof(*nladdr);
 
         if (peer) {
                 nladdr->nl_pid = nlk->dst_portid;
                 nladdr->nl_groups = netlink_group_mask(nlk->dst_group);
         } else {
                 nladdr->nl_pid = nlk->portid;
                 nladdr->nl_groups = nlk->groups ? nlk->groups[0] : 0;
         }
         return 0;
 }
 
 static struct sock *netlink_getsockbyportid(struct sock *ssk, u32 portid)
 {
         struct sock *sock;
         struct netlink_sock *nlk;
 
         sock = netlink_lookup(sock_net(ssk), ssk->sk_protocol, portid);
         if (!sock)
                 return ERR_PTR(-ECONNREFUSED);
 
         /* Don't bother queuing skb if kernel socket has no input function */
         nlk = nlk_sk(sock);
         if (sock->sk_state == NETLINK_CONNECTED &&
             nlk->dst_portid != nlk_sk(ssk)->portid) {
                 sock_put(sock);
                 return ERR_PTR(-ECONNREFUSED);
         }
         return sock;
 }
 
 struct sock *netlink_getsockbyfilp(struct file *filp)
 {
         struct inode *inode = file_inode(filp);
         struct sock *sock;
 
         if (!S_ISSOCK(inode->i_mode))
                 return ERR_PTR(-ENOTSOCK);
 
         sock = SOCKET_I(inode)->sk;
         if (sock->sk_family != AF_NETLINK)
                 return ERR_PTR(-EINVAL);
 
         sock_hold(sock);
         return sock;
 }
 
 static struct sk_buff *netlink_alloc_large_skb(unsigned int size,
                                                int broadcast)
 {
         struct sk_buff *skb;
         void *data;
 
         if (size <= NLMSG_GOODSIZE || broadcast)
                 return alloc_skb(size, GFP_KERNEL);
 
         size = SKB_DATA_ALIGN(size) +
                SKB_DATA_ALIGN(sizeof(struct skb_shared_info));
 
         data = vmalloc(size);
         if (data == NULL)
                 return NULL;
 
         skb = __build_skb(data, size);
         if (skb == NULL)
                 vfree(data);
         else
                 skb->destructor = netlink_skb_destructor;
 
         return skb;
 }
 
 /*
  * Attach a skb to a netlink socket.
  * The caller must hold a reference to the destination socket. On error, the
  * reference is dropped. The skb is not send to the destination, just all
  * all error checks are performed and memory in the queue is reserved.
  * Return values:
  * < 0: error. skb freed, reference to sock dropped.
  * 0: continue
  * 1: repeat lookup - reference dropped while waiting for socket memory.
  */
 int netlink_attachskb(struct sock *sk, struct sk_buff *skb,
                       long *timeo, struct sock *ssk)
 {
         struct netlink_sock *nlk;
 
         nlk = nlk_sk(sk);
 
         if ((atomic_read(&sk->sk_rmem_alloc) > sk->sk_rcvbuf ||
              test_bit(NETLINK_CONGESTED, &nlk->state)) &&
             !netlink_skb_is_mmaped(skb)) {
                 DECLARE_WAITQUEUE(wait, current);
                 if (!*timeo) {
                         if (!ssk || netlink_is_kernel(ssk))
                                 netlink_overrun(sk);
                         sock_put(sk);
                         kfree_skb(skb);
                         return -EAGAIN;
                 }
 
                 __set_current_state(TASK_INTERRUPTIBLE);
                 add_wait_queue(&nlk->wait, &wait);
 
                 if ((atomic_read(&sk->sk_rmem_alloc) > sk->sk_rcvbuf ||
                      test_bit(NETLINK_CONGESTED, &nlk->state)) &&
                     !sock_flag(sk, SOCK_DEAD))
                         *timeo = schedule_timeout(*timeo);
 
                 __set_current_state(TASK_RUNNING);
                 remove_wait_queue(&nlk->wait, &wait);
                 sock_put(sk);
 
                 if (signal_pending(current)) {
                         kfree_skb(skb);
                         return sock_intr_errno(*timeo);
                 }
                 return 1;
         }
         netlink_skb_set_owner_r(skb, sk);
         return 0;
 }
 
 static int __netlink_sendskb(struct sock *sk, struct sk_buff *skb)
 {
         int len = skb->len;
 
         netlink_deliver_tap(skb);
 
 #ifdef CONFIG_NETLINK_MMAP
         if (netlink_skb_is_mmaped(skb))
                 netlink_queue_mmaped_skb(sk, skb);
         else if (netlink_rx_is_mmaped(sk))
                 netlink_ring_set_copied(sk, skb);
         else
 #endif /* CONFIG_NETLINK_MMAP */
                 skb_queue_tail(&sk->sk_receive_queue, skb);
         sk->sk_data_ready(sk);
         return len;
 }
 
 int netlink_sendskb(struct sock *sk, struct sk_buff *skb)
 {
         int len = __netlink_sendskb(sk, skb);
 
         sock_put(sk);
         return len;
 }
 
 void netlink_detachskb(struct sock *sk, struct sk_buff *skb)
 {
         kfree_skb(skb);
         sock_put(sk);
 }
 
 static struct sk_buff *netlink_trim(struct sk_buff *skb, gfp_t allocation)
 {
         int delta;
 
         WARN_ON(skb->sk != NULL);
         if (netlink_skb_is_mmaped(skb))
                 return skb;
 
         delta = skb->end - skb->tail;
         if (is_vmalloc_addr(skb->head) || delta * 2 < skb->truesize)
                 return skb;
 
         if (skb_shared(skb)) {
                 struct sk_buff *nskb = skb_clone(skb, allocation);
                 if (!nskb)
                         return skb;
                 consume_skb(skb);
                 skb = nskb;
         }
 
         if (!pskb_expand_head(skb, 0, -delta, allocation))
                 skb->truesize -= delta;
 
         return skb;
 }
 
 static int netlink_unicast_kernel(struct sock *sk, struct sk_buff *skb,
                                   struct sock *ssk)
 {
         int ret;
         struct netlink_sock *nlk = nlk_sk(sk);
 
         ret = -ECONNREFUSED;
         if (nlk->netlink_rcv != NULL) {
                 ret = skb->len;
                 netlink_skb_set_owner_r(skb, sk);
                 NETLINK_CB(skb).sk = ssk;
                 netlink_deliver_tap_kernel(sk, ssk, skb);
                 nlk->netlink_rcv(skb);
                 consume_skb(skb);
         } else {
                 kfree_skb(skb);
         }
         sock_put(sk);
         return ret;
 }
 
 int netlink_unicast(struct sock *ssk, struct sk_buff *skb,
                     u32 portid, int nonblock)
 {
         struct sock *sk;
         int err;
         long timeo;
 
         skb = netlink_trim(skb, gfp_any());
 
         timeo = sock_sndtimeo(ssk, nonblock);
 retry:
         sk = netlink_getsockbyportid(ssk, portid);
         if (IS_ERR(sk)) {
                 kfree_skb(skb);
                 return PTR_ERR(sk);
         }
         if (netlink_is_kernel(sk))
                 return netlink_unicast_kernel(sk, skb, ssk);
 
         if (sk_filter(sk, skb)) {
                 err = skb->len;
                 kfree_skb(skb);
                 sock_put(sk);
                 return err;
         }
 
         err = netlink_attachskb(sk, skb, &timeo, ssk);
         if (err == 1)
                 goto retry;
         if (err)
                 return err;
 
         return netlink_sendskb(sk, skb);
 }
 EXPORT_SYMBOL(netlink_unicast);
 
 struct sk_buff *netlink_alloc_skb(struct sock *ssk, unsigned int size,
                                   u32 dst_portid, gfp_t gfp_mask)
 {
 #ifdef CONFIG_NETLINK_MMAP
         struct sock *sk = NULL;
         struct sk_buff *skb;
         struct netlink_ring *ring;
         struct nl_mmap_hdr *hdr;
         unsigned int maxlen;
 
         sk = netlink_getsockbyportid(ssk, dst_portid);
         if (IS_ERR(sk))
                 goto out;
 
         ring = &nlk_sk(sk)->rx_ring;
         /* fast-path without atomic ops for common case: non-mmaped receiver */
         if (ring->pg_vec == NULL)
                 goto out_put;
 
         if (ring->frame_size - NL_MMAP_HDRLEN < size)
                 goto out_put;
 
         skb = alloc_skb_head(gfp_mask);
         if (skb == NULL)
                 goto err1;
 
         spin_lock_bh(&sk->sk_receive_queue.lock);
         /* check again under lock */
         if (ring->pg_vec == NULL)
                 goto out_free;
 
         /* check again under lock */
         maxlen = ring->frame_size - NL_MMAP_HDRLEN;
         if (maxlen < size)
                 goto out_free;
 
         netlink_forward_ring(ring);
         hdr = netlink_current_frame(ring, NL_MMAP_STATUS_UNUSED);
         if (hdr == NULL)
                 goto err2;
         netlink_ring_setup_skb(skb, sk, ring, hdr);
         netlink_set_status(hdr, NL_MMAP_STATUS_RESERVED);
         atomic_inc(&ring->pending);
         netlink_increment_head(ring);
 
         spin_unlock_bh(&sk->sk_receive_queue.lock);
         return skb;
 
 err2:
         kfree_skb(skb);
         spin_unlock_bh(&sk->sk_receive_queue.lock);
         netlink_overrun(sk);
 err1:
         sock_put(sk);
         return NULL;
 
 out_free:
         kfree_skb(skb);
         spin_unlock_bh(&sk->sk_receive_queue.lock);
 out_put:
         sock_put(sk);
 out:
 #endif
         return alloc_skb(size, gfp_mask);
 }
 EXPORT_SYMBOL_GPL(netlink_alloc_skb);
 
 int netlink_has_listeners(struct sock *sk, unsigned int group)
 {
         int res = 0;
         struct listeners *listeners;
 
         BUG_ON(!netlink_is_kernel(sk));
 
         rcu_read_lock();
         listeners = rcu_dereference(nl_table[sk->sk_protocol].listeners);
 
         if (listeners && group - 1 < nl_table[sk->sk_protocol].groups)
                 res = test_bit(group - 1, listeners->masks);
 
         rcu_read_unlock();
 
         return res;
 }
 EXPORT_SYMBOL_GPL(netlink_has_listeners);
 
 static int netlink_broadcast_deliver(struct sock *sk, struct sk_buff *skb)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
 
         if (atomic_read(&sk->sk_rmem_alloc) <= sk->sk_rcvbuf &&
             !test_bit(NETLINK_CONGESTED, &nlk->state)) {
                 netlink_skb_set_owner_r(skb, sk);
                 __netlink_sendskb(sk, skb);
                 return atomic_read(&sk->sk_rmem_alloc) > (sk->sk_rcvbuf >> 1);
         }
         return -1;
 }
 
 struct netlink_broadcast_data {
         struct sock *exclude_sk;
         struct net *net;
         u32 portid;
         u32 group;
         int failure;
         int delivery_failure;
         int congested;
         int delivered;
         gfp_t allocation;
         struct sk_buff *skb, *skb2;
         int (*tx_filter)(struct sock *dsk, struct sk_buff *skb, void *data);
         void *tx_data;
 };
 
 static void do_one_broadcast(struct sock *sk,
                                     struct netlink_broadcast_data *p)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
         int val;
 
         if (p->exclude_sk == sk)
                 return;
 
         if (nlk->portid == p->portid || p->group - 1 >= nlk->ngroups ||
             !test_bit(p->group - 1, nlk->groups))
                 return;
 
         if (!net_eq(sock_net(sk), p->net))
                 return;
 
         if (p->failure) {
                 netlink_overrun(sk);
                 return;
         }
 
         sock_hold(sk);
         if (p->skb2 == NULL) {
                 if (skb_shared(p->skb)) {
                         p->skb2 = skb_clone(p->skb, p->allocation);
                 } else {
                         p->skb2 = skb_get(p->skb);
                         /*
                          * skb ownership may have been set when
                          * delivered to a previous socket.
                          */
                         skb_orphan(p->skb2);
                 }
         }
         if (p->skb2 == NULL) {
                 netlink_overrun(sk);
                 /* Clone failed. Notify ALL listeners. */
                 p->failure = 1;
                 if (nlk->flags & NETLINK_BROADCAST_SEND_ERROR)
                         p->delivery_failure = 1;
         } else if (p->tx_filter && p->tx_filter(sk, p->skb2, p->tx_data)) {
                 kfree_skb(p->skb2);
                 p->skb2 = NULL;
         } else if (sk_filter(sk, p->skb2)) {
                 kfree_skb(p->skb2);
                 p->skb2 = NULL;
         } else if ((val = netlink_broadcast_deliver(sk, p->skb2)) < 0) {
                 netlink_overrun(sk);
                 if (nlk->flags & NETLINK_BROADCAST_SEND_ERROR)
                         p->delivery_failure = 1;
         } else {
                 p->congested |= val;
                 p->delivered = 1;
                 p->skb2 = NULL;
         }
         sock_put(sk);
 }
 
 int netlink_broadcast_filtered(struct sock *ssk, struct sk_buff *skb, u32 portid,
         u32 group, gfp_t allocation,
         int (*filter)(struct sock *dsk, struct sk_buff *skb, void *data),
         void *filter_data)
 {
         struct net *net = sock_net(ssk);
         struct netlink_broadcast_data info;
         struct sock *sk;
 
         skb = netlink_trim(skb, allocation);
 
         info.exclude_sk = ssk;
         info.net = net;
         info.portid = portid;
         info.group = group;
         info.failure = 0;
         info.delivery_failure = 0;
         info.congested = 0;
         info.delivered = 0;
         info.allocation = allocation;
         info.skb = skb;
         info.skb2 = NULL;
         info.tx_filter = filter;
         info.tx_data = filter_data;
 
         /* While we sleep in clone, do not allow to change socket list */
 
         netlink_lock_table();
 
         sk_for_each_bound(sk, &nl_table[ssk->sk_protocol].mc_list)
                 do_one_broadcast(sk, &info);
 
         consume_skb(skb);
 
         netlink_unlock_table();
 
         if (info.delivery_failure) {
                 kfree_skb(info.skb2);
                 return -ENOBUFS;
         }
         consume_skb(info.skb2);
 
         if (info.delivered) {
                 if (info.congested && (allocation & __GFP_WAIT))
                         yield();
                 return 0;
         }
         return -ESRCH;
 }
 EXPORT_SYMBOL(netlink_broadcast_filtered);
 
 int netlink_broadcast(struct sock *ssk, struct sk_buff *skb, u32 portid,
                       u32 group, gfp_t allocation)
 {
         return netlink_broadcast_filtered(ssk, skb, portid, group, allocation,
                 NULL, NULL);
 }
 EXPORT_SYMBOL(netlink_broadcast);
 
 struct netlink_set_err_data {
         struct sock *exclude_sk;
         u32 portid;
         u32 group;
         int code;
 };
 
 static int do_one_set_err(struct sock *sk, struct netlink_set_err_data *p)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
         int ret = 0;
 
         if (sk == p->exclude_sk)
                 goto out;
 
         if (!net_eq(sock_net(sk), sock_net(p->exclude_sk)))
                 goto out;
 
         if (nlk->portid == p->portid || p->group - 1 >= nlk->ngroups ||
             !test_bit(p->group - 1, nlk->groups))
                 goto out;
 
         if (p->code == ENOBUFS && nlk->flags & NETLINK_RECV_NO_ENOBUFS) {
                 ret = 1;
                 goto out;
         }
 
         sk->sk_err = p->code;
         sk->sk_error_report(sk);
 out:
         return ret;
 }
 
 /**
  * netlink_set_err - report error to broadcast listeners
  * @ssk: the kernel netlink socket, as returned by netlink_kernel_create()
  * @portid: the PORTID of a process that we want to skip (if any)
  * @group: the broadcast group that will notice the error
  * @code: error code, must be negative (as usual in kernelspace)
  *
  * This function returns the number of broadcast listeners that have set the
  * NETLINK_RECV_NO_ENOBUFS socket option.
  */
 int netlink_set_err(struct sock *ssk, u32 portid, u32 group, int code)
 {
         struct netlink_set_err_data info;
         struct sock *sk;
         int ret = 0;
 
         info.exclude_sk = ssk;
         info.portid = portid;
         info.group = group;
         /* sk->sk_err wants a positive error value */
         info.code = -code;
 
         read_lock(&nl_table_lock);
 
         sk_for_each_bound(sk, &nl_table[ssk->sk_protocol].mc_list)
                 ret += do_one_set_err(sk, &info);
 
         read_unlock(&nl_table_lock);
         return ret;
 }
 EXPORT_SYMBOL(netlink_set_err);
 
 /* must be called with netlink table grabbed */
 static void netlink_update_socket_mc(struct netlink_sock *nlk,
                                      unsigned int group,
                                      int is_new)
 {
         int old, new = !!is_new, subscriptions;
 
         old = test_bit(group - 1, nlk->groups);
         subscriptions = nlk->subscriptions - old + new;
         if (new)
                 __set_bit(group - 1, nlk->groups);
         else
                 __clear_bit(group - 1, nlk->groups);
         netlink_update_subscriptions(&nlk->sk, subscriptions);
         netlink_update_listeners(&nlk->sk);
 }
 
 static int netlink_setsockopt(struct socket *sock, int level, int optname,
                               char __user *optval, unsigned int optlen)
 {
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         unsigned int val = 0;
         int err;
 
         if (level != SOL_NETLINK)
                 return -ENOPROTOOPT;
 
         if (optname != NETLINK_RX_RING && optname != NETLINK_TX_RING &&
             optlen >= sizeof(int) &&
             get_user(val, (unsigned int __user *)optval))
                 return -EFAULT;
 
         switch (optname) {
         case NETLINK_PKTINFO:
                 if (val)
                         nlk->flags |= NETLINK_RECV_PKTINFO;
                 else
                         nlk->flags &= ~NETLINK_RECV_PKTINFO;
                 err = 0;
                 break;
         case NETLINK_ADD_MEMBERSHIP:
         case NETLINK_DROP_MEMBERSHIP: {
                 if (!netlink_allowed(sock, NL_CFG_F_NONROOT_RECV))
                         return -EPERM;
                 err = netlink_realloc_groups(sk);
                 if (err)
                         return err;
                 if (!val || val - 1 >= nlk->ngroups)
                         return -EINVAL;
                 if (optname == NETLINK_ADD_MEMBERSHIP && nlk->netlink_bind) {
                         err = nlk->netlink_bind(sock_net(sk), val);
                         if (err)
                                 return err;
                 }
                 netlink_table_grab();
                 netlink_update_socket_mc(nlk, val,
                                          optname == NETLINK_ADD_MEMBERSHIP);
                 netlink_table_ungrab();
                 if (optname == NETLINK_DROP_MEMBERSHIP && nlk->netlink_unbind)
                         nlk->netlink_unbind(sock_net(sk), val);
 
                 err = 0;
                 break;
         }
         case NETLINK_BROADCAST_ERROR:
                 if (val)
                         nlk->flags |= NETLINK_BROADCAST_SEND_ERROR;
                 else
                         nlk->flags &= ~NETLINK_BROADCAST_SEND_ERROR;
                 err = 0;
                 break;
         case NETLINK_NO_ENOBUFS:
                 if (val) {
                         nlk->flags |= NETLINK_RECV_NO_ENOBUFS;
                         clear_bit(NETLINK_CONGESTED, &nlk->state);
                         wake_up_interruptible(&nlk->wait);
                 } else {
                         nlk->flags &= ~NETLINK_RECV_NO_ENOBUFS;
                 }
                 err = 0;
                 break;
 #ifdef CONFIG_NETLINK_MMAP
         case NETLINK_RX_RING:
         case NETLINK_TX_RING: {
                 struct nl_mmap_req req;
 
                 /* Rings might consume more memory than queue limits, require
                  * CAP_NET_ADMIN.
                  */
                 if (!capable(CAP_NET_ADMIN))
                         return -EPERM;
                 if (optlen < sizeof(req))
                         return -EINVAL;
                 if (copy_from_user(&req, optval, sizeof(req)))
                         return -EFAULT;
                 err = netlink_set_ring(sk, &req, false,
                                        optname == NETLINK_TX_RING);
                 break;
         }
 #endif /* CONFIG_NETLINK_MMAP */
         default:
                 err = -ENOPROTOOPT;
         }
         return err;
 }
 
 static int netlink_getsockopt(struct socket *sock, int level, int optname,
                               char __user *optval, int __user *optlen)
 {
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         int len, val, err;
 
         if (level != SOL_NETLINK)
                 return -ENOPROTOOPT;
 
         if (get_user(len, optlen))
                 return -EFAULT;
         if (len < 0)
                 return -EINVAL;
 
         switch (optname) {
         case NETLINK_PKTINFO:
                 if (len < sizeof(int))
                         return -EINVAL;
                 len = sizeof(int);
                 val = nlk->flags & NETLINK_RECV_PKTINFO ? 1 : 0;
                 if (put_user(len, optlen) ||
                     put_user(val, optval))
                         return -EFAULT;
                 err = 0;
                 break;
         case NETLINK_BROADCAST_ERROR:
                 if (len < sizeof(int))
                         return -EINVAL;
                 len = sizeof(int);
                 val = nlk->flags & NETLINK_BROADCAST_SEND_ERROR ? 1 : 0;
                 if (put_user(len, optlen) ||
                     put_user(val, optval))
                         return -EFAULT;
                 err = 0;
                 break;
         case NETLINK_NO_ENOBUFS:
                 if (len < sizeof(int))
                         return -EINVAL;
                 len = sizeof(int);
                 val = nlk->flags & NETLINK_RECV_NO_ENOBUFS ? 1 : 0;
                 if (put_user(len, optlen) ||
                     put_user(val, optval))
                         return -EFAULT;
                 err = 0;
                 break;
         default:
                 err = -ENOPROTOOPT;
         }
         return err;
 }
 
 static void netlink_cmsg_recv_pktinfo(struct msghdr *msg, struct sk_buff *skb)
 {
         struct nl_pktinfo info;
 
         info.group = NETLINK_CB(skb).dst_group;
         put_cmsg(msg, SOL_NETLINK, NETLINK_PKTINFO, sizeof(info), &info);
 }
 
 static int netlink_sendmsg(struct socket *sock, struct msghdr *msg, size_t len)
 {
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         DECLARE_SOCKADDR(struct sockaddr_nl *, addr, msg->msg_name);
         u32 dst_portid;
         u32 dst_group;
         struct sk_buff *skb;
         int err;
         struct scm_cookie scm;
         u32 netlink_skb_flags = 0;
 
         if (msg->msg_flags&MSG_OOB)
                 return -EOPNOTSUPP;
 
         err = scm_send(sock, msg, &scm, true);
         if (err < 0)
                 return err;
 
         if (msg->msg_namelen) {
                 err = -EINVAL;
                 if (addr->nl_family != AF_NETLINK)
                         goto out;
                 dst_portid = addr->nl_pid;
                 dst_group = ffs(addr->nl_groups);
                 err =  -EPERM;
                 if ((dst_group || dst_portid) &&
                     !netlink_allowed(sock, NL_CFG_F_NONROOT_SEND))
                         goto out;
                 netlink_skb_flags |= NETLINK_SKB_DST;
         } else {
                 dst_portid = nlk->dst_portid;
                 dst_group = nlk->dst_group;
         }
 
         if (!nlk->portid) {
                 err = netlink_autobind(sock);
                 if (err)
                         goto out;
         }
 
         /* It's a really convoluted way for userland to ask for mmaped
          * sendmsg(), but that's what we've got...
          */
         if (netlink_tx_is_mmaped(sk) &&
             msg->msg_iter.type == ITER_IOVEC &&
             msg->msg_iter.nr_segs == 1 &&
             msg->msg_iter.iov->iov_base == NULL) {
                 err = netlink_mmap_sendmsg(sk, msg, dst_portid, dst_group,
                                            &scm);
                 goto out;
         }
 
         err = -EMSGSIZE;
         if (len > sk->sk_sndbuf - 32)
                 goto out;
         err = -ENOBUFS;
         skb = netlink_alloc_large_skb(len, dst_group);
         if (skb == NULL)
                 goto out;
 
         NETLINK_CB(skb).portid  = nlk->portid;
         NETLINK_CB(skb).dst_group = dst_group;
         NETLINK_CB(skb).creds   = scm.creds;
         NETLINK_CB(skb).flags   = netlink_skb_flags;
 
         err = -EFAULT;
         if (memcpy_from_msg(skb_put(skb, len), msg, len)) {
                 kfree_skb(skb);
                 goto out;
         }
 
         err = security_netlink_send(sk, skb);
         if (err) {
                 kfree_skb(skb);
                 goto out;
         }
 
         if (dst_group) {
                 atomic_inc(&skb->users);
                 netlink_broadcast(sk, skb, dst_portid, dst_group, GFP_KERNEL);
         }
         err = netlink_unicast(sk, skb, dst_portid, msg->msg_flags&MSG_DONTWAIT);
 
 out:
         scm_destroy(&scm);
         return err;
 }
 
 static int netlink_recvmsg(struct socket *sock, struct msghdr *msg, size_t len,
                            int flags)
 {
         struct scm_cookie scm;
         struct sock *sk = sock->sk;
         struct netlink_sock *nlk = nlk_sk(sk);
         int noblock = flags&MSG_DONTWAIT;
         size_t copied;
         struct sk_buff *skb, *data_skb;
         int err, ret;
 
         if (flags&MSG_OOB)
                 return -EOPNOTSUPP;
 
         copied = 0;
 
         skb = skb_recv_datagram(sk, flags, noblock, &err);
         if (skb == NULL)
                 goto out;
 
         data_skb = skb;
 
 #ifdef CONFIG_COMPAT_NETLINK_MESSAGES
         if (unlikely(skb_shinfo(skb)->frag_list)) {
                 /*
                  * If this skb has a frag_list, then here that means that we
                  * will have to use the frag_list skb's data for compat tasks
                  * and the regular skb's data for normal (non-compat) tasks.
                  *
                  * If we need to send the compat skb, assign it to the
                  * 'data_skb' variable so that it will be used below for data
                  * copying. We keep 'skb' for everything else, including
                  * freeing both later.
                  */
                 if (flags & MSG_CMSG_COMPAT)
                         data_skb = skb_shinfo(skb)->frag_list;
         }
 #endif
 
         /* Record the max length of recvmsg() calls for future allocations */
         nlk->max_recvmsg_len = max(nlk->max_recvmsg_len, len);
         nlk->max_recvmsg_len = min_t(size_t, nlk->max_recvmsg_len,
                                      16384);
 
         copied = data_skb->len;
         if (len < copied) {
                 msg->msg_flags |= MSG_TRUNC;
                 copied = len;
         }
 
         skb_reset_transport_header(data_skb);
         err = skb_copy_datagram_msg(data_skb, 0, msg, copied);
 
         if (msg->msg_name) {
                 DECLARE_SOCKADDR(struct sockaddr_nl *, addr, msg->msg_name);
                 addr->nl_family = AF_NETLINK;
                 addr->nl_pad    = 0;
                 addr->nl_pid    = NETLINK_CB(skb).portid;
                 addr->nl_groups = netlink_group_mask(NETLINK_CB(skb).dst_group);
                 msg->msg_namelen = sizeof(*addr);
         }
 
         if (nlk->flags & NETLINK_RECV_PKTINFO)
                 netlink_cmsg_recv_pktinfo(msg, skb);
 
         memset(&scm, 0, sizeof(scm));
         scm.creds = *NETLINK_CREDS(skb);
         if (flags & MSG_TRUNC)
                 copied = data_skb->len;
 
         skb_free_datagram(sk, skb);
 
         if (nlk->cb_running &&
             atomic_read(&sk->sk_rmem_alloc) <= sk->sk_rcvbuf / 2) {
                 ret = netlink_dump(sk);
                 if (ret) {
                         sk->sk_err = -ret;
                         sk->sk_error_report(sk);
                 }
         }
 
         scm_recv(sock, msg, &scm, flags);
 out:
         netlink_rcv_wake(sk);
         return err ? : copied;
 }
 
 static void netlink_data_ready(struct sock *sk)
 {
         BUG();
 }
 
 /*
  *      We export these functions to other modules. They provide a
  *      complete set of kernel non-blocking support for message
  *      queueing.
  */
 
 struct sock *
 __netlink_kernel_create(struct net *net, int unit, struct module *module,
                         struct netlink_kernel_cfg *cfg)
 {
         struct socket *sock;
         struct sock *sk;
         struct netlink_sock *nlk;
         struct listeners *listeners = NULL;
         struct mutex *cb_mutex = cfg ? cfg->cb_mutex : NULL;
         unsigned int groups;
 
         BUG_ON(!nl_table);
 
         if (unit < 0 || unit >= MAX_LINKS)
                 return NULL;
 
         if (sock_create_lite(PF_NETLINK, SOCK_DGRAM, unit, &sock))
                 return NULL;
 
         /*
          * We have to just have a reference on the net from sk, but don't
          * get_net it. Besides, we cannot get and then put the net here.
          * So we create one inside init_net and the move it to net.
          */
 
         if (__netlink_create(&init_net, sock, cb_mutex, unit) < 0)
                 goto out_sock_release_nosk;
 
         sk = sock->sk;
         sk_change_net(sk, net);
 
         if (!cfg || cfg->groups < 32)
                 groups = 32;
         else
                 groups = cfg->groups;
 
         listeners = kzalloc(sizeof(*listeners) + NLGRPSZ(groups), GFP_KERNEL);
         if (!listeners)
                 goto out_sock_release;
 
         sk->sk_data_ready = netlink_data_ready;
         if (cfg && cfg->input)
                 nlk_sk(sk)->netlink_rcv = cfg->input;
 
         if (netlink_insert(sk, 0))
                 goto out_sock_release;
 
         nlk = nlk_sk(sk);
         nlk->flags |= NETLINK_KERNEL_SOCKET;
 
         netlink_table_grab();
         if (!nl_table[unit].registered) {
                 nl_table[unit].groups = groups;
                 rcu_assign_pointer(nl_table[unit].listeners, listeners);
                 nl_table[unit].cb_mutex = cb_mutex;
                 nl_table[unit].module = module;
                 if (cfg) {
                         nl_table[unit].bind = cfg->bind;
                         nl_table[unit].unbind = cfg->unbind;
                         nl_table[unit].flags = cfg->flags;
                         if (cfg->compare)
                                 nl_table[unit].compare = cfg->compare;
                 }
                 nl_table[unit].registered = 1;
         } else {
                 kfree(listeners);
                 nl_table[unit].registered++;
         }
         netlink_table_ungrab();
         return sk;
 
 out_sock_release:
         kfree(listeners);
         netlink_kernel_release(sk);
         return NULL;
 
 out_sock_release_nosk:
         sock_release(sock);
         return NULL;
 }
 EXPORT_SYMBOL(__netlink_kernel_create);
 
 void
 netlink_kernel_release(struct sock *sk)
 {
         sk_release_kernel(sk);
 }
 EXPORT_SYMBOL(netlink_kernel_release);
 
 int __netlink_change_ngroups(struct sock *sk, unsigned int groups)
 {
         struct listeners *new, *old;
         struct netlink_table *tbl = &nl_table[sk->sk_protocol];
 
         if (groups < 32)
                 groups = 32;
 
         if (NLGRPSZ(tbl->groups) < NLGRPSZ(groups)) {
                 new = kzalloc(sizeof(*new) + NLGRPSZ(groups), GFP_ATOMIC);
                 if (!new)
                         return -ENOMEM;
                 old = nl_deref_protected(tbl->listeners);
                 memcpy(new->masks, old->masks, NLGRPSZ(tbl->groups));
                 rcu_assign_pointer(tbl->listeners, new);
 
                 kfree_rcu(old, rcu);
         }
         tbl->groups = groups;
 
         return 0;
 }
 
 /**
  * netlink_change_ngroups - change number of multicast groups
  *
  * This changes the number of multicast groups that are available
  * on a certain netlink family. Note that it is not possible to
  * change the number of groups to below 32. Also note that it does
  * not implicitly call netlink_clear_multicast_users() when the
  * number of groups is reduced.
  *
  * @sk: The kernel netlink socket, as returned by netlink_kernel_create().
  * @groups: The new number of groups.
  */
 int netlink_change_ngroups(struct sock *sk, unsigned int groups)
 {
         int err;
 
         netlink_table_grab();
         err = __netlink_change_ngroups(sk, groups);
         netlink_table_ungrab();
 
         return err;
 }
 
 void __netlink_clear_multicast_users(struct sock *ksk, unsigned int group)
 {
         struct sock *sk;
         struct netlink_table *tbl = &nl_table[ksk->sk_protocol];
 
         sk_for_each_bound(sk, &tbl->mc_list)
                 netlink_update_socket_mc(nlk_sk(sk), group, 0);
 }
 
 struct nlmsghdr *
 __nlmsg_put(struct sk_buff *skb, u32 portid, u32 seq, int type, int len, int flags)
 {
         struct nlmsghdr *nlh;
         int size = nlmsg_msg_size(len);
 
         nlh = (struct nlmsghdr *)skb_put(skb, NLMSG_ALIGN(size));
         nlh->nlmsg_type = type;
         nlh->nlmsg_len = size;
         nlh->nlmsg_flags = flags;
         nlh->nlmsg_pid = portid;
         nlh->nlmsg_seq = seq;
         if (!__builtin_constant_p(size) || NLMSG_ALIGN(size) - size != 0)
                 memset(nlmsg_data(nlh) + len, 0, NLMSG_ALIGN(size) - size);
         return nlh;
 }
 EXPORT_SYMBOL(__nlmsg_put);
 
 /*
  * It looks a bit ugly.
  * It would be better to create kernel thread.
  */
 
 static int netlink_dump(struct sock *sk)
 {
         struct netlink_sock *nlk = nlk_sk(sk);
         struct netlink_callback *cb;
         struct sk_buff *skb = NULL;
         struct nlmsghdr *nlh;
         int len, err = -ENOBUFS;
         int alloc_size;
 
         mutex_lock(nlk->cb_mutex);
         if (!nlk->cb_running) {
                 err = -EINVAL;
                 goto errout_skb;
         }
 
         cb = &nlk->cb;
         alloc_size = max_t(int, cb->min_dump_alloc, NLMSG_GOODSIZE);
 
         if (!netlink_rx_is_mmaped(sk) &&
             atomic_read(&sk->sk_rmem_alloc) >= sk->sk_rcvbuf)
                 goto errout_skb;
 
         /* NLMSG_GOODSIZE is small to avoid high order allocations being
          * required, but it makes sense to _attempt_ a 16K bytes allocation
          * to reduce number of system calls on dump operations, if user
          * ever provided a big enough buffer.
          */
         if (alloc_size < nlk->max_recvmsg_len) {
                 skb = netlink_alloc_skb(sk,
                                         nlk->max_recvmsg_len,
                                         nlk->portid,
                                         GFP_KERNEL |
                                         __GFP_NOWARN |
                                         __GFP_NORETRY);
                 /* available room should be exact amount to avoid MSG_TRUNC */
                 if (skb)
                         skb_reserve(skb, skb_tailroom(skb) -
                                          nlk->max_recvmsg_len);
         }
         if (!skb)
                 skb = netlink_alloc_skb(sk, alloc_size, nlk->portid,
                                         GFP_KERNEL);
         if (!skb)
                 goto errout_skb;
         netlink_skb_set_owner_r(skb, sk);
 
         len = cb->dump(skb, cb);
 
         if (len > 0) {
                 mutex_unlock(nlk->cb_mutex);
 
                 if (sk_filter(sk, skb))
                         kfree_skb(skb);
                 else
                         __netlink_sendskb(sk, skb);
                 return 0;
         }
 
         nlh = nlmsg_put_answer(skb, cb, NLMSG_DONE, sizeof(len), NLM_F_MULTI);
         if (!nlh)
                 goto errout_skb;
 
         nl_dump_check_consistent(cb, nlh);
 
         memcpy(nlmsg_data(nlh), &len, sizeof(len));
 
         if (sk_filter(sk, skb))
                 kfree_skb(skb);
         else
                 __netlink_sendskb(sk, skb);
 
         if (cb->done)
                 cb->done(cb);
 
         nlk->cb_running = false;
         mutex_unlock(nlk->cb_mutex);
         module_put(cb->module);
         consume_skb(cb->skb);
         return 0;
 
 errout_skb:
         mutex_unlock(nlk->cb_mutex);
         kfree_skb(skb);
         return err;
 }
 
 int __netlink_dump_start(struct sock *ssk, struct sk_buff *skb,
                          const struct nlmsghdr *nlh,
                          struct netlink_dump_control *control)
 {
         struct netlink_callback *cb;
         struct sock *sk;
         struct netlink_sock *nlk;
         int ret;
 
         /* Memory mapped dump requests need to be copied to avoid looping
          * on the pending state in netlink_mmap_sendmsg() while the CB hold
          * a reference to the skb.
          */
         if (netlink_skb_is_mmaped(skb)) {
                 skb = skb_copy(skb, GFP_KERNEL);
                 if (skb == NULL)
                         return -ENOBUFS;
         } else
                 atomic_inc(&skb->users);
 
         sk = netlink_lookup(sock_net(ssk), ssk->sk_protocol, NETLINK_CB(skb).portid);
         if (sk == NULL) {
                 ret = -ECONNREFUSED;
                 goto error_free;
         }
 
         nlk = nlk_sk(sk);
         mutex_lock(nlk->cb_mutex);
         /* A dump is in progress... */
         if (nlk->cb_running) {
                 ret = -EBUSY;
                 goto error_unlock;
         }
         /* add reference of module which cb->dump belongs to */
         if (!try_module_get(control->module)) {
                 ret = -EPROTONOSUPPORT;
                 goto error_unlock;
         }
 
         cb = &nlk->cb;
         memset(cb, 0, sizeof(*cb));
         cb->dump = control->dump;
         cb->done = control->done;
         cb->nlh = nlh;
         cb->data = control->data;
         cb->module = control->module;
         cb->min_dump_alloc = control->min_dump_alloc;
         cb->skb = skb;
 
         nlk->cb_running = true;
 
         mutex_unlock(nlk->cb_mutex);
 
         ret = netlink_dump(sk);
         sock_put(sk);
 
         if (ret)
                 return ret;
 
         /* We successfully started a dump, by returning -EINTR we
          * signal not to send ACK even if it was requested.
          */
         return -EINTR;
 
 error_unlock:
         sock_put(sk);
         mutex_unlock(nlk->cb_mutex);
 error_free:
         kfree_skb(skb);
         return ret;
 }
 EXPORT_SYMBOL(__netlink_dump_start);
 
 void netlink_ack(struct sk_buff *in_skb, struct nlmsghdr *nlh, int err)
 {
         struct sk_buff *skb;
         struct nlmsghdr *rep;
         struct nlmsgerr *errmsg;
         size_t payload = sizeof(*errmsg);
 
         /* error messages get the original request appened */
         if (err)
                 payload += nlmsg_len(nlh);
 
         skb = netlink_alloc_skb(in_skb->sk, nlmsg_total_size(payload),
                                 NETLINK_CB(in_skb).portid, GFP_KERNEL);
         if (!skb) {
                 struct sock *sk;
 
                 sk = netlink_lookup(sock_net(in_skb->sk),
                                     in_skb->sk->sk_protocol,
                                     NETLINK_CB(in_skb).portid);
                 if (sk) {
                         sk->sk_err = ENOBUFS;
                         sk->sk_error_report(sk);
                         sock_put(sk);
                 }
                 return;
         }
 
         rep = __nlmsg_put(skb, NETLINK_CB(in_skb).portid, nlh->nlmsg_seq,
                           NLMSG_ERROR, payload, 0);
         errmsg = nlmsg_data(rep);
         errmsg->error = err;
         memcpy(&errmsg->msg, nlh, err ? nlh->nlmsg_len : sizeof(*nlh));
         netlink_unicast(in_skb->sk, skb, NETLINK_CB(in_skb).portid, MSG_DONTWAIT);
 }
 EXPORT_SYMBOL(netlink_ack);
 
 int netlink_rcv_skb(struct sk_buff *skb, int (*cb)(struct sk_buff *,
                                                      struct nlmsghdr *))
 {
         struct nlmsghdr *nlh;
         int err;
 
         while (skb->len >= nlmsg_total_size(0)) {
                 int msglen;
 
                 nlh = nlmsg_hdr(skb);
                 err = 0;
 
                 if (nlh->nlmsg_len < NLMSG_HDRLEN || skb->len < nlh->nlmsg_len)
                         return 0;
 
                 /* Only requests are handled by the kernel */
                 if (!(nlh->nlmsg_flags & NLM_F_REQUEST))
                         goto ack;
 
                 /* Skip control messages */
                 if (nlh->nlmsg_type < NLMSG_MIN_TYPE)
                         goto ack;
 
                 err = cb(skb, nlh);
                 if (err == -EINTR)
                         goto skip;
 
 ack:
                 if (nlh->nlmsg_flags & NLM_F_ACK || err)
                         netlink_ack(skb, nlh, err);
 
 skip:
                 msglen = NLMSG_ALIGN(nlh->nlmsg_len);
                 if (msglen > skb->len)
                         msglen = skb->len;
                 skb_pull(skb, msglen);
         }
 
         return 0;
 }
 EXPORT_SYMBOL(netlink_rcv_skb);
 
 /**
  * nlmsg_notify - send a notification netlink message
  * @sk: netlink socket to use
  * @skb: notification message
  * @portid: destination netlink portid for reports or 0
  * @group: destination multicast group or 0
  * @report: 1 to report back, 0 to disable
  * @flags: allocation flags
  */
 int nlmsg_notify(struct sock *sk, struct sk_buff *skb, u32 portid,
                  unsigned int group, int report, gfp_t flags)
 {
         int err = 0;
 
         if (group) {
                 int exclude_portid = 0;
 
                 if (report) {
                         atomic_inc(&skb->users);
                         exclude_portid = portid;
                 }
 
                 /* errors reported via destination sk->sk_err, but propagate
                  * delivery errors if NETLINK_BROADCAST_ERROR flag is set */
                 err = nlmsg_multicast(sk, skb, exclude_portid, group, flags);
         }
 
         if (report) {
                 int err2;
 
                 err2 = nlmsg_unicast(sk, skb, portid);
                 if (!err || err == -ESRCH)
                         err = err2;
         }
 
         return err;
 }
 EXPORT_SYMBOL(nlmsg_notify);
 
 #ifdef CONFIG_PROC_FS
 struct nl_seq_iter {
         struct seq_net_private p;
         struct rhashtable_iter hti;
         int link;
 };
 
 static int netlink_walk_start(struct nl_seq_iter *iter)
 {
         int err;
 
         err = rhashtable_walk_init(&nl_table[iter->link].hash, &iter->hti);
         if (err) {
                 iter->link = MAX_LINKS;
                 return err;
         }
 
         err = rhashtable_walk_start(&iter->hti);
         return err == -EAGAIN ? 0 : err;
 }
 
 static void netlink_walk_stop(struct nl_seq_iter *iter)
 {
         rhashtable_walk_stop(&iter->hti);
         rhashtable_walk_exit(&iter->hti);
 }
 
 static void *__netlink_seq_next(struct seq_file *seq)
 {
         struct nl_seq_iter *iter = seq->private;
         struct netlink_sock *nlk;
 
         do {
                 for (;;) {
                         int err;
 
                         nlk = rhashtable_walk_next(&iter->hti);
 
                         if (IS_ERR(nlk)) {
                                 if (PTR_ERR(nlk) == -EAGAIN)
                                         continue;
 
                                 return nlk;
                         }
 
                         if (nlk)
                                 break;
 
                         netlink_walk_stop(iter);
                         if (++iter->link >= MAX_LINKS)
                                 return NULL;
 
                         err = netlink_walk_start(iter);
                         if (err)
                                 return ERR_PTR(err);
                 }
         } while (sock_net(&nlk->sk) != seq_file_net(seq));
 
         return nlk;
 }
 
 static void *netlink_seq_start(struct seq_file *seq, loff_t *posp)
 {
         struct nl_seq_iter *iter = seq->private;
         void *obj = SEQ_START_TOKEN;
         loff_t pos;
         int err;
 
         iter->link = 0;
 
         err = netlink_walk_start(iter);
         if (err)
                 return ERR_PTR(err);
 
         for (pos = *posp; pos && obj && !IS_ERR(obj); pos--)
                 obj = __netlink_seq_next(seq);
 
         return obj;
 }
 
 static void *netlink_seq_next(struct seq_file *seq, void *v, loff_t *pos)
 {
         ++*pos;
         return __netlink_seq_next(seq);
 }
 
 static void netlink_seq_stop(struct seq_file *seq, void *v)
 {
         struct nl_seq_iter *iter = seq->private;
 
         if (iter->link >= MAX_LINKS)
                 return;
 
         netlink_walk_stop(iter);
 }
 
 
 static int netlink_seq_show(struct seq_file *seq, void *v)
 {
         if (v == SEQ_START_TOKEN) {
                 seq_puts(seq,
                          "sk       Eth Pid    Groups   "
                          "Rmem     Wmem     Dump     Locks     Drops     Inode\n");
         } else {
                 struct sock *s = v;
                 struct netlink_sock *nlk = nlk_sk(s);
 
                 seq_printf(seq, "%pK %-3d %-6u %08x %-8d %-8d %d %-8d %-8d %-8lu\n",
                            s,
                            s->sk_protocol,
                            nlk->portid,
                            nlk->groups ? (u32)nlk->groups[0] : 0,
                            sk_rmem_alloc_get(s),
                            sk_wmem_alloc_get(s),
                            nlk->cb_running,
                            atomic_read(&s->sk_refcnt),
                            atomic_read(&s->sk_drops),
                            sock_i_ino(s)
                         );
 
         }
         return 0;
 }
 
 static const struct seq_operations netlink_seq_ops = {
         .start  = netlink_seq_start,
         .next   = netlink_seq_next,
         .stop   = netlink_seq_stop,
         .show   = netlink_seq_show,
 };
 
 
 static int netlink_seq_open(struct inode *inode, struct file *file)
 {
         return seq_open_net(inode, file, &netlink_seq_ops,
                                 sizeof(struct nl_seq_iter));
 }
 
 static const struct file_operations netlink_seq_fops = {
         .owner          = THIS_MODULE,
         .open           = netlink_seq_open,
         .read           = seq_read,
         .llseek         = seq_lseek,
         .release        = seq_release_net,
 };
 
 #endif
 
 int netlink_register_notifier(struct notifier_block *nb)
 {
         return atomic_notifier_chain_register(&netlink_chain, nb);
 }
 EXPORT_SYMBOL(netlink_register_notifier);
 
 int netlink_unregister_notifier(struct notifier_block *nb)
 {
         return atomic_notifier_chain_unregister(&netlink_chain, nb);
 }
 EXPORT_SYMBOL(netlink_unregister_notifier);
 
 static const struct proto_ops netlink_ops = {
         .family =       PF_NETLINK,
         .owner =        THIS_MODULE,
         .release =      netlink_release,
         .bind =         netlink_bind,
         .connect =      netlink_connect,
         .socketpair =   sock_no_socketpair,
         .accept =       sock_no_accept,
         .getname =      netlink_getname,
         .poll =         netlink_poll,
         .ioctl =        sock_no_ioctl,
         .listen =       sock_no_listen,
         .shutdown =     sock_no_shutdown,
         .setsockopt =   netlink_setsockopt,
         .getsockopt =   netlink_getsockopt,
         .sendmsg =      netlink_sendmsg,
         .recvmsg =      netlink_recvmsg,
         .mmap =         netlink_mmap,
         .sendpage =     sock_no_sendpage,
 };
 
 static const struct net_proto_family netlink_family_ops = {
         .family = PF_NETLINK,
         .create = netlink_create,
         .owner  = THIS_MODULE,  /* for consistency 8) */
 };
 
 static int __net_init netlink_net_init(struct net *net)
 {
 #ifdef CONFIG_PROC_FS
         if (!proc_create("netlink", 0, net->proc_net, &netlink_seq_fops))
                 return -ENOMEM;
 #endif
         return 0;
 }
 
 static void __net_exit netlink_net_exit(struct net *net)
 {
 #ifdef CONFIG_PROC_FS
         remove_proc_entry("netlink", net->proc_net);
 #endif
 }
 
 static void __init netlink_add_usersock_entry(void)
 {
         struct listeners *listeners;
         int groups = 32;
 
         listeners = kzalloc(sizeof(*listeners) + NLGRPSZ(groups), GFP_KERNEL);
         if (!listeners)
                 panic("netlink_add_usersock_entry: Cannot allocate listeners\n");
 
         netlink_table_grab();
 
         nl_table[NETLINK_USERSOCK].groups = groups;
         rcu_assign_pointer(nl_table[NETLINK_USERSOCK].listeners, listeners);
         nl_table[NETLINK_USERSOCK].module = THIS_MODULE;
         nl_table[NETLINK_USERSOCK].registered = 1;
         nl_table[NETLINK_USERSOCK].flags = NL_CFG_F_NONROOT_SEND;
 
         netlink_table_ungrab();
 }
 
 static struct pernet_operations __net_initdata netlink_net_ops = {
         .init = netlink_net_init,
         .exit = netlink_net_exit,
 };
 
 static inline u32 netlink_hash(const void *data, u32 len, u32 seed)
 {
         const struct netlink_sock *nlk = data;
         struct netlink_compare_arg arg;
 
         netlink_compare_arg_init(&arg, sock_net(&nlk->sk), nlk->portid);
         return jhash2((u32 *)&arg, netlink_compare_arg_len / sizeof(u32), seed);
 }
 
 static const struct rhashtable_params netlink_rhashtable_params = {
         .head_offset = offsetof(struct netlink_sock, node),
         .key_len = netlink_compare_arg_len,
         .obj_hashfn = netlink_hash,
         .obj_cmpfn = netlink_compare,
         .automatic_shrinking = true,
 };
 
 static int __init netlink_proto_init(void)
 {
         int i;
         int err = proto_register(&netlink_proto, 0);
 
         if (err != 0)
                 goto out;
 
         BUILD_BUG_ON(sizeof(struct netlink_skb_parms) > FIELD_SIZEOF(struct sk_buff, cb));
 
         nl_table = kcalloc(MAX_LINKS, sizeof(*nl_table), GFP_KERNEL);
         if (!nl_table)
                 goto panic;
 
         for (i = 0; i < MAX_LINKS; i++) {
                 if (rhashtable_init(&nl_table[i].hash,
                                     &netlink_rhashtable_params) < 0) {
                         while (--i > 0)
                                 rhashtable_destroy(&nl_table[i].hash);
                         kfree(nl_table);
                         goto panic;
                 }
         }
 
         INIT_LIST_HEAD(&netlink_tap_all);
 
         netlink_add_usersock_entry();
 
         sock_register(&netlink_family_ops);
         register_pernet_subsys(&netlink_net_ops);
         /* The netlink device handler may be needed early. */
         rtnetlink_init();
 out:
         return err;
 panic:
         panic("netlink_init: Cannot allocate nl_table\n");
 }
 
 core_initcall(netlink_proto_init);
 
```

```
nlattr.c

 /*
  * NETLINK      Netlink attributes
  *
  *              Authors:        Thomas Graf <tgraf@suug.ch>
  *                              Alexey Kuznetsov <kuznet@ms2.inr.ac.ru>
  */
 
 #include <linux/export.h>
 #include <linux/kernel.h>
 #include <linux/errno.h>
 #include <linux/jiffies.h>
 #include <linux/skbuff.h>
 #include <linux/string.h>
 #include <linux/types.h>
 #include <net/netlink.h>
 
 static const u16 nla_attr_minlen[NLA_TYPE_MAX+1] = {
         [NLA_U8]        = sizeof(u8),
         [NLA_U16]       = sizeof(u16),
         [NLA_U32]       = sizeof(u32),
         [NLA_U64]       = sizeof(u64),
         [NLA_MSECS]     = sizeof(u64),
         [NLA_NESTED]    = NLA_HDRLEN,
         [NLA_S8]        = sizeof(s8),
         [NLA_S16]       = sizeof(s16),
         [NLA_S32]       = sizeof(s32),
         [NLA_S64]       = sizeof(s64),
 };
 
 static int validate_nla(const struct nlattr *nla, int maxtype,
                         const struct nla_policy *policy)
 {
         const struct nla_policy *pt;
         int minlen = 0, attrlen = nla_len(nla), type = nla_type(nla);
 
         if (type <= 0 || type > maxtype)
                 return 0;
 
         pt = &policy[type];
 
         BUG_ON(pt->type > NLA_TYPE_MAX);
 
         switch (pt->type) {
         case NLA_FLAG:
                 if (attrlen > 0)
                         return -ERANGE;
                 break;
 
         case NLA_NUL_STRING:
                 if (pt->len)
                         minlen = min_t(int, attrlen, pt->len + 1);
                 else
                         minlen = attrlen;
 
                 if (!minlen || memchr(nla_data(nla), '\0', minlen) == NULL)
                         return -EINVAL;
                 /* fall through */
 
         case NLA_STRING:
                 if (attrlen < 1)
                         return -ERANGE;
 
                 if (pt->len) {
                         char *buf = nla_data(nla);
 
                         if (buf[attrlen - 1] == '\0')
                                 attrlen--;
 
                         if (attrlen > pt->len)
                                 return -ERANGE;
                 }
                 break;
 
         case NLA_BINARY:
                 if (pt->len && attrlen > pt->len)
                         return -ERANGE;
                 break;
 
         case NLA_NESTED_COMPAT:
                 if (attrlen < pt->len)
                         return -ERANGE;
                 if (attrlen < NLA_ALIGN(pt->len))
                         break;
                 if (attrlen < NLA_ALIGN(pt->len) + NLA_HDRLEN)
                         return -ERANGE;
                 nla = nla_data(nla) + NLA_ALIGN(pt->len);
                 if (attrlen < NLA_ALIGN(pt->len) + NLA_HDRLEN + nla_len(nla))
                         return -ERANGE;
                 break;
         case NLA_NESTED:
                 /* a nested attributes is allowed to be empty; if its not,
                  * it must have a size of at least NLA_HDRLEN.
                  */
                 if (attrlen == 0)
                         break;
         default:
                 if (pt->len)
                         minlen = pt->len;
                 else if (pt->type != NLA_UNSPEC)
                         minlen = nla_attr_minlen[pt->type];
 
                 if (attrlen < minlen)
                         return -ERANGE;
         }
 
         return 0;
 }
 
 /**
  * nla_validate - Validate a stream of attributes
  * @head: head of attribute stream
  * @len: length of attribute stream
  * @maxtype: maximum attribute type to be expected
  * @policy: validation policy
  *
  * Validates all attributes in the specified attribute stream against the
  * specified policy. Attributes with a type exceeding maxtype will be
  * ignored. See documenation of struct nla_policy for more details.
  *
  * Returns 0 on success or a negative error code.
  */
 int nla_validate(const struct nlattr *head, int len, int maxtype,
                  const struct nla_policy *policy)
 {
         const struct nlattr *nla;
         int rem, err;
 
         nla_for_each_attr(nla, head, len, rem) {
                 err = validate_nla(nla, maxtype, policy);
                 if (err < 0)
                         goto errout;
         }
 
         err = 0;
 errout:
         return err;
 }
 EXPORT_SYMBOL(nla_validate);
 
 /**
  * nla_policy_len - Determin the max. length of a policy
  * @policy: policy to use
  * @n: number of policies
  *
  * Determines the max. length of the policy.  It is currently used
  * to allocated Netlink buffers roughly the size of the actual
  * message.
  *
  * Returns 0 on success or a negative error code.
  */
 int
 nla_policy_len(const struct nla_policy *p, int n)
 {
         int i, len = 0;
 
         for (i = 0; i < n; i++, p++) {
                 if (p->len)
                         len += nla_total_size(p->len);
                 else if (nla_attr_minlen[p->type])
                         len += nla_total_size(nla_attr_minlen[p->type]);
         }
 
         return len;
 }
 EXPORT_SYMBOL(nla_policy_len);
 
 /**
  * nla_parse - Parse a stream of attributes into a tb buffer
  * @tb: destination array with maxtype+1 elements
  * @maxtype: maximum attribute type to be expected
  * @head: head of attribute stream
  * @len: length of attribute stream
  * @policy: validation policy
  *
  * Parses a stream of attributes and stores a pointer to each attribute in
  * the tb array accessible via the attribute type. Attributes with a type
  * exceeding maxtype will be silently ignored for backwards compatibility
  * reasons. policy may be set to NULL if no validation is required.
  *
  * Returns 0 on success or a negative error code.
  */
 int nla_parse(struct nlattr **tb, int maxtype, const struct nlattr *head,
               int len, const struct nla_policy *policy)
 {
         const struct nlattr *nla;
         int rem, err;
 
         memset(tb, 0, sizeof(struct nlattr *) * (maxtype + 1));
 
         nla_for_each_attr(nla, head, len, rem) {
                 u16 type = nla_type(nla);
 
                 if (type > 0 && type <= maxtype) {
                         if (policy) {
                                 err = validate_nla(nla, maxtype, policy);
                                 if (err < 0)
                                         goto errout;
                         }
 
                         tb[type] = (struct nlattr *)nla;
                 }
         }
 
         if (unlikely(rem > 0))
                 pr_warn_ratelimited("netlink: %d bytes leftover after parsing attributes in process `%s'.\n",
                                     rem, current->comm);
 
         err = 0;
 errout:
         return err;
 }
 EXPORT_SYMBOL(nla_parse);
 
 /**
  * nla_find - Find a specific attribute in a stream of attributes
  * @head: head of attribute stream
  * @len: length of attribute stream
  * @attrtype: type of attribute to look for
  *
  * Returns the first attribute in the stream matching the specified type.
  */
 struct nlattr *nla_find(const struct nlattr *head, int len, int attrtype)
 {
         const struct nlattr *nla;
         int rem;
 
         nla_for_each_attr(nla, head, len, rem)
                 if (nla_type(nla) == attrtype)
                         return (struct nlattr *)nla;
 
         return NULL;
 }
 EXPORT_SYMBOL(nla_find);
 
 /**
  * nla_strlcpy - Copy string attribute payload into a sized buffer
  * @dst: where to copy the string to
  * @nla: attribute to copy the string from
  * @dstsize: size of destination buffer
  *
  * Copies at most dstsize - 1 bytes into the destination buffer.
  * The result is always a valid NUL-terminated string. Unlike
  * strlcpy the destination buffer is always padded out.
  *
  * Returns the length of the source buffer.
  */
 size_t nla_strlcpy(char *dst, const struct nlattr *nla, size_t dstsize)
 {
         size_t srclen = nla_len(nla);
         char *src = nla_data(nla);
 
         if (srclen > 0 && src[srclen - 1] == '\0')
                 srclen--;
 
         if (dstsize > 0) {
                 size_t len = (srclen >= dstsize) ? dstsize - 1 : srclen;
 
                 memset(dst, 0, dstsize);
                 memcpy(dst, src, len);
         }
 
         return srclen;
 }
 EXPORT_SYMBOL(nla_strlcpy);
 
 /**
  * nla_memcpy - Copy a netlink attribute into another memory area
  * @dest: where to copy to memcpy
  * @src: netlink attribute to copy from
  * @count: size of the destination area
  *
  * Note: The number of bytes copied is limited by the length of
  *       attribute's payload. memcpy
  *
  * Returns the number of bytes copied.
  */
 int nla_memcpy(void *dest, const struct nlattr *src, int count)
 {
         int minlen = min_t(int, count, nla_len(src));
 
         memcpy(dest, nla_data(src), minlen);
         if (count > minlen)
                 memset(dest + minlen, 0, count - minlen);
 
         return minlen;
 }
 EXPORT_SYMBOL(nla_memcpy);
 
 /**
  * nla_memcmp - Compare an attribute with sized memory area
  * @nla: netlink attribute
  * @data: memory area
  * @size: size of memory area
  */
 int nla_memcmp(const struct nlattr *nla, const void *data,
                              size_t size)
 {
         int d = nla_len(nla) - size;
 
         if (d == 0)
                 d = memcmp(nla_data(nla), data, size);
 
         return d;
 }
 EXPORT_SYMBOL(nla_memcmp);
 
 /**
  * nla_strcmp - Compare a string attribute against a string
  * @nla: netlink string attribute
  * @str: another string
  */
 int nla_strcmp(const struct nlattr *nla, const char *str)
 {
         int len = strlen(str);
         char *buf = nla_data(nla);
         int attrlen = nla_len(nla);
         int d;
 
         if (attrlen > 0 && buf[attrlen - 1] == '\0')
                 attrlen--;
 
         d = attrlen - len;
         if (d == 0)
                 d = memcmp(nla_data(nla), str, len);
 
         return d;
 }
 EXPORT_SYMBOL(nla_strcmp);
 
 #ifdef CONFIG_NET
 /**
  * __nla_reserve - reserve room for attribute on the skb
  * @skb: socket buffer to reserve room on
  * @attrtype: attribute type
  * @attrlen: length of attribute payload
  *
  * Adds a netlink attribute header to a socket buffer and reserves
  * room for the payload but does not copy it.
  *
  * The caller is responsible to ensure that the skb provides enough
  * tailroom for the attribute header and payload.
  */
 struct nlattr *__nla_reserve(struct sk_buff *skb, int attrtype, int attrlen)
 {
         struct nlattr *nla;
 
         nla = (struct nlattr *) skb_put(skb, nla_total_size(attrlen));
         nla->nla_type = attrtype;
         nla->nla_len = nla_attr_size(attrlen);
 
         memset((unsigned char *) nla + nla->nla_len, 0, nla_padlen(attrlen));
 
         return nla;
 }
 EXPORT_SYMBOL(__nla_reserve);
 
 /**
  * __nla_reserve_nohdr - reserve room for attribute without header
  * @skb: socket buffer to reserve room on
  * @attrlen: length of attribute payload
  *
  * Reserves room for attribute payload without a header.
  *
  * The caller is responsible to ensure that the skb provides enough
  * tailroom for the payload.
  */
 void *__nla_reserve_nohdr(struct sk_buff *skb, int attrlen)
 {
         void *start;
 
         start = skb_put(skb, NLA_ALIGN(attrlen));
         memset(start, 0, NLA_ALIGN(attrlen));
 
         return start;
 }
 EXPORT_SYMBOL(__nla_reserve_nohdr);
 
 /**
  * nla_reserve - reserve room for attribute on the skb
  * @skb: socket buffer to reserve room on
  * @attrtype: attribute type
  * @attrlen: length of attribute payload
  *
  * Adds a netlink attribute header to a socket buffer and reserves
  * room for the payload but does not copy it.
  *
  * Returns NULL if the tailroom of the skb is insufficient to store
  * the attribute header and payload.
  */
 struct nlattr *nla_reserve(struct sk_buff *skb, int attrtype, int attrlen)
 {
         if (unlikely(skb_tailroom(skb) < nla_total_size(attrlen)))
                 return NULL;
 
         return __nla_reserve(skb, attrtype, attrlen);
 }
 EXPORT_SYMBOL(nla_reserve);
 
 /**
  * nla_reserve_nohdr - reserve room for attribute without header
  * @skb: socket buffer to reserve room on
  * @attrlen: length of attribute payload
  *
  * Reserves room for attribute payload without a header.
  *
  * Returns NULL if the tailroom of the skb is insufficient to store
  * the attribute payload.
  */
 void *nla_reserve_nohdr(struct sk_buff *skb, int attrlen)
 {
         if (unlikely(skb_tailroom(skb) < NLA_ALIGN(attrlen)))
                 return NULL;
 
         return __nla_reserve_nohdr(skb, attrlen);
 }
 EXPORT_SYMBOL(nla_reserve_nohdr);
 
 /**
  * __nla_put - Add a netlink attribute to a socket buffer
  * @skb: socket buffer to add attribute to
  * @attrtype: attribute type
  * @attrlen: length of attribute payload
  * @data: head of attribute payload
  *
  * The caller is responsible to ensure that the skb provides enough
  * tailroom for the attribute header and payload.
  */
 void __nla_put(struct sk_buff *skb, int attrtype, int attrlen,
                              const void *data)
 {
         struct nlattr *nla;
 
         nla = __nla_reserve(skb, attrtype, attrlen);
         memcpy(nla_data(nla), data, attrlen);
 }
 EXPORT_SYMBOL(__nla_put);
 
 /**
  * __nla_put_nohdr - Add a netlink attribute without header
  * @skb: socket buffer to add attribute to
  * @attrlen: length of attribute payload
  * @data: head of attribute payload
  *
  * The caller is responsible to ensure that the skb provides enough
  * tailroom for the attribute payload.
  */
 void __nla_put_nohdr(struct sk_buff *skb, int attrlen, const void *data)
 {
         void *start;
 
         start = __nla_reserve_nohdr(skb, attrlen);
         memcpy(start, data, attrlen);
 }
 EXPORT_SYMBOL(__nla_put_nohdr);
 
 /**
  * nla_put - Add a netlink attribute to a socket buffer
  * @skb: socket buffer to add attribute to
  * @attrtype: attribute type
  * @attrlen: length of attribute payload
  * @data: head of attribute payload
  *
  * Returns -EMSGSIZE if the tailroom of the skb is insufficient to store
  * the attribute header and payload.
  */
 int nla_put(struct sk_buff *skb, int attrtype, int attrlen, const void *data)
 {
         if (unlikely(skb_tailroom(skb) < nla_total_size(attrlen)))
                 return -EMSGSIZE;
 
         __nla_put(skb, attrtype, attrlen, data);
         return 0;
 }
 EXPORT_SYMBOL(nla_put);
 
 /**
  * nla_put_nohdr - Add a netlink attribute without header
  * @skb: socket buffer to add attribute to
  * @attrlen: length of attribute payload
  * @data: head of attribute payload
  *
  * Returns -EMSGSIZE if the tailroom of the skb is insufficient to store
  * the attribute payload.
  */
 int nla_put_nohdr(struct sk_buff *skb, int attrlen, const void *data)
 {
         if (unlikely(skb_tailroom(skb) < NLA_ALIGN(attrlen)))
                 return -EMSGSIZE;
 
         __nla_put_nohdr(skb, attrlen, data);
         return 0;
 }
 EXPORT_SYMBOL(nla_put_nohdr);
 
 /**
  * nla_append - Add a netlink attribute without header or padding
  * @skb: socket buffer to add attribute to
  * @attrlen: length of attribute payload
  * @data: head of attribute payload
  *
  * Returns -EMSGSIZE if the tailroom of the skb is insufficient to store
  * the attribute payload.
  */
 int nla_append(struct sk_buff *skb, int attrlen, const void *data)
 {
         if (unlikely(skb_tailroom(skb) < NLA_ALIGN(attrlen)))
                 return -EMSGSIZE;
 
         memcpy(skb_put(skb, attrlen), data, attrlen);
         return 0;
 }
 EXPORT_SYMBOL(nla_append);
 #endif
 
```

###NetLink 关键特性

Linux 3.10 [introduced Netlink mmap interface](http://lwn.net/Articles/512442/)
