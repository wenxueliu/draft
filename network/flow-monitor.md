监控指标

    延迟（Latency）
    丢包率（Packet Loss）
    吞吐量（Throughput）
    链路使用率（Link Utilization）
    可用性（Availability）

测量手段

    主动 vs 被动
    单点 vs 多点
    网络层 vs 应用层
    镜像 vs 采样
    主机端 vs 交换节点

流量抓取协议

镜像/SPAN

 把被监控端口的流量复制一份，发送到特定目的端口。某些硬件交换机支持，OpenvSwitch 支持类似的 Mirror 功能。

分为两类：

    本地 SPAN：被监控端口和目的端口在同一交换机。
    远端 SPAN：被监控端口和目的端口在不同交换机。

被监控的流量从方向上可以为：

    进入流量：支持多个端口或指定 VLAN。
    出去流量：一个端口。

###流量统计协议

####SNMP

[Simple Network Management Protocol](https://www.ietf.org/rfc/rfc1157.txt)，IETF 标准，从路由器内存（MIB 库，管理信息数据库）中定期获取简单 IP 层统计信息，同时支持对设备进行管理。对设备有负担。

####RMON

[Remote Network MONitoring](https://tools.ietf.org/html/rfc3577)，IETF 标准，查询网络设备的 MIB 库。对设备有负担。

####sFlow

[sampled flow](http://localhost:51004/view/sFlow.org)。sFlow 是基于采样（sampling）的流量抓取工具，由 inMon 公司推出，交换机上使用较多。大部分硬件交换机中内置专用芯片支持，OpenvSwitch 支持。

sFlow 支持获取采样数据包的任何数量的字节，由内置 agent 封装为 UDP 包后发给采集器，默认端口为 6343。采集器（或分析器）可以根据这些数据包进行进一步的汇总和统计。sFlow 最大的优点是降低对设备的资源压力，扩展性好。

采样方法包括基于流的和基于时间的。

支持 sFlow 的设备列表可以参考：http://www.sflow.org/products/network.php。

####NetFlow

 Cisco 推出的基于采样的流统计标准，目的是统计每条流的信息，路由器上使用较多。在 NetFlow 技术的演进过程中，Cisco 一共开发出了 V1、V5、V7、V8 和 V9 等 5 个主要的实用版本。

NetFlow 支持采样或全部流量（CPU 占用高）的统计，本地采集到 cache 中进行统计，当流结束时（或超时，或指定时间间隔）以相应格式封装为 UDP 包上报记录并清除本地 cache，采集器典型端口为 2055。大部分设备支持的最低刷新 cache 超时为 60 秒。

定义一条流经典的考虑如下 7 个域：

    源 IP 地址；
    目标 IP 地址；
    源端口号；
    目标端口号；
    三层协议类型；
    服务类型（TOS）字节；
    网络设备输入或输出的逻辑网络端口（iflndex）。

Cisco Flexible NetFlow 协议号称支持用户选择自定义的域来定义流。

对于每条流可以记录其传送方向和目的地等流向特性，统计其起始和结束时间、服务类型、包含的数据包数量和字节数量等流量信息。

典型的一条流记录的格式，例如

 源地址 | 目的地址 | 源自治域 | 目的自治域 | 流入接口号 | 流出接口号 | 协议源端口 | 协议目的端口 | 协议类型 | 包数量 | 字节数 | 流数量。

 例如（经 nfdump 转化）：

Date flow start          Duration Proto   Src IP Addr:Port      Dst IP Addr:Port     Packets    Bytes Flows
 2010-09-01 00:00:00.459     0.000 UDP     127.0.0.1:24920   ->  192.168.0.1:22126        1       46     1
 2010-09-01 00:00:00.363     0.000 UDP     192.168.0.1:22126 ->  127.0.0.1:24920          1       80     1

####IPFIX


 IP Flow Information Export，IETF 推出的基于采样的流统计标准，源自 Cisco 的 NetFlow v9 标准。

定义一个流也考虑 NetFlow 类似的 7 个域。

每条流记录特征信息，包括：

    时间戳
    网包数
    网包平均大小
    总字节数
    流开始时间
    流结束时间

####OpenFlow flow statistics

统计流量信息。

####其他协议

类似协议还包括 Juniper 的 J-Flow/cflowd（类似 sFlow）、HP 的 Extended RMON 等、Ericsson 的 Rflow、Citrix 的 AppFlow。

###流量采集和分析工具

####inMon 自家的侧重 sFlow 的

* [Traffic Sentinel](http://www.inmon.com/products/trafficsentinel.php)：提供大而全的流量性能分析和管控，包括网络、存储、计算热点等。支持主流的网络监控协议。
* [sFlowTrend](http://www.inmon.com/products/sFlowTrend.php)：免费的 sFlow 流量采集，提供端口统计功能。
* [sFlowTrend Pro](http://www.inmon.com/products/sFlowTrend-Pro.php)：增加存储功能，可以查看历史数据。
* [sFlow-RT](http://www.inmon.com/products/sFlow-RT.php)：支持 sflow 和 SDN 控制器功能，实时 sflow 分析，提供负载均衡和 DDoS 检测等。

更多工具可以参考 http://www.sflow.org/products/collectors.php


####ntopng

 开源产品，原先的版本叫 ntop，定位于流量分析和问题定位。

ntopng 以网页形式显示流量统计信息，支持流量实时汇总和监控。

####NetFlow Analyzer

闭源产品。支持 NetFlow, sFlow, JFLow 等格式 flow 的收集器和分析引擎整合。

####Solarwinds NetFlow Traffic Analyzer

solarwinds 的产品，基于 Windows .Net+SQL Server，支持 NetFlow, sFlow, JFLow 等格式，图形界面，支持带宽统计、应用类型统计、

####flowviewer

 对 NetFlow/IPFix 的数据分析工具，提供 Web 界面。http://sourceforge.net/projects/flowviewer

####nfdump

 支持 NetFlow，提供一系列命令行工具，提供基于地址、端口等的流量信息统计。

开源产品，项目地址为 http://nfdump.sourceforge.net/。

####nfsen

 为 nfdump 提供的 Web 前端。

开源产品，项目地址为 http://nfsen.sourceforge.net/。

##参考

http://blog.csdn.net/yeasy/article/details/43114809
