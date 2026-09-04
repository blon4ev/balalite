import random
import time

from .blinds import MAX_ANTE
from .cards import Suit
from .consumables import LEVEL_BONUS
from .decks import deck_by_key
from .jokers import RARITY_LABEL
from .scoring import HandType
from .stakes import stake_by_level

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
CYAN = "\033[36m"
YELLOW = "\033[33m"
GREEN = "\033[32m"
MAGENTA = "\033[35m"
WHITE = "\033[37m"
BLUE = "\033[34m"

BAR_WIDTH = 24

ENHANCEMENT_TAG_COLOR = {
    "bonus": YELLOW,
    "mult": MAGENTA,
    "wild": CYAN,
    "glass": BLUE,
}
ENHANCEMENT_SGR = {
    "bonus": 33,
    "mult": 35,
    "wild": 36,
    "glass": 34,
}
EDITION_TAG_COLOR = {
    "foil": GREEN,
    "holographic": MAGENTA,
    "polychrome": YELLOW,
}
EDITION_SGR = {
    "foil": 32,
    "holographic": 35,
    "polychrome": 33,
}
RARITY_COLOR = {
    "common": WHITE,
    "uncommon": CYAN,
    "rare": BLUE,
    "legendary": YELLOW,
}
SEAL_DOT_COLOR = {
    "red": RED,
    "gold": YELLOW,
    "blue": BLUE,
}


def clear_screen():
    print("\033[2J\033[H", end="")


def _rule(width=60):
    print(f"{DIM}{'─' * width}{RESET}")


def _edition_marked_name(item):
    if getattr(item, "edition", None) == "negative":
        return f"{item.name}{MAGENTA}✦{RESET}"
    return item.name


FAKE_LOG_LINES = [
    "Compiling TypeScript sources...",
    "Waiting for database migration...",
    "Linting changed files...",
    "Rebuilding dependency graph...",
    "Bundling assets...",
    "Running type checker...",
    "Restoring npm cache...",
]


def _fake_terminal_header(progress_ratio=None):
    """실제 빌드/테스트 로그처럼 보이는 위장용 헤더. 사무실에서 흘끗 봐도 게임처럼
    안 보이도록 상단 배너를 이걸로 대체한다."""
    now = time.strftime("%H:%M:%S")
    total = 50
    if progress_ratio is None:
        passed = random.randint(30, 49)
    else:
        passed = max(1, min(total, round(total * min(1.0, max(0.0, progress_ratio)))))
    print(f"{DIM}${RESET} npm run test:integration")
    print(f"{DIM}[{now}]{RESET} Running integration suite... ({GREEN}{passed}/{total} passed{RESET})")
    print(f"{DIM}[{now}] {random.choice(FAKE_LOG_LINES)}{RESET}")


def colorize_card(card):
    """카드를 다음 규칙으로 표시한다:
    - 강화가 있으면 괄호 모양이 ⟦ ⟧로 바뀌고 색이 강화 종류를 나타낸다 (색 없이도 모양으로 구분 가능).
    - 에디션이 있으면 카드 전체가 반전(reverse video)되어 "빛나는" 것처럼 보인다.
    - 씰이 있으면 카드 앞에 색점(●)이 붙는다.
    """
    base_code = 31 if card.suit in (Suit.HEARTS, Suit.DIAMONDS) else 37

    if card.enhancement:
        color_code = ENHANCEMENT_SGR.get(card.enhancement, base_code)
        open_br, close_br = "⟦", "⟧"
    elif card.edition:
        color_code = EDITION_SGR.get(card.edition, base_code)
        open_br, close_br = "[", "]"
    else:
        color_code = base_code
        open_br, close_br = "[", "]"

    reverse = "7;" if card.edition else ""
    body = f"\033[{reverse}{color_code}m{open_br}{card.suit.symbol} {card.rank.label}{close_br}{RESET}"

    if card.seal:
        seal_color = SEAL_DOT_COLOR.get(card.seal, WHITE)
        body = f"{seal_color}●{RESET}{body}"

    return body


