# Configuration settings for the Home Clock and Weather Service application

# 心知天气API设置
# 从心知天气获取API密钥: https://www.seniverse.com/
# API文档: https://docs.seniverse.com/api/start/start.html
WEATHER_API_KEY = "SH_B_ifQypc9TN8N3"  # 请替换为您的心知天气API密钥
WEATHER_API_URL = "https://api.seniverse.com/v3/weather/daily.json"  # 天气预报API接口
WEATHER_NOW_API_URL = "https://api.seniverse.com/v3/weather/now.json"  # 实时天气API接口
WEATHER_LIFE_API_URL = "https://api.seniverse.com/v3/life/suggestion.json"  # 生活指数API接口
WEATHER_LOCATION = "hangzhou"  # 默认位置
WEATHER_LANGUAGE = "zh-Hans"  # 返回数据语言，默认中文简体
WEATHER_UNIT = "c"  # 温度单位，c: 摄氏度，f: 华氏度

# 阿里云NTP服务器设置
# 文档: https://help.aliyun.com/document_detail/92704.html
# 可选NTP服务器地址:
# 公网: ntp.aliyun.com, ntp1-7.aliyun.com
# VPC内网: ntp.cloud.aliyuncs.com, ntp7-12.cloud.aliyuncs.com
# 经典网络内网: ntp1-6.cloud.aliyuncs.com
NTP_SERVER_PRIMARY = "ntp.aliyun.com"  # 主NTP服务器
NTP_SERVER_BACKUP = "ntp1.aliyun.com"  # 备用NTP服务器
NTP_TIMEOUT = 5  # NTP请求超时时间（秒）

# 应用程序设置
UPDATE_INTERVAL = 30 * 60  # 天气更新间隔（秒，默认30分钟）
TIME_SYNC_INTERVAL = 24 * 60 * 60  # 时间同步间隔（秒，默认24小时）
MAX_RETRY_COUNT = 3  # API请求最大重试次数
RETRY_DELAY = 5  # 重试延迟（秒）

# 界面设置
WINDOW_WIDTH = 800  # 窗口宽度
WINDOW_HEIGHT = 480  # 窗口高度，适合树莓派显示器
CLOCK_SIZE = 200  # 模拟时钟尺寸（像素）
FONT_FAMILY = "Microsoft YaHei"  # 默认字体
THEME_COLOR = "#1E88E5"  # 主题颜色（蓝色）
DARK_MODE = False  # 是否启用暗色模式
