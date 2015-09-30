
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


