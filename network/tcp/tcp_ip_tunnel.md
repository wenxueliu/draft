
## TCP 调优

###为什么调优

1. 设定目标, 调优要达到的目的.
2. 设定实现目标关注的指标, 速度, 延迟, TPS ...
3. 理解每次调优的意义(理解参数背后的机理)
4. 测试, 测试, 测试, 重要的事情说三遍, 通过测试来验证是否达到目标
5. 记录每一次测试过程

###误区

不要过于依赖测试工具, 有时候测试工具的结果过于理想化, 但可以作为参考


调优的前提是诊断出问题, 而不是对内核参数的随意或猜测性修改. 犹如名医诊断病人,
能通过望, 闻, 问, 切对诊断病人的病情, 之后对症下药. 网络调优也是如此, 只有
发现问题, 仔细诊断问题根源, 之后解决问题. 下面就谈谈, 网络的望,闻, 问, 切的
精要.

首先, 只有出问题才需要调优. 最常见的问题是发生丢包, 导致应用出现错误.

###望

要诊断网络系统的问题, 首先要通过工具, 下面就先谈谈哪些工具进行网络问题的诊断.

假设我们给系统发生了 6000 个并发持续一小时, 以下是诊断手段

1. 检查是建立了 6000 个 TCP 连接

$ss -s

    Total: 6380 (kernel 0)
    TCP:   24887 (estab 2150, closed 19290, orphaned 0, synrecv 0, timewait
            19289/0), ports 0

    Transport Total     IP        IPv6
    *         0         -         -
    RAW       1         0         1
    UDP       19        13        6
    TCP       5597      5592      5
    INET      5617      5605      12
    FRAG      0         0         0

$ sudo ss -s
Total: 6546 (kernel 6977)
    TCP:   27010 (estab 3174, closed 21253, orphaned 0, synrecv 0, timewait
            21252/0), ports 0

    Transport Total     IP        IPv6
    *         6977      -         -
    RAW       1         0         1
    UDP       19        13        6
    TCP       5757      5752      5
    INET      5777      5765      12
    FRAG      0         0         0

注意, 一定要 sudo, 结果是由区别的

2. 检查网卡是否发生丢包

$ sudo  ping -f SERVER_IP

$ sudo netstat -i

    Kernel Interface table
    Iface      MTU    RX-OK RX-ERR RX-DRP RX-OVR    TX-OK TX-ERR TX-DRP TX-OVR Flg
    em1       1500 975363774      0   5077 0      770774553      0      0      0
    BMRU
    em2       1500  3112089      0      0 0       2910292      0      0      0 BMRU
    lo       65536      761      0      0 0           761      0      0      0 LRU
    virbr0    1500        0      0      0 0             1      0      0      0 BMU

$ sudo ip -s link show em1

    2: em1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP mode DEFAULT qlen 1000
        link/ether f0:1f:af:e5:ba:39 brd ff:ff:ff:ff:ff:ff
        RX: bytes  packets  errors  dropped overrun mcast
        83771290092 979075631 0       4899    0       5107
        TX: bytes  packets  errors  dropped carrier collsns
        160083089401 773788434 0       0       0       0


3. 检查 tcp 更详细的情况

ss -ant | awk ' {++state[$1]} END {for(k in state) print k,state[k]} '

$ nstat

4. 内核参数

##QA

Q: 目前网络的 RTT 是 1 ms, 如何模拟 10ms 的 RTT.
A: 通过 tc, sudo tc qdisc add dev eth0 root netem delay 10ms



##TCP 相关参数介绍

sysctl -a
man tcp
man -S7 socket

###参数调优

两种修改内核参数方法

    使用echo value方式直接追加到文件里如echo "1" >/proc/sys/net/ipv4/tcp_syn_retries, 但这种方法设备重启后又会恢复为默认值

    把参数添加到/etc/sysctl.conf中, 然后执行sysctl -p 使参数生效, 永久生效

    注: 修改参数后需要重启应用. 如 nginx

##/proc/sys/net/ipv4/

###tcp_syn_retries

* 默认值 5
* 建议值 1

对于一个新建连接, 内核要发送多少个 SYN 连接请求才决定放弃. 不应该大于255, 默认值是5,
对应于 180 秒左右时间.(对于大负载而物理通信良好的网络而言, 这个值偏高, 可修改为2.
这个值仅仅是针对对外的连接, 对进来的连接, 是由 tcp_retries1 决定的)

###tcp_synack_retries

* 默认值 5
* 建议值 1

对于远端的连接请求 SYN, 内核会发送 SYN ＋ ACK 数据报, 以确认收到上一个 SYN 连接请求包.
这是所谓的三次握手(three way handshake)机制的第二个步骤. 这里决定内核在放弃连接之前所
送出的 SYN+ACK 数目. 不应该大于255, 默认值是 5, 对应于 180 秒左右时间.

###tcp_keepalive_time 有误??

* 默认值 7200
* 建议值 600

TCP 发送 keepalive 探测消息的间隔时间（秒）, 用于确认 TCP 连接是否有效. 
防止两边建立连接但不发送数据的攻击

###tcp_keepalive_probes

