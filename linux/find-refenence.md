---
layout: post
category : linux
comments : false
tags : [linux, tools, effciency, tutorial]
---
{% include JB/setup %}


find 命令格式
--------------------------------------------

    find  path  -option   [ -print ] [ -exec -ok command ]  {} ;

find命令的参数；
-------------------------------------------
**`pathname`** : find命令所查找的目录路径。

**`-print`** ： find命令将匹配的文件输出到标准输出。

**`-exec`** ： find命令对匹配的文件执行该参数所给出的shell命令。相应命令的形式为 `command  { } \`;，注意 `{ }` 和 `\` ；之间的空格。

**`-ok`** ： 和-exec的作用相同，只不过以一种更为安全的模式来执行该参数所给出的shell命令，在执行每一个命令之前，都会给出提示，让用户来确定是否执行。

find命令选项
--------------------------------------------
    -name  ”filename“       #结合正则表达式查找符合filename描述的文件，记住要用引号将文件名模式引起来。
    -perm                   #按执行权限来查找，最好使用八进制的权限表示法。
    -perm mode:             #文件许可正好符合mode
    -perm +mode:            #文件许可部分符合mode
    -perm -mode:            #文件许可完全符合mode
    -user  username         #按文件属主来查找
    -group groupname        #按组来查找
    -mtime -n +n            #按文件更改时间来查找文件，-n指n天以内，+n指n天以前
    -atime -n +n            #按文件访问时间来查GIN: 0px">
    -ctime -n +n            #按文件创建时间来查找文件，-n指n天以内，+n指n天以前
    -nogroup                #查无效属组的文件，即文件的属组在/etc/groups中不存在
    -nouser                 #查无效属主的文件，即文件的属主在/etc/passwd中不存
    -newer f1 !f2           #找比f1新比f2旧的文件，-n指n天以内，+n指n天以前 
    -type  b/d/c/p/l/f      #查类型是块设备/目录/字符设备/管道/符号链接/普通文件
    -size  n[c]k/M/G        #查长度为n[字节]kbytes/M/G的文件，直接数字表示块(512 bytes)。
    -depth                  #使查找在进入子目录前先行查找完本目录
    -fstype                 #查位于某一类型文件系统中的文件，这些文件系统类型通常可 在/etc/fstab中找到
    -mount                  #查文件时不跨越文件系统mount点
    -follow                 #如果遇到符号链接文件，就跟踪链接所指的文件
    -cpio                   #对匹配的文件使用cpio命令，将他们备份到磁带设备中
    -prune                  #使用这一选项可以使find命令忽略当前指定的目录中查找，如果同时使用-depth选项，那么-prune将被find命令忽略。
    -amin  [+/-]n                #查找系统中最后N分钟访问的文件
    -atime [+/-]n                #查找系统中最后n*24小时访问的文件
    -cmin  [+/-]n                #查找系统中最后N分钟被改变文件状态的文件
    -ctime [+/-]n                #查找系统中最后n*24小时被改变文件状态的文件
    -mmin  [+/-]n                #查找系统中最后N分钟被改变文件数据的文件
    -mtime [+/-]n                #查找系统中最后n*24小时被改变文件数据的文件

NOTE：

* ` - ` : 限定更改时间在距今n日以内的文件
* ` + ` : 限定更改时间在距今n日以前的文件。
* ` ! ` : 逻辑非符号。
* ` o ` : 逻辑与符号
* `() ` : 表示表达式的结合。
* ` \ ` : 表示引用，即指示 shell 不对后面的字符作特殊解释，而留给 find 命令去解释其意义。

1、在$HOME目录中查找文件属主为sam的文件，可以用：
    
    $ find ~ -user sam -print

2、在/etc目录下查找文件属主为uucp的文件：
    
    $ find /etc -user uucp -print

3、在/home目录下查找没有有效帐户的文件：

    $ find /home -nouser -print

4、在/apps目录下查找属于gem用户组的文件：
    
    $ find /apps -group gem -print

5、查找根目录处没有有效所属用户组的所有文件：
    
    $ find / -nogroup -print

6、系统$HOME目录下查找更改时间在5日以内的文件：
    
    $ find ～ -mtime -5 -print

7、在/var/adm目录下查找更改时间在3日以前的文件：
    
    $ find /var/adm -mtime +3 -print

8、查找更改时间比文件sam新但比文件temp旧的文件：

    $ find -newer sam  ! -newer temp -ls

9、查找更改时间在比temp文件新的文件：
    
    $ find . -newer temp -print

10、在当前目录下查找除目录以外的所有类型的文件，可以用：
    
    $ find . ! -type d -print

11、在当前目录下查找文件长度大于1 M字节的文件：
    
    $ find . -size +1000000c -print 

12、在/home/apache目录下查找文件长度恰好为100字节的文件：
    
    $ find /home/apache -size 100c -print

13、当前目录下查找长度超过10块的文件（一块等于512字节）：
    
    $ find . -size +10 -print

11、根目录开始，查找一个名为CON.FILE的文件：
    
    $ find / -name "CON.FILE" -depth -print

12、从当前目录开始查找位于本文件系统中文件名以XC结尾的文件：

    $ find . -name "*.XC" -mount -print

13、在/home下查存取时间比tmp.txt近的文件或目录

    $ find   /home  -anewer  tmp.txt  
    
14、列出文件或目录被改动过之后，在2日内被存取过的文件或目录

    $ find   /home  -used   -2                  

15、列出/home目录内用户的识别码大于501的文件或目录

    $ find   /home  -uid   +501                 
    
16、列出/home内组id为501的文件或目录    
    
    $ find   /home  -gid 501                    
    
17、列出/home内的tmp.txt 查时深度最多为3层

    $ find  /home  -name tmp.txt  -maxdepth  4  
    
18、从第2层开始查

    $ find  /home  -name tmp.txt  -mindepth  3  
 
19、查找大小为0的文件或空目录 

    $ find  /home  -empty                       
    
20、将find出来的东西拷到另一个地方 

    $ find *.c -exec cp ‘{}’ /tmp ‘;’    
    
有特殊文件，可以用cpio
    
    $ find dir -name filename -print | cpio -pdv newdir 
    
21、在/apps目录下查找文件，但不希望在/apps/bin目录下查找，可以用：

    $ find /apps -path "/apps/bin" -prune -o -print
 
22、在/usr/sam目录下查找不在dir1子目录之内的所有文件
    
    $ find /usr/sam -path "/usr/sam/dir1" -prune -o -print
 
这个表达式组合特例可以用伪码写为

    if -path "/usr/sam"  then
        -prune
    else
        -print

23、避开多个文件夹
    
    $ find /usr/sam \( -path /usr/sam/dir1 -o -path /usr/sam/file1 \) -prune -o -print

`()` : 表示表达式的结合。

`\` : 表示引用，即指示 shell 不对后面的字符作特殊解释，而留给 find 命令去解释其意义。

24、查找某一确定文件，-name 等选项加在 -o 之后
    
    $ find /usr/sam  \(-path /usr/sam/dir1 -o -path /usr/sam/file1 \) -prune -o -name "temp" -print    
  
    
用exec或ok来执行shell命令
----------------------------------------------------
使用find时，只要把想要的操作写在一个文件里，就可以用exec来配合find查找，很方便的

在有些操作系统中只允许 -exec 选项执行诸如 `ls` 或 `ls -l` 这样的命令。大多数用户使用这一选项是为了查找旧文件并删除它们。建议在真正执行rm命令删除文件之前，最好先用ls命令看一下，确认它们是所要删除的文件。

exec 选项后面跟随着所要执行的命令或脚本，然后是一对 { }，一个空格和一个 \ ，最后是一个分号。为了使用exec选项，必须要同时使用print选项。如果验证一下find命令，会发现该命令只输出从当前路径起的相对路径及文件名。

**NOTE** : 任何形式的命令都可以在exec中执行

1、匹配当前目录下的所有普通文件，并在 -exec 选项中使用 ls -l 命令将它们列出。
    
    find . -type f -exec ls -l {  } \;


2、在/logs目录中查找更改时间在5日以前的文件并删除它们

    find logs -type f -mtime +5 -exec rm {  } \;

记住：在shell中用任何方式删除文件之前，应当先查看相应的文件，一定要小心！当使用诸如mv或rm命令时，可以使用-exec选项的安全模式。它将在对每个匹配到的文件进行操作之前提示你。

3、在当前目录中查找所有文件名以.LOG结尾、更改时间在5日以上的文件，并删除它们，只不过在删除之前先给出提示。按 y 键删除文件，按 n 键不删除。

    find . -name "*.conf"  -mtime +5 -ok rm {  } \ ; 

4、匹配所有文件名为 "passwd" 的文件，例如， passwd、passwd.old、passwd.bak，然后执行 grep 命令看看在这些文件中是否存在一个sam用户。
    
    find /etc -name "passwd*" -exec grep "sam" {  } \;
 
实例
------------------------------------------

1、查找当前用户主目录下的所有文件：下面两种方法都可以使用：
 
    $ find $HOME -exec ls -l {  } \;
    $ find ~ -exec ls -l {  } \;

2、让当前目录中文件属主具有读、写权限，并且文件所属组的用户和其他用户具有读权限的文件：
    
    $ find . -type f -perm 644 -exec ls -l {  } \;

3、为了查找系统中所有文件长度为0的普通文件，并列出它们的完整路径：

    $ find / -type f -size 0 -exec ls -l {  } \;

4、查找/var/logs目录中更改时间在7日以前的普通文件，并在删除之前询问它们：
    $ find /var/logs -type f -mtime +7 -ok rm {  } \;

5、查找当前目录中所有属于root组的文件：

    $find . -group root -exec ls -l {  } \;

6、删除当目录中访问时间在7日以来、含有数字后缀的admin.log文件：

    $ find . -name "admin.log[0-9][0-9][0-9]" -atime -7  -ok  rm {  } \;




xargs
------------------------------------------

在使用 find 命令的 -exec 选项处理匹配到的文件时， find 命令将所有匹配到的文件一起传递给 exec 执行。但有些系统对能够传递给 exec 的命令长度有限制，这样在find命令运行几分钟之后，就会出现溢出错误。错误信息通常是“参数列太长”或“参数列溢出”。这就是 xargs 命令的用处所在，特别是与find命令一起使用。

find 命令把匹配到的文件传递给 xargs 命令，而 xargs 命令每次只获取一部分文件而不是全部，不像 -exec 选项那样。这样它可以先处理最先获取的一部分文件，然后是下一批，并如此继续下去。

在有些系统中，使用 -exec 选项会为处理每一个匹配到的文件而发起一个相应的进程，并非将匹配到的文件全部作为参数一次执行；这样在有些情况下就会出现进程过多，系统性能下降的问题，因而效率不高；

而使用 xargs 命令则只有一个进程。另外，在使用 xargs 命令时，究竟是一次获取所有的参数，还是分批取得参数，以及每一次获取参数的数目都会根据该命令的选项及系统内核中相应的可调参数来确定。

实例
---------------------------------------------------
1、查找系统中的每一个普通文件，然后使用 xargs 命令来测试它们分别属于哪类文件

    $ find . -type f -print | xargs file
 

2、在当前目中查找内存信息转储文件(core dump) ，然后把结果保存到/tmp/core.log 文件中：

    $find . -name "file*" -print | xargs echo "" > /temp/core.log

3、在当前目录下查找所有用户具有读、写和执行权限的文件，并收回相应的写权限：
    
    $ find . -perm -7 -print | xargs chmod o-w

4、用grep命令在当前目录下的所有普通文件中搜索 hostname 这个词：
    
    $ find . -type f -print | xargs grep "hostname"

可以用 \ 来取消 find 命令中的 * 在 shell 中的特殊含义。

    $ find . -name \* -type f -print | xargs grep "hostnames"

find 命令配合使用 exec 和 xargs 

总之，可以使用户对所匹配到的文件执行几乎所有的命令。


**问题** ：用find / -name filename| rm -rf，不成功，请问为什么不成功？ 

    1. find / -name filename -exec rm -rf {} \;
	   其中，{} 表示你找出来的结果。\ 则相当于“宪法”，没什么说头，就是这么规定的，在 -exec 后面需要一个表示该命令终结的的符号。可以在 man find 中找到答案。
        
    2. 要让 rm 识别 find 的结果，如下：`find / -name filename | xargs rm -rf`，之所以 `find . -name filename |rm -rf` 不通过，是因为rm命令不接受从标准输入传过来的指令

**问题** : find -name ".*" -perm -007 和 find -name ".*" -perm 777 有区别吗？

    007是指查找所有用户都可读、写、执行的文件，要小心呀~~~
    -007是查找含其它用户(不同组,非属主)可读,写,执行的文件.并不一定要同组可读写,-是指最少权限为007.

**问题** : 使用find 命令查找某个时间段的shell怎么写。比如11点到12点的,精确到分钟。

    创建一个脚本judgetime，内容如下：
    ls -l $* | awk ‘{split($8,hour,":"); if((hour[1] > 23 || hour[1] < 1)&&hour[1]<24) print }’
    
    touch -t 04241112 starttemp #开始到11点12分钟
    touch -t 04241220 endtemp #截止到12点20
    find [dir] -newer starttemp -a ! -newer endtemp -exec judgetime {} \;

**问题** : find中, -ctime, -mtime及其-atime有何区别

    mtime ls -l 最近修改文件内容的时间
    atime ls -lu 最近访问文件的时间
    ctime ls -lc 最近文件有所改变的状态 ,如文件修改,属性\属主 改变 ,节点 ,链接变化等 ,应该是不拘泥只是时间前后的改变
    
    摘书如下:
    -c Uses time of last modification of the i-node (file
    created,access, mode changed, and so forth) for sorting (-t)
    or printing (-l or -n).
    -u Uses time of last access instead of last modification
    for sorting (with the -t option) or printing (with the
    -l option).
    -i For each file, prints the i-node number in the first
    column of the report.

