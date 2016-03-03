在构建或管理一个网络系统时, 我们更多的是关心网络的可用性, 即网络是否连通, 而对于其整体的性能往往考虑不多,
或者即使考虑到性能的问题, 但是却发现没有合适的手段去测试网络的性能.

当开发出一个网络应用程序后, 我们会发现, 在实际的网络环境使用中, 网络应用程序的使用效果不是很理想, 问题可能
出现在程序的开发上面, 也有可能由于实际的网络环境中存在着瓶颈. 面对这种问题, 程序员一般会一筹莫展, 原因就在
于不掌握一些网络性能测量的工具.

在本文中, 首先介绍网络性能测量的一些基本概念和方法, 然后结合 netperf 工具的使用, 具体的讨论如何测试不同情况
下的网络性能.

##网络性能测试概述

网络性能测量的五项指标

测量网络性能的五项指标是：

* 可用性(availability)
* 响应时间(response time)
* 网络利用率(network utilization)
* 网络吞吐量(network throughput)
* 网络带宽容量(network bandwidth capacity)

###可用性

测试网络性能的第一步是确定网络是否正常工作, 最简单的方法是使用 ping 命令. 通过向远端的机器发送 icmp echo request,
并等待接收 icmp echo reply 来判断远端的机器是否连通, 网络是否正常工作.

Ping 命令有非常丰富的命令选项, 比如 -c 可以指定发送 echo request 的个数, -s 可以指定每次发送的 ping 包大小.

网络设备内部一般有多个缓冲池, 不同的缓冲池使用不同的缓冲区大小, 分别用来处理不同大小的分组(packet). 例如交换机中
通常具有三种类型的包缓冲：一类针对小的分组, 一类针对中等大小的分组, 还有一类针对大的分组. 为了测试这样的网络设备,
测试工具必须要具有发送不同大小分组的能力. Ping 命令的 -s 就可以使用在这种场合.

###响应时间

Ping 命令的 echo request/reply 一次往返所花费时间就是响应时间. 有很多因素会影响到响应时间, 如网段的负荷, 网络主机的负荷,
广播风暴, 工作不正常的网络设备等等.

在网络工作正常时, 记录下正常的响应时间. 当用户抱怨网络的反应时间慢时, 就可以将现在的响应时间与正常的响应时间对比, 如果
两者差值的波动很大, 就能说明网络设备存在故障.

###网络利用率

网络利用率是指网络被使用的时间占总时间(即被使用的时间+空闲的时间)的比例. 比如, Ethernet 虽然是共享的, 但同时却只能有一个
报文在传输. 因此在任一时刻, Ethernet 或者是 100% 的利用率, 或者是 0% 的利用率.

计算一个网段的网络利用率相对比较容易, 但是确定一个网络的利用率就比较复杂. 因此, 网络测试工具一般使用网络吞吐量和网络带宽
容量来确定网络中两个节点之间的性能.

###网络吞吐量

网络吞吐量是指在某个时刻, 在网络中的两个节点之间, 提供给网络应用的剩余带宽.

网络吞吐量可以帮组寻找网络路径中的瓶颈. 比如, 即使 client 和 server 都被分别连接到各自的 1000M Ethernet 上, 但是如果这两个
1000M 的Ethernet 被 10M 的 Ethernet 连接起来, 那么 10M 的 Ethernet 就是网络的瓶颈.

网络吞吐量非常依赖于当前的网络负载情况. 因此, 为了得到正确的网络吞吐量, 最好在不同时间(一天中的不同时刻, 或者一周中不同的天)
分别进行测试, 只有这样才能得到对网络吞吐量的全面认识.

有些网络应用程序在开发过程的测试中能够正常运行, 但是到实际的网络环境中却无法正常工作(由于没有足够的网络吞吐量). 这是因为测试
只是在空闲的网络环境中, 没有考虑到实际的网络环境中还存在着其它的各种网络流量. 所以, 网络吞吐量定义为剩余带宽是有实际意义的.

