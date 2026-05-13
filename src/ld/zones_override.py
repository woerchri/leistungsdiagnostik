from __future__ import annotations

import pickle
from dataclasses import replace
from pathlib import Path

from ld.types import AnalysisResult, TrainingZone


def apply(basename_path: str, overrides: dict[str, float]) -> None:
    """Apply zone boundary overrides and re-save the pickle.

    basename_path = 'output/<basename>' (no extension).
    overrides keys: 'Z2_upper', 'Z3_upper', 'Z4_upper', 'Z5_upper'.
    Each sets the upper bound of the named zone and the lower of the next.
    """
    base = Path(basename_path)
    pkl_path = Path(f"{base}.pkl")
    result: AnalysisResult = pickle.loads(pkl_path.read_bytes())

    new_zones = list(result.zones_final)
    name_to_idx = {z.name: i for i, z in enumerate(new_zones)}

    for key, value in overrides.items():
        zone_name = key.split("_")[0]
        idx = name_to_idx.get(zone_name)
        if idx is None:
            continue
        new_zones[idx] = replace(new_zones[idx], intensitaet_max=value)
        if idx + 1 < len(new_zones):
            new_zones[idx + 1] = replace(new_zones[idx + 1], intensitaet_min=value)

    result = replace(result, zones_final=tuple(new_zones))
    pkl_path.write_bytes(pickle.dumps(result))

    # Re-render draft to reflect new zones
    from ld import plots, report, versioning
    plot_path = plots.render_main_diagram(result, base)
    draft = versioning.next_version_path(base.parent, base.name, "draft")
    report.render(result, plot_path, draft)
    print(f"Zonen aktualisiert. Neuer Entwurf: {draft}")


def main(argv: list[str] | None = None) -> int:
    """CLI: uv run python -m ld.zones_cli output/<basename> Z3_upper=9.0 Z4_upper=10.5"""
    import argparse
    import sys
    parser = argparse.ArgumentParser(prog="ld.zones_cli")
    parser.add_argument("basename", help="e.g. output/Athlet_2026-05-13 (no extension)")
    parser.add_argument("overrides", nargs="*",
                        help="ZONE_upper=VALUE pairs, e.g. Z3_upper=9.0")
    args = parser.parse_args(argv)

    overrides: dict[str, float] = {}
    for item in args.overrides:
        try:
            k, v = item.split("=")
            overrides[k.strip()] = float(v.strip())
        except ValueError:
            print(f"Warnung: Ungültiges Argument ignoriert: '{item}'", file=sys.stderr)

    if not overrides:
        print("Keine Anpassungen übergeben.", file=sys.stderr)
        return 1

    apply(args.basename, overrides)
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
