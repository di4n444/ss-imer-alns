# PILOT TESTS - ključni nalazi za restart projekta

## Zašto ovaj dokument
Sažetak najvrjednijih nalaza iz pilot faze kako bi novi početak (na Bitcoin Alpha) krenuo s dobrim odlukama i bez ponavljanja slijepih ulica.

## 1) Najvažniji konceptualni nalaz
- **Topološka raznolikost seedova nije isto što i raznolikost kaskadnog dosega.**
- Više različitih čvorova (po degree/betweenness) davalo je **identičan** doseg do decimale jer su u live-edge scenarijima završavali u istoj SCC klasi dosega.
- Posljedica: odabir seedova mora biti vođen **dosegom** (ili SCC/do reach klase), ne samo centralnostima.

## 2) Evaluacija: što radi, što ne radi
- Stari pristup "prosjek preko svih čvorova" bio je skup i sklon slabijem signalu za optimizaciju.
- Bolji kompromis za ALNS:
  - **Targeted optimization** (jedan fiksni seed po eksperimentu),
  - puno in-sample live-edge scenarija (1000),
  - odvojena out-of-sample validacija (1000).
- Ključna praksa: **zamrznuti in-sample scenariji** za fer usporedbu između različitih budžeta i varijanti operatora.

## 3) Što je pokazao pilot run (NetGel, k=20)
- In-sample baseline (target seed 1836): **644.5390**
- In-sample best fitness: **653.6790**
- OOS baseline: **645.2620**
- OOS optimized: **654.3810**
- OOS porast: **+1.41%**

Interpretacija:
- Pomak postoji i generalizira izvan trening scenarija (nema očitog overfittinga na in-sample).
- Dobit je umjerena, što je očekivano kod već "dobro povezanih" seedova.

## 4) Operatori - što je korisno za start
- U pilotu su najkorisniji bili:
  - **spectral_repair**
  - **community_repair**
  - solidno i **random/degree destroy-repair**
- Betweenness operatori su često bili slabiji signal.
- Preporuka za novi kod:
  - zadrži puni set operatora,
  - ali logiraj contribution po operatoru od prve verzije (brza ablacijska analiza).

## 5) Candidate pool - praktična odluka
- Hybrid pool (spectral + degree + inter-community + random) je bio stabilniji od čistog uniform poola.
- Uniform pool je konceptualno "pošteniji", ali je u praksi razvodnio signal i otežao nalaženje dobrih bridova u istom budžetu iteracija.
- Za restart: krenuti s **hybrid pool** kao default, uniform koristiti kao baseline ablation.

## 6) Kritične tehničke lekcije
- Kod evaluacije obavezno raditi na **kopiji podgrafa** (`copy()`), da se scenariji ne kontaminiraju kroz iteracije.
- Za nove bridove u `mode="max"` dosljedno postaviti prijenosnu vjerojatnost (npr. prosjek postojećih bridova), i isto pravilo koristiti i u train i u OOS validaciji.
- Seed izbor za set eksperimenata treba pokriti više reach razina:
  - `reach_min`, `reach_low`, `reach_mid`, `reach_high`, `reach_max`.

## 7) Predloženi plan za novi početak (Bitcoin Alpha)
1. Učitavanje i čišćenje dataseta + konzistentan mapping na `weight/PROBABILITY`.
2. Generiranje fiksnog okruženja:
   - 1000 in-sample scenarija,
   - hybrid pool,
   - lista seedova po reach razinama.
3. Pilot matrica:
   - NetGel za `k in {10, 20, 50}`,
   - barem 3 seed klase: low/mid/high.
4. Za svaki run spremiti:
   - baseline IS, best IS, baseline OOS, best OOS, % gain,
   - finalne težine operatora.
5. Tek nakon toga širiti arhitekturu.

## 8) Što NE ponavljati
- Ne birati seedove samo po centralnosti.
- Ne uspoređivati runove na različitim in-sample scenarijima.
- Ne donositi zaključke samo iz in-sample fitnessa bez OOS provjere.

---

Ako se kod piše ispočetka, ovaj dokument je dovoljan kao "minimum viable methodology" za prvu stabilnu iteraciju.

---

## 9) Što je ovaj chat zapravo testirao (SS-IMER, ne NetGel)

Prethodni odjeljci (1–8) dolaze iz NetGel pilota (dodavanje bridova, max doseg). Kasnija implementacija u starom `kod/` bila je **SS-IMER**: minimizacija IC dosega iz **jednog fiksnog izvora** uklanjanjem točno `k` bridova.

Za restart na Bitcoin Alpha to znači:
- cilj je `min σ(s, G\D)` uz `|D|=k`, ne max/NetGel;
- fitness = SAA na **zamrznutim live-edge scenarijima**, spektralni `u_i·v_j` samo heuristika za rangiranje, **nikad** SA/ALNS fitness;
- validacija najboljeg cuta **out-of-sample** (u starom kodu: 500 SAA / 1000 MC). Ako novi kod ide na 1000/1000 kao u §2, to je OK — bitno je da IS i OOS budu odvojeni i zamrznuti.

