#无锁队列

##关于CAS等原子操作

在开始说无锁队列之前，我们需要知道一个很重要的技术就是CAS操作——Compare & Set，或是 Compare & Swap，现在几乎所有的CPU指令都支持CAS的原子操作，X86下对应的是 **CMPXCHG** 汇编指令。有了这个原子操作，我们就可以用其来实现各种无锁(lock free)的数据结构。

这个操作用C语言来描述就是下面这个样子：（代码来自Wikipedia的Compare And Swap词条）意思就是说，看一看内存*reg里的值是不是oldval，如果是的话，则对其赋值newval。


    int compare_and_swap (int* reg, int oldval, int newval)
    {
      int old_reg_val = *reg;
      if (old_reg_val == oldval)
         *reg = newval;
      return old_reg_val;
    }

这个操作可以变种为返回bool值的形式（返回 bool值的好处在于，可以调用者知道有没有更新成功）：
	
    bool compare_and_swap (int *accum, int *dest, int newval)
    {
      if ( *accum == *dest ) {
          *dest = newval;
          return true;
      }
      return false;
    }

与CAS相似的还有下面的原子操作：（这些东西大家自己看Wikipedia吧）

* [Fetch And Add](http://en.wikipedia.org/wiki/Fetch-and-add)，一般用来对变量做 +1 的原子操作
* [Test-and-set](http://en.wikipedia.org/wiki/Test-and-set)，写值到某个内存位置并传回其旧值。汇编指令BST
* [Test and Test-and-set](http://en.wikipedia.org/wiki/Test_and_Test-and-set)，用来低低Test-and-Set的资源争夺情况

注：在实际的C/C++程序中，CAS的各种实现版本如下：


















##参考

http://coolshell.cn/articles/8239.html