/*
 *  This sketch sends random data over UDP on a ESP32 device
 *
 */
#include "ServoCtrl.h"
#include <WiFi.h>
#include <WiFiUdp.h>

#define Loop_us 5
#define LoopMs 5
#define CommandBufLen 256

//#define APMode
//#define UserDebug

#define local_ip {192,168,4,1}
#define gateway {192,168,4,1}
#define subnet {255,255,255,0}
#define channel 1
#define ssid_hidden 0
#define max_connection 1

#define BoardCastAllServoInfo 1
#define SetAllServoPos 2
#define SetAllServoSpeed 3
#define SetAllServoPosSpeed 4
#define BoardCastAllServoPos 5
#define SendMsg 6
#define UnloadAllServo 7
#define LoadAllServo 8

#define ServoNum 6
HardwareSerial Serial1(2); // 16 17 RX, TX
class ServoInfo
{
    public:
    unsigned char id;
    int pos;
    int expectPos;
    int msPer128Pos; // usetime = (delt(pos)*msPer128Pos)/128
    int vin;
    unsigned char temp;
    bool powerOn;
    bool needMove;
    int getMoveTime(){
        return abs(expectPos-pos)*msPer128Pos/128;
    }
    ServoInfo(){
        id = 0;
        pos = 0;
        expectPos = 0;
        msPer128Pos = 0;
        vin = 0;
        temp = 0;
        powerOn = false;
        needMove = false;
    }
};
ServoInfo servoState[ServoNum];
const unsigned char Header[] = {0XFF,0X00,0XFF};
//unsigned char temp[] = {0,0};
unsigned long int temp = 0;

const char * networkName = "jixiebi";
const char * networkPswd = "jixiebijixie";//"jixiebijixie"

WiFiUDP boardcast;//, controlMsg
const char * boardcastAddr = "255.255.255.255";
const int boardcastPort = 3333;

unsigned char command[CommandBufLen];
unsigned int recvCommandLen = 0;
unsigned long int comTimeStemp = 0;
unsigned char comMode = 0;
unsigned int comLen = 0;
//Are we currently connected?
bool connected = false;

hw_timer_t * timer0 = NULL, * timer1 = NULL;
bool timer0Fired = false, timer1Fired = false;
unsigned int timer0Count = 0, timer1Count = 0, boardCastCount = 0;
portMUX_TYPE timer0Mux = portMUX_INITIALIZER_UNLOCKED;

unsigned long int test = 0, usedTime = 0, globalTimeStemp = 0;

unsigned char ServoGetPosCount = 0, ServoGetExtraInfoCount = 0, ServoGetExtraInfoServoCount = 0;

void setup(){
    Serial.begin(115200);
    Serial1.begin(115200);
    WiFi.onEvent(WiFiEvent);
    while(!connected){
        connectToWiFi(networkName, networkPswd);
        delay(10000);
    }
    
    for(int i=0;i<ServoNum;i++){
        servoState[i].id = i+1;
        servoState[i].msPer128Pos = 5*128;
    }
}

