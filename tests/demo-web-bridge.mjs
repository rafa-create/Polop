// Physical grounding regression: the terrain, bypass and bridge MUST use
// one shared source of truth, independent of the renderer and seek direction.
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const src=await readFile("docs/demo-web/bridge-geometry.js","utf8");
const {
  BRIDGE_NEAR_Z, BRIDGE_FAR_Z, trailX, baseHeight, heightAt,
  bridgeDeckPoint, bridgeDeckAt, detourPoint, supportAt
}=await import("data:text/javascript;base64,"+Buffer.from(src).toString("base64"));
const close=(a,b,tolerance=.000001)=>assert.ok(Math.abs(a-b)<tolerance,
  "Mismatched physical support: "+a+" vs "+b);
close(BRIDGE_NEAR_Z,-10.3); close(BRIDGE_FAR_Z,-14.7);
let deepest=0, detourMax=0;
for(let i=0;i<=200;i++){
  const u=i/200, deck=bridgeDeckPoint(u);
  const height=heightAt(deck.x,deck.z), gap=supportAt(deck.x,deck.z,"bridge")-height;
  assert.ok(gap>.20,"Bridge deck intersects ground at u="+u+" gap="+gap);
  close(deck.y,bridgeDeckAt(deck.z).y);
  close(supportAt(deck.x,deck.z,"bridge"),deck.y+.065);
  deepest=Math.max(deepest,baseHeight(deck.x,deck.z)-height);
  const flank=detourPoint(u);
  close(flank.y,heightAt(flank.x,flank.z));
  detourMax=Math.max(detourMax,baseHeight(flank.x,flank.z)-flank.y);
}
assert.ok(deepest>4,"The gorge must remain visible under the bridge");
assert.ok(detourMax<1.2,"The bypass must stay on the safe hillside, not the ravine floor");
assert.throws(()=>supportAt(trailX(-12.5)+4,-12.5,"bridge"),RangeError,
  "Never snap walkers from the flank onto the bridge");
assert.throws(()=>supportAt(trailX(-9),-9,"bridge"),RangeError,
  "Never place a person off the bridge deck");
console.log("PASS: 201 bridge support samples, 201 stable bypass samples, gorge clearance and off-deck rejection.");
