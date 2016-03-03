
###RIP

RIPv1
RIPv2


###OSPF

* 30分钟或路由改变
* LSA(link state advertise)数据库
* Djk 算法
* 分多个区, 主干区只有一个


###BGP


* iBGP
* eBGP
* AS

如何解决回路: AS_PATH

###多播

节省带宽

223.0.0.0~249.255.255.255

* 稀疏模式 稠密模式

###逆向路由多播(Reserve Path Multicasting)

* 只扩散最短路径
* 每个多播地址源组成源特定多播树(Source-specific multicast tree)
* 剪枝(Prune Message)
* 嫁接(Graft Message)

DVMRP(Distance Vector Multicast Routing Protocol) : RIP 协议
PIM-DM(Protocol Independent Multicast-Dense Mode) : 协议无关

###IGMP(Internet Group Management Protocol)

查询直连组成员

* 三次 10s

