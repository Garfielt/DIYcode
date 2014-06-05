# -*- coding: gbk -*-
"""
Created on Thu Aug 25 10:06:41 2011

@author: 01188416
"""
import os, sys
import wx
import wx.grid
import serial
import struct
import threading
import time
import sqlite3, locale, types
from VideoCapture import Device
import Image
import wx.gizmos
import urllib2
import json
import shutil

Picdata = []
MAX_PIC_NUM = 5
SLEEP_TIME_LONG = 0.5
IMG_SIZE = {"w":96, "h":72}
cam = Device(devnum=0, showVideoWindow=0)

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

class NetLocdFrame(wx.Frame):
    def __init__(self):
        self.data = {}
        AcRe = urllib2.Request(r'http://192.168.79.188/tvs/json.php?t=%i' % time.time())
        data = json.loads(urllib2.urlopen(AcRe).read())
        wx.Frame.__init__(self, None, title="TreeListCtrl", size=(510,500))

        # Create an image list
        il = wx.ImageList(16,16)
		
        # Get some standard images from the art provider and add them
        # to the image list
        self.fldridx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FOLDER, wx.ART_OTHER, (16,16)))
        self.fldropenidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN,   wx.ART_OTHER, (16,16)))
        self.fileidx = il.Add(
            wx.ArtProvider.GetBitmap(wx.ART_NORMAL_FILE, wx.ART_OTHER, (16,16)))

        # Create the tree
        self.tree = wx.gizmos.TreeListCtrl(self, style = wx.TR_DEFAULT_STYLE | wx.TR_FULL_ROW_HIGHLIGHT)

        # Give it the image list
        self.tree.AssignImageList(il)


        # create some columns
        self.tree.AddColumn("测试型号")
        self.tree.AddColumn("TID")
        self.tree.AddColumn("备注")
        self.tree.SetMainColumn(0) # the one with the tree in it...
        self.tree.SetColumnWidth(0, 180)
        self.tree.SetColumnWidth(1, 40)
        self.tree.SetColumnWidth(2, 280)
        

        # Add a root node and assign it some images
        root = self.tree.AddRoot("测试型号")
        self.tree.SetItemText(root, "", 1)
        self.tree.SetItemText(root, "型号备注", 2)
        self.tree.SetItemImage(root, self.fldridx,
                               wx.TreeItemIcon_Normal)
        
        # Add nodes from our data set
        self.AddTreeNodes(root, data)

        # Bind some interesting events
        self.Bind(wx.EVT_TREE_ITEM_EXPANDED, self.OnItemExpanded, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_COLLAPSED, self.OnItemCollapsed, self.tree)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.OnSelChanged, self.tree)
        self.Bind(wx.EVT_TREE_ITEM_ACTIVATED, self.OnActivated, self.tree)

        # Expand the first level
        self.tree.Expand(root)
        

    def AddTreeNodes(self, parentItem, items):
        """
        Recursively traverses the data structure, adding tree nodes to
        match it.
        """
        for item, sitems in items.items():
            newItem = self.tree.AppendItem(parentItem, item)
            self.tree.SetItemText(newItem, "", 1)
            self.tree.SetItemText(newItem, "%s系列型号" % item, 2)
            self.tree.SetItemImage(newItem, self.fldridx,wx.TreeItemIcon_Normal)
            for xh, xhitems in sitems.items():
                childItem = self.tree.AppendItem(newItem, xh)
                self.tree.SetItemText(childItem, "%d" % int(xhitems["id"]), 1)
                self.tree.SetItemText(childItem, "%s" % xhitems["des"], 2)
                self.tree.SetItemImage(childItem, self.fileidx,wx.TreeItemIcon_Normal)
                

    def GetItemText(self, item):
        if item:
            return self.tree.GetItemText(item)
        else:
            return ""
        
    def OnItemExpanded(self, evt):
        print "OnItemExpanded: ", self.GetItemText(evt.GetItem())
        
    def OnItemCollapsed(self, evt):
        print "OnItemCollapsed:", self.GetItemText(evt.GetItem())

    def OnSelChanged(self, evt):
        print "OnSelChanged:   ", self.GetItemText(evt.GetItem())

    def OnActivated(self, evt):
        isEx = self.tree.ItemHasChildren(evt.GetItem())
        if isEx:
            print "Root Nodes"
            return 0
        frame.netconfid = self.tree.GetItemText(evt.GetItem(),1)
        frame.testxh = self.tree.GetItemText(evt.GetItem())
        print "Fetch Url:http://URL/tvtest.php?xh=" + self.GetItemText(evt.GetItem())
        frame.NetConf()
        self.Close()

