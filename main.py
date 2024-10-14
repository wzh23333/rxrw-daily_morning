import datetime
from datetime import timedelta
import math
from wechatpy import WeChatClient, WeChatClientException
from wechatpy.client.api import WeChatMessage
import requests
import os
import random

# 获取当前时间并转换为东八区时间
nowtime = datetime.datetime.now(datetime.UTC) + timedelta(hours=8)
today = datetime.datetime.strptime(str(nowtime.date()), "%Y-%m-%d")

start_date = os.getenv('START_DATE')
city = os.getenv('CITY')
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

# 获取天气信息
def get_weather():
    if city is None:
        print('请设置城市')
        return None
    url = "http://autodev.openspeech.cn/csp/api/v2.1/weather?openId=aiuicus&clientType=android&sign=android&city=" + city
    res = requests.get(url).json()
    if res is None:
        return None
    weather = res['data']['list'][0]
    return weather

# 获取当前日期是星期几
def get_week_day():
    week_list = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return week_list[today.weekday()]

# 计算纪念日天数
def get_memorial_days_count():
    if start_date is None:
        return 0
    return (today - datetime.strptime(start_date, "%Y-%m-%d")).days

# 计算生日倒计时
def get_birthday_left():
    if birthday is None:
        return 0
    next = datetime.strptime(str(today.year) + "-" + birthday, "%Y-%m-%d")
    if next < nowtime:
        next = next.replace(year=next.year + 1)
    return (next - today).days

# 获取彩虹屁文字
def get_words():
    max_retries = 5
    retries = 0
    while retries < max_retries:
        words = requests.get("https://api.shadiao.pro/chp")
        if words.status_code == 200:
            return words.json()['data']['text']
        retries += 1
    return None

def format_temperature(temperature):
    return math.floor(temperature)

# 获取随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)

try:
    client = WeChatClient(app_id, app_secret)
except WeChatClientException as e:
    print('微信获取token失败，请检查 APP_ID 和 APP_SECRET，或当日调用量是否已达到微信限制。')
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
        "value": math.floor(weather['temp']),
        "color": get_random_color()
    },
    "highest": {
        "value": math.floor(weather['high']),
        "color": get_random_color()
    },
    "lowest": {
        "value": math.floor(weather['low']),
        "color": get_random_color()
    },
    "birthday_left": {
        "value": get_birthday_left(),
        "color": get_random_color()
    },
    "words": {
        "value": get_words(),
        "color": get_random_color()
    }
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
