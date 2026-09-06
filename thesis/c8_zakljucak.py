"""Zakljucak.

Unnumbered, as the template requires. States what was asked, what was found, and what the
work does not establish, in that order, with every number read from the CSVs.
"""

import sys
from pathlib import Path

CODE = Path(__file__).resolve().parent.parent / "code"
if str(CODE) not in sys.path:
    sys.path.insert(0, str(CODE))

from results_analysis import (  # noqa: E402  (path must be set first)
    comparison_table, hop_summary, load_results, oracle_summary)


def _signed(value, decimals=3):
    rounded = round(abs(value), decimals)
    text = f"{rounded:.{decimals}f}".replace(".", ",")
    if rounded == 0:
        return text
    return ("+" if value > 0 else "−") + text


def write(t, figures):
    results = load_results(figures.parent / "data" / "results.csv")
    table = comparison_table(results)
    prob = table[table.criterion == "probability"].iloc[0]
    oracle = oracle_summary(results)
    hop = hop_summary(results)

    t.h1("Zaključak", numbered=False)

    t.p("U radu je razmotren problem smanjenja dosega kaskade iz jednog zadanog izvora "
        "uklanjanjem zadanog broja bridova, nazvan SS-IMER. Za njegovo je rješavanje "
        "prilagođena metaheuristika ALNS, koja u svakoj iteraciji razara i ponovno gradi "
        "cijelo rješenje, a uspoređena je sa šest pohlepnih metoda, po jednom za svaki "
        "topološki kriterij. Mjerenje je provedeno na mreži povjerenja Bitcoin Alpha.")

    t.p("Prilagodljivo pretraživanje pokazalo se uspješnim, ali ne jednako na svim "
        "instancama. Pet od šest kriterija metaheuristika nadmašuje uvjerljivo, dok je "
        "naspram vjerojatnosti prijenosa, jedinog ozbiljnog protivnika, prosječna prednost "
        "od ", _signed(prob.mean_delta), " unutar reda veličine same pogreške procjene. "
        "Podjela po izvorima pokazuje da je prednost stvarna na izvorima srednjeg dosega, "
        "a nestaje na zasićenima, kojima zadani broj iteracija nije dovoljan. Najjači je "
        "nalaz da metaheuristika bez ikakva predznanja o instanci postiže gotovo jednako "
        "kao odabir najboljeg od šest kriterija unatrag, uz razliku manju od tisućinke i "
        "izjednačen ili bolji ishod na ", str(oracle["alns_at_least"]), " od ",
        str(oracle["cells"]), " instanci.")

    t.p("Na drugo pitanje, koliko daleko od izvora leže bridovi koje se isplati ukloniti, "
        "odgovor je negativan i objašnjiv. Od ", str(hop["cells"]), " instanci njih ",
        str(hop["pure_hop0"]), " ima rez sastavljen isključivo od bridova uz izvor, a "
        "instance koje su duljom pretragom dobile priliku za usporedbu dublje su bridove "
        "same odbacile. Razlog leži u samoj mreži: gotovo svaki izvor doseže isti skup "
        "čvorova, pa uskih grla u osnovnom grafu nema. Mehanizam slojeva nije zakazao, "
        "nego u ovoj mreži nije imao što pronaći.")

    t.p("Upravo taj nalaz određuje i najvažniji smjer nastavka. Ako osnovni graf ne "
        "razlikuje bridove, korisna struktura mora ležati u samim realizacijama, gdje uska "
        "grla postoje, iako pripadaju pojedinom izvlačenju. Kriterij izveden iz "
        "realizacija bio bi upravo ono za što su svi ovdje ispitani kriteriji slijepi, a "
        "provesti ga nije skupo jer su realizacije već izračunate.")

    t.p("Naposljetku, valja jasno reći što rad ne pokazuje. Uspoređene su prilagodljiva "
        "pretraga i nepromjenjivi topološki kriteriji, a ne pretraga i najbolja poznata "
        "metoda za ovaj problem. Svi rezultati počivaju na jednoj mreži i jednom sjemenu "
        "slučajnosti, a pretraga nikada nije gledala dalje od trećeg sloja oko izvora.")
