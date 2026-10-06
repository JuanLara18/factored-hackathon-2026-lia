const pptxgen = require("pptxgenjs");
const React = require("react");
const ReactDOMServer = require("react-dom/server");
const sharp = require("sharp");
const fa = require("react-icons/fa");

const INK = "0B1F2A", GREEN = "0B6E4F", MINT = "9FE0C4", AMBER = "F2A541", LIGHT = "F1F5F4";
const GRAY = "5B6770", WHITE = "FFFFFF", RED = "B5483A", PALE = "DCEFE7", LINE = "C9D3D0";
const FONT = "Calibri";
const W = 13.333, H = 7.5;

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
  t(slide, "LATAM Bank  ·  Factored AI & Data Hackathon 2026", { x: 0.6, y: 7.02, w: 8, h: 0.3, fontSize: 10, color: dark ? "8FA3AD" : GRAY });
  t(slide, n + " / 6", { x: 11.7, y: 7.02, w: 1.03, h: 0.3, fontSize: 10, color: dark ? "8FA3AD" : GRAY, align: "right" });
}

function stat(slide, x, y, w, h, big, label, color) {
  slide.addShape("roundRect", { x, y, w, h, rectRadius: 0.12, fill: { color: LIGHT }, line: { color: LIGHT } });
  t(slide, big, { x: x + 0.25, y: y + 0.18, w: w - 0.5, h: 0.95, fontSize: 44, bold: true, color: color || GREEN });
  t(slide, label, { x: x + 0.25, y: y + 1.15, w: w - 0.5, h: h - 1.25, fontSize: 14, color: GRAY });
}

