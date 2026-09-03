// Keynote deck (merged): gravity alone fails across Indonesia -> seismology is the
// bridge -> gravity + seismology is far more powerful. Central Java (MERAMEX) case.
// Workshop "From Data Scarcity to Discovery — Unlocking Under-Explored Basin",
// FMIPA UGM, 22-23 Sep 2026. pptxgenjs. Real MERAMEX/CPS + Indonesia-inversion results.
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.defineLayout({ name: "W", width: 13.333, height: 7.5 });
p.layout = "W";

const FIG = "/Users/maswiet/Work/Students/Pak_Zuhdi/figures/rf_java/";
const NAVY = "10233A", DEEP = "065A82", TEAL = "1C7293", MINT = "02C39A",
      LIGHT = "EEF3F6", INK = "10233A", MUT = "5A6B78", WHITE = "FFFFFF",
      RUST = "B0512F", GOLD = "C98A1A";
const HSER = "Cambria", BODY = "Calibri";

function bg(s, c) { s.background = { color: c }; }
function tb(s, t, o) { s.addText(t, Object.assign({ isTextBox: true, fontFace: BODY }, o)); }
function head(s, kicker, title) {
  bg(s, WHITE);
  s.addShape(p.ShapeType.ellipse, { x: 0.6, y: 0.62, w: 0.18, h: 0.18, fill: { color: MINT } });
  tb(s, kicker, { x: 0.9, y: 0.55, w: 11.8, h: 0.34, fontSize: 13, bold: true, color: TEAL, charSpacing: 2, margin: 0 });
  tb(s, title, { x: 0.88, y: 0.86, w: 11.9, h: 0.95, fontSize: 29, bold: true, color: INK, fontFace: HSER, margin: 0 });
}
function figBox(s, file, x, y, w, h) {
  s.addShape(p.ShapeType.roundRect, { x: x-0.06, y: y-0.06, w: w+0.12, h: h+0.12,
     rectRadius: 0.06, fill: { color: LIGHT }, line: { color: "D3DEE5", width: 1 },
     shadow: { type: "outer", color: "9AA9B2", blur: 6, offset: 2, angle: 90, opacity: 0.35 } });
  s.addImage({ path: FIG + file, x, y, w, h, sizing: { type: "contain", w, h } });
}
function card(s, x, y, w, h, hdr, body, accent) {
  s.addShape(p.ShapeType.roundRect, { x, y, w, h, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
  s.addShape(p.ShapeType.ellipse, { x: x+0.28, y: y+0.28, w: 0.34, h: 0.34, fill: { color: accent || TEAL } });
  tb(s, hdr, { x: x+0.8, y: y+0.24, w: w-1.0, h: 0.5, fontSize: 15, bold: true, color: INK, margin: 0 });
  tb(s, body, { x: x+0.3, y: y+0.82, w: w-0.6, h: h-1.05, fontSize: 12.5, color: MUT, margin: 0, lineSpacingMultiple: 1.05 });
}
function statRow(s, y, stats) {   // stats: [[num,label,color],...]
  const n = stats.length, gap = 0.2, w = (12.43 - 0.9 - gap*(n-1)) / n;
  let x = 0.9;
  stats.forEach(([num, lab, col]) => {
    s.addShape(p.ShapeType.roundRect, { x, y, w, h: 1.7, rectRadius: 0.08, fill: { color: LIGHT }, line: { color: "DCE6EB", width: 1 } });
    tb(s, num, { x: x+0.1, y: y+0.22, w: w-0.2, h: 0.8, fontSize: 30, bold: true, color: col || DEEP, fontFace: HSER, align: "center", margin: 0 });
    tb(s, lab, { x: x+0.12, y: y+1.06, w: w-0.24, h: 0.55, fontSize: 12, color: MUT, align: "center", margin: 0, lineSpacingMultiple: 1.0 });
    x += w + gap;
  });
}
function caption(s, t, x, y, w) {
  tb(s, t, { x, y, w, h: 0.5, fontSize: 10, italic: true, color: MUT, margin: 0 });
}

// ============================================================ 1 TITLE
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 1.45, w: 0.28, h: 0.28, fill: { color: MINT } });
  tb(s, "FROM DATA SCARCITY TO DISCOVERY", { x: 0.9, y: 2.0, w: 11.5, h: 0.5, fontSize: 16, color: MINT, charSpacing: 3, bold: true, margin: 0 });
  tb(s, "Seismology as the bridge to sediment-basin models", { x: 0.85, y: 2.5, w: 11.6, h: 1.3, fontFace: HSER, fontSize: 39, color: WHITE, bold: true, margin: 0 });
  tb(s, "Why satellite gravity alone falls short in Indonesia — and how receiver functions make gravity + seismology powerful. A Central Java (MERAMEX) case study.",
     { x: 0.9, y: 4.15, w: 11.4, h: 1.0, fontSize: 17, color: "CADCFC", margin: 0, lineSpacingMultiple: 1.15 });
  tb(s, "Workshop & Discussion Forum — Unlocking Under-Explored Basin  ·  FMIPA Universitas Gadjah Mada  ·  22–23 September 2026",
     { x: 0.9, y: 5.7, w: 11.4, h: 0.7, fontSize: 13, color: "8FA6B8", margin: 0 });
  s.addNotes("Frame: Indonesia's frontier basins are under-explored because data is scarce. Satellite gravity is the obvious cheap tool — but I'll show it is not enough on its own here, and that seismology is the bridge that unlocks it.");
})();

