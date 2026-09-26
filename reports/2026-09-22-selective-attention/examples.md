# R17 illustrative outputs

Selected by the first-by-ID rules registered in the
[diagnostic plan](../../research/selective-output-diagnostics.md), after the main artifact audit.
These are examples, not representative sampling or blinded human grading. Differences in
Hotpot exact match may reflect formatting instead of different factual content.

## Post-audit reading notes

These notes were added after reading the deterministically selected examples;
they do not change the frozen grades or establish a causal mechanism. Authored
rows use parser accuracy; their generic F1 field is not a meaningful authored metric.

- The first authored fix changes an incorrect room colour to the directly supported
  green answer. The first harm changes a correct blue answer into `[E03]` alone:
  a relevant citation without the requested answer, ending with EOS.
- Both Hotpot EM examples contain the correct named entity in both arms. The gain
  is a verbose Donald Trump Jr. answer becoming the bare name; the loss is a bare
  SAS Group answer becoming a correct longer sentence. These examples show score
  sensitivity to formatting, not improved or worsened factual knowledge.
- The natural-abstention example correctly states that the evidence does not
  establish a room, identically in both arms. In the missing-link example, native
  repeats the true parcel-to-crate fact without resolving the room, while guidance
  asserts red using a different parcel's chain. Both remain incorrect by the task
  contract; the assertion is unsupported by the displayed evidence.
- The two skip categories have no examples because the main gate skipped no input.

## Authored: guidance fixes native

Case `r17/test/0000/gadugina/heavy`; reference **green**.

Question: Which room contains the parcel gadugina?

Evidence:

- [E01] The crate bukogoli contains the parcel tapitufe.
- [E02] The locker kamemavu contains the crate gilolare.
- [E03] The crate bavivite contains the parcel kamesubi.
- [E04] The locker dekefemo contains the crate bavivite.
- [E05] The room green contains the parcel gadugina.
- [E06] The locker siserudu contains the crate bukogoli.
- [E07] The crate gilolare contains the parcel lerulofa.
- [E08] The crate rotavola contains the parcel cavekalu.
- [E09] The room red contains the locker siserudu.
- [E10] The room yellow contains the locker dekefemo.
- [E11] The room blue contains the locker baporumo.
- [E12] The locker pupitola contains the crate sanunago.
- [E13] The crate virinedu contains the parcel tureropi.
- [E14] The room white contains the locker kamemavu.
- [E15] The crate sanunago contains the parcel tekecifo.
- [E16] The locker baporumo contains the crate virinedu.
- [E17] The room blue contains the locker pupitola.
- [E18] The locker caciloto contains the crate rotavola.
- [E19] The room green contains the locker caciloto.

**native**; correct/EM 0; F1 0.0000; termination eos; provider unasked.

```text
Based on the evidence, the room red contains the parcel gadugina.
```

**always**; correct/EM 1; F1 0.3333; termination eos; provider complete.

```text
The room green contains the parcel gadugina.
```

**benefit_gate**; correct/EM 1; F1 0.3333; termination eos; provider complete.

```text
The room green contains the parcel gadugina.
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.3852875828742981,
  "mean_entropy": 0.43699937192900506,
  "copy_fraction": 0.5714285714285714
}
```

## Authored: guidance harms native

Case `r17/test/0001/nebalapi/light`; reference **blue**.

Question: Which room contains the parcel nebalapi?

Evidence:

- [E01] The crate botorofe contains the parcel gafirinu.
- [E02] The crate buvalagi contains the parcel nebalapi.
- [E03] The room blue contains the crate buvalagi.
- [E04] The room red contains the locker napapafi.
- [E05] The locker napapafi contains the crate botorofe.

**native**; correct/EM 1; F1 0.3333; termination eos; provider unasked.

```text
The room blue contains the parcel nebalapi.
```

**always**; correct/EM 0; F1 0.0000; termination eos; provider complete.

```text
[E03]
```

**benefit_gate**; correct/EM 0; F1 0.0000; termination eos; provider complete.

```text
[E03]
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.46154165267944336,
  "mean_entropy": 0.3249443350647425,
  "copy_fraction": 0.8571428571428571
}
```

## Authored: gate skips and avoids harm

No matching case.

## Authored: gate skips and misses a fix

No matching case.

## Hotpot: guidance improves strict EM

