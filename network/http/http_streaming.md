##视频基础知识

###帧的概念（Frame）

一个视频序列是由N个帧组成的，采集图像的时候一般有2种扫描方式，一种是逐行扫描（progressive scanning），一种是隔行扫描（interlaced scanning）。对于隔行扫描，每一帧一般有2个场（field），一个叫顶场（top field），一个叫底场（bottom field）。假设一帧图像是720行，那么，顶场就包含其中所有的偶数行，而底场则包含其中所有的奇数行。


##HTTP应用流媒体分析

 严格意义上，基于HTTP的 VOD 不算是真的流媒体，英文称为“progressive downloading”或者“pseudo streaming”，为什么这样呢？因为HTTP缺乏流媒体基本的流控，由此基于HTTP协议很难实现媒体播放的快进，快退，暂停。那么，通常的媒体播 放器又是如何利用HTTP来实现这样的功能呢？

我们都知道，不管媒体文件有多大，HTTP都只是视它为一个HTTP的元素，可以只需要发送一个HTTP请求，WEB Server就会源源不断地将媒体流推送给客户端，而不管客户端是否接受，这就是HTTP协议本身没有流控的原因，那这样会带来什么后果呢？

如果服务器的推流速度和客户端同步， 那么基本不会出现什么大问题；如果小于客户端的接收流的速度，那么播放就会一卡一卡的；如果大于或者远大于客户端的接收速度，那又会是怎么样的结果呢？很 不幸，在我们所有的ISTV项目中，只要是基于HTTP的VOD，都无一例外是第三种情况。因为我们VOD是基于局域网的，大家都知道，局域网的带宽资源 是很丰富的，服务器的推流的速度肯定大于播放器的播放速度，那么在这么速度极端不协调的情况下，服务器的推流速度究竟由谁来限制呢？

答案是：TCP协议栈。我们的VOD点播是基于TCP的HTTP协议。TCP是安全的，可靠的，包肯定不会丢，服务器检测到客户端的接收缓冲区满了，就会减小发送数据滑动窗口的大小。所以HTTP的流控是通过TCP协议栈来调节的，不是HTTP本身。试想，这样对服务器造成的压力有多大！！！
    
下面就分析基于HTTP协议如何实现SEEK，PAUSE等操作。

###SEEK（快进和快退）

先关闭之前的tcp连接，重新连接，发送http请求，该请求带了媒体的偏移位置。由此可见，每一次的快进和快退，都等于是重新开始播放，只是每次开始播放的位置不一样。

###PAUSE

该操作就更有意思了，客户端暂停了播放，也就是不从缓冲区读取数据了，但是服务器不知道客户端停止了播放，依然不停地发送数据给客户端，直到客户端的接收 缓冲区已满，然后服务器的数据发送不出去了，理论上是服务器端的滑动窗口的大小估计就是0了，然后协议栈还在不停在尝试发送数据，因为是基于 tcp，这些 数据还不能丢。nnd，这种方式实现暂停，协议栈都哭了。很不幸，MPLAYER 就是这么干的。所以暂停的时间长了，就容易出现问题。

虽然 HTTP 没有 PAUSE 的支持，但是针对 PAUSE 是可以优化的，优化的方法是，将媒体文件分片，分片的大小以稍小于 TCP 协议栈的缓冲区大小为宜。 HTTP请求一次只请求一个分片的大小，暂停播放后，就不在发送分片请求了。这样可以保证让服务器运行的时间长一些，播放器暂停理论上可以无限长了。


##V4L2

Video4linux2（简称V4L2),是linux中关于视频设备的内核驱动。在Linux中，视频设备是设备文件，可以像访问普通文件一样对其进行读写，摄像头在/dev/video0下。

###一般操作流程（视频设备）

* 打开设备文件。 int fd=open(”/dev/video0″,O_RDWR);
* 取得设备的capability，比如是否具有视频输入,或者音频输入输出等。
* 设置视频的制式和帧格式，制式包括PAL，NTSC，帧的格式个包括宽度和高度等。
* 向驱动申请帧缓冲，一般不超过5个
* 将申请到的帧缓冲映射到用户空间(mmap)，这样就可以直接操作采集到的帧了，而不必去复制
* 将申请到的帧缓冲全部入队列，以便存放采集到的数据 
* 开始视频的采集
* 出队列以取得已采集数据的帧缓冲，取得原始采集数据
* 将缓冲重新入队列尾,这样可以循环采集
* 停止视频的采集
* 关闭视频设备

###常用的结构体(参见/usr/include/linux/videodev2.h)

* struct v4l2_capability cap;     //这个设备的功能，对应命令VIDIOC_QUERYCAP
* struct v4l2_standard std;       //视频的制式，比如PAL，NTSC，对应命令VIDIOC_ENUMSTD
* struct v4l2_requestbuffers reqbufs;//向驱动申请帧缓冲的请求，对应命令VIDIOC_REQBUFS
* struct v4l2_format fmt;         //帧的格式，比如宽度，高度等，对应命令VIDIOC_G_FMT、VIDIOC_S_FMT等
* struct v4l2_buffer buf;         //代表驱动中的一帧图像缓存，对应命令VIDIOC_QUERYBUF
* struct v4l2_std_id stdid;       //视频制式，例如：V4L2_STD_PAL_B
* struct v4l2_queryctrl query;    //查询的控制
* struct v4l2_control control;    //具体控制的值
* struct v4l2_input   input       //视频输入信息，对应命令VIDIOC_ENUMINPUT
* struct v4l2_crop    crop        //视频信号矩形边框

###具体说明开发流程

####打开视频设备

```
    int cameraFd;
    cameraFd= open(“/dev/video0″, O_RDWR| O_NONBLOCK, 0); //非阻塞式
    cameraFd = open(”/dev/video0″, O_RDWR, 0); //阻塞式
```

应用程序能够使用阻塞模式或非阻塞模式打开视频设备，如果使用非阻塞模式调用视频设备，即使尚未捕获到信息，驱动依旧会把缓存（DQBUFF）里的东西返回给应用程序。

####设定属性及采集方式

打开视频设备后，可以设置该视频设备的属性，例如裁剪、缩放等。这一步是可选的。在Linux编程中，一般使用ioctl函数来对设备的I/O通道进行管理：

```
    extern intioctl(int__fd, unsigned long int__request, …) __THROW;

    __fd：设备的ID，例如刚才用open函数打开视频通道后返回的cameraFd；

    __request：具体的命令标志符。
```

在进行V4L2开发中，一般会用到以下的命令标志符：

* VIDIOC_QUERYCAP： 查询驱动功能 
* VIDIOC_QUERYSTD： 检查当前视频设备支持的标准，例如PAL或NTSC。在亚洲，一般使用PAL（720X576）制式的摄像头，而欧洲一般使用NTSC（720X480）
* VIDIOC_ENUM_FMT： 获取当前驱动支持的视频格式 
* VIDIOC_S_FMT： 设置当前驱动的频捕获格式 
* VIDIOC_G_FMT： 读取当前驱动的频捕获格式 
* VIDIOC_REQBUFS： 分配内存 
* VIDIOC_QUERYBUF： 把 VIDIOC_REQBUFS 中分配的数据缓存转换成物理地址 
* VIDIOC_QBUF： 把数据从缓存中读取出来 
* VIDIOC_DQBUF：把数据放回缓存队列 
* VIDIOC_STREAMON：开始视频显示函数 
* VIDIOC_STREAMOFF：结束视频显示函数 

