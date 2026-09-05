"""Uvod + 1. Topologija i dinamika kompleksnih mreza.

Sources read for this chapter, in the order they are used: Erdos & Renyi (1960) for the
random-graph baseline; Watts & Strogatz (1998) for the small-world construction and the
L / C measures; Albert & Barabasi (2002) for the scale-free review and the preferential
attachment mechanism; Albert, Jeong & Barabasi (2000) for error and attack tolerance;
Kempe, Kleinberg & Tardos (2003) for the Independent Cascade model and the live-edge
equivalence (their Claim 2.3); Kimura et al. (2008) for the ICM rules restated for a
blocking problem; Wang et al. (2003) and Castellano & Pastor-Satorras (2010) for the two
epidemic thresholds.
"""

import omml as M
from omml import delim, frac, i, sub, sup, up, v


def mean_k():
    """The mean degree, written the way the cited literature writes it."""
    return delim(v("k"), left="⟨", right="⟩")


def mean_k2():
    return delim(sup(v("k"), up("2")), left="⟨", right="⟩")


def ifunc(name, argument):
    """A function whose name is itself a symbol - P(k), R(u, X) - so the name stays in
    math italic, unlike exp or ln which are set upright."""
    return [v(name), delim(argument)]


def write(t, figures):
    _uvod(t)
    _chapter(t, figures)


# ---------------------------------------------------------------- Uvod ----

def _uvod(t):
    t.h1("Uvod", numbered=False)

    t.p("Kompleksne mreže prikladan su model za velik broj stvarnih sustava u kojima se "
        "odnosi među elementima opisuju bridovima koji povezuju čvorove. Za razliku od "
        "pravilnih struktura koje se proučavaju u klasičnoj teoriji grafova, topologija "
        "kompleksnih mreža ishod je stohastičkih procesa rasta i povezivanja, pa se ni "
        "njihova struktura ni dinamika procesa koji se na njima odvijaju ne mogu opisati "
        "jednostavnim pravilima {albert2002}. Razumijevanje difuzije na takvim strukturama važno je "
        "jer omogućuje predviđanje i, što je za ovaj rad ključno, upravljanje širenjem "
        "informacije ili zaraze.")

    t.p("Optimizacija na mrežama zbog toga ima široku primjenu. U istraživačkim se "
        "radovima koristi za analizu društvenih i političkih kaskada, primjerice za "
        "kontrolu manipulacije izbornim ishodima {castiglioni2021}, za unapređenje sustava preporuka na "
        "društvenim mrežama {coro2021}, pa i u ekologiji, kroz metapopulacijsko modeliranje za "
        "strateško povezivanje ugroženih staništa {sheldon2010}.")

    t.p("U ovom se radu razmatra minimizacija utjecaja ciljanim uklanjanjem bridova. "
        "{~castiglioni2021} taj problem definiraju pod nazivom ",
        i("Influence-Minimization-by-Edge-Removal"), " (IMER): za zadani graf, skup "
        "početnih čvorova i proračun ", v("B"), ", traži se skup od najviše ", v("B"),
        " bridova čije uklanjanje najviše smanjuje broj čvorova do kojih informacija "
        "dopre. Ovdje se razmatra uža varijanta toga problema, u kojoj je početni čvor "
        "jedan jedini i fiksiran, a proračun se troši u cijelosti. Radi kratkoće se u "
        "nastavku koristi oznaka SS-IMER (", i("Single-Source IMER"), "). Prefiks "
        "SS-, kao i sama oznaka, uvedeni su u ovom radu prema uobičajenoj konvenciji "
        "imenovanja inačica optimizacijskih problema i nisu ustaljen naziv u literaturi.")

    t.p("Rani pristupi kontroli širenja oslanjali su se na uklanjanje čvorova "
        "{albert2000}, no u stvarnim je sustavima brisanje korisničkih računa često "
        "pravno, poslovno ili etički neizvedivo. Uklanjanje bridova blaža je intervencija "
        "koja mijenja topologiju bez uklanjanja samih aktera {tong2012}, pa je zato i "
        "praktično privlačnija. Najbliži je algoritamski predak ovoga rada problem "
        "minimizacije kontaminacije {kimura2008}, u kojem se pod istim modelom širenja "
        "blokiraju bridovi, ali se doseg usrednjava preko svih čvorova kao mogućih izvora, "
        "a ne promatra iz jednoga zadanog.")

    t.p("Za modeliranje dinamike širenja odabran je nezavisni kaskadni model (ICM), jedan "
        "od najčešće proučavanih modela difuzije {kempe2003}. Rješenje se eksperimentalno "
        "vrednuje na usmjerenoj mreži povjerenja Bitcoin Alpha {kumar2016,kumar2018}. Primjena je "
        "izravna: uklanjanjem ograničenog broja veza u okruženju sumnjivog korisnika "
        "smanjuje se njegov potencijalni doseg, a da pritom njegov račun ostaje aktivan.")

    t.p("Točna evaluacija dosega pod ICM-om računski je vrlo zahtjevna, a granični "
        "doprinos pojedinog brida u pravilu nije submodularan zbog topološke redundantnosti "
        "i alternativnih staza. Pohlepne metode koje bridove biraju jedan po jedan zato ne "
        "hvataju sinergiju više istodobnih uklanjanja. Kako bi se ta prepreka premostila, "
        "u radu se implementira i prilagođava metaheuristika ", i("Adaptive Large Neighborhood Search"), " (ALNS) {ropke2006}, koja u svakoj iteraciji razara i ponovno "
        "gradi cijelo rješenje umjesto da ga proširuje po jedan element.")

    t.p("Adaptivno učenje ALNS-a ispituje se na dvije razine. Na prvoj razini algoritam "
        "raspolaže s više topoloških kriterija za odabir brida i dodjeljivanjem bodova uči "
        "koji je kriterij bolji procjenitelj u kojem slučaju. Na drugoj razini procjenjuje "
        "se koliko daleko od izvora leže bridovi koje se isplati ukloniti. Intuitivno je "
        "da treba presjeći što više bridova koji izravno izlaze iz izvora. Međutim, ako iz "
        "izvora vodi više neovisnih bridova prema istoj dobro povezanoj komponenti mreže, "
        "uklanjanje samo nekoliko njih neće bitno smanjiti doseg jer se kaskada i dalje "
        "širi preostalim putovima. Ako se ti paralelni putovi spajaju u zajedničko usko "
        "grlo tek nekoliko koraka dalje, isplativije je ukloniti taj dijeljeni brid nego "
        "presijecati svaki od izlaznih bridova posebno.")

    t.p("Rad je organiziran kako slijedi. Prvo se poglavlje bavi teorijskim osnovama "
        "topologije i dinamike kompleksnih mreža. Drugo poglavlje analizira mrežu Bitcoin "
        "Alpha. Treće poglavlje formalno definira problem SS-IMER i način procjene dosega, "
        "četvrto opisuje kriterije za odabir bridova, a peto metode rješavanja. Šesto "
        "poglavlje opisuje implementaciju i eksperimentalni postav, sedmo donosi rezultate "
        "i raspravu, a osmo mogućnosti poboljšanja.")


