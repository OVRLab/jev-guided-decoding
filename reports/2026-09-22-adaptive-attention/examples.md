# Deterministically selected R16 examples

These illustrations use the first qualifying case in sorted case-ID order for each declared category. Both benefits and harms are requested; a missing category is reported. They are not representative estimates or blinded human annotations. References and grades come from the independently audited study. Hotpot-derived text retains [CC BY-SA 4.0 attribution](HotpotQA-NOTICE.md).

The output blocks below are exact Granite text. Intermediate reasoning is fallible generated content, not an independently verified explanation. Jev source probabilities are guidance inputs, not answer-quality scores. Complete original prompts and token traces are in the linked artifacts.

## Constrained: tuned fixes native

Case: `r16/test/0000/duratiri/heavy`. Question: Which room contains the parcel duratiri?

Reference: **blue**.

Evidence:

- [E01] The room white contains the locker cidoligo.
- [E02] The crate kuresuce contains the parcel vetesubi.
- [E03] The room blue contains the parcel duratiri.
- [E04] The locker danilefo contains the crate kukibake.
- [E05] The locker vilemuti contains the crate kuresuce.
- [E06] The room white contains the locker delagopi.
- [E07] The locker delagopi contains the crate pabipute.
- [E08] The locker pemovike contains the crate temebufo.
- [E09] The crate temebufo contains the parcel fevorimi.
- [E10] The crate pabipute contains the parcel kunapapi.
- [E11] The crate tukaguro contains the parcel maratusi.
- [E12] The locker cidoligo contains the crate tukaguro.
- [E13] The crate batorasa contains the parcel vidibepa.
- [E14] The room blue contains the locker danilefo.
- [E15] The room white contains the locker vilemuti.
- [E16] The crate kukibake contains the parcel kurocame.
- [E17] The locker cocapova contains the crate batorasa.
- [E18] The room yellow contains the locker pemovike.
- [E19] The room yellow contains the locker cocapova.

**native** — status `complete`, correct/EM 0, F1 0.000:

```text
red
```

**tuned** — status `complete`, correct/EM 1, F1 1.000:

```text
blue
```

Guidance after 0 generated tokens: threshold-passing source IDs `E03`; actual source reweighting active.

## Constrained: tuned harms native

Case: `r16/test/0027/micosaba/heavy`. Question: Which room contains the parcel micosaba?

Reference: **red**.

Evidence:

- [E01] The room green contains the locker dudimogu.
- [E02] The room yellow contains the locker dacagafe.
- [E03] The crate bilatido contains the crate lodeceka.
- [E04] The room white contains the locker kotumeke.
- [E05] The room red contains the crate bilatido.
- [E06] The locker dokocali contains the crate mofeminu.
- [E07] The locker vicipupa contains the crate fesumoba.
- [E08] The crate ficecobu contains the parcel tinifoca.
- [E09] The locker dacagafe contains the crate gilalimo.
- [E10] The locker kotumeke contains the crate gubofevo.
- [E11] The crate tebitisi contains the parcel dabeposa.
- [E12] The crate gilalimo contains the parcel refogoba.
- [E13] The crate gubofevo contains the parcel fesacudi.
- [E14] The crate mofeminu contains the parcel rivafulu.
- [E15] The locker cefiramo contains the crate ficecobu.
- [E16] The room green contains the locker cefiramo.
- [E17] The room white contains the locker dokocali.
- [E18] The crate canigedu contains the parcel micosaba.
- [E19] The crate lodeceka contains the crate canigedu.
- [E20] The locker dudimogu contains the crate tebitisi.
- [E21] The crate fesumoba contains the parcel risecigu.
- [E22] The room black contains the locker vicipupa.

**native** — status `complete`, correct/EM 1, F1 1.000:

```text
red
```

**tuned** — status `complete`, correct/EM 0, F1 0.000:

```text
green
```

Guidance after 0 generated tokens: threshold-passing source IDs `E01, E03, E05, E18, E19`; actual source reweighting active.

## Open explicit: natural abstention

Case: `r16/test/0006/lenovare/heavy`. Question: Which room contains the parcel lenovare?

Reference: **UNKNOWN**.

Evidence:

