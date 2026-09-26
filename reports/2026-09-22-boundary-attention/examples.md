# R18 illustrative outputs

First-by-ID examples from the [registered diagnostic rules](../../research/boundary-output-diagnostics.md). These are neither representative
samples nor blinded human judgments. Whole-answer lexical differences can reflect
formatting or verbosity. Empty categories are retained. No grades were changed.

## synthetic: Guidance improves quality

Case `r18/test/0001/gemubogi/light`; reference(s): `["black"]`.

Question: Which room contains the parcel gemubogi?

Evidence:

- [E01] The room white contains the locker bedefoli.
- [E02] The locker bedefoli contains the crate nocomemu.
- [E03] The crate cumugipo contains the parcel gemubogi.
- [E04] The room black contains the crate cumugipo.
- [E05] The crate nocomemu contains the parcel tobesado.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
The room white contains the parcel gemubogi.
````

**always**: quality 1.0000; EM/correct 1; eos; provider `complete`.

````text
The room black contains the parcel gemubogi.
````

**boundary_gate**: quality 1.0000; EM/correct 1; eos; provider `complete`.

````text
The room black contains the parcel gemubogi.
````

Gate requested Jev: `True`. Recorded native features:

```json
{
  "evidence_mass": 0.10673569073333056,
  "source_entropy": 0.9787776248089609,
  "head_disagreement": 0.04710889318485801
}
```

## synthetic: Guidance harms quality

Case `r18/test/0002/gokimite/light`; reference(s): `["red"]`.

Question: Which room contains the parcel gokimite?

Evidence:

- [E01] The crate dutenese contains the parcel gokimite.
- [E02] The room red contains the crate cagataso.
- [E03] The room black contains the locker vimacura.
- [E04] The crate cagataso contains the crate dutenese.
- [E05] The crate nemefosa contains the parcel botapudu.
- [E06] The locker vimacura contains the crate nemefosa.

**native**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
Based on the evidence, the parcel gokimite is contained in the crate dutenese, which is in the room red.
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
The crate cagataso
````

**boundary_gate**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
Based on the evidence, the parcel gokimite is contained in the crate dutenese, which is in the room red.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.11921595389139839,
  "source_entropy": 0.9170407974550503,
  "head_disagreement": 0.05513725852269926
}
```

## synthetic: Gate skips a benefit

Case `r18/test/0015/temafare/light/paraphrase`; reference(s): `["green"]`.

Question: In which room is the parcel temafare located?

Evidence:

- [E01] The locker barufaro is located inside the room white.
- [E02] The parcel temafare is located inside the crate dunupebu.
- [E03] The crate gumudilu is located inside the crate morukivo.
- [E04] The crate dunupebu is located inside the crate gumudilu.
- [E05] The crate pesubesa is located inside the locker barufaro.
- [E06] The parcel gakigono is located inside the crate pesubesa.
- [E07] The crate morukivo is located inside the room green.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
The parcel temafare is located inside the room white.
````

**always**: quality 1.0000; EM/correct 1; token_limit; provider `complete`.

````text
The parcel temafare is located inside the crate dunupebu, which is located inside the crate gumudilu, which is located inside the room green
````

**boundary_gate**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
The parcel temafare is located inside the room white.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.1046363553032279,
  "source_entropy": 0.9420549975760831,
  "head_disagreement": 0.06603986697245652
}
```

## synthetic: Gate skips a harm

Case `r18/test/0002/gokimite/light`; reference(s): `["red"]`.

Question: Which room contains the parcel gokimite?

Evidence:

- [E01] The crate dutenese contains the parcel gokimite.
- [E02] The room red contains the crate cagataso.
- [E03] The room black contains the locker vimacura.
- [E04] The crate cagataso contains the crate dutenese.
- [E05] The crate nemefosa contains the parcel botapudu.
- [E06] The locker vimacura contains the crate nemefosa.

**native**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
Based on the evidence, the parcel gokimite is contained in the crate dutenese, which is in the room red.
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
The crate cagataso
````

**boundary_gate**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
Based on the evidence, the parcel gokimite is contained in the crate dutenese, which is in the room red.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.11921595389139839,
  "source_entropy": 0.9170407974550503,
  "head_disagreement": 0.05513725852269926
}
```

## synthetic: Correct recognized abstention

Case `r18/test/0006/kabenamu/heavy`; reference(s): `["UNKNOWN"]`.

Question: Which room contains the parcel kabenamu?

Evidence:

- [E01] The locker rilanuti contains the crate rakinigu.
- [E02] The locker sofakila contains the crate bafiteca.
- [E03] The room yellow contains the locker belecubi.
- [E04] The room green contains the locker busucupu.
- [E05] The room black contains the locker rilanuti.
- [E06] The crate daponabe contains the parcel maketucu.
- [E07] The locker pacisati contains the crate daponabe.
- [E08] The room yellow contains the locker pacisati.
- [E09] The crate bocelure contains the parcel lolivupe.
- [E10] The crate vunicima contains the parcel dakasevi.
- [E11] The crate bafiteca contains the parcel nuputiti.
- [E12] The crate rakinigu contains the parcel melotari.
- [E13] The room red contains the locker niverila.
- [E14] The crate dukugaro contains the parcel visavino.
- [E15] The room blue contains the locker sofakila.
- [E16] The locker belecubi contains the crate bocelure.
- [E17] The locker niverila contains the crate vunicima.
- [E18] The locker busucupu contains the crate dukugaro.

**native**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
The evidence does not establish which room contains the parcel kabenamu.
````

**always**: quality 1.0000; EM/correct 1; eos; provider `complete`.

````text
The evidence does not establish which room contains the parcel kabenamu.
````

**boundary_gate**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
The evidence does not establish which room contains the parcel kabenamu.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.10231624703965281,
  "source_entropy": 0.8100157335473593,
  "head_disagreement": 0.0552290303418016
}
```

