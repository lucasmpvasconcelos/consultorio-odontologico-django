/* ================================================
   DentalCare Pro — app.js  (v2 - corrigido)
   Conecta com API Django REST Framework
   ================================================ */

const API = 'http://127.0.0.1:8000/api/v1';
let ACCESS_TOKEN = localStorage.getItem('access_token');
let REFRESH_TOKEN = localStorage.getItem('refresh_token');
let CURRENT_PAGE = 'dashboard';

// ── UTILS
const $ = id => document.getElementById(id);
const show = el => el && el.classList.remove('hidden');
const hide = el => el && el.classList.add('hidden');

function fmt_money(val) {
  return 'R$ ' + parseFloat(val || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function fmt_date(str) {
  if (!str) return '-';
  try { const d = new Date(str + (str.includes('T') ? '' : 'T00:00:00')); return d.toLocaleDateString('pt-BR'); }
  catch { return str; }
}
function fmt_datetime(str) {
  if (!str) return '-';
  try { const d = new Date(str); return d.toLocaleDateString('pt-BR') + ' ' + d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' }); }
  catch { return str; }
}
function status_badge(status_val, map) {
  const label = map[status_val] || status_val || '-';
  return `<span class="badge badge-${status_val}">${label}</span>`;
}
function extract_list(r) {
  if (!r) return [];
  if (Array.isArray(r)) return r;
  if (r.results && Array.isArray(r.results)) return r.results;
  return [];
}

// ── TOAST
function toast(msg, type = 'info') {
  const icons = {
    success: '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#059669" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>',
    error:   '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>',
    info:    '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/></svg>',
    warn:    '<svg class="toast-icon" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2.5"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>',
  };
  const t = document.createElement('div');
  t.className = `toast toast-${type}`;
  t.innerHTML = (icons[type] || icons.info) + `<span>${msg}</span>`;
  $('toast-container').prepend(t);
  setTimeout(() => { t.style.transition = 'opacity .4s'; t.style.opacity = '0'; }, 3000);
  setTimeout(() => t.remove(), 3500);
}

// ── API CALLS
async function api_fetch(path, opts = {}) {
  try {
    const headers = { 'Content-Type': 'application/json', ...(opts.headers || {}) };
    if (ACCESS_TOKEN) headers['Authorization'] = `Bearer ${ACCESS_TOKEN}`;
    let res = await fetch(`${API}${path}`, { ...opts, headers });
    if (res.status === 401 && REFRESH_TOKEN) {
      const r = await fetch('http://127.0.0.1:8000/api/token/refresh/', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: REFRESH_TOKEN }),
      });
      if (r.ok) {
        const d = await r.json();
        ACCESS_TOKEN = d.access;
        localStorage.setItem('access_token', ACCESS_TOKEN);
        headers['Authorization'] = `Bearer ${ACCESS_TOKEN}`;
        res = await fetch(`${API}${path}`, { ...opts, headers });
      } else { do_logout(); return null; }
    }
    if (!res.ok) { console.warn(`API ${path} => ${res.status}`); return null; }
    if (res.status === 204) return {};
    return res.json().catch(() => ({}));
  } catch (e) { console.error('api_fetch error:', path, e); return null; }
}

// ── AUTH
async function do_login(user, pass) {
  try {
    const r = await fetch('http://127.0.0.1:8000/api/token/', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password: pass }),
    });
    if (!r.ok) return false;
    const d = await r.json();
    ACCESS_TOKEN = d.access; REFRESH_TOKEN = d.refresh;
    localStorage.setItem('access_token', ACCESS_TOKEN);
    localStorage.setItem('refresh_token', REFRESH_TOKEN);
    return true;
  } catch(e) { return false; }
}

function do_logout() {
  localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token');
  hide($('app')); show($('login-screen'));
  ACCESS_TOKEN = REFRESH_TOKEN = null;
}

// ── LOGIN FORM
$('login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const btn = $('btn-login');
  btn.disabled = true; btn.textContent = 'Entrando...';
  let ok = false;
  try { ok = await do_login($('login-user').value.trim(), $('login-pass').value); }
  catch(err) { console.error('Login error:', err); }
  if (ok) {
    hide($('login-screen')); show($('app')); await init_app();
  } else {
    show($('login-error')); btn.disabled = false; btn.textContent = 'Entrar';
  }
});

// ── TOPBAR DATE
function update_date() {
  $('topbar-date').textContent = new Date().toLocaleDateString('pt-BR', { weekday: 'short', day: '2-digit', month: 'short' });
}

// ── NAVIGATION
function navigate(page) {
  document.querySelectorAll('.nav-item').forEach(a => a.classList.remove('active'));
  const nav = document.querySelector(`[data-page="${page}"]`);
  if (nav) nav.classList.add('active');
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  const pg = $(`page-${page}`);
  if (pg) pg.classList.add('active');
  CURRENT_PAGE = page;
  load_page(page);
}

document.querySelectorAll('[data-page]').forEach(el => {
  el.addEventListener('click', e => { e.preventDefault(); navigate(el.dataset.page); });
});

async function load_page(page) {
  const map = { dashboard: load_dashboard, consultas: load_consultas, pacientes: load_pacientes,
    dentistas: load_dentistas, prontuarios: load_prontuarios, procedimentos: load_procedimentos,
    financeiro: load_financeiro, estoque: load_estoque };
  if (map[page]) map[page]();
}

// ── DASHBOARD
// /dashboard/ => { consultas:{hoje_total}, financeiro:{receitas_mes,despesas_mes}, estoque:{itens_criticos}, pacientes:{total} }
// /consultas/hoje/ => { data, total, consultas:[] }
// /financeiro/resumo/ => { receitas:{total,quantidade}, despesas:{total,quantidade}, pendentes:{total,quantidade}, saldo }
async function load_dashboard() {
  const hr = new Date().getHours();
  $('dash-greeting').textContent = `${hr<12?'Bom dia':hr<18?'Boa tarde':'Boa noite'}! Aqui esta o resumo de hoje.`;

  const [dash, fin_r, hoje_r] = await Promise.all([
    api_fetch('/dashboard/'),
    api_fetch('/financeiro/resumo/'),
    api_fetch('/consultas/hoje/'),
  ]);

  if (dash) {
    $('val-consultas-hoje').textContent = dash.consultas?.hoje_total ?? 0;
    $('val-pacientes').textContent      = dash.pacientes?.total ?? '-';
    $('val-receita').textContent        = fmt_money(dash.financeiro?.receitas_mes ?? 0);
    const alertas = dash.estoque?.itens_criticos ?? 0;
    $('val-estoque-alertas').textContent = alertas;
    if (alertas > 0) { show($('badge-estoque')); $('badge-estoque').textContent = alertas; }
  }

  if (hoje_r) {
    const arr = hoje_r.consultas || [];
    $('badge-agenda-hoje').textContent = hoje_r.total || arr.length;
    if (!arr.length) {
      $('lista-consultas-hoje').innerHTML = '<div class="empty-state"><p>Nenhuma consulta hoje</p></div>';
    } else {
      const dot = { agendada:'#2563eb', confirmada:'#0d9488', realizada:'#059669', cancelada:'#dc2626', falta:'#d97706' };
      $('lista-consultas-hoje').innerHTML = arr.slice(0,6).map(c => {
        const hora = c.data_hora ? new Date(c.data_hora).toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}) : '-';
        const pac = c.paciente_nome || (c.paciente && typeof c.paciente==='object' ? c.paciente.nome_completo : '') || 'Paciente';
        const den = c.dentista_nome || (c.dentista && typeof c.dentista==='object' ? c.dentista.nome_completo : '') || '';
        return `<div class="agenda-item">
          <span class="agenda-time">${hora}</span>
          <div class="agenda-dot" style="background:${dot[c.status]||'#9ca3af'}"></div>
          <div class="agenda-info"><div class="agenda-name">${pac}</div><div class="agenda-dent">${den}</div></div>
        </div>`;
      }).join('');
    }
  }

  if (fin_r) {
    const rec   = parseFloat(fin_r.receitas?.total ?? fin_r.receitas ?? 0);
    const des   = parseFloat(fin_r.despesas?.total ?? fin_r.despesas ?? 0);
    const pen   = parseFloat(fin_r.pendentes?.total ?? fin_r.pendentes ?? 0);
    const saldo = parseFloat(fin_r.saldo ?? (rec - des));
    const total = Math.max(rec, des, pen, 1);
    $('fin-receitas').textContent = fmt_money(rec);
    $('fin-despesas').textContent = fmt_money(des);
    $('fin-pendentes').textContent = fmt_money(pen);
    $('fin-saldo').textContent = fmt_money(saldo);
    $('fin-bar-r').style.width = (rec/total*100) + '%';
    $('fin-bar-d').style.width = (des/total*100) + '%';
    $('fin-bar-p').style.width = (pen/total*100) + '%';
  }

  const prox = await api_fetch('/consultas/?ordering=data_hora&limit=5&status=agendada');
  if (prox) render_table_consultas($('tabela-proximas-consultas'), extract_list(prox), true);
}

