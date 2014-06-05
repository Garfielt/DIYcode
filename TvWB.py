# -*- coding: gbk -*-
"""
Created on Thu Aug 25 10:06:41 2011

@author: 01188416
"""
import os, sys
import wx
import serial
import struct
import threading
import time
import sqlite3, locale, types

class BlockWindow(wx.Panel):
    def __init__(self, parent, ID=-1, label="",
                 pos=wx.DefaultPosition, size=(100, 25)):
        wx.Panel.__init__(self, parent, ID, pos, size,
                          wx.RAISED_BORDER, label)
        self.label = label
        self.SetBackgroundColour("white")
        self.SetMinSize(size)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

    def OnPaint(self, evt):
        sz = self.GetClientSize()
        dc = wx.PaintDC(self)
        w,h = dc.GetTextExtent(self.label)
        dc.SetFont(self.GetFont())
        dc.DrawText(self.label, (sz.width-w)/2, (sz.height-h)/2)

class ComDev:
    def __init__(self, comconf, waittime=5):
        self.comport = comconf["port"]
        self.baudrate = comconf["baudrate"]
        self.stopbits = comconf["stopbits"]
        self.bytesize = comconf["bytesize"]
        self.parity = comconf["parity"]
        self.waittime = waittime
        self.com = None
        self.refreshFlag = 0
        self.comData = {}
        self.Open()
        
    def Open(self):
        try:
            #print self.comport,self.baudrate, self.bytesize,self.parity,self.stopbits
            self.com = serial.Win32Serial(self.comport,baudrate=self.baudrate, bytesize=self.bytesize,parity=self.parity,
                                          stopbits=self.stopbits,xonxoff=0, timeout=1)
        except:
            self.com = None
            print 'Open %s fail!' % self.comport
    def Close(self):
        if type(self.com) != type(None):
            self.com.close()
            self.com = None
            return True
        return False

    def ReadData(self,cmdData):
        if type(self.com) != type(None):
            try:
                #tmp = self.com.read(1)
                self.com.write(cmdData)
                timecount = 0
                while timecount < self.waittime:
                    timecount += 1
                    text = self.com.read(1)
                    if text:
                        print text
                        n = self.com.inWaiting()
                        if n:
                            text = text + self.com.read(n)
                        #print ord(text[-1])
                        if ord(text[-1]) == 208:
                            print text[-1]
                            break
                return text
            except:
                print 'ReadData fail!'
                self.Close()
                return None
            return None
    def ReadOnly(self):
        if type(self.com) != type(None):
            text = ""
            try:
                while 1:
                    text = text + self.com.read(1)
                    n = self.com.inWaiting()
                    if n:
                        text = text + self.com.read(n)
                    if ord(text[-1]) == 13:
                        if len(text)>15:
                            comReadData = text[-13:-1]
                            #comReadData = comReadStr.split()[1]
                            [self.comData["dx"], self.comData["dy"], self.comData["Y"]] = comReadData.split(";")
                            frame.reSetvalue(self.comData)
                            text = ""
                            self.refreshFlag = 1
            except:
                print 'ReadData fail!'
                self.ReadOnly()
    def SendData(self,cmdData):
        if type(self.com) != type(None):
            try:
                self.com.write(cmdData)
                return True
            except:
                print 'SendData fail!'
                self.Close()
                return False
            return False
    def IsOpen(self):
        return type(self.com) != type(None)

