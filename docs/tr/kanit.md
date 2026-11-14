> Bu sayfa skill/rontgen/references/kanit.md dosyasının çevirisidir; kaynak İngilizce metindir.

# Kuralların arkasındaki kanıt

SKILL.md'deki ve bu başvurulardaki her kural aşağıdaki bir gözlemden gelir.

Taslak 0.4. Henüz ailenin bir üyesi değil: git deposu yok, iki dilli belge
yok, paket yok, CI yok, token bütçesi yok, şema yok, değerlendirme (eval) yok.

Şimdiye dek kanıt ve sınırları:

- Çekirdek beş depoda (C#/TypeScript, C#/SQL, Python) çalıştı.
  O koşu bunlardan birinde kaynak olarak sayılmış üretilmiş migration
  dosyaları buldu; dışlama kuralı ondan gelir. C ağırlıklı bir depoda (522 C
  dosyası) `#include` çözümlemesi `[K]` modül kenarlarını 1'den 123'e
  çıkardı; `#include` satırlarına karşı elle denetlenen on kenarın hepsi
  tuttu. Adı iki kök altında var olan include'lar (orada 35 tane) kenar
  almaz, oysa derlemenin kök sırası onları belirlerdi. Hiç git olmayan bir
  dizinde (Rust ve C#, 575 kaynak dosyası) iki çekirdek betik de çalıştı ve
  dört geçmiş bölümü "ölçülmedi" dedi; o koşu ayrıca derleme çıktısı olarak
  dışlanmış olan `src/bin`'in Rust kaynağı tuttuğunu gösterdi. C ağırlıklı
  depoda yeni bir okuyucu, davranışın betiklerin saymadığı dört kurum içi
  biçimdeki 300 dosyada yaşadığını buldu; bir sonda 40 kenarından 29'unu
  onlara kaybetti. Onları `extra_sources` içinde adlandırmak 290'ını ölçüme
  kattı ve kaybedilen kenarları 13'e indirdi; var olan her dosyanın bir sonda
  kenarının ucu olmasına izin vermek onları 0'a indirdi. Aynı koşunun
  kaydedilmiş denetim listesi bir sonraki denetimde 13 yanlış "çapasız" atıf
  üretti ve kökteki bir `CMakeLists.txt` belirsiz sayıldı; ikisi de düzeltildi.
  Java ve Go örüntüleri yalnızca öz-sınamalarla denendi. Git olmayan bir Rust
  deposunda (291 Rust dosyası) ilk ana hat genel (generic) kodun
  tanımlarının yarısını kaçırdı ve örneklenen 10 ad kenarından 8'i yanlıştı;
  Rust modülünden (`mod` / `use` çözümlemesi, ad vekili yok) sonra ana hat
  denetlenen dört dosyadaki her tanımı buldu ve örneklenen kenarların 10'da
  10'u tuttu.
- Okuma yarısı **beş kez** yapıldı. Beşincisi Rust koşusunu o kuralla
  yineledi: önce modül haritasını açtı, kaçırılan 8 noktadan 3'ünü adlandırdı
  (önceden 0) ve 20'den 16'sını tuttu; geri kalanı bir bağlantı daha
  ötedeydi, haritayı izle kuralı buradan gelir. C ağırlıklı depoda yukarıdaki
  kurallardan sonra yapılan ikinci yeni bir koşu kör denetiminde 20'den
  12'sini tuttu. Rust deposunda yeni bir koşu (satırların %0.4'ü okundu, git
  yok) 20'den 15'ini tuttu ve mimari belgesiyle hiçbir yerde çelişmedi, ama
  ilkesini, çalışma zamanını, depolama yerleşimini ve çoğaltmayı kaçırdı:
  bunlar açmadığı belgelerdeydi. Gezinme belgeleri kuralı ondan gelir.
  Daha önce, iki kez: Bir kez okuyucusunun zaten tanıdığı bir depoda
  (kaynak satırlarının %6'sı okundu, başka kimse denetlemedi). Bir kez de
  hiç görmediği C ağırlıklı depoda yeni bir oturumla: kaynak satırlarının
  %1.9'u okundu, 30 çapanın 30'u yerinde ve başka bir oturumun (bir kişinin
  değil) atıf yapılmış 20 cümle üzerindeki kör denetimi tutan 9, tutmayan 1
  ve satırının gösterdiğinden fazlasını söyleyen 10 cümle buldu — "bir
  iddia, bir çapa" kuralı oradan gelir. Oturumun haritası mekanizma
  bakımından deponun kendi mimari belgeleriyle örtüştü ve yazarların tasarım
  dağarcığını (katmanlar, ilkeler, numaralı kararlar) kaçırdı; dağarcık
  kuralı oradan gelir. Kör okuması kusurluydu: deponun `CLAUDE.md`'si
  başlangıçta bağlamına kendiliğinden yüklenmişti.
- **Bu skill ile ve onsuz**, bir kez, hiçbir oturumun görmediği küçük bir C#
  kütüphanesinde (1,944 satır), iki yeni oturum aynı görevi aldı. Hangisinin
  neyi yazdığı söylenmeyen kör bir okuyucu, skill'in kolundan atıf yapılmış
  20 cümleden 19'unu, diğerinden 20'den 16'sını tuttu; skill'in kolu hiç
  yanlış iddiada bulunmadı, diğeri bir kez. Ama skill olmayan kol koddan
  yazılmış bir başvuru listesinin 12 noktasının hepsini kapsadı (skill'in
  kolu 10) ve daha çok risk buldu. Burada skill yazılanı daha doğru yaptı,
  anlaşılanı daha geniş değil; doğruluğun geldiği yer, teslimden önce
  çalıştırılan kendi ikinci okuyucusuydu (ilk taslağı 12'den 6'sını tuttu).
  Tek depo, tek örnek: bir hipotez, skill'in genel bir ölçümü değil. Skill
  olmayan ama teslimden önce cümlelerinden on ikisini ikinci bir okuyucuya
  denetletmesi söylenen üçüncü bir kol, yeni bir kör örneklemde skill'in
  17'sine karşı 20'den 16'sını tuttu ve 12 noktanın hepsini kapsadı. Bütünü
  okunacak kadar küçük bir depoda skill'in ölçülebilir kazancı o tek adımdı;
  ölçme yarısı orada sınanmadı. Aynı belgeler iki örneklemde 19 ve 17 aldı:
  iki üç puanlık farklar gürültünün içindedir.
- **Aynı üç kol büyük bir depoda** (Rust, yaklaşık 108k satır, mimari
  belgesi tüm geçmişten silinmiş). Üçü de kaynağın %2'sinden azını okudu ve
  aynı yolu yürüdü (tuş, komut, düzenleme).
  Kör bir okuyucu skill'in kolundan 20'den 18'ini, düz koldan 15'ini ve
  ikinci okuyuculu koldan 20'sini tuttu; hiçbiri yanlış iddiada bulunmadı.
  Silinen belgeden yazılmış 14 noktalık bir listeye karşı 5.5, 6 ve 4.5
  kapsadılar. Hiçbiri belgenin adlandırdığı tasarım fikirlerini (işlevsel
  çekirdek, görünüm başına seçimler, bölme başına bir görünüm) bulamadı.
  Yani büyük bir depoda da ölçme yarısı haritayı genişletmedi ve ikinci bir
  okuyucu çalıştıran kol en doğrusuydu. Skill'in kolu o sefer kendi ikinci
  okuyucusunu atladı; ikinci okuyuculu kol başka bir kolun aynı kopyasını
  okudu; belgenin eski bir sürümü geçmişte başka bir yol altında kalmıştı.
  Bunların hiçbiri skill'in lehine değil. Birlikte ele alındığında: iki kez
  kazanç gösteren tek adım teslimden önceki ikinci okuyucudur.
- Bir sonda yazıldı (kurum içi yapıt adları → kullanıcıları, 40 kenar,
  öz-sınama 6/6). Sondaların maliyetini karşılayıp karşılamadığı hâlâ bir
  hipotez.
- **Yalnızca belgeleri olan bir okuyucu** (kod yok) o büyük depo hakkındaki
  aynı sekiz soruyu yanıtladı: skill'in belgelerinden 8'de 4.5, diğer iki
  koldan 3 ve 2. Farkın bir kısmı yazılı sayfalardan değil, üretilmiş işlev
  ana hattından geldi; bir ayrıntı okuyucuyu bir neden konusunda yanılttı ve
  hiçbir kol görünüm başına durumun nerede yaşadığını söylemedi. Mimari
  sayfası ve "raporları saklayın" kuralı ondan gelir. Kod erişimiyle üç
  okuyucu da sekizini de yanıtladı: o test tavanındaydı.
- **Aynı büyük depoda 0.5 sürümü** (yeni kopya, tek koşu): oturum kendi
  ikinci okuyucusunu çalıştırdı (12'den 11'i tuttu, kaymış bir satır
  düzeltildi) ve mimari sayfasını yazdı. 14 noktalık başvuru listesine karşı
  10'unu kapsadı (önceki skill koşusu 5.5): görünüm başına seçimler, çapa ve
  baş, rope ve küresel düzenleyici durumu artık bulunmuştu. Yalnızca
  belgeleri olan bir okuyucu 8'den 5.5'ini yanıtladı (önceden 4.5; diğer
  kollar 3 ve 2). Kör bir okuyucu cümlelerinin 20'den 17'sini ve ikinci
  okuyuculu ama skill'siz kolun 20'den 20'sini tuttu; üç kaçırma, atıf
  yapılan satırı hücrenin yalnızca bir kısmını içeren tablo hücreleriydi.
  Koda erişimi olmayan bir okuyucu için daha geniş ve daha yararlı; tablolarında
  henüz o kadar doğru değil.
- **Denetim listesinde tablo satırları ağırlıklandırılmış ikinci bir 0.5
  koşusu**: ikinci okuyucu üç tablo hücresi yakaladı ve düzeltildiler, yine
  de kör okuyucu yine 20'den 17'sini tuttu (skill olmayan kol yine 20).
  Üçten ikisi sahip olunan tipin kendi alanına atıf yapan "sahibi" hücreleriydi:
  mimari şablonunun sahiplik sütunu, atfının taşıyamayacağı bir iddiaya davet
  ediyordu. Şablon artık o hücre için sahibin alanına atıf yapıyor.
- **Sahiplik tablosu her sahibin alanına atıf yapan üçüncü bir koşu**: kör
  bir okuyucu skill'in belgelerinden 20'den 19'unu ve skill olmayan koldan
  20'den 19'unu tuttu; hiçbir sahiplik hücresi hatalı bulunmadı. Kapsam
  14'ten 8.5 ve yalnızca belgeli okuyucu 8'den 4.5 idi — 0.5'in üç koşusu
  boyunca bunlar aşağı kaydı (10, 9.5, 8.5; 5.5, 5, 4.5), çünkü her koşu
  yazmak için farklı bir modül seçti. Üç örneklem bir eğilimi gürültüden
  ayıramaz.
- **Toplam beş 0.5 koşusu.** Kör doğruluk 20'den 17, 17, 19, 19, 18 (skill
  olmayan kol, aynı listeler: 20, 20, 19, 18, 20); kapsam 14'ten 10, 9.5,
  8.5, 7.5, 10; yalnızca belgeli okuyucu 8'den 5.5, 5, 4.5, 4, 5. Üçüncü
  koşudan sonraki düşüş gürültüydü: beşincisi 10'a geri döndü. Bir koşu
  kapsamda yaklaşık artı eksi 1.5 değerindedir; bir değişikliği birkaç
  koşuya bakarak yargılayın.
- **0.6 (paket bildirimleri, bir değerin nasıl yapıldığı, giren bağ sayısı ×
  satır ile modül seçimi)**, büyük depoda üç koşu: kapsam 14'ten 11.5, 12.5,
  10.5 (0.5: 9.1); yalnızca bir paket bildirimi özelliğinde görünen uçbirim
  bağı üçten ikisinde bulundu; ana düzenleme arayüzü üçünde de adlandırıldı.
  Kör doğruluk 20'den 19, 19, 18 (skill olmayan kol 19, 19, 20).
- **İkinci bir dil** (bir Go paketleyicisi (bundler), ~139k satır): çekirdek
  önce 2 çözülmüş kenar çizdi, çünkü Go importları bir paketi modül yoluyla
  adlandırır; go.mod üzerinden çözümleme 193 verdi. Yalnızca giren bağ
  sayısıyla modül seçiminde koşu bir günlükleme yardımcısını yazdı ve 14
  noktadan 2'sini kapsadı (skill olmayan kol 3); satırlarla
  ağırlıklandırılınca ayrıştırıcıyı seçti ve 7'sini kapsadı.
