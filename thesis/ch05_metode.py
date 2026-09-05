"""5. Metode rjesavanja.

Sources: Ropke & Pisinger (2006) throughout - the LNS skeleton of their Algorithm 1, the
roulette-wheel selection of eq. (20), the sigma1/sigma2/sigma3 score system and segment-end
weight update of section 3.4, the simulated-annealing acceptance and start-temperature rule
of section 3.5, the removal heuristics of section 3.1 with the y^p draw of Algorithms 2
and 3, the Shaw relatedness of eq. (17), and their tuned parameter vector from 4.3.2;
Kimura et al. (2008) for the sequential greedy over the measured objective.

Structure is fixed: 5.1 greedy, then 5.2 with exactly five subsections - architecture,
destroy, repair, hop layers, acceptance. The chapter describes the architecture as it
stands and justifies it; it does not narrate alternatives that were tried and dropped.

Parameter values are read from code/config.py at build time rather than retyped.
"""

from omml import acc, delim, frac, func, i, sub, sup, up, v
from params import config, hr


def ifunc(name, argument):
    return [v(name), delim(argument)]


def _n(value, decimals=2):
    return f"{value:.{decimals}f}".replace(".", ",")


def write(t, figures):
    t.h1("Metode rješavanja")

    t.p("Treće je poglavlje pokazalo da problem traži metodu koja mijenja više bridova "
        "odjednom, a četvrto je dalo kriterije kojima se bridovi ocjenjuju. Ovo poglavlje "
        "opisuje dvije metode koje se u radu uspoređuju: skup jednostavnih pohlepnih "
        "postupaka, koji služe kao referentna razina, i metaheuristiku ALNS, koja je glavni "
        "predmet rada.")

    _greedy(t)
    _alns(t, figures)


# ------------------------------------------------------------------ 5.1 ----

def _greedy(t):
    t.h2("Pohlepne metode", label="pohlepne")

    t.p("Najjednostavnija metoda uzima jedan od šest kriterija iz četvrtog poglavlja, "
        "ocijeni njime sve kandidatne bridove i uzme najboljih ", v("k"),
        ". Nema iteracija, nema kriterija prihvaćanja i nema slučajnosti osim kod slučajnog "
        "kriterija. Tako nastaje šest pohlepnih metoda, po jedna za svaki kriterij.")

    t.p("Njihov je skup kandidata ograničen na bridove koji izravno izlaze iz izvora. To "
        "nije slabljenje protivnika nego definicija onoga što one predstavljaju: lokalnu "
        "karantenu, dakle najizravniji odgovor na pitanje kako ograničiti sumnjivog "
        "korisnika. Fiksni kriterij na širem skupu kandidata birao bi bridove visoke ocjene "
        "daleko od izvora, koji ne zatvaraju nijedan izlaz iz njega, pa je pitanje isplati "
        "li se gledati dalje od izvora pitanje za metaheuristiku, a lokalna karantena "
        "poštena nulta točka u odnosu na koju se odgovor mjeri.")

    t.p("Odabir je uz to potpuno determinističan: bridovi se sortiraju po ocjeni silazno, a "
        "izjednačeni po identifikatorima krajeva (odjeljak ", t.sec("izjednacenost"),
        "). Time jedna trojka izvora, proračuna i kriterija ima točno jedan odgovor, uvijek "
        "isti, pa se pohlepna rješenja računaju jednom i koriste za sve pokrete "
        "metaheuristike.")

    t.p("Pri tumačenju rezultata važno je znati što ovih šest metoda jest, a što nije. To "
        "su upravo one metode koje {~kimura2008} koriste kao ", i("usporedne"),
        " — međupoloženost, izlazni stupanj i slučajni odabir — ovdje proširene "
        "vjerojatnošću prijenosa, lokalnim mostom i spektralnim kriterijem. Metoda koju oni "
        "sami predlažu bitno je drukčija: u svakom koraku bira brid koji ", i("izmjerena"),
        " procjena dosega najviše smanjuje, i to na mreži iz koje su prethodno odabrani "
        "bridovi već uklonjeni. Usporedba u ovom radu stoga odgovara na pitanje može li "
        "prilagodljivo pretraživanje nadmašiti fiksni topološki kriterij, a ne na pitanje "
        "nadmašuje li ono najbolju poznatu metodu; ta se razlika navodi izrijekom kako se "
        "rezultati ne bi čitali šire nego što dopuštaju. Razlozi zbog kojih ta jača metoda "
        "ovdje nije izvedena i način na koji bi se mogla izvesti opisani su u osmom "
        "poglavlju.")