* 默认值 9
* 建议值 3

如果对方不予应答, TCP发送 keepalive 探测消息的次数, 用于确认 TCP 连接是否有效. 

###tcp_retries1

* 默认值 3
* 建议值 3

放弃回应一个 TCP 连接请求前, 需要进行多少次重试. RFC 规定最低的数值是 3

###tcp_retries2

* 默认值 15
* 建议值 5

在丢弃激活(已建立通讯状况)的 TCP 连接之前﹐需要进行多少次重试. 默认值为 15, 根据 RTO 的值来决定,
相当于 13-30 分钟(RFC1122规定, 必须大于100秒).(这个值根据目前的网络设置,可以适当地改小,我的网络
内修改为了 5)

###tcp_orphan_retries

* 默认值 7
* 建议值 3

在近端丢弃TCP连接之前﹐要进行多少次重试. 默认值是 7 个﹐相当于 50秒 - 16分钟﹐视 RTO 而定. 
如果您的系统是负载很大的 web 服务器﹐那么也许需要降低该值﹐这类 sockets 可能会耗费大量的资源. 
另外参的考 tcp_max_orphans. (事实上做NAT的时候,降低该值也是好处显著的,我本人的网络环境中降低该值为3)

###tcp_fin_timeout

* 默认值 60
* 建议值 2

对于本端断开的 socket 连接, TCP 保持在 FIN-WAIT-2 状态的时间. 对方可能会断开连接或一直不结束连接或
不可预料的进程死亡. 默认值为 60 秒. 

###tcp_max_tw_buckets

* 默认值 180000
* 建议值 36000

系统在同时所处理的最大 timewait sockets 数目. 如果超过此数的话﹐time-wait socket 会被立即砍除
并且显示警告信息. 之所以要设定这个限制﹐纯粹为了抵御那些简单的 DoS 攻击﹐不过﹐如果网络条件需
要比默认值更多﹐则可以提高它(或许还要增加内存). (事实上做 NAT 的时候最好可以适当地增加该值)

###tcp_tw_recycle

* 默认值 0
* 建议值 1

打开快速 TIME-WAIT sockets 回收. 除非得到技术专家的建议或要求﹐请不要随意修改这个值. 
(做NAT的时候, 建议打开它)

###tcp_tw_reuse

* 默认值 0
* 建议值 1

表示是否允许重新应用处于TIME-WAIT状态的socket用于新的TCP连接(这个对快速重启动某些服务,而启动
后提示端口已经被使用的情形非常有帮助)

###tcp_max_orphans

* 默认值 8192
* 建议值 32768

系统所能处理不属于任何进程的 TCP sockets 最大数量. 假如超过这个数量﹐那么不属于任何进程的连接
会被立即 reset, 并同时显示警告信息. 之所以要设定这个限制﹐纯粹为了抵御那些简单的
DoS 攻击﹐千万不要依赖这个或是人为的降低这个限制. 如果内存大更应该增加这个值. (这个值Redhat
AS版本中设置为 32768,但是很多防火墙修改的时候,建议该值修改为 2000)

###tcp_abort_on_overflow

* 默认值 0
* 建议值 0

当守护进程太忙而不能接受新的连接, 就象对方发送 reset 消息, 默认值是 false. 这意味着当溢出的原
因是因为一个偶然的猝发, 那么连接将恢复状态. 只有在你确信守护进程真的不能完成连接请求时才打开该
选项, 该选项会影响客户的使用. (对待已经满载的 sendmail,apache 这类服务的时候,这个可以很快让客
户端终止连接,可以给予服务程序处理已有连接的缓冲机会,所以很多防火墙上推荐打开它)

###tcp_syncookies

* 默认值 0
* 建议值 1

只有在内核编译时选择了 CONFIG_SYNCOOKIES 时才会发生作用. 当出现 syn 等候队列出现溢出时象对方发送
syncookies. 目的是为了防止 syn flood攻击. 

###tcp_stdurg

* 默认值 0
* 建议值 0

使用 TCP urg pointer 字段中的主机请求解释功能. 大部份的主机都使用老旧的 BSD 解释, 因此如果您在 
Linux 打开它﹐或会导致不能和它们正确沟通

###tcp_max_syn_backlog

* 默认值 1024
* 建议值 16384

对于那些依然还未获得客户端确认的连接请求, 处于半连接状态(SYN_RECV)的队列长度.

警告! 假如您将此值设为大于 1024﹐最好修改 include/net/tcp.h 里面的 TCP_SYNQ_HSIZE, 以保持
TCP_SYNQ_HSIZE*16

**SYN Flood**

SYN Flood 攻击利用 TCP 协议散布握手的缺陷, 伪造虚假源 IP 地址发送大量 TCP-SYN
半打开连接到目标系统, 最终导致目标系统 Socket 队列资源耗尽而无法接受新的连接. 


为了应付这种攻击, 现代 Unix 系统中普遍采用多连接队列处理的方式来缓冲(而不是解决)这种攻击, 是用一个基
本队列处理正常的完全连接应用(Connect() 和 Accept()), 是用另一个队列单独存放半打开连接. 这种双队列处理
方式和其他一些系统内核措施(例如Syn-Cookies/Caches)联合应用时, 能够比较有效的缓解小规模的SYN Flood攻击

