// Génère les visuels de référence de Bip & Mocha :
//  - les expressions de l'écran de Bip (textures SVG + PNG 640x480, à charger dans Blender)
//  - les planches de proportions de Bip et de Mocha (images de référence pour la modélisation)
//  - la planche d'échelle et la palette
//
// Utilisation (depuis la racine du dépôt) :  node tools/generer-design.js
// Pour modifier une couleur : changer la constante PALETTE ci-dessous et relancer.

const fs = require('fs');
const path = require('path');
const { chromium } = require('playwright');

const OUT = path.join(__dirname, '..', 'assets', 'design');
const OUT_ECRAN = path.join(OUT, 'bip-ecran');

const PALETTE = {
  // Bip
  bipCorps: '#F2EDE4',
  bipOmbre: '#D9D1C3',
  bipAccent: '#F28C38',
  bipEcranFond: '#10151F',
  bipEcranCadre: '#2A2F3A',
  // Émotions de l'écran
  cyan: '#4FD1FF', // neutre / joie
  bleu: '#5B7CFA', // tristesse
  rouge: '#FF4D4D', // colère / erreur / batterie
  jaune: '#FFD23F', // idée / exclamation / panique
  rose: '#FF6FAE', // amour
  veille: '#3A5A70', // veille
  // Mocha
  mochaPelage: '#C49A6C',
  mochaFonce: '#7A4E2D',
  mochaCreme: '#F3E3CC',
  mochaYeux: '#E8A33D',
  mochaNez: '#B86F6F',
  // Décor / fonds
  fond: '#FBF7F1',
  trait: '#3B2F28',
  grille: '#E6DED2',
};

const P = PALETTE;

// ---------------------------------------------------------------------------
// 1. Expressions de l'écran de Bip (640 x 480, ratio 4:3)
// ---------------------------------------------------------------------------
const W = 640, H = 480;
const EL = 220, ER = 420, EY = 230; // centres des yeux

const eye = (cx, cy, c, w = 64, h = 120) =>
  `<rect x="${cx - w / 2}" y="${cy - h / 2}" width="${w}" height="${h}" rx="${w / 2}" fill="${c}"/>`;
const arcHaut = (cx, cy, c, s = 30) =>
  `<path d="M${cx - 48} ${cy + 22} Q${cx} ${cy - 62} ${cx + 48} ${cy + 22}" fill="none" stroke="${c}" stroke-width="${s}" stroke-linecap="round"/>`;
const ligne = (x1, y1, x2, y2, c, s = 26) =>
  `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" stroke="${c}" stroke-width="${s}" stroke-linecap="round"/>`;
const coeur = (cx, cy, c, k = 1) =>
  `<path transform="translate(${cx} ${cy}) scale(${k})" d="M0 38 C-70 -8 -52 -70 0 -36 C52 -70 70 -8 0 38 Z" fill="${c}"/>`;
const spirale = (cx, cy, c) => {
  let d = '';
  for (let i = 0; i <= 720; i += 15) {
    const a = (i * Math.PI) / 180, r = 4 + i / 15;
    d += `${i ? 'L' : 'M'}${(cx + r * Math.cos(a)).toFixed(1)} ${(cy + r * Math.sin(a)).toFixed(1)} `;
  }
  return `<path d="${d}" fill="none" stroke="${c}" stroke-width="14" stroke-linecap="round"/>`;
};
const larme = (cx, cy, c) =>
  `<path d="M${cx} ${cy} C${cx - 18} ${cy + 26} ${cx - 16} ${cy + 46} ${cx} ${cy + 48} C${cx + 16} ${cy + 46} ${cx + 18} ${cy + 26} ${cx} ${cy} Z" fill="${c}"/>`;

