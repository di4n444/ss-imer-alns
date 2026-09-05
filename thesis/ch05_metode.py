"""5. Metode rješavanja.

Sources read for this chapter: Ropke & Pisinger (2006) throughout — their Algorithm 1
(the LNS skeleton), the roulette-wheel selection of eq. (20), the sigma1/sigma2/sigma3
score system and the segment-end weight update of section 3.4, the simulated-annealing
acceptance and start-temperature rule of section 3.5, the removal heuristics of section
3.1 with the y^p draw of their Algorithms 2 and 3, the Shaw relatedness measure of
eq. (17), and their own tuned parameter vector from section 4.3.2; Kimura et al. (2008)
for the sequential greedy over the measured objective and for the estimator whose
efficiency does not survive a heterogeneous transmission probability.

Every parameter value quoted here is read from code/config.py at build time rather than
retyped, so the text cannot drift from the code. The departures from Ropke & Pisinger are
listed explicitly in 5.2.8 rather than left for a reader to discover.
"""

import pandas as pd

from omml import acc, delim, frac, func, i, sub, sup, up, v
from params import config, hr

EDGES = None  # set by write()


def ifunc(name, argument):
    return [v(name), delim(argument)]


def _n(value, decimals=2):
    return f"{value:.{decimals}f}".replace(".", ",")


def write(t, figures):
    global EDGES
    EDGES = pd.read_csv(figures.parent / "data" / "edge_features.csv")

    t.h1("Metode rješavanja")

    t.p("Treće je poglavlje pokazalo da problem treba metodu koja mijenja više bridova "
        "odjednom, a četvrto je dalo kriterije kojima se bridovi ocjenjuju. Ovo poglavlje "
        "opisuje dvije metode koje se u radu uspoređuju: skup jednostavnih pohlepnih "
        "postupaka, koji služe kao referentna razina, i metaheuristiku ALNS, koja je "
        "glavni predmet rada.")

    _greedy(t)
    _alns(t, figures)


# ------------------------------------------------------------------ 5.1 ----