def render_hand(hand):
    parts = [f"{DIM}{i + 1}{RESET}:{colorize_card(c)}" for i, c in enumerate(hand)]
    print(" ".join(parts))


def render_legend():
    print(
        f"{DIM}표시 범례 — 강화(괄호가 {RESET}⟦ ⟧{DIM}로 바뀌고 색이 다름): "
        f"{ENHANCEMENT_TAG_COLOR['bonus']}노랑{RESET}{DIM}=보너스+30칩 "
        f"{ENHANCEMENT_TAG_COLOR['mult']}자홍{RESET}{DIM}=멀티+4배수 "
        f"{ENHANCEMENT_TAG_COLOR['wild']}청록{RESET}{DIM}=와일드무늬 "
        f"{ENHANCEMENT_TAG_COLOR['glass']}파랑{RESET}{DIM}=유리x2(파괴위험){RESET}"
    )
    print(
        f"{DIM}에디션(카드 전체가 반전되어 빛남): "
        f"{EDITION_TAG_COLOR['foil']}초록빛{RESET}{DIM}=포일+50칩 "
        f"{EDITION_TAG_COLOR['holographic']}자홍빛{RESET}{DIM}=홀로+10배수 "
        f"{EDITION_TAG_COLOR['polychrome']}노랑빛{RESET}{DIM}=폴리x1.5   "
        f"씰(카드 앞 점): "
        f"{SEAL_DOT_COLOR['red']}●{RESET}{DIM}적(레트리거) "
        f"{SEAL_DOT_COLOR['gold']}●{RESET}{DIM}금(+$3) "
        f"{SEAL_DOT_COLOR['blue']}●{RESET}{DIM}청(소모품){RESET}"
    )


def render_hand_guide(game):
    print(f"{BOLD}{CYAN}=== 족보표 (약한 순 → 강한 순) ==={RESET}")
    for ht in HandType:
        level = game.hand_levels.get(ht, 0)
        line = f" {BOLD}{ht.label}{RESET} — 기본 {ht.base_chips}칩 × {ht.base_mult}배"
        if level > 0:
            level_chips, level_mult = LEVEL_BONUS.get(ht, (0, 0))
            cur_chips = ht.base_chips + level * level_chips
            cur_mult = ht.base_mult + level * level_mult
            line += f"  {GREEN}(Lv.{level} 룬 적용 → {cur_chips}칩 × {cur_mult}배){RESET}"
        print(line)
    print()
    print(f"{DIM}점수 = (기본 칩 + 카드 자체 값 + 강화/에디션/조커 보너스) × (기본 배수 + 보너스){RESET}")
    print(f"{DIM}예: 페어(K,K) = 기본 10칩 + 10+10(카드값) = 30칩, 기본 2배 → 30 × 2 = 60점{RESET}")
    print()


def _progress_bar(value, target):
    ratio = min(1.0, value / target) if target else 1.0
    filled = int(ratio * BAR_WIDTH)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    color = GREEN if ratio >= 1.0 else YELLOW
    return f"{color}[{bar}]{RESET}"