class TvTest:
    def __init__(self):
        self.Tvcomconf = {"port":frame.comport, "baudrate":115200, "bytesize":8, "parity":"N", "stopbits":1}
        self.TVcom = ComDev(self.Tvcomconf)
        self.Results = ["Verify Error!", "Execute OK!", "Execute Error!"]

        self.factoryoff = 1
        print "Try Turn Factory On!"
        while self.factoryoff:
            scmd = [0xc9, 0x3c, 0x00, 0x00, 0x00, 0xD0]
            Exresult = self.ExcuteCmd(scmd)
            print self.Results[Exresult]
            if Exresult == 1:
                self.factoryoff = 0
        exrow = 0
        for line in frame.testconf:
            frame.ChangeStat(exrow)
            exnotok = 1
            print line
            scmd = TvCmds[line[0]]
            while exnotok:
                Exresult = self.ExcuteCmd(scmd)
                print self.Results[Exresult]
                if Exresult == 1:
                    exnotok = 0
                time.sleep(1)
            waittime = int(line[1])
            while waittime > 0:
                time.sleep(1)
                if frame.runnext == 1:
                    frame.runnext = 0
                    break
                waittime = waittime - 1
            exrow = exrow + 1
        self.cclose()
        frame.startthread = 0
        frame.Disnum()
        print "Thread End!"
    def ExcuteCmd(self, Cmd):
        while 1:
            print "Sending:",
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
                    return 1
                elif resCmd[-12:] == "c95b000005d0":
                    print ""
                    return 0
                else:
                    print ""
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
    Creattable = 1
    if os.path.isfile(Sqldb):
        Creattable = 0
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

TvCmds = {}
mfile = open('cmd.txt', 'r')
for line in mfile.readlines():
    line = line.replace("\n", "")
    nline = line.split()
    if len(nline)>0:
        temcmd = [0x9c, 0x38, 0, 0, 0, 0xd0]
        ncmd = nline[1:]
        for i in range(0,len(ncmd)):
            temcmd[i] = int(ncmd[i],16)
        temcmd[4] = numOfOne(temcmd[1]) + numOfOne(temcmd[2]) + numOfOne(temcmd[3])
        TvCmds[nline[0]] = temcmd
mfile.close()

def DealSnapshot():
    iNum = 0
    while True:
        picname = "data/" + str(iNum) + '.jpg'
        cam.saveSnapshot(picname, timestamp=3, boldfont=1, quality=100)
        Picdata.insert(0, picname)
        if len(Picdata) > 20:
            del Picdata[3:]
        frame.reSetvalue()
        time.sleep(SLEEP_TIME_LONG)
        if iNum == MAX_PIC_NUM:
            iNum = 0
        else:
            iNum += 1