def _greedy(t):
    t.h2("Pohlepne metode", label="pohlepne")

    t.p("Najjednostavnija metoda uzima jedan od šest kriterija iz četvrtog poglavlja, "
        "ocijeni njime sve kandidatne bridove i uzme najboljih ", v("k"),
        ". Nema iteracija, nema kriterija prihvaćanja i nema slučajnosti osim kod "
        "slučajnog kriterija. Tako nastaje šest pohlepnih metoda, po jedna za svaki "
        "kriterij.")

    t.p("Dvije odluke o njihovoj izvedbi treba obrazložiti, jer bitno određuju što "
        "usporedba uopće mjeri.")

    t.p("Prva je da pohlepne metode biraju ", i("isključivo"),
        " među bridovima koji izravno izlaze iz izvora. To nije nedostatak kojim se "
        "protivnik namjerno slabi, nego definicija onoga što one predstavljaju: lokalnu "
        "karantenu, dakle najizravniji odgovor na pitanje kako ograničiti sumnjivog "
        "korisnika. Proširenje njihova skupa kandidata na udaljenije bridove metode "
        "zapravo pogoršava, jer fiksni kriterij na širem skupu bira bridove visoke ocjene "
        "koji su daleko od izvora i ne zatvaraju nijedan izlaz iz njega, pa kaskada i "
        "dalje slobodno kreće. Pitanje isplati li se gledati dalje od izvora zahtijeva "
        "prilagodbu tijekom pretraživanja, pa je to pitanje za metaheuristiku, a lokalna "
        "karantena poštena je nulta točka u odnosu na koju se odgovor mjeri.")

    t.p("Druga je da je odabir potpuno determinističan: bridovi se sortiraju po ocjeni "
        "silazno, a izjednačeni po identifikatorima krajeva (odjeljak ", t.sec("izjednacenost"), "). Time jedna "
        "trojka izvora, proračuna i kriterija ima točno jedan odgovor, uvijek isti. To "
        "znači i da se pohlepna rješenja računaju jednom i koriste za sve pokrete "
        "metaheuristike, umjesto da se nepotrebno ponavljaju za svako sjeme.")

    t.h3("Odnos prema metodama iz literature")

    t.p("Pri tumačenju rezultata važno je znati što ovih šest metoda jest, a što nije. To "
        "su upravo one metode koje {~kimura2008} koristi kao ", i("usporedne"),
        ", dakle međupoloženost, izlazni stupanj i slučajni odabir, ovdje proširene "
        "vjerojatnošću prijenosa, lokalnim mostom i spektralnim kriterijem. Metoda koju on "
        "sam predlaže bitno je drukčija: ona u svakom koraku bira brid koji ", i("izmjerena"),
        " procjena dosega najviše smanjuje, i to na mreži iz koje su prethodno odabrani "
        "bridovi već uklonjeni.")

    t.p("Usporedba u ovom radu stoga odgovara na pitanje može li prilagodljivo "
        "pretraživanje nadmašiti fiksni topološki kriterij, a ne na pitanje nadmašuje li "
        "ono najbolju poznatu metodu. Ta se razlika ovdje navodi izrijekom kako se "
        "rezultati ne bi čitali šire nego što dopuštaju.")

    # (1 - p_max) * M: the fraction of the frozen sample Kimura's estimator would keep for
    # the very edges most worth cutting. Computed, because it is the whole argument.
    p_max = float(EDGES.probability.max())
    effective = (1.0 - p_max) * config.SAA_SCENARIO_COUNT

    t.p("Vrijedi objasniti i zašto ta jača metoda ovdje nije izvedena. Postupak koji u "
        "svakom koraku mjeri doseg za svaki kandidatni brid izvediv je samo uz trik kojim "
        "{~kimura2008} izbjegava ponovno uzorkovanje: doseg nakon blokiranja brida "
        "procjenjuje se prosjekom po onim realizacijama u kojima taj brid ionako nije bio "
        "propustan. Broj upotrebljivih realizacija time pada na ",
        delim(up("1 − "), sub(v("p"), v("e"))), up(" · "), v("M"),
        ". Kimura radi s jedinstvenom vjerojatnošću od 0,2 odnosno 0,03, pa mu ostaje "
        "gotovo cijeli uzorak. U mreži Bitcoin Alpha vjerojatnosti sežu do ",
        _n(p_max, 3), ", pa bi za najpouzdanije bridove ostalo oko ",
        _n(effective, 1), " od ", hr(config.SAA_SCENARIO_COUNT),
        " realizacija — a upravo su ti bridovi oni koje najviše vrijedi presjeći. Trik "
        "dakle ne podnosi prijenos na mrežu s raznolikim vjerojatnostima, što je samo po "
        "sebi nalaz vrijedan spomena. Izvedba te metode ostaje kao prvi sljedeći korak, o "
        "čemu govori osmo poglavlje.")


# ------------------------------------------------------------------ 5.2 ----

def _alns(t, figures):
    t.h2("Prilagodljivo pretraživanje velikih okolina (ALNS)", label="alns")

    t.p("Metoda kojom se problem zapravo rješava je ", i("Adaptive Large Neighborhood Search"),
        ", koju za problem preuzimanja i dostave s vremenskim prozorima uvode "
        "{~ropke2006}. U ovom se radu prenosi na SS-IMER, uz razlike koje su navedene u "
        "odjeljku ", t.sec("odstupanja"), ".")

    _arhitektura(t, figures)
    _razaranje(t)
    _popravljanje(t)
    _slojevi(t, figures)
    _prihvacanje(t)
    _odstupanja(t)


