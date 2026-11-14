> Bu sayfa skill/rontgen/references/teslim.md dosyasının çevirisidir; kaynak İngilizce metindir.

# Atıflar ve teslim — adım 6'nın ayrıntıları

**Bir iddia, bir çapa.** Atıf yapılan satır yalnızca üzerinde olanı
destekler: bir bildirim "burada bildirilmiş"i, bir başlık yorumu yalnızca
kendisini destekler. Daha fazlasını söyleyen bir cümle ya da tablo hücresi —
bir liste, bir sayım, bir "asla", bir "bu yüzden" — her parçayı gösteren
satırlara ya da onları içeren bir aralığa atıf yapar ya da `[H]` taşır.
`atif.py` çapanın hâlâ satırında olduğunu denetler; cümlenin ondan çıkıp
çıkmadığını denetleyemez.
İkinci bir okuyucu karşısında en sık iki biçim başarısız olur: bir satırın
"yakınına" atıf (`file.c:490 civari`) — satırın kendisine ya da bir aralığa
atıf yapın, asla yaklaşık birine değil — ve tek bir yerden genelleme ("tüm
`*.ctab`", "her zaman") — kaç yere baktığınızı söyleyin ya da `[H]` ile
etiketleyin. Üçüncü bir biçim: doğru satırın üzerine bırakılmış bir niyet,
bir kapsam ya da bir süreç notu ("bilerek", "tek giriş", "günlüğe
kaydedildi"). Bunların hiçbiri bir satırda değildir; onları atıftan ayrı
yazın ya da `[H]` ile etiketleyin.

`kapsam.md` ayrıca **atıf yapılmış ama okunmamış** satırları listeler:
`okunan.tsv`'deki hiçbir aralığın içermediği bir çapa. Her biri ya bağlamı
okunmadan atıf yapıldı ya da aralığı hiç yazılmadı; onu açın ya da
okuduğunuz aralığı kaydedin.

Git olmadan aynı dört komut çalışır: çapalar dosyalara oldukları hâliyle
bağlanır ve commit'siz olarak etiketlenir ve bir dosyanın okunduktan sonra
değişip değişmediği (`DEGISTI`, `BAYAT`) ölçülmemiştir; yalnızca yer
değiştirmiş bir çapa yakalanır.

Denetim listesi belgelerin yanına kaydedilebilir: `atif.py` onu atıf olarak
okumaz, başka bir belgeyi gösteren bir `doc.md:12`'yi de. Çıktı klasöründeki
çekirdeğin kendi raporlarını ve alıntılanmış bir satırı da okumaz: bir
betiğin iletisini bir `>` satırında alıntılayın, yoksa sizin atfınız olarak
sayılır.

**Bir tablo hücresi bir iddiadır.** Bir koşuda kör bir okuyucunun hatalı
bulduğu her cümle bir tablo hücresiydi — bir rol, bir değişken listesi, bir
kısaltma — ve atıf yapılan satır onun yalnızca bir kısmını içeriyordu.
Hücrenin tamamını gösteren alana ya da aralığa atıf yapın ya da fazla
sözcükleri çıkarın. `--ornek` artık belgelerde tablo satırları varsa onlara
denetim listesinin en az üçte birini ayırıyor.

**Bir imza bir adı destekler, bir davranışı değil.** İki depoda dört kör
denetim boyunca skill'in en sık kaçırdığı şey, bir işlevin ya da bir tipin
bildirim satırına, ne yaptığı için atıf yapılmasıydı ("`Run` argümanları
seçeneklere çevirir", "`rebuildImpl`: tara, derle, yaz"). Bildirim adı ve
parametreleri gösterir; işlevin ne yaptığı gövdesindedir. Bunu yapan
satırların aralığına atıf yapın ya da yalnızca orada bildirildiğini söyleyin.

**Ölçülmüş bir sayı raporunu adlandırır.** En sık ikinci kaçırma, bir kod
atfının yanına, sanki satır onu gösteriyormuş gibi yazılmış bir sayımdı
(satırlar, commit'ler, dosya çiftleri, "en büyük sıcak nokta"). Sayıyı
kaynağıyla (`rontgen.md`, `yapi.md`) yazın ve kod atfını kodun söylediği şey
için saklayın.
