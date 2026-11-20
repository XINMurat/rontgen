> Kaynak: skill/rontgen/references/okuma.md · sha256:1fd448e41198 — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Okuma — adım 4'ün tamamı

En üstteki sıcak noktaların her biri için (genellikle beş yeter) dosyayı açın
ve yanıtlayın: neden sorumlu, bilmemesi gereken neyi biliyor, burada bir
değişiklik başka nerede neyi bozabilir. Birlikte değişme tablosunu kodla
karşılaştırın: görünür bir bağımlılık olmadan birlikte değişen bir çift gizli
bir sözleşmedir — onu bulun ve adlandırın. Git olmadan sıcak nokta ve birlikte
değişme tablosu yoktur: modülleri `[K]` giren bağ sayısına göre sıralayın
(`yapi.md` bunu modül başına verir), sonra modül içindeki dosyaları boyuta ve
onları adlandıran bir test olmamasına göre sıralayın, ve sıranın bu olduğunu yazın.

İlk sıcak noktadan önce projenin **kendi gezinme belgelerini** açın: bir
belge dizini, bir katkıcının kod haritası, bir "komut ekleme" kontrol
listesi. Bunlar her iddia gibi kodla karşılaştırılan iddialardır, ama eksenin
yazıya döküldüğü yerdir. Bir koşu 900 satır kod okudu ve belgelerdeki bir
modül haritasının ilk cümlesinde söylediği ilkeyi kaçırdı.
`belge.md` belgeleri, var olan kaç kod yolunu adlandırdıklarına göre sıralar;
o depoda modül haritası ilk geldi. Hiçbir belgenin adlandırmadığı bir modül,
belgelerin yardım edemediği yerdir; var olmayan adlandırılmış bir yol açılana
kadar `[H]`'dir — çoğu bayat kod değil, koşu çıktıları ve yer tutuculardı.
Sonra haritayı izleyin: tasarım olarak listelediği belgeleri (yerleşim,
bellek, dayanıklılık) betimledikleri koddan önce açın. İkinci bir koşu
haritayı açtı, bağlantılarını izlemedi ve depolama yerleşimini, çalışma
zamanını ve çoğaltmayı kaçırdı — her biri bir belge uzaktaydı. `belge.md`'deki
kırık bir bağlantı, kümenin kaybettiği bir belgedir; haritanın göstereceği
yerde bunu söyleyin.
Bir değişikliğin dokunduğu yerlerin kontrol listesi ("komut ekleme": on iki
dosya, her biri atlanan bir adımı neyin yakaladığıyla) projenin kendi birlikte
değişme tablosudur; git olmadan birlikte değişme tablosunun yerini tutar.
Hiçbir şeyin yakalamadığı diye işaretlediği bir adım gizli bir sözleşmedir:
onu kodda denetleyin.

Okurken projenin **kendi tasarım sözcük dağarcığını** arayın: numaralı
kararlar (`ADR-030`), katman adları (`L0`–`L4`), yorumlarda tekrarlayan ilke
kodları (`P3`) ve o belgelerdeki adlandırılmış değişmezler. Bunlar yazarların
düşündüğü eksendir; yalnız dizinler boyunca çizilmiş bir harita doğru olup yine
de onu kaçırabilir. Her birini sözlükte, tanımlandığı yerle birlikte
adlandırın. Deponun kendi mimari belgeleri varsa, belirttikleri tarihi son
commit'le karşılaştırın: kendini güncel sayan ama geçmişin büyük kısmından
eski olan bir belge bir bulgudur. Git olmadan yaşı ölçülmemiştir; bir
kopyanın dosya zamanları yaşı değildir.

**Açtığınız her aralığı** `okunan.tsv`'ye ve atıf yapacağınız her satırı
`atiflar.tsv`'ye ilerledikçe kaydedin. Ölçülen kaynak olmayan dosyalardaki
aralıklar (bir derleme betiği, bir tablo) da oraya aittir: ayrı sayılırlar ve
payı asla artırmazlar. İkisi de birer satırdır; hiçbiri sonradan dürüstçe
yeniden kurulamaz. Bir çapa bir satırdaki metni kanıtlar, onu hangi
fonksiyonun tuttuğunu değil: aynı metin dosyada iki kez geçiyorsa, cümle onu
kapsayan fonksiyonu adlandırır. `atif.py` böyle çapalar için uyarır
(`COKLU`); satırın daha uzun bir parçasını seçin.