Linux 实现了一种称为 SYN cookie 的机制，通过 net.ipv4.tcp_syncookies 控制，设置为1表示开启。简单说
SYN cookie 就是将连接信息编码在 ISN (initial sequence number)中返回给客户端，这时server不需要将半连接
保存在队列中，而是利用客户端随后发来的ACK带回的 ISN 还原连接信息, 以完成连接的建立, 避免了半连接队列被
攻击 SYN 包填满. 对于一去不复返的客户端握手, 不理它就是了.

###tcp_window_scaling

* 默认值 1
* 建议值 1

该文件表示设置 tcp/ip 会话的滑动窗口大小是否可变. 参数值为布尔值, 为 1 时表示可变, 为 0 时表示不可变. 
tcp/ip通常使用的窗口最大可达到 65535 字节, 对于高速网络, 该值可能太小, 这时候如果启用了该功能, 可以
使 tcp/ip 滑动窗口大小增大数个数量级, 从而提高数据传输的能力(RFC 1323). （对普通地百M网络而言, 关闭
会降低开销, 所以如果不是高速网络, 可以考虑设置为 0）

###tcp_timestamps

* 默认值 1
* 建议值 1

Timestamps 用在其它一些东西中﹐可以防范那些伪造的 sequence 号码. 一条 1G 的宽带线路或许会重遇到带
out-of-line 数值的旧 sequence 号码(假如它是由于上次产生的). Timestamp 会让它知道这是个 '旧封包'. 
(该文件表示是否启用以一种比超时重发更精确的方法（RFC 1323）来启用对 RTT 的计算; 为了实现更好的性能
 应该启用这个选项. )

###tcp_sack

* 默认值 1
* 建议值 1

使用 Selective ACK﹐它可以用来查找特定的遗失的数据报 --- 因此有助于快速恢复状态. 该文件表示是否启用
有选择的应答（Selective Acknowledgment）, 这可以通过有选择地应答乱序接收到的报文来提高性能（这样可以
让发送者只发送丢失的报文段）. (对于广域网通信来说这个选项应该启用, 但是这会增加对 CPU 的占用. )

###tcp_fack

* 默认值 1
* 建议值 1

打开 FACK 拥塞避免和快速重传功能. (注意, 当 tcp_sack 设置为 0 的时候, 这个值即使设置为1也无效)[这个是
TCP 连接靠谱的核心功能]

###tcp_dsack

* 默认值 1
* 建议值 1

允许TCP发送"两个完全相同"的SACK. 

###tcp_ecn

* 默认值 0
* 建议值 0

TCP的直接拥塞通告功能

###tcp_reordering

* 默认值 3
* 建议值 6

TCP流中重排序的数据报最大数量.  (一般有看到推荐把这个数值略微调整大一些,比如5)

###tcp_retrans_collapse

* 默认值 0
* 建议值 1

对于某些有bug的打印机提供针对其bug的兼容性. (一般不需要这个支持,可以关闭它)

###tcp_wmem: min default max

* 默认值 4096 16384 131072
* 建议值 8192 131072 16777216

发送缓存设置

min: 为 TCP socket 预留用于发送缓冲的内存最小值. 每个 tcp socket 都可以在建议
以后都可以使用它. 默认值为 4096(4K).

default: 为 TCP socket 预留用于发送缓冲的内存数量, 默认情况下该值会影响其它协议
使用的 net.core.wmem_default 值, 一般要低于 net.core.wmem_default 的值. 默认值为
16384(16K).

max: 用于 TCP socket 发送缓冲的内存最大值. 该值不会影响 net.core.wmem_max, "静态"
选择参数 SO_SNDBUF 则不受该值影响. 默认值为 131072(128K). （对于服务器而言, 增加这
个参数的值对于发送数据很有帮助, 在我的网络环境中, 修改为了 51200 131072 204800）

SO_SNDBUF 是具体连接的写缓存大小, 不受制于 tcp_wmem 的值, 但受制于 net.core.wmem_max
即当 SO_SNDBUF 大于  net.core.wmem_max 时, 取 net.core.wmem_max. 需要注意的是,
实际值是 SO_SNDBUF * 2
发送端缓冲的自动调节机制很早就已经实现, 并且是无条件开启, 没有参数去设置. 如果指
定了 tcp_wmem, 则 net.core.wmem_default 被 tcp_wmem 的覆盖. sendBuffer 在 tcp_wmem
的最小值和最大值之间自动调节. 如果调用 setsockopt() 设置了 socket 选项 SO_SNDBUF,
将关闭发送端缓冲的自动调节机制, tcp_wmem 将被忽略, SO_SNDBUF 的最大值由 net.core.wmem_max
限制。

###tcp_rmem: min default max

* 默认值 4096 87380 174760
* 建议值 32768 131072 16777216

接收缓存设置 同 tcp_wmem

