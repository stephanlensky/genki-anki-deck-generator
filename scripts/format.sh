#!/usr/bin/env bash

set -e
set -x

python_files=(genki_anki_deck_generator)

uv run ruff check "${python_files[@]}" --fix
uv run ruff format "${python_files[@]}"
