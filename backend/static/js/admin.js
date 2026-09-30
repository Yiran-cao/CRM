// ===== 管理员考核管理 JS =====
document.addEventListener('DOMContentLoaded', loadDealers);

// ===== 经销商列表 =====
async function loadDealers() {
  try {
    const dealers = await request('/admin/dealers');
    document.getElementById('adminPeriod').textContent = dealers[0]?.period || '--';
    renderDealerList(dealers);
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function renderDealerList(dealers) {
  const container = document.getElementById('dealerListContainer');
  if (!dealers.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">👥</div><p>暂无经销商</p></div>';
    return;
  }
  let html = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:16px">';
  dealers.forEach(d => {
    const statusIcon = d.submitted ? '✅' : '⏳';
    const statusText = d.submitted ? '已提交' : (d.current_points >= 5 ? '可提交' : '积分不足');
    const statusColor = d.submitted ? '#27ae60' : (d.current_points >= 5 ? '#3498db' : '#e67e22');
    html += `
      <div class="dealer-card" onclick="selectDealer(${d.id},'${escHtml(d.name)}')" data-dealer-id="${d.id}">
        <div class="dealer-card-header">
          <strong>${escHtml(d.name)}</strong>
          <span style="color:${statusColor};font-size:12px">${statusIcon} ${statusText}</span>
        </div>
        <div style="font-size:12px;color:#888;margin-bottom:10px">${escHtml(d.dealer_name || '')}</div>
        <div style="display:flex;gap:16px;font-size:13px">
          <span>📁 项目 <strong>${d.project_count}</strong></span>
          <span>✅ 成交 <strong>${d.delivered_count}</strong></span>
          <span>🚫 无效 <strong>${d.lost_count}</strong></span>
          <span>⭐ 积分 <strong>${d.current_points}</strong></span>
        </div>
      </div>`;
  });
  html += '</div>';
  container.innerHTML = html;
}

// ===== 选中经销商 =====
let selectedDealerId = null;

async function selectDealer(id, name) {
  selectedDealerId = id;
  document.getElementById('dealerProjectTitle').textContent = name + ' 的项目';

  // 高亮选中卡片
  document.querySelectorAll('.dealer-card').forEach(c => c.classList.remove('selected'));
  const targetCard = document.querySelector(`.dealer-card[data-dealer-id="${id}"]`);
  if (targetCard) targetCard.classList.add('selected');

  // 加载项目
  try {
    const projects = await request(`/admin/dealer/${id}/projects`);
    renderDealerProjects(projects);
    document.getElementById('dealerProjectsPanel').style.display = '';
  } catch (err) { showToast(err.message, 'error'); }

  // 加载积分
  try {
    const points = await request(`/admin/dealer/${id}/points`);
    renderDealerPoints(points);
    document.getElementById('dealerPointsPanel').style.display = '';
  } catch (err) { showToast(err.message, 'error'); }
}

function renderDealerProjects(projects) {
  const container = document.getElementById('dealerProjectTable');
  if (!projects.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📁</div><p>暂无项目</p></div>';
    return;
  }
  let html = '<div style="overflow-x:auto"><table class="data-table"><thead><tr><th>ID</th><th>客户</th><th>地区</th><th>产品</th><th>阶段</th><th>预算</th><th>更新时间</th></tr></thead><tbody>';
  projects.forEach(p => {
    const d = new Date(p.updated_at);
    const ts = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
    html += `<tr><td>#${p.id}</td><td>${escHtml(p.customer_name)}</td><td>${escHtml(p.province)} ${escHtml(p.city)}</td><td>${escHtml(p.product)}</td><td>${getStageBadge(p.stage)}</td><td>${p.budget||0}万</td><td>${ts}</td></tr>`;
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

function renderDealerPoints(logs) {
  const container = document.getElementById('dealerPointsTable');
  if (!logs.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">⭐</div><p>暂无积分记录</p></div>';
    return;
  }
  let html = '<table class="data-table"><thead><tr><th>周期</th><th>积分变化</th><th>操作类型</th><th>说明</th><th>时间</th></tr></thead><tbody>';
  logs.forEach(l => {
    const d = l.created_at ? new Date(l.created_at) : null;
    const ts = d ? `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}` : '';
    html += `<tr><td>${l.period}</td><td>${l.points_change>0?'+'+l.points_change:l.points_change}</td><td>${l.operation_type}</td><td>${escHtml(l.description||'')}</td><td>${ts}</td></tr>`;
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}

// ===== 新建经销商 =====
function openCreateDealerModal() {
  document.getElementById('newDealerName').value = '';
  document.getElementById('newDealerUsername').value = '';
  document.getElementById('newDealerPassword').value = '';
  document.getElementById('newDealerCompany').value = '';
  document.getElementById('dealerModal').classList.add('show');
}

function closeDealerModal() {
  document.getElementById('dealerModal').classList.remove('show');
}

async function createDealer() {
  const data = {
    name: document.getElementById('newDealerName').value.trim(),
    username: document.getElementById('newDealerUsername').value.trim(),
    password: document.getElementById('newDealerPassword').value,
    dealer_name: document.getElementById('newDealerCompany').value.trim(),
  };
  if (!data.name || !data.username || !data.password || !data.dealer_name) {
    showToast('请填写所有字段', 'error'); return;
  }
  try {
    await request('/admin/dealers', { method: 'POST', body: JSON.stringify(data) });
    showToast('经销商创建成功！');
    closeDealerModal();
    loadDealers();
  } catch (err) {
    showToast(err.message, 'error');
  }
}

// ===== 事件委托：经销商卡片点击 =====
document.addEventListener('click', (e) => {
  const card = e.target.closest('.dealer-card');
  if (!card) return;
  const id = parseInt(card.dataset.dealerId);
  const name = card.dataset.dealerName;
  if (id && name) selectDealer(id, name);
});