## 10) Arhitektura koja je preživjela A/D test (hop-ALNS)

Stari local/global ALNS je mrtav. Ne uspoređivati novi kod s njim.

Što je ostalo nakon testa hop-mode **A vs D** (D je pobijedio gotovo svugdje):
- **Destroy = D**: uvijek na cijeli trenutni cut `D` (`|D|=k`). Odabrani hop-scope **nije filter** u destroyu.
- **Repair = D**: prvo puni `q` mjesta iz odabranog hop-sloja, ostatak iz cijelog **aktivnog** poola.
- Kandidati nisu cijeli `E`, nego bridovi dohvatljivi iz `s`, složeni po BFS hopu **repa** `u`: hop `h` ⇔ `dist(s,u)=h`.
- Horizon: `INITIAL_MAX_HOP=1` (hop0∪hop1), `HARD_CAP_MAX_HOP=5`. Na kraju epohe horizon +1 **samo ako** vanjski aktivni hop ima prosječnu nagradu **> 0**.
- Priori hopova: hop0=2, hop1=8, zatim `×0.5` po razini. Novi hop: `max(prior, 0.35·w_hop1)`, cap = težina hop1.
- Degree score: usmjereni `out(u)+out(v)` na **baznom** `G` (ne na live-edge realizaciji).
- Greedy baselinei (Random / Degree / Betweenness / Spectral / Community) biraju **samo hop0** (lokalna karantena), istim scoreovima kao ALNS. To je pravi null model: „jesi li uopće trebao ići dalje od susjeda izvora?“
- `q` dinamički: `q_min = max(1, ⌊0.1k⌋)`, `q_max = min(k-1, ⌊0.4k⌋)`.
- Ako `k > out(s)`: uzmi sve hop0 (izolacija), `k_eff = |hop0|`, **nemoj bacati ValueError**. ALNS smije stati kad je spread ≈ 1.

Roulette zasebno bira (i) hop-scope i (ii) heuristiku. Community heuristika: destroy preferira intra-community, repair inter-community — ista binarna oznaka kao baseline.

## 11) Empirija sa starog koda (nije finalni protokol, ali smjer)

Ovo **nije** za tablice u radu. Služi da se zna gdje hop≥1 ima smisla.

- Ekscentricitet / hop bridova od tipičnih izvora na Alpha ~6–8; neusmjereni promjer ~10. Cap=5 pokriva većinu mase — nema razloga dignuti cap „za svaki slučaj“.
- **2765, k=3**: kanonski choke case. Cut na hop≥1 (uplink susjeda u mega-hubove) bije hop0 karantenu. ALNS MC je bio u rangu ~77–108 ovisno o runu, bitno ispod hop0 greedyja. Ako novi kod ne može pobijediti hop0 na 2765/k=3, arhitektura je slomljena.
- **68 i 264**: često završe all-hop0, ali ALNS i dalje može biti bolji od najboljeg hop0 greedyja (bolje pretraživanje istog sloja).
- **51**: k=15 skroman pomak; k=25 veći. Budžet mijenja priču — isti seed nije jedan broj.
- **1, k=25**: ALNS **može izgubiti** hop0 Degree na MC. Hub+veliki k: lokalna karantena je jaka; ne tretirati ALNS kao uvijek-bolji.

Izvori za katalog: ne birati samo po betweennessu (već u §1). U starom kodu ID-evi su **interni igraph** nakon remapiranja, ne SNAP user ID. Katalog (`experiment_candidates.csv`) upsert po `source_node`; `role` / `discovery_method` spajati s `|`.

## 12) Bitcoin Alpha — brojke koje treba reproducirati pri loadu

Pozitivni ratingi (`RATING > 0`); negativni se bacaju. Sigmoid: `p = 1/(1+exp(-(R-5)))`.

Očekivano nakon tog filtera (zadnji `analyze_graph` run):
- N=3683, M=22650, `⟨k_out⟩=6.15`
- directed avg path 3.7395 vs ER 4.7237; C (undirected transitivity) 0.0760 vs ER 0.0030
- assortativity r=−0.1546 (disasortativna)
- SCC 3192 (86.7%), WCC 3670; k-core max=32, u 32-jezgri **73** čvora
- Louvain: **28** zajednica, Q=**0.4931**
- mean p=0.1063, median p=0.0180 — većina bridova slaba, mali broj jakih kanala

Dataset citirati Kumar et al. 2016 (ICDM) i Kumar et al. 2018 (WSDM / REV2), SNAP.

## 13) κ / λ_c — ne miješati definicije

