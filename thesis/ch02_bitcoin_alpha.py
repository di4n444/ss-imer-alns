"""2. Analiza mreze Bitcoin Alpha.

Every number in this chapter is read from data/topology_summary.csv, data/edge_features.csv
or data/source_profile.csv at build time. Nothing is retyped: a figure typed into prose
becomes wrong the moment the analysis is re-run, and there is no way to see that by
reading the text.
"""

import pandas as pd

from omml import delim, frac, func, i, sub, sup, up, v

DATA = None  # set by write()


def _n(value, decimals=4):
    """A number formatted for prose: decimal comma, and a real minus sign rather than
    the ASCII hyphen Python's formatting produces."""
    return f"{value:.{decimals}f}".replace(".", ",").replace("-", "\u2212")


def _int(value):
    return f"{int(value):,}".replace(",", ".")


def _count(value, one, few, many):
    """Croatian numeral agreement: 1 čvor, 73 čvora, 411 čvorova.

    The form follows the last digit, except that 11-14 always take the plural, so
    "3.683 čvorova" is wrong where "3.683 čvora" is right."""
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
    global DATA
    data = figures.parent / "data"
    topo = pd.read_csv(data / "topology_summary.csv").iloc[0]
    edges = pd.read_csv(data / "edge_features.csv")
    profile = pd.read_csv(data / "source_profile.csv")
    DATA = (topo, edges, profile)

    t.h1("Analiza mreže Bitcoin Alpha")
    t.p("Poglavlje opisuje skup podataka na kojem se metoda vrednuje i mjeri ona njegova "
        "svojstva koja izravno utječu na formulaciju problema i na tumačenje rezultata. "
        "Sve navedene vrijednosti dobivene su vlastitom analizom grafa opisanom u "
        "šestom poglavlju.")

    _dataset(t, figures, topo, edges)
    _small_world(t, figures, topo)
    _components(t, figures, topo)
    _communities(t, data, topo, edges)
    _threshold(t, topo)
    _sources(t, figures, profile)


def _dataset(t, figures, topo, edges):
    t.h2("Skup podataka i preslikavanje ocjena u vjerojatnost")

    t.p("Za praktičnu evaluaciju koristi se skup podataka Bitcoin Alpha iz Stanfordove "
        "zbirke mrežnih podataka (SNAP), predstavljen u radovima {kumar2016,kumar2018}. "
        "Bitcoin Alpha decentralizirana je platforma za trgovanje kriptovalutama. Budući "
        "da se trgovanje odvija izravno među korisnicima, bez posrednika koji bi jamčio "
        "za drugu stranu, korisnici su razvili sustav ocjenjivanja povjerenja kojim "
        "označavaju pouzdane partnere i upozoravaju na prevarante.")

    t.p("Sirovi je skup usmjeren i označen (", i("signed"), ") graf: čvorovi su članovi "
        "platforme, a usmjereni brid od ", v("u"), " prema ", v("v"), " znači da je "
        "korisnik ", v("u"), " ocijenio korisnika ", v("v"), " cjelobrojnom ocjenom u "
        "rasponu od −10 do +10. U ovom se radu zadržavaju isključivo bridovi s pozitivnom "
        "ocjenom. Razlog je modelske naravi: brid u kaskadnom modelu predstavlja kanal "
        "kojim informacija može proći, a negativna ocjena izražava nepovjerenje, pa nije "
        "opravdano pretpostaviti da bi tim kanalom informacija tekla jednako kao i "
        "kanalom povjerenja.")

    t.p("Pozitivna ocjena ", sub(v("R"), [v("u"), v("v")]), " preslikava se u vjerojatnost "
        "prijenosa sigmoidalnom funkcijom:")

    t.eq(sub(v("p"), [v("u"), v("v")]), up(" = "),
         frac(up("1"), [up("1 + "), func("exp", [up("−"), delim(sub(v("R"), [v("u"), v("v")]), up(" − 5"))])]),
         label="sigmoid")

    t.p("Sredina raspona ocjena tako se preslikava u vjerojatnost 0,5, a krajevi u "
        "vrijednosti blizu 0 i 1. Ista se uređena dvojka korisnika može ocijeniti više "
        "puta tijekom vremena; budući da model traži jednu vjerojatnost po bridu, "
        "zadržava se najnovija ocjena kao najsvježija procjena povjerenja.")

    p = edges.probability
    t.p("Dobiveni graf ima ", _count(topo.n, "čvor", "čvora", "čvorova"), " i ",
        _count(topo.m, "brid", "brida", "bridova"), ", uz "
        "prosječan izlazni stupanj ", _n(topo.m / topo.n, 2), ". Raspodjela vjerojatnosti "
        "izrazito je asimetrična: srednja vrijednost iznosi ", _n(p.mean()), ", a medijan "
        "samo ", _n(p.median()), ". Drugim riječima, tipičan brid gotovo da i ne prenosi "
        "kaskadu, dok malen broj vrlo pouzdanih kanala prenosi gotovo sigurno.")

    t.p("Vrijedi uočiti posljedicu koju preslikavanje ima na strukturu podataka. Kako "
        "ocjena poprima najviše deset različitih pozitivnih cjelobrojnih vrijednosti, "
        "vjerojatnost prijenosa poprima točno deset različitih vrijednosti, a ne "
        "kontinuum. Najniža od njih, ", _n(p.min(), 3), ", pokriva čak ",
        _n(100 * (p == p.min()).mean(), 1), " % svih bridova. Ta diskretnost nije "
        "tehnički detalj: kriteriji koji bridove rangiraju po vjerojatnosti time dobivaju "
        "vrlo velike skupine jednako ocijenjenih bridova, što se razmatra u odjeljku 4.7.")

    t.figure(figures / "fig2_2_probability_distribution.png",
             "Raspodjela vjerojatnosti prijenosa po bridovima. Vjerojatnost poprima točno "
             "deset vrijednosti jer je izvedena iz cjelobrojne ocjene.",
             label="prob")


