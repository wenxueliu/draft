##HAProxy 调研

* 版本: HAProxy 1.5

HAProxy 的文档非常完善, 源代码 doc 目录是最佳学习起点.

##特性

##负载均衡模式

###完成一次请求之后, 代理与客户端既与客户端保持连接又与服务端保持连接

###完成一次请求之后, 代理与客户端断开连接, 但服务端保持连接

###完成一次请求之后, 代理与客户端保持连接, 与服务端断开连接

###完成一次请求之后, 代理与客户端和服务端都断开连接


##集群功能

##负载均衡算法

####静态轮询与权重

不支持动态调整(权重不可更改), 性能更好

####轮询与权重

支持动态调整权重

####最少连接数

支持动态调整, 适合长连接业务, 不适合短连接

####最少服务器

从第一台服务器开始, 每个后台服务端到达其处理连接上限(maxconn)后, 使用下一个后台服务端,
如果没有设置 maxconn 参数值则没有用, 适合长连接的业务 如 RDP, IMAP.

####源IP 哈希

计算源 IP 哈希, 然后根据权重分配连接给后端服务器. 在后端服务器数量发生变化(增加或删除)
的情况下, 仍然可以保证同一客户端请求始终到同一后端服务器.

####URL 哈希

根据 URL 的(长度可配置)计算哈希, 然后根据权重分配连接给后端服务器.在后端服务器数量发生
变化(增加或删除) 的情况下, 仍然可以保证同一客户端请求始终到同一后端服务器.

####URL参数哈希

根据 URL 的参数(长度可配置)计算哈希, 然后根据权重分配连接给后端服务器.在后端服务器数量发生
变化(增加或删除) 的情况下, 仍然可以保证同一客户端请求始终到同一后端服务器.

####HTTP 头哈希

根据 HTTP 头(长度可配置)计算哈希, 然后根据权重分配连接给后端服务器.在后端服务器数量发生
变化(增加或删除) 的情况下, 仍然可以保证同一客户端请求始终到同一后端服务器.


##压缩

如果请求支持压缩, 如果后端服务器支持压缩, 负载均衡器将不会进行压缩, 如果后端服务器不支持压缩, 负载均衡将代替后端服务器对内容压缩

仅支持 HTTP1.1

##cookie

重写
插入


##其它关键特性

* 在线更新配置, 具体操作见附录
* 支持将一个资源池绑定到特定处理器集合
* 健康检查
* session 支持超时后自动删除
* 支持 lua 绑定
* 支持 SLA 压缩(降低 CPU 和 memory 利用率)
* 支持对来源设备信息的检测
* ebtree (弹性二叉树)
* HAProxy 并不能实现 NAT 等三层负载均衡
* 友好拒绝
* 超时机制
* ACL
* 支持 SSL
* 健康检查
* 基本的监控
* 软停止 : 不再处理新请求, 只维护旧请求
* 慢启动 : 逐渐增加后端服务器的负载

##编译

在内核 2.6.28 之后版本能达到最好的性能

make TARGET=linux2628 CPU=native ARCH=x86-64 SMALL_OPTS="-DBUFSIZE=8030 -DMAXREWRITE=1030 -DSYSTEM_MAXCONN=1024" \
USE_PCPRE=1 USE_STATIC_PCRE=1 USE_PCRE_JIT=1 USE_TFO=1 USE_SLA USE_GETADDRINFO=1 USE_REGPARM=1 \
USE_DLMALLOC=1 USE_LUA=1 USE_TRACE=1 \

其他可选
USE_NS=1
USE_OPENSSL=1 USE_PRIVATE_CACHE=1 | USE_PTHREAD_PSHARED=1 | USE_FUTEX=1




##SLZ 介绍

SLZ is a fast and memory-less stream compressor which produces an output that can be decompressed
with zlib or gzip. It does not implement decompression at all, zlib is perfectly fine for this.

The purpose is to use SLZ in situations where a zlib-compatible stream is needed and zlib's resource
usage would be too high while the compression ratio is not critical. The typical use case is in HTTP
servers and gateways which have to compress many streams in parallel with little CPU resources to
assign to this task, and without having to thottle the compression ratio due to the memory usage.
In such an environment, the server's memory usage can easily be divided by 10 and the CPU usage by 3.

