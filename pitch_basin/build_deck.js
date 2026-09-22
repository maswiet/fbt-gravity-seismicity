// Pitch deck — "Unlocking Under-Explored Basins in Indonesia"
// Gravity + Magnetics reconnaissance (9-basin national portfolio) -> the
// non-uniqueness wall -> Receiver Functions as the absolute-depth key ->
// gravity + magnetics + seismology. Bilingual (EN headings, ID notes).
// 60-min workshop talk. pptxgenjs. Sources: PHE/S3 basin study + MERAMEX RF +
// Western Indonesia Vs models + reprocessed Tomini/Gorontalo satellite gravity.
const pptxgen = require("pptxgenjs");
const fs = require("fs");
const p = new pptxgen();

function imgSize(path) {
  const b = fs.readFileSync(path);
  if (b.length > 24 && b[0] === 0x89 && b[1] === 0x50) return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
  let i = 2;
  while (i < b.length) {
    if (b[i] !== 0xff) { i++; continue; }
    const m = b[i + 1];
    if (m >= 0xc0 && m <= 0xcf && m !== 0xc4 && m !== 0xc8 && m !== 0xcc)
      return { h: b.readUInt16BE(i + 5), w: b.readUInt16BE(i + 7) };
    i += 2 + b.readUInt16BE(i + 2);
  }
  return { w: 1, h: 1 };
}
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";
p.author = "Pak Zuhdi research group";
p.title = "Unlocking Under-Explored Basins in Indonesia";

const FIG = __dirname + "/media/";
const NAVY = "10233A", DEEP = "065A82", TEAL = "1C7293", MINT = "02C39A",
      LIGHT = "EEF3F6", INK = "10233A", MUT = "5A6B78", WHITE = "FFFFFF",
      RUST = "B0512F", GOLD = "C98A1A", PAPER = "F5F8FA";
const HSER = "Cambria", BODY = "Calibri";

