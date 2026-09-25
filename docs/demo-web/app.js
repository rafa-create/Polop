import * as THREE from "three";
import { DURATION, BEATS, CHAPTERS, beatAt, formatTime } from "./storyboard.js";
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
const fullscreenButton = document.getElementById("fullscreen");
const soundButton = document.getElementById("sound");
const chapters = document.getElementById("chapters");
const subtitle = document.getElementById("film-subtitle");
const storyNote = document.getElementById("film-note");
const curtain = document.getElementById("final-curtain");
const appRoot = document.getElementById("app");
const TAU = Math.PI * 2;
const clamp = THREE.MathUtils.clamp;
const mix = THREE.MathUtils.lerp;
let renderer, scene, camera, people = [], riverRing, riverSurface, sunLight;
let reverseThomas, caveRing, collisionRing, bridgeHook, rearEntrance;
const reverseEffects = [], panoramaTrail = [];
const riverParticles = [];
const daylight = new THREE.Color(0x98b6b7), submergedLight = new THREE.Color(0x356c78);
let soundEnabled = false, audioContext, riverGain, windGain;
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
  riverSurface = mesh(new THREE.PlaneGeometry(8.4, 124), material(0x4f9b9f, .23, {
    transparent: true, opacity: .72, depthWrite: false, side: THREE.DoubleSide, metalness: .06
  }));
  riverSurface.rotation.x = -Math.PI / 2;
  riverSurface.position.set(-15, -1.05, 0);
  riverSurface.castShadow = false;
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
  // Water motes are real meshes in the river, animated at absolute film time.
  const moteGeometry = new THREE.SphereGeometry(.022, 5, 4);
  const moteMaterial = material(0xb7ded2, 1, { transparent: true, opacity: .48, depthWrite: false });
  for (let i = 0; i < 65; i++) {
    const mote = mesh(moteGeometry, moteMaterial);
    const x = -18.4 + random() * 6.8, z = 12 + random() * 31;
    const y = -1.45 - random() * 1.10, phase = random() * TAU;
    mote.position.set(x, y, z);
    mote.castShadow = false;
    mote.userData = { x, y, z, phase };
    riverParticles.push(mote);
  }
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
// Spatial blockout of the same family, cave, bridge and reverse traversal.
// It is not a certified physical simulation of all the manuscript's causal events.
const CAVE_FRONT_Z = -28;
const bridgeX = trailX(-12.5);
function between(t, a, b) { return clamp((t - a) / (b - a), 0, 1); }
function move2(a, b, fraction) {
  const f = ease(between(fraction, 0, 1));
  return [mix(a[0], b[0], f), mix(a[1], b[1], f)];
}
function familySnapshot(t) {
  // Forward film time. On the reversed leg we replay the *same* forward poses
  // at their earlier objective instant rather than inventing a second family.
  if (t < 36) return [trailX(10), 10];
  if (t < 57) { const z = mix(10, -9, ease(between(t, 36, 57))); return [trailX(z), z]; }
  if (t < 90) return [trailX(-9), -9];
  if (t < 106) { const z = mix(-9, -26, ease(between(t, 90, 106))); return [trailX(z), z]; }
  return [trailX(-26), -26];
}
const OBJECTIVE_REPLAY = [
  [179, 166], [195, 143], [210, 121], [225, 105],
  [245, 92], [259, 88], [272, 77], [282, 81], [288, 83], [295, 93]
];
function normalFilmTime(t) {
  if (t < 179) return t;
  for (let i = 0; i < OBJECTIVE_REPLAY.length - 1; i++) {
    const [s, a] = OBJECTIVE_REPLAY[i], [e, b] = OBJECTIVE_REPLAY[i + 1];
    if (t <= e) return mix(a, b, between(t, s, e));
  }
  return 93 + (t - 295);
}
function placePerson(person, x, z, filmTime, heading = 0, walk = 1) {
  const p = person.userData;
  const step = filmTime * 5.1 * p.pace + p.startZ;
  person.visible = true;
  person.position.set(x, heightAt(x, z) + .16 + .013 * Math.sin(step * 2) * walk, z);
  person.rotation.y = heading;
  p.arms[0].rotation.x = walk * Math.sin(step) * .42;
  p.arms[1].rotation.x = -walk * Math.sin(step) * .42;
  p.legs[0].rotation.x = -walk * Math.sin(step) * .35;
  p.legs[1].rotation.x = walk * Math.sin(step) * .35;
  p.headPivot.rotation.y = .12 * Math.sin(filmTime * .75 + p.startZ);
  p.headPivot.rotation.x = .05 * Math.sin(filmTime * 1.1 + p.startZ);
  if (p.mixer && p.actions) {
    p.actions.walk?.setEffectiveWeight(walk);
    p.actions.idle?.setEffectiveWeight(1 - walk);
    p.mixer.setTime(filmTime);
  }
}
function updatePeople(seconds) {
  const t = clamp(seconds, 0, DURATION);
  const replayTime = normalFilmTime(t), [normalX, normalZ] = familySnapshot(replayTime);
  const [thomas, eva, lea] = people;
  let thomasX = normalX - .42, thomasZ = normalZ + 1.3;
  let evaX = normalX + .38, evaZ = normalZ -.45;
  let leaX = normalX -.15, leaZ = normalZ - 1.2;
  const hiking = t < 36 ? 0 : 1;
  if (replayTime >= 57 && replayTime < 72) {
    leaZ = mix(-10.3, -14.7, ease(between(replayTime, 57, 72)));
    leaX = trailX(leaZ);
  } else if (replayTime >= 72 && replayTime < 90) {
    const u = ease(between(replayTime, 72, 90));
    leaZ = mix(-14.7, -9.4, u);
    leaX = trailX(leaZ) + 2.7 * Math.sin(Math.PI * u);
    thomasZ = -8.5;
  }
  if (replayTime >= 106 && replayTime < 136) {
    evaZ = -26.3; leaZ = -25.3;
    if (replayTime >= 121) {
      const u = between(replayTime, 121, 136);
      evaX = normalX + 1 + .9 * Math.sin(u * 6);
      leaX = normalX + .2 + .7 * Math.sin(u * 7);
    }
    const u = ease(between(replayTime, 106, 128));
    thomasX = mix(thomasX, trailX(CAVE_FRONT_Z) + 1.6, u);
    thomasZ = mix(thomasZ, CAVE_FRONT_Z, u);
  } else if (replayTime >= 136) {
    const u = ease(between(replayTime, 136, 165));
    thomasX = mix(trailX(CAVE_FRONT_Z) + 1.6, 17.8, u);
    thomasZ = mix(CAVE_FRONT_Z, -27.2, u);
    const womenLeave = ease(between(replayTime, 134, 151));
    evaZ = mix(-26, -19, womenLeave);
    leaZ = evaZ + 1;
  }
  if (replayTime >= 166) {
    thomasX = 17.8; thomasZ = -27.2;
  }
  // The normal occurrence remains physically present in its objective time;
  // distance/relief may conceal it, but no character is removed to resolve a collision.
  placePerson(thomas, thomasX, thomasZ, replayTime, 0, hiking);
  placePerson(eva, evaX, evaZ, replayTime, 0, replayTime >= 121 ? .25 : hiking);
  placePerson(lea, leaX, leaZ, replayTime, 0, replayTime >= 121 ? .3 : hiking);
  // Same collision, seen first in A2 and again in B7/B8.
  const earlyCollision = t >= 80 && t <= 87;
  const reversedLeg = t >= 179 && t <= 288;
  reverseThomas.visible = earlyCollision || reversedLeg;
  if (earlyCollision) {
    const u = between(t, 80, 87);
    placePerson(reverseThomas, trailX(-8.5) + mix(1.6, -.42, u),
      mix(-10, -8.5, u), 282 + 6 * u, Math.PI, 1);
    reverseThomas.visible = true;
  } else if (reversedLeg) {
    let route;
    if (t < 195) route = move2([17.8, -27.2], [32, -26], between(t, 179, 195));
    else if (t < 210) route = move2([32, -26], [42, -16], between(t, 195, 210));
    else if (t < 225) route = move2([42, -16], [39, -4], between(t, 210, 225));
    else if (t < 245) route = move2([39, -4], [27, -8], between(t, 225, 245));
    else if (t < 259) route = move2([27, -8], [19, -12], between(t, 245, 259));
    else if (t < 272) route = move2([19, -12], [bridgeX, -14.7], between(t, 259, 272));
    else if (t < 282) route = move2([bridgeX, -14.7], [trailX(-9), -9], between(t, 272, 282));
    else route = move2([trailX(-9), -9], [trailX(-8.5) - .42, -8.5], between(t, 282, 288));
    placePerson(reverseThomas, route[0], route[1], t, Math.PI, t >= 259 ? 1 : .85);
  }
  const caveFocus = t >= 151 && t < 195;
  caveRing.visible = caveFocus;
  // Simple physical direction cue: ring rises before contact, falls afterwards.
  caveRing.position.set(18.25, heightAt(18.25, -27.5) + .7 +
    (t < 166 ? .35 * between(t, 151, 166) : 1.1 - .45 * between(t, 166, 195)), -27.5);
  collisionRing.visible = earlyCollision || (t >= 282 && t < 289);
  collisionRing.position.set(trailX(-8.5) - .2,
    heightAt(trailX(-8.5), -8.5) + 1.1, -8.5);
  // The hook starts attached, is detached in forward time, and is attached
  // by Thomas during the inverse passage; it never spontaneously snaps shut.
  const hooked = t < 78 || (t >= 278 && t < 288);
  bridgeHook.position.set(bridgeX + .94, heightAt(bridgeX, -10.3) + (hooked ? 1.1 : .3), -10.3);
  bridgeHook.rotation.x = hooked ? .25 : 1.55;
  riverRing.visible = t < 36;
  const reverseNow = reversedLeg || (t >= 166 && t < 179);
  for (const effect of reverseEffects) {
    effect.visible = reverseNow;
    if (!reverseNow) continue;
    const p = effect.userData;
    const s = (t - 166) * .8 + p.phase;
    effect.position.set(p.x + .09 * Math.sin(s), p.y + .18 * Math.abs(Math.sin(s * .9)), p.z);
  }
  if (riverSurface) riverSurface.position.y = -1.05 + .012 * Math.sin(t * 1.7);
  for (const mote of riverParticles) {
    const p = mote.userData;
    mote.position.set(p.x + .11 * Math.sin(t * .8 + p.phase),
      p.y + .035 * Math.sin(t * 1.2 + p.phase), p.z - t * .012);
  }
  // The full topological loop and both mouths are revealed at the ending.
  rearEntrance.visible = t >= 179;
  for (const segment of panoramaTrail) segment.visible = t >= 295;
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

function buildNarrativeSetpieces() {
  const stone = material(0x626a60), darkRock = material(0x353d3a);
  const mouth = material(0x1b292a, 1, { side: THREE.DoubleSide });
  const mouthFront = new THREE.Group();
  const cx = trailX(CAVE_FRONT_Z) + 1.6;
  mouthFront.position.set(cx, heightAt(cx, CAVE_FRONT_Z) + .6, CAVE_FRONT_Z);
  for (const side of [-1, 1]) {
    const rock = mesh(new THREE.DodecahedronGeometry(1.7, 1), darkRock, mouthFront);
    rock.position.set(side * 1.25, 1.2, -.4);
    rock.scale.set(.75, 1.15, 1);
  }
  const roof = mesh(new THREE.DodecahedronGeometry(1.7, 1), stone, mouthFront);
  roof.position.set(0, 2.65, -.35);
  roof.scale.set(1.5, .38, 1);
  const shadow = mesh(new THREE.PlaneGeometry(1.9, 2.7), mouth, mouthFront);
  shadow.position.set(0, 1.2, -.72);
  shadow.castShadow = false;
  scene.add(mouthFront);
  const rear = new THREE.Group();
  rear.position.set(32, heightAt(32, -26) + .6, -26);
  const shadowRear = mesh(new THREE.PlaneGeometry(3.5, 3.4), mouth, rear);
  shadowRear.position.y = 1.5;
  shadowRear.castShadow = false;
  for (const side of [-1, 1]) {
    const rock = mesh(new THREE.DodecahedronGeometry(1.7, 0), stone, rear);
    rock.position.set(side * 2, 1, -.45);
    rock.scale.set(.65, 1.6, 1);
  }
  const lintel = mesh(new THREE.DodecahedronGeometry(2, 0), stone, rear);
  lintel.position.set(0, 3.1, -.4);
  lintel.scale.set(1.45, .42, .85);
  scene.add(rear);
  rearEntrance = rear;
  // Two rock mouths and suggestive dark walls are a blockout, not a tested
  // collision-safe, hidden passage through the source Unreal landscape.
  const corridor = material(0x3d4846);
  for (let i = 0; i <= 9; i++) {
    const u = i / 9, x = mix(cx + .5, 31, u), z = mix(-28, -26, u);
    const floor = heightAt(x, z) + .07;
    const left = mesh(new THREE.DodecahedronGeometry(1.15, 0), corridor);
    left.position.set(x, floor + .8, z - 1.5);
    left.scale.set(.66, 1.15, .9);
    const right = mesh(new THREE.DodecahedronGeometry(1.15, 0), corridor);
    right.position.set(x, floor + .8, z + 1.5);
    right.scale.set(.66, 1.15, .9);
  }
  caveRing = mesh(new THREE.TorusGeometry(.22, .034, 9, 22), material(0xb7a978, .35, { metalness: .42 }));
  collisionRing = mesh(new THREE.TorusGeometry(.12, .023, 7, 20), material(0xb7a978, .35, { metalness: .42 }));
  bridgeHook = mesh(new THREE.TorusGeometry(.16, .033, 7, 20), material(0xb4a49b, .45, { metalness: .4 }));
  const reverseStone = material(0xc2bdb1);
  for (let i = 0; i < 45; i++) {
    const x = 15 + random() * 29, z = -26 + random() * 30;
    const particle = mesh(new THREE.DodecahedronGeometry(.025 + random() * .03, 0), reverseStone);
    particle.castShadow = false;
    particle.userData = { x, y: heightAt(x, z) + .15, z, phase: random() * TAU };
    reverseEffects.push(particle);
  }
  // The same path encircling the mountain; only revealed in the final pullback.
  const pathMat = material(0xa79b77);
  const points = [
    [trailX(-29), -29], [14, -35], [25, -38], [39, -28],
    [47, -12], [42, 5], [29, 16], [17, 19], [trailX(16), 16]
  ];
  for (let j = 0; j < points.length - 1; j++) {
    const a = points[j], b = points[j + 1];
    for (let k = 0; k < 15; k++) {
      const u = k / 15, x = mix(a[0], b[0], u), z = mix(a[1], b[1], u);
      const slab = mesh(new THREE.BoxGeometry(1.25, .06, 1.25), pathMat);
      slab.castShadow = false;
      slab.position.set(x, heightAt(x, z) + .08, z);
      panoramaTrail.push(slab);
    }
  }
  const rock = mesh(new THREE.DodecahedronGeometry(1.45, 1), stone);
  rock.position.set(trailX(-8.5) + 1.1, heightAt(trailX(-8.5), -8.5) + .65, -8.5);
  rock.scale.set(1, 1.2, 1.15);
  reverseThomas = makePerson("Thomas", 0x8b4f3b, -.42, 8.4, .85);
  reverseThomas.visible = false;
}
function buildScene() {
  scene = new THREE.Scene();
  scene.background = daylight.clone();
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
  sunLight = new THREE.DirectionalLight(0xffe4b5, 2.35);
  sunLight.position.set(-18, 36, -15);
  sunLight.castShadow = true;
  sunLight.shadow.mapSize.set(window.innerWidth < 700 ? 512 : 1024, window.innerWidth < 700 ? 512 : 1024);
  sunLight.shadow.camera.left = -44; sunLight.shadow.camera.right = 44;
  sunLight.shadow.camera.top = 48; sunLight.shadow.camera.bottom = -48;
  sunLight.shadow.camera.near = 1; sunLight.shadow.camera.far = 105;
  sunLight.shadow.bias = -.0003;
  scene.add(sunLight);
  drawGround();
  drawTrailAndBridge();
  drawNature();
  people = [
    makePerson("Thomas", 0x8b4f3b, -.42, 8.4, .85),
    makePerson("Éva", 0x8c9076, .24, 7.3, 1),
    makePerson("Léa", 0xb7a46b, -.08, 5.9, 1.13)
  ];
  buildNarrativeSetpieces();
}
// Continuous shot, compressed dramaturgy. No new portal or invented causality.
const cameraStops = [
  { t: 0, pos: v(-15, -1.92, 28.4), look: v(-15.1, -2.22, 20.5), fov: 53 },
  { t: 12, pos: v(-14.95, -1.52, 23.2), look: v(-15.1, -1.95, 17.4), fov: 58 },
  { t: 18, pos: v(-14.85, .45, 19.5), look: v(-11, 1.1, 9), fov: 62 },
  { t: 28, pos: v(-13, 4.9, 19.4), look: v(-5, 6, -8), fov: 65 },
  { t: 36, pos: v(-5, 9.2, 19.8), look: v(9, 11, -8), fov: 60 },
  { t: 49, pos: v(5, heightAt(5, 12) + 4, 12), look: v(trailX(0), heightAt(trailX(0), 0) + 1.2, 0), fov: 50 },
  { t: 57, pos: v(trailX(-8) - 4, heightAt(trailX(-8), -8) + 3.2, -5),
    look: v(bridgeX, heightAt(bridgeX, -12.5) + .8, -12.5), fov: 48 },
  { t: 72, pos: v(bridgeX - 3, heightAt(bridgeX, -12.5) + 2.5, -11),
    look: v(bridgeX, heightAt(bridgeX, -12.5) + .7, -12.5), fov: 44 },
  { t: 83, pos: v(trailX(-8.5) - 2.5, heightAt(trailX(-8.5), -8.5) + 2.1, -6),
    look: v(trailX(-8.5), heightAt(trailX(-8.5), -8.5) + 1.3, -8.5), fov: 45 },
  { t: 90, pos: v(trailX(-9) - 4, heightAt(trailX(-9), -9) + 4, -3),
    look: v(trailX(-9), heightAt(trailX(-9), -9) + 1.5, -9), fov: 52 },
  { t: 106, pos: v(trailX(-25) - 5, heightAt(trailX(-25), -25) + 4, -18),
    look: v(trailX(-26), heightAt(trailX(-26), -26) + 1.5, -26), fov: 50 },
  { t: 121, pos: v(trailX(-26) - 2.6, heightAt(trailX(-26), -26) + 2.4, -22),
    look: v(trailX(-26), heightAt(trailX(-26), -26) + 1.5, -26), fov: 44 },
  { t: 136, pos: v(trailX(-26) - 2.2, heightAt(trailX(-26), -26) + 2.9, -24),
    look: v(trailX(-26), heightAt(trailX(-26), -26) + 1.2, -26), fov: 47 },
  { t: 151, pos: v(trailX(-28) + 1, heightAt(trailX(-28) + 1, -28) + 1.8, -27),
    look: v(17.8, heightAt(17.8, -27.2) + .8, -27.2), fov: 49 },
  { t: 166, pos: v(15.5, heightAt(15.5, -27.2) + 1.8, -25.7),
    look: v(18.25, heightAt(18.25, -27.5) + .8, -27.5), fov: 38 },
  { t: 179, pos: v(17, heightAt(17, -27.2) + 2, -25.1),
    look: v(20, heightAt(20, -27.2) + 1.2, -27.2), fov: 47 },
  { t: 195, pos: v(29, heightAt(29, -26) + 2.3, -24),
    look: v(32, heightAt(32, -26) + 1.5, -26), fov: 55 },
  { t: 210, pos: v(36, heightAt(36, -22) + 4, -19),
    look: v(42, heightAt(42, -16) + 1.6, -16), fov: 56 },
  { t: 225, pos: v(35, heightAt(35, -4) + 6, 2),
    look: v(39, heightAt(39, -4) + 1.3, -4), fov: 56 },
  { t: 245, pos: v(24, heightAt(24, -8) + 4, -3),
    look: v(27, heightAt(27, -8) + 1.5, -8), fov: 50 },
  { t: 259, pos: v(18, heightAt(18, -12) + 3.4, -9),
    look: v(19, heightAt(19, -12) + 1.1, -12), fov: 50 },
  { t: 272, pos: v(bridgeX - 3, heightAt(bridgeX, -12.5) + 3.1, -10),
    look: v(bridgeX, heightAt(bridgeX, -12.5) + .8, -12.5), fov: 42 },
  { t: 282, pos: v(bridgeX - 1.6, heightAt(bridgeX - 1.6, -10) + 3.4, -10),
    look: v(bridgeX + .9, heightAt(bridgeX, -10.3) + 1, -10.3), fov: 41 },
  { t: 288, pos: v(trailX(-8.5) - 2.3, heightAt(trailX(-8.5), -8.5) + 2, -6),
    look: v(trailX(-8.5), heightAt(trailX(-8.5), -8.5) + 1.3, -8.5), fov: 43 },
  { t: 295, pos: v(trailX(-8) - 4, heightAt(trailX(-8), -8) + 3.7, 1),
    look: v(trailX(-8), heightAt(trailX(-8), -8) + 1.5, -8), fov: 52 },
  { t: 300, pos: v(-25, 54, 41), look: v(16, 5, -12), fov: 66 }
];
function ease(s) { return s * s * (3 - 2 * s); }
// Cubic Hermite interpolation preserves a continuous velocity at every
// camera marker. V2's smoothstep paused for an instant at EACH marker.
function scalarTangent(index, key) {
  const left = cameraStops[Math.max(0, index - 1)];
  const right = cameraStops[Math.min(cameraStops.length - 1, index + 1)];
  return (right[key] - left[key]) / (right.t - left.t);
}
function vectorTangent(index, key) {
  const left = cameraStops[Math.max(0, index - 1)];
  const right = cameraStops[Math.min(cameraStops.length - 1, index + 1)];
  return right[key].clone().sub(left[key]).multiplyScalar(1 / (right.t - left.t));
}
function hermite(a, b, tangentA, tangentB, u, duration) {
  const u2 = u * u, u3 = u2 * u;
  return (2 * u3 - 3 * u2 + 1) * a + (u3 - 2 * u2 + u) * duration * tangentA +
    (-2 * u3 + 3 * u2) * b + (u3 - u2) * duration * tangentB;
}
function poseAt(seconds) {
  const t = clamp(seconds, 0, DURATION);
  let i = cameraStops.length - 2;
  for (let j = 0; j < cameraStops.length - 1; j++) {
    if (t <= cameraStops[j + 1].t) { i = j; break; }
  }
  const a = cameraStops[i], b = cameraStops[i + 1];
  const duration = b.t - a.t, u = clamp((t - a.t) / duration, 0, 1);
  const interpolateVector = key => {
    const left = vectorTangent(i, key), right = vectorTangent(i + 1, key);
    return v(
      hermite(a[key].x, b[key].x, left.x, right.x, u, duration),
      hermite(a[key].y, b[key].y, left.y, right.y, u, duration),
      hermite(a[key].z, b[key].z, left.z, right.z, u, duration)
    );
  };
  return {
    pos: interpolateVector("pos"),
    look: interpolateVector("look"),
    fov: hermite(a.fov, b.fov, scalarTangent(i, "fov"),
      scalarTangent(i + 1, "fov"), u, duration)
  };
}
function applyAtmosphere() {
  // The water line is spatial, not based on the caption/timeline chapter.
  const surfaceY = riverSurface?.position.y ?? -1.05;
  const submersion = 1 - ease(clamp((camera.position.y - surfaceY + .20) / .40, 0, 1));
  scene.background.lerpColors(daylight, submergedLight, submersion);
  scene.fog.color.lerpColors(new THREE.Color(0x9bb6b5), submergedLight, submersion);
  scene.fog.density = mix(elapsed >= 295 ? .0035 : .012, .070, submersion);
  sunLight.intensity = mix(2.35, 1.20, submersion);
  renderer.toneMappingExposure = mix(1.35, 1.12, submersion);
  sceneHost.classList.toggle("underwater", submersion > .5);
}
function updateCinematicCamera() {
  const t = clamp(elapsed, 0, DURATION);
  const pose = poseAt(t);
  camera.position.copy(pose.pos);
  camera.lookAt(pose.look);
  camera.fov = pose.fov;
  camera.updateProjectionMatrix();
  applyAtmosphere();
  caption.textContent = beatAt(t).title;
}
function updateOrbitCamera() {
  const focus = elapsed >= 179 && elapsed < 288 ? reverseThomas : people[0];
  const target = focus.position.clone().add(v(0, 1.5, 0));
  const cp = Math.cos(orbitPitch);
  camera.position.copy(target).add(v(
    orbitDistance * cp * Math.sin(orbitYaw),
    orbitDistance * Math.sin(orbitPitch),
    orbitDistance * cp * Math.cos(orbitYaw)
  ));
  camera.lookAt(target);
  camera.fov = 52;
  camera.updateProjectionMatrix();
  applyAtmosphere();
  caption.textContent = "Vue libre · " + beatAt(elapsed).title;
}
// Opt-in, locally synthesized ambience: no music licensing or remote audio.
function createNoiseLoop(context, type, frequency) {
  const buffer = context.createBuffer(1, context.sampleRate * 2, context.sampleRate);
  const data = buffer.getChannelData(0);
  let previous = 0;
  for (let i = 0; i < data.length; i++) {
    const white = Math.random() * 2 - 1;
    previous = (previous + .04 * white) / 1.04;
    data[i] = previous * 3;
  }
  const source = context.createBufferSource();
  source.buffer = buffer;
  source.loop = true;
  const filter = context.createBiquadFilter();
  filter.type = type;
  filter.frequency.value = frequency;
  const gain = context.createGain();
  gain.gain.value = 0;
  source.connect(filter).connect(gain).connect(context.destination);
  source.start();
  return gain;
}
async function toggleSound() {
  if (soundEnabled) {
    soundEnabled = false;
    updateSound();
    updateDisplay();
    return;
  }
  try {
    if (!audioContext) {
      const AudioContextType = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextType) throw new Error("Web Audio unavailable");
      audioContext = new AudioContextType();
      riverGain = createNoiseLoop(audioContext, "lowpass", 650);
      windGain = createNoiseLoop(audioContext, "bandpass", 380);
    }
    await audioContext.resume();
    soundEnabled = true;
  } catch (error) {
    soundEnabled = false;
    console.warn("Ambiance sonore indisponible", error);
    document.getElementById("hint").textContent =
      "Ce navigateur ne permet pas de démarrer l’ambiance sonore. Le film reste utilisable sans son.";
  }
  updateSound();
  updateDisplay();
}
function updateSound() {
  if (!audioContext || !riverGain || !windGain) return;
  const now = audioContext.currentTime, active = soundEnabled && playing ? 1 : 0;
  const waterMix = 1 - ease(clamp((elapsed - 24) / 18, 0, 1));
  const inverseMix = elapsed >= 166 && elapsed < 288 ? .65 : 1;
  riverGain.gain.setTargetAtTime(active * mix(.075, .18, waterMix), now, .12);
  windGain.gain.setTargetAtTime(active * mix(.11, .025, waterMix) * inverseMix, now, .12);
}
function updateDisplay() {
  timeline.value = elapsed.toFixed(2);
  timecode.textContent = formatTime(elapsed) + " / " + formatTime(DURATION);
  const beat = beatAt(elapsed);
  subtitle.textContent = beat.caption;
  storyNote.textContent = beat.note;
  const chapter = [...CHAPTERS].reverse().find(c => c.time <= elapsed);
  if (chapter && chapters.value !== String(chapter.time)) chapters.value = String(chapter.time);
  curtain.style.opacity = String(ease(between(elapsed, 299.3, 300)));
  playPause.textContent = playing ? "⏸ Pause" : "▶ Reprendre";
  playPause.setAttribute("aria-pressed", String(!playing));
  cameraMode.textContent = freeView ? "◉ Vue caméra" : "◎ Vue libre";
  cameraMode.setAttribute("aria-pressed", String(freeView));
  sceneHost.classList.toggle("free-view", freeView);
  sceneHost.dataset.scene = beat.scene;
  sceneHost.dataset.act = beat.act;
  sceneHost.dataset.secondThomas = String(reverseThomas?.visible ?? false);
  soundButton.textContent = soundEnabled ? "♫ Couper le son" : "♫ Activer le son";
  soundButton.setAttribute("aria-pressed", String(soundEnabled));
  soundButton.setAttribute("aria-label", soundEnabled ? "Couper l’ambiance sonore" : "Activer l’ambiance sonore");
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
  updateSound();
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
  for (const chapter of CHAPTERS) {
    const option = document.createElement("option");
    option.value = String(chapter.time);
    option.textContent = chapter.label;
    chapters.append(option);
  }
  chapters.addEventListener("change", () => {
    elapsed = Number(chapters.value);
    freeView = false;
    updatePeople(elapsed);
    updateCinematicCamera();
    updateDisplay();
  });
  soundButton.addEventListener("click", () => { void toggleSound(); });
  fullscreenButton.addEventListener("click", toggleFullscreen);
  document.addEventListener("fullscreenchange", () => { resize(); updateDisplay(); });
  playPause.addEventListener("click", () => { playing = !playing; updateDisplay(); });
  replay.addEventListener("click", () => {
    elapsed = 0; playing = true; freeView = false; updateDisplay();
  });
  cameraMode.addEventListener("click", toggleView);
  timeline.addEventListener("input", () => {
    elapsed = clamp(Number(timeline.value), 0, DURATION);
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
