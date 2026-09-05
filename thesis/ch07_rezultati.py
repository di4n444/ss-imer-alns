"""7. Rezultati i rasprava.

Every number here is computed from data/results.csv and data/results_scaled.csv at build
time, by the same functions the result figures use (code/results_analysis.py). Nothing is
retyped: a figure typed into prose becomes wrong the moment the measurement is re-run, and
no reader can see that from the text.

Four sections, one per question the measurement can answer, in the order the answers
depend on each other. The estimate is validated first, because it says how much of every
later difference is fitted to the frozen sample; the method comparison and the budget
sweep follow; the length of the search comes last, because it is measured on a separate
file at a different iteration budget and must not be pooled with the comparison.

The grouping rules - which tags may be compared, which rows are duplicates, what counts as
a tie - are deliberately not restated here. They live in code/results_analysis.py so that
the text and the figures cannot come to disagree about them.
"""

import sys
from pathlib import Path

import pandas as pd

from omml import i, v

CODE = Path(__file__).resolve().parent.parent / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from results_analysis import (  # noqa: E402  (path must be set first)
    CRITERIA, comparison_cells, comparison_rows, comparison_table, gap_summary,
    load_results, oracle_summary, prior_band, runtime_summary, scaled_summary,
    stratified)

# Croatian names for the criteria, in one place: the tables, the prose and the figure
# legends all have to call the same criterion the same thing.
NAMES = {
    "probability": "vjerojatnost",
    "degree": "zbroj stupnjeva",
    "betweenness": "međupoloženost",
    "spectral": "spektralni",
    "bridge": "lokalni most",
    "random": "slučajni",
}


def _n(value, decimals=3):
    """A number for prose: decimal comma, and a real minus sign."""
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "−")


def _signed(value, decimals=3):
    """A signed number for prose. A value that rounds to zero loses its sign: "−0,000"
    reads as a negative quantity when it is really an absence of one."""
    rounded = round(abs(value), decimals)
    text = f"{rounded:.{decimals}f}".replace(".", ",")
    if rounded == 0:
        return text
    return ("+" if value > 0 else "−") + text


def _int(value):
    return f"{int(value):,}".replace(",", ".")


def _count(value, one, few, many):
    """Croatian numeral agreement: 1 instanca, 22 instance, 95 instanci."""
    n = int(value)
    if 11 <= n % 100 <= 14:
        return f"{_int(n)} {many}"
    last = n % 10
    if last == 1:
        return f"{_int(n)} {one}"
    if last in (2, 3, 4):
        return f"{_int(n)} {few}"
    return f"{_int(n)} {many}"


def write(t, figures):
    data = figures.parent / "data"
    results = load_results(data / "results.csv")
    scaled = pd.read_csv(data / "results_scaled.csv")

    t.h1("Rezultati i rasprava")
    t.p("Mjerenje je provedeno nad ",
        _count(len(comparison_cells(results)), "instancom", "instance", "instanci"),
        ", pri čemu je instanca jedan par izvora i proračuna, a svaka je riješena svim "
        "pohlepnim kriterijima i metaheuristikom. Poglavlje te rezultate ne iznosi kao "
        "jedan prosjek, nego razdvojeno, po pitanjima na koja mjerenje uistinu može "
        "odgovoriti: koliko je procjena pouzdana, nadmašuje li prilagodljivo pretraživanje "
        "nepromjenjiv topološki kriterij, kako se slika mijenja s proračunom i što donosi "
        "dulja pretraga. Prosjek preko svih pokretanja odjednom ne bi odgovorio ni na "
        "jedno od njih.")

    t.p("Redoslijed nije proizvoljan. Valjanost procjene dolazi prva jer određuje koliko "
        "je svaka kasnija razlika uopće čitljiva, a duljina pretrage dolazi posljednja jer "
        "je mjerena nad zasebnom datotekom, uz drukčiji proračun iteracija i bez "
        "pripadajućih pohlepnih rezultata, pa se s usporedbom metoda ne smije objediniti.")

    _validity(t, figures, results)
    _comparison(t, results)
    _budget(t, figures, results)
    _search_length(t, figures, data, results, scaled)


# -- 7.1 ---------------------------------------------------------------------

