"""6. Implementacija i eksperimentalni postav.

Describes the system that produces the results, so nearly all of it is our own rather than
read from a source.

Four sections: architecture, frozen scenarios, source sample, measures and protocol.
Parameter calibration is deliberately not here - it was run, every default held, and a
tuning step that changed nothing is not a result. It is recorded in REPORT.md instead.

Numbers come from data/sample.csv and code/config.py at build time, never retyped.
"""

import pandas as pd

from omml import delim, i, up, v
from params import config, count, hr

SAMPLE = None  # set by write()


def ifunc(name, argument):
    return [v(name), delim(argument)]


def write(t, figures):
    global SAMPLE
    SAMPLE = pd.read_csv(figures.parent / "data" / "sample.csv")

    t.h1("Implementacija i eksperimentalni postav")

    t.p("Ovo poglavlje opisuje sustav koji provodi metode iz petog poglavlja: kako je "
        "podijeljen, kako su pripremljene realizacije nad kojima se mjeri, kako su odabrani "
        "izvori i što se točno bilježi za svako pokretanje.")

    _arhitektura(t, figures)
    _realizacije(t)
    _uzorak(t)
    _protokol(t)


# ------------------------------------------------------------------ 6.1 ----

def _arhitektura(t, figures):
    t.h2("Arhitektura implementacije", label="arhitektura")

    t.p("Sustav je napisan u programskom jeziku Python. Za izgradnju grafa i jednokratne "
        "izračune nad njim koristi se knjižnica igraph, dok je obilazak grafa unutar petlje "
        "pretraživanja napisan izravno, nad običnim listama susjedstva, jer je u toj ulozi "
        "brži od poziva knjižnice.")

    t.p("Cijela je izvedba organizirana oko jednog pravila: sve što se može izračunati iz "
        "nepromjenjivog grafa računa se jednom i pamti, a nikada unutar petlje. Razlog je u "
        "odnosu veličina — jedno pokretanje izvodi stotine iteracija, a svaka iteracija "
        "vrednuje kandidatni rez na svih ", hr(config.SAA_SCENARIO_COUNT),
        " realizacija, pa bi svaki dodatni obilazak grafa po iteraciji bio pomnožen "
        "stotinama tisuća puta. ", t.figref("pipeline"),
        " prikazuje tu podjelu: iznad crte je ono što se plaća jednom, ispod nje ono što se "
        "plaća u svakoj iteraciji.")

    t.figure(figures / "fig6_1_pipeline.png",
             "Tijek obrade. Obilježja bridova i realizacije računaju se jednom po grafu, "
             "kontekst izvora jednom po izvoru, a jedino se procjena dosega izvodi za svaki "
             "kandidatni rez.",
             label="pipeline")

    t.p("Obilježja se prema tome dijele u dvije razine. Globalna obilježja — vjerojatnost "
        "prijenosa, zbroj stupnjeva, oznaka lokalnog mosta i spektralna ocjena — izračunaju "
        "se jednom za cijeli graf. Obilježja koja ovise o izvoru, dakle međupoloženost iz "
        "izvora i razvrstavanje bridova u slojeve, računaju se jednom po izvoru i zatim "
        "koriste za sve proračune, sve metode i sve iteracije za taj izvor. Oboje se u "
        "trenutku pretraživanja svodi na čitanje iz tablice. Međupoloženost i slojevi "
        "dobivaju se pritom iz istog jednog obilaska u širinu: obilazak usput daje "
        "udaljenost svakog čvora od izvora, a povratni prolaz kroz posjećene čvorove u "
        "obrnutom redoslijedu akumulira udjele najkraćih putova po bridovima {predavanja}.")

    t.p("Procjena dosega troši oko devedeset posto vremena pokretanja, pa su tri odluke u "
        "njoj donesene u korist brzine. Prvo, rez se nikada ne primjenjuje na samu "
        "realizaciju: realizacije su nepromjenjive, a rez se poštuje tako da se tijekom "
        "obilaska prijelaz preko presječenog brida preskoči, čime se izbjegava izgradnja "
        "novog grafa za svaki od stotina kandidatnih rezova. Drugo, obilazak ne treba "
        "redoslijed čvorova nego samo veličinu dosegnutog skupa, pa se izvodi nad stogom, a "
        "posjećenost se bilježi u polju koje se između poziva ne briše nego se povećava "
        "brojač generacije.")

    t.p("Treće, razaranje najlošijih iz odjeljka ", t.sec("razaranje"),
        " treba doseg reza bez svakog pojedinog njegovog brida, što bi naivno značilo ",
        delim(v("D"), left="|", right="|"),
        " + 1 potpunih obilazaka po realizaciji. Umjesto toga koristi se opažanje da "
        "vraćanje brida u mrežu može dodati samo čvorove do kojih se dolazi ", i("kroz njega"),
        ", pa je njegov doprinos nula osim ako je taj brid u toj realizaciji propustan, "
        "njegov početni čvor dohvatljiv, a završni nije. Tek se tada obilazi dio grafa, i to "
        "onaj koji dotad nije posjećen, pa se svi doprinosi dobiju u jednom prolazu.")

    t.p("Zbog tih je optimizacija provjera ispravnosti dio sustava, a ne naknadna misao. "
        "Procjena dosega provjerava se protiv neovisne, namjerno spore izvedbe: svaka se "
        "realizacija ponovno izgradi kao pravi graf, iz njega se obrišu bridovi reza i "
        "dohvatljivi se skup izračuna funkcijom knjižnice, čime se brza izvedba mjeri prema "
        "nečemu s čime ne dijeli nijednu pretpostavku. Druga vrsta provjere brani od "
        "pogreške koja se ne očituje iznimkom nego uvjerljivim krivim brojem: obilježja su "
        "indeksirana unutarnjim poretkom čvorova u knjižnici, koji ne mora odgovarati "
        "poretku izvornih identifikatora, pa bi se pri razmimoilaženju ocjene pridružile "
        "krivim bridovima, a rezultat bi i dalje izgledao razumno. Zato se pri svakoj "
        "izgradnji grafa i pri svakom učitavanju tablice obilježja poklapanje tih poredaka "
        "provjerava i pogreška se odmah prijavljuje.")


