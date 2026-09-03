// Keynote deck: Seismology as the bridge to sediment-basin models.
// Workshop "From Data Scarcity to Discovery — Unlocking Under-Explored Basin",
// FMIPA UGM, 22-23 Sep 2026. Built with pptxgenjs. Real MERAMEX/CPS results.
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";

const FIG = "/Users/maswiet/Work/Students/Pak_Zuhdi/figures/rf_java/";
// Ocean-gradient palette (geophysics)
const NAVY = "10233A", DEEP = "065A82", TEAL = "1C7293", MINT = "02C39A",
      LIGHT = "EEF3F6", INK = "10233A", MUT = "5A6B78", WHITE = "FFFFFF";
const HSER = "Cambria", BODY = "Calibri";

function bg(s, c) { s.background = { color: c }; }
function tb(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: BODY }, o)); }

// ---- section/title (dark) helper ----
function titleSlide() {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.rect, { x: 0, y: 0, w: 13.333, h: 7.5, fill: { color: NAVY } });
  // motif: mint dot
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 1.5, w: 0.28, h: 0.28, fill: { color: MINT } });
  tb(s, "FROM DATA SCARCITY TO DISCOVERY", { x: 0.9, y: 2.05, w: 11.5, h: 0.5,
     fontFace: BODY, fontSize: 16, color: MINT, charSpacing: 3, bold: true, margin: 0 });
  tb(s, "Seismology as the bridge to sediment-basin models", { x: 0.85, y: 2.55, w: 11.6, h: 1.6,
     fontFace: HSER, fontSize: 40, color: WHITE, bold: true, margin: 0, lineSpacingMultiple: 1.0 });
  tb(s, "Receiver functions + satellite gravity for under-explored basins — Central Java (MERAMEX)",
     { x: 0.9, y: 4.25, w: 11.4, h: 0.6, fontSize: 18, color: "CADCFC", margin: 0 });
  tb(s, "Workshop & Discussion Forum — Unlocking Under-Explored Basin\nFMIPA Universitas Gadjah Mada  ·  22–23 September 2026",
     { x: 0.9, y: 5.5, w: 11.4, h: 1.0, fontSize: 13, color: "8FA6B8", margin: 0, lineSpacingMultiple: 1.2 });
  s.addNotes("Opening: frontier basins in Indonesia are under-explored precisely because data is scarce. I'll show how passive seismology — receiver functions — gives a direct, physical measurement of sediment thickness that anchors ambiguous satellite gravity.");
}

// ---- content header helper ----
function head(s, kicker, title) {
  bg(s, WHITE);
  s.addShape(p.ShapeType.ellipse, { x: 0.6, y: 0.62, w: 0.18, h: 0.18, fill: { color: MINT } });
  tb(s, kicker, { x: 0.9, y: 0.55, w: 11.8, h: 0.34, fontSize: 13, bold: true,
     color: TEAL, charSpacing: 2, margin: 0 });
  tb(s, title, { x: 0.88, y: 0.86, w: 11.9, h: 0.9, fontSize: 30, bold: true,
     color: INK, fontFace: HSER, margin: 0 });
}

function figBox(s, file, x, y, w, h) {
  s.addShape(p.ShapeType.roundRect, { x: x-0.06, y: y-0.06, w: w+0.12, h: h+0.12,
     rectRadius: 0.06, fill: { color: LIGHT }, line: { color: "D3DEE5", width: 1 },
     shadow: { type: "outer", color: "9AA9B2", blur: 6, offset: 2, angle: 90, opacity: 0.35 } });
  s.addImage({ path: FIG + file, x, y, w, h, sizing: { type: "contain", w, h } });
}

function card(s, x, y, w, h, hdr, body, accent) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08,
     fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
  s.addShape(p.ShapeType.ellipse, { x: x+0.28, y: y+0.28, w: 0.34, h: 0.34, fill: { color: accent || TEAL } });
  tb(s, hdr, { x: x+0.8, y: y+0.24, w: w-1.0, h: 0.5, fontSize: 16, bold: true, color: INK, margin: 0 });
  tb(s, body, { x: x+0.3, y: y+0.78, w: w-0.6, h: h-1.0, fontSize: 13, color: MUT, margin: 0, lineSpacingMultiple: 1.05 });
}

