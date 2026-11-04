// LÚMINA · Three.js: órbita livre + modo caminhada (pointer lock próprio + WASD) com colisão simples.
// Unidades: metros. Eixos: x=leste, y=cima, z=sul (fachada/entrada em z=20 m). Dados: ../data/*.json (export_web.py).
//
// Parâmetros de URL (opcionais):
//   ?debug      → a cada 2 s no console: quadro médio/máx, custo de render, eventos de mouse/s, maior |dx| e maior giro por quadro
//   ?suav=35    → suavização do olhar (taxa 1/s; 0 = desliga; padrão 35 ≈ 30 ms). Maior = mais direto
//   ?dpr=1.5    → pixel ratio (padrão 1)
//   ?aa=0       → desliga antialias
//   ?nohud      → desliga toda escrita no HUD (teste A/B)
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const $ = (s) => document.querySelector(s);
const palco = $('#palco');

const params = new URLSearchParams(location.search);
const PIXEL_RATIO = Number(params.get('dpr')) || 1;
const ANTIALIAS = params.get('aa') !== '0';
const DEBUG = params.has('debug');
const SEM_HUD = params.has('nohud');
const SUAVIZACAO = params.has('suav') ? Math.max(0, Number(params.get('suav')) || 0) : 35;
// Só tela de toque PRIMÁRIA: 'ontouchstart' in window dá true em notebooks com touchscreen
const TOQUE = matchMedia('(pointer:coarse)').matches;
if (TOQUE) document.body.classList.add('toque');
console.info('[LÚMINA] walk.js build 2026-11-04-d (olhar próprio + unadjustedMovement + suavização + rastreio de entrada)');

// ---------- utilidades
const wrapPi = (a) => { a = (a + Math.PI) % (Math.PI * 2); if (a < 0) a += Math.PI * 2; return a - Math.PI; };
const fmtSens = (v) => `${v.toFixed(2).replace('.', ',')}×`;

// ---------- diagnóstico (?debug): contadores só em memória, saída só no console
const dbg = { n: 0, soma: 0, max: 0, render: 0, ultimo: performance.now(), tAnt: 0, prog: null, mm: 0, maxDx: 0, maxDyaw: 0 };

// ---------- DOM cacheado: nós de texto atualizados via .data (só quando o valor muda)
function noTexto(el) { if (!el.firstChild) el.textContent = ' '; return el.firstChild; }
const hudAmbiente = noTexto($('#hud-ambiente'));
const hudDica = noTexto($('#hud-dica'));
const sobrePct = noTexto($('#sobre-pct'));
const sobre = $('#sobre');
let hudNomeAtual = '', hudDicaAtual = '', pctAtual = -1;
function setHudNome(t) { if (SEM_HUD) return; if (t !== hudNomeAtual) { hudNomeAtual = t; hudAmbiente.data = t; } }
function setHudDica(t) { if (SEM_HUD) return; if (t !== hudDicaAtual) { hudDicaAtual = t; hudDica.data = t; } }

// ---------- renderer / cena
const renderer = new THREE.WebGLRenderer({ antialias: ANTIALIAS, powerPreference: 'high-performance' });
renderer.setPixelRatio(PIXEL_RATIO);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 0.9;
palco.prepend(renderer.domElement);
const canvasEl = renderer.domElement;
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xE3D3B5);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
pmrem.dispose();
scene.add(new THREE.HemisphereLight(0xffffff, 0xb8b8b8, 0.55));
const camera = new THREE.PerspectiveCamera(60, 1, 0.05, 200);

// GPU em uso: se aparecer SwiftShader/llvmpipe/Software, o WebGL está rodando na CPU
{
  const gl = renderer.getContext();
  const ext = gl.getExtension('WEBGL_debug_renderer_info');
  const gpu = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'desconhecida';
  console.info('[LÚMINA] GPU:', gpu, '| pixelRatio:', PIXEL_RATIO, '| antialias:', ANTIALIAS);
  if (/swiftshader|llvmpipe|software|basic render/i.test(gpu)) {
    console.warn('[LÚMINA] WebGL em SOFTWARE. Ative a aceleração por hardware do navegador (chrome://gpu).');
  }
}

// Redimensionamento: ResizeObserver entrega o tamanho sem forçar layout; aplicado dentro do loop
let tamW = Math.max(1, palco.clientWidth), tamH = Math.max(1, palco.clientHeight), redim = true;
new ResizeObserver(([e]) => {
  tamW = Math.max(1, Math.round(e.contentRect.width));
  tamH = Math.max(1, Math.round(e.contentRect.height));
  redim = true;
}).observe(palco);

