import requests

# 测试天气API
city_name = "滕州市"
api_key = "89b896c4a9e771e7"
api_url = f"https://v2.xxapi.cn/api/weather?city={city_name}&key={api_key}"
headers = {
    'User-Agent': 'xiaoxiaoapi/1.0.0'
}

print(f"请求URL: {api_url}")

try:
    response = requests.get(api_url, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    # 解析JSON
    data = response.json()
    print(f"\n解析后的数据:")
    print(f"状态码: {data.get('code')}")
    print(f"消息: {data.get('msg')}")
    
    if data.get('code') == 200 and data.get('data'):
        weather_data = data['data']
        print(f"城市: {weather_data.get('city')}")
        print(f"预报列表长度: {len(weather_data.get('data', []))}")
        
        # 打印每日预报
        for i, forecast in enumerate(weather_data.get('data', [])):
            print(f"\n第{i+1}天预报:")
            print(f"日期: {forecast.get('date')}")
            print(f"天气: {forecast.get('weather')}")
            print(f"温度: {forecast.get('temperature')}")
            print(f"风向: {forecast.get('wind')}")
            print(f"空气质量: {forecast.get('air_quality')}")
    
except Exception as e:
    print(f"请求错误: {e}")