BDP(Bandwidth-delayproduct, 带宽延迟积) 是网络的带宽和与 RTT(roundtrip time) 的乘积,
BDP 的含义是任意时刻处于在途未确认的最大数据量. RTT 使用 ping 命令可以很容易的得到.
为了达到最大的吞吐量, recvBuffer 的设置应该大于 BDP, 即 recvBuffer >= bandwidth * RTT.

假设带宽是 100Mbps, RTT 是 100ms, 那么 BDP 的计算如下:

	BDP = 100Mbps * 100ms = (100 / 8) * (100 / 1000) = 1.25MB

Linux 在 2.6.17 以后增加了 rcvBuf 自动调节机制, rcvBuf 的实际大小会自动在最小值和
最大值之间浮动, 以期找到性能和资源的平衡点, 因此大多数情况下不建议将 rcvBuf 手工
设置成固定值.

当 net.ipv4.tcp_moderate_rcvbuf = 1 时, 自动调节机制生效, 每个 TCP 连接的 rcvBuf
由下面的 3 元数组指定:

net.ipv4.tcp_rmem = 4096 87380   6291456

最初 rcvBuf 被设置为 87380, 同时这个缺省值会覆盖 net.core.rmem_default 的设置.
随后 rcvBuf 根据实际情况在最大值和最小值之间动态调节. 在缓冲的动态调优机制开启的情况下,
我们将 net.ipv4.tcp_rmem 的最大值设置为BDP.

当 net.ipv4.tcp_moderate_rcvbuf = 0 时, 或者设置了 socket 选项 SO_RCVBUF, 缓冲的
动态调节机制被关闭. rcvBuf 的缺省值由 net.core.rmem_default 设置, 但如果设置了
net.ipv4.tcp_rmem, 缺省值则被覆盖. 可以通过系统调用 setsockopt() 设置 rcvBuf
(man -S7 socket) 的最大值为 net.core.rmem_max. 在缓冲动态调节机制关闭的情况下,
建议把缓冲的缺省值设置为 BDP.

注意这里还有一个细节，缓冲除了保存接收的数据本身，还需要一部分空间保存 socket 数据结构等额外信息.
因此上面讨论的 recvBuffer 最佳值仅仅等于 BDP 是不够的, 还需要考虑保存 socket 等额外信息的开销.
Linux 根据参数 net.ipv4.tcp_adv_win_scale 计算额外开销的大小:

注意这里还有一个细节, 缓冲除了保存接收的数据本身, 还需要一部分空间保存 socket 数据结构
等额外信息. 因此上面讨论的 rcvbuf 最佳值仅仅等于 BDP 是不够的, 还需要考虑保存 socket
等额外信息的开销. Linux 根据参数 net.ipv4.tcp_adv_win_scale 计算额外开销的大小：

    Buffer / 2^(tcp_adv_win_scale)

如果 net.ipv4.tcp_adv_win_scale 的值为 1, 则二分之一的缓冲空间用来做额外开销, 如果为 2
的话, 则四分之一缓冲空间用来做额外开销. 因此 rcvBuf 的最佳值应该设置为:

  rcvBuf = BDP / (1 - 2^tcp_adv_win_scale)

SO_RCVBUF 是具体连接的值, 受限于 net.core.rmem_max, 最小为 256.

注:

recvBuf 不仅包括 payload, 还包括一些元数据(多达 240 byte), recvBuf 过大, 合并 tcp 包到
一个大的 skb_buff, 合并需要时间, 尤其是在高负载下, 因此显著增加延迟



net.ipv4.tcp_rmem = 4096 5242880 33554432

net.ipv4.tcp_rmem = 4096 1048576 2097152


###tcp_mem: min default max

* 默认值 根据内存计算
* 建议值 786432 1048576 1572864

low: 当 TCP 使用了低于该值的内存页面数时, TCP 不会考虑释放内存. 即低于此值没有内存压力.
(理想情况下, 这个值应与指定给 tcp_wmem 的第 2 个值相匹配 - 这第 2 个值表明, 最大页面大
 小乘以最大并发请求数除以页大小 (131072 300 / 4096). )

pressure: 当TCP使用了超过该值的内存页面数量时, TCP试图稳定其内存使用, 进入pressure模式,
当内存消耗低于 low 值时则退出pressure状态. (理想情况下这个值应该是 TCP 可以使用的总缓冲
区大小的最大值 (204800 300 / 4096).  )

high: 允许所有tcp sockets用于排队缓冲数据报的页面量. (如果超过这个值, TCP 连接将被拒绝,
这就是为什么不要令其过于保守 (512000 * 300 / 4096) 的原因了.  在这种情况下, 提供的价值很
大, 它能处理很多连接, 是所预期的 2.5 倍; 或者使现有连接能够传输 2.5 倍的数据.  我的网络
里为192000 300000 732000)

一般情况下这些值是在系统启动时根据系统内存数量计算得到的.

    net.ipv4.tcp_mem = 262144  524288  1048576
                        1G      2G       4G

###tcp_app_win

* 默认值 31
* 建议值 31

保留 max(window/2^tcp_app_win, mss) 数量的窗口由于应用缓冲. 当为0时表示不需要缓冲

###tcp_adv_win_scale

* 默认值 2
* 建议值 2

