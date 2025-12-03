// 聊天室相关功能

// 全局变量
let socket = null;
let currentUser = '';
const emojiList = ['😀', '😃', '😄', '😁', '😆', '😅', '😂', '🤣', '😊', '😇', '🙂', '🙃', '😉', '😌', '😍', '🥰', '😘', '😗', '😙', '😚', '😋', '😛', '😝', '😜', '🤪', '🤨', '🧐', '🤓', '😎', '🤩', '🥳', '😏', '😒', '😞', '😔', '😟', '😕', '🙁', '☹️', '😣', '😖', '😫', '😩', '🥺', '😢', '😭', '😤', '😠', '😡', '🤬', '🤯', '😳', '🥵', '🥶', '😱', '😨', '😰', '😥', '😓', '🤗', '🤔', '🤭', '🤫', '🤥', '😶', '😐', '😑', '😬', '🙄', '😯', '😦', '😧', '😮', '😲', '🥱', '😴', '🤤', '😪', '😵', '🤐', '🥴', '🤢', '🤮', '🤧', '😷', '🤒', '🤕', '🤑'];

// 页面加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 获取当前用户名
    currentUser = document.getElementById('current-user').textContent;
    
    // 初始化SocketIO连接
    initSocketIO();
    
    // 初始化事件监听
    initEventListeners();
    
    // 初始化Emoji面板
    initEmojiPanel();
    
    // 加载在线用户列表
    loadOnlineUsers();
});

// 初始化SocketIO连接
function initSocketIO() {
    try {
        // SocketIO会自动处理连接协议
        socket = io();
        
        // SocketIO事件处理
        socket.on('connect', function() {
            console.log('SocketIO连接已建立');
        });
        
        socket.on('message', function(message) {
            handleMessage(message);
        });
        
        socket.on('disconnect', function() {
            console.log('SocketIO连接已关闭');
            showSystemMessage('连接已断开，正在尝试重连...');
        });
        
        socket.on('connect_error', function(error) {
            console.error('SocketIO连接错误:', error);
        });
    } catch (e) {
        console.error('创建SocketIO连接失败:', e);
        // 尝试使用WebSocket作为后备方案
        initWebSocketFallback();
    }
}

// WebSocket后备实现
function initWebSocketFallback() {
    console.log('使用WebSocket后备方案');
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${wsProtocol}//${window.location.host}/ws`;
    
    try {
        socket = new WebSocket(wsUrl);
        
        socket.onopen = function() {
            console.log('WebSocket连接已建立');
        };
        
        socket.onmessage = function(event) {
            try {
                const message = JSON.parse(event.data);
                handleMessage(message);
            } catch (e) {
                console.error('解析消息错误:', e);
            }
        };
        
        socket.onclose = function() {
            console.log('WebSocket连接已关闭');
            showSystemMessage('连接已断开，正在尝试重连...');
            setTimeout(initWebSocketFallback, 3000);
        };
        
        socket.onerror = function(error) {
            console.error('WebSocket错误:', error);
        };
        
        // 重写send方法以兼容SocketIO接口
        socket.emit = function(event, data) {
            if (this.readyState === WebSocket.OPEN) {
                this.send(JSON.stringify(data));
            }
        };
    } catch (e) {
        console.error('创建WebSocket连接失败:', e);
    }
}

// 初始化事件监听
function initEventListeners() {
    const messageInput = document.getElementById('message-input');
    const sendBtn = document.getElementById('send-btn');
    const emojiBtn = document.getElementById('emoji-btn');
    const emojiPanel = document.getElementById('emoji-panel');
    
    // 确保所有必要元素都存在
    if (!messageInput || !sendBtn || !emojiBtn || !emojiPanel) {
        console.error('必要的DOM元素未找到');
        return;
    }
    
    // 监听输入框变化，启用/禁用发送按钮
    messageInput.addEventListener('input', function() {
        sendBtn.disabled = this.value.trim() === '';
        // 自动调整输入框高度
        adjustTextareaHeight(this);
    });
    
    // 监听回车键发送消息
    messageInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // 发送按钮点击事件
    sendBtn.addEventListener('click', sendMessage);
    
    // Emoji按钮点击事件
    emojiBtn.addEventListener('click', function() {
        emojiPanel.classList.toggle('show');
    });
    
    // 点击其他区域关闭Emoji面板
    document.addEventListener('click', function(e) {
        if (!emojiBtn.contains(e.target) && !emojiPanel.contains(e.target)) {
            emojiPanel.classList.remove('show');
        }
    });
    
    // @功能按钮点击事件
    const atButtons = document.querySelectorAll('.at-button');
    atButtons.forEach(button => {
        button.addEventListener('click', function() {
            const command = this.getAttribute('data-command');
            const currentValue = messageInput.value;
            // 如果输入框已有内容，在内容前添加命令，否则直接设置为命令
            messageInput.value = currentValue ? `${command} ${currentValue}` : command;
            messageInput.focus();
            // 启用发送按钮
            sendBtn.disabled = false;
            // 自动调整输入框高度
            adjustTextareaHeight(messageInput);
        });
    });
}