def _validity(t, figures, results):
    t.h2("Valjanost procjene", label="valjanost")

    gap = gap_summary(results)
    t.p("Pretraživanje optimira doseg nad zamrznutim skupom realizacija, a izvještava se "
        "vrijednost izmjerena nad neovisnim skupom (odjeljak ", t.sec("realizacije"),
        "). Razlika tih dviju vrijednosti mjeri koliko je pronađeni rez prilagođen "
        "vlastitom uzorku, pa se čita prije svake usporedbe metoda: ona određuje ispod "
        "koje razlike dvije metode nema smisla razlikovati.")

    t.p("Medijan raskoraka iznosi ", _signed(gap["median"]),
        ", uz međukvartilni raspon od ", _signed(gap["q1"]), " do ",
        _signed(gap["q3"]), ". Od ", _count(gap["cells"], "instance", "instance",
                                            "instanci"),
        " njih je ", _int(gap["optimistic"]),
        " unutar uzorka precijenjeno, a ", _int(gap["pessimistic"]),
        " podcijenjeno, pa je odstupanje sustavno, ali maleno. Velikih odstupanja gotovo "
        "i nema: apsolutni raskorak veći od ", _n(0.10, 2), " pojavljuje se u ",
        _count(gap["over_10"], "instanci", "instance", "instanci"),
        ", a najveći zabilježeni iznosi ", _signed(gap["max"]),
        ". Obje procjene, po instanci, prikazuje ", t.figref("saamc"), ".")

    t.figure(figures / "fig7_1_saa_mc.png",
             "Relativno smanjenje dosega na zamrznutom i na neovisnom skupu realizacija, "
             "po instanci. Točke ispod dijagonale precijenjene su na uzorku nad kojim je "
             "pretraživanje radilo.", label="saamc")

    worst = _worst_gap_source(results)
    t.p("Vrijedi pogledati gdje se ta rijetka velika odstupanja pojavljuju. Dva od tri "
        "otpadaju na isti izvor, i to izvor malenog izlaznog stupnja pri malenom "
        "proračunu (izvor ", str(worst["source"]), ", izlazni stupanj ",
        str(worst["out_degree"]), ", pri ", v("k"), " = ", str(worst["k"]),
        " i ", v("k"), " = ", str(worst["k_second"]),
        "). To je očekivano mjesto: kada je bridova malo, malen je i broj bitno različitih "
        "rezova, pa se pretraživanje lakše prisloni uz osobitost pojedine realizacije nego "
        "kada bira između stotina kandidata.")

    t.p("Presudan je, međutim, usporedni podatak. Medijan raskoraka nijednoga pohlepnog "
        "kriterija ne prelazi ", _signed(gap["worst_baseline_median"]),
        ", dakle red veličine manje od metaheuristike. Razlog nije u procjenitelju, koji "
        "je za sve metode isti, nego u tome što pohlepni kriteriji uzorak uopće ne gledaju: "
        "oni biraju rez iz svojstava osnovnoga grafa i nemaju se čemu prilagoditi "
        "(odjeljak ", t.sec("pohlepne"),
        "). Raskorak stoga nije svojstvo procjene dosega, nego cijena pretraživanja — "
        "mjeri koliko optimiranje nad konačnim uzorkom realizacija plaća izvan njega.")

    t.p("Praktična posljedica za ostatak poglavlja: razlike reda veličine medijana "
        "raskoraka, dakle nekoliko stotinki, ne smiju se čitati kao presudne, bez obzira "
        "na to koja je metoda na kojoj strani.")


def _worst_gap_source(results):
    """The source carrying the largest gaps, and its two worst budgets.

    Read rather than asserted: the prose says "two of the three largest gaps fall on one
    source", and that sentence has to be recomputed, not remembered."""
    alns = comparison_rows(results)
    alns = alns[alns.method == "alns"].nlargest(3, "saa_mc_gap")
    top = alns.iloc[0]
    same = alns[alns.source == top.source].sort_values("saa_mc_gap", ascending=False)
    return {"source": int(top.source), "out_degree": int(top.out_degree),
            "k": int(same.iloc[0].k),
            "k_second": int(same.iloc[1].k) if len(same) > 1 else int(top.k)}


# -- 7.2 ---------------------------------------------------------------------

