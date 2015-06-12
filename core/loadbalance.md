##调研

##负载算法

##前提:

1. 流量或链路负载均衡
2. 客户端(client ip)的数量不多, 因此不会存在, 一个端口和其他端口的链路树存在严重的差距.
3. 后端服务器预估为 10 台左右.
4. 流表数量 2000 条左右
5. 以一个 pool 为例, 客户端指目的IP 为虚拟服务器的客户端, 多 pool 情况可类推

###流量监控

通过 sFlow 监控所有客户端的 ip, port, packet(单位bytes), time

以 T(根据时间情况决定) 秒为单位间隔, 统计
1. port 数量, 每个 port 对应的所有 ip 列表及总 packet
2. ip 数量, 每个 ip 对应的 port 列表 及总 packet
3. 总 ip+port, 每个 ip+port 对应的 packet

据此,建立一天,一月,一年的流量模型, 由于银行工作时间,业务具有非常明显的特点,
建立的流量模型可能较为容易

此外,基于调研部分可以看出,如果一个 ip 很多端口出现, 很容易确认是一个非常活跃的客户端.

###负载分配算法

Proactive

1. 将端口 32768-50000 以 M(64) 为一组 Ri, 分成 N = 65536/M 组
2. 获取每组 Ri 的链路数(也可为流量) Ki, 总链路数 K.
4. 将每台服务器(Bi) 权重 Pi 相加得到 P, 每台服务器分配 Si(S = Pi * K * /P) 条链路
3. 将后端服务器根据 IP 从小到大排列. 给第一台服务器(B1), 分配从第一组端口(R1)开始,
   分配分配 l 组, 直到分配给 R1 的链路数大于应该分配的链路数.

Reactive

1. 将端口范围 0-32768,50000-65535 以 M(64) 为一组 Ri, 分为 N = 32768/M + (65535-5000)/M 组
2. 控制器收到 packet_in 消息
3. 判断客户端的端口,如果属于其中某个组 Rk, 根据每台后端服务器的 priority 和负载, 将 Rk 分配给符合条件的某后端服务器.
4. 此时创建的流表 idle_timeout = T 秒(根据时间业务对 TCP 超时要求决定).

####流表示例

####Proactive

**inBound**

* Match: priority=1,idle_timeout=0, hard_timeout=0,src_port_range=M-N, dst_ip=POOL_IP, dst_port=POOL_PORT,
* Action:set_field:dst_ip=BK_IP,dst_port=BK_PORT,dst_mac=BK_MAC output=PORT

**outBound**

* Match: priority=1,idle_timeout=0, hard_timeout=0,src_ip=BK_IP,src_port=BK_PORT,
* Action:set_field:src_ip=POOL_IP,src_port=POOL_PORT,src_mac=POOL_MAC,output=PORT

####Reactive

**inBound**

* Match: priority=1,idle_timeout=60, hard_timeout=0,src_port_range=M-N, dst_ip=POOL_IP, dst_port=POOL_PORT,
* Action:set_field:dst_ip=BK_IP,dst_port=BK_PORT,dst_mac=BK_MAC output=PORT

**outBound**

* Match: priority=1,idle_timeout=0, hard_timeout=0,src_ip=BK_IP,src_port=BK_PORT,
* Action:set_field:src_ip=POOL_IP,src_port=POOL_PORT,src_mac=POOL_MAC,output=PORT

说明
* M-N         : 某一端口范围
* POOL_IP     : 虚拟服务器 ip
* POOL_PORT   : 虚拟服务器 port
* POOL_MAC    : 虚拟服务器 mac
* BK_IP       : 后端服务器的 ip
* BK_PORT     : 后端服务器的 port
* BK_MAC      : 后端服务器 mac
* PORT        : 为某一个后端服务器在端口,或客户端端口

####可能的问题:

1. 最后一或几台服务可能无法分配到链路. 如果最后一台服务器无法分配到端口组, 将端口
粒度降低(如果32个端口为一组)重新分配.

2. 分配后链路不均匀(将端口粒度进一步缩小), 再不行, 引入 IP, 但我们的业务实际客户端很少,
因此, 这里引入 IP 必要性很小.

3. 根据实际情况, 调整 Reactive 和 Proactive 的端口比例

###结果