// ============================================================ 1 TITLE
titleSlide();

// ============================================================ 2 CHALLENGE
(() => {
  const s = p.addSlide(); head(s, "THE CHALLENGE", "Frontier basins are under-explored because data is scarce");
  card(s, 0.9, 2.0, 3.75, 2.3, "Sparse seismic", "Reflection surveys are costly and thin on the ground in frontier areas — the depocentre geometry is poorly known.", DEEP);
  card(s, 4.83, 2.0, 3.75, 2.3, "Gravity is non-unique", "Satellite gravity covers everything, cheaply — but many density models fit one anomaly. It needs an anchor.", TEAL);
  card(s, 8.76, 2.0, 3.65, 2.3, "Volcanic overprint", "In arcs like Java, the Bouguer field is dominated by igneous/basement density, masking thin sediment.", "B06B3A");
  tb(s, "The question:  how do we get an absolute, physical sediment-thickness model where wells and seismic are absent?",
     { x: 0.9, y: 4.7, w: 11.5, h: 0.9, fontSize: 18, italic: true, color: INK, margin: 0 });
  tb(s, "Answer — passive seismology. A single 3-component station records distant earthquakes; the converted waves carry the layering directly beneath it.",
     { x: 0.9, y: 5.6, w: 11.5, h: 1.0, fontSize: 15, color: MUT, margin: 0, lineSpacingMultiple: 1.15 });
})();

// ============================================================ 3 SEISMOLOGY BASICS (diagram)
(() => {
  const s = p.addSlide(); head(s, "SEISMOLOGY 101", "A teleseismic P wave converts to S at every interface");
  // draw layered earth cross-section
  const x0 = 0.9, w = 6.6, yTop = 2.15;
  const layers = [["Sediment (low Vs)", "C9E5F2", 0.9], ["Crust", "AFC7D6", 1.5], ["Mantle", "7E97A6", 1.2]];
  let y = yTop;
  layers.forEach(([lab, col, h]) => {
    s.addShape(p.ShapeType.rect, { x: x0, y, w, h, fill: { color: col }, line: { color: "FFFFFF", width: 1 } });
    tb(s, lab, { x: x0+0.15, y: y+0.08, w: w-0.3, h: 0.3, fontSize: 12, bold: true, color: INK, margin: 0 });
    y += h;
  });
  // incoming ray (up through layers) and station
  s.addShape(p.ShapeType.line, { x: x0+0.6, y: y, w: 2.2, h: -(y-yTop), line: { color: NAVY, width: 2.5, endArrowType: "triangle" } });
  s.addShape(p.ShapeType.line, { x: x0+2.8, y: yTop+2.4, w: 0.9, h: -0.9, line: { color: MINT, width: 2, dashType: "dash", endArrowType: "triangle" } });
  tb(s, "P", { x: x0+0.35, y: y-0.5, w: 0.4, h: 0.3, fontSize: 13, bold: true, color: NAVY, margin: 0 });
  tb(s, "Ps", { x: x0+3.15, y: yTop+1.75, w: 0.6, h: 0.3, fontSize: 13, bold: true, color: "0E8A6E", margin: 0 });
  s.addShape(p.ShapeType.triangle, { x: x0+3.5, y: yTop-0.32, w: 0.5, h: 0.32, fill: { color: "B03030" } });
  tb(s, "station", { x: x0+3.95, y: yTop-0.34, w: 1.2, h: 0.3, fontSize: 11, color: MUT, margin: 0 });
  // right column explanation
  const rx = 8.0;
  tb(s, "The physics", { x: rx, y: 2.15, w: 4.4, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "A magnitude-5+ earthquake 15–90° away sends a near-vertical P wave up to the station.", options: { bullet: true, breakLine: true } },
    { text: "At each velocity contrast, part of the P energy converts to a slower S wave (a “Ps” phase).", options: { bullet: true, breakLine: true } },
    { text: "The delay of Ps after P scales with the depth of the interface.", options: { bullet: true, breakLine: true } },
    { text: "The vertical component ≈ the source; the radial holds the conversions.", options: { bullet: true } },
  ], { x: rx, y: 2.6, w: 4.5, h: 3.2, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 10, lineSpacingMultiple: 1.05 });
  tb(s, "Deeper interface  →  later Ps  →  read structure from time.",
     { x: rx, y: 5.9, w: 4.5, h: 0.7, fontSize: 14, italic: true, color: DEEP, margin: 0 });
})();