def _small_world(t, figures, topo):
    t.h2("Svojstva malog svijeta i raspodjela stupnjeva")

    t.p("Za provjeru efekta malog svijeta {watts1998} mjere se prosječna duljina "
        "najkraćeg puta i koeficijent grupiranja te se uspoređuju s Erdős-Rényijevim "
        "nul-modelom koji ima jednak broj čvorova i bridova. Prosječna duljina puta u "
        "mreži Bitcoin Alpha iznosi ", _n(topo.path_length), ", a u nul-modelu ",
        _n(topo.path_length_er), ". Koeficijent grupiranja iznosi ", _n(topo.clustering),
        ", naspram ", _n(topo.clustering_er), " u nul-modelu, dakle otprilike ",
        _n(topo.clustering / topo.clustering_er, 1), " puta više.")

    t.p("Kombinacija kratkih putova i grupiranja znatno višeg od slučajnoga odgovara "
        "definiciji mreže malog svijeta {watts1998}. Za ovaj je rad važna praktična "
        "posljedica: kaskada iz gotovo bilo kojeg izvora u malom broju koraka dopire do "
        "velikog dijela mreže, pa se učinkovita intervencija mora dogoditi blizu izvora "
        "ili na razmjerno malenom broju veza koje povezuju udaljene dijelove mreže.")

    t.p("Koeficijent asortativnosti po stupnju iznosi ", _n(topo.assortativity_degree),
        ". Negativna vrijednost znači da je mreža disasortativna: čvorišta se pretežno "
        "povezuju s perifernim čvorovima niskog stupnja, a rjeđe međusobno. U kontekstu "
        "Bitcoin Alphe to odražava strukturu u kojoj nekoliko vrlo aktivnih trgovaca "
        "ocjenjuje velik broj povremenih korisnika.")

    t.p("Raspodjela izlaznih stupnjeva ispitana je postupkom koji {~clauset2009} "
        "predlažu za empirijske podatke: prilagodbom zakona potencije metodom najveće "
        "izglednosti uz automatski odabir donje granice ", sub(v("k"), up("min")),
        ". Procijenjeni eksponent iznosi ", v("γ"), " = ", _n(topo.out_gamma, 3), " uz ",
        sub(v("k"), up("min")), " = ", _int(topo.out_xmin), " i Kolmogorov-Smirnovljevu "
        "statistiku ", _n(topo.out_ks, 3), ". Ta vrijednost eksponenta smješta mrežu u "
        "raspon između 2 i 3 koji {~albert2002} navode kao tipičan za stvarne mreže.")

    t.p("Sama prilagodba, međutim, nije dovoljna da bi se raspodjela proglasila zakonom "
        "potencije. {~clauset2009} upozoravaju da se prilagođeni model uvijek mora "
        "usporediti s drugim raspodjelama s teškim repom, pa je provedena i takva "
        "usporedba omjerom izglednosti. Zakon potencije uvjerljivo nadmašuje eksponencijalnu raspodjelu "
        "(", v("R"), " = ", _n(topo.out_R_vs_exponential, 1), "), što potvrđuje da rep "
        "raspodjele doista jest težak. Istodobno gubi od skraćenog zakona potencije "
        "(", v("R"), " = ", _n(topo.out_R_vs_truncated_power_law, 1), "), lognormalne "
        "(", v("R"), " = ", _n(topo.out_R_vs_lognormal, 1), ") i rastegnute "
        "eksponencijalne raspodjele (", v("R"), " = ", _n(topo.out_R_vs_stretched_exponential, 1),
        "), pri čemu su sve razlike statistički značajne.")

    t.p("Zaključak koji se iz toga smije izvesti nešto je oprezniji od uobičajenoga: "
        "raspodjela stupnjeva ima težak rep i eksponent u rasponu koji literatura "
        "povezuje s mrežama bez skale, ali čisti, neograničeni zakon potencije nije "
        "najbolji model za ove podatke jer ga nadmašuje inačica sa skraćenjem repa. "
        "Mrežu je stoga točnije opisati kao mrežu s teškim repom i konačnim skraćenjem "
        "nego kao mrežu bez skale bez zadrške. ", t.figref("degree"), " prikazuje "
        "empirijsku raspodjelu i prilagođeni zakon potencije, na kojoj se odstupanje "
        "repa od pravca vidi i golim okom.")

    t.figure(figures / "fig2_1_degree_distribution.png",
             "Komplementarna kumulativna raspodjela izlaznih stupnjeva s prilagođenim "
             "zakonom potencije, u dvostruko logaritamskom mjerilu.",
             label="degree")


