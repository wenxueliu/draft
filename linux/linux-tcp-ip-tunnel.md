
两种修改内核参数方法

    使用echo value方式直接追加到文件里如echo "1" >/proc/sys/net/ipv4/tcp_syn_retries，但这种方法设备重启后又会恢复为默认值

    把参数添加到/etc/sysctl.conf中，然后执行sysctl -p使参数生效，永久生效

##/proc/sys/net/ipv4/

###tcpsyn_retries

* 默认值 5
* 建议值 1

对于一个新建连接，内核要发送多少个 SYN 连接请求才决定放弃。不应该大于255，默认值是5，
对应于 180 秒左右时间。。(对于大负载而物理通信良好的网络而言,这个值偏高,可修改为2.
这个值仅仅是针对对外的连接,对进来的连接,是由 tcp_retries1 决定的)

###tcp_synack_retries

* 默认值 5
* 建议值 1

对于远端的连接请求 SYN，内核会发送 SYN ＋ ACK 数据报，以确认收到上一个 SYN 连接请求包。
这是所谓的三次握手( threeway handshake)机制的第二个步骤。这里决定内核在放弃连接之前所
送出的 SYN+ACK 数目。不应该大于255，默认值是 5，对应于 180 秒左右时间。

###tcp_keepalive_time 有误??

* 默认值 7200
* 建议值 600

TCP 发送 keepalive 探测消息的间隔时间（秒），用于确认 TCP 连接是否有效。
防止两边建立连接但不发送数据的攻击

###tcp_keepalive_probes

* 默认值 9
* 建议值 3

如果对方不予应答，TCP发送 keepalive 探测消息的次数，用于确认 TCP 连接是否有效。

###tcp_retries1

* 默认值 3
* 建议值 3

放弃回应一个 TCP 连接请求前﹐需要进行多少次重试。RFC 规定最低的数值是 3

###tcp_retries2

* 默认值 15
* 建议值 5

在丢弃激活(已建立通讯状况)的 TCP 连接之前﹐需要进行多少次重试。默认值为 15，根据 RTO 的值来决定，
相当于 13-30 分钟(RFC1122规定，必须大于100秒).(这个值根据目前的网络设置,可以适当地改小,我的网络
内修改为了 5)

###tcp_orphan_retries

* 默认值 7
* 建议值 3

在近端丢弃TCP连接之前﹐要进行多少次重试。默认值是 7 个﹐相当于 50秒 - 16分钟﹐视 RTO 而定。
如果您的系统是负载很大的 web 服务器﹐那么也许需要降低该值﹐这类 sockets 可能会耗费大量的资源。
另外参的考 tcp_max_orphans。(事实上做NAT的时候,降低该值也是好处显著的,我本人的网络环境中降低该值为3)

###tcp_fin_timeout

* 默认值 60
* 建议值 2

对于本端断开的 socket 连接，TCP 保持在 FIN-WAIT-2 状态的时间。对方可能会断开连接或一直不结束连接或
不可预料的进程死亡。默认值为 60 秒。

###tcp_max_tw_buckets

* 默认值 180000
* 建议值 36000

系统在同时所处理的最大 timewait sockets 数目。如果超过此数的话﹐time-wait socket 会被立即砍除
并且显示警告信息。之所以要设定这个限制﹐纯粹为了抵御那些简单的 DoS 攻击﹐不过﹐如果网络条件需
要比默认值更多﹐则可以提高它(或许还要增加内存)。(事实上做 NAT 的时候最好可以适当地增加该值)

###tcp_tw_recycle

* 默认值 0
* 建议值 1

打开快速 TIME-WAIT sockets 回收。除非得到技术专家的建议或要求﹐请不要随意修改这个值。
(做NAT的时候，建议打开它)

###tcp_tw_reuse

* 默认值 0
* 建议值 1

表示是否允许重新应用处于TIME-WAIT状态的socket用于新的TCP连接(这个对快速重启动某些服务,而启动
后提示端口已经被使用的情形非常有帮助)

###tcp_max_orphans

* 默认值 8192
* 建议值 32768

