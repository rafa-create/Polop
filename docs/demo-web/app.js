import * as THREE from "three";
// Optional GLB/GLTF replacements; no network request for absent model files.
// Example: Thomas: { url: "./assets/thomas.glb", scale: 1 }
const CHARACTER_ASSETS = Object.freeze({ Thomas: null, "Éva": null, "Léa": null });

const sceneHost = document.getElementById("scene");
const loading = document.getElementById("loading");
const sceneError = document.getElementById("scene-error");
const caption = document.getElementById("scene-caption");
const timeline = document.getElementById("timeline");
const timecode = document.getElementById("timecode");
const playPause = document.getElementById("play-pause");
const replay = document.getElementById("replay");
const cameraMode = document.getElementById("camera-mode");
const speedControl = document.getElementById("speed");
const DURATION = 15;
const fullscreenButton = document.getElementById("fullscreen");
const appRoot = document.getElementById("app");
const TAU = Math.PI * 2;
const clamp = THREE.MathUtils.clamp;
const mix = THREE.MathUtils.lerp;
let renderer, scene, camera, people = [], riverRing;
let elapsed = 0, lastFrame = 0, playing = true, freeView = false;
let orbitYaw = -0.65, orbitPitch = 0.33, orbitDistance = 13;
let dragStart = null, lastPinchDistance = 0;
const pointers = new Map();
const reducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? false;
let seed = 5318;
const random = () => ((seed = (seed * 1664525 + 1013904223) >>> 0) / 4294967296);
const v = (x, y, z) => new THREE.Vector3(x, y, z);
const trailX = z => 8.7 + Math.sin(z * .115) * 2.0;