###具体功能描述

####VIDIOC_QUERYCAP

* 功能： 查询设备驱动的功能;
* 参数： 参数类型为V4L2的能力描述类型struct v4l2_capability;
```
      struct v4l2_capability {
                __u8    driver[16];     /* i.e. "bttv" */            //驱动名称,
                __u8    card[32];       /* i.e. "Hauppauge WinTV" */        //
                __u8    bus_info[32];   /* "PCI:" + pci_name(pci_dev) */    //PCI总线信息
                __u32   version;        /* should use KERNEL_VERSION() */
                __u32   capabilities;   /* Device capabilities */        //设备能力
                __u32   reserved[4];
        };
```
* 返回值：　执行成功时，函数返回值为 0;    
* 举例
```
        struct v4l2_capability cap;
        iret = ioctl(fd_usbcam, VIDIOC_QUERYCAP, &cap);
        if(iret < 0){
                printf("get vidieo capability error,error code: %d \n", errno);
                return ;
        }
```
函数执行成功后，struct v4l2_capability 结构体变量中的返回当前视频设备所支持的功能;例如支持视频捕获功能V4L2_CAP_VIDEO_CAPTURE、 V4L2_CAP_STREAMING等。


####VIDIOC_QUERYSTD

* 功能：　检查当前视频设备支持的标准，例如PAL或NTSC。在亚洲，一般使用PAL（720X576）制式的摄像头，而欧洲一般使用NTSC（720X480）
* 参数：
```
    typedef __u64 v4l2_std_id;

    struct v4l2_format {
    	__u32	 type;
    	union {
    		struct v4l2_pix_format		pix;     /* V4L2_BUF_TYPE_VIDEO_CAPTURE */
    		struct v4l2_pix_format_mplane	pix_mp;  /* V4L2_BUF_TYPE_VIDEO_CAPTURE_MPLANE */
    		struct v4l2_window		win;     /* V4L2_BUF_TYPE_VIDEO_OVERLAY */
    		struct v4l2_vbi_format		vbi;     /* V4L2_BUF_TYPE_VBI_CAPTURE */
    		struct v4l2_sliced_vbi_format	sliced;  /* V4L2_BUF_TYPE_SLICED_VBI_CAPTURE */
    		__u8	raw_data[200];                   /* user-defined */
    	} fmt;
    };
```
* 返回值： 执行成功时，函数返回值为 0;
* 举例

```    
    v4l2_std_id std;
    do{
        ret= ioctl(fd, VIDIOC_QUERYSTD, &std);
    } while(ret== -1 && errno== EAGAIN);

    switch(std) {
        case:V4L2_STD_NTSC:
        //……
        case:V4L2_STD_PAL:

        //……

    }
```

####VIDIOC_ENUM_FMT

* 功能： 获取当前视频设备支持的视频格式 。
* 参数：参数类型为V4L2的视频格式描述符类型 struct v4l2_fmtdesc

```
        struct v4l2_fmtdesc {
                __u32               index;             /* Format number      */
                enum v4l2_buf_type  type;              /* buffer type        */
                __u32               flags;
                __u8                description[32];   /* Description string */
                __u32               pixelformat;       /* Format fourcc      */
                __u32               reserved[4];
        };
```   

* 返回值： 执行成功时，函数返回值为 0;
* 举例：
```
        struct v4l2_fmtdesc fmt;
        memset(&fmt, 0, sizeof(fmt));
        fmt.index = 0;
        fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        while ((ret = ioctl(dev, VIDIOC_ENUM_FMT, &fmt)) == 0) 
        {
                fmt.index++;
                printf("{ pixelformat = ''%c%c%c%c'', description = ''%s'' }\n",
                          fmt.pixelformat & 0xFF, (fmt.pixelformat >> 8) & 0xFF, (fmt.pixelformat >> 16) & 0xFF, 
                          (fmt.pixelformat >> 24) & 0xFF, fmt.description);
        }
```

####VIDIOC_S_FMT：设置当前驱动的频捕获格式 

* 功能： 设置视频设备的视频数据格式，例如设置视频图像数据的长、宽，图像格式(JPEG、YUYV格式);
* 参数： 参数类型为V4L2的视频数据格式类型 struct v4l2_format;
```        
        struct v4l2_format {
                enum v4l2_buf_type type;    //数据流类型，必须永远是V4L2_BUF_TYPE_VIDEO_CAPTURE
                union {
                        struct v4l2_pix_format          pix;     /* V4L2_BUF_TYPE_VIDEO_CAPTURE */
                        struct v4l2_window              win;     /* V4L2_BUF_TYPE_VIDEO_OVERLAY */
                        struct v4l2_vbi_format          vbi;     /* V4L2_BUF_TYPE_VBI_CAPTURE */
                        struct v4l2_sliced_vbi_format   sliced;  /* V4L2_BUF_TYPE_SLICED_VBI_CAPTURE */
                        __u8    raw_data[200];                   /* user-defined */
                } fmt;
        };
        struct v4l2_pix_format {
                __u32                   width;         // 宽，必须是16的倍数
                __u32                   height;        // 高，必须是16的倍数
                __u32                   pixelformat;   // 视频数据存储类型，例如是YUV4：2：2还是RGB
                enum v4l2_field       field;
                __u32                   bytesperline;
                __u32                   sizeimage;
                enum v4l2_colorspace colorspace;
                __u32                   priv;
        };
```   
* 返回值： 执行成功时，函数返回值为 0;
* 举例
```
        struct v4l2_format    fmt;
        memset( &fmt, 0, sizeof(fmt) );
        fmt.type= V4L2_BUF_TYPE_VIDEO_CAPTURE;
        fmt.fmt.pix.width= 720;
        fmt.fmt.pix.height= 576;
        fmt.fmt.pix.pixelformat= V4L2_PIX_FMT_YUYV;
        fmt.fmt.pix.field= V4L2_FIELD_INTERLACED;
        if(ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
            return-1;
        }

```


####VIDIOC_G_FMT

* 功能：　读取当前驱动的频捕获格式 
* 参数：　
* 注意：如果该视频设备驱动不支持你所设定的图像格式，视频驱动会重新修改struct v4l2_format结构体变量的值为该视频设备所支持的图像格式，所以在程序设计中，设定完所有的视频格式后，要获取实际的视频格式，要重新读取 struct v4l2_format 结构体变量。使用 VIDIOC_G_FMT设 置视频设备的视频数据格式，VIDIOC_TRY_FMT 验证视频设备的视频数据格式。

#### VIDIOC_G_PARM  VIDIOC_S_PARM
* 功能：
* 参数：
struct v4l2_streamparm {
	__u32	 type;			/* enum v4l2_buf_type */
	union {
		struct v4l2_captureparm	capture;
		struct v4l2_outputparm	output;
		__u8	raw_data[200];  /* user-defined */
	} parm;
};

