"""8. Mogućnosti poboljšanja i budući rad.

Three sections, each one thing the measurement showed is worth doing next, and each tied
to a source where one is needed: the sigma-greedy to Kimura et al. (2008) and to the lazy-greedy
acceleration of Leskovec et al. (2007), and the estimate to the sample average
approximation literature (Kleywegt et al., 2002).

Section 5.1 promises this chapter will explain why the sigma-greedy was not built and how
it could be, so 8.2 has to deliver exactly that.

Numbers come from the same CSVs and the same helper functions chapter 7 uses; nothing is
retyped. The chapter proposes work rather than reporting it, so it holds few numbers, and
the ones it holds are the costs that justify the proposals.
"""

import sys
from pathlib import Path

import pandas as pd

from omml import acc, delim, frac, i, nary, sub, up, v
from params import config

CODE = Path(__file__).resolve().parent.parent / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from results_analysis import (  # noqa: E402  (path must be set first)
    load_results, runtime_summary, scaled_summary)


def ifunc(name, argument):
    """A function whose name is itself a symbol, as in chapter 3, so R(s, X) keeps its
    name in math italic."""
    return [v(name), delim(argument)]


def _n(value, decimals=3):
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "−")


def _signed(value, decimals=3):
    rounded = round(abs(value), decimals)
    text = f"{rounded:.{decimals}f}".replace(".", ",")
    return text if rounded == 0 else ("+" if value > 0 else "−") + text


def _int(value):
    return f"{int(value):,}".replace(",", ".")


def write(t, figures):
    data = figures.parent / "data"
    results = load_results(data / "results.csv")
    scaled = pd.read_csv(data / "results_scaled.csv")

    t.h1("Mogućnosti poboljšanja i budući rad")
    t.p("Mjerenje iz sedmog poglavlja pokazalo je gdje metoda radi dobro, ali i tri mjesta "
        "na kojima je slabija nego što bi morala biti. Ovo poglavlje opisuje što bi se na "
        "svakome od njih moglo učiniti. Redoslijed prati koliko je pojedini zahvat "
        "obećavajuć: prvi je izravno podržan izmjerenim podacima, drugi bi usporedbu učinio "
        "strožom, a treći bi povećao pouzdanost svih iznesenih brojeva.")

    _allocation(t, results, scaled)
    _sigma_greedy(t)
    _estimate(t)


# ------------------------------------------------------------------ 8.1 ----

def _allocation(t, results, scaled):
    t.h2("Raspodjela truda pretraživanja prema potrebi", label="raspodjela")

    summary = scaled_summary(results, scaled)
    runtime = runtime_summary(results)

    t.p("Metaheuristika u ovom radu izvodi ", str(config.ALNS_MAX_ITER),
        " iteracija na svakoj instanci, bez obzira na to koliko je instanca teška. "
        "Odjeljak ", t.sec("duljina"), " pokazao je da to nije dobra podjela truda. Kada "
        "je broj iteracija povećan, dobitak je bio ", _signed(summary["mean_delta"]),
        " u prosjeku, a cijena ", _n(summary["cost_factor"], 1),
        " puta veće računalno vrijeme. Pritom su gotovo sav dobitak ostvarile instance "
        "koje su i prije bile loše, dok instance koje su već bile dobre nisu dobile ni "
        "stotinku.")

    t.p("Zaključak nije da pretragu treba produljiti svima. Naprotiv: podizanje "
        "zajedničke konstante troši vrijeme uglavnom ondje gdje ono ništa ne donosi. "
        "Bolje je rješenje trud ", i("usmjeriti"),
        " — dati više iteracija samo onim instancama koje ih doista trebaju. Za to je "
        "potrebno prepoznati takvu instancu, a sedmo poglavlje ponudilo je tri pokazatelja.")

    t.bullets([
        ["Kada je pretraga posljednji put pronašla bolje rješenje, izraženo kao udio "
         "ukupnog broja iteracija. Ako je taj udio blizu jedinice, pretraga je još "
         "napredovala kada ju je proračun prekinuo."],
        ["Koliko je instanca uopće postigla. Udio blizu jedinice sam po sebi nije "
         "dovoljan, jer pretraga može napredovati i onda kada je već blizu najboljega "
         "mogućeg rezultata, pa nema što dobiti."],
        ["Nemonotonost po proračunu. Ako rezultat pri većem proračunu padne, pretraga je "
         "sigurno promašila rješenje koje postoji, kako je pokazano u odjeljku ",
         t.sec("proracun"), "."],
    ])

    t.p("Prva su dva pokazatelja korisna tek zajedno: visok udio govori da pretraga nije "
        "završila, a nizak rezultat da je još imala što naći. Treći je pokazatelj "
        "drukčije naravi jer je dokaz, a ne procjena, ali se pojavljuje samo kada je ista "
        "instanca mjerena pri više proračuna. Postoji i četvrti, najjeftiniji: pohlepne "
        "metode izvode se prije metaheuristike i svih šest zajedno troši oko ",
        _n(100 * runtime["baselines_share"], 0),
        " % vremena jednog njezinog pokretanja, pa je njihov raspon poznat prije nego što "
        "pretraga uopće počne. On je, međutim, samo predviđanje, dok su prva dva "
        "pokazatelja opažanja same pretrage, pa su i pouzdanija.")

    t.p("Zaustavljanje pretrage koja dulje vrijeme ne napreduje uobičajen je postupak u "
        "stohastičkom pretraživanju i naziva se kriterijem stagnacije. Ovdje je "
        "predloženi zahvat njegova zrcalna slika: umjesto da se "
        "prekine pretraga koja više ne napreduje, produljuje se ona koja još napreduje. "
        "Dvije su izvedbe moguće. Jednostavnija je u dva prolaza — sve se instance izvedu "
        "uz skroman proračun, a zatim se ponove samo one koje pokazatelji izdvoje. "
        "Zahtjevnija, ali i bolja, jest da pretraga sama produljuje vlastiti proračun dok "
        "napreduje i stane kada se napredak zaustavi. Pri tome treba paziti na shemu "
        "hlađenja iz odjeljka ", t.sec("prihvacanje"),
        ", jer je ona izvedena iz ukupnog broja iteracija {ropke2006}; ako se proračun "
        "mijenja, iz njega treba izvesti i hlađenje, inače bi se pretraga pri kraju "
        "ponašala toplije nego što shema predviđa.")


