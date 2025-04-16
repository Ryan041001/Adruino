#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <RTClib.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_DC    9
#define OLED_CS    10
#define OLED_RST   8

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &SPI, OLED_DC, OLED_RST, OLED_CS);
RTC_DS1307 rtc;

DateTime now;
DateTime alarmTime;
bool alarmEnabled = false;

// 引脚定义
const int buzzer = A4;

void setup() {
  Serial.begin(9600);
  pinMode(buzzer, OUTPUT);
  
  // OLED初始化
  display.begin(SSD1306_SWITCHCAPVCC);
  display.clearDisplay();
  
  // 显示开机画面
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(10,20);
  display.print("Smart Clock");
  display.display();
  delay(2000);
  
  // RTC初始化
  if (!rtc.begin()) {
    Serial.println("RTC Error");
    while(1);
  }
  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }
}

void loop() {
  now = rtc.now();
  handleSerial();
  updateDisplay();
  checkAlarm();
}

void updateDisplay() {
  display.clearDisplay();
  
  // 顶部日期显示（黄色区域模拟）
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0,0);
  display.print(now.year());
  display.print("-");
  display.print(now.month());
  display.print("-");
  display.print(now.day());
  
  // 星期显示
  display.setCursor(80,0);
  display.print(getWeekday(now.dayOfTheWeek()));

  // 中间时间显示
  display.setTextSize(2);
  display.setCursor(20,25);
  if(now.hour()<10) display.print("0");
  display.print(now.hour());
  display.print(":");
  if(now.minute()<10) display.print("0");
  display.print(now.minute());
  display.print(":");
  if(now.second()<10) display.print("0");
  display.print(now.second());

  display.display();
}

String getWeekday(uint8_t day) {
  const char* days[] = {"Sun","Mon","Tue","Wed","Thu","Fri","Sat"};
  return days[day];
}

void handleSerial() {
  if(Serial.available()){
    String cmd = Serial.readStringUntil('\n');
    
    if(cmd.startsWith("SET")){
      setTime(cmd);
    }
    else if(cmd.startsWith("ALARM")){
      setAlarm(cmd);
    }
  }
}

void setTime(String cmd) {
  int y = cmd.substring(4,8).toInt();
  int m = cmd.substring(9,11).toInt();
  int d = cmd.substring(12,14).toInt();
  int hh = cmd.substring(15,17).toInt();
  int mm = cmd.substring(18,20).toInt();
  int ss = cmd.substring(21,23).toInt();
  
  rtc.adjust(DateTime(y, m, d, hh, mm, ss));
}

void setAlarm(String cmd) {
  int hh = cmd.substring(6,8).toInt();
  int mm = cmd.substring(9,11).toInt();
  alarmTime = DateTime(now.year(), now.month(), now.day(), hh, mm, 0);
  alarmEnabled = true;
}

void checkAlarm() {
  if(alarmEnabled && now.hour()==alarmTime.hour() 
     && now.minute()==alarmTime.minute() && now.second()<10) {
    digitalWrite(buzzer, HIGH);
    delay(100);
    digitalWrite(buzzer, LOW);
  }
}