计算缓冲开销 bytes/2^tcp_adv_win_scale(如果tcp_adv_win_scale > 0) 或者 
bytes-bytes/2^(-tcp_adv_win_scale)(如果tcp_adv_win_scale BOOLEAN>0)

###tcp_low_latency

* 默认值 0
* 建议值 0

允许 TCP/IP 栈适应在高吞吐量情况下低延时的情况; 这个选项一般情形是的禁用. (但在构建
Beowulf 集群的时候,打开它很有帮助)

###tcp_westwood

* 默认值 0
* 建议值 0

启用发送者端的拥塞控制算法, 它可以维护对吞吐量的评估, 并试图对带宽的整体利用情况进行
优化; 对于 WAN 通信来说应该启用这个选项. 

###tcp_bic

* 默认值 0
* 建议值 0

为快速长距离网络启用 Binary Increase Congestion; 这样可以更好地利用以 GB
速度进行操作的链接; 对于 WAN 通信应该启用这个选项

###ip_forward

* 默认值 0
* 建议值 1

NAT必须开启IP转发支持, 把该值写1

###ip_local_port_range:minmax

* 默认值 32768 61000
* 建议值 1024 65000

表示用于向外连接的端口范围, 默认比较小, 这个范围同样会间接用于NAT表规模. 

###ip_conntrack_max

* 默认值 65535
* 建议值 65535

系统支持的最大 ipv4 连接数, 默认65536（事实上这也是理论最大值）, 同时这个值和你的内存大小有关, 
如果内存 128M, 这个值最大 8192, 1G 以上内存这个值都是默认65536


##所处目录/proc/sys/net/ipv4/netfilter/

文件需要打开防火墙才会存在

###ip_conntrack_max

* 默认值 65535
* 建议值 65535

系统支持的最大ipv4连接数, 默认65536（事实上这也是理论最大值）, 同时这个值和你的内存大小有关, 
如果内存128M, 这个值最大8192, 1G以上内存这个值都是默认65536,这个值受/proc/sys/net/ipv4/ip_conntrack_max
限制

###ip_conntrack_tcp_timeout_established

* 默认值 432000
* 建议值 180

已建立的 tcp 连接的超时时间, 默认 432000, 也就是 5 天. 影响: 这个值过大将导致一些可能已经不用
的连接常驻于内存中, 占用大量链接资源, 从而可能导致 NAT ip_conntrack: table full 的问题. 建议: 
对于 NAT 负载相对本机的 NAT 表大小很紧张的时候, 可能需要考虑缩小这个值, 以尽早清除连接, 保证有
可用的连接资源; 如果不紧张, 不必修改

###ip_conntrack_tcp_timeout_time_wait

* 默认值 120
* 建议值 120

time_wait 状态超时时间, 超过该时间就清除该连接

###ip_conntrack_tcp_timeout_close_wait

* 默认值
* 建议值

close_wait 状态超时时间, 超过该时间就清除该连接

###ip_conntrack_tcp_timeout_fin_wait

* 默认值 120
* 建议值 120

fin_wait状态超时时间, 超过该时间就清除该连接


##/proc/sys/net/core/

###netdev_max_backlog

* 默认值 1024
* 建议值 16384

每个网络接口接收数据包的速率比内核处理这些包的速率快时,数据包将会缓冲在TCP层之前的队列中,
该参数表示允许送到队列的数据包的最大数目, 对重负载服务器而言, 该值需要调高一点.

###somaxconn

* 默认值 128
* 建议值 16384

保存 ESTABLISHED 状态的连接. 队列长度为 min(net.core.somaxconn, backlog), 超过这个数量就
会导致链接超时或者触发重传机制. 其中 backlog

    int listen(int sockfd, int backlog);

如果我们设置的 backlog 大于 net.core.somaxconn, accept 队列的长度, 将被设置为
net.core.somaxconn

###wmem_default

* 默认值 129024
* 建议值 129024

默认的发送窗口大小（以字节为单位）

###rmem_default

* 默认值 129024
* 建议值 129024

默认的接收窗口大小（以字节为单位）

###rmem_max

* 默认值 129024
* 建议值 873200

最大的TCP数据接收缓冲

###wmem_max

* 默认值 129024
* 建议值 873200

最大的TCP数据发送缓冲

###tcp_collapse


两种修改内核参数方法

* 1.使用echo value方式直接追加到文件里如echo "1" >/proc/sys/net/ipv4/tcp_syn_retries, 但这种方法设备重启后又会恢复为默认值
* 2.把参数添加到/etc/sysctl.conf中, 然后执行sysctl -p使参数生效, 永久生效

##补充

###interrupt coalescence settings