// 初始化Emoji面板
function initEmojiPanel() {
    const emojiPanel = document.getElementById('emoji-panel');
    
    emojiList.forEach(emoji => {
        const emojiItem = document.createElement('div');
        emojiItem.className = 'emoji-item';
        emojiItem.textContent = emoji;
        emojiItem.addEventListener('click', function() {
            const messageInput = document.getElementById('message-input');
            messageInput.value += emoji;
            messageInput.focus();
            document.getElementById('send-btn').disabled = false;
            adjustTextareaHeight(messageInput);
        });
        emojiPanel.appendChild(emojiItem);
    });
}

// 发送消息
function sendMessage() {
    const messageInput = document.getElementById('message-input');
    const content = messageInput.value.trim();
    
    if (!content || !socket) {
        return;
    }
    
    // 检查是否包含特殊命令
    const hasCommand = /@包子|@音乐一下|@电影|@天气|@新闻|@小视频/.test(content);
    
    const message = {
        type: hasCommand ? 'command' : 'message',
        message: content,
        time: new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    };
    
    // 发送消息 - 区分@消息和普通消息
    if (hasCommand) {
        // @消息不广播给所有用户，使用不同的事件类型发送
        socket.emit('private_message', message);
        
        // 如果是@包子消息，清除当前用户的AI消息引用，确保新消息获得独立响应
        if (/^@包子/.test(content)) {
            delete aiMessageRefs[currentUser];
        }
    } else {
        // 普通消息广播给所有用户
        socket.emit('message', message);
    }
    
    // 清空输入框
    messageInput.value = '';
    messageInput.style.height = 'auto';
    document.getElementById('send-btn').disabled = true;
}

// 保存AI消息的引用，用于流式更新
// 使用对象维护每个用户独立的AI消息引用，避免消息合并
let aiMessageRefs = {};

// 处理接收到的消息
function handleMessage(message) {
    console.log('收到消息:', message);
    if (message.type === 'system') {
        showSystemMessage(message.message);
    } else if (message.type === 'message') {
        // 处理AI的流式响应
        if (message.is_ai) {
            if (message.partial) {
                // 部分响应，更新现有的AI消息
                updateAIMessage(message);
            } else if (message.message.trim() !== '') {
                // 完整响应，且内容不为空时才添加新消息
                addMessageToChat(message);
            }
        } else {
            // 普通消息
            addMessageToChat(message);
        }
    } else if (message.type === 'error' || message.type === 'command') {
        addMessageToChat(message);
    }
    
    // 如果是用户加入或离开消息，刷新在线用户列表
    if (message.type === 'system' && (message.message.includes('加入了聊天室') || message.message.includes('离开了聊天室'))) {
        setTimeout(loadOnlineUsers, 100);
    }
}

