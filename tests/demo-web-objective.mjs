// Regression causale : une seule horloge objective pour A, B et B9.
// Les tests sont indépendants de Three.js et réutilisent les sources web.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const sourceRoot="docs/demo-web/";
const geometryText=await readFile(sourceRoot+"bridge-geometry.js","utf8");
const geometryUrl="data:text/javascript;base64,"+Buffer.from(geometryText).toString("base64");
const clockText=(await readFile(sourceRoot+"objective-timeline.js","utf8"))
  .replace('from "./bridge-geometry.js"', 'from "'+geometryUrl+'"');
const { CLOCK, CONTACT_CAVE, CONTACT_ROCK, HOOK_CHANGE, objectiveAt,
  playbackDirection, worldAt, worldAtFilmTime }=
  await import("data:text/javascript;base64,"+Buffer.from(clockText).toString("base64"));
const { baseHeight, heightAt, bridgeDeckPoint }=await import(geometryUrl);
assert.equal(CONTACT_CAVE,179);
assert.equal(CONTACT_ROCK,81);
assert.equal(HOOK_CHANGE,86);
assert.equal(CLOCK[0].objective,0);
assert.equal(CLOCK.at(-1).film,300);
for(let t=179;t<288;t+=.125) {
  assert.ok(objectiveAt(t+.125)<objectiveAt(t),
    "L'horloge objective doit reculer strictement pendant B : "+t);
  assert.equal(playbackDirection(t),-1);
}
assert.equal(objectiveAt(179),179);
assert.equal(objectiveAt(288),81);
assert.equal(playbackDirection(288),1);
for(const [forward,reverse] of [[160,195],[143,210],[108,245],
  [98,259],[87,272],[86,276],[85,278],[84,282],[81,288]]) {
  const before=worldAtFilmTime(forward),after=worldAtFilmTime(reverse);
  assert.equal(after.objective,forward,"L'horloge B ne pointe pas sur l'événement A");
  for(const who of ["Thomas","Eva","Lea"]) {
    assert.deepEqual(after[who],before[who],
      who+" : l'événement objectif change selon le sens de lecture à "+reverse);
  }
  assert.deepEqual(after.reverseThomas,before.reverseThomas,
    "Les deux apparitions de Thomas inversé doivent réutiliser la même trajectoire");
  assert.equal(after.hookAttached,before.hookAttached);
}
const forwardContact=worldAtFilmTime(81),returnContact=worldAtFilmTime(288);
assert.deepEqual(forwardContact,returnContact,
  "A2 et B8 ne montrent pas le même instant physique");
for(const world of [forwardContact,returnContact]) {
  assert.ok(world.reverseThomas,"Seconde occurrence absente au contact");
  for(const axis of ["x","y","z"])
    assert.equal(world.Thomas[axis],world.reverseThomas[axis],
      "Les deux Thomas ne se rejoignent pas au même endroit");
}
assert.equal(worldAt(80).reverseThomas,null);
assert.ok(worldAt(82).reverseThomas);
assert.equal(worldAt(85.99).hookAttached,true);
assert.equal(worldAt(86).hookAttached,false);
assert.equal(worldAtFilmTime(276).hookAttached,false);
assert.equal(worldAtFilmTime(278).hookAttached,true);
assert.equal(worldAtFilmTime(280).reverseThomas.surface,"bridge");
assert.equal(worldAtFilmTime(68).Lea.surface,"bridge");
assert.equal(worldAtFilmTime(80).Lea.surface,"terrain");
// Pendant B1/B2, ce sont des corps en mouvement, orientés dans leur sens
// NORMAL mais vus parcourant leurs positions dans l'ordre inverse.
const bEarly=worldAtFilmTime(195),bLater=worldAtFilmTime(210);
for(const who of ["Eva","Lea"]) {
  assert.ok(bLater[who].z<bEarly[who].z-3.5,
    who+" doit REVENIR à reculons sur la pente, pas rester immobilisée");
  assert.ok(Math.cos(bEarly[who].heading)<-.5 &&
    Math.cos(bLater[who].heading)<-.5,
    who+" doit rester globalement tournée vers la descente pendant la marche arrière");
}
for(let t=90;t<=99;t+=.05) {
  const world=worldAt(t);
  for(const who of ["Thomas","Eva","Lea"]) {
    const p=world[who],drop=baseHeight(p.x,p.z)-heightAt(p.x,p.z);
    assert.ok(drop<1.2,who+" descend dans le creux malgré le détour à "+t);
    assert.equal(p.surface,"terrain");
  }
}
for(let t=57;t<72;t+=.25) {
  const p=worldAt(t).Lea;
  assert.equal(p.surface,"bridge");
  const deck=bridgeDeckPoint((p.z+10.3)/(-14.7+10.3));
  assert.ok(Math.abs(p.y-deck.y-.065)<.00001);
}
for(const [time,direction] of [[98,1],[195,-1],[235,-1],[259,-1],[289,1]]) {
  assert.equal(playbackDirection(time),direction);
  assert.deepEqual(worldAtFilmTime(time),worldAtFilmTime(time),
    "Un seek ou retour arrière change la pose sans événement objectif");
}
console.log("PASS: horloge objective monotone, famille à reculons, positions A/B identiques, collision unique, mousqueton, détour et pont.");
