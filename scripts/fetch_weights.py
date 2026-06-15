"""Download the BigGAN-deep 256 weights into ./weights.

The weights are too large to keep in git, so run this once after cloning
(and before building the executable) to populate them locally.
"""
import pathlib

import requests
import pytorch_pretrained_biggan.model as m

from ganbreeder import config

DST = pathlib.Path(__file__).resolve().parent.parent / "weights"


def fetch():
    name = config.MODEL_NAME
    folder = DST / name
    folder.mkdir(parents=True, exist_ok=True)
    for url, fname in [
        (m.PRETRAINED_CONFIG_ARCHIVE_MAP[name], "config.json"),
        (m.PRETRAINED_MODEL_ARCHIVE_MAP[name], "pytorch_model.bin"),
    ]:
        out = folder / fname
        if out.exists() and out.stat().st_size > 0:
            print("have", out)
            continue
        print("downloading", url)
        r = requests.get(url, stream=True, timeout=120)
        r.raise_for_status()
        with open(out, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
        print("  ->", out, out.stat().st_size, "bytes")


if __name__ == "__main__":
    fetch()
    print("weights ready")
