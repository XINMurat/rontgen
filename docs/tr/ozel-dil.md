> Kaynak: skill/rontgen/references/ozel-dil.md · sha256:ac892db50295 — bu sayfa o sürümün çevirisidir; kaynak İngilizce metindir.

# Projenin kendine ait bir dil — adım 1

Mantık, deponun kendisi için tanımladığı bir dilde yaşadığında — bir DSL,
derleyicisi yanında duran deneysel bir sistem dili — sınıflandırılmamış
uzantılar listesi ilk işarettir: betiklerin tanımadığı tek bir uzantıdan çok
sayıda dosya. Önce o dosyaları okumayın. Projenin dile ait kendi tanımını
okuyun (dilbilgisi, tanım, sınıflandırma belgeleri; `belge.md` onları var olan
kaç yolu adlandırdıklarına göre sıralar) ve dili yapılandırmada betimleyin:

```json
{"extra_sources": {".path": {"name": "Path",
  "import": "^\\s*use\\s+([\\w.:/]+)",
  "decl": "^\\s*(?:fn|type|cage)\\s+(\\w+)",
  "comment": "//"}}}
```

`import` (tek yakalama grubu: hedef, `a.b`, `a::b` ya da `a/b`) aynı dildeki
dosyalara `[K]` kenarlar verir; `decl` iskeleti ve ad kenarlarını verir;
`comment` yorum metnini dışarıda tutar. Her örüntüyü aldığınız tanım
satırlarını oturum günlüğünde alıntılayın: örüntüler tanımın dil hakkındaki
iddiasıdır ve yanlış biri `yapi.md`'de çözülmemiş importlar olarak görünür.
Sözlük sonra dilin kendi terimlerini, tanıma atıf yaparak taşır.
