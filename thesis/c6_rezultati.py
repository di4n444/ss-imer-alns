"""6. Rezultati i rasprava.

Every number is computed from data/results.csv and data/results_scaled.csv at build time,
by the same functions the result figures use (code/results_analysis.py). Nothing is
retyped.

Five sections, one per question the measurement can answer, in the order the answers
depend on each other. Validity comes first because it fixes the floor below which no
difference is decisive; the method comparison then has to be read against that floor, and
6.2 says so rather than letting a reader notice it.
"""

import sys
from pathlib import Path

import pandas as pd

from omml import v

CODE = Path(__file__).resolve().parent.parent / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from results_analysis import (  # noqa: E402  (path must be set first)
    CRITERIA, comparison_cells, comparison_table, deep_shedding, gap_summary, hop_summary,
    load_results, oracle_summary, prior_band, scaled_summary, stratified)

NAMES = {
    "probability": "vjerojatnost prijenosa",
    "degree": "zbroj stupnjeva",
    "betweenness": "međupoloženost",
    "spectral": "spektralni",
    "bridge": "lokalni most",
    "random": "slučajni odabir",
}


def _n(value, decimals=3):
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "−")


def _signed(value, decimals=3):
    """A signed number. One that rounds to zero loses its sign, since "−0,000" reads as a
    negative quantity when it is really the absence of one."""
    rounded = round(abs(value), decimals)
    text = f"{rounded:.{decimals}f}".replace(".", ",")
    if rounded == 0:
        return text
    return ("+" if value > 0 else "−") + text


def _int(value):
    return f"{int(round(value)):,}".replace(",", ".")


def _count(value, one, few, many):
    """Croatian numeral agreement: 1 instanca, 43 instance, 95 instanci."""
    n = int(value)
    if 11 <= n % 100 <= 14:
        return f"{_int(n)} {many}"
    last = n % 10
    if last == 1:
        return f"{_int(n)} {one}"
    if last in (2, 3, 4):
        return f"{_int(n)} {few}"
    return f"{_int(n)} {many}"


def _instances(value):
    return _count(value, "instanca", "instance", "instanci")


def write(t, figures):
    data = figures.parent / "data"
    results = load_results(data / "results.csv")
    scaled = pd.read_csv(data / "results_scaled.csv")

    t.h1("Rezultati i rasprava", label="rezultati")
    cells = comparison_cells(results)
    t.p("Mjerenje obuhvaća ", _int(len(cells)), " instanci, pri čemu je instanca jedan par "
        "izvora i proračuna riješen svim pohlepnim kriterijima i metaheuristikom. "
        "Rezultate ne iznosimo kao jedan prosjek, nego razdvojeno, po pitanjima na koja "
        "mjerenje uistinu može odgovoriti. Prosjek preko svega odjednom ne bi odgovorio ni "
        "na jedno od njih, jer instance obuhvaćaju izvore čiji se doseg razlikuje za tri "
        "reda veličine.")

    _validity(t, figures, results)
    _comparison(t, results)
    _budget(t, figures, results)
    _length(t, figures, results, scaled)
    _distance(t, results, scaled)


# -- 6.1 ---------------------------------------------------------------------

def _validity(t, figures, results):
    t.h2("Valjanost procjene", label="valjanost")

    gap = gap_summary(results)
    t.p("Pretraga optimira doseg na zamrznutom skupu realizacija, a izvještava se "
        "vrijednost izmjerena na neovisnom skupu. Razlika te dvije vrijednosti mjeri "
        "koliko je pronađeni rez prilagođen vlastitom uzorku, pa je čitamo prije svake "
        "usporedbe metoda: ona određuje ispod koje razlike dvije metode nema smisla "
        "razlikovati.")

    t.p("Medijan razlike iznosi ", _signed(gap["median"]), ", uz međukvartilni raspon od ",
        _signed(gap["q1"]), " do ", _signed(gap["q3"]), ". ", t.figref("uzorak"),
        " prikazuje istu stvar po instanci. Bitno je da nijedna pohlepna metoda nema "
        "medijan veći od ", _signed(gap["worst_baseline_median"]),
        ". Procjenitelj je za sve metode isti, pa razlika ne dolazi od njega nego od "
        "pretrage: pohlepne metode uzorak nikada ne gledaju, pa mu se nemaju čemu ni "
        "prilagoditi. Prilagođenost uzorku je, dakle, cijena pretraživanja.")

    t.p("Praktična je posljedica jednostavna. Razlike reda nekoliko stotinki nisu za ovaj "
        "problem odlučujuće, i to vrijedi za svaku usporedbu u nastavku poglavlja.")

    t.figure(figures / "fig7_1_saa_mc.png",
             "Relativno smanjenje dosega na zamrznutom i na neovisnom skupu realizacija, "
             "po instanci. Točke ispod dijagonale precijenjene su na vlastitom uzorku.",
             label="uzorak", width_cm=12.0)


