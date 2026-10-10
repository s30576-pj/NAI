"""Chomp — gra dla dwóch graczy (człowiek kontra AI) w terminalu.

Zasady: https://github.com/s30576-pj/NAI/blob/main/chomp/README.md

Autorzy: Natan Brzozowski, Patryk Szachniewicz

Przygotowanie środowiska:
    1. Zainstaluj Python 3.8 lub nowszy: https://www.python.org/downloads/
    2. Gra nie wymaga dodatkowych bibliotek.
    3. Pobierz repozytorium: git clone https://github.com/s30576-pj/NAI.git
    4. Przejdź do katalogu gry: cd NAI/chomp
    5. Uruchom: python chomp.py   (Linux/macOS: python3 chomp.py)
"""

import threading
import time
from functools import lru_cache

MIN_SIZE = 2             # najmniejsza liczba wierszy i kolumn
MAX_SIZE = 10            # największa liczba wierszy i kolumn
DEFAULT_ROWS = 3         # domyślna liczba wierszy (Enter)
DEFAULT_COLS = 4         # domyślna liczba kolumn (Enter)
ANIMATION_DELAY = 0.3    # co ile sekund zmieniają się kropki w "AI myśli..."
MIN_THINKING_TIME = 0.9  # najkrótszy czas wyświetlania "AI myśli..." (sekundy)


# --- Zasady gry ---

def create_board(rows, cols):
    """Tworzy pełną planszę (tabliczkę czekolady).

    Parameters:
    rows (int): liczba wierszy
    cols (int): liczba kolumn

    Returns:
    tuple: długości wierszy od dolnego, np. (4, 4, 4) dla planszy 3x4
    """
    return (cols,) * rows


def get_possible_moves(board):
    """Zwraca wszystkie możliwe ruchy oprócz zjedzenia trucizny.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego

    Returns:
    list: pary (wiersz, kolumna) numerowane od 1, bez trucizny (1, 1)
    """
    moves = []
    for row in range(1, len(board) + 1):
        for col in range(1, board[row - 1] + 1):
            if (row, col) != (1, 1):
                moves.append((row, col))
    return moves


def make_move(board, row, col):
    """Zjada wybraną kostkę oraz wszystkie kostki na prawo i powyżej.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego
    row (int): numer wiersza (1 = dolny)
    col (int): numer kolumny (1 = lewa)

    Returns:
    tuple: nowa plansza po ruchu
    """
    new_board = []
    for i, length in enumerate(board):
        if i >= row - 1:                 # wybrany wiersz i wszystkie wyższe
            length = min(length, col - 1)
        if length > 0:                   # pomijamy całkiem zjedzone wiersze
            new_board.append(length)
    return tuple(new_board)


# --- AI ---

@lru_cache(maxsize=None)                     # usprawnienie 1: zapamiętywanie wyników
def minimax(board, ai_turn):
    """Ocenia pozycję algorytmem Minimax, analizując grę aż do końca.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego
    ai_turn (bool): True, jeśli teraz ruch ma AI

    Returns:
    int: 1, jeśli AI wygra przy najlepszej grze obu stron; -1, jeśli przegra
    """
    if board == (1,):                        # została sama trucizna
        return -1 if ai_turn else 1          # gracz na ruchu musi ją zjeść
    if ai_turn:                              # AI wybiera najlepszy wynik dla siebie (max)
        best = -1
        for row, col in get_possible_moves(board):
            best = max(best, minimax(make_move(board, row, col), False))
            if best == 1:                    # usprawnienie 2: lepiej niż wygrana się nie da
                break
        return best
    best = 1                                 # człowiek wybiera najgorszy wynik dla AI (min)
    for row, col in get_possible_moves(board):
        best = min(best, minimax(make_move(board, row, col), True))
        if best == -1:                       # usprawnienie 2: gorzej dla AI się nie da
            break
    return best


def choose_ai_move(board):
    """Wybiera ruch AI na podstawie oceny Minimax.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego (nie sama trucizna)

    Returns:
    tuple: (wiersz, kolumna) wybranej kostki
    """
    moves = get_possible_moves(board)
    for row, col in moves:
        if minimax(make_move(board, row, col), False) == 1:
            return row, col                  # pierwszy ruch, po którym AI na pewno wygra
    # nie da się wygrać: zostawiamy jak najwięcej kostek, żeby przedłużyć grę
    return max(moves, key=lambda move: sum(make_move(board, move[0], move[1])))


# --- Terminal ---

def print_board(board, rows, cols):
    """Wyświetla planszę z legendą oraz numerami wierszy i kolumn.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego
    rows (int): liczba wierszy wybrana na początku gry
    cols (int): liczba kolumn wybrana na początku gry

    Returns:
    None
    """
    print("Legenda: # kostka, X trucizna, . zjedzone")
    for row in range(rows, 0, -1):                       # od górnego wiersza do dolnego
        line = f"{row:>2} "
        for col in range(1, cols + 1):
            if row <= len(board) and col <= board[row - 1]:  # kostka jeszcze istnieje
                symbol = "X" if (row, col) == (1, 1) else "#"
            else:
                symbol = "."
            line += f"{symbol:>3}"
        print(line)
    labels = "   "
    for col in range(1, cols + 1):
        labels += f"{col:>3}"
    print(labels)