def _arhitektura(t, figures):
    t.h3("Arhitektura i adaptivne težine")

    t.p("Polazna je ideja pretraživanja velikih okolina jednostavna. Umjesto da se rješenje "
        "gradi element po element, ono se u svakoj iteraciji djelomično ", i("razori"),
        " i zatim ", i("popravi"), ". Iz trenutačnog reza ", v("D"), " ukloni se ", v("q"),
        " bridova, koji se time vraćaju u mrežu, pa se rez nadopuni s ", v("q"),
        " novoodabranih bridova. Nastali se kandidat vrednuje i prihvaća ili odbacuje "
        "{ropke2006}.")

    t.p("Za problem iz trećeg poglavlja to je upravo ono što treba. Budući da se u jednoj "
        "iteraciji mijenja ", v("q"),
        " bridova odjednom, metoda može prijeći iz reza koji ne zatvara redundantne "
        "putove u onaj koji ih zatvara sve, bez potrebe da svaki međukorak bude poboljšanje. "
        "To je prepreka koju pohlepni postupak strukturno ne može svladati.")

    t.p("Pridjev ", i("prilagodljivo"),
        " odnosi se na sloj iznad te petlje. Umjesto jednog postupka razaranja i jednog "
        "postupka popravljanja, na raspolaganju ih je više, a onaj koji će se u iteraciji "
        "upotrijebiti bira se slučajno, s vjerojatnošću razmjernom težini {ropke2006}:")

    t.eq(up("P"), delim([up("odabran je postupak "), v("j")]), up(" = "),
         frac(sub(v("w"), v("j")), [sub(v("w"), v("i"))]),
         label="roulette")

    t.p("Postupak razaranja i postupak popravljanja biraju se neovisno jedan o drugome, "
        "kao dvije odvojene obitelji s vlastitim težinama {ropke2006}. Težine se ne "
        "zadaju unaprijed nego uče iz onoga što se tijekom pretraživanja dogodilo. ",
        t.figref("alnsloop"), " prikazuje jednu iteraciju i tu petlju učenja.")

    t.figure(figures / "fig5_1_alns_loop.png",
             "Jedna iteracija metode ALNS. Tri se odluke donose neovisno, svaka vlastitim "
             "kotačem sreće, a nagrada ostvarena u iteraciji vraća se svim mehanizmima "
             "koji su u njoj sudjelovali; težine se osvježavaju tek na kraju segmenta.",
             label="alnsloop")

    t.p("Pretraživanje je podijeljeno na segmente od ",
        str(config.ALNS_SEGMENT_LENGTH), " iteracija. Na početku segmenta svakom se "
        "postupku bodovi postave na nulu, a tijekom segmenta uvećavaju se jednim od tri "
        "iznosa {ropke2006}:")

    t.bullets([
        [sub(v("σ"), up("1")), " = ", str(config.ALNS_SIGMA1),
         " ako je iteracija dala novo, globalno najbolje rješenje;"],
        [sub(v("σ"), up("2")), " = ", str(config.ALNS_SIGMA2),
         " ako je rješenje bolje od trenutačnog i dosad neposjećeno;"],
        [sub(v("σ"), up("3")), " = ", str(config.ALNS_SIGMA3),
         " ako je rješenje lošije od trenutačnog i dosad neposjećeno, ali je ipak "
         "prihvaćeno."],
    ])

    t.p("Dvije pojedinosti tog sustava lako je previdjeti, a obje su bitne. Prvo, "
        "nagrađuju se samo ", i("neposjećena"),
        " rješenja: svaki se rez pamti, pa ponovni dolazak na isti rez ne donosi bodove "
        "ni kada bi inače zadovoljio uvjet. Time se potiču postupci koji otvaraju nova "
        "područja prostora rješenja, a ne oni koji kruže po istima {ropke2006}. Drugo, "
        "bodove dobivaju ", i("oba"),
        " postupka upotrijebljena u toj iteraciji, i to u istom iznosu, jer se ne može "
        "znati je li za uspjeh zaslužno razaranje ili popravljanje {ropke2006}. Rez koji "
        "je jednako dobar kao trenutačni pritom ne donosi ništa, jer ne pripada nijednom "
        "od tri navedena slučaja.")

    t.p("Na kraju segmenta težine se osvježavaju prema")

    t.eq(sub(v("w"), [v("i"), up(", "), v("j"), up(" + 1")]), up(" = "),
         sub(v("w"), [v("i"), up(", "), v("j")]), delim([up("1 − "), v("r")]),
         up(" + "), v("r"), frac(sub(v("π"), v("i")), sub(v("θ"), v("i"))),
         label="weights")

    t.p("gdje je ", sub(v("π"), v("i")), " zbroj bodova postupka ", v("i"),
        " u proteklom segmentu, ", sub(v("θ"), v("i")),
        " broj puta koliko je bio odabran, a ", v("r"), " = ",
        _n(config.ALNS_REACTION_FACTOR, 1),
        " faktor reakcije, koji određuje koliko brzo težine slijede nedavni uspjeh "
        "{ropke2006}. Postupak koji u segmentu nije bio odabran zadržava dotadašnju "
        "težinu; taj rubni slučaj izvorni rad ne spominje.")

    t.p("Petlja polazi od početnog rješenja koje čini ", v("k"),
        " nasumično odabranih bridova iz izvora. Odabir je namjerno slučajan, a ne "
        "napravljen nekim od kriterija: kada bi početno rješenje bilo izgrađeno jednim "
        "kriterijem, pripadni bi operator popravljanja krenuo s prednošću koju nije "
        "zaradio, pa usporedba kriterija ne bi bila poštena. Cjelokupna je petlja prikazana "
        "u ", t.coderef("alnskod"), ".")

    t.code([
        "D ← k nasumičnih bridova iz izvora",
        "D_best ← D",
        "T ← početna temperatura",
        "",
        "ponavljaj max_iter puta:",
        "    razaranje  ← kotač(težine razaranja)",
        "    kriterij   ← kotač(težine popravljanja)",
        "    sloj       ← kotač(težine slojeva)",
        "    q          ← slučajan cijeli broj iz [q_min, q_max]",
        "",
        "    D' ← D bez q bridova koje odabere razaranje",
        "    D' ← D' uz q novih bridova koje kriterij odabere iz sloja",
        "",
        "    ako je σ̂(D') < σ̂(D_best):  D_best ← D';  nagrada ← σ1",
        "    inače ako je D' već posjećen:            nagrada ← 0",
        "    inače ako je σ̂(D') < σ̂(D):               nagrada ← σ2",
        "    inače ako je D' prihvaćen:               nagrada ← σ3",
        "    inače:                                   nagrada ← 0",
        "",
        "    dodijeli nagradu svim trima mehanizmima",
        "    ako je D' prihvaćen:  D ← D'",
        "    T ← T · c",
        "",
        "    na kraju svakog segmenta: osvježi sve tri skupine težina",
        "",
        "vrati D_best",
    ], "Petlja metode ALNS prilagođena problemu SS-IMER.", label="alnskod")


