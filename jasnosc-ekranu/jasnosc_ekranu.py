"""Automatyczna jasność ekranu telefonu z wykorzystaniem logiki rozmytej.

Problem: telefon sam dobiera jasność ekranu. Na słońcu ekran musi być jasny,
żeby było coś widać, a w ciemności wystarczy ciemniejszy. Gdy bateria jest
słaba albo nikt od dawna nie dotyka ekranu, jasność spada, żeby oszczędzać
baterię. Program symuluje używanie telefonu w czasie rzeczywistym (jeden krok
na sekundę) i wypisuje jasność wybraną przez logikę rozmytą.

Autorzy: Natan Brzozowski, Patryk Szachniewicz

Przygotowanie środowiska:
    1. Zainstaluj Python 3.8 lub nowszy: https://www.python.org/downloads/
    2. Program nie wymaga dodatkowych bibliotek.
    3. Pobierz repozytorium: git clone https://github.com/s30576-pj/NAI.git
    4. Przejdź do katalogu: cd NAI/jasnosc-ekranu
    5. Uruchom: python jasnosc_ekranu.py   (Linux/macOS: python3 jasnosc_ekranu.py)
    6. Program kończy się sam, gdy bateria się rozładuje, albo skrótem Ctrl+C.

Logika rozmyta (metoda Sugeno): 3 wejścia, 1 wyjście, 8 reguł.
Wejścia: X1 - jasność otoczenia w % (0 = ciemno, 100 = pełne słońce),
X2 - poziom baterii w %, X3 - ile sekund minęło od ostatniego dotknięcia ekranu.
Wyjście: jasność ekranu w %.
"""

import time

# Zbiory rozmyte każdego wejścia: 0 = "mało", 1 = "dużo"
MALO = 0
DUZO = 1

GRANICA_SWIATLA = 100   # od tylu % otoczenie jest w pełni "jasne"
GRANICA_BATERII = 100   # od tylu % bateria jest w pełni "naładowana"
GRANICA_DOTYKU = 30     # od tylu sekund bez dotyku telefon jest w pełni "odłożony"

# Reguły: (jasność otoczenia, poziom baterii, czas bez dotyku, jasność ekranu [%])
# Np. pierwsza: JEŚLI mało światła I mało baterii I mało czasu bez dotyku,
# TO jasność ekranu 20%.
REGULY = [
    (MALO, MALO, MALO, 20),     # ciemno, słaba bateria, telefon używany
    (MALO, MALO, DUZO, 5),      # ciemno, słaba bateria, telefon odłożony
    (MALO, DUZO, MALO, 40),     # ciemno, pełna bateria, telefon używany
    (MALO, DUZO, DUZO, 10),     # ciemno, pełna bateria, telefon odłożony
    (DUZO, MALO, MALO, 60),     # słońce, słaba bateria, telefon używany
    (DUZO, MALO, DUZO, 15),     # słońce, słaba bateria, telefon odłożony
    (DUZO, DUZO, MALO, 100),    # słońce, pełna bateria, telefon używany
    (DUZO, DUZO, DUZO, 30),     # słońce, pełna bateria, telefon odłożony
]

# Sposób używania telefonu: (opis, jasność otoczenia [%], co ile sekund użytkownik dotyka ekranu)
TRYBY = [
    ("w pokoju, przewijanie", 40, 3),
    ("w słońcu, mapa", 100, 10),
    ("wieczorem, czytanie", 5, 20),
]
CZAS_TRYBU = 30  # co ile sekund zmienia się sposób używania telefonu


def przynaleznosc(wartosc, granica):
    """Rozmywanie: liczy, w jakim stopniu wartość jest "mała", a w jakim "duża".

    Stopień "dużo" rośnie liniowo od 0 (dla wartości 0) do 1 (dla granicy
    i więcej). Stopień "mało" to 1 minus stopień "dużo".

    Parameters:
    wartosc (float): jasność otoczenia, poziom baterii albo czas bez dotyku
    granica (int): wartość, od której wejście jest już w pełni "duże"

    Returns:
    list: [stopień "mało", stopień "dużo"], np. [0.7, 0.3] dla 9 s i granicy 30
    """
    duzo = wartosc / granica
    if duzo > 1:
        duzo = 1
    malo = 1 - duzo
    return [malo, duzo]