- Klasični HMF: `λ_c = ⟨k⟩/⟨k²⟩` ≈ **0.021** na ovim podacima (Castellano & Pastor-Satorras).
- Stari `analyze_graph` ispisivao je `κ = ⟨k²⟩/⟨k⟩²` pa `λ_c = 1/κ = ⟨k⟩²/⟨k²⟩ = 0.1307`. To **nije** HMF prag i **nije** fitness.
- Ne tvrditi da je mreža „u kritičnom režimu“ jer je p blizu nekog od ta dva broja. Spektralni prag je `1/λ_max` (Wang; Castellano). Tong NetMelt smanjuje `λ_max` — srodni rad, drugi cilj.

## 14) Literatura — zamke koje su već koštale citate

- **Khalil 2014**: supermodularnost edge-deletion cilja je za **Linear Threshold**, ne IC. Smije se citirati kao srodni argument za sinergiju više bridova, ne kao teorem za IC SS-IMER.
- **Kempe 2003**: IC, live-edge, `1−1/e` za *max* sjemenki. Valiant 1979 za #P/pouzdanost. Sheldon 2010: ekologija + live-edge, **nije** izvor za SS-IMER greedy ni za nesubmodularnost.
- **Tong 2012**: `u_i·v_j` heuristika i motivacija „računi nisu poželjni, bridovi jesu“. Nije pravno/cenzura, nije naš fitness.
- **Kimura 2008**: contamination minimization = blocking links pod IC (≈SIR). To je pravi IMER srodnik.
- **Castiglioni 2021**: izbori / edge removal hardness — OK kao domena. **Ne** za nesubmodularnost IC cuta (samo citira Khalila).
- **Coró 2021**: link recommendation / influence max. **Nije** izvor Bitcoin Alpha grafa.
- Røpke–Pisinger: adaptivne težine + SA accept. Njihovi regret operatori nisu naši.

## 15) Što NE ponavljati (dodatak na §8, samo SS-IMER)

- Ne vraćati hop-mode A (destroy filtriran po hopu).
- Ne vraćati local/global ALNS usporedbu.
- Ne stavljati `λ_max` u fitness.
- Ne tvrdi „ALNS uvijek bije hop0“ — na hubovima s velikim k hop0 Degree je ozbiljan protivnik.
- Ne pisati rezultate/raspravu dok nema finalnog protokola (više izvora, dogovoreni k, isti frozen IS/OOS).
- Ne miješati interne igraph ID-eve s originalnim SNAP ID-evima u tekstu rada.

## 16) Minimalni smoke test za novi SS-IMER kod

Prije širenja na matricu seed×k:
1. Reproducirati load-brojke iz §12 (N, M, mean/median p).
2. Isti frozen IS scenariji za ALNS i sve hop0 baselinee.
3. Obavezni case: **source 2765, k=3** — ALNS treba moći uzeti hop≥1 i biti bolji od hop0 greedyja na OOS.
4. Kontrast: jedan hub (npr. interni ID 1) s većim k — očekuj hop0-teško; ALNS ne mora pobijediti.
5. Logirati contribution po (hop, heuristika) od prvog dana (isto načelo kao §4).

---

## 17) Što ovaj chat dodaje (faze 0–2 na SS-IMER / Bitcoin Alpha)

Odjeljci 1–16 ostaju. Ovo su kasnije zaključane odluke, bugovi koje novi kod ne smije ponoviti, i empirija koju stari `kod/` više ne drži. ID-evi su i dalje **igraph indeksi**, ne SNAP imena.

## 18) Dva buga koja ruše brojke ako se vrate

**igraph ime ≠ indeks.** `Graph.TupleList` čuva SNAP/SRC_ID kao *ime* vrha. Vrh 1 zove se npr. 398. CSR/`u,v` iz `build_graph` idu u poretku imena; ALNS boduje `u[i]·v[j]` po indeksu. Prije poravnanja Spearman(Tong, Δλ_max) ≈ 0.15; poslije **0.969**. Svaki Perron/CSR vektor permutirati na `graph.vs` indeks prije scorea. Bez toga Spectral baseline i spektralni operator su smeće.

**Nagrada za Δ = 0.** `exp(−0/T) = 1`, pa se potez koji ne mijenja SAA-σ prihvaća kao SA i (u starom kodu) dobivao je σ₃. Medijan Δσ po potezu je ~0, pa su `heuristic_stats` bili lažni. Pravilo: Δ=0 se smije prihvatiti, **nagrada 0**. σ₃ samo za stvarno gore. Posebno brojati σ₁ (`best_hits`) po heuristici i po hopu — to je jedini čist dokaz da je operator pomogao.

## 19) Odluke koje *mijenjaju* ranije stavke (ne brisati gore, ovdje vrijedi ovo)

