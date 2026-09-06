"""7. Mogucnosti poboljsanja i buduci rad.

Four items, in decreasing order of how much this thesis's own measurements argue for them.
The first is the one the work genuinely earns: chapter 2 showed the base graph cannot
distinguish edges, chapter 6 showed every criterion built on it underperforms, so the
structure worth measuring is in the realizations, which we never analysed.

The sigma-greedy reformulation in 7.3 is derived rather than quoted. Kimura's own
efficiency trick averages only over scenarios where the edge was unoccupied, which keeps
80-97% of his sample at his uniform p; at our probabilities it would retain a handful of
500, and the high-probability edges are exactly the ones worth cutting.
"""

import params
from omml import delim, frac, nary, sub, up, v
from params import config


def write(t, figures):
    t.h1("Mogućnosti poboljšanja i budući rad", label="poboljsanja")
    t.p("Rezultati otvaraju četiri smjera, i vrijedi ih navesti onim redom kojim ih mjerenja "
        "iz ovog rada podupiru.")

    _criteria(t)
    _effort(t)
    _greedy(t)
    _confidence(t)


def _criteria(t):
    t.h2("Kriteriji izvedeni iz realizacija", label="izrealizacija")

    t.p("Najjači smjer slijedi izravno iz dvaju nalaza ovog rada. Odjeljak ",
        t.sec("uskogrlo"), " pokazao je da osnovni graf gotovo ne razlikuje bridove, jer "
        "gotovo svaki izvor doseže isti skup čvorova, a odjeljak ", t.sec("usporedba"),
        " pokazao je da svi kriteriji izvedeni iz te topologije zaostaju za vjerojatnošću "
        "prijenosa, jedinim kriterijem koji govori o tome je li brid uopće prisutan u "
        "realizaciji.")

    t.p("Zaključak koji se nameće jest da korisna struktura ne leži u osnovnom grafu nego "
        "u samim realizacijama. Realizacija je rijedak slučajan podgraf i u njemu uska "
        "grla postoje, samo što pripadaju tom jednom izvlačenju. Kriterij koji bi mjerio u "
        "koliko od ", params.hr(config.SAA_SCENARIO_COUNT),
        " realizacija uklanjanje nekog brida uistinu odvaja dio "
        "čvorova bio bi upravo ono za što su svih šest naših kriterija slijepi. Takav "
        "kriterij ne bi bio ni skup, jer su realizacije već zamrznute i višekratno se "
        "koriste.")

    t.p("Tu analizu nismo proveli i to je najveći propust ovog rada. Uz nju bi išla i "
        "osnovna provjera samih realizacija, poput toga koliki udio bridova preživi jedno "
        "izvlačenje i preživljava li divovska komponenta, što bi ujedno potvrdilo da je "
        "procjena dosega smislena.")


def _effort(t):
    t.h2("Raspodjela truda pretraživanja prema potrebi", label="raspodjela")

    t.p("Odjeljak ", t.sec("duljina"), " pokazao je da globalno podizanje broja iteracija "
        "nije dobar instrument: skuplja pretragu višestruko, a dobitak odlazi gotovo "
        "isključivo instancama koje su prije stajale loše. Umjesto toga trud treba "
        "usmjeriti onamo gdje se isplati, a za to postoje dva pokazatelja.")

    t.p("Prvi je udio pretrage nakon kojega se rješenje više nije popravilo. Ako je "
        "posljednje poboljšanje došlo pred sam kraj, pretraga je prekinuta dok je još "
        "napredovala. Sam taj udio nije dovoljan, jer instanca može napredovati do kraja i "
        "pritom već biti vrlo dobra: pokazatelj je tek kombinacija visokog udjela i niskog "
        "rezultata. Drugi je pokazatelj pad rezultata s porastom proračuna, opisan u "
        "odjeljku ", t.sec("proracun"), ". On je logički siguran znak promašenog optimuma, "
        "ne traži poznavanje točnog rješenja i ne stoji ništa jer se dobiva iz mjerenja "
        "koje ionako provodimo.")

    t.p("Prirodan je nastavak da pretraga sama produljuje vlastiti proračun dok god se "
        "popravlja, a stane kada napredak splasne. To nije isto što i prekid zbog "
        "stagnacije: takav prekid krati pretragu koja više ne donosi ništa, a ovdje je "
        "riječ o produljenju one koja još donosi.")


