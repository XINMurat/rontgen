> Kaynak: skill/rontgen/references/kanit.md · sha256:f00fb6ba340f — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Kuralların arkasındaki kanıt

SKILL.md'deki ve bu başvurulardaki her kural aşağıdaki bir gözlemden gelir.

Taslak 0.4. Henüz ailenin bir üyesi değil: git deposu yok, iki dilli belge
yok, paket yok, CI yok, token bütçesi yok, şema yok, değerlendirme (eval) yok.

Şimdiye dek kanıt ve sınırları:

- Çekirdek beş depoda çalıştı (C#/TypeScript, C#/SQL, Python).
  O koşu, birinde kaynak olarak sayılmış üretilmiş migration dosyaları buldu;
  dışlama kuralı ondan gelir. C ağırlıklı bir depoda (522 C dosyası)
  `#include` çözümlemesi `[K]` modül kenarlarını 1'den 123'e çıkardı; `#include`
  satırlarına karşı elle denetlenen on kenarın hepsi tuttu. Adı iki kök altında
  bulunan include'lar (orada 35 tane) kenar almaz, oysa derlemenin kök sırası
  onlara karar verirdi. Hiç git'i olmayan bir dizinde (Rust ve C#, 575 kaynak
  dosyası) iki çekirdek betik de çalıştı ve dört geçmiş bölümü "ölçülmedi"
  dedi; o koşu ayrıca `src/bin`'in derleme çıktısı olarak dışlanmış Rust
  kaynağı tuttuğunu gösterdi. C ağırlıklı depoda yeni bir okuyucu, davranışın
  betiklerin saymadığı dört kurum içi biçimdeki 300 dosyada yaşadığını buldu;
  bir sonda 40 kenarının 29'unu onlara kaptırdı. Onları `extra_sources`
  içinde adlandırmak 290'ını ölçüme getirdi ve kaybedilen kenarları 13'e
  indirdi; var olan herhangi bir dosyanın bir sonda kenarını bitirmesine izin
  vermek onları 0'a indirdi. Aynı koşunun kaydedilmiş kontrol listesi bir
  sonraki denetimde 13 sahte "çapasız" atıf üretti ve kökteki bir
  `CMakeLists.txt` belirsiz sayıldı; ikisi de düzeltildi.
  Java ve Go örüntüleri yalnız öz-testlerle sınanıyor. Git'i olmayan bir Rust
  deposunda (291 Rust dosyası) ilk iskelet generic kodun tanımlarının yarısını
  kaçırdı ve örneklenen 10 ad kenarının 8'i yanlıştı; Rust modülünden sonra
  (`mod` / `use` çözümlemesi, ad vekil ölçüsü yok) iskelet denetlenen dört
  dosyadaki her tanımı buldu ve örneklenen 10 kenarın 10'u tuttu.
