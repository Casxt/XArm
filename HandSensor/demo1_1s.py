import threading

import time




import serial
import struct
import math
import socket

            

alfa=0
beta=90
def GetData():
    engine =[500,500,500]
    d = {
        "roll":0.0,
        "pitch":0.0,
        "yaw":0.0,
        }
    ser = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    ser.bind(('0.0.0.0',3332))
    print("Start")
    while(True):
        s = ser.recv(22)
        for s in (s[0:11],s[11:]):
            if(s[1:2] == b'\x53'):
                s = s[2:6]         
                r,p = struct.unpack('<hh', s)
                d["roll"]  = r/32768 * 180 
                d["pitch"]  = p/32768 * 180 
                cita3 =90-alfa-beta+d["pitch"]
                
                if(cita3<120 and cita3>-120):
                    engine[2]= round(500-4.15*cita3)
                elif(cita3<-120):
                    engine[2]=0
                else:
                    engine[2]=1000 
                        
                cita2= d["roll"]          
                if(cita2<90 and cita2>-90):
                    engine[1]= round(500+4.16*cita2)
                elif (cita2<-90):
                    engine[1]=125
                else:
                    engine[1]=875
                
            elif(s[1:2]== b'\x55'):    
                s = s[2:8]         
                D0,D1,D2 = struct.unpack('<hhh', s)
    #            print(D2)
                cita1= (D2-680)*1.65+10          
                if(cita1<500 and cita1>10):
                    engine[0]= cita1
                elif (cita1<10):
                    engine[0]=10
                else:
                    engine[0]=500
        
        print(engine)
        
        
#ta = threading.Thread(target=Draw)  
tb = threading.Thread(target=GetData)
tb.start()  
#ta.start()         
tb.join()