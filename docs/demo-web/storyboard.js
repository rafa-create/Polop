// POLOP — adaptation condensée de cinq minutes du film-manuscrit.
// Les horaires A/B sont des repères narratifs ; les secondes sont le temps de lecture.
export const DURATION = 300;
export const BEATS = Object.freeze([
  { start: 0,   end: 18,  scene: "A0", act: "normal", title: "La rivière · 16 h 58", caption: "Sous l’eau, un anneau repose entre deux pierres.", note: "L’anneau bouge à peine. La caméra continue." },
  { start: 18,  end: 36,  scene: "A0", act: "normal", title: "La vallée", caption: "La caméra sort de l’eau et rejoint la montagne.", note: "Un seul mouvement, sans coupe." },
  { start: 36,  end: 57,  scene: "A1", act: "normal", title: "La randonnée", caption: "Thomas, Éva et Léa avancent sur le sentier.", note: "THOMAS — Après cette montée, il reste juste toutes les autres." },
  { start: 57,  end: 72,  scene: "A1", act: "normal", title: "Le pont", caption: "Léa emprunte le petit pont. Le mousqueton est accroché.", note: "ÉVA — Doucement." },
  { start: 72,  end: 90,  scene: "A2", act: "normal", title: "Le détour", caption: "Léa reprend le flanc ; Thomas est heurté près d’un rocher.", note: "THOMAS — Non, non. Continue. Prends le flanc, cette fois-ci." },
  { start: 90,  end: 106, scene: "A3–A9", act: "normal", title: "La montée · vers 17 h 30", caption: "La famille reprend la montée. Le pont apparaît en contrebas.", note: "ÉVA — C’est pas grave si tu mets pas la montée sur Strava." },
  { start: 106, end: 121, scene: "A10", act: "normal", title: "La pause · 17 h 55", caption: "Thomas s’écarte derrière la roche. Éva et Léa attendent.", note: "THOMAS — Je vais faire une pause pipi." },
  { start: 121, end: 136, scene: "A11–A14", act: "normal", title: "L’absence · 17 h 56", caption: "Éva et Léa cherchent Thomas, puis redescendent chercher de l’aide.", note: "LÉA — Tu crois qu’il est tombé ?" },
  { start: 136, end: 151, scene: "A15", act: "normal", title: "La cavité · 17 h 58", caption: "Après leur départ, la caméra révèle la petite entrée de la caverne.", note: "Thomas n’a pas entendu les appels." },
  { start: 151, end: 166, scene: "A16", act: "normal", title: "L’anneau · 17 h 59", caption: "Dans la fissure, l’anneau remonte de pierre en pierre.", note: "Un frottement métallique. Thomas tend la main." },
  { start: 166, end: 179, scene: "A17", act: "turn", title: "Le contact · 18 h 00", caption: "Les doigts de Thomas touchent l’anneau. Le monde s’inverse.", note: "CONTACT. Aucun flash : l’eau et la poussière remontent." },
  { start: 179, end: 195, scene: "B1", act: "inverse", title: "La seconde lumière", caption: "Thomas découvre un passage latéral dans la caverne.", note: "Une silhouette se retire à reculons vers la petite entrée." },
  { start: 195, end: 210, scene: "B1", act: "inverse", title: "L’autre versant", caption: "Thomas sort sur le versant opposé et cherche sa famille.", note: "Les gouttes remontent vers la roche." },
  { start: 210, end: 225, scene: "B2–B3", act: "inverse", title: "Deux occurrences", caption: "Au loin, Éva et Léa marchent à reculons. Thomas voit sa propre randonnée.", note: "Une pierre remonte jusqu’au pied qui l’avait délogée." },
  { start: 225, end: 245, scene: "B4", act: "inverse", title: "Le temps à rebours", caption: "Feuilles, eau et gravier regagnent leur place autour de Thomas.", note: "Il reprend sa course et s’émerveille du paysage inversé." },
  { start: 245, end: 259, scene: "B4", act: "inverse", title: "La descente", caption: "L’anneau poursuit son trajet dans la roche, sans Thomas.", note: "Le paysage continue de se remettre en place." },
  { start: 259, end: 272, scene: "B5", act: "inverse", title: "Le pont · vers 17 h 30", caption: "Thomas retrouve le pont. Le mousqueton est décroché.", note: "Il regarde sa montre. Son sourire disparaît." },
  { start: 272, end: 282, scene: "B6", act: "inverse", title: "Le geste · vers 17 h 01", caption: "Thomas raccroche le mousqueton avant que Léa revienne vers le pont.", note: "CLAC. Il traverse et rejoint l’autre rive." },
  { start: 282, end: 288, scene: "B7–B8", act: "inverse", title: "La convergence · 17 h 00", caption: "Les deux Thomas se heurtent au moment où l’anneau revient.", note: "Les deux contacts sont simultanés." },
  { start: 288, end: 295, scene: "B9", act: "normal", title: "Le retour", caption: "Le même instant retrouvé : Thomas reprend la marche vers Éva et Léa.", note: "THOMAS — Continue. Prends le flanc, cette fois-ci." },
  { start: 295, end: 300, scene: "B9", act: "normal", title: "La boucle", caption: "La caméra s’éloigne. Le sentier et les deux versants apparaissent ensemble.", note: "La famille continue de marcher. Noir." }
]);
export const CHAPTERS = Object.freeze([
  { time: 0, label: "00:00 · La rivière" },
  { time: 36, label: "00:36 · La randonnée" },
  { time: 106, label: "01:46 · La disparition" },
  { time: 136, label: "02:16 · La caverne" },
  { time: 166, label: "02:46 · Le retournement" },
  { time: 195, label: "03:15 · Le versant inversé" },
  { time: 259, label: "04:19 · Le pont" },
  { time: 282, label: "04:42 · La convergence" },
  { time: 295, label: "04:55 · Le dézoom" }
]);
export function beatAt(time) {
  const t = Math.min(DURATION, Math.max(0, Number.isFinite(time) ? time : 0));
  return BEATS.find(beat => t >= beat.start && t < beat.end) ?? BEATS[BEATS.length - 1];
}
export function phaseAt(time) {
  const b = beatAt(time);
  return b.act === "turn" ? "normal→inverse" : b.act;
}
export function formatTime(seconds) {
  const s = Math.max(0, Math.min(DURATION, Math.floor(seconds)));
  return String(Math.floor(s / 60)).padStart(2, "0") + ":" + String(s % 60).padStart(2, "0");
}
