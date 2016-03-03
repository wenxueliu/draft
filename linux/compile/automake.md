
##简介

###autoscan

autoscan 是用来扫描源代码目录生成 configure.scan 文件的。autoscan 可以用目录名做为参数，
但如果你不使用参数的话，那么 autoscan 将认为使用的是当前目录。autoscan 将扫描你所指定目
录中的源文件，并创建 configure.scan 文件。

###configure.scan

configure.scan 包含了系统配置的基本选项，里面都是一些宏定义。我们需要将它改名为 configure.in

###aclocal

aclocal 是一个perl 脚本程序。aclocal 根据 configure.in 文件的内容，自动生成 aclocal.m4 文件。
aclocal 的定义是："aclocal - create aclocal.m4 by scanning configure.ac" 。

###autoconf

autoconf 是用来产生 configure 文件的。configure 是一个脚本，它能设置源程序来适应各种不同的
操作系统平台，并且根据不同的系统来产生合适的 Makefile ，从而可以使你的源代码能在不同的操作
系统平台上被编译出来。

configure.in 文件的内容是一些宏，这些宏经过 autoconf 处理后会变成检查系统特性、环境变量、软件
必须的参数的 shell 脚本。configure.in 文件中的宏的顺序并没有规定，但是你必须在所有宏的最前面
和最后面分别加上 AC_INIT 宏和 AC_OUTPUT 宏。

在 configure.ini 中：

# 号表示注释，这个宏后面的内容将被忽略。

AC_INIT(FILE)

这个宏用来检查源代码所在的路径。

AM_INIT_AUTOMAKE(PACKAGE, VERSION)

这个宏是必须的，它描述了我们将要生成的软件包的名字及其版本号：PACKAGE 是软件包的名字，VERSION 是版本号。
当你使用 make dist 命令时，它会给你生成一个类似 helloworld-1.0.tar.gz 的软件发行包，其中就有
对应的软件包的名字和版本号。

AC_PROG_CC

这个宏将检查系统所用的 C 编译器。

AC_OUTPUT(FILE)

这个宏是我们要输出的 Makefile 的名字。

我们在使用 automake 时，实际上还需要用到其他的一些宏， 但我们可以用 aclocal 来帮我们自动产生。
执行 aclocal 后我们会得到 aclocal.m4 文件。

产生了 configure.in 和 aclocal.m4 两个宏文件后，我们就可以使用 autoconf 来产生 configure 文件了。

###Makefile.am

Makefile.am 是用来生成 Makefile.in 的，需要你手工书写。Makefile.am 中定义了一些内容：

AUTOMAKE_OPTIONS

这个是 automake 的选项。在执行 automake 时，它会检查目录下是否存在标准 GNU 软件包中应具备的各种文件，
例如AUTHORS 、ChangeLog 、NEWS 等文件。我们将其设置成foreign 时，automake 会改用一般软件包的标准来检查。

bin_PROGRAMS

这个是指定我们所要产生的可执行文件的文件名。如果你要产生多个可执行文件，那么在各个名字间用空格隔开。

helloworld_SOURCES

这个是指定产生 "helloworld" 时所需要的源代码。如果它用到了多个源文件，那么请使用空格符号将它们隔开。
比如需要 helloworld.h ，helloworld.c 那么请写成 helloworld_SOURCES= helloworld.h helloworld.c 。

如果你在 bin_PROGRAMS 定义了多个可执行文件，则对应每个可执行文件都要定义相对的 filename_SOURCES 。

###automake

我们使用 automake --add-missing 来产生 Makefile.in 。

选项 --add-missing 的定义是"add missing standard files to package" ，它会让 automake 加入一个标准的
软件包所必须的一些文件。

我们用 automake 产生出来的 Makefile.in 文件是符合 GNU Makefile 惯例的，接下来我们只要执行 configure
这个shell 脚本就可以产生合适的 Makefile 文件了。

###Makefile

在符合GNU Makefiel 惯例的Makefile 中，包含了一些基本的预先定义的操作：

make

根据 Makefile 编译源代码，连接，生成目标文件，可执行文件。

make clean

清除上次的make 命令所产生的 object 文件（后缀为 ".o" 的文件）及可执行文件。

make install

将编译成功的可执行文件安装到系统目录中，一般为/usr/local/bin 目录。

make dist

产生发布软件包文件（即distribution package）。这个命令将会将可执行文件及相关文件打包成一个tar.gz
压缩的文件用来作为发布软件的软件包。

它会在当前目录下生成一个名字类似 "PACKAGE-VERSION.tar.gz" 的文件。PACKAGE 和 VERSION，是我们在
configure.in 中定义的 AM_INIT_AUTOMAKE(PACKAGE, VERSION)。

make distcheck

生成发布软件包并对其进行测试检查，以确定发布包的正确性。这个操作将自动把压缩包文件解开，然后执行
configure 命令，并且执行 make，来确认编译不出现错误，最后提示你软件包已经准备好，可以发布了。

make distclean

类似make clean，但同时也将 configure 生成的文件全部删除掉，包括 Makefile。