- **`k ≥ out(s)` je tvrda greška**, ne izolacija. Izolacija izjednačuje sve metode. (Suprotno §10 „nemoj bacati ValueError“.)
- **Nema `hard_cap` na hop5.** Horizont kreće od hop0∪hop1 i širi se samo dok vanjski hop u epohi ima prosječnu nagradu > 0. Cap=5 je bio dekoracija (hop0..5 već ~svi dohvatljivi bridovi). `--horizon-limit` samo ablacija. U fazi 2 pretraga je znala otvoriti **hop 7**; to nije isto što i rez (vidi §23).
- **`p_ij` je i ALNS heuristika i hop0/hop0-1 baseline.** Bez nje H5 mjeri portfelj kojem fali najjači lokalni score. Spearman(p, out(u))≈0.03, Spearman(p, deg u+v)≈0.08 — p nije stupanj. Ablacija: jednom pokrenuti ALNS *bez* `probability`.
- **MinCut (max-flow s→jezgra, kapaciteti p) nije peer.** Mjeriti, izvještavati odvojeno (globalno znanje).
- **Warm start = k slučajnih hop0 bridova**, ne Degree. Inače je ALNS na hop0 po konstrukciji ≥ Degree.
- **Kalibracija na disjunktnom skupu** izvora, prije mjernih faza.
- SAA/MC u tom runu: **500 / 2000**, seedovi 42 / 999. Ako novi kod ide 1000/1000 (§2), OK; bitno je zamrznuto i odvojeno. Deterministički greedy (sve osim Random) računati jednom i reciklirati preko ALNS seedova.
- Louvain **obavezno seedati**. Neseedano u §12: 28 zajednica, Q=0.493. Sa `LOUVAIN_SEED=1234`: **30 / Q=0.47**. Community heuristika i Granovetter skaču bez seeda.

## 20) Spektralni prag i priča mreže (dopuna §13)

Ne koristiti `1/κ`. Na ovom loadu:

- λ_max(A)=38.95 ⇒ **λ_c = 1/λ_max(A) = 0.0257**
- λ_max(P)=7.63 ≫ 1; srednji p=0.106 ≈ 4× prag
- Mreža je duboko nadkritična. SS-IMER je **presijeci izvor od gigantske live-edge komponente** (~σ₀ zasićenih ≈ 620–647, ~17 % N), ne „uspori epidemiju“.
- Uklanjanje k bridova **ne pomiče prag**: medijan Δλ_max(P) nakon ALNS reza u fazi 2 ≈ 9·10⁻⁵. Tongov score smije ostati heuristika; fitness ostaje σ.

## 21) Okosnica i Granovetter — što se smije tvrditi

Statično (p prag 0.05): 79 % bridova p<0.05; najjačih 5 % nosi 44 % mase p. Podgraf p>0.05: SCC 3192→834, jezgra 32→13, Q 0.47→0.61. To je **sirova vs efektivna struktura grafa** — zadržati kao prikaz.

**Ne pisati** „kaskada živi na okosnici“. Na 40 izvora σ na podgrafu p>0.05 pada na medijan **~12 %** punog σ (samo ~30 % izvora zadrži >50 %). Slabi bridovi **zajedno** nose IC. To ruši staru poantu 1(a); ne dotjerivati, preformulirati: operatori s ugrađenim `p` procjenjuju što prerezati; čisti stupanj na ovom datasetu slabo bira jer je većina izlaza slaba.

Granovetter (inter vs intra p, fiksnom Louvainu): mean 0.095 vs 0.112, MW p=0.0012 — statistički da, praktički near-null. Ovisi o particiji (neseedano je bilo p=0.161). 1–2 rečenice kontrasta, ne slogan.

Jedan brid vs Δσ: medijan Δσ≈0; scoreovi nisu procjenitelji vrijednosti brida nego **pristrani uzorkivači** nad poolom punim nula. To opravdava pretragu. H5 formulirati tako, ne kao „scoreovi predviđaju Δσ“.

Spearman(σ₀, min-rez_p)≈0.96 vs (σ₀, out)≈0.64 — σ₀ prati grlo. H4 („R_k prati min-rez, ne stupanj“) **nije** isto; to treba isti out ili k-sweep, ne fiksni k=3 preko out=4…486.

## 22) ALNS defaulti nakon grube kalibracije (1b)

6 izvora **izvan** mjernog uzorka: 727, 1822, 45, 80, 422, 655. Jedan faktor po osi vs default.

Zadržano: `max_iter=300`, `segment_length=20`, `ρ=0.15`, q = `[max(1,⌊0.1k⌋), min(k−1,⌊0.4k⌋)]` (za k≤3 to je 1-swap).

Zašto: srednji MC pad default 62.7 % vs ρ=0.30 62.9 % — nije jasno. 150 iteracija na izvoru 80 bolje na SAA, **lošije na MC** (prenaučenost, isti obrazac kao 215/832). Širi q miješan. Ako razlike nisu jasne, ne dirati defaulte.

σ₁/σ₂/σ₃ = 33/9/13 ostaju.

