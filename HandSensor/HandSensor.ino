/*
 *  This sketch sends random data over UDP on a ESP32 device
 *
 */
#include "ServoCtrl.h"
#include <WiFi.h>
#include <WiFiUdp.h>

#define LoopMs 5
#define Loopu_us LoopMs*1000

#define CommandBufLen 256

//#define APMode
//#define UserDebug

#define local_ip {192,168,4,1}
#define gateway {192,168,4,1}
#define subnet {255,255,255,0}
#define channel 1
#define ssid_hidden 0
#define max_connection 1


#define BuffLen 11
#define SendBuffLen BuffLen*2
HardwareSerial Serial1(2); // 16 17 RX, TX

const unsigned char Header[] = {0XFF,0X00,0XFF};

const char * networkName = "jixiebi";
const char * networkPswd = "jixiebijixie";//"jixiebijixie"

const unsigned char SensorOutPutCmd[] = {0xff,0xaa,0x02,0x28,0x00};
const unsigned char SensorAxis6Cmd[] = {0xff,0xaa,0x24,0x01,0x00};
const unsigned char SensorBoudRateCmd[] = {0xff,0xaa,0x04,0x05,0x00};
const unsigned char Sensor20HzCmd[] = {0xff,0xaa,0x03,0x07,0x00};
const unsigned char SensorD2AinCmd[] = {0xff,0xaa,0x10,0x00,0x00};
WiFiUDP boardcast;//, controlMsg
const char * boardcastAddr = "255.255.255.255";
const int boardcastPort = 3332;

//Are we currently connected?
bool connected = false;

unsigned int timer0Count = 0, sendCount = 0;

unsigned long int usedTime = 0, globalTimeStemp = 0;

//方便打印
unsigned char Buff[SendBuffLen] = {0};
unsigned char *PortBuff = Buff, *AngleBuff = Buff + BuffLen;
void WiFiEvent(WiFiEvent_t event);
void connectToWiFi(const char * ssid, const char * pwd);
char CheckSum=0;
void setup(){

    Serial.begin(115200);

    Serial1.begin(9600);
    delay(200);
    Serial1.write(SensorOutPutCmd, 5);
    delay(200);
    Serial1.write(SensorAxis6Cmd, 5);
    delay(200);
    Serial1.write(Sensor20HzCmd, 5);
    delay(200);
    Serial1.write(SensorD2AinCmd, 5);
    WiFi.onEvent(WiFiEvent);
    while(!connected){
        connectToWiFi(networkName, networkPswd);
        delay(5000);
    }
}

void loop(){
    globalTimeStemp = micros();
    timer0Count++; 
    if (connected){
        if(!(timer0Count%5) && Serial1.available()){

                for(char i =0;i < BuffLen;i++){
                    Buff[i] = Serial1.read();
                    delayMicroseconds(150);
                }
                
                CheckSum = 0;
                for(char i =0;i < BuffLen-1;i++){
                    CheckSum += Buff[i];
                }
                if(CheckSum == Buff[BuffLen-1] && Buff[0]==0x55 && (Buff[1]==0x55 ||  Buff[1]==0x53)){
                    if(Buff[1]==0x55){
                        memcpy(PortBuff, Buff, BuffLen);
                    }else if(Buff[1]==0x53){
                        memcpy(AngleBuff, Buff, BuffLen);
                    }
                }else{

                    Serial.println("correct");
      
                    while(Serial1.peek()!=0x55){
                        Serial1.read();
                        delayMicroseconds(100);
                    }
                }
#ifdef UserDebug
                Serial.print("Data:");
                for(char i =0;i < BuffLen-1;i++){
                    Serial.print(Buff[i], HEX);
                }
                Serial.println(Buff[BuffLen-1], HEX);
#endif          
        }
        
        
        if(!(timer0Count%16)){
                boardcast.beginPacket(boardcastAddr,boardcastPort);
                boardcast.write(Buff,SendBuffLen);
                boardcast.endPacket();
        }
    }
#ifdef UserDebug
    //Serial.print("usedTime:");
    //Serial.println((micros()-globalTimeStemp));
#endif
    delayMicroseconds(Loopu_us-(micros()-globalTimeStemp)%Loopu_us);
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