def _comparison(t, results):
    t.h2("Usporedba metoda", label="usporedba")

    table = comparison_table(results)
    cells = comparison_cells(results)
    oracle = oracle_summary(results)

    t.p("Usporedba se iznosi po kriteriju, a ne prema najboljem suparniku po instanci. "
        "Razlog je isti onaj iz odjeljka ", t.sec("protokol"),
        ": najbolji rezultat izabran naknadno, zasebno za svaku instancu, nije metoda koju "
        "bi itko mogao primijeniti, jer pretpostavlja da se unaprijed zna koji će kriterij "
        "na kojoj instanci pobijediti. Takva se veličina iznosi kasnije, i to kao gornja "
        "ograda, a ne kao protivnik.")

    t.table(
        ["Kriterij", "Bolje", "Izjednačeno", "Lošije", "Prosječna razlika", "Prosječni R"],
        [[NAMES[row.criterion], _int(row.better), _int(row.tied), _int(row.worse),
          _signed(row.mean_delta), _n(row.mean_R)]
         for row in table.itertuples()],
        "Metaheuristika ALNS naspram svakoga pohlepnog kriterija zasebno, po "
        f"{_int(oracle['cells'])} instanci. Razlika je izražena u relativnom smanjenju "
        "dosega na neovisnom skupu realizacija.", label="usporedba_tab")

    weakest = table.iloc[0]
    rival = table.iloc[-1]
    t.p("Metaheuristika nadmašuje svaki kriterij u prosjeku, ali raspon je velik i tek ga "
        "razdvajanje čini čitljivim. Naspram kriterija „", NAMES[weakest.criterion],
        "” prednost iznosi ", _signed(weakest.mean_delta),
        ", što je gotovo razlika između rješenja i njegova izostanka. Naspram kriterija „",
        NAMES[rival.criterion], "” pada na ", _signed(rival.mean_delta),
        ", uz omjer ", _int(rival.better), " prema ", _int(rival.worse),
        " u korist metaheuristike i ", _int(rival.tied),
        " izjednačenih ishoda. Vjerojatnost prolaska je, dakle, jedini pravi suparnik; "
        "ostalih pet kriterija metaheuristika nadmašuje uvjerljivo.")

    t.p("Dva su ishoda bila predviđena prije mjerenja i oba se potvrđuju. ",
        "{~kimura2008} izvijestili su da blokiranje bridova između čvorova visokoga "
        "izlaznog stupnja nije nužno djelotvorno, i doista, kriterij „",
        NAMES["degree"], "” postiže prosječnih ",
        _n(float(table[table.criterion == "degree"].mean_R.iloc[0])),
        ", znatno ispod vjerojatnosti prolaska. Spektralni kriterij, koji po konstrukciji "
        "optimira pogrešnu veličinu — najveću svojstvenu vrijednost, koja opisuje prag "
        "cijele mreže, a ne doseg iz jednoga izvora (odjeljak ", t.sec("spektralni"),
        ") — završava na ",
        _n(float(table[table.criterion == "spectral"].mean_R.iloc[0])),
        ", dakle u istom razredu kao stupanj i međupoloženost, a jasno iza vjerojatnosti "
        "prolaska. Nijedno od toga nije naknadno objašnjenje: obje su tvrdnje zapisane kao "
        "provjerljiva očekivanja prije nego što su rezultati postojali.")

    t.p("Tek sada ima smisla iznijeti spomenutu gornju ogradu. Najbolji kriterij izabran "
        "naknadno za svaku instancu postiže prosječnih ",
        _n(oracle["oracle_mean_R"], 4), ", a metaheuristika ",
        _n(oracle["alns_mean_R"], 4),
        " — razlika je manja od tisućinke, a metaheuristika dostiže ili nadmašuje tu "
        "ogradu u ",
        _int(oracle["alns_at_least"]), " od ", _int(oracle["cells"]),
        " instanci. Drugim riječima, jedno pretraživanje bez ikakva predznanja o instanci "
        "izjednačuje se s postupkom koji za svaku instancu unaprijed zna koji od šest "
        "kriterija na njoj pobjeđuje. To je najjača tvrdnja koju ovo mjerenje podupire, i "
        "vrijedi je čitati upravo tako usko kako je izrečena.")

    # Selected by label, never by position: an empty stratum is dropped from the frame,
    # so `.iloc[1]` silently becomes a different band on a different sample.
    reach = stratified(results, "sigma0", [0, 10, 100, 400, 1e9],
                       ["< 10", "10 – 100", "100 – 400", "≥ 400 (zasićeni)"])
    by_reach = reach.set_index("stratum")

    saturated = by_reach.loc["≥ 400 (zasićeni)"]
    t.p("Prosjek koji prikazuje ", t.tabref("usporedba_tab"),
        " spaja, međutim, dvije različite pojave, što se vidi tek kad se instance "
        "razdvoje po početnom dosegu izvora, kako prikazuje ", t.tabref("razredi"),
        ". Na izvorima srednjega dosega prednost metaheuristike iznosi ",
        _signed(by_reach.loc["10 – 100"].mean_delta), " odnosno ",
        _signed(by_reach.loc["100 – 400"].mean_delta),
        ", dok na ", _count(saturated.cells, "zasićenoj instanci", "zasićene instance",
                            "zasićenih instanci"),
        " prelazi u zaostatak od ", _signed(saturated.mean_delta),
        ". Kako zasićeni izvori čine većinu uzorka, upravo taj zaostatak gotovo poništava "
        "ukupnu prednost naspram vjerojatnosti prolaska.")

    t.table(
        ["Razred dosega", "Instanci", "ALNS", "Vjerojatnost", "Razlika", "Bolje", "Lošije"],
        [[str(row.stratum), _int(row.cells), _n(row.alns_mean_R), _n(row.other_mean_R),
          _signed(row.mean_delta), _int(row.better), _int(row.worse)]
         for row in reach.itertuples()],
        "Metaheuristika naspram vjerojatnosti prolaska, razdvojeno po početnom dosegu "
        "izvora. Prosjek preko svih instanci skriva da se prednost gubi upravo na "
        "zasićenim izvorima.", label="razredi")

    share = stratified(results, "budget_share", [0, .2, .4, .7, 1.01],
                       ["≤ 20 %", "20 – 40 %", "40 – 70 %", "> 70 %"]).set_index("stratum")
    low, high = share.loc["≤ 20 %"], share.loc["40 – 70 %"]
    t.p("Isti zaključak daje i razdvajanje po udjelu proračuna u izlaznom stupnju izvora. "
        "Pri udjelu do 20 % prednost iznosi tek ", _signed(low.mean_delta), ", uz ",
        _int(low.better), " pobjeda naspram ", _int(low.worse),
        " poraza, što je blizu ravnoteže; pri udjelu od 40 do 70 % raste na ",
        _signed(high.mean_delta), ", uz ", _int(high.better), " naspram ",
        _int(high.worse),
        ". Zasićeni izvori i maleni udjeli proračuna dvije su strane iste pojave, a "
        "odjeljak ", t.sec("duljina"), " pokazuje da je uzrok u duljini pretrage, a ne u "
        "samoj metodi.")

    _scope(t, results)