def _components(t, figures, topo):
    t.h2("Struktura komponenti i dekompozicija jezgre")

    t.p("Budući da je graf usmjeren, njegova se makroskopska struktura opisuje "
        "razlaganjem na komponente po uzoru na klasičnu strukturu leptir-kravate "
        "{predavanja}. Najveća jako povezana komponenta obuhvaća ",
        _count(topo.bowtie_scc, "čvor", "čvora", "čvorova"), ", odnosno ",
        _n(100 * topo.bowtie_scc / topo.n, 1), " % mreže. Oko nje se nalaze ulazna "
        "komponenta od ", _count(topo.bowtie_in, "čvora", "čvora", "čvorova"),
        ", iz kojih se jezgra može dosegnuti ali ne i obratno, te izlazna komponenta od ",
        _count(topo.bowtie_out, "čvora", "čvora", "čvorova"),
        ", koji su dohvatljivi iz jezgre ali nemaju put natrag. Preostalih ",
        _count(topo.bowtie_rest, "čvor", "čvora", "čvorova"), " pripada perifernim strukturama.")

    t.p("Zanemari li se smjer bridova, najveća slabo povezana komponenta obuhvaća ",
        _int(topo.wcc_giant), " od ", _count(topo.n, "čvora", "čvora", "čvorova"), ". Mreža je dakle gotovo "
        "potpuno povezana kad se gleda samo postojanje veze, dok usmjerenost dijeli "
        "znatan dio čvorova na one koji mogu doprijeti do jezgre i one do kojih jezgra "
        "može doprijeti. Za problem koji se ovdje rješava mjerodavna je isključivo "
        "usmjerena dohvatljivost iz izvora.")

    t.p("Dekompozicija po jezgrama pokazuje da najgušći sloj mreže čini ",
        _int(topo.k_core_max), "-jezgra, u kojoj se nalazi ",
        _count(topo.n_in_max_core, "čvor", "čvora", "čvorova"),
        ". Riječ je o malenoj, iznimno gusto povezanoj skupini unutar koje se "
        "kaskada, jednom kad je dosegne, širi vrlo lako. ", t.figref("bowtie"),
        " prikazuje omjere komponenti.")

    t.figure(figures / "fig2_3_bowtie.png",
             "Makroskopska struktura mreže: ulazna komponenta, jako povezana jezgra i "
             "izlazna komponenta, s pripadnim brojem čvorova.",
             label="bowtie")