通过调整端口的粒度, 最后每个后端服务器的链路数或流量是均匀的. 更为重要的是, 通过分配算法之后,
所需流表数量与 Reactive 的端口分组粒度有关. 以 Reactive 64 个端口为例, 大约需要 800 条流表.

因此,  因为只有在高负载的情况下才需要引入 Reactive, 虽然增加了不少流表项, 但获得的是高负载情
况下的流量迁移更加平滑

###后续工作

端口的粒度可以更加流量监控的结果自动调整, 达到学习流量 -> 生成规则的闭环


###负载重分配算法

当流量变化超过一个阈值, 旧的流表规则已经不能适用新的流量, 需要进行负载重分配.

1. 根据负载均衡算法, 生成新的分配算法.
2. 将转发到同一后端服务器的一条流表,分为 t 组, 每组配置更高 priority 的流表(流表过期时间为链路超时时间, 如 60 s),
待流量超时, 就将该部分流量切换到新的分配算法指定的后端服务器
3. 依据步骤 2, 依次将所有的旧的流量迁移到新的后端服务器.(可以一次进行多个 Ri 的切换, 这与所使用
   的流表数相关.迁移所用的流表数越多, 迁移速度越快.)

####流表示例

**inBound1**

* Match: priority=3,idle_timeout=60, hard_timeout=0,src_port_range=M1-N1, dst_ip=POOL_IP, dst_port=POOL_PORT,
* Action:set_field:dst_ip=BK_IP,dst_port=BK_PORT,dst_mac=BK_MAC output=PORT

**inBound2**

* Match: priority=2,idle_timeout=0, hard_timeout=0,src_port_range=M2-N2, dst_ip=POOL_IP, dst_port=POOL_PORT,
* Action:set_field:dst_ip=NEWBK_IP,dst_port=NEWBK_PORT,dst_mac=NEWBK_MAC output=PORT

说明
* M1-N1       : 某一端口范围
* M2-N2       : 某一端口范围, 一般情况下 M1-N1 为 M2-N2 的子集
* POOL_IP     : 虚拟服务器 ip
* POOL_PORT   : 虚拟服务器 port
* POOL_MAC    : 虚拟服务器 mac
* BK_IP       : 后端服务器的 ip
* BK_PORT     : 后端服务器的 port
* BK_MAC      : 后端服务器 mac
* NEWBK_IP    : 新的后端服务器 ip
* NEWBK_PORT  : 新的后端服务器 port
* NEWBK_MAC   : 新的后端服务器 mac
* PORT        : 为某一个后端服务器在端口,或客户端端口

为了防止 priority 不断递增, 后续会删除原来 priority =1 流表, 创建 priority=1 的新流表, 并删除 priority=2 的新流表

####可能的问题

0. 进行负载切换的时机,1).某台后端服务器处理的链路数超出阈值.(超出服务器应该配置的链路数的两倍)
1. 切换速度太慢, 解决办法增加迁移所用流表数量
2. 部分链路是长链接, 一直无法迁移, 对于链路中存在的长连接, 可以留出一部分流表专门处理长连接的情况.
3. 在高负载的情况下, 可能流表永远不会过期, 解决办法, 通过在 controller 缓存已经建立的链路,
 创建更高权限的流表,将流量转发到 controller, controller 解包 SYN 判断是否是新链路来进行流量切换.
 此外,可以预估流量峰值, 提前分配服务器.
4. 在高负载流量不断突变的情况下, 切换算法可能缺乏灵活性. (待验证)
5. 在迁移过程中，部分后端服务器要暂时性承载非常大的负载导致后端服务器不可用.(很可能遇到)

####后续工作

负载载全部重分配太重, 考虑进行负载的部分重分配

###动态后端服务器

实际情况是当集群负载很大的时候, 通过增加服务器来减小每台服务器的负载, 负载低的时候,通过减少服务器
来节约资源,或用于其他高负载集群.

此种情况重分配算法同负载均衡重分配算法.

##调研

###端口范围

####测试1

客户端端口范围配置:

    /proc/sys/net/ipv4/ip_local_port_range  32768   61000

客户端 ab 100 并发,总 100000 次请求, 访问服务器，服务器记录客户端端口范围:

    35452, 61000,32768,61000,32768,61000,32768,50756

结论，在地址不重用的情况下，客户端端口依次递增，直到最大端口号，然后从最小端口开始．

####测试2

地址重用测试