## 23) Faza 2 — karta k=3, n=40 (korisno, nije protokol rada)

Uzorak 4×10 po out ∈ {[4,9],[10,19],[20,49],[50+]}, SCC, seed 7, disjunktno od §22. k=3 za sve, 1 ALNS seed. **Očekivano** da hab (out≥50) na k=3 ostane na σ≈644; to je kontrola budžeta, ne nalaz.

σ = očekivani broj zaraženih (IC live-edge). R_k = 1 − σ(k)/σ₀. Medijan jer su σ i R iskošeni (habovi s R≈0 vuku mean).

**Baselinei na MC (mean R_k preko 40):**
`p_ij` hop0 **0.48** | ALNS 0.52 | MinCut 0.52 (nije peer) | Spectral hop0 0.39 | Degree hop0 0.35 | Betweenness 0.34 | Random 0.21 | Community 0.18 | **bilo što na hop0∪hop1 ≈ 0.02**.

Greedy na širem poolu uzme hop1 bridove s velikim p koji **ne** zatvaraju izvor (718: hop0 `p` σ=48, hop0-1 `p` σ=642). Lokalna karantena je referentni null; širenje bez pretrage šteti.

ALNS vs najbolji hop0 greedy: **10 bolji / 18 isti / 12 lošiji**. Često isti rez kao `p_ij` kad je grlo na izlazima. Nije dominantan na k=3 (1-swap, slučajni start).

Kanonski parovi za novi smoke (uz 2765 iz §16):

- **718** (out=10, σ₀=642): `p_ij`/ALNS/MinCut → **47.7**; Degree/Spectral → **635**. Čisti stupanj promaši tri jaka izlaza.
- **883 / 1791** (out=20/22): `p_ij`=ALNS=MinCut, σ 57 / 75; Degree ostaje ~607 / 634.
- **585** (out=70): `p_ij` i MinCut **433**; ALNS **642**. Greedy po p vidi grlo; ALNS u 70 hop0 bridova s k=3 ga nije našao.
- **530** (out=23, min-rez_p≈5, 11 okosničkih izlaza): hop0 svi ~640; MinCut 529 — k=3 < širina grla, signal je globalniji.
- **832** (out=4): SAA-opt = ALNS, na MC lošiji od MC-opta među 4 hop0 reza (12.3 vs 9.4). Fitness ≠ izvještaj; nabrajanje hop0 na malom outu to razdvaja.
- Hop0 nabrajanje out≤9: ALNS pogodi SAA-opt **8/10**.

**Hop u rezu vs hop u pretrazi (ne miješati):**
- Najbolji cut: 101/120 bridova hop0; **31/40** čisti `0:3`. hop1=9, hop2=6, hop3=4, hop≥4 u rezu **0**. Miješani rezovi samo na habovima gdje k=3 ne radi.
- `final_max_hop` (otvoreni horizont): max **7**. 1791 otvori hop7, rez i dalje `0:3` i odličan (644→75). Pretraga smije ići daleko; pobjednički rez tad kad radi ostaje hop0.

**Ne tvrditi iz faze 2** da ALNS „pametno bira kriterij“. Po-heuristici σ₁/utezi **nisu** zapisani, samo zbroj `best_hits`. Kad hop0 greedy ima jednog pobjednika, ALNS ima isti σ na 11/26; na ostalima ili nadmaši ili (585, 841, 580, 1863…) promaši gotov `p_ij` rez. U novom kodu od dana 1: CSV stupci `best_hits_{heuristic}`, `best_hits_{hop}`, finalni utezi, `hop_mix` reza i `final_max_hop` odvojeno.

## 24) Implementacijski detalji koji su se isplatili

- Live-edge adjacency: `list[list[int]]` (samo glave), rez kao `dict[tail] → set(heads)`. Oznake posjećenosti: **Python lista** (numpy u unutarnjoj BFS petlji je sporiji zbog boxanja). ~2.3× vs stari tuple+numpy; isti RNG ⇒ bit-identični scenariji.
- Evaluacija na kopiji/maski, ne mutirati zamrznute scenarije (§6).
- Seedovi u jednom `config.py`: Louvain, SAA, MC, uzorak izvora, ALNS run. Promjena SAA/MC seeda invalidira sve σ.
- Pipeline faza-po-faza; crtanje samo na kraju iz CSV-a. `pipeline --all` ne dirati dok arhitektura nije smrznuta.
- BFS ubrzanje i MC=2000 se plaćaju kešom determinističkih baselinea.

## 25) Priča za restart (Bitcoin Alpha ostaje)

Dataset se ne mijenja. Niske p + veliki SCC čine čisti degree/betweenness slabim biračima brida — to je svojstvo podatka. Cilj nije „topologija bez p“, nego: **kad se p ugradi u topološku mjeru** (hop0 `p_ij`, min-rez s kapacitetima p, spektralni `u_i v_j` na P, okosnica), operator ima smislenu procjenu što prerezati. Sirova vs efektivna *struktura* (SCC/jezgra/Q na pragu p) ostaje figura; kaskada ≠ samo okosnica.