// ---------- dados
const [views, rooms, col] = await Promise.all(
  ['views', 'rooms', 'collision'].map((n) => fetch(`../data/${n}.json`).then((r) => r.json()))
);

// ---------- modelo
let predio = null, teto = null;
await new Promise((ok, falha) => new GLTFLoader().load('../modelos/predio_completo.glb',
  (g) => {
    predio = g.scene;
    teto = predio.getObjectByName('teto');
    scene.add(predio);
    ok();
  },
  (e) => {
    if (!e.total) return;
    const p = Math.round((e.loaded / e.total) * 100);
    if (p !== pctAtual) { pctAtual = p; sobrePct.data = p + '%'; }   // só escreve quando o inteiro muda
  },
  (e) => { sobre.innerHTML = '<div>Falha ao abrir modelos/predio_completo.glb<br>Use um servidor local: npx serve dist/web</div>'; falha(e); }));

// O three só compila o shader de um material quando ele entra no frustum pela 1ª vez.
// compileAsync percorre a cena inteira (sem frustum culling), ainda atrás da tela de carregamento.
sobrePct.data = 'Preparando shaders…';
try { await renderer.compileAsync(scene, camera); } catch (e) { renderer.compile(scene, camera); }

// ---------- controles
// Órbita
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true; orbit.dampingFactor = 0.18;
orbit.maxPolarAngle = Math.PI; orbit.minDistance = 0.5; orbit.maxDistance = 80;

// ---------- estado
let modo = 'orbita', anim = null;
let sensibilidade = 0.45;
const teclas = new Set();
let colisao = true;
const eixo = { f: 0, l: 0, giroY: 0, giroX: 0 };
const walk = { x: 0, z: 0 };

const DICA_ORBITA = 'Arraste para girar · roda do mouse/pinça = zoom · botão direito = mover';
const DICA_ANDAR_MOUSE = 'Clique na cena p/ capturar o mouse · WASD = andar · Shift = correr · Esc = soltar · C = colisão · T = teto';
const DICA_ANDAR_TOQUE = 'Joystick esquerdo = andar · direito = olhar';
const DICA_ANDAR_LIVRE = 'Mouse capturado · WASD = andar · Shift = correr · Esc = soltar';

// ---------- olhar (mouse com pointer lock). Substitui o PointerLockControls:
//   · movimento BRUTO (unadjustedMovement) → sem aceleração do ponteiro do Windows
//   · descarta os 2 primeiros eventos após capturar e saltos absurdos (>300 px num evento)
//   · alvo (yawAlvo/pitchAlvo) recebe a entrada; a câmera segue o alvo com suavização exponencial por quadro
const PITCH_MAX = 1.35;
const mira = { yaw: 0, pitch: 0, yawAlvo: 0, pitchAlvo: 0, travado: false, ignorar: 0 };

function travarMouse() {
  try {
    const p = canvasEl.requestPointerLock({ unadjustedMovement: true });
    if (p && typeof p.catch === 'function') p.catch(() => { try { canvasEl.requestPointerLock(); } catch (e) { /* clique no canvas */ } });
  } catch (e) {
    try { canvasEl.requestPointerLock(); } catch (e2) { /* clique no canvas */ }
  }
}
function soltarMouse() { if (document.pointerLockElement === canvasEl) document.exitPointerLock(); }

document.addEventListener('pointerlockchange', () => {
  mira.travado = document.pointerLockElement === canvasEl;
  mira.ignorar = 2;
  if (modo === 'andar') setHudDica(mira.travado ? DICA_ANDAR_LIVRE : DICA_ANDAR_MOUSE);
});
document.addEventListener('mousemove', (e) => {
  if (!mira.travado) return;
  if (mira.ignorar > 0) { mira.ignorar--; return; }
  const dx = e.movementX, dy = e.movementY;
  if (Math.abs(dx) > 300 || Math.abs(dy) > 300) { if (DEBUG) console.warn(`[LÚMINA] evento de mouse descartado: dx=${dx} dy=${dy}`); return; }
  const k = 0.0022 * sensibilidade;                    // rad por pixel (0,45× ≈ 0,001, igual ao ajuste anterior)
  mira.yawAlvo -= dx * k;
  mira.pitchAlvo = THREE.MathUtils.clamp(mira.pitchAlvo - dy * k, -PITCH_MAX, PITCH_MAX);
  if (DEBUG) { dbg.mm++; const a = Math.abs(dx); if (a > dbg.maxDx) dbg.maxDx = a; }
}, { passive: true });

