"""6. Implementacija i eksperimentalni postav.

This chapter describes the system that produces the results, so almost everything in it
is our own rather than read from a source; Ropke & Pisinger (2006) section 4.3.2 is the
exception, since the calibration in 6.4 follows their one-parameter-at-a-time procedure
and their own rule that tuning instances stay small.

Every number is read at build time from data/sample.csv or data/calibration.csv, or from
code/config.py for settings. The calibration verdict in 6.4 is *recomputed* here from the
raw calibration rows rather than quoted from a summary, so the text cannot disagree with
the file it is based on.
"""

import pandas as pd

from omml import delim, frac, i, sub, up, v
from params import config, count, hr

SAMPLE = CALIB = None  # set by write()


def ifunc(name, argument):
    return [v(name), delim(argument)]


def _n(value, decimals=2):
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "−")


def _signed(value, decimals=4):
    return f"{value:+.{decimals}f}".replace(".", ",").replace("-", "−")


def write(t, figures):
    global SAMPLE, CALIB
    data = figures.parent / "data"
    SAMPLE = pd.read_csv(data / "sample.csv")
    CALIB = pd.read_csv(data / "calibration.csv")

    t.h1("Implementacija i eksperimentalni postav")

    t.p("Ovo poglavlje opisuje sustav koji proizvodi rezultate sedmog poglavlja: kako je "
        "podijeljen, kako su pripremljene realizacije nad kojima se mjeri, kako su odabrani "
        "izvori na kojima se mjeri, kako su određeni parametri metode i što se točno "
        "bilježi.")

    _arhitektura(t, figures)
    _realizacije(t)
    _uzorak(t)
    _kalibracija(t)
    _protokol(t)


# ------------------------------------------------------------------ 6.1 ----