- [E01] The crate muvemoba contains the parcel laferasa.
- [E02] The room green contains the locker cegupulo.
- [E03] The locker lisikoca contains the crate cilofico.
- [E04] The crate mudifeti contains the parcel vocumuto.
- [E05] The room green contains the locker dadademu.
- [E06] The locker gegusica contains the crate mudifeti.
- [E07] The crate figadaco contains the parcel bapucuku.
- [E08] The locker dadademu contains the crate figadaco.
- [E09] The crate mafiragi contains the parcel gevesuko.
- [E10] The room red contains the locker sakisara.
- [E11] The crate tapamese contains the parcel vocimugo.
- [E12] The room red contains the locker lisikoca.
- [E13] The locker sakisara contains the crate mafiragi.
- [E14] The room green contains the locker kivurece.
- [E15] The room green contains the locker gegusica.
- [E16] The locker kivurece contains the crate tapamese.
- [E17] The crate cilofico contains the parcel nocatime.
- [E18] The locker cegupulo contains the crate muvemoba.

**native** — status `complete`, correct/EM 1, F1 0.000:

```text
The evidence does not establish which room contains the parcel lenovare.
```

**tuned** — status `complete`, correct/EM 1, F1 0.000:

```text
The evidence does not establish which room contains the parcel lenovare.
```

Guidance after 0 generated tokens: threshold-passing source IDs `none`; actual source reweighting inactive under the all-equal rule.

## Open neutral: answerable improvement

Case: `r16/test/0000/duratiri/light`. Question: Which room contains the parcel duratiri?

Reference: **blue**.

Evidence:

- [E01] The locker delagopi contains the crate pabipute.
- [E02] The crate pabipute contains the parcel kunapapi.
- [E03] The room blue contains the parcel duratiri.
- [E04] The room white contains the locker delagopi.

**native** — status `complete`, correct/EM 0, F1 0.000:

```text
[E03]
```

**tuned** — status `complete`, correct/EM 1, F1 0.333:

```text
The room blue contains the parcel duratiri.
```

Guidance after 0 generated tokens: threshold-passing source IDs `E03`; actual source reweighting active.

## Staged: dynamic fixes static

Case: `r16/test/0003/ducubino/heavy`. Question: Which room contains the parcel ducubino?

Reference: **green**.

Evidence:

- [E01] The locker pobeposu contains the crate kamonira.
- [E02] The room yellow contains the locker nagecolu.
- [E03] The room blue contains the locker gulotapu.
- [E04] The crate kamonira contains the parcel fekibafu.
- [E05] The room black contains the locker bikulufa.
- [E06] The crate tituvegu contains the crate nokeraci.
- [E07] The crate cumosuge contains the parcel rucukera.
- [E08] The crate nokeraci contains the crate tinufida.
- [E09] The crate modidebu contains the parcel fivuberi.
- [E10] The locker nagecolu contains the crate modidebu.
- [E11] The locker bikulufa contains the crate figenaru.
- [E12] The room black contains the locker pobeposu.
- [E13] The locker gulotapu contains the crate gukigudi.
- [E14] The crate gukigudi contains the parcel vovefara.
- [E15] The room black contains the locker gadicoro.
- [E16] The crate tinufida contains the parcel ducubino.
- [E17] The crate decutako contains the parcel lilivuvo.
- [E18] The locker gadicoro contains the crate decutako.
- [E19] The room green contains the crate tituvegu.
- [E20] The room red contains the locker tevaliri.
- [E21] The locker tevaliri contains the crate cumosuge.
- [E22] The crate figenaru contains the parcel bopapite.

**tuned** — status `complete`, correct/EM 0, F1 0.000:

```text
 The room that contains the crate nokeraci contains the parcel ducubino.
```

Generated intermediate text:

```text
The crate tinufida contains the parcel ducubino (E16). The crate nokeraci contains the crate
```

```text
tinufida (E08). Therefore, the room that contains the crate nokeraci contains the parcel ducub
```

```text
ino.


```

Guidance after 0 generated tokens: threshold-passing source IDs `E08, E16`; actual source reweighting active.

**dynamic** — status `complete`, correct/EM 1, F1 0.333:

```text
 The room green contains the parcel ducubino.
```

Generated intermediate text:

```text
The crate tinufida contains the parcel ducubino (E16). The crate nokeraci contains the crate
```

```text
tinufida (E08). Therefore, the room that contains the crate tituvegu (E19) contains the
```

