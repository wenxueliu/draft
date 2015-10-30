Keepalived 是一个基于 VRRP 协议来实现的服务高可用方案, 可以利用其来避免IP单点故障, 类似的工具还有 heartbeat、corosync、pacemaker.
但是它一般不会单独出现, 而是与其它负载均衡技术(如lvs、haproxy、nginx)一起工作来达到集群的高可用. 比如, 一个 LVS 服务会有 2 台服务
器运行 Keepalived, 一台为主服务器(MASTER), 一台为备份服务器(BACKUP), 但是对外表现为一个虚拟 IP, 主服务器会发送特定的消息给备份服务
器, 当备份服务器收不到这个消息的时候, 即主服务器宕机的时候, 备份服务器就会接管虚拟IP, 继续提供服务, 从而保证了高可用性.

##VRRP协议

在现实的网络环境中, 两台需要通信的主机大多数情况下并没有直接的物理连接. 对于这样的情况, 它们之间路由怎样选择? 主机如何选定到达目的
主机的下一跳路由, 这个问题通常的解决方法有二种:

* 在主机上使用动态路由协议(RIP、OSPF等)
* 在主机上配置静态路由

很明显, 在主机上配置动态路由是非常不切实际的, 因为管理、维护成本以及是否支持等诸多问题. 配置静态路由就变得十分流行, 但路由器(或者说
默认网关default gateway)却经常成为单点故障. VRRP 的目的就是为了解决静态路由单点故障问题, VRRP 通过一竞选(election)协议来动态的将路由
任务交给 LAN 中虚拟路由器中的某台 VRRP 路由器.

VRRP 全称 Virtual Router Redundancy Protocol, 即虚拟路由冗余协议. 可以认为它是实现路由器高可用的容错协议, 即将 N 台提供相同功能的路由
器组成一个路由器组(Router Group), 这个组里面有一个 master 和多个 backup, 但在外界看来就像一台一样, 构成虚拟路由器, 拥有一个虚拟IP(vip,
也就是路由器所在局域网内其他机器的默认路由), 占有这个 IP 的 master 实际负责 ARP 相应和转发 IP 数据包, 组中的其它路由器作为备份的角色处
于待命状态. MASTER 会发组播消息, 当 BACKUP 在超时时间内收不到 VRRP 包时就认为 MASTER 宕掉了, 这时就需要根据 VRRP 的优先级来选举一个
BACKUP 当 MASTER, 保证路由器的高可用.

在一个 VRRP 虚拟路由器中, 有多台物理的 VRRP 路由器, 但是这多台的物理的机器并不能同时工作, 而是由一台称为 MASTER 的负责路由工作, 其它
的都是 BACKUP, MASTER 并非一成不变, VRRP 让每个 VRRP 路由器参与竞选, 最终获胜的就是 MASTER. MASTER 拥有一些特权, 比如, 拥有虚拟路由器
的 IP 地址, 我们的主机就是用这个 IP 地址作为静态路由的. 拥有特权的 MASTER 要负责转发发送给网关地址的包和响应 ARP 请求.

VRRP 通过竞选协议来实现虚拟路由器的功能, 所有的协议报文都是通过 IP 多播(multicast)包(多播地址224.0.0.18)形式发送的. 虚拟路由器由VRID(范
围0-255)和一组IP地址组成, 对外表现为一个周知的 MAC 地址. 所以, 在一个虚拟路由 器中, 不管谁是 MASTER, 对外都是相同的 MAC 和 IP(称之为
VIP). 客户端主机并不需要因为 MASTER 的改变而修改自己的路由配置, 对客户端来说, 这种主从的切换是透明的.

在一个虚拟路由器中, 只有作为 MASTER 的 VRRP 路由器会一直发送 VRRP 通告信息(VRRPAdvertisement message), BACKUP 不会抢占 MASTER, 除非它
的优先级(priority)更高. 当MASTER不可用时(BACKUP收不到通告信息),  多台 BACKUP 中优先级最高的这台会被抢占为 MASTER. 这种抢占是非常快速
的(<1s), 以保证服务的连续性. 由于安全性考虑, VRRP 包使用了加密协议进行加密.


在VRRP协议实现里, 虚拟路由器使用 00-00-5E-00-01-XX 作为虚拟MAC地址, XX就是唯一的 VRID (Virtual Router IDentifier), 这个地址同一时间只
有一个物理路由器占用. 在虚拟路由器里面的物理路由器组里面通过多播IP地址 224.0.0.18 来定时发送通告消息. 每个 Router 都有一个 1-255 之间
的优先级别, 级别最高的(highest priority)将成为主控(master)路由器. 通过降低 MASTER 的优先权可以让处于 BACKUP 状态的路由器抢占(pro-empt)
主路由器的状态, 两个 BACKUP 优先级相同的 IP 地址较大者为 MASTER, 接管虚拟IP.

###VRRP 工作流程

(1).初始化

路由器启动时, 如果路由器的优先级是255(最高优先级, 路由器拥有路由器地址), 要发送 VRRP 通告信息, 并发送广播 ARP 信息通告路由器 IP 地址
对应的 MAC 地址为路由虚拟 MAC, 设置通告信息定时器准备定时发送 VRRP 通告信息, 转为 MASTER 状态; 否则进入 BACKUP 状态, 设置定时器检查
定时检查是否收到 MASTER 的通告信息.

