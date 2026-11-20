> Kaynak: skill/rontgen/references/olcum.md · sha256:7093d62ef887 — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Ölçme — adım 1 ve 2'nin ayrıntıları

SKILL.md döngüyü tutar; bu dosya çekirdeğin koşularının öğrettiği
ayrıntıları tutar.

## Çalıştırma ve yapılandırma

Onları her yerden, `python -I` ile ya da onsuz, `python scripts/<name>.py`
olarak çalıştırın; her biri kardeş modüllerini kendi yolundan bulur. Depoya
yazamıyorsanız `rontgen.config.json`'u ve varsa sondaları çıktı klasöründe
tutun ve `rontgen.py`, `yapi.py` ve `belge.py`'ye `--config` verin;
`probe_results` önce yapılandırma dosyasının yanında, sonra deponun kökünden
aranır. `atif.py` ve `kapsam.py` yapılandırma almaz: onu taşıyan çıktı
klasörünü okurlar.

Önce bunları çalıştırın, kodu sonra okuyun: önce okumak sizi açtığınız dosyaya
çapalar. Git geçmişi yoksa değişim sıklığı, birlikte değişme ve bilgi
**ölçülmemiştir**, sıfır değil. Git olmadan dosyalar dizinden okunur; derleme
ve gizli dizinlere girilmez ve her biri listelenir.

Sonra **"Olcume girmeyenler"** listesini okuyun. Betikler üretilmiş görünen
şeyleri dışlar (paketler (bundle), migration'lar, `*.Designer.cs`, üretilmiş
diye işaretlenmiş dosyalar). Listede elle yazılmış bir şey varsa ya da
üretilmiş bir şey yoksa, düzeltmeyi `exclude_globs` içine koyun ve yeniden
çalıştırın — hatayı ileri taşımayın.
Bilerek ölü bırakılmış elle yazılmış kod (bir `_archive/`, bekletilen bir
kopya) aynı biçimde, sizin kararınızla dışlanır: sıcak noktaları ve kapsamı
çarpıtır, ve belgeler onu haritalamak yerine kapsam dışı olarak adlandırır.
Canlı olan ödünç kod (projenin çağırdığı budanmış bir üst kaynak kütüphanesi)
ölçülmeye devam eder; okunmadan bırakılabilir, ama belgeler projenin onu ne
için kullandığını söyler — bir koşu böyle bir kopyaya "kapsam dışı" dedi ve
mimari onun üzerine kuruluydu.
**Sınıflandırılmamış uzantıları** da aynı biçimde okuyun: davranış betiklerin
kaynak olarak tanımadığı dosyalarda yaşıyorsa (bir DSL, bir tablo biçimi),
onları `extra_sources` içinde adlandırın. O zaman sayılır, ölçülür ve bir
sonda kenarını bitirebilirler; asla ayrıştırılmazlar. Program bir `main`
dışında bir yerden başlıyorsa (bir çekirdek girişi, bir eklenti kancası), o
fonksiyonu `entry_points` içinde adlandırın; giriş yüzeyi onu satırıyla
gösterir ve bulunamayan bir ad öyle bildirilir. Giriş adları asla tahmin
edilmez. Bir `main` örüntüyle bulunur (C'de her yerde, Rust'ta yalnız bir
ikili hedefte); kütüphanelerde de geçen bir ad yoluyla verilir,
`src/plugins/*:start`.

## Kenar katmanları

Düz oklar `[K]`'dır: depo içinde çözülen beyan edilmiş bir bağımlılık.
Kesikli oklar `[H]`'dir: bir dosyada beyan edilip başka birinde kullanılan
bir ad. Bir C / C++ `#include` yalnız depodaki tam olarak bir dosyaya
çözüldüğünde `[K]`'dır; çözüldüğü include kökleri kaynaklarıyla yazdırılır,
belirsiz ya da çözülmemiş include'lar çizilmez, kör nokta olarak sayılır. Bir
Rust `mod x;` ya da `use crate::…` / `use <crate>::…` depodaki bir crate'in
dosyasına ulaştığında `[K]`'dır; Rust hiç `[H]` ad kenarı almaz — gerçek bir
depoda denetlenen her durumda yanlıştılar. Yalnız `[K]` kenarlar döngü
oluşturur; bir `[H]` döngü bir **aday**dır ve bir okuyucu doğrulayana kadar
öyle anılır.
