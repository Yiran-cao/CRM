// ===== 通用工具 =====
const API_BASE = '/api';

function getToken() { return localStorage.getItem('token'); }
function getUser() {
  try { return JSON.parse(localStorage.getItem('user')); } catch(e) { return null; }
}

async function request(url, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API_BASE}${url}`, { ...options, headers });
  if (res.status === 401) {
    logout();
    throw new Error('未登录');
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(err.detail || '请求失败');
  }
  return res.json();
}

function showToast(msg, type = 'success') {
  const toast = document.getElementById('toast');
  if (!toast) return;
  toast.textContent = msg;
  toast.className = `toast ${type} show`;
  setTimeout(() => { toast.className = 'toast'; }, 3000);
}

// ===== 认证 =====
async function login(username, password) {
  const data = await fetch(`${API_BASE}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  }).then(r => {
    if (!r.ok) throw new Error('用户名或密码错误');
    return r.json();
  });
  localStorage.setItem('token', data.access_token);
  localStorage.setItem('user', JSON.stringify(data.user));
  return data;
}

async function logout() {
  try {
    const token = getToken();
    if (token) {
      await fetch(`${API_BASE}/auth/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      });
    }
  } catch (e) { /* 忽略登出接口异常，继续清理本地状态 */ }
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = '/login';
}

// ===== 页面初始化 =====
function initSidebar() {
  const user = getUser();
  if (!user) return;

  const userInfo = document.getElementById('userInfo');
  const roleTag = document.getElementById('roleTag');
  if (userInfo) {
    userInfo.querySelector('.user-name').textContent = user.name;
  }
  if (roleTag) {
    roleTag.textContent = user.role === 'admin' ? '管理员' : '经销商';
    roleTag.className = `role-tag ${user.role}`;
  }

  // 管理员显示额外菜单
  if (user.role === 'admin') {
    document.querySelectorAll('.admin-only').forEach(el => el.style.display = '');
  }

  // 高亮当前页面
  const path = window.location.pathname;
  document.querySelectorAll('.sidebar-link').forEach(link => {
    if (link.getAttribute('href') === path) {
      link.classList.add('active');
    }
  });
}

// ===== 页面加载 =====
document.addEventListener('DOMContentLoaded', () => {
  if (window.location.pathname !== '/login') {
    if (!getToken()) {
      window.location.href = '/login';
      return;
    }
    initSidebar();
  }
});

// ===== 公共工具函数 =====
function escHtml(s) {
  return s ? String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;') : '';
}

function getStageBadge(stage) {
  const names = {1:'潜在客户',2:'初步接触',3:'持续跟进',4:'成交客户',5:'忠诚客户',6:'无效客户'};
  const cats = {1:'info',2:'info',3:'success',4:'success',5:'success',6:'danger'};
  const icons = {1:'💡',2:'💬',3:'📞',4:'🤝',5:'⭐',6:'🚫'};
  const name = names[stage] || stage;
  const cat = cats[stage] || 'info';
  const icon = icons[stage] || '';
  return `<span class="stage-badge ${cat}" title="${name}">${icon} ${stage}-${name}</span>`;
}
