from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from flask_socketio import SocketIO, emit, join_room, leave_room
import json
import os
import requests
import threading
import random
from datetime import datetime

app = Flask(__name__)

# 加载配置
with open('config.json', 'r', encoding='utf-8') as f:
    config = json.load(f)

# 设置应用密钥
app.config['SECRET_KEY'] = config['secret_key']

# 初始化SocketIO
socketio = SocketIO(app, cors_allowed_origins="*")

# 用户会话映射
user_sessions = {}

# 获取当前时间格式化字符串
def get_current_time():
    return datetime.now().strftime('%H:%M')

# 登录页面
@app.route('/')
def login():
    return render_template('login.html', servers=config['servers'])

# 登录验证
@app.route('/login', methods=['POST'])
def do_login():
    data = request.get_json()
    nickname = data.get('nickname', '')
    password = data.get('password', '')
    server_url = data.get('server_url', '')
    
    # 验证输入
    if not nickname or not password or not server_url:
        return jsonify({'status': 'error', 'message': '请填写所有字段'})
    
    # 验证密码
    if password != config['fixed_password']:
        return jsonify({'status': 'error', 'message': '密码错误'})
    
    # 验证服务器地址
    valid_servers = [s['url'] for s in config['servers']]
    if server_url not in valid_servers:
        return jsonify({'status': 'error', 'message': '无效的服务器地址'})
    
    # 保存用户信息到session
    session['nickname'] = nickname
    session['server_url'] = server_url
    
    return jsonify({'status': 'success', 'message': '登录成功'})

# 聊天室页面
@app.route('/chat')
def chat():
    if 'nickname' not in session:
        return redirect(url_for('login'))
    return render_template('chat.html', nickname=session['nickname'])

# SocketIO事件处理
@socketio.on('connect')
def handle_connect():
    # 获取用户信息（注意：在实际生产环境中应该有更好的认证机制）
    if 'nickname' in session:
        nickname = session['nickname']
        # 将会话ID与用户昵称关联
        user_sessions[request.sid] = nickname
        
        # 加入默认聊天室
        join_room('public')
        
        # 广播用户上线消息
        welcome_msg = {
            'type': 'system',
            'message': f'{nickname} 加入了聊天室',
            'time': get_current_time(),
            'nickname': '系统'
        }
        socketio.emit('message', welcome_msg, room='public')
    else:
        # 未登录用户拒绝连接
        return False

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in user_sessions:
        nickname = user_sessions[request.sid]
        # 移除会话
        del user_sessions[request.sid]
        # 广播用户下线消息
        leave_msg = {
            'type': 'system',
            'message': f'{nickname} 离开了聊天室',
            'time': get_current_time(),
            'nickname': '系统'
        }
        socketio.emit('message', leave_msg, room='public')

@socketio.on('message')
def handle_message(data):
    if request.sid in user_sessions:
        nickname = user_sessions[request.sid]
        
        # 创建一个新的消息对象，保留所有原始属性
        full_message = data.copy()
        
        # 设置消息时间和发送者
        full_message['time'] = get_current_time()
        full_message['nickname'] = nickname
        
        # 确保必要的属性存在
        full_message.setdefault('is_html', False)
        full_message.setdefault('is_ai', False)
        full_message.setdefault('partial', False)
        full_message.setdefault('sender', '')
        
        # 广播消息到公共聊天室
        socketio.emit('message', full_message, room='public')

@socketio.on('private_message')
def handle_private_message(msg_data):
    if request.sid in user_sessions:
        nickname = user_sessions[request.sid]
        # 处理@命令
        if msg_data.get('type') == 'command' or '@' in msg_data.get('message', ''):
            handle_command(msg_data)

# 广播消息函数（保留接口兼容）
def broadcast(message):
    socketio.emit('message', message, room='public')