客户端修改:

/proc/sys/net/ipv4/tcp_tw_reuse   0   1
/proc/sys/net/ipv4/tcp_tw_recycle 0   1

客户端 ab 100 并发,总 100000 次请求, 访问服务器，服务器记录客户端端口范围:

    53236,53308 53139,53158 53309,53311 53159,53235 53312,61000 32768,61000, ...

结论，在地址回收和重用的情况下,如果系统负载较大, 客户端的端口仍然是依次递增到最大端口号,然后从最小端口号开始

####测试3

不同负载情况下端口使用情况

非端口重用, ab 并发 10 总共 10000 不同时间段访问同一服务器, 服务器记录客户端端口范围

第一次

    Wed Jun 10 16:56:32 CST 2015
    50223,60215

第二次

    Wed Jun 10 17:13:26 CST 2015
    60224,61000 32768,41983

结论, 客户端访问,自身端口总是不断地递增(与访问时间无关),直到最大端口号. 从最小端口号重新开始


端口重用, ab 并发 10 总共 10000 不同时间段访问同一服务器, 服务器记录客户端端口范围

第一次

    Wed Jun 10 18:12:08 CST 2015
    33765,43764

第二次
    Wed Jun 10 18:44:21 CST 2015
    43768,53767

结论, 客户端访问,自身端口总是不断地递增(与访问时间无关),直到最大端口号. 从最小端口号重新开始

注: 由于客户端可以在编程的情况下,在 socket API 中设置端口重用, 与前述端口重用测试可能情况不同, 待验证.

###参考

[端口范围](http://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers)
[端口重用在不同系统的情况](http://stackoverflow.com/questions/14388706/socket-options-so-reuseaddr-and-so-reuseport-how-do-they-differ-do-they-mean-t)

##附录

TCP/UDP的端口采用16bit存储，所以端口范围为0~65535.端口被分为3类使用：

    Well Known ports: 0 ~ 1023
    Registered Ports: 1024 ~ 49151
    Dynamic and/or Private Ports: 49152 ~ 65535

作为客户端连接，我们使用的Dynamic port，端口总数为 16384个。

在不同的平台下，对于Dynamic Port Range的默认值也是不同的。

###AIX

默认的端口范围

    /usr/sbin/no -a | fgrep ephemeral

    tcp_ephemeral_low = 32768
    tcp_ephemeral_high = 65535
    udp_ephemeral_low = 32768
    udp_ephemeral_high = 65535

可以通过下面的命令来调整：

    /usr/sbin/no -o tcp_ephemeral_low=49152 -o tcp_ephemeral_high=65535

这个命令在重启后失效，固化的方法是将命令添加到/etc/rc.tcpip

###HP-UX

默认的端口范围

    #ndd /dev/tcp tcp_smallest_anon_port
    49152
    #ndd /dev/tcp tcp_largest_anon_port
    65535
    #ndd /dev/udp udp_smallest_anon_port
    49152
    #ndd /dev/udp udp_largest_anon_port
    65535

    /usr/bin/ndd -set /dev/tcp tcp_smallest_anon_port 50001

    这个命令在重启后失效，固化的方法是将配置添加到/etc/rc.config.d/nddconf

类似如下：

    /etc/rc.config.d/nddconf:
    TRANSPORT_NAME[0]=tcp
    NDD_NAME[0]=tcp_largest_anon_port
    NDD_VALUE[0]=65535
    TRANSPORT_NAME[1]=tcp
    NDD_NAME[1]=tcp_smallest_anon_port
    NDD_VALUE[1]=49152

###Linux

默认的端口范围：

    #cat /proc/sys/net/ipv4/ip_local_port_range
    32768   61000

设置方法，在/etc/sysctl.conf中添加

    net.ipv4.ip_local_port_range = 9000 65500

###Solaris

默认端口范围：

    /usr/sbin/ndd /dev/tcp tcp_smallest_anon_port
    32768
    /usr/sbin/ndd /dev/tcp tcp_largest_anon_port
    65535
    /usr/sbin/ndd /dev/udp udp_smallest_anon_port
    32768
    /usr/sbin/ndd /dev/udp udp_largest_anon_port
    65535

###Windows

默认端口范围

    从之前的 1025~5000 改变为 49152~65535, 具体见[这里](https://support.microsoft.com/en-us/kb/929851)
