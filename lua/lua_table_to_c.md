###前情提要

Lua 通过一个虚拟栈与 C 的交互，正数索引自底向上取值，负数索引自顶向下取值。

Lua 中的 Table（表）结构可以使用任何数据作为 key 进行取值。使用 C API 访问 Table 中的元素有两种方法：

普适版：

    ​lua_getglobal(L, t) ; 

    lua_pushxxxx(L, k);

    lua_gettable(L, -2);

字符串版本：

    lua_getglobal(L, t);

   	lua_getfields(L, -1, k);

结束时，栈上的情况均为：栈顶为 t[k]，次顶元素为 Table 类型的 t。第二种方法其实是第一种方法在「key 为字符串」时的特殊写法。



###C 获取Lua中的一般全局变量（boolean, number, string）

下面以字符串为例。

Lua 文件 config.lua

	app_name = "Test"
	app_author = "Gotaly"

解析配置文件的C文件 config.c （这里不作出错处理，聚焦于Lua的C API和其逻辑的运用）

	#include <stdio.h>
	#include <string.h>

	#include <lua.h>
	#include <lauxlib.h>
	#include <lualib.h>


	int main(int argc,char *argv[])
	{

		lua_State *lua = luaL_newstate();
		/**
		* luaL_openlibs(lua);
		*/
		luaL_loadfile(lua,"config.lua");
		lua_pcall(lua,0,0,0);

		lua_getglobal(lua,"app_name");
		lua_getglobal(lua,"app_author");
		printf("application name is %s,author is %s \n",lua_tostring(lua,-2),lua_tostring(lua,-1));
		return 0;
	}

这个例子和《programming in lua》中的很类似（其实同样功能的代码都类似，呵呵），这里解释下各 API的作用。

* lua_State lua = luaL_newstate();
这个在你的C程序中创建一个Lua环境，之后就可以通过该句柄和Lua进行通信了。

* luaL_openlibs(lua);
打开Lua中要使用的标准库，具体到我们这个例子可以不使用。

* luaL_loadfile(lua,"config.lua");lua_pcall(lua,0,0,0);
加载Lua程序并执行，这里要做出错处理。例子中为了突出逻辑，没有做相应处理。同样除了loadfile，还有loadbuffer,loadstring等加载Lua程序的接口，可以自行查阅Manual

* lua_getglobal(lua,"app_name");
这里会从句柄lua表示的环境中获取全局变量"app_name",这里说是全局变量，但是它只是相对于该句柄所表示的饿环境中的全局变量。 调用了该接口后，相应的变量的值就被压入到Lua和C交流的栈空间了。后面将其出栈就可以在C程序中得到该值。

* lua_tostring(lua,-2)
这里就根据之前入栈的顺序，将句柄lua和C交互中的栈空间里相应的值出栈。lua_toxxxx是一个系列函数，具体可以参考Lua的Manual，这里主要将其内容转换成字符串。


###C 获取Lua中的 Table

讲完了获取一般的变量，这里切入正题，获取Table内容。

Lua 文件 config.lua

	app_content = {
		name = "app_Test",
		author = "Gota"    
	}

解析配置文件的C文件 config.c （

	#include <stdio.h>
	#include <string.h>

	#include <lua.h>
	#include <lauxlib.h>
	#include <lualib.h>


	int main(int argc,char *argv[])
	{

		lua_State *lua = luaL_newstate();
		/**
		* luaL_openlibs(lua);
		*/
		luaL_loadfile(lua,"config.lua");
		lua_pcall(lua,0,0,0);

		lua_getglobal(lua,"app_content");
		lua_getfield(lua,-1,"name");
		lua_getfield(lua,-2,"author");
		printf("application name is %s,author is %s \n",lua_tostring(lua,-2),lua_tostring(lua,-1));
		return 0;
	}

这里对上面的代码进行说明。主要就是多了一个API的使用

* lua_getfield(lua,-1,"name")
该API主要是用来处理Table。其第一个参数是交互的句柄，第二个参数是Table在交互的栈的位置，第三个参数是前面Table中的键。该函数的结果是将该Table中对于键的值取出来，并压入到交互栈中。这样就使得原来位于（-1）位置的Table就下压了一个位置到了 （-2）。

再说明下上述程序的整个执行过程，首先getglobal得到一个全局变量app_content，然后将他压入到交互栈中，位于（-1）位置。 然后调用lua_getfield(lua,-1,"name");，将（-1）位置的变量作Table解析，并取出其中的“name”键的值压入交互栈，位于（-1）位置， 原来的Table被下压一层至（-2）。然后调用lua_getfield(lua,-2,"author");对（-2）位置的Table进行取值，取出其键为“author”的 值并压入到交互栈位置（-1），这样原来的“name”就被压入到（-2）位置。最后用tostring，将栈中的数据取出来。

这里我省掉了2个API。一个是lua_isxxx系列，这个系列中的lua_istable（ lua_State lua，int index），可以检查index位置的变量是否 为Table。上面我们主要就是对table作测试就没有进行验证了。

* lua_pop(lua，int num)
从交互句柄的交互栈中弹出几个值

