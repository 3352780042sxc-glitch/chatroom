import requests

# 测试小视频API
api_url = "https://v2.xxapi.cn/api/meinv"
headers = {
    'User-Agent': 'xiaoxiaoapi/1.0.0'
}

try:
    response = requests.get(api_url, headers=headers)
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.text}")
    
    data = response.json()
    if data['code'] == 200 and data['data']:
        print(f"\n测试成功！视频URL: {data['data']}")
    else:
        print(f"\n测试失败！API返回错误: {data.get('msg', '未知错误')}")
        
except Exception as e:
    print(f"\n测试失败！发生异常: {e}")