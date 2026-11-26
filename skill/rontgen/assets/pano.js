(() => {
const D = JSON.parse(document.getElementById("pano-data").textContent);
const S = JSON.parse(document.getElementById("pano-strings").textContent);
let L = document.documentElement.lang === "en" ? "en" : "tr";
try { const s = localStorage.getItem("rontgen-pano-lang"); if (s === "tr" || s === "en") L = s; } catch (e) {}
if (location.hash === "#tr" || location.hash === "#en") L = location.hash.slice(1);   // a link that names a language wins
const t = (k) => S[L][k] || k;
const nf = (n) => n == null ? "—" : Number(n).toLocaleString(L === "en" ? "en-US" : "tr-TR");
const NS = "http://www.w3.org/2000/svg";
const el = (tag, attrs, parent) => { const n = document.createElementNS(NS, tag); for (const k in attrs || {}) n.setAttribute(k, attrs[k]); if (parent) parent.append(n); return n; };
const groups = [...new Set(D.modules.map((m) => m.g))].sort((a, b) => D.modules.filter((m) => m.g === b).reduce((s, m) => s + m.lines, 0) - D.modules.filter((m) => m.g === a).reduce((s, m) => s + m.lines, 0));
const col = (g) => { const i = groups.indexOf(g); return i >= 0 && i < 6 ? `var(--c${i})` : "var(--c6)"; };
const GENERIC = new Set(["src", "lib", "test", "tests", "internal", "pkg", "app", "source", "sources", "main", "java", "kotlin", "scripts"]);
const last = (m) => { const p = m.split("/").filter(Boolean); if (!p.length) return m; const z = p[p.length - 1];
  return GENERIC.has(z.toLowerCase()) && p.length > 1 ? p[p.length - 2] + "/" + z : z; };
let sel = "";
const tipOf = (box) => { let tp = box.querySelector(".tip"); if (!tp) { tp = document.createElement("div"); tp.className = "tip"; tp.hidden = true; box.append(tp); } return tp; };
const tip = (box, ev, lines) => { const tp = tipOf(box); tp.replaceChildren(...lines.map((s, i) => { const n = document.createElement(i ? "span" : "b"); n.textContent = s; if (i) n.style.display = "block"; return n; }));
  tp.hidden = false; const r = box.getBoundingClientRect(); tp.style.left = Math.min(ev.clientX - r.left + box.scrollLeft + 12, box.scrollWidth - tp.offsetWidth - 4) + "px"; tp.style.top = (ev.clientY - r.top + 12) + "px"; };
const untip = (box) => { tipOf(box).hidden = true; };
const svgIn = (box, w, h, label) => { box.querySelectorAll("svg").forEach((s) => s.remove()); const s = el("svg", { width: w, height: h, viewBox: `0 0 ${w} ${h}`, role: "img", "aria-label": label }); box.prepend(s); return s; };

function texts() {
  document.documentElement.lang = L;
  document.getElementById("repo").textContent = D.repo;
  document.getElementById("where").textContent = D.measured ? t("measured") + " " + D.measured : "";
  document.title = "Röntgen · " + D.repo;
  document.querySelectorAll("[data-t]").forEach((n) => { n.textContent = t(n.dataset.t); });
  document.querySelectorAll(".sw button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.lang === L)));
}
function tiles() {
  const s = D.summary, box = document.getElementById("tiles");
  box.replaceChildren(...[["files", s.files], ["lines", s.lines], ["modules", s.modules], ["edges", s.edges_k], ["cycles", s.cycles], ["excluded", s.excluded]].map(([k, v]) => {
    const d = document.createElement("div"); d.className = "tile"; const b = document.createElement("b"); b.textContent = nf(v); const sp = document.createElement("span"); sp.textContent = t(k); d.append(b, sp); return d; }));
}
function legend() {
  const box = document.getElementById("legend");
  box.replaceChildren(...groups.slice(0, 7).map((g, i) => { const s = document.createElement("span"); const c = document.createElement("i"); c.style.background = i < 6 ? `var(--c${i})` : "var(--c6)"; s.append(c, document.createTextNode(i < 6 ? g : "…")); return s; }));
  const f = document.getElementById("filter"); f.replaceChildren(new Option(t("all"), ""), ...groups.map((g) => new Option(g, g))); f.value = sel;
}
function order() {
  const box = document.getElementById("order"), O = D.order || [], cov = (D.reading && D.reading.cov && D.reading.cov.modules) || {};
  if (!O.length) { box.replaceChildren(); const li = document.createElement("li"); li.textContent = t("empty"); box.append(li); return; }
  box.replaceChildren(...O.map((x) => {
    const li = document.createElement("li"), b = document.createElement("b"); b.textContent = x.m; li.append(b);
    x.why.split("+").forEach((w) => { const c = document.createElement("span"); c.className = "chip"; c.textContent = t("why_" + w); li.append(c); });
    const st = cov[x.m]; const c = document.createElement("span");
    c.className = "chip" + (st && st.state === "okundu" ? " ok" : st && st.state === "kismen" ? " part" : "");
    c.textContent = st ? t("cov_" + st.state) : t("cov_none"); li.append(c);
    if (x.files.length) {
      const d = document.createElement("details"), s = document.createElement("summary"); s.textContent = t("outline"); d.append(s);
      x.files.forEach((f) => { const p = document.createElement("div"); p.textContent = f.p + " · " + nf(f.lines) + " " + t("lines"); const ul = document.createElement("ul"); ul.className = "outl";
        f.marks.forEach(([ln, k, n]) => { const li2 = document.createElement("li"); li2.textContent = ln + "  " + k + " " + n; ul.append(li2); }); d.append(p, ul); });
      li.append(d);
    }
    return li;
  }));
}
// A share below 0.1% keeps two significant digits: 0.003% must not print as 0%.
function pct(x) { const p = x * 100, o = p > 0 && p < 0.1 ? { maximumSignificantDigits: 2 } : { maximumFractionDigits: 1 };
  return p.toLocaleString(L === "en" ? "en-US" : "tr-TR", o); }
function docs() {
  const box = document.getElementById("docs"), R = D.reading || {}, sub = document.getElementById("docs-sub");
  if (!R.read) { sub.textContent = t("docs_none"); box.replaceChildren(); return; }
  sub.textContent = R.cov && R.cov.share != null ? t("docs_share") + " " + pct(R.cov.share) + "%" : "";
  const parts = [];
  if (R.order.length) { const h = document.createElement("p"); h.textContent = t("docs_order"); const ol = document.createElement("ol"); ol.className = "order";
    R.order.forEach((o) => { const li = document.createElement("li"); li.textContent = o; ol.append(li); }); parts.push(h, ol); }
  R.docs.forEach((x) => { const d = document.createElement("div"); d.className = "doc"; const b = document.createElement("b"); b.textContent = x.title;
    const f = document.createElement("span"); f.className = "chip"; f.textContent = x.f; const p = document.createElement("p"); p.className = "muted"; p.textContent = x.para;
    d.append(b, f, p); parts.push(d); });
  box.replaceChildren(...parts);
}
let showAll = false;
function block() {
  const box = document.getElementById("block"), B0 = D.block, B = { ...B0, edges: showAll ? (B0.edges_all || B0.edges) : B0.edges };
  if (!B.nodes.length) { box.textContent = t("empty"); return; }
  // Boxes in reading order (cycles broken, then topological), B.per_row to a row, each row centred.
  // A link goes down to a later row, arcs over its own row, or, when it runs back, takes a lane on the right.
  const bw = 196, bh = 44, gx = 30, gy = 78, pad = 22, nRows = Math.max(...B.nodes.map((n) => n.row)) + 1;
  const widest = B.per_row * bw + (B.per_row - 1) * gx, P = new Map();
  for (let r = 0; r < nRows; r++) { const ns = B.nodes.filter((n) => n.row === r).sort((p, q) => p.col - q.col), rw = ns.length * bw + (ns.length - 1) * gx;
    ns.forEach((n, i) => P.set(n.m, { ...n, X: pad + (widest - rw) / 2 + i * (bw + gx), Y: pad + 18 + r * (bh + gy) })); }
  const kind = (e) => { const a = P.get(e.a), b = P.get(e.b); return b.o < a.o ? "back" : b.row > a.row ? "down" : "arc"; };
  const back = B.edges.filter((e) => kind(e) === "back");
  const laneX0 = pad + widest + 26, W = laneX0 + back.length * 10 + pad, H = pad * 2 + 18 + nRows * (bh + gy) - gy;
  const s = svgIn(box, W, H, t("block")); s.style.maxWidth = "100%"; s.style.height = "auto"; s.style.margin = "0 auto";
  const mk = el("marker", { id: "ar", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 5, markerHeight: 5, orient: "auto" }, el("defs", {}, s));
  el("path", { d: "M0,0L10,5L0,10z", fill: "var(--axis)" }, mk);
  // one port per link on each edge of a box, ordered by where the other end is, so arrows fan out instead of stacking
  const ports = (side) => { const m = new Map(), by = new Map();
    B.edges.forEach((e) => { const k = kind(e); [["a", "b"], ["b", "a"]].forEach(([me, other]) => {
      const sd = k === "back" ? "right" : k === "arc" ? "top" : me === "a" ? "bottom" : "top";
      if (sd !== side) return; const key = e[me]; if (!by.has(key)) by.set(key, []); by.get(key).push([e, me, other]); }); });
    by.forEach((list, key) => { const n = P.get(key);
      list.sort((p, q) => side === "right" ? P.get(p[0][p[2]]).Y - P.get(q[0][q[2]]).Y : P.get(p[0][p[2]]).X - P.get(q[0][q[2]]).X);
      list.forEach(([e, me], i) => { const f = (i + 1) / (list.length + 1); m.set(e.a + "|" + e.b + "|" + me, side === "right" ? n.Y + 6 + (bh - 12) * f : n.X + 12 + (bw - 24) * f); }); });
    return m; };
  const pb = ports("bottom"), pt = ports("top"), pr = ports("right"), key = (e, me) => e.a + "|" + e.b + "|" + me;
  const path = (e) => { const a = P.get(e.a), b = P.get(e.b), k = kind(e);
    if (k === "down") { const sx = pb.get(key(e, "a")), sy = a.Y + bh, tx = pt.get(key(e, "b")), ty = b.Y - 2, d = ty - sy;
      return `M${sx},${sy} C${sx},${sy + Math.min(40, d / 2)} ${tx},${ty - Math.min(40, d / 2)} ${tx},${ty}`; }
    if (k === "arc") { const sx = pt.get(key(e, "a")), tx = pt.get(key(e, "b")), y0 = a.Y, top = y0 - 14 - Math.min(26, Math.abs(tx - sx) / 12);
      return `M${sx},${y0} C${sx},${top} ${tx},${top} ${tx},${y0 - 2}`; }
    const lx = laneX0 + back.indexOf(e) * 10, ay = pr.get(key(e, "a")), by = pr.get(key(e, "b")), r = 5;
    return `M${a.X + bw},${ay} H${lx - r} Q${lx},${ay} ${lx},${ay - r} V${by + r} Q${lx},${by} ${lx - r},${by} H${b.X + bw + 2}`; };
  const mx = Math.max(1, ...B.edges.map((e) => e.n)), lg = (n) => 1 + 5 * Math.log(1 + n) / Math.log(1 + mx);
  const lines = B.edges.slice().sort((p, q) => p.n - q.n).map((e) => {
    const p = el("path", { d: path(e), fill: "none", stroke: "var(--axis)", "stroke-width": lg(e.n), "marker-end": "url(#ar)", opacity: .55, class: "fade" }, s);
    if (e.t !== "K") p.setAttribute("stroke-dasharray", "5,4");
    p.addEventListener("pointermove", (ev) => tip(box, ev, [e.a + " → " + e.b, nf(e.n) + " " + t("pairs")])); p.addEventListener("pointerleave", () => untip(box)); p._e = e; return p; });
  P.forEach((n) => { const g = el("g", { transform: `translate(${n.X},${n.Y})` }, s);
    el("rect", { width: bw, height: bh, rx: 6, fill: "var(--panel)", stroke: "var(--line)" }, g); el("rect", { width: 5, height: bh, rx: 2, fill: col(n.g) }, g);
    const a = el("text", { x: 12, y: 19, class: "lbl" }, g); const nm = last(n.m); a.textContent = nm.length > 25 ? nm.slice(0, 24) + "…" : nm;
    const b = el("text", { x: 12, y: 35 }, g); b.textContent = n.g + " · " + nf(n.lines) + " " + t("lines");
    g.addEventListener("pointerenter", () => lines.forEach((p) => p.setAttribute("opacity", p._e.a === n.m || p._e.b === n.m ? .95 : .05)));
    g.addEventListener("pointermove", (ev) => tip(box, ev, [n.m, nf(n.lines) + " " + t("lines")]));
    g.addEventListener("pointerleave", () => { lines.forEach((p) => p.setAttribute("opacity", .55)); untip(box); }); });
  const note = document.getElementById("block-note"); if (note) { note.hidden = !B0.dropped || showAll; note.textContent = nf(B0.dropped) + " " + t("dropped"); }
  const sw = document.getElementById("block-all"); if (sw) { sw.parentElement.hidden = !B0.dropped; sw.checked = showAll; }
}
function rows() { return D.modules.filter((m) => !sel || m.g === sel); }
function scatter() {
  const box = document.getElementById("scatter"), R = rows(), W = Math.max(box.clientWidth, 320), H = 340, m = { l: 44, r: 30, t: 30, b: 36 };
  const s = svgIn(box, W, H, t("scatter")); const sl = (v) => Math.log(1 + v);
  const mxX = sl(Math.max(1, ...D.modules.map((r) => r.fo))), mxY = sl(Math.max(1, ...D.modules.map((r) => r.fi))), mxL = Math.max(1, ...D.modules.map((r) => r.lines));
  const X = (v) => m.l + sl(v) / mxX * (W - m.l - m.r), Y = (v) => H - m.b - sl(v) / mxY * (H - m.t - m.b);
  [0, 1, 2, 5, 10, 20, 50, 100, 200, 500].forEach((v) => { if (sl(v) <= mxX) { el("line", { x1: X(v), x2: X(v), y1: m.t, y2: H - m.b, stroke: "var(--grid)" }, s); const tx = el("text", { x: X(v), y: H - m.b + 14, "text-anchor": "middle" }, s); tx.textContent = v; }
    if (sl(v) <= mxY) { el("line", { x1: m.l, x2: W - m.r, y1: Y(v), y2: Y(v), stroke: "var(--grid)" }, s); const ty = el("text", { x: m.l - 6, y: Y(v) + 4, "text-anchor": "end" }, s); ty.textContent = v; } });
  const a = el("text", { x: W - m.r, y: H - 4, "text-anchor": "end" }, s); a.textContent = t("x_out"); const b = el("text", { x: m.l + 4, y: m.t + 10 }, s); b.textContent = t("y_in");
  R.slice().sort((p, q) => q.lines - p.lines).forEach((r) => { const c = el("circle", { cx: X(r.fo), cy: Y(r.fi), r: 2.5 + 22 * Math.sqrt(r.lines / mxL), fill: col(r.g), opacity: .75, stroke: "var(--bg)", "stroke-width": 1.5 }, s);
    c.addEventListener("pointermove", (ev) => tip(box, ev, [r.m, nf(r.lines) + " " + t("lines") + " · " + nf(r.files) + " " + t("files"), t("in") + " " + r.fi + " · " + t("out") + " " + r.fo])); c.addEventListener("pointerleave", () => untip(box)); });
}
function squarify(items, x, y, w, h, out) {
  if (!items.length) return; const total = items.reduce((s, i) => s + i.v, 0); if (total <= 0) return;
  const horiz = w >= h, side = horiz ? h : w; let row = [], best = Infinity, i = 0;
  const worst = (r) => { const s = r.reduce((a, b) => a + b.v, 0) * (w * h) / total, mx = Math.max(...r.map((q) => q.v)) * (w * h) / total, mn = Math.min(...r.map((q) => q.v)) * (w * h) / total; return Math.max(side * side * mx / (s * s), s * s / (side * side * mn)); };
  while (i < items.length) { const nr = row.concat(items[i]), wv = worst(nr); if (row.length && wv > best) break; row = nr; best = wv; i++; }
  const rs = row.reduce((a, b) => a + b.v, 0), thick = rs / total * (horiz ? w : h); let off = 0;
  row.forEach((q) => { const len = q.v / rs * side; out.push(horiz ? { ...q, x, y: y + off, w: thick, h: len } : { ...q, x: x + off, y, w: len, h: thick }); off += len; });
  squarify(items.slice(i), horiz ? x + thick : x, horiz ? y : y + thick, horiz ? w - thick : w, horiz ? h : h - thick, out);
}
function tree() {
  const box = document.getElementById("tree"), W = Math.max(box.clientWidth, 320), H = W < 600 ? 460 : 400, out = [];
  squarify(rows().filter((r) => r.lines > 0).map((r) => ({ v: r.lines, r })).sort((a, b) => b.v - a.v), 0, 0, W, H, out);
  const s = svgIn(box, W, H, t("tree"));
  out.forEach((q) => { const g = el("g", {}, s); const rc = el("rect", { x: q.x + 1, y: q.y + 1, width: Math.max(0, q.w - 2), height: Math.max(0, q.h - 2), rx: 2, fill: col(q.r.g), opacity: .85 }, g);
    if (q.w > 90 && q.h > 22) { const tx = el("text", { x: q.x + 6, y: q.y + 16, fill: "var(--bg)", style: "fill:var(--bg);pointer-events:none" }, g); tx.textContent = last(q.r.m).slice(0, Math.floor(q.w / 7.5)); }
    rc.addEventListener("pointermove", (ev) => tip(box, ev, [q.r.m, nf(q.r.lines) + " " + t("lines") + " · " + nf(q.r.files) + " " + t("files")])); rc.addEventListener("pointerleave", () => untip(box)); });
}
function matrix() {
  const box = document.getElementById("matrix"), M = D.matrix;
  if (!M.cells.length) { box.textContent = t("empty"); return; }
  const n = M.mods.length, ml = 170, mt = 130, cell = Math.max(20, Math.min(44, (Math.max(box.clientWidth, 320) - ml - 12) / n)), W = ml + cell * n + 12, H = mt + cell * n + 8;
  const s = svgIn(box, W, H, t("matrix")), ix = new Map(M.mods.map((m, i) => [m, i])), mx = Math.max(2, ...M.cells.map((c) => c.n));
  M.mods.forEach((m, i) => { const a = el("text", { x: ml - 6, y: mt + i * cell + cell / 2 + 4, "text-anchor": "end" }, s); a.textContent = last(m).slice(0, 22);
    const b = el("text", { transform: `translate(${ml + i * cell + cell / 2 + 4},${mt - 6}) rotate(-50)` }, s); b.textContent = last(m).slice(0, 22);
    M.mods.forEach((_, j) => el("rect", { x: ml + j * cell + 1, y: mt + i * cell + 1, width: cell - 2, height: cell - 2, rx: 3, fill: "var(--grid)" }, s)); });
  M.cells.forEach((c) => { const r = el("rect", { x: ml + ix.get(c.b) * cell + 1, y: mt + ix.get(c.a) * cell + 1, width: cell - 2, height: cell - 2, rx: 3, fill: "var(--c0)", opacity: .15 + .85 * Math.log(c.n) / Math.log(mx) }, s);
    r.addEventListener("pointermove", (ev) => tip(box, ev, [c.a + " → " + c.b, nf(c.n) + " " + t("pairs")])); r.addEventListener("pointerleave", () => untip(box)); });
}
function table(id, head, data) {
  const box = document.getElementById(id); if (data == null) { box.textContent = t(id === "hot" ? "hot_none" : "not_measured"); return; }
  if (!data.length) { box.textContent = t("empty"); return; }
  const tb = document.createElement("table"), tr = document.createElement("tr");
  head.forEach((h) => { const th = document.createElement("th"); th.textContent = t(h); tr.append(th); }); const th_ = document.createElement("thead"); th_.append(tr); tb.append(th_);
  const body = document.createElement("tbody"); data.forEach((r) => { const row = document.createElement("tr"); r.forEach((v, i) => { const td = document.createElement("td"); td.textContent = i ? (typeof v === "number" ? nf(v) : (v ?? "—")) : v; row.append(td); }); body.append(row); });
  tb.append(body); const w = document.createElement("div"); w.className = "tw"; w.append(tb); box.replaceChildren(w);
}
function depth() {
  const box = document.getElementById("depth"), E = D.depth, sub = document.getElementById("depth-sub");
  if (!E) { sub.textContent = ""; box.textContent = t("depth_none"); return; }
  sub.textContent = nf(E.starts) + " " + t(E.from === "giris" ? "depth_from_entry" : "depth_from_root") + " · " + nf(E.reached) + " " + t("depth_reached")
    + " · " + nf(E.unreached) + " " + t("depth_unreached");
  const ks = Object.keys(E.hist).map(Number).sort((a, b) => a - b), mx = Math.max(...ks.map((k) => E.hist[k]));
  const W = Math.max(box.clientWidth, 320), H = 240, m = { l: 52, r: 12, t: 12, b: 32 }, bw = (W - m.l - m.r) / ks.length;
  const s = svgIn(box, W, H, t("depth"));
  [0, .25, .5, .75, 1].forEach((f) => { const y = H - m.b - f * (H - m.t - m.b); el("line", { x1: m.l, x2: W - m.r, y1: y, y2: y, stroke: "var(--grid)" }, s);
    const tx = el("text", { x: m.l - 6, y: y + 4, "text-anchor": "end" }, s); tx.textContent = nf(Math.round(mx * f)); });
  const every = Math.max(1, Math.ceil(ks.length / Math.floor((W - m.l) / 28)));
  ks.forEach((k, i) => { const v = E.hist[k], h = v / mx * (H - m.t - m.b), x = m.l + i * bw + bw * .1;
    const r = el("rect", { x, y: H - m.b - h, width: Math.max(1, bw * .8), height: h, rx: Math.min(4, bw * .3), fill: "var(--c0)" }, s);
    r.addEventListener("pointermove", (ev) => tip(box, ev, [t("step") + " " + k, nf(v) + " " + t("files")])); r.addEventListener("pointerleave", () => untip(box));
    if (i % every === 0) { const tx = el("text", { x: x + bw * .4, y: H - m.b + 14, "text-anchor": "middle" }, s); tx.textContent = k; } });
  const a = el("text", { x: W - m.r, y: H - 2, "text-anchor": "end" }, s); a.textContent = t("step") + " →";
}
function used() {
  const box = document.getElementById("used"), U = D.used; if (!U.length) { box.textContent = t("empty"); return; }
  const W = Math.max(box.clientWidth, 320), H = U.length * 28 + 8, ml = Math.min(W * .5, 260), mx = Math.max(...U.map((u) => u.n));
  const s = svgIn(box, W, H, t("used"));
  U.forEach((u, i) => { const y = 4 + i * 28; const a = el("text", { x: ml - 8, y: y + 15, "text-anchor": "end" }, s); a.textContent = last(u.p).slice(0, 34);
    const w = Math.max(2, (W - ml - 60) * u.n / mx); const r = el("rect", { x: ml, y: y + 3, width: w, height: 18, rx: 4, fill: col(group_of(u.p)) }, s);
    const v = el("text", { x: ml + w + 6, y: y + 16 }, s); v.textContent = nf(u.n);
    r.addEventListener("pointermove", (ev) => tip(box, ev, [u.p, nf(u.n)])); r.addEventListener("pointerleave", () => untip(box)); });
}
function group_of(p) { const q = p.split("/").filter(Boolean); return ["src", "lib", "app", "pkg", "internal"].includes(q[0]) && q.length > 2 ? q[1] : q[0]; }
function trust() {
  const box = document.getElementById("trust"), sec = document.getElementById("trust-sec");
  if (D.trust == null) { sec.hidden = true; return; } sec.hidden = false;
  const ks = Object.keys(D.trust); if (!ks.length) { box.textContent = t("trust_none"); return; }
  table("trust", ["marker", "count"], ks.map((k) => [k, D.trust[k]]));
}
function draw() {
  texts(); tiles(); legend(); order(); docs(); block(); scatter(); tree(); matrix(); depth(); used(); trust();
  if (Object.keys(D.langs).length) table("langs", ["lang", "resolved", "external", "unresolved"], Object.entries(D.langs).map(([k, v]) => [k, v.K, v.dis, v.miss]));
  else document.getElementById("langs").textContent = t("langs_none");
  table("hot", ["file", "commits", "changed", "lines", "people"], D.hot && D.hot.map((h) => [h.p, h.c, h.ch, h.l, h.pp]));
  const more = document.getElementById("more"); more.hidden = !D.modules_cut; more.textContent = nf(D.modules_cut) + " " + t("more");
}
document.querySelectorAll(".sw button").forEach((b) => b.addEventListener("click", () => { L = b.dataset.lang; try { localStorage.setItem("rontgen-pano-lang", L); } catch (e) {} draw(); }));
document.getElementById("block-all").addEventListener("change", (e) => { showAll = e.target.checked; block(); });
document.getElementById("filter").addEventListener("change", (e) => { sel = e.target.value; scatter(); tree(); });
let rt; window.addEventListener("resize", () => { clearTimeout(rt); rt = setTimeout(() => { scatter(); tree(); matrix(); depth(); used(); }, 150); });
draw();
})();