class DBStorage:
    def __init__(self, path):
        self.localcharset = locale.getdefaultlocale()[1]
        self.charset = 'gbk'
        self.path = path
        if type(path) == types.UnicodeType:
            self.path = path.encode(self.charset)
        self.db = sqlite3.connect(self.path)
        self.version = '' 
    def close(self):
        self.db.close()
        self.db = None

    def execute(self, sql, autocommit=True):
        self.db.execute(sql)
        if autocommit:
            self.db.commit()

    def execute_param(self, sql, param, autocommit=True):
        self.db.execute(sql, param)
        if autocommit:
            self.db.commit()

    def commit(self):
        self.db.commit()
        
    def rollback(self):
        self.db.rollback()

    def query(self, sql, iszip=True):
        if type(sql) == types.UnicodeType:
            sql = sql.encode(self.charset, 'ignore')
 
        cur = self.db.cursor()
        cur.execute(sql)
 
        res = cur.fetchall()
        ret = []

        if res and iszip:
            des = cur.description
            names = [x[0] for x in des]
 
            for line in res:
                ret.append(dict(zip(names, line))) 
        else:
            ret = res 

        cur.close()
        return ret 

    def query_one(self, sql):
        if type(sql) == types.UnicodeType:
            sql = sql.encode(self.charset, 'ignore')
 
        cur = self.db.cursor()
        cur.execute(sql)
        one = cur.fetchone()
        cur.close()
        
        if one:
            return one[0]
        return None

    def last_insert_id(self):
        sql = "select last_insert_rowid()"
        cur = self.db.cursor()
        cur.execute(sql)
        one = cur.fetchone()
        cur.close()
        return one[0]

class TvTuning:
    def __init__(self):
        self.Tvcomconf = {"port":"COM8", "baudrate":115200, "bytesize":8, "parity":"N", "stopbits":1}
        self.TVcom = ComDev(self.Tvcomconf)
        self.Gain = {"R":122, "G":122, "B":122}
        self.GainCmd = {"R":[0xc9, 0x32, 0x00, 0x00, 0x00, 0xD0],
                        "G":[0xc9, 0x33, 0x00, 0x00, 0x00, 0xD0],
                        "B":[0xc9, 0x34, 0x00, 0x00, 0x00, 0xD0]}
        self.factoryoff = 1
        self.tnotok = 1
        print "Try Turn Factory On!"
        while self.factoryoff:
            cmdbyte = ""
            #[0xc9, 0x30, 0x00, 0x00, 0x02, 0xD0]
            scmd = [0xc9, 0x3c, 0x00, 0x00, 0x00, 0xD0]
            scmd[4] = numOfOne(scmd[1]) + numOfOne(scmd[2]) + numOfOne(scmd[3])
            for ss in scmd:
                cmdbyte = cmdbyte + struct.pack('B', ss)
            Response = self.TVcom.ReadData(cmdbyte)
            print " - OK!"
            if Response:
                resCmd = self.toHexStr(Response)
                print resCmd[-1:6]
                print "Received:" + resCmd
                print "Hex:",
                for r in Response:
                    print hex(ord(r)),
                if resCmd[-12:] == "c95a000004d0":
                    print "Turn Factory On!"
                    self.factoryoff = 0
                elif resCmd[-12:] == "c95b000005d0":
                    print "Verify Error!"
                else:
                    print "Turn Factory Error!"
            else:
                print "No Answer! Confirm Com Device Or Connect!"
        while self.tnotok:
            dochange = 1
            if ChromaCom.refreshFlag == 1:
                ChromaCom.refreshFlag = 0
                ChromaData = ChromaCom.comData
                print "ChromaData Now:",
                print ChromaData,
                if ChromaData["dy"] <= 276:
                    print "set Bgain down"
                    dochange = 1
                    self.tuning("B", -1)
                elif ChromaData["dy"] >= 280:
                    print "set Bgain up"
                    dochange = 1
                    self.tuning("B", 1)
                if ChromaData["dx"] <= 275:
                    print "set Rgain up"
                    dochange = 1
                    self.tuning("R", 1)
                elif ChromaData["dy"] >= 279:
                    print "set Rgain down"
                    dochange = 1
                    self.tuning("R", -1)
            else:
                print "No Data Refresh!"
            time.sleep(1)
            #if dochange == 1:
                #pass
                #self.tnotok = 0
        self.cclose()
        frame.startthread = 0
        print "Thread End!"
    def tuning(self, G ,direction = 0):
        while 1:
            print "Sending:",
            Cmd = self.GainCmd[G]
            if direction == 1:
                self.Gain[G] = self.Gain[G] + 1
            elif direction == -1:
                self.Gain[G] = self.Gain[G] - 1
            Cmd[3] = self.Gain[G]
            Cmd[4] = numOfOne(Cmd[1]) + numOfOne(Cmd[2]) + numOfOne(Cmd[3])
            cmdbyte = ""
            for ss in Cmd:
                cmdbyte = cmdbyte + struct.pack('B', ss)
                print hex(ss),
            Response = self.TVcom.ReadData(cmdbyte)
            print " - OK!"
            if Response:
                resCmd = self.toHexStr(Response)
                print resCmd[-1:6]
                print "Received:" + resCmd
                print "Hex:",
                for r in Response:
                    print hex(ord(r)),
                if resCmd[-12:] == "c95a000004d0":
                    print ""
                    print "Execute OK!"
                    return 1
                elif resCmd[-12:] == "c95b000005d0":
                    print ""
                    print "Verify Error!"
                    return 0
                else:
                    print ""
                    print "Execute Error!"
                    return 2
            else:
                print "No Answer! Confirm Com Device Or Connect!"
    def toHexStr(self, s):
        lst = []
        for ch in s:
            hv = hex(ord(ch)).replace('0x', '')
            if len(hv) == 1:
                hv = '0' + hv
            lst.append(hv)
        return reduce(lambda x,y:x+y, lst)
    
    def cclose(self):
        self.TVcom.Close()
        self.TVcom = None

