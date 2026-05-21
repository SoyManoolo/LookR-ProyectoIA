function getUserId() {
  let uid = localStorage.getItem('lookr_user_id');
  if (!uid) { uid = crypto.randomUUID(); localStorage.setItem('lookr_user_id', uid); }
  return uid;
}

async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

function switchTab(tab) {
  const tabs = ['texto','imagen','inspiracion','armario','favoritos'];
  document.querySelectorAll('.tab').forEach((t,i) => t.classList.toggle('active', tabs[i] === tab));
  tabs.forEach(t => document.getElementById('panel-'+t).classList.toggle('active', t === tab));
  clearResults();
  document.getElementById('analisis-result')?.classList.remove('visible');
  document.getElementById('analyzing-msg')?.classList.remove('active');
  if (tab === 'favoritos') renderFavoritos();
  if (tab === 'armario') cargarArmario();
}

document.getElementById('input-texto').addEventListener('keydown', e => { if (e.key === 'Enter') buscarTexto(); });

function setQuery(text) {
  document.getElementById('input-texto').value = text;
  buscarTexto();
}

function onFileSelect(e, ctx) {
  const file = e.target.files[0];
  if (!file) return;
  const reader = new FileReader();
  reader.onload = ev => {
    const preview = document.getElementById('preview-'+ctx);
    preview.src = ev.target.result;
    preview.style.display = 'block';
    document.getElementById('placeholder-'+ctx).style.display = 'none';
    document.getElementById('upload-zone-'+ctx).classList.add('filled');
    const btnMap = { buscar: 'btn-imagen', inspiracion: 'btn-inspiracion', armario: 'btn-armario' };
    document.getElementById(btnMap[ctx] || 'btn-'+ctx).disabled = false;
  };
  reader.readAsDataURL(file);
}

async function buscarTexto() {
  const q = document.getElementById('input-texto').value.trim();
  if (!q) return;
  setLoading(true);
  try { renderResults(await fetchJSON(`/recomendar/texto?query=${encodeURIComponent(q)}&top_k=6`)); }
  catch { showError('No se pudo conectar con el servidor.'); }
  finally { setLoading(false); }
}

async function buscarImagen() {
  const file = document.getElementById('file-buscar').files[0];
  if (!file) return;
  const modificador = document.getElementById('input-modificador').value.trim();
  setLoading(true);
  const form = new FormData();
  form.append('imagen', file);
  form.append('top_k', '6');
  if (modificador) { form.append('texto', modificador); form.append('alpha', '0.7'); }
  const url = modificador ? '/recomendar/combinado' : '/recomendar/imagen';
  try { renderResults(await fetchJSON(url, { method: 'POST', body: form })); }
  catch (e) { showError(e.message || 'No se pudo conectar con el servidor.'); }
  finally { setLoading(false); }
}

function setModificador(texto) {
  document.getElementById('input-modificador').value = texto;
}

async function descubrir() {
  const file = document.getElementById('file-inspiracion').files[0];
  if (!file) return;
  document.getElementById('btn-inspiracion').disabled = true;
  document.getElementById('analyzing-msg').classList.add('active');
  document.getElementById('analisis-result').classList.remove('visible');
  clearResults();
  clearNotices();
  const form = new FormData();
  form.append('imagen', file);
  try {
    const data = await fetchJSON('/descubrir', { method: 'POST', body: form });
    mostrarResultadoAnalisis(data);
    renderResults({ resultados: data.recomendaciones });
  } catch (e) { showError(`Error al analizar: ${e.message}`); }
  finally {
    document.getElementById('analyzing-msg').classList.remove('active');
    document.getElementById('btn-inspiracion').disabled = false;
  }
}

const WL_KEY = 'lookr_wishlist';
function getWishlist() { try { return JSON.parse(localStorage.getItem(WL_KEY)) || []; } catch { return []; } }
function saveWishlist(list) { localStorage.setItem(WL_KEY, JSON.stringify(list)); }
function isInWishlist(id) { return getWishlist().some(i => i.id === id); }