function bg(s, c) { s.background = { color: c }; }
function tb(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: BODY }, o)); }
function head(s, kicker, title) {
  bg(s, WHITE);
  s.addShape(p.ShapeType.ellipse, { x: 0.6, y: 0.62, w: 0.18, h: 0.18, fill: { color: MINT } });
  tb(s, kicker, { x: 0.9, y: 0.55, w: 11.8, h: 0.34, fontSize: 13, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  tb(s, title, { x: 0.88, y: 0.86, w: 11.9, h: 0.95, fontSize: 27, bold: true, color: INK, fontFace: HSER, margin: 0 });
}
function figBox(s, file, x, y, w, h, frame = true) {
  const sz = imgSize(FIG + file);
  const ar = sz.w / sz.h;
  let iw = w, ih = w / ar;
  if (ih > h) { ih = h; iw = h * ar; }
  const ix = x + (w - iw) / 2, iy = y + (h - ih) / 2;
  if (frame) s.addShape(p.ShapeType.roundRect, { x: ix-0.05, y: iy-0.05, w: iw+0.1, h: ih+0.1,
     rectRadius: 0.05, fill: { color: LIGHT }, line: { color: "D3DEE5", width: 1 },
     shadow: { type: "outer", color: "9AA9B2", blur: 6, offset: 2, angle: 90, opacity: 0.35 } });
  s.addImage({ path: FIG + file, x: ix, y: iy, w: iw, h: ih });
}
function card(s, x, y, w, h, hdr, body, accent) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
  s.addShape(p.ShapeType.ellipse, { x: x+0.26, y: y+0.26, w: 0.3, h: 0.3, fill: { color: accent || TEAL } });
  tb(s, hdr, { x: x+0.72, y: y+0.2, w: w-0.9, h: 0.5, fontSize: 14.5, bold: true, color: INK, margin: 0 });
  tb(s, body, { x: x+0.3, y: y+0.76, w: w-0.6, h: h-1.0, fontSize: 12, color: MUT, margin: 0, lineSpacingMultiple: 1.05 });
}
function statRow(s, y, stats) {
  const n = stats.length, gap = 0.2, w = (12.43 - 0.9 - gap*(n-1)) / n;
  let x = 0.9;
  stats.forEach(([num, lab, col]) => {
    s.addShape(p.ShapeType.roundRect, { x, y, w, h: 1.7, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
    tb(s, num, { x: x+0.1, y: y+0.22, w: w-0.2, h: 0.8, fontSize: 29, bold: true, color: col || DEEP, fontFace: HSER, align: "center", margin: 0 });
    tb(s, lab, { x: x+0.12, y: y+1.06, w: w-0.24, h: 0.55, fontSize: 11.5, color: MUT, align: "center", margin: 0, lineSpacingMultiple: 1.0 });
    x += w + gap;
  });
}
function caption(s, t, x, y, w) { tb(s, t, { x, y, w, h: 0.4, fontSize: 9.5, italic: true, color: MUT, margin: 0 }); }
function note(s, t) {   // bilingual ID note strip at the bottom
  s.addShape(p.ShapeType.roundRect, { x: 0.9, y: 6.86, w: 11.53, h: 0.5, rectRadius: 0.06, fill: { color: PAPER }, line: { color: "DCE6EB", width: 1 } });
  tb(s, [{ text: "ID  ", options: { bold: true, color: TEAL } }, { text: t, options: { color: MUT } }],
     { x: 1.1, y: 6.9, w: 11.2, h: 0.42, fontSize: 11, italic: true, margin: 0, valign: "middle" });
}
function pageno(s, n) { tb(s, n, { x: 12.4, y: 7.06, w: 0.7, h: 0.3, fontSize: 10, color: MUT, align: "right", margin: 0 }); }
function S() { return p.addSlide(); }

// ---------------------------------------------------------------- title
(() => {
  const s = S(); bg(s, NAVY);
  s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.22, fill: { color: MINT } });
  s.addShape(p.ShapeType.rect, { x: 0, y: 7.28, w: 13.333, h: 0.22, fill: { color: GOLD } });
  tb(s, "WORKSHOP · UNLOCKING UNDER-EXPLORED BASINS IN INDONESIA", { x: 0.9, y: 1.5, w: 11.5, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 2 });
  tb(s, "From Potential Fields to Seismological Constraints", { x: 0.9, y: 2.05, w: 11.6, h: 1.6, fontSize: 40, bold: true, color: WHITE, fontFace: HSER, lineSpacingMultiple: 0.98 });
  tb(s, "Gravity & magnetics map where basins are — receiver functions tell us how deep. Together they turn reconnaissance into a drillable model.",
     { x: 0.9, y: 3.9, w: 11.2, h: 1.0, fontSize: 16, color: "C7D3DC", lineSpacingMultiple: 1.1 });
  tb(s, [{ text: "Gravity + Magnetic reconnaissance of 9 frontier basins", options: { color: "9FB3C0" } }],
     { x: 0.9, y: 5.5, w: 11, h: 0.4, fontSize: 13, italic: true });
  tb(s, "Pak Zuhdi Research Group  ·  Satellite gravity + magnetics + MERAMEX receiver functions  ·  60-minute keynote",
     { x: 0.9, y: 6.5, w: 11.5, h: 0.4, fontSize: 12.5, color: "8FA6B4" });
})();

// ---------------------------------------------------------------- 2 prize
(() => {
  const s = S(); head(s, "THE PRIZE", "Indonesia's under-explored basins are the next frontier");
  figBox(s, "s09_0.png", 6.5, 1.95, 6.2, 4.6);
  card(s, 0.9, 2.0, 5.1, 1.55, "Many basins, little modern data", "Indonesia hosts ~128 sedimentary basins; a large share in the east remain frontier — sparse wells, legacy 2-D seismic, no modern depth model.", RUST);
  card(s, 0.9, 3.7, 5.1, 1.5, "Satellite fields cover everything", "Public satellite gravity & magnetics blanket every basin uniformly — the ideal reconnaissance layer to rank and delineate targets.", DEEP);
  card(s, 0.9, 5.32, 5.1, 1.35, "The question", "Can potential fields alone give a drillable basin model? Or do we need a seismological anchor?", GOLD);
  caption(s, "Sedimentary basins of Indonesia (Badan Geologi, 2020).", 6.5, 6.62, 6.2);
  note(s, "Peta cekungan Indonesia: banyak cekungan timur masih frontier — data sumur & seismik terbatas. Gravity/magnetik satelit menutup semuanya secara merata.");
  pageno(s, "02");
})();

// ---------------------------------------------------------------- 3 agenda
(() => {
  const s = S(); head(s, "ROADMAP", "What this hour covers");
  const items = [
    ["1 · The toolkit", "Why gravity & magnetics respond to basins; processing & edge detection.", DEEP],
    ["2 · National portfolio", "Nine frontier basins screened with satellite gravity + magnetic RTP.", TEAL],
    ["3 · Deep dive: Tomini/Gorontalo", "Reprocessed satellite gravity — better gridding, sharper structure.", MINT],
    ["4 · The non-uniqueness wall", "Why potential fields alone cannot fix absolute basin depth.", RUST],
    ["5 · Seismology as the key", "Receiver functions anchor depth & velocity — MERAMEX & 91-station Vs.", GOLD],
    ["6 · The integrated future", "Gravity + magnetics + seismology, and a roadmap for frontier basins.", NAVY],
  ];
  let y = 2.0;
  items.forEach(([h, b, c], i) => {
    const x = i % 2 ? 6.95 : 0.9;
    card(s, x, y, 5.45, 1.4, h, b, c);
    if (i % 2) y += 1.6;
  });
  note(s, "Alur 60 menit: konsep → portfolio 9 cekungan → reprosesing Tomini → keterbatasan potensi-lapangan → receiver function sebagai kunci → integrasi.");
  pageno(s, "03");
})();

// ---------------------------------------------------------------- 4 why potential fields
(() => {
  const s = S(); head(s, "THE TOOLKIT · 1", "Basins are density & susceptibility contrasts");
  card(s, 0.9, 2.05, 5.7, 2.15, "Gravity — density contrast (Δρ)", "Low-density sedimentary fill (2.2–2.5 g/cm³) over denser basement (2.67–2.9) makes a NEGATIVE gravity anomaly. Depocentres = residual gravity lows.", DEEP);
  card(s, 0.9, 4.35, 5.7, 2.15, "Magnetics — susceptibility contrast (Δκ)", "Sediments are near-non-magnetic; basement & intrusions carry the signal. Magnetics image BASEMENT relief and volcanic/fault trends beneath the fill.", RUST);
  card(s, 6.85, 2.05, 5.55, 4.45, "Why use both", "Gravity senses total mass deficit; magnetics senses basement/structure. Read together they cut the ambiguity of either field alone (Gibson & Millegan, 1998) — the first step toward a basin model.\n\nBut note: both are POTENTIAL fields — smooth, non-unique, and depth-ambiguous. Hold that thought for Part 4.", TEAL);
  note(s, "Gravity peka ke kontras densitas (isi cekungan lebih ringan → anomali rendah); magnetik peka ke kontras suseptibilitas (relief batuan dasar). Dipakai bersama mengurangi ambiguitas.");
  pageno(s, "04");
})();

// ---------------------------------------------------------------- 5 gravity chain
(() => {
  const s = S(); head(s, "THE TOOLKIT · 2", "Gravity processing chain");
  const steps = [
    ["Free-air", "Satellite/altimetry gravity (Sandwell, GGMPlus)", DEEP],
    ["Bouguer", "Remove terrain/bathymetry mass (tesseroid)", TEAL],
    ["Isostatic", "Remove deep root compensation", MINT],
    ["Residual", "Regional–residual split → basin-scale field", RUST],
  ];
  let x = 0.9;
  steps.forEach(([h, b, c], i) => {
    s.addShape(p.ShapeType.roundRect, { x, y: 2.2, w: 2.7, h: 2.2, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
    tb(s, "0" + (i + 1), { x: x + 0.1, y: 2.35, w: 2.5, h: 0.5, fontSize: 15, bold: true, color: c, align: "center" });
    tb(s, h, { x: x + 0.1, y: 2.8, w: 2.5, h: 0.5, fontSize: 16, bold: true, color: INK, align: "center", fontFace: HSER });
    tb(s, b, { x: x + 0.18, y: 3.32, w: 2.34, h: 1.0, fontSize: 11, color: MUT, align: "center", lineSpacingMultiple: 1.05 });
    if (i < 3) tb(s, "→", { x: x + 2.62, y: 2.95, w: 0.35, h: 0.6, fontSize: 24, bold: true, color: TEAL, align: "center" });
    x += 2.88;
  });
  card(s, 0.9, 4.85, 11.5, 1.75, "The residual is the interpretation field", "Regional–residual separation (upward continuation / Gaussian high-pass) isolates shallow basin structure from deep lithospheric trends. Residual gravity LOWS mark sediment depocentres; HIGHS mark basement highs and horsts.", DEEP);
  note(s, "Rantai gravity: free-air → Bouguer (koreksi terrain) → isostatik → residual. Anomali residual RENDAH = depocentre cekungan; TINGGI = tinggian batuan dasar.");
  pageno(s, "05");
})();

// ---------------------------------------------------------------- 6 magnetic RTP
(() => {
  const s = S(); head(s, "THE TOOLKIT · 3", "Magnetics: why Reduce-to-Pole (RTP)");
  figBox(s, "s26_0.png", 6.35, 1.95, 6.3, 4.5);
  card(s, 0.9, 2.05, 5.1, 2.1, "The problem", "At low magnetic latitudes the anomaly is shifted and skewed away from its source — a body's peak does not sit over the body.", RUST);
  card(s, 0.9, 4.25, 5.1, 2.25, "RTP / RTE fix", "Reduce-to-Pole (or Equator) re-centres anomalies over their sources, so magnetic highs/lows line up with basement structure and can be co-interpreted with gravity.", DEEP);
  caption(s, "Total magnetic intensity, reduced to pole (EMAG2 V3 + WDMAM).", 6.35, 6.55, 6.3);
  note(s, "Di lintang magnetik rendah, anomali magnetik bergeser dari sumbernya. Reduce-to-Pole mengembalikan anomali tepat di atas sumber agar bisa dipadu dengan gravity.");
  pageno(s, "06");
})();

// ---------------------------------------------------------------- 7 edge detection + criteria
(() => {
  const s = S(); head(s, "THE TOOLKIT · 4", "Edge detection & basin delineation criteria");
  figBox(s, "s08_0.png", 6.7, 1.95, 6.0, 4.6);
  card(s, 0.9, 2.05, 5.35, 2.05, "Derivative filters find edges", "THD, tilt (TDR), analytic signal and theta maps sharpen gradients — they trace fault scarps, basin margins and intrusive contacts the raw field blurs.", TEAL);
  card(s, 0.9, 4.2, 5.35, 2.3, "A basin = converging evidence", "Diagnose a basin where a residual gravity LOW, a smooth low-gradient magnetic interior, and edge-detected bounding faults all coincide — not from one map alone.", DEEP);
  caption(s, "Basin delineation criteria (source deck).", 6.7, 6.62, 6.0);
  note(s, "Filter turunan (THD/TDR/analytic signal/theta) menandai tepi & sesar. Cekungan didiagnosis saat gravity rendah + interior magnetik tenang + sesar pembatas saling bertemu.");
  pageno(s, "07");
})();

// ---------------------------------------------------------------- 8 portfolio intro + data
(() => {
  const s = S(); head(s, "NATIONAL PORTFOLIO", "One reconnaissance workflow, nine frontier basins");
  statRow(s, 2.05, [["9", "frontier basins screened", DEEP], ["2", "independent fields per basin", TEAL], ["3", "depth slices (deep/crust/shallow)", MINT], ["100%", "public satellite data", GOLD]]);
  card(s, 0.9, 4.05, 5.7, 2.5, "Gravity — GGMPlus 2013 + WGM2012", "Isostatic-corrected satellite gravity, band-pass filtered into deep, crustal and shallow depth slices (wavelength → depth). Deep+shallow composite shown per basin.", DEEP);
  card(s, 6.75, 4.05, 5.65, 2.5, "Magnetics — EMAG2 V3 + WDMAM", "Total magnetic intensity, merged and reduced-to-pole. Same footprint as gravity so the two fields are co-registered and jointly interpreted for each basin.", RUST);
  note(s, "Satu alur untuk 9 cekungan: gravity isostatik (GGMPlus+WGM2012) di-slice per kedalaman + magnetik RTP (EMAG2V3+WDMAM). Semua data publik satelit.");
  pageno(s, "08");
})();

// ---------------------------------------------------------------- 9..17 nine basins
const BASINS = [
  ["Bengkulu", "Fore-arc basin, offshore SW Sumatra", "s33_0.png", "s33_1.png",
   "Elongated fore-arc gravity low parallel to the trench; magnetic quiet zone over the fill, magnetic highs on the outer-arc basement ridge."],
  ["Bogor", "Back-arc trough, West Java", "s34_0.png", "s34_1.png",
   "Deep E–W gravity low tracks the Bogor Trough; volcanic-arc magnetic highs bound it to the south."],
  ["Lombok Selatan", "Fore-arc, southern Nusa Tenggara", "s35_0.png", "s35_1.png",
   "Fore-arc low south of the volcanic arc; strong arc magnetic signature to the north frames the depocentre."],
  ["Tomori Selatan", "East arm, Sulawesi", "s36_0.png", "s36_1.png",
   "Gravity low over the Molucca/East-Sulawesi fill; complex magnetic fabric from ophiolite/basement blocks nearby."],
  ["Kendari", "Southeast Sulawesi", "s37_0.png", "s37_1.png",
   "Intramontane gravity low between metamorphic highs; magnetic contrasts follow the SE-Sulawesi terrane boundaries."],
  ["Gorontalo", "Tomini Bay, North Sulawesi", "s38_0.png", "s38_1.png",
   "Broad deep-marine gravity low in Tomini Bay — a prime depocentre; magnetic highs on the North-arm volcanic basement."],
  ["Poso", "Central Sulawesi", "s39_0.png", "s39_1.png",
   "Gravity low over the Poso/Central-Sulawesi depression; sharp magnetic edges mark bounding fault systems."],
  ["Melawi", "West Kalimantan", "s40_0.png", "s40_1.png",
   "Large intracratonic gravity low (Melawi–Ketungau); smooth magnetic interior typical of thick continental fill."],
  ["Nang Apino", "Frontier area", "s41_0.png", "s41_1.png",
   "Reconnaissance gravity low with edge-bounded margins; magnetics used to separate sedimentary fill from magnetic basement."],
];
BASINS.forEach(([name, region, grav, mag, read], i) => {
  const s = S(); head(s, "PORTFOLIO · BASIN " + (i + 1) + " / 9", name + "  —  " + region);
  figBox(s, grav, 0.9, 1.95, 5.75, 4.35);
  figBox(s, mag, 6.85, 1.95, 5.55, 4.35);
  tb(s, "Isostatic gravity (deep + shallow)", { x: 0.9, y: 6.32, w: 5.75, h: 0.3, fontSize: 11, bold: true, color: DEEP, align: "center", margin: 0 });
  tb(s, "Total magnetic intensity — RTP", { x: 6.85, y: 6.32, w: 5.55, h: 0.3, fontSize: 11, bold: true, color: RUST, align: "center", margin: 0 });
  note(s, "Baca cepat: " + read);
  pageno(s, String(9 + i).padStart(2, "0"));
});

// ---------------------------------------------------------------- 18 portfolio synthesis
(() => {
  const s = S(); head(s, "PORTFOLIO · SYNTHESIS", "Nine basins ranked — but by relative signal only");
  const rows = [
    ["Basin", "Setting", "Gravity low", "Magnetic read"],
    ["Gorontalo", "Tomini Bay", "Strong / broad", "Quiet interior, arc highs N"],
    ["Bogor", "W-Java back-arc", "Strong / linear", "Arc highs bound S"],
    ["Melawi", "W-Kalimantan", "Strong / broad", "Smooth interior"],
    ["Bengkulu", "Sumatra fore-arc", "Moderate", "Outer-arc ridge highs"],
    ["Poso / Kendari", "C/SE Sulawesi", "Moderate", "Fault-edge fabric"],
    ["Lombok S / Tomori / Nang Apino", "Frontier", "Variable", "Mixed basement"],
  ];
  let y = 2.05; const xh = [0.9, 3.7, 7.0, 9.3], wcol = [2.8, 3.3, 2.3, 3.1];
  rows.forEach((r, ri) => {
    const hdr = ri === 0;
    s.addShape(p.ShapeType.rect, { x: 0.9, y, w: 11.5, h: hdr ? 0.5 : 0.62, fill: { color: hdr ? DEEP : (ri % 2 ? LIGHT : WHITE) }, line: { color: "DCE6EB", width: 1 } });
    r.forEach((c, ci) => tb(s, c, { x: xh[ci], y: y + (hdr ? 0.08 : 0.13), w: wcol[ci], h: 0.4, fontSize: hdr ? 12.5 : 11.5, bold: hdr, color: hdr ? WHITE : INK, margin: 0 }));
    y += hdr ? 0.5 : 0.62;
  });
  tb(s, "Ranking uses RELATIVE anomaly strength and pattern — the maps do not yet give absolute depth, thickness, or volume.",
     { x: 0.9, y: 6.35, w: 11.5, h: 0.4, fontSize: 12, italic: true, bold: true, color: RUST, margin: 0 });
  note(s, "Peringkat berdasarkan kekuatan & pola anomali relatif. Peta ini belum memberi kedalaman/ketebalan/volume absolut — itu keterbatasan mendasarnya.");
  pageno(s, "18");
})();

// ---------------------------------------------------------------- 19 deep dive intro
(() => {
  const s = S(); head(s, "DEEP DIVE", "Tomini / Gorontalo — reprocessing the gravity");
  card(s, 0.9, 2.05, 5.6, 2.1, "Why this basin", "A deep-marine frontier depocentre in East Indonesia (Tomini Bay). Excellent test bed: strong gravity signal, active tectonics, no modern depth model.", MINT);
  card(s, 0.9, 4.25, 5.6, 2.25, "What we redid", "Re-fetched free public satellite gravity and re-gridded with minimum-curvature (surface, tension) + light Gaussian — replacing stepped, blocky maps with smooth, continuous fields and clean contours.", DEEP);
  figBox(s, "tomini_bouguer_smooth.png", 6.7, 2.0, 6.0, 4.5);
  caption(s, "Complete Bouguer anomaly, reprocessed (this study).", 6.7, 6.55, 6.0);
  note(s, "Tomini/Gorontalo = depocentre frontier laut-dalam Indonesia Timur. Gravity satelit gratis diproses ulang: gridding minimum-curvature + smoothing → peta halus & kontur bersih.");
  pageno(s, "19");
})();

// ---------------------------------------------------------------- 20 before/after
(() => {
  const s = S(); head(s, "DEEP DIVE · GRIDDING", "Better gridding, sharper structure");
  figBox(s, "tomini_residual_old.png", 0.9, 2.05, 5.75, 4.1);
  figBox(s, "tomini_residual_smooth.png", 6.85, 2.05, 5.55, 4.1);
  tb(s, "Before — stepped / blocky", { x: 0.9, y: 6.2, w: 5.75, h: 0.3, fontSize: 12, bold: true, color: MUT, align: "center", margin: 0 });
  tb(s, "After — minimum-curvature + smooth contours", { x: 6.85, y: 6.2, w: 5.55, h: 0.3, fontSize: 12, bold: true, color: MINT, align: "center", margin: 0 });
  note(s, "Kiri: gridding lama (bertingkat). Kanan: minimum-curvature (surface, tension) + Gaussian + kontur halus. Depocentre & tepi cekungan jauh lebih terbaca.");
  pageno(s, "20");
})();

// ---------------------------------------------------------------- 21 residual interp
(() => {
  const s = S(); head(s, "DEEP DIVE · DEPOCENTRES", "Residual Bouguer — where the sediment is");
  figBox(s, "tomini_residual_smooth.png", 0.9, 1.95, 8.1, 4.7);
  card(s, 9.2, 2.05, 3.2, 2.1, "Blue = basin low", "Deep residual lows in central Tomini Bay mark the main depocentres — thickest low-density fill.", DEEP);
  card(s, 9.2, 4.25, 3.2, 2.05, "Red = basement high", "Highs flank the North & East arms — structural highs / horsts separating sub-basins.", RUST);
  note(s, "Residual Bouguer: biru = anomali rendah (isi cekungan tebal / depocentre); merah = tinggian batuan dasar. Pola memisahkan sub-cekungan di Teluk Tomini.");
  pageno(s, "21");
})();

// ---------------------------------------------------------------- 22 edges
(() => {
  const s = S(); head(s, "DEEP DIVE · STRUCTURE", "Edge detection — the structural framework");
  figBox(s, "tomini_thd_smooth.png", 0.9, 2.0, 5.75, 4.3);
  figBox(s, "tomini_tilt_smooth.png", 6.85, 2.0, 5.55, 4.3);
  tb(s, "Total horizontal derivative (edges)", { x: 0.9, y: 6.32, w: 5.75, h: 0.3, fontSize: 11, bold: true, color: RUST, align: "center", margin: 0 });
  tb(s, "Tilt derivative — 0° contour = source outline", { x: 6.85, y: 6.32, w: 5.55, h: 0.3, fontSize: 11, bold: true, color: DEEP, align: "center", margin: 0 });
  note(s, "THD menandai tepi/sesar; tilt derivative (kontur 0°) menggambar garis batas sumber. Bersama-sama memberi kerangka struktur & batas depocentre Tomini.");
  pageno(s, "22");
})();

// ---------------------------------------------------------------- 23 the wall
(() => {
  const s = S(); bg(s, NAVY);
  tb(s, "PART 4 · THE LIMIT", { x: 0.9, y: 1.35, w: 11, h: 0.4, fontSize: 14, bold: true, color: GOLD, charSpacing: 2 });
  tb(s, "Potential fields are non-unique", { x: 0.9, y: 1.85, w: 11.5, h: 1.0, fontSize: 34, bold: true, color: WHITE, fontFace: HSER });
  tb(s, "A gravity or magnetic low can be a thin low-density layer — or a thick, slightly-less-low-density one. Infinitely many density×thickness models fit the same map.",
     { x: 0.9, y: 3.05, w: 11.4, h: 1.0, fontSize: 17, color: "C7D3DC", lineSpacingMultiple: 1.15 });
  const chips = [
    ["Depth ambiguity", "The field fixes mass deficit, not how it splits into density and depth.", RUST],
    ["Spectral depth = a range", "Wavelength→depth gives broad intervals, not a basement pick.", GOLD],
    ["Magnetics = relief, not scale", "RTP shows basement shape but not absolute burial depth.", MINT],
  ];
  let x = 0.9;
  chips.forEach(([h, b, c]) => {
    s.addShape(p.ShapeType.roundRect, { x, y: 4.5, w: 3.71, h: 1.9, rectRadius: 0.1, fill: { color: "16324F" }, line: { color: c, width: 1.5 } });
    tb(s, h, { x: x + 0.25, y: 4.7, w: 3.25, h: 0.6, fontSize: 15, bold: true, color: c, margin: 0 });
    tb(s, b, { x: x + 0.25, y: 5.32, w: 3.25, h: 1.0, fontSize: 12, color: "C7D3DC", margin: 0, lineSpacingMultiple: 1.08 });
    x += 3.85;
  });
  note(s, "Gravity/magnetik itu ambigu: satu anomali cocok untuk tak-hingga kombinasi densitas×ketebalan. Butuh jangkar kedalaman independen.");
  pageno(s, "23");
})();

// ---------------------------------------------------------------- 24 seismology 101
(() => {
  const s = S(); head(s, "PART 5 · THE KEY", "Seismology gives an independent depth anchor");
  card(s, 0.9, 2.05, 5.6, 2.1, "Teleseismic P waves", "Distant earthquakes send P energy up through the crust beneath a single station — no source, no survey needed.", DEEP);
  card(s, 0.9, 4.25, 5.6, 2.25, "Conversions carry depth", "At each velocity boundary some P converts to S (Ps). The DELAY of Ps after P is a direct clock on interface depth — the anchor gravity lacks.", MINT);
  figBox(s, "cj_rf_demo_BI1.png", 6.7, 2.05, 6.0, 4.4);
  caption(s, "Receiver function, station BI1 (MERAMEX, Central Java).", 6.7, 6.5, 6.0);
  note(s, "Gempa jauh → gelombang P menembus kerak di bawah satu stasiun. Sebagian P berubah jadi S (Ps) di tiap batas; jeda Ps = kedalaman batas. Inilah jangkar yang tak dimiliki gravity.");
  pageno(s, "24");
})();

// ---------------------------------------------------------------- 25 RF -> sediment + Vs
(() => {
  const s = S(); head(s, "PART 5 · METHOD", "Receiver functions → sediment thickness & Vs");
  figBox(s, "cj_vs_inversion_BI4.png", 0.9, 2.0, 7.3, 4.4);
  card(s, 8.5, 2.05, 3.9, 2.1, "Ps move-out → depth", "Convert Ps delay + ray parameter into an ABSOLUTE sediment / basement depth per station.", DEEP);
  card(s, 8.5, 4.25, 3.9, 2.25, "Full Vs inversion", "Herrmann CPS rftn96 inverts the waveform for a layered Vs(z) — physically constrained, PREM-like increase with depth.", MINT);
  note(s, "Move-out Ps → kedalaman absolut sedimen/basement; inversi penuh (CPS rftn96) → profil Vs(z) berlapis yang fisis. Kalibrasi densitas untuk gravity.");
  pageno(s, "25");
})();

// ---------------------------------------------------------------- 26 Central Java result
(() => {
  const s = S(); head(s, "PART 5 · EVIDENCE A", "Central Java — RF maps real sediment thickness");
  figBox(s, "cj_sediment_rf_map.png", 0.9, 1.95, 7.4, 4.7);
  card(s, 8.6, 2.05, 3.8, 2.15, "MERAMEX 2004", "Dozens of temporary broadband stations across Central Java — teleseismic RF at each yields sediment thickness.", DEEP);
  card(s, 8.6, 4.3, 3.8, 2.0, "A depth grid, not a guess", "Each dot is an absolute, station-based sediment estimate — the calibration gravity needs.", MINT);
  note(s, "Central Java (MERAMEX 2004): receiver function tiap stasiun → ketebalan sedimen absolut. Titik-titik ini menjadi kalibrasi untuk inversi gravity.");
  pageno(s, "26");
})();

// ---------------------------------------------------------------- 27 Western Indonesia Vs
(() => {
  const s = S(); head(s, "PART 5 · EVIDENCE B", "Western Indonesia — 91-station Vs models");
  figBox(s, "wi_map_moho_depth.png", 0.9, 1.95, 6.4, 4.5);
  figBox(s, "wi_vs_profiles_by_region.png", 7.5, 2.1, 4.9, 3.9);
  caption(s, "Moho depth (left) and regional Vs(z) profiles (right) — Sumatra, Java-Bali, Kalimantan.", 0.9, 6.5, 11.4);
  note(s, "91 stasiun broadband Indonesia Barat: model Vs 1-D → kedalaman Moho & profil kecepatan per wilayah. Kerangka kecepatan regional untuk membatasi densitas & kedalaman.");
  pageno(s, "27");
})();

// ---------------------------------------------------------------- 28 CJ validation
(() => {
  const s = S(); head(s, "PART 5 · VALIDATION (CENTRAL JAVA)", "Test: does gravity alone see the sediment?");
  figBox(s, "cj_gravity_vs_validation.png", 0.9, 2.0, 11.5, 4.15, false);
  tb(s, "90 MERAMEX stations · residual Bouguer sampled at each RF site · Pearson r = +0.08 (p = 0.44).",
     { x: 0.9, y: 6.2, w: 11.5, h: 0.3, fontSize: 11, italic: true, color: MUT, align: "center", margin: 0 });
  note(s, "Di Jawa Tengah, gravity satelit TIDAK berkorelasi dengan ketebalan sedimen RF (r≈0.1, tidak signifikan) — sinyal sedimen (~20 mGal) tertimbun variasi Moho/volkanik (~58 mGal). Bukti kuantitatif non-uniqueness.");
  pageno(s, "28");
})();

// ---------------------------------------------------------------- 29 CJ constraint
(() => {
  const s = S(); head(s, "PART 5 · CONSTRAINT (CENTRAL JAVA)", "Seismology unlocks the gravity interpretation");
  figBox(s, "cj_seismology_constraint.png", 0.9, 2.0, 11.5, 4.15, false);
  tb(s, "RF supplies absolute depth & Vs → fix density×depth → the coherent basin model gravity alone could not yield.",
     { x: 0.9, y: 6.2, w: 11.5, h: 0.3, fontSize: 11, italic: true, color: MUT, align: "center", margin: 0 });
  note(s, "Justru karena gravity ambigu, receiver function menjadi kunci: kedalaman & Vs absolut per stasiun mengunci skala densitas → model cekungan koheren. Di Central Java kita punya data RF & model Vs — inilah keunggulannya.");
  pageno(s, "29");
})();

// ---------------------------------------------------------------- 30 RF-constrained gravity
(() => {
  const s = S(); head(s, "PART 5 · THE BRIDGE", "RF-constrained gravity — the anchor pays off");
  figBox(s, "cj_sediment_constrained.png", 0.9, 1.95, 7.2, 4.6);
  card(s, 8.4, 2.05, 4.0, 2.1, "Gravity alone drifts", "Unconstrained gravity inversion trades depth against density — weak correlation with true structure.", RUST);
  card(s, 8.4, 4.25, 4.0, 2.05, "RF locks the scale", "Feeding RF depths as constraints fixes the density×depth trade — gravity now resolves basin geometry.", MINT);
  note(s, "Gravity sendirian ambigu (kedalaman vs densitas). Dengan kedalaman RF sebagai constraint, skala terkunci → gravity menghasilkan geometri cekungan yang benar.");
  pageno(s, "30");
})();

// ---------------------------------------------------------------- 3-D inversion (method)
(() => {
  const s = S(); head(s, "PART 5 · 3-D INVERSION", "3-D gravity basin inversion (Uieda & Barbosa, 2017)");
  figBox(s, "cj_uieda_vs_rf.png", 0.9, 1.95, 8.15, 4.5);
  card(s, 9.25, 2.05, 3.15, 2.15, "Tesseroid + Bott", "Spherical-prism forward modelling + regularised Bott inversion (harmonica) for the sediment–basement relief around a reference level.", DEEP);
  card(s, 9.25, 4.3, 3.15, 2.1, "RF-calibrated & constrained", "Δρ and z_ref fixed from RF depths (paper §2.6.2); RF depths added as constraints → the model honours seismology (r = 0.93).", MINT);
  note(s, "Inversi 3D gravity cara Uieda (tesseroid + Bott + Tikhonov). Δρ & z_ref dikalibrasi RF; kedalaman RF jadi constraint → geometri cekungan terkunci ke data seismik.");
  pageno(s, "31");
})();

// ---------------------------------------------------------------- 3-D inversion (density section)
(() => {
  const s = S(); head(s, "PART 5 · BASIN MODEL", "Representative density cross-section (A–A')");
  figBox(s, "cj_uieda_density_section.png", 0.9, 2.05, 11.5, 4.15, false);
  tb(s, "Low-density fill (ρ≈2170) over basement (ρ≈2670); the RF-constrained basement (line) tracks the RF picks (dots).  Vertical exaggeration ×6.",
     { x: 0.9, y: 6.35, w: 11.5, h: 0.3, fontSize: 11, italic: true, color: MUT, align: "center", margin: 0 });
  note(s, "Penampang densitas cekungan: isi sedimen ringan di atas batuan dasar; garis basement (inversi ter-constrain RF) mengikuti titik RF. Depocentre jelas, VE ×6.");
  pageno(s, "32");
})();

// ---------------------------------------------------------------- 3-D inversion (the sharp test)
(() => {
  const s = S(); head(s, "PART 5 · A SHARP TEST", "Why predicted ≠ observed — and the residual looks like the field");
  figBox(s, "cj_uieda_profile.png", 0.9, 1.95, 7.65, 4.7);
  card(s, 8.75, 2.05, 3.65, 2.15, "Gravity vs RF: incompatible", "Fit the gravity → wrong depths (r=−0.1). Match RF → gravity misfit doubles (6→12 mGal). You cannot satisfy both — they carry independent information.", RUST);
  card(s, 8.75, 4.3, 3.65, 2.1, "The low is NOT sediment", "Where the residual is most negative, RF says sediment is THIN → the low comes from a deeper/denser source that gravity-alone would misread as a basin.", DEEP);
  note(s, "Predicted (ter-constrain RF) kecil & tak mirip observed → residual ≈ observed. Sebab: low gravity terbesar justru di tempat sedimen RF tipis — sumbernya lebih dalam, bukan cekungan. Justifikasi kuat perlunya seismologi.");
  pageno(s, "33");
})();

// ---------------------------------------------------------------- two seismic routes
(() => {
  const s = S(); head(s, "PART 5 · TWO SEISMIC ROUTES", "Two independent seismological routes to the basin");
  figBox(s, "an_two_approaches.png", 0.9, 1.95, 11.5, 4.35, false);
  tb(s, "(a) Receiver functions (Ps move-out)   vs   (b) Ambient-noise autocorrelation (Romero & Schimmel 2018) — same stations, independent physics.",
     { x: 0.9, y: 6.35, w: 11.5, h: 0.3, fontSize: 11, italic: true, color: MUT, align: "center", margin: 0 });
  note(s, "Dua jalur seismologi independen ke basement: RF (konversi Ps) & autokorelasi ambient noise (Romero). RF cenderung lebih dalam, AN lebih dangkal — selisihnya mengukur ketidakpastian dan memandu inversi gabungan.");
  pageno(s, "34");
})();

// ---------------------------------------------------------------- ambient-noise method
(() => {
  const s = S(); head(s, "PART 5 · AMBIENT NOISE (ROMERO)", "Basement from noise alone — no earthquakes, no source");
  figBox(s, "an_daily_section.png", 0.9, 1.95, 7.6, 4.7);
  card(s, 8.7, 2.05, 3.7, 2.15, "Autocorrelation = reflection response", "Single-station autocorrelation of continuous ambient noise (PCC + phase-weighted stack) returns the zero-offset P-wave reflection response beneath each site.", DEEP);
  card(s, 8.7, 4.3, 3.7, 2.1, "RF-independent basement", "Multi-band sidelobe discrimination keeps only real reflectors; the deepest band-stable one → basement TWT → depth (independent Vp). 111 stations mapped.", MINT);
  note(s, "Metode Romero & Schimmel: autokorelasi ambient noise satu-stasiun (PCC+PWS) → respons refleksi-P. Diskriminasi multi-band memisahkan reflektor asli dari sidelobe. Basement murni dari korelasi — tanpa RF.");
  pageno(s, "35");
})();

// ---------------------------------------------------------------- joint basement
(() => {
  const s = S(); head(s, "PART 5 · THE UNIFIED MODEL", "One basement from three datasets: RF + noise + gravity");
  figBox(s, "joint_map.png", 0.9, 1.95, 7.05, 4.55);
  card(s, 8.15, 2.05, 4.25, 1.55, "Joint tesseroid inversion", "Gravity gives the smooth lateral shape; RF & ambient-noise depths pin the absolute scale as soft point constraints (Uieda + Bott).", DEEP);
  card(s, 8.15, 3.72, 4.25, 1.5, "Honours both probes", "The unified model correlates with RF (r = 0.69) and with ambient noise (r = 0.63) at once — the RF/AN tension is reconciled, not ignored.", MINT);
  figBox(s, "joint_section.png", 8.15, 5.32, 4.25, 1.35, false);
  note(s, "Model basement TERPADU Central Java: gravity (bentuk lateral) + kedalaman RF & autokorelasi ambient-noise (skala absolut) dalam satu inversi tesseroid. Menghormati kedua data seismik sekaligus — depocentre ~4–5 km, tinggian ~2 km.");
  pageno(s, "36");
})();

// ---------------------------------------------------------------- 29 synthesis (dark)
(() => {
  const s = S(); bg(s, NAVY);
  s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.16, fill: { color: MINT } });
  tb(s, "THE SYNTHESIS", { x: 0.9, y: 0.9, w: 11, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 2 });
  tb(s, "Gravity + magnetics + seismology", { x: 0.9, y: 1.35, w: 11.5, h: 0.9, fontSize: 32, bold: true, color: WHITE, fontFace: HSER });
  const cols = [
    ["Gravity + magnetics", "WHERE the basins are: extent, depocentres, bounding faults, basement relief — over every basin, cheaply.", DEEP, "Reconnaissance"],
    ["Receiver functions", "HOW deep they are: absolute sediment thickness & Vs at each station — the missing scale.", MINT, "Calibration"],
    ["Joint model", "A DRILLABLE basin geometry: potential-field coverage locked to seismological depth. Non-uniqueness resolved.", GOLD, "Decision"],
  ];
  let x = 0.9;
  cols.forEach(([h, b, c, tag]) => {
    s.addShape(p.ShapeType.roundRect, { x, y: 2.7, w: 3.71, h: 3.4, rectRadius: 0.12, fill: { color: "16324F" }, line: { color: c, width: 1.5 } });
    tb(s, tag.toUpperCase(), { x: x + 0.3, y: 2.95, w: 3.1, h: 0.35, fontSize: 11, bold: true, color: c, charSpacing: 1 });
    tb(s, h, { x: x + 0.3, y: 3.35, w: 3.1, h: 0.9, fontSize: 18, bold: true, color: WHITE, fontFace: HSER, margin: 0 });
    tb(s, b, { x: x + 0.3, y: 4.35, w: 3.15, h: 1.6, fontSize: 12.5, color: "C7D3DC", margin: 0, lineSpacingMultiple: 1.12 });
    x += 3.85;
  });
  tb(s, "When we add seismological constraints, gravity + magnetics become far more powerful.",
     { x: 0.9, y: 6.35, w: 11.5, h: 0.5, fontSize: 15, bold: true, italic: true, color: MINT, align: "center" });
  pageno(s, "37");
})();

// ---------------------------------------------------------------- 30 roadmap
(() => {
  const s = S(); head(s, "PART 6 · ROADMAP", "Applying the recipe to frontier basins");
  const steps = [
    ["1 · Screen", "Rank basins by satellite gravity + magnetic RTP (done — 9 basins).", DEEP],
    ["2 · Reprocess", "Minimum-curvature gravity + edge detection on the leads (Tomini shown).", TEAL],
    ["3 · Anchor", "Occupy existing IA / GE broadband near the basin; compute receiver functions.", MINT],
    ["4 · Joint invert", "Gravity + magnetics constrained by RF depth & Vs → basin geometry.", GOLD],
    ["5 · Target", "Deliver depocentre maps & prospect leads for the frontier acreage.", RUST],
  ];
  let y = 2.05;
  steps.forEach(([h, b, c], i) => {
    const x = i % 2 ? 6.95 : 0.9;
    card(s, x, y, 5.45, 1.4, h, b, c);
    if (i % 2) y += 1.6;
  });
  card(s, 6.95, 4.85, 5.45, 1.4, "Data already on the table", "MIGAS legacy wells & 2-D seismic + permanent broadband networks — the anchor stations largely exist.", NAVY);
  note(s, "Resep: screening satelit → reprosesing → jangkar RF di stasiun broadband yang sudah ada → inversi gabungan → peta depocentre & lead. Banyak data sudah tersedia.");
  pageno(s, "38");
})();

// ---------------------------------------------------------------- physics helper
function eqp(s, x, y, w, h, tit, eq, txt, c) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
  tb(s, tit, { x: x+0.25, y: y+0.2, w: w-0.5, h: 0.4, fontSize: 14, bold: true, color: c, margin: 0 });
  s.addShape(p.ShapeType.roundRect, { x: x+0.2, y: y+0.66, w: w-0.4, h: 0.72, rectRadius: 0.05, fill: { color: "FFFFFF" }, line: { color: "D3DEE5", width: 1 } });
  tb(s, eq, { x: x+0.28, y: y+0.72, w: w-0.56, h: 0.6, fontSize: 14.5, bold: true, color: INK, fontFace: HSER, align: "center", valign: "middle", margin: 0 });
  tb(s, txt, { x: x+0.25, y: y+1.5, w: w-0.5, h: h-1.65, fontSize: 11.5, color: MUT, margin: 0, lineSpacingMultiple: 1.06 });
}