def _razaranje(t):
    t.h3("Operatori razaranja", label="razaranje")

    t.p("Operator razaranja bira ", v("q"),
        " bridova koje treba izbaciti iz trenutačnog reza, čime se oni vraćaju u mrežu i "
        "oslobađaju proračun. Preuzeta su sva tri operatora koja navode {~ropke2006}.")

    t.p("Dva od njih koriste isti mehanizam slučajnog, ali pristranog odabira. Kandidati "
        "se poredaju od najboljeg prema najlošijem, izvuče se slučajan broj ", v("y"),
        " iz intervala ", delim(up("0, 1"), left="[", right=")"),
        " i uzme se kandidat na položaju")

    t.eq(up("⌊"), sup(v("y"), v("p")), up(" · "),
         delim(v("L"), left="|", right="|"), up("⌋"), label="ypdraw")

    t.p("u tom poretku, gdje je ", v("L"), " lista kandidata {ropke2006}. Veći ", v("p"),
        " odabir jače povlači prema vrhu liste, dok ", v("p"),
        " = 1 daje jednolik odabir. Time se u jednoj veličini ugađa odnos između "
        "pohlepnosti i istraživanja.")

    t.bullets([
        ["Slučajno razaranje uzima ", v("q"),
         " bridova iz reza jednoliko slučajno. To je gornji mehanizam uz ", v("p"),
         " = 1, izveden zasebno jer mu rangiranje uopće ne treba."],
        ["Razaranje najlošijih uklanja one bridove reza koji najmanje pridonose smanjenju "
         "dosega, dakle one koje je najjeftinije vratiti. Doprinos svakog brida mjeri se "
         "koliko bi doseg porastao kada bi se samo taj brid vratio u mrežu."],
        ["Srodno razaranje polazi od jednog nasumičnog brida reza i zatim uzastopno bira "
         "bridove srodne već odabranima. Zamisao je da se ukloni skupina međusobno "
         "povezanih bridova, jer ih popravljanje tada može zamijeniti nekom smislenom "
         "drugom skupinom, dok bi uklanjanje nepovezanih bridova dalo rez bez strukture."],
    ])

    t.p("Srodnost dvaju bridova mjeri se izrazom koji {~ropke2006} definiraju za svoj "
        "problem kao zbroj četiriju članova, pri čemu je svaki član skaliran na interval ",
        delim(up("0, 1"), left="[", right="]"),
        " i pomnožen vlastitom težinom. Prijenos na SS-IMER traži da se za svaki od tih "
        "članova pronađe odgovarajuća veličina, što prikazuje ", t.tabref("srodnost"), ".")

    t.table(
        ["Član kod Røpkea i Pisingera", "Težina", "Odgovarajuća veličina u SS-IMER-u"],
        [
            ["udaljenost mjesta preuzimanja i dostave", str(config.SHAW_PHI),
             "dijele li dva brida početni, odnosno završni čvor"],
            ["razlika u vremenu posluživanja", str(config.SHAW_CHI),
             "razlika u udaljenosti krajeva od izvora, mjerenoj brojem koraka"],
            ["razlika u količini tereta", str(config.SHAW_PSI),
             "razlika u vjerojatnosti prijenosa"],
            ["preklapanje skupova vozila koja mogu poslužiti zahtjev",
             str(config.SHAW_OMEGA),
             "preklapanje područja mreže do kojih se kroz brid dolazi"],
        ],
        "Preslikavanje četiriju članova mjere srodnosti {ropke2006} na veličine problema "
        "SS-IMER, s njihovim ugođenim težinama.",
        label="srodnost",
        widths_cm=[5.4, 1.8, 6.6])

    t.p("Zadnji član zaslužuje objašnjenje jer je za ovaj problem najvažniji. Kod "
        "{~ropke2006} on uspoređuje skupove vozila kojima se dva zahtjeva mogu poslužiti. "
        "Ovdje mu odgovara područje mreže u koje kaskada ulazi kroz brid, dakle skup "
        "čvorova dohvatljivih iz njegova završnog čvora unutar ograničenog broja koraka. "
        "Dva su brida srodna ako čuvaju isto područje. Ograničenje na malen broj koraka "
        "nije proizvoljno: mreža ima jako povezanu komponentu koja obuhvaća ",
        "veći dio čvorova (odjeljak ", t.sec("komponente"), "), pa bi neograničeni skup potomaka za gotovo svaki "
        "čvor bio gotovo cijela mreža i svi bi parovi izgledali jednako srodno.")

    t.p("Bez tog člana mjera srodnosti na ovom problemu izrođuje se. Unutar jednog sloja "
        "svi bridovi izlaze iz istog čvora i vode do čvorova jednako udaljenih od izvora, "
        "pa su prva dva člana ondje konstantna po konstrukciji; ostaje samo razlika u "
        "vjerojatnosti prijenosa, koja poprima svega deset vrijednosti (odjeljak ", t.sec("izjednacenost"), "). "
        "Srodno bi razaranje time postalo slučajno razaranje s dodatnim koracima. Tek "
        "kada sva četiri člana imaju svoj parnjak, ugođene težine iz izvornog rada imaju "
        "smisla; s jednim članom koji nedostaje njima ne bi bilo što vagati.")