The interrupt coalescence (IC) feature available for the Intel PRO/1000 XT NIC,
(as well as many other NIC's) can be set for receive (RxInt) and transmit (TxInt)
interrupts. These values can be set to delay interrupts in units of 1.024 us. For
the current latest driver, 5.2.20, the default value is 0 which means the host CPU
is interrupted for each packet received. Interrupt reduction can improve CPU efficiency
if properly tuned for specific network traffic. As Ethernet frames arrive, the NIC
places them in memory but the NIC will wait the RxInt time before generating an interrupt
to indicate that one or more frames have been received. Thus increasing IC reduces the
number of context switches made by the kernel to service the interrupts, but adds extra
latency to frame reception.

When increasing the IC there should be a sufficient numbers of descriptors in the ring-buffers
associated with the interface to hold the number of packets expected between consecutive interrupts.

As expected when increasing the IC settings the value of the latency increases,
so that the difference in latency reflects the increased length of time packets
spend in the NICs memory before being processed by the kernel.

If TxInt is reduced to 0 the throughput is significantly affected for all values of
RxInt due to increased PCI activity and insufficient power to cope with the context
switching in the sending PC.

If CPU power is important for your system (for example a shared server machine) than
it is recommended to use a high interrupt coalescence in order to moderate CPU usage.
If the machine is going to be dedicated to a single transfer than interrupt coalescence
should be off.

###NAPI

Since 2.4.20 version of the Linux kernel, the network subsystem has changed
and is now called NAPI (for New API) [1]. This new API allows to handle
received packets no more per packet but per device.

Although NAPI is compatible with the old system and so with the old driver,
you need to use a NAPI-aware driver to enable this improvement in your machine.
It exists e.g. for Syskonnect Gigabit card [LINK TO BE PROVIDED BY MATHIEU].

The NAPI network subsystem is a lot more efficient than the old system,
especially in a high performance context. The pros are:

* limitation of interruption rate (you can see it like an adaptative interruption coalescing mechanism) ;
* not prone to receive livelock [3];
* better data & instruction locality.

One problem is that there is no parallelism in SMP machine for traffic coming in from a single interface, because a device is always handled by a CPU.

####iftxtqueue length high

There are settings available to regulate the size of the queue between
the kernel network subsystems and the driver for network interface card.
Just as with any queue, it is recommended to size it such that losses do
no occur due to local buffer overflows. Therefore careful tuning is required
to ensure that the sizes of the queues are optimal for your network connection.

These settings are especially important for TCP as losses on local queues will
cause TCP to fall into congestion control – which will limit the TCP sending
rates. Meanwhile, full queues will cause packet losses when transporting udp
packets.

There are two queues to consider, the txqueuelen; which is related to the transmit
queue size, and the netdev_backlog; which determines the recv queue size.

To set the length of the transmit queue of the device. It is useful to set this to
small values for slower devices with a high latency (modem links, ISDN) to prevent
fast bulk transfers from disturbing interactive traffic like telnet too much.

Users can manually set this queue size using the ifconfig command on the required
device. Eg.

    /sbin/ifconfig eth2 txqueuelen 2000

The default of 100 is inadequate for long distance, high throughput pipes. For example,
on a network with a rtt of 120ms and at Gig rates, a txqueuelen of at least 10000 is
recommended.

###TCP cache parameter (Yee)

Linux 2.4.x tcp has a function to cache tcp network transfer statistics.
The idea behind this was to improve the performance of tcp on links such
that it does not have to discover the optimal congestion avoidance settings
(ssthresh) of every connection. However, in high speed networks, or during
low network congestion periods, a new tcp connection will use the cached
values and can perform worse as a result.

In order to rectify this, one can flush all the tcp cache settings using the command:

/sbin/sysctl –w sys.net.ipv4.route.flush=1

Note that this flushes all routes, and is only temporary – ie, one must
run this command every time the cache is to be emptied.

###SACKs and Nagle

SACKs (Selective Acknowledgments) are an optimisation to TCP which in normal
scenarios improves considerably performance. In Gigabit networks with no traffic
competition these have the opposite effect. To improve performance they should be
turned off by:

/sbin/sysctl -w net.ipv4.tcp_sack=0

Nagle algorithm should however be turned on. This is the default value. You can check
if your program has Nagle switched off of it sets the TCP_NODELAY socket option. If
this is the case comment this.

###Using large block sizes

Using large data block sizes improves performance. Applications use frequently 8Kb blocks.
A value of 64Kb is a better choice.

###Parallel streams

If possible, the application can always use several TCP streams to transfer the data.
These should involve to create and open more than one socket and parallelise the data
transfer among these sockets. iperf can also be configured to achieve this with the -P option:

###New TCP stack

Current TCP has been shown not to scale to high bandwidth delay product networks. Several
proposals already emerged to overcome this limitation. The main ones are High Speed TCP [5],
Scalable TCP [6] and FAST [7]. Installing the appropriate stacks in your Linux kernel can,
therefore, improve considerably your performance. Implementations of HS-TCP and Scalable TCP
can be found at the DataTAG site (http://www.datatag.org)


###Harware
The first thing to make sure for a good data transfer is appropriate hardware. Here are some
guidelines for hardware configurations for 1 and 10 Gbits/s.

1. 1 Gbit/s network cards

PCI 64-66MHz bus recommended (4Gbit/s theoretical bus limit)

Pay attention to the shared buses on the motherboard (for ex. the SuperMicro motherboard
for Intel Xeon Processors splits the PCI bus in 3 segments: PCI slots 1-3, PCI slot 4 and
the on-board SCSI controller if one exists and PCI slots 5-6.

2. Intel 10Gbit/s network cards.

a)PCI-X 133 MHz bus recommended (8.5 Gbit/s theoretical limit)
b)Processor (and motherboard) with 533 MHz front-side bus
c)PCI slot configured as bus master (improved stability)
d)The Intel 10 Gbit/s card should be alone on its bus segment for optimal performance.
e)The PCI burst size should be increased to 512K
f)The card driver should be configured with the following parameters:
    i. Interrupt coalescence
    ii. Jumbo frames
    iii. Gigabit Ethernet flow control (it should be active also on the connecting switch)
    iv. Increased network card packet buffers (default 1024, maximum 4096)
    v. RX and TX checksum offload enabled 

