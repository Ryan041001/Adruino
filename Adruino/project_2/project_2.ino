// 引脚定义
const int sensorPin = A0;  // 光敏传感器AO接A0
const int ledPin = 9;      // LED接D9（支持PWM）

// 全局变量
int mode = 0;                // 0-夜灯 1-阅读 2-自适应
unsigned long lastRead = 0;  // 时间记录

void setup() {
  Serial.begin(9600);
  pinMode(ledPin, OUTPUT);
  Serial.println("系统启动，当前模式：夜灯(a)/阅读(b)/自适应(c)");
}

void loop() {
  // 串口指令处理
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    switch (cmd) {
      case 'a':
        mode = 0;
        Serial.println("夜灯模式");
        break;
      case 'b':
        mode = 1;
        Serial.println("阅读模式");
        break;
      case 'c':
        mode = 2;
        Serial.println("自适应模式");
        break;
    }
  }

  // 每5秒读取并发送亮度数据
  if (millis() - lastRead >= 5000) {
    int currentLight = 1023 - analogRead(sensorPin);
    Serial.print("当前亮度：");
    Serial.println(currentLight);
    lastRead = millis();
  }

  // 亮度控制逻辑
  switch (mode) {
    case 0:  // 夜灯模式（低亮度）
      analogWrite(ledPin, 5);
      break;

    case 1:  // 阅读模式（高亮度）
      analogWrite(ledPin, 255);
      break;

    case 2:  // 自适应模式
      int currentLight = 1023 - analogRead(sensorPin);
      int brightness = map(currentLight, 0, 1023, 255, 0);
      analogWrite(ledPin, brightness);
      break;
  }
}