###网络带宽容量

与网络吞吐量不同, 网络带宽容量指的是在网络的两个节点之间的最大可用带宽. 这是由组成网络的设备的能力所决定的.

测试网络带宽容量有两个困难之处: 在网络存在其它网络流量的时候, 如何得知网络的最大可用带宽；在测试过程中, 如何对现有的网络流量
不造成影响. 网络测试工具一般采用 packet pairs 和 packet trains 技术来克服这样的困难.

##收集网络性能数据的方式

当确定了网络性能的测试指标以后, 就需要使用网络测试工具收集相应的性能数据, 分别有三种从网络获取数据的方式：

1. 通过 snmp 协议直接到网络设备中获取, 如 net-snmp 工具
2. 侦听相关的网络性能数据, 典型的工具是 tcpdump
3. 自行产生相应的测试数据, 如本文中使用的 netperf 工具


##Netperf

Netperf 是一种网络性能的测量工具, 主要针对基于 TCP 或 UDP 的传输. Netperf 根据应用的不同, 可以进行不同模式的网络性能测试, 即
批量数据传输(bulk data transfer)模式和请求/应答(request/reponse)模式. Netperf测试结果所反映的是一个系统能够以多快的速度向另外
一个系统发送数据, 以及另外一个系统能够以多块的速度接收数据.

Netperf 工具以 client/server 方式工作. server 端是 netserver, 用来侦听来自 client 端的连接, client 端是 netperf, 用来向 server
发起网络测试. 在 client 与 server 之间, 首先建立一个控制连接, 传递有关测试配置的信息, 以及测试的结果; 在控制连接建立并传递了
测试配置信息以后, client 与 server 之间会再建立一个测试连接, 用来来回传递着特殊的流量模式, 以测试网络的性能.

###TCP 网络性能

由于 TCP 协议能够提供端到端的可靠传输, 因此被大量的网络应用程序使用. 但是, 可靠性的建立是要付出代价的. TCP 协议保证可靠性的措施,
如建立并维护连接、控制数据有序的传递等都会消耗一定的网络带宽.

Netperf 可以模拟三种不同的 TCP 流量模式:

1) 单个TCP连接, 批量(bulk)传输大量数据
2) 单个TCP连接, client请求/server应答的交易(transaction)方式
3) 多个TCP连接, 每个连接中一对请求/应答的交易方式

###UDP 网络性能

UDP 没有建立连接的负担, 但是 UDP 不能保证传输的可靠性, 所以使用 UDP 的应用程序需要自行跟踪每个发出的分组, 并重发丢失的分组.

Netperf 可以模拟两种 UDP 的流量模式:

1) 从client到server的单向批量传输
2) 请求/应答的交易方式

由于 UDP 传输的不可靠性, 在使用 netperf 时要确保发送的缓冲区大小不大于接收缓冲区大小, 否则数据会丢失, netperf 将给出错误的结果.
因此, 对于接收到分组的统计不一定准确, 需要结合发送分组的统计综合得出结论.

###Netperf的命令行参数

在 unix 系统中, 可以直接运行可执行程序来启动 netserver, 也可以让 inetd 或 xinetd 来自动启动 netserver.

当 netserver 在 server 端启动以后, 就可以在 client 端运行 netperf 来测试网络的性能. netperf 通过命令行参数来控制测试的类型和具体
的测试选项. 根据作用范围的不同, netperf 的命令行参数可以分为两大类: 全局命令行参数, 测试相关的局部参数, 两者之间使用 -- 分隔;

    netperf [global options]-- [test-specific options]

这里我们只解释那些常用的命令行参数, 其它的参数读者可以查询 netperf 的 man 手册.

* -H host : 指定远端运行 netserver 的 server IP地址.
* -l testlen : 指定测试的时间长度(秒)
* -t testname : 指定进行的测试类型, 包括 TCP_STREAM, UDP_STREAM, TCP_RR, TCP_CRR, UDP_RR, 在下文中分别对它们说明.

