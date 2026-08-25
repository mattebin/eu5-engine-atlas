"""Build promote_graph.json - type-to-type reachability over the data API.

Nodes are datacontext types, edges are members that return another type
(promotes preferred, object-returning functions kept with a penalty).
For every type we compute the cheapest accessor chain from an entry point,
preferring roots the console probes PROVED reachable (VERIFIED.md).

This answers the receivers backlog statically: a function on type T is
obtainable through best_chain(T) + '.' + function. It also feeds task
relevance ("what can I reach from a Location").

Chains rooted in probe-proven receivers are marked proven_root: true.
Chains through other globals are real API but unproven from the console -
present them as leads, not facts.
"""
import argparse
import datetime
import heapq
import json
import pathlib

ROOT = pathlib.Path(r"T:\eu5-engine-atlas")
OUT = ROOT / "promote_graph.json"

# receivers proven reachable from the console (VERIFIED.md, typed passes)
PROVEN_ROOTS = {
    "GetPlayer": "Country",
    "GetPlayer.GetCapital": "Location",
    "GetPlayer.GetCapital.GetProvince": "Province",
    "GetPlayer.GetCapital.GetMarket": "Market",
    "GetPlayer.GetCapital.GetArea": "Area",
    "GetPlayer.GetCapital.GetRegion": "Region",
    "GetPlayer.GetCulture": "Culture",
    "GetPlayer.GetReligion": "Religion",
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sabotage", action="store_true",
                    help="drop GetPlayer; known-chain asserts MUST fail")
    args = ap.parse_args()

    dump = json.loads((ROOT / "data_types_dump.json").read_text("utf-8"))
    globals_, types = dump["globals"], dump["types"]
    if args.sabotage:
        del globals_["GetPlayer"]
    known = set(types) | set(dump["declared_types"])

    # edges[type] = list of (member, target, cost, kind, args)
    def edge_cost(entry):
        kind = entry.get("def_type", "")
        c = 1.0 if "romote" in kind else 1.5     # Promote / Global promote
        return c + 2.0 * entry.get("args", 0)

    edges = {}
    n_edges = 0
    for t, members in types.items():
        out = []
        for name, e in members.items():
            tgt = e.get("returns")
            if tgt in known:
                out.append((name, tgt, edge_cost(e),
                            e.get("def_type", ""), e.get("args", 0)))
                n_edges += 1
        edges[t] = out

    # entry points: proven receiver chains at cost 0, other globals at 1
    heap, best = [], {}
    for chain, t in PROVEN_ROOTS.items():
        if not args.sabotage or not chain.startswith("GetPlayer"):
            heapq.heappush(heap, (0.0, t, chain, True))
    for name, e in globals_.items():
        tgt = e.get("returns")
        if tgt in known:
            heapq.heappush(heap, (1.0 + 2.0 * e.get("args", 0),
                                  tgt, name, False))

    # Dijkstra over types
    while heap:
        cost, t, chain, proven = heapq.heappop(heap)
        if t in best and best[t][0] <= cost:
            continue
        best[t] = (cost, chain, proven)
        if chain.count(".") >= 6:                # depth guard
            continue
        for member, tgt, ec, kind, nargs in edges.get(t, []):
            nc = cost + ec
            if tgt not in best or best[tgt][0] > nc:
                heapq.heappush(heap, (nc, tgt, f"{chain}.{member}", proven))

    nodes = {}
    for t in sorted(known):
        n = {"members": len(types.get(t, {}))}
        if t in best:
            cost, chain, proven = best[t]
            n["best_chain"] = chain
            n["depth"] = chain.count(".") + 1
            n["proven_root"] = proven
        nodes[t] = n

    reachable = {t for t in nodes if "best_chain" in nodes[t]}

    # how much of the receivers backlog this settles: the tested-unreachable
    # GUI functions whose owner type now has a chain
    cat = json.loads((ROOT / "catalogue.json").read_text("utf-8"))["items"]
    backlog = [i for i in cat.values() if i["kind"] == "gui_function"
               and i.get("gui", {}).get("tested_unreachable")]
    covered = 0
    for i in backlog:
        owners = {tp["type"] for tp in i["gui"].get("types", [])
                  if tp["type"] != "(global)"}
        if owners & reachable:
            covered += 1

    out = {
        "meta": {
            "project": "eu5-engine-atlas promote graph",
            "built": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "builder": "tools/build_promote_graph.py",
            "source": "data_types_dump.json (current to 1.3.11)",
            "types": len(nodes),
            "edges": n_edges,
            "reachable_types": len(reachable),
            "backlog_functions_tested_unreachable": len(backlog),
            "backlog_functions_with_chain_now": covered,
            "note": ("proven_root chains start from console-verified "
                     "receivers; others are real API but unproven - "
                     "leads, not facts"),
        },
        "nodes": nodes,
        "edges": {t: [{"member": m, "to": tgt, "kind": k, "args": a}
                      for m, tgt, _c, k, a in sorted(es)]
                  for t, es in sorted(edges.items()) if es},
    }

    # asserts that CAN fail, anchored to probe-proven chains
    assert ("Country", "GetCapital") in {(t, e["member"])
                                         for t, es in out["edges"].items()
                                         for e in es for t in [t]}, \
        "Country.GetCapital edge missing"
    assert nodes["Location"].get("best_chain") == "GetPlayer.GetCapital", \
        nodes["Location"].get("best_chain")
    assert nodes["Market"].get("best_chain") == \
        "GetPlayer.GetCapital.GetMarket", nodes["Market"].get("best_chain")
    assert nodes["Building"].get("best_chain"), "Building unreachable"
    assert nodes["Character"].get("best_chain"), "Character unreachable"
    # measured 2026-08-26: the uncovered remainder lives on UI-view types
    # (SelectInteractionTargetView, LobbyView, editor windows) that the GUI
    # system instantiates as datacontexts - not navigable objects, so no
    # chain can exist for them. Pin exact to catch regressions.
    assert covered == 1193, f"backlog coverage changed: {covered} != 1193"

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"types: {len(nodes)}  edges: {n_edges}  "
          f"reachable: {len(reachable)}")
    print(f"receivers backlog: {covered} of {len(backlog)} tested-"
          f"unreachable functions now have an owner chain")
    for t in ("Building", "Character", "Unit", "War", "TradeNode",
              "Siege", "Combat"):
        n = nodes.get(t, {})
        print(f"  {t:10} -> {n.get('best_chain', 'UNREACHABLE')}"
              f"  (proven_root={n.get('proven_root')})")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