(2).Master

    设置定时通告定时器;

    用 VRRP 虚拟 MAC 地址响应路由器 IP 地址的 ARP 请求;

    转发目的MAC是VRRP虚拟MAC的数据包;

    如果是虚拟路由器IP的拥有者, 将接受目的地址是虚拟路由器IP的数据包, 否则丢弃;

    当收到shutdown的事件时删除定时通告定时器, 发送优先权级为0的通告包, 转初始化状态;

    如果定时通告定时器超时时, 发送VRRP通告信息;

    收到VRRP通告信息时, 如果优先权为0, 发送 VRRP 通告信息; 否则判断数据的优先级是否高于本机, 或相等而且实际 IP 地址大于本地实际 IP, 设置定时通告定时器, 复位主机超时定时器, 转 BACKUP 状态; 否则的话, 丢弃该通告包;

(3).Backup

    设置主机超时定时器;

    不能响应针对虚拟路由器IP的ARP请求信息;

    丢弃所有目的MAC地址是虚拟路由器MAC地址的数据包;

    不接受目的是虚拟路由器IP的所有数据包;

    当收到shutdown的事件时删除主机超时定时器, 转初始化状态;

    主机超时定时器超时的时候, 发送VRRP通告信息, 广播ARP地址信息, 转MASTER状态;

    收到VRRP通告信息时, 如果优先权为0, 表示进入MASTER选举; 否则判断数据的优先级是否高于本机, 如果高的话承认MASTER有效, 复位主机超时定时器; 否则的话, 丢弃该通告包;


###MASTER 和 BACKUP 节点的优先级如何调整?

首先, 每个节点有一个初始优先级, 由配置文件中的 priority 配置项指定, MASTER 节点的 priority 应比 BAKCUP 高.
运行过程中 keepalived 根据 vrrp_script 的 weight 设定, 增加或减小节点优先级. 规则如下:

1. 当 weight > 0 时, vrrp_script script 脚本执行返回0(成功)时优先级为 priority + weight, 否则为 priority.
当 BACKUP 发现自己的优先级大于MASTER通告的优先级时, 进行主从切换.

2. 当 weight < 0 时, vrrp_script script 脚本执行返回非0(失败)时优先级为 priority + weight, 否则为 priority.
当 BACKUP 发现自己的优先级大于 MASTER 通告的优先级时, 进行主从切换.

3. 当两个节点的优先级相同时, 以节点发送 VRRP 通告的 IP 作为比较对象, IP 较大者为 MASTER.

以上文中的配置为例:

    HOST1: 10.15.8.100, priority=91, MASTER(default)
    HOST2: 10.15.8.101, priority=90, BACKUP
    VIP: 10.15.8.102 weight = 2

抓包命令: tcpdump -nn vrrp

示例一: HOST1 和 HOST2 上 keepalived 和 nginx均正常.

16:33:07.697281 IP 10.15.8.100 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 93, authtype simple, intvl 1s, length 20
16:33:08.697588 IP 10.15.8.100 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 93, authtype simple, intvl 1s, length 20

示例二: 关闭 HOST1 上的 nginx.

16:33:09.697928 IP 10.15.8.100 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 93, authtype simple, intvl 1s, length 20
16:33:10.698285 IP 10.15.8.100 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 91, authtype simple, intvl 1s, length 20
16:33:10.698482 IP 10.15.8.101 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 92, authtype simple, intvl 1s, length 20
16:33:11.699441 IP 10.15.8.101 > 224.0.0.18: VRRPv2, Advertisement, vrid 102, prio 92, authtype simple, intvl 1s, length 20

HOST1 上的 nginx 关闭后, killall -0 nginx 返回非 0, HOST1 通告的优先级为 priority = 91, HOST2 的优先级为 priority + weight = 92,
HOST2 抢占成功, 被选举为MASTER. 相关日志可tail /var/log/messages.

由此可见, 主从的优先级初始值 priority 和变化量 weight 设置非常关键, 配错的话会导致无法进行主从切换. 比如, 当 MASTER 初始值定得太高,
即使 script 脚本执行失败, 也比 BACKUP 的 priority + weight 大, 就没法进行 VIP 漂移了. 所以 priority 和 weight 值的设定应遵循: 

    abs(MASTER priority - BAKCUP priority) < abs(weight).

另外, 当网络中不支持多播(例如某些云环境), 或者出现网络分区的情况, keepalived BACKUP 节点收不到 MASTER 的 VRRP 通告, 就会出现脑裂
(split brain)现象, 此时集群中会存在多个MASTER节点.


###ARP查询处理

当内部主机通过 ARP 查询虚拟路由器 IP 地址对应的 MAC 地址时, MASTER 路由器回复的 MAC 地址为虚拟的 VRRP 的 MAC 地址, 而不是实际网卡的
MAC 地址, 这样在路由器切换时让内网机器觉察不到; 而在路由器重新启动时, 不能主动发送本机网卡的实际 MAC 地址. 如果虚拟路由器开启的 ARP
代理 (proxy_arp)功能, 代理的 ARP 回应也回应VRRP虚拟 MAC 地址;

###虚拟IP地址和MAC地址