def _scope(t, results):
    runtime = runtime_summary(results)
    cells = comparison_cells(results)
    everywhere = cells[[f"greedy_{c}" for c in CRITERIA] + ["alns"]].min(axis=1) > 0.9

    t.p("Dosegu ove usporedbe treba jasno odrediti granice. Šest pohlepnih kriterija "
        "obuhvaća, i nadmašuje, skup slabih usporednih metoda koje su objavili ",
        "{~kimura2008} — međupoloženost, izlazni stupanj i slučajni odabir. Metoda koju su "
        "sami ", i("predložili"),
        ", pohlepno pretraživanje po izmjerenom dosegu s ponovnim vrednovanjem u svakom "
        "koraku, u ovoj usporedbi ne sudjeluje. Rezultati stoga odgovaraju na pitanje "
        "nadmašuje li prilagodljivo pretraživanje nepromjenjiv topološki kriterij, a ne "
        "nadmašuje li najbolju poznatu metodu; osmo poglavlje objašnjava zašto se ta "
        "metoda ovdje nije mogla izravno preuzeti.")

    t.p("Uz to, međupoloženost se ovdje računa jednokratno, nad statičkom mjerom "
        "ukorijenjenom u izvoru, dok je izvorna inačica ponovno računa nakon svakoga "
        "uklonjenog brida. Razlika je posljedica troškovnoga modela iz odjeljka ",
        t.sec("arhitektura"),
        ", koji ponovno računanje unutar petlje ne dopušta, ali je razlika stvarna i ne "
        "treba je prešutjeti.")

    t.p("Naposljetku, dvije napomene o samom uzorku instanci. Instanci u kojima svaka "
        "metoda prelazi ", _n(0.9, 1), " ima ",
        ("svega jedna" if int(everywhere.sum()) == 1 else _int(everywhere.sum())),
        " od ", _int(len(cells)),
        ", pa prosjeci nisu polaskani skupinom trivijalno riješenih slučajeva. Cijena "
        "izračuna vrlo je nesimetrična: svih šest pohlepnih kriterija zajedno troši ",
        _n(100 * runtime["baselines_share"], 1),
        " % vremena koje traži jedno pokretanje metaheuristike, a pojedinačni kriterij oko ",
        _n(100 * runtime["one_baseline_share"], 1),
        " %. Time su pohlepni rezultati praktički besplatna prethodna obavijest o instanci, "
        "što osmo poglavlje koristi kao argument.")


