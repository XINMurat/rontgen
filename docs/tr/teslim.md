> Kaynak: skill/rontgen/references/teslim.md · sha256:b8d211d9b4bf — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Atıflar ve teslim — adım 6'nın ayrıntıları

**Bir iddia, bir çapa.** Atıf yapılan bir satır yalnız üzerindekini
destekler: bir bildirim "burada bildirildi"yi destekler, bir başlık yorumu
yalnız kendini. Daha fazlasını söyleyen bir cümle ya da tablo hücresi — bir
liste, bir sayı, bir "asla", bir "bu yüzden" — her parçayı gösteren satırlara
ya da onları içeren bir aralığa atıf yapar, ya da `[H]` taşır. `atif.py`
çapanın hâlâ kendi satırında olduğunu denetler; cümlenin ondan çıktığını
denetleyemez.
İki biçim ikinci okuyucuda en sık düşer: bir satırın "yakınına" atıf
(`file.c:490 civari`) — satırın kendisine ya da bir aralığa atıf yapın, asla
yaklaşık birine değil — ve tek bir yerden genelleme ("tüm `*.ctab`",
"her zaman") — kaç yere baktığınızı söyleyin ya da `[H]` ile etiketleyin.
Üçüncü bir biçim: üzerine bir niyet, bir kapsam ya da bir süreç notu konmuş
doğru satır ("bilerek", "tek giriş", "günlüğe kaydedildi"). Bunların hiçbiri
bir satırda değildir; onları atıftan ayrı yazın ya da `[H]` ile etiketleyin.

`kapsam.md` ayrıca **atıf yapılmış ama okunmamış** satırları listeler:
`okunan.tsv`'deki hiçbir aralığın içermediği bir çapa. Her biri ya bağlamı
okunmadan atıf yapıldı ya da aralığı hiç yazılmadı; onu açın ya da okuduğunuz
aralığı kaydedin.

Git olmadan aynı dört komut çalışır: çapalar dosyaların şimdiki haline bağlanır
ve commit'siz diye etiketlenir, ve bir dosyanın okunduktan sonra değişip
değişmediği (`DEGISTI`, `BAYAT`) ölçülmemiştir; yalnız taşınmış bir çapa yakalanır.

Kontrol listesi belgelerin yanına kaydedilebilir: `atif.py` onu, ya da başka
bir belgeyi gösteren bir `doc.md:12`'yi, atıf olarak okumaz.
Çıktı klasöründeki çekirdeğin kendi raporlarını da, alıntılanmış bir satırı da
okumaz: bir betiğin iletisini bir `>` satırında alıntılayın, yoksa sizin
atfınız olarak sayılır.

**Bir tablo hücresi bir iddiadır.** Bir koşuda kör okuyucunun hatalı bulduğu
her cümle bir tablo hücresiydi — bir rol, bir değişken listesi, bir kısaltma —
ve atıf yapılan satırı onun yalnız bir kısmını tutuyordu. Hücrenin tamamını
gösteren alana ya da aralığa atıf yapın, ya da fazla sözcükleri çıkarın.
`--ornek` artık belgelerde tablo satırları varsa onlara kontrol listesinin en
az üçte birini veriyor.

**Bir imza bir adı destekler, bir davranışı değil.** İki depoda dört kör
denetim boyunca becerinin en sık kaçırdığı şey, bir fonksiyonun ya da bir
türün bildirim satırının onun ne yaptığı için atıf yapılmasıydı ("`Run`
argümanları seçeneklere çevirir", "`rebuildImpl`: tara, derle, yaz").
Bildirim adı ve parametreleri gösterir; fonksiyonun ne yaptığı gövdesindedir.
Bunu yapan satırların aralığına atıf yapın, ya da yalnız orada bildirildiğini söyleyin.

**Ölçülmüş bir sayı raporunu adlandırır.** En sık ikinci kaçırılan şey, bir
kod atfının yanına, sanki satır onu gösteriyormuş gibi yazılmış bir sayıydı
(satırlar, commit'ler, dosya çiftleri, "en büyük sıcak nokta"). Sayıyı
kaynağıyla (`rontgen.md`, `yapi.md`) yazın ve kod atfını kodun söylediği şey
için saklayın.