class MainWindow(wx.Frame):

    def __init__(self):
        self.mainsize = 40
        self.fssize = 28
        self.twidth = 750
        self.totalnum = 0
        self.startthread = 0
        self.conffile = "Tvtest.txt"
        self.testconf = []
        self.testxh = ""
        self.netconfid = 0
        self.keepalive = 1
        self.runnext = 0
        self.runstep = 0
        self.comport = "COM1"
        self.disimg = {}
        
        wx.Frame.__init__(self, None, -1, '单板检测系统 - PowerBy 新品转化平台', 
                size=(960, 750))
        self.SetBackgroundColour('D4D0C8')
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(1)
        self.statusbar.SetStatusWidths([-1])
        self.statusbar.SetStatusText("Power by 新品转化平台", 0)
        
        menu0 = wx.Menu()
        loadlocalconf = menu0.Append(-1, "加载本地配置")
        loadnetconf = menu0.Append(-1, "加载网络配置")
        comset = menu0.Append(-1, "更改配置")
        settest = menu0.Append(-1, "设为样本")
        menu0.AppendSeparator()
        fexit = menu0.Append(-1, "退  出")
        menu1 = wx.Menu()
        starttest = menu1.Append(-1, "开始检测")
        pausetest = menu1.Append(-1, "暂停检测")
        nexttest = menu1.Append(-1, "下一步")
        menuBar = wx.MenuBar()
        menuBar.Append(menu0, "加载配置")
        menuBar.Append(menu1, "检测控制")
        self.SetMenuBar(menuBar)
        self.Bind(wx.EVT_MENU, self.OnExit, fexit)
        self.Bind(wx.EVT_MENU, self.OnLoadLocalConf, loadlocalconf)
        self.Bind(wx.EVT_MENU, self.OnLoadNetConf, loadnetconf)
        self.Bind(wx.EVT_MENU, self.onEnter, starttest)
        self.Bind(wx.EVT_MENU, self.OnPause, pausetest)
        self.Bind(wx.EVT_MENU, self.OnNext, nexttest)
        self.Bind(wx.EVT_MENU, self.OnSetPic, settest)
        self.Bind(wx.EVT_MENU, self.OnSetCom, comset)
        
        #panel = wx.Panel(self, -1)
        
        hbox = wx.BoxSizer(wx.VERTICAL)
        f1box = wx.GridSizer(1, 3, 5, 5)
        f2box = wx.FlexGridSizer(1, 4, 5, 5)
        f3box = wx.FlexGridSizer(1, 9, 10, 10)
        
        #-----------------  单 板 自 动 检 测 系 统  ------------------
        ltLabel = wx.StaticText(self, -1, '单 板 自 动 检 测 系 统',style=wx.TE_CENTER)
        ltLabel.SetFont(wx.Font(36, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        #-----------------  单 板 自 动 检 测 系 统  ------------------
        
        #---------------------  检测控制  ------------------
        self.start = wx.Button(self, label="开始检测(S)", size=(150, 50))
        self.pause = wx.Button(self, label="暂停(P)", size=(150, 50))
        self.next = wx.Button(self, label="下一步(N)", size=(150, 50))
        self.start.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        self.pause.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        self.next.SetFont(wx.Font(20, wx.SWISS, wx.NORMAL, wx.BOLD, False))
        f1box.AddMany([(self.start, 1, wx.EXPAND), (self.pause, 1, wx.EXPAND), 
                       (self.next, 1, wx.EXPAND)])
        
        #---------------------  检测控制  ------------------
        l21label = wx.StaticText(self, -1, '型号:',style=wx.TE_CENTER)
        l21label.SetFont(wx.Font(28, wx.SWISS, wx.NORMAL, wx.BOLD,
              False, 'Tahoma'))

        self.l21Text = wx.StaticText(self, -1, '000000000000000000000')
        self.l21Text.SetForegroundColour("red")
        font = wx.Font(self.fssize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.l21Text.SetFont(font)
        
        l22label = wx.StaticText(self, -1, '检测数量:',style=wx.TE_CENTER)
        l22label.SetFont(wx.Font(28, wx.SWISS, wx.NORMAL, wx.BOLD,
              False, 'Tahoma'))

        self.l22Text = wx.StaticText(self, -1, '0000')
        self.l22Text.SetForegroundColour("red")
        font = wx.Font(self.fssize, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        self.l22Text.SetFont(font)
        f2box.AddMany([(l21label), (self.l21Text, 1, wx.EXPAND),\
                       (l22label), (self.l22Text, 1, wx.EXPAND)])
        #---------------------  检测控制  ------------------
        
        #---------------------  示例窗口  ------------------
        subdis = wx.StaticText(self, -1, '工序', style=wx.TE_CENTER)
        subdis.SetForegroundColour("blue")
        subdis.SetFont(wx.Font(18, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        diswin= wx.Image("0.jpg", wx.BITMAP_TYPE_ANY).Scale(IMG_SIZE["w"], IMG_SIZE["h"])
        img1 = wx.Image("0.jpg", wx.BITMAP_TYPE_ANY).Scale(IMG_SIZE["w"], IMG_SIZE["h"])
        self.disimg[0] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(diswin))
        self.disimg[1] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[2] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[3] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[4] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[5] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[6] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg[7] = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        f3box.AddMany([(self.disimg[0]), (subdis, 0, wx.ALIGN_CENTER), (self.disimg[1]),
                       (self.disimg[2]), (self.disimg[3]), (self.disimg[4]), (self.disimg[5]),\
                       (self.disimg[6]),(self.disimg[7])])
        #---------------------  示例窗口  ------------------
        
        hbox.Add(ltLabel, 0, wx.ALL | wx.EXPAND, 10)        
        hbox.Add(f1box, 0, wx.ALL | wx.EXPAND, 10)
        hbox.Add(f2box, 0, wx.ALIGN_CENTER, 10)
        hbox.Add(f3box, 0, wx.ALIGN_CENTER, 10)
        
        self.colLabels = ["功能码", "时间", "检测说明", "重点项目"]

        
        self.grid = wx.grid.Grid(self)
        self.grid.CreateGrid(1,4)
        
        self.grid.EnableEditing(False)
        self.grid.SetLabelFont(wx.Font(16, wx.SWISS, wx.NORMAL, wx.BOLD))
        
        
        for row in range(0, 4):
            self.grid.SetColLabelValue(row, self.colLabels[row])
         
        #self.grid.SetDefaultColSize(100)
        #self.grid.SetDefaultRowSize(36)
        #self.grid.SetColSize(1, 200)
        self.grid.SetDefaultCellFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
        self.grid.SetDefaultCellAlignment(wx.ALIGN_CENTRE, wx.ALIGN_CENTRE)
        self.grid.SetRowSize(0, 30)
        self.grid.AutoSizeColumns(True)
        
        #self.grid.SetRowSize(1, 100)
        self.grid.SetColSize(0, 120)
        self.grid.SetColSize(1, 60)
        self.grid.SetColSize(2, 400)
        self.grid.SetColSize(3, 260)
        
        hbox.Add(self.grid, 1, wx.ALL | wx.EXPAND, 15)
        self.SetSizer(hbox)


        self.Bind(wx.EVT_BUTTON, self.onEnter, self.start)
        #self.Bind(wx.EVT_KEY_UP, self.OnKeyUp)
        #wx.EVT_KEY_UP(self, self.OnKeyUp)
        #self.Bind(wx.EVT_CHAR, self.OnKeyUp)
        acceltbl = wx.AcceleratorTable([(wx.ACCEL_NORMAL, ord('S'), starttest.GetId()),\
                                        (wx.ACCEL_NORMAL, ord('P'), pausetest.GetId()),\
                                        (wx.ACCEL_NORMAL, ord('N'), nexttest.GetId()),\
                                        (wx.ACCEL_NORMAL, 32, starttest.GetId()),
                                        (wx.ACCEL_NORMAL, ord('W'), loadnetconf.GetId())])
        self.SetAcceleratorTable(acceltbl)
        
    def Init(self):
        try:
            mfile = open('Tvtest.conf', 'r')
            self.conf = json.loads(mfile.read())
            mfile.close()
            print self.conf
        except:
            print "Local Config Not Found!"
    
    def BackConf(self):
        mfile = open('Tvtest.conf', 'w')
        mfile.write(json.dumps(self.conf))
        mfile.close()

    def onEnter(self,event):
        if self.startthread == 1:
            print "Old Thread Still Running"
            return 0
        else:
            print "Start New Thread"
            self.startthread = 1
        for r in range(0,len(self.testconf)):
            self.grid.SetCellBackgroundColour(r, 2, "yellow")
        tline = 0
        for tc in self.testconf:
            self.grid.SetCellValue(tline, 1, tc[1])
            tline = tline + 1
        #TvtestThread = None
        TvtestThread = threading.Thread(target = TvTest, args = (), name = 'TvtestThread')
        TvtestThread.start()
        #ds = json.loads(resp.read())
        #print ds['statue']

    def Disnum(self):
        self.totalnum = self.totalnum + 1
        self.l22Text.SetLabel(str(self.totalnum))
        
    def showMessage(self, msg):
        mdlg = wx.TextEntryDialog(None, msg, '异常！', '清除请输入$next')
        if mdlg.ShowModal() == wx.ID_OK:
            pass
        mdlg.Destroy()
    
    def OnSetCom(self, event):
        dlg = wx.TextEntryDialog(None, "配置检测用串口", '串口配置',self.comport[3:])
        if dlg.ShowModal() == wx.ID_OK:
            self.comport = "COM%s" % dlg.GetValue()
        dlg.Destroy()
        
    def OnExit(self, event):
        self.Close()
    
    def OnPause(self,event):
        if self.keepalive == 1:
            self.keepalive = 0
        else:
            self.keepalive = 1
        print "Set Keepalive = " + str(self.keepalive)
        
    def OnNext(self, event):
        self.runnext = 1

    def OnLoadLocalConf(self, event):
        wildcard = "Tvtest Config(*.txt)|*.txt|" "All files (*.*)|*.*"
        dialog = wx.FileDialog(None, "请选择配置文件", os.getcwd(), "", wildcard, wx.OPEN)
        if dialog.ShowModal() == wx.ID_OK:
            self.conffile = dialog.GetPath()
            print self.conffile
            mfile = open(self.conffile, 'r')
            tdata = mfile.read() 
            mfile.close()
            self.testxh = os.path.basename(self.conffile)[0:-4]
            print self.testxh
            self.DoConf(tdata)

    def DoConf(self, tdata):
        rownum = self.grid.GetNumberRows()
        print rownum
        if rownum > 1:
            print "Reload the Progream"
            self.grid.DeleteRows(0, (rownum-1))
        self.testconf = []
        mconf = tdata.split("\n")
        for line in mconf:
            #line = line.replace("\n", "")
            nline = line.split(",")
            print nline,len(nline)
            if len(nline)>1:
                self.testconf.append(nline)
        
        print self.testconf
        doadd = 0
        for tc in self.testconf:
            if doadd:
                self.grid.InsertRows(doadd, 1)
            for n in range(0,len(tc)):
                self.grid.SetCellValue(doadd, n, tc[n])
            self.grid.SetRowSize(doadd, 30)
            doadd = doadd + 1
        self.l21Text.SetLabel(self.testxh)
            
    def OnLoadNetConf(self, event):
        self.NetLoad = NetLocdFrame()
        self.NetLoad.Show(True)
        
    def NetConf(self):
        print self.netconfid
        AcRe = urllib2.Request(r'http://192.168.79.188/tvs/LE42H300.php?t=%i' % time.time())
        tdata = urllib2.urlopen(AcRe).read()
        self.DoConf(tdata)
        
    def ChangeStat(self, row):
        self.runstep = row
        print "New" + str(row)
        if row<0:
            self.grid.SetCellBackgroundColour((row-1), 2, "red")
        #self.grid.SetAttr(row, 2, self.attrnew)
        self.grid.SetCellBackgroundColour(row, 2, "green")
        #print "Set Attr Error Here!"
        onerow = self.testconf[row]
        for n in range(0,len(onerow)):
            self.grid.SetCellValue(row, n, onerow[n])
        
    def OnKeyUp(self, event): 
        if event.GetKeyCode() == 13:
            print "Enter key was down" 
        else: 
            print "Other key was down"
        event.Skip() 

    def OnSetPic(self,event):
        if 1:
            cimg = "data/c-%d.jpg" % self.runstep
            print cimg
            shutil.copy(Picdata[0], cimg)
            self.disimg[self.runstep].SetBitmap(wx.BitmapFromImage(wx.Image(cimg).Scale(IMG_SIZE["w"], IMG_SIZE["h"])))

    def reSetvalue(self):
        self.disimg[0].SetBitmap(wx.BitmapFromImage(wx.Image(Picdata[0]).Scale(IMG_SIZE["w"], IMG_SIZE["h"])))
        
    def deb(self,msg):
        detxt = open("frame.inc", "a")
        detxt.write(msg + "\n")
        detxt.close()

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MainWindow()
    frame.Show()
    Snapshotthread = threading.Thread(target = DealSnapshot, args = (), name = 'SNAPSHOT')
    Snapshotthread.setDaemon(True)
    Snapshotthread.start()
    app.MainLoop()
