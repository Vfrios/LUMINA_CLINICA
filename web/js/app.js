// LÚMINA · web app (model-viewer). Dados vêm de data/*.json gerados por export_web.py.
import { carregarModelViewer } from './mv-loader.js';

const $ = (s) => document.querySelector(s);
const mv = $('#mv'), elVistas = $('#vistas'), selAmb = $('#sel-ambiente'), info = $('#info-ambiente'), rotulo = $('#rotulo-vista');
let views = [], rooms = [], corTeto = null, ambAtual = null;

function mostrarErro(html) { const e = $('#erro'); e.innerHTML = html; e.hidden = false; $('#carregando').classList.add('some'); }

// ---------- câmera: transição suave entre posições
function irPara(c) {
  let theta = c.theta;
  try { const atual = (mv.getCameraOrbit().theta * 180) / Math.PI; theta += 360 * Math.round((atual - c.theta) / 360); } catch (e) { /* ainda sem modelo */ }
  mv.cameraOrbit = `${theta}deg ${c.phi}deg ${c.r}m`;
  mv.cameraTarget = `${c.target[0]}m ${c.target[1]}m ${c.target[2]}m`;
  mv.fieldOfView = `${c.fov}deg`;
}

function marcarVista(id) {
  elVistas.querySelectorAll('button').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.id === id)));
}

// ---------- materiais (model-viewer scene-graph): teto e realce de piso por ambiente
const mats = (n) => (mv.model?.materials || []).find((m) => m.name === n);
function setTeto(visivel) {
  const m = mats('teto'); if (!m) return;
  if (!corTeto) corTeto = [...m.pbrMetallicRoughness.baseColorFactor];
  m.setAlphaMode(visivel ? 'OPAQUE' : 'BLEND');
  m.pbrMetallicRoughness.setBaseColorFactor([corTeto[0], corTeto[1], corTeto[2], visivel ? 1 : 0]);
}
function realcar(id) {
  if (ambAtual) { mats('piso_' + ambAtual)?.setEmissiveFactor([0, 0, 0]); ambAtual = null; }
  if (id) { const m = mats('piso_' + id); if (m) { m.setEmissiveFactor([0.62, 0.17, 0.26]); ambAtual = id; } }
}

function escolherAmbiente(id) {
  realcar(id);
  if (!id) { info.hidden = true; return; }
  const r = rooms.find((x) => x.id === id);
  info.hidden = false;
  info.innerHTML = `<b>${r.nome}</b><br>${r.largura.toFixed(2).replace('.', ',')} × ${r.profundidade.toFixed(2).replace('.', ',')} m · ${r.area.toFixed(1).replace('.', ',')} m²`;
  marcarVista(null); rotulo.textContent = r.nome;
  irPara({ ...r.camera });
}

function visaoGeral() {
  const v = views.find((x) => x.id === 'aerea'); escolherAmbiente(''); selAmb.value = '';
  if (v) { marcarVista(v.id); rotulo.textContent = v.rotulo; irPara(v); }
}

function montarUI() {
  const vistasDoModelViewer = new Set(['recepcao', 'espera', 'botox', 'peeling', 'corredor', 'wc_acessivel', 'aerea', 'superior']);
  views.filter((v) => vistasDoModelViewer.has(v.id)).forEach((v) => {
    const b = document.createElement('button');
    b.type = 'button'; b.dataset.id = v.id; b.setAttribute('aria-pressed', 'false');
    b.innerHTML = `${v.rotulo}<small>${v.descricao}</small>`;
    b.addEventListener('click', () => { escolherAmbiente(''); selAmb.value = ''; marcarVista(v.id); rotulo.textContent = v.rotulo; irPara(v); });
    elVistas.appendChild(b);
  });
  rooms.forEach((r) => { const o = document.createElement('option'); o.value = r.id; o.textContent = r.nome; selAmb.appendChild(o); });
  selAmb.addEventListener('change', () => escolherAmbiente(selAmb.value));
  $('#opt-teto').addEventListener('change', (e) => setTeto(e.target.checked));
  $('#opt-sombra').addEventListener('change', (e) => { mv.shadowIntensity = e.target.checked ? 0.7 : 0; });
  $('#btn-reset').addEventListener('click', visaoGeral);
}

// ---------- PWA: instalar + service worker
let pedidoInstalar = null;
window.addEventListener('beforeinstallprompt', (e) => { e.preventDefault(); pedidoInstalar = e; $('#btn-instalar').hidden = false; });
$('#btn-instalar').addEventListener('click', async () => { if (!pedidoInstalar) return; pedidoInstalar.prompt(); await pedidoInstalar.userChoice; pedidoInstalar = null; $('#btn-instalar').hidden = true; });
if ('serviceWorker' in navigator && location.protocol.startsWith('http')) navigator.serviceWorker.register('sw.js').catch(() => {});

// ---------- inicialização
(async function iniciar() {
  if (location.protocol === 'file:') {
    return mostrarErro('<h2>Abra por um servidor local</h2><p>Navegadores bloqueiam o carregamento de .glb/.json via <code>file://</code>.<br>Rode: <code>npx serve dist/web</code> e abra o endereço indicado.</p>');
  }
  try {
    [views, rooms] = await Promise.all([fetch('data/views.json').then((r) => r.json()), fetch('data/rooms.json').then((r) => r.json())]);
    montarUI();
  } catch (e) { return mostrarErro('<h2>Dados não encontrados</h2><p>Faltam <code>data/views.json</code> e <code>data/rooms.json</code>. Rode <code>python3 export_web.py</code>.</p>'); }

  mv.addEventListener('progress', (e) => { const p = e.detail.totalProgress; $('#barra-i').style.width = `${Math.round(p * 100)}%`; });
  mv.addEventListener('error', () => mostrarErro('<h2>Falha ao abrir o modelo</h2><p>Não foi possível ler <code>modelos/predio_completo.glb</code>.</p>'));
  mv.addEventListener('load', () => {
    $('#carregando').classList.add('some');
    const v = views.find((x) => x.id === 'aerea'); if (v) { marcarVista(v.id); rotulo.textContent = v.rotulo; }
    setTeto($('#opt-teto').checked);
  });
  try { await carregarModelViewer(); }
  catch (e) { mostrarErro(`<h2>Biblioteca 3D indisponível</h2><p>${e.message}<br>Conecte-se à internet uma vez, ou gere <code>dist/web/vendor/</code> com <code>python3 export_web.py --vendor</code>.</p>`); }
})();