# ----------------------------------------------------------- Poglavlje 1 ----

def _chapter(t, figures):
    t.h1("Topologija i dinamika kompleksnih mreža")

    t.p("Poglavlje uvodi pojmove potrebne za interpretaciju topologije mreže Bitcoin Alpha "
        "i dinamike nezavisnoga kaskadnog modela. Najprije se opisuje put od slučajnih "
        "grafova do modela koji reproduciraju svojstva stvarnih mreža, zatim model širenja "
        "koji se u radu koristi, i na kraju uvjet pod kojim se kaskada uopće može "
        "makroskopski proširiti.")

    _random_to_complex(t, figures)
    _small_world(t)
    _scale_free(t)
    _icm(t, figures)
    _threshold(t)


def _random_to_complex(t, figures):
    t.h2("Od slučajnih do kompleksnih mreža")

    t.p("Sustavno proučavanje slučajnih grafova započinju {~erdos1960}. "
        "U njihovu se modelu mreža s ", v("N"), " čvorova gradi tako da se svaki od "
        "mogućih parova čvorova poveže neovisno, s istom vjerojatnošću ", v("p"), ". "
        "Posljedica takve konstrukcije je da broj veza pojedinog čvora, njegov stupanj, "
        "slijedi binomnu raspodjelu koja za velik ", v("N"), " prelazi u Poissonovu:")

    t.eq(ifunc("P", v("k")), up(" ≈ "),
         frac([sup(v("e"), [up("−"), mean_k()]), sup(mean_k(), v("k"))], up("k!")),
         label="poisson")

    t.p("Ovdje je ", mean_k(), " prosječni stupanj mreže. Ključno svojstvo "
        "takve raspodjele je da je homogena: gotovo svi čvorovi imaju stupanj blizu "
        "prosjeka, a velika odstupanja statistički su zanemariva {albert2002}. Slučajni graf zato "
        "nema izdvojene, iznimno povezane čvorove.")

    t.p("Analiza stvarnih sustava, poput interneta, društvenih i bioloških mreža, pokazala "
        "je da se oni ne mogu dobro opisati takvim homogenim modelom. Stvarne mreže "
        "nastaju decentralizirano i dinamički, što uzrokuje netrivijalna topološka "
        "svojstva, prije svega visoku razinu grupiranja i izrazitu asimetriju stupnjeva, "
        "koja ih razlikuju od slučajnih grafova {albert2002}. Dva modela koja su ta svojstva prva "
        "objasnila opisana su u nastavku, a ", t.figref("er_ws_ba"),
        " prikazuje razliku u strukturi.")

    t.figure(figures / "fig1_1_er_ws_ba.png",
             "Usporedba slučajnog (ER), malosvjetskog (WS) i bezskalnog (BA) grafa.",
             label="er_ws_ba")