// ============================================================ 4 WHAT IS A RECEIVER FUNCTION
(() => {
  const s = p.addSlide(); head(s, "THE METHOD", "Receiver function = radial deconvolved by vertical");
  tb(s, [
    { text: "RF(t)  =  Radial(t)  ÷  Vertical(t)", options: { bold: true, breakLine: true, fontSize: 20, color: INK } },
    { text: "(deconvolution in the time domain)", options: { fontSize: 13, color: MUT } },
  ], { x: 0.9, y: 2.0, w: 6.4, h: 0.9, margin: 0, align: "left" });
  tb(s, [
    { text: "Removes the earthquake source and instrument — what's left is the site's impulse response.", options: { bullet: true, breakLine: true } },
    { text: "A clean spike at t = 0 (direct P), then positive pulses at each Ps conversion.", options: { bullet: true, breakLine: true } },
    { text: "Iterative time-domain deconvolution (Ligorria & Ammon 1999) — the same algorithm as CPS saciterd.", options: { bullet: true, breakLine: true } },
    { text: "A Gaussian width ‘a’ sets resolution: higher a resolves thin sediment.", options: { bullet: true } },
  ], { x: 0.9, y: 3.0, w: 6.4, h: 3.4, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 12, lineSpacingMultiple: 1.1 });
  figBox(s, "rf_demo_BI1.png", 7.7, 1.95, 4.9, 4.9);
  tb(s, "Station BGB: 6 individual RFs (red) and their stack (blue). Direct P at 0 s; sediment Ps in the first seconds.",
     { x: 7.7, y: 6.85, w: 4.9, h: 0.5, fontSize: 10, italic: true, color: MUT, margin: 0 });
})();

// ============================================================ 5 RF WORKFLOW (process)
(() => {
  const s = p.addSlide(); head(s, "WORKFLOW", "From raw teleseism to a receiver function");
  const steps = [
    ["01", "Select events", "M ≥ 5, 15–90°, good SNR"],
    ["02", "Rotate", "N,E → Radial, Transverse (back-azimuth)"],
    ["03", "Deconvolve", "Radial ÷ Vertical, iterative time-domain"],
    ["04", "Quality control", "keep clean, causal RFs"],
    ["05", "Stack", "average per station → stable RF"],
  ];
  let x = 0.9; const w = 2.25, gap = 0.19, y = 2.4, h = 2.7;
  steps.forEach(([n, t, d], i) => {
    s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: i%2 ? TEAL : DEEP } });
    tb(s, n, { x: x+0.2, y: y+0.25, w: w-0.4, h: 0.7, fontSize: 30, bold: true, color: MINT, fontFace: HSER, margin: 0 });
    tb(s, t, { x: x+0.2, y: y+1.1, w: w-0.4, h: 0.6, fontSize: 16, bold: true, color: WHITE, margin: 0 });
    tb(s, d, { x: x+0.2, y: y+1.7, w: w-0.4, h: 0.9, fontSize: 12, color: "DCEAF0", margin: 0, lineSpacingMultiple: 1.05 });
    if (i < steps.length-1) s.addShape(p.ShapeType.line, { x: x+w+0.01, y: y+h/2, w: gap-0.02, h: 0, line: { color: MUT, width: 1.5, endArrowType: "triangle" } });
    x += w + gap;
  });
  tb(s, "MERAMEX 2004: 143 stations · 7 teleseisms (back-azimuth 86–269°) · 110 stations with usable receiver functions.",
     { x: 0.9, y: 5.5, w: 11.5, h: 0.8, fontSize: 15, color: INK, margin: 0 });
})();