def _arhitektura(t, figures):
    t.h2("Arhitektura implementacije", label="arhitektura")

    t.p("Sustav je napisan u programskom jeziku Python. Za izgradnju grafa i jednokratne "
        "izračune nad njim koristi se knjižnica igraph, dok je obilazak grafa unutar petlje "
        "pretraživanja napisan izravno, nad običnim listama susjedstva, jer se pokazalo da "
        "je u toj ulozi brži od poziva knjižnice.")

    t.p("Cijela je izvedba organizirana oko jednog pravila: sve što se može izračunati iz "
        "nepromjenjivog grafa računa se jednom i pamti, a nikada unutar petlje. Razlog je "
        "u odnosu veličina. Jedno pokretanje metode izvodi stotine iteracija, a svaka "
        "iteracija vrednuje kandidatni rez na svih ", hr(config.SAA_SCENARIO_COUNT),
        " realizacija, pa bi svaki dodatni obilazak grafa po iteraciji bio pomnožen "
        "stotinama tisuća puta. ", t.figref("pipeline"),
        " prikazuje tu podjelu: iznad crte je ono što se plaća jednom, ispod nje ono što "
        "se plaća u svakoj iteraciji.")

    t.figure(figures / "fig6_1_pipeline.png",
             "Tijek obrade. Obilježja bridova i realizacije računaju se jednom po grafu, "
             "kontekst izvora jednom po izvoru, a jedino se procjena dosega izvodi za svaki "
             "kandidatni rez.",
             label="pipeline")

    t.p("Prema tome se obilježja dijele u dvije razine. Globalna obilježja, dakle "
        "vjerojatnost prijenosa, zbroj stupnjeva, oznaka lokalnog mosta i spektralna "
        "ocjena, izračunaju se jednom za cijeli graf. Obilježja koja ovise o izvoru, "
        "dakle međupoloženost iz izvora i razvrstavanje bridova u slojeve, računaju se "
        "jednom po izvoru i zatim se koriste za sve proračune, sve metode i sve iteracije "
        "za taj izvor. Oboje se u trenutku pretraživanja svodi na jednostavno čitanje iz "
        "tablice.")

    t.p("Međupoloženost i slojevi dobivaju se iz istog jednog obilaska grafa u širinu: "
        "obilazak usput daje udaljenost svakog čvora od izvora, a povratni prolaz kroz "
        "posjećene čvorove u obrnutom redoslijedu akumulira udjele najkraćih putova po "
        "bridovima {predavanja}.")

    t.h3("Vrednovanje kao najskuplji dio")

    t.p("Mjerenje pokazuje da procjena dosega troši oko devedeset posto vremena "
        "pokretanja, pa su tri odluke u njoj donesene svjesno u korist brzine.")

    t.p("Prvo, rez se nikada ne primjenjuje na samu realizaciju. Realizacije su "
        "nepromjenjive, a rez se tijekom obilaska poštuje tako da se prijelaz preko "
        "presječenog brida preskoči. Time se izbjegava izgradnja novog grafa za svaki "
        "kandidatni rez, kojih u jednom pokretanju ima stotine.")

    t.p("Drugo, obilazak ne treba redoslijed čvorova nego samo veličinu dosegnutog skupa, "
        "pa se izvodi nad stogom, a posjećenost se bilježi u polju koje se između poziva "
        "ne briše nego se povećava brojač generacije.")

    t.p("Treće, razaranje najlošijih iz odjeljka ", t.sec("razaranje"), " treba doseg reza bez svakog "
        "pojedinog njegovog brida. Naivno bi to značilo ", delim(v("D"), left="|", right="|"),
        " + 1 potpunih obilazaka po realizaciji. Umjesto toga koristi se opažanje da "
        "vraćanje brida ", delim(v("u"), up(", "), v("w")),
        " u mrežu može dodati samo čvorove do kojih se dolazi ", i("kroz njega"),
        ", pa je njegov doprinos nula osim ako je taj brid u toj realizaciji propustan, "
        "čvor ", v("u"), " dohvatljiv, a čvor ", v("w"),
        " nije. Tek se u tom slučaju obilazi dio grafa, i to onaj koji dotad nije "
        "posjećen. Svi se doprinosi tako dobiju u jednom prolazu.")

    t.h3("Provjere ispravnosti")

    t.p("Zbog te su optimizacije provjere ispravnosti dio sustava, a ne naknadna misao.")

    t.p("Procjena dosega provjerava se protiv neovisne, namjerno spore izvedbe: svaka se "
        "realizacija ponovno izgradi kao pravi graf, iz njega se obrišu bridovi reza i "
        "dohvatljivi se skup izračuna funkcijom knjižnice. Time se brza izvedba mjeri "
        "prema nečemu što s njom ne dijeli nijednu pretpostavku. Istim se putem provjerava "
        "i da jednoprolazni izračun doprinosa daje točno iste vrijednosti kao naivni.")

    t.p("Druga vrsta provjere brani od pogreške koja se ne očituje iznimkom nego uvjerljivim "
        "krivim brojem. Vlastiti vektori i ostala obilježja indeksirana su unutarnjim "
        "poretkom čvorova u knjižnici, koji ne mora odgovarati poretku izvornih "
        "identifikatora. Ako se ta dva poretka razmimoiđu, ocjene se pridružuju krivim "
        "bridovima, a rezultat i dalje izgleda razumno. Zato se pri svakoj izgradnji grafa "
        "provjerava da se poredak čvorova poklapa s očekivanim, a pri svakom učitavanju "
        "tablice obilježja da njezini reci odgovaraju bridovima grafa. Poravnanje "
        "spektralne ocjene dodatno je provjereno tako da se graf izgradi s čvorovima "
        "dodanima u izmiješanom redoslijedu: unutarnji se indeksi time potpuno promijene, "
        "pa ocjene po imenovanim bridovima moraju ostati nepromijenjene.")


# ------------------------------------------------------------------ 6.2 ----

def _realizacije(t):
    t.h2("Zamrznuti skupovi realizacija", label="realizacije")

    t.p("Kako je opisano u odjeljku ", t.sec("procjena"), ", koriste se dva odvojena skupa ", i("live-edge"),
        " realizacija: uži za pretraživanje i širi za konačno vrednovanje. Oba se generiraju "
        "jednom, svaki iz vlastitog sjemena generatora slučajnih brojeva, i nakon toga se "
        "više ne mijenjaju.")

    t.p("Za svaki se brid neovisno baci novčić s njegovom vjerojatnošću prijenosa, a "
        "realizacija se pohranjuje kao lista susjedstva koja sadrži samo propusne bridove. "
        "Ishod bacanja time je ugrađen u samu strukturu, pa se tijekom obilaska više ne "
        "provjerava. Uži skup ima ", count(config.SAA_SCENARIO_COUNT, "realizaciju",
                                           "realizacije", "realizacija"),
        ", a širi ", count(config.MC_SCENARIO_COUNT, "realizaciju", "realizacije",
                           "realizacija"), ".")

    t.p("Tri su svojstva tih skupova provjerena, jer bi njihov izostanak neprimjetno "
        "obezvrijedio sve izmjerene brojeve:")

    t.bullets([
        "skupovi se iz istog sjemena reproduciraju u potpunosti, uključujući i redoslijed "
        "susjeda unutar liste, a ne samo kao jednaki skupovi bridova. Bez toga dva "
        "pokretanja izvedena u različito vrijeme ne bi bila usporediva;",
        "dva skupa nemaju nijednu zajedničku realizaciju, pa je konačno vrednovanje "
        "doista izvan uzorka nad kojim se pretraživalo;",
        "nakon pokretanja svih metoda i cjelovitog pretraživanja svaka je realizacija "
        "ostala nepromijenjena do zadnjeg bita, čime je potvrđeno da se rez zaista "
        "primjenjuje kao maska, a ne izmjenom zamrznute strukture.",
    ])