// ---------------------------------------------------------------- physics I: RF
(() => {
  const s = S(); head(s, "PHYSICS I · RECEIVER FUNCTIONS", "How receiver functions read absolute depth");
  eqp(s, 0.9, 2.05, 3.7, 4.4, "1 · P → S conversion", "P  →  Ps  at each Δ(ρV)",
      "A teleseismic P wave converts part of its energy to a delayed S wave (Ps) at every velocity / impedance boundary beneath the station.", DEEP);
  eqp(s, 4.77, 2.05, 3.7, 4.4, "2 · Source-equalised", "RF = Radial ⊘ Vertical⁻¹",
      "Deconvolving the vertical from the radial component removes the earthquake source and deep path, leaving the local Ps response (iterative time-domain deconvolution).", TEAL);
  eqp(s, 8.63, 2.05, 3.7, 4.4, "3 · Delay → depth", "H = t_Ps / (√(Vs⁻²−p²) − √(Vp⁻²−p²))",
      "The Ps–P delay t_Ps and the ray parameter p give the ABSOLUTE interface depth H — the sediment–basement pick that gravity lacks.", MINT);
  note(s, "Fisika RF: gelombang P jauh → konversi Ps di tiap batas; dekonvolusi vertikal menghi­langkan sumber; jeda Ps + ray parameter → kedalaman absolut interface.");
  pageno(s, "39");
})();

