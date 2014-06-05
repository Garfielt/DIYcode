DIYcode
=======

My DIY Codes,backup for me,but may be also useful for you.


Introduce:

iNc.py:

Bind DNS,when a clent is found,the service will ping the clent and resolve the clent's mac.


main.box:

A local server write by NetBox.


Pcam.py:

Snap the camera and compare to a local pic。
从抓取摄像头抓取图片，然后与本地的目的图片对比相似度。之前打算做的机芯自动化检测。包括自动发命令（切信号源）并检测画面内容。


TvTest.py：

Auto send command to check a TVset.


TvTest_Full.py:

上面两个的组合，当时的设想还是蛮好的，可惜了了~


TvWB.py：

Auto WB。TV自动白平衡校准。


ZBX_Update.py：

直播星机芯板升级，原厂的工具需要N步操作，直接给仍了，自己抓命令自己写，但负责换板子的小姑娘说手上没事干容易犯困，情何以堪~


Zbx_Trigger.py：

代理Mysql的3306端口，监控到烧录工具发送某句SQL时（时机成熟时）获取GPRS定位模块的IMEI号后重启模块，以便正常完成序列化操作~