# ------------------------------------------------------------------ 5.2 ----

def _alns(t, figures):
    t.h2("Metaheuristika ALNS", label="alns")

    t.p("Metoda kojom se problem zapravo rješava je prilagodljivo pretraživanje velikih "
        "okolina, u literaturi poznato pod engleskim nazivom ",
        i("Adaptive Large Neighborhood Search"), " i kraticom ALNS, koju za problem "
        "preuzimanja i dostave s vremenskim prozorima uvode {~ropke2006}. Naziv se ne "
        "prevodi, pa se u nastavku koristi kratica. Opisuje se prilagodba metode problemu "
        "SS-IMER, a mjesta na kojima izvedba svjesno odstupa od izvorne navedena su uz "
        "svaki dio na koji se odnose.")

    _arhitektura(t, figures)
    _razaranje(t)
    _popravljanje(t)
    _slojevi(t, figures)
    _prihvacanje(t)


def _arhitektura(t, figures):
    t.h3("Arhitektura i adaptivne težine")

    t.p("Polazna je ideja jednostavna. Umjesto da se rješenje "
        "gradi element po element, ono se u svakoj iteraciji djelomično ", i("razori"),
        " i zatim ", i("popravi"), ": iz trenutačnog reza ", v("D"), " ukloni se ", v("q"),
        " bridova, koji se time vraćaju u mrežu, pa se rez nadopuni s ", v("q"),
        " novoodabranih bridova, a nastali se kandidat vrednuje i prihvaća ili odbacuje "
        "{ropke2006}. Za problem iz trećeg poglavlja to je upravo ono što treba: budući da "
        "se mijenja ", v("q"), " bridova odjednom, metoda može prijeći iz reza koji ne "
        "zatvara redundantne putove u onaj koji ih zatvara sve, bez potrebe da svaki "
        "međukorak bude poboljšanje. To je prepreka koju pohlepni postupak strukturno ne "
        "može svladati.")

    t.p("Prilagodljivom je metodu čini sloj iznad te petlje. Umjesto jednog postupka razaranja i jednog "
        "postupka popravljanja na raspolaganju ih je više, a onaj koji će se u iteraciji "
        "upotrijebiti bira se slučajno, s vjerojatnošću razmjernom težini {ropke2006}:")

    t.eq(up("P"), delim([up("odabran je postupak "), v("j")]), up(" = "),
         frac(sub(v("w"), v("j")), [sub(v("w"), v("i"))]),
         label="roulette")

    t.p("Postupak razaranja i postupak popravljanja biraju se neovisno jedan o drugome, kao "
        "dvije odvojene obitelji s vlastitim težinama {ropke2006}, a težine se ne zadaju "
        "unaprijed nego uče iz onoga što se tijekom pretraživanja dogodilo. ",
        t.figref("alnsloop"), " prikazuje jednu iteraciju metode ALNS i tu petlju učenja.")

    t.figure(figures / "fig5_1_alns_loop.png",
             "Jedna iteracija metode ALNS. Tri se odluke donose neovisno, svaka vlastitim "
             "kotačem sreće, a nagrada ostvarena u iteraciji vraća se svim mehanizmima koji "
             "su u njoj sudjelovali; težine se osvježavaju tek na kraju segmenta.",
             label="alnsloop")

    t.p("Pretraživanje je podijeljeno na segmente od ",
        str(config.ALNS_SEGMENT_LENGTH),
        " iteracija. Na početku segmenta bodovi svakog postupka postave se na nulu, a "
        "tijekom segmenta uvećavaju se jednim od tri iznosa {ropke2006}: ",
        sub(v("σ"), up("1")), " = ", str(config.ALNS_SIGMA1),
        " ako je iteracija dala novo, globalno najbolje rješenje; ",
        sub(v("σ"), up("2")), " = ", str(config.ALNS_SIGMA2),
        " ako je rješenje bolje od trenutačnog i dosad neposjećeno; te ",
        sub(v("σ"), up("3")), " = ", str(config.ALNS_SIGMA3),
        " ako je rješenje lošije od trenutačnog i dosad neposjećeno, ali je ipak "
        "prihvaćeno.")

    t.p("Dvije pojedinosti tog sustava lako je previdjeti, a obje su bitne. Prvo, nagrađuju "
        "se samo ", i("neposjećena"),
        " rješenja: svaki se rez pamti, pa ponovni dolazak na isti rez ne donosi bodove ni "
        "kada bi inače zadovoljio uvjet, čime se potiču postupci koji otvaraju nova "
        "područja prostora rješenja umjesto da kruže po istima {ropke2006}. Drugo, bodove "
        "dobivaju ", i("oba"),
        " postupka upotrijebljena u toj iteraciji, i to u istom iznosu, jer se ne može "
        "znati je li za uspjeh zaslužno razaranje ili popravljanje {ropke2006}. Rez jednako "
        "dobar kao trenutačni pritom ne donosi ništa, jer ne pripada nijednom od tri "
        "navedena slučaja.")

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
        "{ropke2006}. Postupak koji u segmentu nije bio odabran zadržava dotadašnju težinu.")

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

    t.p("Dva od njih koriste isti mehanizam slučajnog, ali pristranog odabira: kandidati se "
        "poredaju od najboljeg prema najlošijem, izvuče se slučajan broj ", v("y"),
        " iz intervala ", delim(up("0, 1"), left="[", right=")"),
        " i uzme se kandidat na položaju")

    t.eq(up("⌊"), sup(v("y"), v("p")), up(" · "),
         delim(v("L"), left="|", right="|"), up("⌋"), label="ypdraw")

    t.p("u tom poretku, gdje je ", v("L"), " lista kandidata {ropke2006}. Veći ", v("p"),
        " odabir jače povlači prema vrhu liste, dok ", v("p"),
        " = 1 daje jednolik odabir, pa se jednom veličinom ugađa odnos između pohlepnosti i "
        "istraživanja.")

    t.bullets([
        ["Slučajno razaranje uzima ", v("q"),
         " bridova iz reza jednoliko slučajno; to je gornji mehanizam uz ", v("p"),
         " = 1, izveden zasebno jer mu rangiranje uopće ne treba."],
        ["Razaranje najlošijih uklanja one bridove reza koji najmanje pridonose smanjenju "
         "dosega, dakle one koje je najjeftinije vratiti. Doprinos svakog brida mjeri se "
         "time koliko bi doseg porastao kada bi se samo taj brid vratio u mrežu."],
        ["Srodno razaranje polazi od jednog nasumičnog brida reza i zatim uzastopno bira "
         "bridove srodne već odabranima. Zamisao je da se ukloni skupina međusobno "
         "povezanih bridova, jer ih popravljanje tada može zamijeniti nekom smislenom "
         "drugom skupinom, dok bi uklanjanje nepovezanih bridova dalo rez bez strukture."],
    ])

    t.p("Srodnost dvaju bridova mjeri se izrazom koji {~ropke2006} definiraju kao zbroj "
        "četiriju članova, svaki skaliran na jedinični interval i pomnožen vlastitom "
        "težinom. Prijenos na SS-IMER traži da se za svaki član pronađe odgovarajuća "
        "veličina, što prikazuje ", t.tabref("srodnost"), ".")

    t.table(
        ["Član kod Røpkea i Pisingera", "Težina", "Odgovarajuća veličina u SS-IMER-u"],
        [
            ["udaljenost mjesta preuzimanja i dostave", str(config.SHAW_PHI),
             "broj koraka između početnih, odnosno između završnih čvorova dvaju bridova"],
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

    t.p("Prvi član zahtijeva pojašnjenje jer je prijenos ovdje najmanje očit. Kod "
        "{~ropke2006} riječ je o zemljopisnoj udaljenosti dvaju mjesta, a čvorovi mreže "
        "nemaju položaj u prostoru. Sam je graf, međutim, metrički prostor, pa ulogu "
        "udaljenosti preuzima broj koraka između dvaju čvorova, mjeren bez obzira na smjer "
        "bridova i normiran najvećom udaljenošću u mreži. Dva su brida time bliska ako su "
        "im krajevi blizu u mreži, a ne samo ako ih dijele.")

    t.p("Posljednji član za ovaj je problem najvažniji. Kod {~ropke2006} on uspoređuje "
        "skupove vozila kojima se dva zahtjeva mogu poslužiti; ovdje mu odgovara područje "
        "mreže u koje kaskada ulazi kroz brid, dakle skup čvorova dohvatljivih iz njegova "
        "završnog čvora unutar ograničenog broja koraka, pa su dva brida srodna ako čuvaju "
        "isto područje. Bez njega bi mjera unutar jednog sloja izgubila velik dio "
        "razlučivosti: ondje svi bridovi izlaze iz istog čvora i vode do čvorova jednako "
        "udaljenih od izvora, pa su vremenski član i polovica prvog člana konstantni po "
        "konstrukciji, a vjerojatnost prijenosa poprima svega deset vrijednosti (odjeljak ",
        t.sec("izjednacenost"),
        "). Ograničenje na malen broj koraka također nije proizvoljno: mreža ima jako "
        "povezanu komponentu koja obuhvaća većinu čvorova (odjeljak ", t.sec("komponente"),
        "), pa bi neograničeni skup potomaka za gotovo svaki čvor bio gotovo cijela mreža i "
        "svi bi parovi izgledali jednako srodno.")


def _popravljanje(t):
    t.h3("Operatori popravljanja")

    t.p("Operator popravljanja nadopunjuje rez do ", v("k"),
        " bridova. Njih je šest, po jedan za svaki kriterij iz četvrtog poglavlja, i svaki "
        "bira bridove koje njegov kriterij najbolje ocjenjuje. Time se natjecanje između "
        "kriterija odvija unutar samog pretraživanja: kotač sreće s vremenom povlašćuje one "
        "kriterije koji na toj instanci donose bodove.")

    t.p("Ovdje se javlja razlika u odnosu na izvornu metodu koja nije stvar ugađanja nego "
        "nužnosti. Kod {~ropke2006} operatori popravljanja rade s kontinuiranim troškovima, "
        "gdje se točno izjednačene vrijednosti praktički ne pojavljuju, pa su ti operatori "
        "deterministički i slučajnost ulazi samo kroz razaranje. Naši kriteriji, međutim, "
        "izjednačuju mnogo bridova: lokalni most poprima dvije vrijednosti, a vjerojatnost "
        "prijenosa deset. Doslovan bi prijenos značio da ta dva operatora u svakom "
        "pokretanju vraćaju potpuno isti rez, čime bi prestali biti operatori "
        "pretraživanja.")

    t.p("Rješenje zadržava mehanizam izvornog rada i mijenja samo poredak nad kojim on "
        "djeluje: kandidati se poredaju po ocjeni, unutar skupina s jednakom ocjenom "
        "izmiješaju se slučajno, a zatim se primijeni isti pristrani odabir prema izrazu ",
        t.ref("ypdraw"), ". Pristranost prema vrhu ostaje, ali izbor unutar izjednačene "
        "skupine više nije unaprijed određen.")


def _slojevi(t, figures):
    t.h3("Slojevi udaljenosti od izvora", label="slojevi_sec")

    t.p("Preostaje pitanje iz kojeg dijela mreže operator popravljanja smije birati. "
        "Primjer iz odjeljka ", t.sec("slozenost"),
        " pokazao je da najbolji rez ne mora ležati uz sam izvor: kada iz izvora vodi više "
        "redundantnih putova koji se nizvodno spajaju, jedan brid u uskom grlu vrijedi više "
        "od nekoliko bridova uz izvor. S druge strane, bridovi udaljeni od izvora u velikoj "
        "su većini nevažni, a ima ih neusporedivo više.")

    t.p("Kandidati se stoga razvrstavaju u slojeve prema udaljenosti od izvora: brid "
        "pripada sloju ", v("h"), " ako je njegov početni čvor od izvora udaljen ", v("h"),
        " koraka, mjereno pretraživanjem u širinu na polaznom grafu. Sloj 0 su bridovi koji "
        "izlaze izravno iz izvora, dakle upravo skup kandidata pohlepnih metoda. "
        "Razmatraju se slojevi do dubine ", str(config.ALNS_MAX_HOP_SCOPE),
        ". Ta granica slijedi iz strukture mreže: prosječna duljina najkraćeg puta iznosi "
        "manje od četiri koraka (odjeljak ", t.sec("malisvijet"),
        "), pa treći sloj već obuhvaća veliku većinu bridova dohvatljivih iz izvora, dok "
        "svaki dublji sloj skup kandidata dodatno umnaža, a gotovo ne donosi bridove koji "
        "bi mogli zatvoriti put iz izvora.")

    t.figure(figures / "fig5_2_hop_layers.png",
             "Shematski prikaz slojeva kandidata oko izvora. Svaka točka je jedan kandidatni "
             "brid, a svaki sljedeći sloj sadrži bitno više kandidata od prethodnoga; na "
             "stvarnoj mreži ta razlika doseže tri reda veličine.",
             label="slojevi")

    t.p("Odabir sloja povjeren je ", i("trećem"),
        " kotaču sreće, ravnopravnom s kotačima razaranja i popravljanja i osvježavanom "
        "istim pravilom. U svakoj se iteraciji izabere jedan sloj i popravljanje bridove "
        "traži u njemu; ako taj sloj ne može ponuditi dovoljno kandidata, ostatak se uzima "
        "iz preostalih slojeva, tako da rez uvijek ima točno ", v("k"),
        " bridova. Bodovi se pritom pripisuju sloju iz kojeg su bridovi ", i("stvarno"),
        " došli, a ne onomu koji je bio izabran, pri čemu svaki sloj koji je pridonio dobiva "
        "puni iznos nagrade — jednako kao razaranje i popravljanje, i iz istog razloga "
        "{ropke2006}. Podjela nagrade razmjerno broju bridova pretpostavila bi da je doseg "
        "djeljiv po bridovima reza, a upravo je nedjeljivost ono što treće poglavlje "
        "pokazuje.")

    t.p("Kotač je odabran umjesto skupa kandidata koji bi se postupno širio prema van, jer "
        "se takvo širenje ne može poništiti: sloj koji se pokaže nekorisnim ostao bi u igri "
        "do kraja i razrjeđivao pretraživanje, dok kod kotača jednostavno gubi težinu. Svi "
        "slojevi kreću s jednakim težinama, jer je pitanje koliko se daleko od izvora "
        "isplati tražiti upravo ono koje rad postavlja.")

    t.p("Jedno ograničenje treba navesti već ovdje jer određuje što će se iz rezultata "
        "smjeti pročitati. Slojevi se izrazito razlikuju po veličini, pa ista pristranost "
        "odabira ne znači isto u sloju od desetak bridova i u sloju od desetak tisuća, zbog "
        "čega veća naučena težina sloja 0 dijelom mjeri i to da je taj sloj lakše "
        "pretražiti. Naučene težine stoga ostaju dijagnostika, a pitanje na koje se "
        "odgovara glasi ", i("dolaze li"), " bridovi izvan sloja 0 uopće u najbolji rez, na "
        "što odgovara sastav pronađenog reza.")


def _prihvacanje(t):
    t.h3("Kriterij prihvaćanja i zaustavljanja", label="prihvacanje")

    t.p("Kada bi se prihvaćala samo rješenja bolja od trenutačnog, pretraživanje bi se "
        "zaustavilo u prvom lokalnom minimumu. Zato se, kao i kod {~ropke2006}, koristi "
        "kriterij simuliranog kaljenja: rješenje bolje ili jednako dobro prihvaća se uvijek, "
        "a lošije s vjerojatnošću")

    t.eq(func("exp", [up("−"), frac([acc(v("σ")), delim(sup(v("D"), up("′"))), up(" − "),
                                     acc(v("σ")), delim(v("D"))], v("T"))]),
         label="sa")

    t.p("gdje je ", v("T"), " temperatura, koja se nakon svake iteracije množi faktorom "
        "hlađenja ", v("c"), " < 1, pa pretraživanje postupno prelazi iz istraživanja u "
        "usavršavanje. Početna se temperatura ne zadaje izravno, nego izvodi iz početnog "
        "rješenja {ropke2006}: bira se tako da rješenje koje je za ", v("w"),
        " posto lošije od početnoga bude prihvaćeno s vjerojatnošću 0,5, iz čega slijedi")

    t.eq(sub(v("T"), up("poč")), up(" = "),
         frac([v("w"), up(" · "), acc(v("σ")), delim(sub(v("D"), up("0")))], [up("ln 2")]),
         label="tstart")

    t.p("uz ", v("w"), " = ", _n(config.ALNS_START_TEMP_CONTROL, 2),
        ". Prednost je takvog izvoda što se temperatura sama prilagođava veličini izvora, a "
        "doseg se među izvorima razlikuje za tri reda veličine, pa bi jedna fiksna "
        "vrijednost bila prevruća za jedne i preledena za druge. Faktor hlađenja nije "
        "preuzet od {~ropke2006}, čija vrijednost ima smisla samo uz njihov proračun od "
        "25 000 iteracija; ovdje se izvodi iz vlastitog proračuna od ",
        hr(config.ALNS_MAX_ITER),
        " iteracija tako da završna temperatura bude unaprijed određen mali udio početne.")

    t.p("Pretraživanje se zaustavlja nakon ", hr(config.ALNS_MAX_ITER),
        " iteracija ili ranije, čim doseg padne na jedan, jer je taj slučaj prema odjeljku ",
        t.sec("definicija"), " dokazivo optimalan.")

    t.p("Naposljetku, broj bridova ", v("q"),
        " koji se u iteraciji mijenja bira se slučajno iz raspona razmjernog proračunu:")

    t.eq(sub(v("q"), up("min")), up(" = max"),
         delim([up("1, ⌊"), up(_n(config.ALNS_Q_MIN_FRAC, 1)), up(" · "), v("k"), up("⌋")]),
         up(",       "),
         sub(v("q"), up("max")), up(" = min"),
         delim([v("k"), up(" − 1, ⌊"), up(_n(config.ALNS_Q_MAX_FRAC, 1)), up(" · "),
                v("k"), up("⌋")]),
         label="qbounds")

    t.p("Izvorni rad ovdje propisuje najmanje četiri elementa, što je za ovako male "
        "proračune neupotrebljivo, jer ", v("k"),
        " zna biti i manji od četiri. Zadržana je stoga inačica razmjerna proračunu, koja "
        "uvijek mijenja barem jedan brid i uvijek barem jedan ostavlja na miru. Valja "
        "primijetiti da pri malom ", v("k"),
        " oba ruba padaju na jedan, pa se iteracija svodi na zamjenu jednog brida; ",
        v("q"), " se zato bilježi uz svaki rezultat, kako se ponašanje pri takvim "
        "proračunima ne bi tumačilo kao ponašanje metode općenito.")

    t.p("Time je opis metode potpun. Uz odstupanja navedena uz pojedine dijelove — kotač "
        "slojeva, koji u izvornoj metodi nema pandana, pristrani odabir pri popravljanju, "
        "granice za ", v("q"), " i faktor hlađenja — razlikuje se još samo razaranje "
        "najlošijih, koje kandidate rangira jednom umjesto pri svakom izboru, jer bi "
        "doslovno rangiranje tražilo ponovni prolaz kroz sve realizacije po svakom "
        "odabranom bridu. U svemu ostalome izvedba slijedi izvornu metodu doslovno.")
