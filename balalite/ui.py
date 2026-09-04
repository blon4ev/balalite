import random
import time

from .blinds import BIG_WAVE_FLAVOR, MAX_ANTE, SMALL_WAVE_FLAVOR
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
    - 코팅이 있으면 카드 전체가 반전(reverse video)되어 "빛나는" 것처럼 보인다.
    - 각인이 있으면 카드 앞에 색점(●)이 붙는다.
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
        f"{ENHANCEMENT_TAG_COLOR['bonus']}노랑{RESET}{DIM}=보너스+30데미지 "
        f"{ENHANCEMENT_TAG_COLOR['mult']}자홍{RESET}{DIM}=멀티+4배율 "
        f"{ENHANCEMENT_TAG_COLOR['wild']}청록{RESET}{DIM}=와일드무늬 "
        f"{ENHANCEMENT_TAG_COLOR['glass']}파랑{RESET}{DIM}=유리x2(파괴위험){RESET}"
    )
    print(
        f"{DIM}코팅(카드 전체가 반전되어 빛남): "
        f"{EDITION_TAG_COLOR['foil']}초록빛{RESET}{DIM}=포일+50데미지 "
        f"{EDITION_TAG_COLOR['holographic']}자홍빛{RESET}{DIM}=홀로+10배율 "
        f"{EDITION_TAG_COLOR['polychrome']}노랑빛{RESET}{DIM}=폴리x1.5   "
        f"각인(카드 앞 점): "
        f"{SEAL_DOT_COLOR['red']}●{RESET}{DIM}적(재발동) "
        f"{SEAL_DOT_COLOR['gold']}●{RESET}{DIM}금(+$3) "
        f"{SEAL_DOT_COLOR['blue']}●{RESET}{DIM}청(보급품){RESET}"
    )


def render_hand_guide(game):
    print(f"{BOLD}{CYAN}=== 콤보표 (약한 순 → 강한 순) ==={RESET}")
    for ht in HandType:
        level = game.hand_levels.get(ht, 0)
        line = f" {BOLD}{ht.label}{RESET} — 기본 {ht.base_chips}데미지 × {ht.base_mult}배"
        if level > 0:
            level_chips, level_mult = LEVEL_BONUS.get(ht, (0, 0))
            cur_chips = ht.base_chips + level * level_chips
            cur_mult = ht.base_mult + level * level_mult
            line += f"  {GREEN}(Lv.{level} 교범 적용 → {cur_chips}데미지 × {cur_mult}배){RESET}"
        print(line)
    print()
    print(f"{DIM}데미지 = (기본 데미지 + 카드 자체 값 + 강화/코팅/유물 보너스) × (기본 배율 + 보너스){RESET}")
    print(f"{DIM}예: 페어(K,K) = 기본 10데미지 + 10+10(카드값) = 30데미지, 기본 2배 → 30 × 2 = 60 데미지{RESET}")
    print()


def _hp_bar(remaining, total):
    """목표 데미지에서 남은 양을 몬스터 체력바처럼 표시한다 — 공격할수록 줄어든다."""
    ratio = max(0.0, min(1.0, remaining / total)) if total else 0.0
    filled = int(ratio * BAR_WIDTH)
    bar = "█" * filled + "░" * (BAR_WIDTH - filled)
    if ratio <= 0:
        color = DIM
    elif ratio < 0.3:
        color = RED
    else:
        color = GREEN
    return f"{color}[{bar}]{RESET}"


def _wave_flavor(game):
    blind = game.current_blind
    idx = (game.ante - 1) % len(SMALL_WAVE_FLAVOR)
    if blind.kind == "small":
        return f"{blind.label} · {SMALL_WAVE_FLAVOR[idx]}"
    if blind.kind == "big":
        return f"{blind.label} · {BIG_WAVE_FLAVOR[idx]}"
    return blind.label  # 보스는 label에 이미 몬스터 이름이 포함됨


