#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- the yapi.md report, written from yapi.py's result.

Split out of yapi.py when it reached its 600-line budget: measuring and
writing are separate jobs, and a second report language (F3-AIL-06) needs the
words in one place. yapi.py still owns the measurement and the self-test.
"""
from __future__ import annotations

import json
import os
import re

import c_dili
from ortak import excluded_lines, thresholds_line


def node_id(name: str) -> str:
    return "m_" + re.sub(r"\W", "_", name)


def render(r: dict, max_edges: int, sources: dict, cfg: dict) -> str:
    o = [f"# Yapi — {os.path.basename(r['repo'])}", "",
         "Koddan uretildi; elle cizilmedi. **Duz ok `[K]`**: depoda cozulen beyan edilmis bagimlilik (import, proje basvurusu,",
         "[K] kazanmis sonda). **Kesik ok `[H]`**: tek bir dosyada tanimli bir adin ayni dil ailesinden baska bir dosyada gecmesi —",
         "vekildir: yaygin bir sozcuk sahte ok uretir, yansima ve bagimlilik enjeksiyonu hic ok uretmez.", "",
         "- Ayarlar: " + thresholds_line(cfg, sources, ("module_depth", "weak_edge")), "",
         "## Olcume girmeyenler", ""] + excluded_lines(r["excluded"]) + ["", "## Blok semasi", "", "```mermaid", "flowchart LR"]
    drawn = [e for e in r["edges"] if not e["weak"]][:max_edges]
    used = {e["from"] for e in drawn} | {e["to"] for e in drawn}
    for m, v in r["modules"].items():
        if m in used:
            o.append(f'  {node_id(m)}["{m if m != "." else "(kok dizin)"}<br/>{v["files"]} dosya · {v["lines"]} satir'
                     + (f' · {v["kaynak_disi"]} kaynak disi' if v.get("kaynak_disi") else "") + '"]')
    for e in drawn:
        o.append(f'  {node_id(e["from"])} {"-->" if e["tier"] == "K" else "-.->"}|{e["files"]}| {node_id(e["to"])}')
    c = r["edge_counts"]
    o += ["```", "", f"Cizilen {len(drawn)} bag. Toplam: [K] {c['K']}, [H] {c['H']}, **zayif [H] {c['H_weak']}** "
          f"({r['weak_edge']} dosya ciftinden azina dayanan; cizilmedi, donguye katilmadi). Ok ustundeki sayi: dosya cifti.", ""]
    weak = [e for e in r["edges"] if e["weak"]]
    if weak:
        o += ["Zayif baglar (dogrulanmadan bag sayilmaz): "
              + "; ".join(f"{e['from']} → {e['to']} ({e['files']})" for e in weak[:12]) + (" …" if len(weak) > 12 else ""), ""]

    def table(head, rows):
        o.append("| " + " | ".join(head) + " |"); o.append("|" + "---|" * len(head))
        o.extend("| " + " | ".join(str(x) for x in row) + " |" for row in rows)
        o.append("")

    o += ["## Moduller", "", "Giren: bu module yaslanan modul sayisi; cikan: yaslandigi modul sayisi. [K] ve [H] ayri sayilir.", ""]
    table(["Modul", "Dosya", "Satir", "Giren K", "Giren H", "Cikan K", "Cikan H"],
          [(m + (f" (+{v['kaynak_disi']} kaynak disi)" if v.get("kaynak_disi") else ""), v["files"], v["lines"],
            r["fan"][m]["in_k"], r["fan"][m]["in_h"], r["fan"][m]["out_k"], r["fan"][m]["out_h"])
           for m, v in r["modules"].items()])
    o += ["## Donguler", ""]
    o += ([f"- `[K]` {' ↔ '.join(g)}" for g in r["cycles"]] or ["Beyan edilmis bagimliliklarda (`[K]`) modul dongusu yok."]) + [""]
    if r["cycle_candidates"]:
        o += ["Aday donguler — yalniz `[H]` baglarla kapanir; **dogrulanmadan dongu denmez**:"]
        o += [f"- `[H]` {' ↔ '.join(g['modules'])} (en ince bagi {g['thinnest']} dosya cifti)" for g in r["cycle_candidates"]] + [""]

    o += ["## Kor noktalar — sonda adaylari", "",
          "Bu betiklerin izleyemedigi mekanizmalarin kodda ne kadar gectigi. Bir sayi buyukse o mekanizmanin arkasindaki baglar",
          "semada **yoktur**. Projeye ozgu bir sonda ancak buradaki bir bosluk icin yazilir (sonda.py).", ""]
    if r["blind_spots"]:
        table(["Mekanizma", "Dosya", "Isabet", "En yogun"],
              [(k, v["files"], v["hits"], ", ".join(f"`{p}` ({n})" for p, n in v["top"][:3])) for k, v in r["blind_spots"].items()])
    else:
        o += ["Taninan bir kor nokta kalibi bulunmadi (kaliplarin tanimadigi mekanizmalar olabilir).", ""]
    if r["probes"]:
        o += ["Yuklenen sonda sonuclari:"]
        o += [f"- `{p['sonda']}` [{p['tier']}] — {p['edges']} dosya bagi, {p['accepted']} kabul, commit `{p['commit']}`, oz-test {p['oz_test']}"
              + (f"; ucu kaynak disi dosyada (kabul): {p['outside_count']}" if p["outside_count"] else "")
              + (f"; **ucu dislanan dosyada (red) {p['excluded_count']}**: {', '.join(p['excluded_files'])}" if p["excluded_count"] else "")
              + (f"; **{p['unknown_count']} bilinmeyen dosya yolu yok sayildi**: {', '.join(p['unknown_files'])}" if p["unknown_count"] else "")
              for p in r["probes"]] + [""]

    o += c_dili.render(r["c"]) if r["c"] else []
    for key, title, roots in (("rust", "Rust `mod` / `use`", "crate'ler"), ("go", "Go `import`", "moduller (go.mod)"),
                              ("java", "Java/Kotlin `import`", "kaynak kokleri"),
                              ("ozel", "Projeye ozgu dil (config) `import`", "diller")):
        rn = r.get(key)
        o += ([f"## {title} baglari", "", f"{rn['files']} dosya, {roots}: {', '.join(rn['crates']) or 'bildirim bulunamadi'}. "
              f"`[K]` cozulen: {rn['uses']['K']} (dosya bagi {rn['file_edges']}); depo disi (dis, bag yok): {rn['uses']['dis']}; "
              f"**cozulemeyen** (kor nokta): {rn['uses']['cozulemeyen']}."]
              + ([f"Cozulemeyen ornekleri: " + "; ".join(f"`{x}`" for x in rn["uses"]["ornek"])] if rn["uses"].get("ornek") else []) + [""]
              if rn else [])
    o += ["## En cok yaslanilan dosyalar `[H]`", ""]
    table(["Dosya", "Yaslanan dosya"], [(x["path"], x["used_by"]) for x in r["most_used_files"]] or [("-", "-")])
    e = r["entry"]
    o += ["## Giris yuzeyi `[H]`", "", f"- Kalipla taninan **{e['route_count']} HTTP ucu** "
          f"({e.get('route_test', 0)} tanesi test dosyalarinda); baslangic noktasi sayilan dosyalar: "
          + (", ".join(f"`{m}`" for m in e["mains"][:10]) or "bulunamadi") + (" …" if len(e["mains"]) > 10 else ""),
          "- Giris islevleri (`main` kalipla: C her yerde, Rust yalniz ikili hedefte; digerleri yalniz config `entry_points` adiyla): "
          + (", ".join(f"`{x['name']}` `{x['path']}:{x['line']}` ({x['source']})" for x in e["functions"][:12]) or "yok")
          + (f" … ve {len(e['functions']) - 12} tane daha (`yapi.json`)" if len(e["functions"]) > 12 else "")
          + (f"; **config'te adi olup bulunamayan: {', '.join(e['missing'])}**" if e["missing"] else ""), ""]
    if e["routes_by_file"]:
        table(["Dosya", "Uc"], list(e["routes_by_file"].items())[:10])
        table(["Yol oneki", "Uc"], list(e["routes_by_prefix"].items()))
    s = r["stores"]
    o += ["## Veri depolari `[H]`", "",
          f"SQL ya da ORM'de tanimli {s['tables']} tablo. **Yazan**: INSERT / UPDATE / DELETE ifadesinde; **okuyan**: FROM / JOIN ifadesinde;",
          "**tirnakli**: yalniz tirnak icinde adi gecen (ad kodla kurulan sorguya veriliyor olabilir). Adi duz yazida ya da sutun",
          "basligi olarak gecen dosya sayilmaz. Sorgu metni parcalardan kuruluyorsa eksik sayar.", ""]
    table(["Tablo", "Tanim", "Yazan", "Okuyan", "Tirnakli"],
          [(t, v["declared_in"], len(v["written_by"]), len(v["read_by"]), len(v["quoted_in"])) for t, v in list(s["by_table"].items())[:30]]
          or [("-", "-", "-", "-", "-")])
    if s["unmentioned"]:
        o += [f"Hicbir kod dosyasinda gecmeyen {len(s['unmentioned'])} tablo (olu yuzey adayi; kanit degil): "
              + ", ".join(s["unmentioned"][:40]) + (" …" if len(s["unmentioned"]) > 40 else ""), ""]
    o += ["## En buyuk dosyalarin iskeleti", "",
          "Satir numarali bildirimler ve uclar. Tipler ve Python / TS islevleri `[K]`; C# yontemleri kalipla taninir `[H]`",
          "(niteleyicisiz yerel islevler ve ifade govdeli uyeler kacabilir). C / C++ islev ve tipleri kalipla taninir `[H]`;",
          "makroyla uretilen tanimlar aranmaz.", ""]
    for p, v in r["outline"].items():
        o.append(f"### `{p}` — {v['lines']} satir, {len(v['marks'])} bildirim")
        if not v["marks"]:
            o += ["", "Bildirim bulunamadi: iskelet **olculmedi**.", ""]
            continue
        o.append("")
        o.extend(f"{'  ' * min(m['depth'], 4)}- {m['line']}: {m['kind']} `{m['name']}`" for m in v["marks"][:80])
        if len(v["marks"]) > 80:
            o.append(f"- … {len(v['marks']) - 80} bildirim daha (yapi.json)")
        o.append("")
    return "\n".join(o) + "\n"
