SSH是一个非常伟大的工具，如果你要在互联网上远程连接到服务器，那么SSH无疑是最佳的候选。下面是通过网络投票选出的25个最佳SSH命令，你必须牢记于心。

##三，复制文件或目录命令： 

###基本命令语法

　　从本地复制到远程：`scp [OPTION] [<local_user>@<local_host>:] PATH <remote_user>@<remote_host>:PATH`

　　从远程复制到本地：`scp [OPTION] <remote_user>@<remote_host>:PATH [<local_user>@<local_host>:]本地路径`

    1.[<local_user>@<local_host>:]这一项可以不输入。
    2.如果不输入[<remote_user>@]，那么命令执行后会要求用户输入。
    3.命令执行后可能需要输入远程用户的密码。通常第一次传输时需要输入密码，系统重启后也会视为第一次传输。

###可选参数 :

-v　　和大多数linux命令中的-v意思一样, 用来显示命令执行过程中的具体信息，可以用来查看连接、认证或是配置错误。

-C　　启用压缩选项。

-P　　选择端口，注意-p已经被rcp使用。

-4　　强行使用IPV4地址。

-6　　强行使用IPV6地址。

-r　　用于传送目录时，递归传送子目录与子文件。


###复制文件：

（1）将本地文件拷贝到远程

scp FILE <user>@<host>:FILE (这里的FILE可以是包含路径的文件名)

（2）从远程将文件拷回本地

scp <user>@<host>:FILE  LOCAL_PATH (这里的FILE可以是包含路径的文件名)

###复制目录：
（1）将本地目录拷贝到远程
scp -r PATH <user>@<host>:PATH
2）从远程将目录拷回本地
scp -r   <user>@<host>:PATH  LOCAL_PATH 

## 

###1、复制SSH密钥到目标主机，开启无密码SSH登录

    ssh-copy-id user@host (如果还没有密钥，请使用ssh-keygen命令生成。)

###2、从某主机的80端口开启到本地主机2001端口的 ssh 隧道
	
	ssh -N -L 2001:localhost:80 somemachine

现在你可以直接在浏览器中输入http://localhost:2001访问这个网站。

###3、将你的麦克风输出到远程计算机的扬声器

    dd if=/dev/dsp | ssh -c arcfour -C username@host dd of=/dev/dsp

这样来自你麦克风端口的声音将在SSH目标计算机的扬声器端口输出，但遗憾的是，声音质量很差，你会听到很多嘶嘶声。

###4、比较远程和本地文件

    ssh user@host cat /path/to/remotefile | diff /path/to/localfile –

在比较本地文件和远程文件是否有差异时这个命令很管用。

###5、通过SSH挂载目录/文件系统

    sshfs <user>@<host>:/path/to/folder /path/to/mount/point

从http://fuse.sourceforge.net/sshfs.html下载sshfs，它允许你跨网络安全挂载一个目录。

###6、通过中间主机建立SSH连接

    ssh -t reachable_host ssh unreachable_host

Unreachable_host表示从本地网络无法直接访问的主机，但可以从reachable_host所在网络访问，这个命令通过到reachable_host的“隐藏”连接，创建起到unreachable_host的连接。

###7、通过你的电脑，复制远程 host1 主机上的文件到远程 host2 主机上的文件

    ssh <user>@<host1> “cd /somedir/tocopy/ && tar -cf – .” | ssh <user2>@<host2> “cd /samedir/tocopyto/ && tar -xf -”

如果只有你能同时访问 host1 和 host 2 ，但它们不能访问你的主机（因此 ncat 是无法工作的），而且它们之间也无法直接访问。

###8、运行任何远程主机上的 GUI 程序

    ssh -fX <user>@<host> <program>

SSH 服务器端必须要具备以下条件：

X11Forwarding yes ＃确保 X11 转发是打开的

同时也可以打开

Compression delayed

当然，你要能访问主机A才行。

9、创建到目标主机的持久化连接

    ssh -MNf <user>@<host>

在后台创建到目标主机的持久化连接，将这个命令和你~/.ssh/config中的配置结合使用：

    Host host
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlMaster no

