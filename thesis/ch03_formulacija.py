"""3. Formulacija problema SS-IMER.

Sources: Kempe et al. (2003) for influence maximization, its NP-hardness and the
submodularity that licenses the greedy guarantee; Kimura et al. (2008) for the
contamination minimization problem and its exact-cardinality budget; Castiglioni et al.
(2021) for the IMER definition and the inapproximability result; Valiant (1979) for the
#P-completeness of two-terminal reliability; Tong et al. (2012) for the non-additivity of
edge removal.

Four sections, matching the agreed structure. The chapter states what the problem is and
why it is hard; it does not narrate how the formulation was arrived at.
"""

import math

from omml import acc, delim, frac, i, limlow, nary, sub, sup, up, v
from params import config, count


def ifunc(name, argument):
    """A function whose name is itself a symbol - sigma(s, G), R(s, X) - so the name stays
    in math italic, unlike arg min which is set upright."""
    return [v(name), delim(argument)]


def sigma(*parts):
    return ifunc("σ", list(parts))


def write(t, figures):
    t.h1("Formulacija problema SS-IMER")

    t.p("Prethodna dva poglavlja opisala su model širenja i mrežu na kojoj se on odvija. "
        "Ovo poglavlje postavlja optimizacijski problem koji se u radu rješava: što se "
        "zadaje, što se traži, zašto je to teško i kako se mjeri vrijednost jednog "
        "kandidatnog rješenja.")

    _srodni(t)
    _definicija(t)
    _slozenost(t, figures)
    _procjena(t)


# ------------------------------------------------------------------ 3.1 ----

def _srodni(t):
    t.h2("Temeljni problemi optimizacije utjecaja")

    t.p("Problemi koji se u literaturi razmatraju pod zajedničkim nazivom optimizacije "
        "utjecaja dijele istu strukturu: zadan je model širenja i proračun kojim se smije "
        "zahvatiti u mrežu, a traži se skup elemenata čija izmjena najviše mijenja doseg "
        "kaskade. Razlikuju se po tome što se mijenja, u kojem smjeru i iz čije "
        "perspektive se doseg mjeri.")

    t.p("Ishodišni je problem maksimizacija utjecaja koju formuliraju {~kempe2003}: za "
        "zadani proračun ", v("k"), " traži se početni skup od ", v("k"),
        " čvorova koji maksimizira očekivani broj aktiviranih čvorova. Autori pokazuju da "
        "je problem NP-težak, ali i da funkcija dosega nad početnim skupovima ima dva "
        "svojstva koja zajedno spašavaju situaciju: monotona je, jer dodavanje čvora u "
        "početni skup ne može smanjiti doseg, i submodularna, jer je doprinos novog čvora "
        "to manji što je početni skup veći. Za takve funkcije pohlepni postupak daje "
        "rješenje unutar faktora ", up("1 − 1/"), v("e"),
        " od optimalnog {kempe2003}, zbog čega je taj pristup u ovom području postao "
        "uobičajen.")

    t.p("Zrcalni je problem sprječavanje širenja. Ono se može izvesti uklanjanjem čvorova, "
        "čime {~albert2000} pokazuju krhkost mreža bez skale, ili uklanjanjem bridova. "
        "Uklanjanje brida blaža je intervencija jer ne uklanja sudionika iz mreže nego "
        "samo jedan kanal među dvama sudionicima {tong2012}, pa je u primjenama u kojima "
        "su sudionici stvarni korisnici često i jedina izvediva.")

    t.p("Dva su takva problema izravni preteče ovoga rada. {~kimura2008} definiraju problem "
        "minimizacije kontaminacije, u kojem se minimizira prosječan doseg preko svih "
        "čvorova mreže kao mogućih izvora,")

    t.eq(ifunc("c", v("G")), up(" = "),
         frac(up("1"), delim(v("V"), left="|", right="|")),
         nary("∑", [v("w"), up(" ∈ "), v("V")], None,
              [sigma(v("w"), up("; "), v("G"))]),
         label="kontaminacija")

    t.p("uklanjanjem točno ", v("k"), " bridova. {~castiglioni2021} definiraju problem ",
        i("Influence-Minimization-by-Edge-Removal"), " (IMER), u kojem se za zadani graf, "
        "zadani skup početnih čvorova i proračun ", v("B"), " traži skup od najviše ",
        v("B"), " bridova koji maksimizira pad broja dosegnutih čvorova.")

    t.p("Problem koji se ovdje rješava uža je varijanta te obitelji, određena trima "
        "odlukama: izvor je jedan jedini i unaprijed poznat, umjesto skupa početnih "
        "čvorova {castiglioni2021} ili prosjeka preko svih čvorova {kimura2008}; proračun "
        "se troši u cijelosti, kao kod {~kimura2008}; i mijenjaju se isključivo bridovi. "
        "Prva odluka odgovara praktičnoj situaciji u kojoj je sumnjivi korisnik već "
        "prepoznat. Radi kratkoće se u nastavku koristi oznaka SS-IMER, koja je, kako je "
        "rečeno u uvodu, uvedena u ovom radu.")


