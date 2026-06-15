import secrets

import PIL.Image

from . import config, db


def save_image(arr, key):
    PIL.Image.fromarray(arr).save(config.IMG_DIR / f"{key}.jpeg", format="JPEG", quality=90)


def store(ims, vectors, labels, parent1=None, parent2=None):
    rows = []
    for i in range(len(ims)):
        key = secrets.token_hex(12)
        save_image(ims[i], key)
        rows.append({
            "key": key,
            "vector": vectors[i].tolist(),
            "label": labels[i].tolist(),
            "parent1": parent1,
            "parent2": parent2,
        })
    db.insert_images(rows)
    return [r["key"] for r in rows]
