"""4. Kriteriji odabira bridova.

Sources: Granovetter (1973) for the local bridge and the weak-tie argument; Tong et al.
(2012) for the eigen-score u(i)v(j) and its first-order justification; Kimura et al. (2008)
for betweenness, out-degree and random as the established comparison heuristics and for his
finding that blocking links between high-out-degree nodes is not necessarily effective;
Albert et al. (2000) for the hub-targeting intuition the degree criterion rests on.

Six criteria in 4.1-4.6, tie-breaking in 4.7. The distinct-value counts in 4.7 are read
from data/edge_features.csv at build time: they are the quantitative statement of the tie
problem and must not drift from the table the code actually scores against.
"""

import pandas as pd

from omml import acc, delim, frac, i, nary, sub, up, v

EDGES = None  # set by write()


def ifunc(name, argument):
    return [v(name), delim(argument)]


def _int(value):
    return f"{int(value):,}".replace(",", ".")


def _pct(value, decimals=1):
    return f"{100 * value:.{decimals}f}".replace(".", ",")


def write(t, figures):
    global EDGES
    EDGES = pd.read_csv(figures.parent / "data" / "edge_features.csv")

    t.h1("Kriteriji odabira bridova")

    t.p("Prethodno je poglavlje pokazalo da se prostor rezova ne može pretražiti iscrpno, "
        "pa svaka praktična metoda treba način da među tisućama kandidatnih bridova "
        "prepozna one koje vrijedi razmotriti. Ovo poglavlje opisuje šest takvih kriterija "
        "i pravilo koje odlučuje ondje gdje kriterij ne razlikuje bridove.")

    t.p("Kriterij je preslikavanje koje svakom kandidatnom bridu pridružuje realan broj, "
        "pri čemu veća vrijednost uvijek znači da je brid privlačniji za uklanjanje. Ta je "
        "usmjerenost jednaka za sve kriterije, pa nijedan dio sustava ne mora znati u kojem "
        "smjeru pojedini kriterij raste. Isti se kriteriji koriste na dva mjesta: kao "
        "samostalne pohlepne metode iz odjeljka ", t.sec("pohlepne"),
        " i kao operatori popravljanja unutar metaheuristike iz odjeljka ", t.sec("alns"),
        ". Time se ono što se uspoređuje svodi na način pretraživanja, a ne na to što koja "
        "metoda smatra dobrim bridom.")

    t.p("Za sve kriterije vrijedi zajedničko ograničenje: računaju se isključivo iz "
        "statičnih svojstava grafa, nikada iz uzorkovanih realizacija kojima se procjenjuje "
        "doseg. Razlog je metodološki. Kada bi se brid ocjenjivao veličinom izvedenom iz "
        "istih realizacija nad kojima se optimira, isti bi šum uzorkovanja ulazio i u cilj "
        "i u odabir kandidata, pa te dvije stvari više ne bi bile neovisne provjere jedna "
        "drugoj. Kriteriji stoga opisuju mrežu, a samo procjena dosega gleda realizacije.")

    _random(t)
    _probability(t)
    _degree(t)
    _bridge(t)
    _betweenness(t)
    _spectral(t)
    _ties(t)


# ------------------------------------------------------------------ 4.1 ----

def _random(t):
    t.h2("Slučajni odabir")

    t.p("Prvi kriterij svakom bridu pridružuje slučajan broj, pa je odabir jednolik po "
        "kandidatima. On ne sadrži nikakvo znanje o mreži i ne služi kao ozbiljan takmac, "
        "nego kao referentna točka: svaki strukturni kriterij mora pokazati da je bolji od "
        "njega da bi opravdao svoje postojanje. Istu ulogu slučajni odabir ima i kod "
        "{~kimura2008}. Ujedno je i jedini kriterij čiji ishod ovisi o sjemenu generatora "
        "slučajnih brojeva, pa je i jedini kojemu se rezultati usrednjuju preko više "
        "pokretanja.")


# ------------------------------------------------------------------ 4.2 ----

