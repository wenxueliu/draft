

##SPB 801.2aq

##VLB

##ECMP

###特点

* 负载均衡
* 故障容忍
* 带宽聚合
* 快速重路由


###问题:

* 不同路径的 MTU 不同
* 不同路径的延迟不同
* 包的分片
* 调试更加困难

###实现多链路的方案

考虑因素

* 延迟
* 流量均衡



##MLAG

有数量的限制
非标准协议

##LACP



##ECMP

###L2

TRILL & Shortest Path Bridging



###L3

##TRILL


##IRF (H3C)


##SDN

通过 sFlow 监控流量, 找出不同链路的流量信息, 控制在进行多链路转发的时候, 根据当前带宽来调整流的走向.



[sFlow vs netflow](http://blog.sflow.com/2012/05/software-defined-networking.html)


[The Nature of Datacenter Traffic: Measurement & Analysis](http://research.microsoft.com/en-us/UM/people/srikanth/data/imc09_dcTraffic.pdf)
展示了数据中心的流 50% 小于 1 sec，而且消耗的带宽很小, 而消耗流量的大户都是持续
10 ~ 1000 秒的流.

##参考

* [RFC2991](https://tools.ietf.org/html/rfc2991)
* [RFC2992](https://tools.ietf.org/html/rfc2992)
https://tools.ietf.org/html/draft-ietf-opsawg-large-flow-load-balancing-15

* Yu Li and Deng Pan Florida International University Miami, FL [OpenFlow based Load Balancing for Fat-Tree Networks with Multipath Support]
