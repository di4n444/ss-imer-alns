"""2. Mreza Bitcoin Alpha.

Every number is read from data/*.csv at build time. Nothing is retyped, because a figure
typed into prose is wrong the moment the analysis is re-run and no reader can see that.

Sources: Kumar et al. (2016, 2018) for the dataset; Watts & Strogatz (1998) for the
small-world comparison; Clauset, Shalizi & Newman (2009) for the way the power-law fit is
compared against alternatives; Granovetter (1973) for the local-bridge concept;
Wang et al. (2003) and Castellano & Pastor-Satorras (2010) for the spectral threshold.

The chapter ends on 2.4, which is the structural fact the results chapter leans on: the
base graph barely distinguishes edges at all, because almost every source reaches the same
set of nodes. That is stated here rather than in chapter 6 so the reader meets the
explanation before the results it explains.
"""

import pandas as pd

from omml import delim, frac, func, sub, up, v


def _n(value, decimals=2):
    """A number for Croatian prose: decimal comma, real minus sign."""
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "−")


def _int(value):
    """Thousands separated the Croatian way: 22.650."""
    return f"{int(round(value)):,}".replace(",", ".")


def _pct(share, decimals=1):
    return _n(100 * share, decimals) + " %"


_WORDS = {1: "jedan", 2: "dva", 3: "tri", 4: "četiri", 5: "pet",
          6: "šest", 7: "sedam", 8: "osam", 9: "devet"}


def _small(value):
    """Numbers under ten are spelled out, as Croatian academic prose does."""
    return _WORDS.get(int(value), _int(value))


def _count(value, one, few, many):
    """Croatian numeral agreement: 1 čvor, 22 čvora, 25 čvorova.

    Written out rather than left to the author, because these numbers come from the CSV
    and the noun after them has to follow whatever the data says."""
    n = int(value)
    if 11 <= n % 100 <= 14:
        return f"{_int(n)} {many}"
    last = n % 10
    if last == 1:
        return f"{_int(n)} {one}"
    if last in (2, 3, 4):
        return f"{_int(n)} {few}"
    return f"{_int(n)} {many}"


def _nodes(value):
    return _count(value, "čvor", "čvora", "čvorova")


def _load(figures):
    data = figures.parent / "data"
    topology = pd.read_csv(data / "topology_summary.csv").iloc[0]
    edges = pd.read_csv(data / "edge_features.csv")
    sources = pd.read_csv(data / "source_profile.csv")
    return topology, edges, sources


def write(t, figures):
    topology, edges, sources = _load(figures)

    t.h1("Mreža Bitcoin Alpha", label="mreza")
    t.p("Svojstva koja slijede nisu opisna pozadina: ona određuju što uklanjanje bridova "
        "uopće može postići, a posljednji odjeljak poglavlja objašnjava veći dio rezultata "
        "iz poglavlja ", t.sec("rezultati"), ".")

    _data(t, figures, edges)
    _structure(t, figures, topology, edges)
    _sources(t, figures, sources)
    _no_bottleneck(t, sources, topology)


# -- 2.1 ---------------------------------------------------------------------