// ============================================================ 2 THE PRIZE
(() => {
  const s = p.addSlide(); head(s, "THE OPPORTUNITY", "Indonesia's under-explored basins — the frontier prize");
  card(s, 0.9, 2.05, 3.75, 2.35, "128 basins", "The ESDM 2022 map inventories 128 sedimentary basins; many frontier basins remain undrilled or with only sparse data.", DEEP);
  card(s, 4.83, 2.05, 3.75, 2.35, "Sediment = the container", "Hydrocarbons need a thick sediment fill and depocentres. Mapping basin geometry is step one of exploration.", TEAL);
  card(s, 8.76, 2.05, 3.65, 2.35, "Data is scarce", "Seismic reflection and wells are expensive and thin on the ground in frontier acreage — we need cheaper reconnaissance.", GOLD);
  tb(s, "Can we screen basin geometry — depth-to-basement, sediment thickness — from public, low-cost data before committing to seismic?",
     { x: 0.9, y: 4.75, w: 11.5, h: 1.0, fontSize: 18, italic: true, color: INK, margin: 0, lineSpacingMultiple: 1.1 });
  tb(s, "Two candidates: satellite gravity (dense, cheap, global) and passive seismology (physical, absolute, station-based).",
     { x: 0.9, y: 5.75, w: 11.5, h: 0.7, fontSize: 15, color: MUT, margin: 0 });
})();

// ============================================================ 3 GRAVITY PROMISE
(() => {
  const s = p.addSlide(); head(s, "ATTEMPT 1  ·  GRAVITY ALONE", "Can satellite gravity map basins by itself?");
  card(s, 0.9, 2.1, 5.6, 2.0, "The promise", "Sedimentary basins are low-density fill → they should read as Bouguer/isostatic lows. Satellite gravity covers all of Indonesia, cheaply and uniformly.", DEEP);
  card(s, 0.9, 4.25, 5.6, 2.1, "The test", "A full 3-D gravity inversion for sediment thickness (Parker series, cited densities, compaction), benchmarked against published basin depths.", TEAL);
  s.addShape(p.ShapeType.roundRect, { x: 6.9, y: 2.1, w: 5.5, h: 4.25, rectRadius: 0.1, fill: { color: NAVY } });
  tb(s, "A properly validated pipeline", { x: 7.2, y: 2.35, w: 4.9, h: 0.4, fontSize: 17, bold: true, color: MINT, margin: 0 });
  tb(s, [
    { text: "Literature review → cited physical parameters → conceptual model → 3-D inversion.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Parker forward series verified against the exact forward to 0.0016 mGal.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Synthetic 7-km basin recovered at RMS 79 m, r = 0.9991 — the test even caught a sign error.", options: { bullet: true, color: MINT } },
  ], { x: 7.2, y: 2.85, w: 4.9, h: 3.3, fontSize: 15, margin: 0, paraSpaceAfter: 12, lineSpacingMultiple: 1.12 });
})();

