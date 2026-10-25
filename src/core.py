"""Compositor / window-management library for SigmaOS-window-management-library
(inspired by muffin and hyprland titlebars).

Principles: declarative rules (what) vs compositor (how), pure matching and
workspace assignment (testable without a display server), fail-fast on bad
regex/config, first-match-wins with deterministic ordering.
"""
import argparse, json, os, re, subprocess, sys, tempfile

ENGINE = {
    "name": "sigma-wm",
    "summary": "Window rules, decorations and workspace planning",
    "language": "python",
    "verbs": ["rules", "decorations", "workspaces", "apply-plan"],
    "principles": ["Declarative Configuration", "Separation of Concerns",
                   "Defensive Programming", "Fail-Fast", "KISS", "Deterministic Testing"],
}

cli_doc = """\
$ sigma-wm rules --add --class Firefox --workspace 2
$ sigma-wm rules --list
$ sigma-wm decorations --buttons menu:minimize:close --border 6
$ sigma-wm workspaces --window "class=Firefox,title=.*Mozilla"
$ sigma-wm apply-plan --window "class=Firefox,title=.*Mozilla"   # prints plan (dry-run)
"""

DEFAULT_STORE = os.path.expanduser("~/.config/sigma-wm/wm.json")
BUTTONS = ("menu", "minimize", "maximize", "close", "shade", "stick", "above")
DECOR_DEFAULTS = {"buttons": ["menu", "minimize", "maximize", "close"],
                  "border": 4, "theme": "Mint-Y"}


class WmError(ValueError):
    pass


def validate_rule(rule):
    """Normalise + validate one rule. Pure. Raises WmError (fail-fast)."""
    m = rule.get("match") or {}
    if not m.get("class") and not m.get("title"):
        raise WmError("rule needs a class and/or title match")
    if m.get("title") is not None:
        try:
            re.compile(m["title"])
        except re.error as e:
            raise WmError(f"bad title regex: {e}") from e
    a = rule.get("action") or {}
    ws = a.get("workspace", 1)
    if not isinstance(ws, int) or isinstance(ws, bool) or not 1 <= ws <= 32:
        raise WmError(f"workspace must be 1..32, got {ws!r}")
    return {"match": {"class": m.get("class"), "title": m.get("title")},
            "action": {"workspace": ws, "floating": bool(a.get("floating", False)),
                       "decorate": bool(a.get("decorate", True))}}


def load_config(path):
    if not os.path.exists(path):
        return {"rules": [], "decorations": dict(DECOR_DEFAULTS)}
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {"rules": [validate_rule(r) for r in data.get("rules", [])],  # fail-fast
            "decorations": validate_decorations(data.get("decorations", {}))}


def save_config(path, cfg):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".sigma-tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2)
    os.replace(tmp, path)


def add_rule(rules, match_class=None, match_title=None, workspace=1,
             floating=False, decorate=True):
    rule = validate_rule({"match": {"class": match_class, "title": match_title},
                          "action": {"workspace": workspace, "floating": floating,
                                     "decorate": decorate}})
    rules.append(rule)
    return rules


def match_rule(rule, window):
    """Does this rule apply to the window? Pure."""
    m = rule["match"]
    if m["class"] is not None and m["class"] != window.get("class"):
        return False
    if m["title"] is not None and not re.search(m["title"], window.get("title", "")):
        return False
    return True


def assign_windows(rules, windows):
    """First matching rule wins; default workspace 1. Pure & deterministic."""
    out = []
    for w in windows:
        ws = 1
        for rule in rules:
            if match_rule(rule, w):
                ws = rule["action"]["workspace"]
                break
        out.append({"class": w.get("class", ""), "title": w.get("title", ""),
                    "workspace": ws})
    return out


