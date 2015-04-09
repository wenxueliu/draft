#=============================================================================
# 请确保网络良好。
# 请先注册 Gerrit 账号，否则git clone 代码失败。
# 注册地址：https://identity.opendaylight.org/carbon/user-registration/user-registration.jsp
# 注册教程：https://wiki.opendaylight.org/view/OpenDaylight_Controller:Gerrit_Setup
# 可以参考这里: http://www.dasblinkenlichten.com/installing-opendaylight-on-centos/
# 如果是想用脚本，必须确保你的sudo 是无密码的

#===================== Centos ============================
sudo localedef -v -c -i zh_CN -f UTF-8 zh_CN.UTF-8
sudo yum install -y java-1.7.0-openjdk
java -version
#java version "1.7.0_65"
#OpenJDK Runtime Environment (rhel-2.5.1.2.el6_5-x86_64 u65-b17)
#OpenJDK 64-Bit Server VM (build 24.65-b04, mixed mode)
cat >> ~/.bashrc << EOF
export JAVA_HOME=/usr/lib/jvm/jre-1.7.0-openjdk.x86_64
export JRE_HOME=/usr/lib/jvm/jre-1.7.0
export CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
export PATH=${JAVA_HOME}/bin:${JRE_HOME}/bin:$PATH
export MAVEN_OPTS='-Xmx1048m -XX:MaxPermSize=512m'
EOF

source ~/.bashrc

curl apache.dataguru.cn/maven/maven-3/3.0.5/binaries/apache-maven-3.0.5-bin.zip -o maven-3.0.5
sudo unzip maven-3.0.5 -d /usr/share/
sudo ln -s /usr/share/apache-maven-3.0.5/apache-maven-3.0.5/bin/mvn /usr/bin/mvn

mvn --version
#Apache Maven 3.0.5 (r01de14724cdef164cd33c7c8c2fe155faf9602da; 2013-02-19 13:51:28+0000)
#Maven home: /usr/share/apache-maven-3.0.5/apache-maven-3.0.5
#Java version: 1.7.0_65, vendor: Oracle Corporation
#Java home: /usr/lib/jvm/java-1.7.0-openjdk-1.7.0.65.x86_64/jre
#Default locale: zh_CN, platform encoding: UTF-8
#OS name: "linux", version: "2.6.32-431.3.1.el6.x86_64", arch: "amd64", family: "unix"


#===================== 预备条件 ============================

sudo localedef -v -c -i zh_CN -f UTF-8 zh_CN.UTF-8

sudo apt-get -y install openjdk-7-jdk

sudo cat >> ~/.bashrc <<EOF
export JAVA_HOME=/usr/lib/jvm/java-7-openjdk-amd64
export JRE_HOME=${JAVA_HOME}/jre
export CLASSPATH=.:${JAVA_HOME}/lib:${JRE_HOME}/lib
export PATH=${JAVA_HOME}/bin:${JRE_HOME}/bin:$PATH
export MAVEN_OPTS='-Xmx1048m -XX:MaxPermSize=512m'
EOF

source ~/.bashrc

sudo apt-get install -y maven

mvn -v
#Apache Maven 3.0.4
#Maven home: /usr/share/maven
#Java version: 1.7.0_65, vendor: Oracle Corporation
#Java home: /usr/lib/jvm/java-7-openjdk-amd64/jre
#Default locale: zh_CN, platform encoding: UTF-8
#OS name: "linux", version: "3.8.0-29-generic", arch: "amd64", family: "unix"

#如果需要安装mininet虚拟机,从这里下载： http://onlab.vicci.org/mininet-vm/mininet-2.1.0p2-140718-ubuntu-14.04-server-amd64-ovf.zip
#minineet 教程： mininet.org/walkthrough/
sudo apt-get install -y openvswitch-switch
sudo apt-get install -y mininet
sudo service openvswitch-controller stop
sudo update-rc.d openvswitch-controller disable
sudo mn --test pingall
git clone git://github.com/mininet/mininet
mininet/util/install.sh -fw