const EXPRESSIONS = [
  { id: 'neutre', nom: 'Neutre', usage: 'État par défaut', svg: () => eye(EL, EY, P.cyan) + eye(ER, EY, P.cyan) },
  { id: 'joie', nom: 'Joie', usage: 'Content, fier', svg: () => arcHaut(EL, EY, P.cyan) + arcHaut(ER, EY, P.cyan) },
  {
    id: 'tres-joyeux', nom: 'Très joyeux', usage: 'Euphorie, réussite',
    svg: () => arcHaut(EL, EY - 20, P.cyan) + arcHaut(ER, EY - 20, P.cyan) +
      `<path d="M260 300 Q320 300 380 300 Q370 380 320 380 Q270 380 260 300 Z" fill="${P.cyan}"/>`,
  },
  {
    id: 'triste', nom: 'Triste', usage: 'Déçu, échec',
    svg: () => eye(EL, EY + 20, P.bleu, 60, 80) + eye(ER, EY + 20, P.bleu, 60, 80) +
      ligne(EL - 45, EY - 50, EL + 35, EY - 75, P.bleu, 18) + ligne(ER + 45, EY - 50, ER - 35, EY - 75, P.bleu, 18),
  },
  {
    id: 'pleure', nom: 'Pleure', usage: 'Gros chagrin, émotion',
    svg: () => eye(EL, EY + 10, P.bleu, 60, 70) + eye(ER, EY + 10, P.bleu, 60, 70) +
      ligne(EL - 45, EY - 55, EL + 35, EY - 80, P.bleu, 18) + ligne(ER + 45, EY - 55, ER - 35, EY - 80, P.bleu, 18) +
      larme(EL, EY + 60, P.bleu) + larme(ER, EY + 60, P.bleu),
  },
  {
    id: 'colere', nom: 'Colère', usage: 'Fâché, vexé',
    svg: () =>
      `<path d="M${EL - 40} ${EY - 40} L${EL + 40} ${EY - 10} L${EL + 40} ${EY + 50} Q${EL} ${EY + 70} ${EL - 40} ${EY + 50} Z" fill="${P.rouge}"/>` +
      `<path d="M${ER + 40} ${EY - 40} L${ER - 40} ${EY - 10} L${ER - 40} ${EY + 50} Q${ER} ${EY + 70} ${ER + 40} ${EY + 50} Z" fill="${P.rouge}"/>`,
  },
  {
    id: 'surprise', nom: 'Surprise', usage: 'Étonné, choc',
    svg: () =>
      `<circle cx="${EL}" cy="${EY - 10}" r="56" fill="none" stroke="${P.cyan}" stroke-width="22"/>` +
      `<circle cx="${ER}" cy="${EY - 10}" r="56" fill="none" stroke="${P.cyan}" stroke-width="22"/>` +
      `<circle cx="${EL}" cy="${EY - 10}" r="18" fill="${P.cyan}"/><circle cx="${ER}" cy="${EY - 10}" r="18" fill="${P.cyan}"/>` +
      `<ellipse cx="320" cy="360" rx="26" ry="32" fill="${P.cyan}"/>`,
  },
  {
    id: 'question', nom: 'Question', usage: 'Ne comprend pas',
    svg: () => eye(EL - 30, EY + 10, P.cyan, 56, 100) +
      `<path d="M370 170 Q370 110 430 110 Q490 110 490 165 Q490 205 440 225 Q430 230 430 260" fill="none" stroke="${P.cyan}" stroke-width="30" stroke-linecap="round"/>` +
      `<circle cx="430" cy="320" r="20" fill="${P.cyan}"/>`,
  },
  {
    id: 'exclamation', nom: 'Exclamation', usage: 'Alerte, découverte',
    svg: () => `<rect x="296" y="90" width="48" height="200" rx="24" fill="${P.jaune}"/><circle cx="320" cy="360" r="30" fill="${P.jaune}"/>`,
  },
  {
    id: 'idee', nom: 'Idée', usage: 'Eurêka',
    svg: () =>
      `<circle cx="320" cy="200" r="95" fill="${P.jaune}"/>` +
      `<rect x="275" y="270" width="90" height="70" rx="10" fill="${P.jaune}"/>` +
      `<rect x="285" y="350" width="70" height="18" rx="9" fill="${P.jaune}"/>` +
      `<rect x="295" y="376" width="50" height="18" rx="9" fill="${P.jaune}"/>` +
      ligne(320, 60, 320, 30, P.jaune, 16) + ligne(185, 120, 160, 100, P.jaune, 16) + ligne(455, 120, 480, 100, P.jaune, 16) +
      ligne(165, 210, 135, 210, P.jaune, 16) + ligne(475, 210, 505, 210, P.jaune, 16),
  },
  { id: 'amour', nom: 'Amour', usage: 'Tendresse (pour Mocha)', svg: () => coeur(EL, EY, P.rose, 1.25) + coeur(ER, EY, P.rose, 1.25) },
  { id: 'panique', nom: 'Panique', usage: 'Catastrophe en cours', svg: () => spirale(EL, EY, P.jaune) + spirale(ER, EY, P.jaune) },
  {
    id: 'veille', nom: 'Veille', usage: 'Dort, économie d\'énergie',
    svg: () => ligne(EL - 40, EY + 20, EL + 40, EY + 20, P.veille, 18) + ligne(ER - 40, EY + 20, ER + 40, EY + 20, P.veille, 18) +
      `<path d="M500 90 A45 45 0 1 0 545 150 A35 35 0 1 1 500 90 Z" fill="${P.veille}"/>`,
  },
  {
    id: 'batterie-faible', nom: 'Batterie faible', usage: 'Doit se recharger',
    svg: () =>
      `<rect x="180" y="160" width="250" height="140" rx="22" fill="none" stroke="${P.rouge}" stroke-width="22"/>` +
      `<rect x="440" y="200" width="28" height="60" rx="8" fill="${P.rouge}"/>` +
      `<rect x="205" y="185" width="45" height="90" rx="8" fill="${P.rouge}"/>`,
  },
  {
    id: 'erreur', nom: 'Erreur', usage: 'Assommé, bug',
    svg: () => ligne(EL - 45, EY - 45, EL + 45, EY + 45, P.rouge) + ligne(EL + 45, EY - 45, EL - 45, EY + 45, P.rouge) +
      ligne(ER - 45, EY - 45, ER + 45, EY + 45, P.rouge) + ligne(ER + 45, EY - 45, ER - 45, EY + 45, P.rouge),
  },
  {
    id: 'chargement', nom: 'Chargement', usage: 'Réfléchit, attend',
    svg: () => `<circle cx="230" cy="240" r="30" fill="${P.cyan}"/><circle cx="320" cy="240" r="30" fill="${P.cyan}" opacity=".65"/><circle cx="410" cy="240" r="30" fill="${P.cyan}" opacity=".3"/>`,
  },
  { id: 'clin-oeil', nom: 'Clin d\'œil', usage: 'Complice, malin', svg: () => arcHaut(EL, EY, P.cyan) + eye(ER, EY, P.cyan) },
  {
    id: 'determine', nom: 'Déterminé', usage: 'Passe à l\'action',
    svg: () =>
      `<path d="M${EL - 34} ${EY - 30} L${EL + 34} ${EY - 30} L${EL + 34} ${EY + 30} Q${EL + 34} ${EY + 64} ${EL} ${EY + 64} Q${EL - 34} ${EY + 64} ${EL - 34} ${EY + 30} Z" fill="${P.cyan}"/>` +
      `<path d="M${ER - 34} ${EY - 30} L${ER + 34} ${EY - 30} L${ER + 34} ${EY + 30} Q${ER + 34} ${EY + 64} ${ER} ${EY + 64} Q${ER - 34} ${EY + 64} ${ER - 34} ${EY + 30} Z" fill="${P.cyan}"/>` +
      ligne(EL - 45, EY - 62, EL + 40, EY - 50, P.cyan, 16) + ligne(ER + 45, EY - 62, ER - 40, EY - 50, P.cyan, 16),
  },
];