// ── CONSULTAS
async function load_consultas() {
  const status = $('filter-consultas-status').value;
  const data   = $('filter-consultas-data').value;
  let url = '/consultas/?ordering=data_hora&limit=50';
  if (status) url += `&status=${status}`;
  if (data)   url += `&data=${data}`;
  const r = await api_fetch(url);
  const arr = extract_list(r);
  const q = ($('filter-consultas').value||'').toLowerCase();
  render_table_consultas($('tabela-consultas'), q ? arr.filter(c => JSON.stringify(c).toLowerCase().includes(q)) : arr, false);
}

const STATUS_C = { agendada:'Agendada', confirmada:'Confirmada', realizada:'Realizada', cancelada:'Cancelada', falta:'Falta' };
const TIPO_C   = { consulta:'Consulta', retorno:'Retorno', emergencia:'Emergencia', avaliacao:'Avaliacao' };

function render_table_consultas(el, arr, mini) {
  if (!arr || !arr.length) {
    el.innerHTML = '<div class="empty-state"><p>Nenhuma consulta encontrada</p></div>'; return;
  }
  el.innerHTML = `<table class="data-table"><thead><tr>
    <th>Data/Hora</th><th>Paciente</th><th>Dentista</th><th>Tipo</th><th>Status</th>
    ${!mini ? '<th>Acoes</th>' : ''}
  </tr></thead><tbody>
  ${arr.map(c => {
    const pac = c.paciente_nome || (c.paciente && typeof c.paciente==='object' ? c.paciente.nome_completo : c.paciente) || '-';
    const den = c.dentista_nome || (c.dentista && typeof c.dentista==='object' ? c.dentista.nome_completo : c.dentista) || '-';
    return `<tr>
      <td>${fmt_datetime(c.data_hora)}</td>
      <td><strong>${pac}</strong></td><td>${den}</td>
      <td>${TIPO_C[c.tipo]||c.tipo||'-'}</td>
      <td>${status_badge(c.status, STATUS_C)}</td>
      ${!mini ? `<td><div class="table-actions">
        <button class="btn-icon" onclick="confirmar_consulta(${c.id})" title="Confirmar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg></button>
        <button class="btn-icon" onclick="cancelar_consulta(${c.id})" title="Cancelar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></button>
      </div></td>` : ''}
    </tr>`;
  }).join('')}</tbody></table>`;
}

async function confirmar_consulta(id) {
  const r = await api_fetch(`/consultas/${id}/confirmar/`, { method: 'PATCH' });
  if (r !== null) { toast('Consulta confirmada!', 'success'); load_consultas(); }
  else toast('Erro ao confirmar', 'error');
}
async function cancelar_consulta(id) {
  if (!confirm('Cancelar esta consulta?')) return;
  const r = await api_fetch(`/consultas/${id}/cancelar/`, { method: 'PATCH' });
  if (r !== null) { toast('Consulta cancelada', 'warn'); load_consultas(); }
  else toast('Erro ao cancelar', 'error');
}

// ── PACIENTES
async function load_pacientes() {
  const q = ($('filter-pacientes').value||'').trim();
  const url = q ? `/pacientes/buscar/?q=${encodeURIComponent(q)}` : '/pacientes/?limit=50&ordering=nome_completo';
  const r = await api_fetch(url);
  const arr = extract_list(r);
  if (!arr.length) { $('tabela-pacientes').innerHTML = '<div class="empty-state"><p>Nenhum paciente encontrado</p></div>'; return; }
  $('tabela-pacientes').innerHTML = `<table class="data-table"><thead><tr>
    <th>Nome</th><th>CPF</th><th>Idade</th><th>Telefone</th><th>Plano</th><th>Acoes</th>
  </tr></thead><tbody>
  ${arr.map(p => `<tr>
    <td><strong>${p.nome_completo}</strong></td>
    <td>${p.cpf||'-'}</td>
    <td>${p.idade!=null ? p.idade+' anos' : '-'}</td>
    <td>${p.telefone||'-'}</td>
    <td>${p.plano_odonto||'<span style="color:var(--c-text-3)">Particular</span>'}</td>
    <td><div class="table-actions">
      <button class="btn-icon" onclick="navigate('prontuarios')" title="Prontuario"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></button>
      <button class="btn-icon" onclick="toast('Edicao em breve','info')" title="Editar"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></button>
    </div></td>
  </tr>`).join('')}</tbody></table>`;
}

// ── DENTISTAS
async function load_dentistas() {
  const r = await api_fetch('/dentistas/?limit=50&ordering=nome_completo');
  const arr = extract_list(r);
  if (!arr.length) {
    $('grid-dentistas').innerHTML = `<div class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
      <p>Nenhum dentista cadastrado. <a href="#" onclick="open_modal_novo_dentista(); return false;">Adicionar o primeiro</a></p>
    </div>`;
    return;
  }
  $('grid-dentistas').innerHTML = arr.map(d => {
    const initials = d.nome_completo.split(' ').slice(0,2).map(n=>n[0]).join('').toUpperCase();
    const horario = (d.horario_inicio && d.horario_fim) ? `${d.horario_inicio.slice(0,5)} - ${d.horario_fim.slice(0,5)}` : '';
    const dias = d.dias_trabalho ? d.dias_trabalho.split(',').map(v => ({SEG:'Seg',TER:'Ter',QUA:'Qua',QUI:'Qui',SEX:'Sex',SAB:'Sab'}[v]||v)).join(' · ') : '';
    const email = d.email ? `<div class="dentista-info" style="margin-top:.2rem">${d.email}</div>` : '';
    return `<div class="dentista-card">
      <div class="dentista-card-top">
        <div class="dentista-avatar">${initials}</div>
        <button class="btn-icon dentista-edit-btn" onclick="open_modal_editar_dentista(${d.id})" title="Editar dentista">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </button>
      </div>
      <div class="dentista-name">Dr(a). ${d.nome_completo}</div>
      <div class="dentista-cro">CRO ${d.cro}</div>
      <div class="dentista-spec">${d.especialidade}</div>
      ${horario ? `<div class="dentista-info"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;margin-right:4px;vertical-align:middle"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>${horario}${dias ? ' &nbsp;·&nbsp; '+dias : ''}</div>` : ''}
      ${d.telefone ? `<div class="dentista-info" style="margin-top:.3rem"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="width:12px;height:12px;margin-right:4px;vertical-align:middle"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.71 3.35 2 2 0 0 1 3.7 1h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L7.91 8.6a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/></svg>${d.telefone}</div>` : ''}
      ${email}
    </div>`;
  }).join('');
}

// ── MODAL NOVO DENTISTA
function open_modal_novo_dentista() {
  $('modal-title').textContent = 'Novo Dentista';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar';
  $('modal-body').innerHTML = _dentista_form_html({});
  show($('modal-overlay'));

  $('modal-save').onclick = async () => {
    const dados = _dentista_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/dentistas/', { method: 'POST', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Dentista cadastrado com sucesso!', 'success'); close_modal(); load_dentistas();
    } else {
      toast('Erro ao cadastrar. Verifique o CRO (deve ser unico).', 'error');
    }
  };
}

// ── MODAL EDITAR DENTISTA
async function open_modal_editar_dentista(id) {
  $('modal-title').textContent = 'Editar Dentista';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar Alteracoes';
  show($('modal-overlay'));

  const d = await api_fetch(`/dentistas/${id}/`);
  if (!d) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar.</p></div>'; return; }

  $('modal-body').innerHTML = _dentista_form_html(d);

  $('modal-save').onclick = async () => {
    const dados = _dentista_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/dentistas/${id}/`, { method: 'PATCH', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar Alteracoes'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Dentista atualizado com sucesso!', 'success'); close_modal(); load_dentistas();
    } else {
      toast('Erro ao atualizar dentista.', 'error');
    }
  };
}