http://1wt.eu/projects/libslz/





###编译优化

####march 参数

note that --march=native was introduced in gcc 4.2, prior to which it is just an unrecognized argument.

gcc -march=native -Q --help=target

gcc -march=native -E -v - </dev/null 2>&1 | grep cc1

$ gcc -march=native -Q --help=target | grep march

  -march=                     		corei7

然后 gcc -march=corei7

$ gcc -### -E - -march=native 2>&1 | sed -r '/cc1/!d;s/(")|(^.* - )//g'

-march=corei7 -mcx16 -msahf -mno-movbe -maes -mpclmul -mpopcnt -mno-abm -mno-lwp -mno-fma -mno-fma4 -mno-xop -mno-bmi -mno-bmi2 -mno-tbm -mno-avx -mno-avx2 -msse4.2 -msse4.1 -mno-lzcnt -mno-rtm -mno-hle -mno-rdrnd -mno-f16c -mno-fsgsbase -mno-rdseed -mno-prfchw -mno-adx -mfxsr -mno-xsave -mno-xsaveopt --param l1-cache-size=32 --param l1-cache-line-size=64 --param l2-cache-size=3072 -mtune=corei7 -fstack-protector -Wformat -Wformat-security

$ gcc -### -E - 2>&1 | sed -r '/cc1/!d;s/(")|(^.* - )//g'

-mtune=generic -march=x86-64 -fstack-protector -Wformat -Wformat-security

$ gcc -### -E - -march=native 2>&1 | sed -r '/cc1/!d;s/(")|(^.* - )|( -mno-[^\ ]+)//g'

-march=corei7 -mcx16 -msahf -maes -mpclmul -mpopcnt -msse4.2 -msse4.1 -mfxsr --param l1-cache-size=32 --param l1-cache-line-size=64 --param l2-cache-size=3072 -mtune=corei7 -fstack-protector -Wformat -Wformat-security

参考 http://stackoverflow.com/questions/5470257/how-to-see-which-flags-march-native-will-activate



##附录

###HAProxy 是什么?

HAProxy is a single-threaded, event-driven, non-blocking engine combining a very
fast I/O layer with a priority-based scheduler. As it is designed with a data
forwarding goal in mind, its architecture is optimized to move data as fast as
possible with the least possible operations. As such it implements a layered
model offering bypass mechanisms at each level ensuring data don't reach higher
levels when not needed. Most of the processing is performed in the kernel, and
HAProxy does its best to help the kernel do the work as fast as possible by
giving some hints or by avoiding certain operation when it guesses they could
be grouped later. As a result, typical figures show 15% of the processing time
spent in HAProxy versus 85% in the kernel in TCP or HTTP close mode, and about
30% for HAProxy versus 70% for the kernel in HTTP keep-alive mode.

###HAProxy 不是什么?

* HTTP Proxy : 可以通过 Squid 来说实现
* Cache Proxy : 可以通过 Varnish
* 数据过滤器 : 不能修改请求和应答的数据包体
* Web Server : 不能访问文件系统, 可以通过 Apache 和 nginx 来实现
* 基于包的数据均衡: 不能修改IP 实现 NAT, 可以通过 LVS, IPVS 实现

####性能参照