# ------------------------------------------------------------------ 8.2 ----

def _sigma_greedy(t):
    t.h2("Pohlepna metoda vođena izmjerenim dosegom", label="sigmapohlepna")

    t.p("Kako je rečeno u odjeljku ", t.sec("pohlepne"),
        ", dva pohlepna kriterija u ovom radu odgovaraju heuristikama koje {~kimura2008} "
        "koriste za usporedbu. Metoda koju oni sami predlažu jača je: u svakom koraku bira brid koji "
        "najviše smanjuje ", i("izmjerenu"),
        " procjenu dosega, i to na mreži iz koje su prethodno odabrani bridovi već "
        "uklonjeni. Ona bi bila pravi protivnik metaheuristici i njezino bi uvrštavanje "
        "usporedbu učinilo bitno strožom.")

    t.p("Razlog zbog kojeg ovdje nije izvedena jest cijena. Procjena dosega jednog "
        "kandidata zahtijeva prolazak kroz sve realizacije, a pohlepna metoda takvu "
        "procjenu treba za svaki kandidatni brid u svakom koraku. Kimura i suradnici to "
        "rješavaju domišljatom uštedom: uklanjanje brida mijenja samo one realizacije u "
        "kojima je taj brid uopće bio prohodan, pa se doseg može procijeniti usrednjavanjem "
        "preko preostalih realizacija. Kod njih ta ušteda funkcionira jer je vjerojatnost "
        "prijenosa niska i jednaka za sve bridove, pa velika većina realizacija ostaje "
        "upotrebljiva.")

    t.p("Na mreži Bitcoin Alpha ta pretpostavka ne vrijedi. Vjerojatnost prijenosa nije "
        "jednaka za sve bridove i doseže vrijednosti blizu jedinice (odjeljak ",
        t.sec("skup"), "), pa bi za takav brid od ", str(config.SAA_SCENARIO_COUNT),
        " realizacija ostalo svega nekoliko upotrebljivih. Nevolja je u tome što su upravo "
        "bridovi visoke vjerojatnosti oni koje se najviše isplati presjeći, pa bi ušteda "
        "otkazala točno ondje gdje je najpotrebnija. To nije nedostatak njihove metode nego "
        "posljedica prijenosa na mrežu s neujednačenim vjerojatnostima, i vrijedi ga "
        "zabilježiti kao nalaz.")

    t.p("Postoji, međutim, preinaka koja čuva njihovu zamisao bez gubitka uzorka. "
        "Realizacije se podijele u dvije skupine: one u kojima brid ", v("e"),
        " nije prohodan i one u kojima jest. Procjena dosega tada se može zapisati kao")

    t.eq(acc(v("σ")), delim([v("D"), up(" ∪ {"), v("e"), up("}")]), up(" = "),
         frac([up("1")], [v("M")]),
         delim([
             nary("∑", [v("m"), up(" : "), v("e"), up(" ∉ "), sub(v("X"), v("m"))], None,
                  [delim(ifunc("R", [v("s"), up(", "), sub(v("X"), v("m")),
                                     up(" \\ "), v("D")]), left="|", right="|")]),
             up(" + "),
             nary("∑", [v("m"), up(" : "), v("e"), up(" ∈ "), sub(v("X"), v("m"))], None,
                  [delim(ifunc("R", [v("s"), up(", "), sub(v("X"), v("m")), up(" \\ "),
                                     delim([v("D"), up(" ∪ {"), v("e"), up("}")])]),
                         left="|", right="|")]),
         ], left="[", right="]"),
         label="sigmagreedy")

    t.p("U izrazu ", t.ref("sigmagreedy"), " prvi zbroj ne ovisi o bridu ", v("e"),
        ", pa se dobiva iz jednog jedinog osnovnog prolaska; ponovno se računa samo drugi, "
        "i to na udjelu realizacija razmjernom vjerojatnosti toga brida. Postupak je time "
        "točan i koristi cijeli uzorak, a trošak mu raste s vjerojatnošću brida umjesto da "
        "o njoj propada. Kako je posve determinističan, rezultat bi se za svaki par izvora "
        "i proračuna izračunao jednom i ponovno upotrijebio.")

    t.p("Vrijedi spomenuti i uobičajeno ubrzanje pohlepnih metoda u srodnim problemima. "
        "{~leskovec2007} predlažu postupak koji izbjegava ponovno vrednovanje svakog "
        "kandidata u svakom koraku tako da se oslanja na svojstvo padajućih prinosa, "
        "odnosno submodularnost. Taj se postupak ovdje ne može izravno preuzeti: doseg "
        "kao funkcija ", i("skupa uklonjenih bridova"),
        " nije submodularan, što je pokazano u odjeljku ", t.sec("slozenost"),
        ". Ograničenje je dakle stvarno i ne treba ga zaobići prešutno — ubrzanje opisano "
        "gore ne oslanja se na submodularnost nego na strukturu realizacija, pa ostaje "
        "primjenjivo.")


