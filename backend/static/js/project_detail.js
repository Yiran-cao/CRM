// ===== 项目详情页 JS =====
const STAGE_NAMES = {
  1:'潜在客户',2:'初步接触',3:'持续跟进',
  4:'成交客户',5:'忠诚客户',6:'无效客户'
};

let projectId = null;
let isAdmin = false;

document.addEventListener('DOMContentLoaded', async () => {
  const match = window.location.pathname.match(/^\/projects\/(\d+)$/);
  if (!match) { window.location.href = '/projects'; return; }
  projectId = parseInt(match[1]);

  const user = getUser();
  isAdmin = user && user.role === 'admin';

  try {
    const p = await request(`/projects/${projectId}`);
    renderDetail(p);
  } catch (err) {
    showToast(err.message, 'error');
  }
});

function renderDetail(p) {
  document.getElementById('detailTitle').textContent = `单据详情 #${p.id}`;

  // 状态标签
  const status = getStatusInfo(p.stage);
  const statusEl = document.getElementById('detailStatus');
  statusEl.textContent = status.text;
  statusEl.className = `detail-status ${status.cls}`;

  // 编辑按钮：仅经销商（管理员只读）
  if (!isAdmin) {
    document.getElementById('detailEditBtn').style.display = '';
  }

  // 基础信息两列
  const dept = p.decision_makers && p.decision_makers.length ? p.decision_makers[0].department_name : '--';
  const mainMaker = p.decision_makers && p.decision_makers.length ? p.decision_makers[0] : null;
  const mainContact = mainMaker ? mainMaker.contact_info : '--';

  document.getElementById('detailInfo').innerHTML = `
    <div class="info-item"><span class="info-label">客户名称</span><span class="info-value">${escHtml(p.customer_name)}</span></div>
    <div class="info-item"><span class="info-label">省份</span><span class="info-value">${escHtml(p.province)}</span></div>
    <div class="info-item"><span class="info-label">地区</span><span class="info-value">${escHtml(p.city)}</span></div>
    <div class="info-item"><span class="info-label">产品</span><span class="info-value">${escHtml(p.product)}</span></div>
    <div class="info-item"><span class="info-label">阶段</span><span class="info-value">${getStageBadge(p.stage)}</span></div>
    <div class="info-item"><span class="info-label">预算(万元)</span><span class="info-value">${(p.budget || 0).toFixed(2)}</span></div>
    <div class="info-item"><span class="info-label">创建人</span><span class="info-value">${escHtml(p.dealer_name || '--')}</span></div>
    <div class="info-item"><span class="info-label">科室名称</span><span class="info-value">${escHtml(dept)}</span></div>
    <div class="info-item"><span class="info-label">负责人姓名</span><span class="info-value">${escHtml(mainMaker ? mainMaker.contact_name : '--')}</span></div>
    <div class="info-item"><span class="info-label">负责人电话/微信</span><span class="info-value">${escHtml(maskContact(mainContact))}</span></div>
    <div class="info-item"><span class="info-label">创建时间</span><span class="info-value">${formatDate(p.created_at)}</span></div>
    <div class="info-item"><span class="info-label">备注</span><span class="info-value">${escHtml(p.remark || '--')}</span></div>
    <div class="info-item info-full"><span class="info-label">最后更新</span><span class="info-value">${formatDate(p.updated_at)}</span></div>
  `;

  // 竞争对手及障碍
  const competitor = p.competitor_info || '';
  if (competitor) {
    document.getElementById('detailInfo').innerHTML += `
      <div class="info-item info-full"><span class="info-label">竞争对手及障碍</span><span class="info-value">${escHtml(competitor)}</span></div>
    `;
  }

  // 决策人列表
  const makersHtml = (p.decision_makers && p.decision_makers.length)
    ? p.decision_makers.map((m, i) => `
        <div class="maker-item">
          <div class="maker-item-title">${i === 0 ? '⭐ 主要决策人' : '决策人 ' + (i + 1)}</div>
          <div class="maker-item-line">科室：${escHtml(m.department_name || '--')}</div>
          <div class="maker-item-line">姓名：${escHtml(m.contact_name || '--')}</div>
          <div class="maker-item-line">联系方式：${escHtml(maskContact(m.contact_info || '--'))}</div>
        </div>
      `).join('')
    : '<div class="empty-mini">暂无决策人</div>';
  document.getElementById('detailMakers').innerHTML = makersHtml;

  // 时间线
  renderTimeline(p.operation_logs || []);
}

function renderTimeline(logs) {
  const container = document.getElementById('detailTimeline');
  if (!logs.length) {
    container.innerHTML = '<div class="empty-mini">暂无操作记录</div>';
    return;
  }
  let html = '<div class="timeline">';
  logs.forEach((log, idx) => {
    const isFirst = idx === 0 && log.field_name === '创建';
    const dotCls = isFirst ? 'dot-create' : (log.field_name === '确认无变化' ? 'dot-confirm' : 'dot-edit');
    const content = formatLogContent(log);
    html += `
      <div class="timeline-item">
        <div class="timeline-dot ${dotCls}"></div>
        <div class="timeline-content">
          <div class="timeline-text">${content}</div>
          <div class="timeline-time">${formatDate(log.operation_time)}</div>
        </div>
      </div>
    `;
  });
  html += '</div>';
  container.innerHTML = html;
}

function formatLogContent(log) {
  const operator = escHtml(log.operator);
  if (log.field_name === '创建') {
    return `<strong>${operator}</strong> 创建了此单据`;
  }
  if (log.field_name === '确认无变化') {
    return `<strong>${operator}</strong> 确认了该项目无变化`;
  }
  return `<strong>${operator}</strong> 将【${escHtml(log.field_name)}】从【${escHtml(log.old_value || '（空）')}】修改为【${escHtml(log.new_value || '（空）')}】`;
}

function getStatusInfo(stage) {
  if (stage === 6) return { text: '无效客户', cls: 'status-lost' };
  if (stage === 4 || stage === 5) return { text: '已成交', cls: 'status-delivered' };
  return { text: '跟进中', cls: 'status-active' };
}

function goEdit() {
  window.location.href = `/projects/${projectId}/edit`;
}

// 脱敏展示：管理员查看时隐藏手机号/微信号中间部分（如 138****0000）
function maskContact(value) {
  if (!value) return '--';
  const s = String(value);
  // 仅管理员脱敏；经销商本人可查看完整信息
  if (!isAdmin) return s;
  if (/^\d{7,}$/.test(s)) {  // 纯数字手机/电话
    return s.slice(0, 3) + '****' + s.slice(-4);
  }
  if (s.length > 4) {
    return s.slice(0, 2) + '****' + s.slice(-2);
  }
  return s;
}

function formatDate(dt) {
  if (!dt) return '--';
  const d = new Date(dt);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}
