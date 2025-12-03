import requests
import json

# 测试音乐API调用
song_name = "热门歌曲"
api_url = f"https://v2.xxapi.cn/api/kugousearch?music={song_name}"
headers = {
    'User-Agent': 'xiaoxiaoapi/1.0.0'
}

try:
    response = requests.get(api_url, headers=headers)
    print(f"API调用状态码: {response.status_code}")
    print(f"API响应内容: {response.text[:500]}...")  # 只打印前500个字符
    
    data = response.json()
    print(f"API响应JSON: {json.dumps(data, indent=2, ensure_ascii=False)}")
    
    if data['code'] == 200 and data['data']:
        print("音乐查询成功!")
        print(f"找到 {len(data['data'])} 首歌曲")
        # 打印第一首歌曲的信息
        if data['data']:
            first_song = data['data'][0]
            print(f"歌曲名: {first_song['song']}")
            print(f"歌手: {first_song['singer']}")
            print(f"URL: {first_song['url']}")
    else:
        print(f"音乐查询失败: {data.get('msg', '未知错误')}")
except Exception as e:
    print(f"API调用异常: {str(e)}")
