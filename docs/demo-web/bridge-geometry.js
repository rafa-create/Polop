// Géométrie commune du pont, du creux et du détour — sans dépendance WebGL.
// Tous les pieds (et les planches) doivent appeler les mêmes fonctions.
export const BRIDGE_NEAR_Z = -10.3;
export const BRIDGE_FAR_Z = -14.7;
export const trailX = z => 8.7 + Math.sin(z * .115) * 2.0;
const lerp = (a,b,t) => a+(b-a)*t;
const clamp = (n,a,b)=>Math.max(a,Math.min(b,n));
export function baseHeight(x,z) {
  const peak = 19 * Math.exp(-((x - 18) ** 2 / 550 + (z + 24) ** 2 / 850));
  const shoulder = 10 * Math.exp(-((x - 32) ** 2 / 950 + (z - 5) ** 2 / 1600));
  const far = 4 * Math.exp(-((x + 27) ** 2 / 950 + (z + 37) ** 2 / 900));
  const relief = .45 * Math.sin(x * .23) * Math.cos(z * .18);
  return -1.65 + peak + shoulder + far + relief
    - 4.2 * Math.exp(-((x + 15) ** 2 / 35));
}
export function heightAt(x,z) {
  // Le creux est LOCALISÉ sous le pont. V4 le prolongeait sur 16 mètres
  // transversalement et faisait tomber même les marcheurs du détour.
  const across = Math.exp(-Math.pow((x - trailX(-12.5)) / 1.95, 4));
  const longitudinal = clamp(Math.abs((z + 12.5) / 2.2),0,1);
  const along = Math.pow(1 - longitudinal * longitudinal, 2);
  return baseHeight(x,z) - 5.5 * across * along;
}
export function bridgeDeckPoint(u) {
  const t=clamp(u,0,1);
  const x0=trailX(BRIDGE_NEAR_Z), x1=trailX(BRIDGE_FAR_Z);
  return {
    x:lerp(x0,x1,t),
    y:lerp(baseHeight(x0,BRIDGE_NEAR_Z)+.22,baseHeight(x1,BRIDGE_FAR_Z)+.22,t)-.35*Math.sin(Math.PI*t),
    z:lerp(BRIDGE_NEAR_Z,BRIDGE_FAR_Z,t)
  };
}
export function bridgeDeckAt(z) {
  const u=(z-BRIDGE_NEAR_Z)/(BRIDGE_FAR_Z-BRIDGE_NEAR_Z);
  return bridgeDeckPoint(u);
}
export function detourPoint(u) {
  // Même sentier, flanc à droite du creux, sans traverser le pont.
  const t=clamp(u,0,1);
  const z=lerp(BRIDGE_FAR_Z,-9.4,t);
  const x=trailX(z)+4.7*Math.sin(Math.PI*t);
  return {x,y:heightAt(x,z),z};
}
export function supportAt(x,z,surface="terrain") {
  // L'argument surface vient de la trajectoire choisie, pas d'un test de
  // proximité : le passage sur le pont ne doit pas attirer les piétons du flanc.
  if(surface==="bridge") {
    const deck=bridgeDeckAt(z);
    if(z>BRIDGE_NEAR_Z+1e-6 || z<BRIDGE_FAR_Z-1e-6 || Math.abs(x-deck.x)>.83)
      throw new RangeError("Personnage hors du tablier du pont");
    return deck.y+.065; // dessus des planches de 13 cm.
  }
  if(surface!=="terrain") throw new RangeError("Surface inconnue");
  return heightAt(x,z);
}