# -- 7.3 ---------------------------------------------------------------------

def _budget(t, figures, results):
    t.h2("Ovisnost o proračunu uklanjanja", label="proracun")

    sweep = results[results.tag == "k-sweep"]
    sources = sorted(sweep.source.unique())

    t.p("Populacijsko mjerenje daje po jedan proračun za svaki razred izvora, pa ne može "
        "pokazati kako se ponašanje metoda mijenja duž proračuna. Za to su tri izvora "
        "mjerena kroz cijeli raspon: dva srednje veličine i jedno čvorište, kod kojega "
        "proračun doseže stvarni udio izlaznoga stupnja. Tri se krivulje namjerno ne "
        "objedinjuju u jednu: izlazni se stupnjevi razlikuju, pa isti ", v("k"),
        " kod svakoga izvora znači drukčiji udio, što pokazuje gornja os na ",
        t.figref("sweep"), ".")

    t.figure(figures / "fig7_2_k_sweep.png",
             "Relativno smanjenje dosega u ovisnosti o proračunu, po izvoru. Gornja os "
             "prikazuje udio proračuna u izlaznom stupnju izvora.", label="sweep")

    mid = [s for s in sources if s != _hub_source(sweep)]
    t.p("Na dvama izvorima srednje veličine (", ", ".join(f"izvor {s}" for s in mid),
        ") slika je jednostavna: metaheuristika vodi na cijelom rasponu proračuna, a "
        "poredak kriterija ostaje stabilan. Kod čvorišta je slika bitno drukčija i "
        "poučnija.")

    hub = _hub_summary(sweep)
    t.p("Kod izvora ", str(hub["source"]), ", izlaznoga stupnja ", str(hub["out_degree"]),
        ", nijedna metoda ne postiže gotovo ništa dok je proračun ispod otprilike trećine "
        "izlaznoga stupnja — što je izravna posljedica geometrije opisane u odjeljku ",
        t.sec("populacija"), ": izvor s razgranatim izlazom ne može se zatvoriti "
        "proračunom koji pokriva tek djelić njegovih bridova. U srednjem dijelu raspona "
        "vodi vjerojatnost prolaska, i to uvjerljivo, a metaheuristika je sustiže tek pri ",
        v("k"), " = ", str(hub["alns_overtakes_at"]),
        " i od tada zadržava prednost do kraja raspona.")

    t.p("Jedna pojedinost na toj krivulji nije stvar procjene nego dokaz. Pri ", v("k"),
        " = ", str(hub["dip_k"]), " metaheuristika postiže ", _n(hub["dip_value"]),
        ", što je ", i("manje"), " od ", _n(hub["before_value"]), " koliko je postigla pri "
        "manjem proračunu ", v("k"), " = ", str(hub["before_k"]),
        ". Optimalno rješenje takvo ponašanje ne može pokazati: rez veličine ", v("k"),
        " − 1 nadopunjen bilo kojim dodatnim bridom dopušten je rez veličine ", v("k"),
        ", a doseg je monoton po skupu uklonjenih bridova, pa optimum uz veći proračun ne "
        "može biti lošiji. Pad je stoga nužno promašaj pretraživanja, a ne svojstvo "
        "instance. Nijedan pohlepni kriterij duž nijednoga od tri raspona ne pokazuje "
        "takav pad, jer njihov rezultat i nije ishod pretraživanja nego izravnog poretka.")

    t.p("Ta je opažljivost korisna sama po sebi. Nemonotonost po proračunu jedini je "
        "pokazatelj promašaja koji ne traži poznat optimum ni jaču suparničku metodu — "
        "vidljiv je iz same krivulje. Odjeljak ", t.sec("duljina"),
        " pokazuje da je uzrok upravo ograničen broj iteracija.")


