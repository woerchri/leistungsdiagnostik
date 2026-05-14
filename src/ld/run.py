from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from dataclasses import asdict, replace
from pathlib import Path

from ld import io_input, plots, protocols, redact, report, versioning
from ld.errors import LDError
from ld.types import AnalysisResult, Paths


logger = logging.getLogger("ld")


def main(argv: list[str] | None = None) -> int:
    """Deterministic pipeline only — Codex drafts the interpretation in the
    /ld-report slash command and patches it in via `ld.patch_interpretation`.

    The earlier `--interpret` flag (OpenAI API direct) was removed 2026-05-14:
    the tool no longer makes any LLM calls itself; Anna's ChatGPT/Codex account
    handles all non-deterministic prose.
    """
    parser = argparse.ArgumentParser(prog="ld.run")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--exclude", type=int, action="append", default=[])
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        # Parse first so we can derive the output basename from the data
        # (Anna 2026-05-13: XY_LD_Sportart_JJ_MM_TT, computed from athlete +
        # testdatum — input filename is no longer the source of truth).
        if not args.input_file.exists():
            raise LDError(f"Eingabedatei existiert nicht: {args.input_file}")
        test_run = io_input.parse_input(args.input_file)
        if args.exclude:
            kept = tuple(s for s in test_run.steps if s.stufe not in args.exclude)
            test_run = replace(test_run, steps=kept)

        normalized_basename = _normalize_basename(test_run)
        input_basename = args.input_file.stem
        if normalized_basename != input_basename:
            # Warn but don't force input rename — Anna's recommendation 2026-05-13.
            print(
                f"Hinweis: Eingabedateiname '{input_basename}' folgt nicht der "
                f"Konvention. Ausgabe wird als '{normalized_basename}' gespeichert."
            )

        paths = _resolve_paths(args.input_file, args.output_dir, normalized_basename)
        result = _run_pipeline(paths, test_run)
        print(f"Entwurf:    {paths.draft_docx}")
        print(f"JSON:       {paths.json_full}")
        print(f"Für LLM:    {paths.json_for_llm}")
        print()
        print("Nächster Schritt: /ld-report im Codex liest die JSON und")
        print("erzeugt die Interpretation. Codex patcht sie via")
        print("`uv run python -m ld.patch_interpretation` in den Bericht.")
        _print_check_summary(result)
        return 0
    except LDError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    except Exception:
        logger.exception("Unerwarteter Fehler")
        return 1


def _normalize_basename(test_run) -> str:
    """Build the canonical output basename per Anna 2026-05-13 convention:
        XY_LD_<Sportart>_JJ_MM_TT
    where X = Vorname[0], Y = Name[0], date format is JJ_MM_TT.
    Sportart label is title-cased ("Lauf", "Rad", "Triathlon-Rad", "Unspezifisch").
    """
    athlete = test_run.athlete
    proto = test_run.testprotokoll
    x = (athlete.vorname[:1] or "X").upper()
    y = (athlete.name[:1] or "X").upper()
    sport_part = {
        "lauf": "Lauf",
        "rad": "Rad",
        "triathlon-lauf": "Triathlon-Lauf",
        "triathlon-rad": "Triathlon-Rad",
        "unspezifisch": "Unspezifisch",
    }.get(athlete.sportart, athlete.sportart.title())
    d = proto.testdatum
    date_part = f"{d.year % 100:02d}_{d.month:02d}_{d.day:02d}"
    return f"{x}{y}_LD_{sport_part}_{date_part}"


def _resolve_paths(input_file: Path, output_dir: Path, basename: str) -> Paths:
    return Paths(
        input_xlsx=input_file,
        output_dir=output_dir,
        basename=basename,
        json_full=output_dir / f"{basename}.json",
        json_for_llm=output_dir / f"{basename}_for_llm.json",
        draft_docx=versioning.next_version_path(output_dir, basename, "draft"),
        final_docx=versioning.next_version_path(output_dir, basename, "final"),
        plots_dir=output_dir / basename,
        pickle_path=output_dir / f"{basename}.pkl",
    )


def _run_pipeline(paths: Paths, test_run) -> AnalysisResult:
    result = protocols.analyze(test_run)
    plot_path = plots.render_main_diagram(result, paths.plots_dir)

    paths.json_full.parent.mkdir(parents=True, exist_ok=True)
    paths.json_full.write_text(
        json.dumps(_to_jsonable(result), indent=2, default=str, ensure_ascii=False)
    )
    paths.pickle_path.write_bytes(pickle.dumps(result))
    redact.write_redacted(result, paths.json_for_llm)
    report.render(result, plot_path, paths.draft_docx, interpretation=None)
    return result


def _to_jsonable(result: AnalysisResult) -> dict:
    return asdict(result)


def _print_check_summary(result: AnalysisResult) -> None:
    failed = [p for p in result.pflichtpruefungen if not p.ok]
    if not failed:
        print("Pflichtprüfungen: alle OK.")
        return
    print("Pflichtprüfungen — Hinweise:")
    for p in failed:
        print(f"  • {p.message_de}")


if __name__ == "__main__":
    sys.exit(main())
