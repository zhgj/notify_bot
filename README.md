# 是什么？

是一个定时提醒机器人

# 能干什么？

定时提醒你干某件事情呗

# 谁要这个？

* 年纪大了，容易忘事情的
* 天生记不住事情的
* 用过第三方提醒软件的，但是担心自己的“小秘密”被发现的
* 发现第三方软件不稳定的，什么？不稳定就算了，还有收费？还限制发送条数？

那么统统让他们去吧

# 有什么特点？

* 不需要公网IP
* 不需要公网IP
* 不需要公网IP

只需一台能上网的windows机器

# 如何实现的？

1. 通过手机QQ的【我的电脑】发送要提醒的事情
2. 程序捕获电脑端QQ弹出的窗口，自动截图
3. 通过OCR识别截图中的提醒文字
4. 通过Apprise发送通知消息

呐，就是这么个原理，绕过了必须需要公网IP的限制

# 依赖软件

**QQ**
**[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)**
**[Apprise](https://github.com/caronc/apprise)**
**Python**：版本3.9+吧，因为我用的就是3.9
**Redis**

当然这里还有一堆需要 `pip install xxxx`的，拿到源码自己跑一下，缺啥装啥吧（认真的，我都忘记自己装过啥了，看下）

哈哈，用的其他依赖还不少吧

# 关键点

重点来了
重点来了
重点来了

1. 设置电脑端QQ来消息自动弹出窗口
2. 设置电脑长时间后不要锁屏，电源选项改为：从不，还有锁屏程序选择：无

# 无显示器注意点

设置好上面的两点后，有显示器的可以直接关闭屏幕啦；

没有显示器的要重点注意了，远程桌面连接断开后会导致电脑锁屏！！！所以每次断开远程机器要重启远程机器；那么每次重启就需要

1. 电脑账户自动登录
2. 提醒软件自动运行
3. 电脑QQ自动登录

# 说了这么多怎么用啊？

1. 打开手机QQ
2. 切换到[联系人]
3. 切换到[设备]
4. 点击[我的电脑]
5. 输入：明天晚上提醒我约女朋友看电影（认真脸：你有女朋友吗？）
6. 点击[发送]

我知道你的意思肯定是**如何部署**呀，忘了这茬了，根目录下 `apprise_notify.py` 就是入口文件

# Apprise如何使用呀？

拜托，请看Apprise的官方文档吧，传送门：[Apprise](https://github.com/caronc/apprise)，顺便给出Windows下的OCR识别软件地址吧，传送门：[Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)，QQ就不用给链接了吧？

# 写在最后

代码太乱，有很多无用源码，自己调试时只关注需要的就行，大佬不喜勿喷，这里其实主要提供一个绕过公网IP的思路，公网IP需要花钱不说，还要认证啥的，神JB烦呀，有了这个思路个人可以做其他好玩的软件
