"""Clean a synthetic CRM export using the same pipeline as the local API."""

import argparse
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from unificado import UnifiedCRMPipeline


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Write the cleaned CSV to a new file")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "leads.csv"
        source.write_text(
            "cpf,nome,email,data_cadastro\n"
            "00123456789,Example One,old@example.com,2024-01-01\n"
            "00123456789,Example One,new@example.com,2024-02-01\n"
            "00987654321,Example Two,two@example.com,2024-01-15\n",
            encoding="utf-8",
        )
        pipeline = UnifiedCRMPipeline(str(root / "models"), enable_api_calls=False)
        result = pipeline.run_etl(str(source))
        print(f"Input: 3 rows; output: {len(result)} leads")
        print(result[["cpf", "email", "data_quality_score"]].to_csv(index=False), end="")
        if args.output:
            with args.output.open("x", encoding="utf-8", newline="") as output:
                result.to_csv(output, index=False)
            print(f"Saved: {args.output}")


if __name__ == "__main__":
    main()