function toggleWishlist(r, titulo, btn = null) {
  let list = getWishlist();
  if (isInWishlist(r.id)) {
    list = list.filter(i => i.id !== r.id);
    if (btn) { btn.classList.remove('saved'); btn.title = 'Guardar en favoritos'; }
  } else {
    list.push({ id: r.id, nombre: titulo, descripcion: r.descripcion, imagen_url: r.imagen_url, categoria: r.categoria, estilo: r.estilo });
    if (btn) { btn.classList.add('saved'); btn.title = 'Quitar de favoritos'; }
  }
  saveWishlist(list);
  const saved = isInWishlist(r.id);
  document.querySelectorAll(`.card-heart[data-id="${r.id}"]`).forEach(b => {
    b.classList.toggle('saved', saved);
    const svg = b.querySelector('svg');
    if (svg) { svg.setAttribute('fill', saved ? '#ee0055' : 'none'); svg.setAttribute('stroke', saved ? '#ee0055' : 'currentColor'); }
  });
}

function limpiarFavoritos() { saveWishlist([]); renderFavoritos(); }

function renderFavoritos() {
  const list = getWishlist();
  const container = document.getElementById('cards-favoritos');
  const empty = document.getElementById('favoritos-empty');
  container.innerHTML = '';
  if (!list.length) { empty.classList.add('visible'); return; }
  empty.classList.remove('visible');
  list.forEach(r => container.appendChild(crearTarjeta(r, r.nombre, false, true)));
}

async function agregarAlArmario() {
  const file = document.getElementById('file-armario').files[0];
  if (!file) return;
  document.getElementById('btn-armario').disabled = true;
  document.getElementById('analyzing-armario').classList.add('active');
  const form = new FormData();
  form.append('imagen', file);
  try {
    await fetchJSON(`/armario/${getUserId()}`, { method: 'POST', body: form });
    await cargarArmario();
    document.getElementById('preview-armario').style.display = 'none';
    document.getElementById('placeholder-armario').style.display = '';
    document.getElementById('file-armario').value = '';
    document.getElementById('upload-zone-armario').classList.remove('filled');
  } catch (e) { showError(`Error: ${e.message}`); }
  finally {
    document.getElementById('analyzing-armario').classList.remove('active');
    document.getElementById('btn-armario').disabled = true;
  }
}

async function cargarArmario() {
  const grid = document.getElementById('armario-grid');
  const empty = document.getElementById('armario-empty');
  grid.innerHTML = '';
  try {
    const { items } = await fetchJSON(`/armario/${getUserId()}`);
    if (!items?.length) { empty.classList.add('visible'); return; }
    empty.classList.remove('visible');
    items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'armario-card';
      card.innerHTML = `
        <img class="armario-card-img" src="${item.imagen_url || ''}" alt="" onerror="this.style.background='var(--bg)'" />
        <div class="armario-card-body">
          <div class="armario-card-nombre"></div>
          <div class="armario-card-actions">
            <button class="btn-similares">Buscar similares</button>
            <button class="btn-eliminar-armario"><i data-lucide="x"></i></button>
          </div>
        </div>`;
      card.querySelector('.armario-card-nombre').textContent = item.nombre || '';
      card.querySelector('.btn-similares').addEventListener('click', () => buscarSimilaresArmario(item.id));
      card.querySelector('.btn-eliminar-armario').addEventListener('click', () => eliminarDeArmario(item.id));
      grid.appendChild(card);
      lucide.createIcons({ el: card });
    });
  } catch { empty.classList.add('visible'); }
}

async function buscarSimilaresArmario(itemId) {
  switchTab('texto');
  setLoading(true);
  try { renderResults(await fetchJSON(`/armario/${getUserId()}/${itemId}/similares`)); }
  catch { showError('No se pudieron cargar los similares.'); }
  finally { setLoading(false); }
}