def _data(t, figures, edges):
    t.h2("Podaci i vjerojatnost prijenosa", label="podaci")

    t.p("Bitcoin Alpha platforma je za trgovanje bitcoinom na kojoj korisnici jedni "
        "drugima daju ocjenu povjerenja u rasponu od −10 do +10 {kumar2016,kumar2018}. "
        "Iz tih ocjena gradimo usmjeren graf: brid iz čvora ", v("u"), " u čvor ", v("v"),
        " znači da je korisnik ", v("u"), " ocijenio korisnika ", v("v"),
        ". Zadržavamo samo pozitivno ocijenjene bridove, jer negativna ocjena izražava "
        "nepovjerenje i ne može se pretpostaviti da prenosi kaskadu na jednak način. Kada "
        "je isti korisnik istoga drugog korisnika ocijenio više puta, zadržana je "
        "najnovija ocjena.")

    t.p("Model iz odjeljka ", t.sec("icm"), " traži vjerojatnost prijenosa na svakom "
        "bridu, a podaci daju cjelobrojnu ocjenu. Ocjenu ", sub(v("R"), [v("u"), v("v")]),
        " preslikavamo u vjerojatnost sigmoidalnom funkcijom, tako da niske ocjene daju "
        "malu vjerojatnost prijenosa, a najviše se približavaju jedinici:")

    t.eq(sub(v("p"), [v("u"), v("v")]), up(" = "),
         frac(up("1"), [up("1 + "),
                        func("exp", [up("−"), delim(sub(v("R"), [v("u"), v("v")]),
                                                    up(" − 5"))])]),
         label="sigmoid")

    lowest = (edges.probability == edges.probability.min()).mean()
    t.p("Posljedica takva preslikavanja vidi se na ", t.figref("vjerojatnosti"),
        ". Vjerojatnost poprima točno ", str(edges.probability.nunique()),
        " različitih vrijednosti, jer je izvedena iz cjelobrojne ocjene, a najniža od njih "
        "pokriva ", _pct(lowest), " svih bridova. Medijan iznosi ",
        _n(edges.probability.median(), 3), ", dok najveća vrijednost doseže ",
        _n(edges.probability.max(), 3), ". Ta pojedinost nije kozmetička. Kriterij koji "
        "bridove rangira po vjerojatnosti dobit će golem broj izjednačenih vrijednosti, "
        "što u odjeljku ", t.sec("izjednacene"), " postaje zaseban problem.")

    t.figure(figures / "fig2_2_probability_distribution.png",
             "Raspodjela vjerojatnosti prijenosa po bridovima. Vjerojatnost poprima samo "
             "deset vrijednosti jer je izvedena iz cjelobrojne ocjene, a velika većina "
             "bridova nosi najnižu od njih.",
             label="vjerojatnosti", width_cm=12.5)


# -- 2.2 ---------------------------------------------------------------------

def _structure(t, figures, topology, edges):
    t.h2("Struktura mreže", label="struktura")

    t.p("Osnovna mjera svakog čvora je njegov stupanj, odnosno broj bridova koji ga "
        "dodiruju. U usmjerenom grafu razlikujemo izlazni stupanj, broj bridova koji iz "
        "čvora izlaze, i ulazni stupanj, broj onih koji u njega ulaze. Za ovaj je rad "
        "izlazni stupanj važniji jer određuje koliko drugih korisnika netko može izravno "
        "aktivirati, a time i koliko bridova uopće možemo ukloniti u njegovoj okolini.")

    t.p(t.tabref("svojstva"), " sažima izmjerena svojstva mreže. Prosječna duljina puta "
        "iznosi ", _n(topology.path_length), ", što znači da su dva nasumice odabrana "
        "korisnika u prosjeku manje od četiri koraka udaljena. Koeficijent grupiranja, "
        "koji mjeri koliko su susjedi jednog čvora i međusobno povezani, iznosi ",
        _n(topology.clustering, 3), " naspram ", _n(topology.clustering_er, 4),
        " u slučajnom grafu jednake veličine. Mreža je dakle malosvjetska u smislu "
        "odjeljka ", t.sec("topologija"), ": kratki putovi kakve daje i slučajni graf, uz "
        "grupiranje više od dvadeset puta veće od njegova {watts1998}.")

    bridges = edges.is_local_bridge.mean()
    t.table(
        ["Svojstvo", "Vrijednost"],
        [["Broj čvorova", _int(topology.n)],
         ["Broj bridova", _int(topology.m)],
         ["Prosječna duljina puta", f"{_n(topology.path_length)} "
                                    f"(slučajni graf: {_n(topology.path_length_er)})"],
         ["Koeficijent grupiranja", f"{_n(topology.clustering, 3)} "
                                    f"(slučajni graf: {_n(topology.clustering_er, 4)})"],
         ["Eksponent raspodjele izlaznih stupnjeva", _n(topology.out_gamma)],
         ["Najveća jako povezana komponenta",
          f"{_int(topology.bowtie_scc)} ({_pct(topology.bowtie_scc / topology.n)})"],
         ["Najdublja k-jezgra", _int(topology.k_core_max)],
         ["Udio lokalnih mostova", _pct(bridges)],
         ["Najveća svojstvena vrijednost matrice susjedstva", _n(topology.lambda_max_A)],
         ["Epidemiološki prag", _n(topology.lambda_c, 3)],
         ["Najveća svojstvena vrijednost matrice vjerojatnosti", _n(topology.lambda_max_P)]],
        "Izmjerena svojstva mreže Bitcoin Alpha. Vrijednosti za slučajni graf odnose se na "
        "graf jednakog broja čvorova i bridova.",
        label="svojstva", widths_cm=[9.5, 5.5])

    t.p("Raspodjelu izlaznih stupnjeva prikazuje ", t.figref("stupnjevi"),
        ", u dvostruko logaritamskim osima. Prilagodba zakona potencije daje eksponent ",
        _n(topology.out_gamma), ", što je unutar raspona uobičajenog za stvarne mreže. "
        "Usporedba s drugim razdiobama, provedena postupkom koji predlažu {~clauset2009}, "
        "ipak traži opreznu formulaciju: zakon potencije uvjerljivo nadmašuje eksponencijalnu "
        "razdiobu, ali gubi od skraćenog zakona potencije i od lognormalne. Ispravno je "
        "stoga reći da je raspodjela teškorepa s konačnim odrezom, a ne bezskalna bez "
        "ograde.")

    t.figure(figures / "fig2_1_degree_distribution.png",
             "Komplementarna kumulativna raspodjela izlaznih stupnjeva s prilagođenim "
             "zakonom potencije, u dvostruko logaritamskim osima.",
             label="stupnjevi", width_cm=12.5)

    t.p("Makroskopsku strukturu usmjerenog grafa opisujemo rastavom na komponente. Jako "
        "povezana komponenta skup je čvorova u kojem se iz svakoga može doći do svakog "
        "drugog. ", t.figref("bowtie"), " prikazuje taj rastav. Jezgra obuhvaća ",
        _nodes(topology.bowtie_scc), ", dakle ",
        _pct(topology.bowtie_scc / topology.n), " mreže. U nju vodi ulazna komponenta od ",
        _nodes(topology.bowtie_in), ", a iz nje izlazi izlazna komponenta od ",
        _int(topology.bowtie_out), ". Uz to, najdublja k-jezgra iznosi ",
        _int(topology.k_core_max), ", što znači da postoji skupina korisnika u kojoj "
        "svatko ima barem toliko veza unutar same skupine.")

    t.figure(figures / "fig2_3_bowtie.png",
             "Makroskopska struktura mreže: ulazna komponenta, jako povezana jezgra i "
             "izlazna komponenta, s pripadnim brojem čvorova.",
             label="bowtie", width_cm=11.0)

    t.p("Naposljetku, iz odjeljka ", t.sec("prag"), " znamo da širenje ima prag. Najveća "
        "svojstvena vrijednost matrice susjedstva iznosi ", _n(topology.lambda_max_A),
        ", pa je prag ", _n(topology.lambda_c, 3), ". Otežamo li bridove njihovim "
        "vjerojatnostima, najveća svojstvena vrijednost takve matrice iznosi ",
        _n(topology.lambda_max_P), ", dakle znatno više od jedinice. Mreža je time duboko "
        "u nadkritičnom režimu, što potvrđuje očekivanje iz odjeljka ", t.sec("prag"), ".")


