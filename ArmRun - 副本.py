from ArmCtrl import XarmControl
import LeapAction
import threading
import time
from tkinter import *
class Application(Frame):
    def __init__(self, Xarm, master=None):
        Frame.__init__(self, master)
        self.Xarm = Xarm
        self.createWidgets()
        self.master = master
        
    def createWidgets(self):
        
        self.Frames = []
        for i in range(0,6):
            f = Frame(height = 400,width = 400, borderwidth = 10, relief = "ridge")
            servoInfo = self.Xarm.XArmInfo[i]
            Label(f,text = 'id:').grid(row=0,column=0)
            f.id = Label(f,text = servoInfo.id)
            f.id.grid(row=0,column=1)
            Label(f,text = 'pos:').grid(row=1,column=0)
            f.pos = Label(f,text = servoInfo.pos)
            f.pos.grid(row=1,column=1)
            Label(f,text = 'expectPos:').grid(row=2,column=0)
            f.expectPos = Label(f,text = servoInfo.expectPos)
            f.expectPos.grid(row=2,column=1)
            Label(f,text = 'msPer128Pos:').grid(row=3,column=0)
            f.msPer128Pos = Label(f,text = servoInfo.msPer128Pos)
            f.msPer128Pos.grid(row=3,column=1)
            Label(f,text = 'vin:').grid(row=4,column=0)
            f.vin = Label(f,text = servoInfo.vin)
            f.vin.grid(row=4,column=1)
            Label(f,text = 'temp:').grid(row=5,column=0)
            f.temp = Label(f,text = servoInfo.temp)
            f.temp.grid(row=5,column=1)
            f.grid(row=0,column=i)
            self.Frames.append(f)
            
    def update(self):
        for i in range(0,6):
            f = self.Frames[i]
            servoInfo = self.Xarm.XArmInfo[i]
            f.id.configure(text=servoInfo.id)
            f.pos.configure(text=servoInfo.pos)
            f.expectPos.configure(text=servoInfo.expectPos)
            f.msPer128Pos.configure(text=servoInfo.msPer128Pos)
            f.vin.configure(text=servoInfo.vin)
            f.temp.configure(text=servoInfo.temp)
            
        self.after(100, self.update)
        

def DataMix(Arm, Listener, controller):
    while True:
        Arm.SetAllPos(*Listener.dataQue[0])
        time.sleep(0.09)
    controller.remove_listener(listener)
    
Arm = XarmControl(broadcastPort = 3333, ControlPort = 3333)
Arm.Start()
Arm.PowerOff()
Arm.SetAllSpeed(128,128,128,128,128,128)
Arm.SetAllPos(600,600,600,600,-130,600)

root = Tk()
app = Application(Arm,root)
# 设置窗口标题:
app.master.title('Monitor')
app.after(100,app.update)#ms
app.mainloop()