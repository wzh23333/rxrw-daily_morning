import datetime
from datetime import timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random

# nowtime = datetime.utcnow() + timedelta(hours=8)  # 东八区时间
nowtime = datetime.datetime.now(datetime.timezone.utc) + timedelta(hours=8)
today = nowtime.date()

start_date = os.getenv('START_DATE')
#city = os.getenv('CITY')
city = "101100201"  # 忻州市的行政区划代码
birthday = os.getenv('BIRTHDAY')

app_id = os.getenv('APP_ID')
app_secret = os.getenv('APP_SECRET')

user_ids = os.getenv('USER_ID', '').split("\n")
template_id = os.getenv('TEMPLATE_ID')

if app_id is None or app_secret is None:
    print('请设置 APP_ID 和 APP_SECRET')
    exit(422)

if not user_ids:
    print('请设置 USER_ID，若存在多个 ID 用回车分开')
    exit(422)

if template_id is None:
    print('请设置 TEMPLATE_ID')
    exit(422)

# 使用和风天气API获取天气信息
def get_weather():
    if city is None:
        print('请设置城市')
        return None
    
    # 打印城市名称
    print(f"请求的城市: {city}")
    
    api_key = "d34f6dbb253a4d7cad0b776a35d68be2"  # 和风天气API密钥
    url = f"https://devapi.qweather.com/v7/weather/now?location={city}&key={api_key}&lang=zh"
    
    res = requests.get(url).json()
    
    # 打印API响应以便调试
    print(f"API响应: {res}")
    
    # 检查API响应是否包含预期的字段
    if res is None or res.get('code') != '200':
        print('获取天气信息失败，请检查城市名称或API配置')
        return None
    
    weather = {
        'weather': res['now']['text'],              # 天气描述
        'temp': float(res['now']['temp']),          # 当前温度
        'high': 'N/A',                              # 该接口没有最高温度数据，暂时留空
        'low': 'N/A',                               # 该接口没有最低温度数据，暂时留空
        'humidity': res['now']['humidity'],         # 湿度
        'wind': res['now']['windSpeed'],            # 风速
        'airData': 'N/A',                           # 该接口没有空气数据，暂时留空
        'airQuality': 'N/A'                         # 该接口没有空气质量数据，暂时留空
    }
    return weather

# 获取当前日期为星期几
def get_week_day():
    week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    week_day = week_list[today.weekday()]
    return week_day

# 纪念日正数
def get_memorial_days_count():
    if start_date is None:
        print('没有设置 START_DATE')
        return 0
    delta = today - datetime.datetime.strptime(start_date, "%Y-%m-%d").date()
    return delta.days

# 生日倒计时
def get_birthday_left():
    if birthday is None:
        print('没有设置 BIRTHDAY')
        return 0
    next_date = datetime.datetime.strptime(f"{today.year}-{birthday}", "%Y-%m-%d").date()
    if next_date < today:
        next_date = next_date.replace(year=next_date.year + 1)
    return (next_date - today).days

# 彩虹屁 接口不稳定，所以失败的话会重新调用，直到成功
def get_words():
    words = requests.get("https://api.shadiao.pro/chp")
    if words.status_code != 200:
        return get_words()
    return words.json()['data']['text']

def format_temperature(temperature):
    return math.floor(temperature)

# 随机颜色
def get_random_color():
    color = "#%06x" % random.randint(0, 0xFFFFFF)
    print(f"生成的随机颜色: {color}")  # 输出调试信息
    return color

try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取 token 失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
    exit(502)

wm = WeChatMessage(client)
weather = get_weather()
if weather is None:
    print('获取天气失败')
    exit(422)

data = {
    "city": {
        "value": city,
        "color": get_random_color()
    },
    "date": {
        "value": today.strftime('%Y年%m月%d日'),
        "color": get_random_color()
    },
    "week_day": {
        "value": get_week_day(),
        "color": get_random_color()
    },
    "weather": {
        "value": weather['weather'],
        "color": get_random_color()
    },
    "humidity": {
        "value": weather['humidity'],
        "color": get_random_color()
    },
    "wind": {
        "value": weather['wind'],
        "color": get_random_color()
    },
    "air_data": {
        "value": weather['airData'],
        "color": get_random_color()
    },
    "air_quality": {
        "value": weather['airQuality'],
        "color": get_random_color()
    },
    "temperature": {
        "value": weather['temp'],
        "color": get_random_color()
    },
    "highest": {
        "value": weather['high'],
        "color": get_random_color()
    },
    "lowest": {
        "value": weather['low'],
        "color": get_random_color()
    },
    "birthday_left": {
        "value": get_birthday_left(),
        "color": get_random_color()
    },
    "words": {
        "value": get_words(),
        "color": get_random_color()
    },
}

if __name__ == '__main__':
    count = 0
    try:
        for user_id in user_ids:
            res = wm.send_template(user_id, template_id, data)
            count += 1
    except WeChatClientException as e:
        print('微信端返回错误：%s。错误代码：%d' % (e.errmsg, e.errcode))
        exit(502)

    print("发送了" + str(count) + "条消息")
