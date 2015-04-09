接触OpenStack也半年多了，谈OpenStack的学习roadmap。

1. python 基础，越扎实越好，至少，你应该读过《bit of python》, 《dive into
python》
2. linux 基础: 安装软件，配置，基本的命令,vim等。最佳参考《鸟哥私房菜》。
3. 了解OpenStack的各个组件，自己尝试部署OpenStack，能使用OpenStack的一些command
line, 推荐devstack。
4. paste-deploy 模块:了解OpenStack配置文件工作原理
5. setuptools pbr模块: 了解OpenStack软件构造
6. oslo.config : 了解配置文件如何解析
7. logging : 了解OpenStack中日志处理方式
8. exception : 了解python 异常处理机制，python reference book里面对异常的解释足够用了。
9. sqlalchemy : python 与数据库沟通的模块
10. wsgi : wsgi在OpenStack的每一个项目中都要，可以说无处不在。OpenStack默认
采用webob。
11. rabbitmq : rabbitmq 和wsgi同等重要。OpenStack 默认采用kombu.当然推荐你也看看qpid。
12. greenlet eventlet: 这两个模块与调度有关，理解OpenStack调度必知必会.
13. 开始专注一个project的代码。跟踪mail list, launchpad, irc chat,修复bug向
社区提交，你就开始了真正的OpenStack之旅。

基本能全面掌握上面内容，保守估计得一年时间。如果你已经完成13,我感觉你已经可
以和某个招OpenStack的公司谈薪水了。