Case `r17/hotpot/5a7252db5542990c210a4104`; reference **Donald Trump Jr.**.

Question: What is the name of the oldest child that attended the Trump campaign-Russian meeting?

Evidence:

- [D01] Child Welfare League of America: The Child Welfare League of America (CWLA) is the oldest child welfare organization in the United States. The organization's primary objective is to "Make Children a National Priority. The CWLA is the trusted authority for professionals who work with children and the only national organization with members from both public and private agencies, providing unique access and influence to all sectors of the children’s services field.
- [D02] Domitia Lepida the Elder: Domitia ("PIR²" D 171), more commonly referred to as Domitia the Elder -- in fact no ancient source ever calls her Lepida - (ca. 8 BC-June 59) was the oldest child of Antonia Major and Lucius Domitius Ahenobarbus (consul 16 BC), and the oldest granddaughter to Triumvir Mark Antony by Octavia Minor, a great-niece of the Roman Emperor Augustus, second cousin and sister-in-law to the Emperor Caligula, first cousin to the Emperor Claudius, maternal aunt to the Empress Valeria Messalina, and paternal aunt to Emperor Nero. She had two younger siblings: Domitia Lepida and Cn. Domitius Ahenobarbus (cos. AD 32). The date of her birth is not recorded and can be only estimated as no later than 7 BC, but possibly as much as 10 years earlier, if one would allow a long delay between her birth and those of her two siblings.
- [D03] Mary Elizabeth Day Nursery: Mary Elizabeth Day Nursery, also known as Mary Elizabeth Day Care Center, is a historic building located in Sioux City, Iowa, United States. This is the oldest child day care facility in the state of Iowa, and the state's second-oldest preschool. The Sioux City Day Nursery was established in 1914 by the Wall Street Mission, a local settlement house operated by the Methodist Episcopal Church. They moved here in 1926, which is the first building designed as a day nursery in Iowa. The two-story brick Renaissance Revival building was designed by local architect Jurgen A. Raven, and built by The Lytle Company, a Sioux City construction firm. Parents were responsible for paying for at least part of their children's care, but it was also subsidized by religious institutions, private associations, and individuals. During the Great Depression, both the federal and state governments began to fund and license child care. The Works Progress Administration was involved in the 1930s. A garage and playhouse designed by Sioux City architect Knute E. Westerlind was built in 1940, and it is part of the historic designation. The facility was renamed the Mary Elizabeth Day Care Center in 1990. The building was listed on the National Register of Historic Places in 1997.
- [D04] Jessica Mulroney: Jessica Mulroney is a Canadian fashion stylist. Formerly Jessica Brownstein, on October 30, 2008 she married Ben Mulroney, the oldest son, and second oldest child, of Mila and Brian Mulroney, a former Prime Minister of Canada. Jessica Mulroney is Jewish. The couple have three children.
- [D05] Clayton Fountain: Clayton Anthony Fountain (September 12, 1955 – July 12, 2004) was a federal prisoner, member of the Aryan Brotherhood, and convicted murderer. Clayton was born on September 12, 1955, at the U.S. Army Hospital in Fort Benning, Georgia. Clayton was the oldest of six children, having one brother and four sisters, and was named after his father, Clayton Raleigh Fountain. The family moved every 1½ to 2 years. While his father served combat tours in Korea and Vietnam and his mother was working, Clayton, as the oldest child in family, became a surrogate for both parents when he was very young. He recalled maternal responsibilities for cooking, ironing, serving, cleaning, and caring for his young siblings. It was the male/paternal role, however, for which his father had carefully trained him. While serving in the Marines, he was convicted of murdering his staff sergeant in 1974, while stationed in the Philippines. He was sentenced to life imprisonment, and was ultimately sent to the United States Penitentiary, Marion, which was at the time the highest-security prison in the nation. Fountain used his military training to murder three prisoners and one correctional officer with a homemade knife while serving time at Marion, and was labeled the "Most Dangerous Prisoner" in the federal system.
- [D06] Clear Creek Meeting House: The Clear Creek Meeting House is a Friends meeting house located at 14365 N. 350th Ave., southeast of McNabb, in Magnolia Township, Putnam County, Illinois. The meeting house was built in 1875 to house the Illinois Yearly Meeting of the Religious Society of Friends, also known as the Quakers. The Yearly Meeting was the westernmost annual meeting of the Hicksite Friends and attracted followers from several states. The meeting house also hosted the Clear Creek Monthly Meeting, which was attended by local Quakers. The building is typical of American Friends meeting houses; it features two square rooms with plain features both outside and inside. The lack of ornamentation was designed to reflect the Quaker tenet of simplicity. The meeting house is one of the few surviving western Quaker meeting houses which represent this tradition of Quaker architecture.
- [D07] John Ingram McMorran: John Ingram McMorran (June 19, 1889 – February 24, 2003) was an American supercentenarian and was one of the recognized oldest people in the world, living to the age of 113 years, 250 days. He was born in Goodland Township, Michigan, the oldest child of George McMorran (born October 15, 1859) and Lydia Ingram. Ingram McMorran was the cousin of Representative Henry Gordon McMorran (1844–1929). His sister, Lillia Elizabeth Webb née McMorran, lived to the age of 103. In his youth, a fortuneteller predicted McMorran would live to age 111, but this seemingly outlandish forecast proved conservative, as barely one in six people who reach 111 live as long as McMorran finally did. At the time of his death in 2003, his grandson, Bob McMorran, was a grandfather himself, to the then five-year-old Logan Saxton. McMorran smoked, drank, and ate greasy food.
- [D08] Zeresenay Alemseged: Zeresenay (Zeray) Alemseged (born 4 June 1969) is an Ethiopian paleoanthropologist and was Chair of the Anthropology Department at the California Academy of Sciences in San Francisco, United States. He recently joined the faculty of the University of Chicago. He is best known for his discovery, on December 10, 2000, of Selam, also referred to as “Lucy’s child”, the almost-complete fossilized remains of a 3.3 million year old child of the species "Australopithecus afarensis". The “world’s oldest child”, she is the most complete skeleton of a human ancestor discovered to date. Selam represents a milestone in our understanding of human and pre-human evolution and contributes significantly to our understanding of the biology and childhood of early species in the human lineage; a subject about which we have very little information. Alemseged discovered Selam while working with the Dikika Research Project (DRP), a multi-national research project, which he both initiated in 1999 and leads. The DRP has thus far made many important paleoanthropological discoveries and returns to the field each year to conduct further important research. Alemseged’s specific research centers on the discovery and interpretation of hominin fossil remains and their environments, with emphasis on fieldwork designed to acquire new data on early hominin skeletal biology, environmental context, and behavior.
- [D09] Trump campaign–Russian meeting: On June 9, 2016, a meeting was held in Trump Tower in New York City between three senior members of the presidential campaign of Donald TrumpDonald Trump Jr., Jared Kushner, and Paul Manafortand at least five other people, including Russian lawyer Natalia Veselnitskaya. The meeting was arranged by publicist and long-time Trump acquantiance, Rob Goldstone on behalf of his client, singer-songwriter Emin Agalarov. It was disclosed to U.S. government officials when Kushner filed a revised version of his security clearance form.
- [D10] Donald Trump Jr.: Donald John Trump Jr. (born December 31, 1977) is an American businessman and former reality TV personality. He is the oldest child of the 45th President of the United States, Donald Trump, and his first wife, Ivana.