// ── HELPERS DENTISTA FORM
const DIAS_OPTS = [
  { v:'SEG', l:'Segunda' }, { v:'TER', l:'Terca' }, { v:'QUA', l:'Quarta' },
  { v:'QUI', l:'Quinta'  }, { v:'SEX', l:'Sexta'  }, { v:'SAB', l:'Sabado' },
];

function _dentista_form_html(d) {
  const dias_sel = d.dias_trabalho ? d.dias_trabalho.split(',') : [];
  return `<div class="modal-form">
    <div class="form-row">
      <div class="form-group">
        <label>Nome Completo *</label>
        <input type="text" id="nd-nome" placeholder="Nome completo" value="${d.nome_completo||''}" />
      </div>
      <div class="form-group">
        <label>CRO *</label>
        <input type="text" id="nd-cro" placeholder="Ex: SP-123456" value="${d.cro||''}" />
      </div>
    </div>
    <div class="form-group">
      <label>Especialidade *</label>
      <select id="nd-esp">
        <option value="">Selecione...</option>
        ${[
          'Clinico Geral','Ortodontista','Endodontista','Periodontista',
          'Implantodontista','Cirurgiao Bucomaxilofacial','Odontopediatra',
          'Protesista','Cirurgiao Dentista','Estetica Dental','Radiologista'
        ].map(e => `<option value="${e}" ${d.especialidade===e?'selected':''}>${e}</option>`).join('')}
      </select>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Telefone *</label>
        <input type="tel" id="nd-tel" placeholder="(00) 00000-0000" value="${d.telefone||''}" />
      </div>
      <div class="form-group">
        <label>E-mail</label>
        <input type="email" id="nd-email" placeholder="email@exemplo.com" value="${d.email||''}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Horario Inicio</label>
        <input type="time" id="nd-hin" value="${d.horario_inicio||''}" />
      </div>
      <div class="form-group">
        <label>Horario Fim</label>
        <input type="time" id="nd-hfim" value="${d.horario_fim||''}" />
      </div>
    </div>
    <div class="form-group">
      <label>Dias de Trabalho</label>
      <div class="dias-grid">
        ${DIAS_OPTS.map(d2 => `
          <label class="dia-check">
            <input type="checkbox" value="${d2.v}" ${dias_sel.includes(d2.v)?'checked':''} />
            <span>${d2.l}</span>
          </label>`).join('')}
      </div>
    </div>
  </div>`;
}

function _dentista_form_collect() {
  const nome = $('nd-nome').value.trim();
  const cro  = $('nd-cro').value.trim();
  const esp  = $('nd-esp').value;
  const tel  = $('nd-tel').value.trim();
  if (!nome || !cro || !esp || !tel) {
    toast('Preencha os campos obrigatorios: nome, CRO, especialidade e telefone.', 'warn');
    return null;
  }
  const dias = Array.from(document.querySelectorAll('.dia-check input:checked')).map(c => c.value).join(',');
  return {
    nome_completo: nome, cro, especialidade: esp, telefone: tel,
    email:         $('nd-email').value || null,
    horario_inicio: $('nd-hin').value  || null,
    horario_fim:   $('nd-hfim').value  || null,
    dias_trabalho: dias || null,
  };
}

// ── PRONTUARIOS
async function load_prontuarios() {
  const r = await api_fetch('/prontuarios/?limit=50&ordering=-data_atendimento');
  const arr = extract_list(r);
  const q = ($('filter-prontuarios').value||'').toLowerCase();
  const filtered = q ? arr.filter(p => JSON.stringify(p).toLowerCase().includes(q)) : arr;
  if (!filtered.length) {
    $('tabela-prontuarios').innerHTML = `<div class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
      <p>Nenhum prontuario encontrado. <a href="#" onclick="open_modal_novo_prontuario(); return false;">Criar o primeiro</a></p>
    </div>`;
    return;
  }
  $('tabela-prontuarios').innerHTML = `<table class="data-table"><thead><tr>
    <th>Data</th><th>Paciente</th><th>Dentista</th><th>Diagnostico</th><th>Proxima Consulta</th><th>Acoes</th>
  </tr></thead><tbody>
  ${filtered.map(p => {
    const pac = p.paciente_nome || (p.paciente && typeof p.paciente==='object' ? p.paciente.nome_completo : '') || '-';
    const den = p.dentista_nome || (p.dentista && typeof p.dentista==='object' ? p.dentista.nome_completo : '') || '-';
    const diag = p.diagnostico || '-';
    return `<tr>
      <td>${fmt_date(p.data_atendimento)}</td>
      <td><strong>${pac}</strong></td>
      <td>${den}</td>
      <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${diag}">${diag}</td>
      <td>${p.proxima_consulta ? fmt_date(p.proxima_consulta) : '<span style="color:var(--c-text-3)">-</span>'}</td>
      <td><div class="table-actions">
        <button class="btn-icon" onclick="open_modal_ver_prontuario(${p.id})" title="Ver detalhes">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
        </button>
        <button class="btn-icon" onclick="open_modal_editar_prontuario(${p.id})" title="Editar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </button>
      </div></td>
    </tr>`;
  }).join('')}</tbody></table>`;
}

// ── VER PRONTUÁRIO (detalhes)
async function open_modal_ver_prontuario(id) {
  $('modal-title').textContent = 'Ficha do Prontuario';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = 'none';
  show($('modal-overlay'));

  const p = await api_fetch(`/prontuarios/${id}/`);
  if (!p) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar prontuario.</p></div>'; return; }

  const pac = p.paciente_nome || (p.paciente && typeof p.paciente==='object' ? p.paciente.nome_completo : '') || '-';
  const den = p.dentista_nome || (p.dentista && typeof p.dentista==='object' ? p.dentista.nome_completo : '') || '-';

  $('modal-body').innerHTML = `
    <div class="pront-detail">
      <div class="pront-detail-header">
        <div class="pront-detail-meta">
          <div class="pront-meta-item"><span class="pront-meta-label">Paciente</span><span class="pront-meta-value">${pac}</span></div>
          <div class="pront-meta-item"><span class="pront-meta-label">Dentista</span><span class="pront-meta-value">${den}</span></div>
          <div class="pront-meta-item"><span class="pront-meta-label">Data de Atendimento</span><span class="pront-meta-value">${fmt_date(p.data_atendimento)}</span></div>
          <div class="pront-meta-item"><span class="pront-meta-label">Proxima Consulta</span><span class="pront-meta-value">${p.proxima_consulta ? fmt_date(p.proxima_consulta) : 'Nao agendada'}</span></div>
        </div>
      </div>
      <div class="pront-section">
        <h3 class="pront-section-title">Anamnese</h3>
        <p class="pront-text">${p.anamnese || '<em>Nao informado</em>'}</p>
      </div>
      <div class="pront-section">
        <h3 class="pront-section-title">Diagnostico</h3>
        <p class="pront-text">${p.diagnostico || '<em>Nao informado</em>'}</p>
      </div>
      ${p.tratamento_plano ? `<div class="pront-section">
        <h3 class="pront-section-title">Plano de Tratamento</h3>
        <p class="pront-text">${p.tratamento_plano}</p>
      </div>` : ''}
      ${p.prescricao ? `<div class="pront-section">
        <h3 class="pront-section-title">Prescricao</h3>
        <p class="pront-text pront-prescricao">${p.prescricao}</p>
      </div>` : ''}
      ${p.observacoes ? `<div class="pront-section">
        <h3 class="pront-section-title">Observacoes</h3>
        <p class="pront-text">${p.observacoes}</p>
      </div>` : ''}
    </div>`;

  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Fechar';
  $('modal-save').textContent = 'Editar';
  $('modal-save').onclick = () => { close_modal(); open_modal_editar_prontuario(id); };
}

