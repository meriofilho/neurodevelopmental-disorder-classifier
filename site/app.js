/* Relatório — gráficos interativos (SVG puro), navegação e tema. */
(() => {
  "use strict";
  const NS = "http://www.w3.org/2000/svg";
  const fmt = (v) => v.toFixed(v >= 0.995 && v < 1 ? 3 : 2).replace(".", ",");

  const MODELOS = [
    { k: "log", nome: "Regressão logística", cor: "--s-log" },
    { k: "tree", nome: "Árvore de decisão", cor: "--s-tree" },
    { k: "rf", nome: "Random Forest", cor: "--s-rf" },
    { k: "xgb", nome: "XGBoost", cor: "--s-xgb" },
  ];

  /* ---------------- dados (notebooks 01–06) ---------------- */
  const PRINCIPAL = {
    tea: {
      titulo: "TEA × Controle · ABIDE I · 732 sujeitos, 17 instituições",
      cats: ["Fenótipo", "Conectividade", "Fusão precoce", "Fusão tardia"],
      acc: {
        "Fenótipo": { log: .594, tree: .573, rf: .580, xgb: .561 },
        "Conectividade": { log: .641, tree: .552, rf: .610, xgb: .639 },
        "Fusão precoce": { log: .646, tree: .585, rf: .623, xgb: .648 },
        "Fusão tardia": { log: .662, tree: .585, rf: .610, xgb: .644 },
      },
      auc: {
        "Fenótipo": { log: .62, tree: .59, rf: .61, xgb: .59 },
        "Conectividade": { log: .69, tree: .57, rf: .67, xgb: .69 },
        "Fusão precoce": { log: .69, tree: .60, rf: .69, xgb: .71 },
        "Fusão tardia": { log: .71, tree: .61, rf: .65, xgb: .69 },
      },
    },
    tdah: {
      titulo: "TDAH × Controle · ADHD-200 · 853 sujeitos, 7 instituições",
      cats: ["Fenótipo", "Conectividade", "Fusão precoce", "Fusão tardia"],
      acc: {
        "Fenótipo": { log: .574, tree: .544, rf: .524, xgb: .523 },
        "Conectividade": { log: .502, tree: .499, rf: .493, xgb: .475 },
        "Fusão precoce": { log: .502, tree: .531, rf: .507, xgb: .484 },
        "Fusão tardia": { log: .520, tree: .506, rf: .521, xgb: .507 },
      },
      auc: {
        "Fenótipo": { log: .59, tree: .52, rf: .54, xgb: .51 },
        "Conectividade": { log: .49, tree: .51, rf: .49, xgb: .45 },
        "Fusão precoce": { log: .49, tree: .53, rf: .51, xgb: .48 },
        "Fusão tardia": { log: .53, tree: .51, rf: .53, xgb: .49 },
      },
    },
  };

  const FENO3 = {
    cats: ["Acurácia balanceada", "Sens. TEA", "Sens. TDAH", "Sens. Controle"],
    acc: {
      "Acurácia balanceada": { log: .378, tree: .396, rf: .383, xgb: .374 },
      "Sens. TEA": { log: .392, tree: .319, rf: .402, xgb: .371 },
      "Sens. TDAH": { log: .251, tree: .297, rf: .214, xgb: .204 },
      "Sens. Controle": { log: .491, tree: .573, rf: .532, xgb: .546 },
    },
  };

  const SITIO = {
    cats: ["TDAH · bruto", "TDAH · padronizado", "TDAH · padronizado, sem 2 sítios", "TEA · bruto", "TEA · padronizado"],
    acc: {
      "TDAH · bruto": { log: .453, tree: .446, rf: .454, xgb: .448 },
      "TDAH · padronizado": { log: .502, tree: .499, rf: .493, xgb: .475 },
      "TDAH · padronizado, sem 2 sítios": { log: .534, tree: .503, rf: .524, xgb: .507 },
      "TEA · bruto": { log: .641, tree: .527, rf: .610, xgb: .627 },
      "TEA · padronizado": { log: .645, tree: .552, rf: .610, xgb: .639 },
    },
  };

  const VIES = [
    { g: "feno", rot: "Fenótipo · todas as idades", v: .60 },
    { g: "feno", rot: "Fenótipo · 7–21 anos", v: .55 },
    { g: "feno", rot: "Fenótipo · 4 instituições compartilhadas", v: .64 },
    { g: "feno", rot: "Fenótipo · após pareamento sexo × idade", v: .42 },
    { g: "conn", rot: "Conectividade · bruta", v: .999 },
    { g: "conn", rot: "Conectividade · 4 instituições compartilhadas", v: 1.0 },
    { g: "conn", rot: "Conectividade · normalizada por sujeito", v: .998 },
  ];

  /* ---------------- utilidades ---------------- */
  const el = (tag, attrs = {}, parent) => {
    const n = document.createElementNS(NS, tag);
    for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
    if (parent) parent.appendChild(n);
    return n;
  };
  const txt = (parent, x, y, s, cls, anchor = "middle") => {
    const t = el("text", { x, y, "text-anchor": anchor, class: cls || "" }, parent);
    t.textContent = s;
    return t;
  };
  const cor = (v) => `var(${v})`;

  function legenda(box, series, comAcaso) {
    box.replaceChildren();
    for (const s of series) {
      const sp = document.createElement("span");
      const i = document.createElement("i");
      i.style.background = cor(s.cor);
      sp.append(i, document.createTextNode(s.nome));
      box.append(sp);
    }
    if (comAcaso) {
      const sp = document.createElement("span");
      const i = document.createElement("i");
      i.className = "line";
      sp.append(i, document.createTextNode(comAcaso));
      box.append(sp);
    }
  }

  function tooltip(chart) {
    let t = chart.querySelector(".tip");
    if (!t) { t = document.createElement("div"); t.className = "tip"; t.setAttribute("role", "status"); chart.append(t); }
    return {
      show(ev, linhas, alvo) {
        t.replaceChildren();
        const v = document.createElement("div"); v.className = "tv"; v.textContent = linhas.valor;
        const k = document.createElement("div"); k.className = "tk";
        const i = document.createElement("i"); i.style.borderColor = linhas.cor;
        k.append(i, document.createTextNode(linhas.serie));
        t.append(v, k);
        for (const extra of linhas.extras || []) {
          const x = document.createElement("div"); x.className = "tx"; x.textContent = extra; t.append(x);
        }
        const cr = chart.getBoundingClientRect();
        let x, y;
        if (ev && ev.clientX) { x = ev.clientX - cr.left; y = ev.clientY - cr.top; }
        else { const r = alvo.getBoundingClientRect(); x = r.left - cr.left + r.width / 2; y = r.top - cr.top; }
        t.style.opacity = 1;
        const w = t.offsetWidth, h = t.offsetHeight;
        t.style.left = Math.max(0, Math.min(cr.width - w, x - w / 2)) + "px";
        t.style.top = Math.max(-10, y - h - 14) + "px";
      },
      hide() { t.style.opacity = 0; },
    };
  }

  function tabela(box, cats, series, dados, extraFn) {
    box.replaceChildren();
    const wrap = document.createElement("div"); wrap.className = "table-wrap";
    const tb = document.createElement("table");
    const th = tb.createTHead().insertRow();
    const c0 = document.createElement("th"); c0.textContent = ""; th.append(c0);
    for (const s of series) { const c = document.createElement("th"); c.className = "n"; c.textContent = s.nome; th.append(c); }
    const body = tb.createTBody();
    for (const cat of cats) {
      const r = body.insertRow();
      const a = r.insertCell(); a.textContent = cat;
      for (const s of series) {
        const c = r.insertCell(); c.className = "n";
        const v = dados[cat][s.k];
        c.textContent = fmt(v) + (extraFn ? extraFn(cat, s.k) : "");
      }
    }
    wrap.append(tb); box.append(wrap);
  }

  /* ---------------- barras agrupadas (verticais) ---------------- */
  function barrasAgrupadas(root, cfg) {
    const chart = root.querySelector(".chart");
    const W = 880, H = cfg.altura || 360, m = { t: 26, r: 58, b: 54, l: 44 };
    const iw = W - m.l - m.r, ih = H - m.t - m.b;
    const yMin = cfg.yMin, yMax = cfg.yMax;
    const y = (v) => m.t + ih - ((v - yMin) / (yMax - yMin)) * ih;
    chart.querySelector("svg")?.remove();
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": cfg.aria });
    chart.prepend(svg);
    const tip = tooltip(chart);

    // grade e eixo
    const ax = el("g", { class: "ax" }, svg);
    for (let v = yMin; v <= yMax + 1e-9; v += cfg.passo) {
      el("line", { x1: m.l, x2: W - m.r, y1: y(v), y2: y(v), class: "gl" }, ax);
      txt(ax, m.l - 8, y(v) + 4, fmt(v), "", "end");
    }
    const nC = cfg.cats.length, nS = MODELOS.length;
    const gw = iw / nC, inner = gw * 0.78, bw = (inner - (nS - 1) * 2) / nS;
    cfg.cats.forEach((cat, ci) => {
      const x0 = m.l + ci * gw + (gw - inner) / 2;
      const linhas = cat.split("\n");
      linhas.forEach((ln, li) => txt(svg, m.l + ci * gw + gw / 2, H - m.b + 20 + li * 15, ln, "cat"));
      MODELOS.forEach((s, si) => {
        const v = cfg.dados[cat][s.k];
        const x = x0 + si * (bw + 2);
        const yv = y(Math.max(v, yMin)), y0 = y(yMin);
        const g = el("g", { class: "bar", tabindex: 0, role: "img",
          "aria-label": `${cat.replace("\n", " ")}, ${s.nome}: ${fmt(v)}` }, svg);
        g.dataset.serie = s.k;
        // barra com topo arredondado (4px) ancorada na base
        const h = Math.max(0, y0 - yv), r = Math.min(4, bw / 2, h);
        el("path", {
          class: "m", fill: cor(s.cor),
          d: `M${x},${y0} V${yv + r} Q${x},${yv} ${x + r},${yv} H${x + bw - r} Q${x + bw},${yv} ${x + bw},${yv + r} V${y0} Z`,
        }, g);
        el("rect", { x: x - 1, y: m.t, width: bw + 2, height: ih, fill: "transparent" }, g); // área de toque maior
        if (cfg.rotular !== false) {
          const t = txt(g, x + bw / 2, yv - 6, fmt(v), "vl");
          if (bw < 34) { t.setAttribute("font-size", "9.5"); }
        }
        const info = () => ({ valor: fmt(v), serie: s.nome, cor: getComputedStyle(document.documentElement).getPropertyValue(s.cor),
          extras: [cat.replace("\n", " "), ...(cfg.extras ? cfg.extras(cat, s.k) : [])] });
        g.addEventListener("pointermove", (e) => tip.show(e, info(), g));
        g.addEventListener("pointerleave", () => tip.hide());
        g.addEventListener("focus", () => tip.show(null, info(), g));
        g.addEventListener("blur", () => tip.hide());
      });
    });
    el("line", { x1: m.l, x2: W - m.r, y1: y(yMin), y2: y(yMin), class: "base" }, svg);
    if (cfg.acaso != null) {
      el("line", { x1: m.l, x2: W - m.r, y1: y(cfg.acaso), y2: y(cfg.acaso), class: "ch" }, svg);
      txt(svg, W - m.r + 6, y(cfg.acaso) - 2, "acaso", "ch-l", "start");
      txt(svg, W - m.r + 6, y(cfg.acaso) + 11, fmt(cfg.acaso), "ch-l", "start");
    }
    legenda(root.querySelector(".legend"), MODELOS, cfg.acaso != null ? "acaso" : null);
    tabela(root.querySelector(".tbl-view"), cfg.cats.map((c) => c), MODELOS,
      Object.fromEntries(cfg.cats.map((c) => [c, cfg.dados[c]])),
      cfg.extrasTabela);
  }

  /* ---------------- barras horizontais (viés) ---------------- */
  function barrasHorizontais(root) {
    const chart = root.querySelector(".chart");
    const W = 880, lh = 40, m = { t: 14, r: 64, b: 30, l: 300 };
    const H = m.t + m.b + VIES.length * lh;
    const iw = W - m.l - m.r;
    const x = (v) => m.l + v * iw;
    const svg = el("svg", { viewBox: `0 0 ${W} ${H}`, role: "group", "aria-label": "Acurácia para prever a base de origem entre controles" });
    chart.prepend(svg);
    const tip = tooltip(chart);
    const ax = el("g", { class: "ax" }, svg);
    for (let v = 0; v <= 1.0001; v += 0.25) {
      el("line", { x1: x(v), x2: x(v), y1: m.t, y2: H - m.b, class: "gl" }, ax);
      txt(ax, x(v), H - m.b + 18, fmt(v));
    }
    const grupos = { feno: { nome: "Fenótipo (idade, sexo, QI)", cor: "--s-feno" }, conn: { nome: "Conectividade (AAL)", cor: "--s-conn" } };
    VIES.forEach((d, i) => {
      const yy = m.t + i * lh + 8, bh = lh - 16;
      txt(svg, m.l - 12, yy + bh / 2 + 4, d.rot, "", "end");
      const g = el("g", { class: "bar", tabindex: 0, role: "img", "aria-label": `${d.rot}: ${fmt(d.v)}` }, svg);
      const w = x(d.v) - m.l, r = Math.min(4, bh / 2);
      el("path", { class: "m", fill: cor(grupos[d.g].cor),
        d: `M${m.l},${yy} H${m.l + w - r} Q${m.l + w},${yy} ${m.l + w},${yy + r} V${yy + bh - r} Q${m.l + w},${yy + bh} ${m.l + w - r},${yy + bh} H${m.l} Z` }, g);
      el("rect", { x: m.l, y: yy - 4, width: iw, height: bh + 8, fill: "transparent" }, g);
      txt(g, m.l + w + 8, yy + bh / 2 + 4, fmt(d.v), "vl", "start");
      const info = () => ({ valor: fmt(d.v), serie: grupos[d.g].nome, cor: getComputedStyle(document.documentElement).getPropertyValue(grupos[d.g].cor), extras: [d.rot.split(" · ")[1], "acurácia balanceada; acaso = 0,50"] });
      g.addEventListener("pointermove", (e) => tip.show(e, info(), g));
      g.addEventListener("pointerleave", () => tip.hide());
      g.addEventListener("focus", () => tip.show(null, info(), g));
      g.addEventListener("blur", () => tip.hide());
    });
    el("line", { x1: x(.5), x2: x(.5), y1: m.t - 6, y2: H - m.b, class: "ch" }, svg);
    txt(svg, x(.5) + 4, m.t - 2, "acaso 0,50", "ch-l", "start");
    legenda(root.querySelector(".legend"), Object.values(grupos), "acaso");
    const box = root.querySelector(".tbl-view");
    const wrap = document.createElement("div"); wrap.className = "table-wrap";
    const tb = document.createElement("table");
    const h = tb.createTHead().insertRow();
    for (const [c, n] of [["Cenário (só controles)", ""], ["Acurácia balanceada", "n"]]) { const t = document.createElement("th"); t.textContent = c; if (n) t.className = n; h.append(t); }
    const b = tb.createTBody();
    for (const d of VIES) { const r = b.insertRow(); r.insertCell().textContent = d.rot; const c = r.insertCell(); c.className = "n"; c.textContent = fmt(d.v); }
    wrap.append(tb); box.append(wrap);
  }

  /* ---------------- ligar gráficos ---------------- */
  function alternarTabela(root) {
    const btn = root.querySelector(".linkbtn"), box = root.querySelector(".tbl-view");
    if (!btn) return;
    box.hidden = true;
    btn.addEventListener("click", () => {
      box.hidden = !box.hidden;
      btn.textContent = box.hidden ? "Ver como tabela" : "Ocultar tabela";
      btn.setAttribute("aria-expanded", String(!box.hidden));
    });
  }

  function principal() {
    const root = document.getElementById("g-principal");
    if (!root) return;
    const desenhar = (tarefa) => {
      const d = PRINCIPAL[tarefa];
      root.querySelector(".chart-sub").textContent = d.titulo;
      barrasAgrupadas(root, {
        cats: d.cats, dados: d.acc, yMin: 0.3, yMax: 0.75, passo: 0.05, acaso: 0.5,
        aria: `Acurácia balanceada por conjunto de features e modelo, ${d.titulo}`,
        extras: (c, k) => [`AUC ${fmt(d.auc[c][k])}`],
        extrasTabela: (c, k) => ` (AUC ${fmt(d.auc[c][k])})`,
      });
    };
    root.querySelectorAll(".seg button").forEach((b) => b.addEventListener("click", () => {
      root.querySelectorAll(".seg button").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
      desenhar(b.dataset.tarefa);
    }));
    alternarTabela(root);
    desenhar("tea");
  }

  function feno3() {
    const root = document.getElementById("g-feno3");
    if (!root) return;
    barrasAgrupadas(root, { cats: FENO3.cats, dados: FENO3.acc, yMin: 0, yMax: 0.6, passo: 0.1, acaso: 1 / 3, altura: 330,
      aria: "Desempenho com fenótipo, três classes, por métrica e modelo" });
    alternarTabela(root);
  }

  function sitio() {
    const root = document.getElementById("g-sitio");
    if (!root) return;
    const cats = SITIO.cats.map((c) => c.replace(" · ", "\n"));
    const dados = Object.fromEntries(SITIO.cats.map((c) => [c.replace(" · ", "\n"), SITIO.acc[c]]));
    barrasAgrupadas(root, { cats, dados, yMin: 0.3, yMax: 0.7, passo: 0.1, acaso: 0.5, altura: 350,
      aria: "Efeito da padronização por instituição, por cenário e modelo" });
    alternarTabela(root);
  }

  function vies() {
    const root = document.getElementById("g-vies");
    if (!root) return;
    barrasHorizontais(root);
    alternarTabela(root);
  }

  /* ---------------- navegação, tema, menu ---------------- */
  function scrollspy() {
    const links = [...document.querySelectorAll(".nav a[href^='#']")];
    const mapa = new Map(links.map((a) => [a.getAttribute("href").slice(1), a]));
    const obs = new IntersectionObserver((entradas) => {
      for (const e of entradas) {
        if (e.isIntersecting) {
          links.forEach((a) => a.classList.remove("ativo"));
          mapa.get(e.target.id)?.classList.add("ativo");
        }
      }
    }, { rootMargin: "-35% 0px -60% 0px" });
    mapa.forEach((_, id) => { const s = document.getElementById(id); if (s) obs.observe(s); });
  }

  function tema() {
    const btn = document.getElementById("btn-tema");
    const salvo = localStorage.getItem("tema");
    if (salvo) document.documentElement.dataset.theme = salvo;
    const atual = () => document.documentElement.dataset.theme ||
      (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    const rot = () => { btn.textContent = atual() === "dark" ? "☀ Tema claro" : "☾ Tema escuro"; };
    rot();
    btn.addEventListener("click", () => {
      const novo = atual() === "dark" ? "light" : "dark";
      document.documentElement.dataset.theme = novo;
      localStorage.setItem("tema", novo);
      rot();
    });
  }

  function menu() {
    const sb = document.querySelector(".sidebar"), b = document.getElementById("btn-menu");
    if (!b) return;
    b.addEventListener("click", () => { const ab = sb.classList.toggle("aberta"); b.setAttribute("aria-expanded", String(ab)); });
    sb.querySelectorAll("a").forEach((a) => a.addEventListener("click", () => sb.classList.remove("aberta")));
  }

  document.addEventListener("DOMContentLoaded", () => {
    principal(); feno3(); sitio(); vies(); scrollspy(); tema(); menu();
  });
})();
