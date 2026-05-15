from __future__ import annotations

import argparse
import sys
from pathlib import Path

PYTHON_ROOT = Path(__file__).resolve().parents[1]
if str(PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(PYTHON_ROOT))

from core.config import DEFAULT_IMAGE_PATH
from services.image_description import describir_imagen


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Describe una imagen de ropa y devuelve JSON.")
    parser.add_argument("image", nargs="?", default=str(DEFAULT_IMAGE_PATH), help="Ruta de la imagen")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    datos = describir_imagen(args.image)
    print(datos.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
