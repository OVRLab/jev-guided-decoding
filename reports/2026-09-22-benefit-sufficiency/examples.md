# R19 first-by-ID diagnostic examples

Selected deterministically from frozen metric differences; unblinded qualitative
inspection is supplementary, not independent semantic regrading. F1 improvement
can reflect answer length or incidental word overlap. No grades or policies change.
Static control signals are canned; shuffled signals come from a recorded donor.

## synthetic: dual_metric_benefit

Case `r19/test/0003/felanodi/heavy`. Question: Which room contains the parcel felanodi?
Reference(s): ["white"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.0000 | None | native | The room blue contains the parcel felanodi. |
| relevance | 1.0000 | 0.89 | relevance | The parcel felanodi is contained in the crate kaperige, which is located in the room white. |
| sufficiency | 0.0000 | 0.89 | native | The room blue contains the parcel felanodi. |
| dual | 1.0000 | 0.89 | relevance | The parcel felanodi is contained in the crate kaperige, which is located in the room white. |
| benefit_gate | 1.0000 | 0.89 | relevance | The parcel felanodi is contained in the crate kaperige, which is located in the room white. |
| instruction_always | 0.0000 | canned 0.0 | abstention | The room blue contains the parcel felanodi. |
| shuffled_sufficiency | 0.0000 | donor 0.62 | native | The room blue contains the parcel felanodi. |

Evidence:

- [E01] The room blue contains the locker nobecipe.
- [E02] The locker fuserupu contains the crate romotuvo.
- [E03] The crate kaperige contains the parcel felanodi.
- [E04] The room white contains the crate kasuroba.
- [E05] The locker cisecice contains the crate fudirase.
- [E06] The room green contains the locker mobipufi.
- [E07] The crate gagasoni contains the parcel dugevadi.
- [E08] The crate mekanelu contains the parcel fomecota.
- [E09] The room white contains the locker fuserupu.
- [E10] The crate fudirase contains the parcel madarico.
- [E11] The locker nobecipe contains the crate gagasoni.
- [E12] The crate romotuvo contains the parcel tanovosu.
- [E13] The crate rugidoco contains the crate kaperige.
- [E14] The crate fakikima contains the parcel vicosacu.
- [E15] The room white contains the locker penigune.
- [E16] The locker mobipufi contains the crate mekanelu.
- [E17] The crate kasuroba contains the crate rugidoco.
- [E18] The locker risucava contains the crate fakikima.
- [E19] The crate gitabaru contains the parcel lesatoko.
- [E20] The room blue contains the locker cisecice.
- [E21] The room yellow contains the locker risucava.
- [E22] The locker penigune contains the crate gitabaru.

## synthetic: dual_metric_harm

Case `r19/test/0005/divibigi/heavy`. Question: Which room contains the parcel divibigi?
Reference(s): ["blue"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 1.0000 | None | native | The room blue contains the parcel divibigi. |
| relevance | 0.0000 | 0.88 | relevance | The crate mevadeba contains the crate momepaco, which contains the crate bedegome, which contains the crate rapopeku, which contains |
| sufficiency | 1.0000 | 0.88 | native | The room blue contains the parcel divibigi. |
| dual | 0.0000 | 0.88 | relevance | The crate mevadeba contains the crate momepaco, which contains the crate bedegome, which contains the crate rapopeku, which contains |
| benefit_gate | 0.0000 | 0.88 | relevance | The crate mevadeba contains the crate momepaco, which contains the crate bedegome, which contains the crate rapopeku, which contains |
| instruction_always | 1.0000 | canned 0.0 | abstention | The room blue contains the parcel divibigi. |
| shuffled_sufficiency | 0.0000 | donor 0.97 | relevance | The crate mevadeba contains the crate momepaco, which contains the crate bedegome, which contains the crate rapopeku, which contains |

Evidence:

- [E01] The crate magivafa contains the parcel vigemici.
- [E02] The locker cedoluvo contains the crate latipato.
- [E03] The room blue contains the locker fetisona.
- [E04] The room blue contains the crate mevadeba.
- [E05] The room red contains the locker dulofebi.
- [E06] The room yellow contains the locker cedoluvo.
- [E07] The crate dubaraki contains the crate bedegome.
- [E08] The crate gicorero contains the parcel garikega.
- [E09] The crate tacaduno contains the parcel selogogu.
- [E10] The locker fetisona contains the crate tacaduno.
- [E11] The crate facovuke contains the parcel kosamiva.
- [E12] The locker kakotedi contains the crate delotebo.
- [E13] The crate momepaco contains the crate dubaraki.
- [E14] The crate latipato contains the parcel dipofece.
- [E15] The locker lobesafe contains the crate facovuke.
- [E16] The locker dobateba contains the crate magivafa.
- [E17] The locker dulofebi contains the crate gicorero.
- [E18] The crate delotebo contains the parcel varasepa.
- [E19] The room yellow contains the locker kakotedi.
- [E20] The room black contains the locker lobesafe.
- [E21] The crate bedegome contains the crate rapopeku.
- [E22] The room blue contains the locker dobateba.
- [E23] The crate rapopeku contains the parcel divibigi.
- [E24] The crate mevadeba contains the crate momepaco.

## synthetic: sufficiency_improves_missing

Case `r19/test/0006/mupugara/heavy`. Question: Which room contains the parcel mupugara?
Reference(s): ["UNKNOWN"]; missing evidence: True.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.0000 | None | native | The evidence does not mention the room containing the parcel mupugara. |
| relevance | 0.0000 | 0.08 | relevance | The evidence does not mention the room containing the parcel mupugara. |
| sufficiency | 1.0000 | 0.08 | abstention | The evidence does not establish which room contains the parcel mupugara. |
| dual | 1.0000 | 0.08 | abstention | The evidence does not establish which room contains the parcel mupugara. |
| benefit_gate | 1.0000 | 0.08 | abstention | The evidence does not establish which room contains the parcel mupugara. |
| instruction_always | 1.0000 | canned 0.0 | abstention | The evidence does not establish which room contains the parcel mupugara. |
| shuffled_sufficiency | 1.0000 | donor 0.26 | abstention | The evidence does not establish which room contains the parcel mupugara. |

Evidence:

- [E01] The locker fokasare contains the crate mabovetu.
- [E02] The room blue contains the locker pimorape.
- [E03] The locker pimorape contains the crate gubotedi.
- [E04] The locker rumukeko contains the crate sitotado.
- [E05] The crate letesevi contains the parcel liberelo.
- [E06] The room yellow contains the locker fokasare.
- [E07] The locker dekofuga contains the crate segeroni.
- [E08] The room green contains the locker rumukeko.
- [E09] The room black contains the locker dekofuga.
- [E10] The crate ledesomi contains the parcel vogegita.
- [E11] The crate gubotedi contains the parcel nisecedo.
- [E12] The crate sitotado contains the parcel dituvela.
- [E13] The room red contains the locker nivetosi.
- [E14] The locker cadanina contains the crate letesevi.
- [E15] The room white contains the locker cadanina.
- [E16] The crate segeroni contains the parcel gipufolu.
- [E17] The crate mabovetu contains the parcel dibitabi.
- [E18] The locker nivetosi contains the crate ledesomi.

## synthetic: gate_missed_benefit

Case `r19/test/0006/mupugara/light`. Question: Which room contains the parcel mupugara?
Reference(s): ["UNKNOWN"]; missing evidence: True.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.0000 | None | native | The evidence does not mention a room containing the parcel mupugara. |
| relevance | 0.0000 | 0.11 | relevance | The evidence does not mention a room containing the parcel mupugara. |
| sufficiency | 1.0000 | 0.11 | abstention | The evidence does not establish that any room contains the parcel mupugara. |
| dual | 1.0000 | 0.11 | abstention | The evidence does not establish that any room contains the parcel mupugara. |
| benefit_gate | 0.0000 | None | native | The evidence does not mention a room containing the parcel mupugara. |
| instruction_always | 1.0000 | canned 0.0 | abstention | The evidence does not establish that any room contains the parcel mupugara. |
| shuffled_sufficiency | 0.0000 | donor 0.37 | native | The evidence does not mention a room containing the parcel mupugara. |

Evidence:

- [E01] The room white contains the locker cadanina.
- [E02] The crate letesevi contains the parcel liberelo.
- [E03] The locker cadanina contains the crate letesevi.

## synthetic: gate_avoided_harm

Case `r19/test/0024/covenola/light/dependency`. Question: Following the stated dependencies, which terminal colour does the task covenola lead to?
Reference(s): ["red"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 1.0000 | None | native | Based on the given dependencies, the task covenola leads to the terminal color red. |
| relevance | 0.0000 | 0.79 | relevance | [E01] |
| sufficiency | 1.0000 | 0.79 | native | Based on the given dependencies, the task covenola leads to the terminal color red. |
| dual | 0.0000 | 0.79 | relevance | [E01] |
| benefit_gate | 1.0000 | None | native | Based on the given dependencies, the task covenola leads to the terminal color red. |
| instruction_always | 1.0000 | canned 0.0 | abstention | Based on the given evidence, the task covenola leads to the terminal color red. |
| shuffled_sufficiency | 0.0000 | donor 0.97 | relevance | [E01] |

Evidence:

- [E01] The task covenola depends on the terminal red.
- [E02] The task nodivege depends on the task vetotunu.
- [E03] The task napafecu depends on the terminal yellow.
- [E04] The task vetotunu depends on the task napafecu.

## synthetic: sufficiency_harms_answerable

Case `r19/test/0065/sudasate/heavy/dependency`. Question: Following the stated dependencies, which terminal colour does the task sudasate lead to?
Reference(s): ["black"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.0000 | None | native | The task sudasate depends on the task muvamise, which in turn depends on the task lubifigu. The task lubifigu depends on |
| relevance | 1.0000 | 0.22 | relevance | Following the stated dependencies, the task sudasate leads to the terminal black. |
| sufficiency | 0.0000 | 0.22 | abstention | The evidence shows that the task sudasate depends on the task muvamise, which in turn depends on the task lubifigu. However, there |
| dual | 0.0000 | 0.22 | abstention | The evidence shows that the task sudasate depends on the task muvamise, which in turn depends on the task lubifigu. However, there |
| benefit_gate | 0.0000 | 0.22 | abstention | The evidence shows that the task sudasate depends on the task muvamise, which in turn depends on the task lubifigu. However, there |
| instruction_always | 0.0000 | canned 0.0 | abstention | The evidence shows that the task sudasate depends on the task muvamise, which in turn depends on the task lubifigu. However, there |
| shuffled_sufficiency | 1.0000 | donor 0.95 | relevance | Following the stated dependencies, the task sudasate leads to the terminal black. |

Evidence:

- [E01] The task muvamise depends on the task lubifigu.
- [E02] The task secapidu depends on the task nopobafi.
- [E03] The task fotenice depends on the task fefokabi.
- [E04] The task lelugaba depends on the terminal yellow.
- [E05] The task cebubufa depends on the terminal black.
- [E06] The task decanedo depends on the terminal yellow.
- [E07] The task fefokabi depends on the terminal red.
- [E08] The task rivosege depends on the task lelugaba.
- [E09] The task sudasate depends on the task muvamise.
- [E10] The task lubifigu depends on the task disokuga.
- [E11] The task nopobafi depends on the task decanedo.
- [E12] The task futurice depends on the task titeguno.
- [E13] The task vegikodu depends on the terminal green.
- [E14] The task nafusave depends on the task kibefedi.
- [E15] The task modirovo depends on the terminal white.
- [E16] The task legafeci depends on the task sebegaru.
- [E17] The task debonobu depends on the task negolubi.
- [E18] The task disokuga depends on the task futurice.
- [E19] The task kibefedi depends on the task cebubufa.
- [E20] The task sebegaru depends on the task vegikodu.
- [E21] The task titeguno depends on the terminal black.
- [E22] The task negolubi depends on the task modirovo.
- [E23] The task fotovado depends on the task rivosege.
- [E24] The task kupudife depends on the task fotenice.

## hotpot: dual_metric_benefit

Case `r19/hotpot/5a70f6425542994082a3e44c`. Question: Renamed in 2014, what was the vehicle offered as a prize to contestants on the first season of The Amazing Race Canada?
Reference(s): ["Chevrolet Corvette Stingrays"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2000 | None | native | The vehicle offered as a prize to contestants on the first season of The Amazing Race Canada was a Chevrolet Corvette Stingray. |
| relevance | 0.6667 | 0.76 | relevance | The Chevrolet Corvette Stingray |
| sufficiency | 0.2000 | 0.76 | native | The vehicle offered as a prize to contestants on the first season of The Amazing Race Canada was a Chevrolet Corvette Stingray. |
| dual | 0.6667 | 0.76 | relevance | The Chevrolet Corvette Stingray |
| benefit_gate | 0.6667 | 0.76 | relevance | The Chevrolet Corvette Stingray |
| instruction_always | 0.2000 | canned 0.0 | abstention | The vehicle offered as a prize to contestants on the first season of The Amazing Race Canada was a Chevrolet Corvette Stingray. |
| shuffled_sufficiency | 0.6667 | donor 0.96 | relevance | The Chevrolet Corvette Stingray |

Evidence:

- [D01] The Amazing Race 1 (China): The Amazing Race 1 () is a Chinese reality television series loosely based on the American reality TV series, "The Amazing Race". It is the first season of The Amazing Race (). It features eight teams of two in a race around the world. This is the second version of "The Amazing Race" to be produced in China, following "". This new version is broadcast on Shenzhen TV, and had its premiere on October 17, 2014. The hosts for the show are Hong Kong actor Andy On and Singapore based Chinese-American actor Allan Wu, who was also the host of "The Amazing Race Asia" and "The Amazing Race: China Rush".
- [D02] List of The Amazing Race Canada contestants: This is a list of contestants who have appeared on "The Amazing Race Canada", a Canadian reality game show based on the American series, "The Amazing Race". A total of 104 contestants have appeared in the series.
- [D03] The Amazing Race Canada: The Amazing Race Canada is a reality television competition series that features teams in a grueling race across Canada and the world. The Race is divided into a series of legs and on each leg; teams strive to reach the Pit Stop where they are greeted by the host, Jon Montgomery. During each leg teams receive destination clues and challenges to complete in order to move onto the next task. The first team to cross the finish line wins $500,000 in cash and prizes. This prize is the largest grand prize ever awarded for a Canadian competition series. Commissioned by CTV, "The Amazing Race Canada" is produced by Insight Productions in association with Bell Media and with the support of Profiles Television.
- [D04] The Amazing Race 18: The Amazing Race 18 (also known as The Amazing Race: Unfinished Business) is the eighteenth installment of the reality television show "The Amazing Race". "The Amazing Race 18" featured eleven teams of two – each returning from a previous edition for the first time since Season 11 – in a race around the world for a $1 million prize.
- [D05] The Amazing Race en Discovery Channel 1: The Amazing Race en Discovery Channel (English: The Amazing Race on Discovery Channel ; Portuguese: "The Amazing Race no Discovery Channel" ) is a Latin American reality television game show based on the American series, "The Amazing Race". The first season of the show featured eleven teams of two with a pre-existing relationship, in a race across Latin America to win US$250,000. The race was produced by RGB Entertainment. The host of the show is Harris Whitbeck.
- [D06] The Amazing Race Canada 3: The third season of The Amazing Race Canada is a reality game show based on the American series "The Amazing Race". It features twelve teams of two, each with a pre-existing relationship. The grand prize includes: a CA$ cash payout, “gas for life” from Petro-Canada, the opportunity to fly for a year anywhere Air Canada flies worldwide in Business Class, and two Chevrolet Colorado "Z71" Trucks. For the third year in a row, Jon Montgomery returned as the host.
- [D07] The Amazing Race Canada 2: The second season of The Amazing Race Canada was a reality game show based on the American series "The Amazing Race". It featured eleven teams of two, each with a pre-existing relationship in a race across Canada and around the world. The winning team was awarded CA$ , two Chevrolet Silverado "High Country Edition" trucks, free gasoline for life from Petro-Canada and the ability to fly for free anywhere for a year with Air Canada in business class. Jon Montgomery returned as the host.
- [D08] The Amazing Race Canada 1: The first season of The Amazing Race Canada was a reality game show based on the American series "The Amazing Race". It featured nine teams of two with pre-existing relationships who raced around Canada for CA$ , two Chevrolet Corvette Stingrays and an unlimited air travel for a year with Air Canada. The show was produced by Insight Productions, in association with Bell Media and was broadcast on CTV. The show was hosted by Canadian Olympian Jon Montgomery.
- [D09] Chevrolet Corvette (C7): The Chevrolet Corvette (C7) is a sports car produced by Chevrolet. The seventh generation Corvette was introduced for the 2014 model year as the first to bear the Corvette Stingray name since the 1968 third generation model. The first C7 Corvette was delivered in the third quarter of 2013.
- [D10] The Amazing Race Canada 4: The fourth season of The Amazing Race Canada is a reality game show based on the American series "The Amazing Race". It features 10 teams of two, each with a pre-existing relationship. The grand prize includes: a CA$ cash payout, a "once-in-a-lifetime" trip for two around the world with hotel accommodations provided by new sponsor Hotels.com, and the winning team's choice of any Chevrolet vehicle driven during the race. For the fourth year in a row, Jon Montgomery returned as the host.

## hotpot: gate_missed_benefit

Case `r19/hotpot/5a710d155542994082a3e520`. Question: Who was the defense counsel of a German woman who underwent Catholic exorcism rites during the year before her death?
Reference(s): ["Erich Schmidt-Leichner"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2000 | None | native | The defense counsel of a German woman who underwent Catholic exorcism rites during the year before her death was Erich Schmidt-Leichner. |
| relevance | 1.0000 | 0.76 | relevance | Erich Schmidt-Leichner |
| sufficiency | 0.2000 | 0.76 | native | The defense counsel of a German woman who underwent Catholic exorcism rites during the year before her death was Erich Schmidt-Leichner. |
| dual | 1.0000 | 0.76 | relevance | Erich Schmidt-Leichner |
| benefit_gate | 0.2000 | None | native | The defense counsel of a German woman who underwent Catholic exorcism rites during the year before her death was Erich Schmidt-Leichner. |
| instruction_always | 1.0000 | canned 0.0 | abstention | Erich Schmidt-Leichner |
| shuffled_sufficiency | 1.0000 | donor 0.96 | relevance | Erich Schmidt-Leichner |

Evidence:

- [D01] Anna Ecklund: Anna Ecklund (sometimes documented as Emma Schmidt) was an American woman whose alleged demonic possession and exorcism occurred over several decades, culminating in an extensive exorcism that lasted from August 18 to December 23, 1928 in Earling, Iowa. Ecklund was said to have exhibited symptoms akin to possession beginning at age fourteen, and was forty six-years-old during her final exorcism by Father Theophilus Riesinger, a German Roman Catholic priest.
- [D02] Chief Defense Counsel (United States): The Chief Defense Counsel is a United States Department of Defense military position created by the Military Commissions Act of 2006 to supervise military and civilian defense attorneys for Guantanamo Bay detention camp prisoners in the Guantanamo military commission. The Office of the Chief Defense Counsel is a component of the Office of Military Commissions.
- [D03] Erich Schmidt-Leichner: Erich Schmidt-Leichner (14 October 1910 – 17 March 1983) was a German lawyer who made a name as a distinguished defense counsel at the Nuremberg Trials (1945 - 1946). In 1978, he was a defense counsel in the "Klingenberg Case" (Anneliese Michel), where a married couple were accused of negligent homicide for failing to call a medical doctor during an exorcism of their daughter.
- [D04] Air Force Legal Operations Agency: The Air Force Legal Operations Agency (AFLOA) includes all senior defense counsel, senior trial counsel, and appellate defense and government counsel in the Air Force, as well as all Air Force civil litigators defending the Air Force against civil law suits claiming damages and seeking other remedies in contracts, environmental, labor, and tort litigation. The agency includes numerous field support centers to include Tort Claim, Environmental Law, Labor Law, Commercial Litigation, Contract Law, Medical Law, and Accident Investigation Board. It also includes the utility litigation team, the Medical Cost Reimbursement program, and the Air Force Claims Service Center. The agency also includes the Judge Advocate General’s school and the Information Systems Directorate. This provides information technology services to worldwide Air Force legal offices and provides federal legal information technology through Federal Legal Information Technology and electronics services to legal offices throughout the Department of Defense. AFLOA has offices worldwide at more than 76 locations and consists of 426 military and civilian attorneys and 405 military and civilian paralegals and support personnel.
- [D05] Wiggins v. Smith: Wiggins v. Smith, 539 U.S. 510 (2003) is a case in which the United States Supreme Court spelled out standards for "effectiveness" in the constitutional right to legal counsel guaranteed by the Sixth Amendment. Previously the court had determined that the Sixth Amendment included the right to "effective assistance" of legal counsel, but it did not specify what constitutes "effective", thus leaving the standards for effectiveness vague. In "Wiggins v. Smith", the court set forth the American Bar Association Guidelines for the Appointment and Performance of Defense Counsel in Death Penalty Cases Guideline 11.8.6.(1989), as a specific guideline by which to measure effectiveness and competence of legal counsel.
- [D06] Anneliese Michel: Anneliese Michel ] (21 September 1952 – 1 July 1976) was a German woman who underwent Catholic exorcism rites during the year before her death. Later investigation determined that she was malnourished and dehydrated; her parents and the priests responsible were charged with negligent homicide. She was diagnosed with epileptic psychosis (temporal lobe epilepsy) and had a history of psychiatric treatment, which was overall not effective. Her condition worsened with her displaying various other symptoms which she took medication for as well. Michel and her family became convinced she was possessed by demons. The case attracted media and public attention because of the priests' unusual decision to employ a 400-year-old ritual of exorcism. The film "The Exorcism of Emily Rose" is loosely based on her story.
- [D07] Sophia Goudstikker: Sophia Goudstikker (1865-1924) was a Dutch-born German photographer and feminist pioneer. She was one of the premier women's rights activists in Munich at the turn of the century and a business partner and companion of Anita Augspurg. When their partnership dissolved, Goudstikker became a more moderate feminist and partnered with Ika Freudenberg. Goudstikker was the inspiration for three different writers' depictions of a more masculine woman, who defied typical feminine characterizations. She was the first unmarried German woman to obtain a royal license for photography and the first German woman allowed to argue cases before the youth court.
- [D08] Dwight H. Sullivan: Dwight H. Sullivan is a military officer and lawyer. From 2005 to 2007, he served as the Chief Defense Counsel for the Office of Military Commissions. In 2007, he became a civilian lawyer working for the Air Force doing death penalty defense appellate work. Sullivan is a colonel in the United States Marine Corps Reserve. He is a graduate of the University of Maryland and the University of Virginia School of Law. Prior to his role in defending the Guantanamo Bay detainees he worked with the Maryland office of the American Civil Liberties Union.
- [D09] United States military jury: A United States military jury (or "Members", in military parlance) serves a function similar to an American civilian jury, but with several notable differences. Only a General Court-Martial (which, depending on the offense, may impose any sentence including death and a dishonorable discharge) or Special Court-Martial (which, depending on the offense, can impose a sentence up to one year in confinement and a bad-conduct discharge) includes members. There are no members in a trial by Summary Court-Martial (which, depending on the offense, can impose a sentence up to 30 days in confinement). If the accused at a general court-martial or special court-martial chooses to be tried by members rather than by a military judge alone, then the members are responsible for both rendering a verdict and a sentence should the accused be found guilty of the charges. The charges are brought forward by an officer called a "convening authority", and the convening authority also personally selects each of the members who will try the accused. The charges which have been levied by the convening authority are prosecuted at courts-martial by Judge Advocates called "trial counsel". Accused persons facing general or special courts-martial receive representation free of charge from Judge Advocates acting as defense counsel. Accused persons may also be represented at general or special courts-martial by civilian attorneys hired at their own expense. While not required by Congressional law, service policy provides that many military accused receive the benefit of representation from a Judge Advocate defense counsel free of charge at summary courts-martial as well.
- [D10] The Exorcism of Emily Rose: The Exorcism of Emily Rose is a 2005 American legal drama horror film directed by Scott Derrickson and starring Laura Linney and Tom Wilkinson. The film is loosely based on the story of Anneliese Michel and follows a self-proclaimed agnostic who acts as defense counsel (Linney) representing a parish priest (Wilkinson), accused by the state of negligent homicide after he performed an exorcism.

## hotpot: dual_metric_harm

Case `r19/hotpot/5a732aaa5542992359bc325a`. Question: Which career path did African-American activist Bertha Gilkey pursue in St. Louis, Missouri?
Reference(s): ["Property management"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2500 | None | native | Tenant management of public housing properties |
| relevance | 0.1176 | 0.9 | relevance | Bertha Gilkey pursued a career in tenant management of public housing properties in St. Louis, Missouri. |
| sufficiency | 0.2500 | 0.9 | native | Tenant management of public housing properties |
| dual | 0.1176 | 0.9 | relevance | Bertha Gilkey pursued a career in tenant management of public housing properties in St. Louis, Missouri. |
| benefit_gate | 0.2500 | None | native | Tenant management of public housing properties |
| instruction_always | 0.2500 | canned 0.0 | abstention | Tenant management of public housing properties. |
| shuffled_sufficiency | 0.2500 | donor 0.61 | native | Tenant management of public housing properties |

Evidence:

- [D01] Old North St. Louis: Old North St. Louis is a neighborhood just north and slightly west of the downtown area of St. Louis, Missouri. Known for the landmark Crown Candy Kitchen, historic 19th century brick homes, and its award-winning community gardens, the neighborhood now known as Old North St. Louis was established as the independent village of North St. Louis in 1816 and was annexed by the City of St. Louis in 1841. After many generations as a very densely populated neighborhood, Old North St. Louis experienced several decades of population losses and deterioration of the community's housing stock. Over the past several years, however, the community has started to experience a dramatic revitalization led by the community-based Old North St. Louis Restoration Group, a non-profit organization. ONSLRG pursues a mission of revitalizing the physical and social dimensions of the Old North St. Louis neighborhood in a manner that respects the neighborhood's historic, cultural and urban character.
- [D02] Property management: Property management is the operation, control, and oversight of real estate as used in its most broad terms. Management indicates a need to be cared for, monitored and accountability given for its useful life and condition. This is much akin to the role of management in any business.
- [D03] Bertha Gilkey: Bertha Gilkey (née Knox; March 18, 1949 – May 25, 2014) was an African-American activist of tenant management of public housing properties. She set up the first tenant management association in St. Louis, Missouri, which successfully rehabilitated the once decrepit Cochran Gardens public housing project, and managed it for more than 20 years.
- [D04] Streetcars in St. Louis: Streetcars in St. Louis, Missouri operated as part of the transportation network of St. Louis from the middle of the 19th century through the early 1960s. During the first forty years of the streetcar in the city, a variety of private companies operated several dozen lines; from the start of the 20th century, most of these companies consolidated into the St. Louis Public Service Company, which served both the city of St. Louis and neighboring St. Louis County, Missouri. Other private companies, such as those serving the Metro East region or St. Charles, Missouri, continued separate operations. Starting in the 1930s and continuing through the 1960s, St. Louis Public Service ended all streetcar service, while other regional operators also ended their services.
- [D05] St. Louis tornado history: The St. Louis, Missouri metropolitan area has a history of tornadoes. The third-deadliest, and the costliest in United States history, the 1896 St. Louis – East St. Louis tornado, injured more than one thousand people and caused at least 255 fatalities in the City of St. Louis and in East St. Louis. The second-costliest tornado also occurred in St. Louis in September 1927. More tornado fatalities occurred in St. Louis than any other city in the United States. Also noteworthy is that destructive tornadoes occurred in winter and autumn, as well as the typical months of spring. Additionally, damaging tornadoes occurred in the morning and late at night, as well as the more common late-afternoon to early-evening maximum period.
- [D06] T.R. Carr: T.R. Carr was the mayor of the city of Hazelwood, Missouri in northern St. Louis County, Missouri, from April 2000 until April 2009. He is Professor of Public Administration at Southern Illinois University Edwardsville (SIUE) and Senior Research Fellow at the Institute for Urban Research at SIUE. Carr represents SIUE on the State University Retirement System Member Advisory Board. He is board member and Treasurer of the St. Louis - Samara (Russia) Sister City Committee. Carr is a member of the Board of North County, Inc., an economic development organization in St. Louis County. He is a Commissioner on the St. Louis County Boundary Commission that reviews all municipal annexation plans within St. Louis County. He is a Board Member for the Northwest Chamber of Commerce in St. Louis County. Carr served on the Executive Board of the St. Louis County Municipal League and as League President 2007-2008. Carr served as Chairman of the Standing Committee on Policy and Resolutions of the Missouri Municipal League 2004 to 2009. He served on the St. Louis County Fire Standards Commission 2005 - 2009. He served on the East-West Gateway Council of Governments Board 2007-2009. Carr served as a member, then as Chairman of the Community Advisory Board for SSM Hospital 2000-2009. He has served as Department Chair of Public Administration and Policy Analysis and as Director of the Master of Public Administration Program at SIUE. He maintained these academic positions before, during, and after, his tenure as mayor.
- [D07] Bernard Gilkey: Otis Bernard Gilkey (born September 24, 1966 in St. Louis, Missouri) is a former Major League Baseball (MLB) player for the St. Louis Cardinals, New York Mets, Arizona Diamondbacks, Boston Red Sox, and Atlanta Braves. Primarily a left fielder, Gilkey occasionally played right field as well. He also played a small number of games as a center fielder, first baseman, and designated hitter. Gilkey was a right-handed batter.
- [D08] Louis Vasquez: Pierre Luis Vasquez (October 3, 1798 – September 5, 1868) was a mountain man and trader. He was born and raised at St. Louis, Missouri. Pierre Luis Vasquez was the son of Benito Vasquez and Marie-Julie Papin (daughter of Pierre Papin & Catherine Guichard. Benito was born in Galicia, Spain in 1738 son of Francisco Vasquez and Marie de La Ponte. Many historians write that Pierre Luis was a Mexican-American but he was of French and Spanish (European) descent. In 1823, he became a fur man, receiving his first license to trade with the Pawnee. By the early 1830s he had shifted his operations to the mountains, a popular and active mountain man and trader. Pierre Luis was nicknamed "Old Vaskiss" by other Mountain men. Vasquez became a partner of Andrew Sublette, perhaps in 1834, returned to St. Louis in 1835, and went back to trade on the South Platte that winter and built Fort Vasquez that year after obtaining a trading license in St. Louis, Missouri, from William Clark, the Superintendent of Indian Affairs. He traveled back and forth between the mountains and St. Louis almost yearly, his reputation growing. Unable to turn a profit, they sold Fort Vasquez to Lock and Randolph in 1840 who subsequently went bankrupt and abandoned the structures in 1842. Due to the bankruptcy, Luis Vasquez and Andrew Sublette could not collect the sum owed to them for the sale. Vasquez then became associated with Jim Bridger. By 1843 they had built Fort Bridger on Blacks Fork of the Green River, which became as much an emigrant station as trading post. At St. Louis in 1846 Vasquez married a widow, Mrs. Narcissa Land Ashcraft and took his new family, her son and daughter, to Fort Bridger in Wyoming. Vasquez opened a store at Salt Lake City in 1855. He and Bridger sold their fort in 1858, but Vasquez already had retired to Missouri. He died at his Westport home, and was buried at St. Mary's Church cemetery.
- [D09] 1927 St. Louis – East St. Louis tornado: The 1927 St. Louis – East St. Louis tornado was a powerful and devastating tornado that struck St. Louis, Missouri on September 29, 1927, at 1:00pm. The tornado is estimated to be at least a F3 or F4 on the Fujita scale. The 2nd deadliest tornado to occur in the St. Louis metropolitan area, it caused at minimum 72–79 deaths and injured more than 550 people all within a seven-to-twelve-mile long, 100–600 yard wide path. At one time it was the 2nd costliest tornado in US history. More than 200 city blocks were destroyed. It is one of four tornadoes (1871, 1896, 1927, 1959) that have torn through downtown St. Louis.
- [D10] James M. Carrington: James M. Carrington (April 17, 1904 – January 28, 1995) was a photographer and Democratic politician who served in the Missouri House of Representatives. Born in St. Louis, Missouri, he was first elected to the Missouri House of Representatives in 1972. In 1925, he graduated from Howard University with a degree in electrical engineering. Carrington was the first African-American photographer for the "St. Louis Globe-Democrat" and the first African-American to represent St. Louis County in the Missouri House of Representatives.

## hotpot: gate_avoided_harm

Case `r19/hotpot/5a732aaa5542992359bc325a`. Question: Which career path did African-American activist Bertha Gilkey pursue in St. Louis, Missouri?
Reference(s): ["Property management"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2500 | None | native | Tenant management of public housing properties |
| relevance | 0.1176 | 0.9 | relevance | Bertha Gilkey pursued a career in tenant management of public housing properties in St. Louis, Missouri. |
| sufficiency | 0.2500 | 0.9 | native | Tenant management of public housing properties |
| dual | 0.1176 | 0.9 | relevance | Bertha Gilkey pursued a career in tenant management of public housing properties in St. Louis, Missouri. |
| benefit_gate | 0.2500 | None | native | Tenant management of public housing properties |
| instruction_always | 0.2500 | canned 0.0 | abstention | Tenant management of public housing properties. |
| shuffled_sufficiency | 0.2500 | donor 0.61 | native | Tenant management of public housing properties |

Evidence:

- [D01] Old North St. Louis: Old North St. Louis is a neighborhood just north and slightly west of the downtown area of St. Louis, Missouri. Known for the landmark Crown Candy Kitchen, historic 19th century brick homes, and its award-winning community gardens, the neighborhood now known as Old North St. Louis was established as the independent village of North St. Louis in 1816 and was annexed by the City of St. Louis in 1841. After many generations as a very densely populated neighborhood, Old North St. Louis experienced several decades of population losses and deterioration of the community's housing stock. Over the past several years, however, the community has started to experience a dramatic revitalization led by the community-based Old North St. Louis Restoration Group, a non-profit organization. ONSLRG pursues a mission of revitalizing the physical and social dimensions of the Old North St. Louis neighborhood in a manner that respects the neighborhood's historic, cultural and urban character.
- [D02] Property management: Property management is the operation, control, and oversight of real estate as used in its most broad terms. Management indicates a need to be cared for, monitored and accountability given for its useful life and condition. This is much akin to the role of management in any business.
- [D03] Bertha Gilkey: Bertha Gilkey (née Knox; March 18, 1949 – May 25, 2014) was an African-American activist of tenant management of public housing properties. She set up the first tenant management association in St. Louis, Missouri, which successfully rehabilitated the once decrepit Cochran Gardens public housing project, and managed it for more than 20 years.
- [D04] Streetcars in St. Louis: Streetcars in St. Louis, Missouri operated as part of the transportation network of St. Louis from the middle of the 19th century through the early 1960s. During the first forty years of the streetcar in the city, a variety of private companies operated several dozen lines; from the start of the 20th century, most of these companies consolidated into the St. Louis Public Service Company, which served both the city of St. Louis and neighboring St. Louis County, Missouri. Other private companies, such as those serving the Metro East region or St. Charles, Missouri, continued separate operations. Starting in the 1930s and continuing through the 1960s, St. Louis Public Service ended all streetcar service, while other regional operators also ended their services.
- [D05] St. Louis tornado history: The St. Louis, Missouri metropolitan area has a history of tornadoes. The third-deadliest, and the costliest in United States history, the 1896 St. Louis – East St. Louis tornado, injured more than one thousand people and caused at least 255 fatalities in the City of St. Louis and in East St. Louis. The second-costliest tornado also occurred in St. Louis in September 1927. More tornado fatalities occurred in St. Louis than any other city in the United States. Also noteworthy is that destructive tornadoes occurred in winter and autumn, as well as the typical months of spring. Additionally, damaging tornadoes occurred in the morning and late at night, as well as the more common late-afternoon to early-evening maximum period.
- [D06] T.R. Carr: T.R. Carr was the mayor of the city of Hazelwood, Missouri in northern St. Louis County, Missouri, from April 2000 until April 2009. He is Professor of Public Administration at Southern Illinois University Edwardsville (SIUE) and Senior Research Fellow at the Institute for Urban Research at SIUE. Carr represents SIUE on the State University Retirement System Member Advisory Board. He is board member and Treasurer of the St. Louis - Samara (Russia) Sister City Committee. Carr is a member of the Board of North County, Inc., an economic development organization in St. Louis County. He is a Commissioner on the St. Louis County Boundary Commission that reviews all municipal annexation plans within St. Louis County. He is a Board Member for the Northwest Chamber of Commerce in St. Louis County. Carr served on the Executive Board of the St. Louis County Municipal League and as League President 2007-2008. Carr served as Chairman of the Standing Committee on Policy and Resolutions of the Missouri Municipal League 2004 to 2009. He served on the St. Louis County Fire Standards Commission 2005 - 2009. He served on the East-West Gateway Council of Governments Board 2007-2009. Carr served as a member, then as Chairman of the Community Advisory Board for SSM Hospital 2000-2009. He has served as Department Chair of Public Administration and Policy Analysis and as Director of the Master of Public Administration Program at SIUE. He maintained these academic positions before, during, and after, his tenure as mayor.
- [D07] Bernard Gilkey: Otis Bernard Gilkey (born September 24, 1966 in St. Louis, Missouri) is a former Major League Baseball (MLB) player for the St. Louis Cardinals, New York Mets, Arizona Diamondbacks, Boston Red Sox, and Atlanta Braves. Primarily a left fielder, Gilkey occasionally played right field as well. He also played a small number of games as a center fielder, first baseman, and designated hitter. Gilkey was a right-handed batter.
- [D08] Louis Vasquez: Pierre Luis Vasquez (October 3, 1798 – September 5, 1868) was a mountain man and trader. He was born and raised at St. Louis, Missouri. Pierre Luis Vasquez was the son of Benito Vasquez and Marie-Julie Papin (daughter of Pierre Papin & Catherine Guichard. Benito was born in Galicia, Spain in 1738 son of Francisco Vasquez and Marie de La Ponte. Many historians write that Pierre Luis was a Mexican-American but he was of French and Spanish (European) descent. In 1823, he became a fur man, receiving his first license to trade with the Pawnee. By the early 1830s he had shifted his operations to the mountains, a popular and active mountain man and trader. Pierre Luis was nicknamed "Old Vaskiss" by other Mountain men. Vasquez became a partner of Andrew Sublette, perhaps in 1834, returned to St. Louis in 1835, and went back to trade on the South Platte that winter and built Fort Vasquez that year after obtaining a trading license in St. Louis, Missouri, from William Clark, the Superintendent of Indian Affairs. He traveled back and forth between the mountains and St. Louis almost yearly, his reputation growing. Unable to turn a profit, they sold Fort Vasquez to Lock and Randolph in 1840 who subsequently went bankrupt and abandoned the structures in 1842. Due to the bankruptcy, Luis Vasquez and Andrew Sublette could not collect the sum owed to them for the sale. Vasquez then became associated with Jim Bridger. By 1843 they had built Fort Bridger on Blacks Fork of the Green River, which became as much an emigrant station as trading post. At St. Louis in 1846 Vasquez married a widow, Mrs. Narcissa Land Ashcraft and took his new family, her son and daughter, to Fort Bridger in Wyoming. Vasquez opened a store at Salt Lake City in 1855. He and Bridger sold their fort in 1858, but Vasquez already had retired to Missouri. He died at his Westport home, and was buried at St. Mary's Church cemetery.
- [D09] 1927 St. Louis – East St. Louis tornado: The 1927 St. Louis – East St. Louis tornado was a powerful and devastating tornado that struck St. Louis, Missouri on September 29, 1927, at 1:00pm. The tornado is estimated to be at least a F3 or F4 on the Fujita scale. The 2nd deadliest tornado to occur in the St. Louis metropolitan area, it caused at minimum 72–79 deaths and injured more than 550 people all within a seven-to-twelve-mile long, 100–600 yard wide path. At one time it was the 2nd costliest tornado in US history. More than 200 city blocks were destroyed. It is one of four tornadoes (1871, 1896, 1927, 1959) that have torn through downtown St. Louis.
- [D10] James M. Carrington: James M. Carrington (April 17, 1904 – January 28, 1995) was a photographer and Democratic politician who served in the Missouri House of Representatives. Born in St. Louis, Missouri, he was first elected to the Missouri House of Representatives in 1972. In 1925, he graduated from Howard University with a degree in electrical engineering. Carrington was the first African-American photographer for the "St. Louis Globe-Democrat" and the first African-American to represent St. Louis County in the Missouri House of Representatives.

## hotpot: sufficiency_harms_answerable

Case `r19/hotpot/5a764c0b55429976ec32bd89`. Question: What criteria subjectively qualifies the Houston Astrodome to be called the Eighth Wonder of the World?
Reference(s): ["comparable to the seven Wonders of the World"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.4138 | None | native | The Houston Astrodome was called the Eighth Wonder of the World because it was a groundbreaking, innovative structure that was considered to be comparable to the seven Wonders |
| relevance | 0.2105 | 0.25 | relevance | The Houston Astrodome was named the Eighth Wonder of the World during its opening in 1965. |
| sufficiency | 0.1429 | 0.25 | abstention | The Houston Astrodome was called the Eighth Wonder of the World because it was groundbreaking and innovative in its design and construction, featuring a large, multi-purpose, |
| dual | 0.1429 | 0.25 | abstention | The Houston Astrodome was called the Eighth Wonder of the World because it was groundbreaking and innovative in its design and construction, featuring a large, multi-purpose, |
| benefit_gate | 0.4138 | None | native | The Houston Astrodome was called the Eighth Wonder of the World because it was a groundbreaking, innovative structure that was considered to be comparable to the seven Wonders |
| instruction_always | 0.1429 | canned 0.0 | abstention | The Houston Astrodome was called the Eighth Wonder of the World because it was groundbreaking and innovative in its design and construction, featuring a large, multi-purpose, |
| shuffled_sufficiency | 0.2105 | donor 0.74 | relevance | The Houston Astrodome was named the Eighth Wonder of the World during its opening in 1965. |

Evidence:

- [D01] For the Last Time: Live from the Astrodome: For the Last Time: Live From the Astrodome is the first live album released by George Strait in 2003. The title refers to the fact that this concert was the final event that took place at the Houston Astrodome.
- [D02] Live! The Last Concert: Live! The Last Concert is a live album by American singer Selena. It was recorded on February 26, 1995, at the Houston Astrodome and was televised live on Univision. The album was posthumously released by EMI Latin on March 27, 2001. The singer shared the concert with Tejano singer Emilio Navaira and performed to 66,994 people, which broke the previous attendance record held by Selena the previous year. The concert was critically acclaim for outperforming ticket sales by country music singers Vince Gill, Reba Mcentire, and George Strait. Selena's performance at the astrodome became her final televised concert before she was shot and killed on March 31, 1995.
- [D03] 1973 Astro-Bluebonnet Bowl: The 1973 Astro-Bluebonnet Bowl, part of the 1973 bowl game season, took place on December 29, 1973, at the Houston Astrodome in Houston, Texas. The competing teams were the Tulane Green Wave and Houston Cougars, with each competing as a football independent. Houston won the game 47–7.
- [D04] Fearless (Eighth Wonder album): Fearless is the 1988 debut album by British pop group Eighth Wonder. It is the group's only UK album release, is entirely uptempo, and contains six UK-issued singles (the earliest, "Stay With Me", dating back to 1985) including their highest-selling and best-remembered track, the Pet Shop Boys-produced and written "I'm Not Scared" (a #7 hit), and "Cross My Heart" (#13). "Fearless" peaked at #47 on the UK Albums Chart. Eighth Wonder split up in 1989, with lead singer Patsy Kensit going on to devote herself to her acting career.
- [D05] Astrodome: The NRG Astrodome, also known as the Houston Astrodome or simply The Astrodome, is the world's first multi-purpose, domed sports stadium, located in Houston, Texas. Construction on the stadium began in 1962, and it officially opened in 1965. It served as home to the Houston Astros of Major League Baseball (MLB) from its opening in 1965 until 1999, and the home to the Houston Oilers of the National Football League (NFL) from 1968 until 1996, and also the part-time home of the Houston Rockets of the National Basketball Association (NBA) from 1971 until 1975. Additionally, the Astrodome was the primary venue of the Houston Livestock Show and Rodeo from 1966 until 2002. When opened, it was named the Harris County Domed Stadium and was nicknamed the "Eighth Wonder of the World".
- [D06] Shreveport Steamer: The Shreveport Steamer were a professional American football team in the World Football League. The franchise began the 1974 season in Houston, Texas, as the Houston Texans, who are in no way related to the current NFL team of the same name, playing their home games at the Houston Astrodome. Toward the end of the season the team relocated to Shreveport, Louisiana, and became the Shreveport Steamer. They played at the 30,000-seat State Fair Stadium, now named Independence Stadium.
- [D07] 1965 Houston Astros season: The 1965 Houston Astros season was the franchise's first season in the Houston Astrodome, as well as its first season as the Astros after three seasons known as the Colt .45s. It involved the Houston Astros finishing in ninth place in the National League with a record of 65–97, 32 games behind the eventual World Series champion Los Angeles Dodgers. The Astros were managed by Lum Harris.
- [D08] Walter Suggs: Walt Suggs was a college and professional American football player. An offensive and defensive lineman, he played college football at Mississippi State University, and played professionally in the American Football League for the Houston Oilers from 1962 through 1969, and for the National Football League Oilers in 1970 and 1971. Suggs played in 137 consecutive games. He played in the first pro football game played in the Houston Astrodome in 1967. He was an American Football League All-Star in 1967 and 1968.
- [D09] Eighth Wonder of the World: Eighth Wonder of the World is an unofficial title sometimes given to new buildings, structures, projects, or even designs that are deemed to be comparable to the seven Wonders of the World.
- [D10] Brewster McCloud: Brewster McCloud is a 1970 experimental film directed by Robert Altman. It concerns a young recluse (Bud Cort, as the title character) who lives in a fallout shelter of the Houston Astrodome, where he is building a pair of wings so he can fly. He is helped by his comely and enigmatic "fairy godmother", played by Sally Kellerman, as he becomes a suspect in a series of murders. The film was shot on location in Houston, Texas. During the opening credits, shots of the downtown Houston skyline (with One Shell Plaza under construction) zoom toward the Houston Astrodome and Astrohall, with the emerging Texas Medical Center in the background. It was the first film shot inside the Astrodome.

## squad2: dual_metric_benefit

Case `r19/squad2/56be8c8a3aeaaa14008c90ab`. Question: For which song, did Destiny's Child take home the grammy award for best R&B performance?
Reference(s): ["\"Say My Name\""]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2308 | None | native | According to the evidence, Destiny's Child won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals for the song "Say My Name |
| relevance | 0.2609 | 0.89 | relevance | Based on the provided evidence, "Say My Name" won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals. |
| sufficiency | 0.2308 | 0.89 | native | According to the evidence, Destiny's Child won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals for the song "Say My Name |
| dual | 0.2609 | 0.89 | relevance | Based on the provided evidence, "Say My Name" won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals. |
| benefit_gate | 0.2609 | 0.89 | relevance | Based on the provided evidence, "Say My Name" won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals. |
| instruction_always | 0.2727 | canned 0.0 | abstention | According to the evidence, "Say My Name" won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals. |
| shuffled_sufficiency | 0.2308 | donor 0.49 | native | According to the evidence, Destiny's Child won the Grammy Award for Best R&B Performance by a Duo or Group with Vocals for the song "Say My Name |

Evidence:

- [S01] The group changed their name to Destiny's Child in 1996, based upon a passage in the Book of Isaiah.
- [S02]  In 1997, Destiny's Child released their major label debut song "Killing Time" on the soundtrack to the 1997 film, Men in Black.
- [S03]  The following year, the group released their self-titled debut album, scoring their first major hit "No, No, No".
- [S04]  The album established the group as a viable act in the music industry, with moderate sales and winning the group three Soul Train Lady of Soul Awards for Best R&B/Soul Album of the Year, Best R&B/Soul or Rap New Artist, and Best R&B/Soul Single for "No, No, No".
- [S05]  The group released their multi-platinum second album The Writing's on the Wall in 1999.
- [S06]  The record features some of the group's most widely known songs such as "Bills, Bills, Bills", the group's first number-one single, "Jumpin' Jumpin'" and "Say My Name", which became their most successful song at the time, and would remain one of their signature songs.
- [S07]  "Say My Name" won the Best R&B Performance by a Duo or Group with Vocals and the Best R&B Song at the 43rd Annual Grammy Awards.
- [S08]  The Writing's on the Wall sold more than eight million copies worldwide.
- [S09]  During this time, Beyoncé recorded a duet with Marc Nelson, an original member of Boyz II Men, on the song "After All Is Said and Done" for the soundtrack to the 1999 film, The Best Man.

## squad2: dual_metric_harm

Case `r19/squad2/56cf9d81234ae51400d9be1d`. Question: All five boroughs of New York City formed into one city on what date?
Reference(s): ["1898"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.1111 | None | native | Based on the evidence provided, the five boroughs of New York City were consolidated into a single city in 1898. |
| relevance | 0.1053 | 0.08 | relevance | Based on the evidence provided, all five boroughs of New York City were consolidated into a single city in 1898. |
| sufficiency | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| dual | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| benefit_gate | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| instruction_always | 0.0000 | canned 0.0 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| shuffled_sufficiency | 0.0000 | donor 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |

Evidence:

- [S01] Situated on one of the world's largest natural harbors, New York City consists of five boroughs, each of which is a separate county of New York State.
- [S02]  The five boroughs – Brooklyn, Queens, Manhattan, the Bronx, and Staten Island – were consolidated into a single city in 1898.
- [S03]  With a census-estimated 2014 population of 8,491,079 distributed over a land area of just 305 square miles (790 km2), New York is the most densely populated major city in the United States.
- [S04]  As many as 800 languages are spoken in New York, making it the most linguistically diverse city in the world.
- [S05]  By 2014 census estimates, the New York City metropolitan region remains by a significant margin the most populous in the United States, as defined by both the Metropolitan Statistical Area (20.1 million residents) and the Combined Statistical Area (23.6 million residents).
- [S06]  In 2013, the MSA produced a gross metropolitan product (GMP) of nearly US$1.39 trillion, while in 2012, the CSA generated a GMP of over US$1.55 trillion, both ranking first nationally by a wide margin and behind the GDP of only twelve and eleven countries, respectively.

## squad2: sufficiency_harms_answerable

Case `r19/squad2/56cf9d81234ae51400d9be1d`. Question: All five boroughs of New York City formed into one city on what date?
Reference(s): ["1898"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.1111 | None | native | Based on the evidence provided, the five boroughs of New York City were consolidated into a single city in 1898. |
| relevance | 0.1053 | 0.08 | relevance | Based on the evidence provided, all five boroughs of New York City were consolidated into a single city in 1898. |
| sufficiency | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| dual | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| benefit_gate | 0.0000 | 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| instruction_always | 0.0000 | canned 0.0 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |
| shuffled_sufficiency | 0.0000 | donor 0.08 | abstention | The evidence does not establish a specific date when all five boroughs of New York City formed into one city. |

Evidence:

- [S01] Situated on one of the world's largest natural harbors, New York City consists of five boroughs, each of which is a separate county of New York State.
- [S02]  The five boroughs – Brooklyn, Queens, Manhattan, the Bronx, and Staten Island – were consolidated into a single city in 1898.
- [S03]  With a census-estimated 2014 population of 8,491,079 distributed over a land area of just 305 square miles (790 km2), New York is the most densely populated major city in the United States.
- [S04]  As many as 800 languages are spoken in New York, making it the most linguistically diverse city in the world.
- [S05]  By 2014 census estimates, the New York City metropolitan region remains by a significant margin the most populous in the United States, as defined by both the Metropolitan Statistical Area (20.1 million residents) and the Combined Statistical Area (23.6 million residents).
- [S06]  In 2013, the MSA produced a gross metropolitan product (GMP) of nearly US$1.39 trillion, while in 2012, the CSA generated a GMP of over US$1.55 trillion, both ranking first nationally by a wide margin and behind the GDP of only twelve and eleven countries, respectively.

## squad2: gate_missed_benefit

Case `r19/squad2/56cfdc7f234ae51400d9bf8e`. Question: What was a possible reason for Chopin's failed engagement to Maria Wodzińska?
Reference(s): ["his poor health"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2222 | None | native | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and possibly rumors about his associations with women such as d' |
| relevance | 0.2308 | 0.76 | relevance | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and rumors about his associations with women such as d'Ag |
| sufficiency | 0.2222 | 0.76 | native | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and possibly rumors about his associations with women such as d' |
| dual | 0.2308 | 0.76 | relevance | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and rumors about his associations with women such as d'Ag |
| benefit_gate | 0.2222 | None | native | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and possibly rumors about his associations with women such as d' |
| instruction_always | 0.2308 | canned 0.0 | abstention | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and rumors about his associations with women such as d'Ag |
| shuffled_sufficiency | 0.2308 | donor 0.1 | abstention | A possible reason for Chopin's failed engagement to Maria Wodzińska was his poor health and rumors about his associations with women such as d'Ag |

Evidence:

- [S01] In 1836, at a party hosted by Marie d'Agoult, Chopin met the French author George Sand (born [Amantine] Aurore [Lucile] Dupin).
- [S02]  Short (under five feet, or 152 cm), dark, big-eyed and a cigar smoker, she initially repelled Chopin, who remarked, "What an unattractive person la Sand is.
- [S03]  Is she really a woman?" However, by early 1837 Maria Wodzińska's mother had made it clear to Chopin in correspondence that a marriage with her daughter was unlikely to proceed.
- [S04]  It is thought that she was influenced by his poor health and possibly also by rumours about his associations with women such as d'Agoult and Sand.
- [S05]  Chopin finally placed the letters from Maria and her mother in a package on which he wrote, in Polish, "My tragedy".
- [S06]  Sand, in a letter to Grzymała of June 1838, admitted strong feelings for the composer and debated whether to abandon a current affair in order to begin a relationship with Chopin; she asked Grzymała to assess Chopin's relationship with Maria Wodzińska, without realising that the affair, at least from Maria's side, was over.

## squad2: gate_avoided_harm

Case `r19/squad2/56f97d8a9e9bad19000a09b0`. Question: What is another name for Wu or Eastern Wu?
Reference(s): ["Sun Wu"]; missing evidence: False.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 0.2500 | None | native | Based on the evidence provided, another name for Wu or Eastern Wu is Sun Wu. |
| relevance | 0.1250 | 0.95 | relevance | Based on the evidence provided, another name for Wu or Eastern Wu is Eastern Wu. |
| sufficiency | 0.2500 | 0.95 | native | Based on the evidence provided, another name for Wu or Eastern Wu is Sun Wu. |
| dual | 0.1250 | 0.95 | relevance | Based on the evidence provided, another name for Wu or Eastern Wu is Eastern Wu. |
| benefit_gate | 0.2500 | None | native | Based on the evidence provided, another name for Wu or Eastern Wu is Sun Wu. |
| instruction_always | 0.5000 | canned 0.0 | abstention | Eastern Wu |
| shuffled_sufficiency | 0.1250 | donor 0.96 | relevance | Based on the evidence provided, another name for Wu or Eastern Wu is Eastern Wu. |

Evidence:

- [S01] Zhejiang was part of the Wu during the Three Kingdoms.
- [S02]  Wu (229–280), commonly known as Eastern Wu or Sun Wu, had been the economically most developed state among the Three Kingdoms (220–280 CE).
- [S03]  The historical novel Romance of the Three Kingdoms records that Zhejiang had the best-equipped, strong navy force.
- [S04]  The story depicts how the states of Wei (魏) and Shu (蜀), lack of material resources, avoided direct confrontation with the Wu.
- [S05]  In armed military conflicts with Wu, the two states relied intensively on tactics of camouflage and deception to steal Wu's military resources including arrows and bows.

## squad2: sufficiency_improves_missing

Case `r19/squad2/5a3b04c43ff257001ab84395`. Question: What happens to male and female parts of carpels that are hermaphrodites?
Reference(s): []; missing evidence: True.

| Arm | Frozen score | Sufficiency signal | Action | Output |
| --- | ---: | ---: | --- | --- |
| native | 1.0000 | None | native | The evidence does not establish what happens to male and female parts of carpels that are hermaphrodites. |
| relevance | 0.0000 | 0.48 | relevance | The evidence provided does not establish what happens to male and female parts of carpels that are hermaphrodites. |
| sufficiency | 1.0000 | 0.48 | native | The evidence does not establish what happens to male and female parts of carpels that are hermaphrodites. |
| dual | 1.0000 | 0.48 | native | The evidence does not establish what happens to male and female parts of carpels that are hermaphrodites. |
| benefit_gate | 1.0000 | None | native | The evidence does not establish what happens to male and female parts of carpels that are hermaphrodites. |
| instruction_always | 0.0000 | canned 0.0 | abstention | The evidence provided does not establish an answer to what happens to male and female parts of carpels that are hermaphrodites. |
| shuffled_sufficiency | 0.0000 | donor 0.8 | relevance | The evidence provided does not establish what happens to male and female parts of carpels that are hermaphrodites. |

Evidence:

- [S01] While the majority of flowers are perfect or hermaphrodite (having both pollen and ovule producing parts in the same flower structure), flowering plants have developed numerous morphological and physiological mechanisms to reduce or prevent self-fertilization.
- [S02]  Heteromorphic flowers have short carpels and long stamens, or vice versa, so animal pollinators cannot easily transfer pollen to the pistil (receptive part of the carpel).
- [S03]  Homomorphic flowers may employ a biochemical (physiological) mechanism called self-incompatibility to discriminate between self and non-self pollen grains.
- [S04]  In other species, the male and female parts are morphologically separated, developing on different flowers.
