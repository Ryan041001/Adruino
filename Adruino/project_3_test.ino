#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// OLED引脚定义
#define OLED_MOSI   11  // D1
#define OLED_CLK    13  // D0
#define OLED_DC     9
#define OLED_CS     10
#define OLED_RESET  8

// 超声波模块引脚定义
#define TRIG_PIN 2  // 触发信号
#define ECHO_PIN 7  // 回波信号
#define BUZZER_PIN 3  // 蜂鸣器引脚 (改为3避免与OLED_RESET冲突)

// 报警距离阈值(厘米)
#define ALARM_DISTANCE 20

// 显示屏参数
#define SCREEN_WIDTH 128 // OLED显示宽度，单位像素
#define SCREEN_HEIGHT 64 // OLED显示高度，单位像素

// 显示屏初始化
Adafruit_SSD1306 display(OLED_MOSI, OLED_CLK, OLED_DC, OLED_RESET, OLED_CS);

// 测试模式选择
int testMode = 0;  // 0: OLED测试, 1: 超声波测试

void setup() {
  Serial.begin(9600);
  Serial.println("SSD1306 OLED和超声波测试程序");
  
  // 初始化引脚
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  
  // 初始化OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC)) {
    Serial.println(F("SSD1306初始化失败"));
    for(;;); // 无限循环
  }
  
  Serial.println("OLED初始化成功");
  
  // 显示Adafruit启动画面
  display.display();
  delay(1000); // 暂停1秒
  
  // 清屏
  display.clearDisplay();
  
  // 显示测试选择界面
  displayTestMenu();
  delay(3000);
  
  // 默认先进行OLED测试
  testMode = 0;
}

void loop() {
  if (testMode == 0) {
    // OLED测试模式
    runOLEDTest();
    
    // OLED测试完成后切换到超声波测试
    testMode = 1;
    displayModeChange();
    delay(2000);
  } else {
    // 超声波测试模式
    runUltrasonicTest();
  }
}

// 显示测试菜单
void displayTestMenu() {
  display.clearDisplay();
  
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("SSD1306 & Ultrasonic"));
  display.println(F("Test Program"));
  
  display.drawLine(0, 16, display.width(), 16, SSD1306_WHITE);
  
  display.setCursor(0, 20);
  display.println(F("1. OLED Display Test"));
  display.println(F("2. Ultrasonic Test"));
  
  display.setCursor(0, 45);
  display.println(F("Starting OLED test..."));
  
  display.display();
}

// 显示模式切换信息
void displayModeChange() {
  display.clearDisplay();
  
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Test Mode Change"));
  
  display.drawLine(0, 10, display.width(), 10, SSD1306_WHITE);
  
  display.setCursor(0, 20);
  display.setTextSize(2);
  display.println(F("Starting"));
  display.println(F("Ultrasonic"));
  display.println(F("Test..."));
  
  display.display();
}

// 运行OLED测试
void runOLEDTest() {
  // 测试文本显示
  testText();
  delay(2000);
  
  // 测试绘制图形
  testDrawing();
  delay(2000);
  
  // 测试滚动
  testScrolling();
  delay(2000);
  
  // 测试动画
  testAnimation();
  delay(2000);
}

// 运行超声波测试
void runUltrasonicTest() {
  // 测量距离
  float distance = measureDistance();
  
  // 显示距离
  displayDistance(distance);
  
  // 检查是否需要报警
  if (distance < ALARM_DISTANCE && distance > 0) {
    // 距离小于阈值且大于0时报警
    tone(BUZZER_PIN, 1000); // 发出1kHz的声音
    delay(50);
    noTone(BUZZER_PIN);
  }
  
  // 输出到串口监视器
  Serial.print("Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
  
  delay(200); // 刷新频率
}

// 测量距离函数
float measureDistance() {
  // 发送触发信号
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  // 读取回波时间
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); // 添加超时参数
  
  // 计算距离 (声速340m/s, 来回距离需要除以2)
  float distance = duration * 0.034 / 2;
  
  return distance;
}