def render_status(game):
    blind = game.current_blind
    remaining = max(0, blind.requirement - game.round_score)
    ratio_done = game.round_score / blind.requirement if blind.requirement else 1.0
    _fake_terminal_header(ratio_done)
    _rule()
    print(f"STAGE {game.ante}/{MAX_ANTE}  {BOLD}{_wave_flavor(game)}{RESET}")
    if game.boss_effect:
        print(f"{RED}보스 특성: {game.boss_effect.description}{RESET}")
    bar = _hp_bar(remaining, blind.requirement)
    print(f"몬스터 체력: {remaining} / {blind.requirement}  {bar}")
    print(f"공격 {game.plays_left}회 남음 | 재정비 {game.discards_left}회 남음 | {GREEN}${game.money}{RESET}")
    joker_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(j)}" for i, j in enumerate(game.jokers))
        if game.jokers
        else "(없음)"
    )
    print(f"유물 ({game.joker_slot_count()}/{game.max_joker_slots}): {joker_str}")
    consumable_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(c)}" for i, c in enumerate(game.consumables))
        if game.consumables
        else "(없음)"
    )
    print(f"보급품 ({game.consumable_slot_count()}/{game.max_consumable_slots}): {consumable_str}")
    if game.last_result:
        hand_type, chips, mult, gained, destroyed = game.last_result
        print(
            f"{MAGENTA}{BOLD}▶ {hand_type.label} 콤보 적중!{RESET}{MAGENTA}   {int(chips)}데미지 × {mult:g}배 = "
            f"{RESET}{GREEN}{BOLD}{gained} 데미지{RESET}"
        )
        if remaining > 0:
            print(f"{DIM}   (몬스터 남은 체력: {remaining}){RESET}")
        else:
            print(f"{GREEN}{BOLD}   몬스터 처치! 곧 전리품을 정리합니다.{RESET}")
        if destroyed:
            names = ", ".join(str(c) for c in destroyed)
            print(f"{BLUE}   파손된 카드: {names}{RESET}")
    if game.last_tag_message:
        print(f"{CYAN}{game.last_tag_message}{RESET}")
    _rule()


def render_hand_prompt(game):
    print()
    render_hand(game.hand)
    print()
    hints = ["p 1 2 3 (공격)", "d 1 2 (재정비)", "u 1 [카드번호] (보급품 사용)", "x 1 (유물 판매)"]
    if game.can_skip_blind():
        hints.append("skip (웨이브 회피)")
    hints += [
        "s (정렬)",
        "rank (콤보표)",
        "j (보유 정보)",
        "legend (표시 범례)",
        "save (저장 후 종료)",
        "h (도움말)",
        "q (그만두기)",
    ]
    print(f"{DIM}" + " | ".join(hints) + f"{RESET}")


OFFER_KIND_LABELS = {
    "rune": "교범",
    "enhancer": "강화 키트",
    "editioner": "코팅제",
    "sealer": "각인석",
    "spectral": "이능 물질",
    "charm": "부적",
}


def _offer_kind_tag(item):
    if hasattr(item, "timing"):
        rarity_color = RARITY_COLOR.get(item.rarity, WHITE)
        return f"유물·{rarity_color}{RARITY_LABEL.get(item.rarity, item.rarity)}{RESET}"
    kind = getattr(item, "kind", None)
    if kind == "voucher":
        return "훈련 프로그램"
    if kind == "pack":
        return "보급 상자"
    return OFFER_KIND_LABELS.get(kind, kind)


def _offer_line(i, item, game):
    kind_tag = _offer_kind_tag(item)
    cost = game._discounted_cost(item.cost)
    cost_str = f"{YELLOW}${cost}{RESET}"
    if cost != item.cost:
        cost_str = f"{DIM}${item.cost}{RESET} → {cost_str}"
    return f" {i + 1}: {BOLD}{item.name}{RESET} [{kind_tag}] — {item.description}  ({cost_str})"


# 보급소를 "카드(유물·보급품) / 보급 상자 / 훈련 프로그램" 세 영역으로 시각적으로
# 구분해서 보여준다. 구매·판매에 쓰는 번호는 game.shop_offers의 전체 인덱스를
# 그대로 유지한다 (영역은 표시용일 뿐).
_OFFER_GROUP_ORDER = ["card", "pack", "voucher"]
_OFFER_GROUP_LABELS = {
    "card": "카드 (유물 · 보급품)",
    "pack": "보급 상자",
    "voucher": "훈련 프로그램",
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
        f"보유 자금: {GREEN}${game.money}{RESET}   유물 슬롯: {game.joker_slot_count()}/{game.max_joker_slots}   "
        f"보급품 슬롯: {game.consumable_slot_count()}/{game.max_consumable_slots}"
    )
    joker_str = (
        ", ".join(f"{DIM}{i + 1}:{RESET}{_edition_marked_name(j)}" for i, j in enumerate(game.jokers))
        if game.jokers
        else "(없음)"
    )
    print(f"보유 유물 (판매 대상 번호): {joker_str}")
    _rule()
    if not game.shop_offers:
        print("(더 이상 살 수 있는 물자가 없습니다)")
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
        f"{DIM}b 1 (구매) | r (리롤, ${game.reroll_cost}) | x 1 (유물 판매) | c (다음 웨이브로) | "
        f"j (보유 정보) | save (저장 후 종료) | h (도움말) | q (그만두기){RESET}"
    )


