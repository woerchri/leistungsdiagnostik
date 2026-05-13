from __future__ import annotations

import argparse
import json
import logging
import pickle
import sys
from dataclasses import asdict, replace
from pathlib import Path

from dotenv import load_dotenv

from ld import io_input, plots, protocols, redact, report, versioning
from ld.errors import LDError
from ld.types import AnalysisResult, Paths


logger = logging.getLogger("ld")


def main(argv: list[str] | None = None) -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(prog="ld.run")
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("output"))
    parser.add_argument("--exclude", type=int, action="append", default=[])
    parser.add_argument("--interpret", action="store_true")
    parser.add_argument("--context", type=str, default="",
                        help="Kontext für die LLM-Interpretation")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s: %(message)s",
    )

    try:
        paths = _resolve_paths(args.input_file, args.output_dir)
        result = _run_pipeline(paths, exclude_steps=args.exclude)
        if args.interpret:
            from ld import interpret, patch_interpretation
            interpret.run(result, paths, user_context=args.context)
            patch_interpretation.run(paths)
            print(f"Endbericht: {paths.final_docx}")
        else:
            print(f"Entwurf:    {paths.draft_docx}")
            print(f"JSON:       {paths.json_full}")
            print("Mit --interpret aufrufen für eine erste Interpretation.")
        _print_check_summary(result)
        return 0
    except LDError as e:
        print(f"Fehler: {e}", file=sys.stderr)
        return 2
    except Exception:
        logger.exception("Unerwarteter Fehler")
        return 1


def _resolve_paths(input_file: Path, output_dir: Path) -> Paths:
    from ld.errors import LDInputError
    if not input_file.exists():
        raise LDInputError(f"Eingabedatei existiert nicht: {input_file}")
    basename = input_file.stem
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


def _run_pipeline(paths: Paths, exclude_steps: list[int]) -> AnalysisResult:
    test_run = io_input.parse_input(paths.input_xlsx)
    if exclude_steps:
        kept = tuple(s for s in test_run.steps if s.stufe not in exclude_steps)
        test_run = replace(test_run, steps=kept)

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
