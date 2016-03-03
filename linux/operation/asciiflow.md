

##安装

#测试于 ubuntu 14.04
$sudo apt-get install graphivz

$cpan

根据提示配置 CPAN, 如果已经配置好, 输入

cpan[1]> install Graph::Easy
cpan[2]> quit


##使用

###语法


    ##############################################################
    # 合法的注释

    ##############################################################
    #有问题的注释

    node { label: \#5; }	  # 注意转义！
    edge { color: #aabbcc; }  # 可以使用颜色值


####空格

空格通常没有什么影响，多个空字符会合并成一个，换行的空字符会忽略；下面的表述是等价的。

    [A]->[B][C]->[D]

等效于

    [ A ] -> [ B ]
    [ C ] -> [ D ]

####节点(Node)

用中括号括起来的就是节点，我们简单可以理解为一些形状；比如流程图里面的矩形，圆等；


    [ Single node ]
    [ Node A ] --> [ Node B ]

可以用逗号分割多个节点：

    [ A ], [ B ], [ C ] --> [ D ]


上面的代码图像如下：

    +---+     +---+     +---+
    | A | --> | D | <-- | C |
    +---+     +---+     +---+
                ^
                |
                |
              +---+
              | B |
              +---+

####边(Edges)

将节点连接起来的就是边；Graph::Easy 的DSL支持这几种风格的边：

    ->              实线
    =>              双实线
    .>              点线
    ~>              波浪线
    - >             虚线
    .->             点虚线
    ..->            dot-dot-dash
    = >             double-dash

可以给边加标签，如下：


    [ client ] - request -> [ server ]
    ```

结果如下：

    ```asciidoc
    +--------+  request   +--------+
    | client | ---------> | server |
    +--------+            +--------+

####属性(Attributes)

可以给节点和边添加属性；比如标签，方向等；使用大括号 {} 表示，里面的内容类似css，attribute: value。

    [ "Monitor Size" ] --> { label: 21"; } [ Big ] { label: "Huge"; }

结果如下：

    +----------------+  21"   +------+
    | "Monitor Size" | -----> | Huge |
    +----------------+        +------+

Graph::Easy 提供了非常多的属性; 另外，Graph::Easy的 [文档][1] 非常详细，建议通读一遍；
了解其中的原理和细节，对于绘图和布局有巨大帮助。目前正在翻译，文档[地址][2]

[1]: http://bloodgate.com/perl/graph/manual/index.html
[2]: https://www.gitbook.com/book/weishu/graph-easy-cn/details

###实例

语法是不是非常简单？有了这些知识，我们就可以建立自己的流程图了；Have a try！来个MVP模式的示意图试试～

1. 新建文件，vi mvp.txt; 输入以下代码：

[ View ] {rows:3} - Parse calls to -> [ Presenter ] {flow: south; rows: 3} - Manipulates -> [ Model ]
[ Presenter ] - Updates -> [ View ]

2. 保存然后退出；命令行执行 graph-easy mvp.txt, 输入效果如下：

    +------+  Parse calls to   +--------------+
    |      | ----------------> |              |
    | View |                   |  Presenter   |
    |      |  Updates          |              |
    |      | <---------------- |              |
    +------+                   +--------------+
                                 |
                                 | Manipulates
                                 v
                               +--------------+
                               |    Model     |
                               +--------------+

两行代码就搞定了！自动对齐，调整位置，箭头，标签等等；我们完全不用管具体图形应该如何绘制，
注意力集中在描述图像本身；还在等什么！赶紧试一试吧！！

##参考

http://weishu.me/2016/01/03/use-pure-ascii-present-graph/
http://www.graphviz.org/