def _probability(t):
    t.h2("Vjerojatnost prijenosa")

    t.p("Najizravniji kriterij je sama vjerojatnost prijenosa brida:")

    t.eq(ifunc("c", v("e")), up(" = "), sub(v("p"), v("e")), label="crit_p")

    t.p("Obrazloženje slijedi izravno iz modela. Brid s visokom vjerojatnošću prenosi "
        "aktivaciju u velikoj većini realizacija, pa je prisutan u velikom udjelu ",
        i("live-edge"), " podgrafova; njegovim se uklanjanjem mijenja dohvatljivost u mnogo "
        "realizacija odjednom. Brid s niskom vjerojatnošću u većini realizacija ionako ne "
        "postoji, pa ondje njegovo uklanjanje ne mijenja ništa.")

    t.p("Kriterij ima i očito ograničenje: gleda pojedinačni brid, a ne njegov položaj u "
        "mreži. Vrlo pouzdan brid koji vodi u slijepu ulicu dobiva jednako visoku ocjenu "
        "kao jednako pouzdan brid koji vodi u jako povezanu jezgru, iako je učinak njihova "
        "uklanjanja posve različit.")


# ------------------------------------------------------------------ 4.3 ----

def _degree(t):
    t.h2("Zbroj izlaznih stupnjeva")

    t.p("Kriterij brid ocjenjuje zbrojem izlaznih stupnjeva njegovih krajeva u polaznom "
        "grafu:")

    t.eq(ifunc("c", [v("e"), up(" = "), delim(v("u"), up(", "), v("w"))]), up(" = "),
         ifunc("out", v("u")), up(" + "), ifunc("out", v("w")), label="crit_deg")

    t.p("Ideja je prenesena s razine čvorova: {~albert2000} pokazuju da mreže bez skale "
        "gube povezanost kada se ukloni malen broj čvorišta, pa je prirodno pretpostaviti "
        "da su i bridovi koji dodiruju čvorišta strukturno najvažniji. Ta se pretpostavka, "
        "međutim, u literaturi o blokiranju bridova ne potvrđuje: {~kimura2008} zaključuju "
        "da, za razliku od uklanjanja čvorova, blokiranje veza između čvorova visokog "
        "izlaznog stupnja nije nužno učinkovito. Objašnjenje je da čvorište ima mnogo "
        "izlaznih bridova, pa uklanjanje nekolicine njih ostavlja ostale netaknutima, dok "
        "se uklanjanjem samog čvorišta uklanjaju svi odjednom. Kriterij je zadržan zato što "
        "je uvriježen i što je očekivanje da će podbaciti provjerljiva tvrdnja.")


# ------------------------------------------------------------------ 4.4 ----

def _bridge(t):
    t.h2("Lokalni most", label="most")

    t.p("Jedini kriterij u skupu koji mjeri ", i("odsutnost"),
        " alternativnog puta preuzet je od {~granovetter1973}. Most je veza koja je jedini "
        "put između dvaju dijelova mreže; kako u velikim mrežama pravih mostova gotovo i "
        "nema, Granovetter uvodi blaži pojam lokalnog mosta stupnja ", v("n"),
        ", kod kojeg je najkraći zaobilazni put između krajeva veze, ne računajući samu "
        "vezu, duljine ", v("n"), ". U radu se koristi uobičajena operacionalizacija za ",
        v("n"), " ≥ 3: brid je lokalni most ako njegovi krajevi nemaju nijednog zajedničkog "
        "susjeda, jer bi zajednički susjed značio zaobilazni put duljine dva.")

    t.eq(ifunc("c", [v("e"), up(" = "), delim(v("u"), up(", "), v("w"))]),
         up(" = 1  ako je  "),
         delim([v("N"), delim(v("u")), up(" ∩ "), v("N"), delim(v("w"))],
               left="|", right="|"),
         up(" = 0,   inače 0"), label="crit_bridge")

    t.p("pri čemu je ", ifunc("N", v("u")), " skup susjeda čvora ", v("u"),
        " u neusmjerenoj inačici grafa. Granovetterov je argument da upravo takve veze "
        "prenose informaciju između inače odvojenih skupina i da bi njihovo uklanjanje više "
        "naštetilo prijenosu nego uklanjanje prosječne veze unutar gusto povezane skupine. "
        "Za problem koji se ovdje rješava to je izravno relevantno: ako je brid jedini "
        "kratki put prema nekom dijelu mreže, njegovim se uklanjanjem taj dio zaista "
        "odsijeca, dok se uklanjanjem brida unutar gusto povezane okoline kaskada samo "
        "preusmjeri. Kriterij poprima vrijednost jedan na ",
        _pct(EDGES.is_local_bridge.mean()), " % bridova mreže (odjeljak ",
        t.sec("zajednice"), "), a prednost mu je što, za razliku od podjele na zajednice, "
        "ne ovisi ni o kakvom stohastičkom postupku, pa je potpuno ponovljiv.")