所有到目标主机的SSH连接都将使用持久化SSH套接字，如果你使用SSH定期同步文件（使用rsync/sftp/cvs/svn），这个命令将非常有用，因为每次打开一个SSH连接时不会创建新的套接字。

10、通过SSH 直接开启并还原 screen 命令

    ssh -t remote_host screen –r

直接连接到远程 screen 会话（节省了无用的父bash进程）。

11、端口检测（敲门）

    knock <host> 3000 4000 5000 && ssh -p <port> user@host && knock <host> 5000 4000 3000

在一个端口上敲一下打开某个服务的端口（如SSH），再敲一下关闭该端口，需要先安装knockd，下面是一个配置文件示例。

    [options]
    logfile = /var/log/knockd.log
    [openSSH]
    sequence = 3000,4000,5000
    seq_timeout = 5
    command = /sbin/iptables -A INPUT -i eth0 -s %IP% -p tcp –dport 22 -j ACCEPT
    tcpflags = syn
    [closeSSH]
    sequence = 5000,4000,3000
    seq_timeout = 5
    command = /sbin/iptables -D INPUT -i eth0 -s %IP% -p tcp –dport 22 -j ACCEPT
    tcpflags = syn

12、删除文本文件中的一行内容，有用的修复

    ssh-keygen -R <the_offending_host>

在这种情况下，最好使用专业的工具。

13、通过SSH运行复杂的远程shell命令

    ssh host -l user $(<cmd.txt)

更具移植性的版本：

    ssh host -l user “`cat cmd.txt`”

14、通过SSH将MySQL数据库复制到新服务器

    mysqldump –add-drop-table –extended-insert –force –log-error=error.log -uUSER -pPASS OLD_DB_NAME | ssh -C user@newhost “mysql -uUSER -pPASS NEW_DB_NAME”

通过压缩的SSH隧道Dump一个MySQL数据库，将其作为输入传递给mysql命令，我认为这是迁移数据库到新服务器最快最好的方法。

15、删除文本文件中的一行，修复“SSH主机密钥更改”的警告

    sed -i 8d ~/.ssh/known_hosts

16、从一台没有SSH-COPY-ID命令的主机将你的SSH公钥复制到服务器

    cat ~/.ssh/id_rsa.pub | ssh user@machine “mkdir ~/.ssh; cat >> ~/.ssh/authorized_keys”

如果你使用Mac OS X或其它没有ssh-copy-id命令的*nix变种，这个命令可以将你的公钥复制到远程主机，因此你照样可以实现无密码SSH登录。

17、实时SSH网络吞吐量测试

    yes | pv | ssh $host “cat > /dev/null”

通过SSH连接到主机，显示实时的传输速度，将所有传输数据指向/dev/null，需要先安装pv。

如果是Debian：

    apt-get install pv

如果是Fedora：

    yum install pv

（可能需要启用额外的软件仓库）。

18、如果建立一个可以重新连接的远程GNU screen

    ssh -t user@some.domain.com /usr/bin/screen –xRR

人们总是喜欢在一个文本终端中打开许多shell，如果会话突然中断，或你按下了“Ctrl-a d”，远程主机上的shell不会受到丝毫影响，你可以重新连接，其它有用的screen命令有“Ctrl-a c”（打开新的shell）和“Ctrl-a a”（在shell之间来回切换），请访问http://aperiodic.net/screen/quick_reference阅读更多关于 screen命令的快速参考。

19、继续SCP大文件

    rsync –partial –progress –rsh=ssh $file_source $user@$host:$destination_file

它可以恢复失败的rsync命令，当你通过VPN传输大文件，如备份的数据库时这个命令非常有用，需要在两边的主机上安装rsync。

    rsync –partial –progress –rsh=ssh $file_source $user@$host:$destination_file local -> remote

或

    rsync –partial –progress –rsh=ssh $user@$host:$remote_file $destination_file remote -> local

20、通过SSH W/ WIRESHARK分析流量

    ssh root@server.com ‘tshark -f “port !22″ -w -’ | wireshark -k -i –

