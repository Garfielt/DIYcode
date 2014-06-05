# -*- coding: gbk -*-
"""
Created on Thu Aug 25 10:06:41 2011

@author: 01188416
"""
import os, sys
import time
import wx
import threading
import serial
import json
import pythoncom
import pyHook
import win32api
import win32con
import socket,asyncore


reload(sys)
sys.setdefaultencoding('gbk')
Mtype = "ZTE_GSM"


class ComDev:
    def __init__(self, comconf, waittime=20):
        self.comport = comconf["port"]
        self.baudrate = comconf["baudrate"]
        self.stopbits = comconf["stopbits"]
        self.bytesize = comconf["bytesize"]
        self.parity = comconf["parity"]
        self.waittime = waittime
        self.com = None
        self.Open()
        
    def Open(self):
        try:
            #print self.comport,self.baudrate, self.bytesize,self.parity,self.stopbits
            self.com = serial.Win32Serial(self.comport,baudrate=self.baudrate, bytesize=self.bytesize,parity=self.parity,
                                          stopbits=self.stopbits,xonxoff=0, timeout=0.8)
        except:
            self.com = None
            
    def Close(self):
        if type(self.com) != type(None):
            self.com.close()
            self.com = None
            return True
        return False

    def ReadData(self, cmdData, waittime = 20):
        if type(self.com) != type(None):
            try:
                #tmp = self.com.read(1)
                timecount = 0
                text = ""
                while True:
                    if timecount == waittime:
                        text = ""
                        break
                    self.com.write(cmdData)
                    time.sleep(0.4)
                    text = text + self.com.read(1)
                    if text:
                        n = self.com.inWaiting()
                        if n:
                            text = text + self.com.read(n)
                        if text.find("CGSN")>0:
                            break
                        if text.find("OK")>0:
                            break
                    timecount += 1
                return text
            except:
                print 'ReadData fail!'
                #self.Close()
            return None

    def IsOpen(self):
        return type(self.com) != type(None)

class forwarder(asyncore.dispatcher):
    def __init__(self, ip, port, remoteip,remoteport,backlog=5):
        asyncore.dispatcher.__init__(self)
        self.remoteip=remoteip
        self.remoteport=remoteport
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((ip,port))
        self.listen(backlog)

    def handle_accept(self):
        conn, addr = self.accept()
        # print '--- Connect --- '
        sender(receiver(conn),self.remoteip,self.remoteport)