_PACK_TYPE_LABELS = {"joker": "유물", "consumable": "보급품", "card": "카드"}


def render_pack(game):
    pack = game.pending_pack
    _fake_terminal_header()
    _rule()
    pack_type_label = _PACK_TYPE_LABELS.get(pack["pack_type"], pack["pack_type"])
    print(f"상자 안에서 {pack_type_label} {pack['remaining']}개를 골라 챙기세요.")
    print()
    if pack["pack_type"] == "card":
        for i, card in enumerate(pack["items"]):
            print(f" {i + 1}: {colorize_card(card)}")
    else:
        for i, item in enumerate(pack["items"]):
            kind_tag = _offer_kind_tag(item)
            print(f" {i + 1}: {BOLD}{item.name}{RESET} [{kind_tag}] — {item.description}")
    _rule()
    if game.shop_message:
        print(f"{MAGENTA}{game.shop_message}{RESET}")
    print(f"{DIM}pick 1 (선택) | skip (남은 선택 포기) | h (도움말) | q (그만두기){RESET}")


def blind_clear_line(game):
    blind = game.blinds[game.blind_index]
    if blind.kind == "boss":
        return f"☠ 보스 처치! {blind.label} — 전리품 +${game.last_reward} ☠"
    return f"{blind.label} 처치! 전리품 +${game.last_reward}"


def render_inventory(game):
    deck = deck_by_key(game.deck_key)
    stake = stake_by_level(game.stake_level)
    print(f"{BOLD}생존자{RESET}: {deck.name} — {deck.description}")
    print(f"{BOLD}위협도{RESET}: {stake.name} — {stake.description}")
    print()
    print(f"{BOLD}보유 유물 ({game.joker_slot_count()}/{game.max_joker_slots} 슬롯 사용){RESET}")
    if not game.jokers:
        print("(없음)")
    for i, j in enumerate(game.jokers):
        rarity_color = RARITY_COLOR.get(j.rarity, WHITE)
        print(
            f" {i + 1}: {BOLD}{_edition_marked_name(j)}{RESET} [{rarity_color}{RARITY_LABEL.get(j.rarity, j.rarity)}{RESET}]: "
            f"{j.description} ({YELLOW}${j.cost}{RESET})"
        )
    print()
    print(f"{BOLD}보유 보급품 ({game.consumable_slot_count()}/{game.max_consumable_slots} 슬롯 사용){RESET}")
    if not game.consumables:
        print("(없음)")
    for i, c in enumerate(game.consumables):
        print(f" {i + 1}: {BOLD}{_edition_marked_name(c)}{RESET}: {c.description}")
    print()
    leveled = {ht: lv for ht, lv in game.hand_levels.items() if lv > 0}
    print(f"{BOLD}콤보 숙련도{RESET}")
    if not leveled:
        print("(없음)")
    for ht, lv in leveled.items():
        print(f" - {ht.label}: Lv.{lv}")
    print()
    print(f"{BOLD}보유 훈련 프로그램{RESET}")
    from .vouchers import VOUCHER_POOL

    owned = [v for v in VOUCHER_POOL if v.key in game.owned_vouchers]
    if not owned:
        print("(없음)")
    for v in owned:
        print(f" - {BOLD}{v.name}{RESET}: {v.description}")
    print()


