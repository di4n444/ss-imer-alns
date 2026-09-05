"""3. Formulacija problema SS-IMER.

Sources read for this chapter, in the order they are used: Kempe, Kleinberg & Tardos
(2003) for influence maximization, its NP-hardness (their Theorem 2.4), the submodularity
argument that licenses the greedy guarantee, and their own statement that computing sigma
exactly is an open question; Kimura et al. (2008) for the contamination minimization
problem, its exact-cardinality budget and the bond-percolation estimator; Castiglioni et
al. (2021) for the IMER definition (their Definition 4) and the inapproximability result
(their Theorem 6); Valiant (1979) for the #P-completeness of two-terminal network
reliability, which is what evaluating one candidate cut exactly amounts to; Tong et al.
(2012) for the observation that the effect of removing a set of edges is not the sum of
the individual effects.

The chapter states only what is established in those sources or follows from the
definitions. Everything measured on this dataset is in chapters 2, 6 and 7.
"""

import math

from omml import acc, delim, frac, i, limlow, nary, sub, sup, up, v
from params import config, count, hr


def ifunc(name, argument):
    """A function whose name is itself a symbol — sigma(s, G), R(s, X) — so the name is
    set in math italic, unlike exp or arg min which stay upright."""
    return [v(name), delim(argument)]


def sigma(*parts):
    return ifunc("σ", list(parts))


def write(t, figures):
    t.h1("Formulacija problema SS-IMER")

    t.p("Prethodna dva poglavlja opisala su model širenja i mrežu na kojoj se on odvija. "
        "Ovo poglavlje precizno postavlja optimizacijski problem koji se u radu rješava: "
        "koje se veličine daju, što se traži, zašto je to teško i kako se uopće mjeri "
        "vrijednost jednog kandidatnog rješenja.")

    _srodni(t)
    _definicija(t)
    _slozenost(t, figures)
    _procjena(t)


# ------------------------------------------------------------------ 3.1 ----

def _srodni(t):
    t.h2("Temeljni problemi optimizacije utjecaja")

    t.p("Problemi koji se u literaturi razmatraju pod zajedničkim nazivom optimizacije "
        "utjecaja dijele istu strukturu. Zadan je model širenja, zadan je proračun kojim "
        "se smije zahvatiti u mrežu i traži se skup elemenata čija izmjena najviše mijenja "
        "doseg kaskade. Razlikuju se po tome što se mijenja, u kojem smjeru i iz čije "
        "perspektive se doseg mjeri.")

    t.p("Ishodišni je problem maksimizacija utjecaja koju formuliraju {~kempe2003}. Za "
        "zadani proračun ", v("k"), " traži se početni skup ", v("A"), " od ", v("k"),
        " čvorova koji maksimizira očekivani broj aktiviranih čvorova ", sigma(v("A")),
        ". Autori pokazuju da je problem NP-težak, ali i da funkcija ", v("σ"),
        " nad početnim skupovima ima dva svojstva koja zajedno spašavaju situaciju: "
        "monotona je, jer dodavanje čvora u početni skup ne može smanjiti doseg, i "
        "submodularna, jer je doprinos novog čvora to manji što je početni skup veći. Za "
        "takve funkcije pohlepni postupak, koji u svakom koraku dodaje element s najvećim "
        "trenutnim doprinosom, daje rješenje unutar faktora ", up("1 − 1/"), v("e"),
        " od optimalnog {kempe2003}. Ta je kombinacija razlog zbog kojeg je pohlepni "
        "pristup postao uobičajen u ovom području.")

    t.p("Zrcalni je problem sprječavanje širenja. Ono se može izvesti uklanjanjem čvorova, "
        "što je pristup kojim {~albert2000} pokazuju krhkost mreža bez skale, ili "
        "uklanjanjem bridova. Uklanjanje brida blaža je intervencija jer ne uklanja "
        "sudionika iz mreže, nego samo jedan kanal između dvaju sudionika {tong2012}, pa "
        "je u primjenama u kojima su sudionici stvarni korisnici često jedina izvediva.")

    t.p("Dva su takva problema izravni preteče ovoga rada. {~kimura2008} definiraju problem "
        "minimizacije kontaminacije: mjera koja se minimizira je prosječan doseg preko "
        "svih čvorova mreže kao mogućih izvora,")

    t.eq(ifunc("c", v("G")), up(" = "),
         frac(up("1"), delim(v("V"), left="|", right="|")),
         nary("∑", [v("w"), up(" ∈ "), v("V")], None,
              [sigma(v("w"), up("; "), v("G"))]),
         label="kontaminacija")

    t.p("a traži se skup od točno ", v("k"), " bridova čije uklanjanje tu mjeru najviše "
        "smanjuje {kimura2008}. {~castiglioni2021} definiraju problem uklanjanja bridova "
        "pod nazivom ", i("Influence-Minimization-by-Edge-Removal"), " (IMER): za zadani "
        "graf, zadani skup početnih čvorova i proračun ", v("B"), " traži se skup od "
        "najviše ", v("B"), " bridova koji maksimizira pad broja dosegnutih čvorova.")

    t.p("Problem koji se ovdje rješava uža je varijanta te obitelji, određena trima "
        "odlukama:")

    t.bullets([
        ["izvor je jedan jedini i unaprijed poznat, umjesto skupa početnih čvorova "
         "{castiglioni2021} ili prosjeka preko svih čvorova {kimura2008}. To odgovara "
         "praktičnoj situaciji u kojoj je sumnjivi korisnik već identificiran;"],
        ["proračun se troši u cijelosti, dakle ", delim(v("D"), left="|", right="|"),
         " = ", v("k"), ", kao kod {~kimura2008}, a ne najviše ", v("B"),
         " kao kod {~castiglioni2021};"],
        ["mijenjaju se isključivo bridovi, nikada čvorovi."],
    ])

    t.p("Radi kratkoće se u nastavku koristi oznaka SS-IMER. Kako je rečeno u uvodu, "
        "prefiks je uveden u ovom radu i nije ustaljen naziv u literaturi.")


