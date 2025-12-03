import requests
import json

# 加载配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 测试天气API调用
city_name = "宜宾"
api_url = f"https://v2.xxapi.cn/api/weatherDetails?city={city_name}&key=xiaoxiaoapi"
headers = {
    'User-Agent': 'xiaoxiaoapi/1.0.0'
}

try:
    response = requests.get(api_url, headers=headers)
    print(f"API调用状态码: {response.status_code}")
    print(f"API响应内容: {response.text}")
    
    data = response.json()
    print(f"API响应JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data['code'] == 200 and data['data']:
        print("天气查询成功!")
        weather_data = data['data']
        print(f"城市: {weather_data['city']}")
        today_weather = weather_data['data'][0]
        print(f"日期: {today_weather['date']} {today_weather['day']}")
        print(f"天气: {today_weather['wea']}")
        print(f"温度范围: {today_weather['low_temp']}°C - {today_weather['high_temp']}°C")
    else:
        print(f"天气查询失败: {data.get('msg', '未知错误')}")
except Exception as e:
    print(f"API调用异常: {str(e)}")