// ============================================================ 6 FORWARD MODELING (hrftn96)
(() => {
  const s = p.addSlide(); head(s, "FORWARD MODELLING  ·  PEMODELAN MAJU", "Predict the RF a layered earth would produce");
  figBox(s, "fwd_demo_BI1.png", 0.9, 2.0, 7.2, 4.4);
  tb(s, "Observed RF (black) vs synthetic from Herrmann CPS hrftn96 (red) for the fitted sediment layer.",
     { x: 0.9, y: 6.45, w: 7.2, h: 0.5, fontSize: 10, italic: true, color: MUT, margin: 0 });
  const rx = 8.4;
  tb(s, "hrftn96 (Herrmann)", { x: rx, y: 2.0, w: 4.1, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Input: a velocity model (layer thickness, Vp, Vs, ρ) + ray parameter + Gaussian.", options: { bullet: true, breakLine: true } },
    { text: "Output: the exact receiver function that model predicts.", options: { bullet: true, breakLine: true } },
    { text: "Forward modelling turns interpretation into a test: does my layered model reproduce the data?", options: { bullet: true, breakLine: true } },
    { text: "It is also the engine inside the inversion.", options: { bullet: true } },
  ], { x: rx, y: 2.5, w: 4.2, h: 3.6, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 11, lineSpacingMultiple: 1.1 });
})();

// ============================================================ 7 INVERSION
(() => {
  const s = p.addSlide(); head(s, "INVERSION", "From receiver function to sediment thickness");
  card(s, 0.9, 2.05, 5.6, 2.15, "Read the conversion", "The first strong Ps pulse after direct P marks the sediment–basement interface. Its delay t(Ps) is picked on the stacked RF.", DEEP);
  card(s, 0.9, 4.35, 5.6, 2.15, "Convert delay to depth", "Move-out relation:  H = t(Ps) / [ √(1/Vs² − p²) − √(1/Vp² − p²) ].  Assumed sediment Vs 1.5 km/s.", TEAL);
  s.addShape(p.ShapeType.roundRect, { x: 6.9, y: 2.05, w: 5.5, h: 4.45, rectRadius: 0.1, fill: { color: NAVY } });
  tb(s, "The Herrmann framework", { x: 7.2, y: 2.3, w: 4.9, h: 0.4, fontSize: 17, bold: true, color: MINT, margin: 0 });
  tb(s, [
    { text: "Computer Programs in Seismology (Herrmann 2013) provides the forward RF (hrftn96) and the linearised RF inversion (rftn96).", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "We validate every station's derived layer by forward modelling — synthetic vs observed.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Result: 103 of 110 stations give a resolvable sediment thickness.", options: { bullet: true, color: MINT } },
  ], { x: 7.2, y: 2.8, w: 4.9, h: 3.5, fontSize: 15, margin: 0, paraSpaceAfter: 12, lineSpacingMultiple: 1.12 });
})();

