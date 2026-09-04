from .game import GameState
from . import ui


class InputError(Exception):
    pass


def _parse_indices(tokens, hand_len, max_count=5):
    if not tokens:
        raise InputError("카드 번호를 하나 이상 입력하세요.")
    try:
        nums = [int(t) for t in tokens]
    except ValueError:
        raise InputError("카드 번호는 숫자로 입력하세요.")
    if len(set(nums)) != len(nums):
        raise InputError("같은 카드를 두 번 선택할 수 없습니다.")
    if not (1 <= len(nums) <= max_count):
        raise InputError(f"카드는 1~{max_count}장만 선택할 수 있습니다.")
    for n in nums:
        if not (1 <= n <= hand_len):
            raise InputError(f"{n}번 카드는 존재하지 않습니다.")
    return sorted(n - 1 for n in nums)


def _parse_single_index(args, label="번호"):
    if not args:
        raise InputError(f"{label}를 입력하세요.")
    try:
        return int(args[0]) - 1
    except ValueError:
        raise InputError(f"{label}는 숫자로 입력하세요.")


def _pause():
    input(f"{ui.DIM}(엔터를 눌러 계속){ui.RESET}")


def _handle_blind_command(game, cmd, args):
    if cmd in ("p", "play"):
        indices = _parse_indices(args, len(game.hand))
        game.play_cards(indices)
    elif cmd in ("d", "discard"):
        if game.discards_left <= 0:
            raise InputError("버리기 횟수를 모두 사용했습니다.")
        indices = _parse_indices(args, len(game.hand))
        game.discard_cards(indices)
    elif cmd in ("u", "use"):
        n = _parse_single_index(args, "소모품 번호")
        card_index = None
        if len(args) > 1:
            try:
                card_index = int(args[1]) - 1
            except ValueError:
                raise InputError("카드 번호는 숫자로 입력하세요.")
        message = game.use_consumable(n, card_index)
        print(message)
        _pause()
    elif cmd == "skip":
        message = game.skip_blind()
        print(message)
        _pause()
    elif cmd in ("x", "sell"):
        n = _parse_single_index(args, "조커 번호")
        message = game.sell_joker(n)
        print(message)
        _pause()
    elif cmd in ("s", "sort"):
        game.sort_hand("suit" if game.sort_mode == "rank" else "rank")
    elif cmd in ("j", "jokers", "inventory"):
        ui.render_inventory(game)
        _pause()
    elif cmd in ("h", "help"):
        ui.render_help("blind")
        _pause()
    elif cmd in ("q", "quit"):
        raise SystemExit
    else:
        raise InputError("알 수 없는 명령어입니다. h를 입력해 도움말을 확인하세요.")


def _handle_shop_command(game, cmd, args):
    if cmd in ("b", "buy"):
        n = _parse_single_index(args, "구매할 상품 번호")
        game.buy_offer(n)
    elif cmd in ("r", "reroll"):
        game.reroll_shop()
    elif cmd in ("x", "sell"):
        n = _parse_single_index(args, "조커 번호")
        game.shop_message = game.sell_joker(n)
    elif cmd in ("c", "continue"):
        game.continue_from_shop()
    elif cmd in ("j", "jokers", "inventory"):
        ui.render_inventory(game)
        _pause()
    elif cmd in ("h", "help"):
        ui.render_help("shop")
        _pause()
    elif cmd in ("q", "quit"):
        raise SystemExit
    else:
        raise InputError("알 수 없는 명령어입니다. h를 입력해 도움말을 확인하세요.")


def _run_loop(game):
    error = None
    while not game.is_run_over():
        ui.clear_screen()
        if game.phase == "blind":
            ui.render_status(game)
            ui.render_hand_prompt(game)
        elif game.phase == "shop":
            ui.render_shop(game)

        if error:
            print(f"{ui.RED}{error}{ui.RESET}")
        error = None

        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not raw:
            continue
        parts = raw.split()
        cmd, args = parts[0].lower(), parts[1:]

        try:
            if game.phase == "blind":
                _handle_blind_command(game, cmd, args)
            elif game.phase == "shop":
                _handle_shop_command(game, cmd, args)
        except InputError as e:
            error = str(e)
        except SystemExit:
            return

    ui.clear_screen()
    ui.render_end_screen(game)


def _prompt_seed():
    try:
        raw = input("새 게임을 시작하려면 엔터, 시드를 정해서 시작하려면 시드 문자열, 종료하려면 q: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        return "quit"
    if raw.lower() == "q":
        return "quit"
    return raw or None


def main():
    ui.render_title()
    seed = _prompt_seed()
    if seed == "quit":
        return
    game = GameState(seed=seed)
    _run_loop(game)


if __name__ == "__main__":
    main()