The following numbers were found on a Core i7 running at 3.7 GHz equiped with
a dual-port 10 Gbps NICs running Linux kernel 3.10, HAProxy 1.6 and OpenSSL
1.0.2. HAProxy was running as a single process on a single dedicated CPU core,
and two extra cores were dedicated to network interrupts :

  - 20 Gbps of maximum network bandwidth in clear text for objects 256 kB or
    higher, 10 Gbps for 41kB or higher;

  - 4.6 Gbps of TLS traffic using AES256-GCM cipher with large objects;

  - 83000 TCP connections per second from client to server;

  - 82000 HTTP connections per second from client to server;

  - 97000 HTTP requests per second in server-close mode (keep-alive with the
    client, close with the server);

  - 243000 HTTP requests per second in end-to-end keep-alive mode;

  - 300000 filtered TCP connections per second (anti-DDoS)

  - 160000 HTTPS requests per second in keep-alive mode over persistent TLS
    connections;

  - 13100 HTTPS requests per second using TLS resumed connections;

  - 1300 HTTPS connections per second using TLS connections renegociated with
    RSA2048;

  - 20000 concurrent saturated connections per GB of RAM, including the memory
    required for system buffers; it is possible to do better with careful tuning
    but this setting it easy to achieve.

  - about 8000 concurrent TLS connections (client-side only) per GB of RAM,
    including the memory required for system buffers;

  - about 5000 concurrent end-to-end TLS connections (both sides) per GB of
    RAM including the memory required for system buffers;

Thus a good rule of thumb to keep in mind is that the request rate is divided
by 10 between TLS keep-alive and TLS resume, and between TLS resume and TLS
renegociation, while it's only divided by 3 between HTTP keep-alive and HTTP
close. Another good rule of thumb is to remember that a high frequency core
with AES instructions can do around 5 Gbps of AES-GCM per core.

HAProxy normally spends most of its time in the system and a smaller part in
userland. A finely tuned 3.5 GHz CPU can sustain a rate about 80000 end-to-end
connection setups and closes per second at 100% CPU on a single core. When one
core is saturated, typical figures are :

  - 95% system, 5% user for long TCP connections or large HTTP objects
  - 85% system and 15% user for short TCP connections or small HTTP objects in
    close mode
  - 70% system and 30% user for small HTTP objects in keep-alive mode

###监控


    echo "show info" | socat - /var/run/haproxy.sock | grep ^Idle
    show pools

    strace -tt -s100 -etrace=sendmsg -p <haproxy pid>"
    tcpdump -As0 -ni lo port 514"

####Halog

For in-field troubleshooting without impacting the server's capacity too much,
it is recommended to make use of the "halog" utility provided with HAProxy.
This is sort of a grep-like utility designed to process HAProxy log files at
a very fast data rate. Typical figures range between 1 and 2 GB of logs per
second. It is capable of extracting only certain logs (eg: search for some
classes of HTTP status codes, connection termination status, search by response
time ranges, look for errors only), count lines, limit the output to a number
of lines, and perform some more advanced statistics such as sorting servers
by response time or error counts, sorting URLs by time or count, sorting client
addresses by access count, and so on. It is pretty convenient to quickly spot
anomalies such as a bot looping on the site, and block them.

####align

When an issue seems to randomly appear on a new version of HAProxy (eg: every
second request is aborted, occasional crash, etc), it is worth trying to enable
memory poisonning so that each call to malloc() is immediately followed by the
filling of the memory area with a configurable byte. By default this byte is
0x50 (ASCII for 'P'), but any other byte can be used, including zero (which
will have the same effect as a calloc() and which may make issues disappear).
Memory poisonning is enabled on the command line using the "-dM" option. It
slightly hurts performance and is not recommended for use in production. If
an issue happens all the time with it or never happens when poisoonning uses
byte zero, it clearly means you've found a bug and you definitely need to
report it. Otherwise if there's no clear change, the problem it is not related.

###性能调优

   Pinning haproxy to one CPU core and the interrupts to another one,
all sharing the same L3 cache tends to sensibly increase network performance
because in practice the amount of work for haproxy and the network stack are
quite close, so they can almost fill an entire CPU each.On Linux this is done
using taskset (for haproxy) or using cpu-map (from the haproxy config), and the
interrupts are assigned under /proc/irq. Many network interfaces support
multiple queues and multiple interrupts. In general it helps to spread them
across a small number of CPU cores provided they all share the same L3 cache.
Please always stop irq_balance which always does the worst possible thing on
such workloads.

On Linux versions 3.9 and above, running HAProxy in multi-process mode is much
more efficient when each process uses a distinct listening socket on the same
IP:port ; this will make the kernel evenly distribute the load across all
processes instead of waking them all up. Please check the "process" option of
the "bind" keyword lines in the configuration manual for more information.