VRRP组(备份组)中的虚拟路由器对外表现为唯一的虚拟MAC地址, 地址格式为00-00-5E-00-01-[VRID], VRID 为 VRRP 组的编号, 范围是0~255.

##Keepalived

keepalived可以认为是VRRP协议在Linux上的实现, 主要有三个模块, 分别是 core, check 和 vrrp. core 模块为 keepalived 的核心, 负责主进程的启动,
维护以及全局配置文件的加载和解析. check 负责健康检查, 包括常见的各种检查方式. vrrp 模块是来实现 VRRP 协议的. 本文基于如下的拓扑图:


						   +-------------+
						   |   uplink    |
						   +-------------+
							     |
							     +
		    MASTER           keep|alived           BACKUP
		 172.29.88.224      172.29.88.222       172.29.88.225
		+-------------+    +-------------+    +-------------+
		| nginx01     |----| virtualIP   |----| nginx02     |
		+-------------+    +-------------+    +-------------+
								 |
			  +------------------+------------------+
			  | 				 |                  |
		+-------------+    +-------------+    +-------------+
		|   web01     |    |   web02     |    |   web03     |
		+-------------+    +-------------+    +-------------+

##问题

系统一: 主从节点做双网卡绑定, 都只有一个私有 IP, VIP 也为私有IP, 通过防火墙的 NAT 转发用户的访问请求.
主节点宕机后, VIP 可以漂移至从节点, 但用户无法访问网站, telnet 防火墙公网 IP 的 80 端口提示无法连接.

系统二: 主从节点各有两张网卡, 分别配置一个公网 IP 和一个私有 IP. VIP地址也使用公网 IP 来提供.
主节点宕机后, VIP 可以漂移至从节点, 但用户无法 ping 通 VIP, 自然网站也就打不开.

于是分别对这两种情况进行排查:

系统二: 属于比较常见的配置方案. VIP 漂移后无法 ping 通, 第一反应询问机房工作人员, 是否相应的设备做了
mac地址绑定. 得知无绑定策略后继续排查. 发现配置 net.ipv4.ip_nonlocal_bind = 1 参数并使其生效后重新测
试正常.

系统一: 情况有点特殊, 按系统二的解决方法尝试无果后, 怀疑端口路由器映射上出现问题. 于是继续测试 VIP 漂移,
发现VIP漂移到从节点后, 防火墙上的 arp 表中 vip 对应的 mac 地址依旧是主节点网卡的 mac 地址, 原来防火墙才
是罪魁祸首, 坑爹的货. 机房使用的防火墙型号华为 Quidway Eudemon1000E, 据说默认配置下, 这个 arp 地址表自动
刷新需要20分钟！

好吧！于是用下面的命名手工刷新后, 万事大吉, 网站访问也很顺畅, 比较郁闷的是当主节点重新抢占 VIP 后, 依然
需要手工刷新下, 否则防火墙还是把请求转给从节点响应.

# arping -I 网卡地址 -c 3 -s VIP地址 网关地址

因此, 要彻底解决系统一的问题, 可以从两方面去着手, 首先是考虑去调整防火墙的 arp 表的自动刷新时间; 其次是考
虑在从节点上部署一个无限循环的脚本, 时时去检测是否抢占到了 VIP, 若抢占成功, 则运行前面的刷新命令, 命令成功
运行后退出脚本, 同时可以用 nagios 监控该脚本, 了解最新的主从切换情况. 切记, 循环运行一次接受后 sleep 1 秒,
否则会死机的哦！

如果在主节点上也部署类似的脚本, 则会对网络带来负担, 因而主节点恢复后的刷新手工运行下就好了, 如果忘记运行了,
从节点依然可以工作, 无伤大雅！

##与heartbeat/corosync等比较

Heartbeat, Corosync, Keepalived 这三个集群组件我们到底选哪个好, 首先我想说明的是, Heartbeat, Corosync是属于同一类型,
Keepalived 与 Heartbeat、Corosync, 根本不是同一类型的. Keepalived 使用的 VRRP 协议方式, 虚拟路由冗余协议
(Virtual Router Redundancy Protocol, 简称VRRP); Heartbeat 或 Corosync 是基于主机或网络服务的高可用方式; 简单的说就是,
Keepalived 的目的是模拟路由器的高可用, Heartbeat 或 Corosync 的目的是实现 Service 的高可用.

所以一般 Keepalived 是实现前端高可用, 常用的前端高可用的组合有, 就是我们常见的 LVS+Keepalived, Nginx+Keepalived,
HAproxy+Keepalived. 而 Heartbeat 或 Corosync 是实现服务的高可用, 常见的组合有 Heartbeat v3(Corosync)+Pacemaker+NFS+Httpd
实现 Web 服务器的高可用, Heartbeat v3(Corosync)+Pacemaker+NFS+MySQL 实现MySQL服务器的高可用.

总结一下, Keepalived 中实现轻量级的高可用, 一般用于前端高可用, 且不需要共享存储, 一般常用于两个节点的高可用. 而
Heartbeat(或Corosync) 一般用于服务的高可用, 且需要共享存储, 一般用于多节点的高可用. 这个问题我们说明白了.

