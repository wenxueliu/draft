

最近用了外接显示器, 颈椎病好很多了, 所有建议所有码农都应该用外接显示器.
正常情况下, ubuntu 现在已经能很好的处理双屏了, 无论是克隆方式还是扩展方式.

刚开始一切正常, 但是最近突然不管怎么切换, 外接显示器的比例都不能调整到合适
的比例, 不管怎么重启机器, 都没有办法. 因此, 折腾是不可避免了.

###了解你的显示器

$ xrandr

    Screen 0: minimum 320 x 200, current 1366 x 768, maximum 32767 x 32767
    LVDS1 connected (normal left inverted right x axis y axis)
    1280x800       60.2 +   50.0
    1024x768       60.0
    800x600        60.3     56.2
    640x480        59.9
    VGA1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 194mm
    1366x768       59.8*+
    1024x768       75.1     72.0     70.1     60.0
    832x624        74.6
    800x600        72.2     75.0     60.3     56.2
    640x480        75.0     72.8     66.7     60.0
    720x400        70.1
    HDMI1 disconnected (normal left inverted right x axis y axis)
    DP1 disconnected (normal left inverted right x axis y axis)
    VIRTUAL1 disconnected (normal left inverted right x axis y axis)

LVDS1 是我笔记本的显示器名称, VGA1 是我的外接显示器名称. 我的显示器, 刚开始 VGA1
一直无法显示 1366x768, 因此屏幕比例严重失调, 根本无法使用.


###xrandr 常用命令

$ xrandr --output VGA1 --same-as LVDS1 --auto

打开外接显示器(--auto:最高分辨率), 与笔记本液晶屏幕显示同样内容（克隆）

$ xrandr --output VGA1 --same-as LVDS1 --mode 1280x1024

打开外接显示器(分辨率为1280x1024), 与笔记本液晶屏幕显示同样内容（克隆）

$ xrandr --output VGA1 --right-of LVDS1 --auto

打开外接显示器(--auto:最高分辨率), 设置为右侧扩展屏幕

$ xrandr --output VGA1 --off

关闭外接显示器

$ xrandr --output VGA1 --auto --output LVDS1 --off

打开外接显示器, 同时关闭笔记本液晶屏幕(只用外接显示器工作)

$ xrandr --output VGA1 --off --output LVDS1 --auto

关闭外接显示器，同时打开笔记本液晶屏幕 （只用笔记本液晶屏）

$ xrandr --output VGA1 --mode 1366x768 --output LVDS1 --off

打开外接显示器(分辨率1366x768), 同时关闭笔记本液晶屏幕(只用外接显示器工作),
我的问题就是通过这条解决的.

更多命令见 man xrandr 或 xrandr --help

###我的问题

$ xrandr

    Screen 0: minimum 320 x 200, current 1024 x 768, maximum 32767 x 32767
    LVDS1 connected 1024x768+0+0 (normal left inverted right x axis y axis) 261mm x 163mm
    1280x800       60.2 +   50.0
    1024x768       60.0*
    800x600        60.3     56.2
    640x480        59.9
    VGA1 connected primary 1024x768+0+0 (normal left inverted right x axis y axis) 0mm x 0mm
    1024x768       60.0*
    800x600        60.3     56.2
    848x480        60.0
    640x480        59.9
    HDMI1 disconnected (normal left inverted right x axis y axis)
    DP1 disconnected (normal left inverted right x axis y axis)
    VIRTUAL1 disconnected (normal left inverted right x axis y axis)

我并不知道自己屏幕的分辨率, 根据 [1], 试试呗.

$ xrandr --output VGA1 --same-as LVDS1 --mode 1280x1024

    xrandr: cannot find mode 1280x1024

显然不支持 1280x1024

$ dmesg | grep VGA

    [    1.149514] fb0: VESA VGA frame buffer device
    [    1.662664] fb: conflicting fb hw usage inteldrmfb vs VESA VGA - removing
    generic driver

后来想, 是显示器屏幕分辨率不对, 那就应该增加合适的分辨率, 根据 [2] 试验 1440x900

$ cvt 1440 900

    # 1440x900 59.89 Hz (CVT 1.30MA) hsync: 55.93 kHz; pclk: 106.50 MHz
    Modeline "1440x900_60.00"  106.50  1440 1528 1672 1904  900 903 909 934 -hsync
    +vsync

$ sudo xrandr --newmode "1440x900_60.00"  106.50  1440 1528 1672 1904  900 903
909 934 -hsync +vsync

$ sudo xrandr --addmode VGA1 1440x900

    xrandr: cannot find mode "1440x900"

$ xrandr

    Screen 0: minimum 320 x 200, current 1024 x 768, maximum 32767 x 32767
    LVDS1 connected 1024x768+0+0 (normal left inverted right x axis y axis) 261mm x 163mm
    1280x800       60.2 +   50.0  
    1024x768       60.0* 
    800x600        60.3     56.2  
    640x480        59.9  
    VGA1 connected primary 1024x768+0+0 (normal left inverted right x axis y axis) 0mm x 0mm
    1024x768       60.0* 
    800x600        60.3     56.2  
    848x480        60.0  
    640x480        59.9  
    HDMI1 disconnected (normal left inverted right x axis y axis)
    DP1 disconnected (normal left inverted right x axis y axis)
    VIRTUAL1 disconnected (normal left inverted right x axis y axis)
    1440x900_60.00 (0x160)  106.5MHz
            h: width  1440 start 1528 end 1672 total 1904 skew    0 clock   55.9KHz
            v: height  900 start  903 end  909 total  934           clock   59.9Hz

显然 VGA1 不支持分辨率 1440x900

$ sudo xrandr --rmmode "1440x900_60.00"

$ xrandr

    Screen 0: minimum 320 x 200, current 1366 x 768, maximum 32767 x 32767
    LVDS1 connected (normal left inverted right x axis y axis)
    1280x800       60.2 +   50.0
    1024x768       60.0
    800x600        60.3     56.2
    640x480        59.9
    VGA1 connected primary 1366x768+0+0 (normal left inverted right x axis y axis) 344mm x 194mm
    1366x768       59.8*+
    1024x768       75.1     72.0     70.1     60.0
    832x624        74.6
    800x600        72.2     75.0     60.3     56.2
    640x480        75.0     72.8     66.7     60.0
    720x400        70.1
    HDMI1 disconnected (normal left inverted right x axis y axis)
    DP1 disconnected (normal left inverted right x axis y axis)
    VIRTUAL1 disconnected (normal left inverted right x axis y axis)

VGA1 意外添加了合适的分辨率

$ xrandr --output VGA1 --mode 1366x768 --output LVDS1 --of

搞定.

###参考

[1]: http://blog.chinaunix.net/uid-170694-id-2833685.html
[2]: http://forum.ubuntu.org.cn/viewtopic.php?f=42&t=458723
