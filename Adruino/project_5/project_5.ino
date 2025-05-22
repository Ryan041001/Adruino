/*
 * 环境温湿度检测与报警系统
 * 功能：通过DHT11传感器检测环境温湿度，使用红外遥控器设置报警阈值
 * 当温湿度超过阈值时，蜂鸣器报警
 */

// 引入必要的库
#include <Wire.h>             // <<< 添加 I2C 库
#include <IRremote.h>         // 红外遥控库
#include <DHT.h>              // DHT传感器库
#include <Adafruit_GFX.h>     // OLED显示库基础
#include <Adafruit_SSD1306.h> // OLED显示库

// 定义引脚
#define IR_RECEIVE_PIN 2 // 红外接收模块引脚
#define IR_SEND_PIN 3    // 红外发射模块引脚
#define DHT_PIN 4        // DHT11传感器引脚
#define BUZZER_PIN 5     // 蜂鸣器引脚
#define DHT_TYPE DHT11   // 传感器类型

// OLED显示屏设置
#define SCREEN_WIDTH 128   // OLED显示宽度，单位：像素
#define SCREEN_HEIGHT 64   // OLED显示高度，单位：像素
#define OLED_RESET -1      
#define OLED_I2C_ADDR 0x3C 

// 创建对象
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET); // 构造函数会自动处理 -1
DHT dht(DHT_PIN, DHT_TYPE);
IRrecv irrecv(IR_RECEIVE_PIN);
decode_results results;

// 全局变量
float temperature = 0;      // 当前温度
float humidity = 0;         // 当前湿度
float tempThreshold = 30.0; // 温度报警阈值
float humiThreshold = 80.0; // 湿度报警阈值
bool alarmEnabled = true;   // 报警开关
bool settingTemp = false;   // 是否正在设置温度阈值
bool settingHumi = false;   // 是否正在设置湿度阈值

// 红外遥控器按键编码（需要根据实际遥控器测试获取）
// 这些值需要通过测试获取，以下为示例值
#define IR_BUTTON_TOGGLE_ALARM 0xFF6897 // 0键 - 切换报警开关
#define IR_BUTTON_1 0xFF30CF
#define IR_BUTTON_2 0x9E2DFE6C
#define IR_BUTTON_3 0x6182021B
#define IR_BUTTON_4 0x9E879628
#define IR_BUTTON_5 0x488F3CBB
#define IR_BUTTON_6 0x0449E79F 
#define IR_BUTTON_7 0x32C6FDF7
#define IR_BUTTON_8 0x1BC0157B
#define IR_BUTTON_9 0x3EC3FC1B
#define IR_BUTTON_VOL_UP 0xD7E84B1A // 上键 - 增加阈值 
#define IR_BUTTON_VOL_DOWN 0x52A3D41F // 下键 - 减少阈值 
#define IR_BUTTON_CONFIRM 0x20FE4DBB // OK键 - 确认/退出设置 
#define IR_BUTTON_CH_MINUS 0xE318261B // *键 (CH-) - 进入温度设置 
#define IR_BUTTON_CH_PLUS 0xACA633AC // #键 (CH+) - 进入湿度设置 

void setup()
{
  // 初始化串口通信
  Serial.begin(9600);
  Serial.println("Environment Temp & Humi Monitoring System Starting...");

  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR))
  {
    Serial.println(F("SSD1306 allocation failed"));
    for (;;); // Don't proceed, loop forever
  }
  Serial.println("OLED Initialized");

  //初始化红外接收器
  irrecv.enableIRIn(); // Start the receiver
  Serial.println("红外接收器初始化完成");

  // 初始化DHT11传感器
  dht.begin();
  Serial.println("DHT11传感器初始化完成");

  // 初始化蜂鸣器引脚
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println("Buzzer Initialized");

  // Show startup message
  // display.clearDisplay();
  // display.setTextSize(1);
  // display.setTextColor(SSD1306_WHITE);
  // display.setCursor(0, 0);
  // display.println("Temp/Humi System");
  // display.println("Initialized");
  // display.display();
  // delay(2000);
}

void loop()
{
  // Read temperature and humidity data
  readDHTData();

  // Display data on OLED
  // displayData();

  // 检查红外遥控器输入
  checkIRRemote();

  // 检查是否需要报警
  checkAlarm();

  // 延时更新
  delay(500);
}

// 读取DHT11传感器数据
void readDHTData()
{
  // 读取湿度
  humidity = dht.readHumidity();
  // 读取温度（摄氏度）
  temperature = dht.readTemperature();

  // Check if reading failed
  if (isnan(humidity) || isnan(temperature))
  {
    Serial.println("Failed to read from DHT sensor!");
    return;
  }

  // Print to serial monitor
  Serial.print("Temperature: ");
  Serial.print(temperature);
  Serial.print(" C, Humidity: ");
  Serial.print(humidity);
  Serial.println(" %");
}