// ---------------------------------------------------------------- physics II: gravity+inversion
(() => {
  const s = S(); head(s, "PHYSICS II · GRAVITY & INVERSION", "Gravity: strong signal, weak uniqueness");
  eqp(s, 0.9, 2.05, 3.7, 4.4, "1 · Mass → gravity", "Δg = 2πG·Δρ·h",
      "Low-density fill (Δρ<0) of thickness h makes a negative Bouguer anomaly (infinite slab). Tesseroids sum this over a spherical Earth (Uieda & Barbosa 2017).", DEEP);
  eqp(s, 4.77, 2.05, 3.7, 4.4, "2 · Non-uniqueness", "Δg fixes Δρ·h — not each",
      "Infinitely many density×thickness models fit the same field → gravity ALONE cannot resolve depth. This is why a seismological anchor is essential.", RUST);
  eqp(s, 8.63, 2.05, 3.7, 4.4, "3 · Regularised Bott", "(AᵀA + μRᵀR)Δb = Aᵀr − μRᵀRb",
      "Iterative relief update; Jacobian A ≈ 2πGΔρ (Bouguer-plate), μ = Tikhonov smoothing. Solved with sparse conjugate gradients.", MINT);
  note(s, "Fisika gravity: anomali ∝ Δρ·h (slab); ambigu (densitas×ketebalan tak terpisah) → non-unik. Inversi Bott ter-regularisasi (tesseroid) memperbaiki relief basement.");
  pageno(s, "40");
})();