def jasnosc_ekranu(swiatlo, bateria, bez_dotyku):
    """Logika rozmyta (Sugeno): oblicza, jaka ma być jasność ekranu.

    Parameters:
    swiatlo (int): X1 - jasność otoczenia w % (0 = ciemno, 100 = pełne słońce)
    bateria (float): X2 - poziom baterii w %
    bez_dotyku (int): X3 - ile sekund minęło od ostatniego dotknięcia ekranu

    Returns:
    float: jasność ekranu w % (od 5 do 100)
    """
    # 1. Rozmywanie: każde wejście zamieniamy na stopnie "mało" i "dużo"
    stopnie_swiatla = przynaleznosc(swiatlo, GRANICA_SWIATLA)
    stopnie_baterii = przynaleznosc(bateria, GRANICA_BATERII)
    stopnie_dotyku = przynaleznosc(bez_dotyku, GRANICA_DOTYKU)

    suma_wazona = 0
    suma_wag = 0
    for regula in REGULY:
        zbior_swiatla = regula[0]
        zbior_baterii = regula[1]
        zbior_dotyku = regula[2]
        wynik = regula[3]

        # 2. Reguły: siła reguły to iloczyn stopni jej trzech warunków
        waga = (stopnie_swiatla[zbior_swiatla]
                * stopnie_baterii[zbior_baterii]
                * stopnie_dotyku[zbior_dotyku])
        suma_wazona += waga * wynik
        suma_wag += waga

    # 3. Wyostrzanie: średnia ważona wyników reguł
    return suma_wazona / suma_wag


def main():
    """Uruchamia symulację telefonu: jeden krok co sekundę, aż rozładuje się bateria.

    Co 30 s zmienia się sposób używania telefonu (jasność otoczenia i to, jak często
    użytkownik dotyka ekranu). W każdej sekundzie logika rozmyta liczy jasność ekranu,
    a ekran zużywa baterię: im jaśniejszy, tym szybciej.
    """
    bateria = 100      # poziom baterii w %
    bez_dotyku = 0     # ile sekund minęło od ostatniego dotknięcia ekranu
    sekunda = 0

    print("Symulacja jasności ekranu. Ctrl+C kończy program.")
    while bateria > 0:
        sekunda += 1

        # Co 30 s następny sposób używania telefonu; po ostatnim wracamy do pierwszego
        numer_trybu = (sekunda // CZAS_TRYBU) % len(TRYBY)
        tryb = TRYBY[numer_trybu]
        opis = tryb[0]
        swiatlo = tryb[1]
        co_ile_dotyk = tryb[2]

        # Dotknięcie ekranu zeruje licznik, bez dotknięcia licznik rośnie
        if sekunda % co_ile_dotyk == 0:
            bez_dotyku = 0
        else:
            bez_dotyku += 1

        # Trzy wejścia logiki rozmytej -> jedno wyjście
        jasnosc = jasnosc_ekranu(swiatlo, bateria, bez_dotyku)

        print(f"{sekunda} s | {opis} | otoczenie: {swiatlo}% | bateria: {bateria:.1f}% | bez dotyku: {bez_dotyku} s -> jasność ekranu {jasnosc:.1f}%")

        # Ekran zużywa baterię: przy jasności 100% ubywa 1% baterii na sekundę
        # (dużo szybciej niż w prawdziwym telefonie, żeby efekt było widać po kilku minutach)
        bateria -= jasnosc / 100

        time.sleep(1)

    print("Bateria rozładowana. Koniec symulacji.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nKoniec symulacji.")
