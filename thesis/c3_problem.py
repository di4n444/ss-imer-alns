"""3. Formulacija problema SS-IMER.

Every claim in 3.2 was read from the paper it cites, not from a summary:

  * Castiglioni et al. (2021), Definition 4, defines IMER with budget |E'| <= B and the
    objective of maximizing the drop; their Theorem 6 states verbatim that "for any
    constant rho > 0, there is no polynomial time algorithm returning a rho-approximation
    to IMER problem when the budget B is finite, unless P = NP".
  * Kimura et al. (2008) define the contamination degree c(G) as the average of influence
    degrees over *every* node as a source, and block exactly k links. Our exact budget
    comes from there; our single fixed source does not.
  * Kempe et al. (2003) state that computing sigma exactly "is an open question" and
    estimate it by simulation, and it is their submodularity over *seed sets* that gives
    greedy its 63% guarantee - a guarantee that does not transfer to removed edges.
  * Tong et al. (2012) observe that the impact of deleting a set of edges "is not equal to
    the summation of the impact of deleting each individual edge". They say it of the
    leading eigenvalue rather than of reach, so it is cited as an analogous observation.

Valiant (1979) and Kleywegt et al. (2002) are deliberately not cited here: neither PDF is
in the project folder, and the argument is complete without them - Kempe carries the
intractability of evaluation and Kimura carries the estimator.
"""

from omml import acc, delim, frac, i, limlow, nary, sub, sup, up, v


def ifunc(name, argument):
    return [v(name), delim(argument)]


def sigma_cut():
    """sigma(s, G \\ D), written the same way everywhere it appears."""
    return [v("σ"), delim(v("s"), up(", "), v("G"), up(" \\ "), v("D"))]


def write(t, figures):
    t.h1("Formulacija problema SS-IMER", label="problem")
    t.p("Sada kada znamo kako se kaskada širi i kakva je mreža na kojoj to čini, problem "
        "možemo postaviti precizno.")

    _definition(t)
    _hardness(t, figures)
    _estimation(t)


# -- 3.1 ---------------------------------------------------------------------

def _definition(t):
    t.h2("Definicija problema", label="definicija")

    t.p("Problem pripada obitelji problema minimizacije utjecaja. {~castiglioni2021} "
        "definiraju problem ", i("Influence Minimization by Edge Removal"),
        ": za zadani graf, skup početnih čvorova i proračun ", v("B"),
        ", traži se skup od najviše ", v("B"), " bridova čije uklanjanje najviše smanjuje "
        "očekivani utjecaj. {~kimura2008} razmatraju blisku varijantu, koju zovu problemom "
        "minimizacije kontaminacije, u kojoj se uklanja točno ", v("k"),
        " bridova, ali se doseg usrednjuje preko svih čvorova mreže kao mogućih izvora.")

    t.p("Varijanta koju rješavamo razlikuje se od obiju, i to treba navesti otvoreno. "
        "Izvor je jedan i unaprijed zadan, dakle ni skup početnih čvorova ni prosjek preko "
        "cijele mreže. Proračun se pritom troši u cijelosti, kako to čine i {~kimura2008}, "
        "a ne najviše ", v("B"), ", koliko dopuštaju {~castiglioni2021}. Za tako suženu "
        "varijantu u ovom "
        "radu koristimo oznaku SS-IMER, koja nije ustaljen naziv iz literature nego oznaka "
        "uvedena radi kratkoće.")

    t.p("Neka je ", v("G"), " = ", delim(v("V"), up(", "), v("E")), " usmjeren graf, ",
        v("s"), " zadani izvor, ", v("k"), " proračun, a ", sub(v("E"), v("s")),
        " skup bridova koje smijemo ukloniti. Tražimo skup ", v("D"),
        " koji minimizira očekivani doseg preostaloga grafa:")

    t.eq(sup(v("D"), up("*")), up(" = "),
         limlow(up("arg min"),
                [v("D"), up(" ⊆ "), sub(v("E"), v("s")), up(",  "),
                 delim(v("D"), left="|", right="|"), up(" = "), v("k")]),
         sigma_cut(), label="cilj")

    t.p("Rezultat ne izvještavamo apsolutno nego kao relativno smanjenje dosega. Razlog je "
        "praktičan: izvori se po dosegu razlikuju za tri reda veličine, pa smanjenje od "
        "deset čvorova znači nešto sasvim drugo kod izvora koji doseže petnaest nego kod "
        "onoga koji doseže šest stotina. Uz oznaku ", sub(v("σ"), up("0")),
        " za doseg netaknutog grafa mjera je:")

    t.eq(ifunc("R", v("D")), up(" = 1 − "), frac(sigma_cut(), sub(v("σ"), up("0"))),
         label="mjera")

    t.p("Vrijednost ", v("R"), " = 0 znači da uklanjanje nije promijenilo ništa, a ",
        v("R"), " = 1 da je izvor potpuno odsječen.")


# -- 3.2 ---------------------------------------------------------------------

