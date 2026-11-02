"""Adaptacyjna sygnalizacja świetlna z wykorzystaniem logiki rozmytej.

Problem: skrzyżowanie dwóch kierunków ruchu, A i B. Światła same dobierają,
jak długo ma trwać zielone, na podstawie długości obu kolejek aut i tego,
jak długo czekają auta na czerwonym. Program symuluje skrzyżowanie
w czasie rzeczywistym (jeden krok na sekundę) i wypisuje decyzje sterownika.

Autorzy: Natan Brzozowski, Patryk Szachniewicz

Przygotowanie środowiska:
    1. Zainstaluj Python 3.8 lub nowszy: https://www.python.org/downloads/
    2. Program nie wymaga dodatkowych bibliotek.
    3. Pobierz repozytorium: git clone https://github.com/s30576-pj/NAI.git
    4. Przejdź do katalogu: cd NAI/sygnalizacja-rozmyta
    5. Uruchom: python sygnalizacja.py   (Linux/macOS: python3 sygnalizacja.py)
    6. Zakończ program skrótem Ctrl+C.

Logika rozmyta (metoda Sugeno): 3 wejścia, 1 wyjście, 8 reguł.
Wejścia: X1 - liczba aut na kierunku z zielonym, X2 - liczba aut na kierunku
z czerwonym, X3 - ile sekund czeka pierwsze auto na czerwonym.
Wyjście: ile sekund ma trwać zielone.
"""

import time

# Zbiory rozmyte każdego wejścia: 0 = "mało", 1 = "dużo"
MALO = 0
DUZO = 1

GRANICA_AUT = 10        # od tylu aut kolejka jest w pełni "duża"
GRANICA_CZEKANIA = 30   # od tylu sekund czekanie jest w pełni "duże"

# Reguły: (auta na zielonym, auta na czerwonym, czekanie na czerwonym, czas zielonego [s])
# Np. pierwsza: JEŚLI mało aut na zielonym I mało na czerwonym I mało czekania,
# TO zielone ma trwać 8 s.
REGULY = [
    (MALO, MALO, MALO, 8),
    (MALO, MALO, DUZO, 5),
    (MALO, DUZO, MALO, 6),
    (MALO, DUZO, DUZO, 5),
    (DUZO, MALO, MALO, 20),
    (DUZO, MALO, DUZO, 10),
    (DUZO, DUZO, MALO, 14),
    (DUZO, DUZO, DUZO, 6),
]

# Natężenie ruchu: (nazwa, co ile sekund przyjeżdża auto w A, co ile sekund w B)
NAPLYW = [
    ("ruch równy", 5, 5),
    ("przewaga A", 2, 8),
    ("przewaga B", 8, 2),
]
CZAS_TRYBU = 60  # co ile sekund zmienia się natężenie ruchu

NAZWY = ["A", "B"]


def przynaleznosc(wartosc, granica):
    """Rozmywanie: liczy, w jakim stopniu wartość jest "mała", a w jakim "duża".

    Stopień "dużo" rośnie liniowo od 0 (dla wartości 0) do 1 (dla granicy
    i więcej). Stopień "mało" to 1 minus stopień "dużo".

    Parameters:
    wartosc (int): liczba aut albo czas czekania w sekundach
    granica (int): wartość, od której wejście jest już w pełni "duże"

    Returns:
    list: [stopień "mało", stopień "dużo"], np. [0.7, 0.3] dla 3 aut i granicy 10
    """
    duzo = wartosc / granica
    if duzo > 1:
        duzo = 1
    malo = 1 - duzo
    return [malo, duzo]


def czas_zielonego(auta_zielone, auta_czerwone, czekanie):
    """Logika rozmyta (Sugeno): oblicza, ile sekund ma trwać zielone światło.

    Parameters:
    auta_zielone (int): X1 - liczba aut na kierunku z zielonym światłem
    auta_czerwone (int): X2 - liczba aut na kierunku z czerwonym światłem
    czekanie (int): X3 - ile sekund czeka pierwsze auto na czerwonym

    Returns:
    float: czas zielonego w sekundach (od 5 do 20), liczony od początku zielonego
    """
    # 1. Rozmywanie: każde wejście zamieniamy na stopnie "mało" i "dużo"
    stopnie_zielona = przynaleznosc(auta_zielone, GRANICA_AUT)
    stopnie_czerwona = przynaleznosc(auta_czerwone, GRANICA_AUT)
    stopnie_czekania = przynaleznosc(czekanie, GRANICA_CZEKANIA)

    suma_wazona = 0
    suma_wag = 0
    for regula in REGULY:
        zbior_zielona = regula[0]
        zbior_czerwona = regula[1]
        zbior_czekania = regula[2]
        wynik = regula[3]

        # 2. Reguły: siła reguły to iloczyn stopni jej trzech warunków
        waga = (stopnie_zielona[zbior_zielona]
                * stopnie_czerwona[zbior_czerwona]
                * stopnie_czekania[zbior_czekania])
        suma_wazona += waga * wynik
        suma_wag += waga

    # 3. Wyostrzanie: średnia ważona wyników reguł
    return suma_wazona / suma_wag


def main():
    """Uruchamia symulację skrzyżowania: jeden krok co sekundę, aż do Ctrl+C.

    W każdej sekundzie przyjeżdżają nowe auta, logika rozmyta liczy czas
    zielonego, jedno auto przejeżdża na zielonym, a gdy zielone trwa już
    tyle, ile wyliczyła logika rozmyta, zielone dostaje drugi kierunek.
    """
    kolejki = [[0] * 8, [0] * 3]  # sekundy przyjazdu aut; na starcie 8 aut w A i 3 w B
    zielone = 0                   # który kierunek ma zielone: 0 = A, 1 = B
    ile_trwa_zielone = 0          # ile sekund trwa już obecne zielone
    sekunda = 0

    print("Symulacja skrzyżowania. Ctrl+C kończy program.")
    while True:
        sekunda += 1
        ile_trwa_zielone += 1

        # Co 60 s następny tryb ruchu; po trzecim wracamy do pierwszego
        nazwa_trybu, odstep_a, odstep_b = NAPLYW[(sekunda // CZAS_TRYBU) % 3]

        # Przyjazd aut: zapisujemy, w której sekundzie auto stanęło w kolejce
        if sekunda % odstep_a == 0:
            kolejki[0].append(sekunda)
        if sekunda % odstep_b == 0:
            kolejki[1].append(sekunda)

        # Trzy wejścia logiki rozmytej
        czerwone = 1 - zielone
        auta_zielone = len(kolejki[zielone])
        auta_czerwone = len(kolejki[czerwone])
        czekanie = 0
        if auta_czerwone > 0:
            czekanie = sekunda - kolejki[czerwone][0]

        wynik = czas_zielonego(auta_zielone, auta_czerwone, czekanie)

        print(f"{sekunda} s | {nazwa_trybu} | zielone: {NAZWY[zielone]} od {ile_trwa_zielone} s"
              f" | A: {len(kolejki[0])} aut, B: {len(kolejki[1])} aut"
              f" | czekanie na czerwonym: {czekanie} s -> zielone {wynik:.1f} s")

        # Na zielonym przejeżdża jedno auto na sekundę
        if auta_zielone > 0:
            kolejki[zielone].pop(0)

        # Zmieniamy światła, gdy zielone trwa już tyle, ile wyliczyła logika rozmyta
        if ile_trwa_zielone >= wynik:
            zielone = czerwone
            ile_trwa_zielone = 0

        time.sleep(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKoniec symulacji.")