async function eliminarDeArmario(itemId) {
  await fetch(`/armario/${getUserId()}/${itemId}`, { method: 'DELETE' });
  cargarArmario();
}

function mostrarResultadoAnalisis(data) {
  document.getElementById('analisis-img').src = document.getElementById('preview-inspiracion').src || data.imagen_url || '';
  document.getElementById('analisis-desc').textContent = data.descripcion;
  document.getElementById('analisis-estilo').textContent = `Estilo: ${data.estilo}`;
  document.getElementById('analisis-tags').innerHTML = (data.categoria || []).map((c, i) =>
    `<span class="tag ${i === 0 ? 'primary' : ''}">${c}</span>`).join('');
  document.getElementById('analisis-result').classList.add('visible');
}

let _lastResultados = [];

function renderResults({ resultados }) {
  clearResults();
  if (!resultados?.length) { showError('No se encontraron prendas.'); return; }
  _lastResultados = resultados;
  document.getElementById('results-header').classList.add('visible');
  document.getElementById('results-count').textContent = `${resultados.length} resultado${resultados.length !== 1 ? 's' : ''}`;
  renderFiltros(resultados);
  renderCards(resultados);
}

function renderCards(resultados) {
  const cards = document.getElementById('cards');
  cards.innerHTML = '';
  resultados.forEach((r, idx) => {
    const titulo = r.nombre && !r.nombre.includes('_') ? r.nombre : (r.descripcion || '').split(',')[0].trim();
    cards.appendChild(crearTarjeta(r, titulo, idx === 0, false));
  });
}

function renderFiltros(resultados) {
  const wrap = document.getElementById('filtros');
  const freq = {};
  resultados.forEach(r => (r.categoria || []).forEach(c => { freq[c] = (freq[c] || 0) + 1; }));
  const cats = Object.entries(freq).sort((a, b) => b[1] - a[1]).map(([c]) => c);
  wrap.innerHTML = '';
  if (!cats.length) return;
  const todos = document.createElement('button');
  todos.className = 'filtro-chip active';
  todos.textContent = 'Todos';
  todos.addEventListener('click', () => aplicarFiltro(null, wrap));
  wrap.appendChild(todos);
  cats.forEach(cat => {
    const chip = document.createElement('button');
    chip.className = 'filtro-chip';
    chip.textContent = cat;
    chip.addEventListener('click', () => aplicarFiltro(cat, wrap));
    wrap.appendChild(chip);
  });
}

function aplicarFiltro(cat, wrap) {
  wrap.querySelectorAll('.filtro-chip').forEach(c => c.classList.remove('active'));
  [...wrap.querySelectorAll('.filtro-chip')].find(c => cat ? c.textContent === cat : c.textContent === 'Todos')?.classList.add('active');
  renderCards(cat ? _lastResultados.filter(r => (r.categoria || []).includes(cat)) : _lastResultados);
}

function crearTarjeta(r, titulo, esMejor = false, esFavorito = false) {
  const imgHtml = r.imagen_url ? `<img src="${r.imagen_url}" alt="${titulo}" loading="lazy" onerror="this.style.display='none'" />` : '';
  const tags = (r.categoria || []).slice(0, 3).map((c,i) => `<span class="tag ${i===0?'primary':''}">${c}</span>`).join('');
  const saved = isInWishlist(r.id);
  const div = document.createElement('div');
  div.className = 'card';
  div.innerHTML = `
    <div class="card-img-wrap">
      ${imgHtml}
      <div class="card-img-placeholder" ${r.imagen_url ? 'style="display:none"':''}>
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>
      </div>
      ${esMejor ? '<div class="card-best-badge">Mejor resultado</div>' : ''}
      <button class="card-heart ${saved ? 'saved' : ''}" data-id="${r.id}" title="${saved ? 'Quitar de favoritos' : 'Guardar en favoritos'}">
        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="${saved ? '#ee0055' : 'none'}" stroke="${saved ? '#ee0055' : 'currentColor'}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5-4.5 2-1.5-1.5-2.74-2-4.5-2A5.5 5.5 0 0 0 2 8.5c0 2.29 1.51 4.04 3 5.5l7 7Z"/></svg>
      </button>
    </div>
    <div class="card-body">
      ${tags ? `<div class="card-tags">${tags}</div>` : ''}
      <div class="card-nombre">${titulo}</div>
      <div class="card-desc">${r.descripcion}</div>
    </div>`;
  const heartBtn = div.querySelector('.card-heart');
  heartBtn.addEventListener('click', e => { e.stopPropagation(); toggleWishlist(r, titulo, heartBtn); });
  div.addEventListener('click', () => openModal(r, titulo, esMejor));
  return div;
}