在后面的测试中, netserver 运行在 192.168.0.28, server 与 client 通过局域网连接(1000M Hub).

##Netperf测试网络性能

###测试批量(bulk)网络流量的性能

批量数据传输典型的例子有 ftp 和其它类似的网络应用(即一次传输整个文件). 根据使用传输协议的不同, 批量数据传输又分为 TCP 批量传输
和 UDP 批量传输.

####TCP_STREAM

Netperf缺省情况下进行TCP批量传输, 即-t TCP_STREAM. 测试过程中, netperf向netserver发送批量的TCP数据分组, 以确定数据传输过程中的吞吐量：

    $ netserver -p 5000

    $netperf -H 10.1.2.11 -l 10 -p 5000 -D
    MIGRATED TCP STREAM TEST from 0.0.0.0 (0.0.0.0) port 0 AF_INET to 10.1.2.11 ()
    port 0 AF_INET
    Recv   Send    Send
    Socket Socket  Message  Elapsed
    Size   Size    Size     Time     Throughput
    bytes  bytes   bytes    secs.    10^6bits/sec

    87380  16384  16384    10.00     106.81

从 netperf 的结果输出中, 我们可以知道以下的一些信息:

1 远端系统(即server)使用大小为 87380 字节的 socket 接收缓冲
2 本地系统(即client)使用大小为 16384 字节的 socket 发送缓冲
3 向远端系统发送的测试分组大小为 16384 字节
4 测试经历的时间为 10 秒
5 吞吐量的测试结果为 106 Mbits/秒

在缺省情况下,  netperf 向发送的测试分组大小设置为本地系统所使用的 socket 发送缓冲大小.

客户端

    $sysctl -a | grep tcp_wmem
    net.ipv4.tcp_wmem = 4096    16384   4194304

服务端

    $sysctl -a | grep tcp_rmem
    net.ipv4.tcp_rmem = 4096    87380   4194304

TCP_STREAM方式下与测试相关的局部参数如下表所示:

* -s size	设置本地系统的 socket 发送与接收缓冲大小
* -S size	设置远端系统的 socket 发送与接收缓冲大小
* -m size	设置本地系统发送测试分组的大小
* -M size	设置远端系统接收测试分组的大小
* -D	    对本地与远端系统的 socket 设置 TCP_NODELAY 选项

通过修改以上的参数, 并观察结果的变化, 我们可以确定是什么因素影响了连接的吞吐量. 例如, 如果怀疑路由器由于缺乏足够的缓冲区空间,
使得转发大的分组时存在问题, 就可以增加测试分组(-m)的大小, 以观察吞吐量的变化:

在这里, 测试分组的大小减少到 2048 字节, 而吞吐量却没有很大的变化(与前面例子中测试分组大小为 16K 字节相比). 相反, 如果吞吐量有
了较大的提升, 则说明在网络中间的路由器确实存在缓冲区的问题.

###UDP_STREAM

UDP_STREAM 用来测试进行 UDP 批量传输时的网络性能. 需要特别注意的是, 此时测试分组的大小不得大于 socket 的发送与接收缓冲大小,
否则 netperf 会报出错提示:

    $ netperf -t UDP_STREAM -H 192.168.0.28 -l 60
    UDP UNIDIRECTIONAL SEND TEST to 192.168.0.28
    udp_send: data send error: Message too long

为了避免这样的情况, 可以通过命令行参数限定测试分组的大小, 或者增加 socket 的发送/接收缓冲大小. UDP_STREAM 方式使用与 TCP_STREAM
方式相同的局部命令行参数, 因此, 这里可以使用 -m 来修改测试中使用分组的大小：

    $ netperf -t UDP_STREAM -H 192.168.0.28 -- -m 1024
    UDP UNIDIRECTIONAL SEND TEST to 192.168.0.28
    Socket  Message  Elapsed      Messages
    Size    Size     Time         Okay Errors   Throughput
    bytes   bytes    secs            #      #   10^6bits/sec

     65535    1024   9.99       114127      0      93.55
     65535           9.99       114122             93.54