系统所能处理不属于任何进程的 TCP sockets 最大数量。假如超过这个数量﹐那么不属于任何进程的连接
会被立即 reset，并同时显示警告信息。之所以要设定这个限制﹐纯粹为了抵御那些简单的
DoS 攻击﹐千万不要依赖这个或是人为的降低这个限制。如果内存大更应该增加这个值。(这个值Redhat
AS版本中设置为 32768,但是很多防火墙修改的时候,建议该值修改为 2000)

###tcp_abort_on_overflow

* 默认值 0
* 建议值 0

当守护进程太忙而不能接受新的连接，就象对方发送 reset 消息，默认值是 false。这意味着当溢出的原
因是因为一个偶然的猝发，那么连接将恢复状态。只有在你确信守护进程真的不能完成连接请求时才打开该
选项，该选项会影响客户的使用。(对待已经满载的 sendmail,apache 这类服务的时候,这个可以很快让客
户端终止连接,可以给予服务程序处理已有连接的缓冲机会,所以很多防火墙上推荐打开它)

###tcp_syncookies

* 默认值 0
* 建议值 1

只有在内核编译时选择了 CONFIG_SYNCOOKIES 时才会发生作用。当出现 syn 等候队列出现溢出时象对方发送
syncookies。目的是为了防止 syn flood攻击。

###tcp_stdurg

* 默认值 0
* 建议值 0

使用 TCP urg pointer 字段中的主机请求解释功能。大部份的主机都使用老旧的 BSD 解释，因此如果您在 
Linux 打开它﹐或会导致不能和它们正确沟通

###tcp_max_syn_backlog

* 默认值 1024
* 建议值 16384

对于那些依然还未获得客户端确认的连接请求﹐需要保存在队列中最大数目。对于超过 128Mb 内存的系统﹐
默认值是 1024 ﹐低于 128Mb 的则为 128。如果服务器经常出现过载﹐可以尝试增加这个数字。警告﹗
假如您将此值设为大于 1024﹐最好修改 include/net/tcp.h 里面的TCP_SYNQ_HSIZE﹐以保持 
TCP_SYNQ_HSIZE*16(SYN Flood 攻击利用 TCP 协议散布握手的缺陷，伪造虚假源 IP 地址发送大量 TCP-SYN
半打开连接到目标系统，最终导致目标系统 Socket 队列资源耗尽而无法接受新的连接。为了应付这种攻击，
现代Unix系统中普遍采用多连接队列处理的方式来缓冲(而不是解决)这种攻击，是用一个基本队列处理正常的
完全连接应用(Connect() 和 Accept())，是用另一个队列单独存放半打开连接。这种双队列处理方式和其他
一些系统内核措施(例如Syn-Cookies/Caches)联合应用时，能够比较有效的缓解小规模的SYN Flood攻击(事实证明))

###tcp_window_scaling

* 默认值 1
* 建议值 1

该文件表示设置 tcp/ip 会话的滑动窗口大小是否可变。参数值为布尔值，为 1 时表示可变，为 0 时表示不可变。
tcp/ip通常使用的窗口最大可达到 65535 字节，对于高速网络，该值可能太小，这时候如果启用了该功能，可以
使 tcp/ip 滑动窗口大小增大数个数量级，从而提高数据传输的能力(RFC 1323)。（对普通地百M网络而言，关闭
会降低开销，所以如果不是高速网络，可以考虑设置为 0）

###tcp_timestamps

* 默认值 1
* 建议值 1

Timestamps 用在其它一些东西中﹐可以防范那些伪造的 sequence 号码。一条 1G 的宽带线路或许会重遇到带
out-of-line 数值的旧 sequence 号码(假如它是由于上次产生的)。Timestamp 会让它知道这是个 '旧封包'。
(该文件表示是否启用以一种比超时重发更精确的方法（RFC 1323）来启用对 RTT 的计算；为了实现更好的性能
 应该启用这个选项。)

###tcp_sack

* 默认值 1
* 建议值 1

使用 Selective ACK﹐它可以用来查找特定的遗失的数据报 --- 因此有助于快速恢复状态。该文件表示是否启用
有选择的应答（Selective Acknowledgment），这可以通过有选择地应答乱序接收到的报文来提高性能（这样可以
让发送者只发送丢失的报文段）。(对于广域网通信来说这个选项应该启用，但是这会增加对 CPU 的占用。)