def render_status(game):
    blind = game.current_blind
    ratio = game.round_score / blind.requirement if blind.requirement else 1.0
    _fake_terminal_header(ratio)
    _rule()
    print(f"Ante {game.ante}/{MAX_ANTE}  {BOLD}{blind.label}{RESET}  목표 점수: {YELLOW}{blind.requirement}{RESET}")
    if game.boss_effect:
        print(f"{RED}보스 효과: {game.boss_effect.description}{RESET}")
    bar = _progress_bar(game.round_score, blind.requirement)
    print(f"현재 점수: {game.round_score} / {blind.requirement}  {bar}")
    print(f"플레이 {game.plays_left}회 남음 | 버리기 {game.discards_left}회 남음 | {GREEN}${game.money}{RESET}")
    joker_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(j)}" for i, j in enumerate(game.jokers))
        if game.jokers
        else "(없음)"
    )
    print(f"조커 ({game.joker_slot_count()}/{game.max_joker_slots}): {joker_str}")
    consumable_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(c)}" for i, c in enumerate(game.consumables))
        if game.consumables
        else "(없음)"
    )
    print(f"소모품 ({game.consumable_slot_count()}/{game.max_consumable_slots}): {consumable_str}")
    if game.last_result:
        hand_type, chips, mult, gained, destroyed = game.last_result
        remaining = max(0, blind.requirement - game.round_score)
        print(
            f"{MAGENTA}{BOLD}▶ {hand_type.label}{RESET}{MAGENTA}   {int(chips)}칩 × {mult:g}배 = "
            f"{RESET}{GREEN}{BOLD}+{gained}점{RESET}"
        )
        if remaining > 0:
            print(f"{DIM}   (목표까지 남은 점수: {remaining}){RESET}")
        else:
            print(f"{GREEN}{BOLD}   목표 달성! 곧 블라인드가 클리어됩니다.{RESET}")
        if destroyed:
            names = ", ".join(str(c) for c in destroyed)
            print(f"{BLUE}   유리 카드 파괴됨: {names}{RESET}")
    if game.last_tag_message:
        print(f"{CYAN}{game.last_tag_message}{RESET}")
    _rule()


def render_hand_prompt(game):
    print()
    render_hand(game.hand)
    print()
    hints = ["p 1 2 3 (플레이)", "d 1 2 (버리기)", "u 1 [카드번호] (소모품 사용)", "x 1 (조커 판매)"]
    if game.can_skip_blind():
        hints.append("skip (블라인드 스킵)")
    hints += [
        "s (정렬)",
        "rank (족보표)",
        "j (보유 정보)",
        "legend (표시 범례)",
        "save (저장 후 종료)",
        "h (도움말)",
        "q (그만두기)",
    ]
    print(f"{DIM}" + " | ".join(hints) + f"{RESET}")


OFFER_KIND_LABELS = {
    "rune": "룬",
    "enhancer": "강화석",
    "editioner": "에디션석",
    "sealer": "인장석",
    "spectral": "스펙트럴",
    "charm": "부적",
}


def _offer_kind_tag(item):
    if hasattr(item, "timing"):
        rarity_color = RARITY_COLOR.get(item.rarity, WHITE)
        return f"조커·{rarity_color}{RARITY_LABEL.get(item.rarity, item.rarity)}{RESET}"
    kind = getattr(item, "kind", None)
    if kind == "voucher":
        return "바우처"
    if kind == "pack":
        return "부스터 팩"
    return OFFER_KIND_LABELS.get(kind, kind)


def _offer_line(i, item, game):
    kind_tag = _offer_kind_tag(item)
    cost = game._discounted_cost(item.cost)
    cost_str = f"{YELLOW}${cost}{RESET}"
    if cost != item.cost:
        cost_str = f"{DIM}${item.cost}{RESET} → {cost_str}"
    return f" {i + 1}: {BOLD}{item.name}{RESET} [{kind_tag}] — {item.description}  ({cost_str})"


# 실제 발라트로처럼 상점을 "카드(조커·소모품) / 부스터 팩 / 바우처" 세 영역으로
# 시각적으로 구분해서 보여준다. 구매·판매에 쓰는 번호는 game.shop_offers의
# 전체 인덱스를 그대로 유지한다 (영역은 표시용일 뿐).
_OFFER_GROUP_ORDER = ["card", "pack", "voucher"]
_OFFER_GROUP_LABELS = {
    "card": "카드 (조커 · 소모품)",
    "pack": "부스터 팩",
    "voucher": "바우처",
}


def _offer_group(item):
    kind = getattr(item, "kind", None)
    if kind == "pack":
        return "pack"
    if kind == "voucher":
        return "voucher"
    return "card"