那 heartbaet 与 corosync 我们又应该选择哪个好啊, 我想说我们一般用 corosync, 因为 corosync 的运行机制更优于 heartbeat,
就连从 heartbeat 分离出来的 pacemaker 都说在以后的开发当中更倾向于 corosync, 所以现在 corosync+pacemaker 是最佳组合.

##参考

http://ylw6006.blog.51cto.com/470441/1314004
http://tools.ietf.org/html/rfc3768


##keepalived 测试


安装
============================

$ sudo yum -y install keepalived nginx

配置
============================


		    MASTER           keep|alived           BACKUP
		 192.168.0.86      192.168.0.100       192.168.0.14
		+-------------+    +-------------+    +-------------+
		| nginx01     |----| virtualIP   |----|  nginx02    |
		+-------------+    +-------------+    +-------------+
								 |
			    				 |
	                       +-------------+
						   |   client    |
					       +-------------+

MASTER 配置
----------------------------


$ ifconfig eth1
	eth1      Link encap:Ethernet  HWaddr 08:00:27:6F:34:F4  
		      inet addr:192.168.0.86  Bcast:192.168.0.255  Mask:255.255.255.0
		      inet6 addr: fe80::a00:27ff:fe6f:34f4/64 Scope:Link
		      UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
		      RX packets:476104 errors:0 dropped:0 overruns:0 frame:0
		      TX packets:36466 errors:0 dropped:0 overruns:0 carrier:0
		      collisions:0 txqueuelen:1000 
		      RX bytes:126727813 (120.8 MiB)  TX bytes:3112284 (2.9 MiB)


$ cat /etc/keepalived/keepalived.conf

	! Configuration File for keepalived

	global_defs {
	   notification_email {
		 liuwenxue@cfischina.com
	   }
	   notification_email_from liuwenxue@cfischina.com
	   smtp_server 192.168.200.1
	   smtp_connect_timeout 30
	   router_id Nginx
	}

	vrrp_script chk_nginx {
	   script "/etc/keepalived/check_nginx.sh"
	   interval 2
	   weight -5
	   fall 3
	   rise 2
	}

	vrrp_instance VI_1 {
		state MASTER
		interface eth1
		mcast_src_ip 192.168.0.86
		virtual_router_id 51
		priority 101
		advert_int 2
		authentication {
		    auth_type PASS
		    auth_pass 1111
		}
		virtual_ipaddress {
		    192.168.0.100
		}
		track_script {
		    chk_nginx 
		}
        #notify_master "/etc/keepalived/notify.sh master 192.168.0.100"
    	#notify_backup "/etc/keepalived/notify.sh backup 192.168.0.100"
    	#notify_fault "/etc/keepalived/notify.sh fault 192.168.0.100"
	}

$ cat /etc/keepalived/check_nginx.sh

	#!/bin/bash
	counter=$(ps -C nginx --no-heading|wc -l)
	if [ "${counter}" = "0" ]; then
		    sleep 2
		    counter=$(ps -C nginx --no-heading|wc -l)
		    if [ "${counter}" = "0" ]; then
		            service keepalived stop
		    fi
	fi

$ cat /etc/keepalived/notify.sh

	#!/bin/bash
	# Author: 
	# description: An example of notify script
	#
	contact='root@localhost'
	notify() {
		mailsubject="`hostname` to be $1: $2 floating"
		mailbody="`date '+%F %H:%M:%S'`: vrrp transition, `hostname` changed to be $1"
		echo $mailbody | mail -s "$mailsubject" $contact
	}
	case "$1" in
		master)
		    notify master $2
		    exit 0
		;;
		backup)
		    notify backup $2
		    exit 0
		;;
		fault)
		    notify fault $2
		    exit 0
		;;
		*)
		    echo 'Usage: `basename $0` {master|backup|fault}'
		    exit 1
		;;
	esac


SLAVE 测试
---------------------------------

$ ifconfig eth1
	eth1      Link encap:Ethernet  HWaddr 08:00:27:A8:EE:93  
		      inet addr:192.168.0.14  Bcast:192.168.0.255  Mask:255.255.255.0
		      inet6 addr: fe80::a00:27ff:fea8:ee93/64 Scope:Link
		      UP BROADCAST RUNNING MULTICAST  MTU:1500  Metric:1
		      RX packets:361434 errors:0 dropped:0 overruns:0 frame:0
		      TX packets:8512 errors:0 dropped:0 overruns:0 carrier:0
		      collisions:0 txqueuelen:1000 
		      RX bytes:42927489 (40.9 MiB)  TX bytes:535318 (522.7 KiB)


$ cat /etc/keepalived/keepalived.conf
	
	! Configuration File for keepalived

	global_defs {
	   notification_email {
		    liuwenxue@cfischina.com
	   }
	   notification_email_from liuwenxue@cfischina.com
	   smtp_server 192.168.200.1
	   smtp_connect_timeout 30
	   router_id Nginx
	}

	vrrp_script chk_nginx {
	   # script "killall -0 nginx"
	   script "/etc/keepalived/check_nginx.sh"
	   interval 2
	   weight -5
	   fall 3
	   rise 2
	}

	vrrp_instance VI_1 {
		state BACKUP
		interface eth1
		virtual_router_id 51
		mcast_src_ip 192.168.0.14
		priority 100
		advert_int 1
		authentication {
		    auth_type PASS
		    auth_pass 1111
		}
		virtual_ipaddress {
		    192.168.0.100
		}
		track_script {
		    chk_nginx
		}
        #notify_master "/etc/keepalived/notify.sh master 192.168.0.100"
    	#notify_backup "/etc/keepalived/notify.sh backup 192.168.0.100"
    	#notify_fault "/etc/keepalived/notify.sh fault 192.168.0.100"
	}