官方描述见[这里](http://www.lua.org/manual/5.2/contents.html#index)

###C获取Lua中的嵌套Table

Lua 文件 config.lua

	app_content = {
		name = "app_Test",
		author = "Gota"    
	}

	app_config.content = app_content

解析配置文件的C文件 config.c

	#include <stdio.h>
	#include <string.h>

	#include <lua.h>
	#include <lauxlib.h>
	#include <lualib.h>


	int main(int argc,char *argv[])
	{

		lua_State *lua = luaL_newstate();
		/**
		* luaL_openlibs(lua);
		*/
		luaL_loadfile(lua,"config.lua");
		lua_pcall(lua,0,0,0);

		lua_getglobal(lua,"app_content");
		lua_pushnil(lua);
		while(lua_next(lua,-2)){
		    printf("get key %s\n is table %d\n",lua_tostring(lua,-2),lua_istable(lua,-1));
		    lua_getfield(lua,-1,"name");
		    printf("application name is %s \n",lua_tostring(lua,-2));

		    lua_pop(lua,1);    
		}

		return 0;
	}

对于嵌套解析Table，大家看以看过来,作者对其机制解释的特别清楚。这里我只说下我 看了文章后的学到的内容。

* lua_pushnil(lua);
看过《programming in lua》都知道lua_pushxxx系列函数，可以在C中将一些值压入交互栈。pushnil就是向栈中压入Lua的nil，nil在Lua中是一个类型值，在C中，大家可以 将其视为NULL，并且像 lua_tostring 这样的从栈中未取到值，也就是Lua中的nil，得到的结果就是NULL。

* lua_next（lua,int index）

lua_next（lua_State lua,int index）函数是这个例子的主角，他可以根据指定交互栈中index处的Table，进行遍历，每次取（-1）位置的一个key作为前辈，即将要取得一对元素的上一对元素的key，然后返回Table的该 对元素，将其键先压入栈，再将该键对应的值压入栈，结果就是（-2）位置放的是键，（-1）位置放的是值。Table自然被压入到其后，本例中的（-3）位置。如果key为nil，则默认为首对数据， 会随机的压入一对值。当所有值都被遍历一遍后，next返回0。

* 9)lua_pop(lua_State lua,int num)

该函数如上面所述：从交互句柄的交互栈中弹出 num 个值。这里不得不说下 Lua 作配置文件的另一个好处是 Lua 自己处理堆栈，使得配置文件程序更安全。所有压入栈中的内容，只要 调用该函数，Lua就是自己对其内存进行处理，无需程序员得干预，当然，这样也说明了，不可以带走栈中的内存，也就是不可以将栈中弹出来的内存如字符串内存用作他用，否则可能 在pop后，该内存将失效。

####整个程序逻辑

首先lua_getglobal(lua,"app_content");将配置文件中app_content变量压入交互栈（-1）位置，然后lua_pushnil(lua);将nil压入交互栈（-1）位置以供后续的lua_next作首个元素使用。 app_content被压入下一层（-2），接着进while循环，用lua_next进行迭代，初次遇到nil，会随机的取得一对键值，然后将键和值压入交互栈，得到的结果就是:(-2)位置为key,（-1） 位置为value.Table自然被压入（-3）位置。在处理完value（如printf）后，用pop将value弹出，留下key用作下一对值的前辈，这时，（-1）位置为当前key，（-2）位置为Table，再次进 while循环的next函数，去处理下一对键值。最后当所有键值对都处理完全后，next返回0，退出while循环。


###总结

变量Table的一个总的结构就是

    lua_getglobal(L, table_name);
    lua_pushnil(L);
    while (lua_next(L, -2)) {
        /* 处理相应数据。此时栈上 -1 处为 value, -2 处为 key */
        lua_pop(L, 1);
    }

当然，这里的索引是根据需要进行变更的。


###C API 遍历 table

####按 key 遍历版本

	lua_getglobal(L, t); 
	lua_pushnil(L); 
	while (lua_next(L, -2)){ 
		/* 此时栈上 -1 处为 value, -2 处为 key */ 
		lua_pop(L, 1); 
	}
	
![lua_next]({IMAGE_PATH}/lua_table_to_c/lua_next.png)

lua_next 函数针对 -2 处（参数指定）的 Table 进行遍历。弹出 -1 处（栈顶）的值作为上一个 key（为 nil 时视为请求首个 key），压入 Table 中的下一个 key 和 value。返回值表示是否存在下一个 key。

另外在循环中处理值时要记得随时清理栈，否则 Table 就不在 -2 了。（也可以考虑在 lua_getglobal 后用lua_gettop 存下 Table 的正数索引。）

虽然这是手册中记载的遍历方法，但这种方法在遍历时并没有一定的遍历顺序，于是便又有了下面的方法。

####按整数索引遍历

	lua_getglobal(L, t); 
	len = lua_objlen(L, -1); 
	for (i = 1; i <= len; i++) { 
		lua_pushinteger(L, i); 
		lua_gettable(L, -2); 
		/* 此时栈顶即为 t[i] 元素 */ 
		lua_pop(L, 1);
	}
	
这种方法无视了非整数 key，但可以保证遍历顺序。如果只关注整数 key，可以考虑用这种遍历方法 :)