def _communities(t, data, topo, edges):
    t.h2("Čvorišta i zajednice")

    top = pd.read_csv(data / "top_betweenness_sources.csv")
    names = ", ".join(str(int(r.snap_id)) for _, r in top.head(3).iterrows())

    t.p("Kako bi se profilirali najutjecajniji akteri, izračunata je usmjerena "
        "međupoloženost čvorova. Tri čvora s najvećom vrijednošću nose izvorne "
        "identifikatore ", names, ". Ti čvorovi leže na velikom broju najkraćih putova "
        "između ostalih korisnika, pa imaju strukturno važnu ulogu u brzini širenja "
        "kaskade i predstavljaju zanimljive kandidate za izvor.")

    t.p("Mezoskopska struktura ispitana je Louvainovim algoritmom. Kako je riječ o "
        "stohastičkom postupku čiji rezultat ovisi o početnim uvjetima, izvedeno je "
        "dvadeset pokretanja i zadržana je particija s najvećom modularnošću. Najbolja "
        "particija ima ", _int(topo.louvain_best_n_communities), " zajednica uz "
        "modularnost ", _n(topo.louvain_best_modularity, 3), ", dok se broj zajednica "
        "kroz pokretanja kretao između ", _int(topo.louvain_n_communities_min), " i ",
        _int(topo.louvain_n_communities_max), ". Ta razlika među pokretanjima razlog je "
        "zbog kojeg se u ovom radu podjela na zajednice koristi isključivo kao opis "
        "strukture, a ne kao kriterij za odabir bridova: kriterij koji ovisi o jednoj "
        "proizvoljno odabranoj particiji ne bi bio ponovljiv.")

    bridges = int(edges.is_local_bridge.sum())
    t.p("Umjesto toga, kao strukturni kriterij koristi se pojam lokalnog mosta prema "
        "{~granovetter1973}, koji ne ovisi ni o kakvoj particiji. Lokalni je most brid "
        "čiji krajevi nemaju nijednog zajedničkog susjeda, pa je najkraći zaobilazni put "
        "između njih dulji od same veze. U ovoj mreži takvih bridova ima ", _int(bridges),
        ", odnosno ", _n(100 * bridges / len(edges), 1), " % svih bridova. Granovetter "
        "argumentira da upravo takve veze prenose informaciju između inače odvojenih "
        "skupina, zbog čega su prirodan kandidat za uklanjanje; kriterij se definira u "
        "odjeljku 4.4.")


