


##MAC 地址
MAC（Medium/MediaAccess Control,介质访问控制） MAC 地址是收录在 NetworkInterfaceCard(网卡,NIC) 里的.
MAC地址,也叫硬件地址,是由 48 bit长（6byte，1byte=8bits）的16进制的数字组成。其中，前三个字节是由 
IEEE 的注册管理机构 RA 负责给不同厂家分配的代码(高位24位)，也称为“编制上唯一的标识符”（Organizationally Unique Identifier)，
后三个字节(低位24位)由各厂家自行指派给生产的适配器接口，称为扩展标识符（唯一性）。

ff:ff:ff:ff:ff:ff则作为广播位址。
01:xx:xx:xx:xx:xx是多播地址，01:00:5e:xx:xx:xx是IPv4多播地址。

其中第 1 字节的第 8 Bit（如图中00-50-BA-...对应的 0000000-01010000-10111010-...，加粗字体的Bit）
标识这个地址是组播地址还是单播地址。这是由以太网的传输协议高字节先传，但每一字节内低位先传的特性
所决定的，见 IEEE 802.3 3.2.3 Address fields：

    “The first bit (LSB) shall be used in the Destination Address field as an address type designation
    bit to identify the Destination Address either as an individual or as a group address. If this bit
    is 0, it shall indicate that the address field contains an individual address. If this bit is 1, it
    shall indicate that the address field contains a group address that identifies none, one or more,
    or all of the stations connected to the LAN. In the Source Address field, the first bit is reserved
    and set to 0.”。

事实上这传输的顺序为 000000000000101001011101...“The first bit (LSB)”即是前言的第 8 Bit。



###IP 地址与 MAC 地址区别

IP地址和MAC地址相同点是它们都唯一，不同的特点主要有：

* 对于网络上的某一设备，如一台计算机或一台路由器，其 IP 地址可变（但必须唯一），而 MAC 地址是不可变。
我们可以根据需要给一台主机指定任意的 IP 地址，如我们可以给局域网上的某台计算机分配 IP 地址为 192.168.0.112 ，
也可以将它改成 192.168.0.200。而任一网络设备（如网卡，路由器）一旦生产出来以后，其 MAC 地址不可由本地连接内
的配置进行修改(实际是可以修改的,如果是虚拟机,那么 MAC 就更随意了)。

* 长度不同。IP地址为32位，MAC地址为48位。

* 分配依据不同。IP 地址的分配是基于网络拓扑，MAC 地址的分配是基于制造商。

* 寻址协议层不同。IP 地址应用于 OSI 第三层，即网络层，而 MAC 地址应用在 OSI 第二层，即数据链路层。 数据链路层
协议可以使数据从一个节点传递到相同链路的另一个节点上（通过MAC地址），而网络层协议使数据可以从一个网络传递到另
一个网络上（ARP根据目的IP地址，找到中间节点的MAC地址，通过中间节点传送，从而最终到达目的网络）


