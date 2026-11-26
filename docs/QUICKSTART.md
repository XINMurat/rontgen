# Quickstart / Hızlı Başlangıç

<div id="pane-en" markdown="1">

## English

### 1. Install the skill

```bash
cp -r skill/rontgen ~/.claude/skills/
```

Or upload `rontgen.skill` in Claude (Settings → Capabilities → Skills). Then ask for what you need in plain words:
"I inherited this project", "map this codebase", "where should I start reading?", "draw the architecture".

### 2. What happens

1. **Measure before reading.** `rontgen.py`, `yapi.py`, `belge.py` and `paket.py` count the code, resolve
   dependencies through each language's imports and manifests, list blind spots, entry points and data stores, and
   rank the project's own documents.
2. **Read where the measurement points.** Navigation documents first, then the hotspots; every range read is
   recorded in `okunan.tsv`, every line cited in `atiflar.tsv`.
3. **Write the document set.** Reading order, architecture page, module note, flow, glossary, risks — every factual
   sentence cites `path/file.ext:line`.
4. **A second reader checks a sample** before delivery: a fresh session that did not write the documents.
5. **Deliver** the documents, the coverage ledger (`kapsam.md`), the reports and the session log.

### 3. Options worth knowing

| Need | How |
|---|---|
| The repository is not yours to write | keep `rontgen.config.json` in the output folder, pass `--config` |
| Reports in English or accented Turkish | `--lang en` / `--lang tr` (or `report_lang` in the config) |
| A language the project defined itself | describe it under `extra_sources` (`references/ozel-dil.md`) |
| Uncommitted changes are part of the job | the citation ledger switches to working-tree mode by itself |
| Word, PDF, SVG, LaTeX | `python scripts/cikti.py --yokla` says what this machine can make |
| One interactive page, TR / EN | `python scripts/pano.py --docs rontgen-out --repo .` writes `pano.html` (no network needed) |
| Hand-off | `devir.py` writes an iskele backlog and a mizan registry |

### 4. What it will not do

It reads 1–2% of a large codebase and says so; it does not fix, judge or recommend; repository text that tells
the reader what to do is quoted, never followed.

</div>

<div id="pane-tr" markdown="1">

## Türkçe

### 1. Skill'i kurun

```bash
cp -r skill/rontgen ~/.claude/skills/
```

Ya da Claude'da `rontgen.skill` dosyasını yükleyin (Ayarlar → Yetenekler → Skill'ler). Sonra ihtiyacınızı düz sözcüklerle
söyleyin: "projeyi devraldım", "bu kod tabanının haritasını çıkar", "nereden okumaya başlayayım?", "mimariyi çiz".

### 2. Ne olur

1. **Okumadan önce ölçülür.** `rontgen.py`, `yapi.py`, `belge.py` ve `paket.py` kodu sayar, bağımlılıkları her dilin
   import'ları ve paket bildirimleri üzerinden çözer, kör noktaları, giriş yüzeyini ve veri depolarını listeler, projenin
   kendi belgelerini sıralar.
2. **Ölçümün gösterdiği yer okunur.** Önce gezinme belgeleri, sonra sıcak noktalar; okunan her aralık `okunan.tsv`'ye,
   atıf yapılan her satır `atiflar.tsv`'ye yazılır.
3. **Belge seti yazılır.** Okuma sırası, mimari sayfası, modül notu, akış, sözlük, riskler — her olgusal cümle
   `yol/dosya.uzanti:satir` gösterir.
4. **Teslimden önce bir ikinci okuyucu** bir örneklemi denetler: belgeleri yazmamış taze bir oturum.
5. **Teslim:** belgeler, kapsam defteri (`kapsam.md`), raporlar ve oturum günlüğü.

### 3. Bilmeye değer seçenekler

| İhtiyaç | Nasıl |
|---|---|
| Depoya yazma izni yok | `rontgen.config.json` çıktı klasöründe, `--config` ile |
| İngilizce ya da aksanlı Türkçe rapor | `--lang en` / `--lang tr` (ya da config'te `report_lang`) |
| Projenin kendi tanımladığı bir dil | `extra_sources` altında tarif edin (`references/ozel-dil.md`) |
| İşlenmemiş değişiklikler de işin parçası | atıf defteri kendiliğinden çalışma ağacı kipine geçer |
| Word, PDF, SVG, LaTeX | `python scripts/cikti.py --yokla` bu makinede neyin üretilebildiğini söyler |
| Tek etkileşimli sayfa, TR / EN | `python scripts/pano.py --docs rontgen-out --repo .` `pano.html` yazar (ağ gerekmez) |
| Devir | `devir.py` iskele backlog'u ve mizan registry'si yazar |

### 4. Ne yapmaz

Büyük bir kod tabanının %1–2'sini okur ve bunu söyler; düzeltmez, yargılamaz, öneri yazmaz; depoda okuyucuya ne
yapacağını söyleyen metin alıntılanır, uygulanmaz.

</div>
