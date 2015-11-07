话说Debian系的网卡配置跟Redhat系很不一样， Redhat是放在/etc/sysconfig/network-scripts目录下面的一大堆文件里面，要修改？你一个一个文件来过吧。 Debian系的则是存在/etc/network/interfaces文件里面，无论有多少块网卡，统统扔在这个文件里。下面就来看一下这个文件的内容。
首先，一个基本的配置大概是下面这个样子：

```
        auto lo
        iface  lo  inet  loopback
        # The primary network      interface
        auto   eth0
        iface  eth0  inet static   
        address         192.168.0.42 
        network         192.168.0.0 
        netmask        255.255.255.0 
        broadcast      192.168.0.255 
        gateway        192.168.0.1
```

上面的配置中，
第1行跟第5行说明lo接口跟eth0接口会在系统启动时被自动配置；
第2行将lo接口设置为一个本地回环（loopback）地址；
第6行指出eth0接口具有一个静态的（static）IP配置；
第7行-第11行分别设置eth0接口的ip、网络号、掩码、广播地址和网关。

再来看一个更复杂点的：

```
        auto  eth0
        iface  eth0  inet  static 
        address     192.168.1.42 
        network      192.168.1.0 
        netmask     255.255.255.128 
        broadcast   192.168.1.0  
        up  route  add   -net 192.168.1.128 netmask  255.255.255.128  gw  192.168.1.2
        up  route  add   default   gw  192.168.1.200  
        down route  del  default  gw  192.168.1.200  
        down route  del  -net  192.168.1.128  netmask  255.255.255.128  gw  192.168.1.2
```

这次，有了一个复杂一些的掩码，和一个比较奇怪的广播地址。还有就是增加的接口启用、禁用时的路由设置；
第7行和8行配置的左右是在接口启用的时候，添加一条静态路由和一个缺省路由；
第9行和10行会在接口禁用的时候，删掉这两条路由配置。
至于配置路由的写法，仔细看，它就是route命令嘛。
继续，下面是一个物理网卡上多个接口的配置方法：

```
        auto  eth0
        eth0:1
        iface  eth0  inet   static
        address        192.168.0.100
        network        192.168.0.0
        netmask       255.255.255.0
        broadcast     192.168.0.255
        gateway       192.168.0.1 
        iface  eth0:1 inet static  
        address        192.168.0.200
        network        192.168.0.0
        netmask       255.255.255.0
```

8行到11行在eth0上配置了另外一个地址，这种配置方法在配置一块网卡多个地址的时候很常见：有几个地址就配置几个接口。冒号后面的数字可以随便写的，只要几个配置的名字不重复就可以。
下面是 pre-up 和 post-down 命令时间。这是一组命令（pre-up、up、post-up、pre-down、down、post-down），分别定义在对应的时刻需要执行的命令。

```        
        auto eth0
        iface  eth0  inet dhcp 
        pre-up  [-f  /etc/network/local-network-ok]
```        
第3行会在激活eth0之前检查  /etc/network/local-network-ok 文件是否存在，如果不存在，则不会激活 eth0。
再更进一步的例子：

```
        auto  eth0  eth1
        iface eth0  inet   static
        address      192.168.42.1
        netmask     255.255.255.0 
        pre-up    /path/to/check-mac-address.sh   eth0  11:22:33:44:55:66
        pre-up    /usr/local/sbin/enable-masq
        iface  eth1  inet  dhcp
        pre-up    /path/to/check-mac-address.sh   eth1  AA:BB:CC:DD:EE:FF
        pre-up    /usr/local/sbin/firewall
```
        
第5行和第8行中，check-mac-address.sh    放在    /usr/share/doc/ifupdown/examples/ 目录中，使用的时候需要给它加上可执行权限。这两行命令会检测两块网卡的MAC地址是否为 11:22:33:44:55:66 和 AA:BB:CC:DD:EE:FF，如果正确，则启用网卡。如果MAC地址错误，就不会启用这两块网卡。
第6行和第9行是假定在这两块网卡上分别执行的命令，你可以把它们替换成你想要的任何玩意 ：）
手册上说，这种方法主要是用来检测两块网卡的MAC地址交换（If their MAC addresses get swapped），其实就是两块网卡名互换了，这种情况在 debian 系统上再常见不过了， 主要是因为内核识别网卡的顺序发生了变化。（更新： 2013-05-19 自从有了udev，这种情况应该比较少发生了。）
这个问题可以用下面的这种方法来避免。

```
        auto eth0  eth1
        mapping  eth0  eth1  
        script  /path/to/get-mac-address.sh  map  11:22:33:44:55:66  lan  map   AA:BB:CC:DD:EE:FF  internet  
        iface  lan  inet  static  
        address     192.168.42.1
        netmask    255.255.255.0
        pre-up    /usr/local/sbin/enable-masq$IFACE
        iface  internet  inet  dhcp
         pre-up     /usr/local/sbin/firewall$IFACE
```

