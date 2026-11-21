> Kaynak: skill/rontgen/references/borc.md · sha256:9ec7e09a65ca — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Borç ve yeniden düzenle-mi-yeniden-yaz-mı — bir hüküm değil, bir tablo

"Ne kadar borç var?" ya da "yeniden mi düzenleyelim, yeniden mi yazalım?"
sorulduğunda, raporlardan modül başına bir satır doldurun. Rontgen tartar;
sahibi karar verir ve seçim iskele'ye görev olarak gider. Her hücre kendi
raporunu adlandırır; yapılacak iş (karar) `[H]`'dir.

| Modül | Sıcak nokta sırası | `[K]` fan-in | Döngüde mi | Testler | Kişi | Okunan pay | Karar |
|---|---|---|---|---|---|---|---|
| | `rontgen.json` | `yapi.json` | `yapi.json` | `rontgen.json` | `rontgen.json` | `kapsam.json` | koru / düzenle / boğ / yeniden yaz / emekliye ayır |

Kararlar:

- **koru** — soğuk ya da okunup anlaşılmış: getirisi olmayan maliyet.
- **düzenle** — aynı davranış, daha iyi biçim, yerinde. Önce test ister.
- **boğ** (strangler) — yeni yolu eskinin yanına bir anahtarın arkasında
  kurun, çağıranları tek tek taşıyın, eskiyi en son silin. Pek çok parçanın
  dayandığı büyük bir modül için varsayılan budur: hiçbir zaman tamamını
  birden değiştirmeyin.
- **yeniden yaz** — davranışın kendisi değişiyor ve ona az parça dayanıyor.
- **emekliye ayır** — hiçbir şey onu içe aktarmıyor, hiçbir belge onu
  adlandırmıyor (`belge.json`).

Tekrar eden iki okuma:

- **Test yok, fan-in yüksek.** İlk görev yeniden düzenleme değil, bugünkü
  davranışı sabitleyen nitelendirme testleridir.
- **Tek kişi, döngüde.** Bu maliyet koddan önce bilgidir: herhangi bir
  değişiklikten önce bir modül notu gelir.

Ölçülmedi: bu tablodan çıkan bir kararın bellekten çıkan bir karardan daha
iyi olup olmadığı. Borcu gün olarak boyutlandırmayın; değişecek sayıları
adlandırın.