def _popravljanje(t):
    t.h3("Operatori popravljanja")

    t.p("Operator popravljanja nadopunjuje rez do ", v("k"),
        " bridova. Njih je šest, po jedan za svaki kriterij iz četvrtog poglavlja, i "
        "svaki bira bridove koje njegov kriterij najbolje ocjenjuje. Time se natjecanje "
        "između kriterija odvija unutar samog pretraživanja: kotač sreće s vremenom "
        "povlašćuje one kriterije koji na toj instanci donose bodove.")

    t.p("Ovdje se javlja jedina razlika u odnosu na izvornu metodu koja nije stvar "
        "ugađanja nego nužnosti. Kod {~ropke2006} operatori popravljanja rade s "
        "kontinuiranim troškovima, gdje se točno izjednačene vrijednosti praktički ne "
        "pojavljuju, pa su ti operatori deterministički i slučajnost ulazi samo kroz "
        "razaranje. Naši kriteriji, međutim, izjednačuju mnogo bridova: lokalni most "
        "poprima dvije vrijednosti, a vjerojatnost prijenosa deset. Doslovan bi prijenos "
        "značio da ta dva operatora u svakom pokretanju vraćaju potpuno isti rez, čime bi "
        "prestali biti operatori pretraživanja.")

    t.p("Rješenje zadržava mehanizam izvornog rada i mijenja samo poredak nad kojim on "
        "djeluje: kandidati se poredaju po ocjeni, unutar skupina s jednakom ocjenom "
        "izmiješaju se slučajno, a zatim se primijeni isti pristrani odabir prema izrazu ",
        t.ref("ypdraw"), ". Pristranost prema vrhu ostaje, ali izbor unutar izjednačene "
        "skupine više nije unaprijed određen.")


