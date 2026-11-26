---
title: "Röntgen — examples / örnekler"
description: "Röntgen's one-page output on three real codebases: Lean 4, Rust and Go."
---

# Röntgen

<div id="pane-en" markdown="1">

## See it on real code

Each page below is one `pano.html` exactly as `pano.py` wrote it: one file, no network, a TR / EN switch. They carry
counts and module and file names, never source code, and each project keeps its own licence.

| Project | Language | Size | Page |
|---|---|---|---|
| riemann-lean | Lean 4 | 175,187 files, 17.5 million lines | [open →](ornekler/riemann-lean.html) |
| helix | Rust | 296 files | [open →](ornekler/helix.html) |
| esbuild | Go | 196 files | [open →](ornekler/esbuild.html) |

The Lean page maps the structure of a release that claims a proof of the Riemann Hypothesis, and carries three reading
rounds: about 950 lines from `Main.lean` down to the Galois row and the proof of the window bound, six module notes (in
Turkish), every sentence cited. A blind second reader held 11 of 12 for round 1; rounds 2 and 3 are not yet checked. It says nothing about whether the proof holds.

The same output is made for any repository with `python scripts/pano.py --docs rontgen-out --repo .` after `yapi.py`
(and `rontgen.py`, for hotspots). [Back to the overview](./)

</div>

<div id="pane-tr" markdown="1" class="pane-init">

## Gerçek kod üzerinde görün

Aşağıdaki her sayfa, `pano.py`'nin yazdığı haliyle bir `pano.html`: tek dosya, ağ gerekmez, TR / EN düğmesi. Sayılar ve
modül ve dosya adları taşırlar, kaynak kod asla; her proje kendi lisansını korur.

| Proje | Dil | Boyut | Sayfa |
|---|---|---|---|
| riemann-lean | Lean 4 | 175.187 dosya, 17,5 milyon satır | [aç →](ornekler/riemann-lean.html#tr) |
| helix | Rust | 296 dosya | [aç →](ornekler/helix.html#tr) |
| esbuild | Go | 196 dosya | [aç →](ornekler/esbuild.html#tr) |

Lean sayfası, Riemann Hipotezi'nin bir ispatını iddia eden bir yayının yapısını haritalar ve üç okuma turunu taşır:
`Main.lean`'den Galois satırına ve pencere sınırının kanıtına inen yaklaşık 950 satır, altı modül notu, her cümle atıflı. Kör ikinci
okuyucu tur 1'de 12'nin 11'ini doğruladı; tur 2 ve 3 henüz denetlenmedi.
İspatın geçerli olup olmadığı hakkında bir şey söylemez.

Aynı çıktı her depo için, `yapi.py`'den (sıcak noktalar için `rontgen.py`'den de) sonra
`python scripts/pano.py --docs rontgen-out --repo .` ile üretilir. [Genel bakışa dön](./#tr)

</div>
