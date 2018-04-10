import threading
import struct
import socket
import collections
import math
class HandSensor(object):
    def __init__(self, LeapAction):
        self.dataQue = collections.deque()
        self.dataQue.extend([[500,500,700], [500,500,700], [500,500,700], [500,500,700], [500,500,700], [500,500,700]])
        self.LeapAction = LeapAction

    
    def GetData(self):
        ser = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        ser.bind(('0.0.0.0',3332))
        print("Start")
        engine_3 = 500
        engine_2 = 500
        engine_1 = 500
        while(True):
            s = ser.recv(22)
            for s in (s[:11],s[11:]):
                if(s[1:2] == b'\x53'):
                    s = s[2:6]         
                    r,p = struct.unpack('<hh', s)
                    roll  = r/32768 * 180 
                    pitch  = p/32768 * 180 
                    cita3 =90-self.LeapAction.alfa-self.LeapAction.beta+pitch
                    #cita3 =90+80-100+pitch
                    if(cita3<120 and cita3>-120):
                        engine_3= round(500-4.15*cita3)
                    elif(cita3<-120):
                        engine_3=1000
                    else:
                        engine_3=0 
                            
                    cita2= roll  
                    if(cita2<90 and cita2>-90):
                        engine_2= round(500+4.16*cita2)
                    elif (cita2<-90):
                        engine_2=125
                    else:
                        engine_2=875
                        
                elif(s[1:2]== b'\x55'):    
                    s = s[2:8]
                    D0,D1,D2 = struct.unpack('<hhh', s)
                    #print(D0,D1,D2)
                    crawl = D2
                    #print("crawl",crawl)
                    cita1= (crawl-800)*1.63+10
                    #cita1= (crawl-1200)*1.5+10    
                    #print("cita1",cita1)
                    if(cita1<500 and cita1>10):
                        engine_1= cita1
                    elif (cita1<10):
                        engine_1=10
                    else:
                        engine_1=500
                    engine_1 = round(engine_1)
            self.putData(engine_1,engine_2,engine_3)
                
    def putData(self,a1,a2,a3):
        newData = [a1,a2,a3]
        #lastData = self.dataQue[0]
        #for i in range(0,3):
        #    newData[i] = int(0.70*newData[i] + 0.20*self.dataQue[0][i] + 0.10*self.dataQue[1][i])
                
        self.dataQue.appendleft(newData)
        self.dataQue.pop()
        
    def start(self): 
        tb = threading.Thread(target=self.GetData)
        tb.setDaemon(True)
        tb.start()  