# ------------------------------------------------------------------ 3.2 ----

def _definicija(t):
    t.h2("Matematička definicija problema", label="definicija")

    t.p("Neka je ", v("G"), " = ", delim(v("V"), up(", "), v("E")), " usmjeren graf i "
        "neka svakom bridu ", v("e"), " = ", delim(v("u"), up(", "), v("w")),
        " pripada vjerojatnost prijenosa ", sub(v("p"), v("e")), " ∈ ",
        delim(up("0, 1"), left="(", right="]"), ", određena preslikavanjem iz odjeljka "
        "2.1. Neka je ", v("s"), " ∈ ", v("V"), " zadani izvor. Za skup bridova ", v("D"),
        " ⊆ ", v("E"), " oznaka ", v("G"), " \\ ", v("D"), " označava graf ",
        delim(v("V"), up(", "), [v("E"), up(" \\ "), v("D")]),
        ", dakle mrežu u kojoj su bridovi iz ", v("D"), " uklonjeni. Skup ", v("D"),
        " naziva se rezom.")

    t.p("Očekivani doseg ", sigma(v("s"), up(", "), v("G")),
        " je očekivani broj čvorova koji su na kraju procesa iz odjeljka ", t.sec("icm"), " aktivni ako "
        "je na početku aktivan samo čvor ", v("s"), ". Problem SS-IMER glasi: za zadane ",
        v("G"), ", ", v("s"), " i cjelobrojni proračun ", v("k"), " pronaći")

    t.eq(sup(v("D"), up("*")), up(" = "),
         limlow(up("arg min"),
                [v("D"), up(" ⊆ "), sub(v("E"), v("s")), up(",  "),
                 delim(v("D"), left="|", right="|"), up(" = "), v("k")]),
         sigma(v("s"), up(", "), [v("G"), up(" \\ "), v("D")]),
         label="ssimer")

    t.p("Skup kandidata ", sub(v("E"), v("s")), " nisu svi bridovi mreže, nego samo oni "
        "čiji je početni čvor dohvatljiv iz ", v("s"), " u grafu ", v("G"),
        ". Brid do čijeg početnog čvora kaskada ne može doći ne može ni prenijeti "
        "aktivaciju, pa njegovo uklanjanje ne mijenja doseg ni u jednoj realizaciji. "
        "Ograničenje na ", sub(v("E"), v("s")),
        " stoga ne isključuje nijedno rješenje, nego samo uklanja bridove koji su za ovaj "
        "izvor bez učinka.")

    t.p("Uvjet ", delim(v("D"), left="|", right="|"), " = ", v("k"),
        " ne gubi na općenitosti u odnosu na blaži uvjet ",
        delim(v("D"), left="|", right="|"), " ≤ ", v("k"), ". Funkcija ", v("σ"),
        " je naime nerastuća po rezu: uklanjanjem dodatnog brida nijedan put ne nastaje, "
        "pa doseg ne može porasti. Svako rješenje s manje od ", v("k"),
        " bridova zato se može nadopuniti do ", v("k"), " bez pogoršanja.")

    t.p("Za usporedbu različitih izvora potrebna je mjera neovisna o njihovoj veličini, "
        "jer se doseg među izvorima razlikuje za tri reda veličine (odjeljak ", t.sec("populacija"), "). "
        "Koristi se relativno smanjenje dosega")

    t.eq(ifunc("R", v("D")), up(" = 1 − "),
         frac(sigma(v("s"), up(", "), [v("G"), up(" \\ "), v("D")]),
              sub(v("σ"), up("0"))),
         up(",       "), sub(v("σ"), up("0")), up(" = "), sigma(v("s"), up(", "), v("G")),
         label="reduction")

    t.p("pri čemu je ", sub(v("σ"), up("0")),
        " doseg neizmijenjene mreže. Vrijednost ", ifunc("R", v("D")),
        " = 0 znači da rez nije promijenio ništa, a veće vrijednosti znače uspješniju "
        "intervenciju.")

    t.p("Iz definicije slijedi i jedan rubni slučaj koji nije pogreška nego instanca s "
        "poznatim rješenjem. Ako je proračun barem jednak izlaznom stupnju izvora, dakle ",
        v("k"), " ≥ ", ifunc("out", v("s")),
        ", tada se mogu presjeći svi bridovi koji izlaze iz izvora. Izvor time postaje "
        "izoliran i doseg pada na ", sigma(v("s"), up(", "), [v("G"), up(" \\ "), v("D")]),
        " = 1, jer izvor uvijek broji sam sebe. To je ujedno i globalni optimum, budući da "
        "je doseg uvijek barem jedan, pa takvu instancu nema smisla pretraživati. Kako je "
        "pokazano u odjeljku ", t.sec("populacija"), ", na mreži Bitcoin Alpha to nije rijetkost nego svojstvo "
        "većine čvorova.")