Fiksni k za usporedbu metoda treba **režim po out** (npr. 3 / 10 / 20); fiksni k=3 je karta malog budžeta, ne H4/H5.

## 26) Što NE ponavljati (dodatak)

- Ne bodovati Perrona u poretku SRC_ID/imena.
- Ne nagrađivati Δ=0 sa σ₃.
- Ne warm-startati Degree-om.
- Ne stavljati MinCut u istu tablicu s greedyjem.
- Ne zaključivati H4 s k=3 preko svih out pojaseva.
- Ne pisati da kaskada ide samo po p>0.05.
- Ne tvrditi adaptivni izbor operatora dok CSV nema σ₁ po heuristici.
- Ne citirati Spectral brojke iz runova prije poravnanja indeksa.

---

## 27) Što ovaj chat dodaje (revizija 2.9. — audit prije restarta)

Odjeljci 1–26 ostaju. Ovo su nalazi iz revizije cijelog SS-IMER koda: bugovi usporedbe, ispravljeni Granovetter, diskretni p, i zašto stari ALNS operatori nisu bili R&P. Stari `kod/` je obrisan; brojke ovdje su smjer, ne tablice za rad. ID-evi su i dalje igraph indeksi.

## 28) Bug usporedbe koji laže da ALNS pobjeđuje

`best_peer_mc = min([alns_mc, *baselines])` stavlja ALNS u pool s kojim se uspoređuje. Stupac **nikad** ne može pokazati da ALNS gubi: na 25/40 redova bio je jednak `alns_mc`, a ALNS je strogo najbolji na samo **11/40**.

Ispravna H4 slika (isti run, ručno bez tog stupca): fiksni hop0 **0.4775** · ALNS **0.5225** · MinCut **0.5170** · proročište **0.5357**. ALNS i dalje vodi, ali usko, i MinCut (koji vidi cijeli graf) nije daleko.

Novi kod: **jedan red po metodi** u `runs.csv`. „Najbolji fiksni“ i „proročište“ samo kao `groupby` nakon mjerenja. Nikad stupac koji u pool stavlja metodu koju ocjenjuješ.

## 29) Granovetter je *pozitivan* nalaz — §21 je artefakt particije

§21 mjeri inter- vs intra-community p na **jednom** Louvainu. To nije Granovetterova definicija. Njegov most: krajevi **bez zajedničkog susjeda** (`local_bridge`).

Na istom grafu, isti p (ponovljeno na čistom loadu 2.9.):

| definicija | n mostova | udio | mean p most / ostali | Cliff δ | p |
|---|---|---|---|---|---|
| lokalni most (Granovetter) | 7266 | 32.1 % | 0.086 / 0.116 | **−0.118** | **1.4·10⁻⁶⁰** |
| inter-community (Louvain, best-of-20) | 6801 | 30.0 % | 0.102 / 0.108 | +0.002 | 0.78 |

Stari „negativan nalaz“ (MW p=0.0012, near-null; ili neseedano p=0.161) bio je Louvain, ne Granovetter. Effect size lokalnog mosta je ~5× veći od one Louvain verzije u §21.

Posljedica za kod: operator `community` (inter-community) zamijeniti s **`bridge`** na `is_local_bridge`. Louvain ostaje deskriptivan (poglavlje 2.3: Q raste s pragom p, 0.49→0.62→0.73→0.78). Operatori ne ovise o `LOUVAIN_SEED`.

U `edges.csv` nositi **obe** zastavice. Test: Mann-Whitney + Cliff δ (p ima 10 razina, t-test ne valja; n=22650 pa je p-value uvijek „značajan“).

## 30) p ima deset razina — to mijenja i operatore i okosnicu

`p = sigmoid(rating − 5)`, rating ∈ {1…10}, pa p uzima **točno**:
`0.018, 0.047, 0.119, 0.269, 0.500, 0.731, 0.881, 0.953, 0.982, 0.993`.

- 60.75 % bridova na **p=0.018** (rating 1); 78.9 % ima p<0.05.
- `p > 0.05` i `p > 0.1` biraju **isti** 4777 bridova (oba = rating ≥ 3). Prag okosnice je rez na ratingu, ne kontinuirana ručica. Koristiti pragove koji razdvajaju razine, npr. 0 / 0.05 / 0.2 / 0.4 / 0.6 / 0.9.
- `probability` kao **baseline** ostaje (najjači fiksni, mean R=0.48, ortogonalno na stupanj — Spearman 0.03–0.08). Ali na 28/40 izvora rez na granici k ovisi o poretku, raspon do **39.6 pp**. To je osjetljivost, ne „random operator“.
- `probability` kao **ALNS operator** je krut, ne slučajan: destroy izbaci najslabiji po p, repair vrati isti brid. Zagarantiran no-op koji ipak troši stagnacijski budžet. Izmjereno: 2.68× mase pri k=3, degeneriran na 12.7 % izvora — nije random, ali ciklus ubija run.

