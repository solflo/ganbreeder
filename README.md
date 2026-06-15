# Ganbreeder

> [Ganbreeder](https://ganbreeder.app) is a collaborative art tool for discovering images. Images are 'bred' by having children, mixing with other images and being shared via their URL. This is an experiment in using breeding + sharing as methods of exploring high complexity spaces. GANs are simply the engine enabling this. Ganbreeder is very similar to, and named after, Picbreeder. It is also inspired by an earlier project of Joel Simon's, [Facebook Graffiti](http://www.joelsimon.net/facebook-graffiti.html), which demonstrated the creative capacity of crowds.

This fork rebuilds Ganbreeder as a self-contained desktop app. The BigGAN models are bundled in.

## Running the app

Download the `Ganbreeder` folder, unzip it, and double-click `Ganbreeder.exe`. A console window will open and your browser pops up at the app. The first launch takes a few minutes while it loads a model and generates some starter images; later launches are quick. Close the console window to quit.

Your images and history are stored next to the exe in a `data/` folder.

## Dependencies used

- **Python + Flask** served by waitress.
- **PyTorch BigGAN-deep** at 256x256, CPU-only, no cuda sorry, I'm not packing more 2gb into this.
    - This is the only dependency that might rot in the future, the packed app comes with the models already downloaded (this is why it's huge), but for development one day this might stop working.
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

The Windows `.exe` is produced by running that last command on Windows.

### Building the Linux package (if you are in windows)

Easiest is via Docker:

```bash
docker build -f Dockerfile.build --target artifact --output type=local,dest=dist-linux .
tar czf Ganbreeder-linux.tar.gz -C dist-linux Ganbreeder
```

This produces `dist-linux/Ganbreeder/Ganbreeder` plus `_internal/`. Users unzip it and run `./Ganbreeder/Ganbreeder` from a terminal. Running the same `uv` commands directly on a Linux machine or WSL2 works too.

Original tool by Joel Simon ([joelsimon.net](https://www.joelsimon.net) · [@_joelsimon](https://twitter.com/_joelsimon)). 2026 fork and rework by [sol](https://solflo.neocities.org/) and their friend.