Jumbo frames should be used if possible

Increase Routers queue sizes. In Cisco equipment for example, the maximum, 4096, should me used.

Gigabit Ethernet Flow Control should be ON

Avoid Fragmentation.

Watch out for IPv6 MTU advertisements. Some routers have IPv6 router advertisement on by default.
This usually advertises a small value (typically 1500). End systems should turn off listening to
these advertisements. This is easily configured in the /proc file system

##例子

生产中常用的参数: 

    net.ipv4.tcp_syn_retries = 1
    net.ipv4.tcp_synack_retries = 1
    net.ipv4.tcp_keepalive_time = 600
    net.ipv4.tcp_keepalive_probes = 3
    net.ipv4.tcp_keepalive_intvl =15
    net.ipv4.tcp_retries2 = 5
    net.ipv4.tcp_fin_timeout = 2
    net.ipv4.tcp_max_tw_buckets = 36000
    net.ipv4.tcp_tw_recycle = 1
    net.ipv4.tcp_tw_reuse = 1
    net.ipv4.tcp_max_orphans = 32768
    net.ipv4.tcp_syncookies = 1
    net.ipv4.tcp_max_syn_backlog = 16384
    net.ipv4.tcp_wmem = 8192 131072 16777216
    net.ipv4.tcp_rmem = 32768 131072 16777216
    net.ipv4.tcp_mem = 786432 1048576 1572864
    net.ipv4.ip_local_port_range = 1024 65000
    net.ipv4.ip_conntrack_max = 65536
    net.ipv4.netfilter.ip_conntrack_max=65536
    net.ipv4.netfilter.ip_conntrack_tcp_timeout_established=180
    net.core.somaxconn = 16384
    net.core.netdev_max_backlog = 16384


    net.core.optmem_max = 10000000
    #该参数指定了每个套接字所允许的最大缓冲区的大小
    net.ipv4.conf.all.rp_filter = 1
    net.ipv4.conf.default.rp_filter = 1
    #严谨模式 1 (推荐)
    #松散模式 0

    net.ipv4.tcp_congestion_control = bic
    #默认推荐设置是 htcp
    net.ipv4.tcp_keepalive_intvl = 15
    #keepalive探测包的发送间隔
    net.ipv4.tcp_slow_start_after_idle = 0
    #关闭tcp的连接传输的慢启动, 即先休止一段时间, 再初始化拥塞窗口. 
    net.ipv4.route.gc_timeout = 100
    #路由缓存刷新频率, 当一个路由失败后多长时间跳到另一个路由, 默认是300. 
    net.ipv4.tcp_syn_retries = 1
    #在内核放弃建立连接之前发送SYN包的数量. 
    net.ipv4.icmp_echo_ignore_broadcasts = 1
    # 避免放大攻击
    net.ipv4.icmp_ignore_bogus_error_responses = 1
    # 开启恶意icmp错误消息保护
    net.inet.udp.checksum=1
    #防止不正确的udp包的攻击
    net.ipv4.conf.default.accept_source_route = 0
    #是否接受含有源路由信息的ip包. 参数值为布尔值, 1表示接受, 0表示不接受. 
    #在充当网关的linux主机上缺省值为1, 在一般的linux主机上缺省值为0. 
    #从安全性角度出发, 建议你关闭该功能. 

在高并发下修改如下参数:

    net.core.somaxconn    8192
    net.ipv4.tcp_max_syn_backlog 1024
    listen系统调用的backlog参数  8192


##附录

##硬件调优

###NUMA

** NUMA locality**

    cat /sys/class/net/$DEV/device/numa_node for PCIe device locality
    -1 means no locality, depends on hardware platform

###丢包统计

    ethtool --statistics NETNAME(eth0)

    xsos --net has a handy grep for common driver discards

    Packet loss after the OS hands to the NIC
    ethtool -S ethX and xsos --net again

    Packet loss before the OS hands to the NIC
    tc -s qdisc to view qdisc dropped

原因

    Poor Interrupt Handling
    Ring Buffer Overflows(Transmit ring buffer in hardware too small)
    Lack of Offloading
    Kernel not picking traffic fast enough
    Ethernet Flow Control (aka Pause Frames)

    Insufficient length of queue
    If you must drop, you can decide what to drop

###网卡中断

/proc/interrupts

###中断平衡

* irqbalance 1.0.8 or later
* 手动平衡中断 /proc/irq/$IRQ/smp_affinity