def _hub_source(sweep):
    return int(sweep.loc[sweep.out_degree.idxmax()].source)


def _hub_summary(sweep):
    """The hub sweep, read rather than remembered: where ALNS overtakes the strongest
    criterion, and the non-monotone dip that proves a search failure."""
    src = _hub_source(sweep)
    grp = sweep[sweep.source == src]
    wide = grp.pivot_table(index="k", columns="method", values="R_mc").sort_index()

    # The overtake is the budget after the LAST one at which the criterion still led, not
    # the first at which ALNS happened to be ahead: at the smallest budgets both score
    # near zero and the sign of a thousandth means nothing.
    behind = wide.index[wide["alns"] <= wide["greedy_probability"]]
    overtakes = int(wide.index[wide.index > behind.max()][0])

    dip_k, dip_value, before_k, before_value = None, None, None, None
    for (prev_k, prev), (this_k, this) in zip(wide["alns"].items(),
                                              list(wide["alns"].items())[1:]):
        if this < prev - 1e-9:
            dip_k, dip_value, before_k, before_value = this_k, this, prev_k, prev
    return {"source": src, "out_degree": int(grp.out_degree.iloc[0]),
            "alns_overtakes_at": overtakes, "dip_k": int(dip_k), "dip_value": dip_value,
            "before_k": int(before_k), "before_value": before_value}


# -- 7.4 ---------------------------------------------------------------------

