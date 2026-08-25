"""Query catalogue.json from the command line.

Examples:
  python tools/catalogue_query.py --stats
  python tools/catalogue_query.py --kind effect --status confirmed_working
  python tools/catalogue_query.py --kind gui_function --type Location --min-usability 90
  python tools/catalogue_query.py --search variable_map
  python tools/catalogue_query.py --kind define --block NAI --undocumented
  python tools/catalogue_query.py --kind effect --scope location
"""
import argparse
import json
import pathlib

CAT = pathlib.Path(r"T:\eu5-engine-atlas\catalogue.json")


def item_types(it):
    return {t["type"] for t in it.get("gui", {}).get("types", [])}


def item_scopes(it):
    sc = it.get("scope", {})
    out = set()
    if "required" in sc:
        out.add(sc["required"])
    out.update(sc.get("ok_in", []))
    out.update(s for s, _ in sc.get("observed", []))
    if "hint" in sc:
        out.add(sc["hint"])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind")
    ap.add_argument("--status")
    ap.add_argument("--type", dest="gui_type",
                    help="GUI datacontext type, e.g. Location")
    ap.add_argument("--scope", help="effect/trigger scope, e.g. country")
    ap.add_argument("--block", help="define block, e.g. NAI")
    ap.add_argument("--family", help="curated family substring")
    ap.add_argument("--search", help="substring over name/desc/notes/syntax")
    ap.add_argument("--undocumented", action="store_true")
    ap.add_argument("--min-usability", type=int, default=0)
    ap.add_argument("--stats", action="store_true")
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--json", action="store_true",
                    help="print full item JSON instead of one-line rows")
    args = ap.parse_args()

    cat = json.loads(CAT.read_text(encoding="utf-8"))
    items = cat["items"]

    if args.stats:
        print(json.dumps(cat["meta"]["counts"], indent=1, sort_keys=True))
        print("total:", cat["meta"]["items_total"],
              "built:", cat["meta"]["built"])
        return

    hits = []
    q = args.search.lower() if args.search else None
    for iid, it in items.items():
        if args.kind and it["kind"] != args.kind:
            continue
        if args.status and it["status"] != args.status:
            continue
        if args.undocumented and not it.get("undocumented"):
            continue
        if it["usability"] < args.min_usability:
            continue
        if args.gui_type and args.gui_type not in item_types(it):
            continue
        if args.scope and args.scope not in item_scopes(it):
            continue
        if args.block and it.get("define", {}).get("block") != args.block:
            continue
        if args.family and args.family.lower() not in it.get(
                "family", "").lower():
            continue
        if q:
            hay = " ".join([it["name"], it.get("syntax", ""),
                            it.get("family", ""),
                            " ".join(it.get("notes", [])),
                            " ".join(t.get("desc", "")
                                     for t in it.get("gui", {}).get(
                                         "types", []))]).lower()
            if q not in hay:
                continue
        hits.append((iid, it))

    hits.sort(key=lambda p: (-p[1]["usability"], p[0]))
    for iid, it in hits[:args.limit]:
        if args.json:
            print(json.dumps({iid: it}, indent=1))
            continue
        extra = ""
        if it["kind"] == "gui_function":
            ts = sorted(item_types(it))
            if ts:
                extra = " [" + ",".join(ts[:4]) + ("..." if len(ts) > 4
                                                   else "") + "]"
        elif it["kind"] == "define":
            v = it["define"].get("vanilla_value")
            extra = f" = {v}" if v is not None else ""
            if "tier_label" in it["define"]:
                extra += f"  ({it['define']['tier_label']})"
        elif "scope" in it:
            sc = it["scope"]
            extra = f"  scope:{sc.get('required') or sc.get('ok_in') or sc.get('hint') or '(observed)'}"
        print(f"{it['usability']:3}  {it['status']:18} {iid}{extra}")
    print(f"-- {len(hits)} matches" +
          (f", showing {args.limit}" if len(hits) > args.limit else ""))


if __name__ == "__main__":
    main()