*　返回值
*  举例
```
     struct v4l2_streamparm setfps={0}; 
     setfps.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
     setfps.parm.capture.timeperframe.numerator = 1;
     setfps.parm.capture.timeperframe.denominator = fps;
 
     if (-1 == ioctl(cam->camera_fd, VIDIOC_S_PARM, &setfps))
     {
         printf("ioctl request VIDIOC_S_PARM error: %s\n", strerror(errno));                                                              
         return -1;
     }
```





#### VIDIOC_REQBUFS

* 功能： 请求V4L2驱动分配视频缓冲区(申请V4L2视频驱动分配内存)，V4L2 是视频设备的驱动层，位于内核空间，所以通
过 VIDIOC_REQBUFS 控制命令字申请的内存位于内核空间，应用程序不能直接访问，需要通过调用mmap内存映射函数把内核
空间内存映射到用户空间后，应用程序通过访问用户空间地址来访问内核空间。

* 参数：参数类型为 V4L2 的申请缓冲区数据结构体类型
```
        struct v4l2_requestbuffers {
                u32                   count;        //缓存数量,也就是说在缓存队列里保持多少张照片
                enum v4l2_buf_type    type;         //数据流类型,必须永远是V4L2_BUF_TYPE_VIDEO_CAPTURE
                enum v4l2_memory      memory;       //V4L2_MEMORY_MMAP或V4L2_MEMORY_USERPTR
                u32                   reserved[2];
        };
```
* 返回值： 执行成功时，函数返回值为 0，V4L2驱动层分配好了视频缓冲区;

```
    struct v4l2_requestbuffers tV4L2_reqbuf;
    memset(&tV4L2_reqbuf, 0, sizeof(struct v4l2_requestbuffers ));
    tV4L2_reqbuf.count = 1;             //申请缓冲区的个数
    tV4L2_reqbuf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    tV4L2_reqbuf.memory = V4L2_MEMORY_MMAP;        //mmap方式
    iret = ioctl(fd_usbcam, VIDIOC_REQBUFS, &tV4L2_reqbuf);

```
* 注意：VIDIOC_REQBUFS会修改tV4L2_reqbuf的count值，tV4L2_reqbuf的count值返回实际申请成功的视频缓冲区数目;


####VIDIOC_QUERYBUF
* 功能： 查询已经分配的V4L2的视频缓冲区的相关信息，包括视频缓冲区的使用状态、在内核空间的偏移地址、缓冲区长度等。
在应用程序设计中通过调 VIDIOC_QUERYBUF来获取内核空间的视频缓冲区信息，然后调用函数mmap把内核空间地址映射到用户
空间，这样应用程序才能够访问位于内核空间的视频缓冲区。

* 参数：参数类型为V4L2缓冲区数据结构类型 struct v4l2_buffer;

```
    struct v4l2_buffer {
            __u32                   index;
            enum v4l2_buf_type      type;
            __u32                   bytesused;
            __u32                   flags;
            enum v4l2_field         field;
            struct timeval          timestamp;
            struct v4l2_timecode    timecode;
            __u32                   sequence;
            /* memory location */
            enum v4l2_memory        memory;
            union {
                    __u32           offset;
                    unsigned long   userptr;
            } m;
            __u32                   length;
            __u32                   input;
            __u32                   reserved;
    };
```
* 返回值： 执行成功时，函数返回值为 0;
* 举例

struct v4l2_buffer 结构体变量中保存了指令的缓冲区的相关信息;一般情况下，应用程序中调用 VIDIOC_QUERYBUF 
取得了内核缓冲区信息后，紧接着调用 mmap 函数把内核空间地址映射到用户空间,方便用户空间应用程序的访问。

```
    typedef struct VideoBuffer{
        void*start;
        size_t  length;
    } VideoBuffer;

    VideoBuffer*          buffers= calloc( req.count, sizeof(*buffers) );
    struct v4l2_buffer    buf;

    for(numBufs= 0; numBufs< req.count; numBufs++) {
        memset( &buf, 0, sizeof(buf) );
        buf.type= V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory= V4L2_MEMORY_MMAP;
        buf.index= numBufs;
        //读取缓存
        if(ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
            return -1;
        }
        buffers[numBufs].length= buf.length;
        //转换成相对地址,把内核空间缓冲区映射到用户空间缓冲区
        buffers[numBufs].start= mmap(NULL, buf.length,
                                    PROT_READ| PROT_WRITE,
                                    MAP_SHARED,
                                    fd, buf.m.offset);
        if(buffers[numBufs].start== MAP_FAILED) {
            return -1;
        }
    }
```

操作系统一般把系统使用的内存划分成用户空间和内核空间，分别由应用程序管理和操作系统管理。应用程序可以直接访问内存的地址，而内核空间存放的是供内核访问的代码和数据，用户不能直接访问。v4l2捕获的数据，最初是存放在内核空间的，这意味着用户不能直接访问该段内存，必须通过某些手段来转换地址。

一共有三种视频采集方式:

* read、write方式:在用户空间和内核空间不断拷贝数据，占用了大量用户内存空间，效率不高。
* 内存映射方式：把设备里的内存映射到应用程序中的内存控件，直接处理设备内存，这是一种有效的方式。上面的mmap函数就是使用这种方式。
* 用户指针模式：内存片段由应用程序自己分配。这点需要在v4l2_requestbuffers里将memory字段设置成V4L2_MEMORY_USERPTR。



####VIDIOC_QBUF

* 功能： 投放一个空的视频缓冲区到视频缓冲区输入队列中;
* 参数： 参数类型为V4L2缓冲区数据结构类型 struct v4l2_buffer;
* 返回值： 执行成功时，函数返回值为 0;
* 举例： 函数执行成功后，指令(指定)的视频缓冲区进入视频输入队列，在启动视频设备拍摄图像时，相应的视频数据被保存到视频输入队列相应的视频缓冲区中。

```   
    struct v4l2_buffer tV4L2buf;

    memset(&tV4L2buf, 0, sizeof(struct v4l2_buffer));

    tV4L2buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    tV4L2buf.memory = V4L2_MEMORY_MMAP;
    tV4L2buf.index = i; //指令(指定)要投放到视频输入队列中的内核空间视频缓冲区的编号;

    iret = ioctl(fd_usbcam, VIDIOC_QBUF, &tV4L2buf);
```


####VIDIOC_DQBUF
* 功能： 从视频缓冲区的输出队列中取得一个已经保存有一帧视频数据的视频缓冲区;
* 参数： 参数类型为V4L2缓冲区数据结构类型 struct v4l2_buffer;
* 返回值： 执行成功时，函数返回值为 0;
* 举例：
函数执行成功后，相应的内核视频缓冲区中保存有当前拍摄到的视频数据，
应用程序可以通过访问用户空间来读取该视频数据。(前面已经通过调用函数 mmap做了用户空间和内核空间的内存映射).

```
    structv 4l2_buffer buf;
    memset(&buf,0,sizeof(buf));
    buf.type=V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory=V4L2_MEMORY_MMAP;
    buf.index=0;
    //读取缓存
    if(ioctl(cameraFd, VIDIOC_DQBUF, &buf) == -1)
    {
        return -1;
    }

    //…………视频处理算法

    //重新放入缓存队列
    if(ioctl(cameraFd, VIDIOC_QBUF, &buf) == -1) {
        return -1;
    }
```