def _hardness(t, figures):
    t.h2("Zašto je problem težak", label="tezina")

    # Allocated in the order the figures are placed, not in the order the sentence below
    # mentions them: figref hands out the next number on each first call, so referring to
    # the first and third in one sentence would otherwise number the middle figure 3.3.
    first, second, third = (t.figref("primjer1"), t.figref("primjer2"),
                            t.figref("primjer3"))

    t.p("Tri razloga vrijedi razlikovati, jer se odnose na tri različite stvari: na ocjenu "
        "jednog rješenja, na sam problem i na način na koji rješenje gradimo.")

    t.p("Prvo, ocjena jednog jedinog kandidatnog rješenja nije jeftina. {~kempe2003} "
        "navode da je točno izračunavanje očekivanog dosega otvoreno pitanje i da se u "
        "praksi procjenjuje simulacijom slučajnog procesa. Pretraga koja tijekom rada "
        "ocijeni tisuće rezova zato mora računati s time da svaka ocjena stoji.")

    t.p("Drugo, sam problem nema dobru aproksimaciju. {~castiglioni2021} dokazuju da za "
        "IMER s konačnim proračunom ne postoji polinomijalan algoritam koji bi jamčio "
        "rješenje unutar bilo koje unaprijed zadane konstante, osim ako vrijedi P = NP.")

    t.p("Treće, i za izbor metode najvažnije, doseg nije submodularan u skupu uklonjenih "
        "bridova. Kod maksimizacije utjecaja doseg je submodularan u skupu početnih "
        "čvorova, pa pohlepni postupak koji dodaje jedan po jedan čvor jamči rješenje "
        "unutar 63 % optimalnoga {kempe2003}. To se jamstvo ne prenosi na naš problem, a ",
        first, " do ", third, " pokazuju zašto.")

    t.figure(figures / "fig3_base_choke.png",
             "Izvor je dvama neovisnim putovima povezan s gusto povezanom regijom. Doseg "
             "netaknutog grafa iznosi osam čvorova.",
             label="primjer1", width_cm=11.5)

    t.p("U netaknutom grafu izvor doseže svih osam čvorova. Uklonimo li samo brid prema ",
        v("a"), ", kao na ", second, ", doseg pada na sedam, jer kaskada i dalje teče "
        "kroz ", v("b"), ". Isto vrijedi i obrnuto. Uklonimo li pak oba brida iz izvora, "
        "doseg pada na "
        "jedan. Prvi brid donosi dobitak od jednog čvora, a drugi, dodan na prvi, dobitak "
        "od šest. Doprinos je dakle veći na većem skupu, što je rastući prinos i upravo "
        "suprotno od onoga što pohlepnom postupku treba.")

    t.figure(figures / "fig3_near_choke.png",
             "Uklonjen je jedan brid uz izvor, uz ograničenje k = 1. Doseg se smanjuje za "
             "jedan čvor jer kaskada i dalje teče drugim putom.",
             label="primjer2", width_cm=11.5)

    t.p("Isti primjer pokazuje i drugu stvar. Uz ograničenje ", v("k"),
        " = 1 najbolji potez nije uklanjanje brida uz izvor nego brida u uskom grlu, ",
        "kroz koje oba puta prolaze prije ulaska u gusto povezanu regiju. Time doseg pada "
        "s osam na četiri, dakle dvostruko više nego uklanjanjem brida uz izvor. Postavlja "
        "se pitanje koliko su takve prilike česte u stvarnoj mreži, na koje odgovaramo u "
        "odjeljku ", t.sec("udaljenost"), ".")

    t.figure(figures / "fig3_choke_choke.png",
             "Uklonjen je jedan brid u uskom grlu, uz isto ograničenje. Cijela gusto "
             "povezana regija time postaje nedohvatljiva.",
             label="primjer3", width_cm=11.5)

    t.p("Oba zapažanja vode istom zaključku o metodi. Postupak koji bridove bira jedan po "
        "jedan ne vidi da se dva brida isplate tek zajedno, pa je potrebna metoda koja "
        "mijenja više bridova odjednom. Slično zapažanje o skupovima bridova, doduše za "
        "drugu ciljnu veličinu, iznose i {~tong2012}: učinak uklanjanja skupa bridova nije "
        "zbroj učinaka pojedinačnih uklanjanja.")


# -- 3.3 ---------------------------------------------------------------------

def _estimation(t):
    t.h2("Procjena dosega", label="realizacije")

    t.p("Budući da se doseg ne može izračunati točno, procjenjujemo ga. Iz odjeljka ",
        t.sec("icm"), " znamo da je doseg u jednoj realizaciji obično pitanje "
        "dohvatljivosti. {~kimura2008} taj postupak koriste pod nazivom metode perkolacije "
        "veza: uzorkuje se ", v("M"), " realizacija, a doseg se procjenjuje prosječnom "
        "veličinom dohvatljivog skupa preko njih:")

    t.eq(acc(v("σ")), delim(v("s"), up(", "), v("D")), up(" = "), frac(up("1"), v("M")),
         nary("∑", [v("m"), up(" = 1")], v("M"),
              delim(ifunc("R", [v("s"), up(", "), sub(v("X"), v("m")), up(" \\ "), v("D")]),
                    left="|", right="|")),
         label="procjena")

    t.p("Jedna je pojedinost ovdje ključna. Realizacije uzorkujemo jednom i potom ih "
        "zamrznemo, umjesto da za svaki kandidatni rez izvlačimo nove. Time cilj postaje "
        "determinističan, pa razlika između dvaju rezova odražava njihovu kvalitetu, a ne "
        "šum uzorkovanja. Bez toga pretraga ne bi mogla pouzdano razlikovati dva bliska "
        "rješenja, jer bi se razlika među njima gubila u slučajnosti uzorka.")

    t.p("Cijena je te odluke da pronađeni optimum vrijedi za taj uzorak, a ne nužno i "
        "općenito. Zbog toga koristimo dva odvojena skupa realizacija: jedan vodi pretragu, "
        "a drugi, s njime nepovezan, služi isključivo za izvještavanje rezultata. Koliko se "
        "te dvije vrijednosti razilaze mjerimo u odjeljku ", t.sec("valjanost"),
        ", i to prije svake usporedbe metoda.")
