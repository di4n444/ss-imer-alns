"""Uvod + 1. Teorijska podloga.

The Uvod is the author's own text, kept verbatim. Only the citations are rewritten as keys
so they render from the bibliography instead of being typed by hand.

Chapter 1 carries the minimum theory the rest of the thesis actually uses, and nothing
else: two structural properties of real networks (short paths with clustering, and hubs),
the Independent Cascade model with its live-edge reading, and the epidemic threshold. Each
is introduced because a later chapter needs it, and the text says which one.

Sources: Erdos & Renyi (1960) for the random-graph baseline; Watts & Strogatz (1998) for
small-world; Albert & Barabasi (2002) for the scale-free review and preferential
attachment; Kempe, Kleinberg & Tardos (2003) for ICM and the live-edge equivalence (their
Claim 2.3); Castellano & Pastor-Satorras (2010) for the spectral threshold.
"""

from omml import delim, frac, i, sub, sup, up, v


def mean_k():
    """The mean degree, written the way the cited literature writes it."""
    return delim(v("k"), left="⟨", right="⟩")


def ifunc(name, argument):
    """A function whose name is itself a symbol, P(k) or R(s, X), so the name stays in
    math italic rather than being set upright like ln or exp."""
    return [v(name), delim(argument)]


def write(t, figures):
    _uvod(t)
    _chapter(t, figures)


# ------------------------------------------------------------------ Uvod ----

def _uvod(t):
    t.h1("Uvod", numbered=False)

    t.p("Kompleksne mreže prikladan su model za velik broj stvarnih sustava u kojima se "
        "odnosi među elementima opisuju bridovima koji povezuju čvorove. Za razliku od "
        "klasičnih grafova, topologija kompleksnih mreža ishod je stohastičkih procesa "
        "rasta i povezivanja. Zato se njihova struktura i dinamika procesa na njima ne "
        "mogu opisati jednostavnim pravilima {albert2002}. Razumijevanje difuzije na "
        "takvim strukturama važno je jer omogućuje predviđanje i upravljanje širenjem "
        "informacije ili zaraze.")

    t.p("Optimizacija na mrežama posjeduje bogatu domensku primjenu koja se proteže daleko "
        "izvan očekivanih okvira računalne sigurnosti i epidemiologije. Na primjer, u "
        "istraživačkim radovima služi za analizu društvenih i političkih kaskada, poput "
        "kontrole manipulacije izbornim ishodima {castiglioni2021}, unapređenje sustava za "
        "preporuke na društvenim mrežama {coro2021}, pa čak i u ekologiji kroz "
        "metapopulacijsko modeliranje za strateško povezivanje ugroženih prirodnih "
        "staništa {sheldon2010}.")

    t.p("U ovom se radu optimizacija protoka informacije razmatra kroz problem "
        "minimizacije utjecaja ciljanim uklanjanjem bridova. Iako pojam protoka asocira na "
        "brzinu širenja kroz vrijeme, u ovom se modelu on promatra isključivo kroz konačni "
        "doseg kaskade: protok je to veći što informacija (ili zaraza) dosegne više "
        "čvorova. Optimizacija se stoga svodi na pronalaženje bridova čijim se uklanjanjem "
        "taj doseg maksimalno smanjuje. Zbog toga se u nastavku rada koristi preciznija "
        "terminologija iz područja minimizacije utjecaja (engl. ",
        i("Influence Minimization"), "), pri čemu utjecaj označava upravo doseg kaskade.")

    t.p("{~castiglioni2021} taj problem definiraju pod nazivom ",
        i("Influence Minimization by Edge Removal"), " (IMER), pri čemu dinamiku širenja "
        "utjecaja modeliraju nezavisnim kaskadnim modelom (ICM). Koristeći isti model "
        "širenja, ovdje se razmatra uža varijanta toga problema u kojoj je izvor kaskade "
        "jedan i fiksiran, a ograničenje broja bridova za uklanjanje troši se u cijelosti. "
        "Po uzoru na praksu za probleme s jednim izvorom, za ovu se varijantu uvodi oznaka "
        "SS-IMER (", i("Single-Source IMER"), ").")

    t.p("Optimizacija se eksperimentalno testira na usmjerenoj mreži povjerenja Bitcoin "
        "Alpha {kumar2016,kumar2018} za koju rješavanje problema ima praktičnu "
        "interpretaciju. Primjenom predloženog rješenja, mrežni administratori mogu "
        "djelovati preventivno: uklanjanjem određenog broja bridova na mreži u okruženju "
        "sumnjivog korisnika, značajno se smanjuje njegov potencijalni doseg i mogućnost "
        "prijevare, bez potrebe za brisanjem samog profila, što je često pravno, poslovno "
        "ili etički neizvedivo.")

    t.p("Točna evaluacija dosega pod ICM-om računski je vrlo zahtjevna, a granični "
        "doprinos pojedinog brida u pravilu nije submodularan zbog topološke redundantnosti "
        "i alternativnih staza. Pohlepne metode koje bridove biraju jedan po jedan ne bi "
        "uhvatile sinergiju više istodobnih uklanjanja. Upravo zato se u radu implementira "
        "i prilagođava metaheuristika ", i("Adaptive Large Neighborhood Search"),
        " (ALNS), koja u svakoj iteraciji razara i ponovno gradi cijelo rješenje umjesto "
        "da ga proširuje po jedan element {ropke2006}.")

    t.p("Adaptivno učenje ALNS-a ispituje se na dvije razine. Na prvoj razini algoritam "
        "raspolaže s više topoloških kriterija za odabir brida i dodjeljivanjem bodova uči "
        "koji je kriterij bolji procjenitelj u kojem slučaju. Na drugoj razini procjenjuje "
        "se koliko daleko od izvora leže bridovi koje se isplati ukloniti. Postavlja se "
        "pitanje jesu li to samo bridovi koji direktno izlaze iz izvora ili je ponekad "
        "ključan neki udaljeniji brid. Upitno je postoji li takav slučaj dovoljno često da "
        "ga se isplati tražiti i može li ga ALNS prepoznati.")

    t.p("Struktura rada prati logički slijed rješavanja ovog problema. Najprije se "
        "postavlja teorijski okvir na temelju kojeg provodimo analizu stvarne mreže na "
        "kojoj rješavamo matematički formaliziran problem. Središnji dio rada opisuje "
        "kriterije za prepoznavanje ključnih bridova i metode pretraživanja prostora "
        "rješenja koje ih koriste. Konačno, implementacijom i provedbom eksperimenta, rad "
        "kritički vrednuje uspješnost predloženih pristupa i nudi smjernice za njihovo "
        "daljnje usavršavanje.")