def _slojevi(t, figures):
    t.h3("Slojevi udaljenosti od izvora", label="slojevi_sec")

    t.p("Preostaje pitanje iz kojeg dijela mreže operator popravljanja uopće smije birati. "
        "Primjer iz odjeljka ", t.sec("slozenost"), " pokazao je da najbolji rez ne mora ležati uz sam izvor: "
        "kada iz izvora vodi više redundantnih putova koji se nizvodno spajaju, jedan "
        "brid u uskom grlu vrijedi više od nekoliko bridova uz izvor. S druge strane, "
        "bridovi udaljeni od izvora u velikoj su većini nevažni, a ima ih neusporedivo "
        "više.")

    t.p("Kandidati se stoga razvrstavaju u slojeve prema udaljenosti od izvora: brid "
        "pripada sloju ", v("h"),
        " ako je njegov početni čvor od izvora udaljen ", v("h"),
        " koraka, mjereno pretraživanjem u širinu na polaznom grafu. Sloj 0 su bridovi "
        "koji izlaze izravno iz izvora, dakle upravo skup kandidata pohlepnih metoda. "
        "Razmatraju se slojevi do dubine ", str(config.ALNS_MAX_HOP_SCOPE),
        "; ta je granica parametar koji se ugađa (odjeljak ", t.sec("kalibracija"), "), a ne nalaz.")

    t.figure(figures / "fig5_2_hop_layers.png",
             "Shematski prikaz slojeva kandidata oko izvora. Svaka točka je jedan "
             "kandidatni brid, a svaki sljedeći sloj sadrži bitno više kandidata od "
             "prethodnoga; na stvarnoj mreži ta razlika doseže tri reda veličine.",
             label="slojevi")

    t.p("Odabir sloja povjeren je ", i("trećem"),
        " kotaču sreće, ravnopravnom s kotačima razaranja i popravljanja i osvježavanom "
        "istim pravilom. U svakoj se iteraciji izabere jedan sloj i popravljanje bridove "
        "traži u njemu; ako taj sloj ne može ponuditi dovoljno kandidata, ostatak se uzima "
        "iz preostalih slojeva, tako da rez uvijek ima točno ", v("k"),
        " bridova. Bodovi se pritom pripisuju sloju iz kojeg su bridovi ", i("stvarno"),
        " došli, a ne onomu koji je bio izabran, pri čemu svaki sloj koji je pridonio "
        "dobiva puni iznos nagrade — jednako kao što ga dobivaju i razaranje i "
        "popravljanje, i iz istog razloga {ropke2006}.")

    t.p("Svi slojevi kreću s jednakim težinama. To je namjerno: koliko se daleko od izvora "
        "isplati tražiti upravo je pitanje koje rad postavlja, pa bi početna prednost "
        "bilo kojem sloju značila da je odgovor unaprijed pretpostavljen.")

    t.h3("Zašto kotač, a ne rastući horizont")

    t.p("Prvotna izvedba ovog mehanizma bila je drukčija i vrijedi je opisati, jer je "
        "njezin neuspjeh sam po sebi metodološki nalaz. Umjesto kotača, pretraživanje je "
        "imalo rastući horizont: počinjalo je s prvim dvama slojevima i horizont je širilo "
        "kad god bi vanjski sloj u segmentu ostvario prosječnu nagradu veću od nule.")

    t.p("Taj se uvjet pokazao praznim. Sve su nagrade po konstrukciji nenegativne, jer je "
        "najmanji mogući iznos nula, pa je zahtjev da prosječna nagrada bude pozitivna "
        "sveden na zahtjev da je nagrada uopće ostvarena, što je gotovo uvijek istina. "
        "Horizont bi se stoga širio gotovo svaki segment i, kako mehanizam sužavanja nije "
        "postojao, više se nikad ne bi zatvorio. Nakon nekoliko segmenata skup kandidata "
        "obuhvaćao bi gotovo sve bridove dohvatljive iz izvora, a nekoliko bridova koji "
        "izvor zaista zatvaraju utopilo bi se u njima. Provjera na malim izvorima, kod "
        "kojih se svi rezovi mogu nabrojati pa je optimum poznat, pokazala je da je "
        "inačica s horizontom bila daleko od optimuma ondje gdje su inačice s nepromjenjivim "
        "skupom kandidata optimum redovito pogađale.")

    t.p("Kotač te dvije mane nema. Sloj koji prestane donositi bodove jednostavno gubi "
        "težinu, čime se sužavanje dobiva besplatno, a slojevi ostaju odvojeni umjesto da "
        "se stapaju u jedan veliki skup, pa sloj 0 zadržava svoje izglede.")

    t.h3("Što se iz naučenih težina smije zaključiti")

    t.p("Jedno ograničenje treba navesti prije rezultata, jer određuje što se iz njih "
        "smije pročitati. Slojevi se izrazito razlikuju po veličini, kako pokazuje ",
        t.figref("slojevi"),
        ", a na stvarnim izvorima ta razlika doseže tri reda veličine. Pristrani odabir "
        "prema izrazu ", t.ref("ypdraw"), " bira očekivano mjesto ",
        frac(delim(v("L"), left="|", right="|"), [v("p"), up(" + 1")]),
        " u poretku, pa isti ", v("p"),
        " u malom i u velikom sloju ne znači isto: u sloju od desetak bridova bira među "
        "najboljima, a u sloju od desetak tisuća duboko u sredini poretka.")

    t.p("Posljedica je da veća naučena težina sloja 0 dijelom mjeri i to da je taj sloj "
        "lakše pretražiti, a ne samo da su njegovi bridovi bolji. Naučene težine zato "
        "ostaju dijagnostika, a ne dokaz. Pitanje koje se postavlja glasi ", i("dolaze li"),
        " bridovi izvan sloja 0 uopće u najbolji rez, a odgovara mu se sastavom pronađenog "
        "reza i podatkom o tome iz kojeg su sloja došli bridovi koji su donijeli novo "
        "najbolje rješenje. Ta je asimetrija u našu korist: potvrdan nalaz razlika u "
        "veličini slojeva samo pojačava, jer je pronađen unatoč njoj, dok bi niječan nalaz "
        "trebalo tumačiti oprezno, budući da se tada ne bi moglo razlučiti jesu li "
        "udaljeniji bridovi nekorisni ili su njihovi slojevi jednostavno preveliki da bi "
        "se pretražili.")


