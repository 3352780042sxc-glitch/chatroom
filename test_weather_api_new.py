import requests
import urllib.parse

# 测试新的天气API
def test_weather_api():
    city_name = '枣庄滕州'
    encoded_city = urllib.parse.quote(city_name)
    api_key = "89b896c4a9e771e7"
    api_url = f"https://v2.xxapi.cn/api/weather?city={encoded_city}&key={api_key}"
    headers = {
        'User-Agent': 'xiaoxiaoapi/1.0.0'
    }
    
    try:
        response = requests.get(api_url, headers=headers)
        print(f"状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        data = response.json()
        print(f"\n解析后的数据:")
        print(f"状态码: {data.get('code')}")
        print(f"消息: {data.get('msg')}")
        
        if data.get('code') == 200 and data.get('data'):
            weather_data = data['data']
            print(f"城市: {weather_data.get('city')}")
            print(f"天气预报数据:")
            
            forecast_list = weather_data.get('data', [])
            for forecast in forecast_list:
                print(f"日期: {forecast.get('date')}")
                print(f"天气: {forecast.get('weather')}")
                print(f"温度: {forecast.get('temperature')}")
                print(f"风向: {forecast.get('wind')}")
                print(f"空气质量: {forecast.get('air_quality')}")
                print("-" * 30)
            
        return True
    except Exception as e:
        print(f"错误: {str(e)}")
        return False

if __name__ == "__main__":
    print("测试天气API")
    print("=" * 50)
    test_weather_api()