# ----------------------------------------------------------- 1. Teorija ----

def _chapter(t, figures):
    t.h1("Teorijska podloga")
    t.p("Prije nego što se zapitamo kako zaustaviti širenje u mreži, treba reći kakve su "
        "te mreže i po kojim se pravilima širenje odvija. Poglavlje uvodi samo ono što se "
        "dalje u radu koristi.")

    _networks(t, figures)
    _icm(t, figures)
    _threshold(t)


def _networks(t, figures):
    t.h2("Od slučajnih do kompleksnih mreža", label="topologija")

    t.p("Najjednostavniji model mreže je slučajni graf {erdos1960}: uzmemo ", v("N"),
        " čvorova i svaki par povežemo neovisno, s istom vjerojatnošću. Tada gotovo svi "
        "čvorovi imaju sličan broj veza. Jedno svojstvo takav graf ipak dijeli sa "
        "stvarnima, a to je da je put između dva nasumično odabrana čvora kratak i raste "
        "tek logaritamski s veličinom mreže, gdje je ", mean_k(),
        " prosječan stupanj čvora:")

    t.eq(sub(v("L"), up("sluč")), up(" ≈ "),
         frac([up("ln "), v("N")], [up("ln "), mean_k()]), label="smallworld")

    t.p("Od slučajnoga se grafa stvarne mreže razlikuju u dvjema stvarima. Prva je "
        "grupiranje. U društvenoj mreži prijatelji jedne osobe najčešće su i međusobno "
        "prijatelji, dok u slučajnom grafu takvih trokuta gotovo nema. {~watts1998} "
        "pokazali su da se kratki putovi i grupiranje mogu imati istodobno: dovoljno je "
        "krenuti od pravilne, gusto grupirane strukture i mali broj bridova preusmjeriti "
        "nasumično. Nekoliko takvih prečaca sruši prosječnu udaljenost, a grupiranje "
        "ostane visoko. Takvu mrežu zovemo mrežom malog svijeta.")

    t.p("Druga je razlika postojanje čvorišta. U slučajnom grafu nitko nema mnogo više "
        "veza od prosjeka, a u stvarnim mrežama postoji malen broj čvorova s izrazito "
        "mnogo veza. Razlog je u načinu na koji mreža raste: novi se čvorovi radije vežu "
        "uz one koji već imaju mnogo veza {albert2002}. Raspodjela stupnjeva tada slijedi "
        "zakon potencije:")

    t.eq(ifunc("P", v("k")), up(" ~ "), sup(v("k"), [up("−"), v("γ")]), label="powerlaw")

    t.p("Takve mreže zovemo mrežama bez skale. Eksponent ", v("γ"), " najčešće se nalazi "
        "između 2 i 3 {albert2002}, pa čvorovi s vrlo velikim brojem veza nisu iznimka "
        "nego očekivan dio slike.")

    t.p(t.figref("modeli"), " prikazuje sva tri modela na jednakom broju čvorova i "
        "bridova. Slučajni je graf ravnomjeran, malosvjetski je prsten s nekoliko "
        "prečaca, a u bezskalnom nekoliko čvorova nosi neusporedivo više veza od ostalih.")

    t.figure(figures / "fig1_1_er_ws_ba.png",
             "Tri modela mreže na jednakom broju čvorova i bridova. Slučajni graf (lijevo) "
             "raspodjeljuje veze ravnomjerno, malosvjetski (sredina) zadržava grupiranje uz "
             "nekoliko prečaca, a bezskalni (desno) ima izražena čvorišta.",
             label="modeli", width_cm=15.0)

    t.p("Za nas je važna posljedica. U mreži s kratkim putovima i čvorištima kaskada brzo "
        "dosegne velik dio mreže, a između dva čvora u pravilu postoji više različitih "
        "putova. Uklanjanje nekoliko bridova zato rijetko išta razdvoji, i upravo je ta "
        "zalihost razlog zbog kojeg je naš problem težak.")


