// ─────────────────────────────────────────────────────────────
//  supabase.js  —  NZ Temple 全站共用 Supabase 客户端
//  所有页面在加载本文件前，必须先加载 Supabase SDK：
//  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
//  <script src="supabase.js"></script>
// ─────────────────────────────────────────────────────────────

const SUPABASE_URL = 'https://slditilymhrlfufmpxhr.supabase.co';
const SUPABASE_ANON_KEY = 'sb_publishable_b1rZTUmreA00TdirQ5LNmQ_LXon2lfm';

const _sb = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
  auth: {
    persistSession: true,
    autoRefreshToken: true,
    detectSessionInUrl: true
  }
});

// ─── 认证 ────────────────────────────────────────────────────

/** 获取当前 session（异步） */
async function getSession() {
  const { data: { session } } = await _sb.auth.getSession();
  return session;
}

/**
 * 要求已登录，否则跳转到 login.html
 * @returns {Session|null}
 */
async function requireAuth() {
  const session = await getSession();
  if (!session) {
    window.location.href = 'login.html';
    return null;
  }
  return session;
}

/** 退出登录，跳转首页 */
async function signOut() {
  await _sb.auth.signOut();
  window.location.href = 'index.html';
}

// ─── 用户资料 ─────────────────────────────────────────────────

/**
 * 获取当前登录用户的 member_profiles 记录
 * @returns {object|null}
 */
async function getMyProfile() {
  const session = await getSession();
  if (!session) return null;
  const { data, error } = await _sb
    .from('member_profiles')
    .select('*')
    .eq('id', session.user.id)
    .single();
  if (error) { console.error('getMyProfile:', error.message); return null; }
  return data;
}

/**
 * 更新当前用户的 member_profiles（不含 level / merit_points，后台才能改）
 * @param {object} updates
 */
async function updateMyProfile(updates) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };
  //
  const safe = { ...updates };
  delete safe.level;
  delete safe.merit_points;
  delete safe.id;
  delete safe.role;
  const { data, error } = await _sb
    .from('member_profiles')
    .update(safe)
    .eq('id', session.user.id)
    .select()
    .single();
  return { data, error };
}

// ─── 亲友资料 ─────────────────────────────────────────────────

/** 获取当前用户所有亲友档案 */
async function getFamilyFriends() {
  const session = await getSession();
  if (!session) return [];
  const { data, error } = await _sb
    .from('family_friends')
    .select('*')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  if (error) { console.error('getFamilyFriends:', error.message); return []; }
  return data || [];
}

/** 新增一条亲友档案 */
async function addFamilyFriend(record) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };
  const { data, error } = await _sb
    .from('family_friends')
    .insert({ ...record, user_id: session.user.id })
    .select()
    .single();
  return { data, error };
}

/** 更新亲友档案 */
async function updateFamilyFriend(id, updates) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };
  const { data, error } = await _sb
    .from('family_friends')
    .update(updates)
    .eq('id', id)
    .eq('user_id', session.user.id)
    .select()
    .single();
  return { data, error };
}

/** 删除亲友档案 */
async function deleteFamilyFriend(id) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };
  const { error } = await _sb
    .from('family_friends')
    .delete()
    .eq('id', id)

    .eq('user_id', session.user.id);
  return { error };
}

// ─── 功德记录 ─────────────────────────────────────────────────

/** 获取当前用户的功德记录（只读，后台维护） */
async function getMeritRecords() {
  const session = await getSession();
  if (!session) return [];
  const { data, error } = await _sb
    .from('merit_records')
    .select('*')
    .eq('user_id', session.user.id)
    .order('record_date', { ascending: false });
  if (error) { console.error('getMeritRecords:', error.message); return []; }
  return data || [];
}

// ─── 证书 ─────────────────────────────────────────────────────

/** 获取当前用户的证书列表 */
async function getCertificates() {
  const session = await getSession();
  if (!session) return [];
  const { data, error } = await _sb
    .from('certificates')
    .select('*')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  if (error) { console.error('getCertificates:', error.message); return []; }
  return data || [];
}

/**
 * 上传证书文件到 Supabase Storage，并在 certificates 表写入记录
 * Storage bucket 名称：certificates（需在 Supabase 后台手动创建，设为 Public）
 * @param {File}   file
 * @param {string} title     证书名称
 * @param {string} certType  皈依证 / 传度证 / 授禄证 / 其他
 */
