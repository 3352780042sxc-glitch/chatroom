import requests
import time

# 测试多个视频URL
def test_video_url(url, headers=None):
    if headers is None:
        headers = {
            'User-Agent': 'xiaoxiaoapi/1.0.0'
        }
    
    print(f"\n测试URL: {url}")
    print("=" * 60)
    
    # 测试1: 检查URL是否可访问
    try:
        response = requests.head(url, headers=headers, timeout=10)
        print(f"HEAD请求状态码: {response.status_code}")
        print(f"内容类型: {response.headers.get('Content-Type', '未知')}")
        print(f"内容长度: {response.headers.get('Content-Length', '未知')}")
        print(f"允许的源: {response.headers.get('Access-Control-Allow-Origin', '未知')}")
        print(f"服务器: {response.headers.get('Server', '未知')}")
    except Exception as e:
        print(f"HEAD请求失败: {e}")
        return False
    
    # 测试2: 尝试获取少量视频数据
    try:
        response = requests.get(url, headers=headers, timeout=10, stream=True)
        if response.status_code == 200:
            # 只读取前1024字节
            data = response.raw.read(1024)
            print(f"GET请求状态码: 200")
            print(f"成功读取前 {len(data)} 字节")
            return True
        else:
            print(f"GET请求失败，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"GET请求失败: {e}")
        return False

# 测试视频API
def test_video_api():
    api_url = "https://v2.xxapi.cn/api/meinv"
    headers = {
        'User-Agent': 'xiaoxiaoapi/1.0.0'
    }
    
    print(f"测试视频API: {api_url}")
    print("=" * 60)
    
    video_urls = []
    
    # 获取3个视频URL进行测试
    for i in range(3):
        try:
            response = requests.get(api_url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data['code'] == 200 and data['data']:
                    video_url = data['data']
                    video_urls.append(video_url)
                    print(f"获取到视频URL {i+1}: {video_url}")
                else:
                    print(f"API返回错误: {data.get('msg', '未知错误')}")
            time.sleep(1)  # 避免请求过快
        except Exception as e:
            print(f"API请求失败: {e}")
    
    # 测试获取到的视频URL
    print("\n" + "=" * 60)
    print("测试视频URL可用性:")
    print("=" * 60)
    
    for i, url in enumerate(video_urls):
        print(f"\n视频 {i+1}:")
        test_video_url(url, headers)

# 主函数
if __name__ == "__main__":
    test_video_api()