(async () => {
  const pres = new pptxgen();
  pres.layout = "LAYOUT_WIDE";
  pres.title = "LATAM Bank: AI-first intake of unrecognized card charges";
  pres.author = "Team Lia";

  // ---------- 1. Title
  let s = pres.addSlide();
  s.background = { color: INK };
  t(s, "LATAM Bank", { x: 0.7, y: 1.35, w: 6.6, h: 1.1, fontSize: 60, bold: true, color: WHITE });
  t(s, "AI-first intake of unrecognized card charges", { x: 0.7, y: 2.55, w: 6.4, h: 1.0, fontSize: 26, color: WHITE });
  t(s, "The model understands and writes. Code decides.", { x: 0.7, y: 3.85, w: 6.4, h: 0.5, fontSize: 19, italic: true, color: MINT });
  const pills = [[fa.FaGlobeAmericas, "Spanish + Portuguese"], [fa.FaUserShield, "Human one click away"], [fa.FaCloud, "Live on Google Cloud"]];
  let py = 4.75;
  for (const [ic, label] of pills) {
    await badge(s, ic, 0.7, py, 0.46, GREEN, WHITE);
    t(s, label, { x: 1.32, y: py + 0.08, w: 5, h: 0.35, fontSize: 16, color: WHITE });
    py += 0.6;
  }
  t(s, "latam-bank-hackaton-2026.web.app", { x: 0.7, y: 6.72, w: 6.5, h: 0.35, fontSize: 14, color: "8FA3AD" });
  // chat mock
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

  // ---------- 2. Problem
  s = pres.addSlide();
  title(s, "The top complaint waits 37 hours for a first answer");
  s.addChart(pres.charts.BAR, [{ name: "Complaints", labels: ["No subcategory", "Service quality", "Branch service", "App problem", "Wrong charge", "Unrecognized charge"], values: [6698, 11886, 11892, 12128, 12194, 12297] }], {
    x: 0.5, y: 1.55, w: 6.9, h: 4.9, barDir: "bar", chartColors: [LINE, LINE, LINE, LINE, LINE, GREEN],
    showTitle: true, title: "67,095 complaints by subcategory", titleFontSize: 14, titleColor: INK, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 12, dataLabelFontFace: FONT, dataLabelFormatCode: "#,##0",
    catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT, valAxisHidden: true, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: false, barGapWidthPct: 45,
  });
  stat(s, 7.85, 1.55, 2.35, 2.25, "18.3%", "of complaints are unrecognized charges");
  stat(s, 10.4, 1.55, 2.35, 2.25, "37 h", "median first response");
  stat(s, 7.85, 4.0, 2.35, 2.25, "24.5%", "closed or resolved");
  stat(s, 10.4, 4.0, 2.35, 2.25, "20.4%", "breach the SLA", RED);
  t(s, "Fraud is contained in minutes, not days. One focused workflow: dispute intake. Source: 686,296 contacts from 148,443 customers.", { x: 0.6, y: 6.5, w: 12.1, h: 0.4, fontSize: 13, color: GRAY });
  foot(s, 2);

  // ---------- 3. Solution
  s = pres.addSlide();
  title(s, "The model talks. Policy as code acts");
  const nodes = [
    [fa.FaUser, "Customer", "Banking web and chat"],
    [fa.FaShieldAlt, "Channel", "Session, on-screen approval, output filter"],
    [fa.FaRobot, "Agent", "Gemini + 8 typed tools"],
    [fa.FaBalanceScale, "Policy v1", "Versioned rules outside the prompt"],
    [fa.FaDatabase, "Data", "BigQuery gold, Firestore cases"],
  ];
  let nx = 0.75;
  for (let i = 0; i < nodes.length; i++) {
    const [ic, name, sub] = nodes[i];
    await badge(s, ic, nx + 0.55, 1.55, 1.1, i === 3 ? AMBER : GREEN, i === 3 ? INK : WHITE);
    t(s, name, { x: nx, y: 2.8, w: 2.2, h: 0.35, fontSize: 17, bold: true, align: "center" });
    t(s, sub, { x: nx, y: 3.18, w: 2.2, h: 0.6, fontSize: 12.5, color: GRAY, align: "center" });
    if (i < nodes.length - 1) s.addShape("rightArrow", { x: nx + 1.95, y: 1.95, w: 0.5, h: 0.3, fill: { color: LINE }, line: { color: LINE } });
    nx += 2.42;
  }
  const paths = [
    [fa.FaCheckCircle, GREEN, WHITE, "Normal", "Server pins the charge. Nothing runs until the customer approves on screen."],
    [fa.FaQuestionCircle, AMBER, INK, "Ambiguous or unsupported", "Asks which charge. Policy answers only with a cited source. Abstains on credit."],
    [fa.FaUserTie, INK, WHITE, "Needs a human", "19-field handoff package. AI copilot drafts, the expert edits and sends."],
  ];
  let cx = 0.6;
  for (const [ic, bg, fg, head, body] of paths) {
    s.addShape("roundRect", { x: cx, y: 4.2, w: 3.9, h: 2.45, rectRadius: 0.12, fill: { color: LIGHT }, line: { color: LIGHT } });
    await badge(s, ic, cx + 0.25, 4.42, 0.62, bg, fg);
    t(s, head, { x: cx + 1.05, y: 4.55, w: 2.7, h: 0.4, fontSize: 17, bold: true });
    t(s, body, { x: cx + 0.25, y: 5.25, w: 3.4, h: 1.3, fontSize: 14, color: GRAY });
    cx += 4.1;
  }
  foot(s, 3);

  // ---------- 4. Data and ML
  s = pres.addSlide();
  title(s, "A tested data pipeline and three models, each against a baseline");
  const layers = [["Bronze", "13 raw tables", "B08D57"], ["Silver", "Typed, PII pseudonymized", "8A9BA8"], ["Gold", "8 contracts, no PII", "D9A400"], ["Platinum", "Lineage and quality", "5C6F7B"]];
  let ly = 1.6;
  for (let i = 0; i < layers.length; i++) {
    const [name, sub, col] = layers[i];
    s.addShape("roundRect", { x: 0.6, y: ly, w: 4.3, h: 0.85, rectRadius: 0.1, fill: { color: col }, line: { color: col } });
    t(s, name, { x: 0.85, y: ly + 0.22, w: 1.6, h: 0.4, fontSize: 18, bold: true, color: WHITE });
    t(s, sub, { x: 2.3, y: ly + 0.27, w: 2.5, h: 0.35, fontSize: 13, color: WHITE });
    if (i < layers.length - 1) s.addShape("downArrow", { x: 2.6, y: ly + 0.88, w: 0.3, h: 0.22, fill: { color: LINE }, line: { color: LINE } });
    ly += 1.13;
  }
  const chips = [[fa.FaVial, "56 dbt tests"], [fa.FaLink, "Manifest"], [fa.FaSyncAlt, "Update fixture"]];
  let chx = 0.6;
  for (const [ic, label] of chips) {
    await badge(s, ic, chx, 6.2, 0.42, PALE, GREEN);
    t(s, label, { x: chx + 0.5, y: 6.28, w: 1.2, h: 0.3, fontSize: 11.5, color: INK });
    chx += 1.48;
  }
  s.addChart(pres.charts.BAR, [
    { name: "Learned component", labels: ["Policy retrieval (accuracy)", "Contact reason (macro-F1)", "SLA risk (AUC)"], values: [0.9, 0.4, 0.5] },
    { name: "Baseline", labels: ["Policy retrieval (accuracy)", "Contact reason (macro-F1)", "SLA risk (AUC)"], values: [0.52, 0.34, 0.5] },
  ], {
    x: 5.4, y: 1.5, w: 7.4, h: 4.2, barDir: "col", barGrouping: "clustered", chartColors: [GREEN, LINE],
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 13, dataLabelFontFace: FONT, dataLabelFormatCode: "0.00",
    catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT, valAxisHidden: true, valAxisMaxVal: 1, valGridLine: { style: "none" }, catGridLine: { style: "none" },
    showLegend: true, legendPos: "t", legendFontSize: 13, legendFontFace: FONT, legendColor: INK, barGapWidthPct: 60,
  });
  t(s, [
    { text: "In the workflow: ", options: { bold: true, color: GREEN } },
    { text: "retrieval cites the policy rule or says it does not know. 0 false citations on 15 uncovered questions.  " },
    { text: "Negative result reported: ", options: { bold: true, color: RED } },
    { text: "the SLA model has no signal, so it always abstains." },
  ], { x: 5.5, y: 5.85, w: 7.2, h: 0.95, fontSize: 13.5, color: GRAY });
  foot(s, 4);

  // ---------- 5. Evaluation
  s = pres.addSlide();
  title(s, "Zero unsafe outcomes in 96 runs, and an honest baseline");
  stat(s, 0.6, 1.5, 2.9, 2.05, "0 / 96", "unsafe outcomes. Bounds the risk at 4%, does not prove zero");
  stat(s, 3.7, 1.5, 2.9, 2.05, "81%", "safe automated resolution on resolvable cases (29 of 36)");
  stat(s, 6.8, 1.5, 2.9, 2.05, "1.4 s", "median agent turn. p95 4.6 s");
  stat(s, 9.9, 1.5, 2.85, 2.05, "$0.002", "model cost per attempted case");
  s.addChart(pres.charts.BAR, [{ name: "Runs passing every check", labels: ["Rules baseline", "AI agent"], values: [91, 80] }], {
    x: 0.5, y: 3.85, w: 5.6, h: 2.95, barDir: "bar", chartColors: [LINE, GREEN],
    showTitle: true, title: "Runs passing every check (%)", titleFontSize: 13, titleColor: INK, titleFontFace: FONT,
    showValue: true, dataLabelPosition: "outEnd", dataLabelColor: INK, dataLabelFontSize: 13, dataLabelFontFace: FONT,
    catAxisLabelColor: INK, catAxisLabelFontSize: 13, catAxisLabelFontFace: FONT, valAxisHidden: true, valAxisMaxVal: 110, valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, barGapWidthPct: 50,
  });
  t(s, "Rules follow policy as well as the agent. The agent adds language, conversation and coverage. Four defects found, fixed in the tool layer.", { x: 6.5, y: 3.95, w: 6.2, h: 1.0, fontSize: 14.5, color: INK });
  const tested = [[fa.FaClock, "Expired session"], [fa.FaUserSecret, "Unauthorized access"], [fa.FaSyringe, "Prompt injection"], [fa.FaPlug, "Tool outage"], [fa.FaQuestion, "Missing data"], [fa.FaLanguage, "Mixed languages"]];
  for (let i = 0; i < tested.length; i++) {
    const x = 6.5 + (i % 3) * 2.1, y = 5.15 + Math.floor(i / 3) * 0.82;
    await badge(s, tested[i][0], x, y, 0.5, PALE, GREEN);
    t(s, tested[i][1], { x: x + 0.6, y: y + 0.03, w: 1.45, h: 0.5, fontSize: 12.5, color: INK, valign: "middle" });
  }
  foot(s, 5);

  // ---------- 6. Operation
  s = pres.addSlide();
  s.background = { color: INK };
  title(s, "Live today, and clear about what is missing", true);
  t(s, "IN PLACE", { x: 0.7, y: 1.55, w: 5.6, h: 0.35, fontSize: 14, bold: true, color: MINT, charSpacing: 3 });
  t(s, "BEFORE REAL OPERATION", { x: 7.0, y: 1.55, w: 5.6, h: 0.35, fontSize: 14, bold: true, color: AMBER, charSpacing: 3 });
  const ok = [[fa.FaCloud, "End to end on Google Cloud", "81 browser tests pass in production"], [fa.FaRoute, "Tracing without message content", "Explanations from sources, rules and records"], [fa.FaLifeRing, "Bounded retries, safe fallback", "Handoff works without the model"], [fa.FaLock, "Least privilege and secrets", "30-day retention, alerts, Terraform"]];
  const todo = [[fa.FaFlask, "All results are offline", "Synthetic data, simulated customer"], [fa.FaLanguage, "Portuguese not native-reviewed", "No Brazilian accounts in the data"], [fa.FaServer, "One instance, no load test", "Sessions still in memory"], [fa.FaPhoneAlt, "Voice and WhatsApp", "Designed, not deployed"]];
  for (let i = 0; i < 4; i++) {
    const y = 2.15 + i * 1.08;
    await badge(s, ok[i][0], 0.7, y, 0.7, GREEN, WHITE);
    t(s, ok[i][1], { x: 1.6, y: y + 0.02, w: 4.9, h: 0.36, fontSize: 17, bold: true, color: WHITE });
    t(s, ok[i][2], { x: 1.6, y: y + 0.4, w: 4.9, h: 0.32, fontSize: 13, color: "B8C6CC" });
    await badge(s, todo[i][0], 7.0, y, 0.7, AMBER, INK);
    t(s, todo[i][1], { x: 7.9, y: y + 0.02, w: 4.8, h: 0.36, fontSize: 17, bold: true, color: WHITE });
    t(s, todo[i][2], { x: 7.9, y: y + 0.4, w: 4.8, h: 0.32, fontSize: 13, color: "B8C6CC" });
  }
  t(s, "latam-bank-hackaton-2026.web.app   ·   /banca/ for the customer   ·   /operador/ for the human expert", { x: 0.7, y: 6.5, w: 12, h: 0.35, fontSize: 13, color: MINT });
  foot(s, 6, true);

  await pres.writeFile({ fileName: process.argv[2] });
  console.log("ok", process.argv[2]);
})();
