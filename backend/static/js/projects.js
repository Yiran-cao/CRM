// ===== 项目管理列表页 JS =====
let isArchived = false;
const currentUser = getUser();
const isAdmin = currentUser && currentUser.role === 'admin';

// ===== 阶段数据 =====
const STAGE_NAMES = {
  1:'潜在客户',2:'初步接触',3:'持续跟进',
  4:'成交客户',5:'忠诚客户',6:'无效客户'
};

const STAGE_CATEGORY = {
  1:'info',2:'info',3:'success',4:'success',5:'success',6:'danger'
};

const STAGE_ICONS = {
  1:'💡',2:'💬',3:'📞',4:'🤝',5:'⭐',6:'🚫'
};

function getStageBadge(stage) {
  const name = STAGE_NAMES[stage] || stage;
  const icon = STAGE_ICONS[stage] || '';
  const cat = STAGE_CATEGORY[stage] || 'info';
  return `<span class="stage-badge ${cat}" title="${name}">${icon} ${stage}-${name}</span>`;
}

// ===== 省份-城市数据 =====
const PROVINCE_CITIES = {
  '北京':['东城区','西城区','朝阳区','海淀区','丰台区','通州区','大兴区'],
  '上海':['黄浦区','徐汇区','长宁区','静安区','浦东新区','闵行区','嘉定区'],
  '广东':['广州','深圳','珠海','佛山','东莞','中山','惠州','汕头'],
  '浙江':['杭州','宁波','温州','嘉兴','湖州','绍兴','金华','台州'],
  '江苏':['南京','苏州','无锡','常州','南通','徐州','扬州','镇江'],
  '山东':['济南','青岛','烟台','潍坊','临沂','淄博','威海','日照'],
  '四川':['成都','绵阳','德阳','宜宾','南充','泸州','乐山','达州'],
  '湖北':['武汉','宜昌','襄阳','荆州','黄石','十堰','鄂州','孝感'],
  '湖南':['长沙','株洲','湘潭','衡阳','岳阳','常德','郴州','益阳'],
  '河南':['郑州','洛阳','开封','南阳','许昌','新乡','安阳','焦作'],
  '河北':['石家庄','唐山','保定','邯郸','廊坊','沧州','邢台','秦皇岛'],
  '福建':['福州','厦门','泉州','漳州','莆田','龙岩','三明','宁德'],
  '安徽':['合肥','芜湖','蚌埠','马鞍山','安庆','滁州','阜阳','六安'],
  '辽宁':['沈阳','大连','鞍山','抚顺','锦州','营口','盘锦','丹东'],
  '陕西':['西安','咸阳','宝鸡','渭南','汉中','榆林','延安','安康'],
  '重庆':['渝中区','江北区','沙坪坝区','九龙坡区','南岸区','渝北区','巴南区'],
  '天津':['和平区','河西区','南开区','河东区','河北区','红桥区','滨海新区'],
  '江西':['南昌','九江','赣州','景德镇','上饶','宜春','吉安','抚州'],
  '广西':['南宁','柳州','桂林','北海','玉林','梧州','钦州','百色'],
  '云南':['昆明','曲靖','大理','玉溪','丽江','普洱','保山','昭通'],
  '贵州':['贵阳','遵义','毕节','六盘水','安顺','铜仁','黔东南','黔南'],
  '山西':['太原','大同','长治','临汾','运城','晋中','阳泉','朔州'],
  '吉林':['长春','吉林','四平','通化','延边','松原','白城','辽源'],
  '黑龙江':['哈尔滨','齐齐哈尔','大庆','牡丹江','佳木斯','鸡西','鹤岗','绥化'],
  '甘肃':['兰州','天水','白银','酒泉','张掖','武威','平凉','庆阳'],
  '海南':['海口','三亚','儋州','琼海','文昌','万宁','东方','五指山'],
  '内蒙古':['呼和浩特','包头','鄂尔多斯','赤峰','通辽','呼伦贝尔','乌海','巴彦淖尔'],
  '新疆':['乌鲁木齐','克拉玛依','吐鲁番','哈密','喀什','伊犁','阿克苏','昌吉'],
  '西藏':['拉萨','日喀则','昌都','林芝','山南','那曲','阿里'],
  '宁夏':['银川','石嘴山','吴忠','固原','中卫'],
  '青海':['西宁','海东','海西','海北','黄南','果洛','玉树'],
};
const PROVINCE_LIST = Object.keys(PROVINCE_CITIES).sort();