使用tshark捕捉远程主机上的网络通信，通过SSH连接发送原始pcap数据，并在wireshark中显示，按下Ctrl+C将停止捕捉，但 也会关闭wireshark窗口，可以传递一个“-c #”参数给tshark，让它只捕捉“#”指定的数据包类型，或通过命名管道重定向数据，而不是直接通过SSH传输给wireshark，我建议你过滤数 据包，以节约带宽，tshark可以使用tcpdump替代：

    ssh root@example.com tcpdump -w – ‘port !22′ | wireshark -k -i –

21、保持SSH会话永久打开

    autossh -M50000 -t server.example.com ‘screen -raAd mysession’

打开一个SSH会话后，让其保持永久打开，对于使用笔记本电脑的用户，如果需要在Wi-Fi热点之间切换，可以保证切换后不会丢失连接。

22、更稳定，更快，更强的SSH客户端

    ssh -4 -C -c blowfish-cbc

强制使用IPv4，压缩数据流，使用Blowfish加密。

23、使用cstream控制带宽

    tar -cj /backup | cstream -t 777k | ssh host ‘tar -xj -C /backup’

使用bzip压缩文件夹，然后以777k bit/s速率向远程主机传输。Cstream还有更多的功能，请访问http://www.cons.org/cracauer/cstream.html#usage了解详情，例如：

    echo w00t, i’m 733+ | cstream -b1 -t2

24、一步将SSH公钥传输到另一台机器

    ssh-keygen; ssh-copy-id user@host; ssh user@host

这个命令组合允许你无密码SSH登录，注意，如果在本地机器的~/.ssh目录下已经有一个SSH密钥对，ssh-keygen命令生成的新密钥可 能会覆盖它们，ssh-copy-id将密钥复制到远程主机，并追加到远程账号的~/.ssh/authorized_keys文件中，使用SSH连接 时，如果你没有使用密钥口令，调用ssh user@host后不久就会显示远程shell。

25、将标准输入（stdin）复制到你的X11缓冲区

    ssh user@host cat /path/to/some/file | xclip

你是否使用scp将文件复制到工作用电脑上，以便复制其内容到电子邮件中？xclip可以帮到你，它可以将标准输入复制到X11缓冲区，你需要做的就是点击鼠标中键粘贴缓冲区中的内容。

如果你还有其它SSH命令技巧，欢迎在本文评论中帖出。另外，想学到更多 Shell 命令，请下载最牛B的 Linux Shell 命令PDF 手册。










一.(引子)SSH由IETF的網路工作小組（Network Working Group）所制定；SSH為建立在应用层和传输层基础上的安全协议。
传统的网络服务程序，如FTP、POP和Telnet其本质上都是不安全的；因为它们在网络上用明文传送数据、用户帐号和用户口令，很容易受到中间人 （man-in-the-middle）攻击方式的攻击。就是存在另一个人或者一台机器冒充真正的服务器接收用户传给服务器的数据，然后再冒充用户把数据 传给真正的服务器。
而SSH是目前较可靠，專为远程登录会话和其他网络服务提供安全性的协议。利用SSH协议可以有效防止远程管理过程中的信息泄露问题。透過SSH可以對所有传输的数据进行加密，也能够防止DNS欺骗和IP欺骗。
SSH之另一項優點為其传输的数据是经过压缩的，所以可以加快传输的速度。SSH有很多功能，它既可以代替Telnet，又可以为FTP、POP、甚至为PPP提供一个安全的「通道」。
1.首先 了解一下其简单应用，你可以通过ssh  root@192.168.0.122意思就是本地连接到192.168.0.122这个IP地址所代表的主机上。你可以进入该主机进行一系列的操作哈！
ssh中有一个鎖的验证机制，分为用口令的和不用口令的，还有用代理的，这样你几不用每次连进去就输入密码了。在每个用户主目录下都有一个.ssh的隐含 文件，进入之后，运行命令ssh-keygen会产生id-rsa(相当于密钥) id_rsa.pub（相当于鎖） authorized_keys authorized_keys2 ，然后你通过
        ssh-copy-id -i id_rsa.pub student@192.168.0.22