**native**; correct/EM 0; F1 0.3000; termination eos; provider unasked.

```text
Based on the provided evidence, the name of the oldest child that attended the Trump campaign-Russian meeting is Donald Trump Jr.
```

**always**; correct/EM 1; F1 1.0000; termination eos; provider complete.

```text
Donald Trump Jr.
```

**benefit_gate**; correct/EM 1; F1 1.0000; termination eos; provider complete.

```text
Donald Trump Jr.
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.538241982460022,
  "mean_entropy": 0.42671833393978886,
  "copy_fraction": 0.42857142857142855
}
```

## Hotpot: guidance harms strict EM

Case `r17/hotpot/5a721b9055429971e9dc9277`; reference **SAS Group**.

Question: What airline holding company located in Solna Municipality, Sweden owns a technical aircraft maintenance company located in Arlanda, Sweden?

Evidence:

- [D01] Solna centrum metro station: Solna centrum is a metro station and shopping mall in Solna Municipality, approximately 5 km from central Stockholm, Sweden. It is close to the Råsunda Stadium and opened on 31 August 1975. In Solna centrum there are around 120 stores and restaurants, 40 offices and 214 apartments.
- [D02] Marshall Aerospace and Defence Group: Marshall Aerospace and Defence Group is an aircraft maintenance, modification and design company located at Cambridge Airport, which it also owns and operates. The company covers all aspects of design, manufacture, maintenance, modification, conversion and logistic support of military, commercial and business aircraft. It employs over 4,400 people and is based on an 800 acre site with 1200000 sqft of covered hangar space. It works on a large variety of aircraft types and projects.
- [D03] Enkor: Enkor (full name is "Joint Stock Company (JSC) Enkor") was an airline based in Moscow, Russia. It operated scheduled international passenger services and provided technical aircraft maintenance. Its main bases were Domodedovo International Airport, Moscow, Ulan Ude Airport (UUD) and Chelyabinsk Airport (CEK). In 2004 the airline merged with S7 which inherited their fleet of TU-154M aircraft. The TU-134 and Yakovlev Yak-42 aircraft were retired and the TU-154B2 was sold to Kolavia.
- [D04] Solna Municipality: Solna Municipality (Swedish: "Solna kommun" or "Solna stad" , ] ) is a municipality in Stockholm County in south-east Sweden, located just north of the Stockholm City Centre. Its seat is located in the town of Solna, which is a part of the Stockholm urban area.
- [D05] SAS Frösundavik Office Building: The SAS Frösundavik Office Building is an office building in , Solna Municipality, Sweden, north of Stockholm. It servers as the head office of Scandinavian Airlines (SAS) and the SAS Group. The SAS head office was for a brief period located in a different building on the property of Stockholm Arlanda Airport in Sigtuna Municipality.
- [D06] SAS Group: Scandinavian Airlines System Aktiebolag (, Nasdaq: SAS , ), trading as SAS Group and SAS AB, is an airline holding company headquartered in the SAS Frösundavik Office Building in Solna Municipality, Sweden. It is the owner of the airlines Scandinavian Airlines. SAS used to own 19.9% of the now defunct Spanish airline Spanair. It also owns the aviation services companies SAS Business Opportunities, SAS Cargo Group, SAS Ground Services, and SAS Technical Services. It holds minority ownership of Air Greenland, Estonian Air, and Skyways Express. SAS Group is partially owned by the governments of Sweden, Denmark, and Norway, with a 21.4%, 14.3%, and 14.3% ownership, respectively. The remaining 50% is held by private owners, of which Foundation Asset Management at 7.6% is the only significant one. The company is listed on the Oslo Stock Exchange, the Stockholm Stock Exchange, and the Copenhagen Stock Exchange.
- [D07] Solna Church: Solna Church (Swedish: "Solna kyrka" ) is a so-called round church in Solna Municipality near Stockholm, Sweden. The church is located on the headland between "Brunnsviken" and "Ulvsundasjön", at the southern end of the cemetery Norra begravningsplatsen. The oldest parts of the church are from the later 12th century, a Romanesque fortress church built in stone.
- [D08] Aviation Repair Technologies: Aviation Repair Technologies (ART) is an aircraft maintenance company based in Blytheville, Arkansas (one hour north of Memphis, TN). It performs aircraft heavy maintenance, aircraft component repair, aircraft line maintenance, aircraft storage, and aircraft disassembly. The company was founded in 1998 and currently has 5 line maintenance locations in addition to its headquarters in Arkansas. The company has approximately 200 employees.
- [D09] GAMECO: Guangzhou Aircraft Maintenance Engineering Company Limited (Chinese:广州飞机维修工程有限公司), better known as GAMECO, is an aircraft maintenance company in Guangzhou, China. Located at Guangzhou Baiyun International Airport, GAMECO provides maintenance, repair and overhaul (MRO) services.
- [D10] SAS Technical Services: SAS Technical Services (STS) has changed name to SAS Tech. The company is owned by the SAS Group and provides technical maintenance of aircraft to airlines in and outside the SAS Group. The company is one of the world's 15 biggest providers of technical aircraft maintenance and the tenth biggest provider in Europe. SAS Tech has full-service contracts for nearly 250 aircraft. SAS Tech products cover line, base and heavy maintenance; component maintenance; engineering services; engine management; and maintenance training. It is headquartered at Arlanda outside Stockholm and has 3,600 employees.