// ============================================================ 4 GRAVITY FAILS
(() => {
  const s = p.addSlide(); head(s, "THE HONEST RESULT", "The method works — but gravity alone fails on real basins");
  statRow(s, 2.05, [["r = 0.9991", "synthetic recovery (framework works)", DEEP],
                    ["r = 0.75", "CRUST1.0 control (same tests)", TEAL],
                    ["r = −0.15", "real inversion vs published thickness", RUST]]);
  tb(s, "Through identical tests, polygons and metrics, CRUST1.0 scores r = 0.75 — so the validation framework is healthy. The near-zero real-data result is therefore real, not a bug.",
     { x: 0.9, y: 4.05, w: 11.5, h: 0.9, fontSize: 16, color: INK, margin: 0, lineSpacingMultiple: 1.15 });
  tb(s, "Satellite gravity, inverted on its own, does NOT recover Indonesian basin sediment thickness. Why?",
     { x: 0.9, y: 5.05, w: 11.5, h: 0.9, fontSize: 19, bold: true, italic: true, color: RUST, margin: 0 });
  s.addNotes("Key credibility point: the same framework recovers a synthetic basin near-perfectly AND scores CRUST1.0 at 0.75. So the r=-0.15 on real data is a physical result, not a coding error.");
})();

// ============================================================ 5 WHY GRAVITY FAILS (Kutai schematic)
(() => {
  const s = p.addSlide(); head(s, "WHY  ·  THE PHYSICS", "In Indonesia the gravity signal is not the sediment");
  // schematic: basin low vs Moho up
  const x0 = 0.9, y0 = 2.3, w = 5.6;
  s.addShape(p.ShapeType.rect, { x: x0, y: y0, w, h: 0.9, fill: { color: "C9E5F2" }, line: { color: WHITE, width: 1 } });
  tb(s, "Sediment fill 10–11 km  (− density → gravity LOW)", { x: x0+0.12, y: y0+0.28, w: w-0.24, h: 0.4, fontSize: 11, bold: true, color: INK, margin: 0 });
  s.addShape(p.ShapeType.rect, { x: x0, y: y0+0.9, w, h: 1.5, fill: { color: "AFC7D6" }, line: { color: WHITE, width: 1 } });
  tb(s, "Crust", { x: x0+0.12, y: y0+1.5, w: 2, h: 0.3, fontSize: 11, color: INK, margin: 0 });
  // Moho pushed up under basin (rift)
  s.addShape(p.ShapeType.rect, { x: x0, y: y0+2.4, w, h: 1.0, fill: { color: "7E97A6" }, line: { color: WHITE, width: 1 } });
  tb(s, "Mantle — Moho rises under the rift  (+ density → gravity HIGH)", { x: x0+0.12, y: y0+2.55, w: w-0.24, h: 0.5, fontSize: 11, bold: true, color: WHITE, margin: 0 });
  s.addShape(p.ShapeType.line, { x: x0, y: y0+2.4, w: w, h: -0.55, line: { color: RUST, width: 2.5, dashType: "dash" } });
  const rx = 6.9;
  tb(s, "The Kutai paradox", { x: rx, y: 2.2, w: 5.4, h: 0.4, fontSize: 18, bold: true, color: RUST, margin: 0 });
  tb(s, [
    { text: "Kutai holds 10–11 km of sediment — yet its isostatic anomaly is +2.6 mGal (positive).", options: { bullet: true, breakLine: true } },
    { text: "Rifting raises the Moho; the mantle's positive pull cancels the sediment low.", options: { bullet: true, breakLine: true } },
    { text: "Compaction closes the density contrast — only −115 kg/m³ left at 8 km depth.", options: { bullet: true, breakLine: true } },
    { text: "The Indonesian residual field is dominated by plate-boundary & isostatic processes, not sediment.", options: { bullet: true } },
  ], { x: rx, y: 2.7, w: 5.5, h: 3.4, fontSize: 14.5, color: INK, margin: 0, paraSpaceAfter: 11, lineSpacingMultiple: 1.1 });
  caption(s, "A basin low and a rift-raised Moho high partly cancel — gravity is non-unique.", x0, y0+3.5, w);
})();

