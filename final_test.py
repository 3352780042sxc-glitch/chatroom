import requests
import json
import time
import socketio

# 测试API连接
def test_api_connection():
    print("测试API连接...")
    try:
        url = "https://v2.xxapi.cn/api/meinv"
        headers = {
            'User-Agent': 'xiaoxiaoapi/1.0.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data['code'] == 200 and data['data']:
                print(f"✅ API连接成功，获取到视频URL: {data['data']}")
                return data['data']
            else:
                print(f"❌ API返回错误: {data.get('msg', '未知错误')}")
                return None
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ API连接异常: {e}")
        return None

# 测试视频URL有效性
def test_video_url(url):
    print(f"\n测试视频URL: {url}")
    try:
        headers = {
            'User-Agent': 'xiaoxiaoapi/1.0.0'
        }
        response = requests.head(url, headers=headers, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get('Content-Type', '未知')
            content_length = response.headers.get('Content-Length', '未知')
            cors = response.headers.get('Access-Control-Allow-Origin', '未知')
            print(f"✅ URL有效，状态码: 200")
            print(f"   内容类型: {content_type}")
            print(f"   内容长度: {content_length}")
            print(f"   CORS设置: {cors}")
            return True
        else:
            print(f"❌ URL无效，状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ URL访问异常: {e}")
        return False

# 测试聊天室服务器
def test_chat_server():
    print("\n测试聊天室服务器连接...")
    try:
        # 测试登录接口
        login_response = requests.post('http://localhost:5000/login', 
                                     data={'username': 'testuser', 'password': 'testpassword'}, 
                                     timeout=5)
        if login_response.status_code == 302:
            print("✅ 登录接口正常")
            return True
        else:
            print(f"❌ 登录接口异常，状态码: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 服务器连接失败: {e}")
        return False

# 主测试函数
def main():
    print("=" * 60)
    print("@小视频功能最终测试")
    print("=" * 60)
    
    # 1. 测试API连接
    video_url = test_api_connection()
    
    # 2. 测试视频URL有效性
    if video_url:
        test_video_url(video_url)
    
    # 3. 测试聊天室服务器
    test_chat_server()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("您可以在浏览器中访问 http://localhost:5000 并输入@小视频来测试功能")
    print("=" * 60)

if __name__ == "__main__":
    main()