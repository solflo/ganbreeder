# Ganbreeder

> [Ganbreeder](https://ganbreeder.app) is a collaborative art tool for discovering images. Images are 'bred' by having children, mixing with other images and being shared via their URL. This is an experiment in using breeding + sharing as methods of exploring high complexity spaces. GANs are simply the engine enabling this. Ganbreeder is very similar to, and named after, Picbreeder. It is also inspired by an earlier project of Joel Simon's, [Facebook Graffiti](http://www.joelsimon.net/facebook-graffiti.html), which demonstrated the creative capacity of crowds.

This fork rebuilds Ganbreeder as a self-contained desktop app. The BigGAN models are bundled in.

## Running the app

Download the `Ganbreeder` folder, unzip it, and double-click `Ganbreeder.exe`. A console window will open and your browser pops up at the app. The first launch takes a few minutes while it loads a model and generates some starter images; later launches are quick. Close the console window to quit.

Your images and history are stored next to the exe in a `data/` folder.

## Under the hood

- **Python + Flask** served by waitress.
- **PyTorch BigGAN-deep** at 256x256, CPU-only, weights bundled for offline use.
- **SQLite** for storage (`data/ganbreeder.db`) and plain JPEGs in `data/img/`.
- Vanilla-JS frontend with Jinja2 templates.

## Developing / building from source

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
uv sync

uv run python scripts/fetch_weights.py

uv run python -m ganbreeder

uv run pyinstaller ganbreeder.spec --noconfirm
```

Original tool by Joel Simon ([joelsimon.net](https://www.joelsimon.net) · [@_joelsimon](https://twitter.com/_joelsimon)). 2026 fork and rework by [sol](https://solflo.neocities.org/) and their friend.
