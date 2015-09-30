当我觉得对Linux系统下修改hostname已经非常熟悉的时候，今天碰到了几个个问题，这几个问题给我好好上了一课，很多知识点，当你觉得你已经掌握的时候，其实你了解的还只是皮毛。技术活，切勿浅尝则止！

实验环境：Red Hat Enterprise Linux Server release 5.7 (Tikanga) ，其它版本Linux可能有所不同。请以实际环境为准。

其实我多次修改过hostname，一般只需要修改 /etc/hosts 和 /etc/sysconfig/network 两个文件下相关配置即可。但是，今天我遇到了两个问题：

   问题1： 为什么/etc/sysconfig/network配置文件中HOSTNAME为localhost.localdomain，但是显示的hostname为po132345806-a，那到底hostname的配置值放在哪里？
1: [root@po132345806-a ~]# more /etc/hosts 2: # Do not remove the following line, or various programs 3: # that require network functionality will fail. 4: 127.0.0.1 localhost.localdomain localhost 5: ::1 localhost6.localdomain6 localhost6 6: [root@po132345806-a ~]# more /etc/sysconfig/network 7: NETWORKING=yes 8: NETWORKING_IPV6=yes 9: HOSTNAME=localhost.localdomain

有图有真相，免得大家不相信这个现象，当我第一次碰到这种特殊情况时，我也非常纳闷。Google了一些资料加上自己的实践才弄明白

    问题2： 修改了hostname后，如何使其立即生效而不用重启操作系统。

    问题3： 修改hostname有几种方式？

    问题4： hostname跟/etc/hosts 下配置有关系吗？

    问题5： 如何查看hostname的值，以那个为准？


问题1解答：我一直以为hostname的值配置在/etc/sysconfig/network中，这个文件里面HOSTNAME配置为啥，hostname值就是啥。但是为什么出现上面那种情况呢？难道/etc/sysconfig/network

   不是hostname的配置文件，难道还另有其它配置文件？于是我当时实验了一下修改了/etc/sysconfig/network文件中HOSTNAME为DB-Server，发现

hostname的值依然没有变化，于是重启了计算机

   1: "/etc/sysconfig/network" 3L, 66C written

   2: 132345806-a ~]# hostname

   3: 806-a.gfg1.esquel.com

   4: 132345806-a ~]# more /proc/sys/kernel/hostname

   5: 806-a.gfg1.esquel.com

   6: 132345806-a ~]# sysctl kernel.hostname

   7: ostname = po132345806-a.gfg1.esquel.com

   8: 132345806-a ~]#

   9: 132345806-a ~]# reboot


  重启过后发现居然hostname变为DB-Server了，也就是说修改配置文件/etc/sysconfig/network下的HOSTNAME生效了。那么也就是说应该是有人修改过 kernel.hostname,请看下面实验

   1: [root@DB-Server ~]# more /etc/sysconfig/network

   2:  

   3: NETWORKING=yes

   4:  

   5: NETWORKING_IPV6=yes

   6:  

   7: HOSTNAME=DB-Server.localdomain

   8:  

   9: [root@DB-Server ~]# echo Test > /proc/sys/kernel/hostname

  10:  

  11: [root@DB-Server ~]# more /etc/proc/sys/kernel/hostname

  12:  

  13: /etc/proc/sys/kernel/hostname: No such file or directory

  14:  

  15: [root@DB-Server ~]# more /proc/sys/kernel/hostname

  16:  

  17: Test

  18:  

  19: [root@DB-Server ~]# /etc/init.d/network restart

  20:  

  21: Shutting down interface eth0: [ OK ]

  22:  

  23: Shutting down loopback interface: [ OK ]

  24:  

  25: Bringing up loopback interface: [ OK ]

  26:  

  27: Bringing up interface eth0:

  28:  

  29: Determining IP information for eth0... done.

  30:  

  31: [ OK ]

  32:  

  33: [root@DB-Server ~]# hostname

  34:  

  35: Test

  36:  

  37: [root@DB-Server ~]# 

  38:  

注意：其实 /etc/init.d/network restart 没有什么用。只是当时实验时以为必须重启网络服务。

在SecureCRT新建克隆一个会话发现hostanme已经从DB-Server变为Test了，但是/etc/sysconfig/network的值还是DB-Server.localdomain，并没有变为Test。

   1: [root@Test ~]# more /etc/sysconfig/network

   2:  

   3: NETWORKING=yes

   4:  

   5: NETWORKING_IPV6=yes

   6:  

   7: HOSTNAME=DB-Server.localdomain

   8:  

   9: [root@Test ~]# hostname

  10:  

  11: Test

  12:  

  13: [root@Test ~]# more /etc/hosts

  14:  

  15: # Do not remove the following line, or various programs

  16:  

  17: # that require network functionality will fail.

  18:  

  19: 127.0.0.1 localhost.localdomain localhost

  20:  

  21: ::1 localhost6.localdomain6 localhost6

  22:  

  23: [root@Test ~]# more /proc/sys/kernel/hostname

  24:  

  25: Test

  26:  

  27: [root@Test ~]# 

  28:  

但是如果重启系统后hostname会变为DB-Server，Google了一些英文文档资料才知道，hostname是Linux系统下的一个内核参数，它保存在/proc/sys/kernel/hostname下，但是它的值是Linux启动时从rc.sysinit读取的。

hostname is a kernel parameter which stores hostname of the system. Its location is"/proc/sys/kernel/hostname"

The value for this parameter is loaded to kernel by rc.sysinit file during the boot process.

而/etc/rc.d/rc.sysinit中HOSTNAME的取值来自与/etc/sysconfig/network下的HOSTNAME，代码如下所示，至此，我们可以彻底明白了。

HOSTNAME=`/bin/hostname`

