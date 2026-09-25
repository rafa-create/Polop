// Source unique des positions/gestes de POLOP sur une horloge objective
// CONDENSÉE pour la préviz web (unités de lecture de la partie A, et non
// secondes réelles de 16 h 58 à 18 h). La partie B ne contient aucune
// trajectoire alternative pour la famille : elle échantillonne celle-ci à
// des instants objectifs décroissants.
import { trailX, heightAt, supportAt, bridgeDeckPoint, detourPoint,
  BRIDGE_NEAR_Z, BRIDGE_FAR_Z } from "./bridge-geometry.js";

export const CONTACT_CAVE = 179;   // 18 h 00 dans la version condensée
export const CONTACT_ROCK = 81;    // vers 17 h 00, scène A2 = B8
export const HOOK_CHANGE = 86;    // vers 17 h 01, un seul geste matériel
const clamp = (v,a,b)=>Math.max(a,Math.min(b,v));
const mix = (a,b,s)=>a+(b-a)*s;
const progress = (t,a,b)=>clamp((t-a)/(b-a),0,1);
const smooth = s=>s*s*(3-2*s);
const pos=(x,z,surface="terrain",walk=1,heading=0)=>({
  x,z,surface,y:supportAt(x,z,surface),walk,heading
});
const trail=(z,lateral=0,walk=1,heading=0)=>pos(trailX(z)+lateral,z,"terrain",walk,heading);
// Normal first ascent: the family stops on the NEAR bank as Léa alone crosses.
function approach(name,t) {
  const u=smooth(progress(t,36,57));
  const z=mix(10,-9.7,u);
  const offsets={Thomas:[-.42,1.2],"Éva":[.38,.65],"Léa":[0,-.6]};
  const [dx,dz]=offsets[name];
  return trail(z+dz,dx,t<36?0:1);
}
function nearBank(name) {
  if(name==="Thomas")return trail(-8.5,-.42,.1);
  if(name==="Éva")return trail(-9.05,.38,.15);
  return pos(bridgeDeckPoint(0).x,BRIDGE_NEAR_Z,"terrain",.3);
}
// Le détour est le MÊME segment physique dans les deux directions de lecture.
// Les décalages de départ évitent une téléportation des deux parents à 01:30.
function groupOnBypass(name,t) {
  const lag={Thomas:1.2,"Éva":.6,"Léa":0}[name];
  const u=smooth(progress(t,90+lag,99));
  const destination=detourPoint(1-u);
  const start=name==="Léa"?detourPoint(1):nearBank(name);
  const lateral={Thomas:-.42,"Éva":.38,"Léa":0}[name];
  // Join the *drawn* bypass immediately, rather than cutting across the
  // ravine through a straight interpolation between the bank and the flank.
  const join=smooth(clamp(u/.22,0,1));
  const x=destination.x+lateral+(start.x-(trailX(-9.4)+lateral))*(1-join);
  const z=destination.z+(start.z+9.4)*(1-join);
  return pos(x,z,"terrain",u>.01&&u<.99?1:.3);
}
function groupAboveBypass(name,t) {
  const u=smooth(progress(t,99,106));
  const offsets={Thomas:[-.42,1],"Éva":[.38,-.15],"Léa":[0,.42]};
  const [dx,dz]=offsets[name];
  const z=mix(BRIDGE_FAR_Z,-26,u)+dz*u;
  return trail(z,dx,1);
}
function womenAtPlatform(name,t) {
  const isEva=name==="Éva", u=progress(t,121,139);
  const z0=isEva?-26.15:-25.58;
  const x0=trailX(z0)+(isEva ? .38 : 0);
  // Attente, courte recherche puis départ. Pas de mouvement fictif lors
  // d'une pause ; la marche à rebours sera visible pendant leur descente.
  const search=Math.sin(Math.PI*u);
  return pos(x0+(.65*search)*(isEva?1:-1),
    z0-.55*search,"terrain",.25,Math.PI*smooth(progress(t,132,147)));
}
function womenDescending(name,t) {
  const u=smooth(progress(t,139,179));
  const isEva=name==="Éva";
  const z=mix(isEva?-26.15:-25.58,isEva?-16.4:-15.7,u);
  return trail(z,isEva ? .38 : 0,u<.98?.85:.12,Math.PI*smooth(progress(t,132,147)));
}
function normalThomas(t) {
  if(t<106)return normalPerson("Thomas",t);
  if(t<115)return trail(-25,-.42,.12);
  if(t<136) {
    const u=smooth(progress(t,115,136));
    return pos(mix(trailX(-25)-.42,trailX(-28)+1.6,u),
      mix(-25,-28,u),"terrain",u<.99?.65:.1);
  }
  if(t<166) {
    const u=smooth(progress(t,136,166));
    return pos(mix(trailX(-28)+1.6,17.8,u),mix(-28,-27.2,u),
      "terrain",u>.01&&u<.99?.65:.1);
  }
  return pos(17.8,-27.2,"terrain",0);
}
export function normalPerson(name,objective) {
  const t=clamp(objective,0,CONTACT_CAVE);
  if(!["Thomas","Éva","Léa"].includes(name))throw new RangeError("Personnage inconnu");
  if(name==="Thomas"&&t>=106)return normalThomas(t);
  if(t<57)return approach(name,t);
  if(t<72) {
    if(name==="Léa"){
      const p=bridgeDeckPoint(smooth(progress(t,57,72)));
      return pos(p.x,p.z,"bridge",1);
    }
    return nearBank(name);
  }
  if(t<90) {
    if(name==="Léa"){
      const u=smooth(progress(t,72,90)),p=detourPoint(u);
      // Marche vers le point d'arrivée du flanc ; lue à rebours en B6.
      return pos(p.x,p.z,"terrain",1,Math.PI);
    }
    return nearBank(name);
  }
  if(t<99)return groupOnBypass(name,t);
  if(t<106)return groupAboveBypass(name,t);
  if(name==="Thomas")return normalThomas(t);
  if(t<121)return trail(name==="Éva"?-26.15:-25.58,name==="Éva"?.38:0,.13);
  if(t<139)return womenAtPlatform(name,t);
  return womenDescending(name,t);
}