* VIDIOC_CROPCAP：查询驱动的修剪能力 
* VIDIOC_S_CROP：设置视频信号的边框 
* VIDIOC_G_CROP：读取视频信号的边框 


####VIDIOC_STREAMON
* 功能： 启动视频采集命令，应用程序调用VIDIOC_STREAMON启动视频采集命令后，视频设备驱动程序开始采集视频数据，并把采集到的视频数据保存到视频驱动的视频缓冲区中。
* 参数：参数类型为V4L2的视频缓冲区类型 enum v4l2_buf_type ;

```
        enum v4l2_buf_type {
                V4L2_BUF_TYPE_VIDEO_CAPTURE        = 1,
                V4L2_BUF_TYPE_VIDEO_OUTPUT         = 2,
                V4L2_BUF_TYPE_VIDEO_OVERLAY        = 3,
                V4L2_BUF_TYPE_VBI_CAPTURE          = 4,
                V4L2_BUF_TYPE_VBI_OUTPUT           = 5,
                V4L2_BUF_TYPE_SLICED_VBI_CAPTURE   = 6,
                V4L2_BUF_TYPE_SLICED_VBI_OUTPUT    = 7,
        #if 1
                /* Experimental */
                V4L2_BUF_TYPE_VIDEO_OUTPUT_OVERLAY = 8,
        #endif
                V4L2_BUF_TYPE_PRIVATE              = 0x80,
        };
```   
* 返回值： 执行成功时，函数返回值为 0;函数执行成功后，视频设备驱动程序开始采集视频数据，此时应用程序一般通过调用select函数来判断一帧视频数据是否采集完成，当视频设备驱动完成一帧视频数据采集并保存到视频缓冲区中时，select函数返回，应用程序接着可以读取视频数据;否则select函数阻塞直到视频数据采集完成。 Select函数的使用请读者参考相关资料。

* 举例：
```
    enum v4l2_buf_type v4l2type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    fd_set fds ;
    struct timeval tv;

    iret = ioctl(fd_usbcam, VIDIOC_STREAMON, &v4l2type);

    FD_ZERO(&fds);
    FD_SET(fd_usbcam, &fds);
    tv.tv_sec = 2; /* Timeout. */
    tv.tv_usec = 0;
    iret = select(fd_usbcam+ 1, &fds, NULL, NULL, &tv);
```

####VIDIOC_STREAMOFF
* 功能： 停止视频采集命令，应用程序调用VIDIOC_ STREAMOFF停止视频采集命令后，视频设备驱动程序不在采集视频数据。
* 参数：参数类型为V4L2的视频缓冲区类型 enum v4l2_buf_type;
* 返回值： 执行成功时，函数返回值为 0;函数执行成功后，视频设备停止采集视频数据。
* 举例：
```
        enum v4l2_buf_type v4l2type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

        iret = ioctl(fd_usbcam, VIDIOC_STREAMOFF, &v4l2type);
```
使用close函数关闭一个视频设备 `close(cameraFd)` 还需要使用munmap方法。
    
以上就是Linux 视频设备驱动V4L2最常用的控制命令使用说明，通过使用以上控制命令，可以完成一幅视频数据的采集过程。

