import requests
import json

# 测试Open-Meteo天气API调用
# 首先需要将城市名转换为经纬度
# 使用Nominatim地理编码API将城市名转换为经纬度
def get_coordinates(city_name):
    geocoding_url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json&limit=1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(geocoding_url, headers=headers)
        data = response.json()
        if data:
            lat = float(data[0]['lat'])
            lon = float(data[0]['lon'])
            return lat, lon
        else:
            print(f"未找到城市: {city_name}")
            return None, None
    except Exception as e:
        print(f"地理编码API调用异常: {str(e)}")
        return None, None

# 获取天气数据
def get_weather(lat, lon):
    weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_probability_max,weather_code&current_weather=true&timezone=Asia/Shanghai"
    try:
        response = requests.get(weather_url)
        data = response.json()
        return data
    except Exception as e:
        print(f"天气API调用异常: {str(e)}")
        return None

# 天气代码映射
def get_weather_description(code):
    weather_codes = {
        0: "晴朗",
        1: "主要是晴天",
        2: "部分多云",
        3: "多云",
        45: "雾",
        48: "沉积雾",
        51: "小雨",
        53: "中雨",
        55: "大雨",
        56: "冻毛毛雨",
        57: "冻毛毛雨",
        61: "小雨",
        63: "中雨",
        65: "大雨",
        66: "冻雨",
        67: "冻雨",
        71: "小雪",
        73: "中雪",
        75: "大雪",
        77: "雪粒",
        80: "阵雨",
        81: "阵雨",
        82: "阵雨",
        85: "阵雪",
        86: "阵雪",
        95: "雷暴",
        96: "雷暴伴冰雹",
        99: "雷暴伴冰雹"
    }
    return weather_codes.get(code, "未知天气")

# 测试函数
city_name = "宜宾"
lat, lon = get_coordinates(city_name)
if lat and lon:
    print(f"{city_name} 的经纬度: {lat}, {lon}")
    weather_data = get_weather(lat, lon)
    if weather_data:
        print(f"天气数据: {json.dumps(weather_data, indent=2, ensure_ascii=False)}")
        
        # 解析当前天气
        current_weather = weather_data['current_weather']
        print(f"当前天气: {get_weather_description(current_weather['weather_code'])}")
        print(f"当前温度: {current_weather['temperature']}°C")
        print(f"风速: {current_weather['windspeed']} km/h")
        
        # 解析每日预报
        if 'daily' in weather_data:
            daily = weather_data['daily']
            print(f"\n今日预报:")
            print(f"最高温度: {daily['temperature_2m_max'][0]}°C")
            print(f"最低温度: {daily['temperature_2m_min'][0]}°C")
            print(f"天气: {get_weather_description(daily['weather_code'][0])}")
            print(f"降水概率: {daily['precipitation_probability_max'][0]}%")
else:
    print("无法获取城市坐标")
