# genki-anki-deck-generator

> Forked from [mi-ael/genki-anki-deck-generator](https://github.com/mi-ael/genki_anki_deck_generator) with added fixes from [zmjohnso/genki_anki_deck_generator](https://github.com/zmjohnso/genki_anki_deck_generator). All credit to original authors.

A collection of Python tools for Anki deck generation from Genki audio files and vocabulary lists.

## Usage

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/).
2. Clone the repository:

   ```bash
   git clone https://github.com/stephanlensky genki-anki-deck-generator.git
   ```

3. Generate Anki decks:

   ```bash
   uv run genki-anki-deck-generator
   ```

Resulting Anki decks will be written to `genki.apkg`.

### Advanced usage

The `uv run genki-anki-deck-generator` command above is equivalent to running the following commands in sequence:

1. `uv run genki-anki-deck-generator download`
2. `uv run genki-anki-deck-generator process-audio`
3. `uv run genki-anki-deck-generator generate`

Running these commands separately allows you to customize the behavior of each step. For more information, try running any of the above commands with the `--help` flag, e.g.:

```bash
uv run genki-anki-deck-generator process-audio --help
```
