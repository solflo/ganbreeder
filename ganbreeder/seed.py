from . import config, db, gan, store


def seed_if_empty():
    if db.count_images() > 0:
        return
    print(f"First run: generating {config.SEED_COUNT} starter images.")
    print("Loading the BigGAN model for the first time may take a few minutes...")
    ims, vectors, labels = gan.create_random_images(config.SEED_COUNT)
    store.store(ims, vectors, labels)
    print("Starter images ready.")