const ecranSVG = (e) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">` +
  `<rect width="${W}" height="${H}" fill="${P.bipEcranFond}"/>${e.svg()}</svg>`;

// ---------------------------------------------------------------------------
// 2. Planches de référence (à importer dans Blender : Ajouter > Image > Référence)
// ---------------------------------------------------------------------------
const grille = (w, h, pas, y0) => {
  let g = '';
  for (let y = y0; y >= 0; y -= pas) g += `<line x1="0" y1="${y}" x2="${w}" y2="${y}" stroke="${P.grille}" stroke-width="1.5"/>`;
  return g + `<line x1="0" y1="${y0}" x2="${w}" y2="${y0}" stroke="${P.trait}" stroke-width="3"/>`;
};
const titre = (x, y, t) => `<text x="${x}" y="${y}" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="${P.trait}" text-anchor="middle">${t}</text>`;
const note = (x, y, t, a = 'start') => `<text x="${x}" y="${y}" font-family="Arial, sans-serif" font-size="15" fill="${P.trait}" text-anchor="${a}">${t}</text>`;
const S = `stroke="${P.trait}" stroke-width="4" stroke-linejoin="round"`;

// Bip : unité = 100 px = 10 cm. Hauteur totale (antenne comprise) ≈ 3,2 unités = 32 cm.
const bipFace = (cx, sol, ecran = 'neutre') => {
  const cy = sol - 150; // centre du corps
  const e = EXPRESSIONS.find((x) => x.id === ecran);
  return `
  <line x1="${cx}" y1="${cy - 110}" x2="${cx}" y2="${cy - 160}" ${S}/>
  <circle cx="${cx}" cy="${cy - 170}" r="14" fill="${P.bipAccent}" ${S}/>
  <path d="M${cx - 98} ${cy + 20} Q${cx - 140} ${cy + 40} ${cx - 132} ${cy + 80}" fill="none" ${S} stroke-width="12" stroke-linecap="round"/>
  <path d="M${cx + 98} ${cy + 20} Q${cx + 140} ${cy + 40} ${cx + 132} ${cy + 80}" fill="none" ${S} stroke-width="12" stroke-linecap="round"/>
  <circle cx="${cx - 132}" cy="${cy + 88}" r="12" fill="${P.bipAccent}" ${S}/>
  <circle cx="${cx + 132}" cy="${cy + 88}" r="12" fill="${P.bipAccent}" ${S}/>
  <ellipse cx="${cx}" cy="${sol - 26}" rx="34" ry="26" fill="${P.bipAccent}" ${S}/>
  <ellipse cx="${cx}" cy="${cy}" rx="105" ry="115" fill="${P.bipCorps}" ${S}/>
  <path d="M${cx - 80} ${cy + 70} Q${cx} ${cy + 118} ${cx + 80} ${cy + 70}" fill="none" stroke="${P.bipOmbre}" stroke-width="6"/>
  <rect x="${cx - 72}" y="${cy - 64}" width="144" height="108" rx="26" fill="${P.bipEcranCadre}" ${S}/>
  <svg x="${cx - 62}" y="${cy - 55}" width="124" height="93" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" rx="90" fill="${P.bipEcranFond}"/>${e.svg()}</svg>`;
};
const bipProfil = (cx, sol) => {
  const cy = sol - 150;
  return `
  <line x1="${cx}" y1="${cy - 110}" x2="${cx - 8}" y2="${cy - 160}" ${S}/>
  <circle cx="${cx - 9}" cy="${cy - 170}" r="14" fill="${P.bipAccent}" ${S}/>
  <ellipse cx="${cx}" cy="${sol - 26}" rx="34" ry="26" fill="${P.bipAccent}" ${S}/>
  <ellipse cx="${cx}" cy="${cy}" rx="100" ry="115" fill="${P.bipCorps}" ${S}/>
  <path d="M${cx + 82} ${cy - 62} Q${cx + 118} ${cy - 10} ${cx + 82} ${cy + 46}" fill="${P.bipEcranCadre}" ${S}/>
  <path d="M${cx + 10} ${cy + 22} Q${cx + 40} ${cy + 50} ${cx + 30} ${cy + 88}" fill="none" ${S} stroke-width="12" stroke-linecap="round"/>
  <circle cx="${cx + 30}" cy="${cy + 96}" r="12" fill="${P.bipAccent}" ${S}/>`;
};