def _small_world(t):
    t.h3("Mreže malog svijeta")

    t.p("{~watts1998} primjećuju da stvarne mreže istodobno imaju dva "
        "naizgled nespojiva svojstva. Prvo je visok koeficijent grupiranja ", v("C"),
        ", mjera sklonosti susjeda nekog čvora da i sami budu međusobno povezani. Drugo je "
        "kratka karakteristična duljina puta ", v("L"), ", odnosno prosječna udaljenost "
        "između dva čvora u mreži. Pravilna rešetka ima visok ", v("C"), " ali i velik ",
        v("L"), "; slučajni graf ima malen ", v("L"), " ali i zanemariv ", v("C"), ".")

    t.p("Kako bi se ta dva režima povezala, autori polaze od prstenaste rešetke u kojoj je "
        "svaki od ", v("N"), " čvorova povezan sa svojih ", v("k"), " najbližih susjeda, "
        "te svaki brid s vjerojatnošću ", v("p"), " premoštavaju na nasumično odabran "
        "čvor. Parametar ", v("p"), " tako ugađa mrežu između pravilnosti i potpune "
        "slučajnosti. Za slučajni graf vrijedi {watts1998}:")

    t.eq(sub(v("L"), up("sluč")), up(" ≈ "), frac([up("ln "), v("N")], [up("ln "), v("k")]),
         up(",       "), sub(v("C"), up("sluč")), up(" ≈ "), frac(v("k"), v("N")),
         label="ws_random")

    t.p("Bitan je nalaz da postoji širok raspon vrijednosti ", v("p"), " u kojem je ",
        v("L"), " gotovo jednako malen kao u slučajnom grafu, dok ", v("C"), " ostaje "
        "znatno veći od slučajnoga {watts1998}. Razlog je nelinearan učinak malog broja "
        "premoštenih bridova: takav brid, koji autori nazivaju prečacem, ne skraćuje samo "
        "udaljenost između dvaju čvorova koje spaja, nego i između njihovih okolina. "
        "Uklanjanje jednoga brida iz gusto povezane okoline, s druge strane, na ", v("C"),
        " djeluje najviše linearno. Autori naglašavaju da je zbog toga prijelaz u mali "
        "svijet na lokalnoj razini gotovo neprimjetan.")

    t.p("Watts i Strogatz izričito povezuju tu strukturu sa širenjem zaraze i pokazuju da "
        "se bolest u malosvjetskim mrežama širi lakše nego u pravilnim rešetkama {watts1998}. To "
        "je izravno relevantno za ovaj rad: prečaci su bridovi čije uklanjanje ima "
        "nerazmjeran učinak na doseg. Ograničenje je modela što raspodjela stupnjeva "
        "ostaje zvonolika, pa model ne proizvodi mrežna čvorišta kakva se opažaju u "
        "stvarnim sustavima {albert2002}.")


