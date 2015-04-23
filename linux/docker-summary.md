###导出(Export)

Export命令用于持久化容器（不是镜像）。所以，我们就需要通过以下方法得到容器ID：

    sudo docker ps -a

接着执行导出：
	
    sudo docker export <CONTAINER ID> > /home/export.tar

最后的结果是一个2.7MB大小的Tar文件（比使用save命令稍微小些）。

###保存(Save)

Save命令用于持久化镜像（不是容器）。所以，我们就需要通过以下方法得到镜像名称：

	 sudo docker images

接着执行保存：

     sudo docker save busybox-1 > /home/save.tar

最后的结果是一个2.8MB大小的Tar文件（比使用export命令稍微大些）。

###它们之间的不同

导出后再导入(exported-imported)的镜像会丢失所有的历史，而保存后再加载（saveed-loaded）的镜像没有丢失历史和层(layer)。
这意味着使用导出后再导入的方式，你将无法回滚到之前的层(layer)，同时，使用保存后再加载的方式持久化整个镜像，就可以做到
层回滚（可以执行docker tag <LAYER ID> <IMAGE NAME>来回滚之前的层）。

执行下面的命令就知道了：

	    sudo docker images --tree