$ cat /etc/keepalived/check_nginx.sh 


	#!/bin/bash

	counter=$(ps -C nginx --no-heading|wc -l)
	if [ "${counter}" = "0" ]; then
		    #/usr/local/bin/nginx
		    #service nginx stop
		    sleep 2
		    counter=$(ps -C nginx --no-heading|wc -l)
		    if [ "${counter}" = "0" ]; then
		       #/etc/init.d/keepalived stop
		        service keepalived stop
		    fi
	fi

$ cat /etc/keepalived/notify.sh

	#!/bin/bash
	# Author: 
	# description: An example of notify script
	#
	contact='root@localhost'
	notify() {
		mailsubject="`hostname` to be $1: $2 floating"
		mailbody="`date '+%F %H:%M:%S'`: vrrp transition, `hostname` changed to be $1"
		echo $mailbody | mail -s "$mailsubject" $contact
	}
	case "$1" in
		master)
		    notify master $2
		    exit 0
		;;
		backup)
		    notify backup $2
		    exit 0
		;;
		fault)
		    notify fault $2
		    exit 0
		;;
		*)
		    echo 'Usage: `basename $0` {master|backup|fault}'
		    exit 1
		;;
	esac

验证
============================

MASTER
---------------------

$ service nginx start
$ service keepalived start

在新的终端

$ sudo tcpdump -i eth1 vrrp

	07:15:38.089918 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	07:15:40.091316 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	07:15:42.092725 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	07:15:44.094038 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	07:15:46.095177 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	07:15:48.096548 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20

在新的终端

$ sudo tail -f /var/log/messages

	Oct 30 07:15:02 web-server Keepalived[25527]: Starting Keepalived v1.2.13 (03/19,2015)
	Oct 30 07:15:02 web-server Keepalived[25528]: Starting Healthcheck child process, pid=25529
	Oct 30 07:15:02 web-server Keepalived[25528]: Starting VRRP child process, pid=25530
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP 10.0.2.15 added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP 192.168.0.86 added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP 192.168.2.10 added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP fe80::a00:27ff:fe4f:b806 added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP fe80::a00:27ff:fe6f:34f4 added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP fe80::a00:27ff:fe6b:195b added
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Registering Kernel netlink reflector
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Registering Kernel netlink command channel
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP 10.0.2.15 added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP 192.168.0.86 added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP 192.168.2.10 added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP fe80::a00:27ff:fe4f:b806 added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP fe80::a00:27ff:fe6f:34f4 added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Netlink reflector reports IP fe80::a00:27ff:fe6b:195b added
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Registering Kernel netlink reflector
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Opening file '/etc/keepalived/keepalived.conf'.
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Registering Kernel netlink command channel
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Configuration is using : 7837 Bytes
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Registering gratuitous ARP shared channel
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Opening file '/etc/keepalived/keepalived.conf'.
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Configuration is using : 65535 Bytes
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: Using LinkWatch kernel netlink reflector...
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: VRRP sockpool: [ifindex(3), proto(112), unicast(0), fd(10,11)]
	Oct 30 07:15:02 web-server Keepalived_healthcheckers[25529]: Using LinkWatch kernel netlink reflector...
	Oct 30 07:15:02 web-server Keepalived_vrrp[25530]: VRRP_Script(chk_nginx) succeeded
	Oct 30 07:15:04 web-server Keepalived_vrrp[25530]: VRRP_Instance(VI_1) Transition to MASTER STATE
	Oct 30 07:15:06 web-server Keepalived_vrrp[25530]: VRRP_Instance(VI_1) Entering MASTER STATE
	Oct 30 07:15:06 web-server Keepalived_vrrp[25530]: VRRP_Instance(VI_1) setting protocol VIPs.
	Oct 30 07:15:06 web-server Keepalived_vrrp[25530]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100
	Oct 30 07:15:06 web-server Keepalived_healthcheckers[25529]: Netlink reflector reports IP 192.168.0.100 added

BACKUP
---------------------

$ service nginx start
$ service keepalived start

在新的终端

$ sudo tcpdump -i eth1 vrrp


07:16:58.181460 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:00.182850 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:02.184554 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:04.186121 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:06.185243 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:08.187574 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:10.189484 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:12.189914 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
07:17:14.190994 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertis

在新的终端