// ============================================================ 6 LESSON -> SEISMOLOGY
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 1.5, w: 0.26, h: 0.26, fill: { color: MINT } });
  tb(s, "THE LESSON", { x: 1.3, y: 1.46, w: 11, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 2, margin: 0 });
  tb(s, "Gravity alone is non-unique. It needs an independent depth anchor.",
     { x: 0.9, y: 2.0, w: 11.5, h: 1.5, fontSize: 32, bold: true, color: WHITE, fontFace: HSER, margin: 0, lineSpacingMultiple: 1.05 });
  tb(s, "One more caveat: the ESDM 2022 basin outlines already list Badan Geologi gravity as a data source — so gravity outlines are a PRIOR, not an independent check on a gravity inversion.",
     { x: 0.9, y: 3.7, w: 11.4, h: 1.0, fontSize: 15, color: "CADCFC", margin: 0, lineSpacingMultiple: 1.15 });
  tb(s, "That anchor is seismology — the P-to-S conversions recorded at a single station read the layering directly beneath it.",
     { x: 0.9, y: 4.9, w: 11.4, h: 1.0, fontSize: 18, italic: true, color: MINT, margin: 0, lineSpacingMultiple: 1.1 });
})();

// ============================================================ 7 SEISMOLOGY 101
(() => {
  const s = p.addSlide(); head(s, "SEISMOLOGY 101", "A teleseismic P wave converts to S at every interface");
  const x0 = 0.9, yTop = 2.2, w = 6.4;
  const layers = [["Sediment (low Vs)", "C9E5F2", 0.9], ["Crust", "AFC7D6", 1.5], ["Mantle", "7E97A6", 1.2]];
  let y = yTop;
  layers.forEach(([lab, col, h]) => {
    s.addShape(p.ShapeType.rect, { x: x0, y, w, h, fill: { color: col }, line: { color: WHITE, width: 1 } });
    tb(s, lab, { x: x0+0.15, y: y+0.08, w: w-0.3, h: 0.3, fontSize: 12, bold: true, color: INK, margin: 0 });
    y += h;
  });
  s.addShape(p.ShapeType.line, { x: x0+0.6, y: y, w: 2.2, h: -(y-yTop), line: { color: NAVY, width: 2.5, endArrowType: "triangle" } });
  s.addShape(p.ShapeType.line, { x: x0+2.8, y: yTop+2.4, w: 0.9, h: -0.9, line: { color: MINT, width: 2, dashType: "dash", endArrowType: "triangle" } });
  tb(s, "P", { x: x0+0.35, y: y-0.5, w: 0.4, h: 0.3, fontSize: 13, bold: true, color: NAVY, margin: 0 });
  tb(s, "Ps", { x: x0+3.15, y: yTop+1.75, w: 0.6, h: 0.3, fontSize: 13, bold: true, color: "0E8A6E", margin: 0 });
  s.addShape(p.ShapeType.triangle, { x: x0+3.5, y: yTop-0.32, w: 0.5, h: 0.32, fill: { color: "B03030" } });
  tb(s, "station", { x: x0+3.95, y: yTop-0.34, w: 1.2, h: 0.3, fontSize: 11, color: MUT, margin: 0 });
  const rx = 8.0;
  tb(s, "The physics", { x: rx, y: 2.2, w: 4.4, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "A distant M5+ earthquake sends a near-vertical P wave up to the station.", options: { bullet: true, breakLine: true } },
    { text: "At each velocity jump, part of P converts to a slower S wave (a “Ps” phase).", options: { bullet: true, breakLine: true } },
    { text: "Ps delay after P scales with interface depth.", options: { bullet: true, breakLine: true } },
    { text: "Vertical ≈ source; radial carries the conversions.", options: { bullet: true } },
  ], { x: rx, y: 2.65, w: 4.5, h: 3.2, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 10, lineSpacingMultiple: 1.05 });
  tb(s, "Deeper interface → later Ps → structure straight from arrival time.", { x: rx, y: 5.95, w: 4.5, h: 0.7, fontSize: 14, italic: true, color: DEEP, margin: 0 });
})();

// ============================================================ 8 WHAT IS RF
(() => {
  const s = p.addSlide(); head(s, "THE METHOD", "Receiver function = radial deconvolved by vertical");
  tb(s, [
    { text: "RF(t)  =  Radial(t)  ÷  Vertical(t)", options: { bold: true, breakLine: true, fontSize: 20, color: INK } },
    { text: "iterative time-domain deconvolution (Ligorria & Ammon 1999 = CPS saciterd)", options: { fontSize: 12, color: MUT } },
  ], { x: 0.9, y: 2.0, w: 6.4, h: 0.9, margin: 0 });
  tb(s, [
    { text: "Removes the earthquake source & instrument — leaves the site's impulse response.", options: { bullet: true, breakLine: true } },
    { text: "A spike at t = 0 (direct P), then positive pulses at each Ps conversion.", options: { bullet: true, breakLine: true } },
    { text: "Stacking many events per station beats down noise.", options: { bullet: true, breakLine: true } },
    { text: "Gaussian width sets resolution — higher to resolve thin sediment.", options: { bullet: true } },
  ], { x: 0.9, y: 3.0, w: 6.4, h: 3.3, fontSize: 15, color: INK, margin: 0, paraSpaceAfter: 12, lineSpacingMultiple: 1.1 });
  figBox(s, "rf_demo_BI1.png", 7.7, 1.95, 4.9, 4.9);
  caption(s, "Station BI1: individual RFs (red) and their stack (blue).", 7.7, 6.85, 4.9);
})();

