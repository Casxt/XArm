import socket
import sys
import struct
import threading
import time
from pprint import pprint
import os
import time


class ServoInfo(object):
    """保存舵机信息"""
    def __init__(self,id,msPer128Pos=5):
        self.id = id            #char
        self.pos = 0            #int
        self.expectPos = 0      #int
        self.msPer128Pos = msPer128Pos    #int usetime = (delt(pos)*msPer128Pos)/128
        self.vin = 0            #int
        self.temp = 0            #char
        
    def __str__(self):
        s = """id:{id}
pos:{pos}
expectPos:{expectPos}
msPer128Pos:{msPer128Pos} msPer128Pos
vin:{vin} V
temp:{temp}℃""".format(id = self.id,pos = self.pos,expectPos = self.expectPos,
                        msPer128Pos = self.msPer128Pos,vin = self.vin/1000,temp = self.temp)
        return s
    def GetIDByte(self):
        return struct.pack("<B",self.id)
        
    def GetExpectPosByte(self):
        return struct.pack("<H",self.expectPos)

    def GetSpeedByte(self):
        return struct.pack("<H",self.msPer128Pos)

    def GetExpectPosSpeedByte(self):
        return struct.pack("<HH",self.expectPos,self.msPer128Pos)

class XarmControl(object):
    """控制舵机"""
    def __init__(self, broadcastPort = 3333, ControlPort = 3333):
        """初始化"""
        self.XArmInfo = [ServoInfo(1),ServoInfo(2),ServoInfo(3),ServoInfo(4),ServoInfo(5),ServoInfo(6)]
        self.Client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.Client.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ip = '0.0.0.0'
        self.broadcastPort = broadcastPort
        self.ControlPort = ControlPort
        self.ServerIP = None
        self.serverMillis = 0
        self.header = b'\xff\x00\xff'
        self.ServoInfoThread = threading.Thread(target=self.GetBoardCastInfo)
        self.lock = threading.Lock()
        
        self.BoardCastServoInfo = 1
        self.SetAllServoPos = 2
        self.SetAllServoSpeed = 3
        self.SetAllServoPosSpeed = 4
        self.BoardCastAllServoPos = 5
        self.SendMsg = 6
        self.UnloadAllServo = 7
        self.LoadAllServo = 8
        self.ServerUnknowErr = 255
        
        self.PacketOnSending = 0
        self.MaxSendingPack = 5
        
        self.app = None
        
        
    def Start(self):
        self.FindServer(self.ip, self.broadcastPort)
        self.ServoInfoThread.setDaemon(True)
        self.ServoInfoThread.start()
        
    def FindServer(self,ip='0.0.0.0',broadcastPort=3333):
        """与服务器建立连接"""
        self.ip = ip
        self.broadcastPort = broadcastPort
        self.Client.bind((self.ip, self.broadcastPort))
        for i in range(0,300):
            Header,RemoteIPTuple = self.Client.recvfrom(256)
            if (len(Header) >= 7 and Header[0:3] == b'\xff\x00\xff'):
                self.serverMillis = struct.unpack('I', Header[3:7])[0]
                print("serverMillis",self.serverMillis)
                self.ServerIP = RemoteIPTuple[0]
                print("Server Ip Find:",self.ServerIP)
                return RemoteIPTuple[0]
        return None

    def UnpackHeader(self, Data, RemoteIPTuple):
        """解析头部信息"""
        if len(Data)>=10 and Data[0:3] == b'\xff\x00\xff' and RemoteIPTuple[0] == self.ServerIP:
            #self.lock.acquire()
            self.serverMillis = struct.unpack('<I', Data[3:7])[0] #同步全局要加锁?
            #清空发包计数
            self.PacketOnSending = 0 
            #self.lock.release()
            Mode = struct.unpack('<B', Data[7:8])[0]
            Length = struct.unpack('<H', Data[8:10])[0]
            return (Mode,Data[10:])
        elif RemoteIPTuple[0] == self.ServerIP:
            print("DropData:",Header,RemoteIPTuple)
            return (self.ServerUnknowErr,None)
            
    def UnpackBoardCastServoInfo(self, Data):
        for S in self.XArmInfo:
            try:
                id = struct.unpack('<B', Data[0:1])[0]
                if id == S.id :
                    #注意此处expectPos不读入
                    pos,msPer128Pos,vin,temp = struct.unpack('<HHHB', Data[1:8])
                    if(pos<=1000 and vin<=8500 and temp < 90):
                        S.pos,S.msPer128Pos,S.vin,S.temp = pos,msPer128Pos,vin,temp
                    else:
                        #print("Wrong Data:",pos,msPer128Pos,vin,temp)
                        #input()
                        #Wrong Data: 1109 2560 8006 85 （only id 4）
                        #Wrong Data: 63488 2560 63488 0
                        break
                else:
                    print("id:",id)
                    print("Data:",Data)
                Data = Data[8:]
            except Exception as e:
                pass
                
    def UnpackBoardCastServoPos(self, Data):
        for S in self.XArmInfo:
            try:
                id = struct.unpack('<B', Data[0:1])[0]
                if id == S.id :
                    #注意此处expectPos不读入
                    pos = struct.unpack('<H', Data[1:3])[0]
                    if(pos<=1000):
                        S.pos = pos
                    else:
                        #print("Wrong Data:",pos)
                        #input()
                        #Wrong Data: 1109 2560 8006 85 （only id 4）
                        #Wrong Data: 63488 2560 63488 0
                        break
                else:
                    print("id:",id)
                    print("Data:",Data)
                Data = Data[3:]
            except Exception as e:
                pass
                
    def GetBoardCastInfo(self):
        """获取服务器广播信息"""
        while True:
            try:
                Data, RemoteIPTuple = self.Client.recvfrom(256)
                Mode,Data = self.UnpackHeader(Data, RemoteIPTuple)
                if Mode == self.BoardCastServoInfo:
                    self.UnpackBoardCastServoInfo(Data)
                elif Mode == self.BoardCastAllServoPos:
                    self.UnpackBoardCastServoPos(Data)
                elif Mode == self.ServerUnknowErr:
                    print("ServerUnknowErr")
                    continue
                
                #for S in self.XArmInfo:
                #    print("ServoInfo:",S)
                
            except Exception as e:
                self.ServerIP = None
                ServerIP = self.FindServer(self.ip, self.broadcastPort)
                if ServerIP is None:
                    print("Server Lost")
                    raise("Server Lost")
        time.sleep(0.25)
        
    def GetHeader(self,Mode,Length):#Mode Length int
        """生成包头信息"""
        #发包计数
        self.PacketOnSending =  self.PacketOnSending + 1
        return self.header + struct.pack("<I",self.serverMillis) + struct.pack("<b",Mode) + struct.pack("<H",Length)
        
    def SetAllPos(self,*posList):
        """设置舵机角度"""
        if(self.PacketOnSending <= self.MaxSendingPack):
            #print("""设置舵机角度""")
            dataByte = b''
            for i in range(0,len(self.XArmInfo)):
                self.XArmInfo[i].expectPos = posList[i]
                dataByte = dataByte + self.XArmInfo[i].GetIDByte() + self.XArmInfo[i].GetExpectPosByte()
            Header = self.GetHeader(Mode = self.SetAllServoPos, Length = len(dataByte))
            #data = Header + dataByte
            self.Client.sendto(Header + dataByte, (self.ServerIP,self.ControlPort))
            return True
        else:
            #print("Waiting!")
            return False
        
    def SetAllSpeed(self,*speedList):
        """设置舵机转动速度"""
        if(self.PacketOnSending <= self.MaxSendingPack):
            print("""设置舵机转动速度""")
            dataByte = b''
            for i in range(0,len(self.XArmInfo)):
                self.XArmInfo[i].msPer128Pos = speedList[i]
                dataByte = dataByte + self.XArmInfo[i].GetIDByte() + self.XArmInfo[i].GetSpeedByte()
            Header = self.GetHeader(Mode = self.SetAllServoSpeed, Length = len(dataByte))
            #data = Header + dataByte
            self.Client.sendto(Header + dataByte, (self.ServerIP,self.ControlPort))
            return True
        else:
            print("Waiting!")
            return False
        
    def SetAllPosSpeed(self,*posSpeedList):
        """设置舵机角度速度"""
        if(self.PacketOnSending <= self.MaxSendingPack):
            #print("""设置舵机角度速度""")
            dataByte = b''
            for i in range(0,len(self.XArmInfo)):
                self.XArmInfo[i].expectPos = posSpeedList[i][0]
                self.XArmInfo[i].msPer128Pos = posSpeedList[i][1]
                dataByte = dataByte + self.XArmInfo[i].GetIDByte() + self.XArmInfo[i].GetExpectPosByte() + self.XArmInfo[i].GetSpeedByte()
                
            Header = self.GetHeader(Mode = self.SetAllServoPosSpeed, Length = len(dataByte))
            self.Client.sendto(Header + dataByte, (self.ServerIP,self.ControlPort))
            return True
        else:
            #print("Waiting!")
            return False
        
    def PowerOff(self):
        """设置舵机角度速度"""
        if(self.PacketOnSending <= self.MaxSendingPack):
            print("""舵机掉电""")
            dataByte = b''
            for i in range(0,len(self.XArmInfo)):
                dataByte = dataByte + self.XArmInfo[i].GetIDByte()
            Header = self.GetHeader(Mode = self.UnloadAllServo, Length = len(dataByte))
            self.Client.sendto(Header + dataByte, (self.ServerIP,self.ControlPort))
            return True
        else:
            print("Waiting!")
            return False
            
    def PowerOn(self):
        """设置舵机角度速度"""
        if(self.PacketOnSending <= self.MaxSendingPack):
            print("""舵机上电""")
            dataByte = b''
            for i in range(0,len(self.XArmInfo)):
                dataByte = dataByte + self.XArmInfo[i].GetIDByte()
                
            Header = self.GetHeader(Mode = self.LoadAllServo, Length = len(dataByte))
            self.Client.sendto(Header + dataByte, (self.ServerIP,self.ControlPort))
            return True
        else:
            print("Waiting!")
            return False