- Okuma yarısı **beş kez** yapıldı. Beşincisi Rust koşusunu o kuralla
  yineledi: önce modül haritasını açtı, kaçırılan 8 noktanın 3'ünü adlandırdı
  (önce 0'dı) ve 20'nin 16'sını tuttu; geri kalanı bir bağlantı daha
  ötedeydi, haritayı izleme kuralı oradan gelir. Yukarıdaki kurallardan sonra
  C ağırlıklı depoda ikinci bir yeni koşu kör denetiminde 20'nin 12'sini
  tuttu. Rust deposunda yeni bir koşu (satırların %0.4'ü okundu, git yok)
  20'nin 15'ini tuttu ve mimari belgesiyle hiçbir yerde çelişmedi, ama
  ilkesini, çalışma zamanını, depolama yerleşimini ve çoğaltmayı kaçırdı:
  bunlar açmadığı belgelerdeydi. Gezinme belgeleri kuralı ondan gelir.
  Daha önce, iki kez: Bir kez okuyucusunun zaten bildiği bir depoda (kaynak
  satırlarının %6'sı okundu, başka kimse denetlemedi). Bir kez de yeni bir
  oturum tarafından, hiç görmediği C ağırlıklı depoda: kaynak satırlarının
  %1.9'u okundu, 30 çapanın 30'u yerinde, ve atıflı 20 cümlenin başka bir
  oturumca (bir kişi değil) yapılan kör denetimi 9'unun tuttuğunu, 1'inin
  tutmadığını ve 10'unun satırlarının gösterdiğinden fazlasını söylediğini
  buldu — "bir iddia, bir çapa" kuralı oradan gelir. Oturumun haritası
  mekanizmada deponun kendi mimari belgeleriyle örtüştü ve yazarların tasarım
  sözcük dağarcığını (katmanlar, ilkeler, numaralı kararlar) kaçırdı; sözcük
  dağarcığı kuralı oradan gelir. Kör okuması kusurluydu: deponun `CLAUDE.md`'si
  başlangıçta bağlamına otomatik olarak yüklenmişti.
- **Bu beceriyle ve onsuz**, bir kez, hiçbir oturumun görmediği küçük bir C#
  kütüphanesinde (1,944 satır), iki yeni oturum aynı görevi aldı. Hangisinin
  neyi yazdığı söylenmeyen kör bir okuyucu becerinin kolundan atıflı 20
  cümlenin 19'unu, diğerinden 20'nin 16'sını tuttu; becerinin kolu hiç yanlış
  iddiada bulunmadı, diğeri bir kez. Ama beceri olmayan kol koddan yazılmış
  bir referans listesinin 12 noktasının hepsini kapsadı (becerinin kolu 10)
  ve daha çok risk buldu. Burada beceri yazılanı daha doğru yaptı, anlaşılanı
  daha geniş değil; doğruluğun geldiği yer, teslimden önce çalıştırılan kendi
  ikinci okuyucusuydu (ilk taslağı 12'nin 6'sını tuttu). Bir depo, bir
  örneklem: genel olarak becerinin bir ölçümü değil, bir hipotez. Becerisiz
  ama teslimden önce cümlelerinin on ikisini bir ikinci okuyucuya
  denetletmesi söylenen üçüncü bir kol, yeni bir kör örneklemde becerinin
  17'sine karşı 20'nin 16'sını tuttu ve 12 noktanın hepsini kapsadı. Bütünüyle
  okunabilecek kadar küçük bir depoda becerinin ölçülebilir kazancı o tek
  adımdı; ölçme yarısı orada sınanmadı. Aynı belgeler iki örneklemde 19 ve 17
  aldı: iki üç farklar gürültünün içindedir.
- **Aynı üç kol büyük bir depoda** (Rust, yaklaşık 108k satır, mimari belgesi
  tüm geçmişten çıkarılmış). Üçü de kaynağın %2'sinden azını okudu ve aynı
  yolu yürüdü (tuş, komut, düzenleme). Kör bir okuyucu becerinin kolundan
  20'nin 18'ini, düz koldan 15'ini ve ikinci okuyuculu koldan 20'sini tuttu;
  hiçbiri yanlış iddiada bulunmadı. Çıkarılmış belgeden yazılmış 14 noktalık
  bir listeye karşı 5.5, 6 ve 4.5 kapsadılar. Hiçbiri belgenin adlandırdığı
  tasarım fikirlerini (işlevsel çekirdek, görünüm başına seçimler, bölme başına
  bir görünüm) bulmadı. Yani büyük bir depoda da ölçme yarısı haritayı
  genişletmedi ve ikinci okuyucu çalıştıran kol en doğrusuydu. Becerinin kolu
  o sefer kendi ikinci okuyucusunu atladı; ikinci okuyuculu kol başka bir
  kolun özdeş kopyasını okudu; belgenin eski bir sürümü geçmişte başka bir yol
  altında hayatta kalmıştı. Bunların hiçbiri beceriden yana değil. Hep birlikte:
  iki kez kazanç göstermiş tek adım teslimden önceki ikinci okuyucudur.
- Bir sonda yazıldı (kurum içi yapıt adları → kullanıcıları, 40 kenar, öz-test
  6/6). Sondaların zahmetine değip değmediği hâlâ bir hipotez.
- **Yalnız belgeleri olan bir okuyucu** (kod yok) o büyük depo hakkında aynı
  sekiz soruyu yanıtladı: becerinin belgelerinden 8'in 4.5'ini, diğer iki
  koldan 3 ve 2'sini. Farkın bir kısmı yazılı sayfalardan değil, üretilmiş
  fonksiyon iskeletinden geldi; bir ayrıntı okuyucuyu bir neden konusunda
  yanılttı; ve hiçbir kol görünüm başına durumun nerede yaşadığını söylemedi.
  Mimari sayfası ve "raporları saklayın" kuralı ondan gelir. Koda erişimle üç
  okuyucu da sekizinin hepsini yanıtladı: o test tavanındaydı.
- **Aynı büyük depoda sürüm 0.5** (yeni kopya, bir koşu): oturum kendi ikinci
  okuyucusunu çalıştırdı (12'nin 11'i tuttu, kaymış bir satır düzeltildi) ve
  mimari sayfasını yazdı. 14 noktalık referans listesine karşı 10 kapsadı
  (önceki beceri koşusu 5.5): görünüm başına seçimler, anchor ve head, rope ve
  global editör durumu artık bulunmuştu. Yalnız belgeleri olan bir okuyucu
  8'in 5.5'ini yanıtladı (önce 4.5; diğer kollar 3 ve 2). Kör bir okuyucu
  cümlelerinin 20'nin 17'sini ve ikinci okuyuculu ama becerisiz kolun 20'nin
  20'sini tuttu; üç kaçırma, atıf yapılan satırı hücrenin yalnız bir kısmını
  tutan tablo hücreleriydi. Koda erişimi olmayan bir okuyucu için daha geniş
  ve daha yararlı; tablolarında henüz o kadar doğru değil.
- **0.5'in ikinci koşusu, kontrol listesinde tablo satırları ağırlıklı**:
  ikinci okuyucu üç tablo hücresini yakaladı ve düzeltildiler, yine de kör
  okuyucu yine 20'nin 17'sini tuttu (beceri olmayan kol yine 20). Üçünden
  ikisi sahip olunan türün kendi alanına atıf yapan "sahibi" hücreleriydi:
  mimari şablonunun sahiplik sütunu, atfının taşıyamayacağı bir iddiayı davet
  ediyordu. Şablon artık o hücre için sahibin alanına atıf yapıyor.
- **Üçüncü bir koşu, sahiplik tablosu her sahibin alanına atıf yaparak**:
  kör bir okuyucu becerinin belgelerinden 20'nin 19'unu ve beceri olmayan
  koldan 20'nin 19'unu tuttu; hiçbir sahiplik hücresi hatalı bulunmadı.
  Kapsam 14'ün 8.5'iydi ve yalnız belgeli okuyucu 8'in 4.5'i — 0.5'in üç
  koşusu boyunca bunlar aşağı kaydı (10, 9.5, 8.5; 5.5, 5, 4.5), çünkü her
  koşu yazmak için farklı bir modül seçti. Üç örneklem bir eğilimi gürültüden ayıramaz.
- **Toplam beş 0.5 koşusu.** Kör doğruluk 20'nin 17, 17, 19, 19, 18'i (beceri
  olmayan kol, aynı listeler: 20, 20, 19, 18, 20); kapsam 14'ün 10, 9.5,
  8.5, 7.5, 10'u; yalnız belgeli okuyucu 8'in 5.5, 5, 4.5, 4, 5'i. Üçüncü
  koşudan sonraki düşüş gürültüydü: beşincisi 10'a geri döndü. Bir koşu
  kapsamda yaklaşık artı eksi 1.5 değerindedir; bir değişikliği birkaç koşu
  üzerinden değerlendirin.
- **0.6 (paket bildirimleri, bir değerin nasıl yapıldığı, giren bağ sayısı ×
  satırlarla modül seçimi)**, büyük depoda üç koşu: kapsam 14'ün 11.5, 12.5,
  10.5'i (0.5: 9.1); yalnız bir paket bildirimi özelliğinde görünen terminal
  bağı üçün ikisinde bulundu; ana düzenleme arayüzü üçünde de adlandırıldı.
  Kör doğruluk 20'nin 19, 19, 18'i (beceri olmayan kol 19, 19, 20).
- **İkinci bir dil** (bir Go paketleyicisi (bundler), ~139k satır): çekirdek
  önce 2 çözülmüş kenar çizdi, çünkü Go importları bir paketi modül yoluyla
  adlandırır; go.mod üzerinden çözümleme 193 verdi. Yalnız giren bağ sayısıyla
  modül seçiminde koşu bir günlükleme yardımcısını yazdı ve 14 noktanın 2'sini
  kapsadı (beceri olmayan kol 3); satırlarla ağırlıklandırınca ayrıştırıcıyı
  seçti ve 7 kapsadı.
- **Düzeltilmiş seçimle Go deposunda üç koşu**: kapsam 14'ün 7, 8.5 ve 5.5'i
  (becerisiz iki koşu: 3 ve 1); kör doğruluk, beceri olmayan kolun 19, 19 ve
  19'una karşı 20'nin 16, 20 ve 20'si. İmza ve ölçülmüş sayı kurallarından
  sonraki iki koşu 20'nin 20'sini tuttu.
- **Tek ad alanlı bir C# deposunda ad kenarları**: modüller arası örneklenen
  20 `[H]` kullanımın 19'u gerçek tür kullanımıydı ve 1'i bir belge yorumunda
  duruyordu; yorumlar artık taranmıyor. Aynı depoda **ORM tabloları**: önce 0,
  EF Core `DbSet` bildirimleri okununca 30. **İlk gerçek sonda** (DI
  kayıtları) oradaki boşluğunu boş buldu: 11 arayüzün hepsi gerçeklemeleriyle
  aynı dosyada yaşıyordu.