RSS: Receive Side Scaling (hardware-controlled balancing)
RPS: Receive Packet Steering (software-controlled balancing)
RFS: Receive Flow Scaling (application-aware software balancing)
XPS: Transmit Packet Steering (software selection of transmit queue)

###中断队列

建议: 每个 NUMA 节点对应一个网卡, 每个网卡的多个队列分别对应同一 NUMA 节点的不同的 CPU

一个网卡的多个队列分配到多个 NUMA 节点的不同 CPU 是不建议的

一个网卡的一个队列绑定到一个 CPU. 一个网卡的多个队列绑定到一个 CPU 是不建议的.

ethtool --set-channels $DEV [channel type] N

ethtool --coalesce $DEV rx-usecs N rx-frames N

ip addr show eth0
ip link set $DEV txqueuelen N (default 500 to 1000)


中断和延迟是一个负相关的.

Amount of packets to buffer before sending to the NIC
Can be enlarged a little for bulk transfer
can also be reduced for super-low latency, less than 10ms
Virtual devices (bond, VLAN, tun) don't have a queue, you can add one

Queuing Disciplines allows prioritization and bandwidth restriction
http://lartc.org/howto/lartc.qdisc.html

###Ring Buffer

ethtool --show-ring eth0
ethtool --set-ring $DEV rx N tx N

设置尽量大, 但不要超过 4096

###Offload

ethtool --show-features eth0
ethtool --offload $DEV $FEATURE on

对应转发类的应用(路由器, 交换机), recv offload 是不建议的(如 LRO).

###Kernel 取包速度

cat /proc/net/softnet_stat

0004b220 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
00006085 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
0000620d 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000
000058fa 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000 00000000

第一列: 总共接受的包
第二列: backlog overruns
第三列: SoftIRQ ended with traffic left in the NIC

net.core.netdev_budget = 300 kernel tunable can be slightly increased

Probably dont set budget into the thousands, SoftIRQ can hog the CPU

###协议层

netstat -s

* collapsed - under socket buffer memory pressure, but no loss yet
* pruned - incoming data was lost due to lack of socket buffer memory
* Many of these stats are symptoms of packet loss, not causes: retransmit, slow start, congestion, SACK

###Socket Buffer

/etc/sysctl.conf

net.ipv4.tcp_rmem = 4096 262144 16777216
net.ipv4.tcp_wmem = 4096 262144 16777216

net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.core.rmem_default = 262144
net.core.wmem_default = 262144

通过 sysdig, strace 跟踪配置

注:
1. 如果应用程序设置了, 则自动 tunning 被关闭
2. 每个参数的值都应用于每个 socket, 值越大, 消耗的内存越大

###Tcp Timestamps

Precise calculation of when traffic was transmitted and received

    Allows for better auto-tuning of buffers and accurate TCP Windowing


Provides Protection Against Wrapped Sequence Numbers (PAWS)

    Sequence Numbers are 32-bit, and wrap in 1.8s at 10Gbps
    A TCP stream can hang on wrap!

Definitely on: net.ipv4.tcp_timestamps = 1

not compatible with NAT, as multiple hosts have different uptimes

###SACK

SACK 增加的系统负载, 但因系统而异, 自己测试

net.ipv4.tcp_sack = 1

###Tcp Backlog

net.core.somaxconn = N

    Not accepting new connections fast enough
    Also just too many valid incoming connections
    netstat -s for LISTEN backlog
    syslog for SYN cookies

###没有很好接受数据

netstat -s for collapsed, pruned

ss for sockets with data in Recv-Q for a long time

###NUMA 亲合性

借助 numactl mumad 工具

尽量将应用程序与网卡中断在同一NUMA 节点
尽量将应用程序与网卡中断在同一 CPU

###Ethernet Flow Control

Lets the NIC tell the switch to buffer traffic

Lets the switch tell the NIC to buffer traffic

Pause Frames are generated when a watermark in the ring buffer is hit
A bit of a tradeoff, as it's per-port not per-queue, so one full recv
queue generates a pause frame which stops all traffic

Try with this on first, test with it off

ethtool --pause $DEV autoneg on rx on tx on

###queueing discipline

The order and amount of packets able to be submitted for transmit is controlled by the interface's queueing discipline

###SoftIRQ

SoftIRQ uses device-specific code to send queued traffic to the hardware Ring Buffer

256 KiB x 100,000 sockets = 24 GiB

SO_REUSEPORT in kernel v3.9 or later can provide in-kernel listen balancing to multiple tasks: https://lwn.net/Articles/542629/

Multiple multicast tasks reading the same socket leads to packet duplication, probably won't scale past four tasks

If possible, design so there is one RX handler, use IPC to distribute data

##参考

Documentation/networking/ip-sysctl.txt
http://sandilands.info/sgordon/impact-of-bandwidth-delay-product-on-tcp-throughput
http://jbainbri.github.io/lca2016.html
https://www.kernel.org/doc/Documentation/networking/scaling.txt
https://www.kernel.org/doc/Documentation/networking/ip-sysctl.txt
http://lartc.org/howto/lartc.qdisc.html
http://www.kegel.com/c10k.html
http://bagder.github.io/I-D/httpbis-tcp/
