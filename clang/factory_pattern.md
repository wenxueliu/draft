
在 C 语言如何实现工厂模式?

先看一段C代码：

```
    typedef int type;
    typedef void(*draw)(void); 

    struct shape {
        type t;
        draw f;
    };

    struct rectange {
        type t;
        int a;
        draw f;
    };

    struct circle {
        type t;
        int r;
        draw f;
    };

    #define T1 0
    #define T2 1
    #define T3 2

    void drawall(shape[] s, int count) {
        for (int i = 0; i != count; i++) {
            switch((s + i)->t) {
            case T1:
                ((struct shape*)(s + i))->f();
                break;
            case T2:
                ((struct rectange*)(s + i))->f();
                break;
            case T3:
                ((struct circle*)(s + i))->f();
                break;
            default:
                break;
            }
        }
    }
```

代码中需要根据图形的形状去调用具体的 draw 方法, 对 type 的判断只是为了确定该调用哪个结构体中的
draw 类型的函数. 那么能否简化一下这个 switch case 呢? 最简单的, 修改各个抽象形状的结构体定义,
然后定义一个共有的"基类", 即只定义类型和函数指针, 将各种形状对象强转为"基类型", 然后统一调用
函数指针即可, 同时可以将指向形状对象的基类指针作为参数传入, 在函数中再将基类型的指针转为具体
的子类. 达到去除 case switch 的目的。

按照如上思路修改之后的代码应该是类似这样的：

```
    struct base {
        type t;
        draw f;
    };

    typedef int type;
    typedef void(*draw)(struct base*); 

    struct shape {
        type t;
        draw f;
    };

    struct rectange {
        type t;
        draw f;
        int a;
    };

    struct circle {
        type t;
        draw f;
        int r;
    };

    #define T1 0
    #define T2 1
    #define T3 2

    void drawall(struct base[] s, int count)
    {
        struct base* b = s;
        for (int i = 0; i != count; i++)
        {
            (b + i)->draw(b + i);
        }
    }
```

这样, 要求所有的类型都应该"符合" base 类型的结构, 当出现不符合该类型的结构传入时, 编译时并不会报错,
运行时才会寻址错误. 这样做不是特别好.

按照表驱动模式进一步改造该代码:

```
   struct config {
       type t;
       int l;
   };

   typedef int type;
   typedef void(*draw)(struct config*);

   void drawshape(struct config*);
   void drawsrectange(struct config*);
   void drawcircle(struct config*);

   #define T1 0
   #define T2 1
   #define T3 2

   draw call_table[] = {
       [T1] = {&drawshape},
       [T2] = {&drawsrectange},
       [T3] = {&drawcircle},
   };

   void drawall(struct config[] s, int count) {
       draw* d = call_table;
       struct config* b = s;
       for (int i = 0; i != count; i++)
       {
           (*(d + (b + i)->t))(b + i);
       }
   }

```

著名的开源项目 openvSwitch 就是这么干的.

###参考

http://codefine.co/%e5%a6%82%e4%bd%95%e6%9c%89%e6%95%88%e9%81%bf%e5%85%8d%e5%a4%a7%e9%87%8f%e9%87%8d%e5%a4%8d%e7%9a%84switch%e5%88%86%e6%94%af/?utm_source=rss&utm_medium=rss&utm_campaign=%25e5%25a6%2582%25e4%25bd%2595%25e6%259c%2589%25e6%2595%2588%