def validate_decorations(cfg):
    """Normalise decoration config (buttons string or list, border, theme)."""
    out = dict(DECOR_DEFAULTS)
    out.update(cfg or {})
    buttons = out["buttons"]
    if isinstance(buttons, str):
        buttons = [b for b in buttons.split(":") if b]
    if not buttons or any(b not in BUTTONS for b in buttons):
        raise WmError(f"bad buttons: {buttons} (have: {':'.join(BUTTONS)})")
    if len(set(buttons)) != len(buttons):
        raise WmError(f"duplicate buttons: {buttons}")
    try:
        border = int(out["border"])
    except (TypeError, ValueError):
        raise WmError(f"bad border: {out['border']!r}")
    if not 0 <= border <= 20:
        raise WmError(f"border must be 0..20, got {border}")
    return {"buttons": buttons, "border": border, "theme": str(out["theme"])}


def render_plan(assignments, decorations):
    """Pure renderer: assignments + decoration config -> plan lines."""
    lines = []
    for a in assignments:
        lines.append(f"wm rule workspace={a['workspace']} class={a['class']!r} "
                     f"title={a['title']!r}")
    lines.append("wm decoration buttons=" + ":".join(decorations["buttons"]) +
                 f" border={decorations['border']} theme={decorations['theme']}")
    return lines


def apply_plan(plan, runner=None):
    """Execute layer: feed plan lines to the live compositor.

    self_test NEVER calls this without an injected (recording) runner.
    """
    if runner is None:
        runner = lambda line: subprocess.run(["sigma-wm-apply", "-c", line], check=True)
    for line in plan:
        runner(line)
    return len(plan)