##代码

    #include <stdio.h>
    #include <stdlib.h>
    #include <string.h>
    #include <assert.h>
    #include <getopt.h>
    #include <fcntl.h>
    #include <unistd.h>
    #include <errno.h>
    #include <malloc.h>
    #include <sys/stat.h>
    #include <sys/types.h>
    #include <sys/time.h>
    #include <sys/mman.h>
    #include <sys/ioctl.h>
    #include <asm/types.h>
    #include <linux/videodev2.h>

    #define CLEAR(x) memset (&(x), 0, sizeof (x))

    struct buffer {
            void *                  start;
            size_t                  length;
    };

    static char *           dev_name        = "/dev/video0";//摄像头设备名
    //static int              fd              = -1;
    struct buffer *         buffers         = NULL;
    static unsigned int     n_buffers       = 0;

    FILE *file_fd;

    #define BUF_COUNT          2

    #define VIDEO_WIDTH      620    
    #define VIDEO_HEIGHT     480
    //V4L2_PIX_FMT_JPEG;V4L2_PIX_FMT_YUYV;V4L2_PIX_FMT_YVU420;V4L2_PIX_FMT_YUYV;
    #define VIDEO_FORMAT     V4L2_PIX_FMT_YUYV

    typedef struct VideoBuffer {
        void   *start;
        size_t  length;
    } VideoBuffer;

    VideoBuffer framebuf[BUFFER_COUNT]


    static unsigned long file_length;
    static unsigned char *file_name;

    //获取一帧数据
    static int write_frame_to_fd (file_fd)
    {
        //取出FIFO缓存中已经采样的帧缓存
        struct v4l2_buffer buf;
        CLEAR (buf);
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        buf.index=0;
        int ret = ioctl(fd, VIDIOC_DQBUF, &buf);
        if( ret < 0 ){
            printf("VIDIOC_DQBUF error: %s\n",strerror(errno)); //出列采集的帧缓冲
            return -1;
        }

        assert (buf.index < n_buffers);
        printf ("buf.index dq is %d,\n",buf.index);
        fwrite(buffers[buf.index].start, buffers[buf.index].length, 1, file_fd); //将其写入文件中
        
        //将刚刚处理完的缓冲重新入队列尾，这样可以循环采集
        ff=ioctl (fd, VIDIOC_QBUF, &buf); //再将其入列
        if(ff<0){
            printf("failture VIDIOC_QBUF\n");
            return -1;
        }
        return 1;
    }

    int main (int argc,char ** argv)
    {
        int ret,i;

        // 打开设备
        int fd = open (dev_name, O_RDWR /* required */ | O_NONBLOCK, 0);
        if(fd < 0){
            printf("open video device error : %s\n", strerror(errno));
            return -1;        
        }
        
        // 获取驱动信息
        struct v4l2_capability cap;
        ret = ioctl(fd, VIDIOC_QUERYCAP, &cap);
        if ( ret < 0 ) {
            printf("VIDIOC_QUERYCAP error : %s \n", strerror(errno));
            return -1;
        }

        printf("Capability Informations:\n");
        printf(" driver: %s\n", cap.driver);
        printf(" card: %s\n", cap.card);
        printf(" bus_info: %s\n", cap.bus_info);
        printf(" version: %08X\n", cap.version);
        printf(" capabilities: %08X\n", cap.capabilities);

        // 设置视频格式
        struct v4l2_format fmt;
        memset(&fmt, 0, sizeof(fmt));
        fmt.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        fmt.fmt.pix.width       = VIDEO_WIDTH;
        fmt.fmt.pix.height      = VIDEO_HEIGHT;
        fmt.fmt.pix.pixelformat = VIDEO_FORMAT
        fmt.fmt.pix.field       = V4L2_FIELD_INTERLACED;
        ret = ioctl (fd, VIDIOC_S_FMT, &fmt); //设置图像格式
        if( ret < 0 ){
            printf("failture VIDIOC_S_FMT error: %s \n", strerror(errno));
            return -1;        
        }

        // 获取视频格式
        ret = ioctl(fd, VIDIOC_G_FMT, &fmt);
        if (ret < 0) {
            printf("VIDIOC_G_FMT error : %s\n", strerror(errno));
            return -1;
        }

        printf("Stream Format Informations:\n");
        printf(" type: %d\n", fmt.type);
        printf(" width: %d\n", fmt.fmt.pix.width);
        printf(" height: %d\n", fmt.fmt.pix.height);
        
        char fmtstr[8];
        memset(fmtstr, 0, 8);
        memcpy(fmtstr, &fmt.fmt.pix.pixelformat, 4);
        printf(" pixelformat: %s\n", fmtstr);
        printf(" field: %d\n", fmt.fmt.pix.field);
        printf(" bytesperline: %d\n", fmt.fmt.pix.bytesperline);
        printf(" sizeimage: %d\n", fmt.fmt.pix.sizeimage);
        printf(" colorspace: %d\n", fmt.fmt.pix.colorspace);
        printf(" priv: %d\n", fmt.fmt.pix.priv);
        printf(" raw_date: %s\n", fmt.fmt.raw_data);   

        /*
        struct v4l2_fmtdesc fmt1;
        memset(&fmt1, 0, sizeof(fmt1));
        fmt1.index = 0;
        fmt1.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

        int ret;
        while ((ret = ioctl(fd, VIDIOC_ENUM_FMT, &fmt1)) == 0)
        {
            fmt1.index++;
            printf("{ pixelformat = '%c%c%c%c', description = '%s' }\n",
                    fmt1.pixelformat & 0xFF,
                    (fmt1.pixelformat >> 8) & 0xFF,
                    (fmt1.pixelformat >> 16) & 0xFF,
                    (fmt1.pixelformat >> 24) & 0xFF,
                    fmt1.description);
        }


        file_length = fmt.fmt.pix.bytesperline * fmt.fmt.pix.height; //计算图片大小
        */


        struct v4l2_requestbuffers req;
        CLEAR (req);
        req.count               = BUF_COUNT;
        req.type                = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        req.memory              = V4L2_MEMORY_MMAP;
        ret = ioctl (fd, VIDIOC_REQBUFS, &req); //申请缓冲，count是申请的数量
        if( ret < 0){
            printf(" VIDIOC_REQBUFS error: %s\n", strerror(errno));
            return -1;
        }
        if (req.count < 1){
            printf("Insufficient buffer memory\n");
            return -1;
        }

        // 获取空间
        buffers = calloc (req.count, sizeof (*buffers));//内存中建立对应空间
        struct v4l2_buffer buf;   //驱动中的一帧
        
        for (n_buffers = 0; n_buffers < req.count; ++n_buffers)
        {
            CLEAR (buf);
            buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory      = V4L2_MEMORY_MMAP;
            buf.index       = n_buffers;

            if ((ret = ioctl (fd, VIDIOC_QUERYBUF, &buf)) < 0){ //映射用户空间
                printf ("VIDIOC_QUERYBUF error: %s\n", strerror(errno));
                return -1;
            }

            //mmap 从内核空间到用户空间
            buffers[n_buffers].length = buf.length;
            buffers[n_buffers].start = 
            (char *)mmap (NULL /* start anywhere */,    //通过mmap建立映射关系
                        buf.length,
                        PROT_READ | PROT_WRITE /* required */,
                        MAP_SHARED /* recommended */,
                        fd, buf.m.offset);

            if (MAP_FAILED == buffers[n_buffers].start){
                    printf ("mmap failed\n");
                    return -1;
            }

            ret = ioctl(fd , VIDIOC_QBUF, &buf);
            if (ret < 0) {
                printf("VIDIOC_QBUF (%d) failed (%d)\n", i, ret);
                return -1;
            }
            printf("Frame buffer %d: address=0x%x, length=%d\n", 
                        i, 
                        (unsigned int)framebuf[i].start, 
                        framebuf[i].length);
        }

        /*
        for (i = 0; i < n_buffers; ++i)
        {
            struct v4l2_buffer buf;
            CLEAR (buf);
            buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
            buf.memory      = V4L2_MEMORY_MMAP;
            buf.index       = i;
            //申请到的缓冲进入列队
            if (-1 == ioctl (fd, VIDIOC_QBUF, &buf)) {
                printf ("VIDIOC_QBUF error: %s\n", strerror(errno));
                return -1;
            }
        }
        */


        //开始捕捉图像数据
        enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

        if ((ret = ioctl (fd, VIDIOC_STREAMON, &type)) < 0){ 
            printf ("VIDIOC_STREAMON error: %s\n", strerror(errno));
            return -1;
        }

        // Get frame
        ret = ioctl(fd, VIDIOC_DQBUF, &buf);
        if (ret < 0) {
            printf("VIDIOC_DQBUF failed (%d)\n", ret);
            return ret;
        }

        
        // Process the frame
        file_fd = fopen("test-mmap.jpg", "w");//图片文件名

        for (;;) //这一段涉及到异步IO
        {
            fd_set fds;
            struct timeval tv;
            int r;
            FD_ZERO (&fds);//将指定的文件描述符集清空
            FD_SET (fd, &fds);//在文件描述符集合中增加一个新的文件描述符

            /* Timeout. */
            tv.tv_sec = 2;
            tv.tv_usec = 0;
            r = select (fd + 1, &fds, NULL, NULL, &tv);//判断是否可读（即摄像头是否准备好），tv是定时

            if (-1 == r) {
                if (EINTR == errno)
                    continue;
                printf ("select err\n");
            }

            if (0 == r) {
                fprintf (stderr, "select timeout\n");
                exit (EXIT_FAILURE);
            }
            //如果可读，执行read_frame ()函数，并跳出循环
            if (write_frame_to_fd (file_fd))
                break;
        }

    unmap:

        for (i = 0; i < n_buffers; ++i){
        if (-1 == munmap (buffers[i].start, buffers[i].length))
                printf ("munmap error");
        }
        type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        if (-1 == ioctl(fd, VIDIOC_STREAMOFF, &type))
            printf("VIDIOC_STREAMOFF");
        close (fd);
        fclose (file_fd);
        exit (EXIT_SUCCESS);
        return 0;
    }

http://linuxtv.org/downloads/v4l-dvb-apis/capture-example.html


##附录
 Q:现在小弟初次尝试H264的编码通过RTP方式传输，具体实验环境的问题如下：
环境：
服务器端，H264的帧数据（可能超过64k），分成N个1460字节的包，然后加上RTP头发送。
客户端，VLC播放器，通过RTSP协议建立连接，然后接收数据解码播放。
结果：
VLC不能解码接收到的数据，解码出错，VLC的信息中显示不能解码帧数据。
我已经阅读了一遍rfc3984的文档，对里面的如何进行打包和用rtp传输不是非常理解，希望各位大虾能够帮小弟一把，告诉小弟这些和H264的帧该如何发送，该如何分包，该如何加头信息等等。
（其中看到FUs的方式好像适合分包发送，因为小弟的数据帧可能超过64k，所以忘大虾们能够仔细解释一下对于小弟这种情况下的RTP传输）