// ---------------------------------------------------------------- physics III: Romero
(() => {
  const s = S(); head(s, "PHYSICS III · AMBIENT-NOISE AUTOCORRELATION", "Turning noise into a reflection seismogram");
  eqp(s, 0.9, 2.05, 3.7, 4.4, "1 · Claerbout principle", "AC[u(t)]  ≈  reflection response",
      "The autocorrelation of the transmitted ambient wavefield equals the zero-offset P reflection response beneath the station — no earthquake, no active source.", DEEP);
  eqp(s, 4.77, 2.05, 3.7, 4.4, "2 · Phase cross-correlation", "c(τ) = ⟨cos[φ(t+τ)−φ(t)]⟩",
      "Amplitude-unbiased (Schimmel 1999): uses only the instantaneous phase φ of the analytic signal, then a phase-weighted stack — robust to transients & noise bursts.", TEAL);
  eqp(s, 8.63, 2.05, 3.7, 4.4, "3 · Two-way time → depth", "H = Vp · t_bsm / 2",
      "The basement reflection’s two-way time gives depth. Multi-band stacking keeps real reflections (fixed TWT) and rejects zero-lag sidelobes (which move with band).", MINT);
  note(s, "Fisika Romero: autokorelasi noise = respons refleksi (Claerbout); PCC pakai fase sesaat (amplitude-unbiased); TWT basement → kedalaman; multi-band menyaring sidelobe.");
  pageno(s, "41");
})();