// ============================================================ 9 WORKFLOW
(() => {
  const s = p.addSlide(); head(s, "WORKFLOW", "From raw teleseism to a receiver function");
  const steps = [["01","Select events","M≥5, 15–90°, good SNR"],["02","Rotate","N,E → Radial, Transverse"],
    ["03","Deconvolve","Radial ÷ Vertical (iterative)"],["04","Quality control","keep clean, causal RFs"],["05","Stack","average → stable RF"]];
  let x = 0.9; const w = 2.25, gap = 0.19, y = 2.4, h = 2.6;
  steps.forEach(([n,t,d],i)=>{
    s.addShape(p.ShapeType.roundRect,{x,y,w,h,rectRadius:0.08,fill:{color:i%2?TEAL:DEEP}});
    tb(s,n,{x:x+0.2,y:y+0.22,w:w-0.4,h:0.7,fontSize:28,bold:true,color:MINT,fontFace:HSER,margin:0});
    tb(s,t,{x:x+0.2,y:y+1.05,w:w-0.4,h:0.6,fontSize:15,bold:true,color:WHITE,margin:0});
    tb(s,d,{x:x+0.2,y:y+1.62,w:w-0.4,h:0.9,fontSize:11.5,color:"DCEAF0",margin:0,lineSpacingMultiple:1.05});
    if(i<steps.length-1)s.addShape(p.ShapeType.line,{x:x+w+0.01,y:y+h/2,w:gap-0.02,h:0,line:{color:MUT,width:1.5,endArrowType:"triangle"}});
    x+=w+gap;
  });
  tb(s,"MERAMEX 2004: 143 stations · 7 teleseisms (back-azimuth 86–269°) · 106 stations with usable receiver functions.",
     {x:0.9,y:5.4,w:11.5,h:0.8,fontSize:15,color:INK,margin:0});
})();

// ============================================================ 10 FORWARD MODELLING
(() => {
  const s = p.addSlide(); head(s, "FORWARD MODELLING  ·  PEMODELAN MAJU", "Predict the RF a layered earth would produce");
  figBox(s, "fwd_demo_BI1.png", 0.9, 2.0, 7.2, 4.3);
  caption(s, "Observed RF (black) vs Herrmann CPS hrftn96 best-fit synthetic (red) — station BI1.", 0.9, 6.35, 7.2);
  const rx = 8.4;
  tb(s, "hrftn96 (Herrmann CPS)", { x: rx, y: 2.0, w: 4.1, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Input: a velocity model (thickness, Vp, Vs, ρ) + ray parameter + Gaussian.", options: { bullet: true, breakLine: true } },
    { text: "Output: the exact receiver function that model predicts.", options: { bullet: true, breakLine: true } },
    { text: "Forward modelling turns interpretation into a test: does my layered model reproduce the data?", options: { bullet: true, breakLine: true } },
    { text: "It is the engine inside the inversion.", options: { bullet: true } },
  ], { x: rx, y: 2.5, w: 4.2, h: 3.6, fontSize: 14.5, color: INK, margin: 0, paraSpaceAfter: 11, lineSpacingMultiple: 1.1 });
})();

// ============================================================ 11 DEEPER INVERSION
(() => {
  const s = p.addSlide(); head(s, "INVERSION  ·  LAYERED Vs", "Invert the RF for a shear-velocity profile");
  figBox(s, "vs_inversion_BI4.png", 0.9, 2.0, 7.4, 4.3);
  caption(s, "BI4 — damped, smoothed, PREM-constrained least-squares (CPS rftn96 scheme; hrftn96 forward). RMS 0.11.", 0.9, 6.35, 7.4);
  figBox(s, "vs_profiles.png", 8.55, 2.0, 4.0, 4.9);
  caption(s, "Flagship-station Vs profiles (increase with depth).", 8.55, 6.9, 4.0);
})();