def _greedy(t):
    t.h2("Pohlepna metoda vođena izmjerenim dosegom", label="sigmapohlepna")

    t.p("Usporedba u ovom radu ne obuhvaća metodu koju {~kimura2008} predlažu kao vlastitu, "
        "a to je pohlepni postupak koji u svakom koraku bira brid s najvećim izmjerenim "
        "smanjenjem dosega. Ona je jači protivnik od svakog topološkog kriterija i tek bi "
        "ona pokazala koliko prilagodljiva pretraga uistinu vrijedi.")

    t.p("Razlog zbog kojeg je nismo uključili nije načelan nego računski, i vrijedan je "
        "spomena jer je sam po sebi nalaz. Postupak kojim {~kimura2008} tu metodu "
        "ubrzavaju oslanja se na to da su vjerojatnosti u njihovoj mreži male i jednake, "
        "pa se procjena može temeljiti na velikoj većini realizacija. U našoj mreži "
        "vjerojatnosti sežu gotovo do jedinice, a upravo su bridovi s visokom "
        "vjerojatnošću oni koje se isplati ukloniti, pa bi ista računica zadržala tek "
        "nekolicinu realizacija.")

    t.p("Izlaz postoji i ne zahtijeva njihovu pretpostavku. Uklanjanje brida mijenja samo "
        "one realizacije u kojima je taj brid uopće prisutan, pa se doseg može rastaviti "
        "na dva dijela: onaj koji se ne mijenja i računa se jednom, i onaj koji se "
        "ponovno računa, i to samo na dijelu realizacija razmjernom vjerojatnosti brida:")

    t.eq(v("σ"), delim([v("D"), up(" ∪ {"), v("e"), up("}")]), up(" = "),
         frac(up("1"), v("M")),
         nary("∑", [v("m"), up(": "), v("e"), up(" ∉ "), sub(v("X"), v("m"))], None,
              [sub(v("r"), v("m")), delim(v("D"))]),
         up(" + "),
         frac(up("1"), v("M")),
         nary("∑", [v("m"), up(": "), v("e"), up(" ∈ "), sub(v("X"), v("m"))], None,
              [sub(v("r"), v("m")), delim([v("D"), up(" ∪ {"), v("e"), up("}")])]),
         label="sigmagreedy")

    t.p("Ovdje je ", sub(v("r"), v("m")), " doseg u ", v("m"), "-toj realizaciji. Prvi se "
        "zbroj računa jednom i dalje se ne mijenja, a ponavlja se samo drugi, i to na "
        "onoliko realizacija koliko ih brid ", v("e"), " uopće dodiruje. Procjena time "
        "ostaje točna i koristi cijeli uzorak, bez pretpostavke o jednakim "
        "vjerojatnostima.")


def _confidence(t):
    t.h2("Pouzdanija procjena rezultata", label="pouzdanost")

    t.p("Naposljetku, tri ograde iz poglavlja ", t.sec("rezultati"),
        " valja ukloniti prije nego što se zaključci prošire. Sve počiva na jednom sjemenu "
        "slučajnosti, pa bi ponavljanje s više njih pokazalo koliki je dio razlika među "
        "metodama stvaran, a koliki slučajan. Pretraga nikada nije gledala dalje od trećeg "
        "sloja, pa negativan nalaz o udaljenim bridovima vrijedi samo unutar te granice. "
        "Konačno, mjerenje je provedeno na jednoj mreži: nalaz da topologija osnovnog "
        "grafa ne razlikuje bridove posljedica je njezine osobito guste jezgre, pa bi "
        "mreža s izraženijim uskim grlima mogla dati sasvim drukčiju sliku, a upravo bi "
        "ona bila prava provjera mehanizma slojeva.")