def _prihvacanje(t):
    t.h3("Kriterij prihvaćanja i zaustavljanja")

    t.p("Kada bi se prihvaćala samo rješenja bolja od trenutačnog, pretraživanje bi se "
        "zaustavilo u prvom lokalnom minimumu. Zato se, kao i kod {~ropke2006}, koristi "
        "kriterij simuliranog kaljenja: rješenje bolje ili jednako dobro prihvaća se "
        "uvijek, a lošije s vjerojatnošću")

    t.eq(func("exp", [up("−"), frac([acc(v("σ")), delim(sup(v("D"), up("′"))), up(" − "),
                                     acc(v("σ")), delim(v("D"))], v("T"))]),
         label="sa")

    t.p("gdje je ", v("T"), " temperatura, koja se nakon svake iteracije množi faktorom "
        "hlađenja ", v("c"), " < 1. Pretraživanje time postupno prelazi iz istraživanja u "
        "usavršavanje.")

    t.p("Početna se temperatura ne zadaje izravno, nego izvodi iz početnog rješenja "
        "{ropke2006}: bira se tako da rješenje koje je za ", v("w"),
        " posto lošije od početnoga bude prihvaćeno s vjerojatnošću 0,5. Iz toga slijedi")

    t.eq(sub(v("T"), up("poč")), up(" = "),
         frac([v("w"), up(" · "), acc(v("σ")), delim(sub(v("D"), up("0")))],
              [up("ln 2")]),
         label="tstart")

    t.p("uz ", v("w"), " = ", _n(config.ALNS_START_TEMP_CONTROL, 2),
        ". Prednost je takvog izvoda što se temperatura sama prilagođava veličini izvora, "
        "a doseg se među izvorima razlikuje za tri reda veličine, pa bi jedna fiksna "
        "vrijednost bila prevruća za jedne i preledena za druge.")

    t.p("Faktor hlađenja nije preuzet od {~ropke2006}. Njihova vrijednost ima smisla "
        "isključivo uz njihov proračun od 25 000 iteracija; primijenjena na ovdje korištenih ",
        hr(config.ALNS_MAX_ITER), " iteracija ostavila bi temperaturu gotovo netaknutom. "
        "Umjesto toga ", v("c"),
        " se izvodi iz vlastitog proračuna iteracija tako da završna temperatura bude "
        "unaprijed određen mali udio početne.")

    t.p("Pretraživanje se zaustavlja nakon ", hr(config.ALNS_MAX_ITER),
        " iteracija ili ranije, čim doseg padne na jedan. Taj je slučaj, kako je pokazano "
        "u odjeljku ", t.sec("definicija"), ", dokazivo optimalan, pa nema smisla trošiti preostale iteracije na "
        "traženje nečega što je već pronađeno.")

    t.p("Napokon, broj bridova ", v("q"),
        " koji se u iteraciji mijenja bira se slučajno iz raspona razmjernog proračunu:")

    t.eq(sub(v("q"), up("min")), up(" = max"),
         delim([up("1, ⌊"), up(_n(config.ALNS_Q_MIN_FRAC, 1)), up(" · "), v("k"), up("⌋")]),
         up(",       "),
         sub(v("q"), up("max")), up(" = min"),
         delim([v("k"), up(" − 1, ⌊"), up(_n(config.ALNS_Q_MAX_FRAC, 1)), up(" · "),
                v("k"), up("⌋")]),
         label="qbounds")

    t.p("Izvorni rad ovdje propisuje najmanje četiri elementa, što je za proračune veličine "
        "kakvi se ovdje javljaju neupotrebljivo, jer ", v("k"),
        " zna biti i manji od četiri. Zadržana je stoga inačica razmjerna proračunu, koja "
        "uvijek mijenja barem jedan brid i uvijek barem jedan ostavlja na miru. Valja "
        "primijetiti da pri malom ", v("k"), " oba ruba padaju na jedan, pa se iteracija "
        "svodi na zamjenu jednog brida; ", v("q"),
        " se zato bilježi uz svaki rezultat, kako se ponašanje pri takvim proračunima ne bi "
        "tumačilo kao ponašanje metode općenito.")