# -- 2.3 ---------------------------------------------------------------------

def _sources(t, figures, sources):
    t.h2("Populacija izvora", label="izvori")

    eligible = sources[sources.out_degree >= 2]
    t.p("Prije odabira izvora za eksperiment treba znati kako izgleda populacija iz koje "
        "ih biramo. ", t.figref("doseg"), " prikazuje kumulativnu raspodjelu očekivanog "
        "dosega po čvorovima. Krivulja je glatka i nema stube koja bi razdvojila slabe "
        "izvore od jakih, pa izvori čine kontinuum, a ne dvije skupine. Medijan dosega "
        "među čvorovima s barem dva izlazna brida iznosi ",
        _n(eligible.sigma0_saa.median(), 1), ", a prosjek ",
        _n(eligible.sigma0_saa.mean(), 1), ". Razlika između te dvije vrijednosti tipična "
        "je za teškorepu raspodjelu, u kojoj malen broj vrlo velikih dosega podiže prosjek "
        "znatno iznad onoga što je uobičajeno.")

    zero = int((sources.out_degree == 0).sum())
    small = int(sources.out_degree.between(1, 3).sum())
    t.p("Druga činjenica izravno ograničava eksperiment. Uklanjamo ", v("k"),
        " bridova iz okoline izvora, pa je slučaj u kojem je ", v("k"),
        " veći ili jednak izlaznom stupnju izvora trivijalan: uklonimo li sve izlazne "
        "bridove, izvor je potpuno izoliran i nikakva pretraga nije potrebna. Čvorova bez "
        "ijednog izlaznog brida ima ", _int(zero), ", a još ih ", _int(small),
        " ima najviše tri. Netrivijalnih izvora zato je mnogo manje nego čvorova: za ",
        v("k"), " = 3 ostaje ih ", _int((sources.out_degree > 3).sum()), ", za ", v("k"),
        " = 10 njih ", _int((sources.out_degree > 10).sum()), ", a za ", v("k"),
        " = 20 samo ", _int((sources.out_degree > 20).sum()), ".")

    t.figure(figures / "fig2_4_source_reach.png",
             "Kumulativna raspodjela očekivanog dosega po izvorima. Krivulja nema stube "
             "koja bi razdvojila dvije skupine, nego se doseg mijenja postupno.",
             label="doseg", width_cm=12.5)

    t.p(t.figref("pojasevi"), " pokazuje kako se doseg raspoređuje po pojasevima izlaznog "
        "stupnja. Izlazni stupanj snažno predviđa doseg, ali ne i savršeno, jer i među "
        "čvorovima s malo izlaznih bridova ima onih koji dosežu velik dio mreže. Zbog toga "
        "uzorak izvora u poglavlju ", t.sec("postav"), " raslojavamo po objema veličinama, "
        "a ne samo po izlaznom stupnju.")

    t.figure(figures / "fig2_5_source_outdegree.png",
             "Sastav pojaseva izlaznog stupnja s obzirom na doseg. Prvi pojas ne može biti "
             "izvor ni za najmanji razmatrani proračun.",
             label="pojasevi", width_cm=12.5)