// Display data on OLED

void displayData()
{
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);

  // Show current mode
  if (settingTemp)
  {
    display.println("Set Temp Thresh");
  }
  else if (settingHumi)
  {
    display.println("Set Humi Thresh");
  }
  else
  {
    display.println("Monitor Mode");
  }

  // Show temperature
  display.print("Temp: ");
  display.print(temperature);
  display.println(" C");

  // Show humidity
  display.print("Humi: ");
  display.print(humidity);
  display.println(" %");

  // Show thresholds
  display.print("Temp Thresh: ");
  display.println(tempThreshold);
  display.print("Humi Thresh: ");
  display.println(humiThreshold);

  // Show alarm status
  display.print("Alarm: ");
  display.println(alarmEnabled ? "ON" : "OFF");

  display.display();
}


// 检查红外遥控器输入
void checkIRRemote()
{
  if (irrecv.decode(&results))
  { // Check if an IR signal is received and decode it
    // 获取红外编码
    // Note: The way to get the raw data might differ slightly based on the exact library version and protocol.
    // decodedRawData might not be the correct field. Often it's results.value
    // Let's assume results.value holds the code for common protocols.
    // If 0xFFFFFFFF is received, it's often a repeat code, which we can ignore or handle.
    if (results.value != 0xFFFFFFFF)
    {
      uint32_t irCode = results.value;

      // 输出红外编码到串口（用于测试获取按键编码）
      Serial.print("接收到红外编码: 0x");
      Serial.println(irCode, HEX);

      // 根据不同按键执行不同操作
      processIRCommand(irCode); // 暂时注释掉，以便测试
    }

    // 准备接收下一个信号
    irrecv.resume(); // Receive the next value
  }
}

//处理红外遥控器命令
void processIRCommand(uint32_t irCode)
{
  // 根据接收到的红外编码执行相应操作
  switch (irCode)
  {
  case IR_BUTTON_CH_MINUS: // *键 (CH-) - 切换到温度阈值设置模式
    settingTemp = true;
    settingHumi = false;
    Serial.println("Entering Temp Threshold Setting Mode");
    break;

  case IR_BUTTON_CH_PLUS: // #键 (CH+) - 切换到湿度阈值设置模式
    settingTemp = false;
    settingHumi = true;
    Serial.println("Entering Humi Threshold Setting Mode");
    break;

  case IR_BUTTON_CONFIRM: // OK键 - 退出设置模式
    settingTemp = false;
    settingHumi = false;
    Serial.println("Exiting Setting Mode");
    break;

  case IR_BUTTON_VOL_UP: // 上键 - 增加阈值
    if (settingTemp)
    {
      tempThreshold += 1.0;
      Serial.print("Temp threshold increased to: ");
      Serial.println(tempThreshold);
    }
    else if (settingHumi)
    {
      humiThreshold += 5.0;
      Serial.print("Humi threshold increased to: ");
      Serial.println(humiThreshold);
    }
    break;

  case IR_BUTTON_VOL_DOWN: // 下键 - 减少阈值
    if (settingTemp)
    {
      tempThreshold -= 1.0;
      Serial.print("Temp threshold decreased to: ");
      Serial.println(tempThreshold);
    }
    else if (settingHumi)
    {
      humiThreshold -= 5.0;
      Serial.print("Humi threshold decreased to: ");
      Serial.println(humiThreshold);
    }
    break;

  case IR_BUTTON_TOGGLE_ALARM: // 0 key - Toggle alarm
    alarmEnabled = !alarmEnabled;
    Serial.print("Alarm function: ");
    Serial.println(alarmEnabled ? "ON" : "OFF");
    break;

  default:
    // 其他按键可以根据需要添加功能
    break;
  }
}

// 检查是否需要报警
void checkAlarm()
{
  if (!alarmEnabled)
    return; // 如果报警功能关闭，直接返回

  bool alarmTriggered = false;

  // Check if temperature exceeds threshold
  if (temperature > tempThreshold)
  {
    Serial.println("Warning: Temperature exceeds threshold!");
    alarmTriggered = true;
  }

  // Check if humidity exceeds threshold
  if (humidity > humiThreshold)
  {
    Serial.println("Warning: Humidity exceeds threshold!");
    alarmTriggered = true;
  }

  // 如果触发报警，蜂鸣器短音报警
  if (alarmTriggered)
  {
    beepAlarm();
  }
}

// 蜂鸣器报警函数
void beepAlarm()
{
  // 短音报警
  digitalWrite(BUZZER_PIN, HIGH);
  delay(200);
  digitalWrite(BUZZER_PIN, LOW);
  delay(200);
}