Ne izbacivati p iz portfelja (H2/H4/H5). Mjeriti `neutral_moves` **po heuristici** i ablaciju `no_probability`. Ako mu je σ₁ hit-rate kao `random`, izlazi iz repaira, ostaje baseline.

## 31) Tie-break: dva posla, dva pravila, jedna funkcija

Baseline je **pravilo** → deterministički `(score ↓, u ↑, v ↑)`, jedan broj po (izvor, k, metoda). Jedini baseline koji se prosječuje preko seedova je **`Random`**.

Operator je **uzorkivač** → slučajno **među izjednačenima**. Bez toga `probability` i `bridge` imaju točno jedan rez.

Stari kod: greedy `nlargest` bez sekundarnog ključa, repair `sorted(score, u, v)`. Uz §30 to nije kozmetika. Ista `topk(edges, score, k, rng=None|rng)` za oboje.

`bridge` je binaran (0/1); `degree` se veže na 2/40 izvora; `betweenness`/`spectral` su kontinuirani.

## 32) Destroy i repair su dvije obitelji (R&P, ne „score unatrag“)

Stari kod je vukao **jednu** heuristiku za destroy i repair. To nije pojednostavljenje — to je §30. Røpke–Pisinger: dvije neovisne rolete.

- Destroy (što dirati): `random` / `worst` / `related` (Shaw). Worst po **pravom** SAA trošku puštanja brida (keš na rezu); related po dijeljenom repu / čvoru / hopu / p. Determinism: worst≈3, related≈6 (indeks `floor(y**p * n)`).
- Repair (što vratiti): domain scoreovi (`random`, `degree`, `betweenness`, `spectral`, `bridge`, `probability`). Tu se odlučuje H5.

Tri knjige utega: destroy, repair, hop-scope. Nagrada ista. Δ=0: prihvatiti, nagrada 0, brojati `neutral` (§18 ostaje).

Kalibracija iz §22 je **obesnažena** (nagrađivanje, tie-break, RNG, izlazak MinCuta, razdvojene obitelji). Defaulti 300/20/ρ=0.15/q∈[0.1k,0.4k] su razumna *početna* točka, ne zaključani. Ponoviti na disjunktnom skupu.

## 33) Horizont ne dokazuje adaptivno učenje dok se ne skuplja

Na karti k=3: 36/40 runova prošlo hop1; najbolji rez čisti hop0 u **31/40**. Pravilo `avg reward > 0` uz hop1 utež 8 širi se na jedan σ₂=9. Nema zatvaranja — jednom otvoren, sloj ostaje do kraja. Utezi po segmentu se nisu zapisivali.

Tvrdnja „ALNS uči kada ići dublje“ (H6) treba:
1. strože pravilo širenja (kandidati: σ₁ hit vanjskog hopa; prosjek > udio σ₁; staro `> 0`) — birati **mjerenjem**, ne pretpostavkom;
2. **zatvaranje** sloja koji N segmenata nije zaradio ništa;
3. `alns_trace.csv`: utezi scopeova i heuristika + `best_spread` + `active_max_hop` po segmentu;
4. protokol: `horizon0` vs `horizon1` vs adaptivno vs `open_all` — adaptivno mora pratiti bolji ekstrem **po izvoru**, ne u prosjeku.

§23 ostaje: pretraga smije otvoriti hop7, pobjednički rez tad kad radi ostaje hop0. To nije isto što i „uči“.

Baselinei **samo hop0**. hop0∪hop1 greedy bije hop0 na 1/40 za 0.002 R. `Degree` na širem poolu: 42/42 pickova izvan hop0, R 0.353→0.021. `Betweenness` ionako ostane lokalna (39/42 unutar hop0). Širenje je ALNS pitanje.

## 34) SAA šum se izvještava, ne „popravlja“

Podjela SAA na polovicu za pretragu i polovicu za odabir: regret 1.61→1.38 σ, ali pogodak MC-optimuma 11/17→9/17. Ne implementirati.

Na nabrojivim hop0 instancama (`C(out,k)≤220`): SAA-opt vs MC-opt, srednji regret **1.61 σ ≈ 2 % σ₀**. `EnumSAA` i `EnumMC` kao metode u `runs.csv`. Fitness ≠ izvještaj — §23/832 ostaje, ovo je veličina pogreške.

Jedan kasniji smoke (izvor 45, k=3, novi R&P loop, ~97 s): ALNS bolji na SAA od Degree, **lošiji na MC** (R 0.018 vs 0.023), horizont otišao na hop2. Može biti šum, može biti da je pretraga napustila hop0. Ne zaključivati; mjeriti oba σ i `hop_mix`.

