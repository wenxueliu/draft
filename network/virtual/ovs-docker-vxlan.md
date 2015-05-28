目前docker主要应用于单机环境，使用网桥模式，但如果想把多台主机网络互相，让多台主机内部的
container 互相通信，就得使用其他的软件来帮忙，可以使用 Weave、Kubernetes、Flannel、SocketPlane
或者 openvswitch 等，我这里就使用 openvswitch 来介绍 docker 多台主机网络互通。

先看一个使用 openvswitch 连接的架构图，连接的方式是 vxlan

!(ovs-docker_1.jpg)[]

说明：

这里有2台主机，分别是 NODEA 与 NODEB，系统是 centos7，内核是3.18（默认centos7内核是3.10，
但想使用vxlan，所以得升级，参考http://dl528888.blog.51cto.com/2382721/1609850）

docker是 1.3.2 版本，存储引擎是devicemapper。

每台主机里都有 2 个网桥 ovs1 与 ovs2，ovs1 是管理网络，连接内网网卡 em1，ovs2 是数据网络，
docker 测试机都连接这个 ovs2，并且 container 创建的时候网络都是 none，使用 pipework 指定固定 ip。

然后2台主机使用vxlan连接网络。

重要：

我个人认为使用这个模式并且指定固定ip，适用于的环境主要是给研发或者个人的测试模式，如果是集群环境，
没必要指定固定ip（我这里的集群就没有使用固定ip，使用动态ip，效果很好，后续给大家介绍集群）。

下面是部署方法

##安装 docker

###Ubuntu 14.04

    $ sudo add-apt-repository ppa:docker-maint/testing
    $ sudo apt-get update
    $ sudo apt-get install docker.io
    $ docker --version

##安装openvswitch

###CentOS

####安装基础环境

    $yum install gcc make python-devel openssl-devel kernel-devel graphviz \
           kernel-debug-devel autoconf automake rpm-build redhat-rpm-config \
              libtool

####下载最新的包

    $wget http://openvswitch.org/releases/openvswitch-2.3.1.tar.gz

####解压与打包

    $tar zxvf openvswitch-2.3.1.tar.gz
    $mkdir -p ~/rpmbuild/SOURCES
    $cp openvswitch-2.3.1.tar.gz ~/rpmbuild/SOURCES/
    $sed 's/openvswitch-kmod, //g' openvswitch-2.3.1/rhel/openvswitch.spec > openvswitch-2.3.1/rhel/openvswitch_no_kmod.spec
    $rpmbuild -bb --without check openvswitch-2.3.1/rhel/openvswitch_no_kmod.spec

之后会在~/rpmbuild/RPMS/x86_64/里有2个文件

    total 9500
    -rw-rw-r-- 1 ovswitch ovswitch 2013688 Jan 15 03:20 openvswitch-2.3.1-1.x86_64.rpm
    -rw-rw-r-- 1 ovswitch ovswitch 7712168 Jan 15 03:20 openvswitch-debuginfo-2.3.1-1.x86_64.rpm

安装第一个就行

####安装

    $yum localinstall ~/rpmbuild/RPMS/x86_64/openvswitch-2.3.1-1.x86_64.rpm

####启动

    $systemctl start openvswitch

####查看状态

    $systemctl status openvswitch

验证是否正常运行

