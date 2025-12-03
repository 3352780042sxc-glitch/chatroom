import requests
import json

# 测试@小视频功能的API调用
def test_video_api():
    print("测试@小视频API...")
    
    try:
        # 调用API获取视频数据
        api_url = "https://api.qqsuu.cn/api/dm-woman?apiKey=2bd43ef694f249f03d91c012715b1fa3"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(api_url, headers=headers)
        print(f"API响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("API响应数据:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
            
            # 检查响应数据结构
            if data['code'] == 200 and data['data']['newslist']:
                print("\n✅ API调用成功！")
                print(f"📋 共获取到 {len(data['data']['newslist'])} 个视频项目")
                
                # 打印第一个视频的详细信息
                first_video = data['data']['newslist'][0]
                print("\n第一个视频信息:")
                print(f"标题: {first_video['title']}")
                print(f"来源: {first_video['source']}")
                print(f"发布时间: {first_video['ctime']}")
                print(f"描述: {first_video['description']}")
                print(f"视频URL: {first_video['url']}")
                return True
            else:
                print(f"❌ API返回错误: {data.get('msg', '未知错误')}")
                return False
        else:
            print(f"❌ API请求失败，状态码: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API调用异常: {str(e)}")
        return False

if __name__ == "__main__":
    test_video_api()