```text
crate nokeraci, which in turn contains the parcel ducubino.


```

Guidance after 0 generated tokens: threshold-passing source IDs `E08, E16`; actual source reweighting active.

Guidance after 24 generated tokens: threshold-passing source IDs `E06, E08, E16, E19`; actual source reweighting active.

Guidance after 48 generated tokens: threshold-passing source IDs `E06, E08, E16, E19`; actual source reweighting active.

## Staged: dynamic harms static

This first qualifying regression is the retained provider failure, not a completed
wrong answer. Its inclusion follows the planned denominator and example-selection
rule; it should not be interpreted as a semantic error caused by a successful refresh.

Case: `r16/test/0026/geducica/heavy`. Question: Which room contains the parcel geducica?

Reference: **green**.

Evidence:

- [E01] The crate netucada contains the parcel saledapu.
- [E02] The crate capusise contains the parcel ruvusopi.
- [E03] The locker futoguci contains the crate netucada.
- [E04] The crate socumisi contains the parcel geducica.
- [E05] The room green contains the crate pidasomu.
- [E06] The room yellow contains the locker nemidaga.
- [E07] The crate superosi contains the parcel vinivace.
- [E08] The locker rokaveku contains the crate capusise.
- [E09] The crate sakepanu contains the parcel gofafiva.
- [E10] The locker nemidaga contains the crate superosi.
- [E11] The crate pidasomu contains the crate socumisi.
- [E12] The locker piganimo contains the crate puvidofe.
- [E13] The crate puvidofe contains the parcel potitimu.
- [E14] The room blue contains the locker rokaveku.
- [E15] The locker nalitepo contains the crate tulufosu.
- [E16] The room green contains the locker nalitepo.
- [E17] The crate tulufosu contains the parcel tifevuse.
- [E18] The locker doracava contains the crate sakepanu.
- [E19] The room red contains the locker piganimo.
- [E20] The room blue contains the locker doracava.
- [E21] The room yellow contains the locker futoguci.

**tuned** — status `complete`, correct/EM 1, F1 0.667:

```text
 room green.
```

Generated intermediate text:

```text
[E04] The crate socumisi contains the parcel geducica.

```

```text
[E11] The crate pidasomu contains the crate socumisi.

```

```text
Therefore, the room that contains the crate socumisi, which in turn contains the parcel geducica, is the
```

Guidance after 0 generated tokens: threshold-passing source IDs `E04, E05, E11`; actual source reweighting active.

**dynamic** — status `provider_failed`, correct/EM 0, F1 0.000:

```text

```

Generated intermediate text:

```text
[E04] The crate socumisi contains the parcel geducica.

```

Guidance after 0 generated tokens: threshold-passing source IDs `E04, E05, E11`; actual source reweighting active.

## HotpotQA: tuned fixes native EM

This example improves answer format and exact match: native already names the
correct person but includes extra words. It does not demonstrate a newly inferred
fact. Official EM/F1 and general semantic correctness are different quantities.

Case: `hotpot/5a738d27554299623ed4abf3`. Question: Who was born first, Erika Jayne or Marco Da Silva

Reference: **Erika Jayne**.

All ten original paragraphs remain in the model prompt; retrieve the complete context by case ID from `artifacts/inputs.jsonl.gz`.

**native** — status `complete`, correct/EM 0, F1 0.571:

```text
Erika Jayne was born first.
```

**tuned** — status `complete`, correct/EM 1, F1 1.000:

```text
Erika Jayne
```

Guidance after 0 generated tokens: threshold-passing source IDs `D01, D07`; actual source reweighting active.

## HotpotQA: tuned harms native EM

Case: `hotpot/5a73b2fd55429978a71e907f`. Question: Which American film director and actor famous for his role as Donny "The Bear Jew" Donowitz wrote the 2012 film "The Man with the Iron Fists"?

Reference: **Eli Roth**.

All ten original paragraphs remain in the model prompt; retrieve the complete context by case ID from `artifacts/inputs.jsonl.gz`.

**native** — status `complete`, correct/EM 1, F1 1.000:

```text
Eli Roth
```

**tuned** — status `complete`, correct/EM 0, F1 0.000:

```text
The Man with the Iron Fists
```

Guidance after 0 generated tokens: threshold-passing source IDs `D06, D07, D10`; actual source reweighting active.