const planche = (w, h, contenu) =>
  `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}"><rect width="${w}" height="${h}" fill="${P.fond}"/>${contenu}</svg>`;

const bipPlanche = () => {
  const sol = 520;
  let c = grille(1000, 620, 100, sol);
  c += bipFace(280, sol) + bipProfil(720, sol);
  c += titre(280, 590, 'BIP — face') + titre(720, 590, 'BIP — profil');
  for (let i = 1; i <= 4; i++) c += note(985, sol - i * 100 + 5, `${i * 10} cm`, 'end');
  c += note(20, 40, 'Échelle : 1 carreau = 10 cm · hauteur totale ≈ 32 cm (antenne comprise) · corps ≈ 21 × 23 cm');
  return planche(1000, 620, c);
};

// Mocha : même échelle. Assis ≈ 45 cm aux oreilles.
const mochaFaceAssis = (cx, sol) => `
  <path d="M${cx + 70} ${sol - 20} Q${cx + 170} ${sol - 30} ${cx + 160} ${sol - 140} Q${cx + 155} ${sol - 190} ${cx + 120} ${sol - 200}" fill="none" stroke="${P.trait}" stroke-width="34" stroke-linecap="round"/>
  <path d="M${cx + 70} ${sol - 20} Q${cx + 170} ${sol - 30} ${cx + 160} ${sol - 140} Q${cx + 155} ${sol - 190} ${cx + 120} ${sol - 200}" fill="none" stroke="${P.mochaPelage}" stroke-width="26" stroke-linecap="round"/>
  <path d="M${cx + 145} ${sol - 185} Q${cx + 135} ${sol - 200} ${cx + 120} ${sol - 200}" fill="none" stroke="${P.mochaFonce}" stroke-width="26" stroke-linecap="round"/>
  <path d="M${cx - 95} ${sol} Q${cx - 120} ${sol - 160} ${cx - 60} ${sol - 240} L${cx + 60} ${sol - 240} Q${cx + 120} ${sol - 160} ${cx + 95} ${sol} Z" fill="${P.mochaPelage}" ${S}/>
  <path d="M${cx - 50} ${sol - 10} Q${cx - 60} ${sol - 150} ${cx} ${sol - 190} Q${cx + 60} ${sol - 150} ${cx + 50} ${sol - 10} Z" fill="${P.mochaCreme}"/>
  <ellipse cx="${cx - 40}" cy="${sol - 14}" rx="30" ry="16" fill="${P.mochaCreme}" ${S}/>
  <ellipse cx="${cx + 40}" cy="${sol - 14}" rx="30" ry="16" fill="${P.mochaCreme}" ${S}/>
  <path d="M${cx - 95} ${sol - 360} L${cx - 85} ${sol - 450} L${cx - 30} ${sol - 395} Z" fill="${P.mochaPelage}" ${S}/>
  <path d="M${cx + 95} ${sol - 360} L${cx + 85} ${sol - 450} L${cx + 30} ${sol - 395} Z" fill="${P.mochaPelage}" ${S}/>
  <path d="M${cx - 85} ${sol - 450} L${cx - 73} ${sol - 420} L${cx - 60} ${sol - 425} Z" fill="${P.mochaFonce}"/>
  <path d="M${cx + 85} ${sol - 450} L${cx + 73} ${sol - 420} L${cx + 60} ${sol - 425} Z" fill="${P.mochaFonce}"/>
  <ellipse cx="${cx}" cy="${sol - 320}" rx="115" ry="95" fill="${P.mochaPelage}" ${S}/>
  <path d="M${cx - 18} ${sol - 410} Q${cx} ${sol - 370} ${cx + 18} ${sol - 410} Z" fill="${P.mochaFonce}"/>
  <ellipse cx="${cx}" cy="${sol - 280}" rx="58" ry="38" fill="${P.mochaCreme}"/>
  <ellipse cx="${cx - 45}" cy="${sol - 330}" rx="24" ry="20" fill="${P.mochaYeux}" ${S} stroke-width="3"/>
  <ellipse cx="${cx + 45}" cy="${sol - 330}" rx="24" ry="20" fill="${P.mochaYeux}" ${S} stroke-width="3"/>
  <rect x="${cx - 49}" y="${sol - 340}" width="8" height="20" rx="4" fill="${P.trait}"/>
  <rect x="${cx + 41}" y="${sol - 340}" width="8" height="20" rx="4" fill="${P.trait}"/>
  <path d="M${cx - 72} ${sol - 336} Q${cx - 45} ${sol - 344} ${cx - 18} ${sol - 336} L${cx - 18} ${sol - 352} Q${cx - 45} ${sol - 362} ${cx - 72} ${sol - 352} Z" fill="${P.mochaPelage}" ${S} stroke-width="3"/>
  <path d="M${cx + 72} ${sol - 336} Q${cx + 45} ${sol - 344} ${cx + 18} ${sol - 336} L${cx + 18} ${sol - 352} Q${cx + 45} ${sol - 362} ${cx + 72} ${sol - 352} Z" fill="${P.mochaPelage}" ${S} stroke-width="3"/>
  <path d="M${cx - 10} ${sol - 296} L${cx + 10} ${sol - 296} L${cx} ${sol - 284} Z" fill="${P.mochaNez}"/>
  <path d="M${cx} ${sol - 284} Q${cx - 6} ${sol - 272} ${cx - 16} ${sol - 274} M${cx} ${sol - 284} Q${cx + 6} ${sol - 272} ${cx + 16} ${sol - 274}" fill="none" stroke="${P.trait}" stroke-width="3" stroke-linecap="round"/>`;