def parse_window(spec):
    """Parse 'class=X,title=Y' into a window dict. Pure."""
    win = {}
    for part in spec.split(","):
        if "=" not in part:
            raise WmError(f"bad window spec part: {part!r}")
        k, v = part.split("=", 1)
        k = k.strip()
        if k not in ("class", "title"):
            raise WmError(f"unknown window field: {k!r}")
        win[k] = v.strip()
    if not win:
        raise WmError(f"empty window spec: {spec!r}")
    return win


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog=ENGINE["name"], description=ENGINE["summary"])
    p.add_argument("--store", default=DEFAULT_STORE, help="config store (JSON)")
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rules", help="list or add window rules")
    r.add_argument("--list", action="store_true", help="list rules (default)")
    r.add_argument("--add", action="store_true", help="add a rule")
    r.add_argument("--class", dest="cls", default=None)
    r.add_argument("--title", default=None, help="title regex")
    r.add_argument("--workspace", type=int, default=1)
    r.add_argument("--floating", action="store_true")
    r.add_argument("--no-decorate", action="store_true")
    d = sub.add_parser("decorations", help="get/set decoration config")
    d.add_argument("--buttons", default=None, help="colon-separated button layout")
    d.add_argument("--border", type=int, default=None)
    d.add_argument("--theme", default=None)
    w = sub.add_parser("workspaces", help="assign windows to workspaces (pure)")
    w.add_argument("--window", action="append", required=True,
                   help="window spec class=X,title=Y (repeatable)")
    ap = sub.add_parser("apply-plan", help="render the full plan (dry-run by default)")
    ap.add_argument("--window", action="append", default=[],
                    help="window spec class=X,title=Y (repeatable)")
    ap.add_argument("--execute", action="store_true",
                    help="actually apply (requires a live session)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = load_config(args.store)
        if args.cmd == "rules":
            if args.add:
                add_rule(cfg["rules"], match_class=args.cls, match_title=args.title,
                         workspace=args.workspace, floating=args.floating,
                         decorate=not args.no_decorate)
                save_config(args.store, cfg)
                print(f"rules: {len(cfg['rules'])}")
            else:
                for i, rule in enumerate(cfg["rules"]):
                    a = rule["action"]
                    print(f"{i}: match={rule['match']} -> workspace={a['workspace']} "
                          f"floating={a['floating']} decorate={a['decorate']}")
        elif args.cmd == "decorations":
            patch = {}
            if args.buttons is not None:
                patch["buttons"] = args.buttons
            if args.border is not None:
                patch["border"] = args.border
            if args.theme is not None:
                patch["theme"] = args.theme
            cfg["decorations"] = validate_decorations({**cfg["decorations"], **patch})
            if patch:
                save_config(args.store, cfg)
            dec = cfg["decorations"]
            print(f"buttons={':'.join(dec['buttons'])} border={dec['border']} "
                  f"theme={dec['theme']}")
        elif args.cmd == "workspaces":
            windows = [parse_window(s) for s in args.window]
            for a in assign_windows(cfg["rules"], windows):
                print(f"{a['class']!r} {a['title']!r} -> workspace {a['workspace']}")
        elif args.cmd == "apply-plan":
            windows = [parse_window(s) for s in args.window]
            assignments = assign_windows(cfg["rules"], windows)
            plan = render_plan(assignments, cfg["decorations"])
            if args.execute:
                n = apply_plan(plan)
                print(f"applied {n} command(s)", file=sys.stderr)
            else:
                for line in plan:
                    print(line)
        return 0
    except (WmError, OSError, ValueError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 1


def self_test() -> None:
    rules = []
    add_rule(rules, match_class="Firefox", workspace=2)
    add_rule(rules, match_title=r"^Picture-in-Picture$", workspace=3, floating=True)
    add_rule(rules, match_class="Pavucontrol", workspace=4, decorate=False)
    # matching (pure)
    assert match_rule(rules[0], {"class": "Firefox", "title": "Mozilla Firefox"})
    assert not match_rule(rules[0], {"class": "Nautilus", "title": "Mozilla"})
    assert match_rule(rules[1], {"class": "firefox", "title": "Picture-in-Picture"})
    # assignment: first match wins, deterministic, default 1
    wins = [{"class": "Firefox", "title": "Mozilla Firefox"},
            {"class": "Nautilus", "title": "Home"},
            {"class": "firefox", "title": "Picture-in-Picture"},
            {"class": "XTerm", "title": "shell"}]
    got = assign_windows(rules, wins)
    assert [a["workspace"] for a in got] == [2, 1, 3, 1]
    # decoration validation (fail-fast)
    dec = validate_decorations({"buttons": "menu:minimize:close", "border": 6})
    assert dec["buttons"] == ["menu", "minimize", "close"]
    for bad in ({"buttons": "menu:nope"}, {"buttons": "close:close"}, {"border": 99}):
        try:
            validate_decorations(bad)
        except WmError:
            pass
        else:
            raise AssertionError(f"should reject decorations {bad}")
    # plan rendering is pure & deterministic; execute uses an injected sink
    plan = render_plan(got, dec)
    assert plan[0] == "wm rule workspace=2 class='Firefox' title='Mozilla Firefox'"
    assert plan[-1].startswith("wm decoration buttons=menu:minimize:close border=6")
    seen = []
    assert apply_plan(plan, runner=seen.append) == len(plan)
    assert seen == plan
    # persistence round-trip (tempdir only)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "wm.json")
        save_config(path, {"rules": rules, "decorations": dec})
        again = load_config(path)
        assert assign_windows(again["rules"], wins) == got
        assert again["decorations"] == dec
        assert load_config(os.path.join(d, "none.json"))["rules"] == []
    # bad input (fail-fast)
    for bad_rule in ({}, {"match": {"title": "("}},
                     {"match": {"class": "X"}, "action": {"workspace": 0}},
                     {"match": {"class": "X"}, "action": {"workspace": True}}):
        try:
            validate_rule(bad_rule)
        except WmError:
            pass
        else:
            raise AssertionError(f"should reject rule {bad_rule}")
    assert parse_window("class=Firefox,title=Hello World")["title"] == "Hello World"
    try:
        parse_window("colour=red")
    except WmError:
        pass
    else:
        raise AssertionError("bad window field not caught")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
