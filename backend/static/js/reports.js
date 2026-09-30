// ===== 提交报表 JS =====
document.addEventListener('DOMContentLoaded', async () => {
  await loadReportStatus();
  const history = await request('/reports/history');
  renderHistory(history);
});

async function loadReportStatus() {
  try {
    const status = await request('/reports/status');
    document.getElementById('rptPoints').textContent = status.total_points;
    document.getElementById('rptPeriod').textContent = status.period;
    document.getElementById('rptDeadline').textContent = formatDeadline(status.deadline);
    document.getElementById('rptStatus').textContent = status.status;

    const btn = document.getElementById('submitReportBtn');
    const hint = document.getElementById('submitHint');

    if (status.submitted) {
      btn.disabled = true;
      btn.textContent = '✅ 本期报表已提交';
      btn.style.background = '#27ae60';
      hint.style.display = 'none';
    } else if (status.can_submit) {
      btn.disabled = false;
      btn.textContent = '📤 提交当前周期报表';
      btn.style.background = '#3498db';
      hint.style.display = 'none';
    } else {
      btn.disabled = true;
      btn.textContent = '📤 提交当前周期报表';
      btn.style.background = '';
      hint.style.display = 'inline';
      hint.textContent = `当前积分：${status.total_points} 分，需要至少 5 分才能提交`;
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function formatDeadline(dt) {
  if (!dt) return '--';
  const d = new Date(dt);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}

function renderHistory(logs) {
  const container = document.getElementById('pointsHistoryTable');
  if (!logs.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📝</div><p>暂无积分记录</p></div>';
    return;
  }
  let html = `<table class="data-table"><thead><tr>
    <th>周期</th><th>积分变化</th><th>操作类型</th><th>说明</th><th>时间</th>
  </tr></thead><tbody>`;
  logs.forEach(l => {
    const d = l.created_at ? new Date(l.created_at) : null;
    const timeStr = d ? `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')} ${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}` : '';
    html += `<tr>
      <td>${l.period}</td>
      <td>${l.points_change > 0 ? '+' + l.points_change : l.points_change}</td>
      <td>${l.operation_type}</td>
      <td>${l.description || ''}</td>
      <td>${timeStr}</td>
    </tr>`;
  });
  html += '</tbody></table>';
  container.innerHTML = html;
}

async function submitReport() {
  if (!confirm('确认提交当前周期报表？提交后将记录积分快照。')) return;
  try {
    const result = await request('/reports/submit', { method: 'POST', body: '{}' });
    showToast(`✅ 报表提交成功！当期积分：${result.total_points} 分`);
    // 刷新状态和历史
    await loadReportStatus();
    const history = await request('/reports/history');
    renderHistory(history);
  } catch (err) {
    showToast(err.message, 'error');
  }
}