// ---------- sensibilidade
const controleSensibilidade = $('#sensibilidade');
const saidaSensibilidade = $('#sensibilidade-valor');
function aplicarSensibilidade() {
  sensibilidade = Number(controleSensibilidade.value) || 0.45;
  orbit.rotateSpeed = sensibilidade;
  saidaSensibilidade.value = fmtSens(sensibilidade);
}
controleSensibilidade.addEventListener('input', aplicarSensibilidade);
aplicarSensibilidade();

// ---------- transições de câmera (órbita)
const ease = (t) => t * t * (3 - 2 * t);
function irPara(pos, alvo, fov, ms = 1000) {
  const p0 = camera.position.clone(), t0 = orbit.target.clone();
  const p1 = new THREE.Vector3(...pos), t1 = new THREE.Vector3(...alvo);
  const f0 = camera.fov, t_ini = performance.now();
  ms = Math.max(ms, Math.min(2400, Math.max(p0.distanceTo(p1), t0.distanceTo(t1)) * 80));
  anim = (agora) => {
    const k = ease(Math.min((agora - t_ini) / ms, 1));
    camera.position.lerpVectors(p0, p1, k);
    orbit.target.lerpVectors(t0, t1, k);
    camera.fov = f0 + (fov - f0) * k;
    camera.updateProjectionMatrix();
    camera.lookAt(orbit.target);
    if (k >= 1) anim = null;
  };
}

function marcarModo() {
  $('#m-orbita').setAttribute('aria-pressed', modo === 'orbita');
  $('#m-andar').setAttribute('aria-pressed', modo === 'andar');
}

// ---------- modos
function modoOrbita() {
  modo = 'orbita'; anim = null;
  soltarMouse();
  orbit.enabled = true;
  camera.fov = 45; camera.updateProjectionMatrix();
  marcarModo();
  setHudDica(DICA_ORBITA);
}

function modoAndar(x = col.inicio.pos[0], z = col.inicio.pos[1], yaw = (col.inicio.yaw_graus * Math.PI) / 180, pitch = 0) {
  modo = 'andar'; orbit.enabled = false; anim = null; marcarModo();
  walk.x = x; walk.z = z;
  mira.yaw = mira.yawAlvo = wrapPi(yaw);
  mira.pitch = mira.pitchAlvo = THREE.MathUtils.clamp(pitch, -PITCH_MAX, PITCH_MAX);
  camera.fov = 70; camera.updateProjectionMatrix();
  camera.position.set(x, col.altura_olhos, z);
  camera.rotation.set(mira.pitch, mira.yaw, 0, 'YXZ');
  setHudDica(TOQUE ? DICA_ANDAR_TOQUE : (mira.travado ? DICA_ANDAR_LIVRE : DICA_ANDAR_MOUSE));
  // pointer lock precisa de gesto do usuário; se falhar, o clique no canvas captura
  if (!TOQUE && !mira.travado) setTimeout(travarMouse, 50);
}

$('#m-orbita').onclick = () => { modoOrbita(); irParaVista(views.find((v) => v.id === 'aerea'), false); };
$('#m-andar').onclick = () => modoAndar();
$('#b-teto').onclick = (e) => {
  if (!teto) return;
  teto.visible = !teto.visible;
  e.currentTarget.setAttribute('aria-pressed', teto.visible);
};
$('#b-colisao').onclick = (e) => { colisao = !colisao; e.currentTarget.setAttribute('aria-pressed', colisao); };

// ---------- vistas
function irParaVista(v, permitirAndar = true) {
  if (modo === 'andar' && v.interno && permitirAndar) {
    const dx = v.target[0] - v.eye[0], dz = v.target[2] - v.eye[2];
    const pitch = Math.atan2(v.target[1] - v.eye[1], Math.hypot(dx, dz));
    modoAndar(v.eye[0], v.eye[2], Math.atan2(-dx, -dz), pitch);
    return;
  }
  if (modo === 'andar') modoOrbita();
  irPara(v.eye, v.target, v.fov);
}

const vistasDaBarra = ['recepcao', 'espera', 'tecnica', 'botox', 'drenagem', 'peeling', 'banheiro', 'tecnologia'];
{
  const frag = document.createDocumentFragment();
  vistasDaBarra.forEach((id) => {
    const v = views.find((item) => item.id === id);
    if (!v) throw new Error(`Vista não encontrada: ${id}`);
    const b = document.createElement('button');
    b.type = 'button'; b.textContent = v.rotulo;
    b.onclick = () => irParaVista(v);
    frag.appendChild(b);
  });
  $('#barra-vistas').appendChild(frag);   // 1 inserção só
}
{
  const v0 = views.find((v) => v.id === 'aerea');
  camera.position.set(...v0.eye);
  orbit.target.set(...v0.target);
  camera.fov = v0.fov; camera.updateProjectionMatrix();
  camera.lookAt(orbit.target);
}