# ------------------------------------------------------------------ 4.5 ----

def _betweenness(t):
    t.h2("Međupoloženost s obzirom na izvor")

    t.p("Međupoloženost je mjera koja element mreže ocjenjuje brojem najkraćih putova koji "
        "kroz njega prolaze {predavanja}. U klasičnom se obliku promatraju putovi između "
        "svih parova čvorova, no ovdje je izvor jedan i unaprijed poznat, pa putovi koji iz "
        "njega ne polaze nisu relevantni. Kriterij se stoga ograničava na putove koji "
        "počinju u izvoru:")

    t.eq(ifunc("c", v("e")), up(" = "),
         nary("∑", [v("w"), up(" ∈ "), v("V")], None,
              [frac([sub(v("σ"), [v("s"), v("w")]), delim(v("e"))],
                    sub(v("σ"), [v("s"), v("w")]))]),
         label="crit_btw")

    t.p("gdje je ", sub(v("σ"), [v("s"), v("w")]),
        " broj najkraćih putova od izvora do čvora ", v("w"), ", a ",
        sub(v("σ"), [v("s"), v("w")]), delim(v("e")),
        " broj onih među njima koji koriste brid ", v("e"),
        ". Brid s visokom vrijednošću leži na velikom udjelu najkraćih putova kojima se "
        "kaskada iz izvora najbrže širi. Za razliku od ostalih kriterija ovaj se mora "
        "izračunati zasebno za svaki izvor, jer o izvoru ovisi po definiciji.")

    t.p("Vrijedi navesti jednu razliku u odnosu na {~kimura2008}, koji međupoloženost "
        "također koristi kao usporednu metodu: on je nakon svakog uklonjenog brida ponovno "
        "izračunava na izmijenjenoj mreži, dok se ovdje računa jednom i tijekom "
        "pretraživanja ne obnavlja, jer bi ponovni izračun unutar petlje bio nerazmjerno "
        "skup (odjeljak ", t.sec("arhitektura"),
        "). Riječ je o namjernoj razlici koju pri tumačenju rezultata treba imati na umu.")


# ------------------------------------------------------------------ 4.6 ----

def _spectral(t):
    t.h2("Spektralni kriterij", label="spektralni")

    t.p("Posljednji kriterij dolazi iz spektralne teorije uvedene u odjeljku ",
        t.sec("prag"), ". {~tong2012} razmatraju koliko se najveća vlastita vrijednost "
        "matrice susjedstva smanji uklanjanjem skupa bridova. Ponovni izračun za svaki "
        "kandidatni skup nije izvediv, pa primjenom teorije perturbacija prvog reda "
        "pokazuju da vrijedi")

    t.eq(v("λ"), up(" − "), acc(v("λ")), up(" ≈ "), v("c"),
         nary("∑", [v("e"), up(" ∈ "), v("S")], None,
              [v("u"), delim(v("i")), v("w"), delim(v("j"))]),
         label="eigendrop")

    t.p("gdje su ", v("u"), " i ", v("w"),
        " lijevi i desni vlastiti vektor pridruženi najvećoj vlastitoj vrijednosti, a ",
        v("i"), " i ", v("j"), " indeksi krajeva brida. Pad vlastite vrijednosti time se "
        "raspada na doprinose pojedinih bridova, pa se svaki brid može ocijeniti neovisno:")

    t.eq(ifunc("c", [v("e"), up(" = "), delim(v("i"), up(", "), v("j"))]), up(" = "),
         v("u"), delim(v("i")), up(" · "), v("w"), delim(v("j")), label="crit_spec")

    t.p("Prema Perron-Frobeniusovu teoremu vlastiti se vektori nenegativne matrice mogu "
        "odabrati nenegativnima, pa se predznak po potrebi obrne prije ocjenjivanja "
        "{tong2012}.")

    t.p("Kod ovog kriterija treba biti izričit oko jedne razlike u ciljevima. Najveća "
        "vlastita vrijednost određuje epidemiološki prag cijele mreže, dakle hoće li se "
        "kaskada uopće moći makroskopski proširiti, dok je cilj ovog rada smanjenje dosega "
        "iz jednog zadanog izvora; uklanjanje nekoliko bridova prag mreže ionako ne pomiče "
        "mjerljivo. Kriterij se stoga ne koristi zato što optimira pravu veličinu, nego kao "
        "strukturno utemeljena ocjena globalne važnosti brida, a koliko je takva ocjena "
        "korisna za ovaj cilj empirijsko je pitanje.")