具体的安装详细步骤可以参考[这里](https://github.com/openvswitch/ovs/blob/master/INSTALL.RHEL.md与http://www.linuxidc.com/Linux/2014-12/110272.htm)

###Ubuntu


##部署单机环境的docker

###下载 pipework

使用这个软件进行固定ip设置

    $ cd /tmp/
    $ git clone https://github.com/jpetazzo/pipework.git

###在NODEA（ip是10.10.17.3）运行如下脚本

    #!/bin/bash
    #author: Deng Lei
    #email: dl528888@gmail.com
    #删除docker测试机
    docker rm `docker stop $(docker ps -a -q)`
    #删除已有的openvswitch交换机
    ovs-vsctl list-br|xargs -I {} ovs-vsctl del-br {}
    #创建交换机
    ovs-vsctl add-br ovs1
    ovs-vsctl add-br ovs2
    #把物理网卡加入ovs2
    ovs-vsctl add-port ovs1 em1
    ip link set ovs1 up
    ifconfig em1 0
    ifconfig ovs1 10.10.17.3
    ip link set ovs2 up
    ip addr add 172.16.0.3/16 dev ovs2

    pipework_dir='/tmp/pipework'
    docker run --restart always --privileged -d  --net="none" --name='test1'
    docker.ops-chukong.com:5000/centos6-http:new /usr/bin/supervisord
    $pipework_dir/pipework ovs2 test1 172.16.0.5/16@172.16.0.3

    docker run --restart always --privileged -d  --net="none" --name='test2'
    docker.ops-chukong.com:5000/centos6-http:new /usr/bin/supervisord
    $pipework_dir/pipework ovs2 test2 172.16.0.6/16@172.16.0.3

确保以 root 权限执行如上脚本, 根据自己的环境修改上面内容

###验证

已经启动了2个容器，分别是test1与test2

    $ docker ps -a

下面从本地登陆指定的 ip 试试

    $ ssh 172.16.0.5 #如果容器没有配置 ssh, 可通 docker attach 登陆进入容器

进入容器后

    #ifconfig
    #ping 10.10.17.3 -c 2
    #ping 10.10.17.4 -c 2
    #ping 172.16.0.6 -c 2
    #ping 172.16.0.3 -c 2
    #ping 172.16.0.4 -c 2
    #ping www.baidu.com -c 2

登陆后可以看到容器内的 ip 是指定的，并且能 ping 另外同一个网段的 172.16.0.6，
外网也能 ping 通, NODEB 的 em1 也可以 ping 通, 但是 NODEB 中的容器地址却 ping 不通。

###NODEB（ip是10.10.17.4）运行如下脚本

    #!/bin/bash
    #author: Deng Lei
    #email: dl528888@gmail.com
    #删除docker测试机
    docker rm `docker stop $(docker ps -a -q)`
    #删除已有的openvswitch交换机
    ovs-vsctl list-br|xargs -I {} ovs-vsctl del-br {}
    #创建交换机
    ovs-vsctl add-br ovs1
    ovs-vsctl add-br ovs2
    #把物理网卡加入ovs2
    ovs-vsctl add-port ovs1 em1
    ip link set ovs1 up
    ifconfig em1 0
    ifconfig ovs1 10.10.17.4
    ip link set ovs2 up
    ip addr add 172.16.0.4/16 dev ovs2

    pipework_dir='/tmp/pipework'
    docker run --restart always --privileged -d  --net="none" --name='test1'
    docker.ops-chukong.com:5000/centos6-http:new /usr/bin/supervisord
    $pipework_dir/pipework ovs2 test1 172.16.0.8/16@172.16.0.4

    docker run --restart always --privileged -d  --net="none" --name='test2'
    docker.ops-chukong.com:5000/centos6-http:new /usr/bin/supervisord
    $pipework_dir/pipework ovs2 test2 172.16.0.9/16@172.16.0.4


###验证

已经启动了2个容器，分别是test1与test2

    $ docker ps -a

下面从本地登陆指定的 ip 试试

    $ ssh 172.16.0.8 #如果容器没有配置 ssh, 可通 docker attach 登陆进入容器

进入容器后

    #ifconfig
    #ping 10.10.17.4 -c2
    #ping 10.10.17.3 -c2
    #ping 172.16.0.9 -c 2
    #ping 172.16.0.4 -c 2
    #ping 172.16.0.3 -c2
    #ping www.baidu.com -c 2

可以看到结果跟 NODEA（10.10.17.3）里运行的一样，登陆后可以看到容器内的 ip 是指定的，
并且能 ping 另外同一个网段的 172.16.0.9，外网也能 ping 通, NODEA 的 em1 可以ping
通, 但是 NODEA 的容器却 ping 不通

## VxLAN 配置

下面进行 vxlan 测试，连通 NODEA 和 NODEB 的容器

在 NODEA 里运行

    $ sudo ovs-vsctl add-port ovs2 vx1 -- set interface vx1 type=vxlan options:remote_ip=10.10.17.4
    $ sudo ovs-vsctl show

在 NODEB 里运行

    $ ovs-vsctl add-port ovs2 vx1 -- set interface vx1 type=vxlan options:remote_ip=10.10.17.3
    $ ovs-vsctl show

现在 NODEA 与 NODEB 这 2 台物理机的网络都是互通的，容器的网络也是互通。

然后在 NODEA（10.10.17.3）容器里 ping NODEB（10.10.17.4）的 ovs2 ip 与容器的 ip

    $ ssh 172.16.0.5

进入容器后

    #ifconfig
    #ping 10.10.17.3 -c 2
    #ping 10.10.17.4 -c 2
    #ping 172.16.0.6 -c 2
    #ping 172.16.0.8 -c 2
    #ping 172.16.0.9 -c 2
    #ping 172.16.0.3 -c 2
    #ping 172.16.0.4 -c 2
    #ping www.baidu.com -c 2

可以看到可以在 NODEA（10.10.17.3）容器里 ping 通 NODEB（10.10.17.4）的 ovs2 ip与交换机下面的容器 ip

然后在 NODEB（10.10.17.4）容器里 ping NODEA（10.10.17.3）的 ovs2 ip 与容器的 ip

    $ ssh 172.16.0.8

进入容器后

进入容器后

    #ifconfig
    #ping 10.10.17.4 -c2
    #ping 10.10.17.3 -c2
    #ping 172.16.0.9 -c 2
    #ping 172.16.0.4 -c 2
    #ping 172.16.0.3 -c 2
    #ping 172.16.0.5 -c2
    #ping 172.16.0.6 -c2
    #ping www.baidu.com -c 2

目前是2个节点的vxlan，如果是3个节点呢

提示: 相信不能难倒能举一反三的你

    ovs-vsctl add-port ovs2 vx2 -- set interface vx2 type=vxlan options:remote_ip=10.10.21.199
    ovs-vsctl add-port ovs2 vx1 -- set interface vx1 type=vxlan options:remote_ip=10.10.17.3

##FQA

如果各自设置 vxlan，还是无法连接请看看 iptables 里是否给 ovs1 进行了 input 放行

    cat /etc/sysconfig/iptables

##参考

http://dl528888.blog.51cto.com/2382721/1611491