// ---------- colisão
const SEM_CAIXAS = [];
const caixasAtivas = col.paredes.concat(col.moveis);   // concat feito uma vez, não a cada teste
function bate(x, z) {
  const r = col.raio, [bx0, bz0, bx1, bz1] = col.limites;
  if (x < bx0 + r || x > bx1 - r || z < bz0 + r || z > bz1 - r) return true;
  const caixas = colisao ? caixasAtivas : SEM_CAIXAS;
  for (let i = 0; i < caixas.length; i++) {
    const c = caixas[i];
    const px = Math.min(Math.max(x, c[0]), c[2]), pz = Math.min(Math.max(z, c[1]), c[3]);
    if ((x - px) ** 2 + (z - pz) ** 2 < r * r) return true;
  }
  return false;
}
function mover(dx, dz) {
  if (!bate(walk.x + dx, walk.z + dz)) { walk.x += dx; walk.z += dz; return; }
  if (!bate(walk.x + dx, walk.z)) walk.x += dx;
  if (!bate(walk.x, walk.z + dz)) walk.z += dz;
}

// ---------- teclado
addEventListener('keydown', (e) => {
  if (modo !== 'andar') return;
  const k = e.key.toLowerCase();
  teclas.add(k);
  if (!e.repeat) {
    if (k === 'c') $('#b-colisao').click();
    if (k === 't') $('#b-teto').click();
  }
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(k)) e.preventDefault();
});
addEventListener('keyup', (e) => teclas.delete(e.key.toLowerCase()));
addEventListener('blur', () => teclas.clear());                       // evita tecla "presa" ao trocar de janela
document.addEventListener('visibilitychange', () => { if (document.hidden) teclas.clear(); });

// Clique no canvas recaptura o mouse (se o Esc soltou)
canvasEl.addEventListener('click', () => {
  if (modo === 'andar' && !TOQUE && !mira.travado) travarMouse();
});

// ---------- joysticks (toque). Só escrevem style.transform (compositor) e valores numéricos.
function joystick(el, cb) {
  const knob = el.querySelector('i');
  let id = null, cx = 0, cy = 0;
  const set = (x, y) => { knob.style.transform = `translate(${x * 40}px,${y * 40}px)`; cb(x, y); };
  el.addEventListener('pointerdown', (e) => {
    id = e.pointerId; el.setPointerCapture(id);
    const r = el.getBoundingClientRect(); cx = r.left + r.width / 2; cy = r.top + r.height / 2;
    e.preventDefault();
  });
  el.addEventListener('pointermove', (e) => {
    if (e.pointerId !== id) return;
    set(THREE.MathUtils.clamp((e.clientX - cx) / 50, -1, 1), THREE.MathUtils.clamp((e.clientY - cy) / 50, -1, 1));
  });
  const fim = (e) => { if (e.pointerId === id) { id = null; set(0, 0); } };
  el.addEventListener('pointerup', fim);
  el.addEventListener('pointercancel', fim);
}
if (TOQUE) {
  joystick($('#joy-mov'), (x, y) => { eixo.l = x; eixo.f = -y; });
  joystick($('#joy-olhar'), (x, y) => { eixo.giroY = x; eixo.giroX = y; });
}

// ---------- diagnóstico (?debug)
function amostra(agora, msRender, dyawGraus) {
  if (dyawGraus > dbg.maxDyaw) dbg.maxDyaw = dyawGraus;
  if (dbg.tAnt) {
    const f = agora - dbg.tAnt; dbg.soma += f; if (f > dbg.max) dbg.max = f; dbg.n++;
    const np = renderer.info.programs ? renderer.info.programs.length : 0;
    // Se "shaders" mudar (ex.: 12→13) o pico foi compilação de shader; se "render" for baixo e o quadro alto, o gargalo está fora do three
    if (f > 50) console.warn(`[LÚMINA] quadro lento: ${f.toFixed(0)} ms · renderer.render ${msRender.toFixed(0)} ms · modo=${modo} · mouse capturado=${mira.travado} · shaders ${dbg.prog ?? '?'}→${np} · texturas ${renderer.info.memory.textures}`);
    dbg.prog = np;
  }
  dbg.tAnt = agora; dbg.render += msRender;
  const dtJanela = agora - dbg.ultimo;
  if (dtJanela >= 2000 && dbg.n) {
    const i = renderer.info.render, med = dbg.soma / dbg.n;
    console.log(`[LÚMINA] quadro médio ${med.toFixed(1)} ms (${(1000 / med).toFixed(0)} fps) · máx ${dbg.max.toFixed(1)} ms · render CPU ${(dbg.render / dbg.n).toFixed(2)} ms · ` +
      `chamadas ${i.calls} · tri ${i.triangles} | ENTRADA: mousemove ${(dbg.mm / (dtJanela / 1000)).toFixed(0)}/s · |dx| máx ${dbg.maxDx}px · giro máx/quadro ${dbg.maxDyaw.toFixed(2)}°`);
    dbg.n = 0; dbg.soma = 0; dbg.max = 0; dbg.render = 0; dbg.mm = 0; dbg.maxDx = 0; dbg.maxDyaw = 0; dbg.ultimo = agora;
  }
}

