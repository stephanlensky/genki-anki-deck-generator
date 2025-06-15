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