def _odstupanja(t):
    t.h3("Odstupanja od izvorne metode", label="odstupanja")

    t.p("Radi preglednosti, ", t.tabref("odstupanja"),
        " objedinjuje sva mjesta na kojima izvedba svjesno odstupa od izvorne metode "
        "{ropke2006}, zajedno s razlogom. Ostatak metode slijedi izvorni rad doslovno.")

    t.table(
        ["Odstupanje", "Razlog"],
        [
            ["kotač slojeva udaljenosti",
             "izvorna metoda nema pojam ograničenog skupa kandidata; to je dodatak ovog "
             "rada, bodovan njihovim pravilom"],
            ["popravljanje koristi pristrani slučajni odabir",
             "njihovi su operatori popravljanja deterministički, što bi kod naših "
             "izjednačenih ocjena dalo uvijek isti rez"],
            ["granice za q razmjerne proračunu",
             "njihova donja granica od četiri elementa nije definirana za ovako male "
             "proračune"],
            ["faktor hlađenja izveden iz vlastitog proračuna iteracija",
             "njihova je vrijednost ugođena za 25 000 iteracija"],
            ["razaranje najlošijih rangira jednom",
             "doslovno rangiranje pri svakom izboru zahtijeva ponovni prolaz kroz sve "
             "realizacije i višestruko poskupljuje pokretanje"],
            ["šum u funkciji cilja nije prenesen",
             "definiran je preko matrice udaljenosti, čega ovdje nema"],
        ],
        "Svjesna odstupanja izvedbe od metode {ropke2006}.",
        label="odstupanja",
        widths_cm=[5.6, 8.2])
