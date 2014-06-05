# -*- coding: gbk -*-

import wx
from VideoCapture import Device
import threading
import Image
import time
import shutil

Picdata = []
MAX_PIC_NUM = 5
SLEEP_TIME_LONG = 0.3
cam = Device(devnum=0, showVideoWindow=0)

def DealSnapshot():
    iNum = 0
    while True:
        picname = "data/" + str(iNum) + '.jpg'
        cam.saveSnapshot(picname, timestamp=3, boldfont=1, quality=100)
        Picdata.insert(0, picname)
        if len(Picdata) > 20:
            del Picdata[3:]
        time.sleep(SLEEP_TIME_LONG)
        if iNum == MAX_PIC_NUM:
            iNum = 0
        else:
            iNum += 1

def make_regalur_image(img, size = (256, 256)):
    return img.resize(size).convert('L')

def split_image(img, part_size = (64, 64)):
    w, h = img.size
    pw, ph = part_size
    assert w % pw == h % ph == 0
    return [img.crop((i, j, i+pw, j+ph)).copy()
            for i in xrange(0, w, pw) \
            for j in xrange(0, h, ph)]

def hist_similar(lh, rh):
    assert len(lh) == len(rh)
    return sum(1 - (0 if l == r else float(abs(l - r))/max(l, r)) for l, r in zip(lh, rh))/len(lh)

def calc_similar(li, ri):
    #	return hist_similar(li.histogram(), ri.histogram())
    return sum(hist_similar(l.histogram(), r.histogram()) for l, r in zip(split_image(li), split_image(ri))) / 16.0
			

def calc_similar_by_path(lf, rf):
    li, ri = make_regalur_image(Image.open(lf)), make_regalur_image(Image.open(rf))
    return calc_similar(li, ri)

def make_doc_data(lf, rf):
    li, ri = make_regalur_image(Image.open(lf)), make_regalur_image(Image.open(rf))
    #li.save(lf + '_regalur.png')
    #ri.save(rf + '_regalur.png')
    fd = open('stat.csv', 'w')
    fd.write('\n'.join(l + ',' + r for l, r in zip(map(str, li.histogram()), map(str, ri.histogram()))))
    #	print >>fd, '\n'
    #	fd.write(','.join(map(str, ri.histogram())))
    fd.close()

class MainWindow(wx.Frame):

    def __init__(self):        
        wx.Frame.__init__(self, None, -1, '对比工具 - PowerBy 青岛电子 新品转化平台 ', 
                          size=(950, 750), style=wx.DEFAULT_FRAME_STYLE)
        self.SetBackgroundColour('D4D0C8')
        self.statusbar = self.CreateStatusBar()
        self.statusbar.SetFieldsCount(2)
        self.statusbar.SetStatusWidths([-1, -1])
        self.statusbar.SetStatusText("型号: 平均亮度  最小亮度 平均能效", 0)
        self.statusbar.SetStatusText(" Power by 青岛电子新品 刘卫涛 liuweitao@haier.com ", 1)
        
        
        menuBar = wx.MenuBar()
        menu = wx.Menu()
        fexit = menu.Append(-1, "退  出")
        menuBar.Append(menu, "更改配置")
        menu = wx.Menu()
        starttest = menu.Append(-1, "开始测量")
        settest = menu.Append(-1, "设为样本")
        restart = menu.Append(-1, "重新测量(I)")
        menuBar.Append(menu, "检测控制")
        self.SetMenuBar(menuBar)
        #menuBar.Enable(ID_COST, 0)
        
        self.Bind(wx.EVT_MENU, self.OnSetTest, settest)
        
        #panel = wx.Panel(self, -1)
        
        hbox = wx.BoxSizer(wx.VERTICAL)
        f0box = wx.FlexGridSizer(1, 3, 10, 10)
        
        #-----------------  单 板 自 动 检 测 系 统  ------------------
        ltLabel = wx.StaticText(self, -1, '青 岛 电 子 监 控 工 具', style=wx.TE_CENTER)
        ltLabel.SetFont(wx.Font(36, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        
        #-----------------f0box-----------------------
        self.simer = wx.StaticText(self, -1, '99.00%', style=wx.TE_CENTER)
        self.simer.SetForegroundColour("blue")
        self.simer.SetFont(wx.Font(24, wx.SWISS, wx.NORMAL, wx.BOLD, False, 'Tahoma'))
        img1 = wx.Image("data/0.jpg", wx.BITMAP_TYPE_ANY)
        img2 = wx.Image("data/1.jpg", wx.BITMAP_TYPE_ANY)

        # turn them into static bitmap widgets
        self.disimg1 = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img1))
        self.disimg2 = wx.StaticBitmap(self, -1, wx.BitmapFromImage(img2))

        f0box.AddMany([(self.disimg1), (self.simer, 0, wx.ALIGN_CENTER), (self.disimg2)])
        hbox.Add(ltLabel, 0, wx.ALL | wx.EXPAND, 5)
        hbox.Add(f0box, 0, wx.ALIGN_CENTER, 5)
        self.SetSizer(hbox)

    def OnSetTest(self,event):
        shutil.copy(Picdata[0], "data/c.jpg")
        
    def onEnter(self, event):
        macnum = len(self.dmacs)
        
    def OnExit(self, event):
        self.Close()
    
    def showMessage(self, msg):
        mdlg = wx.TextEntryDialog(None, msg, '异常！', '清除请输入$next')
        if mdlg.ShowModal() == wx.ID_OK:
            pass
        mdlg.Destroy()
        
    def reSetvalue(self,value):
        self.disimg1.SetBitmap(wx.BitmapFromImage(wx.Image(Picdata[0])))
        self.disimg2.SetBitmap(wx.BitmapFromImage(wx.Image("data/k.jpg")))
        self.simer.SetLabel("%.2f%%" % value)

def DealPic():
    total = 0
    times = 0
    while 1:
        if len(Picdata) > 1:
            samier = calc_similar_by_path(Picdata[0], "data/k.jpg")*100
            if samier > 65:
                print ">>>>>>>>>>>>>>>OK<<<<<<<<<<<<<<<<<<"
                time.sleep(5)
            print time.strftime("%Y-%m-%d %X",time.localtime()),
            print 'Result: %.3f' % samier
            frame.reSetvalue(samier)
            #make_doc_data(Picdata[0], Picdata[1])
        time.sleep(SLEEP_TIME_LONG)

if __name__ == "__main__":
    app = wx.PySimpleApp()
    frame = MainWindow()
    frame.Show()
    Snapshotthread = threading.Thread(target = DealSnapshot, args = (), name = 'SNAPSHOT')
    DealPicthread = threading.Thread(target = DealPic, args = (), name = 'DealPic')
    Snapshotthread.setDaemon(True)
    DealPicthread.setDaemon(True)
    Snapshotthread.start()
    DealPicthread.start()
    app.MainLoop()

        