# ------------------------------------------------------------------ 3.2 ----

def _definicija(t):
    t.h2("Matematička definicija problema", label="definicija")

    t.p("Neka je ", v("G"), " = ", delim(v("V"), up(", "), v("E")), " usmjeren graf i "
        "neka svakom bridu ", v("e"), " = ", delim(v("u"), up(", "), v("w")),
        " pripada vjerojatnost prijenosa ", sub(v("p"), v("e")), " ∈ ",
        delim(up("0, 1"), left="(", right="]"), ", određena preslikavanjem iz odjeljka ",
        t.sec("skup"), ". Neka je ", v("s"), " ∈ ", v("V"),
        " zadani izvor. Za skup bridova ", v("D"), " ⊆ ", v("E"), " oznaka ", v("G"),
        " \\ ", v("D"), " označava graf ",
        delim(v("V"), up(", "), [v("E"), up(" \\ "), v("D")]),
        ", dakle mrežu bez tih bridova; skup ", v("D"), " naziva se rezom.")

    t.p("Očekivani doseg ", sigma(v("s"), up(", "), v("G")),
        " je očekivani broj čvorova aktivnih na kraju procesa iz odjeljka ", t.sec("icm"),
        " ako je na početku aktivan samo čvor ", v("s"),
        ". Problem SS-IMER glasi: za zadane ", v("G"), ", ", v("s"),
        " i cjelobrojni proračun ", v("k"), " pronaći")

    t.eq(sup(v("D"), up("*")), up(" = "),
         limlow(up("arg min"),
                [v("D"), up(" ⊆ "), sub(v("E"), v("s")), up(",  "),
                 delim(v("D"), left="|", right="|"), up(" = "), v("k")]),
         sigma(v("s"), up(", "), [v("G"), up(" \\ "), v("D")]),
         label="ssimer")

    t.p("Skup kandidata ", sub(v("E"), v("s")),
        " nisu svi bridovi mreže, nego samo oni čiji je početni čvor dohvatljiv iz ",
        v("s"), ". Brid do čijeg početnog čvora kaskada ne može doći ne može ni prenijeti "
        "aktivaciju, pa njegovo uklanjanje ne mijenja doseg ni u jednoj realizaciji; to "
        "ograničenje dakle ne isključuje nijedno rješenje.")

    t.p("Uvjet ", delim(v("D"), left="|", right="|"), " = ", v("k"),
        " ne gubi na općenitosti u odnosu na blaži uvjet ",
        delim(v("D"), left="|", right="|"), " ≤ ", v("k"),
        ", jer je doseg nerastuća funkcija reza: uklanjanjem dodatnog brida nijedan put ne "
        "nastaje, pa se svako rješenje s manje od ", v("k"), " bridova može nadopuniti do ",
        v("k"), " bez pogoršanja.")

    t.p("Za usporedbu različitih izvora potrebna je mjera neovisna o njihovoj veličini, "
        "jer se doseg među izvorima razlikuje za tri reda veličine (odjeljak ",
        t.sec("populacija"), "). Koristi se relativno smanjenje dosega")

    t.eq(ifunc("R", v("D")), up(" = 1 − "),
         frac(sigma(v("s"), up(", "), [v("G"), up(" \\ "), v("D")]),
              sub(v("σ"), up("0"))),
         up(",       "), sub(v("σ"), up("0")), up(" = "), sigma(v("s"), up(", "), v("G")),
         label="reduction")

    t.p("pri čemu je ", sub(v("σ"), up("0")), " doseg neizmijenjene mreže, a veće "
        "vrijednosti znače uspješniju intervenciju.")

    t.p("Iz definicije slijedi i jedan rubni slučaj koji nije pogreška nego instanca s "
        "poznatim rješenjem. Ako je ", v("k"), " ≥ ", ifunc("out", v("s")),
        ", mogu se presjeći svi bridovi koji izlaze iz izvora; izvor time postaje izoliran, "
        "doseg pada na jedan, jer izvor uvijek broji sam sebe, i to je ujedno globalni "
        "optimum. Takve se instance rješavaju bez pretraživanja i posebno označuju, kako "
        "ne bi ušle u prosjeke u kojima bi jednako polaskale svakoj metodi.")