# ------------------------------------------------------------------ 6.2 ----

def _realizacije(t):
    t.h2("Zamrznuti skupovi realizacija", label="realizacije")

    t.p("Kako je opisano u odjeljku ", t.sec("procjena"), ", koriste se dva odvojena skupa ",
        i("live-edge"), " realizacija: uži za pretraživanje i širi za konačno vrednovanje. "
        "Oba se generiraju jednom, svaki iz vlastitog sjemena generatora slučajnih brojeva, "
        "i nakon toga se više ne mijenjaju.")

    t.p("Za svaki se brid neovisno baci novčić s njegovom vjerojatnošću prijenosa, a "
        "realizacija se pohranjuje kao lista susjedstva koja sadrži samo propusne bridove. "
        "Ishod bacanja time je ugrađen u samu strukturu, pa se tijekom obilaska više ne "
        "provjerava. Uži skup ima ",
        count(config.SAA_SCENARIO_COUNT, "realizaciju", "realizacije", "realizacija"),
        ", a širi ",
        count(config.MC_SCENARIO_COUNT, "realizaciju", "realizacije", "realizacija"), ".")

    t.p("Tri su svojstva tih skupova provjerena, jer bi njihov izostanak neprimjetno "
        "obezvrijedio sve izmjerene brojeve. Skupovi se iz istog sjemena reproduciraju u "
        "potpunosti, uključujući i redoslijed susjeda unutar liste, a ne samo kao jednaki "
        "skupovi bridova; bez toga dva pokretanja izvedena u različito vrijeme ne bi bila "
        "usporediva. Dva skupa nemaju nijednu zajedničku realizaciju, pa je konačno "
        "vrednovanje doista izvan uzorka nad kojim se pretraživalo. Naposljetku, nakon "
        "pokretanja svih metoda svaka je realizacija ostala nepromijenjena do zadnjeg bita, "
        "čime je potvrđeno da se rez zaista primjenjuje kao maska, a ne izmjenom zamrznute "
        "strukture.")


# ------------------------------------------------------------------ 6.3 ----