// ---------------------------------------------------------------- physics IV: joint
(() => {
  const s = S(); head(s, "PHYSICS IV · JOINT INVERSION", "Fusing three physics into one basement");
  s.addShape(p.ShapeType.roundRect, { x: 0.9, y: 2.05, w: 11.5, h: 1.15, rectRadius: 0.08, fill: { color: NAVY } });
  tb(s, "Φ(b) = ‖g(b) − d_grav‖²  +  μ‖Rb‖²  +  w_RF² Σ(b−z_RF)²  +  w_AN² Σ(b−z_AN)²",
     { x: 1.1, y: 2.28, w: 11.1, h: 0.7, fontSize: 17, bold: true, color: WHITE, fontFace: HSER, align: "center", valign: "middle", margin: 0 });
  eqp(s, 0.9, 3.45, 3.7, 3.0, "gravity + smoothness", "shape between stations",
      "The dense gravity term sets the smooth LATERAL geometry of the basement; μ‖Rb‖² keeps the model stable where data are sparse.", DEEP);
  eqp(s, 4.77, 3.45, 3.7, 3.0, "RF + AN = absolute depth", "z_RF , z_AN as anchors",
      "Two independent seismological depths pin the vertical scale as soft constraints; where they disagree, the model takes a weight-balanced compromise.", MINT);
  eqp(s, 8.63, 3.45, 3.7, 3.0, "weights = confidence", "w² ∝ 1/σ²",
      "Each dataset enters with a weight = its inverse variance (a Bayesian likelihood). Result: r=0.69 vs RF and r=0.63 vs AN at once.", GOLD);
  note(s, "Fisika joint: satu fungsi objektif menggabungkan gravity (bentuk), kehalusan, dan kedalaman RF & AN (skala). Bobot = 1/σ² (Bayesian). Basement terpadu yang konsisten dengan semua data.");
  pageno(s, "42");
})();