def _icm(t, figures):
    t.h2("Nezavisni kaskadni model", label="icm")

    t.p("Širenje modeliramo nezavisnim kaskadnim modelom {kempe2003}. Svakom je bridu ",
        delim(v("u"), up(", "), v("v")), " pridružena vjerojatnost prijenosa ",
        sub(v("p"), [v("u"), v("v")]), ", a kaskada počinje od izvora ", v("s"),
        ". Kada se čvor aktivira, dobiva jednu jedinu priliku da aktivira svakog svog još "
        "neaktivnog susjeda. Svaki je takav pokušaj jedno bacanje novčića: brid s "
        "vjerojatnošću ", sub(v("p"), [v("u"), v("v")]), " propusti kaskadu dalje, a inače "
        "je zaustavi. Uspio ili ne, pokušaj se ne ponavlja. Postupak staje kada u nekom "
        "koraku nijedan novi čvor nije aktiviran.")

    t.p("{~kempe2003} pokazali su da se isti proces može gledati i drukčije, i taj je "
        "pogled temelj cijeloga rada. Ishod bacanja na nekom bridu ne ovisi o tome kada "
        "smo ga bacili, pa umjesto da novčiće bacamo dok se kaskada širi, možemo ih baciti "
        "sve unaprijed: svaki brid neovisno zadržimo s njegovom vjerojatnošću, a inače ga "
        "obrišemo. Ono što ostane fiksan je podgraf koji zovemo realizacijom. Skup "
        "aktiviranih čvorova tada je točno skup čvorova dohvatljivih iz izvora u toj "
        "realizaciji.")

    t.p(t.figref("liveedge"), " to prikazuje na malom primjeru. Lijevo je izvorni graf, s "
        "vjerojatnošću zapisanom na svakom bridu. U sredini je jedna realizacija: četiri "
        "su brida preživjela bacanje, a tri su nestala. Desno je ono što nas zanima. Iz "
        "izvora se u toj realizaciji može doći do četiri čvora, pa je doseg pet čvorova "
        "zajedno s izvorom. Čvor ", v("b"), " ostao je izvan kaskade jer je jedini brid "
        "koji do njega vodi nestao pri bacanju.")

    t.figure(figures / "fig1_2_live_edge.png",
             "Od stohastičke kaskade do dohvatljivosti. Bacanjem svih novčića unaprijed "
             "slučajno se širenje pretvara u obično pitanje dohvatljivosti u fiksnom "
             "podgrafu.",
             label="liveedge", width_cm=15.0)

    t.p("Korist je te zamjene praktična. Slučajan je proces sveden na pitanje "
        "dohvatljivosti, koje se rješava običnim obilaskom grafa. Očekivani doseg izvora ",
        v("s"), " tada je prosječna veličina dohvatljivog skupa preko svih realizacija:")

    t.eq(v("σ"), delim(v("s"), up(", "), v("G")), up(" = "), sub(up("E"), v("X")),
         delim(ifunc("R", [v("s"), up(", "), v("X")]), left="|", right="|"), label="sigma")

    t.p("Tu veličinu u ovom radu minimiziramo, a poglavlje ", t.sec("problem"),
        " pokazuje da ju je moguće samo procijeniti, ne i točno izračunati.")


def _threshold(t):
    t.h2("Epidemiološki prag", label="prag")

    t.p("Preostaje pitanje hoće li se kaskada uopće održati. Za širenje na mreži postoji "
        "prag: ispod njega se kaskada gasi i ostaje lokalna, a iznad njega zahvaća velik "
        "dio mreže. {~wang2003} pokazali su da prag ne ovisi samo o vjerojatnostima nego i "
        "o obliku mreže, i to preko najveće svojstvene vrijednosti njezine matrice "
        "susjedstva {castellano2010}:")

    t.eq(sub(v("λ"), up("c")), up(" = "), frac(up("1"), sub(v("λ"), up("max"))),
         label="prag")

    t.p("Prag koristimo samo jednom, u odjeljku ", t.sec("struktura"),
        ", da utvrdimo nalazi li se naša mreža iznad njega. Ako se nalazi, kaskada iz "
        "dobro povezanog izvora neće se ugasiti sama, pa zadatak nije usporiti mrežu nego "
        "odvojiti jedan izvor od nje.")