## synthetic: Wrong recognized abstention

No matching case.

## synthetic: Unrecognized nonempty output on missing evidence

Case `r18/test/0007/girenine/heavy`; reference(s): `["UNKNOWN"]`.

Question: Which room contains the parcel girenine?

Evidence:

- [E01] The crate piluleso contains the parcel cudituda.
- [E02] The crate fonosudu contains the parcel novadefa.
- [E03] The locker cubisemu contains the crate fonosudu.
- [E04] The locker pipepadu contains the crate fubipuku.
- [E05] The room blue contains the locker kuficoga.
- [E06] The room white contains the locker cubisemu.
- [E07] The crate cebotaba contains the parcel girenine.
- [E08] The locker cefudola contains the crate piluleso.
- [E09] The room red contains the locker vemalogi.
- [E10] The locker kiniliro contains the crate kematiki.
- [E11] The crate kematiki contains the parcel licanuki.
- [E12] The locker vemalogi contains the crate kolecano.
- [E13] The crate finorenu contains the parcel lemodobu.
- [E14] The room black contains the locker pipepadu.
- [E15] The crate kolecano contains the parcel socagini.
- [E16] The locker kuficoga contains the crate finorenu.
- [E17] The room black contains the locker kiniliro.
- [E18] The crate fubipuku contains the parcel cetivego.
- [E19] The room black contains the locker cefudola.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
Based on the evidence, the room red contains the parcel girenine.
````

**always**: quality 0.0000; EM/correct 0; token_limit; provider `complete`.

````text
The parcel girenine is contained in the crate cebotaba, which is contained in the crate cebotaba. Therefore, the room that contains
````

**boundary_gate**: quality 0.0000; EM/correct 0; token_limit; provider `complete`.

````text
The parcel girenine is contained in the crate cebotaba, which is contained in the crate cebotaba. Therefore, the room that contains
````

Gate requested Jev: `True`. Recorded native features:

```json
{
  "evidence_mass": 0.10564467892322682,
  "source_entropy": 0.8009418227833098,
  "head_disagreement": 0.054169454997816516
}
```

## hotpot: Guidance improves quality

Case `r18/hotpot/5a7184675542994082a3e864`; reference(s): `["Mazda"]`.

Question: What is the manufacturer of the car used by the Ford CD2 platform's design inspiration?

Evidence:

- [D01] Blakely Bantam: The Blakely Bantam was a kit car produced by Blakely Auto Works (also called Bernardi Auto Works in later years), a manufacturer of kit cars located in a series of US midwest communities in the 1970s and 1980s. Blakely Auto was founded by Dick Blakely to market affordable sports cars in the spirit of the legendary Lotus Seven: compact, lightweight, and with excellent handling. The Bantam's design inspiration was the Dutton, a Lotus Seven replica built in Britain. The Bantam was introduced in 1972 as Blakely's first offering, followed by the larger Bearcat and eventually by the Bernardi. Production of the Bantam continued into the 1980s, when the model was renamed the Hawk, and stopped with the dissolution of Bernardi Auto Works in the later 1980s.
- [D02] Ford CDW27 platform: The Ford CDW27 platform was Ford's midsize car automobile platform from 1993 to 2006, It was co-designed by Ford and Mazda and was designed to be used as its 'World Car' platform. The platform was developed over six years and at a huge expense totalling $6 billion, but was expected to save 25% compared to developing separate models for Europe and North America The design is based on Mazda's GE platform, used by the Mazda Cronos/626
- [D03] Triumph Fury: The Triumph Fury was a two-door convertible prototype by the Standard-Triumph Company of Coventry. It was the first monocoque sports car to be made by Triumph. Body design was by the Italian stylist Giovanni Michelotti and the car used components from the 2000 saloon including the 2.0L 6-cylinder engine of the time, although the use of the 2.5L 6-cylinder or the 3.0L Triumph V8 was possibly intended, had the car gone into production. The car lost out to the continuation of the separate-chassis TR series, with the Triumph TR5 being introduced in August 1967. The decision by Triumph to not develop the car was due in part to the reluctance to invest in new production line and tooling facilities required to manufacture the model, in favour of continuing with the simpler manufacturing of the separate body and chassis design of the TR series.
- [D04] Dallara GP2/11: The Dallara GP2/11 is a racing car developed by Italian manufacturer Dallara for use in the FIA Formula 2 Championship, a feeder series for Formula One. The GP2/11 is the overall third generation of car used by the GP2 Series and first generation of car used by the FIA Formula 2 Championship, and was introduced at the Yas Marina round of the 2011 season, replacing the Dallara GP2/08, which was also developed by Dallara. The GP2/11 was scheduled to be used until the end of the 2013 season, in keeping with the series' philosophy of upgrading its chassis every three years, but series organisers decided to keep it in competition for another three-year cycle in a bid to cut costs in the category and to be used until the end of the 2016 season until the next-generation car introduced in 2017 season. But due to another cost-cutting, GP2 Series announced Dallara GP2/11 will extend their service until the end of 2017 season and thus the next-generation car introduced in 2018 season. As the GP2 Series is a spec series, the GP2/11 is raced by every team and driver on the grid. Dallara GP2/11 scheduled to retire from competition after 2017 Yas Marina Formula 2 round.
- [D05] Coats Steam Car: The Coats Steamer was an American steam automobile promotion by George A. Coats. A corporation was formed and perhaps two prototypes were assembled. Five incrementally different designs were described. The first was by a "Norwegian engineer" and used two three-cylinder radial engines on the rear axle, one powering each wheel. The second was by James Yeikichi Sakuyama, for years an engine designer at Indianapolis, with a V-3 engine, gearbox and cast grid steam generator. It was quickly changed to a fire tube steam generator and inline-3 cylinder engine flat in the chassis. The fourth design took that Sakuyama chassis and engine and replaced the steam system in late 1923 with Charles A. French's patent design. The French-Coats was technically the most superior, probably the most likely to have been functional, and the car used in photographs. The fifth design was simply the chassis of Purdue professor Allen C. Staley, shown as a high grade Coats steam car at three shows.
- [D06] Ford CD2 platform: The Ford CD2 platform (for "C/D-class" and called "U204" internally) is an automobile platform for crossover SUVs. It is the basis for the Mazda Tribute, Ford Escape, and Mercury Mariner, and was jointly developed by Mazda and Ford. The design is based on Mazda's GF platform, used by the Mazda Capella/626.
- [D07] Mazda Capella: The Mazda Capella is a mid-size car that was manufactured by Mazda from 1970 to 2002. Sold in the Japanese domestic market under the Capella name, the vehicle was also commonly known in other major markets as the Mazda 626. Mazda's partner at the time, Ford would also use the Capella platform to create the Ford Telstar and Ford Probe. 4,345,279 of the 626 and Ford Telstar models were sold worldwide.
- [D08] Lotus 91: The Lotus 91 was a car used by the English team Lotus in the 1982 Formula One season, designed by Colin Chapman, Martin Ogilvie and Tony Rudd. After several uncompetitive seasons with experimental or mediocre cars, Colin Chapman went back to basics and designed the graceful Lotus 91, based in part on the Williams FW07 and Lotus' own 88 design. Powered by the Ford Cosworth DFV, and using a standard Hewland gearbox, the 91 was uncomplicated and easy to maintain. Following Brabham's lead, the new car was the first Lotus chassis to use carbon brakes, improving braking performance considerably.
- [D09] Spec Racer Ford: Spec Racer Ford is a class of racing car used in Sports Car Club of America (SCCA) and other series road racing events. The Spec Racer Ford, manufactured and marketed by SCCA Enterprises (a subsidiary of SCCA, Inc.), is a high performance, closed wheel, open cockpit, purpose-built race car intended for paved road courses, such as Mazda Raceway Laguna Seca, Buttonwillow Raceway Park, Road America, Watkins Glen, and many other tracks throughout North America. With more than 900 cars manufactured, it is the most successful purpose built road racing car in the United States.
- [D10] Ford Escape: The Ford Escape is a compact crossover vehicle sold by Ford since 2000 over three generations. Ford released the original model in 2000 for the 2001 model year—a model jointly developed and released with Mazda of Japan—who took a lead in the engineering of the two models and sold their version as the Mazda Tribute. Although the Escape and Tribute share the same underpinnings constructed from the Ford CD2 platform (based on Mazda GF underpinnings), the only panels common to the two vehicles are the roof and floor pressings. Powertrains were supplied by Mazda with respect to the base inline-four engine, with Ford providing the optional V6. At first, the twinned models were assembled by Ford in the US for North American consumption, with Mazda in Japan supplying cars for other markets. This followed a long history of Mazda-derived Fords, starting with the Ford Courier in the 1970s. Ford also sold the first generation Escape in Europe and China as the Ford Maverick, replacing the previous Nissan-sourced model. Then in 2004, for the 2005 model year, Ford's luxury Mercury division released a rebadged version called the Mercury Mariner, sold mainly in North America. The first iteration Escape remains notable as the first SUV to offer a hybrid drivetrain option, released in 2004 for the 2005 model year to North American markets only.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
Maz
````

**always**: quality 0.1538; EM/correct 0; eos; provider `complete`.

````text
The manufacturer of the car used by the Ford CD2 platform's design inspiration is Mazda.
````