# 处理特殊命令
def handle_command(msg_data):
    command = msg_data.get('message', '')
    response = {
        'type': 'system',
        'time': get_current_time(),
        'nickname': '系统'
    }
    
    if '@包子' in command:
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        # 提取用户的问题（去掉@包子前缀）
        user_question = command.replace('@包子', '').strip()
        if not user_question:
            user_question = '你好，我想和你聊天'
        
        # 获取当前用户昵称
        user_nickname = session.get('nickname', '用户')
        
        # 启动一个线程来处理AI请求，避免阻塞SocketIO事件循环
        threading.Thread(target=call_ai_api, args=(user_question, request.sid, user_nickname)).start()
    elif '@电影' in command:
        # 处理@电影命令
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        # 提取电影URL
        url_part = command.split('@电影')[-1].strip()
        if url_part:
            # 构建解析后的URL
            parsed_url = f"https://jx.m3u8.tv/jiexi/?url={url_part}"
            # 创建包含iframe的HTML消息
            iframe_html = f'<iframe src="{parsed_url}" width="400" height="400" frameborder="0" allowfullscreen></iframe>'
            # 创建普通消息对象（不是系统消息）
            movie_response = {
                'type': 'message',
                'message': iframe_html,
                'time': get_current_time(),
                'nickname': '电影助手',
                'is_html': True  # 添加标记，表示这是HTML内容
            }
            # 发送响应
            socketio.emit('message', movie_response, room='public')
        else:
            # 如果没有提供URL，发送系统错误消息
            error_response = {
                'type': 'system',
                'message': '请输入@电影 [url] 格式的命令',
                'time': get_current_time(),
                'nickname': '系统'
            }
            socketio.emit('message', error_response, room=request.sid)
    elif '@天气' in command:
        # 处理@天气命令
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        # 提取城市名
        city_name = command.split('@天气')[-1].strip()
        if not city_name:
            city_name = '滕州市'  # 默认城市
        
        try:
            # 调用天气API获取数据
            api_url = f"https://v2.xxapi.cn/api/weather?city={city_name}&key=89b896c4a9e771e7"
            headers = {
                'User-Agent': 'xiaoxiaoapi/1.0.0'
            }
            response = requests.get(api_url, headers=headers)
            data = response.json()
            
            if data['code'] == 200 and data['data']:
                # 解析天气数据
                weather_data = data['data']
                city = weather_data['city']
                forecast_list = weather_data['data']
                
                # 构建天气卡片HTML
                weather_card_html = f'''<div class="weather-card">
                    <div class="weather-card-header">
                        <h3 class="weather-city">{city} 天气预报</h3>
                    </div>
                    <div class="weather-forecast-list">'''
                
                # 添加每日天气预报
                for forecast in forecast_list:
                    weather_card_html += f'''<div class="weather-forecast-item">
                        <div class="forecast-date">{forecast['date']}</div>
                        <div class="forecast-weather">{forecast['weather']}</div>
                        <div class="forecast-temperature">{forecast['temperature']}</div>
                        <div class="forecast-wind">{forecast['wind']}</div>
                        <div class="forecast-air-quality">空气质量：{forecast['air_quality']}</div>
                    </div>'''
                
                weather_card_html += '''</div>
                </div>'''
                
                # 创建天气响应消息
                weather_response = {
                    'type': 'message',
                    'message': weather_card_html,
                    'time': get_current_time(),
                    'nickname': '天气助手',
                    'is_html': True
                }
                
                # 发送天气信息到公共聊天室
                socketio.emit('message', weather_response, room='public')
            else:
                # API返回错误
                error_response = {
                    'type': 'system',
                    'message': f'天气查询失败：{data.get("msg", "未知错误")}',
                    'time': get_current_time(),
                    'nickname': '系统'
                }
                socketio.emit('message', error_response, room=request.sid)
                print(f"天气API返回错误: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            # 处理异常
            error_response = {
                'type': 'system',
                'message': f'天气查询失败：{str(e)}',
                'time': get_current_time(),
                'nickname': '系统'
            }
            socketio.emit('message', error_response, room=request.sid)
            print(f"天气API调用错误: {e}")
            
    elif '@音乐一下' in command:
        # 处理@音乐一下命令
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        # 提取歌曲名
        song_name = command.split('@音乐一下')[-1].strip()
        if song_name:
            # 调用音乐API获取数据
            try:
                api_url = f"https://v2.xxapi.cn/api/kugousearch?music={song_name}"
                headers = {
                    'User-Agent': 'xiaoxiaoapi/1.0.0'
                }
                response = requests.get(api_url, headers=headers)
                data = response.json()
                
                # 默认可爱、温柔风格的封面图片列表
                default_covers = [
                    'https://img.lovepik.com/photo/40158/2419.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/7246.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/2780.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/3942.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/4878.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/2594.jpg_wh860.jpg'
                ]
                
                if data['code'] == 200 and data['data']:
                    # 查找有效的歌曲URL
                    valid_song = None
                    for song in data['data']:
                        try:
                            # 验证音乐URL是否可访问
                            audio_response = requests.head(song['url'], timeout=3)
                            if audio_response.status_code == 200:
                                valid_song = song
                                break
                        except:
                            # 如果URL不可访问，继续尝试下一首
                            continue
                    
                    if not valid_song:
                        # 没有找到有效的歌曲URL
                        error_response = {
                            'type': 'system',
                            'message': '未找到可播放的音乐资源，请稍后重试',
                            'time': get_current_time(),
                            'nickname': '系统'
                        }
                        socketio.emit('message', error_response, room=request.sid)
                        return
                    
                    song_data = valid_song
                    
                    # 检查歌曲封面是否为空或无效，若为空则随机选择一张默认封面
                    cover_url = song_data['image']
                    if not cover_url or cover_url.strip() == '':
                        cover_url = random.choice(default_covers)
                    
                    # 构建音乐卡片HTML，添加音频错误处理
                    music_card_html = f'''<div class="music-card">
                        <div class="music-card-header">
                            <img class="music-cover" src="{cover_url}" alt="{song_data['song']} 封面" onerror="this.onerror=null;this.src='/static/images/user-avatar.svg';">
                            <div class="music-info">
                                <div class="music-title">{song_data['song']}</div>
                                <div class="music-singer">{song_data['singer']}</div>
                            </div>
                        </div>
                        <div class="music-card-player">
                            <audio controls class="music-audio" onerror="this.onerror=null;alert('音频播放失败，请尝试其他歌曲');">
                                <source src="{song_data['url']}" type="audio/mpeg">
                                您的浏览器不支持音频播放
                             </audio>
                        </div>
                    </div>'''
                    
                    # 创建普通消息对象
                    music_response = {
                        'type': 'message',
                        'message': music_card_html,
                        'time': get_current_time(),
                        'nickname': '音乐助手',
                        'is_html': True
                    }
                    # 发送响应
                    socketio.emit('message', music_response, room='public')
                else:
                    # API返回错误
                    error_response = {
                        'type': 'system',
                        'message': '未找到相关音乐，请尝试其他关键词',
                        'time': get_current_time(),
                        'nickname': '系统'
                    }
                    socketio.emit('message', error_response, room=request.sid)
                    
            except Exception as e:
                # 处理异常
                error_response = {
                    'type': 'system',
                    'message': '音乐搜索失败，请稍后重试',
                    'time': get_current_time(),
                    'nickname': '系统'
                }
                socketio.emit('message', error_response, room=request.sid)
                print(f"音乐API调用错误: {e}")
        else:
            # 如果没有提供歌曲名，随机播放一首歌
            try:
                # 使用默认关键词搜索热门歌曲
                default_keywords = ['热门歌曲', '流行音乐', '经典歌曲', '我用什么把你留住', '孤勇者', '起风了']
                random_keyword = random.choice(default_keywords)
                
                # 默认可爱、温柔风格的封面图片列表
                default_covers = [
                    'https://img.lovepik.com/photo/40158/2419.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/7246.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/2780.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/3942.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/4878.jpg_wh860.jpg',
                    'https://img.lovepik.com/photo/40158/2594.jpg_wh860.jpg'
                ]
                
                # 记录API调用信息
                print(f"[DEBUG] 调用音乐API，关键词: {random_keyword}")
                
                api_url = f"https://v2.xxapi.cn/api/kugousearch?music={random_keyword}"
                headers = {
                    'User-Agent': 'xiaoxiaoapi/1.0.0'
                }
                response = requests.get(api_url, headers=headers)
                
                # 记录API响应状态
                print(f"[DEBUG] API响应状态码: {response.status_code}")
                print(f"[DEBUG] API响应内容: {response.text[:200]}...")  # 只打印前200个字符
                
                data = response.json()
                
                if data['code'] == 200 and data['data']:
                    # 查找有效的歌曲URL
                    valid_songs = []
                    for song in data['data']:
                        try:
                            # 验证音乐URL是否可访问
                            audio_response = requests.head(song['url'], timeout=3)
                            if audio_response.status_code == 200:
                                valid_songs.append(song)
                        except:
                            # 如果URL不可访问，跳过
                            continue
                    
                    if not valid_songs:
                        # 没有找到有效的歌曲URL
                        error_response = {
                            'type': 'system',
                            'message': '未找到可播放的音乐资源，请稍后重试',
                            'time': get_current_time(),
                            'nickname': '系统'
                        }
                        socketio.emit('message', error_response, room=request.sid)
                        return
                    
                    # 随机选择一首有效的歌曲
                    song_data = random.choice(valid_songs)
                    
                    # 检查歌曲封面是否为空或无效，若为空则随机选择一张默认封面
                    cover_url = song_data['image']
                    if not cover_url or cover_url.strip() == '':
                        cover_url = random.choice(default_covers)
                    
                    # 构建音乐卡片HTML，添加音频错误处理
                    music_card_html = f'''<div class="music-card">
                        <div class="music-card-header">
                            <img class="music-cover" src="{cover_url}" alt="{song_data['song']} 封面" onerror="this.onerror=null;this.src='/static/images/user-avatar.svg';">
                            <div class="music-info">
                                <div class="music-title">{song_data['song']}</div>
                                <div class="music-singer">{song_data['singer']}</div>
                            </div>
                        </div>
                        <div class="music-card-player">
                            <audio controls class="music-audio" onerror="this.onerror=null;alert('音频播放失败，请尝试其他歌曲');">
                                <source src="{song_data['url']}" type="audio/mpeg">
                                您的浏览器不支持音频播放
                            </audio>
                        </div>
                    </div>'''
                    
                    # 创建普通消息对象
                    music_response = {
                        'type': 'message',
                        'message': music_card_html,
                        'time': get_current_time(),
                        'nickname': '音乐助手',
                        'is_html': True
                    }
                    # 发送响应
                    socketio.emit('message', music_response, room='public')
                else:
                    # API返回错误
                    error_response = {
                        'type': 'system',
                        'message': '获取音乐失败，请稍后重试',
                        'time': get_current_time(),
                        'nickname': '系统'
                    }
                    socketio.emit('message', error_response, room=request.sid)
                    
            except Exception as e:
                # 处理异常
                error_response = {
                    'type': 'system',
                    'message': '音乐播放失败，请稍后重试',
                    'time': get_current_time(),
                    'nickname': '系统'
                }
                socketio.emit('message', error_response, room=request.sid)
                print(f"音乐随机播放错误: {e}")
    elif '@小视频' in command:
        # 处理@小视频命令
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        try:
            # 调用小视频API获取数据
            api_url = "https://v2.xxapi.cn/api/meinv"
            headers = {
                'User-Agent': 'xiaoxiaoapi/1.0.0'
            }
            response = requests.get(api_url, headers=headers)
            data = response.json()
            
            if data['code'] == 200 and 'data' in data:
                # 获取视频URL
                video_url = data['data']
                
                # 构建视频卡片HTML
                video_card_html = f'''<div class="video-card">
                    <div class="video-container">
                        <video width="100%" controls="controls" autoplay="autoplay" playsinline="playsinline" preload="auto">
                            <source src="{video_url}" type="video/mp4">
                            您的浏览器不支持HTML5视频播放
                        </video>
                    </div>
                </div>'''
                
                # 创建视频响应消息
                video_response = {
                    'type': 'message',
                    'message': video_card_html,
                    'time': get_current_time(),
                    'nickname': '小视频助手',
                    'is_html': True
                }
                
                # 发送视频信息到公共聊天室
                socketio.emit('message', video_response, room='public')
            else:
                # API返回错误
                error_response = {
                    'type': 'system',
                    'message': f'小视频获取失败：{data.get("msg", "未知错误")}',
                    'time': get_current_time(),
                    'nickname': '系统'
                }
                socketio.emit('message', error_response, room=request.sid)
                print(f"小视频API返回错误: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            # 处理异常
            error_response = {
                'type': 'system',
                'message': f'小视频获取失败：{str(e)}',
                'time': get_current_time(),
                'nickname': '系统'
            }
            socketio.emit('message', error_response, room=request.sid)
            print(f"小视频API调用错误: {e}")
    elif '@新闻' in command:
        # 处理@新闻命令
        # 首先将用户的消息发送到聊天记录中（只发送给提问者自己）
        user_message = {
            'type': 'message',
            'message': command,
            'time': get_current_time(),
            'nickname': session.get('nickname', '用户')
        }
        socketio.emit('message', user_message, room=request.sid)
        
        try:
            # 调用新闻API获取数据
            api_url = "https://api.qqsuu.cn/api/dm-woman?apiKey=2bd43ef694f249f03d91c012715b1fa3"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(api_url, headers=headers)
            data = response.json()
            
            if data['code'] == 200 and data['data']['newslist']:
                # 构建新闻列表HTML
                news_items_html = ""
                for news in data['data']['newslist'][:5]:  # 显示前5条新闻
                    news_items_html += f'''<div class="news-item">
                        <div class="news-header">
                            <h4 class="news-title">{news['title']}</h4>
                            <span class="news-source">{news['source']} · {news['ctime']}</span>
                        </div>
                        <p class="news-description">{news['description']}</p>
                        <a href="{news['url']}" class="news-link" target="_blank" rel="noopener noreferrer">阅读全文</a>
                    </div>'''
                
                # 构建新闻卡片HTML
                news_card_html = f'''<div class="news-card">
                    <div class="news-card-header">
                        <h3 class="news-card-title">最新新闻</h3>
                        <span class="news-count">共 {len(data['data']['newslist'])} 条</span>
                    </div>
                    <div class="news-list">
                        {news_items_html}
                    </div>
                </div>'''
                
                # 创建新闻响应消息
                news_response = {
                    'type': 'message',
                    'message': news_card_html,
                    'time': get_current_time(),
                    'nickname': '新闻助手',
                    'is_html': True
                }
                
                # 发送新闻信息到公共聊天室
                socketio.emit('message', news_response, room='public')
            else:
                # API返回错误
                error_response = {
                    'type': 'system',
                    'message': f'新闻获取失败：{data.get("msg", "未知错误")}',
                    'time': get_current_time(),
                    'nickname': '系统'
                }
                socketio.emit('message', error_response, room=request.sid)
                print(f"新闻API返回错误: {data.get('msg', '未知错误')}")
                
        except Exception as e:
            # 处理异常
            error_response = {
                'type': 'system',
                'message': f'新闻获取失败：{str(e)}',
                'time': get_current_time(),
                'nickname': '系统'
            }
            socketio.emit('message', error_response, room=request.sid)
            print(f"新闻API调用错误: {e}")
    elif '@天气' in command:
        response['message'] = '该功能正在建设中，敬请期待！'
        socketio.emit('message', response, room=request.sid)
    else:
        response['message'] = '未知命令'
        socketio.emit('message', response, room=request.sid)

# 调用AI API
# 注意：这里使用了SSE格式，但在SocketIO环境中，我们会将响应拆分为多个消息发送
def call_ai_api(question, sid, user_nickname):
    api_key = "sk-qnhvpfxfxwmcfqywwjmqravexflvuneiqdumqcwgeojpilyr"
    model = "Qwen/Qwen2.5-7B-Instruct"
    api_url = "https://api.siliconflow.cn/v1/chat/completions"
    
    try:
        # 准备请求数据
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是一个名为'包子'的智能助手，友好且乐于助人。"},
                {"role": "user", "content": question}
            ],
            "temperature": 0.7,
            "max_tokens": 1024,
            "stream": True  # 使用流式响应
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        # 发送请求
        with requests.post(api_url, headers=headers, json=payload, stream=True) as response:
            response.raise_for_status()
            
            # 处理流式响应
            first_chunk = True
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    # 跳过非数据行
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            # 流式响应结束，不需要发送空消息
                            break
                        try:
                            data = json.loads(data_str)
                            if 'choices' in data and data['choices']:
                                delta = data['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    content = delta['content']
                                    
                                    # 在第一个响应块添加@用户昵称
                                    if first_chunk:
                                        content = f"@{user_nickname}，{content}"
                                        first_chunk = False
                                    
                                    # 通过SocketIO发送部分响应，只发送给提问者
                                    socketio.emit('message', {
                                        'type': 'message',
                                        'message': content,
                                        'time': get_current_time(),
                                        'nickname': '包子',
                                        'is_ai': True,
                                        'partial': True,  # 标记为部分响应
                                        'sender': user_nickname  # 标记发送者，用于客户端区分不同用户的AI回复
                                    }, room=sid)
                        except json.JSONDecodeError:
                            continue
    
    except requests.exceptions.RequestException as e:
        # 发送错误信息
        socketio.emit('message', {
            'type': 'system',
            'message': f'抱歉，AI服务暂时不可用：{str(e)}',
            'time': get_current_time(),
            'nickname': '系统'
        }, room=sid)
    except Exception as e:
        # 发送其他错误信息
        socketio.emit('message', {
            'type': 'system',
            'message': f'处理请求时发生错误：{str(e)}',
            'time': get_current_time(),
            'nickname': '系统'
        }, room=sid)

# 退出登录
@app.route('/logout')
def logout():
    session.pop('nickname', None)
    session.pop('server_url', None)
    return redirect(url_for('login'))

# 获取在线用户列表
@app.route('/get_users')
def get_users():
    users = list(user_sessions.values())
    return jsonify({'users': users})

# 历史记录接口（预留）
@app.route('/history')
def history():
    return jsonify({'status': 'info', 'message': '历史记录功能正在建设中'})

if __name__ == '__main__':
    port = config.get('server_port', 5000)
    print(f'服务器启动在 http://localhost:{port}')
    # 使用SocketIO的run方法启动服务器
    socketio.run(app, host='0.0.0.0', port=port, debug=True)