// Browser-level smoke tests for the real Three.js scene (not a graphics mock).
// Run in GitHub Actions with Playwright Chromium and WebGL/SwiftShader enabled.
import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { resolve, sep, extname } from "node:path";
import { chromium } from "playwright";

const root = resolve("docs");
const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".glb": "model/gltf-binary"
};
const server = createServer(async (request, response) => {
  try {
    const pathname = decodeURIComponent(new URL(request.url, "http://localhost").pathname);
    const file = resolve(root, "." + pathname, pathname.endsWith("/") ? "index.html" : "");
    if (!file.startsWith(root + sep)) throw new Error("Path outside docs");
    const bytes = await readFile(file);
    response.writeHead(200, { "Content-Type": contentTypes[extname(file)] || "application/octet-stream" });
    response.end(bytes);
  } catch {
    response.writeHead(404);
    response.end("Not found");
  }
});
const listen = () => new Promise(resolveReady => server.listen(0, "127.0.0.1", resolveReady));
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const seek = async (page, second) => {
  await page.locator("#timeline").evaluate((element, t) => {
    element.value = String(t);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  }, second);
  await page.waitForFunction(t => {
    const mm = String(Math.floor(t / 60)).padStart(2, "0");
    const ss = String(Math.floor(t % 60)).padStart(2, "0");
    return document.getElementById("timecode").textContent.startsWith(mm + ":" + ss);
  }, second);
  await page.waitForTimeout(180);
};
let browser;
try {
  await listen();
  const address = server.address();
  const baseUrl = "http://127.0.0.1:" + address.port + "/demo-web/";
  browser = await chromium.launch({
    headless: true,
    args: ["--enable-webgl", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const errors = [];
  page.on("pageerror", error => errors.push(String(error)));
  await page.goto(baseUrl, { waitUntil: "load" });
  await page.waitForFunction(() => document.getElementById("loading").hidden, null,
    { timeout: 45000 });
  assert.equal(await page.locator("#scene-error").isHidden(), true, "WebGL start failed");
  assert.equal(await page.locator("#scene canvas").count(), 1, "Missing 3D canvas");
  assert.equal(await page.locator("#timeline").getAttribute("max"), "300");
  assert.equal(await page.locator("#chapters option").count(), 9);
  assert.equal(await page.locator("#film-subtitle").count(), 1);
  assert.equal(await page.locator("#play-pause").count(), 1);
  assert.equal(await page.locator("#replay").count(), 1);
  assert.equal(await page.locator("#camera-mode").count(), 1);
  assert.equal(await page.locator("#fullscreen").count(), 1);
  assert.equal(await page.locator("#sound").count(), 1);
  assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "false");
  const canvas = page.locator("#scene canvas");
  const viewport = await canvas.boundingBox();
  assert.ok(viewport?.width > 100 && viewport?.height > 100, "Invisible 3D canvas");
  const gl = await canvas.evaluate(el => Boolean(el.getContext("webgl2") || el.getContext("webgl")));
  assert.ok(gl, "WebGL context unavailable");
  if (await page.locator("#play-pause").getAttribute("aria-pressed") !== "true")
    await page.locator("#play-pause").click();
  await seek(page, 0);
  const frameA = sha(await canvas.screenshot());
  await seek(page, 170);
  assert.equal(await page.locator("#scene").getAttribute("data-scene"), "A17");
  const frameB = sha(await canvas.screenshot());
  assert.notEqual(frameA, frameB, "Scrubbing did not change the rendered 3D frame");
  await seek(page, 240);
  assert.equal(await page.locator("#scene").getAttribute("data-scene"), "B4");
  assert.equal(await page.locator("#scene").getAttribute("data-second-thomas"), "true");
  const inverseFrame = sha(await canvas.screenshot());
  assert.notEqual(inverseFrame, frameB, "The inverted world must render a distinct 3D frame");
  await seek(page, 4);
  const frameC = sha(await canvas.screenshot());
  assert.notEqual(frameC, frameB, "Backwards scrubbing did not change the frame");
  await page.locator("#chapters").selectOption("259");
  await page.waitForFunction(() => document.getElementById("timecode").textContent.startsWith("04:19"));
  assert.equal(await page.locator("#scene").getAttribute("data-scene"), "B5");
  // User-reported regression: people were placed at the bottom of the ravine
  // instead of standing on the bridge deck and the visible bypass path.
  for (const seconds of [59, 64, 68, 71]) {
    await seek(page, seconds);
    assert.equal(await page.locator("#scene").getAttribute("data-lea-surface"), "bridge",
      "Léa must be grounded on bridge planks at " + seconds + " s");
    const gap = Number(await page.locator("#scene").getAttribute("data-lea-foot-gap"));
    assert.ok(gap >= .035 && gap <= .08, "Léa's feet float or sink at " + seconds + " s: " + gap);
  }
  for (const seconds of [75, 80, 85]) {
    await seek(page, seconds);
    assert.equal(await page.locator("#scene").getAttribute("data-lea-surface"), "terrain",
      "The return path must be on the flank, not the bridge");
  }
  for (const seconds of [279, 280, 281]) {
    await seek(page, seconds);
    assert.equal(await page.locator("#scene").getAttribute("data-thomas-inverse-surface"), "bridge",
      "Inverted Thomas must cross the actual bridge deck");
    const gap = Number(await page.locator("#scene").getAttribute("data-thomas-inverse-foot-gap"));
    assert.ok(gap >= .035 && gap <= .08,
      "Inverted Thomas floats or sinks on the bridge: " + gap);
  }
  await seek(page, 276);
  assert.equal(await page.locator("#scene").getAttribute("data-hook-attached"), "false",
    "At objective 17 h 01 the hook is detached until Thomas reconnects it");
  await seek(page, 279);
  assert.equal(await page.locator("#scene").getAttribute("data-hook-attached"), "true",
    "The hook must be attached before inverted Thomas crosses");
  // Same objective instant => SAME positions, orientations and walking
  // phases, including the two Thomas occurrences, whichever way we seek.
  const evaAt195 = {}, evaAt210 = {};
  for (const [normalTime, inverseTime] of
    [[160,195],[143,210],[108,245],[98,259],[87,272],[85,278],[84,282],[81,288]]) {
    await seek(page, normalTime);
    const forward = JSON.parse(await page.locator("#scene").getAttribute("data-family-poses"));
    await seek(page, inverseTime);
    const backward = JSON.parse(await page.locator("#scene").getAttribute("data-family-poses"));
    assert.equal(await page.locator("#scene").getAttribute("data-objective"),
      normalTime.toFixed(5), "Wrong shared objective time at "+inverseTime);
    assert.deepEqual(backward, forward,
      "Objective family poses differ between A and B at "+normalTime);
    if (inverseTime === 195) evaAt195.value = backward[1];
    if (inverseTime === 210) evaAt210.value = backward[1];
  }
  assert.ok(evaAt210.value.z < evaAt195.value.z - 3.5,
    "Éva must move visibly uphill BACKWARDS in the inverted world");
  assert.ok(evaAt195.value.yaw > 3 && evaAt210.value.yaw > 3,
    "Éva must keep her forward-time orientation when her movements reverse");
  await seek(page, 272);
  assert.equal(await page.locator("#scene").getAttribute("data-scene"), "B6");
  await seek(page, 285);
  assert.equal(await page.locator("#scene").getAttribute("data-second-thomas"), "true", "Two 3D Thomas occurrences missing at convergence");
  await seek(page, 299.9);
  assert.equal(await page.locator("#scene").getAttribute("data-scene"), "B9");
  await seek(page, 300);
  assert.equal(await page.locator("#timecode").textContent(), "05:00 / 05:00");
  assert.ok(await page.locator("#final-curtain").evaluate(el => Number(el.style.opacity)) > .99, "Missing final fade to black");
  await seek(page, 4);
  await page.locator("#sound").click();
  await page.waitForFunction(() => document.getElementById("sound").getAttribute("aria-pressed") === "true", null, { timeout: 10000 });
  await page.locator("#sound").click();
  assert.equal(await page.locator("#sound").getAttribute("aria-pressed"), "false");
  await page.locator("#camera-mode").click();
  assert.equal(await page.locator("#camera-mode").getAttribute("aria-pressed"), "true");
  const box = await canvas.boundingBox();
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(box.x + box.width / 2 + 100, box.y + box.height / 2 + 24, { steps: 5 });
  await page.mouse.up();
  const rotated = sha(await canvas.screenshot());
  assert.notEqual(rotated, frameC, "Free camera drag had no visual effect");
  await page.locator("#camera-mode").click();
  assert.equal(await page.locator("#camera-mode").getAttribute("aria-pressed"), "false");
  await page.locator("#fullscreen").click();
  const fullscreenState = await page.evaluate(() => ({
    supported: Boolean(document.fullscreenEnabled),
    active: Boolean(document.fullscreenElement),
    fallback: document.getElementById("hint").textContent.includes("indisponible")
  }));
  assert.ok(fullscreenState.active || fullscreenState.fallback,
    "Fullscreen control did not activate or report unavailability");
  if (fullscreenState.active) await page.evaluate(() => document.exitFullscreen());
  await page.locator("#replay").click();
  assert.ok(Number(await page.locator("#timeline").inputValue()) < 1, "Replay did not reset time");
  assert.deepEqual(errors, [], "Uncaught desktop browser errors");

  const mobile = await browser.newPage({
    viewport: { width: 390, height: 844 },
    isMobile: true, hasTouch: true, deviceScaleFactor: 1
  });
  const mobileErrors = [];
  mobile.on("pageerror", error => mobileErrors.push(String(error)));
  await mobile.goto(baseUrl, { waitUntil: "load" });
  await mobile.waitForFunction(() => document.getElementById("loading").hidden, null,
    { timeout: 45000 });
  assert.equal(await mobile.locator("#scene-error").isHidden(), true, "Mobile WebGL start failed");
  assert.ok((await mobile.locator("#scene canvas").boundingBox())?.width > 100);
  await mobile.locator("#camera-mode").tap();
  assert.equal(await mobile.locator("#camera-mode").getAttribute("aria-pressed"), "true");
  await seek(mobile, 211);
  assert.equal(await mobile.locator("#scene").getAttribute("data-scene"), "B2–B3");
  assert.deepEqual(mobileErrors, [], "Uncaught mobile browser errors");
  await mobile.close();
  await page.close();
  console.log("PASS: Chromium WebGL launch, 300s story, normal/inverted 3D frames, two Thomas occurrences, chapters, scrubbing, replay, free camera, optional Web Audio, fullscreen, mobile touch.");
} finally {
  await browser?.close();
  await new Promise(resolveClosed => server.close(resolveClosed));
}