// ============================================================ 12 SEDIMENT FROM RF
(() => {
  const s = p.addSlide(); head(s, "SEDIMENT FROM RF", "Reading sediment thickness from the conversion delay");
  card(s, 0.9, 2.05, 5.6, 2.15, "Pick the Ps", "The first strong positive pulse after the direct P is the sediment–basement conversion. Its delay t(Ps) is measured on the stacked RF.", DEEP);
  card(s, 0.9, 4.35, 5.6, 2.15, "Delay → depth", "Move-out:  H = t(Ps) / [√(1/Vs² − p²) − √(1/Vp² − p²)].  Robust for noisy single-station data; Vs 1.5 km/s assumed.", TEAL);
  s.addShape(p.ShapeType.roundRect, { x: 6.9, y: 2.05, w: 5.5, h: 4.45, rectRadius: 0.1, fill: { color: NAVY } });
  tb(s, "Absolute, physical", { x: 7.2, y: 2.3, w: 4.9, h: 0.4, fontSize: 17, bold: true, color: MINT, margin: 0 });
  tb(s, [
    { text: "No density assumption — thickness comes from a measured travel time.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "92 of 106 stations give a resolvable sediment conversion.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Median ≈ 3.5 km; range 1–7 km — consistent with published Central-Java basins.", options: { bullet: true, color: MINT } },
  ], { x: 7.2, y: 2.8, w: 4.9, h: 3.5, fontSize: 15, margin: 0, paraSpaceAfter: 12, lineSpacingMultiple: 1.12 });
})();

// ============================================================ 13 THE EXPERIMENT
(() => {
  const s = p.addSlide(); head(s, "THE EXPERIMENT", "MERAMEX 2004 — a dense passive array over Central Java");
  statRow(s, 2.0, [["143","seismic stations",DEEP],["106","stations with RFs",TEAL],["7","teleseisms",GOLD],["~3.5 km","median sediment",DEEP]]);
  figBox(s, "sediment_rf_map.png", 3.7, 3.95, 5.9, 3.2);
  tb(s, [
    { text: "Merapi Amphibious Experiment (GFZ), May–Oct 2004.", options: { bullet: true, breakLine: true } },
    { text: "Broadband + short-period, ~10–20 km spacing.", options: { bullet: true, breakLine: true } },
    { text: "Public / experiment data — no new acquisition.", options: { bullet: true, breakLine: true } },
    { text: "Volcanic arc (▲) crosses the array.", options: { bullet: true } },
  ], { x: 0.9, y: 4.05, w: 2.55, h: 3.0, fontSize: 12.5, color: INK, margin: 0, paraSpaceAfter: 9 });
})();

// ============================================================ 14 RESULT: sediment map
(() => {
  const s = p.addSlide(); head(s, "RESULT  ·  SEISMOLOGY", "Sediment thickness measured directly at 92 stations");
  figBox(s, "sediment_rf_map.png", 0.9, 1.9, 7.4, 5.0);
  const rx = 8.6;
  tb(s, "What the RFs give", { x: rx, y: 2.1, w: 4.0, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Absolute thickness, no density model.", options: { bullet: true, breakLine: true } },
    { text: "Thick pockets = depocentres; thin = basement / volcanic highs.", options: { bullet: true, breakLine: true } },
    { text: "Geographic context: Merapi, Merbabu, Dieng, Lawu, Muria; Yogyakarta, Semarang, Surakarta.", options: { bullet: true } },
  ], { x: rx, y: 2.55, w: 4.1, h: 3.2, fontSize: 14.5, color: INK, margin: 0, paraSpaceAfter: 11, lineSpacingMultiple: 1.1 });
  tb(s, "This is the anchor gravity was missing.", { x: rx, y: 6.0, w: 4.1, h: 0.7, fontSize: 17, bold: true, italic: true, color: DEEP, margin: 0 });
})();

// ============================================================ 15 GRAVITY CJAVA
(() => {
  const s = p.addSlide(); head(s, "THE OTHER HALF", "Satellite gravity over Central Java — dense but ambiguous");
  figBox(s, "bouguer.png", 0.9, 2.0, 5.7, 4.5);
  figBox(s, "residual.png", 6.75, 2.0, 5.7, 4.5);
  caption(s, "GGM+WGM complete Bouguer anomaly (▲ volcanoes).", 0.9, 6.55, 5.7);
  caption(s, "Residual (40 km high-pass) — basin-scale signal.", 6.75, 6.55, 5.7);
})();

// ============================================================ 16 THE FINDING (CJava)
(() => {
  const s = p.addSlide(); head(s, "THE KEY INSIGHT", "Even in Central Java, gravity alone cannot see the sediment");
  figBox(s, "rf_vs_gravity.png", 0.9, 2.05, 5.2, 4.5);
  const rx = 6.6;
  s.addShape(p.ShapeType.roundRect, { x: rx, y: 2.05, w: 5.8, h: 4.5, rectRadius: 0.1, fill: { color: NAVY } });
  tb(s, "Correlation r ≈ 0.1", { x: rx+0.35, y: 2.35, w: 5.1, h: 0.6, fontSize: 24, bold: true, color: MINT, fontFace: HSER, margin: 0 });
  tb(s, [
    { text: "RF sediment thickness does NOT track the Bouguer residual — same story as the Indonesia-wide inversion.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "Central Java's gravity is dominated by the volcanic arc and basement density.", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "So gravity inversion for sediment is under-determined without depth control...", options: { bullet: true, breakLine: true, color: "E4EEF3" } },
    { text: "...which the receiver functions now supply.", options: { bullet: true, color: MINT } },
  ], { x: rx+0.35, y: 3.05, w: 5.1, h: 3.4, fontSize: 14, margin: 0, paraSpaceAfter: 9, lineSpacingMultiple: 1.08 });
})();

// ============================================================ 17 THE BRIDGE
(() => {
  const s = p.addSlide(); head(s, "THE BRIDGE", "RF-anchored, gravity-contextualised sediment model");
  figBox(s, "sediment_constrained.png", 0.9, 1.95, 7.2, 5.0);
  const rx = 8.4;
  tb(s, "Integration", { x: rx, y: 2.1, w: 4.2, h: 0.4, fontSize: 17, bold: true, color: TEAL, margin: 0 });
  tb(s, [
    { text: "Receiver functions set absolute thickness at ~90 points.", options: { bullet: true, breakLine: true } },
    { text: "Gravity fills the continuous spatial fabric between stations.", options: { bullet: true, breakLine: true } },
    { text: "Collocation ties the map to the seismology.", options: { bullet: true, breakLine: true } },
    { text: "A public-data reconnaissance depth-to-basement model.", options: { bullet: true } },
  ], { x: rx, y: 2.55, w: 4.2, h: 3.3, fontSize: 14.5, color: INK, margin: 0, paraSpaceAfter: 10, lineSpacingMultiple: 1.1 });
})();

// ============================================================ 18 SYNTHESIS (dark, the highlight)
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 0.85, w: 0.24, h: 0.24, fill: { color: MINT } });
  tb(s, "THE SYNTHESIS", { x: 1.28, y: 0.82, w: 11, h: 0.4, fontSize: 14, bold: true, color: MINT, charSpacing: 2, margin: 0 });
  tb(s, "When we have seismology constraints, gravity + seismology is far more powerful",
     { x: 0.9, y: 1.25, w: 11.5, h: 1.3, fontSize: 30, bold: true, color: WHITE, fontFace: HSER, margin: 0, lineSpacingMultiple: 1.03 });
  // two columns: gravity alone vs gravity+seismology
  s.addShape(p.ShapeType.roundRect, { x: 0.9, y: 2.85, w: 5.5, h: 3.6, rectRadius: 0.1, fill: { color: "3A2320" }, line: { color: RUST, width: 1 } });
  tb(s, "Gravity alone", { x: 1.2, y: 3.05, w: 4.9, h: 0.4, fontSize: 18, bold: true, color: "F3B0A0", margin: 0 });
  tb(s, [
    { text: "Non-unique: basin low cancels rift Moho high.", options: { bullet: true, breakLine: true, color: "EAD9D4" } },
    { text: "Indonesia inversion: r = −0.15 vs published thickness.", options: { bullet: true, breakLine: true, color: "EAD9D4" } },
    { text: "Dominated by plate-boundary & isostatic effects.", options: { bullet: true, breakLine: true, color: "EAD9D4" } },
    { text: "Outlines built from gravity aren't an independent check.", options: { bullet: true, color: "EAD9D4" } },
  ], { x: 1.2, y: 3.55, w: 4.9, h: 2.8, fontSize: 13.5, margin: 0, paraSpaceAfter: 9, lineSpacingMultiple: 1.08 });
  s.addShape(p.ShapeType.roundRect, { x: 6.9, y: 2.85, w: 5.5, h: 3.6, rectRadius: 0.1, fill: { color: "12352B" }, line: { color: MINT, width: 1 } });
  tb(s, "Gravity + seismology", { x: 7.2, y: 3.05, w: 4.9, h: 0.4, fontSize: 18, bold: true, color: MINT, margin: 0 });
  tb(s, [
    { text: "RF gives absolute, physical thickness — no density guess.", options: { bullet: true, breakLine: true, color: "DCEFE7" } },
    { text: "Seismology anchors & calibrates the ambiguous gravity field.", options: { bullet: true, breakLine: true, color: "DCEFE7" } },
    { text: "Gravity then interpolates between stations, cheaply and densely.", options: { bullet: true, breakLine: true, color: "DCEFE7" } },
    { text: "Together: a calibrated basin model where neither works alone.", options: { bullet: true, color: MINT } },
  ], { x: 7.2, y: 3.55, w: 4.9, h: 2.8, fontSize: 13.5, margin: 0, paraSpaceAfter: 9, lineSpacingMultiple: 1.08 });
  tb(s, "Central Java is the proof: the RF constraint is exactly what turns gravity from ambiguous into useful.",
     { x: 0.9, y: 6.6, w: 11.5, h: 0.6, fontSize: 15, italic: true, color: "CADCFC", margin: 0 });
  s.addNotes("This is the core message for Pertamina Upstream: don't expect gravity alone to deliver basin geometry in Indonesia; pair it with seismological depth control and it becomes powerful.");
})();