function baseHeight(x, z) {
  const peak = 19 * Math.exp(-((x - 18) ** 2 / 550 + (z + 24) ** 2 / 850));
  const shoulder = 10 * Math.exp(-((x - 32) ** 2 / 950 + (z - 5) ** 2 / 1600));
  const far = 4 * Math.exp(-((x + 27) ** 2 / 950 + (z + 37) ** 2 / 900));
  const relief = .45 * Math.sin(x * .23) * Math.cos(z * .18);
  return -1.65 + peak + shoulder + far + relief
    - 4.2 * Math.exp(-((x + 15) ** 2 / 35));
}
function heightAt(x, z) {
  const gorge = (x > 2 && x < 18) ? 5.5 * Math.exp(-((z + 12.5) ** 2 / 2.4)) : 0;
  return baseHeight(x, z) - gorge;
}
function material(color, roughness = 1, extras = {}) {
  return new THREE.MeshStandardMaterial({ color, roughness, ...extras });
}
function mesh(geometry, mat, parent = scene) {
  const object = new THREE.Mesh(geometry, mat);
  object.castShadow = true;
  object.receiveShadow = true;
  parent.add(object);
  return object;
}
function cylinderBetween(a, b, radius, mat, parent = scene) {
  const delta = b.clone().sub(a);
  const item = mesh(new THREE.CylinderGeometry(radius, radius, delta.length(), 7), mat, parent);
  item.position.copy(a).add(b).multiplyScalar(.5);
  item.quaternion.setFromUnitVectors(v(0, 1, 0), delta.normalize());
  return item;
}
function tube(points, radius, mat, parent = scene) {
  return mesh(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(points), 40, radius, 5, false), mat, parent);
}
function drawGround() {
  const geometry = new THREE.PlaneGeometry(112, 124, 108, 112);
  geometry.rotateX(-Math.PI / 2);
  const p = geometry.attributes.position;
  const shades = [], color = new THREE.Color();
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), y = heightAt(x, z);
    p.setY(i, y);
    const light = clamp(.64 + y * .012 + .055 * Math.sin(x * .8 + z * .5), .45, .94);
    color.set(y > 14 ? 0x8b8b80 : y > 8 ? 0x7f8874 : 0x5b8069);
    if (Math.abs(x + 15) < 6 && y < -1) color.set(0x5b6c5c);
    color.multiplyScalar(light);
    shades.push(color.r, color.g, color.b);
  }
  p.needsUpdate = true;
  geometry.setAttribute("color", new THREE.Float32BufferAttribute(shades, 3));
  geometry.computeVertexNormals();
  const ground = mesh(geometry, material(0xffffff, 1, { vertexColors: true, side: THREE.DoubleSide }));
  ground.castShadow = false;
  const water = mesh(new THREE.PlaneGeometry(8.4, 124), material(0x4f9b9f, .23, {
    transparent: true, opacity: .72, depthWrite: false, side: THREE.DoubleSide, metalness: .06
  }));
  water.rotation.x = -Math.PI / 2;
  water.position.set(-15, -1.05, 0);
  water.castShadow = false;
}
function drawTrailAndBridge() {
  const path = [], color = material(0xb7ad88);
  for (let z = 25; z >= -33; z -= .65) {
    if (z < -10.3 && z > -14.7) continue;
    const x = trailX(z), y = heightAt(x, z) + .09;
    path.push(v(x, y, z));
    const slab = mesh(new THREE.BoxGeometry(1.42, .075, .76), color);
    slab.position.set(x, y, z);
    slab.rotation.y = -.08 * Math.cos(z * .115);
    slab.castShadow = false;
  }
  const startZ = -10.3, endZ = -14.7;
  const start = v(trailX(startZ), baseHeight(trailX(startZ), startZ) + .22, startZ);
  const end = v(trailX(endZ), baseHeight(trailX(endZ), endZ) + .22, endZ);
  const plank = material(0x745642), rope = material(0xb9a78c), post = material(0x645040);
  for (let i = 0; i <= 20; i++) {
    const t = i / 20, point = start.clone().lerp(end, t);
    point.y -= .35 * Math.sin(Math.PI * t);
    const board = mesh(new THREE.BoxGeometry(1.85, .13, .21), plank);
    board.position.copy(point);
    board.rotation.y = -.04;
  }
  for (const side of [-1, 1]) {
    const rail = [];
    for (let i = 0; i <= 12; i++) {
      const t = i / 12, point = start.clone().lerp(end, t);
      point.x += side * .96;
      point.y += 1.13 - .33 * Math.sin(Math.PI * t);
      rail.push(point);
      if (i % 3 === 0) cylinderBetween(point.clone().add(v(0, -.98, 0)), point, .055, post);
    }
    tube(rail, .026, rope);
  }
}
function drawNature() {
  const bark = material(0x4a4335), needles = material(0x2d594c), rock = material(0x727c73);
  for (let i = 0; i < 125; i++) {
    const x = random() * 105 - 51, z = random() * 116 - 58;
    if (Math.abs(x + 15) < 6 || (Math.abs(x - trailX(z)) < 2.6 && z > -32)) continue;
    const y = heightAt(x, z);
    if (y < -1 || y > 13) continue;
    const scale = .7 + random() * 1.7;
    const tree = new THREE.Group();
    tree.position.set(x, y, z);
    const trunk = mesh(new THREE.CylinderGeometry(.08, .12, 1.25 * scale, 5), bark, tree);
    trunk.position.y = .61 * scale;
    for (let tier = 0; tier < 3; tier++) {
      const foliage = mesh(new THREE.ConeGeometry((.72 - tier * .14) * scale, 1.4 * scale, 6), needles, tree);
      foliage.position.y = (1.12 + tier * .43) * scale;
    }
    scene.add(tree);
  }
  for (let i = 0; i < 90; i++) {
    const x = random() * 105 - 51, z = random() * 116 - 58;
    if (Math.abs(x - trailX(z)) < 1.35) continue;
    const stone = mesh(new THREE.DodecahedronGeometry(.22 + random() * .56, 0), rock);
    stone.position.set(x, heightAt(x, z) + .13, z);
    stone.scale.set(1.2, .55, .9);
    stone.rotation.y = random() * TAU;
  }
  const riverStone = material(0x6a7974);
  for (let i = 0; i < 32; i++) {
    const x = -15 + (random() - .5) * 7, z = random() * 95 - 47;
    const stone = mesh(new THREE.DodecahedronGeometry(.19 + random() * .35, 0), riverStone);
    stone.position.set(x, -2.27, z);
    stone.scale.y = .55;
  }
  riverRing = mesh(new THREE.TorusGeometry(.19, .028, 9, 22), material(0xb2a36d, .32, { metalness: .42 }));
  riverRing.position.set(-15.1, -2.18, 20.5);
  riverRing.rotation.set(-.3, .4, .25);
  for (let i = 0; i < 24; i++) {
    const x = -18.8 + random() * 7.6, z = 12 + random() * 31;
    const h = .28 + random() * .75, plant = material(0x426f60, 1, { side: THREE.DoubleSide });
    tube([v(x, -2.12, z), v(x + .07, -2.12 + h * .5, z), v(x + .14, -2.12 + h, z + .1)], .014, plant);
  }
}
function makePerson(name, coatColor, xOffset, startZ, pace) {
  const figure = new THREE.Group();
  const coat = material(coatColor, .92), skin = material(0xc9a183, 1), trousers = material(0x343e47);
  const hair = material(0x332b29), pack = material(0x6c5842);
  const body = mesh(new THREE.CapsuleGeometry(.25, .72, 4, 8), coat, figure);
  body.position.y = 1.19;
  const headPivot = new THREE.Group();
  headPivot.position.set(0, 1.78, 0);
  figure.add(headPivot);
  const head = mesh(new THREE.SphereGeometry(.23, 12, 9), skin, headPivot);
  head.position.set(0, .14, -.015);
  const haircap = mesh(new THREE.SphereGeometry(.238, 12, 8, 0, TAU, 0, Math.PI * .46), hair, headPivot);
  haircap.position.copy(head.position);
  const backpack = mesh(new THREE.BoxGeometry(.42, .62, .2), pack, figure);
  backpack.position.set(0, 1.26, .29);
  const arms = [], legs = [];
  for (const side of [-1, 1]) {
    const arm = new THREE.Group();
    arm.position.set(side * .31, 1.52, 0);
    const sleeve = mesh(new THREE.CapsuleGeometry(.075, .43, 3, 6), coat, arm);
    sleeve.position.y = -.3;
    figure.add(arm);
    arms.push(arm);
    const leg = new THREE.Group();
    leg.position.set(side * .12, .83, 0);
    const pant = mesh(new THREE.CapsuleGeometry(.09, .56, 3, 6), trousers, leg);
    pant.position.y = -.39;
    const boot = mesh(new THREE.BoxGeometry(.19, .14, .3), material(0x302c2a), leg);
    boot.position.set(0, -.79, -.09);
    figure.add(leg);
    legs.push(leg);
  }
  figure.scale.setScalar(name === "Léa" ? .78 : name === "Éva" ? .94 : 1.04);
  const modelHolder = new THREE.Group();
  figure.add(modelHolder);
  figure.userData = { name, xOffset, startZ, pace, arms, legs, headPivot, modelHolder,
    proceduralParts: figure.children.filter(part => part !== modelHolder), mixer: null, actions: null };
  scene.add(figure);
  return figure;
}
// Animations évaluées à temps absolu : pause et retour arrière déterministes.
function updatePeople(seconds) {
  const travelTime = Math.min(seconds, 13.2);
  const walkWeight = clamp((13.6 - seconds) / .6, 0, 1);
  for (const person of people) {
    const p = person.userData;
    const z = p.startZ - travelTime * .19 * p.pace;
    const x = trailX(z) + p.xOffset;
    const stride = seconds * 5.2 * p.pace + p.startZ;
    person.position.set(x, heightAt(x, z) + .13 +
      .009 * Math.sin(seconds * 2 + p.startZ) +
      walkWeight * .024 * Math.sin(stride * 2), z);
    person.rotation.y = -.12 * Math.cos(z * .115);
    p.arms[0].rotation.x = walkWeight * Math.sin(stride) * .40;
    p.arms[1].rotation.x = -walkWeight * Math.sin(stride) * .40;
    p.legs[0].rotation.x = -walkWeight * Math.sin(stride) * .34;
    p.legs[1].rotation.x = walkWeight * Math.sin(stride) * .34;
    p.headPivot.rotation.y = .15 * Math.sin(seconds * .95 + p.startZ) +
      (p.name === "Thomas" ? .2 * ease(clamp((seconds - 11.8) / 2, 0, 1)) : 0);
    p.headPivot.rotation.x = .045 * Math.sin(seconds * 1.35 + p.startZ);
    if (p.mixer && p.actions) {
      p.actions.walk?.setEffectiveWeight(walkWeight);
      p.actions.idle?.setEffectiveWeight(1 - walkWeight);
      p.mixer.setTime(seconds);
    }
  }
  if (riverRing) riverRing.rotation.z = .25 + .065 * Math.sin(seconds * 2.1) *
    Math.exp(-Math.max(0, seconds - .5));
}