// ── NOVO PRONTUÁRIO (criação)
async function open_modal_novo_prontuario(paciente_id_pre) {
  $('modal-title').textContent = 'Novo Prontuario';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando dados...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar';
  show($('modal-overlay'));

  const [pacs, dents] = await Promise.all([
    api_fetch('/pacientes/?limit=300&ordering=nome_completo'),
    api_fetch('/dentistas/?limit=50&ordering=nome_completo'),
  ]);
  const pac_arr  = extract_list(pacs);
  const dent_arr = extract_list(dents);
  const hoje = new Date().toISOString().slice(0, 10);

  $('modal-body').innerHTML = `<div class="modal-form">
    <div class="form-row">
      <div class="form-group">
        <label>Paciente *</label>
        <select id="np-pac">
          <option value="">Selecione o paciente...</option>
          ${pac_arr.map(p => `<option value="${p.id}" ${p.id == paciente_id_pre ? 'selected' : ''}>${p.nome_completo}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>Dentista *</label>
        <select id="np-dent">
          <option value="">Selecione o dentista...</option>
          ${dent_arr.map(d => `<option value="${d.id}">Dr(a). ${d.nome_completo} — ${d.especialidade}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>Data de Atendimento *</label>
      <input type="date" id="np-data" value="${hoje}" max="${hoje}" />
    </div>
    <div class="form-group">
      <label>Anamnese *</label>
      <textarea id="np-anamnese" placeholder="Historico do paciente, queixas, historico medico, alergias..." style="min-height:90px"></textarea>
    </div>
    <div class="form-group">
      <label>Diagnostico *</label>
      <textarea id="np-diag" placeholder="Diagnostico clinico e odontologico..." style="min-height:80px"></textarea>
    </div>
    <div class="form-group">
      <label>Plano de Tratamento</label>
      <textarea id="np-plano" placeholder="Descricao dos procedimentos planejados..." style="min-height:75px"></textarea>
    </div>
    <div class="form-group">
      <label>Prescricao</label>
      <textarea id="np-presc" placeholder="Medicamentos receitados, posologia..." style="min-height:70px"></textarea>
    </div>
    <div class="form-group">
      <label>Proxima Consulta</label>
      <input type="date" id="np-prox" min="${hoje}" />
    </div>
  </div>`;

  $('modal-save').onclick = async () => {
    const pac_id   = parseInt($('np-pac').value);
    const dent_id  = parseInt($('np-dent').value);
    const data_at  = $('np-data').value;
    const anamnese = $('np-anamnese').value.trim();
    const diag     = $('np-diag').value.trim();
    if (!pac_id || !dent_id || !data_at || !anamnese || !diag) {
      toast('Preencha os campos obrigatorios: paciente, dentista, data, anamnese e diagnostico.', 'warn'); return;
    }
    const body = {
      paciente: pac_id, dentista: dent_id,
      data_atendimento: data_at,
      anamnese, diagnostico: diag,
      tratamento_plano: $('np-plano').value || null,
      prescricao:       $('np-presc').value || null,
      proxima_consulta: $('np-prox').value  || null,
    };
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/prontuarios/', { method: 'POST', body: JSON.stringify(body) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Prontuario criado com sucesso!', 'success');
      close_modal();
      load_prontuarios();
    } else {
      toast('Erro ao criar prontuario. Verifique os dados.', 'error');
    }
  };
}