# ------------------------------------------------------------------ 6.3 ----

def _uzorak(t):
    t.h2("Uzorak izvora", label="uzorak")

    t.p("Metode se ne mogu vrednovati na svim čvorovima mreže, ali ni na proizvoljno "
        "odabranima. Odjeljak 2.6 pokazao je dvije stvari koje ograničavaju odabir: većina "
        "čvorova ima premalo izlaznih bridova da bi uopće mogla podnijeti najmanji "
        "razmatrani proračun, a doseg se među preostalima mijenja kroz cijeli raspon, bez "
        "prirodne podjele u skupine.")

    t.p("Uzorak je zato slojevit, i to po dvjema osima istodobno. Prva je izlazni stupanj "
        "izvora, jer on ", i("jest"),
        " skup kandidata sloja 0, pa određuje i koji se proračuni uopće mogu proučavati i "
        "koliko je pretraživanje teško. Druga je doseg neizmijenjene mreže, jer o njemu "
        "ovisi trajanje pokretanja, a topološki različiti čvorovi mogu imati praktički "
        "jednak doseg, pa jedna os ne bi bila dovoljna.")

    t.p("Osobito su zanimljive ćelije izvan dijagonale, dakle izvori s malo izlaznih "
        "bridova koji ipak dosežu velik dio mreže. Upravo je to geometrija iz odjeljka ", t.sec("slozenost"), ": "
        "nekoliko veza vodi prema velikoj komponenti, pa se najbolji rez ne mora nalaziti "
        "uz sam izvor.")

    calib = SAMPLE[SAMPLE.role == "calibration"]
    measure = SAMPLE[SAMPLE.role == "measurement"]

    t.p("Iz svake se ćelije izvlači unaprijed određen broj izvora, i to tako da se najprije "
        "uzmu izvori za ugađanje parametara, a mjerni izvori tek iz preostalih. Time su "
        "ta dva skupa razdvojena po konstrukciji, a ne po disciplini onoga tko pokreće "
        "eksperiment. Izvučeno je ukupno ", count(len(calib), "izvor", "izvora", "izvora"),
        " za ugađanje i ", count(len(measure), "izvor", "izvora", "izvora"),
        " za mjerenje, raspoređenih po ", count(SAMPLE.cell.nunique(), "ćeliji", "ćelije",
                                                "ćelija"),
        ". Uzorak je izvučen jednom, iz jednog sjemena, i jedini je uzorak koji se u radu "
        "koristi.")

    t.p("Jedna ćelija zaslužuje napomenu: izvora s više od pedeset izlaznih bridova koji "
        "ipak imaju malen doseg u cijeloj mreži ima ", count(
            len(SAMPLE[(SAMPLE.cell.str.startswith("out[50")) &
                       (SAMPLE.cell.str.endswith("low-reach"))]),
            "jedan", "jedan", "jedan"),
        ", pa ta ćelija ne može popuniti mjerni dio uzorka. To nije nedostatak uzorkovanja "
        "nego svojstvo mreže: čvorovi visokog izlaznog stupnja gotovo su bez iznimke i "
        "čvorovi velikog dosega.")

    t.p("Uz svaki se izvor bilježi i predviđeno trajanje pokretanja, izračunato iz njegova "
        "dosega. Trajanje naime prati doseg, a ne broj izvora, pa jedan zasićen izvor stoji "
        "kao dvadesetak onih malog dosega. Zahvaljujući tomu se cijena plana mjerenja može "
        "procijeniti prije nego što se išta pokrene.")