function setLoading(val) {
  document.getElementById('skeleton').classList.toggle('active', val);
  document.getElementById('cards').style.display = val ? 'none' : 'grid';
  document.getElementById('btn-texto').disabled = val;
  if (val) clearResults(false);
}

function clearResults(clearNotices_ = true) {
  _lastResultados = [];
  document.getElementById('cards').innerHTML = '';
  document.getElementById('filtros').innerHTML = '';
  document.getElementById('results-header').classList.remove('visible');
  if (clearNotices_) clearNotices();
}

function clearNotices() {
  document.getElementById('error-msg').classList.remove('active');
  document.getElementById('success-msg').classList.remove('active');
}

function showError(msg) {
  const el = document.getElementById('error-msg');
  el.textContent = msg;
  el.classList.add('active');
}

let _modalItem = null;

function openModal(r, titulo, esMejor = false) {
  _modalItem = { r, titulo };
  const wrap = document.getElementById('modal-img-wrap');
  const closeBtn = wrap.querySelector('.modal-close');
  wrap.innerHTML = r.imagen_url
    ? `<img class="modal-img" src="${r.imagen_url}" alt="${titulo}" />`
    : `<div class="modal-img-placeholder"><svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect width="18" height="18" x="3" y="3" rx="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg></div>`;
  wrap.appendChild(closeBtn);
  document.getElementById('modal-meta').innerHTML = esMejor ? '<span class="modal-best">Mejor resultado</span>' : '';
  document.getElementById('modal-titulo').textContent = titulo;
  const estiloEl = document.getElementById('modal-estilo');
  estiloEl.textContent = r.estilo || '';
  estiloEl.style.display = r.estilo ? '' : 'none';
  document.getElementById('modal-tags').innerHTML = (r.categoria || []).map((c, i) =>
    `<span class="tag ${i === 0 ? 'primary' : ''}">${c}</span>`).join('');
  document.getElementById('modal-desc').textContent = r.descripcion;
  _updateModalSaveBtn(r, titulo);
  document.getElementById('modal-overlay').classList.add('open');
  document.body.style.overflow = 'hidden';
  lucide.createIcons();
}

function _updateModalSaveBtn(r, titulo) {
  const saved = isInWishlist(r.id);
  const btn = document.getElementById('modal-save-btn');
  const lbl = document.getElementById('modal-save-label');
  btn.className = 'modal-save-btn' + (saved ? ' saved' : '');
  lbl.textContent = saved ? 'Guardado en favoritos' : 'Guardar en favoritos';
  const svg = btn.querySelector('svg');
  if (svg) { svg.setAttribute('fill', saved ? '#ee0055' : 'none'); svg.setAttribute('stroke', saved ? '#ee0055' : 'currentColor'); }
  btn.onclick = () => { toggleWishlist(r, titulo); _updateModalSaveBtn(r, titulo); };
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('open');
  document.body.style.overflow = '';
}

document.addEventListener('keydown', e => { if (e.key === 'Escape') closeModal(); });
document.getElementById('modal-overlay').addEventListener('click', function(e) {
  if (e.target === this) { this.classList.remove('open'); document.body.style.overflow = ''; }
});

lucide.createIcons();
