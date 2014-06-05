# -*- coding: gbk -*-

import os, sys
import subprocess
import socket
import time

PWD = os.path.dirname(os.path.abspath(sys.argv[0]))
Checktimes = 1
lastmech = ""

def Ip2Mac(remoteinfo):
    '''Trs MAC to Ip.
    
    To trs between mac and ip'''
    cmd = "ping %s -n 2" % remoteinfo
    subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    pi = subprocess.Popen("arp -a", shell=True, stdout=subprocess.PIPE)
    output, errors = pi.communicate()
    del errors
    if output is not None :
        arpitems = output.split("\n")
        for i in arpitems:
            if remoteinfo in i:
                return i.split()[1]
    return "00-00-00-00-00-00"
def TvNicCheck(remoteinfo, cmethod = "ping"):
    '''Check the NIC.
    
    Use different protocal to check NIC'''
    global Checktimes
    if cmethod == "ping":
        cmd = "ping %s -n 2" % remoteinfo
    elif cmethod == "telnet":
        pass
    else:
        pass
    pi = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    output, errors = pi.communicate()
    del errors
    if output is not None :
        item = output.split("\n")
        print item[7][23:35]
        checkresult = int(item[7][34:35])
        ttime = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
        if checkresult > 1:
            print "*****************************************"
            print "*****************************************"
            print "***            检测成功 %i 次" % Checktimes
            print "***        共检测 2 次,成功 %d 次" % checkresult 
            print "***      检测时间:%s" % ttime
            print "*****************************************"
            print "*****************************************"
            Checktimes += 1
        else:
            print "*****************************************"
            print "*****************************************"
            print "***             检测失败！"
            print "***         检测时间:%s" % ttime
            print "*****************************************"
            print "*****************************************"

def deb(msg):
    '''Debug SQL.
    
    To log all sql in a inc file.'''
    tvdb = open(os.path.join(PWD, "debug.inc"), "a")
    tvdb.write(msg + "\n")
    tvdb.close()

def DealInfo(rip):
    '''Deal the main function.
    
    To deal the mac stuf.'''
    global lastmech
    rmac = Ip2Mac(rip)
    if rmac == lastmech:
        return 200
    else:
        lastmech = rmac
        print "------------------------------------------------"
        print "**New TV Find %s=>%s**" % (rmac, rip)
        print "Checking ...... "
        TvNicCheck(rip)
        print "------------------------------------------------"
        return 200
  

class DNSQuery:
    '''Respinse The DNS request.
    
    To org the date back'''
    def __init__(self, rdata):
        self.data = rdata
        self.dominio = ''
        
        tipo = (ord(data[2]) >> 3) & 15   # Opcode bits
        if tipo == 0:                     # Standard query
            ini = 12
            lon = ord(data[ini])
            while lon != 0:
                self.dominio += data[ini+1:ini+lon+1] + '.'
                ini += lon + 1
                lon = ord(data[ini])
    
    def respuesta(self, rip):
        '''Creat the dns response.
        
        Creat the response strings.'''
        packet = ''
        if self.dominio:
            packet += self.data[:2] + "\x81\x80"
            packet += self.data[4:6] + self.data[4:6] + '\x00\x00\x00\x00'   # Questions and Answers Counts
            packet += self.data[12:]                                         # Original Domain Name Question
            packet += '\xc0\x0c'                                             # Pointer to domain name
            packet += '\x00\x01\x00\x01\x00\x00\x00\x3c\x00\x04'             # Response type, ttl and resource data length -> 4 bytes
            packet += str.join('', map(lambda x: chr(int(x)), rip.split('.'))) # 4bytes of IP
        return packet

if __name__ == '__main__':
    ip = "192.168.200.10"
    addr = ()
    print 'iNc  Network Check Tool - liuwt123@gmail.com'
  
    udps = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udps.bind(('', 53))
  
    try:
        while 1:
            try:
                data, addr = udps.recvfrom(1024)
                print addr
                p = DNSQuery(data)
                udps.sendto(p.respuesta(ip), addr)
            except socket.error:
                print "SocketError Here!"
            if addr[0] <> ip:
                DealInfo(addr[0])
    except KeyboardInterrupt:
        print 'Finalizando'
        udps.close()