void loop(){
    globalTimeStemp = micros();
    timer0Count++; 
    if (connected){
        if(!(timer0Count%(35/LoopMs))){
            boardcast.parsePacket();
            if(boardcast.available()){
                recvCommandLen = boardcast.read(command,CommandBufLen-1);
                if (recvCommandLen > 7 && command[0] == 0xff && command[1] == 0x00 && command[2] == 0xff){
                    
                    memcpy(&comTimeStemp,&command[3],4);
                    comMode = command[7];
                    memcpy(&comLen,&command[8],2);
                    
                    if(globalTimeStemp-comTimeStemp < 1230000){
#ifdef UserDebug
                        Serial.print("comLen:");
                        Serial.print(recvCommandLen);
                        Serial.print(" comMode:");
                        Serial.println(comMode);
#endif                  
                        switch(comMode){   
                            case SetAllServoPos: 
                                setAllServoPos(&command[10]);
                                break;
                                
                            case SetAllServoSpeed: 
                                setAllServoSpeed(&command[10]);
                                break;
                                
                            case SetAllServoPosSpeed:
                                setAllServoPosSpeed(&command[10]);
                                break;
                                
                            case UnloadAllServo:
                                unloadAllServo(&command[10]);
                                break;
                                
                            case LoadAllServo:
                                loadAllServo(&command[10]);
                                break;
                        }
                    }else{
#ifdef UserDebug      
                        Serial.print("Timeout Command: Local:");
                        Serial.print(globalTimeStemp);
                        Serial.print(" Com:");
                        Serial.print(comTimeStemp);
                        Serial.print(" Delay:");
                        Serial.println(globalTimeStemp - comTimeStemp);
#endif
                    }
                }
#ifdef UserDebug
                else{
                    Serial.print("failedData:");
                    Serial.println((char *)command);
                }
#endif
            }
        }else if(!(timer0Count%(150/LoopMs))){
#ifdef UserDebug
            Serial.println("Send boardCastAllServo");
#endif
            if (boardCastCount++%19){//!=0
                    boardCastAllServoPos();
                }else{//==0
                    boardCastAllServoInfo();
                }
        }  
    }
    
    //Move The Servo
    if(servoState[timer0Count%6].powerOn && servoState[timer0Count%6].needMove){
        LobotSerialServoMove(Serial1, servoState[timer0Count%6].id, servoState[timer0Count%6].expectPos, servoState[timer0Count%6].getMoveTime());
        servoState[timer0Count%6].needMove = false;
        servoState[timer0Count%6].powerOn = true;
    }
    
    if(!(timer0Count%(30/LoopMs))){
        refreshServoPos();
    }
    else if(!(timer0Count%(199/LoopMs))){
        refreshServoInfo();
    }
#ifdef UserDebug
    Serial.print("usedTime:");
    Serial.println((micros()-globalTimeStemp));
#endif
    delayMicroseconds(Loop_us-(micros()-globalTimeStemp)%Loop_us);
}
void correctServoPos(int pos[]){
    if(pos[0] > 500){
        pos[0] = 500;
    }else if(pos[0] < 0){
        pos[0] = 0;
    }
    if(pos[1] > 1000){
        pos[1] = 1000;
    }else if(pos[1] < 0){
        pos[1] = 0;
    }
    if(pos[2] > 900){
        pos[2] = 900;
    }else if(pos[2] < 60){
        pos[2] = 60;
    }
    if(pos[3] > 980){
        pos[3] = 980;
    }else if(pos[3] < 20){
        pos[3] = 20;
    }
    if(pos[4] > 880){
        pos[4] = 880;
    }else if(pos[4] < 160){
        pos[4] = 160;
    }
    if(pos[5] > 1000){
        pos[5] = 1000;
    }else if(pos[5] < 0){
        pos[5] = 0;
    }
}
void refreshServoInfo(){
    int vin = 0, temp = 0;
    switch(ServoGetExtraInfoCount%2){
        case 0:
            vin = LobotSerialServoReadVin(Serial1, servoState[(ServoGetExtraInfoCount/2)%6].id);
            if(vin > 0){
                servoState[(ServoGetExtraInfoCount/2)%6].vin = vin;
            }
#ifdef UserDebug
            else{
                Serial.print("Error vin:");
                Serial.print(vin);
                }
#endif 
            break;
        case 1:
            temp = LobotSerialServoReadTemp(Serial1, servoState[(ServoGetExtraInfoCount/2)%6].id);
            if(temp > 0){
                servoState[(ServoGetExtraInfoCount/2)%6].temp = temp;
            }
#ifdef UserDebug
            else{
                Serial.print("Error temp:");
                Serial.print(temp);
                }
#endif 
    }
    ServoGetExtraInfoCount++;
}

void refreshServoPos(){
#ifdef UserDebug
    Serial.println("refreshAllServoPos");
#endif   
    int pos = 0;
    pos = LobotSerialServoReadPosition(Serial1, servoState[ServoGetPosCount%6].id);
    if (pos > 0){
        servoState[ServoGetPosCount%6].pos = pos;
#ifdef UserDebug
        Serial.print("Error after:");
        Serial.println(test);
        test = 0;
#endif  
    }else{
        test++;
    }
    ServoGetPosCount++;
}

void boardCastAllServoInfo(){
    boardcast.beginPacket(boardcastAddr,boardcastPort);
    boardcast.write((const unsigned char *)Header,3);
    boardcast.write((const unsigned char *)&globalTimeStemp,4);
    boardcast.write(BoardCastAllServoInfo);
    temp = 48;
    boardcast.write((const unsigned char *)&temp,2);
    for(int i = 0;i < ServoNum;i++){
        boardcast.write(servoState[i].id);//id len=1
        boardcast.write((const unsigned char *)&servoState[i].pos,2);//pos len=2
        boardcast.write((const unsigned char *)&servoState[i].msPer128Pos,2);//msPer128Pos len=2
        boardcast.write((const unsigned char *)&servoState[i].vin,2);//vin len=2
        boardcast.write(servoState[i].temp);//temp len=1
    }
    boardcast.endPacket();
}

void boardCastAllServoPos(){
#ifdef UserDebug
    Serial.println("boardCastAllServoPos");
#endif   
    boardcast.beginPacket(boardcastAddr,boardcastPort);
    boardcast.write((const unsigned char *)Header,3);
    boardcast.write((const unsigned char *)&globalTimeStemp,4);
    boardcast.write(BoardCastAllServoPos); 
    temp = 18;
    boardcast.write((const unsigned char *)&temp,2);
    for(int i = 0;i < ServoNum;i++){
        boardcast.write(servoState[i].id);//id
        boardcast.write((const unsigned char *)&servoState[i].pos,2);//pos
    }
    boardcast.endPacket();
}