// 显示系统消息
function showSystemMessage(content) {
    const chatMessages = document.getElementById('chat-messages');
    const systemMessageDiv = document.createElement('div');
    systemMessageDiv.className = 'system-message';
    systemMessageDiv.innerHTML = `<span class="system-text">${content}</span>`;
    chatMessages.appendChild(systemMessageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 添加消息到聊天区域
function addMessageToChat(message) {
    console.log('添加消息到聊天区域:', message);
    console.log('message.is_html:', message.is_html);
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    const isOwn = message.nickname === currentUser;
    
    messageDiv.className = `message-item ${isOwn ? 'own' : ''}`;
    
    // 创建头像
    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.textContent = message.nickname.charAt(0);
    
    // 创建消息内容
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    // 消息头部（昵称和时间）
    const headerDiv = document.createElement('div');
    headerDiv.className = 'message-header';
    
    const nicknameSpan = document.createElement('span');
    nicknameSpan.className = 'message-nickname';
    nicknameSpan.textContent = message.nickname;
    
    const timeSpan = document.createElement('span');
    timeSpan.className = 'message-time';
    timeSpan.textContent = message.time;
    
    headerDiv.appendChild(nicknameSpan);
    headerDiv.appendChild(timeSpan);
    
    // 消息文本
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    
    // 确保HTML内容能够正确渲染
    let shouldRenderAsHtml = message.is_html === true;
    
    // 额外检查：如果消息包含视频、音乐或天气卡片标签，也使用HTML渲染
    const htmlTags = ['<video', '<div class="music-card"', '<div class="weather-card"', '<div class="video-card"'];
    const messageLower = message.message.toLowerCase();
    
    for (const tag of htmlTags) {
        if (messageLower.includes(tag.toLowerCase())) {
            shouldRenderAsHtml = true;
            console.log('检测到HTML标签，使用innerHTML渲染:', tag);
            break;
        }
    }
    
    if (shouldRenderAsHtml) {
        console.log('使用innerHTML渲染HTML内容');
        textDiv.innerHTML = message.message;
    } else {
        console.log('使用textContent渲染文本内容');
        textDiv.textContent = message.message;
    }
    
    contentDiv.appendChild(headerDiv);
    contentDiv.appendChild(textDiv);
    
    // 组装消息项
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(contentDiv);
    
    // 如果是AI消息，为发送者保存独立的AI消息引用
    if (message.is_ai) {
        const sender = message.sender || currentUser;
        aiMessageRefs[sender] = {
            div: messageDiv,
            textDiv: textDiv,
            fullMessage: message.message
        };
    }
    
    // 添加到聊天区域
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 更新AI消息（用于流式响应）
function updateAIMessage(message) {
    const chatMessages = document.getElementById('chat-messages');
    const sender = message.sender || currentUser;
    
    // 使用发送者特定的AI消息引用
    if (aiMessageRefs[sender] && aiMessageRefs[sender].div.parentNode) {
        // 更新现有消息的文本
        aiMessageRefs[sender].textDiv.textContent += message.message;
        aiMessageRefs[sender].fullMessage += message.message;
        // 滚动到底部
        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        // 如果没有找到现有消息，添加新消息
        addMessageToChat({
            ...message,
            message: message.message
        });
    }
}

// 加载在线用户列表
function loadOnlineUsers() {
    fetch('/get_users')
        .then(response => response.json())
        .then(data => {
            updateContactList(data.users);
        })
        .catch(error => {
            console.error('加载在线用户失败:', error);
        });
}

// 更新联系人列表
function updateContactList(users) {
    const contactList = document.getElementById('contact-list');
    const onlineCountElement = document.getElementById('online-count');
    
    contactList.innerHTML = '';
    
    // 更新在线用户数显示
    if (onlineCountElement) {
        onlineCountElement.textContent = `${users.length} 人在线`;
    }
    
    // 按昵称排序
    users.sort();
    
    users.forEach(user => {
        const contactItem = document.createElement('div');
        contactItem.className = 'contact-item';
        
        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.textContent = user.charAt(0);
        
        const contactInfo = document.createElement('div');
        contactInfo.className = 'contact-info';
        
        const contactName = document.createElement('div');
        contactName.className = 'contact-name';
        contactName.textContent = user;
        
        const contactMessage = document.createElement('div');
        contactMessage.className = 'contact-message';
        contactMessage.textContent = user === currentUser ? '您' : '在线';
        
        const contactTime = document.createElement('div');
        contactTime.className = 'contact-time';
        contactTime.textContent = new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
        
        contactInfo.appendChild(contactName);
        contactInfo.appendChild(contactMessage);
        
        contactItem.appendChild(avatar);
        contactItem.appendChild(contactInfo);
        contactItem.appendChild(contactTime);
        
        // 如果是当前用户，标记为活跃
        if (user === currentUser) {
            contactItem.classList.add('active');
        }
        
        contactList.appendChild(contactItem);
    });
}

// 自动调整文本框高度
function adjustTextareaHeight(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
}

// 页面关闭时关闭SocketIO连接
window.addEventListener('beforeunload', function() {
    if (socket) {
        if (socket.disconnect) {
            socket.disconnect();
        } else if (socket.close) {
            socket.close();
        }
    }
});