// ============================================================ 19 ROADMAP
(() => {
  const s = p.addSlide(); head(s, "THE ROADMAP", "Scaling the bridge across Indonesia's frontier basins");
  const items = [
    ["Mine passive seismology", "Every temporary/permanent broadband deployment already recorded can yield RF depth control — like MERAMEX here.", DEEP],
    ["Add real ground truth", "MIGAS opens 42,461 wells and 63,691 2-D seismic lines via ArcGIS REST — the true depth-to-basement, still unused.", TEAL],
    ["Terrestrial gravity", "The 2025 Bouguer Anomaly compilation adds resolution satellite gravity cannot.", GOLD],
    ["Joint inversion", "Invert gravity with RF/well depths as hard constraints — basin by basin, nationally.", RUST],
  ];
  let i = 0;
  for (const [h, d, c] of items) {
    const x = i % 2 ? 6.9 : 0.9, y = i < 2 ? 2.05 : 4.35;
    card(s, x, y, 5.5, 2.15, h, d, c); i++;
  }
})();

// ============================================================ 20 CLOSING (dark)
(() => {
  const s = p.addSlide(); bg(s, NAVY);
  s.addShape(p.ShapeType.ellipse, { x: 0.9, y: 2.1, w: 0.3, h: 0.3, fill: { color: MINT } });
  tb(s, "The takeaway", { x: 1.35, y: 2.05, w: 11, h: 0.5, fontSize: 16, bold: true, color: MINT, charSpacing: 2, margin: 0 });
  tb(s, "Where data is scarce, seismology is the bridge — and gravity + seismology beats either alone.",
     { x: 0.9, y: 2.7, w: 11.4, h: 1.8, fontSize: 31, bold: true, color: WHITE, fontFace: HSER, margin: 0, lineSpacingMultiple: 1.05 });
  tb(s, "Receiver functions  +  satellite gravity  +  Herrmann CPS  →  a public-data depth-to-basement model for Central Java, and a template for every frontier basin.",
     { x: 0.9, y: 4.7, w: 11.4, h: 0.9, fontSize: 16, color: "CADCFC", margin: 0, lineSpacingMultiple: 1.15 });
  tb(s, "Terima kasih  ·  Thank you", { x: 0.9, y: 5.9, w: 11.4, h: 0.6, fontSize: 20, bold: true, color: MINT, margin: 0 });
})();

p.writeFile({ fileName: "/Users/maswiet/Work/Students/Pak_Zuhdi/pitch_rf_gravity/RF_Gravity_CentralJava_keynote.pptx" })
 .then(f => console.log("WROTE", f));