$ sudo tail -f /var/log/messages

	Oct 30 07:16:43 web-client Keepalived[3851]: Starting Keepalived v1.2.13 (03/19,2015)
	Oct 30 07:16:43 web-client Keepalived[3852]: Starting Healthcheck child process, pid=3853
	Oct 30 07:16:43 web-client Keepalived[3852]: Starting VRRP child process, pid=3854
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP 10.0.2.15 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP 192.168.0.14 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP 192.168.2.11 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP fe80::a00:27ff:fe4f:b806 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP fe80::a00:27ff:fea8:ee93 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Netlink reflector reports IP fe80::a00:27ff:fefd:cfb2 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Registering Kernel netlink reflector
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Registering Kernel netlink command channel
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Registering gratuitous ARP shared channel
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Opening file '/etc/keepalived/keepalived.conf'.
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Configuration is using : 65535 Bytes
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: Using LinkWatch kernel netlink reflector...
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: VRRP_Instance(VI_1) Entering BACKUP STATE
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP 10.0.2.15 added
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP 192.168.0.14 added
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP 192.168.2.11 added
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: VRRP sockpool: [ifindex(3), proto(112), unicast(0), fd(10,11)]
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP fe80::a00:27ff:fe4f:b806 added
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP fe80::a00:27ff:fea8:ee93 added
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Netlink reflector reports IP fe80::a00:27ff:fefd:cfb2 added
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Registering Kernel netlink reflector
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Registering Kernel netlink command channel
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Opening file '/etc/keepalived/keepalived.conf'.
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Configuration is using : 7837 Bytes
	Oct 30 07:16:43 web-client Keepalived_healthcheckers[3853]: Using LinkWatch kernel netlink reflector...
	Oct 30 07:16:43 web-client Keepalived_vrrp[3854]: VRRP_Script(chk_nginx) succeeded
	Oct 30 07:16:44 web-client Keepalived_vrrp[3854]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 07:16:44 web-client Keepalived_vrrp[3854]: Sync instance needed on eth1 !!!
	Oct 30 07:16:46 web-client Keepalived_vrrp[3854]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 07:16:46 web-client Keepalived_vrrp[3854]: Sync instance needed on eth1 !!!


由上日志和网络抓包得知, MASTER 和 BACKUP 的 keepalived 和 nginx 启动成功


角色切断测试
============================

宕机测试
============================

通过关闭 MASTER 或 BACKUP 的 keepalived 来模拟宕机

1.  MASTER 关闭 keepalived, 保持 nginx , BACKUP 保持 nginx, keepalived 正常运行

$ sudo service keepalived stop

虚拟 IP 自动漂移到 192.168.0.14, 具体见如下分析

MASTER 和 BACKUP 网络抓包记录
----------------------------

$ sudo tcpdump -i eth1 vrrp

	05:56:30.306232 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	05:56:32.307883 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	05:56:34.309309 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	05:56:36.311171 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	05:56:38.312234 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	05:56:40.152948 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 0, authtype simple, intvl 2s, length 20
	05:56:40.763527 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	05:56:41.765179 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	05:56:42.767492 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	05:56:43.768883 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	05:56:44.769898 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20

MASTER keepalived 日志
----------------------------

	Oct 30 05:44:55 web-server Keepalived_healthcheckers[16962]: Netlink reflector reports IP 192.168.0.100 added
	Oct 30 05:44:55 web-server Keepalived_vrrp[16963]: VRRP_Script(chk_nginx) succeeded
	Oct 30 05:45:00 web-server Keepalived_vrrp[16963]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100
	Oct 30 05:54:08 web-server Keepalived_vrrp[16963]: Process [18397] didn't respond to SIGTERM
	Oct 30 05:56:40 web-server Keepalived[16961]: Stopping Keepalived v1.2.13 (03/19,2015)
	Oct 30 05:56:40 web-server Keepalived_vrrp[16963]: VRRP_Instance(VI_1) sending 0 priority
	Oct 30 05:56:40 web-server Keepalived_vrrp[16963]: VRRP_Instance(VI_1) removing protocol VIPs.
	Oct 30 05:56:40 web-server Keepalived_healthcheckers[16962]: Netlink reflector reports IP 192.168.0.100 removed

MASTER 虚拟 IP 
----------------------------

$ ip a

	3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
		link/ether 08:00:27:6f:34:f4 brd ff:ff:ff:ff:ff:ff
		inet 192.168.0.86/24 brd 192.168.0.255 scope global eth1
		inet6 fe80::a00:27ff:fe6f:34f4/64 scope link 
		   valid_lft forever preferred_lft forever


BACKUP keepalived 日志
----------------------------

$ sudo tail -f /var/log/messages

	Oct 30 05:56:38 web-client Keepalived_vrrp[3382]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 05:56:38 web-client Keepalived_vrrp[3382]: Sync instance needed on eth1 !!!
	Oct 30 05:56:40 web-client Keepalived_vrrp[3382]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 05:56:40 web-client Keepalived_vrrp[3382]: Sync instance needed on eth1 !!!
	Oct 30 05:56:40 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) Transition to MASTER STATE
	Oct 30 05:56:41 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) Entering MASTER STATE
	Oct 30 05:56:41 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) setting protocol VIPs.
	Oct 30 05:56:41 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100
	Oct 30 05:56:41 web-client Keepalived_healthcheckers[3380]: Netlink reflector reports IP 192.168.0.100 added
	Oct 30 05:56:46 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100
	Oct 30 05:56:54 web-client kernel: device eth1 left promiscuous mode
	Oct 30 05:58:15 web-client kernel: device eth1 entered promiscuous mode

BACKUP 虚拟 IP 
----------------------------

