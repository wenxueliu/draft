
##

nmcli 是一个非常丰富和灵活的命令行工具。nmcli使用的情况有：

    设备 – 正在使用的网络接口
    连接 – 一组配置设置，对于一个单一的设备可以有多个连接，可以在连接之间切换。

找出有多少连接服务于多少设备

    [root@localhost ~]# nmcli connection show

得到特定连接的详情

    [root@localhost ~]# nmcli connection show eno1

示例输出：



得到网络设备状态

    [root@localhost ~]# nmcli device status

     DEVICE TYPE STATE CONNECTION
    eno16777736 ethernet connected eno1
    lo loopback unmanaged --

使用“dhcp”创建新的连接

    [root@localhost ~]# nmcli connection add con-name "dhcp" type ethernet ifname eno16777736


这里，

    connection add – 添加新的连接
    con-name – 连接名
    type – 设备类型
    ifname – 接口名

这个命令会使用dhcp协议添加连接

示例输出：

    Connection 'dhcp' (163a6822-cd50-4d23-bb42-8b774aeab9cb) successfully added.

不通过dhcp分配IP，使用“static”添加地址

    [root@localhost ~]# nmcli connection add con-name "static" ifname eno16777736 autoconnect no type ethernet ip4 192.168.1.240 gw4 192.168.1.1

示例输出：

    Connection 'static' (8e69d847-03d7-47c7-8623-bb112f5cc842) successfully added.

更新连接：

    [root@localhost ~]# nmcli connection up eno1

再检查一遍，ip地址是否已经改变

    [root@localhost ~]# ip addr show

添加DNS设置到静态连接中

    [root@localhost ~]# nmcli connection modify "static" ipv4.dns 202.131.124.4

添加更多的DNS

    [root@localhost ~]# nmcli connection modify "static" +ipv4.dns 8.8.8.8

	注意：要使用额外的+符号，并且要是+ipv4.dns，而不是ip4.dns。
添加一个额外的ip地址

    [root@localhost ~]# nmcli connection modify "static" +ipv4.addresses 192.168.200.1/24

使用命令刷新设置：

    [root@localhost ~]# nmcli connection up eno1




参考

http://www.unixmen.com/
