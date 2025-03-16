#define LED_NORMAL1_PIN 2   // 普通 LED，接口2
#define LED_BREATH_PIN  3   // PWM LED（呼吸效果），接口3
#define LED_NORMAL2_PIN 4   // 普通 LED，接口4
#define LED_NORMAL3_PIN 5   // 普通 LED，接口5

#define BUTTON_PIN      7   // 按钮接在接口7

int lastButtonState = HIGH; // 上一次按钮的状态
unsigned long lastDebounceTime = 0; // 防抖计时器
const unsigned long debounceDelay = 50; // 防抖延时
unsigned long buttonPressTime = 0; // 按钮按下时间
bool isRandomMode = false; // 是否随机模式
bool modeSelected = false; // 是否已选择模式
bool buttonPressed = false; // 按钮是否被按下

void setup() {
  delay(1000); // 等待开发板完全启动
  Serial.begin(9600);
  Serial.println("系统启动，请选择模式：短按为固定顺序，长按为随机顺序");

  // 初始化 LED 引脚
  pinMode(LED_NORMAL1_PIN, OUTPUT);
  pinMode(LED_BREATH_PIN, OUTPUT);
  pinMode(LED_NORMAL2_PIN, OUTPUT);
  pinMode(LED_NORMAL3_PIN, OUTPUT);

  // 初始化按钮引脚（内部上拉）
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  // 等待用户选择模式
  while (!modeSelected) {
    int buttonState = digitalRead(BUTTON_PIN);

    if (buttonState == LOW && lastButtonState == HIGH) {
      buttonPressTime = millis();
    }

    if (buttonState == HIGH && lastButtonState == LOW) {
      unsigned long pressDuration = millis() - buttonPressTime;

      if (pressDuration < 1000) {
        isRandomMode = false;
        modeSelected = true;
        Serial.println("选择模式：固定顺序");
      } else {
        isRandomMode = true;
        modeSelected = true;
        Serial.println("选择模式：随机顺序");
      }
    }

    lastButtonState = buttonState;
  }

  Serial.println("系统启动，开始运行");
}

void loop() {
  // 读取按钮状态
  int buttonState = digitalRead(BUTTON_PIN);

  // 检测按钮状态变化（下降沿）
  if (buttonState == LOW && lastButtonState == HIGH) {
    buttonPressTime = millis();
    buttonPressed = true; // 标记按钮被按下
  }

  // // 检测按钮状态变化（上升沿）
  if (buttonState == HIGH && lastButtonState == LOW) {
    unsigned long pressDuration = millis() - buttonPressTime;

    // 防抖逻辑
    if (pressDuration > debounceDelay) {
      if (pressDuration >= 1000 && buttonPressed) {
        // 长按：切换顺序模式
        isRandomMode = !isRandomMode;
        Serial.print("切换顺序模式：");
        Serial.println(isRandomMode ? "随机顺序" : "固定顺序");
        buttonPressed = false; // 重置按钮按下标志
      }
    }
  }

  // // 更新上一次按钮状态
  lastButtonState = buttonState;

  // 根据当前模式调用相应函数
  if (isRandomMode) {
    // 随机顺序模式
    static unsigned long lastModeChangeTime = 0;
    static int randomMode = 0;

    if (millis() - lastModeChangeTime > 2000) { // 每2秒切换一次模式
      randomMode = random(0, 5);
      lastModeChangeTime = millis();
    }

    switch (randomMode) {
      case 0:
        mode1();
        break;
      case 1:
        mode2();
        break;
      case 2:
        mode3();
        break;
      case 3:
        mode4();
        break;
      case 4:
        mode5();
        break;
      default:
        break;
    }
  } else {
    // 固定顺序模式
    mode1();
    delay(1000);
    mode2();
    delay(1000);
    mode3();
    delay(1000);
    mode4();
    delay(1000);
    mode5();
    delay(1000);
  }
}