// ============================================================ 8 DATASET
(() => {
  const s = p.addSlide(); head(s, "THE EXPERIMENT", "MERAMEX 2004 — a dense passive array over Central Java");
  const stats = [["143", "seismic stations"], ["110", "stations with RFs"], ["7", "teleseisms used"], ["~2.8 km", "median sediment"]];
  let x = 0.9; const w = 2.85, gap = 0.2;
  stats.forEach(([n, l]) => {
    s.addShape(p.ShapeType.roundRect, { x, y: 2.0, w, h: 1.7, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
    tb(s, n, { x: x+0.1, y: 2.2, w: w-0.2, h: 0.8, fontSize: 34, bold: true, color: DEEP, fontFace: HSER, align: "center", margin: 0 });
    tb(s, l, { x: x+0.1, y: 3.05, w: w-0.2, h: 0.5, fontSize: 13, color: MUT, align: "center", margin: 0 });
    x += w + gap;
  });
  figBox(s, "sediment_rf_map.png", 3.4, 3.95, 6.5, 3.2);
  tb(s, [
    { text: "Merapi Amphibious Experiment (GFZ), May–Oct 2004.", options: { bullet: true, breakLine: true } },
    { text: "Broadband + short-period stations, ~10–20 km spacing.", options: { bullet: true, breakLine: true } },
    { text: "Public / experiment data — no new acquisition.", options: { bullet: true, breakLine: true } },
    { text: "Each dot = one RF-derived sediment estimate.", options: { bullet: true } },
  ], { x: 0.9, y: 4.05, w: 2.4, h: 3.0, fontSize: 13, color: INK, margin: 0, paraSpaceAfter: 9, lineSpacingMultiple: 1.05 });
})();

// ============================================================ 9 RESULT: sediment map (hero)
(() => {
  const s = p.addSlide(); head(s, "RESULT  ·  SEISMOLOGY", "Sediment thickness measured directly at 103 stations");
  figBox(s, "sediment_rf_map.png", 0.9, 1.95, 7.4, 5.0);
  const rx = 8.6;
  tb(s, "What the RFs say", { x: rx, y: 2.1, w: 4.0, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Median ~2.8 km; range 0.9–7.2 km.", options: { bullet: true, breakLine: true } },
    { text: "Consistent with published Central-Java basin depths.", options: { bullet: true, breakLine: true } },
    { text: "Thick pockets mark depocentres; thin zones mark basement/volcanic highs.", options: { bullet: true, breakLine: true } },
    { text: "Absolute, physical — no density assumption needed.", options: { bullet: true } },
  ], { x: rx, y: 2.55, w: 4.1, h: 3.2, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 11, lineSpacingMultiple: 1.1 });
  tb(s, "This is the anchor.", { x: rx, y: 6.0, w: 4.1, h: 0.6, fontSize: 18, bold: true, italic: true, color: DEEP, margin: 0 });
})();

// ============================================================ 10 GRAVITY context
(() => {
  const s = p.addSlide(); head(s, "THE OTHER HALF", "Satellite gravity — dense coverage, but ambiguous");
  figBox(s, "bouguer.png", 0.9, 2.0, 5.7, 4.6);
  figBox(s, "residual.png", 6.75, 2.0, 5.7, 4.6);
  tb(s, "GGM+WGM complete Bouguer anomaly", { x: 0.9, y: 6.6, w: 5.7, h: 0.4, fontSize: 12, bold: true, color: INK, align: "center", margin: 0 });
  tb(s, "Residual (short-wavelength) — basin-scale signal", { x: 6.75, y: 6.6, w: 5.7, h: 0.4, fontSize: 12, bold: true, color: INK, align: "center", margin: 0 });
})();

// ============================================================ 11 THE HONEST FINDING
(() => {
  const s = p.addSlide(); head(s, "THE KEY INSIGHT", "In a volcanic arc, gravity alone cannot see the sediment");
  figBox(s, "rf_vs_gravity.png", 0.9, 2.05, 5.2, 4.5);
  const rx = 6.6;
  s.addShape(p.ShapeType.roundRect, { x: rx, y: 2.05, w: 5.8, h: 4.5, rectRadius: 0.1, fill: { color: NAVY } });
  tb(s, "Correlation r ≈ 0.1", { x: rx+0.35, y: 2.35, w: 5.1, h: 0.6, fontSize: 24, bold: true, color: MINT, fontFace: HSER, margin: 0 });
  tb(s, [
    { text: "RF sediment thickness does NOT track the Bouguer residual here.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Why: Central Java's gravity field is dominated by the volcanic arc and basement density — not by thin, low-density sediment.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "So gravity inversion for sediment is under-determined without an independent depth control.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "That control is the receiver function.", options: { bullet: true, color: MINT } },
  ], { x: rx+0.35, y: 3.05, w: 5.1, h: 3.4, fontSize: 14.5, margin: 0, paraSpaceAfter: 10, lineSpacingMultiple: 1.1 });
})();

// ============================================================ 12 INTEGRATED MODEL
(() => {
  const s = p.addSlide(); head(s, "THE BRIDGE", "RF-anchored, gravity-contextualised sediment model");
  figBox(s, "sediment_constrained.png", 0.9, 1.95, 7.2, 5.0);
  const rx = 8.4;
  tb(s, "Integration", { x: rx, y: 2.1, w: 4.2, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Receiver functions set the absolute thickness at 103 points.", options: { bullet: true, breakLine: true } },
    { text: "Gravity supplies the continuous spatial fabric between stations.", options: { bullet: true, breakLine: true } },
    { text: "Collocation ties the map to the seismology (honours every station).", options: { bullet: true, breakLine: true } },
    { text: "A first, reconnaissance depth-to-basement model — from public data only.", options: { bullet: true } },
  ], { x: rx, y: 2.55, w: 4.2, h: 3.3, fontSize: 14.5, color: INK, margin: 0, paraSpaceAfter: 10, lineSpacingMultiple: 1.1 });
  tb(s, "Seismology turns ambiguous gravity into a calibrated basin model.",
     { x: rx, y: 6.0, w: 4.2, h: 0.9, fontSize: 15, italic: true, bold: true, color: DEEP, margin: 0 });
})();

// ============================================================ 13 IMPLICATIONS (dark)
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 0.85, w: 0.22, h: 0.22, fill: { color: MINT } });
  tb(s, "WHY IT MATTERS FOR EXPLORATION", { x: 1.25, y: 0.8, w: 11, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 2, margin: 0 });
  tb(s, "A cheap, public-data workflow for frontier basins", { x: 0.9, y: 1.25, w: 11.5, h: 0.9, fontSize: 30, bold: true, color: WHITE, fontFace: HSER, margin: 0 });
  const items = [
    ["Reconnaissance first", "Screen an under-explored basin for depocentres before committing to seismic."],
    ["Physical anchor", "RF gives absolute thickness where wells and reflection data are absent."],
    ["Re-use passive data", "Any temporary or permanent broadband network already on the ground can be mined."],
    ["Scales nationally", "Same recipe applies to Sumatra fore-arc, Makassar, Banda and other frontiers."],
  ];
  let y = 2.5; items.forEach(([h, d], i) => {
    const x = i % 2 ? 6.9 : 0.9; if (i === 2) y = 4.55;
    s.addShape(p.ShapeType.roundRect, { x, y, w: 5.5, h: 1.8, rectRadius: 0.08, fill: { color: "16324D" }, line: { color: TEAL, width: 1 } });
    tb(s, h, { x: x+0.35, y: y+0.25, w: 4.9, h: 0.5, fontSize: 18, bold: true, color: MINT, margin: 0 });
    tb(s, d, { x: x+0.35, y: y+0.78, w: 4.9, h: 0.9, fontSize: 14, color: "D6E4EC", margin: 0, lineSpacingMultiple: 1.1 });
  });
  s.addNotes("Tie-back for Pertamina Upstream: this is a low-cost screening layer that de-risks where to spend seismic dollars in frontier acreage.");
})();