// 在OLED上显示距离
void displayDistance(float distance) {
  display.clearDisplay();
  
  // 标题
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Distance Measurement"));
  display.drawLine(0, 10, display.width(), 10, SSD1306_WHITE);
  
  // 显示当前距离
  display.setTextSize(2);
  display.setCursor(10, 16);
  
  if (distance > 400 || distance <= 0) {
    display.println(F("Out of"));
    display.setCursor(10, 34);
    display.println(F("Range!"));
  } else {
    display.print(distance, 1); // 显示一位小数
    display.println(F(" cm"));
    
    // 显示距离条形图
    int barLength = map(min(distance, 100), 0, 100, 0, display.width() - 4);
    display.drawRect(2, 40, display.width() - 4, 10, SSD1306_WHITE);
    display.fillRect(2, 40, barLength, 10, SSD1306_WHITE);
  }
  
  // 显示报警阈值
  display.setTextSize(1);
  display.setCursor(0, 56);
  display.print(F("Alarm: <"));
  display.print(ALARM_DISTANCE);
  display.print(F("cm"));
  
  // 如果距离小于报警阈值，显示警告
  if (distance < ALARM_DISTANCE && distance > 0) {
    display.fillRect(90, 54, 38, 10, SSD1306_WHITE);
    display.setTextColor(SSD1306_BLACK);
    display.setCursor(92, 56);
    display.print(F("ALERT!"));
  }
  
  display.display();
}

// 测试文本显示
void testText() {
  display.clearDisplay();
  
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Hello, SSD1306!"));
  
  display.setTextSize(2);
  display.setCursor(0, 16);
  display.println(F("OLED Test"));
  
  display.setTextSize(1);
  display.setCursor(0, 40);
  display.println(F("SPI Interface"));
  
  display.setTextSize(1);
  display.setCursor(0, 56);
  display.println(F("Testing 1,2,3..."));
  
  display.display();
}

// 测试绘制图形
void testDrawing() {
  display.clearDisplay();
  
  // 绘制矩形
  display.drawRect(0, 0, 60, 30, SSD1306_WHITE);
  display.fillRect(64, 0, 60, 30, SSD1306_WHITE);
  
  // 绘制圆形
  display.drawCircle(30, 45, 15, SSD1306_WHITE);
  display.fillCircle(95, 45, 15, SSD1306_WHITE);
  
  // 绘制线条
  display.drawLine(0, 63, 127, 63, SSD1306_WHITE);
  
  display.display();
}

// 测试滚动
void testScrolling() {
  display.clearDisplay();
  
  display.setTextSize(2);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("Scroll"));
  display.println(F("Test"));
  display.display();
  
  // 水平向右滚动
  display.startscrollright(0x00, 0x07);
  delay(2000);
  display.stopscroll();
  
  // 水平向左滚动
  display.startscrollleft(0x00, 0x07);
  delay(2000);
  display.stopscroll();
  
  // 对角线向右滚动
  display.startscrolldiagright(0x00, 0x07);
  delay(2000);
  display.stopscroll();
  
  // 对角线向左滚动
  display.startscrolldiagleft(0x00, 0x07);
  delay(2000);
  display.stopscroll();
  
  display.stopscroll();
}

// 测试动画
void testAnimation() {
  display.clearDisplay();
  
  // 简单动画：移动的点
  for(int16_t i=0; i<display.width(); i+=4) {
    display.clearDisplay();
    display.drawCircle(i, display.height()/2, 10, SSD1306_WHITE);
    display.display();
    delay(50);
  }
  
  // 简单动画：扩大的圆
  for(int16_t i=0; i<30; i+=2) {
    display.clearDisplay();
    display.drawCircle(display.width()/2, display.height()/2, i, SSD1306_WHITE);
    display.display();
    delay(50);
  }
  
  // 简单动画：闪烁的矩形
  for(int16_t i=0; i<5; i++) {
    display.clearDisplay();
    display.fillRect(20, 10, 80, 40, SSD1306_WHITE);
    display.display();
    delay(200);
    
    display.clearDisplay();
    display.drawRect(20, 10, 80, 40, SSD1306_WHITE);
    display.display();
    delay(200);
  }
}