class receiver(asyncore.dispatcher):
    def __init__(self,conn):
        asyncore.dispatcher.__init__(self,conn)
        self.from_remote_buffer=''
        self.to_remote_buffer=''
        self.sender=None

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        if read.find("cainfo")>0:
            frame.GprsToff()
        self.from_remote_buffer += read

    def writable(self):
        return (len(self.to_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.to_remote_buffer)
        # print '%04i <--'%sent
        self.to_remote_buffer = self.to_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        if self.sender:
            self.sender.close()

class sender(asyncore.dispatcher):
    def __init__(self, receiver, remoteaddr,remoteport):
        asyncore.dispatcher.__init__(self)
        self.receiver=receiver
        receiver.sender=self
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((remoteaddr, remoteport))

    def handle_connect(self):
        pass

    def handle_read(self):
        read = self.recv(4096)
        # print '<-- %04i'%len(read)
        self.receiver.to_remote_buffer += read

    def writable(self):
        return (len(self.receiver.from_remote_buffer) > 0)

    def handle_write(self):
        sent = self.send(self.receiver.from_remote_buffer)
        # print '--> %04i'%sent
        self.receiver.from_remote_buffer = self.receiver.from_remote_buffer[sent:]

    def handle_close(self):
        self.close()
        self.receiver.close()

class GPRSDate:
    def __init__(self, comport, disport=0):
        comconf = {"baudrate":9600, "bytesize":8, "parity":"N", "stopbits":1}
        comconf["port"] = comport
        self.GPRSCom = ComDev(comconf)
        if self.GPRSCom.com == None:
            frame.button.SetLabel("串口错误")
            self.cclose()
            frame.running = 0
        CmdConf = {'ZTE_GSM':'AT+CGSN\r', 'HOMTAR':'AT+EGMR=0,7\n',
                   'MINXUN':'AT+CGSN\r', 'ZTE_CDMA':'AT+CIMI\r'}
        #self.KeyOutput("862602003478088")
        Exresult = self.ExcuteCmd(CmdConf[Mtype])
        disstr = "读取成功"
        getok = 1
        if Exresult["stat"] == 1:
            if Mtype == 'ZTE_GSM':
                startint = Exresult["data"].find('CGSN')
                imei = Exresult["data"][(startint+7):(startint+22)]
            elif Mtype == 'HOMTAR':
                startint = Exresult["data"].find(':')
                imei = Exresult["data"][(startint+1):(startint+16)]
            elif Mtype == 'MINXUN':
                startint = Exresult["data"].find(':')
                imei = Exresult["data"][(startint+3):(startint+17)]
            elif Mtype == 'ZTE_CDMA':
                startint = Exresult["data"].find(':')
                imei = Exresult["data"][(startint+3):(startint+18)]
            else:
                frame.button.SetLabel("模块异常")
            try:
                doct = range(96, 106)
                for s in imei:
                    n = int(s)
                    if 0 <= n <= 9:
                        win32api.keybd_event(doct[n], 0, 0, 0)
                        win32api.keybd_event(doct[n], 0, win32con.KEYEVENTF_KEYUP, 0)
                win32api.keybd_event(13, 0, 0, 0)
                win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
            except:
                getok = 0
                disstr = "发送失败"
        else:
            getok = 0
            disstr = "读取失败"
        
        self.cclose()
        frame.running = 0
        frame.button.SetLabel(disstr)
        if frame.conf["detime"] and getok:
            time.sleep(frame.conf["detime"]/1000.0)
            frame.GprsToff()


    def KeyOutput(self, data):
        doct = range(96, 106)
        for s in data:
            n = int(s)
            if 0 <= n <= 9:
                win32api.keybd_event(doct[n], 0, 0, 0)
                win32api.keybd_event(doct[n], 0, win32con.KEYEVENTF_KEYUP, 0)
        win32api.keybd_event(13, 0, 0, 0)
        win32api.keybd_event(13, 0, win32con.KEYEVENTF_KEYUP, 0)
        
    def ExcuteCmd(self, Cmd):
        Returns = {}
        Response = self.GPRSCom.ReadData(Cmd)
        if Response != "":
            Returns["stat"] = 1
            Returns["data"] = Response
        else:
            Returns["stat"] = 0
            Returns["data"] = Response
        return Returns
    
    def cclose(self):
        self.GPRSCom.Close()
        self.GPRSCom = None

class GPRSReset:
    def __init__(self, comport, disport=0):
        comconf = {"baudrate":9600, "bytesize":8, "parity":"N", "stopbits":1}
        comconf["port"] = comport
        self.GPRSCom = ComDev(comconf)
        if self.GPRSCom.com == None:
            frame.button.SetLabel("串口错误")
            self.cclose()
            frame.running = 0
        disstr = "重启成功"
        Exresult = self.ExcuteCmd("AT+CFUN=1,1\r")
        if Exresult["stat"] != 1:
            disstr = "重启失败"
        self.cclose()
        frame.running = 0
        frame.button.SetLabel(disstr)

    def ExcuteCmd(self, Cmd):
        Returns = {}
        #print CmdStr
        Response = self.GPRSCom.ReadData(Cmd, 8)
        if Response != "":
            Returns["stat"] = 1
            Returns["data"] = Response
        else:
            Returns["stat"] = 0
            Returns["data"] = Response
        return Returns
    
    def cclose(self):
        self.GPRSCom.Close()
        self.GPRSCom = None
        
class MainFrame(wx.Frame):

    def __init__(self):
        self.conf = {"comport": "COM4", "mtype":0, "triglen":12, "detime":1000}
        self.running = 0
        self.ScanData = ""
        self.Mtypes = ['ZTE_GSM', 'HOMTAR', 'MINXUN', 'ZTE_CDMA']
        self.Init()
        
        wx.Frame.__init__(self, None, -1, '直播星IMEI号自动获取工具',
                size=(400, 168))
        self.panel = wx.Panel(self)
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(5)
        self.statusbar.SetStatusWidths([-3, -3, -3, -2, -3])
        self.statusbar.SetStatusText(" 新品转化平台", 0)
        self.statusbar.SetStatusText("串口:%s" % self.conf["comport"], 1)
        self.statusbar.SetStatusText("模块:%s" % self.Mtypes[self.conf["mtype"]], 2)
        self.statusbar.SetStatusText("码长:%s" % self.conf["triglen"], 3)
        self.statusbar.SetStatusText("延时:%s" % self.conf["detime"], 4)
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        comset = menu.Append(-1, "串口设置")
        typeset = menu.Append(-1, "模块设置")
        tlenset = menu.Append(-1, "码长设置")
        detimeset = menu.Append(-1, "延时设置")
        menuBar.Append(menu, "软件设置")
        menu = wx.Menu()
        sabout = menu.Append(-1, "关于软件")
        menuBar.Append(menu, "关于软件")
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.OnSetCom, comset)
        self.Bind(wx.EVT_MENU, self.About, sabout)
        self.Bind(wx.EVT_MENU, self.OnSetType, typeset)
        self.Bind(wx.EVT_MENU, self.OnSetTlen, tlenset)
        self.Bind(wx.EVT_MENU, self.OnSetDtime, detimeset)
        
        self.button = wx.Button(self.panel, label="开 始 运 行", pos=(100, 20),
                size=(200, 50))
        self.button.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        self.button.SetLabel("运行中")
        self.panel.SetBackgroundColour('Green')
        self.panel.Refresh()

    def Init(self):
        global Mtype
        if os.path.isfile('zbxTrig.conf'):
            mfile = open('zbxTrig.conf', 'r')
            self.conf = json.loads(mfile.read())
            mfile.close()
            if not self.conf.has_key("detime"):
                self.conf["detime"] = 1000
            Mtype = self.Mtypes[self.conf["mtype"]]
        else:
            print "Local Config Not Found!"

    def BackConf(self):
        mfile = open('zbxTrig.conf', 'w')
        mfile.write(json.dumps(self.conf))
        mfile.close()
     
    def OnSetCom(self, event):
        dlg = wx.TextEntryDialog(None, "配置检测用串口", '串口配置', self.conf["comport"][3:])
        if dlg.ShowModal() == wx.ID_OK:
            self.conf["comport"] = "COM%s" % dlg.GetValue()
        dlg.Destroy()
        self.statusbar.SetStatusText("串口:%s" % self.conf["comport"], 1)
        self.BackConf()
        
    def OnSetType(self, event):
        global Mtype
        dlg = wx.SingleChoiceDialog(None, u'请选择生产模块类型！', u'模块类型选择', self.Mtypes)
        dlg.SetSelection(self.conf["mtype"])
        if dlg.ShowModal() == wx.ID_OK:
            #self.conf["mtype"] = dlg.GetStringSelection()
            self.conf["mtype"] = dlg.GetSelection()
            Mtype = self.Mtypes[self.conf["mtype"]]
            self.statusbar.SetStatusText("模块:%s" % self.Mtypes[self.conf["mtype"]], 2)
        dlg.Destroy()
        self.BackConf()
        
    def OnSetTlen(self, event):
        dlg = wx.TextEntryDialog(None, "配置触发码长", '触发码长设置', str(self.conf["triglen"]))
        if dlg.ShowModal() == wx.ID_OK:
            self.conf["triglen"] = int(dlg.GetValue())
        dlg.Destroy()
        self.statusbar.SetStatusText("码长:%s" % self.conf["triglen"], 3)
        self.BackConf()
        
    def OnSetDtime(self, event):
        dlg = wx.TextEntryDialog(None, "设置GPRS模块关闭延时毫秒数（1S=1000ms）", '关闭延时设置', str(self.conf["detime"]))
        if dlg.ShowModal() == wx.ID_OK:
            self.conf["detime"] = int(dlg.GetValue())
        dlg.Destroy()
        self.statusbar.SetStatusText("延时:%s" % self.conf["detime"], 4)
        self.BackConf()
        
    def DealKey(self):
        if self.running == 0:
            if len(self.ScanData) == self.conf['triglen']:
                self.running = 1
                self.button.SetLabel("读取数据")
                GPRSImeiThread = threading.Thread(target = GPRSDate, args = (self.conf["comport"], 0), name = 'GPRSImeiThread')
                GPRSImeiThread.start()
        self.ScanData = ""
        return True
        
    def GprsToff(self):
        if self.running == 0:
            self.running = 1
            self.button.SetLabel("执行重启")
            GPRSResetThread = threading.Thread(target = GPRSReset, args = (self.conf["comport"], 0), name = 'GPRSResetThread')
            GPRSResetThread.start()
        return True
        
    def About(self, event):
        msg = "软件流程:\n\n"
        msg += "检测\"回车\"键，符合触发码长后自动获取IMEI并开始序列化。\n\n\n"
        msg += "Power By 青岛电子 新品转化平台\n\n"
        msg += "问题反馈：Email:liuweitao@haier.com    Tel:88937715\n\n"
        msg += "软件更新请访问：http://192.168.79.188/iscsky/"
        dlg = wx.MessageDialog(None, msg, '关于软件', wx.OK | wx.ICON_INFORMATION)
        result = dlg.ShowModal()
        dlg.Destroy()

def SQLMonitor():
    try:
        forwarder("127.0.0.1",3306,"192.168.10.10",3306)
        asyncore.loop()
    except:
        frame.button.SetLabel("监控失败")

def MonitorKeyboard():
    hm = pyHook.HookManager()
    hm.KeyDown = onKeyboardEvent
    hm.HookKeyboard()
    pythoncom.PumpMessages()

def onKeyboardEvent(event):
    exceptkeys = {0}
    intkey = event.Ascii
    #print intkey, chr(intkey)
    if intkey == 13:
        frame.DealKey()
    elif intkey == 32:
        frame.GprsToff()
        return False
    elif intkey in exceptkeys:
        pass
    else:
        frame.ScanData += chr(intkey)
    return True
   
if __name__ == '__main__':
    app = wx.PySimpleApp()
    frame = MainFrame()
    frame.Show()
    MonitorThread = threading.Thread(target = MonitorKeyboard, args = (), name = 'MonitorKeyboard')
    SQLMonitorThread = threading.Thread(target = SQLMonitor, args = (), name = 'SQLMonitorThread')
    MonitorThread.setDaemon(True)
    SQLMonitorThread.setDaemon(True)
    MonitorThread.start()
    SQLMonitorThread.start()
    app.MainLoop()