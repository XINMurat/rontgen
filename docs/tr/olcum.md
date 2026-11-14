> Bu sayfa skill/rontgen/references/olcum.md dosyasının çevirisidir; kaynak İngilizce metindir.

# Ölçme — adım 1 ve 2'nin ayrıntıları

SKILL.md döngüyü tutar; bu dosya çekirdeğin koşularının öğrettiği
ayrıntıları tutar.

## Çalıştırma ve yapılandırma

Onları herhangi bir yerden düz `python scripts/<name>.py` olarak çalıştırın;
birbirlerini import ederler, bu yüzden `python -I` başarısız olur. Depoya
yazamıyorsanız `rontgen.config.json`'u ve sondaları çıktı klasöründe tutun
ve `rontgen.py`, `yapi.py` ve `belge.py`'ye `--config` verin; `probe_results`
önce yapılandırma dosyasının yanında, sonra depo kökünden aranır. `atif.py`
ve `kapsam.py` yapılandırma almaz: onu taşıyan çıktı klasörünü okurlar.

Önce bunları çalıştırın, kodu sonra okuyun: önce okumak sizi açtığınız
dosyaya çapalar. Git geçmişi yoksa değişim sıklığı, birlikte değişme ve
bilgi **ölçülmemiştir**, sıfır değil. Git olmadan dosyalar dizinden okunur;
derleme ve gizli dizinlere girilmez ve her biri listelenir.

Sonra **"Olcume girmeyenler"** listesini okuyun. Betikler üretilmiş
görünenleri dışlar (paketler (bundle), migration'lar, `*.Designer.cs`,
üretilmiş olarak işaretli dosyalar). Listede elle yazılmış bir şey varsa ya
da üretilmiş bir şey yoksa, düzeltmeyi `exclude_globs`'a koyun ve yeniden
çalıştırın — hatayı ileri taşımayın. Bilerek ölü bırakılmış elle yazılmış kod
(bir `_archive/`, kenara alınmış bir kopya) aynı biçimde, sizin kararınızla
dışlanır: sıcak noktaları ve kapsamı çarpıtır ve belgeler onu haritalamak
yerine kapsam dışı olarak adlandırır.
Canlı olan dışarıdan alınmış kod (projenin çağırdığı budanmış bir üst akış
kütüphanesi) ölçülmeye devam eder; okunmadan bırakılabilir, ama belgeler
projenin onu ne için kullandığını söyler — bir koşu böyle bir kopyaya "kapsam
dışı" dedi ve mimari ona dayanıyordu.
**Sınıflandırılmamış uzantıları** da aynı biçimde okuyun: davranış betiklerin
kaynak olarak tanımadığı dosyalarda yaşıyorsa (bir DSL, bir tablo biçimi),
onları `extra_sources` içinde adlandırın. O zaman sayılır, ölçülür ve bir
sonda kenarının ucu olabilirler; asla ayrıştırılmazlar. Program `main`
dışında bir yerden başlıyorsa (bir çekirdek girişi, bir eklenti kancası), o
işlevi `entry_points` içinde adlandırın; giriş yüzeyi onu satırıyla
gösterir ve bulunamayan bir ad bu hâliyle bildirilir. Giriş adları asla
tahmin edilmez. Bir `main` örüntüyle bulunur (C'de her yerde, Rust'ta
yalnızca bir ikili hedefte); kütüphanelerde de geçen bir ad yoluyla verilir,
`src/plugins/*:start`.

## Kenar katmanları

Düz oklar `[K]`'dir: depoda çözülen bildirilmiş bir bağımlılık. Kesik oklar
`[H]`'dir: bir dosyada bildirilip başka bir dosyada kullanılan bir ad. Bir C
/ C++ `#include`, yalnızca depoda tam olarak bir dosyaya çözüldüğünde
`[K]`'dir; çözüldüğü include kökleri kaynaklarıyla birlikte yazdırılır ve
belirsiz ya da çözülmemiş include'lar çizilmez, kör nokta olarak sayılır.
Bir Rust `mod x;` ya da `use crate::…` / `use <crate>::…`, depodaki bir
crate'in bir dosyasına ulaştığında `[K]`'dir; Rust hiç `[H]` ad kenarı
almaz — gerçek bir depoda denetlenen her durumda yanlıştılar. Döngüyü
yalnızca `[K]` kenarlar oluşturur; bir `[H]` döngüsü bir **aday**dır ve bir
okuyucu doğrulayana dek öyle anılır.