// ===== 初始化省份筛选下拉框 =====
function initProvinceSelects() {
  const options = PROVINCE_LIST.map(p => `<option value="${p}">${p}</option>`).join('');
  const fp = document.getElementById('filterProvince');
  if (fp) fp.innerHTML = '<option value="">全部省份</option>' + options;
}

function onProvinceChange() {
  const p = document.getElementById('filterProvince').value;
  document.getElementById('filterCity').innerHTML = p
    ? PROVINCE_CITIES[p].map(c => `<option value="${c}">${c}</option>`).join('')
    : '<option value="">全部地区</option>';
}

// ===== Tab 切换 =====
function switchTab(archived) {
  isArchived = archived;
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', (i === 0 && !archived) || (i === 1 && archived));
  });
  loadProjects();
}

function resetFilters() {
  document.getElementById('filterCustomer').value = '';
  document.getElementById('filterStage').value = '';
  document.getElementById('filterProvince').value = '';
  document.getElementById('filterCity').innerHTML = '<option value="">全部地区</option>';
  loadProjects();
}

// ===== 加载项目列表 =====
async function loadProjects() {
  const params = {};
  const customer = document.getElementById('filterCustomer').value.trim();
  const stage = document.getElementById('filterStage').value;
  const province = document.getElementById('filterProvince').value;
  const city = document.getElementById('filterCity').value;
  if (customer) params.customer_name = customer;
  if (stage) params.stage = parseInt(stage);
  if (province) params.province = province;
  if (city) params.city = city;
  if (isArchived) params.archived = true;
  const qs = new URLSearchParams(params).toString();
  try {
    const projects = await request(`/projects${qs ? '?' + qs : ''}`);
    renderTable(projects);
  } catch (err) { showToast(err.message, 'error'); }
}

// ===== 渲染表格 =====
function renderTable(projects) {
  const container = document.getElementById('projectTableContainer');
  if (!projects || !projects.length) {
    container.innerHTML = '<div class="empty-state"><div class="icon">📁</div><p>暂无项目数据，点击右上角"新建项目"开始</p></div>';
    return;
  }
  let html = `<div style="overflow-x:auto"><table class="data-table">
    <thead><tr>
      <th>ID</th><th>客户名称</th><th>省份</th><th>地区</th><th>产品</th>
      <th>阶段</th><th>预算(万)</th><th>科室</th><th>最后更新时间</th><th>操作</th>
    </tr></thead><tbody>`;
  projects.forEach(p => {
    const actions = isAdmin
      ? `<button class="btn-sm" onclick="goDetail(${p.id})">详情</button>`
      : `<button class="btn-sm" onclick="goDetail(${p.id})">详情</button>
         <button class="btn-sm" onclick="goEdit(${p.id})">编辑</button>
         <button class="btn-sm" onclick="confirmNoChange(${p.id})">确认无变化</button>`;
    html += `<tr>
      <td><strong>#${p.id}</strong></td>
      <td>${escHtml(p.customer_name)}</td>
      <td>${escHtml(p.province)}</td>
      <td>${escHtml(p.city)}</td>
      <td>${escHtml(p.product)}</td>
      <td>${getStageBadge(p.stage)}</td>
      <td>${p.budget ? p.budget.toFixed(2) : '0.00'}</td>
      <td>${escHtml(p.department || '-')}</td>
      <td>${formatDate(p.updated_at)}</td>
      <td class="actions">${actions}</td></tr>`;
  });
  html += '</tbody></table></div>';
  container.innerHTML = html;
}

// ===== 导航 =====
function goNew() { window.location.href = '/projects/new'; }
function goDetail(id) { window.location.href = `/projects/${id}`; }
function goEdit(id) { window.location.href = `/projects/${id}/edit`; }

// ===== 确认无变化 =====
async function confirmNoChange(id) {
  if (!confirm('确认该项目当前无变化？点击确定后将更新最后更新时间并计入积分。')) return;
  try {
    const result = await request(`/projects/${id}/confirm`, { method: 'POST' });
    showToast(`已确认无变化！积分+1（当前周期共 ${result.total_points} 分）`);
    loadProjects();
  } catch (err) { showToast(err.message, 'error'); }
}

// ===== 工具 =====
function formatDate(dt) {
  if (!dt) return '';
  const d = new Date(dt);
  const pad = n => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth()+1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', () => {
  initProvinceSelects();
  loadProjects();
});
