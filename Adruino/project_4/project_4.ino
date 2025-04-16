#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <RTClib.h>

// OLED配置
#define OLED_DC     9
#define OLED_CS     10
#define OLED_RESET  8
Adafruit_SSD1306 display(128, 64, &SPI, OLED_DC, OLED_RESET, OLED_CS);

// RTC对象
RTC_DS1307 rtc;

// 硬件引脚定义
#define BUZZER_PIN  6
#define SET_PIN     2
#define ADD_PIN     3
#define DEC_PIN     4

// 全局变量
DateTime currentTime;
uint8_t alarmHour = 7;
uint8_t alarmMinute = 30;
bool alarmEnabled = false;
uint8_t settingMode = 0;  // 0:正常 1:设置小时 2:设置分钟 3:闹钟小时 4:闹钟分钟
bool blinkState = false;
unsigned long lastUpdate = 0;
unsigned long lastBeep = 0;

// 星期缩写
const char* dayNames[] = {"Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"};

void setup() {
  Serial.begin(9600);
  
  // 初始化OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC)) {
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  showSplash();
  
  // 初始化RTC
  if (!rtc.begin()) {
    display.println("RTC Error");
    display.display();
    while(1);
  }
  if (!rtc.isrunning()) {
    rtc.adjust(DateTime(F(__DATE__), F(__TIME__)));
  }

  // 配置引脚
  pinMode(BUZZER_PIN, OUTPUT);
  pinMode(SET_PIN, INPUT_PULLUP);
  pinMode(ADD_PIN, INPUT_PULLUP);
  pinMode(DEC_PIN, INPUT_PULLUP);

  // 初始化显示
  display.setTextWrap(false);
  display.cp437(true);
}

void loop() {
  currentTime = rtc.now();
  handleButtons();
  updateDisplay();
  checkAlarm();
  handleSerial();
}

// 显示开机画面
void showSplash() {
  display.clearDisplay();
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  
  // 绘制动态进度条
  for(int i=0; i<128; i+=4){
    display.drawLine(i, 55, i+2, 55, SSD1306_WHITE);
    display.display();
    delay(30);
  }
  delay(500);
}

// 处理按键输入（带防抖）
void handleButtons() {
  static unsigned long lastDebounce = 0;
  const uint8_t debounceDelay = 200;

  if ((millis() - lastDebounce) < debounceDelay) return;

  // SET键切换模式
  if (!digitalRead(SET_PIN)) {
    settingMode = (settingMode + 1) % 5;
    lastDebounce = millis();
    return;
  }

  // 加减键处理
  if (settingMode > 0) {
    int adjust = 0;
    if (!digitalRead(ADD_PIN)) adjust = 1;
    if (!digitalRead(DEC_PIN)) adjust = -1;

    if (adjust != 0) {
      adjustSettings(adjust);
      lastDebounce = millis();
    }
  }
}

// 调整设置参数
void adjustSettings(int delta) {
  DateTime temp = currentTime;
  
  switch(settingMode) {
    case 1:  // 调整小时
      temp = DateTime(temp.year(), temp.month(), temp.day(),
                     constrain(temp.hour() + delta, 0, 23), 
                     temp.minute(), 0);
      rtc.adjust(temp);
      break;
      
    case 2:  // 调整分钟
      temp = DateTime(temp.year(), temp.month(), temp.day(),
                     temp.hour(),
                     constrain(temp.minute() + delta, 0, 59), 
                     0);
      rtc.adjust(temp);
      break;
      
    case 3:  // 闹钟小时
      alarmHour = constrain(alarmHour + delta, 0, 23);
      break;
      
    case 4:  // 闹钟分钟
      alarmMinute = constrain(alarmMinute + delta, 0, 59);
      break;
  }
}

// 更新显示界面
void updateDisplay() {
  if (millis() - lastUpdate < 500) return;
  lastUpdate = millis();
  blinkState = !blinkState;

  display.clearDisplay();
  
  // 顶部状态栏
  display.fillRect(0, 0, 128, 16, SSD1306_WHITE);
  
  // 日期显示
  display.setTextColor(SSD1306_BLACK);
  display.setTextSize(1);
  display.setCursor(2, 4);
  display.printf("%04d/%02d/%02d", 
                currentTime.year(), 
                currentTime.month(), 
                currentTime.day());
  
  // 星期显示
  display.setCursor(90, 4);
  display.print(dayNames[currentTime.dayOfTheWeek()]);

  // 时间显示
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(2);
  
  // 处理闪烁效果
  if(!(settingMode == 1 && blinkState)) {
    display.setCursor(15, 25);
    display.printf("%02d", currentTime.hour());
  }
  
  display.print(":");
  
  if(!(settingMode == 2 && blinkState)) {
    display.printf("%02d", currentTime.minute());
  }

  // 闹钟状态
  display.setTextSize(1);
  display.setCursor(0, 50);
  display.print("Alarm: ");
  if(alarmEnabled) {
    if(settingMode == 3 && blinkState) display.print("  ");
    else display.printf("%02d", alarmHour);
    display.print(":");
    if(settingMode == 4 && blinkState) display.print("  ");
    else display.printf("%02d", alarmMinute);
  } else {
    display.print("OFF ");
  }

  // 模式指示器
  display.setCursor(100, 50);
  display.print("[");
  display.print(settingMode);
  display.print("]");

  display.display();
}

// 闹钟检测（非阻塞式）
void checkAlarm() {
  if(alarmEnabled && 
     currentTime.hour() == alarmHour &&
     currentTime.minute() == alarmMinute &&
     currentTime.second() < 30) {
       
    if(millis() - lastBeep > 1000) {
      tone(BUZZER_PIN, 2000, 500);
      lastBeep = millis();
    }
  }
}

// 处理串口命令
void handleSerial() {
  if(Serial.available()) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    if(input.startsWith("SETTIME")) {
      setTimeViaSerial(input);
    }
    else if(input.startsWith("SETALARM")) {
      setAlarmViaSerial(input);
    }
    else if(input.equals("TOGGLEALARM")) {
      alarmEnabled = !alarmEnabled;
    }
  }
}

// 通过串口设置时间
void setTimeViaSerial(String cmd) {
  int y, mo, d, h, mi, s;
  if(sscanf(cmd.c_str(), "SETTIME %d %d %d %d %d %d", 
           &y, &mo, &d, &h, &mi, &s) == 6) {
    DateTime newTime(y, mo, d, h, mi, s);
    rtc.adjust(newTime);
  }
}

// 通过串口设置闹钟
void setAlarmViaSerial(String cmd) {
  int h, m;
  if(sscanf(cmd.c_str(), "SETALARM %d %d", &h, &m) == 2) {
    alarmHour = constrain(h, 0, 23);
    alarmMinute = constrain(m, 0, 59);
    alarmEnabled = true;
  }
}