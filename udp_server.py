from ArmCtrl import XarmControl
import time
Arm = XarmControl(broadcastPort = 3333, ControlPort = 3333)
Arm.Start()


#Arm.SetAllPos(600,400,400,400,400,400)
#Arm.SetAllPosSpeed((500,20),(500,20),(500,20),(500,20),(500,20),(500,20))
#Arm.ServoInfoThread.join()
Arm.PowerOff()
Arm.SetAllSpeed(64,64,64,64,64,64)
Arm.SetAllPos(500,500,1000,500-0,500-0,500-0)
while(1):
    pass
    #Arm.PowerOff()
    
    #time.sleep(10)
    #Arm.PowerOff()
    #time.sleep(10)
    for i in range(0,10):
        Arm.SetAllPos(500,450+i*15,450+i*15,125+i*10,450+i*10,450+i*10)
        time.sleep(1/10)
    for i in range(0,10):
        Arm.SetAllPos(500,600-i*15,600-i*15,225-i*10,550-i*10,550-i*10)
        time.sleep(1/10)

    #i=0
    #Arm.SetAllPos(500-i,500-i,500-i,500-i,500-i,500-i)
    #time.sleep(1/5)
    #time.sleep(2)