def render_help(phase):
    print(f"{BOLD}도움말{RESET}")
    print(" · 카드 1~5장으로 콤보(페어, 플러시 등)를 만들면 '데미지 × 배율'만큼 몬스터에게 피해를 입힙니다.")
    print(" · '웨이브'는 이번에 처치해야 할 몬스터 무리, '스테이지'는 게임 진행 단계(1~8, 오를수록 어려워짐)입니다.")
    print(" · '유물'은 계속 켜져 있는 패시브 효과, '보급품'(부적/교범/강화 키트 등)은 원할 때 한 번 쓰는 소모성 아이템입니다.")
    print(" · 목표 데미지를 넘기면 몬스터를 처치하고 전리품을 받아 보급소에서 유물/보급품을 산 뒤 다음 웨이브로 넘어갑니다.")
    print(" · 보스 웨이브를 처치하면 보급소에 유물이 최소 1개 확정으로 진열됩니다.")
    print()
    print("카드/상품 번호는 화면에 표시된 1부터 시작하는 인덱스입니다.")
    if phase == "blind":
        print(" p <번호...>  선택한 1~5장으로 공격해 데미지를 입힙니다 (예: p 1 3 5)")
        print(" d <번호...>  선택한 카드를 버리고 재정비합니다 (예: d 2 4)")
        print(" u <번호> [대상번호]  보급품을 사용합니다. 강화 키트/코팅제/각인석/'파괴' 이능 물질은 대상이 필요합니다 (예: u 1 3)")
        print("              대상은 종류에 따라 다릅니다 — 카드: 카드 패 번호 / 유물·보급품용 코팅제: 화면에 표시된 보유 목록 번호")
        print(" skip         (아직 아무 행동도 하지 않은 1·2차 웨이브에서) 웨이브를 회피하고 포상을 얻습니다")
        print(" s            카드 패 정렬 방식을 랭크/무늬로 전환합니다")
        print(" rank         콤보표(하이 카드~플러시 파이브까지 기본 데미지)를 확인합니다")
        print(" legend       카드 강화/코팅/각인 표시 범례(색/기호 의미)를 확인합니다")
        print(" save         현재 진행 상황을 저장하고 게임을 종료합니다 (다음 실행 시 이어하기)")
        print(" x <번호>     보유한 유물을 판매합니다 (화면의 유물 목록 번호 사용, 구매가의 절반 환불, 예: x 1)")
    elif phase == "shop":
        print(" b <번호>     보급소에서 해당 번호의 물자를 구매합니다 (예: b 1)")
        print(" r            보급소 재고를 새로고침합니다 (같은 방문 내에서 리롤할 때마다 비용이 오릅니다)")
        print(" c            다음 웨이브로 진행합니다")
        print(" save         현재 진행 상황을 저장하고 게임을 종료합니다 (다음 실행 시 이어하기)")
        print(" x <번호>     보유한 유물을 판매합니다 (구매가의 절반 환불, 예: x 1)")
    elif phase == "pack":
        print(" pick <번호>  개봉한 상자에서 해당 번호의 물건을 챙깁니다")
        print(" skip         남은 선택을 포기하고 보급소로 돌아갑니다")
    print(" j            보유 유물/보급품/훈련 프로그램/콤보 숙련도 정보를 확인합니다")
    print(" h            이 도움말을 다시 봅니다")
    print(" q            게임을 종료합니다 (저장하지 않음)")
    print()


def render_title():
    clear_screen()
    print(f"{BOLD}{RED}")
    print("  ╔══════════════════════════════════════╗")
    print("  ║   L A S T   W A V E  —  라스트 웨이브   ║")
    print("  ╚══════════════════════════════════════╝")
    print(f"{RESET}")
    print(f"{DIM}해가 지면 놈들이 몰려온다. 살아남아라.{RESET}")
    print("카드 콤보로 몬스터 웨이브를 물리치는 생존 로그라이크 — 사무실 몰래 즐기는 인디 프로토타입")
    print()


def render_end_screen(game):
    print()
    if game.phase == "victory":
        print(f"{BOLD}{GREEN}🎉 축하합니다! {MAX_ANTE}개 스테이지를 모두 생존했습니다! 🎉{RESET}")
    else:
        blind = game.current_blind
        print(f"{BOLD}{RED}전멸 — STAGE {game.ante} {blind.label}에서 쓰러짐{RESET}")
        print(f"목표 데미지 {blind.requirement} 중 {game.round_score} 달성")
    print()
    render_inventory(game)
    print(f"최종 자금: ${game.money}")
    if game.seed is not None:
        print(f"시드: {game.seed}")
    print()