# ------------------------------------------------------------------ 8.3 ----

def _estimate(t):
    t.h2("Pouzdanija procjena i višestruka sjemena", label="pouzdanost")

    t.p("Odjeljak ", t.sec("valjanost"),
        " pokazao je da rezultat izmjeren na zamrznutom uzorku realizacija u pravilu bude "
        "nešto bolji od onoga izmjerenog na neovisnom uzorku. To nije neočekivano. Riječ je "
        "o poznatoj pojavi kod postupka poznatog kao aproksimacija uzorkovanjem "
        "(engl. ", i("sample average approximation"),
        "), u kojem se očekivana vrijednost zamijeni prosjekom po konačnom uzorku, a zatim "
        "se optimira taj prosjek {kleywegt2002}. Rješenje pronađeno na jednom uzorku "
        "prilagođeno je i njegovim slučajnostima, pa je procjena na tom istom uzorku "
        "sustavno preoptimistična.")

    t.p("U ovom je radu ta pojava izmjerena tako da se rezultat provjeri na jednom većem "
        "neovisnom uzorku od ", str(config.MC_SCENARIO_COUNT),
        " realizacija. To je dovoljno da se pokaže da pojava postoji i koliko je velika, "
        "ali ne daje ocjenu njezine nesigurnosti. Postupak koji to omogućuje opisan je u "
        "istom radu: optimizacija se ponovi na više ", i("neovisnih"),
        " uzoraka jednake veličine, pa se iz raspršenja dobivenih rješenja procijeni "
        "razlika do pravog optimuma. Cijena je izravna: pretraživanje se izvodi onoliko "
        "puta koliko ima uzoraka.")

    t.p("Uz to bi vrijedilo provjeriti i same realizacije. Svaka je realizacija podgraf "
        "polazne mreže dobiven zadržavanjem svakog brida s njegovom vjerojatnošću "
        "(odjeljak ", t.sec("realizacije"),
        "), pa je razumno izmjeriti koliko takav podgraf uopće nalikuje polaznoj mreži: "
        "koliki udio bridova preživi, ostaje li velika povezana komponenta i koliko se ta "
        "svojstva razlikuju od realizacije do realizacije. Ta provjera ne mijenja metodu, "
        "ali potkrepljuje pretpostavku na kojoj počiva cijelo mjerenje.")

    t.p("Naposljetku, sva su mjerenja u ovom radu izvedena uz jedno sjeme generatora "
        "slučajnih brojeva. To je dovoljno za ponovljivost, ali ne i za ocjenu koliko "
        "rezultat ovisi o slučajnim izborima unutar pretrage, osobito o izboru među "
        "jednako ocijenjenim bridovima, kojih na ovoj mreži ima mnogo (odjeljak ",
        t.sec("izjednacenost"),
        "). Ponavljanje svake instance s više sjemena pretvorilo bi svaki rezultat iz jedne "
        "vrijednosti u raspodjelu, što je za stohastičko pretraživanje primjereniji opis. "
        "Raspršenje bi se tada iskazalo kao svojstvo metode, a ne usrednjilo.")