def render_shop(game):
    _fake_terminal_header()
    _rule()
    print(f"{blind_clear_line(game)}")
    if game.last_interest:
        print(f"{GREEN}이자 수입: +${game.last_interest}{RESET}")
    print(
        f"보유 금액: {GREEN}${game.money}{RESET}   조커 슬롯: {game.joker_slot_count()}/{game.max_joker_slots}   "
        f"소모품 슬롯: {game.consumable_slot_count()}/{game.max_consumable_slots}"
    )
    joker_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(j)}" for i, j in enumerate(game.jokers))
        if game.jokers
        else "(없음)"
    )
    print(f"보유 조커 (판매 대상 번호): {joker_str}")
    _rule()
    if not game.shop_offers:
        print("(더 이상 살 수 있는 상품이 없습니다)")
    else:
        for group in _OFFER_GROUP_ORDER:
            indices = [i for i, item in enumerate(game.shop_offers) if _offer_group(item) == group]
            if not indices:
                continue
            print(f"{DIM}— {_OFFER_GROUP_LABELS[group]} —{RESET}")
            for i in indices:
                print(_offer_line(i, game.shop_offers[i], game))
    _rule()
    if game.shop_message:
        print(f"{MAGENTA}{game.shop_message}{RESET}")
    print(
        f"{DIM}b 1 (구매) | r (리롤, ${game.reroll_cost}) | x 1 (조커 판매) | c (다음 블라인드로) | "
        f"j (보유 정보) | save (저장 후 종료) | h (도움말) | q (그만두기){RESET}"
    )


def render_pack(game):
    pack = game.pending_pack
    _fake_terminal_header()
    _rule()
    pack_type_label = "조커" if pack["pack_type"] == "joker" else "소모품"
    print(f"{pack_type_label} 중 {pack['remaining']}개를 선택하세요.")
    print()
    for i, item in enumerate(pack["items"]):
        kind_tag = _offer_kind_tag(item)
        print(f" {i + 1}: {BOLD}{item.name}{RESET} [{kind_tag}] — {item.description}")
    _rule()
    if game.shop_message:
        print(f"{MAGENTA}{game.shop_message}{RESET}")
    print(f"{DIM}pick 1 (선택) | skip (남은 선택 포기) | h (도움말) | q (그만두기){RESET}")


def blind_clear_line(game):
    blind = game.blinds[game.blind_index]
    return f"{blind.label} 클리어! 보상 +${game.last_reward}"


def render_inventory(game):
    deck = deck_by_key(game.deck_key)
    stake = stake_by_level(game.stake_level)
    print(f"{BOLD}덱{RESET}: {deck.name} — {deck.description}")
    print(f"{BOLD}스테이크{RESET}: {stake.name} — {stake.description}")
    print()
    print(f"{BOLD}보유 조커 ({game.joker_slot_count()}/{game.max_joker_slots} 슬롯 사용){RESET}")
    if not game.jokers:
        print("(없음)")
    for i, j in enumerate(game.jokers):
        rarity_color = RARITY_COLOR.get(j.rarity, WHITE)
        print(
            f" {i + 1}: {BOLD}{_edition_marked_name(j)}{RESET} [{rarity_color}{RARITY_LABEL.get(j.rarity, j.rarity)}{RESET}]: "
            f"{j.description} ({YELLOW}${j.cost}{RESET})"
        )
    print()
    print(f"{BOLD}보유 소모품 ({game.consumable_slot_count()}/{game.max_consumable_slots} 슬롯 사용){RESET}")
    if not game.consumables:
        print("(없음)")
    for i, c in enumerate(game.consumables):
        print(f" {i + 1}: {BOLD}{_edition_marked_name(c)}{RESET}: {c.description}")
    print()
    leveled = {ht: lv for ht, lv in game.hand_levels.items() if lv > 0}
    print(f"{BOLD}족보 강화 레벨{RESET}")
    if not leveled:
        print("(없음)")
    for ht, lv in leveled.items():
        print(f" - {ht.label}: Lv.{lv}")
    print()
    print(f"{BOLD}보유 바우처{RESET}")
    from .vouchers import VOUCHER_POOL

    owned = [v for v in VOUCHER_POOL if v.key in game.owned_vouchers]
    if not owned:
        print("(없음)")
    for v in owned:
        print(f" - {BOLD}{v.name}{RESET}: {v.description}")
    print()