# -- 2.4 ---------------------------------------------------------------------

def _no_bottleneck(t, sources, topology):
    t.h2("Topologija osnovnog grafa ne razlikuje bridove", label="uskogrlo")

    eligible = sources[sources.out_degree >= 2]
    core = int(topology.bowtie_scc + topology.bowtie_out)
    same = int((eligible.reachable == core).sum())
    near = int((eligible.reachable > core).sum())
    excess = int(eligible.reachable.max() - core)
    tiny = int((eligible.reachable < 8).sum())

    t.p("Sve dosad izmjereno vodi do jednog nalaza koji objašnjava većinu kasnijih "
        "rezultata. Promotrimo li samo dohvatljivost, dakle postoji li uopće put od izvora "
        "do nekog čvora, bez obzira na vjerojatnosti, gotovo svaki izvor doseže isti skup "
        "čvorova. Taj je skup jezgra zajedno sa svime nizvodno od nje, ukupno ",
        _nodes(core), ", što je upravo zbroj jako povezane i izlazne komponente iz "
        "odjeljka ", t.sec("struktura"), ".")

    t.p("Brojke su izrazite. Od ", _int(len(eligible)),
        " čvorova s barem dva izlazna brida njih ", _int(same),
        " doseže točno taj skup, a još njih ", _small(near), " doseže isti skup uvećan za "
        "najviše ", _small(excess), " čvora, koliko im visi u vlastitoj slijepoj ulici. "
        "Preostalih ", _small(tiny), " doseže manje od osam čvorova. Između tih dviju "
        "krajnosti nema nijednog izvora.")

    t.p("Posljedica je važnija od samih brojeva. Dohvatljivost je pitanje sve ili ništa: "
        "ili izvor dodiruje jezgru i doseže je cijelu, ili je u slijepoj ulici s nekoliko "
        "čvorova. Ako pritom gotovo svaki izvor doseže isti skup, onda topologija osnovnog "
        "grafa gotovo ništa ne govori o tome koji je brid važan. Uskog grla kojim bismo "
        "izvor odvojili od jezgre jednostavno nema, jer alternativnih putova ima previše.")

    t.p("Usko grlo ipak može postojati, ali tek nakon bacanja novčića. Realizacija je "
        "rijedak slučajan podgraf u kojem neki čvor može visjeti o jednom jedinom "
        "preživjelom bridu. Takvo je grlo svojstvo toga jednog izvlačenja, a ne mreže, pa "
        "ga nijedan kriterij izračunat iz osnovnog grafa ne može vidjeti. Upravo to "
        "objašnjava zašto u poglavlju ", t.sec("rezultati"), " topološki kriteriji "
        "podbacuju, a vjerojatnost prijenosa, jedina veličina koja govori o tome je li brid "
        "uopće prisutan u realizaciji, nadmašuje ostale.")

    t.p("Isti nalaz razrješava i prividnu proturječnost. Ako svaki izvor doseže ",
        _int(core), " čvorova, zašto je očekivani doseg iz odjeljka ", t.sec("izvori"),
        " tek nekoliko desetaka? Zato što se kaskada ne širi osnovnim grafom nego "
        "realizacijom, a uz medijan vjerojatnosti od svega nekoliko postotaka većina je "
        "bridova u većini realizacija odsutna.")
