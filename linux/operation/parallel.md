你是否曾经有过要计算一个非常大的数据(几百GB)的需求? 或在里面搜索, 或其它操作-- 一些无法并行的操作.
数据专家们, 我是在对你们说. 你可能有一个 16 核或更多核的 CPU, 但我们合适的工具, 例如 grep, bzip2,
 wc, awk, sed等等, 都是单线程的, 只能使用一个 CPU 内核.

但是"如何我能使用这些CPU核心"?

要想让 Linux 命令使用所有的 CPU 核心, 我们需要用到 GNU Parallel 命令, 它让我们所有的 CPU 核心在
单机内做神奇的 map-reduce 操作, 当然, 这还要借助很少用到的 –pipes 参数(也叫做–spreadstdin). 这样,
你的负载就会平均分配到各 CPU 上.

###BZIP2

bzip2 是比 gzip 更好的压缩工具, 但它很慢| 别折腾了, 我们有办法解决这问题.

以前的做法:

    cat bigfile.bin | bzip2 --best > compressedfile.bz2

现在这样:

    cat bigfile.bin | parallel --pipe --recend '' -k bzip2 --best > compressedfile.bz2

尤其是针对 bzip2, GNU parallel 在多核 CPU 上是超级的快. 你一不留神, 它就执行完成了.


###GREP

如果你有一个非常大的文本文件, 以前你可能会这样:

    grep pattern bigfile.txt

现在你可以这样:

    cat bigfile.txt | parallel --pipe grep 'pattern'

或者这样:

    cat bigfile.txt | parallel --block 10M --pipe grep 'pattern'

这第二种用法使用了 -block 10M 参数, 这是说每个内核处理 1 千万行, 你可以用这个参数来调整每个
CUP 内核处理多少行数据。

###AWK

下面是一个用 awk 命令计算一个非常大的数据文件的例子.

常规用法:

    cat rands20M.txt | awk '{s+=$1} END {print s}'

现在这样:

    cat rands20M.txt | parallel --pipe awk \'{s+=\$1} END {print s}\' | awk '{s+=$1} END {print s}'

这个有点复杂: parallel 命令中的 -pipe 参数将 cat 输出分成多个块分派给 awk 调用, 形成了很多
子计算操作. 这些子计算经过第二个管道进入了同一个 awk 命令, 从而输出最终结果. 第一个 awk 有
三个反斜杠, 这是 GNU parallel 调用 awk 的需要.

###WC

想要最快的速度计算一个文件的行数吗?

传统做法:

    wc -l bigfile.txt

现在你应该这样:

    cat bigfile.txt | parallel --pipe wc -l | awk '{s+=$1} END {print s}'

非常的巧妙, 先使用 parallel 命令 'mapping' 出大量的 wc -l 调用, 形成子计算, 最后通过管道发送给 awk 进行汇总.

###SED

想在一个巨大的文件里使用 sed 命令做大量的替换操作吗?

常规做法:

    sed s^old^new^g bigfile.txt

现在你可以:

    cat bigfile.txt | parallel --pipe sed s^old^new^g

然后你可以使用管道把输出存储到指定的文件里.

##参考
http://blog.chinaunix.net/uid-24404943-id-4020546.html