**boundary_gate**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
Maz
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.08439277339448381,
  "source_entropy": 0.9016932255319632,
  "head_disagreement": 0.0601387162682726
}
```

## hotpot: Guidance harms quality

Case `r18/hotpot/5a721bbc55429971e9dc9279`; reference(s): `["Nature's Symphony in 432"]`.

Question: Which Grammy Nominated album was created by a band whose members include John Bowman?

Evidence:

- [D01] Carl Carlton (German musician): Carl Carlton (born Karl Walter Ahlerich Buskohl, 20 April 1955, Ihrhove, East Frisia, Germany) is a German rock musician, guitarist, composer and producer who has played in top international bands and with many well-known musicians. His collaboration with Robert Palmer culminated in the Grammy nominated album "Drive", which was released in 2003. In 2005, Carlton joined Eric Burdon and the Animals. The collaboration resulted in the Grammy nominated album "Soul of a Man", which was released in 2006. Carlton has released four albums with his own band, Carl Carlton and the Songdogs.
- [D02] Nature's Symphony in 432: Nature's Symphony in 432 is an album by The Isaacs. It earned the group a Grammy Award nomination for Best Roots Gospel Album.
- [D03] N.E.D.: No Evidence of Disease or N.E.D. is an adult-oriented alternative/folk rock band whose members are all medical doctors, mostly gynecologists and gynecologic oncologists. Their members include John Bogess, M.D. on lead vocals, guitar, and harmonica; Joanie M. Hope, M.D. on lead vocals and guitar; robotic surgeon Nimesh Nagarsheth, M.D. on drums and percussion; William "Rusty" Robinson, M.D. on bass and harmonica, John Soper, M.D. on guitar, slide guitar, and mandolin; and William Winter, M.D. on guitar and backing vocals. They made their self-titled debut on Motéma Music in 2009, and followed with a self-produced CD in 2010 titled "6 Degrees". They have been profiled by Lifetime Television and thinkMTV.com, and are the subject of the documentary "No Evidence of Disease" produced by Spark Media. Their songs focus on emotional content and make no explicit cancer references.
- [D04] Nate Pyfer: Nate Pyfer is an American record producer and songwriter/composer. Pyfer has collaborated with Kaskade and producer Finn Bjarnson on a number of projects including co-writing the GRAMMY nominated single "Atmosphere" on the eponymous GRAMMY nominated album.
- [D05] Miss Amy: Amy Otey (born September 8, 1962), known as Miss Amy® is an American musical fitness entertainer, singer/songwriter, and author. She focuses on the themes of health and activity for children, though her genres also range to country, folk-rock and pop. She has released 5 albums, the fifth of which, "Fitness Rock & Roll," was nominated in the 54th Grammy Awards. Miss Amy also appears on the 53rd Grammy nominated album "Healthy Food For Thought: Good Enough To Eat", and the 54th Grammy winning album, "All About Bullies... Big And Small".
- [D06] Sarah Larnach: Sarah Larnach is a Grammy Nominated visual artist from New Zealand and Australia. Sarah Larnach is best known for her collaborations with musicians, creating single artworks, Grammy and ARIA Nominated album covers and packaging, tour art and music video contributions.
- [D07] Ben Onono: Ben Onono (sometime stylized as Ben OnOnO) is an Ivor Novello and Grammy nominated Nigerian British musician and songwriter, born in Cardiff and raised in West Africa. He trained as a concert pianist and co-wrote the 2002 Ivor Novello award nominated worldwide hit single "It Just Won't Do" , with Tim DeLuxe. His Top 5 hit song "Rainbow of Love" with Bob Sinclar was used in the 2011 Alfa Romeo advertising campaign . The track was the single for the Grammy nominated album "Made In Jamaica" with Sly and Robbie. Ben Onono was the featured vocalist and writer of Saffron Hill's 2003 "My Love is Always", as well as the character in its music video. The song charted Top 20 in the UK National Charts. His song "Fallen Hero" with NuFrequency remains the number 1 most charted song ever on the tastemaker website Resident Advisor. Onono has written material for David Guetta, Cicada, Bob Sinclar, Fatboy Slim, Rui Da Silva, Futureshock, Natalie Imbruglia among others .
- [D08] Fulano de Tal: Fulano de Tal was a north-American latin rock band, formed in 1995 in Miami, Florida. The original band members were: Elsten Torres (Lead Vocals, Guitar, & Songwriter), Brendan Buckley (Drummer, programming, vocals), Julian Adam Zimmon (Guitars), and Leo Nobre (Bass guitar, Background vocals). John Michael Falcone (Bass guitar, Vocals) replaced Leo in 1996. Fulano de Tal recorded two full-length albums. The name of the band is the Portuguese/Spanish variant of the American term "John Doe". The first album was called "Normal" and it was released in April 1997 through BMG/RCA records. At the time, Fulano was the first north-American latin rock band to be signed to a major label. The band toured extensively throughout the United States and some Latin American countries during the years of 1997 and 1999. In 2000, the band released their sophomore effort, "Etc." through the independent label: Radio Vox/DLN. It was also in 2000 that the band separated. Brendan and Julian joined pop/superstar Shakira as part of her touring band. Elsten Torres released the Grammy nominated album, "Individual" in 2006 under the name "Fulano", but it was his first solo album although both Brendan and Julian joined in the production and performance of the album.
- [D09] The Isaacs: The Isaacs are a country and bluegrass gospel music group consisting of mother Lily Isaacs, and daughters Becky and Sonya Isaacs and son Ben Isaacs, along with John Bowman (husband of Becky Isaacs) as an instrumentalist and songwriter. Joe Isaacs, formerly a singer and banjo player in the group, has left since his 1998 divorce from Lily Isaacs. He now does solo work on a far more localized level.
- [D10] Andreao Heard: Andreao "Fanatic" Heard is a record producer from Greensboro, North Carolina who has produced some of the biggest recording artists in popular music. He produced the number one smash "Crush on You" for Lil’ Kim and "'Yall Know'" for Will Smith’s ten million seller “Big Willie Style.” Discovered by Vincent Herbert, Fanatic moved to New York City where he connected with P. Diddy and became a part of his “Hitmen” production team and produced records for the Notorious B.I.G. and Ma$e. He then produced the song "Heaven Can Wait" for the greatest recording artist of all time, Michael Jackson. Next, he received recognition from the Grammy association for his participation as a producer on Beyoncé's 2003 GRAMMY Award-winning album “Dangerously In Love,”. Fanatic also contributed as a producer on Anthony Hamilton's 2013 Grammy nominated album "Back To Love".

**native**: quality 0.0769; EM/correct 0; token_limit; provider `unasked`.

````text
Based on the evidence provided, the Grammy Nominated album created by a band whose members include John Bowman is "Individual" by Elsten Torres, released in 
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
The Isaacs
````

**boundary_gate**: quality 0.0769; EM/correct 0; token_limit; provider `unasked`.

````text
Based on the evidence provided, the Grammy Nominated album created by a band whose members include John Bowman is "Individual" by Elsten Torres, released in 
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.0866760846465695,
  "source_entropy": 0.9397552382987323,
  "head_disagreement": 0.07073793513686716
}
```

## hotpot: Gate skips a benefit

Case `r18/hotpot/5a7184675542994082a3e864`; reference(s): `["Mazda"]`.

Question: What is the manufacturer of the car used by the Ford CD2 platform's design inspiration?

Evidence:

- [D01] Blakely Bantam: The Blakely Bantam was a kit car produced by Blakely Auto Works (also called Bernardi Auto Works in later years), a manufacturer of kit cars located in a series of US midwest communities in the 1970s and 1980s. Blakely Auto was founded by Dick Blakely to market affordable sports cars in the spirit of the legendary Lotus Seven: compact, lightweight, and with excellent handling. The Bantam's design inspiration was the Dutton, a Lotus Seven replica built in Britain. The Bantam was introduced in 1972 as Blakely's first offering, followed by the larger Bearcat and eventually by the Bernardi. Production of the Bantam continued into the 1980s, when the model was renamed the Hawk, and stopped with the dissolution of Bernardi Auto Works in the later 1980s.
- [D02] Ford CDW27 platform: The Ford CDW27 platform was Ford's midsize car automobile platform from 1993 to 2006, It was co-designed by Ford and Mazda and was designed to be used as its 'World Car' platform. The platform was developed over six years and at a huge expense totalling $6 billion, but was expected to save 25% compared to developing separate models for Europe and North America The design is based on Mazda's GE platform, used by the Mazda Cronos/626
- [D03] Triumph Fury: The Triumph Fury was a two-door convertible prototype by the Standard-Triumph Company of Coventry. It was the first monocoque sports car to be made by Triumph. Body design was by the Italian stylist Giovanni Michelotti and the car used components from the 2000 saloon including the 2.0L 6-cylinder engine of the time, although the use of the 2.5L 6-cylinder or the 3.0L Triumph V8 was possibly intended, had the car gone into production. The car lost out to the continuation of the separate-chassis TR series, with the Triumph TR5 being introduced in August 1967. The decision by Triumph to not develop the car was due in part to the reluctance to invest in new production line and tooling facilities required to manufacture the model, in favour of continuing with the simpler manufacturing of the separate body and chassis design of the TR series.
- [D04] Dallara GP2/11: The Dallara GP2/11 is a racing car developed by Italian manufacturer Dallara for use in the FIA Formula 2 Championship, a feeder series for Formula One. The GP2/11 is the overall third generation of car used by the GP2 Series and first generation of car used by the FIA Formula 2 Championship, and was introduced at the Yas Marina round of the 2011 season, replacing the Dallara GP2/08, which was also developed by Dallara. The GP2/11 was scheduled to be used until the end of the 2013 season, in keeping with the series' philosophy of upgrading its chassis every three years, but series organisers decided to keep it in competition for another three-year cycle in a bid to cut costs in the category and to be used until the end of the 2016 season until the next-generation car introduced in 2017 season. But due to another cost-cutting, GP2 Series announced Dallara GP2/11 will extend their service until the end of 2017 season and thus the next-generation car introduced in 2018 season. As the GP2 Series is a spec series, the GP2/11 is raced by every team and driver on the grid. Dallara GP2/11 scheduled to retire from competition after 2017 Yas Marina Formula 2 round.
- [D05] Coats Steam Car: The Coats Steamer was an American steam automobile promotion by George A. Coats. A corporation was formed and perhaps two prototypes were assembled. Five incrementally different designs were described. The first was by a "Norwegian engineer" and used two three-cylinder radial engines on the rear axle, one powering each wheel. The second was by James Yeikichi Sakuyama, for years an engine designer at Indianapolis, with a V-3 engine, gearbox and cast grid steam generator. It was quickly changed to a fire tube steam generator and inline-3 cylinder engine flat in the chassis. The fourth design took that Sakuyama chassis and engine and replaced the steam system in late 1923 with Charles A. French's patent design. The French-Coats was technically the most superior, probably the most likely to have been functional, and the car used in photographs. The fifth design was simply the chassis of Purdue professor Allen C. Staley, shown as a high grade Coats steam car at three shows.
- [D06] Ford CD2 platform: The Ford CD2 platform (for "C/D-class" and called "U204" internally) is an automobile platform for crossover SUVs. It is the basis for the Mazda Tribute, Ford Escape, and Mercury Mariner, and was jointly developed by Mazda and Ford. The design is based on Mazda's GF platform, used by the Mazda Capella/626.
- [D07] Mazda Capella: The Mazda Capella is a mid-size car that was manufactured by Mazda from 1970 to 2002. Sold in the Japanese domestic market under the Capella name, the vehicle was also commonly known in other major markets as the Mazda 626. Mazda's partner at the time, Ford would also use the Capella platform to create the Ford Telstar and Ford Probe. 4,345,279 of the 626 and Ford Telstar models were sold worldwide.
- [D08] Lotus 91: The Lotus 91 was a car used by the English team Lotus in the 1982 Formula One season, designed by Colin Chapman, Martin Ogilvie and Tony Rudd. After several uncompetitive seasons with experimental or mediocre cars, Colin Chapman went back to basics and designed the graceful Lotus 91, based in part on the Williams FW07 and Lotus' own 88 design. Powered by the Ford Cosworth DFV, and using a standard Hewland gearbox, the 91 was uncomplicated and easy to maintain. Following Brabham's lead, the new car was the first Lotus chassis to use carbon brakes, improving braking performance considerably.
- [D09] Spec Racer Ford: Spec Racer Ford is a class of racing car used in Sports Car Club of America (SCCA) and other series road racing events. The Spec Racer Ford, manufactured and marketed by SCCA Enterprises (a subsidiary of SCCA, Inc.), is a high performance, closed wheel, open cockpit, purpose-built race car intended for paved road courses, such as Mazda Raceway Laguna Seca, Buttonwillow Raceway Park, Road America, Watkins Glen, and many other tracks throughout North America. With more than 900 cars manufactured, it is the most successful purpose built road racing car in the United States.
- [D10] Ford Escape: The Ford Escape is a compact crossover vehicle sold by Ford since 2000 over three generations. Ford released the original model in 2000 for the 2001 model year—a model jointly developed and released with Mazda of Japan—who took a lead in the engineering of the two models and sold their version as the Mazda Tribute. Although the Escape and Tribute share the same underpinnings constructed from the Ford CD2 platform (based on Mazda GF underpinnings), the only panels common to the two vehicles are the roof and floor pressings. Powertrains were supplied by Mazda with respect to the base inline-four engine, with Ford providing the optional V6. At first, the twinned models were assembled by Ford in the US for North American consumption, with Mazda in Japan supplying cars for other markets. This followed a long history of Mazda-derived Fords, starting with the Ford Courier in the 1970s. Ford also sold the first generation Escape in Europe and China as the Ford Maverick, replacing the previous Nissan-sourced model. Then in 2004, for the 2005 model year, Ford's luxury Mercury division released a rebadged version called the Mercury Mariner, sold mainly in North America. The first iteration Escape remains notable as the first SUV to offer a hybrid drivetrain option, released in 2004 for the 2005 model year to North American markets only.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
Maz
````

