"""4. Kriteriji i metode rjesavanja.

The Uvod describes criteria and search methods as one central part, so they are one
chapter rather than two.

Everything attributed to Ropke & Pisinger (2006) below was read from the paper:

  * roulette wheel, their eq. (20), P(j) = w_j / sum w_i, with the insertion heuristic
    selected independently of the removal heuristic;
  * segments, scores reset to zero at the start of each, raised by exactly one of
    sigma1 (new global best), sigma2 (better than current, not accepted before),
    sigma3 (accepted but not better);
  * the weight update w_{i,j+1} = w_ij(1-r) + r*(pi_i/theta_i), where theta_i counts the
    attempts, and equal weights in the first segment;
  * the determinism parameter p >= 1, where a low p means much randomness;
  * the relatedness measure, their eq. (17), four terms weighted by (phi, chi, psi, omega),
    each scaled to [0,1], with the servable-set term written as the min-normalised overlap;
  * their tuned vector (phi, chi, psi, omega, p, p_worst, w, c, ...) = (9, 3, 2, 5, 6, 3,
    0.05, 0.99975, ...).

Kimura et al. (2008) is quoted for two things, both verbatim from the paper: their
comparison methods are betweenness, out-degree and random, and "blocking links between
nodes with high out-degrees is not necessarily effective".

Parameter values are imported from code/config.py rather than typed, for the same reason
measurements are read from CSV.
"""

import pandas as pd

import params
from omml import delim, frac, i, sub, sup, up, v
from params import config


def ifunc(name, argument):
    return [v(name), delim(argument)]


def write(t, figures):
    edges = pd.read_csv(figures.parent / "data" / "edge_features.csv")

    t.h1("Kriteriji i metode rješavanja")
    t.p("Rješenje se gradi u dva sloja. Prvi je kriterij koji bridovima pridružuje ocjenu "
        "važnosti, a drugi je postupak koji na temelju tih ocjena bira skup od ", v("k"),
        " bridova. Ista se šest kriterija koriste u obje metode koje uspoređujemo, pa "
        "razlika među metodama leži isključivo u načinu pretraživanja.")

    _criteria(t, edges)
    _ties(t, edges)
    _greedy(t)
    _alns(t, figures)
    _operators(t)
    _layers(t, figures)


# -- 4.1 ---------------------------------------------------------------------

def _criteria(t, edges):
    t.h2("Šest kriterija za odabir bridova", label="kriteriji")

    t.p("Svaki kriterij utjelovljuje jednu pretpostavku o tome što neki brid čini važnim. "
        "Nijedan ne gleda realizacije, nego se svi računaju iz osnovnog grafa. Razlog je "
        "metodološki: kada bi kriterij bio izveden iz istih realizacija na kojima mjerimo "
        "doseg, isti bi šum ulazio i u ocjenu i u odabir, pa jedno drugom više ne bi bilo "
        "neovisna provjera.")

    t.p("Slučajni odabir ne mjeri ništa i služi kao kontrola. Vjerojatnost prijenosa "
        "pretpostavlja da je važan onaj brid kroz koji kaskada najčešće prolazi. Zbroj "
        "izlaznih stupnjeva pretpostavlja da su važni bridovi u blizini čvorišta:")

    t.eq(ifunc("c", [v("e"), up(" = "), delim(v("u"), up(", "), v("w"))]), up(" = out"),
         delim(v("u")), up(" + out"), delim(v("w")), label="stupnjevi")

    t.p("Lokalni most preuzima ideju {~granovetter1973} da je veza koja spaja dvije inače "
        "nepovezane okoline vrednija od one unutar već povezane skupine. Brid ovdje "
        "smatramo lokalnim mostom ako njegova dva kraja nemaju nijednog zajedničkog "
        "susjeda, što je uobičajena operacionalizacija toga pojma. Međupoloženost s "
        "obzirom na izvor mjeri koliki udio najkraćih putova iz izvora prolazi kroz brid, "
        "pa je jedini kriterij koji se računa za svaki izvor posebno. Spektralni kriterij "
        "preuzimamo od {~tong2012}, koji brid ocjenjuju umnoškom lijeve i desne svojstvene "
        "komponente njegovih krajeva:")

    t.eq(ifunc("c", [v("e"), up(" = "), delim(v("i"), up(", "), v("j"))]), up(" = "),
         ifunc("u", v("i")), up(" · "), ifunc("v", v("j")), label="spektralni")

    t.p("Dvije je pretpostavke vrijedno iznijeti unaprijed, jer ih mjerenje može opovrgnuti. "
        "{~kimura2008} nalaze da blokiranje veza između čvorova s velikim izlaznim "
        "stupnjem nije nužno djelotvorno, pa očekujemo da će kriterij stupnjeva podbaciti. "
        "Spektralni kriterij pak po samoj konstrukciji optimira pogrešnu veličinu, jer "
        "spektralni radijus upravlja pragom cijele mreže, a ne dosegom iz jednog izvora.")

    counts = {
        "vjerojatnost prijenosa": edges.probability.nunique(),
        "zbroj izlaznih stupnjeva": edges.degree_sum.nunique(),
        "lokalni most": edges.is_local_bridge.nunique(),
        "spektralni": edges.spectral_score.nunique(),
    }
    t.table(
        ["Kriterij", "Što mjeri", "Broj različitih vrijednosti"],
        [["slučajni odabir", "ništa, kontrola", "–"],
         ["vjerojatnost prijenosa", "pouzdanost kanala",
          params.hr(counts["vjerojatnost prijenosa"])],
         ["zbroj izlaznih stupnjeva", "blizinu čvorištima",
          params.hr(counts["zbroj izlaznih stupnjeva"])],
         ["lokalni most", "odsutnost zaobilaznog puta",
          params.hr(counts["lokalni most"])],
         ["međupoloženost", "udio najkraćih putova iz izvora", "računa se po izvoru"],
         ["spektralni", "doprinos spektralnom radijusu",
          params.hr(counts["spektralni"])]],
        "Šest kriterija za odabir bridova i broj različitih vrijednosti koje poprimaju na "
        "mreži Bitcoin Alpha.",
        label="kriterijitab", widths_cm=[4.2, 6.3, 4.5])


