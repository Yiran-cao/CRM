// ===== 项目编辑/新建页 JS =====
const STAGE_NAMES = {
  1:'潜在客户',2:'初步接触',3:'持续跟进',
  4:'成交客户',5:'忠诚客户',6:'无效客户'
};

const PRODUCT_LIST = [
  'CT', 'MRI', 'DSA血管造影机', '超声诊断仪', 'DR数字X光机', 'PET-CT',
  'C臂X光机', '内窥镜系统', '监护仪', '呼吸机', '心电图机',
  '血液透析机', '麻醉机', '手术显微镜', '放射治疗设备', '检验分析仪',
];

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

let projectId = null;      // null 表示新建
let makerCounter = 0;
let loadedVersion = 0;     // 乐观锁版本号

// ===== 初始化 =====
document.addEventListener('DOMContentLoaded', async () => {
  initDropdowns();
  addDecisionMaker();  // 初始一个主要决策人

  // 判断新建 or 编辑
  const path = window.location.pathname;
  const match = path.match(/^\/projects\/(\d+)\/edit$/);
  if (match) {
    projectId = parseInt(match[1]);
    document.getElementById('editPageTitle').textContent = '📝 编辑单据';
    await loadProject(projectId);
  } else {
    document.getElementById('editPageTitle').textContent = '📝 新建单据';
  }
});

function initDropdowns() {
  // 省份
  const provOpts = PROVINCE_LIST.map(p => `<option value="${p}">${p}</option>`).join('');
  document.getElementById('fProvince').innerHTML = '<option value="">请选择省份</option>' + provOpts;

  // 产品
  const prodOpts = PRODUCT_LIST.map(p => `<option value="${p}">${p}</option>`).join('');
  document.getElementById('fProduct').innerHTML = '<option value="">请选择产品</option>' + prodOpts;

  // 阶段（10个阶段）
  let stageOpts = '<option value="">请选择阶段</option>';
  for (let i = 1; i <= 6; i++) {
    stageOpts += `<option value="${i}">${i}-${STAGE_NAMES[i]}</option>`;
  }
  document.getElementById('fStage').innerHTML = stageOpts;
}

function onProvinceChange() {
  const p = document.getElementById('fProvince').value;
  const citySel = document.getElementById('fCity');
  if (!p) {
    citySel.innerHTML = '<option value="">请先选择省份</option>';
  } else {
    citySel.innerHTML = '<option value="">请选择地区</option>' +
      (PROVINCE_CITIES[p] || []).map(c => `<option value="${c}">${c}</option>`).join('');
  }
}

// ===== 决策人 =====
function addDecisionMaker(dm = {}) {
  makerCounter++;
  const container = document.getElementById('decisionMakersContainer');
  const isFirst = makerCounter === 1;
  const div = document.createElement('div');
  div.className = 'maker-row';
  div.innerHTML = `
    <div class="maker-badge">${isFirst ? '主要决策人' : '决策人 ' + makerCounter}</div>
    <div class="maker-fields">
      <input type="text" class="maker-department" placeholder="科室名称" value="${escHtml(dm.department_name || '')}">
      <input type="text" class="maker-name" placeholder="负责人姓名" value="${escHtml(dm.contact_name || '')}">
      <input type="text" class="maker-contact" placeholder="负责人电话/微信" value="${escHtml(dm.contact_info || '')}">
    </div>
    ${isFirst ? '' : '<button type="button" class="btn-sm btn-remove-maker" onclick="removeDecisionMaker(this)">✕ 移除</button>'}
  `;
  container.appendChild(div);
}

function removeDecisionMaker(btn) {
  btn.parentElement.remove();
}

function getDecisionMakers() {
  const rows = document.querySelectorAll('.maker-row');
  const makers = [];
  rows.forEach(row => {
    const dept = row.querySelector('.maker-department').value.trim();
    const name = row.querySelector('.maker-name').value.trim();
    const contact = row.querySelector('.maker-contact').value.trim();
    if (dept || name || contact) {
      makers.push({ department_name: dept, contact_name: name, contact_info: contact });
    }
  });
  return makers;
}