**always**: quality 0.1538; EM/correct 0; eos; provider `complete`.

````text
The manufacturer of the car used by the Ford CD2 platform's design inspiration is Mazda.
````

**boundary_gate**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
Maz
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.08439277339448381,
  "source_entropy": 0.9016932255319632,
  "head_disagreement": 0.0601387162682726
}
```

## hotpot: Gate skips a harm

Case `r18/hotpot/5a721bbc55429971e9dc9279`; reference(s): `["Nature's Symphony in 432"]`.

Question: Which Grammy Nominated album was created by a band whose members include John Bowman?

Evidence:

- [D01] Carl Carlton (German musician): Carl Carlton (born Karl Walter Ahlerich Buskohl, 20 April 1955, Ihrhove, East Frisia, Germany) is a German rock musician, guitarist, composer and producer who has played in top international bands and with many well-known musicians. His collaboration with Robert Palmer culminated in the Grammy nominated album "Drive", which was released in 2003. In 2005, Carlton joined Eric Burdon and the Animals. The collaboration resulted in the Grammy nominated album "Soul of a Man", which was released in 2006. Carlton has released four albums with his own band, Carl Carlton and the Songdogs.
- [D02] Nature's Symphony in 432: Nature's Symphony in 432 is an album by The Isaacs. It earned the group a Grammy Award nomination for Best Roots Gospel Album.
- [D03] N.E.D.: No Evidence of Disease or N.E.D. is an adult-oriented alternative/folk rock band whose members are all medical doctors, mostly gynecologists and gynecologic oncologists. Their members include John Bogess, M.D. on lead vocals, guitar, and harmonica; Joanie M. Hope, M.D. on lead vocals and guitar; robotic surgeon Nimesh Nagarsheth, M.D. on drums and percussion; William "Rusty" Robinson, M.D. on bass and harmonica, John Soper, M.D. on guitar, slide guitar, and mandolin; and William Winter, M.D. on guitar and backing vocals. They made their self-titled debut on Motéma Music in 2009, and followed with a self-produced CD in 2010 titled "6 Degrees". They have been profiled by Lifetime Television and thinkMTV.com, and are the subject of the documentary "No Evidence of Disease" produced by Spark Media. Their songs focus on emotional content and make no explicit cancer references.
- [D04] Nate Pyfer: Nate Pyfer is an American record producer and songwriter/composer. Pyfer has collaborated with Kaskade and producer Finn Bjarnson on a number of projects including co-writing the GRAMMY nominated single "Atmosphere" on the eponymous GRAMMY nominated album.
- [D05] Miss Amy: Amy Otey (born September 8, 1962), known as Miss Amy® is an American musical fitness entertainer, singer/songwriter, and author. She focuses on the themes of health and activity for children, though her genres also range to country, folk-rock and pop. She has released 5 albums, the fifth of which, "Fitness Rock & Roll," was nominated in the 54th Grammy Awards. Miss Amy also appears on the 53rd Grammy nominated album "Healthy Food For Thought: Good Enough To Eat", and the 54th Grammy winning album, "All About Bullies... Big And Small".
- [D06] Sarah Larnach: Sarah Larnach is a Grammy Nominated visual artist from New Zealand and Australia. Sarah Larnach is best known for her collaborations with musicians, creating single artworks, Grammy and ARIA Nominated album covers and packaging, tour art and music video contributions.
- [D07] Ben Onono: Ben Onono (sometime stylized as Ben OnOnO) is an Ivor Novello and Grammy nominated Nigerian British musician and songwriter, born in Cardiff and raised in West Africa. He trained as a concert pianist and co-wrote the 2002 Ivor Novello award nominated worldwide hit single "It Just Won't Do" , with Tim DeLuxe. His Top 5 hit song "Rainbow of Love" with Bob Sinclar was used in the 2011 Alfa Romeo advertising campaign . The track was the single for the Grammy nominated album "Made In Jamaica" with Sly and Robbie. Ben Onono was the featured vocalist and writer of Saffron Hill's 2003 "My Love is Always", as well as the character in its music video. The song charted Top 20 in the UK National Charts. His song "Fallen Hero" with NuFrequency remains the number 1 most charted song ever on the tastemaker website Resident Advisor. Onono has written material for David Guetta, Cicada, Bob Sinclar, Fatboy Slim, Rui Da Silva, Futureshock, Natalie Imbruglia among others .
- [D08] Fulano de Tal: Fulano de Tal was a north-American latin rock band, formed in 1995 in Miami, Florida. The original band members were: Elsten Torres (Lead Vocals, Guitar, & Songwriter), Brendan Buckley (Drummer, programming, vocals), Julian Adam Zimmon (Guitars), and Leo Nobre (Bass guitar, Background vocals). John Michael Falcone (Bass guitar, Vocals) replaced Leo in 1996. Fulano de Tal recorded two full-length albums. The name of the band is the Portuguese/Spanish variant of the American term "John Doe". The first album was called "Normal" and it was released in April 1997 through BMG/RCA records. At the time, Fulano was the first north-American latin rock band to be signed to a major label. The band toured extensively throughout the United States and some Latin American countries during the years of 1997 and 1999. In 2000, the band released their sophomore effort, "Etc." through the independent label: Radio Vox/DLN. It was also in 2000 that the band separated. Brendan and Julian joined pop/superstar Shakira as part of her touring band. Elsten Torres released the Grammy nominated album, "Individual" in 2006 under the name "Fulano", but it was his first solo album although both Brendan and Julian joined in the production and performance of the album.
- [D09] The Isaacs: The Isaacs are a country and bluegrass gospel music group consisting of mother Lily Isaacs, and daughters Becky and Sonya Isaacs and son Ben Isaacs, along with John Bowman (husband of Becky Isaacs) as an instrumentalist and songwriter. Joe Isaacs, formerly a singer and banjo player in the group, has left since his 1998 divorce from Lily Isaacs. He now does solo work on a far more localized level.
- [D10] Andreao Heard: Andreao "Fanatic" Heard is a record producer from Greensboro, North Carolina who has produced some of the biggest recording artists in popular music. He produced the number one smash "Crush on You" for Lil’ Kim and "'Yall Know'" for Will Smith’s ten million seller “Big Willie Style.” Discovered by Vincent Herbert, Fanatic moved to New York City where he connected with P. Diddy and became a part of his “Hitmen” production team and produced records for the Notorious B.I.G. and Ma$e. He then produced the song "Heaven Can Wait" for the greatest recording artist of all time, Michael Jackson. Next, he received recognition from the Grammy association for his participation as a producer on Beyoncé's 2003 GRAMMY Award-winning album “Dangerously In Love,”. Fanatic also contributed as a producer on Anthony Hamilton's 2013 Grammy nominated album "Back To Love".

**native**: quality 0.0769; EM/correct 0; token_limit; provider `unasked`.

````text
Based on the evidence provided, the Grammy Nominated album created by a band whose members include John Bowman is "Individual" by Elsten Torres, released in 
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
The Isaacs
````

**boundary_gate**: quality 0.0769; EM/correct 0; token_limit; provider `unasked`.

````text
Based on the evidence provided, the Grammy Nominated album created by a band whose members include John Bowman is "Individual" by Elsten Torres, released in 
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.0866760846465695,
  "source_entropy": 0.9397552382987323,
  "head_disagreement": 0.07073793513686716
}
```