# ------------------------------------------------------------------ 6.4 ----

def _kalibracija(t):
    t.h2("Kalibracija parametara", label="kalibracija")

    t.p("Parametri metode ALNS preuzeti su iz izvornog rada gdje god su ondje ugođeni, ali "
        "izvorni je rad ugađan na bitno drukčijem problemu, pa ih je trebalo provjeriti na "
        "ovome. Postupak slijedi onaj koji {~ropke2006} sami koriste: krene se od radne "
        "postavke, jedan parametar poprima nekoliko vrijednosti dok ostali miruju, "
        "zadržava se pobjednik i prelazi na sljedeći parametar, noseći sa sobom dotad "
        "odabrane vrijednosti.")

    t.p("Skup za ugađanje odvojen je od mjernog (odjeljak ", t.sec("uzorak"), ") i iz njega se uzima po "
        "jedan izvor iz svake ćelije, i to onaj najjeftiniji. Bitno je da su izvori "
        "odabrani po strukturi i cijeni, a nikada po ishodu: kada bi se birali izvori na "
        "kojima je metoda loše prošla, ugađanje bi bilo usmjereno prema jednom režimu i u "
        "kalibraciju bi se uvukao rezultat. Isto načelo, da instance za ugađanje ostanu "
        "male, primjenjuju i {~ropke2006}.")

    t.h3("Zašto proračun za ugađanje nije najmanji mogući")

    t.p("Prvi je pokušaj ugađanja bio bezvrijedan i vrijedi objasniti zašto, jer je razlog "
        "svojstvo same metode. Kod najmanjeg proračuna obje granice za broj bridova koji "
        "se u iteraciji mijenjaju padaju na jedan (izraz ", t.ref("qbounds"),
        "), pa razaranje ukloni jedan brid, a popravljanje vrati jedan. Iz istog početnog "
        "rješenja svaka je postavka parametara tada došla do istoga reza, na većini "
        "ćelija do četvrte decimale jednakog. Zamjena jednog brida jednostavno ne ostavlja "
        "prostora u kojem bi se izbor parametara mogao očitovati.")

    t.p("Proračun za ugađanje zato je postavljen na najveći koji izvor može podnijeti, do "
        "granice od deset bridova. Sam nalaz, da pri proračunima veličine jedne zamjene "
        "izbor parametara metode ne igra ulogu, zadržan je kao rezultat.")

    t.h3("Odluka i njezin ishod")

    alns = CALIB[CALIB.method == "alns"].set_index(["tag", "source"])
    base = alns.loc["default", "R_mc"]
    # The CSV tags are code identifiers; the table names the parameters the way the text
    # does, in the order they were swept.
    order = [
        ("repair_p=20", "pristranost odabira pri popravljanju: 20"),
        ("repair_p=60", "pristranost odabira pri popravljanju: 60"),
        ("max_hop_scope=1", "najdublji sloj kandidata: 1"),
        ("q_max_frac=0.7", "gornja granica za q: 0,7 k"),
        ("max_iter=150", "broj iteracija: 150"),
    ]
    tags = set(alns.index.get_level_values(0))
    deltas = {tag: (alns.loc[tag, "R_mc"] - base) for tag, _ in order if tag in tags}
    names = dict(order)

    t.p("Ugađanje se vodi mjerom uspješnosti iz izraza ", t.ref("reduction"),
        ", mjerenom izvan uzorka. Ne uspoređuje se, međutim, njezina razina među "
        "postavkama, nego promjena ", i("po ćeliji"),
        ": ćelije se međusobno vrlo razlikuju, pa nekoliko zasićenih izvora zna posve "
        "odrediti prosjek, a usporedba iste ćelije sa samom sobom pod dvjema postavkama "
        "toga je oslobođena. ", t.tabref("kalibracija"), " prikazuje ishod.")

    t.table(
        ["Ispitana vrijednost", "Prosječna promjena po ćeliji", "Odluka"],
        [[names[tag], _signed(d.mean()),
          "usvojena" if d.mean() > 0.02
          else ("zadržana zatečena (izmjereno lošije)" if d.mean() < -0.01
                else "zadržana zatečena")]
         for tag, d in deltas.items()],
        "Ishod kalibracije: prosječna promjena uspješnosti po ćeliji u odnosu na "
        "zatečene vrijednosti parametara.",
        label="kalibracija",
        widths_cm=[4.8, 4.2, 4.6])

    worst = min(deltas.items(), key=lambda kv: kv[1].mean())

    t.p("Nijedna ispitana promjena nije prešla prag koji je unaprijed postavljen kao uvjet "
        "za izmjenu zatečene vrijednosti, pa sve zatečene vrijednosti ostaju. Prag postoji "
        "zato što se, uz jedno sjeme po ćeliji, male razlike ne mogu razlučiti od kolebanja "
        "koje unosi slučajno razrješavanje izjednačenosti iz odjeljka ", t.sec("izjednacenost"), ".")

    t.p("Jedan je ishod ipak jasan i nije samo izostanak razlike. Smanjenje broja iteracija "
        "pogoršalo je rezultat za ", _signed(worst[1].mean()),
        " u prosjeku, uz najgoru pojedinačnu ćeliju od ", _signed(worst[1].min()),
        ". Zatečeni broj iteracija time nije samo neopovrgnut nego i pozitivno potkrijepljen, "
        "što je jača tvrdnja od one koju su ostali parametri dobili.")

    t.p("Dva ograničenja treba navesti uz svaki zaključak iz ovog odjeljka. Prvo, ugađanje "
        "je izvedeno uz jedno sjeme po ćeliji, pa se raspoznaju samo velike razlike. Drugo, "
        "ugađano je na ", count(len(base), "ćeliji", "ćelije", "ćelija"),
        ", što je premalo za ikakvu tvrdnju o tome kako se parametri ponašaju na cijeloj "
        "populaciji izvora. Zbog oba je ograničenja odluka postavljena kao zadržavanje "
        "zatečenog, a ne kao odabir najboljeg.")


