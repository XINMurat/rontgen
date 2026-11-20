#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rontgen -- report language: the same report in accented Turkish or English.

WHY THIS EXISTS
---------------
Every report was written in Turkish without diacritics ("satir", "olculmedi"),
which reads as broken to a Turkish reader and as noise to everyone else.
The reports are rendered once, in that plain form, and translated on the way
out; the JSON outputs never change, so nothing that parses them is affected.

  report_lang   "tr-ascii"  as rendered (default, what the scripts always wrote)
                "tr"        diacritics restored, by word stem with its suffixes
                "en"        English, by phrase then by word
An unknown value is refused (exit 2), never silently replaced by the default.

Nothing inside backticks or a fenced block is touched: paths, code and
citations stay byte-identical. `leftover()` counts lines that still carry a
Turkish-only word, so a gap in the English tables shows as a number.
"""
from __future__ import annotations

import re
import sys

LANGS = ("tr-ascii", "tr", "en")

# stem (as rendered) -> accented stem; matched at a word start, suffixes kept
TR_STEMS = {
    "acilir": "açılır", "adlandir": "adlandır", "adres": "adres", "akis": "akış", "alarm": "alarm", "anil": "anıl",
    "anmadig": "anmadığ", "arac": "araç", "aralig": "aralığ", "arali": "aralı", "ariyor": "arıyor", "asagi": "aşağı",
    "asan": "aşan", "atif": "atıf", "ayni": "aynı", "ayri": "ayrı", "ayristir": "ayrıştır", "ayrim": "ayrım", "azina": "azına",
    "bag": "bağ", "baglam": "bağlam", "baglanti": "bağlantı", "basin": "başın", "basi": "başı", "baska": "başka",
    "basla": "başla", "basli": "başlı", "basvuru": "başvuru", "betig": "betiğ", "bicim": "biçim", "bilgi": "bilgi",
    "bolum": "bölüm", "bosluk": "boşluk", "buyuk": "büyük", "bulunamad": "bulunamad", "calis": "çalış", "capa": "çapa",
    "capali": "çapalı", "cift": "çift", "cikan": "çıkan", "cikar": "çıkar", "cikm": "çıkm", "ciz": "çiz", "cok": "çok",
    "cozul": "çözül", "cumle": "cümle", "dagilim": "dağılım", "dayan": "dayan", "degil": "değil", "degis": "değiş",
    "derinlik": "derinlik", "disi": "dışı", "dis": "dış", "dislan": "dışlan", "dogru": "doğru", "dokun": "dokun",
    "dongu": "döngü", "dosyalardir": "dosyalardır", "dusuk": "düşük", "duz": "düz", "esik": "eşik", "eslesme": "eşleşme",
    "gecen": "geçen", "gecip": "geçip", "gecm": "geçm", "gectig": "geçtiğ", "genis": "geniş", "gerek": "gerek",
    "giris": "giriş", "gorun": "görün", "gore": "göre", "govde": "gövde", "guvence": "güvence", "hic": "hiç",
    "icin": "için", "icinde": "içinde", "icerik": "içerik", "ikinci": "ikinci", "iliski": "ilişki", "incelenebilir": "incelenebilir",
    "isaret": "işaret", "isiya": "ısıya", "iskelet": "iskelet", "islev": "işlev", "izleyemedig": "izleyemediğ",
    "kacabilir": "kaçabilir", "kalip": "kalıp", "kalib": "kalıb", "kapanir": "kapanır", "karakter": "karakter",
    "karsilas": "karşılaş", "katil": "katıl", "katman": "katman", "kaynag": "kaynağ", "kimlig": "kimliğ", "kirik": "kırık",
    "kisi": "kişi", "kismen": "kısmen", "kok": "kök", "kor": "kör", "kucuk": "küçük", "kullanil": "kullanıl",
    "kume": "küme", "modul": "modül", "nokta": "nokta", "numarali": "numaralı", "okunmamis": "okunmamış", "olcu": "ölçü",
    "olcul": "ölçül", "olcum": "ölçüm", "oldug": "olduğ", "onay": "onay", "orani": "oranı", "ornek": "örnek",
    "ortu": "örtü", "ozel": "özel", "ozellig": "özelliğ", "ozgu": "özgü", "pahali": "pahalı", "parca": "parça",
    "satir": "satır", "sayi": "sayı", "sayil": "sayıl", "sayis": "sayıs", "sema": "şema", "seye": "şeye", "seyi": "şeyi",
    "sey": "şey", "sicak": "sıcak", "sifir": "sıfır", "sinanmi": "sınanmı", "sinif": "sınıf", "sira": "sıra",
    "soyler": "söyler", "sozcuk": "sözcük", "sutun": "sütun", "tahmin": "tahmin", "tanim": "tanım", "tani": "tanı",
    "tasarim": "tasarım", "tirnak": "tırnak", "tus": "tuş", "ucu": "ucu", "uret": "üret", "ust": "üst",
    "uyan": "uyan", "uye": "üye", "uzanti": "uzantı", "uzlasim": "uzlaşım", "varsayilan": "varsayılan",
    "yalniz": "yalnız", "yanilabilir": "yanılabilir", "yanlis": "yanlış", "yansima": "yansıma", "yapi": "yapı",
    "yargil": "yargıl", "yaslan": "yaslan", "yaygin": "yaygın", "yazili": "yazılı", "yazil": "yazıl", "yazin": "yazın",
    "yogun": "yoğun", "yuzey": "yüzey", "yuzde": "yüzde", "zayif": "zayıf", "olasilik": "olasılık", "gecmis": "geçmiş",
    "degisiklik": "değişiklik", "kisinin": "kişinin", "uclar": "uçlar", "dilim": "dilim", "defter": "defter",
    "okundu": "okundu", "okunmadi": "okunmadı", "okunmasina": "okunmasına", "tamsayi": "tamsayı", "ikili": "ikili",
    "baglarla": "bağlarla", "bulunmadi": "bulunmadı", "yoktur": "yoktur", "girmeyen": "girmeyen", "envanter": "envanter",
    "siniflanmayan": "sınıflanmayan", "dizin": "dizin", "derleme": "derleme", "medyan": "medyan", "dosyanin": "dosyanın",
    "tanesi": "tanesi", "tanesine": "tanesine", "payi": "payı", "kisinin": "kişinin", "yolu": "yolu", "yola": "yola",
    "iddia": "iddia", "yeterlilik": "yeterlilik", "belge": "belge", "yazan": "yazan", "okuyan": "okuyan",
    "dogrulug": "doğruluğ", "baslayacag": "başlayacağ", "dosyasi": "dosyası", "dosyalari": "dosyaları",
    "dosyalarin": "dosyaların", "dosyasinin": "dosyasının", "adin": "adın", "basinda": "başında", "basina": "başına",
    "yaslandig": "yaslandığ", "dagit": "dağıt", "agac": "ağaç", "degerl": "değerl", "goster": "göster", "olustur": "oluştur",
}
_TR = sorted(TR_STEMS.items(), key=lambda kv: -len(kv[0]))
_TR_RX = re.compile(r"(?<![\w./\\-])(" + "|".join(re.escape(k) for k, _ in _TR) + r")([a-z]*)(?![\w./\\-])", re.I)
# a word joined to _ . / \ - is a name (disa_aktar.py, helix-view): one run turned a file name into Turkish

# phrase (as rendered, exact) -> English; longest first
EN = [
    ("Katmanlar:", "Tiers:"), ("dogrudan sayildi", "counted directly"), ("vekil olcu (yanilabilir)", "proxy (can be wrong)"),
    ("Bu rapor tasarimi, adlandirmayi", "This report does not judge design, naming"),
    ("ya da dogrulugu yargilamaz; okuyana nereden baslayacagini ve ne kadar oldugunu soyler.",
     "or correctness; it tells the reader where to start and how much there is."),
    ("Esikler", "Thresholds"), ("(varsayilan)", "(default)"), ("(config)", "(config)"),
    ("## Envanter", "## Inventory"), ("Kaynak sayilan uzantilar", "Extensions counted as source"),
    ("Config'le kaynak sayilan", "Counted as source by config"), ("sayilir, ayristirilmaz", "counted, not parsed"),
    ("Siniflanmayan uzantilar (sifir sayilmadi, **olculmedi**)", "Unclassified extensions (not zero, **unmeasured**)"),
    ("Olcume girmeyen kaynak dosyalari:", "Source files left out of the measurement:"),
    ("Dislanan kaynak dosyasi yok.", "No source file was excluded."),
    ("test dosyasi ayrimi yola gore", "test files told apart by path"),
    ("uretilmis (dosya basinda isaret)", "generated (marked at the top of the file)"), ("derleme dizini", "build directory"),
    ("Ust dizin", "Top directory"), ("## Boyut", "## Size"), ("Kaynak dosya basina medyan", "Median per source file"),
    ("satiri asan", "lines or more:"), ("karakteri asan", "characters or more:"),
    ("Uzun satir", "Long lines"), ("Derinlik", "Depth"),
    ("## Sicak noktalar", "## Hotspots"), ("cok degisen VE buyuk", "changed often AND large"),
    ("Sira: commit sayisi x satir. Ust siralar hem en cok okunmasi gereken hem en pahali okunan dosyalardir.",
     "Rank: commits x lines. The top rows are the files most worth reading and the most expensive to read."),
    ("Degisen satir", "Lines changed"), ("## Bilgi dagilimi", "## Knowledge spread"),
    ("en cok commit atan kisinin payi", "share of the top committer"),
    ("tanesine tek kisi dokunmus", "were touched by one person only"), ("Gecmisi olan", "Of the"),
    ("kaynak dosyanin", "source files with history,"),
    ("Yazar kimligi e-posta adresidir; ayni kisinin iki adresi iki kisi sayilir",
     "An author is an e-mail address; one person with two addresses counts as two"),
    ("## Birlikte degisenler", "## Changed together"), ("gorunmeyen baglar", "ties no import shows"),
    ("Ayni commit'te en az", "Pairs that changed together in the same commit at least"), ("kez birlikte degisen ciftler.", "times."),
    ("Pay: birlikte / (ikisinden az degisenin commit sayisi).", "Share: together / (commits of the less changed one)."),
    ("dosyadan genis commit'ler sayilmadi (her seyi her seye baglarlar).", "files or more per commit were not counted (they tie everything to everything)."),
    ("Birlikte", "Together"), ("## Degisiklik bicimi", "## Change shape"), ("gecmis incelenebilir mi", "was the history reviewable"),
    ("Kaynaga dokunan", "Touching source:"), ("satir medyan", "lines median"), ("en buyuk", "largest"), ("dosya medyan", "files median"),
    ("bunlar buyuk olasilikla okunmadan onaylandi", "these were most likely approved unread"),
    ("## Test ortusu", "## Test coverage"), ("vekil olcu", "proxy"),
    ("Kapsam raporu kullanilamadi", "No coverage report could be used"), ("config'te", "in config:"),
    ("Projenin kapsam araci varsa calistirip raporu config'e yazin; asagidaki vekilin yerini alir.",
     "If the project has a coverage tool, run it and name its report in config; it replaces the proxy below."),
    ("Test / kaynak satir orani", "Test / source line ratio"),
    ("Adi hicbir test dosyasinin adinda gecmeyen kaynak dosyalari", "Source files whose name appears in no test file name"),
    ("Ad eslesmesidir: test baska adla yaziyorsa yanlis alarm, ad gecip davranis",
     "A name match: a test under another name gives a false alarm, a name present while the behaviour"),
    ("sinanmiyorsa yanlis guvence.", "is untested gives false comfort."),
    ("Koddan uretildi; elle cizilmedi.", "Generated from the code; not drawn by hand."),
    ("Duz ok", "Solid arrow"), ("Kesik ok", "Dashed arrow"),
    ("depoda cozulen beyan edilmis bagimlilik", "a declared dependency that resolves in the repository"),
    ("proje basvurusu", "project reference"), ("kazanmis sonda", "probe that earned it"),
    ("tek bir dosyada tanimli bir adin ayni dil ailesinden baska bir dosyada gecmesi",
     "a name defined in one file appearing in another file of the same language family"),
    ("vekildir: yaygin bir sozcuk sahte ok uretir, yansima ve bagimlilik enjeksiyonu hic ok uretmez.",
     "a proxy: a common word draws a false arrow; reflection and dependency injection draw none."),
    ("Ayarlar", "Settings"), ("## Olcume girmeyenler", "## Left out of the measurement"), ("## Blok semasi", "## Block diagram"),
    ("Cizilen", "Drawn:"), ("Toplam:", "Total:"), ("zayif", "weak"),
    ("dosya ciftinden azina dayanan; cizilmedi, donguye katilmadi", "resting on fewer file pairs; not drawn, not in cycles"),
    ("Ok ustundeki sayi: dosya cifti.", "The number on an arrow: file pairs."),
    ("Zayif baglar (dogrulanmadan bag sayilmaz)", "Weak edges (not an edge until checked)"),
    ("## Moduller", "## Modules"),
    ("Giren: bu module yaslanan modul sayisi; cikan: yaslandigi modul sayisi. [K] ve [H] ayri sayilir.",
     "In: modules leaning on this one; out: modules it leans on. [K] and [H] are counted apart."),
    ("Giren", "In"), ("Cikan", "Out"), ("## Donguler", "## Cycles"),
    ("Beyan edilmis bagimliliklarda (`[K]`) modul dongusu yok.", "No module cycle in declared (`[K]`) dependencies."),
    ("Aday donguler — yalniz", "Candidate cycles — closed only by"), ("baglarla kapanir;", "edges;"),
    ("dogrulanmadan dongu denmez", "not a cycle until checked"), ("en ince bagi", "thinnest edge"),
    ("## Kor noktalar — sonda adaylari", "## Blind spots — probe candidates"),
    ("Bu betiklerin izleyemedigi mekanizmalarin kodda ne kadar gectigi. Bir sayi buyukse o mekanizmanin arkasindaki baglar",
     "How often the code uses mechanisms these scripts cannot follow. Where a number is large, the edges behind it"),
    ("semada **yoktur**. Projeye ozgu bir sonda ancak buradaki bir bosluk icin yazilir (sonda.py).",
     "are **absent** from the diagram. A project-specific probe is written only for a gap listed here (sonda.py)."),
    ("Taninan bir kor nokta kalibi bulunmadi (kaliplarin tanimadigi mekanizmalar olabilir).",
     "No known blind-spot pattern was found (mechanisms the patterns do not know may exist)."),
    ("Mekanizma", "Mechanism"), ("Isabet", "Hits"), ("En yogun", "Densest"),
    ("Yuklenen sonda sonuclari:", "Probe results loaded:"), ("baglari", "edges"),
    ("crate'ler", "crates"), ("moduller (go.mod)", "modules (go.mod)"), ("kaynak kokleri", "source roots"),
    ("bildirim bulunamadi", "no manifest found"), ("cozulen:", "resolved:"), ("dosya bagi", "file edges"),
    ("depo disi (dis, bag yok)", "outside the repository (external, no edge)"), ("cozulemeyen", "unresolved"),
    ("(kor nokta)", "(blind spot)"), ("Cozulemeyen ornekleri", "Unresolved examples"),
    ("## En cok yaslanilan dosyalar", "## Most leaned-on files"), ("Yaslanan dosya", "Files leaning on it"),
    ("## Giris yuzeyi", "## Entry surface"), ("Kalipla taninan", "Recognised by pattern:"), ("HTTP ucu", "HTTP endpoints"),
    ("tanesi test dosyalarinda", "of them in test files"), ("baslangic noktasi sayilan dosyalar", "files counted as starting points"),
    ("Giris islevleri", "Entry functions"), ("C her yerde, Rust yalniz ikili hedefte; digerleri yalniz config",
                                              "C anywhere, Rust only in a binary target; others only by config"),
    ("adiyla", "by name"), ("kalipla", "by pattern"), ("## Veri depolari", "## Data stores"),
    ("SQL ya da ORM'de tanimli", "Declared in SQL or an ORM:"), ("SQL'de tanimli", "Declared in SQL:"),
    ("ifadesinde", "statements"), ("yalniz tirnak icinde adi gecen", "named only inside quotes"),
    ("ad kodla kurulan sorguya veriliyor olabilir", "the name may be passed to a query built in code"),
    ("Adi duz yazida ya da sutun", "A file naming it in plain prose or as a column"),
    ("basligi olarak gecen dosya sayilmaz. Sorgu metni parcalardan kuruluyorsa eksik sayar.",
     "header is not counted. Where query text is built from parts, this undercounts."),
    ("Tablo", "Table"), ("Tanim", "Declared in"), ("Yazan", "Writes"), ("Okuyan", "Reads"), ("Tirnakli", "Quoted"),
    ("## En buyuk dosyalarin iskeleti", "## Outline of the largest files"),
    ("Satir numarali bildirimler ve uclar.", "Declarations and endpoints with line numbers."),
    ("bildirim daha", "more declarations"),
    ("# Kapsam defteri", "# Coverage ledger"), ("Ikinci okuyucu: yapilmadi.", "Second reader: not done."),
    ("Ikinci okuyucu", "Second reader"), ("cumleden", "sentences,"), ("yargilandi", "judged"),
    ("Atiflari yalniz yazar denetledi; belgeyle birlikte bunu soyleyin.", "Only the author checked the citations; say so with the documents."),
    ("Kor denetim listesi yok.", "No blind checklist."),
    ("Yazili belgeler, test olmayan", "The written documents rest on"), ("kaynak satirin", "non-test source lines:"),
    ("okunmasina dayaniyor", "read"), ("Her capali satir bir okuma araliginin icinde.", "Every anchored line lies inside a read range."),
    ("Atifli ama okunmamis", "Cited but unread:"), ("kaynak sayilmayan", "non-source"), ("paya girmez", "not in the share"),
    ("## Sicak noktalar ne kadar okundu", "## How much of the hotspots was read"), ("## Belge kapsami", "## Document coverage"),
    ("Modul notu", "Module notes"), ("Akis belgesi", "Flow documents"), ("## Siradaki dilim", "## Next slice"),
    ("Okunmamis isiya gore (commit x okunmamis satir). Bir oturumda bir dilim; oturum bu defteri ve belgeleri okuyup devam eder.",
     "By unread heat (commits x unread lines). One slice per sitting; a sitting reads this ledger and the documents, then goes on."),
    ("okunmamis satir", "unread lines"), ("Durum", "State"), ("Okunan", "Read"), ("Pay", "Share"), ("Capa", "Anchors"),
    ("Dokunulan dosya", "Files touched"), ("okundu", "read"), ("kismen", "partly"), ("okunmadi", "unread"),
    ("# Belge haritasi", "# Document map"), ("# Paket bildirimleri", "# Package manifests"),
    ("Ekosistem", "Ecosystem"), ("Ic bagimliliklar", "Internal dependencies"), ("Dis", "External"),
    ("Yalniz test/derleme ic", "Test/build-only internal"), ("Ozellige bagli / istege bagli", "Feature-gated / optional"),
    ("# Yapi", "# Structure"), ("# Rontgen", "# Rontgen"), ("Kaynak", "Source"), ("Dosya", "File"), ("Satir", "Lines"),
    ("cizilmedi", "not drawn"), ("Kisi", "People"), ("Dil", "Language"), ("Modul", "Module"), ("dosya", "files"), ("satir", "lines"),
    ("kisi", "people"), ("tablo", "tables"), ("yok", "none"), ("olculmedi", "unmeasured"), ("tuttu", "held"),
    ("tutmadi", "did not hold"), ("satirdan cikmiyor", "says more than its line"), ("ve", "and"), ("ya da", "or"),
]
_EN = sorted(EN, key=lambda kv: -len(kv[0]))
_EN_RX = re.compile("|".join(r"(?<![\w`])" + re.escape(k) + r"(?![\w])" for k, _ in _EN))
_EN_MAP = dict(EN)
TURKISH_ONLY = re.compile(r"\b(satir|dosya|olculmedi|yalniz|degil|icin|ile|bag|baglari|okunan|yazan|kaynak|gore|daha|tanesi|cozulen|"
                          r"modul|dongu|sayi|cikan|giren|tablo|uret\w*|sicak|kor|tuttu|okundu|yok)\b", re.I)


def _outside_code(text, fn):
    out, fence = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence
            out.append(line); continue
        if fence:
            out.append(line); continue
        parts = re.split(r"(`[^`]*`)", line)
        out.append("".join(p if p.startswith("`") and p.endswith("`") and len(p) > 1 else fn(p) for p in parts))
    return "\n".join(out)


def _accent(s):
    def rep(m):
        stem, suf = m.group(1), m.group(2)
        new = TR_STEMS[stem.lower()]
        new = new[0].upper() + new[1:] if stem[0].isupper() else new
        vowels = re.findall(r"[aeıioöuü]", new.lower())
        suf = suf.replace("i", "ı") if vowels and vowels[-1] in "aıou" else suf   # back vowel: the suffix follows
        return new + suf
    return _TR_RX.sub(rep, s)


EN_NUM = [(re.compile(r"\b(\d+) dosya ciftinden azina dayanan"), r"resting on fewer than \1 file pairs"),
          (re.compile(r"\b(\d+) bag\b"), r"\1 edges"), (re.compile(r"\b(\d+) commit\b"), r"\1 commits")]


def _english(s):
    for rx, rep in EN_NUM:                  # word order differs: number-bound phrases first
        s = rx.sub(rep, s)
    return _EN_RX.sub(lambda m: _EN_MAP[m.group(0)], s)


def check(lang):
    if lang not in LANGS:
        print(f"olculmedi: report_lang '{lang}' bilinmiyor; secenekler: {', '.join(LANGS)} (varsayilana dusulmez)", file=sys.stderr)
        raise SystemExit(2)
    return lang


def cevir(text: str, lang: str) -> str:
    check(lang)
    if lang == "tr-ascii":
        return text
    return _outside_code(text, _accent if lang == "tr" else _english)


def leftover(text: str) -> int:
    """Lines (outside code) that still carry a Turkish-only word: the gap in the English tables."""
    n = 0
    _outside_code(text, lambda p: p)
    fence = False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fence = not fence; continue
        if not fence and TURKISH_ONLY.search(re.sub(r"`[^`]*`", "", line)):
            n += 1
    return n


def self_test() -> int:
    ok = []

    def t(name, cond):
        ok.append(cond); print(("ok   " if cond else "FAIL ") + name)

    md = "## Sicak noktalar\n- Kaynak: **3 dosya, 10 satir** `src/satir.rs:4`\n```\nsatir yok\n```\nOlculmedi: yalniz test."
    tr = cevir(md, "tr")
    t("tr: aksan geri gelir, ekler korunur", "## Sıcak noktalar" in tr and "10 satır" in tr and "Ölçülmedi" in tr and "yalnız" in tr)
    t("tr: ters tirnak ve kod blogu degismez", "`src/satir.rs:4`" in tr and "\nsatir yok\n" in tr)
    t("tr: dosya adi gibi bitisik sozcuk degismez", cevir("disa_aktar.py ve kor-nokta ile satir/yol", "tr")
      == "disa_aktar.py ve kor-nokta ile satir/yol")
    en = cevir(md, "en")
    t("en: baslik ve etiketler cevrilir, kod degismez", "## Hotspots" in en and "10 lines" in en and "`src/satir.rs:4`" in en
      and "\nsatir yok\n" in en)
    t("tr-ascii: dokunulmaz", cevir(md, "tr-ascii") == md)
    try:
        cevir(md, "de"); t("bilinmeyen dil durur", False)
    except SystemExit as e:
        t("bilinmeyen dil durur (cikis 2), varsayilana dusmez", e.code == 2)
    t("leftover: Turkce kalan satiri sayar", leftover("satir var\n`satir`\nok") == 1 and leftover(en) <= 1)
    print(f"\n{sum(ok)}/{len(ok)} gecti")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(self_test() if "--self-test" in sys.argv else 0)
