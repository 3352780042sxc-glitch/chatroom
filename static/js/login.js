// 登录页面相关功能

// 页面加载完成后执行
window.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const loginBtn = document.getElementById('login-btn');
    const nicknameInput = document.getElementById('nickname');
    const passwordInput = document.getElementById('password');
    const serverSelect = document.getElementById('server_url');
    const messageDiv = document.getElementById('message');
    
    // 为登录按钮添加点击事件
    loginBtn.addEventListener('click', handleLogin);
    
    // 为输入框添加回车键登录功能
    nicknameInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            passwordInput.focus();
        }
    });
    
    passwordInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            serverSelect.focus();
        }
    });
    
    serverSelect.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleLogin();
        }
    });
    
    // 设置密码输入框占位符
    passwordInput.placeholder = '请输入密码';
});

// 处理登录逻辑
function handleLogin() {
    const nickname = document.getElementById('nickname').value.trim();
    const password = document.getElementById('password').value;
    const server_url = document.getElementById('server_url').value;
    
    // 表单验证
    if (!validateForm(nickname, password, server_url)) {
        return;
    }
    
    // 显示加载状态
    const loginBtn = document.getElementById('login-btn');
    const originalText = loginBtn.textContent;
    loginBtn.textContent = '登录中...';
    loginBtn.disabled = true;
    
    // 发送登录请求
    fetch('/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            nickname: nickname,
            password: password,
            server_url: server_url
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('网络响应错误');
        }
        return response.json();
    })
    .then(data => {
        // 恢复按钮状态
        loginBtn.textContent = originalText;
        loginBtn.disabled = false;
        
        if (data.status === 'success') {
            showMessage(data.message, 'success');
            // 跳转到聊天室页面
            setTimeout(() => {
                window.location.href = '/chat';
            }, 1000);
        } else {
            showMessage(data.message, 'error');
        }
    })
    .catch(error => {
        // 恢复按钮状态
        loginBtn.textContent = originalText;
        loginBtn.disabled = false;
        
        showMessage('登录失败，请稍后重试', 'error');
        console.error('登录错误:', error);
    });
}

// 表单验证
function validateForm(nickname, password, server_url) {
    // 检查昵称
    if (!nickname) {
        showMessage('请输入昵称', 'error');
        return false;
    }
    
    if (nickname.length < 2 || nickname.length > 20) {
        showMessage('昵称长度应在2-20个字符之间', 'error');
        return false;
    }
    
    // 检查密码
    if (!password) {
        showMessage('请输入密码', 'error');
        return false;
    }
    
    // 检查服务器选择
    if (!server_url) {
        showMessage('请选择服务器地址', 'error');
        return false;
    }
    
    return true;
}

// 显示消息提示
function showMessage(message, type) {
    const messageDiv = document.getElementById('message');
    messageDiv.textContent = message;
    messageDiv.className = 'message';
    messageDiv.classList.add(type);
    
    // 添加简单的动画效果
    messageDiv.style.opacity = '0';
    messageDiv.style.transition = 'opacity 0.3s ease';
    
    setTimeout(() => {
        messageDiv.style.opacity = '1';
    }, 10);
    
    // 3秒后清除消息
    setTimeout(() => {
        messageDiv.style.opacity = '0';
        setTimeout(() => {
            messageDiv.textContent = '';
            messageDiv.className = 'message';
        }, 300);
    }, 3000);
}