`worst_removal` po točnom SAA košta do k evaluacija po prihvaćenom potezu. Ako run ostane ~90 s, grid nije 80 min. Imati jeftin proxy (`p_ij`) kao varijantu.

## 35) Ostali bugovi koje restart ne smije vratiti

- **B2:** `continue` na kratkom repairu preskače hlađenje, stagnaciju i granicu segmenta. Knjigovodstvo **uvijek**; `|cut|≠k` je assert, ne tihi skip.
- **B6:** usporedba σ na punom grafu vs okosnici mora ići iz **istih** uniform bacanja (`live_backbone ⊆ live_full` u svakom proboju). Dva nezavisna seeda (42 s 22650 vs 43 s 4777) miješaju prag sa šumom. To je jedini način da „slabi bridovi nose kaskadu“ (§21) ostane čist.
- **B7:** jedan `sample.csv`, jedan `SOURCE_SAMPLE_SEED`. Audit je našao tri uzorka u opticaju (stratificiranih 40, nestratificiranih 40, 12). Kalibracija **disjunktna** od mjerenja. ID-evi iz §22 (727, 1822, 45, …) su iz bačenog uzorka — princip ostaje, brojevi ne.
- **D4:** brojač operatora tek **nakon** izvedenog poteza, ne pri `select`.
- **D5:** keš `σ₀` po imenu skupa (`saa`/`mc`), ne po `id(lista)` (adresa se reciklira).
- **R13:** `random.Random(seed)` po runu, ne globalni `random`. Mijenja trajektorije; prihvatiti.
- Jedan pojam, jedno mjesto. Louvain na tri poziva dao je tri particije i Granovetterov p je skakao preko 0.05. Indeks čvora = id = indeks CSR-a **po konstrukciji** (ne `TupleList` + permutacija — §18 ostaje kao klasa buga).

## 36) MinCut izlazi; γ se mora izmjeriti

§19 kaže „mjeriti MinCut, izvještavati odvojeno“. Kasnija odluka: **izlazi u cijelosti**. Za 71 % čvorova min-rez s kapacitetima p **jest** Σp_out (preimenovana izlazna masa). Rez slabiji od ALNS-a (0.517 vs 0.523) iako vidi cijeli graf. `sum_p_out` nosi isti signal; jezgra-32 nije ciljni skup.

Za „mreža bez skale“ treba Clauset–Shalizi–Newman MLE, ne samo κ. Na raw loadu: **γ_out=2.81, γ_in=2.84**, x_min_out=41, KS≈0.058 vs 0.23 na ER (γ≈4.06). Bez γ/KS poglavlje 2.1 nema dokaz.

Louvain: jedno pokretanje daje 21–31 zajednicu (Q skaka). Izvještavati **najbolji od ≥20 restarta** + raspon. Jedan seedani run (§12: 28/0.493; §19: 30/0.47) nije brojka. Best-of-20 na istom loadu: **31, Q=0.491**.

Sampler check u `graphs.csv`: mean(realizirani p − deklarirani p) ~10⁻⁴. Ako driftne, svaki σ je kriv.

## 37) Jedinica, log i što NE tvrditi dok nema CSV-a

R = 1 − σ_cut/σ₀ (razlomak). σ₀ ide 39–647; apsolutni pad nije usporediv. Medijan preko izvora (iskošeno).

Od dana 1 u dijagnostici, uz §23:
- `neutral_moves` po heuristici (krutost, §30);
- `stop_reason` ∈ {`max_iter`, `stagnation`, `isolated`} — „konvergirao“ ≠ „ciklus potrošio stagnaciju“;
- `iters_done` (rani stop ≠ `max_iter`);
- svi razriješeni ALNS parametri u istom redu (varijanta = override, ne kodni put).

**Ne tvrditi** iz k=3 da ALNS nalazi nelokalna grla — to čeka veći k po out-režimu (§25). **Ne tvrditi** adaptivnu dubinu dok nema zatvaranja + trace (§33). **Ne tvrditi** negativan Granovetter — vrijedi §29, ne §21.

## 38) Što NE ponavljati (dodatak, samo revizija)

- Ne stavljati ALNS u `best_peer`.
- Ne spajati destroy i repair u jedan draw.
- Ne tretirati `p>0.05` i `p>0.1` kao dva praga.
- Ne raditi Granovetter na Louvain zastavici i zvati to Granovetterom.
- Ne držati MinCut ni kao „poseban“ stupac.
- Ne nasljeđivati kalibraciju iz §22 u novi R&P loop.
- Ne širiti horizont bez mehanizma koji ga može i skupiti.
- Ne „popravljati“ SAA splitom skupa; izvijestiti `EnumMC`.
- Ne imati tri uzorka izvora.
- Ne uspoređivati okosnicu i puni graf na nezavisnim scenarijima.