/* ------------------------ */
/*    呼吸灯辅助函数         */
/* ------------------------ */
void breathFadeIn() {
  for (int brightness = 0; brightness <= 255; brightness += 5) {
    analogWrite(LED_BREATH_PIN, brightness);
    delay(10);
  }
  
}

void breathFadeOut(){
  for (int brightness = 255; brightness >= 0; brightness -= 5) {
    analogWrite(LED_BREATH_PIN, brightness);
    delay(10);
  }
}
/* ------------------------ */
/*       模式1：从左到右逐个点亮 */
/* ------------------------ */
void mode1() {
  Serial.println("mode1");
  digitalWrite(LED_NORMAL1_PIN, HIGH);
  delay(200);
  breathFadeIn();
  delay(200);
  digitalWrite(LED_NORMAL2_PIN, HIGH);
  delay(200);
  digitalWrite(LED_NORMAL3_PIN, HIGH);
  delay(500);
  

  // 全部熄灭
  digitalWrite(LED_NORMAL1_PIN, LOW);
  digitalWrite(LED_NORMAL2_PIN, LOW);
  digitalWrite(LED_NORMAL3_PIN, LOW);
  breathFadeOut();
  delay(500);
}

/* ------------------------ */
/*    模式2：从左到右逐个先亮后灭  */
/* ------------------------ */
void mode2() {
  Serial.println("mode2");
  digitalWrite(LED_NORMAL1_PIN, HIGH);
  delay(200);
  digitalWrite(LED_NORMAL1_PIN, LOW);

  breathFadeIn();
  breathFadeOut();
  delay(200);

  digitalWrite(LED_NORMAL2_PIN, HIGH);
  delay(200);
  digitalWrite(LED_NORMAL2_PIN, LOW);

  digitalWrite(LED_NORMAL3_PIN, HIGH);
  delay(200);
  digitalWrite(LED_NORMAL3_PIN, LOW);

  delay(500);
}

/* ------------------------ */
/*    模式3：从两边到中间逐个点亮  */
/* ------------------------ */
void mode3() {
  Serial.println("mode3");
  digitalWrite(LED_NORMAL1_PIN, HIGH);
  digitalWrite(LED_NORMAL3_PIN, HIGH);
  delay(200);

  digitalWrite(LED_NORMAL2_PIN, HIGH);
  breathFadeIn();
  delay(500);

  // 全部熄灭
  digitalWrite(LED_NORMAL1_PIN, LOW);
  digitalWrite(LED_NORMAL2_PIN, LOW);
  digitalWrite(LED_NORMAL3_PIN, LOW);
  breathFadeOut();
  delay(500);
}

/* ------------------------ */
/*   模式4：从两边到中间逐个先亮后灭  */
/* ------------------------ */
void mode4() {
  Serial.println("mode4");
  digitalWrite(LED_NORMAL1_PIN, HIGH);
  digitalWrite(LED_NORMAL3_PIN, HIGH);
  delay(200);
  digitalWrite(LED_NORMAL1_PIN, LOW);
  digitalWrite(LED_NORMAL3_PIN, LOW);

  digitalWrite(LED_NORMAL2_PIN, HIGH);
  breathFadeIn();
  delay(200);
  digitalWrite(LED_NORMAL2_PIN, LOW);
  breathFadeOut();

  delay(500);
}

/* ------------------------ */
/*    模式5：全亮后从一边开始逐个灭灯  */
/* ------------------------ */
void mode5() {
  Serial.println("mode5");
  // 先将所有 LED 全亮
  digitalWrite(LED_NORMAL1_PIN, HIGH);
  digitalWrite(LED_NORMAL2_PIN, HIGH);
  digitalWrite(LED_NORMAL3_PIN, HIGH);
  breathFadeIn();

  delay(500);

  // 从左到右依次熄灭
  digitalWrite(LED_NORMAL1_PIN, LOW);
  delay(200);
  breathFadeOut();
  delay(200);
  digitalWrite(LED_NORMAL2_PIN, LOW);
  delay(200);
  digitalWrite(LED_NORMAL3_PIN, LOW);

  delay(500);
}