// ============================================================ 14 CLOSING (dark)
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 2.2, w: 0.3, h: 0.3, fill: { color: MINT } });
  tb(s, "The takeaway", { x: 1.35, y: 2.15, w: 11, h: 0.5, fontSize: 16, bold: true, color: MINT, charSpacing: 2, margin: 0 });
  tb(s, "Where data is scarce, seismology is the bridge to the sediment basin.",
     { x: 0.9, y: 2.8, w: 11.4, h: 1.8, fontSize: 34, bold: true, color: WHITE, fontFace: HSER, margin: 0, lineSpacingMultiple: 1.0 });
  tb(s, "Receiver functions  +  satellite gravity  +  Herrmann CPS  →  a public-data depth-to-basement model for Central Java.",
     { x: 0.9, y: 4.7, w: 11.4, h: 0.8, fontSize: 17, color: "CADCFC", margin: 0 });
  tb(s, "Terima kasih  ·  Thank you", { x: 0.9, y: 5.8, w: 11.4, h: 0.6, fontSize: 20, bold: true, color: MINT, margin: 0 });
})();

p.writeFile({ fileName: "/Users/maswiet/Work/Students/Pak_Zuhdi/pitch_rf_gravity/RF_Gravity_CentralJava_keynote.pptx" })
 .then(f => console.log("WROTE", f));