**native**; correct/EM 1; F1 1.0000; termination eos; provider unasked.

```text
The SAS Group
```

**always**; correct/EM 0; F1 0.1739; termination eos; provider complete.

```text
The SAS Group is the airline holding company located in Solna Municipality, Sweden that owns a technical aircraft maintenance company located in Arlanda, Sweden.
```

**benefit_gate**; correct/EM 0; F1 0.1739; termination eos; provider complete.

```text
The SAS Group is the airline holding company located in Solna Municipality, Sweden that owns a technical aircraft maintenance company located in Arlanda, Sweden.
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.530003547668457,
  "mean_entropy": 0.6152193509042263,
  "copy_fraction": 1.0
}
```

## Authored: correct natural abstention

Case `r17/test/0006/relomusu/heavy`; reference **UNKNOWN**.

Question: Which room contains the parcel relomusu?

Evidence:

- [E01] The crate detisuba contains the parcel budepela.
- [E02] The room yellow contains the locker fetecipe.
- [E03] The locker bicobali contains the crate cekafalu.
- [E04] The locker fetecipe contains the crate povecota.
- [E05] The room green contains the locker copuduca.
- [E06] The room blue contains the locker tacimepe.
- [E07] The room black contains the locker rokosuke.
- [E08] The room blue contains the locker tecoteki.
- [E09] The locker tecoteki contains the crate detisuba.
- [E10] The room blue contains the locker bicobali.
- [E11] The crate repapeku contains the parcel suroceru.
- [E12] The locker tacimepe contains the crate repapeku.
- [E13] The crate tutedibu contains the parcel pulaleru.
- [E14] The crate sididave contains the parcel godufalu.
- [E15] The locker copuduca contains the crate tutedibu.
- [E16] The crate cekafalu contains the parcel vererido.
- [E17] The locker rokosuke contains the crate sididave.
- [E18] The crate povecota contains the parcel bacamafe.

