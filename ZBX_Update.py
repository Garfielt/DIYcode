# -*- coding: gbk -*-
"""
Created on Thu Aug 25 10:06:41 2011

@author: 01188416
"""
import os, sys
import wx
import serial
import threading
import time
import json
import struct
import urllib2

PWD = os.path.dirname(os.path.abspath(sys.argv[0]))
today = time.strftime("%Y%m%d",time.localtime())
VERSION = "V1.1"

pfile = open('update.bin','rb')
programe = pfile.read()
pfile.close()


class ComDev:
    def __init__(self, comconf):
        self.comport = comconf["port"]
        self.baudrate = comconf["baudrate"]
        self.stopbits = comconf["stopbits"]
        self.bytesize = comconf["bytesize"]
        self.parity = comconf["parity"]
        self.timeout = 0.2
        self.com = None
        self.Open()
        
    def Open(self):
        try:
            #print self.comport,self.baudrate, self.bytesize,self.parity,self.stopbits
            self.com = serial.Win32Serial(self.comport,baudrate=self.baudrate, bytesize=self.bytesize,parity=self.parity,
                                          stopbits=self.stopbits,xonxoff=0, timeout=self.timeout)
        except:
            self.com = None
            print 'Open %s fail!' % self.comport
            
    def Close(self):
        if type(self.com) != type(None):
            self.com.close()
            self.com = None
            return True
        return False

    def ReadData(self, cmdData, returnFlag = 0, stime = 0.2):
        if type(self.com) != type(None):
            try:
                text = ""
                while True:
                    self.com.write(cmdData)
                    time.sleep(0.5)
                    text = text + self.com.read(1)
                    if text:
                        n = self.com.inWaiting()
                        if n:
                            text = text + self.com.read(n)
                        if ord(text[-1]) == 62:
                            break
                    if returnFlag:
                        break
                return text
            except:
                print 'ReadData fail!'
                #self.Close()
                return None
            return None

    def IsOpen(self):
        return type(self.com) != type(None)