# ------------------------------------------------------------------ 4.7 ----

def _ties(t):
    t.h2("Razrješavanje izjednačenih vrijednosti", label="izjednacenost")

    t.p("Kriteriji se razlikuju po tome koliko su fino stupnjevani, i ta razlika nije "
        "tehnička sitnica nego svojstvo koje bitno utječe na ponašanje metoda. ",
        t.tabref("kriteriji"), " prikazuje koliko različitih vrijednosti svaki kriterij "
        "poprima na svih ", _int(len(EDGES)), " bridova mreže.")

    t.table(
        ["Kriterij", "Što mjeri", "Razina", "Različitih vrijednosti"],
        [
            ["slučajni", "ništa (kontrola)", "po pozivu", "praktički sve"],
            ["vjerojatnost", "pouzdanost kanala", "globalno",
             _int(EDGES.probability.nunique())],
            ["zbroj stupnjeva", "blizina čvorištima", "globalno",
             _int(EDGES.degree_sum.nunique())],
            ["lokalni most", "nepostojanje obilaznice", "globalno",
             _int(EDGES.is_local_bridge.nunique())],
            ["međupoloženost", "udio najkraćih putova iz izvora", "po izvoru",
             "ovisi o izvoru"],
            ["spektralni", "doprinos spektralnom polumjeru", "globalno",
             _int(EDGES.spectral_score.nunique())],
        ],
        "Šest kriterija za odabir bridova i broj različitih vrijednosti koje poprimaju na "
        "mreži Bitcoin Alpha.",
        label="kriteriji",
        widths_cm=[3.0, 5.2, 2.6, 3.4])

    t.p("Raspon je izrazit. Spektralni kriterij gotovo svakom bridu daje vlastitu "
        "vrijednost, dok lokalni most ima samo dvije, a vjerojatnost prijenosa točno deset, "
        "jer je izvedena iz cjelobrojne ocjene (odjeljak ", t.sec("skup"),
        "). Kod tih dvaju kriterija rangiranje kandidata nije poredak nego nekoliko velikih "
        "skupina jednako ocijenjenih bridova, pa kriterij zapravo ne određuje koji će "
        "konkretni bridovi ući u rez; to određuje pravilo kojim se izjednačenost "
        "razrješava.")

    t.p("U radu se koriste dva takva pravila, namjerno različita. Pohlepne metode iz "
        "odjeljka ", t.sec("pohlepne"), " razrješavaju izjednačenost ", i("deterministički"),
        ", poretkom po identifikatorima krajeva brida, čime jedna trojka izvora, proračuna "
        "i kriterija uvijek daje isti rez — što je uvjet da usporedba metoda bude "
        "ponovljiva. Operatori metaheuristike iz odjeljka ", t.sec("alns"), " biraju ",
        i("slučajno"), " među izjednačenima, jer bi deterministično pravilo ondje bilo "
        "štetno: kriteriji poput lokalnog mosta u svakom bi pokretanju vraćali potpuno isti "
        "rez, pa pretraživanje ne bi imalo što istraživati. Oba se pravila oslanjaju na "
        "istu funkciju rangiranja, pa se ne mogu neprimjetno razići.")

    t.p("Posljedica je da kod slabo stupnjevanih kriterija dio odluke ne donosi kriterij "
        "nego pravilo razrješavanja. To se ne pokušava sakriti ni ukloniti: uz svako "
        "pohlepno rješenje bilježi se veličina izjednačene skupine na rubu proračuna, "
        "podijeljena na bridove koji su ušli u rez i one koji nisu, a kod metaheuristike se "
        "raspršenje rezultata preko nekoliko sjemena izvještava kao svojstvo metode, a ne "
        "usrednjuje. Protokol je opisan u odjeljku ", t.sec("protokol"), ".")