A:我觉得所有的问题在 RFC3984 里面都已经说得很清楚了。不知道你有哪点不懂，请具体提出来。

Q:斑竹好，我这边是用VLC和服务器端进行通讯的，他们是用RTSP协议建立开始时的连 接的，服务器返回DISCRIBERS请求的SDP和下面描述的相同，我使用的packetization-mode=1，即FU-As方式打包，因为我 这边上来的数据帧可能超过64k数据。能否麻烦斑竹看看我这边的SDP写的是否正确。
SDP:
v=0
o=- 1 1 IN IP4 127.0.0.1
s=VStream Live
a=type:broadcast
t=0 0
c=IN   IP4 0.0.0.0
m=video 49170 RTP/AVP 99
a=rtpmap:99 H264/90000
a=fmtp:99 profile-level-id=42A01E; packetization-mode=1; sprop-parameter-ets=Z0IACpZTBYmI, aMljiA==
a=control:trackID=0

还有就是在RTP发送时，我打好包的数据方式如下面所示：
上来的帧数据为：NALU头＋EBSP数据
因为帧数据大于1460字节，所以我把数据分为N个不大于1460字节的包，每个包前面加上RTP头发出去。
其中NALU头的数值I帧为0x65，参数集为0x67和0x68，这个值是不是有点错误，我看RFC3984上面说的好像和我现在的有点不 同，RFC3984上面说FU-As方式打包类型值为28，我不知道这个是否十进制的，如果按照RFC3984上说的NALU头应该是多少？还是用FU- As方式的FU indicator代替原来的NALU头。
还有这个FU-As方式的头好像是有两个值，一个是FU indicator，另外一个是FU header，这两个值我应该填写什么？

按照我现在填写的内容，VLC会出现解不出码的情况，希望斑竹可以帮我回答的细致一点。谢谢了。

A:我觉得 RFC3984 上面说得非常清楚啊。
首先你把一个 NALU 的 EBSP 根据需求拆分为多个包，例如 3 个，则：

第一个 FU-A 包的 FU indicator 应该是：F = NALU 头中的 F；NRI = NALU 头中的 NRI；Type = 28。FU header 应该是：S = 1；E = 0；R = 0；Type = NALU 头中的 Type。

第二个 FU-A 包的 FU indicator 应该是：F = NALU 头中的 F；NRI = NALU 头中的 NRI；Type = 28。FU header 应该是：S = 0；E = 0；R = 0；Type = NALU 头中的 Type。

第三个 FU-A 包的 FU indicator 应该是：F = NALU 头中的 F；NRI = NALU 头中的 NRI；Type = 28。FU header 应该是：S = 0；E = 1；R = 0；Type = NALU 头中的 Type。

Q:版主，我按照你的方式分好包发送了，发现VLC不会出现不能解帧的情况了，但是，还是 出不来图像。我想可能是因为发送序列参数集和图像参数集的方法不对，他们两个的长度都很小，只要一个包就可以了，我现在将他们按照singal NALU的方式发送，就是直接在NALU包前加一个RTP的头，然后发出去。
是不是我这样发参数集存在着问题，反正我这边VLC是解不了这个参数集，因为参数集解不了，所以下面的帧肯定解不了，所以出不了图像。
麻烦版主再解释一下如何发参数集。

A:今天刚接受了流媒体的相关培训。懂得看你的   SDP 了。

对于你的问题，不知道 SPS、PPS 打包是否有问题。按照 RFC3984，而且感觉你打单一包的方式也是错的。我希望你能通过自己学习的方式去把这个问题弄清楚，因为 RFC3984 里面说得很清楚，请你自己学习学习 RFC3984 吧。既然你在做这个工作，还是应该仔细学习一下 RFC3984。

另外， SDP 中的 sprop-parameter-ets=Z0IACpZTBYmI 实际就是 SPS 和 PPS 的 BASE64 转码，你不用在码流中再传输 SPS/PPS，直接从 SDP 就可以得到。

A2:1. SDP中已经包括SPS&PPS，码流中完全可以不用传输SPS&PPS
2. profile-level-id=42A01E，这是SPS的开头几个字节，剩下的在sprop-parameter- ets=Z0IACpZTBYmI, aMljiA==中，BASE64编码，把“Z0IACpZTBYmI, aMljiA==”反BASE64转换回去，应该刚好是SPS&PPS的内容
3. 打包注意，要求H.264码流不是byte stream格式的，即没有0x000001分隔，也没有插入0x03，具体如何生成，检查你的编码器选项。
4. packetization-mode=1模式下，要求每个RTP中只有一个NAL单元，或者一个FU，不分段的NAL不做任何修改，直接作为RTP负 载；分段的NAL注意，NAL头不传输，有效负载从NAL头之后开始，根据NAL头的信息生成FU的头两个字节（相当于NAL头拆为两部分），具体生成方 式版主已经讲得很清楚。
5. RTP的payload type要与SDP中一致，不然解的出才怪



/*
 *  V4L2 video capture example
 *
 *  This program can be used and distributed without restrictions.
 *
 *      This program is provided with the V4L2 API
 * see http://linuxtv.org/docs.php for more information
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include <getopt.h>             /* getopt_long() */

#include <fcntl.h>              /* low-level i/o */
#include <unistd.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/time.h>
#include <sys/mman.h>
#include <sys/ioctl.h>

#include <linux/videodev2.h>

#define CLEAR(x) memset(&(x), 0, sizeof(x))

enum io_method {
        IO_METHOD_READ,
        IO_METHOD_MMAP,
        IO_METHOD_USERPTR,
};

struct buffer {
        void   *start;
        size_t  length;
};

static char            *dev_name;
static enum io_method   io = IO_METHOD_MMAP;
static int              fd = -1;
struct buffer          *buffers;
static unsigned int     n_buffers;
static int              out_buf;
static int              force_format;
static int              frame_count = 70;

static void errno_exit(const char *s)
{
        fprintf(stderr, "%s error %d, %s\n", s, errno, strerror(errno));
        exit(EXIT_FAILURE);
}

static int xioctl(int fh, int request, void *arg)
{
        int r;

        do {
                r = ioctl(fh, request, arg);
        } while (-1 == r && EINTR == errno);

        return r;
}

static void process_image(const void *p, int size)
{
        if (out_buf)
                fwrite(p, size, 1, stdout);

        fflush(stderr);
        fprintf(stderr, ".");
        fflush(stdout);
}

