mmap()系统调用使得进程之间通过映射同一个普通文件实现共享内存。普通文件被映射到进程地址空间后，进程可以向访问普通内存一样对文件进行访问，不必再调用read(),write()等操作。

注：实际上, mmap()系统调用并不是完全为了用于共享内存而设计的。它本身提供了不同于一般对普通文件的访问方式，进程可以像读写内存一样对普通文件的操作。而 Posix 或系统 V 的共享内存IPC则纯粹用于共享目的，当然 mmap()实现共享内存也是其主要应用之一。

##mmap()系统调用形式如下：

    void* mmap ( void * addr , size_t len , int prot , int flags , int fd , off_t offset )

参数

* fd 为即将映射到进程空间的文件描述字，一般由open()返回，同时，fd可以指定为-1，此时须指定flags参数中的MAP_ANON，表明进行的是匿名映射（不涉及具体的文件名，避免了文件的创建及打开，很显然只能用于具有亲缘关系的进程间通信）。

* len是映射到调用进程地址空间的字节数，它从被映射文件开头offset个字节开始算起。

* prot 参数指定共享内存的访问权限。可取如下几个值的或：PROT_READ（可读） , PROT_WRITE （可写）, PROT_EXEC （可执行）, PROT_NONE（不可访问）。

* flags由以下几个常值指定：MAP_SHARED , MAP_PRIVATE , MAP_FIXED，其中，MAP_SHARED , MAP_PRIVATE必选其一，而MAP_FIXED则不推荐使用。

* offset 参数一般设为0，表示从文件头开始映射。参数addr指定文件应被映射到进程空间的起始地址，一般被指定一个空指针，此时选择起始地址的任务留给内核来完成。函数的返回值为最后文件映射到进程空间的地址，进程可直接操作起始地址为该值的有效地址。这里不再详细介绍 mmap()的参数，读者可参考mmap()手册页获得进一步的信息。

##系统调用mmap()用于共享内存的两种方式：

###使用普通文件提供的内存映射

适用于任何进程之间；此时，需要打开或创建一个文件，然后再调用mmap()；典型调用代码如下：


        fd=open(name, flag, mode);
        if(fd<0)
        ...

        ptr=mmap(NULL, len , PROT_READ|PROT_WRITE, MAP_SHARED , fd , 0); 

通过 mmap()实现共享内存的通信方式有许多特点和要注意的地方，我们将在范例中进行具体说明。

###使用特殊文件提供匿名内存映射

适用于具有亲缘关系的进程之间；由于父子进程特殊的亲缘关系，在父进程中先调用 mmap()，然后调用 fork()。那么在调用 fork()之后，子进程继承父进程匿名映射后的地址空间，同样也继承mmap()返回的地址，这样，父子进程就可以通过映射区域进行通信了。注意，这里不是一般的继承关系。一般来说，子进程单独维护从父进程继承下来的一些变量。而 mmap() 返回的地址，却由父子进程共同维护。

对于具有亲缘关系的进程实现共享内存最好的方式应该是采用匿名内存映射的方式。此时，不必指定具体的文件，只要设置相应的标志即可，参见范例2。

##系统调用munmap()

```c
    int munmap( void * addr, size_t len )
```

该调用在进程地址空间中解除一个映射关系，addr是调用mmap()时返回的地址，len是映射区的大小。当映射关系解除后，对原来映射地址的访问将导致段错误发生。

##系统调用msync()

    int msync ( void * addr , size_t len, int flags)

一般说来，进程在映射空间的对共享内容的改变并不直接写回到磁盘文件中，往往在调用munmap（）后才执行该操作。可以通过调用msync()实现磁盘上文件内容与共享内存区的内容一致。 

##实例

下面将给出使用 mmap() 的两个范例：范例1给出两个进程通过映射普通文件实现共享内存通信；范例2给出父子进程通过匿名映射实现共享内存。系统调用 mmap() 有许多有趣的地方，下面是通过mmap() 映射普通文件实现进程间的通信的范例，我们通过该范例来说明 mmap() 实现共享内存的特点及注意事项。

###范例1：两个进程通过映射普通文件实现共享内存通信

范例1包含两个子程序：map_normalfile1.c及map_normalfile2.c。编译两个程序，可执行文件分别为 map_normalfile1及map_normalfile2。两个程序通过命令行参数指定同一个文件来实现共享内存方式的进程间通信。 map_normalfile2试图打开命令行参数指定的一个普通文件，把该文件映射到进程的地址空间，并对映射后的地址空间进行写操作。 map_normalfile1把命令行参数指定的文件映射到进程地址空间，然后对映射后的地址空间执行读操作。这样，两个进程通过命令行参数指定同一个文件来实现共享内存方式的进程间通信。
下面是两个程序代码：