def ask_number(prompt, low, high, default):
    """Pyta o liczbę całkowitą z podanego zakresu, aż gracz poda poprawną.

    Parameters:
    prompt (str): treść pytania
    low (int): najmniejsza dozwolona liczba
    high (int): największa dozwolona liczba
    default (int): liczba wybierana po wciśnięciu samego Enter

    Returns:
    int: liczba wybrana przez gracza
    """
    while True:
        answer = input(f"{prompt} ({low}-{high}, Enter = {default}): ").strip()
        if answer == "":
            return default
        if answer.isdecimal() and low <= int(answer) <= high:
            return int(answer)
        print(f"Wpisz liczbę od {low} do {high}.")


def ask_settings():
    """Pyta o rozmiar planszy i o to, kto zaczyna grę.

    Parameters:
    brak

    Returns:
    tuple: (liczba wierszy, liczba kolumn, True jeśli zaczyna człowiek)
    """
    rows = ask_number("Liczba wierszy", MIN_SIZE, MAX_SIZE, DEFAULT_ROWS)
    cols = ask_number("Liczba kolumn", MIN_SIZE, MAX_SIZE, DEFAULT_COLS)
    print("Zaczynający ma przewagę: grając bezbłędnie, zawsze wygrywa.")
    starter = ask_number("Kto zaczyna? 1 = ty, 2 = AI", 1, 2, 1)
    return rows, cols, starter == 1


def ask_human_move(board):
    """Pyta gracza o ruch, aż poda współrzędne istniejącej kostki.

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego

    Returns:
    tuple: (wiersz, kolumna) wybranej kostki; (1, 1) oznacza zjedzenie trucizny
    """
    while True:
        parts = input("Twój ruch (wiersz kolumna, np. 2 3): ").split()
        if len(parts) != 2 or not parts[0].isdecimal() or not parts[1].isdecimal():
            print("Wpisz dwie liczby oddzielone spacją, np. 2 3.")
            continue
        row, col = int(parts[0]), int(parts[1])
        if 1 <= row <= len(board) and 1 <= col <= board[row - 1]:
            return row, col
        print("Tej kostki nie ma na planszy. Wybierz pole oznaczone # albo X.")


def animate_thinking(stop_event):
    """Wyświetla w jednej linii animowany napis "AI myśli...", aż dostanie sygnał stopu.

    Parameters:
    stop_event (threading.Event): sygnał zakończenia animacji

    Returns:
    None
    """
    dots = 1
    while not stop_event.is_set():
        print("\rAI myśli" + "." * dots + "   ", end="", flush=True)  # spacje zamazują stare kropki
        dots = dots % 3 + 1                                           # 1, 2, 3, 1, 2, 3...
        stop_event.wait(ANIMATION_DELAY)


def get_ai_move_with_animation(board):
    """Wybiera ruch AI, pokazując w tym czasie animację "AI myśli...".

    Parameters:
    board (tuple): długości wierszy planszy, od dolnego (nie sama trucizna)

    Returns:
    tuple: (wiersz, kolumna) wybranej kostki
    """
    stop_event = threading.Event()
    spinner = threading.Thread(target=animate_thinking, args=(stop_event,), daemon=True)
    start = time.time()
    spinner.start()
    try:
        move = choose_ai_move(board)         # AI liczy w głównym wątku, więc Ctrl+C działa
        time.sleep(max(0, MIN_THINKING_TIME - (time.time() - start)))
    finally:                                 # zawsze zatrzymaj animację, także po Ctrl+C
        stop_event.set()
        spinner.join()
        print("\r" + " " * 20 + "\r", end="", flush=True)
    return move


# --- Gra ---

def play_game(rows, cols, human_starts):
    """Prowadzi jedną partię i ogłasza zwycięzcę.

    Parameters:
    rows (int): liczba wierszy planszy
    cols (int): liczba kolumn planszy
    human_starts (bool): True, jeśli pierwszy ruch wykonuje człowiek

    Returns:
    None
    """
    board = create_board(rows, cols)
    human_turn = human_starts
    while True:
        print()
        print_board(board, rows, cols)
        if board == (1,):                            # została sama trucizna
            print("Została tylko zatruta kostka — trzeba ją zjeść.")
            break
        if human_turn:
            row, col = ask_human_move(board)
        else:
            row, col = get_ai_move_with_animation(board)
            print(f"AI wybiera: wiersz {row}, kolumna {col}")
        if (row, col) == (1, 1):                     # ktoś zjadł truciznę
            print("Zatruta kostka zjedzona!")
            break
        board = make_move(board, row, col)
        human_turn = not human_turn
    # przegrywa ten, kto miał ruch, gdy zjedzono truciznę
    print("Wygrywa AI!" if human_turn else "Wygrywasz!")


def main():
    """Uruchamia grę Chomp i pozwala rozegrać kolejne partie.

    Parameters:
    brak

    Returns:
    None
    """
    print("=== CHOMP ===")
    try:
        while True:
            rows, cols, human_starts = ask_settings()
            play_game(rows, cols, human_starts)
            print()
            if ask_number("Zagrać jeszcze raz? 1 = tak, 2 = nie", 1, 2, 1) == 2:
                break
    except (KeyboardInterrupt, EOFError):    # Ctrl+C albo Ctrl+D (Windows: Ctrl+Z)
        print()
    print("Do zobaczenia!")


if __name__ == "__main__":
    main()