def Tvrecord(data):
    PWD = os.path.dirname(os.path.abspath(sys.argv[0]))
    Sqldb  = os.path.join(PWD, "Tv-white.db")
    Creattable = 0
    if os.path.isfile(Sqldb):
        Creattable = 1
    db = DBStorage(Sqldb)
    if Creattable:
        db.execute("CREATE TABLE IF NOT EXISTS tvwhite (id integer PRIMARY KEY, \
                    sern varchar(24), dx int(3), dy int(3), Y int(3), ptime int(10))")
    sql = "insert into tvwhite (sern,dx,dy,Y,ptime) values (?,?,?,?,?)"
    db.execute_param(sql,(data["sern"], data["dx"], data["dy"], data["Y"],int(time.time())))
    db.close()

def toHexStr(s):
    lst = []
    for ch in s:
        hv = hex(ord(ch)).replace('0x', '')
        if len(hv) == 1:
            hv = '0' + hv
        lst.append(hv)
    return reduce(lambda x,y:x+y, lst)

def numOfOne(n):
    c = 0
    while(n):
        n = n & (n-1)
        c = c + 1
    return c

def toHex(h):
    hs = h.replace("0x","")
    return int(hs,16)

def doChange(Gtype, value):
    print "Set " + Gtype + "value:" + str(value)
    time.sleep(1)

ComCmd = {}
mfile = open('Tvcom.txt', 'r')
for line in mfile.readlines():
    line = line.replace("\n", "")
    nline = line.split()
    ComCmd[nline[0]] = nline[1:]
mfile.close()