$ ip a

	3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
		link/ether 08:00:27:a8:ee:93 brd ff:ff:ff:ff:ff:ff
		inet 192.168.0.14/24 brd 192.168.0.255 scope global eth1
		inet 192.168.0.100/32 scope global eth1
		inet6 fe80::a00:27ff:fea8:ee93/64 scope link 
		   valid_lft forever preferred_lft forever


2.  MASTER 重启 keepalived, 保持 nginx , BACKUP 保持 nginx, keepalived 正常运行

此时, 并没有进行 ip 漂移. 

3.  MASTER 保持 keepalived nginx 正常运行 , BACKUP 关闭 keepalived, keepalived 正常运行

MASTER 和 BACKUP 网络抓包记录
----------------------------

	06:09:24.743023 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	06:09:25.744506 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	06:09:26.745645 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	06:09:27.747297 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	06:09:28.748731 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 100, authtype simple, intvl 1s, length 20
	06:09:28.834381 IP 192.168.0.14 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 0, authtype simple, intvl 1s, length 20
	06:09:30.836224 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	06:09:32.837531 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	06:09:34.837875 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20
	06:09:36.838398 IP 192.168.0.86 > vrrp.mcast.net: VRRPv2, Advertisement, vrid 51, prio 101, authtype simple, intvl 2s, length 20


MASTER keepalived 日志
----------------------------

	Oct 30 06:09:28 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) Dropping received VRRP packet...
	Oct 30 06:09:28 web-server Keepalived_vrrp[18900]: advertissement interval mismatch mine=2000000 rcved=1
	Oct 30 06:09:28 web-server Keepalived_vrrp[18900]: Sync instance needed on eth1 !!!
	Oct 30 06:09:28 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) Dropping received VRRP packet...
	Oct 30 06:09:30 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) Entering MASTER STATE
	Oct 30 06:09:30 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) setting protocol VIPs.
	Oct 30 06:09:30 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100
	Oct 30 06:09:30 web-server Keepalived_healthcheckers[18899]: Netlink reflector reports IP 192.168.0.100 added
	Oct 30 06:09:35 web-server Keepalived_vrrp[18900]: VRRP_Instance(VI_1) Sending gratuitous ARPs on eth1 for 192.168.0.100

MASTER 虚拟 IP 
----------------------------

	3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
		link/ether 08:00:27:6f:34:f4 brd ff:ff:ff:ff:ff:ff
		inet 192.168.0.86/24 brd 192.168.0.255 scope global eth1
		inet 192.168.0.100/32 scope global eth1
		inet6 fe80::a00:27ff:fe6f:34f4/64 scope link 
		   valid_lft forever preferred_lft forever


BACKUP keepalived 日志
----------------------------

$ sudo tail -f /var/log/messages

	Oct 30 05:56:54 web-client kernel: device eth1 left promiscuous mode
	Oct 30 05:58:15 web-client kernel: device eth1 entered promiscuous mode
	Oct 30 06:08:24 web-client Keepalived_vrrp[3382]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 06:08:24 web-client Keepalived_vrrp[3382]: Sync instance needed on eth1 !!!
	Oct 30 06:08:24 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) Dropping received VRRP packet...
	Oct 30 06:09:28 web-client Keepalived[3379]: Stopping Keepalived v1.2.13 (03/19,2015)
	Oct 30 06:09:28 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) sending 0 priority
	Oct 30 06:09:28 web-client Keepalived_vrrp[3382]: VRRP_Instance(VI_1) removing protocol VIPs.
	Oct 30 06:10:40 web-client kernel: device eth1 left promiscuous mode
	Oct 30 06:19:01 web-client kernel: device eth1 entered promiscuous mode

BACKUP 虚拟 IP 
----------------------------
$ ip a

	3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP qlen 1000
		link/ether 08:00:27:a8:ee:93 brd ff:ff:ff:ff:ff:ff
		inet 192.168.0.14/24 brd 192.168.0.255 scope global eth1
		inet6 fe80::a00:27ff:fea8:ee93/64 scope link 
		   valid_lft forever preferred_lft forever

4.  MASTER 保持 keepalived,nginx 正常运行, BACKUP 重启 keepalived, 保持 nginx 正常运行

此时, 并没有进行 ip 漂移.


应用 Crash 测试
============================

发现应用 Crash 的时候关闭 keepalived, 结果与宕机测试相同


问题
===========================

BACKUP 角色一直出现如下信息, 应该是期望的

	Oct 30 07:19:20 web-client Keepalived_vrrp[3854]: Sync instance needed on eth1 !!!
	Oct 30 07:19:22 web-client Keepalived_vrrp[3854]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 07:19:22 web-client Keepalived_vrrp[3854]: Sync instance needed on eth1 !!!
	Oct 30 07:19:24 web-client Keepalived_vrrp[3854]: advertissement interval mismatch mine=1000000 rcved=2
	Oct 30 07:19:24 web-client Keepalived_vrrp[3854]: Sync instance needed on eth1 !!!


参考
===========================

http://xxrenzhe.blog.51cto.com/4036116/1405571

附录
===========================

配置选项说明
--------------------------

global_defs

* notification\_email :  keepalived 在发生诸如切换操作时需要发送 email 通知地址, 后面的 smtp_server 相比也都知道是邮件服务器地址. 也可以通过其它方式报警, 毕竟邮件不是实时通知的.
* router_id :  机器标识, 通常可设为hostname. 故障发生时, 邮件通知会用到