UDP_STREAM 方式的结果中有两行测试数据, 第一行显示的是本地系统的发送统计, 这里的吞吐量表示 netperf 向本地 socket 发送分组的能力.
但是, 我们知道, UDP 是不可靠的传输协议, 发送出去的分组数量不一定等于接收到的分组数量.

第二行显示的就是远端系统接收的情况, 由于 client 与 server 直接连接在一起, 而且网络中没有其它的流量, 所以本地系统发送过去的分组
几乎都被远端系统正确的接收了, 远端系统的吞吐量也几乎等于本地系统的发送吞吐量. 但是, 在实际环境中, 一般远端系统的 socket 缓冲大
小不同于本地系统的 socket 缓冲区大小, 而且由于 UDP 协议的不可靠性, 远端系统的接收吞吐量要远远小于发送出去的吞吐量.

###测试请求/应答(request/response)网络流量的性能

另一类常见的网络流量类型是应用在 client/server 结构中的 request/response 模式. 在每次交易(transaction)中, client 向 server 发出
小的查询分组, server 接收到请求, 经处理后返回大的结果数据.

####TCP_RR

TCP_RR 方式的测试对象是多次 TCP request 和 response 的交易过程, 但是它们发生在同一个 TCP 连接中, 这种模式常常出现在数据库应用中.
数据库的 client 程序与 server 程序建立一个 TCP 连接以后, 就在这个连接中传送数据库的多次交易过程.

    $ netperf -t TCP_RR -H 192.168.0.28
    TCP REQUEST/RESPONSE TEST to 192.168.0.28
    Local /Remote
    Socket Size   Request  Resp.   Elapsed  Trans.
    Send   Recv   Size     Size    Time     Rate
    bytes  Bytes  bytes    bytes   secs.    per sec
    16384  87380  1        1       10.00    9502.73
    16384  87380

Netperf 输出的结果也是由两行组成. 第一行显示本地系统的情况, 第二行显示的是远端系统的信息. 平均的交易率(transaction rate)为 9502.73
次/秒. 注意到这里每次交易中的 request 和 response 分组的大小都为 1 个字节, 不具有很大的实际意义. 用户可以通过测试相关的参数来改变
request 和 response 分组的大小, TCP_RR 方式下的参数如下表所示:

* -r req,resp	设置 request 和 reponse 分组的大小
* -s size	    设置本地系统的 socket 发送与接收缓冲大小
* -S size	    设置远端系统的 socket 发送与接收缓冲大小
* -D	        对本地与远端系统的 socket 设置 TCP_NODELAY 选项

通过使用-r参数, 我们可以进行更有实际意义的测试：

    $netperf -t TCP_RR -H 192.168.0.28 -- -r 32,1024
    TCP REQUEST/RESPONSE TEST to 192.168.0.28
    Local /Remote
    Socket Size   Request  Resp.   Elapsed  Trans.
    Send   Recv   Size     Size    Time     Rate
    bytes  Bytes  bytes    bytes   secs.    per sec

    16384  87380  32       1024    10.00    4945.97
    16384  87380

从结果中可以看出, 由于 request/reponse 分组的大小增加了, 导致了交易率明显的下降.  注:相对于实际的系统, 这里交易率的计算没有充分考虑
到交易过程中的应用程序处理时延, 因此结果往往会高于实际情况.

###TCP_CRR

与 TCP_RR 不同, TCP_CRR 为每次交易建立一个新的TCP连接. 最典型的应用就是 HTTP, 每次 HTTP 交易是在一条单独的 TCP 连接中进行的.
因此, 由于需要不停地建立新的TCP连接, 并且在交易结束后拆除 TCP 连接, 交易率一定会受到很大的影响.

    $netperf -t TCP_CRR -H 192.168.0.28
    TCP Connect/Request/Response TEST to 192.168.0.28
    Local /Remote
    Socket Size   Request  Resp.   Elapsed  Trans.
    Send   Recv   Size     Size    Time     Rate
    bytes  Bytes  bytes    bytes   secs.    per sec

    131070 131070 1        1       9.99     2662.20
    16384  87380

