
##Description

TUN/TAP provides packet reception and transmission for user space programs.
It can be seen as a simple Point-to-Point or Ethernet device, which,
instead of receiving packets from physical media, receives them from
user space program and instead of sending packets via physical media
writes them to the user space program.

###What is the TUN ?

The TUN is Virtual Point-to-Point network device.
TUN driver was designed as low level kernel support for
**IP** tunneling. It provides to userland application two interfaces:

- /dev/tunX - character device;
- tunX - virtual Point-to-Point interface.

Userland application can write IP frame to /dev/tunX and kernel will
receive this frame from tunX interface. In the same time every frame
that kernel writes to tunX interface can be read by userland application
from /dev/tunX device.

###What is the TAP ?

The TAP is a Virtual Ethernet network device.
TAP driver was designed as low level kernel support for **Ethernet** tunneling.
It provides to userland application two interfaces:

* /dev/tapX - character device;
* tapX - virtual Ethernet interface.

Userland application can write Ethernet frame to /dev/tapX
and kernel will receive this frame from tapX interface.
In the same time every frame that kernel writes to tapX
interface can be read by userland application from /dev/tapX
device.

In order to use the driver a program has to open /dev/net/tun and issue a
corresponding ioctl() to register a network device with the kernel. A network
device will appear as tunXX or tapXX, depending on the options chosen. When
the program closes the file descriptor, the network device and all
corresponding routes will disappear.

Depending on the type of device chosen the userspace program has to read/write
IP packets (with tun) or ethernet frames (with tap). Which one is being used
depends on the flags given with the ioctl().

The package from http://vtun.sourceforge.net/tun contains two simple examples
for how to use tun and tap devices. Both programs work like a bridge between
two network interfaces.

* br_select.c - bridge based on select system call.
* br_sigio.c  - bridge based on async io and SIGIO signal.

However, the best example is VTun http://vtun.sourceforge.net :))

##Configuration

####Create device node:

    mkdir /dev/net (if it does not exist already)
    mknod /dev/net/tun c 10 200

####Set permissions: e.g. chmod 0666 /dev/net/tun

There is no harm in allowing the device to be accessible by non-root users,
since CAP_NET_ADMIN is required for creating network devices or for
connecting to network devices which are not owned by the user in
question. If you want to create persistent devices and give ownership of
them to  unprivileged users, then you need the /dev/net/tun device
to be usable by those users.

###Driver module autoloading

Make sure that "Kernel module loader" - module auto-loading support is enabled
in your kernel.  The kernel should load it on first access.

###Manual loading

insert the module by hand: modprobe tun

If you do it the latter way, you have to load the module every time you
need it, if you do it the other way it will be automatically loaded when
/dev/net/tun is being opened.

##Program interface

###Network device allocation:

char *dev should be the name of the device with a format string (e.g.
"tun%d"), but (as far as I can see) this can be any valid network
device name.

Note that the character pointer becomes overwritten with the real device name
(e.g. "tun0")

```c
    #include <linux/if.h>
    #include <linux/if_tun.h>

    int tun_alloc(char *dev)
    {
        struct ifreq ifr;
        int fd, err;

        if( (fd = open("/dev/net/tun", O_RDWR)) < 0 ) {
            return tun_alloc_old(dev);
        }

        memset(&ifr, 0, sizeof(ifr));

        /* Flags: IFF_TUN   - TUN device (no Ethernet headers) 
         *        IFF_TAP   - TAP device
         *        IFF_NO_PI - Do not provide packet information
         */
        ifr.ifr_flags = IFF_TUN;
        if ( *dev ) {
            strncpy(ifr.ifr_name, dev, IFNAMSIZ);
        }

        if( (err = ioctl(fd, TUNSETIFF, (void *) &ifr)) < 0 ){
            close(fd);
            return err;
        }
        strcpy(dev, ifr.ifr_name);
        return fd;
    }
```

###Frame format:

If flag IFF_NO_PI is not set each frame format is:

   Flags [2 bytes]
   Proto [2 bytes]
   Raw protocol(IP, IPv6, etc) frame.

###Multiqueue tuntap interface:

From version 3.8, Linux supports multiqueue tuntap which can uses multiple
file descriptors (queues) to parallelize packets sending or receiving. The
device allocation is the same as before, and if user wants to create
multiple queues, TUNSETIFF with the same device name must be called many
times with IFF_MULTI_QUEUE flag.

char *dev should be the name of the device, queues is the number of queues to
be created, fds is used to store and return the file descriptors (queues)
created to the caller. Each file descriptor were served as the interface
of a queue which could be accessed by userspace.