def _scale_free(t):
    t.h3("Mreže bez skale")

    t.p("Drugi se proboj odnosi na nejednakost u raspodjeli veza. {~albert2002} pokazuju "
        "da mnoge stvarne mreže imaju raspodjelu stupnjeva koja slijedi zakon potencije:")

    t.eq(ifunc("P", v("k")), up(" ~ "), sup(v("k"), [up("−"), v("γ")]), label="powerlaw")

    t.p("Eksponent ", v("γ"), " za stvarne se mreže najčešće nalazi u rasponu između 2 i 3 "
        "{albert2002}. Takva raspodjela nema dobro definiranu karakterističnu vrijednost stupnja "
        "koja bi služila kao skala sustava, pa se mreže s tim svojstvom nazivaju mrežama "
        "bez skale {antulov2008}. Velika većina čvorova ima vrlo malo veza, dok malen broj čvorova, "
        "koji se nazivaju čvorištima ili habovima, ima izrazito velik stupanj {antulov2008}.")

    t.p("Barabási-Albertov model nastanak takve strukture objašnjava dvama mehanizmima "
        "{albert2002}. Prvi je rast: mreža se razvija dodavanjem novih čvorova, za razliku od "
        "statičnih ER i WS modela. Drugi je preferencijalno pridruživanje, po kojem se "
        "novi čvorovi radije povezuju s čvorovima koji već imaju visok stupanj, čime "
        "povezaniji čvorovi postaju sve povezaniji.")

    t.p("Asimetrija stupnjeva ima izravne posljedice na otpornost sustava. {~albert2000} "
        "pokazuju da su mreže bez skale iznimno otporne na slučajne kvarove, jer "
        "nasumičan gubitak čvora gotovo sigurno pogađa neki od brojnih slabo povezanih "
        "čvorova, ali su istodobno vrlo osjetljive na ciljane napade: uklanjanje malog "
        "broja čvorišta dovodi do raspada gigantske komponente. Upravo je ta "
        "asimetrija, u kojoj nekoliko strukturno ključnih elemenata nosi nerazmjeran dio "
        "funkcije mreže, temeljna pretpostavka ovoga rada, uz razliku što se ovdje ciljano "
        "uklanjaju bridovi, a ne čvorovi.")


def _icm(t, figures):
    t.h2("Nezavisni kaskadni model (ICM)", label="icm")

    t.p("Za modeliranje širenja u radu se koristi nezavisni kaskadni model, koji su "
        "formalizirali {~kempe2003}. U tom se modelu svaki čvor u svakom "
        "trenutku nalazi u jednom od dva stanja, aktivnom ili neaktivnom, a prijelaz je "
        "moguć samo iz neaktivnog u aktivno stanje. Proces se odvija u diskretnim koracima "
        "prema sljedećim pravilima {kempe2003,kimura2008}:")

    t.bullets([
        ["U trenutku ", v("t"), " = 0 aktivira se početni skup čvorova, dok su svi ostali "
         "čvorovi neaktivni."],
        ["Kada čvor ", v("u"), " prvi put postane aktivan u koraku ", v("t"), ", dobiva "
         "jednu jedinu priliku aktivirati svakoga svog trenutno neaktivnog susjeda ",
         v("w"), ". Pokušaj uspijeva s vjerojatnošću ", sub(v("p"), [v("u"), v("w")]),
         ", neovisno o dotadašnjem tijeku procesa."],
        ["Ako pokušaj uspije, čvor ", v("w"), " postaje aktivan u koraku ", v("t"),
         " + 1. Bez obzira na ishod, čvor ", v("u"), " ne može ponoviti pokušaj prema ",
         v("w"), " u kasnijim koracima."],
        "Proces se zaustavlja kada u nekom koraku nema novih aktivacija.",
    ], numbered=True)

    t.p("Model je stohastičan, pa je doseg kaskade slučajna veličina. {~kempe2003} "
        "pokazuju da se proces može promatrati na ekvivalentan, ali znatno pogodniji "
        "način. Budući da ishod pokušaja aktivacije preko brida ovisi samo o "
        "vjerojatnosti tog brida, nije važno baca li se novčić u trenutku kada čvor ",
        v("u"), " postane aktivan ili već na samom početku procesa. Ako se svi novčići "
        "bace unaprijed, svaki se brid unaprijed proglašava propusnim ili blokiranim, čime "
        "nastaje statični podgraf propusnih bridova.")

    t.p("Za tako fiksiran ishod bacanja, označen s ", v("X"), ", vrijedi njihova tvrdnja: "
        "čvor završava aktivan ako i samo ako postoji put od nekog početnog čvora do njega "
        "koji se u cijelosti sastoji od propusnih bridova {kempe2003}. Ako se s ",
        ifunc("R", [v("u"), up(", "), v("X")]), " označi skup čvorova dohvatljivih iz ",
        v("u"), " takvim putovima, doseg kaskade iz početnog skupa ", v("A"),
        " postaje puka veličina skupa:")

    t.eq(sub(v("σ"), v("X")), delim(v("A")), up(" = "),
         delim(M.nary("∪", [v("u"), up(" ∈ "), v("A")], None,
                      [ifunc("R", [v("u"), up(", "), v("X")])]), left="|", right="|"),
         label="liveedge_eq")

    t.p("Time se, za zadani ishod bacanja, stohastički proces svodi na determinističko "
        "pitanje dohvatljivosti u grafu, koje se rješava pretraživanjem u širinu. Ta je "
        "ekvivalencija temelj cijeloga postupka procjene korištenog u ovom radu i "
        "detaljno se razrađuje u odjeljku ", t.sec("procjena"), ". Podgraf propusnih bridova naziva se ",
        i("live-edge"), " realizacijom, a ", t.figref("liveedge_fig"), " prikazuje jedan takav "
        "primjer.")

    t.figure(figures / "fig1_2_live_edge.png",
             "Od stohastičke kaskade do dohvatljivosti: izvorni graf s vjerojatnostima "
             "prijenosa (lijevo), jedna live-edge realizacija nakon bacanja novčića za "
             "svaki brid (sredina) i skup čvorova dohvatljiv iz izvora u toj realizaciji "
             "(desno).",
             label="liveedge_fig")