# -- 4.2 ---------------------------------------------------------------------

def _ties(t, edges):
    t.h2("Izjednačene vrijednosti", label="izjednacene")

    t.p("Zadnji stupac ", t.tabref("kriterijitab"), " otkriva problem koji se lako "
        "previdi. Na ", params.count(len(edges), "bridu", "brida", "bridova"),
        " lokalni most poprima samo dvije vrijednosti, a vjerojatnost prijenosa deset. "
        "Rangiranje po takvom kriteriju ne daje poredak nego nekoliko velikih skupina "
        "jednako ocijenjenih bridova. Za polovicu kriterija pravilo kojim razrješavamo "
        "izjednačenost zato nije tehnička sitnica nego dio same metode.")

    t.p("Koristimo dva različita pravila, i to namjerno. Pohlepne metode razrješavaju "
        "izjednačenost determinističkim poretkom, pa jedan izvor uz zadani proračun i "
        "kriterij uvijek daje isti rez, što usporedbu metoda čini ponovljivom. "
        "Metaheuristika ih razrješava slučajnim odabirom, jer bi deterministično pravilo "
        "značilo da kriteriji lokalnog mosta i vjerojatnosti u svakom pokretanju vrate "
        "isti rez, pa pretraživati ne bi imalo što.")


# -- 4.3 ---------------------------------------------------------------------

def _greedy(t):
    t.h2("Pohlepne metode", label="pohlepne")

    t.p("Pohlepna metoda ocijeni sve bridove koji izlaze iz izvora, poreda ih i uzme "
        "najboljih ", v("k"), ". Jedna takva metoda postoji za svaki kriterij, pa ih je "
        "šest. Njihova uloga nije da budu slab protivnik: one su upravo ono što bi "
        "razuman inženjer napravio bez pretraživanja, a tri od njih, međupoloženost, "
        "izlazni stupanj i slučajni odabir, {~kimura2008} koriste kao vlastite metode za "
        "usporedbu.")

    t.p("Treba pritom biti iskren o tome što usporedba dokazuje. Metoda koju {~kimura2008} "
        "predlažu kao vlastitu nije pohlepni odabir po topološkom kriteriju, nego pohlepni "
        "postupak vođen izmjerenim dosegom, uz ponovnu procjenu u svakom koraku. Nju u "
        "ovom radu ne uspoređujemo, pa rad odgovara na pitanje nadmašuje li prilagodljivo "
        "pretraživanje nepromjenjiv topološki kriterij, a ne nadmašuje li najbolju poznatu "
        "metodu.")


# -- 4.4 ---------------------------------------------------------------------