```
    #include <linux/if.h>
    #include <linux/if_tun.h>

    int tun_alloc_mq(char *dev, int queues, int *fds)
    {
        struct ifreq ifr;
        int fd, err, i;

        if (!dev) {
            return -1;
        }
        memset(&ifr, 0, sizeof(ifr));
        /* Flags: IFF_TUN   - TUN device (no Ethernet headers)
         *        IFF_TAP   - TAP device
         *
         *        IFF_NO_PI - Do not provide packet information
         *        IFF_MULTI_QUEUE - Create a queue of multiqueue device
         */
        ifr.ifr_flags = IFF_TAP | IFF_NO_PI | IFF_MULTI_QUEUE;
        strcpy(ifr.ifr_name, dev);

        for (i = 0; i < queues; i++) {
            if ((fd = open("/dev/net/tun", O_RDWR)) < 0) {
                goto err;
            }
            err = ioctl(fd, TUNSETIFF, (void *)&ifr);
            if (err) {
                close(fd);
                goto err;
            }
            fds[i] = fd;
        }
        return 0;
    err:
        for (--i; i >= 0; i--)
            close(fds[i]);
        return err;
    }
```

A new ioctl(TUNSETQUEUE) were introduced to enable or disable a queue. When
calling it with IFF_DETACH_QUEUE flag, the queue were disabled. And when
calling it with IFF_ATTACH_QUEUE flag, the queue were enabled. The queue
were enabled by default after it was created through TUNSETIFF.

fd is the file descriptor (queue) that we want to enable or disable, when
enable is true we enable it, otherwise we disable it

```
    #include <linux/if.h>
    #include <linux/if_tun.h>

    int tun_set_queue(int fd, int enable)
    {
        struct ifreq ifr;

        memset(&ifr, 0, sizeof(ifr));

        if (enable) {
            ifr.ifr_flags = IFF_ATTACH_QUEUE;
        } else {
            ifr.ifr_flags = IFF_DETACH_QUEUE;
        }

        return ioctl(fd, TUNSETQUEUE, (void *)&ifr);
    }
```

##QA:

Universal TUN/TAP device driver Frequently Asked Question.

Q: What platforms are supported by TUN/TAP driver ?

    Currently driver has been written for 3 Unices:
    Linux kernels 2.2.x, 2.4.x
    FreeBSD 3.x, 4.x, 5.x
    Solaris 2.6, 7.0, 8.0

Q: What is TUN/TAP driver used for?