# ------------------------------------------------------------------ 3.3 ----

def _slozenost(t, figures):
    t.h2("Složenost problema", label="slozenost")

    t.p("Problem je težak na dvije odvojene razine, i korisno ih je razlikovati jer traže "
        "različite odgovore. Prva je razina vrednovanje jednog jedinog kandidatnog reza, a "
        "druga pretraživanje prostora svih rezova.")

    t.h3("Vrednovanje jednog reza")

    t.p("Prema ekvivalenciji iz odjeljka ", t.sec("icm"), " očekivani se doseg može zapisati kao zbroj "
        "vjerojatnosti po čvorovima:")

    t.eq(sigma(v("s"), up(", "), v("G")), up(" = "),
         nary("∑", [v("w"), up(" ∈ "), v("V")], None,
              [up("Pr"), delim([up("postoji propusan put od "), v("s"), up(" do "),
                                v("w")], left="[", right="]")]),
         label="reachsum")

    t.p("Svaki pojedini pribrojnik je vjerojatnost da su dva zadana čvora povezana u "
        "slučajnom grafu u kojem svaki brid postoji neovisno o ostalima. To je klasičan "
        "problem pouzdanosti mreže s dva terminala, jedan od prvih problema za koje je "
        "{~valiant1979} pokazao da su #P-potpuni. Riječ je o klasi koja se odnosi na "
        "prebrojavanje, a ne na odlučivanje, i koja je barem toliko teška kao NP. "
        "Vrednovanje jednog reza egzaktno stoga nije izvedivo za mrežu ove veličine.")

    t.p("Isti zaključak stoji i u literaturi o širenju: {~kempe2003} navode da je "
        "učinkovito egzaktno računanje dosega otvoreno pitanje i doseg procjenjuju "
        "simuliranjem slučajnog procesa, a {~kimura2008} iz istog razloga uvode procjenu "
        "temeljenu na uzorkovanju. Postupak koji se ovdje koristi opisan je u odjeljku ", t.sec("procjena"), ".")

    t.h3("Pretraživanje prostora rezova")

    t.p("Broj mogućih rezova je binomni koeficijent")

    t.eq(delim(sub(v("E"), v("s")), left="|", right="|"), up(" nad "), v("k"),
         up(" = "), frac([delim(sub(v("E"), v("s")), left="|", right="|"), up("!")],
                         [v("k"), up("!"),
                          delim([delim(sub(v("E"), v("s")), left="|", right="|"),
                                 up(" − "), v("k")]), up("!")]),
         label="prostor")

    # Order of magnitude computed, not asserted: a retyped exponent is exactly the kind of
    # number that survives a change to the example and quietly stops being true.
    candidates, budget = 20_000, 10
    exponent = len(str(math.comb(candidates, budget))) - 1

    t.p("koji za tipičan izvor u mreži Bitcoin Alpha, kojemu je dohvatljivo oko ",
        hr(candidates), " bridova, već pri ", v("k"), " = ", str(budget), " prelazi ",
        sup(up("10"), up(str(exponent))),
        ". Iscrpno pretraživanje otpada, pa preostaje aproksimacija. Ni ona, međutim, ne "
        "nudi jamstvo: {~castiglioni2021} pokazuju da za problem IMER s konačnim "
        "proračunom ne postoji polinomni algoritam koji bi za bilo koju konstantu ", v("ρ"),
        " dao ", v("ρ"), "-aproksimaciju optimalnog rješenja, osim ako je P = NP. Nije "
        "dakle riječ o tome da dobra aproksimacija još nije pronađena, nego o tome da "
        "aproksimacija s konstantnim jamstvom ne postoji.")

    t.h3("Zašto pohlepni pristup ovdje nema jamstvo")

    t.p("Prirodno je pitanje zašto se ne primijeni isti pohlepni postupak koji kod "
        "maksimizacije utjecaja daje jamstvo ", up("1 − 1/"), v("e"),
        ". Odgovor je da se to jamstvo oslanja na submodularnost funkcije ", v("σ"),
        " nad ", i("početnim skupovima"), " {kempe2003}, a ta se svojstva ne prenose na "
        "funkciju dosega promatranu nad ", i("skupovima uklonjenih bridova"), ".")

    t.p("Razlog je topološka redundantnost, koju ", t.figref("choke"),
        " prikazuje na najmanjem primjeru. Iz izvora vode dva neovisna brida prema istoj "
        "gusto povezanoj regiji. Uklanjanje bilo kojega od njih pojedinačno smanjuje doseg "
        "s osam na sedam čvorova, dakle gotovo ništa, jer kaskada nastavlja teći onim "
        "drugim. Uklanjanje obaju istodobno, pri proračunu ", v("k"),
        " = 2, izvor potpuno izolira i doseg pada na jedan. Doprinos drugog brida time "
        "iznosi šest čvorova ako je prvi već uklonjen, a samo jedan ako nije. Drugim "
        "riječima, doprinos je ", i("veći"),
        " na većem skupu, dok submodularnost zahtijeva upravo suprotno.")

    t.p("Pohlepni postupak, koji bridove bira jedan po jedan i svakog vrednuje zasebno, "
        "takvu sinergiju ne može uočiti: pojedinačno oba brida izgledaju gotovo "
        "bezvrijedno, a vrijedni su tek zajedno. Isti primjer pokazuje i drugu posljedicu "
        "redundantnosti. Ako se putovi nizvodno ponovno spajaju, jedan jedini brid u tom "
        "uskom grlu pri istom proračunu ", v("k"),
        " = 1 smanjuje doseg s osam na četiri, dakle znatno više od bilo kojeg brida uz "
        "sam izvor. Najbolji rez ne mora ležati uz izvor, što je pitanje na koje se rad "
        "vraća u odjeljku ", t.sec("slojevi_sec"), ".")

    t.p("Ista se pojava opaža i kod srodnog cilja: {~tong2012} izričito napominju da "
        "učinak uklanjanja skupa bridova na spektralni polumjer nije jednak zbroju učinaka "
        "uklanjanja pojedinih bridova, zbog čega i oni odustaju od kombinatornog "
        "pretraživanja.")

    t.figure(figures / "fig3_1_choke_point.png",
             "Redundantnost i zajedničko usko grlo. Izvor je dvama neovisnim putovima "
             "povezan s gusto povezanom regijom, pa uklanjanje samo jednoga brida uz izvor "
             "doseg gotovo ne mijenja (sredina), dok uklanjanje jednoga brida u uskom "
             "grlu, uz jednak proračun, odsijeca cijelu regiju (desno). Ispunjeni su "
             "čvorovi oni dohvatljivi iz izvora.",
             label="choke")

    t.p("Iz toga slijedi zahtjev na metodu rješavanja. Postupak koji rješenje gradi "
        "postupno, dodavanjem jednog po jednog brida, strukturno ne može iskoristiti "
        "sinergiju više istodobnih uklanjanja. Potreban je postupak koji u jednom koraku "
        "mijenja više bridova odjednom, što je upravo ono što radi metaheuristika opisana "
        "u petom poglavlju.")