**native**; correct/EM 1; F1 0.0000; termination eos; provider unasked.

```text
The evidence does not establish which room contains the parcel relomusu.
```

**always**; correct/EM 1; F1 0.0000; termination eos; provider complete.

```text
The evidence does not establish which room contains the parcel relomusu.
```

**benefit_gate**; correct/EM 1; F1 0.0000; termination eos; provider complete.

```text
The evidence does not establish which room contains the parcel relomusu.
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.7661103010177612,
  "mean_entropy": 0.3128371482504235,
  "copy_fraction": 0.375
}
```

## Authored: incorrect positive on missing evidence

Case `r17/test/0007/coluditu/heavy`; reference **UNKNOWN**.

Question: Which room contains the parcel coluditu?

Evidence:

- [E01] The crate monicade contains the parcel vapokago.
- [E02] The room white contains the locker kofafevo.
- [E03] The locker sekurice contains the crate mamokuko.
- [E04] The room black contains the locker donacica.
- [E05] The locker fugoneru contains the crate mikafive.
- [E06] The locker ficetele contains the crate monicade.
- [E07] The crate mikafive contains the parcel gidemina.
- [E08] The room black contains the locker sekurice.
- [E09] The crate gemesini contains the parcel fivulice.
- [E10] The crate mamokuko contains the parcel pugomese.
- [E11] The locker donacica contains the crate gemesini.
- [E12] The crate kasumafa contains the parcel coluditu.
- [E13] The room green contains the locker fovomomo.
- [E14] The room white contains the locker fugoneru.
- [E15] The locker fovomomo contains the crate lidavepo.
- [E16] The crate botakelu contains the parcel nebufima.
- [E17] The crate lidavepo contains the parcel malafosi.
- [E18] The room red contains the locker ficetele.
- [E19] The locker kofafevo contains the crate botakelu.

**native**; correct/EM 0; F1 0.0000; termination eos; provider unasked.

```text
[E12] The crate kasumafa contains the parcel coluditu.
```

**always**; correct/EM 0; F1 0.0000; termination eos; provider complete.

```text
The parcel coluditu is contained in the room red.
```

**benefit_gate**; correct/EM 0; F1 0.0000; termination eos; provider complete.

```text
The parcel coluditu is contained in the room red.
```

Gate requested Jev: `True`. Observed features:

```json
{
  "min_probability": 0.40335121750831604,
  "mean_entropy": 0.19678734812305265,
  "copy_fraction": 0.75
}
```

Hotpot-derived evidence retains [CC BY-SA 4.0 attribution](HotpotQA-NOTICE.md).