###tcp_fack

* 默认值 1
* 建议值 1

打开 FACK 拥塞避免和快速重传功能。(注意，当 tcp_sack 设置为 0 的时候，这个值即使设置为1也无效)[这个是
TCP 连接靠谱的核心功能]

###tcp_dsack

* 默认值 1
* 建议值 1

允许TCP发送"两个完全相同"的SACK。

###tcp_ecn

* 默认值 0
* 建议值 0

TCP的直接拥塞通告功能

###tcp_reordering

* 默认值 3
* 建议值 6

TCP流中重排序的数据报最大数量。 (一般有看到推荐把这个数值略微调整大一些,比如5)

###tcp_retrans_collapse

* 默认值 0
* 建议值 1

对于某些有bug的打印机提供针对其bug的兼容性。(一般不需要这个支持,可以关闭它)

###tcp_wmem：mindefaultmax

* 默认值 4096 16384 131072
* 建议值 8192 131072 16777216

发送缓存设置

min：为 TCP socket 预留用于发送缓冲的内存最小值。每个 tcp socket 都可以在建议
以后都可以使用它。默认值为4096(4K)。

default：为 TCP socket 预留用于发送缓冲的内存数量，默认情况下该值会影响其它协议
使用的 net.core.wmem_default 值，一般要低于 net.core.wmem_default 的值。默认值为
16384(16K)。

max: 用于 TCP socket 发送缓冲的内存最大值。该值不会影响 net.core.wmem_max，"静态"
选择参数SO_SNDBUF则不受该值影响。默认值为 131072(128K)。（对于服务器而言，增加这
个参数的值对于发送数据很有帮助,在我的网络环境中,修改为了51200 131072 204800）

###tcprmem：mindefaultmax

* 默认值 4096 87380 174760
* 建议值 32768 131072 16777216

接收缓存设置 同tcp_wmem

###tcp_mem：mindefaultmax

* 默认值 根据内存计算
* 建议值 786432 1048576 1572864

low：当 TCP 使用了低于该值的内存页面数时，TCP 不会考虑释放内存。即低于此值没有内存压力。
(理想情况下，这个值应与指定给 tcp_wmem 的第 2 个值相匹配 - 这第 2 个值表明，最大页面大
 小乘以最大并发请求数除以页大小 (131072 300 / 4096)。)

pressure：当TCP使用了超过该值的内存页面数量时，TCP试图稳定其内存使用，进入pressure模式，
当内存消耗低于 low 值时则退出pressure状态。(理想情况下这个值应该是 TCP 可以使用的总缓冲
区大小的最大值 (204800 300 / 4096)。 )

high：允许所有tcp sockets用于排队缓冲数据报的页面量。(如果超过这个值，TCP 连接将被拒绝，
这就是为什么不要令其过于保守 (512000 * 300 / 4096) 的原因了。 在这种情况下，提供的价值很
大，它能处理很多连接，是所预期的 2.5 倍；或者使现有连接能够传输 2.5 倍的数据。 我的网络
里为192000 300000 732000)

一般情况下这些值是在系统启动时根据系统内存数量计算得到的。

###tcp_app_win

* 默认值 31
* 建议值 31

保留 max(window/2^tcp_app_win, mss) 数量的窗口由于应用缓冲。当为0时表示不需要缓冲

###tcp_adv_win_scale

* 默认值 2
* 建议值 2

计算缓冲开销 bytes/2^tcp_adv_win_scale(如果tcp_adv_win_scale > 0) 或者 
bytes-bytes/2^(-tcp_adv_win_scale)(如果tcp_adv_win_scale BOOLEAN>0)

###tcp_low_latency

* 默认值 0
* 建议值 0

允许 TCP/IP 栈适应在高吞吐量情况下低延时的情况；这个选项一般情形是的禁用。(但在构建
Beowulf 集群的时候,打开它很有帮助)

###tcp_westwood

* 默认值 0
* 建议值 0

启用发送者端的拥塞控制算法，它可以维护对吞吐量的评估，并试图对带宽的整体利用情况进行
优化；对于 WAN 通信来说应该启用这个选项。

###tcp_bic

* 默认值 0
* 建议值 0