class ZbxTesting:
    def __init__(self, comport, disport=0):
        self.errorflag = 0
        self.tvoice = 1
        comconf = {"baudrate":115200, "bytesize":8, "parity":"N", "stopbits":1}
        comconf["port"] = comport
        self.ZBXCom = ComDev(comconf)
        frame.reSetvalue("***开始检测***", 1, disport)
        if True:
            frame.reSetvalue("正在连接……", 1, disport)
            self.ZBXCom.ReadData(struct.pack('B', 0x1c))
            Ident = self.ZBXCom.ReadData("IDENT\r\n", 1)
            if Ident.find("NEC61215"):
                frame.reSetvalue("1、IDENT OK", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("1、IDENT Fail", 1, disport)
            Ver = self.ZBXCom.ReadData("VER\r\n", 1)
            if Ver.find("Ver01.02"):
                frame.reSetvalue("2、Ver OK", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("2、Ver Fail", 1, disport)
            cinfo = self.ZBXCom.ReadData("INFO\r\n", 1)
            if cinfo.find("Done"):
                frame.reSetvalue("3、INFO OK", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("3、INFO Fail", 1, disport)
            self.ZBXCom.Close()
            self.ZBXCom.Open()
            Ident = self.ZBXCom.ReadData("IDENT\r\n", 1)
            if Ident.find("NEC61215"):
                frame.reSetvalue("7、Ident OK", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("7、IDENT Fail", 1, disport)
            Ver = self.ZBXCom.ReadData("VER\r\n", 1)
            if Ver.find("Ver01.02"):
                frame.reSetvalue("8、Ver OK", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("8、Ver Fail", 1, disport)
            self.ZBXCom.ReadData("UPDATE 0 50000\r\n", 1)
            self.ZBXCom.ReadData(programe, 1)
            Uprog = self.ZBXCom.ReadData(struct.pack('B', 0x04), 1, 0.5)
            if Uprog.find("Done"):
                frame.reSetvalue("9、Update OK!", 1, disport)
            else:
                self.errorflag = 1
                frame.reSetvalue("9、Update Fail", 1, disport)
            #print Uprog
            self.ZBXCom.Close()
            self.ZBXCom = None
            frame.reSetvalue("***检测完成，耗时：%.2f S***" % (time.time()-frame.dtime), 1, disport)
            frame.reSetColor(self.errorflag, disport)
            if self.errorflag:
                frame.reSetvalue("=====> NG <=====", 1, disport)
            else:
                frame.reSetvalue("=====> OK <=====", 1, disport)
            frame.upthreads[disport] = 0
            print "Thread_%s End" % disport

class MainWindow(wx.Frame):
    def __init__(self):
        self.upthreads = [0, 0]
        self.conffile = "zbx.conf"
        self.conf = {"twotest":0, "left":"COM1", "right":"COM2"}
        self.twidth = 330
        self.dtime = 0
        self.Init()
        
        wx.Frame.__init__(self, None, -1, '青岛电子直播星升级工具 - PowerBy 青岛电子 新品转化平台 ' + VERSION, 
                          size=(950, 680), style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour('D4D0C8')
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-3, -2])
        self.statusbar.SetStatusText(" Power by 青岛电子 新品转化平台 liuweitao@haier.com " + VERSION, 0)
        self.statusbar.SetStatusText(u" 使用串口：%s|%s" % (self.conf["left"], self.conf["right"]), 1)
        

        ID_TWO = wx.NewId()        
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        comset = menu.Append(-1, "串 口 配 置")
        twotest = menu.AppendCheckItem(ID_TWO, "双串口检测")
        fexit = menu.Append(-1, "退  出")
        menuBar.Append(menu, "更改配置")
        menu = wx.Menu()
        starttest = menu.Append(-1, "开始测量")
        restart = menu.Append(-1, "重新测量(R)")
        menuBar.Append(menu, "检测控制")
        menu = wx.Menu()
        sabout = menu.Append(-1, "关于软件")
        menuBar.Append(menu, "关于软件")
        self.SetMenuBar(menuBar)
        if self.conf["twotest"]:
            menuBar.Check(ID_TWO, 1)
        self.Bind(wx.EVT_MENU, self.OnExit, fexit)
        self.Bind(wx.EVT_MENU, self.OnEnter, starttest)
        self.Bind(wx.EVT_MENU, self.OnRestart, restart)
        self.Bind(wx.EVT_MENU, self.OnTwoTest, twotest)
        self.Bind(wx.EVT_MENU, self.OnSetCom, comset)
        self.Bind(wx.EVT_MENU, self.About, sabout)
        
        hbox = wx.BoxSizer(wx.VERTICAL)
        f1box = wx.FlexGridSizer(1, 2, 10, 50)
        f2box = wx.FlexGridSizer(1, 2, 10, 10)
        f3box = wx.FlexGridSizer(2, 4, 10, 10)
        
        #-----------------  Title  ------------------
        ltLabel = wx.StaticText(self, -1, '青岛电子直播星升级工具', style=wx.TE_CENTER)
        ltLabel.SetFont(wx.Font(36, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        
        #---------------------  检测控制  ------------------
        self.start = wx.Button(self, label="开始检测(S)", size=(400, 50))
        self.restart = wx.Button(self, label="重新检测(R)", size=(400, 50))
        self.start.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        self.restart.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        f1box.AddMany([(self.start, 1, wx.ALIGN_CENTRE), (self.restart, 1, wx.ALIGN_CENTRE)])
                       
        #-----------------Display-----------------------
        self.displayleft = wx.TextCtrl(self, -1, "", size=(420, 450), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.displayleft.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        self.displayright = wx.TextCtrl(self, -1, "", size=(420, 450), style=wx.TE_MULTILINE|wx.TE_READONLY)
        self.displayright.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        
     
        f2box.AddMany([(self.displayleft), (self.displayright)])
        hbox.Add(ltLabel, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
        hbox.Add(f1box, 0, wx.ALL | wx.ALIGN_CENTRE, 10)
        hbox.Add(f2box, 0, wx.ALL | wx.ALIGN_CENTRE, 5)
        self.SetSizer(hbox)

        self.Bind(wx.EVT_BUTTON, self.OnEnter, self.start)
        self.Bind(wx.EVT_BUTTON, self.OnRestart, self.restart)
        acceltbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord("R"), restart.GetId()),\
                                        (wx.ACCEL_NORMAL, ord("S"), starttest.GetId()),
                                        (wx.ACCEL_NORMAL, 32, starttest.GetId())])
        self.SetAcceleratorTable(acceltbl)

    def Init(self):
        try:
            mfile = open(self.conffile, 'r')
            self.conf = json.loads(mfile.read())
            mfile.close()
            print self.conf
        except:
            print "Local Config Not Found!"
    
    def BackConf(self):
        mfile = open(self.conffile, 'w')
        mfile.write(json.dumps(self.conf))
        mfile.close()

    def OnEnter(self,event):
        self.dtime = time.time()
        if self.upthreads[0] == 0:
            self.upthreads[0] = 1
            self.displayleft.SetBackgroundColour("white")
            self.displayleft.SetValue("")
            ZbxTestThread1 = threading.Thread(target = ZbxTesting, args = (self.conf["left"], 0), name = 'ZbxTestThread1')
            ZbxTestThread1.start()
        if self.upthreads[1] == 0:
            if self.conf["twotest"]:
                self.upthreads[1] = 1
                self.displayright.SetBackgroundColour("white")
                self.displayright.SetValue("")
                ZbxTestThread2 = threading.Thread(target = ZbxTesting, args = (self.conf["right"], 1), name = 'ZbxTestThread2')
                ZbxTestThread2.start()

    def OnSetCom(self, event):
        dlg = wx.TextEntryDialog(None, "配置检测用串口，两个串口用\",\"隔开", '串口配置',
                                 self.conf["left"][3:]+","+self.conf["right"][3:])
        if dlg.ShowModal() == wx.ID_OK:
            try:
                coms = map(lambda c: "COM%s" % int(c), dlg.GetValue().split(","))
                if len(coms) > 1:
                    (self.conf["left"], self.conf["right"]) = coms[0:2]
                else:
                    self.conf["left"] = coms[0]
                print self.conf
            except:
                print "Input Error!"
        dlg.Destroy()
        self.BackConf()
        self.statusbar.SetStatusText(" 使用串口：%s|%s" % (self.conf["left"], self.conf["right"]), 1)

    def OnTwoTest(self, event):
        if self.conf["twotest"]:
            self.conf["twotest"] = 0
            print "Test One Box"
        else:
            self.conf["twotest"] = 1
            print "Test Two Box"
        self.BackConf()
        
    def showMessage(self, msg):
        dlg = wx.MessageDialog(None, msg, '确认！', wx.OK | wx.ICON_EXCLAMATION)
        result = dlg.ShowModal()
        dlg.Destroy()
        
    def OnExit(self, event):
        self.Close()

    def About(self, event):
        msg = "软件检测项目及流程:\n\n"
        msg += "1、尝试打开机顶盒串口;\n\n"
        msg += "2、发送初始化命令;\n\n"
        msg += "3、传输程序，完成升级。\n\n"
        msg += "PowerBy 青岛电子 新品转化平台\n\n"
        msg += "问题反馈：Email:liuweitao@haier.com    Tel:88937715\n\n"
        msg += "软件更新请访问：http://192.168.79.188/iscsky/"
        dlg = wx.MessageDialog(None, msg, '使用帮助', wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()
        
    def OnRestart(self,event):
        self.upthreads = [0, 0]
        print "Reset"
        
    def reSetColor(self, errorflag, disport = 0):
        if disport:
            if errorflag:
                self.displayright.SetBackgroundColour("yellow")
            else:
                self.displayright.SetBackgroundColour("green")
        else:
            if errorflag:
                self.displayleft.SetBackgroundColour("yellow")
            else:
                self.displayleft.SetBackgroundColour("green")
                
    def reSetvalue(self, data, lr = 1, disport = 0):
        if disport:
            tmpdataright = self.displayright.GetValue()
            if lr:
                self.displayright.SetValue(tmpdataright + data + "\n")
            else:
                self.displayright.SetValue(tmpdataright + data)
        else:
            tmpdataleft = self.displayleft.GetValue()
            if lr:
                self.displayleft.SetValue(tmpdataleft + data + "\n")
            else:
                self.displayleft.SetValue(tmpdataleft + data)

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MainWindow()
    frame.Show()
    app.MainLoop()
