

    C/C++提供了函数的可变参数(variadic)机制。printf就是一个使用可变参数的典型，它的原型声明为，

    int printf(const char *fmt, ...);
    　　其中返回值为实际输出字符个数，fmt为格式控制字符串，而”…”便声明了一个可变参数，
    你可以根据传递0个或多个参数给printf。printf内部会根据格式控制串中的格式指定符号（d, f, p等等）
    来逐个解析通过可变参数传进的实参变量。

    　　为解析可变参数，C语言提供了一个va_list类型和四个宏，分别是va_start, va_arg, va_end, 和va_copy，
    这些宏声明在stdarg.h中。为了方便描述，下面实现一个简单的类似printf的函数：

    void mockprintf(const char *fmt, ...)
    {
        va_list ap;
        va_start(ap, fmt);
        for (const char *s = fmt; *s; ++s)
        {
            switch(*s)
            {
                case 'd':
                    printf("meet d\n");
                    int d = va_arg(ap, int);
                    printf("%d\n", d);
                    break;
                case 's':
                    printf("meet s\n");
                    const char *str = va_arg(ap, char*);
                    printf("%s\n", str);
                    break;
                case 'c':
                    printf("meet c\n");
                    char c = va_arg(ap, int);
                    printf("%c\n", c);
                    break;
                default:
                    printf("unknown format specifier\n");
            }
        }
        va_end(ap);
    }

    int main()
    {
        mockprintf("cdfs", 'A', 0x45, "string");
        return 0;
    }
    　　va_list的实现与编译器和平台相关，通常是一个指向参数栈的指针。va_start使用变参列表前的最后一个命名参数（named argument）作为参数，
    以此定位变参列表的第一个参数的地址，并将ap指向该参数（此处假设va_list实现为指针）。宏va_arg需要两个参数，va_list变量和下一个预期的参数的类型，
    该宏以指定类型返回（展开为）对应的参数值，并调整va_list指向下一个参数。最后，每一个va_start需要一个va_end作为结束。
    另外，示例函数中没有用到va_copy，这是一个用来复制va_list变量到另一个va_list变量的宏，目的是应对平台间va_list实现的差异。
    　　值得一提的是，va_start和va_end可以重复调用，用以多次对变参列表进行解析。

    printf家族
    　　C的printf家族包含8个成员，原型如下，

    #include <stdio.h>
    int printf(const char *fmt, ...);
    int fprintf(FILE *stream, const char *fmt, ...);
    int sprintf(char *str, const char *fmt, ...);
    int snprintf(char *str, size_t size, const char *fmt, ...);
     
    #include <stdarg.h>
    int vprintf(const char *fmt, va_list ap);
    int vfprintf(FILE *stream, const char *fmt, va_list ap);
    int vsprintf(char *str, const char *fmt, va_list ap);
    int vsnprintf(char *str, size_t size, const char *fmt, va_list ap);
    　　前四个函数没有什么特殊的。后面四个v系列可以接受va_list变量，通常用在对可变参数输出的包装，在日志记录系统中较为常用。比如下面代码，

    enum LogLevel { ERROR, WARN, INFO, DEBUG }
    void log(LogLevel level, const char *fmt, ...)
    {
        va_list ap;
        va_start(ap, fmt);
        vsnprintf(buf, sizeof(buf), fmt, ap);
        va_end(ap);
        //~ write buf to file, or do something else.
    }
    　　v系列函数并不会调用va_end宏，因此在这些函数返回后，需要调用函数自己进行va_end。若要再次解析变参列表，就需要重新va_start, va_end。

    宏变参
    　　除了函数，在C/C++中，带参宏定义也可以接受变参，使用方法和函数类似。比如，若将上面的log函数的某个级别的日志输入定义成宏，

    #define log_warn(fmt, ...) log(WARN, fmt, __VA_ARGS__)
    　　__VA_ARGS__只是被预处理器简单的展开为传递给宏log_warn的变参列表，包括逗号分隔符。若想使用具有鲜明意义的名字，而不是统一的__VA_ARGS__，可以这样，

    #define log_warn(fmt, args...) log(WARN, fmt, args)
    　　上述宏定义中，有一个问题值得注意，就是当变参列表为空时，log函数调用的参数列表会有一个结尾的逗号，这在某些编译器中会被诊断为错误（据说MSVC不会），这种情况下可以将fmt也纳入变参列表，

    #define log_warn(...) log(WARN, __VA_ARGS__)


