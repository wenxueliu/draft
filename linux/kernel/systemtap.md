
##Generating Instrumentation for Other Computers

When users run a SystemTap script, a kernel module is built out of that script.  SystemTap then loads
the module into the kernel, allowing it to extract the specified data directly from the kernel

Normally, SystemTap scripts can only be run on systems where SystemTap is deployed.  This could mean
that to run SystemTap on ten systems, SystemTap needs to be deployed on all those systems. In some
cases, this may be neither feasible nor desired. For instance, corporate policy may prohibit an administrator
from installing RPMs that provide compilers or debug information on specific machines, which will
prevent the deployment of SystemTap.

To work around this, use cross-instrumentation. Cross-instrumentation is the process of generating SystemTap
instrumentation modules from a SystemTap script on one computer to be used on another computer. This process
offers the following benefits:

* The kernel information packages for various machines can be installed on a single host machine.
* Each target machine only needs one RPM to be installed to use the generated SystemTap instrumentation module: systemtap-runtime.

###Configuring a Host System and Target Systems

1. Install the systemtap-runti me RPM on each target system.
2. Determine the kernel running on each target system by running uname -r on each target system.
3. Install SystemTap on the host system. The instrumentation module will be built for the target systems on the host system.
4. Using the target kernel version determined earlier, install the target kernel and related RPMs on the host system
If multiple target systems use different target kernels, repeat this step for each different kernel used on the target systems

To build the instrumentation module, run the following command on the host system (be sure to specify the appropriate values):

    stap -r kernel_version script -m module_name -p4

Here, kernel_version refers to the version of the target kernel (the output of uname -r on the target machine), script refers
to the script to be converted into an instrumentation module, and module_name is the desired name of the instrumentation module.

Once the instrumentation module is compiled, copy it to the target system and then load it using:

    staprun module_name.ko

For example, to create the instrumentation module simple.ko from a SystemTap script named simple.stp for the target kernel
2.6.32-53.el6, use the following command:

    stap -r 2. 6 . 32-53. el 6 -e ' pro be vfs. read {exi t()}' -m si mpl e -p4

This will create a module named simple.ko . To use the instrumentation module simple.ko, copy it to the target system and run
the following command (on the target system):

    staprun simple.ko

The host system must be the same architecture and running the same distribution of Linux as the target system in order for the
built instrumentation module to work.

##SystemTap Flight Recorder Mode

systemTap 是基于事件驱动的, 通过监听内核的各个事件, 并更加监听到的事件进行对应的处理. 因此, stp 脚本的工作是:捕捉事件; 事件对应的处理函数

SystemTap 工作原理

1. 检查 stp 脚本对应的 tapset 库(一般位于 /usr/share/systemtap/tapset), 用 tapset 库中替代脚本
2. 将 stp 脚本对应的 stap 库编译为 C 代码. 然后将用 C 编译器将 C 代码编译为内核模块
3. systemtap 加载该内核模块, 监听对应的事件, 并根据脚本的处理对应的事件.
4. 一旦 systemtap 停止, systemtap 监听事件终止, 对应的内核模块从内核卸载