# ------------------------------------------------------------------ 3.3 ----

def _slozenost(t, figures):
    t.h2("Složenost problema", label="slozenost")

    t.p("Problem je težak na dvije odvojene razine, i korisno ih je razlikovati jer traže "
        "različite odgovore: teško je vrednovati i jedan jedini kandidatni rez, a teško je "
        "i pretražiti prostor svih rezova.")

    t.p("Prema ekvivalenciji iz odjeljka ", t.sec("icm"),
        " očekivani se doseg može zapisati kao zbroj vjerojatnosti po čvorovima:")

    t.eq(sigma(v("s"), up(", "), v("G")), up(" = "),
         nary("∑", [v("w"), up(" ∈ "), v("V")], None,
              [up("Pr"), delim([up("postoji propusan put od "), v("s"), up(" do "),
                                v("w")], left="[", right="]")]),
         label="reachsum")

    t.p("Svaki je pribrojnik vjerojatnost da su dva zadana čvora povezana u slučajnom grafu "
        "u kojem svaki brid postoji neovisno o ostalima. To je problem pouzdanosti mreže s "
        "dva terminala, jedan od prvih problema za koje je {~valiant1979} pokazao da su "
        "#P-potpuni, dakle barem toliko teški kao NP-potpuni problemi. Egzaktno vrednovanje "
        "jednog reza stoga nije izvedivo na mreži ove veličine, što je i razlog zbog kojeg "
        "{~kempe2003} doseg procjenjuju simulacijom, a {~kimura2008} uzorkovanjem.")

    # Order of magnitude computed rather than asserted, so a change to the example cannot
    # leave a stale exponent behind in the text.
    candidates, budget = 20_000, 10
    exponent = len(str(math.comb(candidates, budget))) - 1

    t.p("Druga je razina kombinatorna. Broj mogućih rezova je binomni koeficijent ",
        delim([delim(sub(v("E"), v("s")), left="|", right="|"), up(" nad "), v("k")]),
        ", koji za tipičan izvor u ovoj mreži, kojemu je dohvatljivo oko dvadeset tisuća "
        "bridova, već pri ", v("k"), " = ", str(budget), " prelazi ",
        sup(up("10"), up(str(exponent))),
        ". Iscrpno pretraživanje otpada, a ni aproksimacija ne nudi jamstvo: "
        "{~castiglioni2021} pokazuju da za problem IMER s konačnim proračunom ne postoji "
        "polinomni algoritam koji bi za bilo koju konstantu ", v("ρ"), " dao ", v("ρ"),
        "-aproksimaciju optimuma, osim ako je P = NP. Nije dakle riječ o tome da dobra "
        "aproksimacija još nije pronađena, nego o tome da aproksimacija s konstantnim "
        "jamstvom ne postoji.")

    t.p("Postavlja se pitanje zašto se onda ne primijeni pohlepni postupak koji kod "
        "maksimizacije utjecaja daje jamstvo ", up("1 − 1/"), v("e"),
        ". Odgovor je da se to jamstvo oslanja na submodularnost dosega nad ",
        i("početnim skupovima"), " {kempe2003}, a to se svojstvo ne prenosi na doseg "
        "promatran nad ", i("skupovima uklonjenih bridova"), ".")

    t.p("Razlog je topološka redundantnost, koju ", t.figref("choke"),
        " prikazuje na najmanjem primjeru. Iz izvora vode dva neovisna brida prema istoj "
        "gusto povezanoj regiji: uklanjanje bilo kojega od njih smanjuje doseg s osam na "
        "sedam čvorova, dakle gotovo ništa, jer kaskada nastavlja teći onim drugim, dok "
        "uklanjanje obaju izvor potpuno izolira. Doprinos drugog brida time je ", i("veći"),
        " kada je prvi već uklonjen, dok submodularnost zahtijeva upravo suprotno. "
        "Pohlepni postupak, koji bridove bira jedan po jedan i svakog vrednuje zasebno, "
        "takvu sinergiju ne može uočiti: pojedinačno oba brida izgledaju bezvrijedno, a "
        "vrijedna su tek zajedno. Do iste pojave dolazi i kod srodnog cilja, pa "
        "{~tong2012} napominju da učinak uklanjanja skupa bridova nije jednak zbroju "
        "učinaka uklanjanja pojedinih bridova.")

    t.p("Isti primjer pokazuje i drugu posljedicu redundantnosti. Ako se putovi nizvodno "
        "ponovno spajaju, jedan jedini brid u tom uskom grlu pri istom proračunu smanjuje "
        "doseg s osam na četiri, dakle znatno više od bilo kojeg brida uz sam izvor. "
        "Najbolji rez, drugim riječima, ne mora ležati uz izvor.")

    t.figure(figures / "fig3_1_choke_point.png",
             "Redundantnost i zajedničko usko grlo. Izvor je dvama neovisnim putovima "
             "povezan s gusto povezanom regijom, pa uklanjanje jednoga brida uz izvor "
             "doseg gotovo ne mijenja (sredina), dok uklanjanje jednoga brida u uskom "
             "grlu, uz jednak proračun, odsijeca cijelu regiju (desno). Ispunjeni su "
             "čvorovi oni dohvatljivi iz izvora.",
             label="choke")

    t.p("Iz oba svojstva slijedi zahtjev na metodu rješavanja: potreban je postupak koji u "
        "jednom koraku mijenja više bridova odjednom i koji nije unaprijed ograničen na "
        "neposrednu okolinu izvora. Takva je metoda opisana u petom poglavlju.")