def _alns(t, figures):
    t.h2("Metaheuristika ALNS", label="alns")

    t.p("Iz odjeljka ", t.sec("tezina"), " znamo da se bridovi isplate tek zajedno, pa "
        "metoda mora mijenjati više njih odjednom. Upravo to radi ",
        i("Adaptive Large Neighborhood Search"), " {ropke2006}: u svakoj iteraciji razori "
        "dio postojećeg rješenja i ponovno ga izgradi, umjesto da ga proširuje po jedan "
        "element. Uklonimo li ", v("q"), " bridova iz reza i vratimo drugih ", v("q"),
        ", susjedstvo koje pretražujemo mnogo je šire od zamjene jednog brida.")

    t.p("Pridjev prilagodljiv odnosi se na to da metoda uči koji joj se operatori "
        "isplate. U svakoj se iteraciji operator bira kotačem sreće, dakle s vjerojatnošću "
        "razmjernom njegovoj težini {ropke2006}:")

    t.eq(up("P"), delim([up("odabran je operator "), v("j")]), up(" = "),
         frac(sub(v("w"), v("j")), [up("∑"), sub(v("w"), v("i"))]), label="kotac")

    t.p("Uspješna iteracija donosi bodove operatorima koji su u njoj sudjelovali, ali samo "
        "ako rješenje dotad nije bilo viđeno. Novo najbolje rješenje nosi ",
        params.hr(config.ALNS_SIGMA1), " bodova, rješenje prihvaćeno iako je lošije ",
        params.hr(config.ALNS_SIGMA3), ", a rješenje bolje od trenutnoga ",
        params.hr(config.ALNS_SIGMA2), " {ropke2006}. Bodove uvijek dobivaju oba "
        "operatora, jer se ne može znati koji je od njih zaslužan za uspjeh. Na kraju "
        "svakog segmenta od ",
        params.count(config.ALNS_SEGMENT_LENGTH, "iteracije", "iteracije", "iteracija"),
        " težine se osvježavaju, gdje je ", sub(v("π"), v("i")),
        " skupljeni broj bodova, ", sub(v("θ"), v("i")),
        " broj pokušaja, a ", v("r"), " brzina reakcije:")

    t.eq(sub(v("w"), [v("i"), up(", "), v("j"), up(" + 1")]), up(" = "),
         sub(v("w"), [v("i"), v("j")]), up(" ("), up("1 − "), v("r"), up(") + "), v("r"),
         up(" · "), frac(sub(v("π"), v("i")), sub(v("θ"), v("i"))), label="tezine")

    t.p("U prvom su segmentu sve težine jednake, pa metoda ne polazi ni od kakve "
        "pretpostavke o tome koji je kriterij bolji {ropke2006}. Novo se rješenje prihvaća "
        "ako je bolje, a ako je lošije, prihvaća se s vjerojatnošću koja pada kako "
        "pretraga odmiče, po uzoru na simulirano kaljenje. Početna se temperatura ne "
        "zadaje nego izvodi iz početnog rješenja, jer se doseg među izvorima razlikuje za "
        "tri reda veličine pa bi jedna fiksna vrijednost bila pogrešna za gotovo svaki "
        "izvor. ", t.figref("petlja"), " prikazuje jednu iteraciju, a ",
        t.coderef("alnskod"), " istu petlju u obliku pseudokoda.")

    t.figure(figures / "fig5_1_alns_loop.png",
             "Jedna iteracija metode ALNS. Tri se odluke donose neovisno, svaka vlastitim "
             "kotačem sreće, a nagrada ostvarena u iteraciji pripisuje se svima trima.",
             label="petlja", width_cm=13.0)

    t.code([
        "D ← početno rješenje od k bridova",
        "D* ← D;  T ← početna temperatura",
        "ponavljaj max_iter puta:",
        "    kotačem sreće odaberi operator razaranja, operator popravljanja i sloj",
        "    q ← broj bridova koji se uklanja",
        "    D′ ← popravi(razori(D, q), q, sloj)",
        "    ako je σ(D′) < σ(D) ili slučajan broj < exp(−(σ(D′) − σ(D)) / T):",
        "        D ← D′",
        "    ako je σ(D) < σ(D*):  D* ← D",
        "    dodijeli bodove upotrijebljenim operatorima;  T ← T · c",
        "    na kraju segmenta: osvježi težine i poništi bodove",
        "vrati D*",
    ], "Petlja metode ALNS prilagođena problemu SS-IMER.", label="alnskod")


# -- 4.5 ---------------------------------------------------------------------