// ===== 预算步进 =====
function stepBudget(delta) {
  const input = document.getElementById('fBudget');
  const current = parseFloat(input.value) || 0;
  const next = Math.max(0, current + delta);
  input.value = next.toFixed(2);
}

// ===== 加载项目（编辑模式） =====
async function loadProject(id) {
  try {
    const p = await request(`/projects/${id}`);
    loadedVersion = p.version || 0;
    document.getElementById('fCustomerName').value = p.customer_name;
    document.getElementById('fProvince').value = p.province;
    onProvinceChange();
    document.getElementById('fCity').value = p.city;
    setProductValue(p.product);
    document.getElementById('fStage').value = p.stage;
    document.getElementById('fBudget').value = (p.budget || 0).toFixed(2);
    document.getElementById('fCompetitor').value = p.competitor_info || '';
    document.getElementById('fRemark').value = p.remark || '';

    // 决策人
    const container = document.getElementById('decisionMakersContainer');
    container.innerHTML = '';
    makerCounter = 0;
    if (p.decision_makers && p.decision_makers.length) {
      p.decision_makers.forEach(dm => addDecisionMaker(dm));
    } else {
      addDecisionMaker();
    }
  } catch (err) {
    showToast(err.message, 'error');
  }
}

function setProductValue(product) {
  const sel = document.getElementById('fProduct');
  let found = false;
  for (const opt of sel.options) {
    if (opt.value === product) { found = true; break; }
  }
  if (!found && product) {
    sel.appendChild(new Option(product, product));
  }
  sel.value = product;
}

// ===== 保存 =====
async function saveProject() {
  const customer = document.getElementById('fCustomerName').value.trim();
  const province = document.getElementById('fProvince').value;
  const city = document.getElementById('fCity').value;
  const product = document.getElementById('fProduct').value;
  const stage = document.getElementById('fStage').value;
  const budget = parseFloat(document.getElementById('fBudget').value) || 0;
  const competitor = document.getElementById('fCompetitor').value.trim();
  const remark = document.getElementById('fRemark').value.trim();
  const makers = getDecisionMakers();

  // 必填校验
  if (!customer) { showToast('请填写客户名称', 'error'); return; }
  if (!province) { showToast('请选择省份', 'error'); return; }
  if (!city) { showToast('请选择地区', 'error'); return; }
  if (!product) { showToast('请选择产品', 'error'); return; }
  if (!stage) { showToast('请选择阶段', 'error'); return; }
  if (budget < 0) { showToast('预算不能为负数', 'error'); return; }
  const mainMaker = makers[0];
  if (!mainMaker || !mainMaker.department_name) { showToast('请填写主要决策人的科室名称', 'error'); return; }
  if (!mainMaker.contact_name) { showToast('请填写主要决策人的负责人姓名', 'error'); return; }
  if (!mainMaker.contact_info) { showToast('请填写主要决策人的电话/微信', 'error'); return; }

  const data = {
    customer_name: customer,
    province, city, product,
    stage: parseInt(stage),
    budget,
    competitor_info: competitor,
    remark,
    decision_makers: makers,
    version: loadedVersion,
  };

  const btn = document.getElementById('saveBtn');
  btn.disabled = true;
  btn.textContent = '保存中...';
  try {
    if (projectId) {
      await request(`/projects/${projectId}`, { method: 'PUT', body: JSON.stringify(data) });
      showToast('保存成功！积分+1');
    } else {
      await request('/projects', { method: 'POST', body: JSON.stringify(data) });
      showToast('新建成功！');
    }
    setTimeout(() => window.location.href = '/projects', 800);
  } catch (err) {
    showToast(err.message, 'error');
    btn.disabled = false;
    btn.textContent = '保存';
  }
}

function goBack() {
  window.location.href = '/projects';
}