```
        /*-------------map_normalfile1.c-----------*/
        #include <sys/mman.h>
        #include <sys/types.h>
        #include <fcntl.h>
        #include <unistd.h>

        typedef struct{
            char name[4];
            int age;
        }people;

        main(int argc, char** argv) // map a normal file as shared mem:
        {
            int fd,i;
            people *p_map;
            char temp;
            fd=open(argv[1],O_CREAT|O_RDWR|O_TRUNC,00777);
            lseek(fd,sizeof(people)*5-1,SEEK_SET);
            write(fd,"",1);
            p_map = (people*) mmap( NULL,sizeof(people)*10,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0 );
            close( fd );
            temp = 'a';
            for(i=0; i<10; i++)
            {
                temp += 1;
                memcpy( ( *(p_map+i) ).name, &temp,2 );
                ( *(p_map+i) ).age = 20+i;
            }

            printf(" initialize over \n ")；
            sleep(10);
            munmap( p_map, sizeof(people)*10 );
            printf( "umap ok \n" );
        }

```

```
    /*-------------map_normalfile2.c-----------*/
    #include <sys/mman.h>
    #include <sys/types.h>
    #include <fcntl.h>
    #include <unistd.h>

    typedef struct{
        char name[4];
        int age;
    }people;

    main(int argc, char** argv) // map a normal file as shared mem:
    {
        int fd,i;
        people *p_map;
        fd=open( argv[1],O_CREAT|O_RDWR,00777 );
        p_map = (people*)mmap(NULL,sizeof(people)*10,PROT_READ|PROT_WRITE,MAP_SHARED,fd,0);
        for(i = 0;i<10;i++)
        {
            printf( "name: %s age %d;\n",(*(p_map+i)).name, (*(p_map+i)).age );
        }
        munmap( p_map,sizeof(people)*10 );
    }

```
map_normalfile1.c 首先定义了一个people数据结构，（在这里采用数据结构的方式是因为，共享内存区的数据往往是有固定格式的，这由通信的各个进程决定，采用结构的方式有普遍代表性）。map_normfile1首先打开或创建一个文件，并把文件的长度设置为5个people结构大小。然后从mmap()的返回地址开始，设置了10个people结构。然后，进程睡眠10秒钟，等待其他进程映射同一个文件，最后解除映射。
 
map_normfile2.c 只是简单的映射一个文件，并以people数据结构的格式从mmap()返回的地址处读取10个people结构，并输出读取的值，然后解除映射。
分别把两个程序编译成可执行文件 map_normalfile1 和 map_normalfile2 后，在一个终端上先运行./map_normalfile2 /tmp/test_shm，程序输出结果如下：

```
    initialize over
    umap ok
```

在map_normalfile1输出initialize over 之后，输出umap ok之前，在另一个终端上运行map_normalfile2 /tmp/test_shm，将会产生如下输出(为了节省空间，输出结果为稍作整理后的结果)：

```
    name: b age 20; name: c age 21; name: d age 22; name: e age 23; name: f age 24;
    name: g age 25; name: h age 26; name: I age 27; name: j age 28; name: k age 29;
```
在 map_normalfile1 输出 umap ok 后，运行map_normalfile2则输出如下结果：

```
    name: b age 20; name: c age 21; name: d age 22; name: e age 23; name: f age 24;
    name: age 0; name: age 0; name: age 0; name: age 0; name: age 0;
```
从程序的运行结果中可以得出的结论

最终被映射文件的内容的长度不会超过文件本身的初始大小，即映射不能改变文件的大小；

可以用于进程通信的有效地址空间大小大体上受限于被映射文件的大小，但不完全受限于文件大小。打开文件被截短为5个 people 结构大小，而在 map_normalfile1 中初始化了10个people数据结构，在恰当时候（map_normalfile1输出initialize over 之后，输出 umap ok 之前）调用 map_normalfile2 会发现map_normalfile2 将输出全部10个people结构的值，后面将给出详细讨论。

注：在linux中，内存的保护是以页为基本单位的，即使被映射文件只有一个字节大小，内核也会为映射分配一个页面大小的内存。当被映射文件小于一个页面大小时，进程可以对从mmap()返回地址开始的一个页面大小进行访问，而不会出错；但是，如果对一个页面以外的地址空间进行访问，则导致错误发生，后面将进一步描述。因此，可用于进程间通信的有效地址空间大小不会超过文件大小及一个页面大小的和。

文件一旦被映射后，调用mmap()的进程对返回地址的访问是对某一内存区域的访问，暂时脱离了磁盘上文件的影响。所有对mmap()返回地址空间的操作只在内存中有意义，只有在调用了munmap()后或者msync()时，才把内存中的相应内容写回磁盘文件，所写内容仍然不能超过文件的大小。 