第3行中的 get-mac-address.sh 也在 /usr/share/doc/ifupdown/examples/ 目录里，也同样要加可执行权限。这个脚本的作用，就是获得每块网卡的MAC地址。
这段配置首先配置了两个逻辑接口（这个名词的定义请参见[1]）lan和internet，然后根据网卡的MAC地址，将逻辑接口映射（mapped）到物理接口上去。
再来看下面这段配置：

```
        auto  eth0
        iface  eth0  inet  manual  up     
        ifconfig  $IFACE  0.0.0.0  up   
        up   /usr/local/bin/myconfigscript  
        down ifconfig  $IFACE  down
```

这段配置只是启用一个网卡，但是 ifupdown 不对这个网卡设置任何 ip，而是由外部程序来设置ip。
最后一段配置，这段配置启用了网卡的混杂模式，用来当监听接口。

```
	auto  eth0 
	iface  eth0  inet  manual  
	up ifconfig  $IFACE  0.0.0.0  up  
	up ip  link  set  $IFACE  promiscon  
	down ip  link  set  $IFACE promisc  off  
	down  ifconfig  $IFACE  down
```

####虚拟 IP

如何让一个网卡可以有多个 IP, 虚拟 IP　应运而生

    auto   eth0
    iface  eth0  inet static
    address        192.168.0.42
    network        192.168.0.0
    netmask        255.255.255.0
    broadcast      192.168.0.255
    gateway        192.168.0.1

    iface  eth0:1 inet static
    address        192.168.1.42
    network        192.168.1.0
    netmask        255.255.255.0
    broadcast      192.168.2.255
    gateway        192.168.1.1

    iface  eth0:2 inet static
    address        192.168.2.42
    network        192.168.2.0
    netmask        255.255.255.0
    broadcast      192.168.2.255
    gateway        192.168.2.1

###Server版本 与 Desktop 版本

在 Ubuntu Server 版本中, 因为只存有命令行模式, 所以要想进行网络参数设置, 只能通过修改配置文件 /etc/network/interfaces.

在 Desktop 版本中，除了可以修改 /etc/network/interfaces 来进行配置以外; 还可以直接在 network-manager 中配置. 通过 interfaces
修改的方法参照 Server 版本. 如果修改了 interfaces, 又配置了 network-manager(简称nm), 你就会发现出现了一些莫名其妙的问题:

interfaces 和 nm 中的网络设置不一样, 系统实际的 IP 是哪个? 有时候莫名其妙的, 界面右上角的网络连接图标就丢失了.

明明在 nm 中配置了正确的网络设置, 为什么就上不了网呢?

在 /etc/network/interface 配置的网络, 刚开始好好的, 一旦浏览器访问外网, ip 就变了.

其实，我们要知道 interfaces 和 nm 之间的关系, 这些问题就不难解释了.

当系统内无第三方网络管理工具（如 nm）时, 系统默认使用 interfaces 文件内的参数进行网络配置.

当系统内安装了 nm 之后, nm 默认接管了系统的网络配置, 使用 nm 自己的网络配置参数来进行配置.

但若用户在安装 nm 之后（Desktop版本默认安装了nm）, 自己又手动修改了 interfaces 文件, 那 nm 就自动停止对系统网络的管理,
系统改使用 interfaces 文件内的参数进行网络配置. 此时, 再去修改 nm 内的参数, 不影响系统实际的网络配置. 若要让 nm 内的配
置生效，必须重新启用nm 接管系统的网络配置

现在知道了两者之间的工作关系, 再看上面的三个问题:

* 如果 nm 没有接管, 系统实际的 IP 设置以 interfaces 中的为准. 反之, 以 nm 中的为准.
* 当 nm 停止接管的时候, 网络连接图标就丢失了.

同样是接管的问题. 如果用户希望在 Desktop 版本中, 直接使用 interfaces 进行网络配置, 那最好停止 network-manager. network-manager 重新接管
如果在出现上述问题之后, 希望能继续使用 nm 来进行网络配置, 则需要进行如下操作：

    sudo service network-manager  stop
    sudo rm/var/lib/NetworkManager/NetworkManager.state
    sudo gedit /etc/NetworkManager/nm-system-settings.conf

    ## 里面有一行：managed=true
    ## 如果你手工改过 /etc/network/interfaces , nm 会自己把这行改成: managed=false
    ## 将 false 修改成 true

    sudo service network-manager start

###ubuntu 14.04 重新配置网卡

在 ubuntu 14.04 运行

    service networking stop
    service networking start

你会发现已经不起作用了, 在 14.04 采用 ifup 和 ifdown 命令来重启网络接口(eth0, eth1, wlan0)
这个命令会加载　/etc/networking/interface 中对应接口的配置

如果你　ifdown 或　ifup 命令出错，如　

    ifdown: interface eth0 not configured

编辑　/run/network/ifstate 文件，增加　eth0=eth0, 重新运行命令就没有问题了

更多见 man ifdown

###hack

    sudo strace -e open ifup eth0
    sh -x `which ifup` eth0

###参考
[1](debian参考手册)
[2](http://unix.stackexchange.com/questions/50602/cant-ifdown-eth0-main-interface)
[3](http://gfrog.net/2008/01/config-file-in-debian-interfaces-1)