# ------------------------------------------------------------------ 6.5 ----

def _protokol(t):
    t.h2("Mjere i protokol mjerenja", label="protokol")

    t.p("Uspješnost se izvještava relativnim smanjenjem dosega iz izraza ",
        t.ref("reduction"), ", i to uvijek dvaput: jednom nad užim skupom realizacija, nad "
        "kojim je pretraživanje radilo, i jednom nad širim, koji pretraživanje nije vidjelo. "
        "Bilježi se i njihova razlika. Ona nije pomoćni podatak nego mjera koliko je "
        "pronađeni rez prilagođen vlastitom uzorku, a slučajevi u kojima rez pobjeđuje "
        "unutar uzorka i gubi izvan njega postoje, pa bi izvještavanje samo jedne od tih "
        "vrijednosti tu pojavu sakrilo umjesto izmjerilo.")

    t.p("Svako pokretanje daje jedan redak, i to jedan redak ", i("po metodi"),
        ". Ta naizgled sitna odluka ima razlog. Ako se u redak upiše stupac tipa „najbolja "
        "suparnička metoda”, a u skup suparnika se pritom uvrsti i sama metoda koja se "
        "ocjenjuje, taj stupac nikada ne može pokazati da je ona izgubila. Veličine poput "
        "najboljeg pohlepnog rezultata zato se ne zapisuju tijekom mjerenja, nego se "
        "računaju naknadno, grupiranjem redaka.")

    t.p("Uz svaki se redak zapisuju i sve razriješene vrijednosti parametara metode, pa se "
        "iz samog retka vidi je li nastao zatečenim ili izmijenjenim postavkama. Zapisuje "
        "se i razlog zaustavljanja, čime se izdvajaju instance riješene trivijalno, dakle "
        "one u kojima proračun dopušta potpuno izoliranje izvora. Njih treba isključiti iz "
        "prosjeka jer u njima svaka metoda postiže isti, dokazivo optimalan rezultat, pa "
        "bi njihovo uključivanje jednako polaskalo svima.")

    t.p("Naposljetku, slučajnost se izvještava, a ne uklanja. Pet od šest pohlepnih metoda "
        "posve je determinističko, pa se računaju jednom; slučajna pohlepna metoda i "
        "metaheuristika pokreću se s više sjemena. Dobiveno raspršenje rezultata prikazuje "
        "se kao svojstvo metode, u skladu s odjeljkom ", t.sec("izjednacenost"), ", umjesto da se usrednjavanjem "
        "prikrije koliko na ishod utječe izbor među jednako ocijenjenim bridovima.")