def _threshold(t, topo):
    t.h2("Spektralni prag i režim širenja")

    t.p("Prag opisan u odjeljku 1.3 sada se može izračunati za ovu mrežu. Najveća "
        "vlastita vrijednost matrice susjedstva iznosi ", sub(v("λ"), up("max")), " = ",
        _n(topo.lambda_max_A, 2), ", pa je pripadni epidemiološki prag ",
        sub(v("λ"), up("c")), " = ", _n(topo.lambda_c, 4), ". Prosječna vjerojatnost "
        "prijenosa u mreži, ", _n(topo.p_mean), ", nekoliko je puta veća od te "
        "vrijednosti.")

    t.p("Izravnija je provjera preko matrice u kojoj svaki brid nosi svoju vjerojatnost "
        "prijenosa. Njezina najveća vlastita vrijednost iznosi ", _n(topo.lambda_max_P, 2),
        ", dakle znatno više od jedan, što znači da se mreža nalazi duboko u "
        "nadkritičnom režimu {wang2003,castellano2010}.")

    t.p("Ta činjenica oblikuje cijeli ostatak rada. Kaskada iz dobro povezanog izvora "
        "neće izumrijeti sama od sebe, nego će zahvatiti velik dio jako povezane jezgre. "
        "Problem koji se rješava zato nije usporavanje širenja, nego odvajanje izvora od "
        "te jezgre. Uklanjanje ograničenog broja bridova pritom ne pomiče prag mreže u "
        "cjelini; ono mijenja isključivo dohvatljivost iz jednoga zadanog izvora, što je "
        "razlog zbog kojeg je cilj optimizacije očekivani doseg, a ne spektralni polumjer.")


def _sources(t, figures, profile):
    t.h2("Populacija izvora")

    t.p("Posljednje svojstvo koje treba utvrditi tiče se same populacije mogućih izvora, "
        "jer ono ograničava koje se instance problema uopće mogu postaviti.")

    isolated = int((profile.out_degree == 0).sum())
    usable = profile[profile.out_degree > 0]
    small = int(((profile.out_degree >= 1) & (profile.out_degree < 4)).sum())
    ok3 = int((profile.out_degree >= 4).sum())

    t.p("Od ukupno ", _count(len(profile), "čvora", "čvora", "čvorova"), " njih ", _count(isolated, "čvor", "čvora", "čvorova"), " nema "
        "nijedan izlazni brid, pa iz njih kaskada ne može ni započeti. Daljnjih ",
        _count(small, "čvor", "čvora", "čvorova"), " ima jedan do tri izlazna brida. Budući da proračun ",
        v("k"), " mora biti manji od izlaznog stupnja izvora da bi problem bio "
        "netrivijalan, ti čvorovi ne mogu podnijeti ni najmanji proračun koji se u ovom "
        "radu razmatra. Kao izvori za ", v("k"), " ≥ 3 preostaje ", _count(ok3, "čvor", "čvora", "čvorova"),
        ", odnosno ", _n(100 * ok3 / len(profile), 1), " % mreže.")

    t.p("Očekivani doseg praznog reza, ", sub(v("σ"), up("0")), ", mjeren je za svaki "
        "čvor. Raspon je vrlo širok: medijan iznosi ", _n(usable.sigma0_saa.median(), 1),
        ", dok deveti decil iznosi ", _n(usable.sigma0_saa.quantile(0.9), 1),
        ". Udio izvora koji dosežu jako povezanu jezgru, ovdje definiranih kao oni s ",
        sub(v("σ"), up("0")), " ≥ 400, iznosi ",
        _n(100 * (usable.sigma0_saa >= 400).mean(), 1), " %.")

    t.p("Bitno je da između tih dviju skupina nema jasnog reza. Doseg se mijenja "
        "postupno kroz cijeli raspon, kako pokazuje ", t.figref("population"),
        ". Izlazni stupanj snažno predviđa doseg, ali ne i potpuno: među čvorovima s "
        "najviše devet izlaznih bridova ima i onih koji dosežu jezgru. Upravo su takvi "
        "izvori zanimljivi za drugu razinu istraživačkog pitanja, jer kod njih malen broj "
        "veza vodi prema velikoj komponenti, pa se učinkovit rez ne mora nalaziti uz sam "
        "izvor. Obje veličine zato ulaze u raspored uzorkovanja izvora opisan u "
        "odjeljku 6.3.")

    t.figure(figures / "fig2_4_source_population.png",
             "Populacija mogućih izvora: kumulativna raspodjela očekivanog dosega "
             "(lijevo) i sastav pojasa izlaznog stupnja s obzirom na doseg (desno).",
             label="population")