// ---------------------------------------------------------------- 31 closing
(() => {
  const s = S(); bg(s, NAVY);
  s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 0.22, fill: { color: MINT } });
  s.addShape(p.ShapeType.rect, { x: 0, y: 7.28, w: 13.333, h: 0.22, fill: { color: GOLD } });
  tb(s, "THANK YOU", { x: 0.9, y: 1.7, w: 11, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 3 });
  tb(s, "From data scarcity to a drillable basin", { x: 0.9, y: 2.2, w: 11.5, h: 1.5, fontSize: 34, bold: true, color: WHITE, fontFace: HSER, lineSpacingMultiple: 1.0 });
  tb(s, "Satellite gravity & magnetics screen and delineate every Indonesian frontier basin. Receiver functions supply the absolute depth that potential fields cannot. Together they are far more powerful than either alone.",
     { x: 0.9, y: 3.85, w: 11.2, h: 1.4, fontSize: 16, color: "C7D3DC", lineSpacingMultiple: 1.2 });
  tb(s, "Discussion / Q&A  ·  30 minutes", { x: 0.9, y: 5.5, w: 11, h: 0.5, fontSize: 16, bold: true, color: GOLD });
  tb(s, "Pak Zuhdi Research Group  ·  Gravity + Magnetics + Receiver Functions  ·  Unlocking Under-Explored Basins in Indonesia",
     { x: 0.9, y: 6.4, w: 11.5, h: 0.4, fontSize: 12, color: "8FA6B4" });
})();

const OUT = __dirname + "/Boko_Basin_Gravity_Magnetic_RF_keynote.pptx";
p.writeFile({ fileName: OUT }).then(() => console.log("WROTE", OUT));
