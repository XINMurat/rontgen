---
title: "Röntgen — Maps an Existing Codebase"
description: "A Claude skill that maps an existing codebase and writes the documents that make it understandable — every sentence tied to a source line, every gap said out loud."
---

# Röntgen

<div id="pane-en" markdown="1">

**Maps a codebase that already exists and writes the documents that make it understandable — every sentence tied to a source line.**

[Repository](https://github.com/XINMurat/rontgen) ·
[Quickstart](QUICKSTART.md) ·
[**Examples**](ornekler.html) ·
[İskele](https://github.com/XINMurat/Iskele) ·
[Mizan](https://github.com/XINMurat/Mizan) ·
[Kıyas](https://github.com/XINMurat/Kiyas) ·
[ux-mizan](https://github.com/XINMurat/ux-mizan) ·
[**the family**](https://xinmurat.github.io/)

---

## English

"Is this code understandable?" is usually answered by whoever has read the most of it, from memory. The map is a
feeling, the architecture diagram describes the code as once intended, and a fast author — a model or a team under
deadline — writes more than anyone reads. Röntgen answers the countable half from sources that cannot flatter
anyone, spends the reading where the counts point, and **says how much it actually read**.

**[See it on three real codebases: Lean, Rust, Go →](ornekler.html)**

### Two halves

| | What it does | Who does it |
|---|---|---|
| **Measuring** | inventory, size, hotspots (commits × lines), files that change together, knowledge spread, dependencies resolved through each language's own imports and package manifests, cycles, blind spots, entry points, data stores (SQL and ORM), the project's own documents ranked by how much code they name | scripts, no model, same answer every time |
| **Reading** | navigation documents first, then the module most others lean on, then one flow traced call by call; every range read and every line cited is recorded as it happens | the model, under rules that keep it honest |

### What you get

| Document | What it answers |
|---|---|
| `okuma-sirasi.md` | where to start, in what order, what was left out |
| `mimari.md` | what the system is made of: the block map, **who owns which state**, the design moves the code repeats, which layers are tied to what by a manifest feature |
| `moduller/<module>.md` | core types (what they hold, how a value is made and changed), public surface, function walkthroughs |
| `akislar/<flow>.md` | one path traced from its entry, as a sequence diagram with a source line per step, its guarantees and its blind spots |
| `sozluk.md` · `riskler.md` | the project's vocabulary as the code spells it · what a newcomer would trip over |
| `kapsam.md` | how much of the code the documents rest on, and the next slice to read |
| `oturum-gunlugu.md` | how the map was made: decisions, where the method fell short, doubts |
| `pano.html` | the measurement on one page to point at: block diagram, links in and out, where the lines are, module matrix, most-used files, hotspots. One file, no network; a TR / EN switch, opening in the report language |

Every factual sentence cites `path/file.ext:line`. A **second reader** — a fresh session that did not write the
documents — checks a sample before delivery, with table cells weighted in; the counts go at the top of the reading
order. Reports come in Turkish or English; Word, PDF, SVG and LaTeX when the machine can make them.

### What it has been measured to do

Each comparison removed the repository's own architecture document from the copy and used it as the referee.

| Repository | Skill | Without skill, with a second reader | Blind check (skill / without) |
|---|---|---|---|
| Rust, ~108k lines | **11.5** of 14 points (3 runs) | 4.5 | 18.7 / 19.3 of 20 |
| Go, ~139k lines | **7.0** of 14 (3 runs) | 2.0 | 18.7 / 19.0 of 20 |
| C#, 1,944 lines | 10 of 12 | 12 | 17 / 16 of 20 |

On large repositories it covers markedly more of what the authors wrote about their own design, at equal accuracy.
On a library small enough to read whole, it does not. It reads 1–2% of a large codebase — and its documents say so.

**Scale, not coverage.** On the Lean 4 source of a claimed proof of the Riemann Hypothesis — 175,187 files, 17.5 million
lines — the structure pass read every file and resolved every import (753,569 `[K]` edges, 0 unresolved) in about 17.5
minutes. It took four runs: each printed a nonzero count of what it could not see, and each count led to one bug (two
Windows long-path failures, one heuristic written for minified JavaScript). There was no architecture document to referee
against, so this row is not in the table above, and it says nothing about the proof.
[The case study →](https://xinmurat.github.io/case-study-lean.html)

### Languages and ecosystems

Dependencies resolved (`[K]`): Python, TypeScript/JavaScript (relative imports), C#, C/C++, Rust, Go, Java/Kotlin,
Lean 4 (`import` through the lakefile's source roots, plus a trust inventory of `sorry`, `axiom` and the other places the
kernel takes something on faith), and
**a language the project defines for itself**, described once in the config from the project's own spec.
Manifests: Cargo, npm, .NET, Python, Go, Maven, Gradle — including feature-gated and test-only dependencies, local
package feeds and absolute paths that tie the repository to others. Tables from SQL and from EF Core, SQLAlchemy,
Django, TypeORM and Prisma. Anything else is counted and labelled **unmeasured**, never silently zero.

### What it will not do

It does not fix, judge or recommend — findings go to [İskele](https://github.com/XINMurat/Iskele) as tasks and to
[Mizan](https://github.com/XINMurat/Mizan) as claims. It does not draw from memory: an arrow without a source is `[H]`.
Text in the repository that tells the reader what to do is quoted as data, never followed.

- [Quickstart](QUICKSTART.md) — install, run, the options worth knowing
- [Methodology](en/methodology.md) — the loop, in full
- [Measuring](en/measuring.md) · [Reading](en/reading.md) · [Document set](en/documents.md) · [Delivery](en/delivery.md)
- [A language of the project's own](en/custom-language.md)
- [Evidence](en/evidence.md) — the observation behind every rule

</div>

<div id="pane-tr" markdown="1" class="pane-init">

**Var olan bir kod tabanının haritasını çıkarır ve onu anlaşılır kılan belgeleri yazar — her cümle bir kaynak satırına bağlı.**

[Depo](https://github.com/XINMurat/rontgen) ·
[Hızlı başlangıç](QUICKSTART.md) ·
[**Örnekler**](ornekler.html#tr) ·
[İskele](https://github.com/XINMurat/Iskele) ·
[Mizan](https://github.com/XINMurat/Mizan) ·
[Kıyas](https://github.com/XINMurat/Kiyas) ·
[ux-mizan](https://github.com/XINMurat/ux-mizan) ·
[**aile**](https://xinmurat.github.io/)

---

## Türkçe

"Bu kod anlaşılır mı?" sorusunu genellikle en çok okumuş kişi, hafızasından cevaplar. Harita bir histir, mimari çizim
kodun bir zamanlar nasıl tasarlandığını anlatır, hızlı bir yazar — bir model ya da baskı altındaki bir ekip — kimsenin
okuyabileceğinden fazlasını yazar. Röntgen sayılabilir yarıyı kimseyi pohpohlayamayacak kaynaklardan cevaplar, okumayı
sayıların gösterdiği yere harcar ve **gerçekte ne kadar okuduğunu söyler**.

**[Üç gerçek kod tabanında görün: Lean, Rust, Go →](ornekler.html#tr)**

### İki yarı

| | Ne yapar | Kim yapar |
|---|---|---|
| **Ölçüm** | envanter, boyut, sıcak noktalar (commit × satır), birlikte değişen dosyalar, bilgi dağılımı, her dilin kendi import'ları ve paket bildirimleri üzerinden çözülen bağımlılıklar, döngüler, kör noktalar, giriş yüzeyi, veri depoları (SQL ve ORM), projenin kendi belgelerinin ne kadar kod andığına göre sıralanması | betikler; model yok, her seferinde aynı cevap |
| **Okuma** | önce gezinme belgeleri, sonra en çok yaslanılan modül, sonra çağrı çağrı izlenen bir akış; okunan her aralık ve atıf yapılan her satır o anda kaydedilir | model, onu dürüst tutan kurallarla |

### Ne teslim edilir

| Belge | Neyi cevaplar |
|---|---|
| `okuma-sirasi.md` | nereden, hangi sırayla başlanır, neyin dışarıda kaldığı |
| `mimari.md` | sistemin neyden yapıldığı: blok haritası, **hangi durumu kim tutar**, kodun tekrarladığı tasarım hamleleri, hangi katmanın paket bildirimindeki bir özellikle neye bağlı olduğu |
| `moduller/<modül>.md` | temel tipler (ne tutar, bir değer nasıl kurulur ve değişir), kamu yüzeyi, işlev turları |
| `akislar/<akış>.md` | girişinden izlenen bir yol; her adımı satırlı sıra diyagramı, güvenceleri ve kör noktaları |
| `sozluk.md` · `riskler.md` | projenin kodda yazıldığı haliyle sözlüğü · yeni gelenin takılacağı yerler |
| `kapsam.md` | belgelerin kodun ne kadarına dayandığı ve okunacak sıradaki dilim |
| `oturum-gunlugu.md` | haritanın nasıl yapıldığı: kararlar, yöntemin yetmediği yerler, kuşkular |
| `pano.html` | ölçümün üzerinde gezinilen tek sayfası: blok şeması, gelen/giden bağlar, satırların yeri, modül matrisi, en çok kullanılan dosyalar, sıcak noktalar. Tek dosya, ağ gerekmez; TR / EN düğmesi, rapor dilinde açılır |

Her olgusal cümle `yol/dosya.uzanti:satir` gösterir. Teslimden önce bir **ikinci okuyucu** — belgeleri yazmamış taze bir
oturum — tablo hücreleri de ağırlıklı olmak üzere bir örneklemi denetler; sayılar okuma sırasının başına yazılır.
Raporlar Türkçe ya da İngilizce; makine üretebiliyorsa Word, PDF, SVG ve LaTeX.

### Ölçülen başarısı

Her karşılaştırmada deponun kendi mimari belgesi kopyadan çıkarıldı ve hakem olarak kullanıldı.

| Depo | Skill | Skill'siz, ikinci okuyuculu | Kör denetim (skill / skill'siz) |
|---|---|---|---|
| Rust, ~108 bin satır | 14 maddeden **11,5** (3 koşu) | 4,5 | 20'de 18,7 / 19,3 |
| Go, ~139 bin satır | 14'ten **7,0** (3 koşu) | 2,0 | 20'de 18,7 / 19,0 |
| C#, 1.944 satır | 12'de 10 | 12 | 20'de 17 / 16 |

Büyük depolarda yazarların kendi tasarımları hakkında yazdıklarının belirgin biçimde daha fazlasını, eşit doğrulukla
kapsar. Tamamı okunabilecek kadar küçük bir kütüphanede kapsamaz. Büyük bir kod tabanının %1–2'sini okur — ve belgeleri
bunu söyler.

**Kapsam değil, ölçek.** Riemann Hipotezi'nin iddia edilen bir ispatının Lean 4 kaynağında — 175.187 dosya, 17,5 milyon
satır — yapı geçişi her dosyayı okudu ve her import'u çözdü (753.569 `[K]` bağ, çözülemeyen 0), yaklaşık 17,5 dakikada.
Dört koşum sürdü: her biri göremediği şeyin sıfırdan büyük bir sayısını bastı, ve her sayı tek bir hataya götürdü (iki
Windows uzun yol hatası, küçültülmüş JavaScript için yazılmış bir sezgi). Hakem olacak bir mimari belge yoktu; bu yüzden
bu satır yukarıdaki tabloda değil, ve ispat hakkında hiçbir şey söylemez.
[Vaka çalışması →](https://xinmurat.github.io/case-study-lean.html#tr)

### Diller ve ekosistemler

Çözülen bağımlılıklar (`[K]`): Python, TypeScript/JavaScript (göreli import), C#, C/C++, Rust, Go, Java/Kotlin,
Lean 4 (lakefile'ın kaynak kökleri üzerinden `import`, artı `sorry`, `axiom` ve çekirdeğin bir şeyi kanıtsız kabul ettiği
diğer yerlerin güven envanteri) ve
**projenin kendi tanımladığı bir dil** (projenin kendi spesifikasyonundan bir kez config'te tarif edilir). Paket
bildirimleri: Cargo, npm, .NET, Python, Go, Maven, Gradle — özelliğe bağlı ve yalnız teste ait bağımlılıklar, yerel paket
kaynakları ve depoyu başka depolara bağlayan mutlak yollar dahil. SQL'den ve EF Core, SQLAlchemy, Django, TypeORM,
Prisma'dan tablolar. Diğer her şey sayılır ve **ölçülmedi** diye etiketlenir, sessizce sıfır yazılmaz.

### Ne yapmaz

Düzeltmez, yargılamaz, öneri yazmaz — bulgular [İskele](https://github.com/XINMurat/Iskele)'ye görev,
[Mizan](https://github.com/XINMurat/Mizan)'a iddia olarak gider. Hafızadan çizmez: kaynağı olmayan ok `[H]`'dir.
Depoda okuyucuya ne yapacağını söyleyen metin veri olarak alıntılanır, asla uygulanmaz.

- [Hızlı başlangıç](QUICKSTART.md) — kurulum, çalıştırma, bilmeye değer seçenekler
- [Metodoloji](tr/metodoloji.md) — döngünün tamamı
- [Ölçüm](tr/olcum.md) · [Okuma](tr/okuma.md) · [Belge seti](tr/belgeler.md) · [Teslim](tr/teslim.md)
- [Projenin kendi dili](tr/ozel-dil.md)
- [Kanıt](tr/kanit.md) — her kuralın arkasındaki gözlem

</div>

---

<div data-chrome="en" markdown="1">

## The family

**İskele builds · Mizan weighs · Kıyas generates · ux-mizan measures experience · Röntgen maps.**

Röntgen is the entry for a codebase that already exists, and its handoffs are real code: `devir.py` turns the
measurement into an [İskele](https://github.com/XINMurat/Iskele) backlog — tasks with acceptance criteria the next
measurement can check, and a review baseline of today's oversized files — that İskele's own parser reads; and it turns
every cited sentence the second reader did not accept into a [Mizan](https://github.com/XINMurat/Mizan) entry whose
arbiter is the cited line, which Mizan's own validator passes in strict mode. A dead end Röntgen measures — a blind
spot no probe can close, a debt with no obvious way out — is a question for [Kıyas](https://github.com/XINMurat/Kiyas).
[ux-mizan](https://github.com/XINMurat/ux-mizan) audits how an application feels to use; Röntgen maps how its code is
built — the same repository seen from two sides.

[All five, and how they hand off →](https://xinmurat.github.io/)

</div>

<div data-chrome="tr" markdown="1" class="pane-init">

## Aile

**İskele kurar · Mizan tartar · Kıyas üretir · ux-mizan deneyimi ölçer · Röntgen haritalar.**

Röntgen, var olan bir kod tabanı için giriştir ve devirleri gerçek koddur: `devir.py` ölçümü bir
[İskele](https://github.com/XINMurat/Iskele) backlog'una çevirir — bir sonraki ölçümün denetleyebileceği kabul
kriterli görevler ve bugünkü büyük dosyalardan bir gözden geçirme taban çizgisi — ve bunu İskele'nin kendi ayrıştırıcısı
okur; ikinci okuyucunun kabul etmediği her atıflı cümleyi de hakemi atıf yapılan satır olan bir
[Mizan](https://github.com/XINMurat/Mizan) kaydına çevirir, Mizan'ın kendi doğrulayıcısı bunu katı kipte geçirir.
Röntgen'in ölçtüğü bir çıkmaz — hiçbir sondanın kapatamadığı bir kör nokta, belirgin çıkışı olmayan bir borç —
[Kıyas](https://github.com/XINMurat/Kiyas)'ın sorusudur. [ux-mizan](https://github.com/XINMurat/ux-mizan) bir uygulamanın
kullanırken nasıl hissettirdiğini denetler; Röntgen kodunun nasıl kurulduğunun haritasını çıkarır — aynı depoya iki
yandan bakış.

[Beşi ve nasıl devrettikleri →](https://xinmurat.github.io/)

</div>