def _uzorak(t):
    t.h2("Uzorak izvora", label="uzorak")

    t.p("Metode se ne mogu vrednovati na svim čvorovima mreže, ali ni na proizvoljno "
        "odabranima. Odjeljak ", t.sec("populacija"),
        " pokazao je dvije stvari koje ograničavaju odabir: većina čvorova ima premalo "
        "izlaznih bridova da bi podnijela i najmanji razmatrani proračun, a doseg se među "
        "preostalima mijenja kroz cijeli raspon, bez prirodne podjele u skupine.")

    t.p("Uzorak je zato slojevit po dvjema osima istodobno, a svaka kombinacija pojasa "
        "jedne i razreda druge osi čini jednu skupinu izvora iz koje se zasebno izvlači. "
        "Prva je os izlazni stupanj izvora, jer on ", i("jest"),
        " skup kandidata sloja 0, pa određuje i koji se proračuni mogu proučavati i koliko "
        "je pretraživanje teško. Druga je doseg neizmijenjene mreže, jer o njemu ovisi "
        "trajanje pokretanja, a topološki različiti čvorovi mogu imati praktički jednak "
        "doseg, pa jedna os ne bi bila dovoljna. Osobito su zanimljive skupine izvan "
        "dijagonale, dakle izvori s malo izlaznih bridova koji ipak dosežu velik dio mreže: "
        "upravo je to geometrija iz odjeljka ", t.sec("slozenost"),
        ", u kojoj nekoliko veza vodi prema velikoj komponenti, pa se najbolji rez ne mora "
        "nalaziti uz sam izvor.")

    calib = SAMPLE[SAMPLE.role == "calibration"]
    measure = SAMPLE[SAMPLE.role == "measurement"]

    t.p("Iz svake se skupine izvlači unaprijed određen broj izvora, i to tako da se najprije "
        "uzmu izvori namijenjeni pripremnim pokretanjima, a mjerni izvori tek iz preostalih. "
        "Time su ta dva skupa razdvojena po konstrukciji, a ne po disciplini onoga tko "
        "pokreće eksperiment. Izvučeno je ", count(len(measure), "izvor", "izvora", "izvora"),
        " za mjerenje i ", count(len(calib), "izvor", "izvora", "izvora"),
        " za pripremu, raspoređenih po ",
        count(SAMPLE.cell.nunique(), "skupini", "skupine", "skupina"),
        ". Uzorak je izvučen jednom, iz jednog sjemena, i jedini je uzorak koji se u radu "
        "koristi.")

    t.p("Jedna skupina zaslužuje napomenu: izvora s više od pedeset izlaznih bridova koji "
        "ipak imaju malen doseg u cijeloj mreži ima svega jedan, pa ta skupina ne može "
        "popuniti mjerni dio uzorka. To nije nedostatak uzorkovanja nego svojstvo mreže — "
        "čvorovi visokog izlaznog stupnja gotovo su bez iznimke i čvorovi velikog dosega. "
        "Uz svaki se izvor bilježi i predviđeno trajanje pokretanja, izračunato iz njegova "
        "dosega, jer trajanje prati doseg a ne broj izvora, pa jedan zasićen izvor stoji kao "
        "dvadesetak onih malog dosega; zahvaljujući tomu cijena plana mjerenja može se "
        "procijeniti prije nego što se išta pokrene.")


# ------------------------------------------------------------------ 6.4 ----

def _protokol(t):
    t.h2("Mjere i protokol mjerenja", label="protokol")

    t.p("Uspješnost se izvještava relativnim smanjenjem dosega iz izraza ",
        t.ref("reduction"),
        ", i to uvijek dvaput: jednom nad užim skupom realizacija, nad kojim je "
        "pretraživanje radilo, i jednom nad širim, koji pretraživanje nije vidjelo. Bilježi "
        "se i njihova razlika, koja nije pomoćni podatak nego mjera koliko je pronađeni rez "
        "prilagođen vlastitom uzorku; budući da rez može pobijediti unutar uzorka i izgubiti "
        "izvan njega, izvještavanje samo jedne od tih vrijednosti tu bi pojavu sakrilo "
        "umjesto izmjerilo.")

    t.p("Svako pokretanje daje jedan redak, i to jedan redak ", i("po metodi"),
        ". Ta naizgled sitna odluka ima razlog: kada bi se u redak upisao stupac tipa "
        "„najbolja suparnička metoda”, a u skup suparnika pritom uvrstila i sama metoda koja "
        "se ocjenjuje, taj stupac nikada ne bi mogao pokazati da je ona izgubila. Veličine "
        "poput najboljeg pohlepnog rezultata zato se ne zapisuju tijekom mjerenja, nego "
        "računaju naknadno, grupiranjem redaka.")

    t.p("Uz svaki se redak zapisuju i sve razriješene vrijednosti parametara metode, pa se "
        "iz samog retka vidi pod kojim je postavkama nastao. Zapisuje se i razlog "
        "zaustavljanja, čime se izdvajaju instance riješene trivijalno, dakle one u kojima "
        "proračun dopušta potpuno izoliranje izvora; njih treba isključiti iz prosjeka jer u "
        "njima svaka metoda postiže isti, dokazivo optimalan rezultat.")

    t.p("Naposljetku, o slučajnosti. Pet od šest pohlepnih metoda posve je "
        "determinističko, pa im je rezultat jednoznačan i računa se jednom. Slučajna "
        "pohlepna metoda i metaheuristika ovise o sjemenu generatora slučajnih brojeva, "
        "koje se zato bilježi uz svaki rezultat, tako da je svako pokretanje moguće "
        "ponoviti. Koliko ishod ovisi o izboru među jednako ocijenjenim bridovima "
        "(odjeljak ", t.sec("izjednacenost"),
        ") može se utvrditi jedino ponavljanjem istog pokretanja s više sjemena; to je "
        "mjerenje zbog svoje cijene ostavljeno kao zasebno pitanje, o kojem govori osmo "
        "poglavlje. Ondje gdje se više sjemena koristi, raspršenje se prikazuje kao "
        "svojstvo metode, a ne usrednjuje.")
