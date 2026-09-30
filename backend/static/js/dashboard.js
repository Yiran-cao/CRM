// ===== 工作台仪表盘 JS =====
document.addEventListener('DOMContentLoaded', async () => {
  try {
    const data = await request('/dashboard');
    renderDashboard(data);
  } catch (err) {
    console.error('Dashboard load error:', err);
    // 保持显示 "--"
  }
});

function renderDashboard(data) {
  setStat('statTotal', data.total_projects, '个项目');
  setStat('statPredicted', data.predicted, '个待成交');
  setStat('statDelivered', data.delivered, '个已成交');
  setStat('statLost', data.lost, '个无效');
  setStat('statPoints', data.total_points, '分');
  setStat('statPeriod', data.period, '');

  // 账号状态 - 带颜色
  const statusEl = document.getElementById('statStatus');
  const colors = { green: '#27ae60', orange: '#e67e22', gray: '#999' };
  statusEl.textContent = data.account_status;
  statusEl.style.color = colors[data.status_color] || '#333';
}

function setStat(id, value, suffix) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = `<span class="stat-number">${value}</span><span class="stat-suffix">${suffix}</span>`;
}
