> Bu sayfa skill/rontgen/references/okuma.md dosyasının çevirisidir; kaynak İngilizce metindir.

# Okuma — adım 4'ün tamamı

En üstteki sıcak noktaların her biri için (genellikle beşi yeter) dosyayı
açın ve yanıtlayın: neden sorumlu, bilmemesi gereken neyi biliyor, burada
bir değişiklik başka yerde neyi bozabilir. Birlikte değişme tablosunu kodla
karşılaştırın: görünür bir bağımlılık olmadan birlikte değişen bir çift gizli
bir sözleşmedir — onu bulun ve adlandırın. Git olmadan ne sıcak nokta ne de
birlikte değişme tablosu vardır: modülleri `[K]` giren bağ sayısına göre
sıralayın (`yapi.md` bunu modül başına verir), sonra modül içinde dosyaları
boyuta ve onları adlandıran bir test olmamasına göre sıralayın ve sıranın
bu olduğunu yazın.

İlk sıcak noktadan önce projenin **kendi gezinme belgelerini** açın: bir
belge dizini, katkıcılar için bir kod haritası, bir "komut ekleme" denetim
listesi. Bunlar iddiadır, her iddia gibi kodla karşılaştırılır, ama eksenin
yazıya döküldüğü yer onlardır. Bir koşu 900 satır kod okudu ve belgelerdeki
bir modül haritasının ilk cümlesinde söylediği ilkeyi kaçırdı.
`belge.md` belgeleri andıkları var olan kod yolu sayısına göre sıralar;
o depoda modül haritası birinci geldi. Hiçbir belgenin anmadığı bir modül,
belgelerin yardım edemediği yerdir; var olmayan, adı geçen bir yol açılana
dek `[H]`'dir — çoğu eskimiş kod değil, koşu çıktıları ve yer tutuculardı.
Sonra haritayı izleyin: tasarım olarak listelediği belgeleri (yerleşim,
bellek, kalıcılık) betimledikleri koddan önce açın. İkinci bir koşu haritayı
açtı, bağlantılarını izlemedi ve depolama yerleşimini, çalışma zamanını ve
çoğaltmayı kaçırdı — her biri bir belge ötedeydi. `belge.md`'deki kırık bir
bağlantı, kümenin kaybettiği bir belgedir; haritanın göstereceği yerde bunu
söyleyin.
Bir değişikliğin dokunduğu yerlerin denetim listesi ("komut ekleme": on iki
dosya, her biri atlanan bir adımı neyin yakaladığıyla) projenin kendi
birlikte değişme tablosudur; git olmadan birlikte değişme tablosunun yerini
tutar. Listenin hiçbir şeyin yakalamadığını işaretlediği bir adım gizli bir
sözleşmedir: kodda denetleyin.

Okurken projenin **kendi tasarım dağarcığını** arayın: numaralı kararlar
(`ADR-030`), katman adları (`L0`–`L4`), yorumlarda yinelenen ilke kodları
(`P3`) ve o belgelerdeki adlandırılmış değişmezler. Bunlar yazarların
düşündüğü eksendir; yalnızca dizinler boyunca çizilmiş bir harita doğru olup
yine de onu kaçırabilir. Her birini sözlükte, tanımlandığı yerle birlikte
adlandırın. Deponun kendi mimari belgeleri varsa, belirttikleri tarihi son
commit ile karşılaştırın: kendini güncel sayan ama geçmişin büyük bölümünden
eski olan bir belge bir bulgudur. Git olmadan yaşı ölçülmemiştir; bir
kopyanın dosya zamanları ölçü değildir.

**Açtığınız her aralığı** `okunan.tsv`'ye, atıf yapacağınız her satırı
`atiflar.tsv`'ye, ilerledikçe **kaydedin**. Ölçülen kaynak olmayan
dosyalardaki aralıklar (bir derleme betiği, bir tablo) da oraya aittir: ayrı
sayılırlar ve payı asla yükseltmezler. İkisi de birer satırdır; hiçbiri
sonradan dürüstçe yeniden kurulamaz. Bir çapa bir satırdaki metni kanıtlar,
onu hangi işlevin içerdiğini değil: aynı metin dosyada iki kez geçiyorsa,
cümle onu kapsayan işlevi adlandırır. `atif.py` böyle çapalar için uyarır
(`COKLU`); satırın daha uzun bir parçasını seçin.