class MainWindow(wx.Frame):
    def __init__(self):
        self.dxywidth = 150
        self.dxysize = 48
        self.idsize = 48
        self.idwidth = 800
        self.startthread = 0
        self.tdata = {}
        
        wx.Frame.__init__(self, None, -1, '白平衡自动校正系统   Powerby 新品转化平台',  
                size=(960, 400))
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)
        self.statusbar.SetStatusText("Power by 新品转化平台", 0)
        menu = wx.Menu()
        menu.Append(-1, "功能")
        menu.AppendSeparator()
        exit = menu.Append(-1, "功能")
        self.Bind(wx.EVT_MENU, self.OnExit, exit)
        menuBar = wx.MenuBar()
        menuBar.Append(menu, "附加功能")
        self.SetMenuBar(menuBar)
        
        panel = wx.Panel(self, -1)
        
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        fbox = wx.FlexGridSizer(2, 2,30, 30)

        dxLabel = wx.StaticText(panel, -1, 'dx:',style=wx.TE_CENTER)
        dxLabel.SetFont(wx.Font(48, wx.SWISS, wx.NORMAL, wx.BOLD,
              False, 'Tahoma'))
        
        self.dxText = wx.TextCtrl(panel, -1, "等待数据...", size=(self.dxywidth, -1),style=wx.TE_READONLY)
        self.dxText.SetForegroundColour("red")
        self.dxText.SetBackgroundColour("yellow")
        font = wx.Font(self.dxysize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.dxText.SetFont(font)
        
        dyLabel = wx.StaticText(panel, -1, 'dy:',style=wx.TE_CENTER)
        dyLabel.SetFont(wx.Font(48, wx.SWISS, wx.NORMAL, wx.BOLD,
              False, 'Tahoma'))
        
        self.dyText = wx.TextCtrl(panel, -1, "等待数据...", size=(self.dxywidth, -1),style=wx.TE_READONLY)
        self.dyText.SetForegroundColour("red")
        self.dyText.SetBackgroundColour("yellow")
        font = wx.Font(self.dxysize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.dyText.SetFont(font)
        #bw = BlockWindow(self, label="span all columns")

        idlabel = wx.StaticText(panel, -1, 'ID:',style=wx.TE_CENTER)
        idlabel.SetFont(wx.Font(48, wx.SWISS, wx.NORMAL, wx.BOLD,
              False, 'Tahoma'))
        
        self.idText = wx.TextCtrl(panel, -1, "", size=(self.idwidth, -1),
                                  style=wx.TE_PROCESS_ENTER)
        self.idText.SetForegroundColour("red")
        self.idText.SetBackgroundColour("blue")
        self.idText.SetMaxLength(24)
        font = wx.Font(self.idsize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.idText.SetFont(font)
        
        fbox.AddMany([(dxLabel), (self.dxText),(dyLabel), (self.dyText), (idlabel),
                      (self.idText, 1, wx.EXPAND)])
        hbox.Add(fbox, 1, wx.ALL | wx.EXPAND, 15)
        panel.SetSizer(hbox)

        self.Bind(wx.EVT_TEXT_ENTER, self.onEnter,self.idText)
        self.idText.SetSelection(0,25)
        self.idText.SetFocus()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

        
    def onEnter(self, event):
        if self.startthread == 1:
            print "Old Thread Still Running"
            return 0
        else:
            print "Start New Thread"
            self.startthread = 1
        Tid = self.idText.GetValue()
        if len(Tid) < 2:
            self.showMessage('整机条码位数异常，请重新扫描！')
            self.idText.SetSelection(0,24)
            return 0
        self.tdata["sern"] = Tid
        Tvrecord(self.tdata)
        TvsetThread = threading.Thread(target = TvTuning, args = (), name = 'TvsetThread')
        TvsetThread.start()
        #Tvset = TvTuning()
        
    def OnExit(self, event):
        self.Close()

    def OnCloseWindow(self, event):
        print "exit"
        self.Destroy()

    
    def showMessage(self, msg):
        mdlg = wx.TextEntryDialog(None, msg, '异常！', '清除请输入$next')
        if mdlg.ShowModal() == wx.ID_OK:
            pass
        mdlg.Destroy()
        
    def reSetvalue(self,cdata):
        self.tdata = cdata
        self.dxText.SetValue(cdata["dx"])
        self.dyText.SetValue(cdata["dy"])
        self.dxText.SetBackgroundColour("green")
        self.dyText.SetBackgroundColour("green")
        #self.idText.SetSelection(0,24)


app = wx.PySimpleApp()
frame = MainWindow()
frame.Show()
Chromacomconf = {"port":"COM1", "baudrate":9600, "bytesize":8, "parity":"N", "stopbits":2}
ChromaCom = ComDev(Chromacomconf)
ChromaReadThread = threading.Thread(target = ChromaCom.ReadOnly, args = (), name = 'ChromaReadThread')
ChromaReadThread.start()
app.MainLoop()

ChromaCom.Close()