def render_help(phase):
    print(f"{BOLD}도움말{RESET}")
    print(f"{DIM}(발라트로를 몰라도 괜찮습니다 — 기본 개념부터 정리했습니다){RESET}")
    print(" · 카드 1~5장으로 포커 족보(페어, 플러시 등)를 만들면 '칩 × 배수'만큼 점수를 얻습니다.")
    print(" · '블라인드'는 이번 판에서 넘어야 할 목표 점수, '앤티'는 게임 진행 단계(1~8, 오를수록 어려워짐)입니다.")
    print(" · '조커'는 계속 켜져 있는 패시브 능력, '소모품'(부적/룬/강화석 등)은 원할 때 한 번 사용하는 아이템입니다.")
    print(" · 목표 점수를 넘기면 상금을 받고 상점에 들러 조커/소모품을 산 뒤 다음 블라인드로 넘어갑니다.")
    print()
    print("카드/상품 번호는 화면에 표시된 1부터 시작하는 인덱스입니다.")
    if phase == "blind":
        print(" p <번호...>  선택한 1~5장을 플레이해 점수를 냅니다 (예: p 1 3 5)")
        print(" d <번호...>  선택한 카드를 버리고 새로 뽑습니다 (예: d 2 4)")
        print(" u <번호> [대상번호]  소모품을 사용합니다. 강화석/에디션석/인장석/'파괴' 스펙트럴은 대상이 필요합니다 (예: u 1 3)")
        print("              대상은 종류에 따라 다릅니다 — 카드: 손패 번호 / 조커·소모품용 에디션석: 화면에 표시된 보유 목록 번호")
        print(" skip         (스몰/빅 블라인드에서, 아직 아무 행동도 하지 않았을 때) 블라인드를 스킵하고 태그를 얻습니다")
        print(" s            손패 정렬 방식을 랭크/무늬로 전환합니다")
        print(" rank         족보표(하이 카드~스트레이트 플러시 기본 점수)를 확인합니다")
        print(" legend       카드 강화/에디션/씰 표시 범례(색/기호 의미)를 확인합니다")
        print(" save         현재 진행 상황을 저장하고 게임을 종료합니다 (다음 실행 시 이어하기)")
        print(" x <번호>     보유한 조커를 판매합니다 (화면의 조커 목록 번호 사용, 구매가의 절반 환불, 예: x 1)")
    elif phase == "shop":
        print(" b <번호>     상점에서 해당 번호의 상품을 구매합니다 (예: b 1)")
        print(" r            상점을 새로고침합니다 (같은 상점 방문 내에서 리롤할 때마다 비용이 오릅니다)")
        print(" c            다음 블라인드로 진행합니다")
        print(" save         현재 진행 상황을 저장하고 게임을 종료합니다 (다음 실행 시 이어하기)")
        print(" x <번호>     보유한 조커를 판매합니다 (구매가의 절반 환불, 예: x 1)")
    elif phase == "pack":
        print(" pick <번호>  개봉한 팩에서 해당 번호의 상품을 선택합니다")
        print(" skip         남은 선택을 포기하고 상점으로 돌아갑니다")
    print(" j            보유 조커/소모품/바우처/족보 강화 정보를 확인합니다")
    print(" h            이 도움말을 다시 봅니다")
    print(" q            게임을 종료합니다 (저장하지 않음)")
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
    render_inventory(game)
    print(f"최종 자금: ${game.money}")
    if game.seed is not None:
        print(f"시드: {game.seed}")
    print()
