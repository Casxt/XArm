from ArmCtrl import XarmControl
import LeapAction
from  HandSensor import HandSensor
import threading
import time
from tkinter import *
import math
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
        
        f = Frame(height = 400,width = 400, borderwidth = 10, relief = "ridge")
        #f = Frame(height = 400,width = 400, borderwidth = 10, relief = "ridge")
        UnloadButton = Button(f, text='Unload', command=self.Xarm.PowerOff)
        UnloadButton.grid(row=1,column=1)
        LoadButton = Button(f, text='Load', command=self.Xarm.PowerOn)
        LoadButton.grid(row=1,column=2)
        f.grid(row=1)
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
        
def DataCheck(a, b, c):
    # a=Arm.XArmInfo[2].pos
    # b=Arm.XArmInfo[3].pos
    # c=Arm.XArmInfo[4].pos
    engine_31= (0.24*a-120)
    engine_41= (0.264*b-26.4)
    engine_51= (0.24*c-120)
    engine_3=engine_31*math.pi/180
    engine_4=engine_41*math.pi/180
    engine_5=engine_51*math.pi/180
    result=100*math.cos(engine_5)+100*math.cos(engine_5+engine_4)+155*math.cos(engine_5+engine_4-engine_3)+90
    
    if(result<0):
        return False
        print("3=",engine_31,"4=",engine_41,"5=",engine_51,"a=",a,"result=",result)
    else:
        return True
        
        
def DataMix(Arm, Listener, controller, HandSensor):
    while True:
        L = list()
        L.extend(HandSensor.dataQue[0])
        L.extend(Listener.dataQue[0][3:])
        print("SetPos:",L)
        #L = Listener.dataQue[0]
        if DataCheck(*L[2:5]) is True:
            Arm.SetAllPos(*L)
        time.sleep(0.06)
    controller.remove_listener(listener)
    
Arm = XarmControl(broadcastPort = 3333, ControlPort = 3333)
Arm.Start()
Arm.PowerOn()
Arm.SetAllSpeed(128,64,64,64,128,64)
Listener, controller = LeapAction.start()

Hand = HandSensor(Listener)
Hand.start()

DataMixThread = threading.Thread(target=DataMix,args=(Arm, Listener, controller, Hand))
DataMixThread.setDaemon(True)
DataMixThread.start()

root = Tk()
app = Application(Arm,root)
# 设置窗口标题:
app.master.title('Monitor')
app.after(100,app.update)#ms
app.mainloop()