// L'horloge du film peut changer de sens mais la position du monde ne dépend
// QUE de objective : A et B sont deux lectures des mêmes événements.
export const CLOCK = Object.freeze([
  {film:0,objective:0},{film:CONTACT_CAVE,objective:CONTACT_CAVE},
  {film:195,objective:160},{film:210,objective:143},
  {film:225,objective:127},{film:245,objective:108},
  {film:259,objective:98},{film:272,objective:87},
  {film:276,objective:86},{film:278,objective:85},
  {film:282,objective:84},{film:288,objective:CONTACT_ROCK},
  {film:295,objective:90},{film:300,objective:99}
]);
export function objectiveAt(filmTime) {
  const t=clamp(Number.isFinite(filmTime)?filmTime:0,0,300);
  for(let i=0;i<CLOCK.length-1;i++) {
    const a=CLOCK[i],b=CLOCK[i+1];
    if(t<=b.film)return mix(a.objective,b.objective,progress(t,a.film,b.film));
  }
  return CLOCK.at(-1).objective;
}
export function playbackDirection(filmTime) {
  return filmTime>=CONTACT_CAVE&&filmTime<288?-1:1;
}
// Même occurrence inversée pendant le premier visionnage et le second,
// indexée sur l'instant OBJECTIF, pas sur le temps de caméra.
const INVERSE_ROUTE = Object.freeze([
  {t:81,x:trailX(-8.5)-.42,z:-8.5},
  {t:82,x:trailX(-9.3),z:-9.3},
  {t:84,x:bridgeDeckPoint(0).x,z:BRIDGE_NEAR_Z,surface:"bridge"},
  {t:85,x:bridgeDeckPoint(1).x,z:BRIDGE_FAR_Z,surface:"bridge"},
  {t:86,x:bridgeDeckPoint(1).x,z:BRIDGE_FAR_Z},
  {t:87,x:trailX(-15.3),z:-15.3},
  {t:98,x:19,z:-12},{t:108,x:27,z:-8},
  {t:127,x:39,z:-4},{t:143,x:42,z:-16},
  {t:160,x:32,z:-26},{t:179,x:17.8,z:-27.2}
]);
export function inversePerson(objective) {
  const t=clamp(objective,CONTACT_ROCK,CONTACT_CAVE);
  for(let i=0;i<INVERSE_ROUTE.length-1;i++) {
    const a=INVERSE_ROUTE[i],b=INVERSE_ROUTE[i+1];
    if(t<=b.t) {
      const u=progress(t,a.t,b.t),x=mix(a.x,b.x,u),z=mix(a.z,b.z,u);
      const bridge=(t>=84&&t<=85);
      const snap=bridge?bridgeDeckPoint(progress(t,84,85)):null;
      // In objective time the inverted Thomas walks away from the collision.
      // On screen, while objective decreases, he follows this route backwards.
      const dx=b.x-a.x,dz=b.z-a.z, heading=Math.atan2(dx,dz);
      return pos(snap?.x??x,snap?.z??z,bridge?"bridge":"terrain",
        Math.abs(dx)+Math.abs(dz)>.02?1:.1,heading);
    }
  }
  const last=INVERSE_ROUTE.at(-1);
  return pos(last.x,last.z,"terrain",0);
}
export function worldAt(objective) {
  const t=clamp(objective,0,CONTACT_CAVE);
  return {
    objective:t,
    Thomas:normalPerson("Thomas",t),
    Eva:normalPerson("Éva",t),
    Lea:normalPerson("Léa",t),
    reverseThomas:t>=CONTACT_ROCK?inversePerson(t):null,
    hookAttached:t<HOOK_CHANGE
  };
}
export function worldAtFilmTime(time) {
  return worldAt(objectiveAt(time));
}