HOSTTYPE=`uname -m`

unamer=`uname -r`

set -m

if [ -f /etc/sysconfig/network ]; then

. /etc/sysconfig/network

fi

if [ -z "$HOSTNAME" -o "$HOSTNAME" = "(none)" ]; then

    HOSTNAME=localhost

fi

结论：/etc/sysconfig/network 确实是hostname的配置文件，hostname的值跟该配置文件中的HOSTNAME有一定的关联关系，但是没有必然关系，hostname的值来自内核参数/proc/sys/kernel/hostname，如果我通过命令sysctl kernel.hostname=Test修改了内核参数，那么hostname就变为了Test了。

问题2： 修改了hostname后，如何使其立即生效而不用重启操作系统。

    方法1：修改了/etc/sysconfig/network下的HOSTNAME后，然后使用echo  servername > /proc/sys/kernel/hostname。

         [root@DB-Server ~]# echo Test >/proc/sys/kernel/hostname

          注意当前会话还是不会变化，但是后续新建会话则会生效。

    方法2：修改了/etc/sysconfig/network下的HOSTNAME后，然后使用sysctl kernel.hostname命令使其立即生效

        [root@DB-Server ~]# sysctl kernel.hostname=Test2

        kernel.hostname = Test2

注意当前会话还是不会变化，但是后续新建会话会生效。

    方法3：修改了/etc/sysconfig/network下的HOSTNAME后，然后使用hostname命令使其生效

        [root@Test ~]# hostname DB-Server

        注意当前会话还是不会变化，但是后续新建会话会生效。

    其实呢，这几种方式只是结合永久性修改和临时性修改hostname，使其不必重启Linux服务器，哈哈，不知道你明白没。

 

问题3： 修改hostname有几种方式？

    1：  hostname DB-Server                                   --运行后立即生效（新会话生效），但是在系统重启后会丢失所做的修改

    2：  echo DB-Server  > /proc/sys/kernel/hostname          --运行后立即生效（新会话生效），但是在系统重启后会丢失所做的修改

    3： sysctl kernel.hostname=DB-Server                      --运行后立即生效（新会话生效），但是在系统重启后会丢失所做的修改

    4: 修改/etc/sysconfig/network下的HOSTNAME变量             --需要重启生效，永久性修改。

问题4： hostname跟/etc/hosts 下配置有关系吗？

      如果从我上面的实验来看，其实hostname跟/etc/hosts下的配置是没有关系的。hostname的修改、变更完全不依赖hosts文件。 其实hosts文件的作用相当如DNS，提供IP地址到hostname的对应。早期的互联网计算机数量少，单机hosts文件里足够存放所有联网计算机。不过随着互联网的发展，这就远远不够了。于是就出现了分布式的DNS系统。由DNS服务器来提供类似的IP地址到域名的对应。具体可以man hosts查看相关信息。

Linux系统在向DNS服务器发出域名解析请求之前会查询/etc/hosts文件，如果里面有相应的记录，就会使用hosts里面的记录。/etc/hosts文件通常里面包含这一条记录

     127.0.0.1 localhost.localdomain localhost

hosts文件格式是一行一条记录，分别是IP地址 、hostname、 aliases，三者用空白字符分隔，aliases可选。

127.0.0.1到localhost这一条建议不要修改，因为很多应用程序会用到这个，比如sendmail，修改之后这些程序可能就无法正常运行。

但是呢，其实hostname也不是说跟/etc/hosts一点关系都没有。在/etc/rc.d/rc.sysinit中，有如下逻辑判断，当hostname为localhost后localhost.localdomain时，将会使用接口IP地址对应的hostname来重新设置系统的hostname。

        # In theory there should be no more than one network interface active

        # this early in the boot process -- the one we're booting from.

        # Use the network address to set the hostname of the client. This

        # must be done even if we have local storage.

        ipaddr=

        if [ "$HOSTNAME" = "localhost" -o "$HOSTNAME" = "localhost.localdomain" ]; then

                ipaddr=$(ip addr show to 0/0 scope global | awk '/[[:space:]]inet / { print gensub("/.*","","g",$2) }')

                if [ -n "$ipaddr" ]; then

                        eval $(ipcalc -h $ipaddr 2>/dev/null)

                        hostname ${HOSTNAME}

                fi

        fi

我们来实验一下吧，修改hosts、network文件，修改后的值如下所示：

[root@localhost ~]# more /etc/hosts

# Do not remove the following line, or various programs

# that require network functionality will fail.

::1 localhost.localdomain localhost

127.0.0.1 localhost.localdomain localhost

192.168.244.128 DB-Server.localdomain DB-Server

[root@localhost  ~]# more /etc/sysconfig/network

NETWORKING=yes

NETWORKING_IPV6=yes

HOSTNAME=localhost.localdomain

重启系统后，我们再截图看看情况：

    所以这也是有时候人们以为hostname的值跟hosts文件有关系的缘故。

问题5： 如何查看hostname的值，以那个为准？

[root@DB-Server ~]# hostname

DB-Server

[root@DB-Server ~]# more /proc/sys/kernel/hostname

DB-Server

[root@DB-Server ~]# more /etc/sysconfig/network

NETWORKING=yes

NETWORKING_IPV6=yes

HOSTNAME=localhost.localdomain

   以那个为准呢，如果你理解了前面4个问题，那么理解这个问题就很简单了。

参考资料：

http://jblevins.org/log/hostname

http://www.ducea.com/2006/08/07/how-to-change-the-hostname-of-a-linux-system/

https://www.kernel.org/doc/Documentation/sysctl/kernel.txt

http://soft.chinabyte.com/os/281/11563281.shtml

参考

http://www.cnblogs.com/kerrycode/p/3595724.html

