
###避免垃圾回收对结果造成的误差

方案一：JVM启动时使用-verbose:gc观察垃圾回收动作，确认整个测试期间垃圾回收根本不会执行

方案二：运行足够的次数和时间，这样测试程序能够充分的反应出运行期间分配与垃圾回收的开销（推荐）。

###避免动态编译对记过造成的误差

方案一：让测试程序长时间运行，让编译过程和解释执行仅仅占总体运行时间的一小部分。

方案二：让测试代码“热身”，充分的执行，这样开始计时前，代码已经被编译了(JVM启动时使用-xx:PrintCompilation观察是否有编译动作)。

    package self.study;  
      
    import java.util.concurrent.CountDownLatch;  
      
    public class TestHarness {  
      
        public static void main(String[] args) throws InterruptedException {  
      
            TestHarness testHarness = new TestHarness();  
      
            long timeTasks = testHarness.timeTasks(10, new Runnable() {  
      
                @Override  
                public void run() {  
                    try {  
                        Thread.sleep(1000);  
                    } catch (InterruptedException e) {  
                        e.printStackTrace();  
                    }  
                }  
      
            });  
            System.out.println(timeTasks);  
        }  
      
      
        public long timeTasks(int nThreads, final Runnable task) throws InterruptedException {  
            //预热，编译  
            for (int i = 0; i < 10000; i++) {  
                task.run();  
            }  
              
            // 真正的测试  
            final CountDownLatch startGate = new CountDownLatch(1);  
            final CountDownLatch endGate = new CountDownLatch(nThreads);  
            for (int i = 0; i < nThreads; i++) {  
                Thread t = new Thread() {  
                    @Override  
                    public void run() {  
                        try {  
                            startGate.await();  
                            try {  
      
                                task.run();  
                            } finally {  
                                endGate.countDown();  
                            }  
                        } catch (InterruptedException e) {  
                            e.printStackTrace();  
                        }  
                    }  
                };  
                t.start();  
            }  
            long start = System.currentTimeMillis();  
            startGate.countDown();  
            endGate.await();  
            long end = System.currentTimeMillis();  
            return end - start;  
        }  
    }  
