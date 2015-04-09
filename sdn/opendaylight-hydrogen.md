 opendaylight Hydrogen 环境搭建 
====================================

**作者** 

刘文学

**版本及修订**

0.1 完成初始化

预备条件
=====================
 
* 除标准环境外，运行本文档确保你有足够的内存。本机至少需要 8G 内存。
* 如果你要进行进一步开发插件编译等，请确保良好的网络。

opendaylight 虚拟机创建
==================================
在[标准环境](http://www.agreeqzdev.net:8081/projects/scm/wiki/GalaLua%E5%BC%80%E5%8F%91%E7%8E%AF%E5%A2%83%E6%9E%84%E5%BB%BA%E6%A0%87%E5%87%86)的 vagrant 目录下，执行如下

更新vagrang 配置文件

    $ git pull

切换到 opendaylight 分支

    $ git checkout -b opendaylight origin/opendaylight

创建 opendaylight-hydrogen 虚拟机

    $ vagrant up  opendaylight-hydrogen

等安装完成，opendaylight-hydrogen 已经启动，环境已经搭建好

进入新创建的虚拟机

    $ vagrant ssh opendaylight-hydrogen

controller 验证
=============================

运行

    $ifconfig

记住一个你可以通过浏览器访问的 IP

* 启动 controller 


    $. go
    $ ./run.sh

* 启动 mininet 创建网络拓扑

重新创建一个窗口，vagrant ssh 到虚拟机后，运行（当然你可以通过ssh vagrant@IP 进入创建的虚拟机，密码 vagrant）

    $sudo mn --controller=remote,ip=IP --topo tree,3  //这个ip必须通过浏览器可以访问。

* 测试controller 启动是否正常

在你本机中通过浏览器访问 http://IP:8080/， 登陆：用户名：admin 密码：admin


插件加载验证
=======================

* 查看插件

在运行 ./run.sh 窗口中运行 

    osgi > lb learn  //会提示没有相关 plugin

* 新增插件到 controller 

新增加一个连接窗口（如上），运行 

    $. go
    $mv  plugins/org.opendaylight.controller.samples.simpleforwarding-0.4.1-1-20140715.135847-7.jar ~/tmp/
    $cp ~/opendaylight-hydrogen/openflowplugin/samples/learning-switch/target/learning-switch-0.0.2-1-SNAPSHOT.jar plugins/

* 验证插件是否加载成功

在运行 ./run.sh 窗口中运行 

    osgi > lb learn
    
        START LEVEL 6
           ID|State      |Level|Name
          256|Active     |    4|org.opendaylight.openflowplugin.learning-switch (0.0.2.1-SNAPSHOT)

RESTCONF 验证
========================

* 浏览器下载 RESTful 插件

firefox 下载 RESTClient 插件
chrome 下载 postman 插件

* 列出所有节点

URL: http://IP:8080/restconf/operational/opendaylight-inventory:nodes/ 
method : GET

* 创建 flow

HTTP header: 

    Content-Type: application/xml 
    Accept: application/xml 

Authentication
    
    用户名：admin
    密码： admin

URL: http://IP:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/1 
method : PUT
HTTP body:

		<?xml version="1.0" encoding="UTF-8" standalone="no"?>
		<flow xmlns="urn:opendaylight:flow:inventory">
			<priority>2</priority>
			<flow-name>Foo</flow-name>
			<match>
				<ethernet-match>
				    <ethernet-type>
				        <type>2048</type>
				    </ethernet-type>
				</ethernet-match>
				<ipv4-destination>10.0.10.2/24</ipv4-destination>
			</match>
			<id>1</id>
			<table_id>0</table_id>
			<instructions>
				<instruction>
				    <order>0</order>
				    <apply-actions>
				        <action>
				           <order>0</order>
				           <dec-nw-ttl/>
				        </action>
				    </apply-actions>
				</instruction>
			</instructions>
		</flow>

你可以修改上面的 table 和 flow 后面的数字，来创建多个table，多个flow,注意 url 和 http body 的数字要一致。

* 验证创建的flow

1)
URL:http://IP:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/1 
HTTP header: Accept: application/xml 
method:GET

2)
URL:http://IP:8080/restconf/operational/opendaylight-inventory:nodes/node/openflow:1/table/0/ 
http header:Accept: application/xml 
method:GET

对于RESTConf 的验证更详细可以参考[这里](https://wiki.opendaylight.org/view/OpenDaylight_OpenFlow_Plugin:User_Guide)
[RESTConf OVSDB](https://wiki.opendaylight.org/view/OVSDB_Integration:Mininet_OVSDB_Tutorial)
