from .blinds import MAX_ANTE
from .cards import Suit

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"

BAR_WIDTH = 24


def clear_screen():
    print("\033[2J\033[H", end="")


def colorize_card(card):
    color = RED if card.suit in (Suit.HEARTS, Suit.DIAMONDS) else WHITE
    return f"{color}[{card.rank.label}{card.suit.symbol}]{RESET}"


def render_hand(hand):
    parts = [f"{DIM}{i + 1}{RESET}:{colorize_card(c)}" for i, c in enumerate(hand)]
    print(" ".join(parts))


def _progress_bar(value, target):
    ratio = min(1.0, value / target) if target else 1.0
    filled = int(ratio * BAR_WIDTH)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    color = GREEN if ratio >= 1.0 else YELLOW
    return f"{color}[{bar}]{RESET}"


def render_status(game):
    blind = game.current_blind
    print(f"{BOLD}{CYAN}=== BALALITE — Balatro 팬게임 (비공식) ==={RESET}")
    print(f"Ante {game.ante}/{MAX_ANTE}  {BOLD}{blind.label}{RESET}  목표 점수: {YELLOW}{blind.requirement}{RESET}")
    bar = _progress_bar(game.round_score, blind.requirement)
    print(f"현재 점수: {game.round_score} / {blind.requirement}  {bar}")
    print(f"플레이 {game.plays_left}회 남음 | 버리기 {game.discards_left}회 남음 | {GREEN}${game.money}{RESET}")
    joker_str = ", ".join(j.name for j in game.jokers) if game.jokers else "(없음)"
    print(f"조커 ({len(game.jokers)}/5): {joker_str}")
    if game.last_result:
        hand_type, chips, mult, gained = game.last_result
        print(f"{MAGENTA}지난 플레이: {hand_type.label}  {int(chips)} 칩 x {mult:g} 배 = {gained}점{RESET}")
    print()


def render_hand_prompt(game):
    render_hand(game.hand)
    print()
    print(f"{DIM}p 1 2 3 (플레이) | d 1 2 (버리기) | s (정렬) | j (조커 도감) | h (도움말) | q (그만두기){RESET}")


def render_shop(game):
    print(f"{BOLD}{CYAN}=== 상점 ==={RESET}")
    print(f"{blind_clear_line(game)}")
    print(f"보유 금액: {GREEN}${game.money}{RESET}   조커 슬롯: {len(game.jokers)}/5")
    print()
    if not game.shop_offers:
        print("(더 이상 살 수 있는 조커가 없습니다)")
    for i, joker in enumerate(game.shop_offers):
        print(f" {i + 1}: {BOLD}{joker.name}{RESET} — {joker.description}  ({YELLOW}${joker.cost}{RESET})")
    print()
    if game.shop_message:
        print(f"{MAGENTA}{game.shop_message}{RESET}")
    print(f"{DIM}b 1 (구매) | c (다음 블라인드로) | j (보유 조커) | h (도움말) | q (그만두기){RESET}")


def blind_clear_line(game):
    blind = game.blinds[game.blind_index]
    return f"{blind.label} 클리어! 보상 +${game.last_reward}"


def render_joker_details(jokers, title="보유 조커"):
    print(f"{BOLD}{title}{RESET}")
    if not jokers:
        print("(없음)")
    for j in jokers:
        print(f" - {BOLD}{j.name}{RESET}: {j.description} ({YELLOW}${j.cost}{RESET})")
    print()


def render_help(phase):
    print(f"{BOLD}도움말{RESET}")
    print("카드 번호는 화면에 표시된 1부터 시작하는 인덱스입니다.")
    if phase == "blind":
        print(" p <번호...>  선택한 1~5장을 플레이해 점수를 냅니다 (예: p 1 3 5)")
        print(" d <번호...>  선택한 카드를 버리고 새로 뽑습니다 (예: d 2 4)")
        print(" s            손패 정렬 방식을 랭크/무늬로 전환합니다")
    else:
        print(" b <번호>     상점에서 해당 번호의 조커를 구매합니다 (예: b 1)")
        print(" c            다음 블라인드로 진행합니다")
    print(" j            조커 정보를 확인합니다")
    print(" h            이 도움말을 다시 봅니다")
    print(" q            게임을 종료합니다")
    print()


def render_title():
    clear_screen()
    print(f"{BOLD}{CYAN}")
    print("  ____        _       _ _ _       ")
    print(" |  _ \\      | |     | (_) |      ")
    print(" | |_) | __ _| | __ _| |_| |_ ___  ")
    print(" |  _ < / _` | |/ _` | | | __/ _ \\ ")
    print(" | |_) | (_| | | (_| | | | ||  __/ ")
    print(" |____/ \\__,_|_|\\__,_|_|_|\\__\\___| ")
    print(f"{RESET}")
    print("포커 카드로 승부하는 로그라이크 — 사무실 몰래 즐기는 팬게임 MVP")
    print(f"{DIM}본 게임은 'Balatro'(LocalThunk/Playstack)에서 영감을 받은{RESET}")
    print(f"{DIM}비공식·비상업적 팬게임이며 원작과 관련이 없습니다.{RESET}")
    print()


def render_end_screen(game):
    print()
    if game.phase == "victory":
        print(f"{BOLD}{GREEN}🎉 축하합니다! 모든 앤티({MAX_ANTE})를 클리어했습니다! 🎉{RESET}")
    else:
        blind = game.current_blind
        print(f"{BOLD}{RED}게임 오버 — Ante {game.ante} {blind.label}에서 탈락{RESET}")
        print(f"목표 {blind.requirement}점 중 {game.round_score}점 달성")
    print()
    render_joker_details(game.jokers, title="최종 보유 조커")
    print(f"최종 자금: ${game.money}")
    print()