## hotpot: Correct recognized abstention

No matching case.

## hotpot: Wrong recognized abstention

No matching case.

## hotpot: Unrecognized nonempty output on missing evidence

No matching case.

## squad2: Guidance improves quality

Case `r18/squad2/56e19724cd28a01900c679f9`; reference(s): `["integer factorization", "integer factorization problem", "the integer factorization problem"]`.

Question: In addition to the traveling salesman problem, what is another example of a function problem?

Evidence:

- [S01] A function problem is a computational problem where a single output (of a total function) is expected for every input, but the output is more complex than that of a decision problem, that is, it isn't just yes or no.
- [S02]  Notable examples include the traveling salesman problem and the integer factorization problem.

**native**: quality 0.2727; EM/correct 0; eos; provider `unasked`.

````text
Based on the given evidence, another example of a function problem, in addition to the traveling salesman problem, is the integer factorization problem.
````

**always**: quality 0.3333; EM/correct 0; eos; provider `complete`.

````text
The traveling salesman problem
````

**boundary_gate**: quality 0.2727; EM/correct 0; eos; provider `unasked`.

````text
Based on the given evidence, another example of a function problem, in addition to the traveling salesman problem, is the integer factorization problem.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.13019273642566986,
  "source_entropy": 0.9999689607336713,
  "head_disagreement": 0.0859514279407527
}
```

## squad2: Guidance harms quality

Case `r18/squad2/571c8eb9dd7acb1400e4c0f8`; reference(s): `["weight"]`.

Question: What did Lavoisier perceive the air had lost as much as the tin had gained

Evidence:

- [S01] In one experiment, Lavoisier observed that there was no overall increase in weight when tin and air were heated in a closed container.
- [S02]  He noted that air rushed in when he opened the container, which indicated that part of the trapped air had been consumed.
- [S03]  He also noted that the tin had increased in weight and that increase was the same as the weight of the air that rushed back in.
- [S04]  This and other experiments on combustion were documented in his book Sur la combustion en général, which was published in 1777.
- [S05]  In that work, he proved that air is a mixture of two gases; 'vital air', which is essential to combustion and respiration, and azote (Gk.
- [S06]  ἄζωτον "lifeless"), which did not support either.
- [S07]  Azote later became nitrogen in English, although it has kept the name in French and several other European languages.

**native**: quality 0.1000; EM/correct 0; token_limit; provider `unasked`.

````text
According to Lavoisier's observations, the air had lost the weight of the nitrogen gas (azote) that was consumed during the combustion experiment, while
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
Lavoisier observed that the air had lost part of itself as much as the tin had gained.
````

**boundary_gate**: quality 0.1000; EM/correct 0; token_limit; provider `unasked`.

````text
According to Lavoisier's observations, the air had lost the weight of the nitrogen gas (azote) that was consumed during the combustion experiment, while
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.12134317435629782,
  "source_entropy": 0.8909844577368344,
  "head_disagreement": 0.07110179654394112
}
```

## squad2: Gate skips a benefit

Case `r18/squad2/56e19724cd28a01900c679f9`; reference(s): `["integer factorization", "integer factorization problem", "the integer factorization problem"]`.

Question: In addition to the traveling salesman problem, what is another example of a function problem?

Evidence:

- [S01] A function problem is a computational problem where a single output (of a total function) is expected for every input, but the output is more complex than that of a decision problem, that is, it isn't just yes or no.
- [S02]  Notable examples include the traveling salesman problem and the integer factorization problem.

