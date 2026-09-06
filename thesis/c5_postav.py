"""5. Eksperimentalni postav.

Short by design: the pipeline figure carries the architecture, and the prose covers only
what a reader needs in order to judge the results in chapter 6. Scenario counts, seeds and
the iteration budget are imported from code/config.py; the sample composition is read from
data/sample.csv.
"""

import pandas as pd

import params
from params import config


def write(t, figures):
    sample = pd.read_csv(figures.parent / "data" / "sample.csv")
    roles = sample.role.value_counts()

    t.h1("Eksperimentalni postav", label="postav")

    t.p("Postupak je organiziran tako da se sve što ne ovisi o pojedinom rješenju izračuna "
        "unaprijed. ", t.figref("cjevovod"), " prikazuje tijek obrade. Iz sirovih se "
        "podataka jednom gradi graf s vjerojatnostima, iz njega jednom sva obilježja "
        "bridova i zamrznute realizacije, a jednom po izvoru sve što ovisi o izvoru, poput "
        "udaljenosti i slojeva. Unutar petlje ostaje samo procjena dosega, koja se za svaki "
        "kandidatni rez mora računati iznova i koja je zato jedini stvarni trošak pretrage.")

    t.figure(figures / "fig6_1_pipeline.png",
             "Tijek obrade. Obilježja bridova i realizacije računaju se jednom po grafu, "
             "kontekst izvora jednom po izvoru, a jedino se procjena dosega ponavlja za "
             "svaki kandidatni rez.",
             label="cjevovod", width_cm=13.0)

    t.p("Realizacije su podijeljene u dva odvojena skupa, kako traži odjeljak ",
        t.sec("realizacije"), ". Pretragu vodi skup od ",
        params.count(config.SAA_SCENARIO_COUNT, "realizacije", "realizacije",
                     "realizacija"),
        ", a rezultat se izvještava na neovisnom skupu od ",
        params.count(config.MC_SCENARIO_COUNT, "realizacije", "realizacije", "realizacija"),
        ". Skupovi su izvedeni iz različitih sjemena slučajnosti pa nemaju nijednu "
        "zajedničku realizaciju, čime je neovisnost osigurana konstrukcijom, a ne "
        "provjerom nakon činjenice.")

    t.p("Izvore biramo raslojenim uzorkom, po pojasevima izlaznog stupnja i razredima "
        "dosega, iz razloga navedenih u odjeljku ", t.sec("izvori"), ". Uzorak obuhvaća ",
        params.count(roles.get("calibration", 0), "izvor", "izvora", "izvora"),
        " za ugađanje parametara i ", params.count(roles.get("measurement", 0), "izvor",
                                                   "izvora", "izvora"),
        " za mjerenje. Ta su dva skupa razdvojena po konstrukciji, jer se uzorak za "
        "ugađanje izdvaja prvi, a mjerni se popunjava iz preostalih izvora, pa se nijedan "
        "izvor ne pojavljuje u oba.")

    t.p("Mjerenje bilježi jedan redak po trojcu izvora, proračuna i metode. Nikada se ne "
        "zapisuje stupac koji bi neku metodu miješao s njezinim protivnicima, jer se svaka "
        "takva veličina može izračunati naknadno, a upisana u mjerenje postala bi "
        "nepromjenjiva. Uz svaki se redak bilježe obje vrijednosti dosega, ona na kojoj je "
        "pretraga optimirala i ona s neovisnog skupa, kao i njihova razlika. Kada bi se "
        "bilježila samo jedna, prilagođenost uzorku ne bi se mogla ni izmjeriti.")

    t.p("Metaheuristika je pokrenuta uz ",
        params.count(config.ALNS_MAX_ITER, "iteraciju", "iteracije", "iteracija"),
        " po instanci. Pohlepne su metode determinističke, pa se za svaki par izvora i "
        "proračuna računaju jednom i ponovno koriste. Ponovljivost cijeloga postupka nije "
        "samo tvrdnja: dio je instanci u kasnijoj obradi nenamjerno ponovljen uz "
        "identične postavke i sve su redom reproducirale prijašnji rezultat do zadnje "
        "decimale.")
