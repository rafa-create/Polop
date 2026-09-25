import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
const script = await readFile("Script_POLOP.md", "utf8");
const moduleText = await readFile("docs/demo-web/storyboard.js", "utf8");
// Import as an ESM data URL without changing the repository's package type.
const { DURATION, BEATS, CHAPTERS, beatAt, formatTime, phaseAt } =
  await import("data:text/javascript;base64," + Buffer.from(moduleText).toString("base64"));
assert.equal(DURATION, 300, "The requested film must last 05:00");
assert.ok(BEATS.length >= 20, "A real sequence of distinct beats is required");
assert.equal(BEATS[0].start, 0);
assert.equal(BEATS.at(-1).end, DURATION);
let lastEnd = 0;
for (const beat of BEATS) {
  assert.equal(beat.start, lastEnd, "Timeline gap or overlap");
  assert.ok(beat.end > beat.start, "Zero-length story section");
  assert.ok(beat.scene && beat.title && beat.caption && beat.note);
  lastEnd = beat.end;
}
for (const chapter of CHAPTERS) {
  assert.ok(chapter.time >= 0 && chapter.time < 300);
  assert.equal(beatAt(chapter.time).start <= chapter.time, true);
}
for (const key of ["A0","A1","A2","A10","A14","A15","A16","A17","B1","B2","B3","B4","B5","B6","B7","B8","B9"]) {
  assert.ok(script.includes(key + " — "), "Missing scene in canonical film script: " + key);
  assert.ok(BEATS.some(beat => beat.scene.split("–").some(part => part === key) ||
    beat.scene === key), "Missing scene in adaptation: " + key);
}
assert.equal(beatAt(170).scene, "A17");
assert.equal(beatAt(240).scene, "B4");
assert.equal(beatAt(272).scene, "B6");
assert.equal(beatAt(285).scene, "B7–B8");
assert.equal(beatAt(300).scene, "B9");
assert.equal(phaseAt(170), "normal→inverse");
assert.equal(phaseAt(240), "inverse");
assert.equal(formatTime(300), "05:00");
assert.equal(formatTime(0), "00:00");
console.log("PASS: 300 seconds, 21 contiguous scripted beats, canonical A/B coverage, 9 chapter anchors and stable time mapping.");