# -- 6.2 ---------------------------------------------------------------------

def _comparison(t, results):
    t.h2("Usporedba metoda", label="usporedba")

    table = comparison_table(results)
    cells = comparison_cells(results)
    rows = [[NAMES[r.criterion], f"{r.better} / {r.tied} / {r.worse}",
             _signed(r.mean_delta), _n(r.mean_R)] for r in table.itertuples()]

    t.p(t.tabref("usporedbatab"), " prikazuje metaheuristiku naspram svakoga kriterija "
        "zasebno. Usporedba je namjerno po kriteriju, a ne prema najboljem od njih, jer "
        "najbolji kriterij po instanci nije metoda koju bi itko mogao primijeniti: on se "
        "bira unatrag, kada je rezultat već poznat.")

    t.table(
        ["Kriterij", "Bolje / neriješeno / lošije", "Prosječna razlika",
         "Prosječni R kriterija"],
        rows,
        "Metaheuristika ALNS naspram svakoga pohlepnog kriterija zasebno, po " +
        _int(len(cells)) + " instanci. Razlika je izražena u relativnom smanjenju dosega.",
        label="usporedbatab", widths_cm=[3.8, 4.2, 3.2, 3.8])

    prob = table[table.criterion == "probability"].iloc[0]
    t.p("Nalaz treba iznijeti onako kako stoji. Metaheuristika nadmašuje pet od šest "
        "kriterija uvjerljivo, ali jedini pravi protivnik je vjerojatnost prijenosa, i "
        "ondje prosječna prednost iznosi svega ", _signed(prob.mean_delta),
        ". To je isti red veličine kao prilagođenost uzorku iz odjeljka ",
        t.sec("valjanost"), ", pa se na temelju samog prosjeka ne bi smjelo tvrditi da je "
        "jedna metoda bolja. Da je vjerojatnost prijenosa najjači kriterij nije "
        "iznenađenje: odjeljak ", t.sec("uskogrlo"), " objasnio je zašto topologija "
        "osnovnog grafa ovdje ne razlikuje bridove, pa preostaje jedino to koliko je često "
        "kanal uopće otvoren.")

    t.p("Prosjek ipak nije jedini dokaz. Omjer pobjeda i poraza iznosi ", str(prob.better),
        " naprama ", str(prob.worse), " uz ", str(prob.tied),
        " neriješenih, što nije slika izjednačenih metoda. Još je važnije da se prednost "
        "ne raspoređuje ravnomjerno.")

    reach = stratified(results, "sigma0", [0, 100, 400, 10 ** 9],
                       ["10 do 100", "100 do 400", "zasićeni izvori"])
    t.table(
        ["Razred dosega izvora", "Instanci", "R metaheuristike", "R vjerojatnosti",
         "Razlika"],
        [[str(r.stratum), str(r.cells), _n(r.alns_mean_R), _n(r.other_mean_R),
          _signed(r.mean_delta)] for r in reach.itertuples()],
        "Metaheuristika naspram vjerojatnosti prijenosa, razdvojeno po početnom dosegu "
        "izvora.",
        label="raslojeno", widths_cm=[3.6, 2.0, 3.2, 3.2, 2.8])

    t.p("Prednost je jasna na izvorima srednjeg dosega, a negativna postaje tek na "
        "zasićenima, koji čine većinu uzorka i zato povlače ukupni prosjek prema nuli. U "
        "odjeljku ", t.sec("duljina"), " pokazuje se da su upravo te instance one kojima "
        "zadani broj iteracija nije dovoljan, pa usporedba metoda i pitanje duljine "
        "pretrage nisu dvije priče nego jedna.")

    oracle = oracle_summary(results)
    t.p("Naposljetku, vrijedi navesti gornju ogradu. Uzmemo li za svaku instancu najbolji "
        "od šest kriterija, dakle biramo li pobjednika unatrag, prosječni relativni "
        "rezultat iznosi ", _n(oracle["oracle_mean_R"], 4), ", dok metaheuristika postiže ",
        _n(oracle["alns_mean_R"], 4), ". Razlika je manja od tisućinke, a metaheuristika tu "
        "ogradu dostiže ili nadmašuje na ", str(oracle["alns_at_least"]), " od ",
        str(oracle["cells"]), " instanci. Jedna pretraga bez ikakva predznanja o instanci "
        "time postiže otprilike ono što bi postiglo unaprijedno znanje o tome koji "
        "kriterij na kojoj instanci pobjeđuje. To je najjača tvrdnja koju mjerenje "
        "podupire i treba je iznijeti upravo tako usko.")