即使是使用一个字节的 request/response分组, 交易率也明显的降低了, 只有 2662.20 次/秒. TCP_CRR 使用与 TCP_RR 相同的局部参数.

###UDP_RR

UDP_RR 方式使用 UDP 分组进行 request/response 的交易过程. 由于没有 TCP 连接所带来的负担, 所以我们推测交易率一定会有相应的提升.

    $netperf -t UDP_RR -H 192.168.0.28
    UDP REQUEST/RESPONSE TEST to 192.168.0.28
    Local /Remote
    Socket Size   Request  Resp.   Elapsed  Trans.
    Send   Recv   Size     Size    Time     Rate
    bytes  Bytes  bytes    bytes   secs.    per sec

    65535  65535  1        1       9.99     10141.16
    65535  65535

结果证实了我们的推测, 交易率为 10141.16 次/秒, 高过 TCP_RR 的数值. 不过, 如果出现了相反的结果, 即交易率反而降低了, 也不需要担心,
因为这说明了在网络中, 路由器或其它的网络设备对 UDP 采用了与 TCP 不同的缓冲区空间和处理技术.

除了 netperf 以外, 还有很多其它的网络性能测试工具, 如 dbs, iperf, pathrate, nettest, netlogger, tcptrace, ntop 等. 这些工具有其各
自的特色和不同的侧重点, 我们可以根据具体的应用环境, 有选择的使用它们, 这样就可以使这些工具发挥出最大的功效. 虽然都是开放源代码的软件,
但是这些工具的功能与商业的网络测试工具同样强大, 而且也得到了广泛的应用, 熟悉这些工具对我们的实际工作一定会有很大的帮助.


##其他

sysctl –e net.ipv4.tcp_autocorking=0

The -m option controls how many bytes are presented to the transport in
any one send call.

The -M option controls the upper bound on how many bytes are requested
of the transport in any one receive call.

The -m option will certainly interact with other things to affect the
size of packets "on the wire" but it is not a "direct" control of TCP
segment size.

It is only by chance/luck/timing that you can "control" the TCP segment
size via netperf.  As has been mentioned, there is the -D option to set
TCP_NODELAY, which will help, but it is still not going to guarantee a
given segment size when used in conjuction with -m.  The effects of
packet loss and congestion control can still leave you with at least
occasional, larger TCP segments.

This is an issue for the packet-per-second testing I used to be able to
do (years ago, with TCP was simpler :) ).  About the only way to "know"
the TCP segment size is no larger than N is to have no more than one,
N-headers size send outstanding at one time on any given TCP connection.

Depending on just how small one wishes the quantity of data in any given
TCP segment to be, it *might* be possible to use the test-specific -G
option to cause a setsockopt(TCP_MAXSEG) to be issued.  It will not
enable one to go larger than the MSS could be for the physical
network(s) in play but it should allow one to go smaller, though perhaps
bounded. (Looks like the smallest effective MSS I have been able to
create is 76 bytes, your mileage may vary).

There are some heuristics - eg ACK policy - which have MSS as part of
their input, so you might have some behaviour changes in TCP as you play
with that.

And if you were concerned with "things" in the end-systems rather than
in the middle, you may have to concern yourself with the settings for
things like TSO/GSO and GRO/LRO.

In some ways, if you want to have fully-controlled packet sizes, it may
be easier to use UDP tests.


###增加控制发送速率

./configure --enable-intervals

When netperf is configured with --enable-intervals or --enable-spin and
recompiled then the global -w option will set how often burst of up to
-b sends will be send.  However, if it takes longer than the interval
specified by -w to send that burst, behaviour is undefined on many
platforms the test may end prematurely.


##参考

http://www.netperf.org/svn/netperf2/trunk/doc/netperf.html#Top
http://www.netperf.org/pipermail/netperf-talk/2015-July/001271.html