传给对方主机上的.ssh目录中，这样你每次要连接的时候，只需要开一次鎖就可以啦！
（1）ssh-keygen
         <Enter>
        <Enter>
         <Enter>
   ssh-copy-id -i id_rsa.pub student@192.168.0.22（这时候你传东西的时候要输入密码）
这样设置完成之后，你可以通过ssh student@192.168.0.122命令以student的身份连接到对方的主机上，退出，甚至将该shell终端关闭，再重新打开一个新的终端 在连，还可以连上。（不过要注意两者身份哈，例如122主机root产生的私钥和公钥，传给22的student身份，那么你连接的时候也是要用122的 root连22的student才行）
(2) 需要口令才能进去的，
        ssh-keygen
             <Enter>
        接下来你可以输入两遍你要设置的密码，
  ssh-copy-id -i id_rsa.pub student@192.168.0.22
  测试：
    ssh  student@192.168.0.22
(这样你每次进去的时候都要输入口令，和输入密码没有什么区别了，所以我们需要使用代理，就不用每次都属密码了)
(3) 加代理服务器和口令的
     ssh-keygen
             <Enter>
        接下来你可以输入两遍你要设置的密码，
      ssh-copy-id -i id_rsa.pub student@192.168.0.22
      ssh-agent
      ssh-agent bash
      ssh-add
    测试：
    ssh  student@192.168.0.22
这样你只需要输入一次密码，然后在退出，在连接就不需要再次输入口令了，但是你在关闭该shall的时候在打开一个新的shell终端的就不行了，还需要从新添加代理。
2   排错处理：
 将拥有公钥的那台主机的/etc/ssh_host_*删除，然后/etc/init.d/sshd restart ,之 后在连接的时候就会出现好多@@@@@,这是因为你每次链接的时候客户机和服务器之间会拿/etc/ssh_host_*的文件与拥有私钥的那台主机上 的. ~/.ssh/known_hosts进行对比，之后你删了在产生的就不符合了，所以肯定连不上了。
 解决办法：将拥有私钥的那台主机上的 ~/.ssh/known_hosts删除，然后重新传一遍公钥。
 
3.关于ssh一些配置文件的修改问题假设设置的在192.168.0.122上
  vi /etc/ssh/ssd_config
  (1)  PermitRootlogin  yes
     默认是yes,意思是允许其他主机以root身份ssh连接到本机，若是no，意思就是不允许以root身份登录到本机
  （2）AllowUsers  student
     意思是只允许以student身份登录到本台机子。不允许以其他身份登录
        ssh  student@192.168.0.22  可以连接到
    ssh   root@192.168.0.22    连接不上
（3）Password Authentication yes
 默认是yes，意思是允许通过密码登录
 若no,意思就是说不允许以密码登录，那么你只能通过ssh密码密钥设置访问，这样你就不用输入密码了，做实验的时候注意在设置好ssh之后在改动好你的SSH
  上述三个改动好了之后要注意重启sshd服务在测试。
有一点需要注意，分不清谁是服务器谁是客户端的时候，要想着连谁谁是服务器。
4.
   ssh -x student@192.168.0.122 firefox
这条命令会在192.168.0.122 那台主机上以student身份代开firefox。在你的电脑上显示出来，对方可能看不到，可是查看本机进程就会发现哦。

5.vi   /etc/motd
写的内容会在你通过ssh连接到你的机子上时的时候显示出来。
6.关于ssh链接对方主机显示ssh: connect to host 192.168.0.24 port 22: No route to host
有以下几种可能性：（首先要注意将iptables 和selinux都要关闭哦！）
（1）检查对方主机是否可以ping 通，也就是查看对方主机是否开机着呢。
（2）查看出错方在哪里，看你本机连其他的机子是否有问题，排查错误主机设置，      有可能是对方主机的/ect/hosts.allow或者/etc/hosts.deny的设置，又或者是/etc/xinetd.conf中的设置，本 人一次出错是因为发现./ect/ssh/下面什么也没有，所以只有重新安装喽，不过安装好之后要重启sshd服务的哦！
（3）查看/etc/sshd/sshd_config下面有没有设置将端口号分配的问题！