// Render de aquecimento: sobe texturas e geometrias para a GPU enquanto a tela de carregamento ainda cobre a cena
renderer.setSize(tamW, tamH, false);
camera.aspect = tamW / tamH; camera.updateProjectionMatrix(); redim = false;
renderer.render(scene, camera);
sobre.classList.add('some');
setTimeout(() => { sobre.hidden = true; }, 500);   // depois do fade, sai do hit-testing e da pintura

// ---------- laço principal (sem alocações, sem leitura de layout)
const relogio = new THREE.Clock();
const UP = new THREE.Vector3(0, 1, 0);
const fwd = new THREE.Vector3(), right = new THREE.Vector3();

function ambienteEm(x, z) {
  for (let i = 0; i < rooms.length; i++) {
    const r = rooms[i].rect;
    if (x >= r[0] && x <= r[2] && z >= r[1] && z <= r[3]) return rooms[i];
  }
  return null;
}

renderer.setAnimationLoop(() => {
  const agora = performance.now();
  const dt = Math.min(relogio.getDelta(), 0.05);
  let dyaw = 0;

  if (redim) {
    renderer.setSize(tamW, tamH, false);
    camera.aspect = tamW / tamH; camera.updateProjectionMatrix();
    redim = false;
  }
  if (anim) anim(agora);

  if (modo === 'andar') {
    // --- olhar: joystick (toque) alimenta o alvo; a câmera segue o alvo com suavização independente do fps
    if (eixo.giroY !== 0 || eixo.giroX !== 0) {
      mira.yawAlvo -= eixo.giroY * 2.0 * dt * sensibilidade;
      mira.pitchAlvo = THREE.MathUtils.clamp(mira.pitchAlvo - eixo.giroX * 1.5 * dt * sensibilidade, -PITCH_MAX, PITCH_MAX);
    }
    const a = SUAVIZACAO > 0 ? 1 - Math.exp(-dt * SUAVIZACAO) : 1;
    const yawAntes = mira.yaw;
    mira.yaw += (mira.yawAlvo - mira.yaw) * a;
    mira.pitch += (mira.pitchAlvo - mira.pitch) * a;
    camera.rotation.set(mira.pitch, mira.yaw, 0, 'YXZ');
    if (DEBUG) dyaw = Math.abs(mira.yaw - yawAntes) * 57.29578;

    // --- movimento relativo à direção do olhar
    const f = (teclas.has('w') || teclas.has('arrowup') ? 1 : 0) - (teclas.has('s') || teclas.has('arrowdown') ? 1 : 0) + eixo.f;
    const l = (teclas.has('d') ? 1 : 0) - (teclas.has('a') ? 1 : 0) + eixo.l;
    const n = Math.hypot(f, l);
    if (n > 0) {
      const vel = (teclas.has('shift') ? 3.2 : 1.4) * dt * Math.min(1, n);
      camera.getWorldDirection(fwd); fwd.y = 0; fwd.normalize();
      right.crossVectors(fwd, UP).normalize();
      const dx = (fwd.x * f + right.x * l) / n * vel;
      const dz = (fwd.z * f + right.z * l) / n * vel;
      const passos = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.02));
      for (let i = 0; i < passos; i++) mover(dx / passos, dz / passos);
    }

    camera.position.set(walk.x, col.altura_olhos, walk.z);
    const r = ambienteEm(walk.x, walk.z);
    setHudNome(r ? r.nome : 'Circulação / vão');
  } else {
    orbit.update();
    const r = ambienteEm(orbit.target.x, orbit.target.z);
    setHudNome(r ? r.nome : 'Clínica LÚMINA');
  }

  if (DEBUG) {
    const t0 = performance.now();
    renderer.render(scene, camera);
    amostra(agora, performance.now() - t0, dyaw);
  } else {
    renderer.render(scene, camera);
  }
});

window.__lumina = { camera, orbit, mira, walk, renderer, bate, modoAndar, modoOrbita };