As mentioned above, main purpose of TUN/TAP driver is tunneling.
It is used by VTun (http://vtun.sourceforge.net).

Another interesting application using TUN/TAP is pipsecd
(http://perso.enst.fr/~beyssac/pipsec/), a userspace IPSec
implementation that can use complete kernel routing (unlike FreeS/WAN).

Q:  How does Virtual network device actually work ?

Virtual network device can be viewed as a simple Point-to-Point or
Ethernet device, which instead of receiving packets from a physical
media, receives them from user space program and instead of sending
packets via physical media sends them to the user space program.

Let us say that you configured IPX on the tap0, then whenever
the kernel sends an IPX packet to tap0, it is passed to the application
(VTun for example). The application encrypts, compresses and sends it to
the other side over TCP or UDP. The application on the other side decompresses
and decrypts the data received and writes the packet to the TAP device,
the kernel handles the packet like it came from real physical device.

Q: What is the difference between TUN driver and TAP driver?

TUN works with IP frames. TAP works with Ethernet frames.

This means that you have to read/write IP packets when you are using tun and
ethernet frames when using tap.

Q: what is the difference between BPF and TUN/TAP driver?

BPF is an advanced packet filter. It can be attached to existing
network interface. It does not provide a virtual network interface.
A TUN/TAP driver does provide a virtual network interface and it is possible
to attach BPF to this interface

Q: Does TAP driver support kernel Ethernet bridging?

Yes. Linux and FreeBSD drivers support Ethernet bridging.

##Example

```br_select.c
    #include <stdio.h>
    #include <fcntl.h>
    #include <unistd.h>
    #include <sys/time.h>
    #include <sys/types.h>

    #include <linux/if_tun.h>

    #define max(a,b) ((a)>(b) ? (a):(b))

    int main(int argc, char *argv[])
    {
        char buf[1600];
        int f1,f2,l,fm;
        fd_set fds;

        if(argc < 2) {
                printf("Usage: bridge tap|tun\n");
                exit(1);
            }

        sprintf(buf,"/dev/%s%d",argv[1],0);
        f1 = open(buf, O_RDWR);

        sprintf(buf,"/dev/%s%d",argv[1],1);
        f2 = open(buf, O_RDWR);

        fm = max(f1, f2) + 1;

        ioctl(f1, TUNSETNOCSUM, 1); 
        ioctl(f2, TUNSETNOCSUM, 1); 

        while(1) {
            FD_ZERO(&fds);
            FD_SET(f1, &fds);
            FD_SET(f2, &fds);

            select(fm, &fds, NULL, NULL, NULL);

            if( FD_ISSET(f1, &fds) ) { l = read(f1,buf,sizeof(buf)); write(f2,buf,l);
            }
            if( FD_ISSET(f2, &fds) ) {
                l = read(f2,buf,sizeof(buf));
                    write(f1,buf,l);
            }
        }
    }
```

```br_sigio.c

#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include <sys/time.h>
#include <sys/types.h>
#include <signal.h>
#include <errno.h>

#include <linux/if_tun.h>

extern int errno;

int bridge_term = 0;
int f1, f2;

    void sig_io(int sig)
    {
        static char buf[1600];
        register int r;

        while( (r=read(f1, buf, sizeof(buf))) > 0 ) {
            write(f2, buf, r);
        }

        if( r < 0 && (errno != EAGAIN && errno != EINTR) ) {
            bridge_term = 1;
            return;
        }

        while( (r=read(f2, buf, sizeof(buf))) > 0 ) {
            write(f1, buf, r);
        }
        if( r < 0 && (errno != EAGAIN && errno != EINTR) ) {
            bridge_term = 1;
            return;
        }
    }

    int main(int argc, char *argv[])
    {
        struct sigaction sa;
        char buf[20];

        if(argc < 2) {
            printf("Usage: bridge tap|tun\n");
            exit(1);
        }

        sprintf(buf,"/dev/%s%d",argv[1],0);
        f1 = open(buf, O_RDWR);

        sprintf(buf,"/dev/%s%d",argv[1],1);
        f2 = open(buf, O_RDWR);

        ioctl(f1, TUNSETNOCSUM, 1);
        ioctl(f2, TUNSETNOCSUM, 1);

        fcntl(f1, F_SETFL, O_NONBLOCK | O_ASYNC);
        fcntl(f2, F_SETFL, O_NONBLOCK | O_ASYNC);

        memset(&sa, 0, sizeof(sa));
        sa.sa_handler = sig_io;
        sigaction(SIGIO, &sa, NULL);

        while( !bridge_term ) {
            sleep(1000);
        }
    }
```

Tun/tap 驱动程序中包含两个部分, 一部分是字符设备驱动, 还有一部分是网卡驱动部分. 利用网卡驱动部分接收来自
TCP/IP 协议栈的网络分包并发送或者反过来将接收到的网络分包传给协议栈处理, 而字符驱动部分则将网络分包在内核
与用户态之间传送, 模拟物理链路的数据接收和发送. Tun/tap 驱动很好的实现了两种驱动的结合.

##参考

[tun-tap](http://www.mjmwired.net/kernel/Documentation/networking/tuntap.txt)
[vtun](http://vtun.sourceforge.net/)


##附录

```c
    #include <unistd.h>
    #include <stdio.h>
    #include <curses.h>
    #include <string.h>
    #include <assert.h>
    #include <sys/types.h>
    #include <sys/socket.h>
    #include <netinet/in.h>
    #include <signal.h>
    #include <unistd.h>
    #include <linux/if_tun.h>
    #include <netinet/in.h>
    #include <sys/ioctl.h>
    #include <sys/time.h>
    #include <linux/if.h>
    #include <netinet/in.h>
    #include <arpa/inet.h>
    #include <errno.h>
    #include <fcntl.h>

    int tun_creat(char *dev,int flags) {
        struct ifreq ifr;
        int fd,err;
        assert(dev != NULL);
        //you can replace it to tap to create tap device.
        if ((fd = open ("/dev/net/tun",O_RDWR))<0) {
            return fd;
        }
        memset(&ifr,0,sizeof (ifr));
        ifr.ifr_flags|=flags;
        if (*dev != '\0') {
            strncpy(ifr.ifr_name, dev, IFNAMSIZ);
        }

        if((err = ioctl(fd,TUNSETIFF,(void *)&ifr))<0) {
            close (fd);
            return err;
        }
        strcpy(dev,ifr.ifr_name);
        return fd;
    }

    int main() {
        int tun,ret;
        char tun_name[IFNAMSIZ];
        unsigned char buf[4096];
        tun_name[0]='\0';
        tun = tun_creat(tun_name,IFF_TAP|IFF_NO_PI);//如果需要配置tun设备，则把"IFF_TAP"改成“IFF_TUN”
        if(tun<0) {
            perror("tun_create");
            return 1;
        }
        printf("TUN name is %s\n",tun_name);
        while (1) {
            unsigned char ip[4];
            ret = read(tun, buf, sizeof(buf));
            if (ret < 0) {
                break;
            }
            memcpy(ip, &buf[12], 4);
            memcpy(&buf[12], &buf[16], 4);
            memcpy(&buf[16], ip, 4);
            buf[20] = 0;
            *((unsigned short*)&buf[22]) += 8;
            printf("read %d bytes\n", ret);
            ret = write(tun, buf, ret);
            printf("write %d bytes\n", ret);
        }
        return 0;
    }
```