// Seuls les modèles explicitement configurés sont demandés au navigateur.
// En cas d'absence ou d'erreur le personnage procédural est conservé.
async function loadCharacterModels() {
  if (!Object.values(CHARACTER_ASSETS).some(Boolean)) return;
  const { GLTFLoader } = await import("three/addons/loaders/GLTFLoader.js");
  const loader = new GLTFLoader();
  for (const person of people) {
    const config = CHARACTER_ASSETS[person.userData.name];
    if (!config?.url) continue;
    try {
      const gltf = await loader.loadAsync(config.url);
      const model = gltf.scene;
      model.scale.setScalar(config.scale ?? 1);
      model.rotation.y = config.rotationY ?? 0;
      model.position.y = config.yOffset ?? 0;
      person.userData.modelHolder.add(model);
      const clips = gltf.animations || [];
      if (clips.length) {
        const mixer = new THREE.AnimationMixer(model);
        const walk = clips.find(clip => /walk|marche/i.test(clip.name)) ?? clips[0];
        const idle = clips.find(clip => /idle|rest|repos/i.test(clip.name));
        const walkAction = mixer.clipAction(walk);
        walkAction.play();
        const idleAction = idle && idle !== walk ? mixer.clipAction(idle) : null;
        idleAction?.play();
        person.userData.mixer = mixer;
        person.userData.actions = { walk: walkAction, idle: idleAction };
      }
      for (const part of person.userData.proceduralParts) part.visible = false;
    } catch (error) {
      console.warn("Modèle externe indisponible : silhouette conservée pour " + person.userData.name, error);
    }
  }
}