###多进程多 haproxy 的影响

  - health checks are run per process, so the target servers will get as many
    checks as there are running processes ;
  - maxconn values and queues are per-process so the correct value must be set
    to avoid overloading the servers ;
  - outgoing connections should avoid using port ranges to avoid conflicts
  - stick-tables are per process and are not shared between processes ;
  - each peers section may only run on a single process at a time ;
  - the CLI operations will only act on a single process at a time.

###在线更新配置

  # save previous state
  mv /etc/haproxy/config /etc/haproxy/config.old
  mv /var/run/haproxy.pid /var/run/haproxy.pid.old

  mv /etc/haproxy/config.new /etc/haproxy/config
  kill -TTOU $(cat /var/run/haproxy.pid.old)
  if haproxy -p /var/run/haproxy.pid -f /etc/haproxy/config; then
    echo "New instance successfully loaded, stopping previous one."
    kill -USR1 $(cat /var/run/haproxy.pid.old)
    rm -f /var/run/haproxy.pid.old
    exit 1
  else
    echo "New instance failed to start, resuming previous one."
    kill -TTIN $(cat /var/run/haproxy.pid.old)
    rm -f /var/run/haproxy.pid
    mv /var/run/haproxy.pid.old /var/run/haproxy.pid
    mv /etc/haproxy/config /etc/haproxy/config.new
    mv /etc/haproxy/config.old /etc/haproxy/config
    exit 0
  fi

当然如果要强制旧的haproxy 立即退出, 运行如下命令:

    kill $(cat /var/run/haproxy.pid.old)
    rm -f /var/run/haproxy.pid.old

    1.6 全面支持环境变量


注:

    配置文件支持环境变量, 是否可以通过更改环境变量来更改权限.

为了方便后端服务器进行平滑服务升级,维护等, 每个后端服务器可以增加一个或多个备份服务.
如果该服务失败, 之前本应该转到该服务器的请求将被转到备份服务而不是其他服务.
相当于在负载均衡器上实现服务的重定向功能

后端服务器可以将新请求重定向到备份服务器. 待已经存在的请求处理完毕, 将服务器停掉即可.

当然还可以有的选项是服务器本身内部进行防火墙的重定向映射. 但是这不能跨机器,
此外对于没有防火墙的服务器则没有办法. 比如 iptabls :

  # iptables -t nat -A PREROUTING -p tcp --dport 81 -j REDIRECT --to-port 80

  # iptables -t nat -A OUTPUT -d 192.168.1.11 -p tcp --dport 81 -j DNAT --to-dest :80

  # iptables -t nat -D OUTPUT -d 192.168.1.12 -p tcp --dport 81 -j DNAT --to-dest :80


##两地三中心的问题

假设在 A 城市有两个数据中心, 延迟在 10ms 以内, 在 B 城市也由两个数据中心.
都是一主一备.

###存储一致性

在A 失败, 负载均衡可以切换到 B, 但是, 存储却无法实时切换, 此外, 如果是基于
Session 的负载均衡, session 也是没有切换的,

###通信延迟:

两个城市通信是在几十毫秒级, 而同一个城市网络延迟在 10 ms 左右.

##Qos

每个 pool 包含 maxconn
每个后端服务器报告 minconn, maxconn
一个新请求队列, 元素在队列的超时时间 conntimeout 如果超时还没有被处理, 连接将被重置
一个已经存在请求队列, 元素在队列的超时时间 conntimeout 如果超时还没有被处理, 连接将被重置
优先处理在已经存在请求队列中的元素


当并发数低于 pool 的 maxconn, 后端服务器的处理请求将保持在 minconn. 以保证低延迟
新请求优先保证已经存在的请求先被处理.

当并发数超过 pool 的 maxconn, 后续请求将被缓存在队列, 后端服务器处理能力被调整为
maxconn, 以增加延迟为代价应对高并发的情况.

1. 所有的客户端请求都可以被处理, 只是延迟不一样
2. 不会出现多米诺骨牌(domino)消息
3. 可以增加服务器的利用率, 并且防止了服务端过载的出现.
