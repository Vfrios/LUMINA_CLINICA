// LÚMINA · Three.js: órbita livre + modo caminhada (WASD / setas / joysticks de toque) com colisão simples.
// Unidades: metros. Eixos: x=leste, y=cima, z=sul (fachada/entrada em z=20 m). Dados: ../data/*.json (export_web.py).
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const $ = (s) => document.querySelector(s);
const palco = $('#palco');

// ---------- renderer / cena
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
palco.prepend(renderer.domElement);
const scene = new THREE.Scene(); scene.background = new THREE.Color(0xE3D3B5);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;      // reflexos/iluminação neutra (≈ environment-image="neutral")
scene.add(new THREE.HemisphereLight(0xffffff, 0xd9c7a8, 0.45));
const camera = new THREE.PerspectiveCamera(60, 1, 0.05, 200);

function redimensionar() {
  const w = palco.clientWidth, h = palco.clientHeight; renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener('resize', redimensionar); redimensionar();

// ---------- dados
const [views, rooms, col] = await Promise.all(['views', 'rooms', 'collision'].map((n) => fetch(`../data/${n}.json`).then((r) => r.json())));

// ---------- modelo
let predio = null;
await new Promise((ok, falha) => new GLTFLoader().load('../modelos/predio_completo.glb',
  (g) => { predio = g.scene; scene.add(predio); ok(); },
  (e) => { if (e.total) $('#sobre-pct').textContent = Math.round((e.loaded / e.total) * 100) + '%'; },
  (e) => { $('#sobre').innerHTML = '<div>Falha ao abrir modelos/predio_completo.glb<br>Use um servidor local: npx serve dist/web</div>'; falha(e); }));
$('#sobre').classList.add('some');

// ---------- modos
const orbit = new OrbitControls(camera, renderer.domElement);
orbit.enableDamping = true; orbit.dampingFactor = 0.12; orbit.maxPolarAngle = Math.PI; orbit.minDistance = 0.5; orbit.maxDistance = 80;
let modo = 'orbita', anim = null, bloqueado = false;
const walk = { x: 0, z: 0, yaw: 0, pitch: 0 };
const eixo = { f: 0, l: 0, giroY: 0, giroX: 0 };
const teclas = new Set();
let colisao = true;
const controleSensibilidade = $('#sensibilidade');
const saidaSensibilidade = $('#sensibilidade-valor');
let sensibilidade = Number(controleSensibilidade.value);
orbit.rotateSpeed = sensibilidade;
controleSensibilidade.addEventListener('input', () => {
  sensibilidade = Number(controleSensibilidade.value);
  orbit.rotateSpeed = sensibilidade;
  saidaSensibilidade.value = `${sensibilidade.toFixed(2).replace('.', ',')}×`;
});

const ease = (t) => t * t * (3 - 2 * t);
function irPara(pos, alvo, fov, ms = 1000) {
  const p0 = camera.position.clone(), t0 = orbit.target.clone(), p1 = new THREE.Vector3(...pos), t1 = new THREE.Vector3(...alvo);
  const f0 = camera.fov, t_ini = performance.now();
  ms = Math.max(ms, Math.min(2400, Math.max(p0.distanceTo(p1), t0.distanceTo(t1)) * 80));
  anim = (agora) => {
    const k = ease(Math.min((agora - t_ini) / ms, 1));
    camera.position.lerpVectors(p0, p1, k); orbit.target.lerpVectors(t0, t1, k);
    camera.fov = f0 + (fov - f0) * k; camera.updateProjectionMatrix(); camera.lookAt(orbit.target);
    if (k >= 1) anim = null;
  };
}
function marcarModo() { $('#m-orbita').setAttribute('aria-pressed', modo === 'orbita'); $('#m-andar').setAttribute('aria-pressed', modo === 'andar'); }

function modoOrbita() {
  modo = 'orbita'; if (document.pointerLockElement) document.exitPointerLock();
  orbit.enabled = true; camera.fov = 45; camera.updateProjectionMatrix(); marcarModo();
  $('#hud-dica').textContent = 'Arraste para girar · roda do mouse/pinça = zoom · botão direito = mover';
}
function modoAndar(x = col.inicio.pos[0], z = col.inicio.pos[1], yaw = (col.inicio.yaw_graus * Math.PI) / 180) {
  modo = 'andar'; orbit.enabled = false; anim = null; marcarModo();
  walk.x = x; walk.z = z; walk.yaw = yaw; walk.pitch = 0; camera.fov = 70; camera.updateProjectionMatrix();
  $('#hud-dica').textContent = document.body.classList.contains('toque')
    ? 'Joystick esquerdo = andar · direito = olhar'
    : 'Clique na cena p/ capturar o mouse · WASD/setas = andar · Shift = correr · Esc = soltar · C = colisão · T = teto';
}
$('#m-orbita').onclick = () => { modoOrbita(); irParaVista(views.find((v) => v.id === 'aerea'), false); };
$('#m-andar').onclick = () => modoAndar();
$('#b-teto').onclick = (e) => { const t = predio.getObjectByName('teto'); t.visible = !t.visible; e.currentTarget.setAttribute('aria-pressed', t.visible); };
$('#b-colisao').onclick = (e) => { colisao = !colisao; e.currentTarget.setAttribute('aria-pressed', colisao); };

// ---------- vistas (mesmas câmeras dos renders 01..08)
function irParaVista(v, permitirAndar = true) {
  if (modo === 'andar' && v.interno && permitirAndar) {                        // teletransporta p/ o olho da vista, olhando o alvo
    const dx = v.target[0] - v.eye[0], dz = v.target[2] - v.eye[2];
    modoAndar(v.eye[0], v.eye[2], Math.atan2(-dx, -dz)); walk.pitch = Math.atan2(v.target[1] - v.eye[1], Math.hypot(dx, dz)); return;
  }
  if (modo === 'andar') modoOrbita();
  irPara(v.eye, v.target, v.fov);
}
views.forEach((v) => { const b = document.createElement('button'); b.type = 'button'; b.textContent = v.rotulo; b.onclick = () => irParaVista(v); $('#barra-vistas').appendChild(b); });
{ const v0 = views.find((v) => v.id === 'aerea'); camera.position.set(...v0.eye); orbit.target.set(...v0.target); camera.fov = v0.fov; camera.updateProjectionMatrix(); camera.lookAt(orbit.target); }

// ---------- colisão: círculo (aprox. quadrado) × AABBs de parede (sem vãos de porta) e móveis grandes
const caixas = () => (colisao ? col.paredes.concat(col.moveis) : []);
function bate(x, z) {
  const r = col.raio, [bx0, bz0, bx1, bz1] = col.limites;
  if (x < bx0 + r || x > bx1 - r || z < bz0 + r || z > bz1 - r) return true;      // não sai do prédio
  for (const [x0, z0, x1, z1] of caixas()) if (x > x0 - r && x < x1 + r && z > z0 - r && z < z1 + r) return true;
  return false;
}
function mover(dx, dz) {                                                       // desliza nas paredes (eixo a eixo)
  if (!bate(walk.x + dx, walk.z)) walk.x += dx;
  if (!bate(walk.x, walk.z + dz)) walk.z += dz;
}

// ---------- entrada: teclado, mouse (pointer lock), toque (2 joysticks)
addEventListener('keydown', (e) => {
  if (modo !== 'andar') return; const k = e.key.toLowerCase(); teclas.add(k);
  if (k === 'c') $('#b-colisao').click(); if (k === 't') $('#b-teto').click();
  if (['arrowup', 'arrowdown', 'arrowleft', 'arrowright', ' '].includes(k)) e.preventDefault();
});
addEventListener('keyup', (e) => teclas.delete(e.key.toLowerCase()));
renderer.domElement.addEventListener('click', () => { if (modo === 'andar' && !document.body.classList.contains('toque')) renderer.domElement.requestPointerLock?.(); });
document.addEventListener('pointerlockchange', () => { bloqueado = document.pointerLockElement === renderer.domElement; });
document.addEventListener('mousemove', (e) => {
  if (modo !== 'andar' || !bloqueado) return;
  walk.yaw -= e.movementX * 0.0022 * sensibilidade;
  walk.pitch = THREE.MathUtils.clamp(walk.pitch - e.movementY * 0.0022 * sensibilidade, -1.35, 1.35);
});
function joystick(el, cb) {
  const knob = el.querySelector('i'); let id = null, cx = 0, cy = 0;
  const set = (x, y) => { knob.style.transform = `translate(${x * 40}px,${y * 40}px)`; cb(x, y); };
  el.addEventListener('pointerdown', (e) => { id = e.pointerId; el.setPointerCapture(id); const r = el.getBoundingClientRect(); cx = r.left + r.width / 2; cy = r.top + r.height / 2; e.preventDefault(); });
  el.addEventListener('pointermove', (e) => { if (e.pointerId !== id) return; const x = THREE.MathUtils.clamp((e.clientX - cx) / 50, -1, 1), y = THREE.MathUtils.clamp((e.clientY - cy) / 50, -1, 1); set(x, y); });
  const fim = (e) => { if (e.pointerId === id) { id = null; set(0, 0); } };
  el.addEventListener('pointerup', fim); el.addEventListener('pointercancel', fim);
}
if (matchMedia('(pointer:coarse)').matches || 'ontouchstart' in window) document.body.classList.add('toque');
joystick($('#joy-mov'), (x, y) => { eixo.l = x; eixo.f = -y; });
joystick($('#joy-olhar'), (x, y) => { eixo.giroY = x; eixo.giroX = y; });

// ---------- laço principal
const rel = new THREE.Clock(); const ambiente = $('#hud-ambiente');
function ambienteEm(x, z) { return rooms.find((r) => x >= r.rect[0] && x <= r.rect[2] && z >= r.rect[1] && z <= r.rect[3]); }
renderer.setAnimationLoop((agora) => {
  const dt = Math.min(rel.getDelta(), 0.05);
  if (anim) anim(agora);
  if (modo === 'andar') {
    const f = (teclas.has('w') || teclas.has('arrowup') ? 1 : 0) - (teclas.has('s') || teclas.has('arrowdown') ? 1 : 0) + eixo.f;
    const l = (teclas.has('d') ? 1 : 0) - (teclas.has('a') ? 1 : 0) + eixo.l;
    // giro: seta esquerda => yaw aumenta (vira à esquerda); joystick à direita => yaw diminui
    walk.yaw += ((teclas.has('arrowleft') ? 1 : 0) - (teclas.has('arrowright') ? 1 : 0)) * 1.6 * dt * sensibilidade - eixo.giroY * 2.0 * dt * sensibilidade;
    walk.pitch = THREE.MathUtils.clamp(walk.pitch - eixo.giroX * 1.5 * dt * sensibilidade, -1.35, 1.35);
    const n = Math.hypot(f, l);
    if (n > 0) {
      const vel = (teclas.has('shift') ? 3.2 : 1.4) * dt * Math.min(1, n);      // m/s (correr = Shift)
      const fx = -Math.sin(walk.yaw), fz = -Math.cos(walk.yaw), rx = Math.cos(walk.yaw), rz = -Math.sin(walk.yaw);   // yaw 0 olha para -z
      const dx = ((fx * f + rx * l) / n) * vel, dz = ((fz * f + rz * l) / n) * vel;
      const passos = Math.max(1, Math.ceil(Math.hypot(dx, dz) / 0.08));          // passos curtos: não atravessa parede fina (10 cm)
      for (let i = 0; i < passos; i++) mover(dx / passos, dz / passos);
    }
    camera.position.set(walk.x, col.altura_olhos, walk.z); camera.rotation.set(walk.pitch, walk.yaw, 0, 'YXZ');
    const r = ambienteEm(walk.x, walk.z); ambiente.textContent = r ? r.nome : 'Circulação / vão';
  } else { orbit.update(); const r = ambienteEm(orbit.target.x, orbit.target.z); ambiente.textContent = r ? r.nome : 'Clínica LÚMINA'; }
  renderer.render(scene, camera);
});
window.__lumina = { camera, orbit, walk, bate, modoAndar, modoOrbita };         // depuração no console