[Ethernet](http://en.wikipedia.org/wiki/Ethernet_frame)
[VLAN](http://en.wikipedia.org/wiki/IEEE_802.1Q)





#附录

[多播，单播，广播](http://bradhedlund.com/2007/11/21/identifying-ethernet-multicast/)



Just like there are 3 different Ethernet header types, there are also 3 different types of Ethernet addresses:

    Unicast
    Broadcast
    Multicast

A unicast frame contains the unique MAC address of the destination receiver. A broadcast frame contains all binary 1’s as the destination address (FFFF.FFFF.FFFF). A multicast frame contains the unique multicast MAC address of an application, protocol, or datastream.

Why is it important to be able to distinguish between the 3 types of Ethernet address type? In an Ethernet switch, each of the three are treated differently.

A unicast addressed frame is only sent out the specific port leading to the receiver. A broadcast frame is flooded out all ports. A multicast addressed frame is either flooded out all ports (if no multicast optimization is configured) or sent out only the ports interested in receiving the traffic.

It’s easy for the ethernet switch to identify a broadcast frame because there is only one universally known broadcast address, FFFF.FFFF.FFFF (all binary ones). Therefore it is easy for the switch to know these frames need to be flooded out all ports.

However, given there is such a wide variety of possible unicast and multicast Ethernet addresses, how does the switch distinguish between the two? It is important to properly make the distinction because the the two are handled so differently within the switch (a unicast frames goes to only one port, a multicast frame goes to some or all ports).

Does the switch have a database of all possible multicast MAC addresses it references for each frame? No, that would be inefficient.

How this is done efficiently is there is one specific bit in a Ethernet MAC address that signifies if the frame is unicast or multicast. The switch need only look at this one bit to make the distinction.

The IEEE has specified that the most significant bit of the most significant byte be used for this purpose. If it‘s a 1, that means multicast, 0 means unicast. The most significant byte is the left most byte in the address, and the most significant bit is the right most bit of the byte (this is counter intuitive to most binary implementations where the left most bit usually labeled most significant). 

      Most Significant                                             Least Significant                                                                  
       | 1st Byte  |  2nd Byte   |  3rd Byte  |  4th Byte  |  5th Byte  |  6th Byte  |   
       |          OUI                     |           Vendor-Assigned          |

                           U/L I/G
      1st Byte |0|1|2|3|4|5|6|7|
              least           most 
            significant    significant
               bit            bit


Some quick examples of mulicast MAC addresses:

    0100.CCCC.DDDD
    0900.AAAA.BBBB

Some quick examples of unicast MAC addresses:

    0001.4455.6677
    0800.2233.4455

Each of the bolded numbers represents a 1 or 0 present in the most significant bit of the most significant byte.

This bit is also referred to as the Individual/Group bit.

From the perspective of an Ethernet hub device, none of this matters, as all frames are flooded out all ports regardless of their address being unicast, broadcast, or multicast. It makes no sense for an Ethernet hub to distinguish between the three.



###TRUNK

在网络的分层结构和宽带的合理分配方面，TRUNK 被解释为“端口汇聚”，是带宽扩展和链路备份的一个重要途径。
TRUNK 把多个物理端口捆绑在一起当作一个逻辑端口使用，可以把多组端口的宽带叠加起来使用。TRUNK 技术可以
实现 TRUNK 内部多条链路互为备份的功能，即当一条链路出现故障时，不影响其他链路的工作，同时多链路之间还
能实现流量均衡，就像我们熟悉的打印机池和 MODEM 池一样。

 但是在最普遍的路由与交换领域，VLAN 的端口聚合也有的叫 TRUNK，不过大多数都叫 TRUNKING，如 CISCO 公司。
 所谓的 TRUNKING 是用来在不同的交换机之间进行连接，以保证在跨越多个交换机上建立的同一个 VLAN 的成员能
 够相互通讯。其中交换机之间互联用的端口就称为 TRUNK 端口。与一般的交换机的级联不同，TRUNKING 是基于 OSI
 第二层数据链路层（DataLinkLayer)TRUNKING 技术，如果你在 2 个交换机上分别划分了多个 VLAN（VLAN也是基于
 Layer2的），那么分别在两个交换机上的 VLAN10 和 VLAN20 的各自的成员如果要互通，就需要在 A 交换机上设为
 VLAN10 的端口中取一个和交换机 B 上设为 VLAN10 的某个端口作级联连接。VLAN20 也是这样。那么如果交换机上
 划了10个VLAN就需要分别连 10 条线作级联，端口效率就太低了。

 当交换机支持 TRUNKING 的时候，事情就简单了，只需要 2 个交换机之间有一条级联线，并将对应的端口设置为 Trunk，
 这条线路就可以承载交换机上所有 VLAN 的信息。这样的话，就算交换机上设了上百个个 VLAN 也只用1个端口就解决了。
 当一个 VLAN 跨过不同的交换机时，在同一 VLAN 上但是却是在不同的交换机上的计算机进行通讯时需要使用 Trunk。
 Trunk技术使得一条物理线路可以传送多个 VLAN 的数据。交换机从属于某一 VLAN（例如VLAN 3）的端口接收到数据，
 在 Trunk 链路上进行传输前，会加上一个标记，表明该数据是 VLAN 3 的；到了对方交换机，交换机会把该标记去掉，
 只发送到属于 VLAN 3 的端口如果是不同台的交换机上相同 id 的 vlan 要相互通信，那么可以通过共享的 trunk 端口
 就可以实现，如果是同一台上不同 id 的 vlan /不同台不同 id 的 vlan 它们之间要相互通信，需要通过第三方的路由
 来实现；

 trunk 在路由和交换中 VLAN 的端口聚合也有的叫 TRUNK.只需要 2 个交换机之间有一条级联线，并将对应的端口设置为
 Trunk，这条线路就可以承载交换机上所有 VLAN 的信息.现在有些交换机不用设置 Trunk,只要两个交换相连,就会成为 TRUNK.

 总结一下，我们提到的是两种不同的东西：VLAN Trunk和Link Trunk。

 VLAN Trunk是指一个链路（有可能是Link Trunk）上可以同时传送多个VLAN的流量，一般可以通过GVRP、VTP或者手工来配置。

 Link Trunk标准里称为Link Aggregation，即满足某种要求的一组链路组合起来对上层表现为一条链路，即拥有一个虚拟
 MAC 地址和流量调度能力（一般根据 SIP、DIP 等等条件），在一定条件下增加了带宽。同样，可以提供手工（static）或者
 LACP协议动态配置。至于 enable、disable 应该是指是否启用该特性。

 Lacp

 lacp的话是一种链路动态汇聚的协议,如果说你混淆的话就是把 lacp 和 trunk 的另一个概念(端口汇聚)混淆了.而他们接近
 的用途:实现内部多条链路互为备份的功能，即当一条链路出现故障时，不影响其他链路的工作，同时多链路之间还能实现流量均衡.

 1) 在带宽比较紧张的情况下，可以通过逻辑聚合可以扩展带宽到原链路的n倍
 2) 在需要对链路进行动态备份的情况下，可以通过配置链路聚合实现同一聚合组各个成员端口之间彼此动态备份

 而聚合则有很多解释.端口聚合.或者路由聚合.

