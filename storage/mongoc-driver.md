
##MongoDB 安装

下载 mongo-c-driver-0.96.2.tar.gz

###安装依赖

Debian

    $ sudo apt-get install git gcc automake autoconf libtool pkg-config
    $ apt-get install libreadline-dev
    $ apt-get install openssl

REHT
	$ sudo yum install git gcc automake autoconf libtool pkg-config
	$ sudo yum install openssl-devel
    $ yum install readline-devel 
    
###编译安装

	$ tar xzf mongo-c-driver-0.96.2.tar.gz
	$ cd mongo-c-driver-0.96.2
	$ ./configure
	$ make
	$ sudo make install

###bug 修复

	$ sudo cp mongo-c-driver-0.96.2/src/mongoc/mongoc-ssl.h /usr/local/include/libmongoc-1.0/
	
	
##Lua5.2 安装
    
 下载 lua-5.2.3.tar.gz
 
  	$make linux  #根据自己的平台安装
  	$sudo make install