def _operators(t):
    t.h2("Operatori razaranja i popravljanja", label="operatori")

    t.p("Operatori razaranja biraju koje bridove izbaciti iz trenutnog reza. Slučajno "
        "razaranje bira ih nasumično. Razaranje najgoreg izbacuje one čiji je doprinos "
        "najmanji. Razaranje srodnih izbacuje bridove koji su međusobno slični, u nadi da "
        "će ih popravljanje moći zamijeniti kao cjelinu. Nijedan od njih ne bira strogo "
        "najbolji kandidat, nego iz poretka izvlači element pomoću slučajnog broja "
        "potenciranog parametrom determinizma: veći parametar znači pohlepniji izbor, a "
        "vrijednost bliska jedinici gotovo ravnomjeran {ropke2006}.")

    t.p("Mjeru srodnosti {~ropke2006} definiraju za problem prijevoza, gdje se uspoređuju "
        "dva zahtjeva s dvjema lokacijama. Naš je zahtjev brid, a njegove su dvije "
        "lokacije početak i kraj, pa se sva četiri člana preslikavaju izravno, s njihovim "
        "ugođenim težinama. ", t.tabref("srodnost"), " prikazuje to preslikavanje.")

    t.table(
        ["Član mjere srodnosti", "Težina", "Značenje u problemu SS-IMER"],
        [["udaljenost", params.hr(config.SHAW_PHI),
          "broj koraka između početaka i između krajeva dvaju bridova"],
         ["vrijeme", params.hr(config.SHAW_CHI),
          "udaljenost krajeva brida od izvora, jer je to najranije vrijeme aktivacije"],
         ["opterećenje", params.hr(config.SHAW_PSI),
          "vjerojatnost prijenosa koju brid nosi"],
         ["poslužen skup", params.hr(config.SHAW_OMEGA),
          "preklapanje područja koje svaki brid opskrbljuje"]],
        "Preslikavanje četiriju članova mjere srodnosti {ropke2006} na veličine problema "
        "SS-IMER, s njihovim ugođenim težinama.",
        label="srodnost", widths_cm=[3.6, 1.8, 9.6])

    t.p("Operatori popravljanja vraćaju uklonjene bridove, i njih je po jedan za svaki "
        "kriterij iz ", t.tabref("kriterijitab"), ". Time kriteriji ulaze u pretragu kao "
        "ravnopravni kandidati, a kotač sreće tijekom rada uči koji se od njih na kojoj "
        "instanci isplati. To je prva razina prilagodljivog učenja koju rad ispituje.")


# -- 4.6 ---------------------------------------------------------------------

def _layers(t, figures):
    t.h2("Slojevi udaljenosti od izvora", label="slojevi")

    t.p("Druga se razina odnosi na to koliko daleko od izvora tražimo. Primjer iz odjeljka ",
        t.sec("tezina"), " pokazao je da najbolji potez ponekad nije brid uz izvor nego "
        "brid u uskom grlu dublje u mreži. Da bismo to mogli ispitati, kandidate dijelimo "
        "u slojeve prema tome koliko je koraka početak brida udaljen od izvora. Sloj nula "
        "sadrži bridove koji izlaze izravno iz izvora, dakle točno ono što gledaju "
        "pohlepne metode.")

    t.figure(figures / "fig5_2_hop_layers.png",
             "Shematski prikaz slojeva kandidata oko izvora. Svaka je točka jedan "
             "kandidatni brid, a svaki sljedeći sloj sadrži bridove koji su za jedan korak "
             "udaljeniji od izvora.",
             label="slojevi", width_cm=13.0)

    t.p("U svakoj iteraciji popravljanje crpi iz jednog sloja, izabranog trećim kotačem "
        "sreće. Slojevi na početku imaju jednake težine, jer je upravo pitanje koliko se "
        "daleko isplati gledati ono na koje tražimo odgovor. Dubina je ograničena na ",
        params.hr(config.ALNS_MAX_HOP_SCOPE),
        ", što je opravdano prosječnom duljinom puta iz odjeljka ", t.sec("struktura"),
        ": do te udaljenosti kandidati već obuhvaćaju gotovo sve što je iz izvora "
        "dohvatljivo, a svaki dublji sloj samo umnaža njihov broj.")

    t.p("Jedno ograničenje treba navesti odmah, jer određuje što se iz rezultata smije "
        "zaključiti. Slojevi se po veličini razlikuju i do tri reda veličine, a manji je "
        "sloj lakše pretražiti, pa veća naučena težina sloja nula dijelom mjeri samo tu "
        "lakoću. Zato u odjeljku ", t.sec("udaljenost"), " ne čitamo naučene težine, nego "
        "izravno gledamo dolaze li bridovi izvan sloja nula uopće do pobjedničkog reza.")