# ------------------------------------------------------------------ 3.4 ----

def _procjena(t):
    t.h2("Procjena dosega", label="procjena")

    t.p("Budući da se doseg ne može izračunati egzaktno, cijela se optimizacija vodi nad "
        "njegovom procjenom. Kako je ta procjena ujedno i kriterij po kojem se rješenja "
        "uspoređuju, njezina svojstva određuju što uopće znači da je jedan rez bolji od "
        "drugoga, pa se ovdje definira u cijelosti.")

    t.p("Polazište je ekvivalencija iz odjeljka ", t.sec("icm"),
        ". Ako se ishodi svih bacanja novčića fiksiraju unaprijed, dobiva se ",
        i("live-edge"), " realizacija ", v("X"),
        ", statični podgraf propusnih bridova, a doseg u toj realizaciji jednak je "
        "veličini skupa čvorova dohvatljivih iz izvora. Očekivani je doseg očekivanje te "
        "veličine, a procjenjuje se prosjekom po uzorku od ", v("M"),
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
        "dvije i obje su bitne za ostatak rada. Prvo, kriterij postaje determinističan: "
        "isti rez uvijek dobiva istu vrijednost, pa razlika između dvaju rezova odražava "
        "njihovu kvalitetu, a ne šum uzorkovanja. Bez toga pretraživanje ne bi moglo "
        "pouzdano usporediti dva bliska rješenja, jer bi razlika u procjeni često bila "
        "manja od kolebanja same procjene. Drugo, pronađeni je optimum optimum ",
        i("uzorka"), ", a ne stvarne funkcije, pa rez koji je najbolji na tih ", v("M"),
        " realizacija može biti prilagođen upravo njima.")

    t.p("Druga posljedica traži mjeru opreza, pa se koriste ", i("dva"),
        " odvojena i neovisno generirana skupa realizacija. Uži skup od ",
        count(config.SAA_SCENARIO_COUNT, "realizacije", "realizacije", "realizacija"),
        " služi kao kriterij tijekom pretraživanja, a širi skup od ",
        count(config.MC_SCENARIO_COUNT, "realizacije", "realizacije", "realizacija"),
        " isključivo za konačno vrednovanje pronađenog reza. Razlika između tih dviju "
        "vrijednosti sama je po sebi mjerodavan podatak, jer pokazuje koliko je rješenje "
        "prilagođeno vlastitom uzorku, pa se bilježi uz svaki rezultat. Način na koji su "
        "skupovi generirani i provjereni opisan je u odjeljku ", t.sec("realizacije"), ".")
