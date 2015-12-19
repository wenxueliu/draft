
#基本要求

* 理解网卡常见参数
* 熟悉 ethtool 的使用

##网卡 Bonding 模式

当主机有 1 个以上的网卡时, Linux 会将多个网卡绑定为一个虚拟的 bonded 网络接口, 对 TCP/IP 而言只存在一个 bonded 网卡.
多网卡绑定一方面能够提高网络吞吐量, 另一方面也可以增强网络高可用. Linux 支持 7 种[Bonding模式](http://www.cloudibee.com/network-bonding-modes/):

    Mode 0 (balance-rr)  Round-robin策略，这个模式具备负载均衡和容错能力
    Mode 1 (active-backup)  主备策略，在绑定中只有一个网卡被激活，其他处于备份状态
    Mode 2 (balance-xor)  XOR策略，通过源MAC地址与目的MAC地址做异或操作选择slave网卡
    Mode 3 (broadcast)  广播，在所有的网卡上传送所有的报文
    Mode 4 (802.3ad)  IEEE 802.3ad 动态链路聚合。创建共享相同的速率和双工模式的聚合组
    Mode 5 (balance-tlb)  Adaptive transmit load balancing
    Mode 6 (balance-alb)  Adaptive load balancing

详细的说明参考内核文档 [Linux Ethernet Bonding Driver HOWTO](https://www.kernel.org/doc/Documentation/networking/bonding.txt).
我们可以通过 cat /proc/net/bonding/bond0 查看本机的Bonding模式:

$ cat /proc/net/bonding/bond0


###Bonding 创建

$ cat /etc/sysconfig/network-scripts/ifcfg-bond0

    DEVICE=bond0
    IPADDR=192.168.1.12
    NETMASK=255.255.255.0
    GATEWAY=192.168.1.1
    USERCTL=no
    BOOTPROTO=none
    ONBOOT=yes

$ cat /etc/sysconfig/network-scripts/ifcfg-eth0

    DEVICE=eth0
    BOOTPROTO=none
    ONBOOT=yes
    # Settings for Bond
    MASTER=bond0
    SLAVE=yes

$ cat /etc/sysconfig/network-scripts/ifcfg-eth1

    DEVICE=eth1
    BOOTPROTO=none
    ONBOOT=yes
    # Settings for Bond
    MASTER=bond0
    SLAVE=yes

$ cat /etc/sysconfig/network-scripts/ifcfg-eth2

    DEVICE=eth2
    BOOTPROTO=none
    ONBOOT=yes
    # Settings for Bond
    MASTER=bond0
    SLAVE=yes

文件 /etc/modprobe.conf 增加如下:

    # bonding commands
    alias bond0 bonding
    options bond0 mode=1 miimon=100

$ modprobe bonding

$ service network restart

$ cat /proc/net/bonding/bond0

    Ethernet Channel Bonding Driver
    Bonding Mode: adaptive load balancing
    Primary Slave: None
    Currently Active Slave: eth2
    MII Status: up
    MII Polling Interval (ms): 100
    Up Delay (ms): 0
    Down Delay (ms): 0
    Slave Interface: eth2
    MII Status: up
    Link Failure Count: 0
    Permanent HW addr: 00:13:72:80: 62:f0


$ ifdown eth0

$ cat /proc/net/bonding/bond0 

检查 "Current Active slave".

从不同的机器 ping bond0, 期间 ifdown eth0 , ifdown eth1, ping 一直能够成功

##RPS and RFS

网卡收到一定的数据后, 驱动会产生中断, 然后交由 CPU 来处理, 在单核时代, 直接扔给那个核处理就 OK,
但多核时代呢, 怎么办呢, 一种最简单的能想到的方法自然是 RR, 就第一个给 cpu 0，第二个给cpu 1,
但这会导致包乱序的问题, 没办法采用.

普通的 NIC 来分发这些接收到的数据包到 CPU 核处理需要一定的知识智能以帮助提升性能, 如果数据包被
任意的分配给某个 CPU 核来处理就可能会导致所谓的 "CACHELINE-PINGPONG" 现象, 这时候 RPS 就出现了.

为了能充分发挥多核的能力, google 的 Tom Herbert 做了个 patch, 称为 Receive Packet Steering,
缩写为 RPS, 能够做到将网卡中断较为均衡的分散到多个 CPU, 简单来说, 是网卡驱动对每个流生成一个
hash(比如IP地址和端口号) 标识, 然后由中断处理的地方根据这个 hash 标识分配到相应的 CPU 上去, 这
样就可以把软中断的负载均衡分到各个cpu, 实现了类似多队列网卡的功能.

随着 RPS 的投入使用, 又发现上面的改进可能会碰到一个问题, 由于 RPS 只是单纯的把同一流的数据包分
发给同一个 CPU 核来处理了, 但是有可能出现这样的情况, 即给该数据流分发的 CPU 核和执行处理该数据
流的应用程序的 CPU 核不是同一个: 数据包均衡到不同的 CPU, 这个时候如果应用程序所在的 CPU 和软中
断处理的 CPU 不是同一个, 此时对于 CPU cache 的影响会很大. 因此 Tom 继续做了个改进版,
称为 Receive flow steering, 缩写为 RFS.

这两个补丁往往都是一起设置, 来达到最好的优化效果, 主要是针对单队列网卡多 CPU 环境.

目前 RPS 和 RFS 已集成到 linux 2.6.35 中, 如果内核是这个版本的以上的可以直接使用, 如果是低于这个
版本的, 就只能自己backport了, 但据一些玩内核的同学的经验, 这个 patch 还不是很好 backport...

默认情况下, 这个功能并没有开启

    $ cat /sys/class/net/eth2/queues/rx-0/rps_cpus
    00000000,00000000,00000000,00000000,00000000,00000000,00000000,00000000

    $ cat /sys/class/net/eth2/queues/rx-0/rps_flow_cnt
    0

    $ cat /proc/sys/net/core/rps_sock_flow_entries
    0

需要手动开启开启方法, 开启的前提是多队列网卡才有效果.

    echo ff > /sys/class/net/<interface>/queues/rx-<number>/rps_cpus
    echo 4096 > /sys/class/net/<interface>/queues/rx-<number>/rps_flow_cnt
    echo 30976 > /proc/sys/net/core/rps_sock_flow_entries

对于 2 个物理 cpu, 8 核的机器为ff, 具体计算方法是第一颗 cpu 是 00000001, 第二颗 cpu 是 00000010, 第三颗 cpu 是 00000100,
依次类推, 由于是所有的 cpu 都负担, 所以所有的 cpu 数值相加, 得到的数值为 11111111, 十六进制就刚好是 ff. 而对于
/proc/sys/net/core/rps_sock_flow_entries 的数值是根据你的网卡多少个通道, 计算得出的数据, 例如你是 8 通道的网卡, 那么 1
个网卡, 每个通道设置 4096 的数值, 8*4096 就是 /proc/sys/net/core/rps_sock_flow_entries 的数值, 对于内存大的机器可以适当
调大 rps_flow_cnt, 这个时候基本可以把软中断均衡到各个 cpu 上了


NOTE:

    网卡驱动必须是 NAPI 的

上面的这种是比较乞丐版的让网卡中断能够均衡的方法, 而更"高富帅"一点的做法是采用支持多队列的网卡.

###RPS VS RFS

RPS 只依靠 hash 来控制数据包, 提供了好的负载平衡, 但是它没有考虑应用程序的位置(注:这个位置
是指程序在哪个cpu上执行). RFS 则考虑到了应用程序的位置. RFS 的目标是通过指派应用线程正在运
行的 CPU 来进行数据包处理, 以此来增加数据缓存的命中率. RFS 依靠 RPS 的机制插入数据包到指定
CPU 的 backlog 队列, 并唤醒那个 CPU 来执行.

RFS中, 数据包并不会直接的通过数据包的 hash 值被转发, 但是 hash 值将会作为流查询表的索引.这
个表映射数据流与处理这个流的 CPU. 这个数据流的 hash 值(就是这个流中的数据包的hash值)将被用
来计算这个表的索引. 流查询表的每条记录中所记录的 CPU 是上次处理数据流的 CPU. 如果记录中没有
CPU, 那么数据包将会使用 RPS 来处理. 多个记录会指向相同的 CPU. 确实, 当流很多而 CPU 很少时,
很有可能一个应用线程处理多个不同 hash 值的数据流.

rps_sock_flow_table 是一个全局的数据流表, 这个表中包含了数据流渴望运行的 CPU. 这个 CPU 是当
前正在用户层处理流的 CPU. 每个数据流表项的值是 CPU 号, 这个会在调 recvmsg, sendmsg (特别是
inet_accept(), inet_recvmsg(), inet_sendmsg(), inet_sendpage() and tcp_splice_read()), 被更
新.(注:使用 sock_rps_record_flow() 来记录 rps_sock_flow_table 表中每个数据流表项的 CPU 号.)

当调度器移动一个线程到一个新的 CPU, 而内核正在旧的 CPU 上处理接收到的数据包, 这会导致数据包
的乱序. 为了避免这个, RFS 使用了第二个数据流表来为每个数据流跟踪数据包 : rps_dev_flow_table
是一个表, 被指定到每个设备的每个硬件接收队列. 每个表值存储了 CPU 号和一个计数值. 这个 CPU
号表示了数据流中的数据包将被内核进一步处理的 CPU. 理想状态下，内核和用户处理发生正在同一个
CPU上, 由此在这两个表中这个 CPU 号是相同的. 如果调度器已经迁移用户进程, 而内核仍然有数据包
被加到旧的 CPU 上, 那么这两个值就不等了.

当这个流中的数据包最终被加到队列中,  rps_dev_flow_table 中的计数值记录了当前 CPU 的 backlog
队列的长度. 每个 backlog 队列有一个队列头, 当数据包从队列中出去后, 这个队列头就会增加. 队列
尾部则等于队列头加上队列长度. 换句话说, rps_dev_flow[i] 中的计数值记录了流 i 中的最后一个数
据包, 这个数据包已经添加到了目标 CPU 的 backlog 队列. 当然, 流 i 是由 hash 值选择的, 并且多
个数据流可以 hash 到同一个流 i.


下面描述避免数据包乱序的技巧, 当从 get_rps_cpu() 选择 CPU 来进行数据包处理, rps_sock_flow 和
rps_dev_flow 将会进行比较. 如果数据流的理想 CPU(found in therps_sock_flow table) 和当前CPU
(found in the rps_dev_flow table)匹配, 这个包将会加到这个 CPU 的 backlog 队列. 如果他们不同,
并且下面规则中任一个为真, 则当前的 CPU 将会被更新, 去匹配理想 CPU.

* 当前CPU的队列头部大于等于 rps_dev_flow[i] 中记录的尾部计数值, 这个计数值指向了CPU的队列的尾部.(说明当前 CPU 中没有多余的数据包未处理.)
* 当前CPU是未设置的(等于NR_CPUS，RPS_NO_CPU=0xffff)
* 当前CPU是离线的(注:应该是没有启用)

(注:如果他们不同, 并且当前 CPU 是有效的, 则会继续用当前的 CPU 来处理.) 检查了之后, 数据包
被发送到(可能)更新后的CPU. 这些规则目标是当旧的 CPU 上没有接收到的数据包, 才会移动数据流
移动到一个新的 CPU 上. 接收到的数据包能够在新的 CPU 切换后到达.


##XPS: Transmit Packet Steering

XPS 是一种机制, 用来智能的选择多队列设备的队列来发送数据包. 为了达到这个目标, 从 CPU 到硬件队列
的映射需要被记录. 这个映射的目标是专门地分配队列到一个 CPU 列表, 这些 CPU 列表中的某个 CPU 来完
成队列中的数据传输. 这个有两点优势, 第一点, 设备队列上的锁竞争会被减少, 因为只有很少的 CPU 对相
同的队列进行竞争.(如果每个 CPU 只有自己的传输队列, 锁的竞争就完全没有了.)第二点, 传输时的缓存不
命中的概率就减少, 特别是持有 sk_buff 的数据缓存.

XPS 通过设置使用队列进行传输的 CPU 位图, 对每一个队列进行配置. 相反的映射, 从 CPU 到传输队列,是
由网络设备计算并维护的. 当传输数据流的第一个数据包时, 函数 get_xps_queue() 被调用来选择一个队列.
这个函数使用正在运行的 CPU 的 ID 号作为指向 CPU- 到 - 队列的查找表的 key 值. 如果这个 ID 匹配一
个单独的队列, 那么这个队列被用来传输. 如果多个队列被匹配, 通过数据流的 hash 值作为 key 值来选择队列.

选择传输特殊数据流的队列被存储在相应的数据流的socket结构体(sk_tx_queue_mapping).

这个传输队列被用来传输接下来的数据包, 以防乱序(OOO)的包. 这个选择也分担了为这个流中的所有数据包调用
 get_xps_queues() 的开销. 为了避免乱序的包, 只有这个数据流中的某个包的skb->ooo_okay标志被设置了,
这个数据流所使用的队列才能改变. 这个标志表示数据流中没有待解决的数据包(注:被解决的数据包应该是指
tcp_packets_in_flight()等于0. 也就是说发送出去的数据包都被应答了), 所以, 这个传输队列才能安全的改变,
而不会有产生乱序包的危险. 传输层即 L4 层相应地有责任来设置 ooo_okay 标志位. 例如, 当一个连接的所有
数据包被应答了, tcp 才设置这个标志位. (UDP协议没有流的概念, 所以没有必要设置这个标志.)


###XPS Configuration

XPS 要求内核编译了 CONFIG_XPS 选项(SMP上默认是打开的). 尽管编译到内核, 直到被配置了才能启用.
为了使用XPS, 需要使用 sysfs 来配置传输队列的 CPU 位图:

/sys/class/net/[eth-x]/queues/tx-[x]/xps_cpus

###Suggested Configuration

对于只有一个传输队列的网络设置而言，XPS的配置没有任何效果，因为这种情况下没有选择。对于一个多队列系统，XPS更好的配置是每个CPU映射到一个队列中。如果有CPU一样多的队列，那么每个队列可以映射到每个CPU上，这就导致没有竞争的专一配对。如果队列比CPU少，共享指定队列的CPU最好是与处理传输硬中断(这个中断用来清理队列传输结束后的工作)的CPU共享缓存的CPU。


XPS在2.6.38中被引入. 原始的patches是由Tom Herbert (therbert@google.com)来提交的。

加速RFS在2.6.35中被引入，原始的patches是由Ben Hutchings (bhutchings@solarflare.com)提交的。



##网卡多队列

多队列网卡是一种技术, 最初是用来解决网络 IO QoS （quality of service）问题的, 后来随着网络 IO 的带宽的不断提升,
单核CPU不能完全处满足网卡的需求, 通过多队列网卡驱动的支持, 将各个队列通过中断绑定到不同的核上, 以满足网卡的需求.

常见的有 Intel 的 82575, 82576, Boardcom 的 57711 等, 下面以公司的服务器使用较多的 Intel 82575 网卡为例, 分析一
下多队列网卡的硬件的实现以及 linux 内核软件的支持.

###多队列网卡硬件实现

下图是Intel 82575硬件逻辑图, 有四个硬件队列. 当收到报文时, 通过 hash 包头的 SIP, Sport, DIP, Dport 四元组, 将一条
流总是收到相同的队列. 同时触发与该队列绑定的中断.

![intel 82575 硬件逻辑图](intel_82575.gif)

###2.6.21以前网卡驱动实现

kernel 从 2.6.21 之前不支持多队列特性, 一个网卡只能申请一个中断号, 因此同一个时刻只有一个核在处理网卡收到的包.
如下图1, 协议栈通过 NAPI 轮询收取各个硬件 queue 中的报文到下图2 的 net_device 数据结构中, 通过 QDisc 队列将报文
发送到网卡.

![2.6.21之前内核协议栈](2_6_21_kernel_stack.gif)

![2.6.21之前net_device](2_6_21_net_device.gif)


###2.6.21后网卡驱动实现

2.6.21 开始支持多队列特性, 当网卡驱动加载时, 通过获取的网卡型号, 得到网卡的硬件 queue 的数量, 并结合 CPU 核的数量,
最终通过Sum=Min(网卡queue, CPU core)得出所要激活的网卡 queue 数量(Sum), 并申请 Sum 个中断号, 分配给激活的各个 queue.

下图1, 当某个 queue 收到报文时, 触发相应的中断, 收到中断的核, 将该任务加入到协议栈负责收包的该核的 NET_RX_SOFTIRQ 队
列中(NET_RX_SOFTIRQ在每个核上都有一个实例), 在 NET_RX_SOFTIRQ 中, 调用 NAPI 的收包接口, 将报文收到 CPU 中下图2 的有多
个 netdev_queue 的 net_device 数据结构中.

这样, CPU 的各个核可以并发的收包, 就不会应为一个核不能满足需求, 导致网络 IO 性能下降.

![2.6.32之前内核协议栈](2_6_32_kernel_stack.gif)

![2.6.32之前net_device](2_6_32_net_device.gif)


###中断绑定

当 CPU 可以平行收包时, 就会出现不同的核收取了同一个 queue 的报文, 这就会产生报文乱序的问题, 解决方法是将一个 queue 的
中断绑定到唯一的一个核上去, 从而避免了乱序问题. 同时如果网络流量大的时候, 可以将软中断均匀的分散到各个核上, 避免 CPU
成为瓶颈.

如下 8 核心的服务器中, p2p1 不支持网卡多队列, 而 p4p1, p4p2, p4p3, p4p4
都支持网卡多队列, 因此每个网卡分配了 8 个队列

$cat /proc/interrnet

               CPU0       CPU1       CPU2       CPU3       CPU4       CPU5       CPU6       CPU7

	 42:       1431        773         28        243         63        857         30        263  IR-PCI-MSI-edge      xhci_hcd
	 43:       2419      37979          0          0        239          0          0          0  IR-PCI-MSI-edge      p2p1
	 44:      28396       3589       3554       5499      29244      23712       6976      34999  IR-PCI-MSI-edge      ahci
	 45:          0          0          0          0          0          0          0          0  IR-PCI-MSI-edge      p4p1
	 46:         73          0         10          0          0          0          0       1169  IR-PCI-MSI-edge      p4p1-TxRx-0
	 47:         73          0          0        709        470          0          0          0  IR-PCI-MSI-edge      p4p1-TxRx-1
	 48:         83          0         55          0          0        760        255         99  IR-PCI-MSI-edge      p4p1-TxRx-2
	 49:        577          5         25        625          0         10          0         10  IR-PCI-MSI-edge      p4p1-TxRx-3
	 50:       1098          0          0        144          0          0         10          0  IR-PCI-MSI-edge      p4p1-TxRx-4
	 51:        313          0         65         30          0          0        755         89  IR-PCI-MSI-edge      p4p1-TxRx-5
	 52:         73          0        195        549        270        145          0         20  IR-PCI-MSI-edge      p4p1-TxRx-6
	 53:        323         10        520          0        110          0          0        289  IR-PCI-MSI-edge      p4p1-TxRx-7
	 54:          0          0          0          0          0          0          0          0  IR-PCI-MSI-edge      p4p2
	 55:        143          5          0        349          0         20        735          0  IR-PCI-MSI-edge      p4p2-TxRx-0
	 56:        233          0         30        114          0          0        695        180  IR-PCI-MSI-edge      p4p2-TxRx-1
	 57:        148         10        170         49          0        175        510        190  IR-PCI-MSI-edge      p4p2-TxRx-2
	 58:        183         20        455        229         15          0        260         90  IR-PCI-MSI-edge      p4p2-TxRx-3
	 59:        442          0        425        155        125         15         30         60  IR-PCI-MSI-edge      p4p2-TxRx-4
	 60:         73         15        450         75         25        195        195        224  IR-PCI-MSI-edge      p4p2-TxRx-5
	 61:        143         25        295        184         20          0        380        205  IR-PCI-MSI-edge      p4p2-TxRx-6
	 62:        208         10        255        129         10         85        265        290  IR-PCI-MSI-edge      p4p2-TxRx-7
	 63:          0          0          0          0          0          0          0          0  IR-PCI-MSI-edge      p4p3
	 64:        388         15         70        220        170         40        235        114  IR-PCI-MSI-edge      p4p3-TxRx-0
	 65:        298          5        105        239        140        130        280         55  IR-PCI-MSI-edge      p4p3-TxRx-1
	 66:        183         50        155        190         30        185        225        234  IR-PCI-MSI-edge      p4p3-TxRx-2
	 67:        143          0        275        249        125        140        250         70  IR-PCI-MSI-edge      p4p3-TxRx-3
	 68:        283         10         90        155        130        135        150        299  IR-PCI-MSI-edge      p4p3-TxRx-4
	 69:        258         30         65        329          0         90        390         90  IR-PCI-MSI-edge      p4p3-TxRx-5
	 70:        158         20        280         85          5         50        155        499  IR-PCI-MSI-edge      p4p3-TxRx-6
	 71:        118          0        415        230        210        125         25        129  IR-PCI-MSI-edge      p4p3-TxRx-7
	 72:          0          0          0          0          0          0          0          0  IR-PCI-MSI-edge      p4p4
	 73:        133          5        290        144          0         55        440        185  IR-PCI-MSI-edge      p4p4-TxRx-0
	 74:        423         35        120        195          0         60        215        204  IR-PCI-MSI-edge      p4p4-TxRx-1
	 75:        213         20         15        314          0          0        545        145  IR-PCI-MSI-edge      p4p4-TxRx-2
	 76:        193         20         85        249        115         75        405        110  IR-PCI-MSI-edge      p4p4-TxRx-3
	 77:        373         10         95         54        110          0        300        310  IR-PCI-MSI-edge      p4p4-TxRx-4
	 78:        133         15        405        165         50        160        115        209  IR-PCI-MSI-edge      p4p4-TxRx-5
	 79:        138         45        430         75        215          0         40        309  IR-PCI-MSI-edge      p4p4-TxRx-6
	 80:        498         45        270        165          0         55          0        219  IR-PCI-MSI-edge      p4p4-TxRx-7
	 81:         13          0          0          0          0          0          0          0  IR-PCI-MSI-edge      mei_me
	 82:        499          0          0          0          0          0          0          0  IR-PCI-MSI-edge      snd_hda_intel
	 83:       3015          0          0          0          0          0          0          0  IR-PCI-MSI-edge      nouveau


###中断亲合纠正

一些多队列网卡驱动实现的不是太好, 在初始化后会出现下图中同一个队列的 tx, rx 中断绑定到不同核上的问题, 这样数据在 core0 与 core1 之间
流动, 导致核间数据交互加大, cache命中率降低, 降低了效率.

![不合理中断绑定](unexpected_interrupt.gif)

linux network 子系统的负责人 David Miller 提供了一个脚本, 首先检索 /proc/interrupts 文件中的信息, 按照下图中 eth0-rx-0($VEC) 中的 VEC
得出中断 MASK, 并将 MASK 写入中断号 53 对应的 smp_affinity 中. 由于 eth-rx-0 与 eth-tx-0 的 VEC 相同, 实现同一个 queue 的 tx 与 rx 中
断绑定到一个核上, 如下图所示.

![合理中断绑定](unexpected_interrupt.gif)

###多队列网卡识别

#lspci -vvv

Ethernet controller 的条目内容, 如果有 MSI-X && Enable+ && TabSize > 1, 则该网卡是多队列网卡

$ sudo lspci -vvv | grep "MSI-X\|MSI:"

	Capabilities: [90] MSI: Enable+ Count=1/1 Maskable- 64bit-
	Capabilities: [80] MSI: Enable+ Count=1/8 Maskable- 64bit+
	Capabilities: [8c] MSI: Enable+ Count=1/1 Maskable- 64bit+
	Capabilities: [60] MSI: Enable+ Count=1/1 Maskable- 64bit+
	Capabilities: [80] MSI: Enable- Count=1/1 Maskable- 64bit-
	Capabilities: [80] MSI: Enable- Count=1/1 Maskable- 64bit-
	Capabilities: [80] MSI: Enable- Count=1/1 Maskable- 64bit-
	Capabilities: [80] MSI: Enable- Count=1/1 Maskable- 64bit-
	Capabilities: [80] MSI: Enable+ Count=1/1 Maskable- 64bit-
	Capabilities: [68] MSI: Enable+ Count=1/1 Maskable- 64bit+
	Capabilities: [68] MSI: Enable- Count=1/1 Maskable- 64bit+
	Capabilities: [50] MSI: Enable+ Count=1/1 Maskable- 64bit+
	Capabilities: [b0] MSI-X: Enable- Count=4 Masked-
	Capabilities: [50] MSI: Enable- Count=1/1 Maskable+ 64bit+
	Capabilities: [70] MSI-X: Enable+ Count=10 Masked-
	Capabilities: [50] MSI: Enable- Count=1/1 Maskable+ 64bit+
	Capabilities: [70] MSI-X: Enable+ Count=10 Masked-
	Capabilities: [50] MSI: Enable- Count=1/1 Maskable+ 64bit+
	Capabilities: [70] MSI-X: Enable+ Count=10 Masked-
	Capabilities: [50] MSI: Enable- Count=1/1 Maskable+ 64bit+
	Capabilities: [70] MSI-X: Enable+ Count=10 Masked-


Message Signaled Interrupts(MSI) 是 PCI 规范的一个实现, 可以突破 CPU 256 条 interrupt 的限制, 使每个设备具有多个中断线变成可能,
多队列网卡驱动给每个 queue 申请了 MSI. MSI-X 是 MSI 数组, Enable+ 指使能, TabSize 是数组大小.


##Ring Buffer

Ring Buffer 位于 NIC 和 IP 层之间, 是一个典型的 FIFO(先进先出) 环形队列. Ring Buffer
没有包含数据本身, 而是包含了指向 sk_buff (socket kernel buffers) 的描述符.

可以使用 ethtool -g eth0 查看当前 Ring Buffer 的设置:

$ ethtool -g eth0

    Ring parameters for eth0:
    Pre-set maximums:
    RX:     4096
    RX Mini:    0
    RX Jumbo:   0
    TX:     4096
    Current hardware settings:
    RX:     256
    RX Mini:    0
    RX Jumbo:   0
    TX:     256

上面的例子接收队列为 4096, 传输队列为 256. 可以通过 ifconfig 观察接收和传输队列的运行状况:

$ ifconfig eth0

    eth0    Link encap:Ethernet  HWaddr 5c:ff:35:06:d5:71
            UP BROADCAST MULTICAST  MTU:1500  Metric:1
            RX packets:0 errors:0 dropped:0 overruns:0 frame:0
            TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:1000
            RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
            Interrupt:20 Memory:f2500000-f2520000

其中

* RXerrors      : 收包总的错误数
* RX dropped    : 表示数据包已经进入了 RingBuffer, 但是由于内存不够等系统原因, 导致在拷贝到内存的过程中被丢弃.
* RX overruns   : overruns 意味着数据包没到 RingBuffer 就被网卡物理层给丢弃了, 而 CPU 无法及时的处理中断是造成
RingBuffer 满的原因之一, 例如中断分配的不均匀. 当 dropped 数量持续增加, 建议增大 RingBuffer, 使用 ethtool-G 进行设置.


##QDisc

QDisc(queueing discipline) 位于 IP 层和网卡的 Ring buffer 之间. 我们已经知道, Ring buffer 是一个简单的FIFO队列,
这种设计使网卡的驱动层保持简单和快速. 而 QDisc 实现了流量管理的高级功能, 包括流量分类, 优先级和流量整形(rate-shaping).
可以使用 tc 命令配置 QDisc.

QDisc 的队列长度由 txqueuelen 设置, 和接收数据包的队列长度由内核参数 net.core.netdev_max_backlog 控制所不同, txqueuelen
是和网卡关联, 可以用 ifconfig 命令查看当前的大小:

$ ifconfig eth0

    eth0    Link encap:Ethernet  HWaddr 5c:ff:35:06:d5:71
            UP BROADCAST MULTICAST  MTU:1500  Metric:1
            RX packets:0 errors:0 dropped:0 overruns:0 frame:0
            TX packets:0 errors:0 dropped:0 overruns:0 carrier:0
            collisions:0 txqueuelen:1000
            RX bytes:0 (0.0 B)  TX bytes:0 (0.0 B)
            Interrupt:20 Memory:f2500000-f2520000

其中

txqueuelen      : QDisc 的长度

使用 ifconfig 调整 txqueuelen 的大小; ifconfig eth0 txqueuelen 2000

##TCPSegmentation和Checksum Offloading

操作系统可以把一些 TCP/IP 的功能转交给网卡去完成, 特别是 Segmentation(分片) 和 checksum 的计算, 这样可以节省 CPU 资源,
并且由硬件代替 OS 执行这些操作会带来性能的提升. 一般以太网的
MTU(MaximumTransmission Unit)为 1500 bytes, 有效负载

    MTU 1500字节 - IP头部20字节 - TCP头部20字节 = 有效负载为1460字节

假设应用要发送数据包的大小为 7300 bytes, 因此 7300 字节需要拆分成 5 个 segment:

![TCP CPU 分片](tcp_segment_cpu.png)

Segmentation(分片) 操作可以由操作系统移交给网卡完成, 虽然最终线路上仍然是传输 5 个包, 但这样节省了 CPU 资源并带来性能
的提升:

![TCP 网卡分片](tcp_segment_device.png)

可以使用 ethtool -k eth0 查看网卡当前的 offloading 情况:

$ sudo ethtool -k eth0 | grep offload

    tcp-segmentation-offload: on
    udp-fragmentation-offload: off [fixed]
    generic-segmentation-offload: on
    generic-receive-offload: on
    large-receive-offload: off [fixed]
    rx-vlan-offload: on
    tx-vlan-offload: on
    l2-fwd-offload: off [fixed]

上面这个例子 checksum 和 tcp segmentation 的 offloading 都是打开的. 如果想设置网卡的 offloading 开关, 可以使用 ethtool-K
(注意K是大写)命令, 例如下面的命令关闭了 tcp

    sudo ethtool -K eth0 tso off

##参考

[RPS](http://lwn.net/Articles/362339/)
[RFS](http://lwn.net/Articles/382428/)
[大量小包的CPU密集型系统调优案例一则](http://blog.netzhou.net/?p=181)
[linux kernel 2.6.35中RFS特性详解](http://www.pagefault.info/?p=115?)
http://blog.chinaunix.net/uid-20662820-id-3850582.html

##附录

通过 /proc/interrupts 找到不同网卡的中断号, 然后计算网卡的MASK, 把掩码写入 /proc/irq/中断号/smp_affinity

```shell

	# setting up irq affinity according to /proc/interrupts
	# 2008-11-25 Robert Olsson
	# 2009-02-19 updated by Jesse Brandeburg
	#
	# > Dave Miller:
	# (To get consistent naming in /proc/interrups)
	# I would suggest that people use something like:
	# char buf[IFNAMSIZ+6];
	#
	# sprintf(buf, "%s-%s-%d",
	#         netdev->name,
	#  (RX_INTERRUPT ? "rx" : "tx"),
	#  queue->index);
	#
	#  Assuming a device with two RX and TX queues.
	#  This script will assign:
	#
	# eth0-rx-0  CPU0
	# eth0-rx-1  CPU1
	# eth0-tx-0  CPU0
	# eth0-tx-1  CPU1
	#

	set_affinity()
	{
		MASK=$((1<<$VEC))
		printf "%s mask=%X for /proc/irq/%d/smp_affinity\n" $DEV $MASK $IRQ
        #printf "%X" $MASK > /proc/irq/$IRQ/smp_affinity
		#echo $DEV mask=$MASK for /proc/irq/$IRQ/smp_affinity
		#echo $MASK > /proc/irq/$IRQ/smp_affinity
	}

	if [ "$1" = "" ] ; then
	 echo "Description:"
	 echo "    This script attempts to bind each queue of a multi-queue NIC"
	 echo "    to the same numbered core, ie tx0|rx0 --> cpu0, tx1|rx1 --> cpu1"
	 echo "usage:"
	 echo "    $0 eth0 [eth1 eth2 eth3]"
	fi


	# check for irqbalance running
	IRQBALANCE_ON=`ps ax | grep -v grep | grep -q irqbalance; echo $?`
	if [ "$IRQBALANCE_ON" == "0" ] ; then
	 echo " WARNING: irqbalance is running and will"
	 echo "          likely override this script's affinitization."
	 echo "          Please stop the irqbalance service and/or execute"
	 echo "          'killall irqbalance'"
	fi

	#
	# Set up the desired devices.
	#

	for DEV in $*
	do
	  for DIR in rx tx TxRx
	  do
		 MAX=`grep $DEV-$DIR /proc/interrupts | wc -l`
		 if [ "$MAX" == "0" ] ; then
		   MAX=`egrep -i "$DEV:.*$DIR" /proc/interrupts | wc -l`
		 fi
		 if [ "$MAX" == "0" ] ; then
		   echo no $DIR vectors found on $DEV
		   continue
		   #exit 1
		 fi
		 for VEC in `seq 0 1 $MAX`
		 do
		    IRQ=`cat /proc/interrupts | grep -i $DEV-$DIR-$VEC"$"  | cut  -d:  -f1 | sed "s/ //g"`
		    if [ -n  "$IRQ" ]; then
		      set_affinity
		    else
		       IRQ=`cat /proc/interrupts | egrep -i $DEV:v$VEC-$DIR"$"  | cut  -d:  -f1 | sed "s/ //g"`
		       if [ -n  "$IRQ" ]; then
		         set_affinity
		       fi
		    fi
		 done
	  done
	done

```



		HOWTO for multiqueue network device support
		===========================================

Section 1: Base driver requirements for implementing multiqueue support

Intro: Kernel support for multiqueue devices
---------------------------------------------------------

Kernel support for multiqueue devices is always present.

Section 1: Base driver requirements for implementing multiqueue support
-----------------------------------------------------------------------

Base drivers are required to use the new alloc_etherdev_mq() or
alloc_netdev_mq() functions to allocate the subqueues for the device.  The
underlying kernel API will take care of the allocation and deallocation of
the subqueue memory, as well as netdev configuration of where the queues
exist in memory.

The base driver will also need to manage the queues as it does the global
netdev->queue_lock today.  Therefore base drivers should use the
netif_{start|stop|wake}_subqueue() functions to manage each queue while the
device is still operational.  netdev->queue_lock is still used when the device
comes online or when it's completely shut down (unregister_netdev(), etc.).


Section 2: Qdisc support for multiqueue devices

-----------------------------------------------

Currently two qdiscs are optimized for multiqueue devices.  The first is the
default pfifo_fast qdisc.  This qdisc supports one qdisc per hardware queue.
A new round-robin qdisc, sch_multiq also supports multiple hardware queues. The
qdisc is responsible for classifying the skb's and then directing the skb's to
bands and queues based on the value in skb->queue_mapping.  Use this field in
the base driver to determine which queue to send the skb to.

sch_multiq has been added for hardware that wishes to avoid head-of-line
blocking.  It will cycle though the bands and verify that the hardware queue
associated with the band is not stopped prior to dequeuing a packet.

On qdisc load, the number of bands is based on the number of queues on the
hardware.  Once the association is made, any skb with skb->queue_mapping set,
will be queued to the band associated with the hardware queue.


Section 3: Brief howto using MULTIQ for multiqueue devices
---------------------------------------------------------------

The userspace command 'tc,' part of the iproute2 package, is used to configure
qdiscs.  To add the MULTIQ qdisc to your network device, assuming the device
is called eth0, run the following command:

# tc qdisc add dev eth0 root handle 1: multiq

The qdisc will allocate the number of bands to equal the number of queues that
the device reports, and bring the qdisc online.  Assuming eth0 has 4 Tx
queues, the band mapping would look like:

band 0 => queue 0
band 1 => queue 1
band 2 => queue 2
band 3 => queue 3

Traffic will begin flowing through each queue based on either the simple_tx_hash
function or based on netdev->select_queue() if you have it defined.

The behavior of tc filters remains the same.  However a new tc action,
skbedit, has been added.  Assuming you wanted to route all traffic to a
specific host, for example 192.168.0.3, through a specific queue you could use
this action and establish a filter such as:

tc filter add dev eth0 parent 1: protocol ip prio 1 u32 \
	match ip dst 192.168.0.3 \
	action skbedit queue_mapping 3

Author: Alexander Duyck <alexander.h.duyck@intel.com>
Original Author: Peter P. Waskiewicz Jr. <peter.p.waskiewicz.jr@intel.com>


###网卡


Scaling in the Linux Networking Stack


Introduction
============

This document describes a set of complementary techniques in the Linux
networking stack to increase parallelism and improve performance for
multi-processor systems.

The following technologies are described:

  RSS: Receive Side Scaling
  RPS: Receive Packet Steering
  RFS: Receive Flow Steering
  Accelerated Receive Flow Steering
  XPS: Transmit Packet Steering


RSS: Receive Side Scaling
=========================

Contemporary NICs support multiple receive and transmit descriptor queues
(multi-queue). On reception, a NIC can send different packets to different
queues to distribute processing among CPUs. The NIC distributes packets by
applying a filter to each packet that assigns it to one of a small number
of logical flows. Packets for each flow are steered to a separate receive
queue, which in turn can be processed by separate CPUs. This mechanism is
generally known as “Receive-side Scaling” (RSS). The goal of RSS and
the other scaling techniques is to increase performance uniformly.
Multi-queue distribution can also be used for traffic prioritization, but
that is not the focus of these techniques.

The filter used in RSS is typically a hash function over the network
and/or transport layer headers-- for example, a 4-tuple hash over
IP addresses and TCP ports of a packet. The most common hardware
implementation of RSS uses a 128-entry indirection table where each entry
stores a queue number. The receive queue for a packet is determined
by masking out the low order seven bits of the computed hash for the
packet (usually a Toeplitz hash), taking this number as a key into the
indirection table and reading the corresponding value.

Some advanced NICs allow steering packets to queues based on
programmable filters. For example, webserver bound TCP port 80 packets
can be directed to their own receive queue. Such “n-tuple” filters can
be configured from ethtool (--config-ntuple).

==== RSS Configuration

The driver for a multi-queue capable NIC typically provides a kernel
module parameter for specifying the number of hardware queues to
configure. In the bnx2x driver, for instance, this parameter is called
num_queues. A typical RSS configuration would be to have one receive queue
for each CPU if the device supports enough queues, or otherwise at least
one for each memory domain, where a memory domain is a set of CPUs that
share a particular memory level (L1, L2, NUMA node, etc.).

The indirection table of an RSS device, which resolves a queue by masked
hash, is usually programmed by the driver at initialization. The
default mapping is to distribute the queues evenly in the table, but the
indirection table can be retrieved and modified at runtime using ethtool
commands (--show-rxfh-indir and --set-rxfh-indir). Modifying the
indirection table could be done to give different queues different
relative weights.

== RSS IRQ Configuration

Each receive queue has a separate IRQ associated with it. The NIC triggers
this to notify a CPU when new packets arrive on the given queue. The
signaling path for PCIe devices uses message signaled interrupts (MSI-X),
that can route each interrupt to a particular CPU. The active mapping
of queues to IRQs can be determined from /proc/interrupts. By default,
an IRQ may be handled on any CPU. Because a non-negligible part of packet
processing takes place in receive interrupt handling, it is advantageous
to spread receive interrupts between CPUs. To manually adjust the IRQ
affinity of each interrupt see Documentation/IRQ-affinity.txt. Some systems
will be running irqbalance, a daemon that dynamically optimizes IRQ
assignments and as a result may override any manual settings.

== Suggested Configuration

RSS should be enabled when latency is a concern or whenever receive
interrupt processing forms a bottleneck. Spreading load between CPUs
decreases queue length. For low latency networking, the optimal setting
is to allocate as many queues as there are CPUs in the system (or the
NIC maximum, if lower). The most efficient high-rate configuration
is likely the one with the smallest number of receive queues where no
receive queue overflows due to a saturated CPU, because in default
mode with interrupt coalescing enabled, the aggregate number of
interrupts (and thus work) grows with each additional queue.

Per-cpu load can be observed using the mpstat utility, but note that on
processors with hyperthreading (HT), each hyperthread is represented as
a separate CPU. For interrupt handling, HT has shown no benefit in
initial tests, so limit the number of queues to the number of CPU cores
in the system.


RPS: Receive Packet Steering
============================

Receive Packet Steering (RPS) is logically a software implementation of
RSS. Being in software, it is necessarily called later in the datapath.
Whereas RSS selects the queue and hence CPU that will run the hardware
interrupt handler, RPS selects the CPU to perform protocol processing
above the interrupt handler. This is accomplished by placing the packet
on the desired CPU’s backlog queue and waking up the CPU for processing.
RPS has some advantages over RSS: 1) it can be used with any NIC,
2) software filters can easily be added to hash over new protocols,
3) it does not increase hardware device interrupt rate (although it does
introduce inter-processor interrupts (IPIs)).

RPS is called during bottom half of the receive interrupt handler, when
a driver sends a packet up the network stack with netif_rx() or
netif_receive_skb(). These call the get_rps_cpu() function, which
selects the queue that should process a packet.

The first step in determining the target CPU for RPS is to calculate a
flow hash over the packet’s addresses or ports (2-tuple or 4-tuple hash
depending on the protocol). This serves as a consistent hash of the
associated flow of the packet. The hash is either provided by hardware
or will be computed in the stack. Capable hardware can pass the hash in
the receive descriptor for the packet; this would usually be the same
hash used for RSS (e.g. computed Toeplitz hash). The hash is saved in
skb->rx_hash and can be used elsewhere in the stack as a hash of the
packet’s flow.

Each receive hardware queue has an associated list of CPUs to which
RPS may enqueue packets for processing. For each received packet,
an index into the list is computed from the flow hash modulo the size
of the list. The indexed CPU is the target for processing the packet,
and the packet is queued to the tail of that CPU’s backlog queue. At
the end of the bottom half routine, IPIs are sent to any CPUs for which
packets have been queued to their backlog queue. The IPI wakes backlog
processing on the remote CPU, and any queued packets are then processed
up the networking stack.

==== RPS Configuration

RPS requires a kernel compiled with the CONFIG_RPS kconfig symbol (on
by default for SMP). Even when compiled in, RPS remains disabled until
explicitly configured. The list of CPUs to which RPS may forward traffic
can be configured for each receive queue using a sysfs file entry:

 /sys/class/net/<dev>/queues/rx-<n>/rps_cpus

This file implements a bitmap of CPUs. RPS is disabled when it is zero
(the default), in which case packets are processed on the interrupting
CPU. Documentation/IRQ-affinity.txt explains how CPUs are assigned to
the bitmap.

== Suggested Configuration

For a single queue device, a typical RPS configuration would be to set
the rps_cpus to the CPUs in the same memory domain of the interrupting
CPU. If NUMA locality is not an issue, this could also be all CPUs in
the system. At high interrupt rate, it might be wise to exclude the
interrupting CPU from the map since that already performs much work.

For a multi-queue system, if RSS is configured so that a hardware
receive queue is mapped to each CPU, then RPS is probably redundant
and unnecessary. If there are fewer hardware queues than CPUs, then
RPS might be beneficial if the rps_cpus for each queue are the ones that
share the same memory domain as the interrupting CPU for that queue.

==== RPS Flow Limit

RPS scales kernel receive processing across CPUs without introducing
reordering. The trade-off to sending all packets from the same flow
to the same CPU is CPU load imbalance if flows vary in packet rate.
In the extreme case a single flow dominates traffic. Especially on
common server workloads with many concurrent connections, such
behavior indicates a problem such as a misconfiguration or spoofed
source Denial of Service attack.

Flow Limit is an optional RPS feature that prioritizes small flows
during CPU contention by dropping packets from large flows slightly
ahead of those from small flows. It is active only when an RPS or RFS
destination CPU approaches saturation.  Once a CPU's input packet
queue exceeds half the maximum queue length (as set by sysctl
net.core.netdev_max_backlog), the kernel starts a per-flow packet
count over the last 256 packets. If a flow exceeds a set ratio (by
default, half) of these packets when a new packet arrives, then the
new packet is dropped. Packets from other flows are still only
dropped once the input packet queue reaches netdev_max_backlog.
No packets are dropped when the input packet queue length is below
the threshold, so flow limit does not sever connections outright:
even large flows maintain connectivity.

== Interface

Flow limit is compiled in by default (CONFIG_NET_FLOW_LIMIT), but not
turned on. It is implemented for each CPU independently (to avoid lock
and cache contention) and toggled per CPU by setting the relevant bit
in sysctl net.core.flow_limit_cpu_bitmap. It exposes the same CPU
bitmap interface as rps_cpus (see above) when called from procfs:

 /proc/sys/net/core/flow_limit_cpu_bitmap

Per-flow rate is calculated by hashing each packet into a hashtable
bucket and incrementing a per-bucket counter. The hash function is
the same that selects a CPU in RPS, but as the number of buckets can
be much larger than the number of CPUs, flow limit has finer-grained
identification of large flows and fewer false positives. The default
table has 4096 buckets. This value can be modified through sysctl

 net.core.flow_limit_table_len

The value is only consulted when a new table is allocated. Modifying
it does not update active tables.

== Suggested Configuration

Flow limit is useful on systems with many concurrent connections,
where a single connection taking up 50% of a CPU indicates a problem.
In such environments, enable the feature on all CPUs that handle
network rx interrupts (as set in /proc/irq/N/smp_affinity).

The feature depends on the input packet queue length to exceed
the flow limit threshold (50%) + the flow history length (256).
Setting net.core.netdev_max_backlog to either 1000 or 10000
performed well in experiments.


RFS: Receive Flow Steering
==========================

While RPS steers packets solely based on hash, and thus generally
provides good load distribution, it does not take into account
application locality. This is accomplished by Receive Flow Steering
(RFS). The goal of RFS is to increase datacache hitrate by steering
kernel processing of packets to the CPU where the application thread
consuming the packet is running. RFS relies on the same RPS mechanisms
to enqueue packets onto the backlog of another CPU and to wake up that
CPU.

In RFS, packets are not forwarded directly by the value of their hash,
but the hash is used as index into a flow lookup table. This table maps
flows to the CPUs where those flows are being processed. The flow hash
(see RPS section above) is used to calculate the index into this table.
The CPU recorded in each entry is the one which last processed the flow.
If an entry does not hold a valid CPU, then packets mapped to that entry
are steered using plain RPS. Multiple table entries may point to the
same CPU. Indeed, with many flows and few CPUs, it is very likely that
a single application thread handles flows with many different flow hashes.

rps_sock_flow_table is a global flow table that contains the *desired* CPU
for flows: the CPU that is currently processing the flow in userspace.
Each table value is a CPU index that is updated during calls to recvmsg
and sendmsg (specifically, inet_recvmsg(), inet_sendmsg(), inet_sendpage()
and tcp_splice_read()).

When the scheduler moves a thread to a new CPU while it has outstanding
receive packets on the old CPU, packets may arrive out of order. To
avoid this, RFS uses a second flow table to track outstanding packets
for each flow: rps_dev_flow_table is a table specific to each hardware
receive queue of each device. Each table value stores a CPU index and a
counter. The CPU index represents the *current* CPU onto which packets
for this flow are enqueued for further kernel processing. Ideally, kernel
and userspace processing occur on the same CPU, and hence the CPU index
in both tables is identical. This is likely false if the scheduler has
recently migrated a userspace thread while the kernel still has packets
enqueued for kernel processing on the old CPU.

The counter in rps_dev_flow_table values records the length of the current
CPU's backlog when a packet in this flow was last enqueued. Each backlog
queue has a head counter that is incremented on dequeue. A tail counter
is computed as head counter + queue length. In other words, the counter
in rps_dev_flow[i] records the last element in flow i that has
been enqueued onto the currently designated CPU for flow i (of course,
entry i is actually selected by hash and multiple flows may hash to the
same entry i).

And now the trick for avoiding out of order packets: when selecting the
CPU for packet processing (from get_rps_cpu()) the rps_sock_flow table
and the rps_dev_flow table of the queue that the packet was received on
are compared. If the desired CPU for the flow (found in the
rps_sock_flow table) matches the current CPU (found in the rps_dev_flow
table), the packet is enqueued onto that CPU’s backlog. If they differ,
the current CPU is updated to match the desired CPU if one of the
following is true:

- The current CPU's queue head counter >= the recorded tail counter
  value in rps_dev_flow[i]
- The current CPU is unset (>= nr_cpu_ids)
- The current CPU is offline

After this check, the packet is sent to the (possibly updated) current
CPU. These rules aim to ensure that a flow only moves to a new CPU when
there are no packets outstanding on the old CPU, as the outstanding
packets could arrive later than those about to be processed on the new
CPU.

==== RFS Configuration

RFS is only available if the kconfig symbol CONFIG_RPS is enabled (on
by default for SMP). The functionality remains disabled until explicitly
configured. The number of entries in the global flow table is set through:

 /proc/sys/net/core/rps_sock_flow_entries

The number of entries in the per-queue flow table are set through:

 /sys/class/net/<dev>/queues/rx-<n>/rps_flow_cnt

== Suggested Configuration

Both of these need to be set before RFS is enabled for a receive queue.
Values for both are rounded up to the nearest power of two. The
suggested flow count depends on the expected number of active connections
at any given time, which may be significantly less than the number of open
connections. We have found that a value of 32768 for rps_sock_flow_entries
works fairly well on a moderately loaded server.

For a single queue device, the rps_flow_cnt value for the single queue
would normally be configured to the same value as rps_sock_flow_entries.
For a multi-queue device, the rps_flow_cnt for each queue might be
configured as rps_sock_flow_entries / N, where N is the number of
queues. So for instance, if rps_sock_flow_entries is set to 32768 and there
are 16 configured receive queues, rps_flow_cnt for each queue might be
configured as 2048.


Accelerated RFS
===============

Accelerated RFS is to RFS what RSS is to RPS: a hardware-accelerated load
balancing mechanism that uses soft state to steer flows based on where
the application thread consuming the packets of each flow is running.
Accelerated RFS should perform better than RFS since packets are sent
directly to a CPU local to the thread consuming the data. The target CPU
will either be the same CPU where the application runs, or at least a CPU
which is local to the application thread’s CPU in the cache hierarchy.

To enable accelerated RFS, the networking stack calls the
ndo_rx_flow_steer driver function to communicate the desired hardware
queue for packets matching a particular flow. The network stack
automatically calls this function every time a flow entry in
rps_dev_flow_table is updated. The driver in turn uses a device specific
method to program the NIC to steer the packets.

The hardware queue for a flow is derived from the CPU recorded in
rps_dev_flow_table. The stack consults a CPU to hardware queue map which
is maintained by the NIC driver. This is an auto-generated reverse map of
the IRQ affinity table shown by /proc/interrupts. Drivers can use
functions in the cpu_rmap (“CPU affinity reverse map”) kernel library
to populate the map. For each CPU, the corresponding queue in the map is
set to be one whose processing CPU is closest in cache locality.

==== Accelerated RFS Configuration

Accelerated RFS is only available if the kernel is compiled with
CONFIG_RFS_ACCEL and support is provided by the NIC device and driver.
It also requires that ntuple filtering is enabled via ethtool. The map
of CPU to queues is automatically deduced from the IRQ affinities
configured for each receive queue by the driver, so no additional
configuration should be necessary.

== Suggested Configuration

This technique should be enabled whenever one wants to use RFS and the
NIC supports hardware acceleration.

XPS: Transmit Packet Steering
=============================

Transmit Packet Steering is a mechanism for intelligently selecting
which transmit queue to use when transmitting a packet on a multi-queue
device. To accomplish this, a mapping from CPU to hardware queue(s) is
recorded. The goal of this mapping is usually to assign queues
exclusively to a subset of CPUs, where the transmit completions for
these queues are processed on a CPU within this set. This choice
provides two benefits. First, contention on the device queue lock is
significantly reduced since fewer CPUs contend for the same queue
(contention can be eliminated completely if each CPU has its own
transmit queue). Secondly, cache miss rate on transmit completion is
reduced, in particular for data cache lines that hold the sk_buff
structures.

XPS is configured per transmit queue by setting a bitmap of CPUs that
may use that queue to transmit. The reverse mapping, from CPUs to
transmit queues, is computed and maintained for each network device.
When transmitting the first packet in a flow, the function
get_xps_queue() is called to select a queue. This function uses the ID
of the running CPU as a key into the CPU-to-queue lookup table. If the
ID matches a single queue, that is used for transmission. If multiple
queues match, one is selected by using the flow hash to compute an index
into the set.

The queue chosen for transmitting a particular flow is saved in the
corresponding socket structure for the flow (e.g. a TCP connection).
This transmit queue is used for subsequent packets sent on the flow to
prevent out of order (ooo) packets. The choice also amortizes the cost
of calling get_xps_queues() over all packets in the flow. To avoid
ooo packets, the queue for a flow can subsequently only be changed if
skb->ooo_okay is set for a packet in the flow. This flag indicates that
there are no outstanding packets in the flow, so the transmit queue can
change without the risk of generating out of order packets. The
transport layer is responsible for setting ooo_okay appropriately. TCP,
for instance, sets the flag when all data for a connection has been
acknowledged.

==== XPS Configuration

XPS is only available if the kconfig symbol CONFIG_XPS is enabled (on by
default for SMP). The functionality remains disabled until explicitly
configured. To enable XPS, the bitmap of CPUs that may use a transmit
queue is configured using the sysfs file entry:

/sys/class/net/<dev>/queues/tx-<n>/xps_cpus

== Suggested Configuration

For a network device with a single transmission queue, XPS configuration
has no effect, since there is no choice in this case. In a multi-queue
system, XPS is preferably configured so that each CPU maps onto one queue.
If there are as many queues as there are CPUs in the system, then each
queue can also map onto one CPU, resulting in exclusive pairings that
experience no contention. If there are fewer queues than CPUs, then the
best CPUs to share a given queue are probably those that share the cache
with the CPU that processes transmit completions for that queue
(transmit interrupts).

Per TX Queue rate limitation:
=============================

These are rate-limitation mechanisms implemented by HW, where currently
a max-rate attribute is supported, by setting a Mbps value to

/sys/class/net/<dev>/queues/tx-<n>/tx_maxrate

A value of zero means disabled, and this is the default.

Further Information
===================
RPS and RFS were introduced in kernel 2.6.35. XPS was incorporated into
2.6.38. Original patches were submitted by Tom Herbert
(therbert@google.com)

Accelerated RFS was introduced in 2.6.35. Original patches were
submitted by Ben Hutchings (bwh@kernel.org)

Authors:
Tom Herbert (therbert@google.com)
Willem de Bruijn (willemb@google.com)