static int read_frame(void)
{
        struct v4l2_buffer buf;
        unsigned int i;

        switch (io) {
        case IO_METHOD_READ:
                if (-1 == read(fd, buffers[0].start, buffers[0].length)) {
                        switch (errno) {
                        case EAGAIN:
                                return 0;

                        case EIO:
                                /* Could ignore EIO, see spec. */

                                /* fall through */

                        default:
                                errno_exit("read");
                        }
                }

                process_image(buffers[0].start, buffers[0].length);
                break;

        case IO_METHOD_MMAP:
                CLEAR(buf);

                buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                buf.memory = V4L2_MEMORY_MMAP;

                if (-1 == xioctl(fd, VIDIOC_DQBUF, &buf)) {
                        switch (errno) {
                        case EAGAIN:
                                return 0;

                        case EIO:
                                /* Could ignore EIO, see spec. */

                                /* fall through */

                        default:
                                errno_exit("VIDIOC_DQBUF");
                        }
                }

                assert(buf.index < n_buffers);

                process_image(buffers[buf.index].start, buf.bytesused);

                if (-1 == xioctl(fd, VIDIOC_QBUF, &buf))
                        errno_exit("VIDIOC_QBUF");
                break;

        case IO_METHOD_USERPTR:
                CLEAR(buf);

                buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                buf.memory = V4L2_MEMORY_USERPTR;

                if (-1 == xioctl(fd, VIDIOC_DQBUF, &buf)) {
                        switch (errno) {
                        case EAGAIN:
                                return 0;

                        case EIO:
                                /* Could ignore EIO, see spec. */

                                /* fall through */

                        default:
                                errno_exit("VIDIOC_DQBUF");
                        }
                }

                for (i = 0; i < n_buffers; ++i)
                        if (buf.m.userptr == (unsigned long)buffers[i].start
                            && buf.length == buffers[i].length)
                                break;

                assert(i < n_buffers);

                process_image((void *)buf.m.userptr, buf.bytesused);

                if (-1 == xioctl(fd, VIDIOC_QBUF, &buf))
                        errno_exit("VIDIOC_QBUF");
                break;
        }

        return 1;
}

static void mainloop(void)
{
        unsigned int count;

        count = frame_count;

        while (count-- > 0) {
                for (;;) {
                        fd_set fds;
                        struct timeval tv;
                        int r;

                        FD_ZERO(&fds);
                        FD_SET(fd, &fds);

                        /* Timeout. */
                        tv.tv_sec = 2;
                        tv.tv_usec = 0;

                        r = select(fd + 1, &fds, NULL, NULL, &tv);

                        if (-1 == r) {
                                if (EINTR == errno)
                                        continue;
                                errno_exit("select");
                        }

                        if (0 == r) {
                                fprintf(stderr, "select timeout\n");
                                exit(EXIT_FAILURE);
                        }

                        if (read_frame())
                                break;
                        /* EAGAIN - continue select loop. */
                }
        }
}

static void stop_capturing(void)
{
        enum v4l2_buf_type type;

        switch (io) {
        case IO_METHOD_READ:
                /* Nothing to do. */
                break;

        case IO_METHOD_MMAP:
        case IO_METHOD_USERPTR:
                type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                if (-1 == xioctl(fd, VIDIOC_STREAMOFF, &type))
                        errno_exit("VIDIOC_STREAMOFF");
                break;
        }
}

static void start_capturing(void)
{
        unsigned int i;
        enum v4l2_buf_type type;

        switch (io) {
        case IO_METHOD_READ:
                /* Nothing to do. */
                break;

        case IO_METHOD_MMAP:
                for (i = 0; i < n_buffers; ++i) {
                        struct v4l2_buffer buf;

                        CLEAR(buf);
                        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                        buf.memory = V4L2_MEMORY_MMAP;
                        buf.index = i;

                        if (-1 == xioctl(fd, VIDIOC_QBUF, &buf))
                                errno_exit("VIDIOC_QBUF");
                }
                type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                if (-1 == xioctl(fd, VIDIOC_STREAMON, &type))
                        errno_exit("VIDIOC_STREAMON");
                break;

        case IO_METHOD_USERPTR:
                for (i = 0; i < n_buffers; ++i) {
                        struct v4l2_buffer buf;

                        CLEAR(buf);
                        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                        buf.memory = V4L2_MEMORY_USERPTR;
                        buf.index = i;
                        buf.m.userptr = (unsigned long)buffers[i].start;
                        buf.length = buffers[i].length;

                        if (-1 == xioctl(fd, VIDIOC_QBUF, &buf))
                                errno_exit("VIDIOC_QBUF");
                }
                type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                if (-1 == xioctl(fd, VIDIOC_STREAMON, &type))
                        errno_exit("VIDIOC_STREAMON");
                break;
        }
}

static void uninit_device(void)
{
        unsigned int i;

        switch (io) {
        case IO_METHOD_READ:
                free(buffers[0].start);
                break;

        case IO_METHOD_MMAP:
                for (i = 0; i < n_buffers; ++i)
                        if (-1 == munmap(buffers[i].start, buffers[i].length))
                                errno_exit("munmap");
                break;

        case IO_METHOD_USERPTR:
                for (i = 0; i < n_buffers; ++i)
                        free(buffers[i].start);
                break;
        }

        free(buffers);
}

static void init_read(unsigned int buffer_size)
{
        buffers = calloc(1, sizeof(*buffers));

        if (!buffers) {
                fprintf(stderr, "Out of memory\n");
                exit(EXIT_FAILURE);
        }

        buffers[0].length = buffer_size;
        buffers[0].start = malloc(buffer_size);

        if (!buffers[0].start) {
                fprintf(stderr, "Out of memory\n");
                exit(EXIT_FAILURE);
        }
}

static void init_mmap(void)
{
        struct v4l2_requestbuffers req;

        CLEAR(req);

        req.count = 4;
        req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        req.memory = V4L2_MEMORY_MMAP;

        if (-1 == xioctl(fd, VIDIOC_REQBUFS, &req)) {
                if (EINVAL == errno) {
                        fprintf(stderr, "%s does not support "
                                 "memory mapping\n", dev_name);
                        exit(EXIT_FAILURE);
                } else {
                        errno_exit("VIDIOC_REQBUFS");
                }
        }

        if (req.count < 2) {
                fprintf(stderr, "Insufficient buffer memory on %s\n",
                         dev_name);
                exit(EXIT_FAILURE);
        }

        buffers = calloc(req.count, sizeof(*buffers));

        if (!buffers) {
                fprintf(stderr, "Out of memory\n");
                exit(EXIT_FAILURE);
        }

        for (n_buffers = 0; n_buffers < req.count; ++n_buffers) {
                struct v4l2_buffer buf;

                CLEAR(buf);

                buf.type        = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                buf.memory      = V4L2_MEMORY_MMAP;
                buf.index       = n_buffers;

                if (-1 == xioctl(fd, VIDIOC_QUERYBUF, &buf))
                        errno_exit("VIDIOC_QUERYBUF");

                buffers[n_buffers].length = buf.length;
                buffers[n_buffers].start =
                        mmap(NULL /* start anywhere */,
                              buf.length,
                              PROT_READ | PROT_WRITE /* required */,
                              MAP_SHARED /* recommended */,
                              fd, buf.m.offset);

                if (MAP_FAILED == buffers[n_buffers].start)
                        errno_exit("mmap");
        }
}