# -- 6.3 ---------------------------------------------------------------------

def _budget(t, figures, results):
    t.h2("Ovisnost o proračunu", label="proracun")

    t.p("Dosadašnje su usporedbe pomiješale male i velike proračune. ",
        t.figref("proracunsl"), " prikazuje relativno smanjenje dosega u ovisnosti o "
        "proračunu, po izvoru zasebno, jer isti broj bridova kod izvora s trideset izlaznih "
        "veza znači nešto sasvim drugo nego kod onoga s devedeset.")

    t.figure(figures / "fig7_2_k_sweep.png",
             "Relativno smanjenje dosega u ovisnosti o proračunu, po izvoru. Gornja os "
             "prikazuje udio proračuna u izlaznom stupnju izvora.",
             label="proracunsl", width_cm=13.5)

    t.p("Jedna je pojedinost na tim krivuljama vrijedna posebne pažnje, jer je sama sebi "
        "dokaz. Rezultat metaheuristike na jednom mjestu pada kada proračun poraste, a to "
        "optimalno rješenje ne može učiniti: rez veličine ", v("k"),
        " − 1 uvijek se može dopuniti još jednim bridom, pa optimum s proračunom ne smije "
        "padati. Pad je stoga siguran znak da optimum nije pronađen, i za taj zaključak "
        "nije potrebno poznavati točno rješenje niti imati jačeg protivnika. Nijedna "
        "pohlepna metoda ne pokazuje takav pad, jer one ne pretražuju nego rangiraju.")


# -- 6.4 ---------------------------------------------------------------------

def _length(t, figures, results, scaled):
    t.h2("Duljina pretrage", label="duljina")

    summary = scaled_summary(results, scaled)
    t.p("Dio je instanci ponovno pokrenut uz proračun iteracija vezan uz veličinu "
        "problema, umjesto uz fiksnu vrijednost. Od ", _instances(summary["more"]),
        " koje su uistinu dobile više iteracija, njih se ", str(summary["improved"]),
        " popravilo, ", str(summary["unchanged"]), " ih je ostalo nepromijenjeno, a ",
        str(summary["worse"]), " ih se pogoršalo. Prosječna promjena iznosi ",
        _signed(summary["mean_delta"]), ", a najbolja pojedinačna ",
        _signed(summary["best_delta"]), ".")

    bands = summary["bands"]
    t.table(
        ["Kako je instanca stajala prije", "Instanci", "Prosječna promjena"],
        [[r.band, str(r.cells), _signed(r.mean_delta)] for r in bands.itertuples()],
        "Promjena relativnog smanjenja dosega nakon produljenja pretrage, razvrstana po "
        "tome kako je instanca stajala prije toga.",
        label="duljinatab", widths_cm=[6.5, 2.5, 4.0])

    t.p("Obrazac je jednosmjeran: što je instanca prije stajala lošije, to joj dulja "
        "pretraga više donosi, dok one koje su već bile dobre ne dobivaju gotovo ništa. ",
        t.figref("duljinasl"), " prikazuje isto po instanci. Cijena je pritom bila ",
        _n(summary["cost_factor"], 1), " puta više računanja za prosječni dobitak od ",
        _signed(summary["mean_delta"]), ", raspoređen vrlo neravnomjerno. To je argument "
        "protiv globalnog podizanja broja iteracija i za njegovu raspodjelu prema potrebi, "
        "o čemu govori poglavlje ", t.sec("poboljsanja"), ".")

    t.figure(figures / "fig7_3_scaled_gain.png",
             "Promjena relativnog smanjenja dosega nakon produljenja pretrage, po "
             "instanci, u ovisnosti o rezultatu prije produljenja.",
             label="duljinasl", width_cm=12.0)

    t.p("Dvije ograde treba navesti. Instance za ponovno pokretanje birane su kao "
        "najjeftinije u svojoj skupini, a jeftino se poklapa s time da je pretraga već bila "
        "završila, pa mjerenje govori o tipičnoj instanci, a ne o onoj koja se muči. "
        "Nadalje, ", _instances(summary["worse"]), " duljom je pretragom postalo lošije, "
        "što nije šum: dulja pretraga jače prianja uz zamrznuti uzorak, pa rez prilagođen "
        "njemu na neovisnom skupu može proći slabije. To je ista pojava koju odjeljak ",
        t.sec("valjanost"), " mjeri, viđena s druge strane.")