async function uploadCertificate(file, title, certType) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };

  const filePath = `${session.user.id}/${Date.now()}_${file.name}`;

  const { error: uploadError } = await _sb.storage
    .from('certificates')
    .upload(filePath, file, { cacheControl: '3600', upsert: false });

  if (uploadError) return { error: uploadError };

  const { data: urlData } = _sb.storage
    .from('certificates')
    .getPublicUrl(filePath);

  const { data, error } = await _sb
    .from('certificates')
    .insert({
      user_id: session.user.id,
      title: title,
      file_path: filePath,
      file_url: urlData.publicUrl
    })
    .select()
    .single();

  return { data, error };
}

/** 删除证书（同时删除 Storage 文件） */
async function deleteCertificate(id, filePath) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };

  if (filePath) {
    await _sb.storage.from('certificates').remove([filePath]);
  }

  const { error } = await _sb
    .from('certificates')
    .delete()
    .eq('id', id)
    .eq('user_id', session.user.id);

  return { error };
}

// ─── 表文模板 ─────────────────────────────────────────────────

/** 获取所有表文模板（登录用户可读） */
async function getDocumentTemplates() {
  const { data, error } = await _sb
    .from('document_templates')
    .select('*')
    .order('title');
  if (error) { console.error('getDocumentTemplates:', error.message); return []; }
  return data || [];
}

// ─── 生成表文 ─────────────────────────────────────────────────

/** 获取当前用户历史生成表文 */
async function getGeneratedDocuments() {
  const session = await getSession();
  if (!session) return [];
  const { data, error } = await _sb
    .from('generated_documents')
    .select('*, document_templates(title, code)')
    .eq('user_id', session.user.id)
    .order('created_at', { ascending: false });
  if (error) { console.error('getGeneratedDocuments:', error.message); return []; }
  return data || [];
}

/**
 * 生成表文：替换模板占位符 {{字段名}} 并保存记录
 * @param {string} templateId       模板 ID
 * @param {string} docTitle         表文标题
 * @param {object} fields           占位符映射，如 { '姓名': '张三', '生辰': '...' }
 * @param {string} templateContent  模板原文（已从 DB 取出的 content 字段）
 */
async function generateDocument(templateId, docTitle, fields, templateContent) {
  const session = await getSession();
  if (!session) return { error: { message: 'Not logged in' } };

  let content = templateContent;
  for (const [key, val] of Object.entries(fields)) {
    const re = new RegExp(`\\{\\{${key}\\}\\}`, 'g');
    content = content.replace(re, val || '___');
  }

  const { data, error } = await _sb
    .from('generated_documents')
    .insert({
      user_id: session.user.id,
      template_id: templateId || null,
      title: docTitle,
      content: content
    })
    .select()
    .single();

  return { data, error, content };
}

// ─── 导航栏 ──────────────────────────────────────────────────

/**
 * 在任意页面调用，把 id="navAuthBtn" 的元素：
 *   已登录 → 改为"退出"按钮
 *   未登录 → 保持"登录"链接
 */
async function renderNavAuthBtn() {
  const btn = document.getElementById('navAuthBtn');
  if (!btn) return;

  const session = await getSession();
  if (session) {
    btn.innerHTML = '<span class="lang-en">Logout</span><span class="lang-zh">退出</span>';
    btn.href = '#';
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      await _sb.auth.signOut();
      window.location.href = 'index.html';
    });
  } else {
    btn.innerHTML = '<span class="lang-en">Login</span><span class="lang-zh">登录</span>';
    btn.href = 'login.html';
  }
}

// ─── 工具函数 ─────────────────────────────────────────────────

/** 下载文字内容为 .txt 文件 */
function downloadAsText(content, filename) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = (filename || 'document') + '.txt';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

/** 格式化 timestamptz 为 YYYY-MM-DD HH:mm */
function formatDateTime(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.getFullYear() + '-'
    + String(d.getMonth() + 1).padStart(2, '0') + '-'
    + String(d.getDate()).padStart(2, '0') + ' '
    + String(d.getHours()).padStart(2, '0') + ':'
    + String(d.getMinutes()).padStart(2, '0');
}

/** 格式化为 YYYY-MM-DD */
function formatDate(ts) {
  if (!ts) return '—';
  const d = new Date(ts);
  return d.getFullYear() + '-'
    + String(d.getMonth() + 1).padStart(2, '0') + '-'
    + String(d.getDate()).padStart(2, '0');
}

/** 阴历格式化（浏览器原生，无需第三方库） */
function formatLunar(ts) {
  if (!ts) return '—';
  try {
    const fmt = new Intl.DateTimeFormat('zh-Hans-u-ca-chinese', {
      year: 'numeric', month: 'numeric', day: 'numeric'
    });
    return fmt.format(new Date(ts));
  } catch (e) {
    return '—';
  }
}
