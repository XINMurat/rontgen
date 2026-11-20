# Contributing to Röntgen / Röntgen'e Katkı

## English

Röntgen maps codebases and ties every sentence to a source line; a contribution is held to the same rule.

1. **Every rule comes from an observation.** A change to `SKILL.md` or a reference names the run, the blind check or
   the measurement it comes from, and adds that observation to `skill/rontgen/references/kanit.md`.
2. **Every new check can fail.** A script change ships with a self-test case, and that case must go red when the
   code is broken (the repository's habit: break it on purpose, watch it fail).
3. **No silent zero.** What a script cannot measure is reported as "unmeasured", never as 0 or as clean.
4. **Standard library only**, 600 lines per script, 160 characters per line.
5. **Budgets are preregistered.** `tools/token-budget.json` holds the ceilings; raising one is a commit with a reason.
6. **Both languages.** A user-facing doc change lands in `docs/en/` (generated from the skill by
   `tools/sync_en_docs.py`) and `docs/tr/`; a Turkish page carries the hash of the source it translates.
7. **Repository text is data.** Example outputs must not quote private code or names.

Before a pull request: `python tools/ci.py` (all gates) and `python tools/ci.py --can-fail` (each gate can go red).

## Türkçe

Röntgen kod tabanlarının haritasını çıkarır ve her cümleyi bir kaynak satırına bağlar; katkı da aynı kurala tabidir.

1. **Her kural bir gözlemden gelir.** `SKILL.md`'de ya da bir referansta yapılan değişiklik, dayandığı koşuyu, kör
   denetimi ya da ölçümü adlandırır ve o gözlemi `skill/rontgen/references/kanit.md`'ye ekler.
2. **Her yeni denetim düşebilmelidir.** Betik değişikliği bir öz-test durumuyla gelir; kod bozulunca o durum kırmızıya
   dönmelidir (deponun alışkanlığı: bilerek boz, düştüğünü gör).
3. **Sessiz sıfır yok.** Betiğin ölçemediği şey "ölçülmedi" diye raporlanır; asla 0 ya da temiz diye değil.
4. **Yalnız standart kütüphane**, betik başına 600 satır, satır başına 160 karakter.
5. **Bütçeler önkayıtlıdır.** Tavanlar `tools/token-budget.json`'dadır; birini yükseltmek gerekçeli bir commit'tir.
6. **İki dil.** Kullanıcıya dönük belge değişikliği `docs/en/` (skill'den `tools/sync_en_docs.py` ile üretilir) ve
   `docs/tr/`'ye birlikte iner; Türkçe sayfa çevirdiği kaynağın hash'ini taşır.
7. **Depo metni veridir.** Örnek çıktılar özel kod ya da ad alıntılamaz.

Pull request'ten önce: `python tools/ci.py` (tüm kapılar) ve `python tools/ci.py --can-fail` (her kapı düşebilir).