# ------------------------------------------------------------------ 3.4 ----

def _procjena(t):
    t.h2("Procjena dosega uzorkovanjem", label="procjena")

    t.p("Budući da se doseg ne može izračunati egzaktno, cijela se optimizacija vodi nad "
        "njegovom procjenom. Kako je ta procjena istodobno i kriterij po kojem se rješenja "
        "uspoređuju, njezina svojstva izravno određuju što uopće znači da je jedan rez "
        "bolji od drugoga, pa se ovdje definira u cijelosti.")

    t.p("Polazište je ekvivalencija iz odjeljka ", t.sec("icm"), ". Ako se ishodi svih bacanja novčića "
        "fiksiraju unaprijed, dobiva se ", i("live-edge"), " realizacija ", v("X"),
        ", statični podgraf propusnih bridova, a doseg u toj realizaciji je veličina skupa "
        "čvorova dohvatljivih iz izvora. Očekivani je doseg očekivanje te veličine preko "
        "slučajne realizacije. Procjenjuje se prosjekom po uzorku od ", v("M"),
        " neovisno generiranih realizacija:")

    t.eq(acc(v("σ")), delim(v("s"), up(", "), v("D")), up(" = "),
         frac(up("1"), v("M")),
         nary("∑", [v("m"), up(" = 1")], v("M"),
              [delim(ifunc("R", [v("s"), up(", "), sub(v("X"), v("m")), up(" \\ "),
                                 v("D")]), left="|", right="|")]),
         label="saa")

    t.p("gdje je ", ifunc("R", [v("s"), up(", "), sub(v("X"), v("m")), up(" \\ "), v("D")]),
        " skup čvorova dohvatljivih iz ", v("s"),
        " u realizaciji iz koje su uklonjeni bridovi reza. Isti postupak, uz procjenu "
        "temeljenu na perkolaciji bridova, koriste i {~kimura2008}.")

    t.p("Ključna je odluka da se uzorak generira ", i("jednom"),
        " i zatim zamrzne, umjesto da se za svaki kandidatni rez baca novi. Posljedice su "
        "dvije i obje su bitne za ostatak rada:")

    t.bullets([
        ["kriterij postaje determinističan. Isti rez uvijek dobiva istu vrijednost, pa "
         "razlika između dvaju rezova odražava njihovu stvarnu kvalitetu, a ne šum "
         "uzorkovanja. Bez toga pretraživanje ne bi moglo pouzdano usporediti dva bliska "
         "rješenja, jer bi razlika u procjeni često bila manja od kolebanja same procjene;"],
        ["optimum koji se pronađe optimum je uzorka, a ne stvarne funkcije. Rez koji je "
         "najbolji na tih ", v("M"), " realizacija može biti prilagođen upravo njima."],
    ])

    t.p("Druga posljedica traži mjeru opreza, pa se u radu koriste ", i("dva"),
        " odvojena i neovisno generirana skupa realizacija. Uži skup od ",
        count(config.SAA_SCENARIO_COUNT, "realizacije", "realizacije", "realizacija"),
        " služi kao kriterij tijekom pretraživanja, a širi skup od ",
        count(config.MC_SCENARIO_COUNT, "realizacije", "realizacije", "realizacija"),
        " koristi se isključivo za konačno vrednovanje pronađenog reza. Rezultati koji se "
        "u sedmom poglavlju izvještavaju mjereni su na drugom skupu. Razlika između tih "
        "dviju vrijednosti sama je po sebi mjerodavan podatak: pokazuje koliko je rješenje "
        "prilagođeno vlastitom uzorku, pa se bilježi uz svaki rezultat. Način na koji su "
        "skupovi generirani i provjereni opisan je u odjeljku ", t.sec("realizacije"), ".")
