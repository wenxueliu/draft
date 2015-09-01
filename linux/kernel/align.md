
#define __ALIGN_MASK(x,mask) (((x)+(mask))&~(mask))
#define ALIGN(x,a)  __ALIGN_MASK(x,(typeof(x))(a)-1)

写简单点，宏ALIGN实际上是这样定义的：

    #define ALIGN(x, a)  (x + (a - 1)) & ~(a - 1)

并且在计算的过程中将a强制转换成x的类型该宏的作用: 将x按a的值来对齐, 比如

ALIGN(9,4)=12
ALIGN(10,4)=12
ALIGN(11,4)=12
ALIGN(12,4)=12
ALIGN(13,4)=16
ALIGN(14,4)=16
ALIGN(15,4)=16
ALIGN(16,4)=16

/* Returns X / Y, rounding up.  X must be nonnegative to round correctly. */
#define DIV_ROUND_UP(X, Y) (((X) + ((Y) - 1)) / (Y))

/* Returns X rounded up to the nearest multiple of Y. */
#define ROUND_UP(X, Y) (DIV_ROUND_UP(X, Y) * (Y))