# -- 6.5 ---------------------------------------------------------------------

def _distance(t, results, scaled):
    t.h2("Udaljenost korisnih bridova od izvora", label="udaljenost")

    hop = hop_summary(results)
    share = hop["edge_share"]
    t.p("Preostaje drugo pitanje postavljeno u uvodu: leže li bridovi koje se isplati "
        "ukloniti samo uz izvor ili je ponekad ključan neki udaljeniji. Odgovor ne čitamo "
        "iz naučenih težina slojeva, iz razloga navedenog u odjeljku ", t.sec("slojevi"),
        ", nego iz toga što pobjednički rezovi doista sadrže.")

    t.p("Od ", str(hop["cells"]), " instanci njih ", str(hop["pure_hop0"]),
        " ima rez sastavljen isključivo od bridova uz izvor. Promatramo li pojedinačne "
        "bridove, ", _n(100 * share.get(0, 0), 1), " % svih uklonjenih bridova pripada "
        "sloju nula, a preostalo se raspoređuje po dubljim slojevima u sve manjim "
        "udjelima. Rezovi koji sadrže barem jedan dublji brid postižu u prosjeku ",
        _signed(hop["mean_margin_deep"]), " naprama najboljem kriteriju, dok oni sastavljeni "
        "samo od bridova uz izvor postižu ", _signed(hop["mean_margin_pure"]),
        ". Dublji bridovi, dakle, ne prate bolje rezultate nego lošije.")

    shed = deep_shedding(results, scaled)
    t.p("Sama ta korelacija ne bi bila dovoljna. Negativan nalaz ne može razlikovati "
        "mogućnost da su dublji bridovi beskorisni od mogućnosti da su dublji slojevi "
        "prostraniji nego što ih pretraga stigne pretražiti. Odlučujuće je stoga što se "
        "dogodi kada se instanci koja se muči dade više vremena.")

    rows = [[f"{int(r.source)}", f"{int(r.k)}", str(int(r.deep_before)),
             str(int(r.deep_after)), _n(r.R_before), _n(r.R_after)]
            for r in shed["shed"].itertuples()]
    t.table(
        ["Izvor", "Proračun", "Dubokih bridova prije", "Poslije", "R prije", "R poslije"],
        rows,
        "Instance u kojima je produljena pretraga odbacila sve bridove izvan sloja nula.",
        label="dubina", widths_cm=[2.0, 2.2, 3.4, 2.0, 2.2, 2.4])

    t.p("Te su pretrage dublje bridove imale i, dobivši priliku da ih usporede, zamijenile "
        "ih bridovima uz izvor. Prosječno su pritom dobile ",
        _signed(shed["mean_delta_shed"]), " naprama ", _signed(shed["mean_delta_rest"]),
        " kod preostalih ", str(shed["n_rest"]), " instanci. Brid odbačen pri ponovnom "
        "razmatranju nije bio neistražen, nego lošiji.")

    t.p("Zaključak je stoga negativan, i to je uredan ishod: na ovoj mreži nijedan brid "
        "izvan sloja nula nema potvrdu da je pomogao. To se slaže s odjeljkom ",
        t.sec("uskogrlo"), ", gdje je pokazano da uskih grla u osnovnom grafu naprosto "
        "nema, pa mehanizam nije zakazao nego u ovoj mreži nije imao što pronaći. Tri "
        "ograde ipak vrijede: pretraga nikada nije gledala dalje od trećeg sloja, mjerenje "
        "počiva na jednom sjemenu slučajnosti, a instance s dubokim bridovima okupljene su "
        "oko nekoliko izvora s velikim izlaznim stupnjem.")