def _search_length(t, figures, data, results, scaled):
    t.h2("Utjecaj duljine pretrage", label="duljina")

    summary = scaled_summary(results, scaled)

    t.p("Broj je iteracija u dosadašnjim mjerenjima nepromjenjiv, bez obzira na proračun i "
        "na veličinu izvora (odjeljak ", t.sec("prihvacanje"),
        "). Prethodna dva odjeljka pokazala su dva traga da je to premalo upravo ondje "
        "gdje su instance najteže. Zato je dio instanci ponovno pokrenut uz proračun "
        "iteracija razmjeran veličini problema, uz sve ostalo nepromijenjeno, i zapisan u "
        "zasebnu datoteku. Uspoređuje se upareno, po instanci: riječ je o istim "
        "instancama, pa uparivanje uklanja svu razliku među njima i time čini promjenu od "
        "nekoliko stotinki uopće čitljivom.")

    t.p("Prije rezultata treba pročitati kako su instance izabrane, jer izbor ograničava "
        "zaključak. Uzeta je najjeftinija instanca po svakom razredu i proračunu, a jeftino "
        "je u ovom mjerenju usko povezano s lakim: većina je izabranih instanci već bila "
        "konvergirala. Ponovno pokretanje stoga mjeri koliko dulja pretraga pomaže "
        "prosječnoj instanci, a ne koliko pomaže onoj koja se muči.")

    t.p("Od ", _count(summary["paired"], "uparene instance", "uparene instance",
                      "uparenih instanci"),
        " njih je ", _int(summary["more"]), " doista dobilo više iteracija; preostalih ",
        _int(summary["budget_unchanged"]), " ima najmanji proračun, pri kojem novo "
        "pravilo daje isti broj iteracija kao i staro. Te su instance nehotice ponovljene "
        "pod istim postavkama i sve su do zadnje znamenke ponovile raniji rezultat, pa je "
        "ponovljivost cijeloga postupka ovdje izmjerena, a ne pretpostavljena.")

    t.p("Među instancama koje su dobile više iteracija, napredovalo ih je ",
        _int(summary["improved"]), ", nepromijenjeno ih je ostalo ",
        _int(summary["unchanged"]), ", a nazadovalo ih je ", _int(summary["worse"]),
        ". Prosječna promjena iznosi ", _signed(summary["mean_delta"]),
        ", uz najveći pojedinačni dobitak od ", _signed(summary["best_delta"]),
        ". Sam prosjek, međutim, krivo opisuje što se dogodilo, jer je dobitak izrazito "
        "neravnomjerno raspoređen: sažetak po skupinama daje ", t.tabref("produljenje"),
        ", a promjenu svake pojedine instance ", t.figref("gain"), ".")

    bands = summary["bands"]
    t.table(
        ["Stanje instance prije produljenja", "Instanci", "Prosječna promjena",
         "Najveća promjena"],
        [[row.band, _int(row.cells), _signed(row.mean_delta), _signed(row.max_delta)]
         for row in bands.itertuples()],
        "Promjena relativnog smanjenja dosega nakon produljenja pretrage, razvrstana po "
        "tome kako je instanca stajala prije produljenja.", label="produljenje")

    t.figure(figures / "fig7_3_scaled_gain.png",
             "Promjena relativnog smanjenja dosega nakon produljenja pretrage, po "
             "instanci, u ovisnosti o rezultatu prije produljenja.", label="gain")

    t.p("Uzorak je monoton i to je glavni nalaz ovoga odjeljka: što je instanca stajala "
        "lošije, to joj dulja pretraga više vraća, dok instance koje su već bile dobre ne "
        "dobivaju gotovo ništa. Cijena je pritom bila ",
        _n(summary["cost_factor"], 1), " puta veće računalno vrijeme za prosječan dobitak "
        "od ", _signed(summary["mean_delta"]),
        ". Zaključak nije da pretragu treba produljiti, nego da je globalno podizanje "
        "konstante pogrešan alat: gotovo sav uloženi trud otpada na instance koje ga ne "
        "trebaju. Raspored truda prema potrebi tema je osmoga poglavlja.")

    t.p("Nazadovanje u ", _count(summary["worse"], "instanci", "instance", "instanci"),
        " nije šum. Dulja pretraga jače optimira procjenu nad zamrznutim uzorkom, a rez "
        "tješnje prilagođen tim realizacijama može izvan njih postići manje — dakle upravo "
        "ona pojava koju mjeri raskorak iz odjeljka ", t.sec("valjanost"),
        ", ovdje viđena s druge strane, kao cijena uloženoga truda, a ne kao svojstvo "
        "procjenitelja.")

    _diagnostic(t, pd.read_csv(data / "iteration_probe.csv"))


def _diagnostic(t, probe):
    t.p("Ostaje pitanje kako unaprijed prepoznati instancu kojoj dulja pretraga treba, jer "
        "je pokazano da sam proračun to ne otkriva. Izravan pokazatelj daje trenutak "
        "posljednjega poboljšanja, izražen kao udio proteklog pretraživanja: vrijednost "
        "blizu jedinice znači da je pretraga još napredovala kada ju je proračun prekinuo. "
        "Taj se podatak dobiva iz zapisa koji pretraživanje ionako vodi i ne mijenja ništa "
        "u samom postupku.")

    still = probe[probe.improvement_share >= 0.8]
    starved = still[still.R_mc_at_300 < 0.3]
    t.p("Mjerenje na ", _count(len(probe), "instanci", "instance", "instanci"),
        " pokazuje, međutim, da taj udio sam po sebi nije dovoljan. Pretraga je pri kraju "
        "još napredovala u ", _count(len(still), "instanci", "instance", "instanci"),
        ", ali su od njih samo ", _int(len(starved)),
        " pritom postizale gotovo ništa — i upravo su te instance produljenjem najviše "
        "dobile. One koje su još napredovale, ali su već bile blizu vrha, nisu imale što "
        "dobiti. Pokazatelj je, dakle, spoj dvaju uvjeta — da pretraga nije završila i da "
        "je ostalo što naći — a ne nijedan od njih zasebno. Za kalibrirano pravilo to je "
        "premalo instanci, ali je dovoljno za argument osmoga poglavlja.")
