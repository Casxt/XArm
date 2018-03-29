################################################################################
# Copyright (C) 2012-2016 Leap Motion, Inc. All rights reserved.               #
# Leap Motion proprietary and confidential. Not for distribution.              #
# Use subject to the terms of the Leap Motion SDK Agreement available at       #
# https://developer.leapmotion.com/sdk_agreement, or another agreement         #
# between Leap Motion and you, your company or other organization.             #
################################################################################
import threading as thread
import os, sys, inspect, time
import collections
#sys.path.insert(0, r"C:\Users\zhang\Desktop\LeapDeveloperKit_3.2.1_win\LeapDeveloperKit_3.2.1+45911_win\LeapSDK2\samples")

from ArmCtrl import XarmControl
import Leap
import math
import numpy as np

class SampleListener(Leap.Listener):
    
    def init(self):
        pass
    def on_init(self, controller,defaultPos = (500,500,700,600,200,500)):
        self.BasicInfo = {
        "HandId":0,
        "HandType":0,
        "HandPosition":(0,0,0),
        "Pitch":0,
        "Roll":0,
        "Yaw":0,
        "ArmDirection":0,
        "WristPosition":0,
        "ElbowPosition":0
        }
                        #拇指      食指     中指     无名指   小指
        self.finger_names = ['Thumb', 'Index', 'Middle', 'Ring', 'Pinky']
                        #近心端          ？         ？            远心端
        self.bone_names = ['Metacarpal', 'Proximal', 'Intermediate', 'Distal']
        
        self.dataQue = collections.deque()
        self.dataQue.extend([defaultPos,defaultPos,defaultPos,defaultPos,defaultPos,defaultPos])
        
        self.alfa = 0
        self.beta = 0
        
        controller.enable_gesture(Leap.Gesture.TYPE_KEY_TAP)
        controller.enable_gesture(Leap.Gesture.TYPE_SCREEN_TAP)
        controller.config.set("Gesture.ScreenTap.MinForwardVelocity", 30.0)
        controller.config.set("Gesture.ScreenTap.HistorySeconds", .5)
        controller.config.set("Gesture.ScreenTap.MinDistance", 1.0)
        controller.config.save()
        print ("Initialized")
        
    def CovToServoAngel(self,x,y,z):
        a=0
        b=100
        c=-30

        x = x*3/5                       #左右归一化
        y = y                           #高低归一化
        z = -z*3/5                      #前后归一化
        if (z<-30):
            z=-30

        x1 = math.sqrt((z-c)**2+x**2)   #计算俯视平面投影
        h=y-b                           #搬移y轴（高低）
        AC=math.sqrt((h-140)**2+x1**2)   #3号舵机与5号舵机距离
        #print("x1",x1,"h",h,"AC",AC)
        if x1**2+(h-140)**2>= 40000:
            beta=0
            alfa=math.pi/2-math.atan((h-140)/x1)

        else:
            
            beta=2*math.acos(AC/200)
            alfa=math.pi/2-math.atan((h-140)/x1)-math.acos(AC/200)
            
        gama=-math.atan(x*16/9/(z+70))/2                                 #存疑
        alfa_d=alfa*180/math.pi
        beta_d=beta*180/math.pi
        gama_d=gama*180/math.pi
        #print(alfa_d,beta_d,gama_d)
        s4 = round(beta*750/math.pi)+100
        s5 = round(alfa*750/math.pi)+500
        s6 = round(gama*750/math.pi)+500
        #s6 = round(-x*1+500)                                         #s6采用什么方式呢
        if (s6 > 1000):
            s6 = 1000
        elif s6<0:
            s6=0
        if (s5 > 1000 ):
            s5 = 1000
        elif (s5 < 0 ):
            s5 = 0
        if (s4 > 1000 ):
            s4 = 1000
        elif (s4 < 0 ):
            s4 = 0
        
        return s6,s5,s4,alfa,beta

    def CovToServoAngelold(self,x0,y0,z0):
        a=0
        b=100
        c=100
        x=-(x0-a)/1
        y=(y0-b)/1
        z=-(z0-c)/1
        h=(y0-b-82)/1
        #print("CovToServoAngel x,y,z",x,y,z)

        if z>0:
            x1 = math.sqrt((x)**2+(z)**2)
            if x1**2+(h)**2>= 40000:
                beta1=0
            else:
                beta1= math.acos((x1**2+(h)**2-20000)/20000)
                
            if h>=0:
                alfa1 = math.atan(x1/(h))-beta1/2
            else :
                alfa1 = math.atan(x1/(h))-beta1/2 + math.pi
        else:
            z = 1
            x1 = math.sqrt((x)**2+(z)**2)
            if x1**2+(h)**2>= 40000:
                beta1=0
            else:
                beta1= math.acos((x1**2+(h)**2-20000)/20000)
            if h>=0:
                alfa1 = math.atan(x1/(h))-beta1/2
            else :
               alfa1 = math.atan(x1/(h))-beta1/2 + math.pi


        gama1=math.atan(x/(z+70))
        alfa=180*alfa1/math.pi
        beta=180*beta1/math.pi
        s5 = round(alfa1*750/math.pi)+500
        s4 = round(beta1*750/math.pi)+125
        s6 = round(gama1*750/math.pi)+500
        s6 = round(x*1+500)
        if (s6 > 1000):
            s6 = 1000
        elif s6<0:
            s6=0
        #if (s5 > 1000 or s4 > 1000 or s5 < 0 or s4 < 0):
        if (s5 > 1000 ):
            s5_to_e3 = 1000
        if (s4 > 1000 ):
            s4_to_e3 = 1000
        if (s5 < 0 ):
            s5_to_e3 = 0
        if (s4 < 0 ):
            s4_to_e3 = 0

        return s6,s5,s4,alfa1,beta1


    def on_connect(self, controller):
        print ("Connected")

    def on_disconnect(self, controller):
        print ("Disconnected")

    def on_exit(self, controller):
        print ("Exited")

    def on_frame(self, controller):
        frame = controller.frame()

        for gesture in frame.gestures():
            if gesture.type is Leap.Gesture.TYPE_SCREEN_TAP:
                screen_tap = Leap.ScreenTapGesture(gesture)
                
        if not frame.hands.is_empty:
            hand = frame.hands[0]
            wp = hand.arm.wrist_position
           # print("wp",wp[0],wp[1],wp[2])
            s6,s5,s4,alfa,beta = self.CovToServoAngel(wp[0],wp[1],wp[2])

            self.alfa = 180*alfa/math.pi
            self.beta = 180*beta/math.pi
            
            a = []
            for finger in hand.fingers:
                for b in range(0, 4):
                    bone = finger.bone(b)
                a.append(finger)

            index_point=(a[1].bone(0).next_joint[0],a[1].bone(0).next_joint[1],a[1].bone(0).next_joint[2])
            pinky_point=(a[4].bone(0).next_joint[0],a[4].bone(0).next_joint[1],a[4].bone(0).next_joint[2])
         
            index_pinky=    (index_point[0]-pinky_point[0],
                            index_point[1]-pinky_point[1],
                            index_point[2]-pinky_point[2])   
                            
            vector=(index_pinky[0]/57,index_pinky[1]/57,index_pinky[2]/57)
            
            thumb_tip=(a[0].bone(3).next_joint[0]/10,a[0].bone(3).next_joint[1]/10,a[0].bone(3).next_joint[2]/10)
            index_tip=(a[1].bone(3).next_joint[0]/10,a[1].bone(3).next_joint[1]/10,a[1].bone(3).next_joint[2]/10)
            distance=math.pow((thumb_tip[0]-index_tip[0]),2)+math.pow((thumb_tip[1]-index_tip[1]),2)+math.pow((thumb_tip[1]-index_tip[1]),2)
            
            v_y =vector[1] 
            
            if vector[2]<0:                      #下降
                cita3=180-alfa-beta-90*vector[1]
            else:                            #上升
                cita3=(90*v_y)-alfa-beta
            
            if cita3<120 and cita3>-120:
                engine_3= round(500-4.15*cita3)
            elif(cita3<-120):
                engine_3=1000
            else:
                engine_3=0 

            
            if vector[1]>0:
                cita2=90*vector[0]
            else:
                cita2=-180-90*vector[0]
             
            if cita2<120 and cita2>-120:
                engine_2= round(500+4.15*cita2)
            elif cita2<-120:
                engine_2=1000
            else:
                engine_2=0         
            
            
            if distance<8:
                engine_1=10
            else:
                engine_1=500
                
            #print("cita3,cita2,alfa,beta:",cita3,cita2,alfa,beta)
            self.putData(engine_1,engine_2,engine_3,s4,s5,s6)
        else:

            self.putData(500,500,700,600,200,500)

    def putData(self,a1,a2,a3,a4,a5,a6):
        newData = [a1,a2,a3,a4,a5,a6]
        lastData = self.dataQue[0]
        for i in range(0,6):
            newData[i] = int(0.4*newData[i] + 0.25*self.dataQue[0][i] + 0.15*self.dataQue[1][i]
                                            + 0.10*self.dataQue[2][i] + 0.05*self.dataQue[3][i]
                                            + 0.05*self.dataQue[4][i])
                
        self.dataQue.appendleft(newData)
        self.dataQue.pop()
        
def start():
    # Create a sample listener and controller
    listener = SampleListener()
    controller = Leap.Controller()

    # Have the sample listener receive events from the controller
    controller.add_listener(listener)
    
    return listener, controller
    # # Keep this process running until Enter is pressed
    # print ("Press Enter to quit...")
    # try:
        # sys.stdin.readline()
    # except KeyboardInterrupt:
        # pass
    # finally:
        # # Remove the sample listener when done
        # controller.remove_listener(listener)