// ── EDITAR PRONTUÁRIO
async function open_modal_editar_prontuario(id) {
  $('modal-title').textContent = 'Editar Prontuario';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar Alteracoes';
  show($('modal-overlay'));

  const [p, pacs, dents] = await Promise.all([
    api_fetch(`/prontuarios/${id}/`),
    api_fetch('/pacientes/?limit=300&ordering=nome_completo'),
    api_fetch('/dentistas/?limit=50&ordering=nome_completo'),
  ]);
  if (!p) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar.</p></div>'; return; }

  const pac_arr  = extract_list(pacs);
  const dent_arr = extract_list(dents);
  const pac_id_atual  = p.paciente && typeof p.paciente==='object' ? p.paciente.id : p.paciente;
  const dent_id_atual = p.dentista && typeof p.dentista==='object' ? p.dentista.id : p.dentista;
  const hoje = new Date().toISOString().slice(0, 10);

  $('modal-body').innerHTML = `<div class="modal-form">
    <div class="form-row">
      <div class="form-group">
        <label>Paciente *</label>
        <select id="ep-pac">
          ${pac_arr.map(pa => `<option value="${pa.id}" ${pa.id == pac_id_atual ? 'selected' : ''}>${pa.nome_completo}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>Dentista *</label>
        <select id="ep-dent">
          ${dent_arr.map(d => `<option value="${d.id}" ${d.id == dent_id_atual ? 'selected' : ''}>Dr(a). ${d.nome_completo} — ${d.especialidade}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>Data de Atendimento *</label>
      <input type="date" id="ep-data" value="${p.data_atendimento||hoje}" max="${hoje}" />
    </div>
    <div class="form-group">
      <label>Anamnese *</label>
      <textarea id="ep-anamnese" style="min-height:90px">${p.anamnese||''}</textarea>
    </div>
    <div class="form-group">
      <label>Diagnostico *</label>
      <textarea id="ep-diag" style="min-height:80px">${p.diagnostico||''}</textarea>
    </div>
    <div class="form-group">
      <label>Plano de Tratamento</label>
      <textarea id="ep-plano" style="min-height:75px">${p.tratamento_plano||''}</textarea>
    </div>
    <div class="form-group">
      <label>Prescricao</label>
      <textarea id="ep-presc" style="min-height:70px">${p.prescricao||''}</textarea>
    </div>
    <div class="form-group">
      <label>Proxima Consulta</label>
      <input type="date" id="ep-prox" value="${p.proxima_consulta||''}" min="${hoje}" />
    </div>
  </div>`;

  $('modal-save').onclick = async () => {
    const pac_id   = parseInt($('ep-pac').value);
    const dent_id  = parseInt($('ep-dent').value);
    const data_at  = $('ep-data').value;
    const anamnese = $('ep-anamnese').value.trim();
    const diag     = $('ep-diag').value.trim();
    if (!pac_id || !dent_id || !data_at || !anamnese || !diag) {
      toast('Preencha os campos obrigatorios.', 'warn'); return;
    }
    const body = {
      paciente: pac_id, dentista: dent_id,
      data_atendimento: data_at,
      anamnese, diagnostico: diag,
      tratamento_plano: $('ep-plano').value || null,
      prescricao:       $('ep-presc').value || null,
      proxima_consulta: $('ep-prox').value  || null,
    };
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/prontuarios/${id}/`, { method: 'PATCH', body: JSON.stringify(body) });
    $('modal-save').textContent = 'Salvar Alteracoes'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Prontuario atualizado com sucesso!', 'success');
      close_modal();
      load_prontuarios();
    } else {
      toast('Erro ao atualizar prontuario.', 'error');
    }
  };
}

// ── PROCEDIMENTOS
const CAT = { preventivo:'Preventivo', restaurador:'Restaurador', endodontia:'Endodontia',
  periodontia:'Periodontia', ortodontia:'Ortodontia', implante:'Implante',
  cirurgia:'Cirurgia', estetico:'Estetico', pediatrico:'Pediatrico', outro:'Outro' };

async function load_procedimentos() {
  const cat = $('filter-proc-cat').value;
  let url = '/procedimentos/?limit=100&ordering=categoria,nome';
  if (cat) url += `&categoria=${cat}`;
  const r = await api_fetch(url);
  const arr = extract_list(r);
  const q = ($('filter-proc').value||'').toLowerCase();
  const filtered = q ? arr.filter(p => (p.nome+p.categoria+p.descricao).toLowerCase().includes(q)) : arr;
  if (!filtered.length) {
    $('tabela-procedimentos').innerHTML = `<div class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>
      <p>Nenhum procedimento encontrado. <a href="#" onclick="open_modal_novo_proc(); return false;">Adicionar o primeiro</a></p>
    </div>`;
    return;
  }
  $('tabela-procedimentos').innerHTML = `<table class="data-table"><thead><tr>
    <th>Procedimento</th><th>Categoria</th><th>Valor</th><th>Duracao</th><th>Status</th><th>Acoes</th>
  </tr></thead><tbody>
  ${filtered.map(p => `<tr>
    <td>
      <strong>${p.nome}</strong>
      ${p.codigo_tuss ? `<br><span style="font-size:.7rem;color:var(--c-text-3)">TUSS: ${p.codigo_tuss}</span>` : ''}
      ${p.descricao ? `<br><span style="font-size:.73rem;color:var(--c-text-3);display:block;max-width:220px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${p.descricao}">${p.descricao}</span>` : ''}
    </td>
    <td><span class="badge badge-cat-${p.categoria}">${CAT[p.categoria]||p.categoria}</span></td>
    <td><strong>${fmt_money(p.valor_padrao)}</strong></td>
    <td>${p.duracao_media} min</td>
    <td><span class="badge ${p.ativo ? 'badge-realizada' : 'badge-cancelado'}">${p.ativo ? 'Ativo' : 'Inativo'}</span></td>
    <td><div class="table-actions">
      <button class="btn-icon" onclick="open_modal_editar_proc(${p.id})" title="Editar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
      </button>
      <button class="btn-icon" onclick="toggle_proc_ativo(${p.id}, ${p.ativo})" title="${p.ativo ? 'Desativar' : 'Ativar'}" style="color:${p.ativo ? 'var(--c-amber)' : 'var(--c-green)'}">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">${p.ativo
          ? '<circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>'
          : '<polyline points="20 6 9 17 4 12"/>'}
        </svg>
      </button>
    </div></td>
  </tr>`).join('')}</tbody></table>`;
}

async function toggle_proc_ativo(id, ativo_atual) {
  const acao = ativo_atual ? 'desativar' : 'ativar';
  if (!confirm(`Deseja ${acao} este procedimento?`)) return;
  const r = await api_fetch(`/procedimentos/${id}/`, { method: 'PATCH', body: JSON.stringify({ ativo: !ativo_atual }) });
  if (r && r.id !== undefined) {
    toast(`Procedimento ${!ativo_atual ? 'ativado' : 'desativado'}!`, !ativo_atual ? 'success' : 'warn');
    load_procedimentos();
  } else { toast('Erro ao alterar status.', 'error'); }
}

// ── MODAL NOVO PROCEDIMENTO
function open_modal_novo_proc() {
  $('modal-title').textContent = 'Novo Procedimento';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar';
  $('modal-body').innerHTML = _proc_form_html({});
  show($('modal-overlay'));

  $('modal-save').onclick = async () => {
    const dados = _proc_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/procedimentos/', { method: 'POST', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Procedimento cadastrado!', 'success'); close_modal(); load_procedimentos();
    } else { toast('Erro ao cadastrar procedimento.', 'error'); }
  };
}

// ── MODAL EDITAR PROCEDIMENTO
async function open_modal_editar_proc(id) {
  $('modal-title').textContent = 'Editar Procedimento';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar Alteracoes';
  show($('modal-overlay'));

  const p = await api_fetch(`/procedimentos/${id}/`);
  if (!p) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar.</p></div>'; return; }

  $('modal-body').innerHTML = _proc_form_html(p);

  $('modal-save').onclick = async () => {
    const dados = _proc_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/procedimentos/${id}/`, { method: 'PATCH', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar Alteracoes'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Procedimento atualizado!', 'success'); close_modal(); load_procedimentos();
    } else { toast('Erro ao atualizar procedimento.', 'error'); }
  };
}

// ── HELPERS PROCEDIMENTO FORM
function _proc_form_html(p) {
  const cats = Object.entries(CAT);
  return `<div class="modal-form">
    <div class="form-group">
      <label>Nome do Procedimento *</label>
      <input type="text" id="pc-nome" placeholder="Ex: Restauracao de Resina" value="${p.nome||''}" />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Categoria *</label>
        <select id="pc-cat">
          <option value="">Selecione...</option>
          ${cats.map(([v,l]) => `<option value="${v}" ${p.categoria===v?'selected':''}>${l}</option>`).join('')}
        </select>
      </div>
      <div class="form-group">
        <label>Valor Padrao (R$) *</label>
        <input type="number" id="pc-valor" placeholder="0,00" min="0" step="0.01" value="${p.valor_padrao||''}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Duracao Media (min)</label>
        <input type="number" id="pc-dur" min="5" max="480" step="5" value="${p.duracao_media||60}" />
      </div>
      <div class="form-group">
        <label>Codigo TUSS</label>
        <input type="text" id="pc-tuss" placeholder="Ex: 81000030" value="${p.codigo_tuss||''}" />
      </div>
    </div>
    <div class="form-group">
      <label>Descricao</label>
      <textarea id="pc-desc" placeholder="Descricao do procedimento, indicacoes..." style="min-height:80px">${p.descricao||''}</textarea>
    </div>
    <div class="form-group">
      <label class="proc-ativo-label">
        <span>Procedimento Ativo</span>
        <label class="toggle-switch">
          <input type="checkbox" id="pc-ativo" ${(p.ativo===undefined || p.ativo) ? 'checked' : ''} />
          <span class="toggle-slider"></span>
        </label>
      </label>
    </div>
  </div>`;
}

function _proc_form_collect() {
  const nome  = $('pc-nome').value.trim();
  const cat   = $('pc-cat').value;
  const valor = parseFloat($('pc-valor').value);
  if (!nome || !cat || isNaN(valor) || valor < 0) {
    toast('Preencha os campos obrigatorios: nome, categoria e valor.', 'warn');
    return null;
  }
  return {
    nome, categoria: cat, valor_padrao: valor,
    duracao_media: parseInt($('pc-dur').value) || 60,
    codigo_tuss:  $('pc-tuss').value || null,
    descricao:    $('pc-desc').value || null,
    ativo:        $('pc-ativo').checked,
  };
}

// ── FINANCEIRO
async function load_financeiro() {
  const tipo   = $('filter-fin-tipo').value;
  const status = $('filter-fin-status').value;
  let url = '/financeiro/?limit=50&ordering=-criado_em';
  if (tipo)   url += `&tipo=${tipo}`;
  if (status) url += `&status=${status}`;
  const [r, fin_r] = await Promise.all([api_fetch(url), api_fetch('/financeiro/resumo/')]);

  if (fin_r) {
    const rec   = parseFloat(fin_r.receitas?.total ?? fin_r.receitas ?? 0);
    const des   = parseFloat(fin_r.despesas?.total ?? fin_r.despesas ?? 0);
    const pen   = parseFloat(fin_r.pendentes?.total ?? fin_r.pendentes ?? 0);
    const saldo = parseFloat(fin_r.saldo ?? (rec - des));
    $('fin-pg-receitas').textContent  = fmt_money(rec);
    $('fin-pg-despesas').textContent  = fmt_money(des);
    $('fin-pg-pendentes').textContent = fmt_money(pen);
    $('fin-pg-saldo').textContent     = fmt_money(saldo);
  }

  const arr = extract_list(r);
  if (!arr.length) {
    $('tabela-financeiro').innerHTML = `<div class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
      <p>Nenhum lancamento. <a href="#" onclick="open_modal_novo_lancamento(); return false;">Adicionar o primeiro</a></p>
    </div>`;
    return;
  }
  const tmap = { receita:'Receita', despesa:'Despesa' };
  const smap = { pendente:'Pendente', pago:'Pago', atrasado:'Atrasado', cancelado:'Cancelado' };
  const fmap = { dinheiro:'Dinheiro', debito:'Debito', credito:'Credito', pix:'PIX', boleto:'Boleto', convenio:'Convenio', outro:'Outro' };
  $('tabela-financeiro').innerHTML = `<table class="data-table"><thead><tr>
    <th>Tipo</th><th>Descricao</th><th>Valor</th><th>Forma Pag.</th><th>Vencimento</th><th>Status</th><th>Acoes</th>
  </tr></thead><tbody>
  ${arr.map(f => `<tr>
    <td>${status_badge(f.tipo, tmap)}</td>
    <td>
      <strong>${f.descricao}</strong>
      ${f.paciente_nome ? `<br><span style="font-size:.72rem;color:var(--c-text-3)">${f.paciente_nome}</span>` : ''}
    </td>
    <td>
      <strong>${fmt_money(f.valor_liquido !== undefined ? f.valor_liquido : f.valor)}</strong>
      ${parseFloat(f.desconto||0)>0 ? `<br><span style="font-size:.7rem;color:var(--c-text-3)">-${fmt_money(f.desconto)}</span>` : ''}
    </td>
    <td>${fmap[f.forma_pagamento]||f.forma_pagamento||'-'}</td>
    <td>${fmt_date(f.vencimento)}</td>
    <td>${status_badge(f.status, smap)}</td>
    <td><div class="table-actions">
      <button class="btn-icon" onclick="open_modal_editar_lancamento(${f.id})" title="Editar">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
      </button>
      ${f.status === 'pendente' || f.status === 'atrasado' ? `
      <button class="btn-icon" onclick="marcar_pago(${f.id})" title="Marcar como Pago" style="color:var(--c-green)">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
      </button>` : ''}
    </div></td>
  </tr>`).join('')}</tbody></table>`;
}

async function marcar_pago(id) {
  const hoje = new Date().toISOString().slice(0,10);
  const r = await api_fetch(`/financeiro/${id}/`, {
    method: 'PATCH',
    body: JSON.stringify({ status: 'pago', pago_em: hoje })
  });
  if (r && r.id) { toast('Lancamento marcado como pago!', 'success'); load_financeiro(); }
  else toast('Erro ao atualizar status.', 'error');
}

// ── MODAL NOVO LANCAMENTO
async function open_modal_novo_lancamento() {
  $('modal-title').textContent = 'Novo Lancamento';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar';
  show($('modal-overlay'));

  const pacs = await api_fetch('/pacientes/?limit=300&ordering=nome_completo');
  const pac_arr = extract_list(pacs);
  const hoje = new Date().toISOString().slice(0,10);

  $('modal-body').innerHTML = _lancamento_form_html({}, pac_arr, hoje);

  $('modal-save').onclick = async () => {
    const dados = _lancamento_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/financeiro/', { method: 'POST', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) { toast('Lancamento criado!', 'success'); close_modal(); load_financeiro(); }
    else toast('Erro ao criar lancamento.', 'error');
  };
}

// ── MODAL EDITAR LANCAMENTO
async function open_modal_editar_lancamento(id) {
  $('modal-title').textContent = 'Editar Lancamento';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar Alteracoes';
  show($('modal-overlay'));

  const [f, pacs] = await Promise.all([
    api_fetch(`/financeiro/${id}/`),
    api_fetch('/pacientes/?limit=300&ordering=nome_completo'),
  ]);
  if (!f) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar.</p></div>'; return; }

  const pac_arr = extract_list(pacs);
  const hoje = new Date().toISOString().slice(0,10);
  $('modal-body').innerHTML = _lancamento_form_html(f, pac_arr, hoje);

  $('modal-save').onclick = async () => {
    const dados = _lancamento_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/financeiro/${id}/`, { method: 'PATCH', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar Alteracoes'; $('modal-save').disabled = false;
    if (r && r.id) { toast('Lancamento atualizado!', 'success'); close_modal(); load_financeiro(); }
    else toast('Erro ao atualizar.', 'error');
  };
}

// ── HELPERS LANCAMENTO FORM
function _lancamento_form_html(f, pac_arr, hoje) {
  const pac_id = f.paciente && typeof f.paciente==='object' ? f.paciente.id : f.paciente;
  return `<div class="modal-form">
    <div class="form-row">
      <div class="form-group">
        <label>Tipo *</label>
        <select id="lc-tipo">
          <option value="receita" ${f.tipo==='receita'||!f.tipo?'selected':''}>Receita</option>
          <option value="despesa" ${f.tipo==='despesa'?'selected':''}>Despesa</option>
        </select>
      </div>
      <div class="form-group">
        <label>Status</label>
        <select id="lc-status">
          <option value="pendente" ${f.status==='pendente'||!f.status?'selected':''}>Pendente</option>
          <option value="pago"     ${f.status==='pago'?'selected':''}>Pago</option>
          <option value="atrasado" ${f.status==='atrasado'?'selected':''}>Atrasado</option>
          <option value="cancelado" ${f.status==='cancelado'?'selected':''}>Cancelado</option>
        </select>
      </div>
    </div>
    <div class="form-group">
      <label>Descricao *</label>
      <input type="text" id="lc-desc" placeholder="Ex: Consulta de avaliacao, Aluguel..." value="${f.descricao||''}" />
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Valor (R$) *</label>
        <input type="number" id="lc-valor" min="0" step="0.01" placeholder="0,00" value="${f.valor||''}" />
      </div>
      <div class="form-group">
        <label>Desconto (R$)</label>
        <input type="number" id="lc-desc2" min="0" step="0.01" placeholder="0,00" value="${f.desconto||0}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Forma de Pagamento</label>
        <select id="lc-forma">
          <option value="dinheiro"  ${f.forma_pagamento==='dinheiro'||!f.forma_pagamento?'selected':''}>Dinheiro</option>
          <option value="debito"    ${f.forma_pagamento==='debito'?'selected':''}>Cartao Debito</option>
          <option value="credito"   ${f.forma_pagamento==='credito'?'selected':''}>Cartao Credito</option>
          <option value="pix"       ${f.forma_pagamento==='pix'?'selected':''}>PIX</option>
          <option value="boleto"    ${f.forma_pagamento==='boleto'?'selected':''}>Boleto</option>
          <option value="convenio"  ${f.forma_pagamento==='convenio'?'selected':''}>Convenio</option>
          <option value="outro"     ${f.forma_pagamento==='outro'?'selected':''}>Outro</option>
        </select>
      </div>
      <div class="form-group">
        <label>Vencimento</label>
        <input type="date" id="lc-venc" value="${f.vencimento||''}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Pago Em</label>
        <input type="date" id="lc-pago" value="${f.pago_em||''}" max="${hoje}" />
      </div>
      <div class="form-group">
        <label>Parcelas</label>
        <input type="number" id="lc-parc" min="1" max="60" value="${f.parcelas||1}" />
      </div>
    </div>
    <div class="form-group">
      <label>Paciente (opcional)</label>
      <select id="lc-pac">
        <option value="">Nenhum / Despesa geral</option>
        ${pac_arr.map(p => `<option value="${p.id}" ${p.id==pac_id?'selected':''}>${p.nome_completo}</option>`).join('')}
      </select>
    </div>
    <div class="form-group">
      <label>Observacoes</label>
      <textarea id="lc-obs" style="min-height:65px" placeholder="Observacoes adicionais...">${f.observacoes||''}</textarea>
    </div>
  </div>`;
}

function _lancamento_form_collect() {
  const desc  = $('lc-desc').value.trim();
  const valor = parseFloat($('lc-valor').value);
  if (!desc || isNaN(valor) || valor < 0) {
    toast('Preencha descricao e valor.', 'warn'); return null;
  }
  return {
    tipo:           $('lc-tipo').value,
    status:         $('lc-status').value,
    descricao:      desc,
    valor:          valor,
    desconto:       parseFloat($('lc-desc2').value) || 0,
    forma_pagamento: $('lc-forma').value,
    vencimento:     $('lc-venc').value  || null,
    pago_em:        $('lc-pago').value  || null,
    parcelas:       parseInt($('lc-parc').value) || 1,
    paciente:       parseInt($('lc-pac').value)  || null,
    observacoes:    $('lc-obs').value   || null,
  };
}

// ── ESTOQUE
// /estoque/alertas/ => { estoque_baixo:[], vencendo_em_30_dias:[], vencidos:[] }
async function load_estoque() {
  const cat      = $('filter-estoque-cat').value;
  const only_low = $('filter-estoque-baixo').checked;
  let arr = [];
  if (only_low) {
    const r = await api_fetch('/estoque/alertas/');
    if (r) arr = Array.isArray(r) ? r : (r.estoque_baixo || []);
  } else {
    let url = '/estoque/?limit=100&ordering=categoria,nome';
    if (cat) url += `&categoria=${cat}`;
    arr = extract_list(await api_fetch(url));
  }
  const q = ($('filter-estoque').value||'').toLowerCase();
  const filtered = q ? arr.filter(i => (i.nome||'').toLowerCase().includes(q)) : arr;
  if (!filtered.length) {
    $('tabela-estoque').innerHTML = `<div class="empty-state">
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/></svg>
      <p>Nenhum item encontrado. <a href="#" onclick="open_modal_novo_estoque(); return false;">Adicionar o primeiro</a></p>
    </div>`;
    return;
  }
  const CAT_EST = { anestesico:'Anestesico', instrumental:'Instrumental', resina:'Resina',
    cimento:'Cimento', descartavel:'Descartavel', radiografia:'Radiografia',
    higiene:'Higiene', medicamento:'Medicamento', outro:'Outro' };
  $('tabela-estoque').innerHTML = `<table class="data-table"><thead><tr>
    <th>Item</th><th>Categoria</th><th>Qtd</th><th>Minimo</th><th>Unidade</th><th>Validade</th><th>Status</th><th>Acoes</th>
  </tr></thead><tbody>
  ${filtered.map(i => {
    const alerta = i.estoque_baixo || (i.quantidade <= i.quantidade_minima);
    return `<tr>
      <td>
        <strong>${i.nome}</strong>
        ${i.fornecedor ? `<br><span style="font-size:.72rem;color:var(--c-text-3)">${i.fornecedor}</span>` : ''}
        ${i.localizacao ? `<br><span style="font-size:.7rem;color:var(--c-text-3)">&#128204; ${i.localizacao}</span>` : ''}
      </td>
      <td>${CAT_EST[i.categoria]||i.categoria}</td>
      <td><strong style="color:${alerta?'var(--c-amber)':'var(--c-text-1)'}">${i.quantidade}</strong></td>
      <td>${i.quantidade_minima}</td>
      <td>${i.unidade}</td>
      <td>${fmt_date(i.validade)}</td>
      <td><span class="badge ${alerta ? 'badge-alerta' : 'badge-ok'}">${alerta ? 'Alerta' : 'OK'}</span></td>
      <td><div class="table-actions">
        <button class="btn-icon" onclick="open_modal_ajustar_estoque(${i.id}, ${i.quantidade})" title="Ajustar Quantidade" style="color:var(--c-teal)">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
        </button>
        <button class="btn-icon" onclick="open_modal_editar_estoque(${i.id})" title="Editar">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
        </button>
      </div></td>
    </tr>`;
  }).join('')}</tbody></table>`;
}

// ── MODAL NOVO ITEM ESTOQUE
function open_modal_novo_estoque() {
  $('modal-title').textContent = 'Novo Item de Estoque';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar';
  $('modal-body').innerHTML = _estoque_form_html({});
  show($('modal-overlay'));

  $('modal-save').onclick = async () => {
    const dados = _estoque_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/estoque/', { method: 'POST', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) { toast('Item adicionado ao estoque!', 'success'); close_modal(); load_estoque(); }
    else toast('Erro ao adicionar item.', 'error');
  };
}

// ── MODAL EDITAR ITEM ESTOQUE
async function open_modal_editar_estoque(id) {
  $('modal-title').textContent = 'Editar Item de Estoque';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando...</p></div>';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Salvar Alteracoes';
  show($('modal-overlay'));

  const i = await api_fetch(`/estoque/${id}/`);
  if (!i) { $('modal-body').innerHTML = '<div class="empty-state"><p>Erro ao carregar.</p></div>'; return; }

  $('modal-body').innerHTML = _estoque_form_html(i);

  $('modal-save').onclick = async () => {
    const dados = _estoque_form_collect();
    if (!dados) return;
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/estoque/${id}/`, { method: 'PATCH', body: JSON.stringify(dados) });
    $('modal-save').textContent = 'Salvar Alteracoes'; $('modal-save').disabled = false;
    if (r && r.id) { toast('Item atualizado!', 'success'); close_modal(); load_estoque(); }
    else toast('Erro ao atualizar item.', 'error');
  };
}

// ── MODAL AJUSTAR QUANTIDADE
function open_modal_ajustar_estoque(id, qtd_atual) {
  $('modal-title').textContent = 'Ajustar Quantidade';
  $('modal-footer').style.display = '';
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-save').textContent = 'Confirmar';
  $('modal-body').innerHTML = `<div class="modal-form">
    <p style="font-size:.85rem;color:var(--c-text-2);margin-bottom:.5rem">Quantidade atual: <strong>${qtd_atual}</strong></p>
    <div class="form-group">
      <label>Operacao</label>
      <select id="aj-op">
        <option value="adicionar">&#43; Adicionar</option>
        <option value="remover">&#8722; Remover</option>
        <option value="definir">&#61; Definir quantidade exata</option>
      </select>
    </div>
    <div class="form-group">
      <label>Quantidade *</label>
      <input type="number" id="aj-qtd" min="0" placeholder="0" value="" />
    </div>
  </div>`;
  show($('modal-overlay'));

  $('modal-save').onclick = async () => {
    const qtd = parseInt($('aj-qtd').value);
    const op  = $('aj-op').value;
    if (isNaN(qtd) || qtd < 0) { toast('Informe uma quantidade valida.', 'warn'); return; }
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch(`/estoque/${id}/ajustar-quantidade/`, {
      method: 'PATCH',
      body: JSON.stringify({ quantidade: qtd, operacao: op }),
    });
    $('modal-save').textContent = 'Confirmar'; $('modal-save').disabled = false;
    if (r && r.id) { toast('Quantidade ajustada!', 'success'); close_modal(); load_estoque(); }
    else toast('Erro ao ajustar quantidade.', 'error');
  };
}

// ── HELPERS ESTOQUE FORM
function _estoque_form_html(i) {
  const cats_est = [
    ['anestesico','Anestesico'], ['instrumental','Instrumental'], ['resina','Resina'],
    ['cimento','Cimento'], ['descartavel','Descartavel'], ['radiografia','Radiografia'],
    ['higiene','Higiene'], ['medicamento','Medicamento'], ['outro','Outro'],
  ];
  return `<div class="modal-form">
    <div class="form-row">
      <div class="form-group">
        <label>Nome do Item *</label>
        <input type="text" id="es-nome" placeholder="Ex: Luva nitrilo M" value="${i.nome||''}" />
      </div>
      <div class="form-group">
        <label>Categoria *</label>
        <select id="es-cat">
          <option value="">Selecione...</option>
          ${cats_est.map(([v,l]) => `<option value="${v}" ${i.categoria===v?'selected':''}>${l}</option>`).join('')}
        </select>
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Quantidade Atual *</label>
        <input type="number" id="es-qtd" min="0" placeholder="0" value="${i.quantidade??''}" />
      </div>
      <div class="form-group">
        <label>Quantidade Minima (alerta)</label>
        <input type="number" id="es-qtdmin" min="0" placeholder="5" value="${i.quantidade_minima??5}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Unidade *</label>
        <input type="text" id="es-unidade" placeholder="Ex: caixa, unidade, ml" value="${i.unidade||''}" />
      </div>
      <div class="form-group">
        <label>Validade</label>
        <input type="date" id="es-val" value="${i.validade||''}" />
      </div>
    </div>
    <div class="form-row">
      <div class="form-group">
        <label>Fornecedor</label>
        <input type="text" id="es-forn" placeholder="Nome do fornecedor" value="${i.fornecedor||''}" />
      </div>
      <div class="form-group">
        <label>Custo Unitario (R$)</label>
        <input type="number" id="es-custo" min="0" step="0.01" placeholder="0,00" value="${i.custo_unitario||''}" />
      </div>
    </div>
    <div class="form-group">
      <label>Localizacao</label>
      <input type="text" id="es-loc" placeholder="Ex: Gaveta 3, Armario A" value="${i.localizacao||''}" />
    </div>
  </div>`;
}

function _estoque_form_collect() {
  const nome   = $('es-nome').value.trim();
  const cat    = $('es-cat').value;
  const qtd    = parseInt($('es-qtd').value);
  const unid   = $('es-unidade').value.trim();
  if (!nome || !cat || isNaN(qtd) || !unid) {
    toast('Preencha: nome, categoria, quantidade e unidade.', 'warn'); return null;
  }
  return {
    nome, categoria: cat, quantidade: qtd, unidade: unid,
    quantidade_minima: parseInt($('es-qtdmin').value) || 5,
    validade:     $('es-val').value   || null,
    fornecedor:   $('es-forn').value  || null,
    custo_unitario: parseFloat($('es-custo').value) || null,
    localizacao:  $('es-loc').value   || null,
  };
}

// ── MODAL NOVA CONSULTA
async function open_modal_nova_consulta() {
  $('modal-title').textContent = 'Nova Consulta';
  $('modal-body').innerHTML = '<div class="empty-state"><p>Carregando dados...</p></div>';
  show($('modal-overlay'));

  const [pacs, dents] = await Promise.all([
    api_fetch('/pacientes/?limit=200&ordering=nome_completo'),
    api_fetch('/dentistas/?limit=50&ordering=nome_completo'),
  ]);
  const pac_arr  = extract_list(pacs);
  const dent_arr = extract_list(dents);

  const amanha = new Date(); amanha.setDate(amanha.getDate()+1); amanha.setHours(9,0,0,0);
  const dt_default = amanha.toISOString().slice(0,16);

  $('modal-body').innerHTML = `<div class="modal-form">
    <div class="form-group"><label>Paciente *</label>
      <select id="nc-paciente"><option value="">Selecione o paciente...</option>
        ${pac_arr.map(p=>`<option value="${p.id}">${p.nome_completo}</option>`).join('')}
      </select></div>
    <div class="form-group"><label>Dentista *</label>
      <select id="nc-dentista"><option value="">Selecione o dentista...</option>
        ${dent_arr.map(d=>`<option value="${d.id}">Dr(a). ${d.nome_completo} — ${d.especialidade}</option>`).join('')}
      </select></div>
    <div class="form-row">
      <div class="form-group"><label>Data e Hora *</label><input type="datetime-local" id="nc-data" value="${dt_default}" /></div>
      <div class="form-group"><label>Tipo</label>
        <select id="nc-tipo">
          <option value="consulta">Consulta</option><option value="retorno">Retorno</option>
          <option value="emergencia">Emergencia</option><option value="avaliacao">Avaliacao</option>
        </select></div>
    </div>
    <div class="form-group"><label>Duracao (min)</label><input type="number" id="nc-dur" value="60" min="10" max="480" /></div>
    <div class="form-group"><label>Observacoes</label><textarea id="nc-obs" placeholder="Observacoes opcionais..."></textarea></div>
  </div>`;

  $('modal-save').onclick = async () => {
    const pac_id  = parseInt($('nc-paciente').value);
    const dent_id = parseInt($('nc-dentista').value);
    const data_h  = $('nc-data').value;
    if (!pac_id || !dent_id || !data_h) { toast('Preencha paciente, dentista e data/hora', 'warn'); return; }
    const body = {
      paciente: pac_id, dentista: dent_id, data_hora: data_h,
      tipo: $('nc-tipo').value, duracao_min: parseInt($('nc-dur').value)||60,
      observacoes: $('nc-obs').value || null,
    };
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/consultas/', { method: 'POST', body: JSON.stringify(body) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Consulta agendada com sucesso!', 'success'); close_modal();
      if (CURRENT_PAGE === 'consultas') load_consultas();
      else if (CURRENT_PAGE === 'dashboard') load_dashboard();
    } else { toast('Erro ao agendar. Verifique os dados.', 'error'); }
  };
}

// ── MODAL NOVO PACIENTE
function open_modal_novo_paciente() {
  $('modal-title').textContent = 'Novo Paciente';
  $('modal-body').innerHTML = `<div class="modal-form">
    <div class="form-group"><label>Nome Completo *</label><input type="text" id="np-nome" placeholder="Nome completo do paciente" /></div>
    <div class="form-row">
      <div class="form-group"><label>CPF *</label><input type="text" id="np-cpf" placeholder="000.000.000-00" /></div>
      <div class="form-group"><label>Data de Nascimento *</label><input type="date" id="np-nasc" /></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Telefone *</label><input type="tel" id="np-tel" placeholder="(00) 00000-0000" /></div>
      <div class="form-group"><label>Email</label><input type="email" id="np-email" placeholder="email@exemplo.com" /></div>
    </div>
    <div class="form-row">
      <div class="form-group"><label>Plano Odontologico</label><input type="text" id="np-plano" placeholder="Ex: Amil Dental" /></div>
      <div class="form-group"><label>N. do Convenio</label><input type="text" id="np-convenio" placeholder="Numero" /></div>
    </div>
    <div class="form-group"><label>Alergias</label><textarea id="np-alergias" placeholder="Alergias conhecidas..." style="min-height:60px"></textarea></div>
    <div class="form-group"><label>Endereco</label><textarea id="np-end" placeholder="Endereco completo..." style="min-height:55px"></textarea></div>
  </div>`;

  $('modal-save').onclick = async () => {
    const nome = $('np-nome').value.trim();
    const cpf  = $('np-cpf').value.trim();
    const nasc = $('np-nasc').value;
    const tel  = $('np-tel').value.trim();
    if (!nome || !cpf || !nasc || !tel) { toast('Preencha os campos obrigatorios (*)', 'warn'); return; }
    const body = {
      nome_completo: nome, cpf, data_nascimento: nasc, telefone: tel,
      email: $('np-email').value || null, plano_odonto: $('np-plano').value || null,
      convenio_numero: $('np-convenio').value || null, alergias: $('np-alergias').value || null,
      endereco: $('np-end').value || null,
    };
    $('modal-save').textContent = 'Salvando...'; $('modal-save').disabled = true;
    const r = await api_fetch('/pacientes/', { method: 'POST', body: JSON.stringify(body) });
    $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
    if (r && r.id) {
      toast('Paciente cadastrado com sucesso!', 'success'); close_modal(); load_pacientes();
    } else { toast('Erro ao cadastrar. Verifique o CPF (formato: 000.000.000-00).', 'error'); }
  };

  show($('modal-overlay'));
}

function close_modal() {
  hide($('modal-overlay'));
  $('modal-save').textContent = 'Salvar'; $('modal-save').disabled = false;
  $('modal-cancel').textContent = 'Cancelar';
  $('modal-footer').style.display = '';
}

// ── EVENTOS
$('modal-close').addEventListener('click', close_modal);
$('modal-cancel').addEventListener('click', close_modal);
$('modal-overlay').addEventListener('click', e => { if (e.target === $('modal-overlay')) close_modal(); });
$('btn-nova-consulta-dash').addEventListener('click', open_modal_nova_consulta);
$('btn-nova-consulta').addEventListener('click', open_modal_nova_consulta);
$('btn-novo-paciente').addEventListener('click', open_modal_novo_paciente);
$('btn-novo-prontuario').addEventListener('click', () => open_modal_novo_prontuario());
$('btn-novo-dentista').addEventListener('click', open_modal_novo_dentista);
$('btn-novo-proc').addEventListener('click', open_modal_novo_proc);
$('btn-novo-lancamento').addEventListener('click', open_modal_novo_lancamento);
$('btn-novo-item').addEventListener('click', open_modal_novo_estoque);
$('btn-logout').addEventListener('click', do_logout);
$('filter-consultas').addEventListener('input', load_consultas);
$('filter-consultas-status').addEventListener('change', load_consultas);
$('filter-consultas-data').addEventListener('change', load_consultas);
$('filter-pacientes').addEventListener('input', load_pacientes);
$('filter-prontuarios').addEventListener('input', load_prontuarios);
$('filter-proc').addEventListener('input', load_procedimentos);
$('filter-proc-cat').addEventListener('change', load_procedimentos);
$('filter-fin-tipo').addEventListener('change', load_financeiro);
$('filter-fin-status').addEventListener('change', load_financeiro);
$('filter-estoque').addEventListener('input', load_estoque);
$('filter-estoque-cat').addEventListener('change', load_estoque);
$('filter-estoque-baixo').addEventListener('change', load_estoque);
document.querySelectorAll('.card-link').forEach(a => {
  a.addEventListener('click', e => { e.preventDefault(); navigate(a.dataset.page); });
});

// ── INIT
async function init_app() {
  update_date(); setInterval(update_date, 60000);
  const me = await api_fetch('/usuarios/me/');
  if (me) {
    const nome = me.first_name ? `${me.first_name} ${me.last_name}`.trim() : me.username;
    $('user-name').textContent  = nome;
    $('user-role').textContent  = me.perfil_display || me.perfil || 'Usuario';
    $('user-avatar').textContent = (nome[0] || 'U').toUpperCase();
  }
  navigate('dashboard');
}

// ── STARTUP
if (ACCESS_TOKEN) { hide($('login-screen')); show($('app')); init_app(); }
