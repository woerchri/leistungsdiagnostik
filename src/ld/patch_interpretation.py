from __future__ import annotations

import json
import pickle
from pathlib import Path

from ld import plots, report, versioning
from ld.errors import LDError
from ld.types import Paths


def run(paths: Paths) -> Path:
    interp_path = paths.output_dir / f"{paths.basename}_interpretation.json"
    if not interp_path.exists():
        raise LDError(f"Interpretation-JSON nicht gefunden: {interp_path}.")
    if not paths.pickle_path.exists():
        raise LDError(f"Analyse-Pickle nicht gefunden: {paths.pickle_path}.")

    interpretation = json.loads(interp_path.read_text())
    result = pickle.loads(paths.pickle_path.read_bytes())
    plot_path = paths.plots_dir / "diagramm.png"
    if not plot_path.exists():
        plot_path = plots.render_main_diagram(result, paths.plots_dir)
    return report.render(result, plot_path, paths.final_docx, interpretation=interpretation)


def main(argv: list[str] | None = None) -> int:
    import argparse
    import sys
    parser = argparse.ArgumentParser(prog="ld.patch_interpretation")
    parser.add_argument(
        "output_basename", type=Path,
        help="e.g. output/Athlet_2026-05-13  (no extension)"
    )
    args = parser.parse_args(argv)
    output_dir = args.output_basename.parent
    basename = args.output_basename.name
    paths = Paths(
        input_xlsx=Path("/dev/null"),
        output_dir=output_dir,
        basename=basename,
        json_full=output_dir / f"{basename}.json",
        json_for_llm=output_dir / f"{basename}_for_llm.json",
        draft_docx=Path("/dev/null"),
        final_docx=versioning.next_version_path(output_dir, basename, "final"),
        plots_dir=output_dir / basename,
        pickle_path=output_dir / f"{basename}.pkl",
    )
    final = run(paths)
    print(f"Endbericht: {final}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