function buildScene() {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x98b6b7);
  scene.fog = new THREE.FogExp2(0x9bb6b5, .012);
  camera = new THREE.PerspectiveCamera(60, 1, .08, 230);
  renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, window.innerWidth < 700 ? 1.25 : 1.65));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.35;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  sceneHost.prepend(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xe5f2eb, 0x50604f, 2.1));
  const sun = new THREE.DirectionalLight(0xffe4b5, 2.35);
  sun.position.set(-18, 36, -15);
  sun.castShadow = true;
  sun.shadow.mapSize.set(window.innerWidth < 700 ? 512 : 1024, window.innerWidth < 700 ? 512 : 1024);
  sun.shadow.camera.left = -44; sun.shadow.camera.right = 44;
  sun.shadow.camera.top = 48; sun.shadow.camera.bottom = -48;
  sun.shadow.camera.near = 1; sun.shadow.camera.far = 105;
  sun.shadow.bias = -.0003;
  scene.add(sun);
  drawGround();
  drawTrailAndBridge();
  drawNature();
  people = [
    makePerson("Thomas", 0x8b4f3b, -.42, 8.4, .85),
    makePerson("Éva", 0x8c9076, .24, 7.3, 1),
    makePerson("Léa", 0xb7a46b, -.08, 5.9, 1.13)
  ];
}
// A0 → A1 : 0–3 s rivière, 3–7,5 s vallée, 7,5–11 s relief,
// 11–15 s rapprochement du groupe. Mouvement continu sans coupe.
const cameraStops = [
  { t: 0, pos: v(-15, -1.92, 28.4), look: v(-15.1, -2.22, 20.5), fov: 53 },
  { t: 2, pos: v(-14.95, -1.45, 23.3), look: v(-15.05, -1.95, 17.5), fov: 57 },
  { t: 3.1, pos: v(-14.85, .45, 19.5), look: v(-11, 1.1, 9), fov: 62 },
  { t: 5.3, pos: v(-13, 4.9, 19.4), look: v(-5, 6, -8), fov: 65 },
  { t: 7.5, pos: v(-5, 9.2, 19.8), look: v(9, 11, -8), fov: 60 },
  { t: 9.5, pos: v(1.3, heightAt(1.3, 20) + 8, 20), look: v(9.7, heightAt(9.7, 8) + 1.7, 8), fov: 56 },
  { t: 11.3, pos: v(5.5, heightAt(5.5, 17) + 6, 17), look: v(9.4, heightAt(9.4, 7) + 1.5, 7), fov: 51 },
  { t: 13.2, pos: v(6.6, heightAt(6.6, 12) + 3.8, 12), look: v(trailX(6), heightAt(trailX(6), 6) + 1.4, 6), fov: 47 },
  { t: 15, pos: v(7.4, heightAt(7.4, 9) + 2.9, 9), look: v(trailX(5), heightAt(trailX(5), 5) + 1.5, 5), fov: 43 }
];
function ease(s) { return s * s * (3 - 2 * s); }
function updateCinematicCamera() {
  const t = clamp(elapsed, 0, DURATION);
  let a = cameraStops[0], b = cameraStops[cameraStops.length - 1];
  for (let i = 0; i < cameraStops.length - 1; i++) {
    if (t >= cameraStops[i].t && t <= cameraStops[i + 1].t) {
      a = cameraStops[i]; b = cameraStops[i + 1]; break;
    }
  }
  const s = ease(clamp((t - a.t) / (b.t - a.t), 0, 1));
  camera.position.copy(a.pos).lerp(b.pos, s);
  camera.lookAt(a.look.clone().lerp(b.look, s));
  camera.fov = mix(a.fov, b.fov, s);
  camera.updateProjectionMatrix();
  sceneHost.classList.toggle("underwater", camera.position.y < -1.05);
  if (t < 3) caption.textContent = "La rivière · 16 h 58";
  else if (t < 7.5) caption.textContent = "La vallée · le plan continue";
  else if (t < 11) caption.textContent = "La montagne · le sentier";
  else caption.textContent = "Thomas, Éva et Léa · la randonnée";
}
function updateOrbitCamera() {
  const target = people[0].position.clone().add(v(0, 1.5, 0));
  const cp = Math.cos(orbitPitch);
  camera.position.copy(target).add(v(
    orbitDistance * cp * Math.sin(orbitYaw),
    orbitDistance * Math.sin(orbitPitch),
    orbitDistance * cp * Math.cos(orbitYaw)
  ));
  camera.lookAt(target);
  camera.fov = 52;
  camera.updateProjectionMatrix();
  caption.textContent = "Vue libre · la randonnée";
}
function updateDisplay() {
  timeline.value = elapsed.toFixed(2);
  const n = Math.min(Math.floor(elapsed), DURATION);
  timecode.textContent = "00:" + String(n).padStart(2, "0") + " / 00:15";
  playPause.textContent = playing ? "⏸ Pause" : "▶ Reprendre";
  playPause.setAttribute("aria-pressed", String(!playing));
  cameraMode.textContent = freeView ? "◉ Vue caméra" : "◎ Vue libre";
  cameraMode.setAttribute("aria-pressed", String(freeView));
  sceneHost.classList.toggle("free-view", freeView);
  fullscreenButton.setAttribute("aria-pressed", String(Boolean(document.fullscreenElement)));
  fullscreenButton.textContent = document.fullscreenElement ? "⛶ Quitter le plein écran" : "⛶ Plein écran";
}
function resize() {
  const rect = sceneHost.getBoundingClientRect();
  if (!renderer || !rect.width || !rect.height) return;
  camera.aspect = rect.width / rect.height;
  camera.updateProjectionMatrix();
  renderer.setSize(rect.width, rect.height, false);
}
function tick(now) {
  const delta = lastFrame ? Math.min((now - lastFrame) / 1000, .05) : 0;
  lastFrame = now;
  if (playing) {
    const speed = Number(speedControl.value);
    if (elapsed < DURATION) elapsed = Math.min(DURATION, elapsed + delta * speed);
    if (elapsed >= DURATION) playing = false;
  }
  updatePeople(elapsed);
  if (freeView) updateOrbitCamera(); else updateCinematicCamera();
  updateDisplay();
  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
function toggleView() {
  freeView = !freeView;
  dragStart = null;
  pointers.clear();
  lastPinchDistance = 0;
  if (freeView) orbitYaw = -.65;
  updateDisplay();
}
async function toggleFullscreen() {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else if (appRoot.requestFullscreen) await appRoot.requestFullscreen();
    else throw new Error("Fullscreen API unavailable");
  } catch (error) {
    console.warn("Mode plein écran indisponible", error);
    document.getElementById("hint").textContent = "Plein écran indisponible sur ce navigateur.";
  }
  updateDisplay();
}
function setupControls() {
  fullscreenButton.addEventListener("click", toggleFullscreen);
  document.addEventListener("fullscreenchange", () => { resize(); updateDisplay(); });
  playPause.addEventListener("click", () => { playing = !playing; updateDisplay(); });
  replay.addEventListener("click", () => {
    elapsed = 0; playing = true; freeView = false; updateDisplay();
  });
  cameraMode.addEventListener("click", toggleView);
  timeline.addEventListener("input", () => {
    elapsed = Number(timeline.value);
    if (freeView) freeView = false;
    updateDisplay();
  });
  window.addEventListener("keydown", event => {
    if (event.target instanceof HTMLElement && ["INPUT", "SELECT", "BUTTON", "TEXTAREA"].includes(event.target.tagName)) return;
    if (event.code === "Space") { event.preventDefault(); playing = !playing; }
    if (event.key.toLowerCase() === "r") { elapsed = 0; playing = true; freeView = false; }
    if (event.key.toLowerCase() === "v") toggleView();
    if (event.key.toLowerCase() === "f") void toggleFullscreen();
    if (freeView && event.code === "ArrowLeft") orbitYaw -= .1;
    if (freeView && event.code === "ArrowRight") orbitYaw += .1;
  });
  renderer.domElement.addEventListener("pointerdown", event => {
    if (!freeView) return;
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    dragStart = { x: event.clientX, y: event.clientY };
    sceneHost.classList.add("is-dragging");
    renderer.domElement.setPointerCapture(event.pointerId);
    lastPinchDistance = 0;
  });
  renderer.domElement.addEventListener("pointermove", event => {
    if (!freeView || !pointers.has(event.pointerId)) return;
    const prev = pointers.get(event.pointerId);
    pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
    if (pointers.size >= 2) {
      const [first, second] = [...pointers.values()];
      const distance = Math.hypot(first.x - second.x, first.y - second.y);
      if (lastPinchDistance > 0 && distance > 0)
        orbitDistance = clamp(orbitDistance * lastPinchDistance / distance, 4, 34);
      lastPinchDistance = distance;
    } else {
      orbitYaw -= (event.clientX - prev.x) * .007;
      orbitPitch = clamp(orbitPitch + (event.clientY - prev.y) * .005, -.1, 1.27);
    }
  });
  for (const kind of ["pointerup", "pointercancel", "lostpointercapture"]) {
    renderer.domElement.addEventListener(kind, event => {
      pointers.delete(event.pointerId);
      lastPinchDistance = 0;
      if (!pointers.size) {
        dragStart = null;
        sceneHost.classList.remove("is-dragging");
      }
    });
  }
  renderer.domElement.addEventListener("wheel", event => {
    if (!freeView) return;
    event.preventDefault();
    orbitDistance = clamp(orbitDistance * Math.exp(event.deltaY * .001), 4, 34);
  }, { passive: false });
  window.addEventListener("resize", resize);
}
try {
  buildScene();
  setupControls();
  resize();
  if (reducedMotion) { elapsed = 0; playing = false; }
  loading.hidden = true;
  requestAnimationFrame(tick);
  void loadCharacterModels().catch(error => console.warn("Modèles externes indisponibles ; silhouettes conservées.", error));
} catch (error) {
  console.error("POLOP : impossible de lancer la démo 3D", error);
  loading.hidden = true;
  sceneError.hidden = false;
  sceneError.textContent = "La démo 3D ne peut pas démarrer sur cet appareil. Vérifiez la prise en charge de WebGL et réessayez dans un navigateur récent.";
}
