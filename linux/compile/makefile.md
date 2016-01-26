
$ tree

	src
	makefile
	lib/
	lib/makefile
	obj/
	obj/makefile
	include/*.h



###makefile

CC := gcc  
SUBDIRS := lib src obj  
BIN := main  
PWD := $(shell pwd)  
OBJS_DIR := $(PWD)/obj  
BIN_DIR := $(PWD)/bin  
export CC PWD BIN OBJS_DIR BIN_DIR  
all : CHECK_DIR $(SUBDIRS)  
CHECK_DIR :  
<span style="white-space:pre">  </span>mkdir -p $(BIN_DIR)  
<span style="white-space:pre">  </span>  
$(SUBDIRS) : ECHO  
<span style="white-space:pre">  </span>make -C $@  
<span style="white-space:pre">  </span>  
ECHO :  
<span style="white-space:pre">  </span>@echo $(SUBDIRS)  
<span style="white-space:pre">  </span>@echo begin complie  
<span style="white-space:pre">  </span>  
CLEAN :  
<span style="white-space:pre">  </span>@rm -rf $(OBJS_DIR)/*.o  
<span style="white-space:pre">  </span>@rm -rf $(BIN_DIR)  

###lib/makefile

    AR := ar rc  
      
    LOCAL_SRC := $(wildcard *.c)  
    LOCAL_OBJ := $(patsubst %.c,%.o,$(LOCAL_SRC))  
    CFLAGS := -c  
    LIB := libxid.a  
      
    .PHONY : all  
      
    all : ECHO $(LIB)   
      
    ECHO :  
        @echo $(LOCAL_OBJ)  
          
      
    $(LIB) : $(LOCAL_OBJ)  
        $(AR) $(LIB) $^  
        #mv $(LIB) $(LIB_DIR)  
      
    $(LOCAL_OBJ) : $(LOCAL_SRC)  
        $(CC) $(CFLAGS) $(LOCAL_SRC) -I$(INCLUDE_DIR)   


###src/makefile

    CFLAGS = -c  
    LOCAL_SRC := $(wildcard *.c)  
    LOCAL_OBJ := $(patsubst %.c,%.o,$(LOCAL_SRC))   
      
    #$(BIN) : $(LOCAL_OBJ)  
        #$(CC) $(CFLAGS) $(BIN) $(LOCAL_OBJ) -L$(LIB_DIR) -lxid  
      
    $(LOCAL_OBJ) : $(LOCAL_SRC)  
        $(CC) $(CFLAGS) $(LOCAL_SRC) -I$(INCLUDE_DIR) -I$(LIB_DIR)  
        -mv $(LOCAL_OBJ) $(OBJS_DIR)  
      
    clean :  
        -rm -rf *.o  

###obj/makefile

    LOCAL_OBJ := $(wildcard *.o)  
    CFLAGS = -o  
      
    $(BIN) : $(LOCAL_OBJ)  
        $(CC) $(CFLAGS) $@ $^ -L$(LIB_DIR) -lxid -lpthread  
        -mv $(BIN) $(BIN_DIR)   



##递归式Makefile模板 

自已写的程序，源文件分在了不同的目录，需要make来管理。参考了很多的Makefile模板，一直没有找到合适的，于是动手自已写了一个，花费了我一天时间来看文档，然后动手实践。

先看一下我的目录结构：

.
├── list
│   ├── list.c
│   ├── list.h
│   ├── main.c
│   └── Makefile
├── Makefile
├── Makefile.in
└── platform
    └── platform.h

2 directories, 7 files


其中根目录下有两个Makefile, 一个用来递归编译，一个Makefile.in用来实现公共的命令及操作。子目录list下有自已的Makefile, 用来编译本目录下的文件。
首先讲解一下根目录下的Makefile:

 1 DIRS=list 　　　　//定义要编译的目录，这里只有一个list目录.
 2 
 3 all:　　　　　　　 //编译目标，递归式编译，进入到各级目录进行编译.
 4     @for dir in $(DIRS) ; do \
 5         if test -d $$dir ; then \
 6             echo "$$dir: $(MAKE) $@" ; \
 7             if (cd $$dir; $(MAKE) $@) ; then \
 8                 true; \
 9             else \
10                 exit 1; \
11             fi; \
12         fi \
13     done
14 
15 clean:
16     @for dir in $(DIRS) ; do \
17         if test -d $$dir ; then \
18             echo "$$dir: $(MAKE) $@" ; \
19             if (cd $$dir; $(MAKE) $@) ; then \
20                 true; \
21             else \
22                 exit 1; \
23             fi; \
24         fi \
25     done

在Makefile.in中对于各级目录中的共同的操作部分进行了实现，同时对于编译选项进行了定义：

 1 DEBUG = 1
 2 
 3 SOURCE_FOR_C = $(foreach source_file_1, $(SOURCES),$(filter %.c, $(source_file_1)))
 4 #DEPENDS_C    = $(addprefix obj/,$(SOURCE_FOR_C:.c=.c.d))
 5 #OBJS         = $(DEPENDS_C:.c.d=.o)
 6 OBJS         = $(SOURCE_FOR_C:.c=.o)
 7 
 8 CFLAGS += -I$(INCLUDE_DIR) -Werror
 9 ifeq (1,$(DEBUG))
10 CFLAGS += -g
11 endif
12 
13 .PYONY:all clean
14 all:$(TARGET)
15 $(TARGET):$(OBJS)
16     $(CC) $(CFLAGS) $^ -o $@
17 
18 clean:
19     @echo "[CLEAN]"
20     @rm -rfv  *.o *.d *.tmp *.bin *.spz *.spgzip *.lzma *.text $(OBJS) $(DEPENDS) obj *.bak
21     @rm -rfv $(TARGET)

在各级目录下包含此文件，并定义相关的源文件，则在进入到各级目录时进行相关的编译动作：

1 ifndef ROOT_DIR
2 ROOT_DIR = ..
3 endif
4 
5 SOURCES = list.c main.c
6 INCLUDE_DIR = $(ROOT_DIR)/platform
7 TARGET = $(ROOT_DIR)/dslist
8 
9 sinclude $(ROOT_DIR)/Makefile.in

至于，一个用于小型编译的递归式Makefile就初步完成了，可以完成基本的编译动作。编译过程如下：

1 list: make all
2 make[1]: Entering directory `/home/xxx/workspace/google/datastruct/list'
3 cc -I../platform -Werror -g   -c -o list.o list.c
4 cc -I../platform -Werror -g   -c -o main.o main.c
5 cc -I../platform -Werror -g list.o main.o -o ../dslist
6 make[1]: Leaving directory `/home/xxx/workspace/google/datastruct/list'

至于再添加新的目录，可以按照此结构进行。

不过，还遗留一个问题。我修改了platform/platform.h中的内容，不会进行更新编译。估计是因为没有添加.c.d编译规则的原因吧，再查!
人生有限，要聚集你的精力到一件事情上，做到最好！


##例子

　　建立一个测试目录，在测试目录下建立一个名为sub的子目录

　　$ mkdir test

　　$ cd test

　　$ mkdir sub

　　在test下，建立a.c和b.c2个文件，在sub目录下，建立sa.c和sb.c2 个文件

　　建立一个简单的Makefile

　　src=$(wildcard *.c ./sub/*.c)

　　dir=$(notdir $(src))

　　obj=$(patsubst %.c,%.o,$(dir) )

　　all:

　　@echo $(src)

　　@echo $(dir)

　　@echo $(obj)

　　@echo "end"


执行结果分析：

第一行输出：

　　a.c b.c ./sub/sa.c ./sub/sb.c

wildcard把 指定目录 ./ 和 ./sub/ 下的所有后缀是c的文件全部展开。

第二行输出：

　　a.c b.c sa.c sb.c

notdir把展开的文件去除掉路径信息

第三行输出：

　　a.o b.o sa.o sb.o

在$(patsubst %.c,%.o,$(dir) )中，patsubst把$(dir)中的变量符合后缀是.c的全部替换成.o，

任何输出或者可以使用

　　obj=$(dir:%.c=%.o)

效果也是一样的。这里用到 makefile 里的替换引用规则，即用您指定的变量替换另一个变量。

它的标准格式是

　　$(var:a=b) 或 ${var:a=b}

它的含义是把变量var中的每一个值结尾用b替换掉a

###wildcard 扩展通配符

　　SRC = $(wildcard *.c)

等于指定编译当前目录下所有.c文件，如果还有子目录，比如子目录为inc，则再增加一个wildcard函数，象这样：

　　SRC = $(wildcard *.c) $(wildcard inc/*.c)

也可以指定汇编源程序：

　　ASRC = $(wildcard *.S)

###notdir 去除路径

###patsubst 替换通配符


格式：$(patsubst <pattern>,<replacement>,<text> )

名称：模式字符串替换函数——patsubst。

功能：查找<text>中的单词（单词以“空格”、“Tab”或“回车”“换行”分隔）是否符合模式<pattern>，如果匹配的话，
则以<replacement>替换。这里，<pattern>可以包括通配符“%”，表示任意长度的字串。如果<replacement>中也包含“%”，
那么，<replacement>中的这个“%”将是<pattern>中的那个“%”所代表的字串。（可以用“\”来转义，以“\%”来表示真实含义的“%”字符）

返回：函数返回被替换过后的字符串。

示例：

　　$(patsubst %.c,%.o,x.c.c bar.c)

把字串“x.c.c bar.c”符合模式[%.c]的单词替换成[%.o]，返回结果是“x.c.o bar.o”

make中有个变量替换引用

对于一个已经定义的变量，可以使用“替换引用”将其值中的后缀字符（串）使用指定的字符（字符串）替换。
格式为“$(VAR:A=B)”（或者“${VAR:A=B}”），意思是，替换变量“VAR”中所有“A”字符结尾的字为“B”结尾的字。
“结尾”的含义是空格之前（变量值多个字之间使用空格分开）。而对于变量其它部分的“A”字符不进行替换。例如：

　　foo := a.o b.o c.o

　　bar := $(foo:.o=.c)

在这个定义中，变量“bar”的值就为“a.c b.c c.c”。使用变量的替换引用将变量“foo”以空格分开的值中的所有的字
的尾字符“o”替换为“c”，其他部分不变。如果在变量“foo”中如果存在“o.o”时，那么变量“bar”的值为“a.c b.c c.c o.c”
而不是“a.c b.c c.c c.c”。

它是patsubst的一个简化，那么到底是简化成了什么样子呢

　　CROSS=

　　CC=$(CROSS)gcc

　　CFLAGS= -Wall

　　LDFLAGS=

　　PKG = src

　　SRCS = $(wildcard $(PKG)/inc/*.c) $(wildcard $(PKG)/*.c)

　　BOJS = $(patsubst %.c,%.o,$(SRCS))

　　#BOJS = $(SRCS: .c = .o)

　　#%.o:%.c

　　# $(CC) -c $< $(CFLAGS) -o $@

　　.PHONY:main

　　main:$(BOJS)

　　-$(CC) -o $@ $(CFLAGS) $^ $(LDFLAGS)

　　-mv main ./myfile

起初使用的是变量替换引用的方式，但是却始终不生成中间的.o文件，但是使用 patsubst 后，一切正常了.