const mochaProfilDebout = (cx, sol) => `
  <path d="M${cx - 150} ${sol - 160} Q${cx - 250} ${sol - 170} ${cx - 245} ${sol - 290} Q${cx - 240} ${sol - 330} ${cx - 205} ${sol - 335}" fill="none" stroke="${P.trait}" stroke-width="34" stroke-linecap="round"/>
  <path d="M${cx - 150} ${sol - 160} Q${cx - 250} ${sol - 170} ${cx - 245} ${sol - 290} Q${cx - 240} ${sol - 330} ${cx - 205} ${sol - 335}" fill="none" stroke="${P.mochaPelage}" stroke-width="26" stroke-linecap="round"/>
  <path d="M${cx - 243} ${sol - 305} Q${cx - 238} ${sol - 332} ${cx - 205} ${sol - 335}" fill="none" stroke="${P.mochaFonce}" stroke-width="26" stroke-linecap="round"/>
  <rect x="${cx - 135}" y="${sol - 110}" width="42" height="110" rx="20" fill="${P.mochaPelage}" ${S}/>
  <rect x="${cx + 70}" y="${sol - 110}" width="42" height="110" rx="20" fill="${P.mochaPelage}" ${S}/>
  <ellipse cx="${cx - 20}" cy="${sol - 150}" rx="165" ry="80" fill="${P.mochaPelage}" ${S}/>
  <path d="M${cx - 120} ${sol - 95} Q${cx - 20} ${sol - 60} ${cx + 90} ${sol - 100}" fill="none" stroke="${P.mochaCreme}" stroke-width="18" stroke-linecap="round"/>
  <path d="M${cx + 110} ${sol - 305} L${cx + 112} ${sol - 385} L${cx + 160} ${sol - 330} Z" fill="${P.mochaPelage}" ${S}/>
  <ellipse cx="${cx + 160}" cy="${sol - 260}" rx="100" ry="88" fill="${P.mochaPelage}" ${S}/>
  <ellipse cx="${cx + 225}" cy="${sol - 225}" rx="40" ry="30" fill="${P.mochaCreme}"/>
  <path d="M${cx + 255} ${sol - 238} L${cx + 262} ${sol - 228} L${cx + 250} ${sol - 224} Z" fill="${P.mochaNez}"/>
  <ellipse cx="${cx + 200}" cy="${sol - 270}" rx="16" ry="18" fill="${P.mochaYeux}" ${S} stroke-width="3"/>
  <path d="M${cx + 182} ${sol - 272} Q${cx + 200} ${sol - 278} ${cx + 218} ${sol - 272} L${cx + 218} ${sol - 286} Q${cx + 200} ${sol - 294} ${cx + 182} ${sol - 286} Z" fill="${P.mochaPelage}" ${S} stroke-width="3"/>`;