为快速长距离网络启用 Binary Increase Congestion；这样可以更好地利用以 GB
速度进行操作的链接；对于 WAN 通信应该启用这个选项

###ip_forward

* 默认值 0
* 建议值 1

NAT必须开启IP转发支持，把该值写1

###ip_local_port_range:minmax

* 默认值 32768 61000
* 建议值 1024 65000

表示用于向外连接的端口范围，默认比较小，这个范围同样会间接用于NAT表规模。

###ip_conntrack_max

* 默认值 65535
* 建议值 65535

系统支持的最大 ipv4 连接数，默认65536（事实上这也是理论最大值），同时这个值和你的内存大小有关，
如果内存 128M，这个值最大 8192，1G 以上内存这个值都是默认65536


##所处目录/proc/sys/net/ipv4/netfilter/

文件需要打开防火墙才会存在

###ip_conntrack_max

* 默认值 65535
* 建议值 65535

系统支持的最大ipv4连接数，默认65536（事实上这也是理论最大值），同时这个值和你的内存大小有关，
如果内存128M，这个值最大8192，1G以上内存这个值都是默认65536,这个值受/proc/sys/net/ipv4/ip_conntrack_max
限制

###ip_conntrack_tcp_timeout_established

* 默认值 432000
* 建议值 180

已建立的 tcp 连接的超时时间，默认 432000，也就是 5 天。影响：这个值过大将导致一些可能已经不用
的连接常驻于内存中，占用大量链接资源，从而可能导致 NAT ip_conntrack: table full 的问题。建议：
对于 NAT 负载相对本机的 NAT 表大小很紧张的时候，可能需要考虑缩小这个值，以尽早清除连接，保证有
可用的连接资源；如果不紧张，不必修改

###ip_conntrack_tcp_timeout_time_wait

* 默认值 120
* 建议值 120

time_wait 状态超时时间，超过该时间就清除该连接

###ip_conntrack_tcp_timeout_close_wait

* 默认值
* 建议值

close_wait 状态超时时间，超过该时间就清除该连接

###ip_conntrack_tcp_timeout_fin_wait

* 默认值 120
* 建议值 120

fin_wait状态超时时间，超过该时间就清除该连接


##/proc/sys/net/core/

###netdev_max_backlog

* 默认值 1024
* 建议值 16384

每个网络接口接收数据包的速率比内核处理这些包的速率快时，允许送到队列的数据包的最大数目，
对重负载服务器而言，该值需要调高一点。

###somaxconn

* 默认值 128
* 建议值 16384

用来限制监听(LISTEN)队列最大数据包的数量，超过这个数量就会导致链接超时或者触发重传机制。

web 应用中 listen 函数的 backlog 默认会给我们内核参数的 net.core.somaxconn 限制到128，
而 nginx 定义的 NGX_LISTEN_BACKLOG 默认为 511，所以有必要调整这个值。对繁忙的服务器,增
加该值有助于网络性能

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


两种修改内核参数方法

* 1.使用echo value方式直接追加到文件里如echo "1" >/proc/sys/net/ipv4/tcp_syn_retries，但这种方法设备重启后又会恢复为默认值
* 2.把参数添加到/etc/sysctl.conf中，然后执行sysctl -p使参数生效，永久生效



##例子

生产中常用的参数：

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
    #关闭tcp的连接传输的慢启动，即先休止一段时间，再初始化拥塞窗口。
    net.ipv4.route.gc_timeout = 100
    #路由缓存刷新频率，当一个路由失败后多长时间跳到另一个路由，默认是300。
    net.ipv4.tcp_syn_retries = 1
    #在内核放弃建立连接之前发送SYN包的数量。
    net.ipv4.icmp_echo_ignore_broadcasts = 1
    # 避免放大攻击
    net.ipv4.icmp_ignore_bogus_error_responses = 1
    # 开启恶意icmp错误消息保护
    net.inet.udp.checksum=1
    #防止不正确的udp包的攻击
    net.ipv4.conf.default.accept_source_route = 0
    #是否接受含有源路由信息的ip包。参数值为布尔值，1表示接受，0表示不接受。
    #在充当网关的linux主机上缺省值为1，在一般的linux主机上缺省值为0。
    #从安全性角度出发，建议你关闭该功能。