vrrp_instance

* state :  指定instance(Initial)的初始状态, 就是说在配置好后, 这台服务器的初始状态就是这里指定的, 但这里指定的不算, 还是得要通过竞选通过优先级来确定. 如果这里设置为MASTER, 但如若他的优先级不及另外一台, 那么这台在发送通告时, 会发送自己的优先级, 另外一台发现优先级不如自己的高, 那么他会就回抢占为MASTER
* interface :  实例绑定的网卡, 因为在配置虚拟IP的时候必须是在已有的网卡上添加的
* mcast_src_ip :  发送多播数据包时的源IP地址, 这里注意了, 这里实际上就是在那个地址上发送VRRP通告, 这个非常重要, 一定要选择稳定的网卡端口来发送, 这里相当于heartbeat的心跳端口, 如果没有设置那么就用默认的绑定的网卡的IP, 也就是interface指定的IP地址
* virtual_router_id :  这里设置VRID, 这里非常重要, 相同的VRID为一个组, 他将决定多播的MAC地址
* priority :  设置本节点的优先级, 优先级高的为master
* advert_int :  检查间隔, 默认为1秒. 这就是VRRP的定时器, MASTER每隔这样一个时间间隔, 就会发送一个advertisement报文以通知组内其他路由器自己工作正常
* authentication :  定义认证方式和密码, 主从必须一样
* virtual_ipaddress :  这里设置的就是VIP, 也就是虚拟IP地址, 他随着state的变化而增加删除, 当state为master的时候就添加, 当state为backup的时候删除, 这里主要是有优先级来决定的, 和state设置的值没有多大关系, 这里可以设置多个IP地址
* track_script :  引用VRRP脚本, 即在 vrrp_script 部分指定的名字. 定期运行它们来改变优先级, 并最终引发主备切换. 

vrrp_script 告诉 keepalived 在什么情况下切换, 所以尤为重要. 可以有多个 vrrp_script

* script :  自己写的检测脚本. 也可以是一行命令如killall -0 nginx
* interval 2 :  每2s检测一次
* weight -5 :  检测失败（脚本返回非0）则优先级 -5
* fall 2 :  检测连续 2 次失败才算确定是真失败. 会用weight减少优先级（1-255之间）
* rise 1 :  检测 1 次成功就算成功. 但不修改优先级

这里要提示一下 script 一般有2种写法:

    通过脚本执行的返回结果, 改变优先级, keepalived 继续发送通告消息, backup 比较优先级再决定
    脚本里面检测到异常, 直接关闭 keepalived 进程, backup 机器接收不到 advertisement 会抢占IP

上文 vrrp_script 配置部分, killall -0 nginx 属于第 1 种情况, /etc/keepalived/check_nginx.sh 属于第 2 种情况(脚本中关闭keepalived).


通过shell脚本判断, 异常时 exit 1, 正常退出 exit 0, 然后 keepalived 根据动态调整的 vrrp_instance 优先级选举决定是
否抢占VIP:

    如果脚本执行结果为0, 并且 weight 配置的值大于0, 则优先级相应的增加
    如果脚本执行结果非0, 并且 weight 配置的值小于0, 则优先级相应的减少

其他情况, 原本配置的优先级不变, 即配置文件中 priority 对应的值.

注意:

* 优先级不会不断的提高或者降低
* 可以编写多个检测脚本并为每个检测脚本设置不同的weight（在配置中列出就行）
* 不管提高优先级还是降低优先级, 最终优先级的范围是在[1,254], 不会出现优先级小于等于0或者优先级大于等于255的情况
* 在MASTER节点的 vrrp_instance 中 配置 nopreempt , 当它异常恢复后, 即使它 prio 更高也不会抢占, 这样可以避免正常情况下做无谓的切换

MASTER 和 BACKUP 节点的优先级如何调整?
--------------------------------------

首先, 每个节点有一个初始优先级, 由配置文件中的 priority 配置项指定, MASTER 节点的 priority 应比 BAKCUP 高.
运行过程中 keepalived 根据 vrrp_script 的 weight 设定, 增加或减小节点优先级. 规则如下:

vrrp_script 里的 script 返回值为 0 时认为检测成功, 其它值都会当成检测失败;

1. 当 weight > 0 时, 脚本检测成功时此 weight 会加到priority上, 检测失败时不加;

* 主失败: 主 priority < 从 priority + weight 时会切换.
* 主成功: 主 priority + weight > 从 priority + weight 时，主依然为主

2. 当 weight < 0 时, 脚本检测成功时此 weight 不影响priority, 检测失败时 priority – abs(weight)

* 主失败: 主 priority – abs(weight) < 从priority 时会切换主从
* 主成功: 主 priority > 从priority 主依然为主

3. 当两个节点的优先级相同时, 以节点发送 VRRP 通告的 IP 作为比较对象, IP 较大者为 MASTER.

所以 priority 和 weight 值的设定应遵循:

    abs(MASTER priority - BAKCUP priority) < abs(weight).

另外, 当网络中不支持多播(例如某些云环境), 或者出现网络分区的情况, keepalived BACKUP 节点收不到 MASTER 的 VRRP 通告, 就会出现脑裂
(split brain)现象, 此时集群中会存在多个MASTER节点.