void setAllServoPos(const unsigned char Data[]){
    int pos[ServoNum] = {0};
    bool trueData = true;
    for(int i=0;i<ServoNum;i++){
        if(servoState[i].id == Data[i*3]){
            memcpy(&(pos[i]), &Data[i*3+1], 2);
#ifdef UserDebug
            Serial.print("Set Pos:");
            Serial.println(pos[i]);
#endif
            //if(pos[i] > 1000 || pos[i] < 0){
            //    trueData = false;
            //}
        }else{
            Serial.print("Worng ID:");
            Serial.println(Data[i*3]);
            trueData = false;
        }
    }
    if(trueData == true){
        correctServoPos(pos);
        for(int i=0;i<ServoNum;i++){
            servoState[i].expectPos = pos[i];
            servoState[i].needMove = true;
        }
    }
}

void setAllServoSpeed(const unsigned char Data[]){
    int speed[ServoNum] = {0};
    bool trueData = true;
    for(int i=0;i<ServoNum;i++){
        if(servoState[i].id == Data[i*3]){
            memcpy(&(speed[i]), &Data[i*3+1], 2);
            if(speed[i] < 0){
                trueData = false;
            }
        }else{
            Serial.print("Worng ID:");
            Serial.println(Data[i*3]);
            trueData = false;
        }
    }
    if(trueData == true){
        for(int i=0;i<ServoNum;i++){
            servoState[i].msPer128Pos = speed[i];
        }
    }
}

void setAllServoPosSpeed(const unsigned char Data[]){
    int speed[ServoNum] = {0}, pos[ServoNum] = {0};
    bool trueData = true;
    for(int i=0;i<ServoNum;i++){
        if(servoState[i].id == Data[i*5]){
            memcpy(&(pos[i]), &Data[i*5+1], 2);//expectPos msPer128Pos
            memcpy(&(speed[i]), &Data[i*5+3], 2);
#ifdef UserDebug
            Serial.print("expectPos");
            Serial.println(servoState[i].expectPos);
#endif
            if(pos[i] > 1000 || pos[i] < 0 || speed[i] < 0){
                trueData = false;
            }
        }else{
            Serial.print("Worng ID:");
            Serial.println(Data[i*5]);
            trueData = false;
        }
    }
    if(trueData == true){
        correctServoPos(pos);
        for(int i=0;i<ServoNum;i++){
            servoState[i].expectPos = pos[i];
            servoState[i].msPer128Pos = speed[i];
            servoState[i].needMove = true;
        }
    }
}

void unloadAllServo(const unsigned char Data[]){
    bool trueData = true;
    for(int i=0;i<ServoNum;i++){
        if(servoState[i].id == Data[i]){
#ifdef UserDebug
            Serial.print("unloadAllServo");
#endif
        }else{
            Serial.print("Worng ID:");
            Serial.println(Data[i]);
            trueData = false;
        }
    }
    if(trueData == true){
        for(int i=0;i<ServoNum;i++){
            servoState[i].powerOn = false;
            LobotSerialServoUnload(Serial1, servoState[i].id);
        }
    }
}

void loadAllServo(const unsigned char Data[]){
    bool trueData = true;
    for(int i=0;i<ServoNum;i++){
        if(servoState[i].id == Data[i]){
#ifdef UserDebug
            Serial.print("unloadAllServo");
#endif
        }else{
            Serial.print("Worng ID:");
            Serial.println(Data[i]);
            trueData = false;
        }
    }
    if(trueData == true){
        for(int i=0;i<ServoNum;i++){
            servoState[i].powerOn = true;
            LobotSerialServoLoad(Serial1, servoState[i].id);
        }
    }
}

void connectToWiFi(const char * ssid, const char * pwd){
#ifdef APMode
    Serial.println("Creating WiFi network: " + String(ssid));
    WiFi.softAPConfig(local_ip, gateway, subnet);
    WiFi.softAP(ssid, pwd, channel, ssid_hidden, max_connection);
    WiFi.enableAP(true);
#else
    Serial.println("Connecting to WiFi network: " + String(ssid));
    WiFi.begin(ssid, pwd);
    Serial.println("Waiting for WIFI connection...");
#endif
}

void WiFiEvent(WiFiEvent_t event){
#ifdef APMode
    switch(event) {
        case SYSTEM_EVENT_AP_STACONNECTED:
            Serial.print("A STA connected!");
            Serial.println(WiFi.softAPIP()); 
            boardcast.begin({0,0,0,0},boardcastPort);
            connected = true;
            break;
        case SYSTEM_EVENT_AP_PROBEREQRECVED:
            Serial.print("A STA disconnected!");
            connected = false;
            break;
    }
#else
    switch(event) {
      case SYSTEM_EVENT_STA_GOT_IP:
          Serial.print("WiFi connected! IP address: ");
          Serial.println(WiFi.localIP());  
          boardcast.begin({0,0,0,0},boardcastPort);
          connected = true;
          break;
      case SYSTEM_EVENT_STA_DISCONNECTED:
          Serial.println("WiFi lost connection");
          connected = false;
          break;
    }
#endif
}