def _threshold(t):
    t.h2("Epidemiološki prag", label="prag")

    t.p("Ključno pitanje pri analizi širenja na mreži jest hoće li proces pokrenut iz "
        "izvora brzo odumrijeti ili će zahvatiti makroskopski udio mreže. Granica koja "
        "razdvaja ta dva režima naziva se epidemiološkim pragom i označava s ",
        sub(v("λ"), up("c")), ".")

    t.p("U klasičnoj teoriji srednjeg polja, koja pretpostavlja da se veze u mreži stalno "
        "preslaguju, prag ovisi samo o prva dva momenta raspodjele stupnjeva:")

    t.eq(sub(v("λ"), up("c")), up(" = "),
         frac(mean_k(), mean_k2()),
         label="hmf")

    t.p("Stvarni sustavi poput mreže Bitcoin Alpha imaju, međutim, fiksnu topologiju. "
        "{~castellano2010} pokazuju da za takve mreže teorija srednjeg polja zakazuje jer "
        "zanemaruje njihovu geometrijsku strukturu. Već {~wang2003} pokazuju da je prag na "
        "proizvoljnom grafu određen najvećom vlastitom vrijednošću ", sub(v("λ"), up("max")), " matrice susjedstva {wang2003,castellano2010}:")

    t.eq(sub(v("λ"), up("c")), up(" = "), frac(up("1"), sub(v("λ"), up("max"))),
         label="spectral")

    t.p("Ta spoznaja ima izravne posljedice za mreže bez skale. Prema teoriji srednjeg "
        "polja drugi moment stupnja za ", v("γ"), " ≤ 3 divergira, pa bi prag težio nuli i "
        "takve bi mreže bilo nemoguće zaštititi. Spektralna teorija na konačnim mrežama "
        "pokazuje suprotno: prag ostaje strogo pozitivan i određen strukturom grafa, pri "
        "čemu je za ", v("γ"), " > 5/2 vezan uz stupanj najpovezanijeg čvorišta {castellano2010}.")

    t.p("{~tong2012} na temelju te veze predlažu ciljanu izmjenu bridova radi smanjenja ", sub(v("λ"), up("max")), ". U ovom radu, međutim, cilj "
        "optimizacije nije ", sub(v("λ"), up("max")), ", nego očekivani doseg iz jednog "
        "izvora. Spektralna se veličina koristi isključivo kao jedan od kriterija za "
        "rangiranje bridova, što se obrazlaže u odjeljku ", t.sec("spektralni"), ".")