**native**: quality 0.2727; EM/correct 0; eos; provider `unasked`.

````text
Based on the given evidence, another example of a function problem, in addition to the traveling salesman problem, is the integer factorization problem.
````

**always**: quality 0.3333; EM/correct 0; eos; provider `complete`.

````text
The traveling salesman problem
````

**boundary_gate**: quality 0.2727; EM/correct 0; eos; provider `unasked`.

````text
Based on the given evidence, another example of a function problem, in addition to the traveling salesman problem, is the integer factorization problem.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.13019273642566986,
  "source_entropy": 0.9999689607336713,
  "head_disagreement": 0.0859514279407527
}
```

## squad2: Gate skips a harm

Case `r18/squad2/571c8eb9dd7acb1400e4c0f8`; reference(s): `["weight"]`.

Question: What did Lavoisier perceive the air had lost as much as the tin had gained

Evidence:

- [S01] In one experiment, Lavoisier observed that there was no overall increase in weight when tin and air were heated in a closed container.
- [S02]  He noted that air rushed in when he opened the container, which indicated that part of the trapped air had been consumed.
- [S03]  He also noted that the tin had increased in weight and that increase was the same as the weight of the air that rushed back in.
- [S04]  This and other experiments on combustion were documented in his book Sur la combustion en général, which was published in 1777.
- [S05]  In that work, he proved that air is a mixture of two gases; 'vital air', which is essential to combustion and respiration, and azote (Gk.
- [S06]  ἄζωτον "lifeless"), which did not support either.
- [S07]  Azote later became nitrogen in English, although it has kept the name in French and several other European languages.

**native**: quality 0.1000; EM/correct 0; token_limit; provider `unasked`.

````text
According to Lavoisier's observations, the air had lost the weight of the nitrogen gas (azote) that was consumed during the combustion experiment, while
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
Lavoisier observed that the air had lost part of itself as much as the tin had gained.
````

**boundary_gate**: quality 0.1000; EM/correct 0; token_limit; provider `unasked`.

````text
According to Lavoisier's observations, the air had lost the weight of the nitrogen gas (azote) that was consumed during the combustion experiment, while
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.12134317435629782,
  "source_entropy": 0.8909844577368344,
  "head_disagreement": 0.07110179654394112
}
```

## squad2: Correct recognized abstention

Case `r18/squad2/5a0c6c78f5590b0018dab404`; reference(s): `[]`.

Question: What has been easily proven about the rain forest

Evidence:

- [S01] There is evidence that there have been significant changes in Amazon rainforest vegetation over the last 21,000 years through the Last Glacial Maximum (LGM) and subsequent deglaciation.
- [S02]  Analyses of sediment deposits from Amazon basin paleolakes and from the Amazon Fan indicate that rainfall in the basin during the LGM was lower than for the present, and this was almost certainly associated with reduced moist tropical vegetation cover in the basin.
- [S03]  There is debate, however, over how extensive this reduction was.
- [S04]  Some scientists argue that the rainforest was reduced to small, isolated refugia separated by open forest and grassland; other scientists argue that the rainforest remained largely intact but extended less far to the north, south, and east than is seen today.
- [S05]  This debate has proved difficult to resolve because the practical limitations of working in the rainforest mean that data sampling is biased away from the center of the Amazon basin, and both explanations are reasonably well supported by the available data.

**native**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
The evidence does not establish anything that has been easily proven about the rainforest.
````

**always**: quality 0.0000; EM/correct 0; token_limit; provider `complete`.

````text
The evidence indicates that rainfall in the Amazon basin during the Last Glacial Maximum (LGM) was lower than it is today, leading to reduced moist tropical vegetation
````

**boundary_gate**: quality 1.0000; EM/correct 1; eos; provider `unasked`.

````text
The evidence does not establish anything that has been easily proven about the rainforest.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.122664021433593,
  "source_entropy": 0.9105675324438445,
  "head_disagreement": 0.07362527948961359
}
```

## squad2: Wrong recognized abstention

No matching case.

## squad2: Unrecognized nonempty output on missing evidence

Case `r18/squad2/5a0c817df5590b0018dab459`; reference(s): `[]`.

Question: What is the second smallest global producer of soybean?

Evidence:

- [S01] Between 1991 and 2000, the total area of forest lost in the Amazon rose from 415,000 to 587,000 square kilometres (160,000 to 227,000 sq mi), with most of the lost forest becoming pasture for cattle.
- [S02]  Seventy percent of formerly forested land in the Amazon, and 91% of land deforested since 1970, is used for livestock pasture.
- [S03]  Currently, Brazil is the second-largest global producer of soybeans after the United States.
- [S04]  New research however, conducted by Leydimere Oliveira et al., has shown that the more rainforest is logged in the Amazon, the less precipitation reaches the area and so the lower the yield per hectare becomes.
- [S05]  So despite the popular perception, there has been no economical advantage for Brazil from logging rainforest zones and converting these to pastoral fields.

**native**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
The second smallest global producer of soybeans is the United States.
````

**always**: quality 0.0000; EM/correct 0; eos; provider `complete`.

````text
The second smallest global producer of soybeans is Brazil.
````

**boundary_gate**: quality 0.0000; EM/correct 0; eos; provider `unasked`.

````text
The second smallest global producer of soybeans is the United States.
````

Gate requested Jev: `False`. Recorded native features:

```json
{
  "evidence_mass": 0.1272028943822079,
  "source_entropy": 0.9319549252851488,
  "head_disagreement": 0.0656909131738512
}
```

External evidence retains [HotpotQA](HotpotQA-NOTICE.md) and [SQuAD2.0](SQuAD-NOTICE.md) CC BY-SA 4.0 attribution.