#============================================================================
#Hydrogen 版本

#=============================================================================

sudo apt-get -y install git
mkdir ~/opendaylight
cd ~/opendaylight
git clone https://github.com/opendaylight/controller.git  ~/opendaylight/controller
cd ~/opendaylight/controller
git checkout -b hydrogen origin/stable/hydrogen
cd ~/opendaylight/controller/opendaylight/distribution/opendaylight
mvn clean install

cd ~/opendaylight
git clone https://github.com/opendaylight/openflowjava.git  ~/opendaylight/openflowjava
cd ~/opendaylight/openflowjava
git checkout -b hydrogen origin/stable/hydrogen

cd ~/opendaylight
git clone https://github.com/opendaylight/openflowplugin.git  ~/opendaylight/openflowplugin
cd ~/opendaylight/openflowplugin
git checkout -b hydrogen origin/stable/hydrogen

cd ~/opendaylight/openflowplugin/distribution/base
mvn clean install




#=============================================================================

Eclipse

* 下载 Eclipse

下载[Eclipse IDE for Java Developers](http://www.eclipse.org/downloads/packages/eclipse-ide-java-developers/lunasr1)

* 在 ubuntu 中安装 eclipse。

	$ sudo tar –xzvf eclipse-java-kepler-SR1-linux-gtk.tar.gz –C /usr/lib

/usr/share/applications 目录下,新建 eclipse.desktop 文件,添加如下内容:

		[Desktop Entry]
		Name=Eclipse
		Comment=Eclipse SDK
		Encoding=UTF-8
		Exec=/usr/lib /eclipse/eclipse
		Icon=/usr/lib/eclipse/icon.xpm
		Terminal=false
		Type=Application
		Categories=Application; Development;

修改 /usr/lib/esclipse.ini

	--launcher.XXMaxPermSize
	300m
	-Xmx1024m

#============================================================================
#Helium 版本
[参考 SDNLab](http://www.sdnlab.com/?p=1931)
#=============================================================================

* 解包

	$unzip distribution-karaf-0.2.0-Helium

* 切换到项目目录

	$cd distribution-karaf-0.2.0-Helium

* 修改配置

	$vi etc/org.apache.karaf.management.cfg

	将
	serviceUrl = service:jmx:rmi://0.0.0.0:${rmiServerPort}/jndi/rmi://0.0.0.0:${rmiRegistryPort}/karaf-${karaf.name}

	修改成

	serviceUrl = service:jmx:rmi://127.0.0.1:${rmiServerPort}/jndi/rmi://127.0.0.1:${rmiRegistryPort}/karaf-${karaf.name}，

* 开始安装

	$./bin/karaf


* 安装支持REST API的组件：

    opendaylight-user@root>feature:install odl-restconf

* 安装L2 switch和OpenFlow插件：

    opendaylight-user@root>feature:install odl-l2switch-switch
    opendaylight-user@root>feature:install odl-openflowplugin-all

* 安装基于karaf控制台的md-sal控制器功能，包括nodes、yang UI、Topology：

    opendaylight-user@root>feature:install odl-mdsal-apidocs ##此组件写错，很容易无法登录

* 安装DLUX功能

    opendaylight-user@root>feature:install odl-dlux-all

* 安装基于karaf控制台的ad-sal功能，包括Connection manager、Container、Network、Flows：

    opendaylight-user@root>feature:install odl-adsal-northbound
    
注意，上面一定要按照顺序安装组件。如果不能登陆，

	$ opendaylight-user@root>logout
	$ rm -rf ~/distribution-karaf-0.2.0-Helium/data
	$ ./bin/karaf clean

	重新上面安装组件过程

* 登陆

    在 firefox 或 chrome 登陆 http://IP:8181/dlux/index.html //IP修改为你的安装本软件的 IP
    用户名：admin 密码：admin

* 验证

重新开一个窗口

	sudo mn --controller=remote,ip=IP,port=6633 //修改IP

重载登陆后的 topology 窗口

