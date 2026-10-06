const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const INK = "0B1F2A", GREEN = "0B6E4F", MINT = "9FE0C4", AMBER = "F2A541", LIGHT = "F1F5F4";
const GRAY = "5B6770", WHITE = "FFFFFF", RED = "B5483A", PALE = "DCEFE7", LINE = "C9D3D0", SOFT = "8FA3AD";
const FONT = "Calibri";

async function icon(Comp, color) {
  const svg = ReactDOMServer.renderToStaticMarkup(React.createElement(Comp, { color: "#" + color, size: 256 }));
  const buf = await sharp(Buffer.from(svg)).resize(256, 256, { fit: "contain", background: { r: 0, g: 0, b: 0, alpha: 0 } }).png().toBuffer();
  return "image/png;base64," + buf.toString("base64");
}
function t(slide, text, o) {
  slide.addText(text, { fontFace: FONT, color: INK, margin: 0, isTextBox: true, valign: "top", ...o });
}
async function badge(slide, Comp, x, y, d, bg, fg) {
  slide.addShape("ellipse", { x, y, w: d, h: d, fill: { color: bg }, line: { color: bg } });
  const p = d * 0.26;
  slide.addImage({ data: await icon(Comp, fg), x: x + p, y: y + p, w: d - 2 * p, h: d - 2 * p });
}
function title(slide, text, dark) {
  t(slide, text, { x: 0.6, y: 0.45, w: 12.1, h: 0.8, fontSize: 32, bold: true, color: dark ? WHITE : INK });
}
function foot(slide, n, dark) {
  t(slide, "LATAM Bank  ·  Factored AI & Data Hackathon 2026", { x: 0.6, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: dark ? SOFT : GRAY });
  t(slide, n + " / 6", { x: 11.7, y: 7.02, w: 1.03, h: 0.3, fontSize: 10, color: dark ? SOFT : GRAY, align: "right" });
}
function tile(slide, x, y, w, h, big, label, color, bigSize) {
  slide.addShape("roundRect", { x, y, w, h, rectRadius: 0.12, fill: { color: LIGHT }, line: { color: LIGHT } });
  t(slide, big, { x: x + 0.25, y: y + 0.15, w: w - 0.5, h: 0.9, fontSize: bigSize || 40, bold: true, color: color || GREEN });
  t(slide, label, { x: x + 0.25, y: y + 1.05, w: w - 0.5, h: h - 1.1, fontSize: 13.5, color: GRAY });
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "LATAM Bank: the bank that keeps its word";
  pres.author = "Team Lia";

  // ---------- 1. Hook
  let s = pres.addSlide();
  s.background = { color: INK };
  t(s, "We didn't build a chatbot.", { x: 0.7, y: 1.5, w: 6.7, h: 0.8, fontSize: 38, color: WHITE });
  t(s, "We built a bank.", { x: 0.7, y: 2.3, w: 6.7, h: 1.2, fontSize: 64, bold: true, color: MINT });
  t(s, "LATAM Bank keeps its word to every customer, by design.", { x: 0.7, y: 3.95, w: 6.3, h: 0.9, fontSize: 22, color: WHITE });
  const pills = [[fa.FaHandshake, "Five promises, enforced in code"], [fa.FaUsers, "Run like a bank: owners, debate, audit"], [fa.FaCloud, "Live today, in Spanish and Portuguese"]];
  let py = 5.05;
  for (const [ic, label] of pills) {
    await badge(s, ic, 0.7, py, 0.46, GREEN, WHITE);
    t(s, label, { x: 1.32, y: py + 0.08, w: 5.6, h: 0.35, fontSize: 16, color: WHITE });
    py += 0.58;
  }
  s.addShape("roundRect", { x: 7.75, y: 0.75, w: 4.85, h: 6.0, rectRadius: 0.2, fill: { color: WHITE }, line: { color: WHITE }, shadow: { type: "outer", color: "000000", opacity: 0.35, blur: 14, offset: 4, angle: 90 } });
  await badge(s, fa.FaRobot, 8.05, 1.0, 0.55, GREEN, WHITE);
  t(s, "Lía", { x: 8.75, y: 1.0, w: 3, h: 0.32, fontSize: 16, bold: true });
  t(s, "AI assistant, always disclosed", { x: 8.75, y: 1.3, w: 3.6, h: 0.28, fontSize: 11, color: GRAY });
  s.addShape("roundRect", { x: 9.35, y: 1.95, w: 2.95, h: 0.62, rectRadius: 0.14, fill: { color: PALE }, line: { color: PALE } });
  t(s, "No reconozco este cargo", { x: 9.5, y: 2.1, w: 2.7, h: 0.35, fontSize: 13 });
  s.addShape("roundRect", { x: 8.05, y: 2.8, w: 3.5, h: 0.95, rectRadius: 0.14, fill: { color: LIGHT }, line: { color: LIGHT } });
  t(s, "Encontré el cargo: 152.000 COP en Super Norte, el 2 de octubre.", { x: 8.2, y: 2.9, w: 3.25, h: 0.8, fontSize: 13 });
  s.addShape("roundRect", { x: 8.05, y: 4.0, w: 4.25, h: 1.75, rectRadius: 0.14, fill: { color: WHITE }, line: { color: GREEN, width: 1.5 } });
  t(s, "Abrir reclamo", { x: 8.25, y: 4.12, w: 3.8, h: 0.32, fontSize: 14, bold: true });
  t(s, "152.000 COP · tarjeta terminada en 0001", { x: 8.25, y: 4.45, w: 3.9, h: 0.3, fontSize: 11.5, color: GRAY });
  s.addShape("roundRect", { x: 8.25, y: 4.95, w: 1.9, h: 0.55, rectRadius: 0.1, fill: { color: GREEN }, line: { color: GREEN } });
  t(s, "Confirmar", { x: 8.25, y: 5.08, w: 1.9, h: 0.3, fontSize: 14, bold: true, color: WHITE, align: "center" });
  s.addShape("roundRect", { x: 10.3, y: 4.95, w: 1.8, h: 0.55, rectRadius: 0.1, fill: { color: WHITE }, line: { color: LINE } });
  t(s, "Cancelar", { x: 10.3, y: 5.08, w: 1.8, h: 0.3, fontSize: 14, color: GRAY, align: "center" });
  await badge(s, fa.FaUserTie, 8.05, 6.0, 0.42, AMBER, INK);
  t(s, "Hablar con una persona", { x: 8.6, y: 6.08, w: 3.5, h: 0.3, fontSize: 13, color: INK });

  // ---------- 2. The broken promise
  s = pres.addSlide();
  title(s, "The promise banks break every day");
  s.addShape("roundRect", { x: 0.6, y: 1.5, w: 5.4, h: 3.3, rectRadius: 0.14, fill: { color: "F8ECEA" }, line: { color: "F8ECEA" } });
  t(s, "TODAY", { x: 0.95, y: 1.72, w: 4, h: 0.3, fontSize: 13, bold: true, color: RED, charSpacing: 3 });
  t(s, "37 hours", { x: 0.95, y: 2.1, w: 4.8, h: 1.3, fontSize: 80, bold: true, color: RED });
  t(s, "for a first answer after a customer reports a charge they never made", { x: 0.95, y: 3.6, w: 4.7, h: 0.9, fontSize: 16, color: INK });
  s.addShape("rightArrow", { x: 6.2, y: 2.85, w: 0.9, h: 0.6, fill: { color: LINE }, line: { color: LINE } });
  s.addShape("roundRect", { x: 7.3, y: 1.5, w: 5.4, h: 3.3, rectRadius: 0.14, fill: { color: PALE }, line: { color: PALE } });
  t(s, "WITH LATAM BANK", { x: 7.65, y: 1.72, w: 4.5, h: 0.3, fontSize: 13, bold: true, color: GREEN, charSpacing: 3 });
  t(s, "Seconds", { x: 7.65, y: 2.1, w: 4.8, h: 1.3, fontSize: 80, bold: true, color: GREEN });
  t(s, "Lía finds the charge and proposes the claim. 95% of answers in under 5 seconds, measured offline", { x: 7.65, y: 3.6, w: 4.7, h: 0.9, fontSize: 16, color: INK });
  tile(s, 0.6, 5.05, 3.9, 1.7, "#1 complaint", "Unrecognized charges: 12,297 of 67,095 complaints", INK, 30);
  tile(s, 4.72, 5.05, 3.9, 1.7, "3 in 4", "of those complaints are still open", RED, 30);
  tile(s, 8.84, 5.05, 3.86, 1.7, "Minutes", "is how fast fraud moves. Trust is lost in hours", INK, 30);
  foot(s, 2);

  // ---------- 3. Built like a bank
  s = pres.addSlide();
  title(s, "We ran it like a bank: owners, debate, a record");
  await badge(s, fa.FaLandmark, 3.55, 1.45, 1.0, INK, WHITE);
  t(s, "Presidency", { x: 2.8, y: 2.5, w: 2.5, h: 0.35, fontSize: 16, bold: true, align: "center" });
  s.addShape("line", { x: 4.05, y: 2.9, w: 0, h: 0.35, line: { color: LINE, width: 1.5 } });
  s.addShape("line", { x: 1.2, y: 3.25, w: 5.7, h: 0, line: { color: LINE, width: 1.5 } });
  const vps = [[fa.FaHeart, "Customers"], [fa.FaRobot, "AI"], [fa.FaDatabase, "Data"], [fa.FaServer, "Technology"], [fa.FaBalanceScale, "Governance"]];
  for (let i = 0; i < vps.length; i++) {
    const x = 0.75 + i * 1.425;
    s.addShape("line", { x: x + 0.45, y: 3.25, w: 0, h: 0.25, line: { color: LINE, width: 1.5 } });
    await badge(s, vps[i][0], x, 3.5, 0.9, GREEN, WHITE);
    t(s, vps[i][1], { x: x - 0.3, y: 4.5, w: 1.5, h: 0.3, fontSize: 13.5, bold: true, align: "center" });
  }
  await badge(s, fa.FaSearch, 5.95, 1.5, 0.9, AMBER, INK);
  t(s, "Independent Audit", { x: 5.35, y: 2.5, w: 2.1, h: 0.35, fontSize: 14, bold: true, align: "center" });
  s.addShape("line", { x: 4.6, y: 1.95, w: 1.3, h: 0, line: { color: AMBER, width: 1.5, dashType: "dash" } });
  s.addShape("roundRect", { x: 0.6, y: 5.2, w: 6.9, h: 1.5, rectRadius: 0.12, fill: { color: LIGHT }, line: { color: LIGHT } });
  t(s, "Governance challenged the design. Audit reviewed it cold. Every vice presidency owns its folder, its rules and its tests.", { x: 0.85, y: 5.4, w: 6.4, h: 1.2, fontSize: 15, color: INK });
  tile(s, 8.0, 1.45, 2.25, 1.65, "21", "research studies before writing code");
  tile(s, 10.45, 1.45, 2.25, 1.65, "34", "decisions, each with its reason");
  tile(s, 8.0, 3.3, 2.25, 1.65, "10", "architecture decision records");
  tile(s, 10.45, 3.3, 2.25, 1.65, "66", "sources tracked by Audit");
  s.addShape("roundRect", { x: 8.0, y: 5.2, w: 4.7, h: 1.5, rectRadius: 0.12, fill: { color: INK }, line: { color: INK } });
  t(s, "The disagreements are in the repository, not hidden behind the demo.", { x: 8.25, y: 5.45, w: 4.2, h: 1.1, fontSize: 15, color: WHITE, italic: true });
  foot(s, 3);

  // ---------- 4. Five promises
  s = pres.addSlide();
  title(s, "Five promises a bank can actually keep");
  const promesas = [
    [fa.FaHandPointer, "Nothing without your yes", "Every action waits for your approval on screen"],
    [fa.FaUserLock, "Only your data", "Other customers do not exist for your session"],
    [fa.FaUserTie, "A person, whenever you ask", "With your whole story. You never repeat it"],
    [fa.FaBookOpen, "Answers with a source", "Policy cited by rule, or an honest “I don't know”"],
    [fa.FaCheckDouble, "Only what was verified", "It reports what the system actually did"],
  ];
  for (let i = 0; i < promesas.length; i++) {
    const x = 0.6 + i * 2.46;
    s.addShape("roundRect", { x, y: 1.5, w: 2.28, h: 3.75, rectRadius: 0.14, fill: { color: LIGHT }, line: { color: LIGHT } });
    await badge(s, promesas[i][0], x + 0.64, 1.8, 1.0, GREEN, WHITE);
    t(s, String(i + 1), { x: x + 0.15, y: 1.6, w: 0.4, h: 0.4, fontSize: 16, bold: true, color: SOFT });
    t(s, promesas[i][1], { x: x + 0.18, y: 3.05, w: 1.92, h: 0.8, fontSize: 17, bold: true, align: "center" });
    t(s, promesas[i][2], { x: x + 0.18, y: 3.95, w: 1.92, h: 1.15, fontSize: 13, color: GRAY, align: "center" });
  }
  s.addShape("roundRect", { x: 0.6, y: 5.55, w: 12.12, h: 1.15, rectRadius: 0.12, fill: { color: INK }, line: { color: INK } });
  await badge(s, fa.FaCode, 0.9, 5.82, 0.62, MINT, INK);
  t(s, "Enforced in code and versioned policy, not in a prompt. A prompt injection cannot break them.", { x: 1.75, y: 5.93, w: 10.7, h: 0.45, fontSize: 19, bold: true, color: WHITE });
  foot(s, 4);

  // ---------- 5. Architecture
  s = pres.addSlide();
  title(s, "Under the hood: the model talks, policy as code acts");
  function caja(x, y, w, h, color, head, sub, fg) {
    s.addShape("roundRect", { x, y, w, h, rectRadius: 0.1, fill: { color }, line: { color } });
    t(s, head, { x: x + 0.2, y: y + 0.12, w: w - 0.4, h: 0.32, fontSize: 15, bold: true, color: fg || INK });
    t(s, sub, { x: x + 0.2, y: y + 0.46, w: w - 0.4, h: h - 0.5, fontSize: 11.5, color: fg ? "D5E2E0" : GRAY });
  }
  function flecha(x, y) { s.addShape("downArrow", { x, y, w: 0.3, h: 0.24, fill: { color: LINE }, line: { color: LINE } }); }
  caja(0.6, 1.45, 3.75, 0.95, PALE, "Online banking and chat", "Firebase Hosting. Lía, always disclosed as AI");
  caja(4.55, 1.45, 3.75, 0.95, PALE, "Expert console + AI copilot", "19-field handoff, drafted reply, human sends");
  flecha(2.3, 2.43); flecha(6.3, 2.43);
  caja(0.6, 2.7, 7.7, 0.95, LIGHT, "Channel service on Cloud Run", "Trusted session, one-time on-screen approval, output filter, bounded retries");
  flecha(4.3, 3.68);
  caja(0.6, 3.95, 3.75, 1.15, GREEN, "Agent on Agent Runtime", "Gemini 3.1 Flash-Lite, 8 typed tools. The customer comes from the session, never from the model", WHITE);
  caja(4.55, 3.95, 3.75, 1.15, AMBER, "Policy v1 as code", "Escalation, auth level per action, provisional credit. Versioned and hashed");
  flecha(2.3, 5.13); flecha(6.3, 5.13);
  caja(0.6, 5.4, 4.75, 1.35, INK, "BigQuery: bronze, silver, gold, platinum", "19M rows, dbt with 56 tests, data contracts, hashed lineage, PII pseudonymized, freshness fixture", WHITE);
  caja(5.55, 5.4, 2.75, 1.35, INK, "Firestore", "Cases and handoffs, 30-day retention", WHITE);
  t(s, "MACHINE LEARNING, EACH VS A BASELINE", { x: 8.75, y: 1.45, w: 4, h: 0.3, fontSize: 11.5, bold: true, color: GREEN, charSpacing: 2 });
  const ml = [[fa.FaSearch, "Policy retrieval with citation", "0.90 vs 0.52 (BM25). In the workflow"], [fa.FaTags, "Contact-reason classifier", "macro-F1 0.40 vs 0.34 (rules)"], [fa.FaChartLine, "SLA-breach risk", "No signal (AUC 0.50). Reported, abstains"]];
  for (let i = 0; i < ml.length; i++) {
    const y = 1.85 + i * 0.82;
    await badge(s, ml[i][0], 8.75, y, 0.55, GREEN, WHITE);
    t(s, ml[i][1], { x: 9.45, y: y + 0.0, w: 3.3, h: 0.3, fontSize: 14, bold: true });
    t(s, ml[i][2], { x: 9.45, y: y + 0.3, w: 3.3, h: 0.3, fontSize: 11.5, color: GRAY });
  }
  t(s, "OPERATIONS", { x: 8.75, y: 4.45, w: 4, h: 0.3, fontSize: 11.5, bold: true, color: GREEN, charSpacing: 2 });
  const ops = [[fa.FaRoute, "Tracing without message content"], [fa.FaLock, "Least privilege, Secret Manager"], [fa.FaBell, "Uptime check and alerts, Terraform"], [fa.FaVial, "588 unit + 81 browser tests in CI"]];
  for (let i = 0; i < ops.length; i++) {
    const y = 4.85 + i * 0.5;
    await badge(s, ops[i][0], 8.75, y, 0.4, PALE, GREEN);
    t(s, ops[i][1], { x: 9.3, y: y + 0.06, w: 3.5, h: 0.3, fontSize: 13, color: INK });
  }
  foot(s, 5);

  // ---------- 6. Proof
  s = pres.addSlide();
  title(s, "We tried to break it. Then we published the results");
  s.addChart(pres.charts.BAR, [
    { name: "LATAM Bank assistant", labels: ["Dispute flow", "Policy, follow-up, multi-request"], values: [92, 82] },
    { name: "Rules engine", labels: ["Dispute flow", "Policy, follow-up, multi-request"], values: [87, 38] },
  ], {
    x: 0.5, y: 1.45, w: 6.5, h: 4.0, barDir: "col", barGrouping: "clustered", chartColors: [GREEN, LINE],
    showTitle: true, title: "Test runs passing every check (%), fresh held-out set", titleFontSize: 13, titleColor: INK, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 14, dataLabelFontFace: FONT,
    catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT, valAxisHidden: true, valAxisMaxVal: 110, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "t", legendFontSize: 13, legendFontFace: FONT, legendColor: INK, barGapWidthPct: 60,
  });
  tile(s, 7.4, 1.45, 2.55, 1.9, "89%", "of 129 runs pass. Rules engine: 72%");
  tile(s, 10.15, 1.45, 2.55, 1.9, "0", "actions without approval, in 225 runs");
  tile(s, 7.4, 3.55, 2.55, 1.9, "0 / 18", "missed handoffs to a person");
  tile(s, 10.15, 3.55, 2.55, 1.9, "1", "real flaw in 129 runs. Found and published", RED);
  s.addShape("roundRect", { x: 0.6, y: 5.65, w: 12.12, h: 1.15, rectRadius: 0.12, fill: { color: INK }, line: { color: INK } });
  const cambios = [[fa.FaUser, "Customers: 37 hours to seconds"], [fa.FaUserTie, "Experts: the full picture, drafted"], [fa.FaLandmark, "The bank: auditable policy"]];
  for (let i = 0; i < cambios.length; i++) {
    const x = 0.9 + i * 4.0;
    await badge(s, cambios[i][0], x, 5.93, 0.58, i === 2 ? AMBER : GREEN, i === 2 ? INK : WHITE);
    t(s, cambios[i][1], { x: x + 0.72, y: 6.05, w: 3.2, h: 0.35, fontSize: 15, bold: true, color: WHITE });
  }
  t(s, "LATAM Bank  ·  Live today: latam-bank-hackaton-2026.web.app  ·  Offline measurements on synthetic data", { x: 0.6, y: 7.02, w: 10.5, h: 0.3, fontSize: 10, color: GRAY });
  t(s, "6 / 6", { x: 11.7, y: 7.02, w: 1.03, h: 0.3, fontSize: 10, color: GRAY, align: "right" });

  await pres.writeFile({ fileName: process.argv[2] });
  console.log("ok", process.argv[2]);
})();