static void init_userp(unsigned int buffer_size)
{
        struct v4l2_requestbuffers req;

        CLEAR(req);

        req.count  = 4;
        req.type   = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        req.memory = V4L2_MEMORY_USERPTR;

        if (-1 == xioctl(fd, VIDIOC_REQBUFS, &req)) {
                if (EINVAL == errno) {
                        fprintf(stderr, "%s does not support "
                                 "user pointer i/o\n", dev_name);
                        exit(EXIT_FAILURE);
                } else {
                        errno_exit("VIDIOC_REQBUFS");
                }
        }

        buffers = calloc(4, sizeof(*buffers));

        if (!buffers) {
                fprintf(stderr, "Out of memory\n");
                exit(EXIT_FAILURE);
        }

        for (n_buffers = 0; n_buffers < 4; ++n_buffers) {
                buffers[n_buffers].length = buffer_size;
                buffers[n_buffers].start = malloc(buffer_size);

                if (!buffers[n_buffers].start) {
                        fprintf(stderr, "Out of memory\n");
                        exit(EXIT_FAILURE);
                }
        }
}

static void init_device(void)
{
        struct v4l2_capability cap;
        struct v4l2_cropcap cropcap;
        struct v4l2_crop crop;
        struct v4l2_format fmt;
        unsigned int min;

        if (-1 == xioctl(fd, VIDIOC_QUERYCAP, &cap)) {
                if (EINVAL == errno) {
                        fprintf(stderr, "%s is no V4L2 device\n",
                                 dev_name);
                        exit(EXIT_FAILURE);
                } else {
                        errno_exit("VIDIOC_QUERYCAP");
                }
        }

        if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
                fprintf(stderr, "%s is no video capture device\n",
                         dev_name);
                exit(EXIT_FAILURE);
        }

        switch (io) {
        case IO_METHOD_READ:
                if (!(cap.capabilities & V4L2_CAP_READWRITE)) {
                        fprintf(stderr, "%s does not support read i/o\n",
                                 dev_name);
                        exit(EXIT_FAILURE);
                }
                break;

        case IO_METHOD_MMAP:
        case IO_METHOD_USERPTR:
                if (!(cap.capabilities & V4L2_CAP_STREAMING)) {
                        fprintf(stderr, "%s does not support streaming i/o\n",
                                 dev_name);
                        exit(EXIT_FAILURE);
                }
                break;
        }


        /* Select video input, video standard and tune here. */


        CLEAR(cropcap);

        cropcap.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;

        if (0 == xioctl(fd, VIDIOC_CROPCAP, &cropcap)) {
                crop.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
                crop.c = cropcap.defrect; /* reset to default */

                if (-1 == xioctl(fd, VIDIOC_S_CROP, &crop)) {
                        switch (errno) {
                        case EINVAL:
                                /* Cropping not supported. */
                                break;
                        default:
                                /* Errors ignored. */
                                break;
                        }
                }
        } else {
                /* Errors ignored. */
        }


        CLEAR(fmt);

        fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        if (force_format) {
                fmt.fmt.pix.width       = 640;
                fmt.fmt.pix.height      = 480;
                fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_YUYV;
                fmt.fmt.pix.field       = V4L2_FIELD_INTERLACED;

                if (-1 == xioctl(fd, VIDIOC_S_FMT, &fmt))
                        errno_exit("VIDIOC_S_FMT");

                /* Note VIDIOC_S_FMT may change width and height. */
        } else {
                /* Preserve original settings as set by v4l2-ctl for example */
                if (-1 == xioctl(fd, VIDIOC_G_FMT, &fmt))
                        errno_exit("VIDIOC_G_FMT");
        }

        /* Buggy driver paranoia. */
        min = fmt.fmt.pix.width * 2;
        if (fmt.fmt.pix.bytesperline < min)
                fmt.fmt.pix.bytesperline = min;
        min = fmt.fmt.pix.bytesperline * fmt.fmt.pix.height;
        if (fmt.fmt.pix.sizeimage < min)
                fmt.fmt.pix.sizeimage = min;

        switch (io) {
        case IO_METHOD_READ:
                init_read(fmt.fmt.pix.sizeimage);
                break;

        case IO_METHOD_MMAP:
                init_mmap();
                break;

        case IO_METHOD_USERPTR:
                init_userp(fmt.fmt.pix.sizeimage);
                break;
        }
}

static void close_device(void)
{
        if (-1 == close(fd))
                errno_exit("close");

        fd = -1;
}

static void open_device(void)
{
        struct stat st;

        if (-1 == stat(dev_name, &st)) {
                fprintf(stderr, "Cannot identify '%s': %d, %s\n",
                         dev_name, errno, strerror(errno));
                exit(EXIT_FAILURE);
        }

        if (!S_ISCHR(st.st_mode)) {
                fprintf(stderr, "%s is no device\n", dev_name);
                exit(EXIT_FAILURE);
        }

        fd = open(dev_name, O_RDWR /* required */ | O_NONBLOCK, 0);

        if (-1 == fd) {
                fprintf(stderr, "Cannot open '%s': %d, %s\n",
                         dev_name, errno, strerror(errno));
                exit(EXIT_FAILURE);
        }
}

static void usage(FILE *fp, int argc, char **argv)
{
        fprintf(fp,
                 "Usage: %s [options]\n\n"
                 "Version 1.3\n"
                 "Options:\n"
                 "-d | --device name   Video device name [%s]\n"
                 "-h | --help          Print this message\n"
                 "-m | --mmap          Use memory mapped buffers [default]\n"
                 "-r | --read          Use read() calls\n"
                 "-u | --userp         Use application allocated buffers\n"
                 "-o | --output        Outputs stream to stdout\n"
                 "-f | --format        Force format to 640x480 YUYV\n"
                 "-c | --count         Number of frames to grab [%i]\n"
                 "",
                 argv[0], dev_name, frame_count);
}

static const char short_options[] = "d:hmruofc:";

static const struct option
long_options[] = {
        { "device", required_argument, NULL, 'd' },
        { "help",   no_argument,       NULL, 'h' },
        { "mmap",   no_argument,       NULL, 'm' },
        { "read",   no_argument,       NULL, 'r' },
        { "userp",  no_argument,       NULL, 'u' },
        { "output", no_argument,       NULL, 'o' },
        { "format", no_argument,       NULL, 'f' },
        { "count",  required_argument, NULL, 'c' },
        { 0, 0, 0, 0 }
};

int main(int argc, char **argv)
{
        dev_name = "/dev/video0";

        for (;;) {
                int idx;
                int c;

                c = getopt_long(argc, argv,
                                short_options, long_options, &idx);

                if (-1 == c)
                        break;

                switch (c) {
                case 0: /* getopt_long() flag */
                        break;

                case 'd':
                        dev_name = optarg;
                        break;

                case 'h':
                        usage(stdout, argc, argv);
                        exit(EXIT_SUCCESS);

                case 'm':
                        io = IO_METHOD_MMAP;
                        break;

                case 'r':
                        io = IO_METHOD_READ;
                        break;

                case 'u':
                        io = IO_METHOD_USERPTR;
                        break;

                case 'o':
                        out_buf++;
                        break;

                case 'f':
                        force_format++;
                        break;

                case 'c':
                        errno = 0;
                        frame_count = strtol(optarg, NULL, 0);
                        if (errno)
                                errno_exit(optarg);
                        break;

                default:
                        usage(stderr, argc, argv);
                        exit(EXIT_FAILURE);
                }
        }

        open_device();
        init_device();
        start_capturing();
        mainloop();
        stop_capturing();
        uninit_device();
        close_device();
        fprintf(stderr, "\n");
        return 0;
}