const mochaPlanche = () => {
  const sol = 560;
  let c = grille(1100, 660, 100, sol);
  c += mochaFaceAssis(250, sol) + mochaProfilDebout(720, sol);
  c += titre(250, 630, 'MOCHA — face (assis)') + titre(720, 630, 'MOCHA — profil (debout)');
  for (let i = 1; i <= 4; i++) c += note(1085, sol - i * 100 + 5, `${i * 10} cm`, 'end');
  c += note(20, 40, 'Même échelle que Bip · assis ≈ 45 cm aux oreilles · tête ≈ 40 % de la hauteur assise · queue épaisse = outil d\'expression');
  return planche(1100, 660, c);
};

const echellePlanche = () => {
  const sol = 560;
  let c = grille(900, 640, 100, sol);
  c += mochaFaceAssis(560, sol) + bipFace(250, sol, 'joie');
  c += titre(250, 610, 'BIP ≈ 32 cm') + titre(560, 610, 'MOCHA assis ≈ 45 cm');
  c += note(20, 40, 'Rapport de taille : Mocha domine Bip — c\'est lui le « grand frère » blasé.');
  return planche(900, 640, c);
};

const palettePlanche = () => {
  const groupes = [
    ['Bip', [['Corps', P.bipCorps], ['Ombre', P.bipOmbre], ['Accent', P.bipAccent], ['Cadre écran', P.bipEcranCadre], ['Fond écran', P.bipEcranFond]]],
    ['Écran (émotions)', [['Neutre / joie', P.cyan], ['Tristesse', P.bleu], ['Colère / erreur', P.rouge], ['Idée / panique', P.jaune], ['Amour', P.rose], ['Veille', P.veille]]],
    ['Mocha', [['Pelage', P.mochaPelage], ['Foncé', P.mochaFonce], ['Crème', P.mochaCreme], ['Yeux', P.mochaYeux], ['Nez', P.mochaNez]]],
  ];
  let c = '', y = 60;
  for (const [g, couleurs] of groupes) {
    c += `<text x="30" y="${y}" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="${P.trait}">${g}</text>`;
    couleurs.forEach(([n, hex], i) => {
      const x = 30 + i * 150;
      c += `<rect x="${x}" y="${y + 15}" width="130" height="80" rx="12" fill="${hex}" stroke="${P.trait}" stroke-width="2"/>`;
      c += note(x, y + 118, n) + note(x, y + 138, hex);
    });
    y += 180;
  }
  return planche(940, y - 10, c);
};

// ---------------------------------------------------------------------------
// 3. Écriture des fichiers + rendu PNG
// ---------------------------------------------------------------------------
(async () => {
  fs.mkdirSync(OUT_ECRAN, { recursive: true });
  const fichiers = [];
  for (const e of EXPRESSIONS) fichiers.push([path.join(OUT_ECRAN, e.id), ecranSVG(e), W, H]);
  fichiers.push([path.join(OUT, 'bip-proportions'), bipPlanche(), 1000, 620]);
  fichiers.push([path.join(OUT, 'mocha-proportions'), mochaPlanche(), 1100, 660]);
  fichiers.push([path.join(OUT, 'echelle-bip-mocha'), echellePlanche(), 900, 640]);
  const pal = palettePlanche();
  fichiers.push([path.join(OUT, 'palette'), pal, 940, Number(pal.match(/height="(\d+)"/)[1])]);

  // Planche récapitulative des expressions (4 colonnes)
  const cols = 4, cw = 320, ch = 240, lab = 50;
  const rows = Math.ceil(EXPRESSIONS.length / cols);
  let rec = '';
  EXPRESSIONS.forEach((e, i) => {
    const x = (i % cols) * (cw + 20) + 20, y = Math.floor(i / cols) * (ch + lab + 20) + 20;
    rec += `<svg x="${x}" y="${y}" width="${cw}" height="${ch}" viewBox="0 0 ${W} ${H}"><rect width="${W}" height="${H}" rx="40" fill="${P.bipEcranFond}"/>${e.svg()}</svg>`;
    rec += `<text x="${x + cw / 2}" y="${y + ch + 30}" font-family="Arial, sans-serif" font-size="20" font-weight="700" fill="${P.trait}" text-anchor="middle">${e.nom}</text>`;
  });
  const rw = cols * (cw + 20) + 20, rh = rows * (ch + lab + 20) + 20;
  fichiers.push([path.join(OUT, 'planche-ecrans-bip'), planche(rw, rh, rec), rw, rh]);

  // Atlas des expressions (6 colonnes x 3 lignes, dans l'ordre de EXPRESSIONS) :
  // une seule texture pour l'écran de Bip dans Blender (voir tools/blender/preparer-scene.py)
  const AC = 6, AR = Math.ceil(EXPRESSIONS.length / AC);
  let atlas = '';
  EXPRESSIONS.forEach((e, i) => {
    atlas += `<svg x="${(i % AC) * W}" y="${Math.floor(i / AC) * H}" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${e.svg()}</svg>`;
  });
  fichiers.push([path.join(OUT, 'bip-ecran-atlas'),
    `<svg xmlns="http://www.w3.org/2000/svg" width="${AC * W}" height="${AR * H}"><rect width="100%" height="100%" fill="${P.bipEcranFond}"/>${atlas}</svg>`,
    AC * W, AR * H]);
  fs.writeFileSync(path.join(OUT, 'bip-ecran-atlas.json'),
    JSON.stringify({ colonnes: AC, lignes: AR, expressions: EXPRESSIONS.map((e) => e.id) }, null, 2) + '\n');

  const browser = await chromium.launch();
  const page = await browser.newPage({ deviceScaleFactor: 1 });
  for (const [base, svg, w, h] of fichiers) {
    fs.writeFileSync(base + '.svg', svg);
    await page.setViewportSize({ width: w, height: h });
    await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
    await page.screenshot({ path: base + '.png', clip: { x: 0, y: 0, width: w, height: h } });
  }
  await browser.close();
  console.log(`${fichiers.length} visuels générés dans ${path.relative(process.cwd(), OUT)}`);
})();
