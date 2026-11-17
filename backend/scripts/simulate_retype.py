"""Simulasi ketik ulang Lapis 2: ketahanan dekoder terhadap potongan, typo, dan kata diganti.

Jalankan dari backend/:  python -m scripts.simulate_retype [--trials 200]
"""

import argparse
import random
import string
from pathlib import Path

from app.core.layer2_semantic import (
    Template,
    TemplateError,
    encode_text,
    extract_scores,
    load_template,
    normalize,
    parse_template,
)
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload


def synthetic_template(slots: int, seed: int = 3) -> Template:
    """Template sintetis (kata acak) hanya untuk mengukur dampak kapasitas pada ketahanan."""
    rng = random.Random(seed)
    letters = string.ascii_lowercase
    while True:
        words = ["".join(rng.choice(letters) for _ in range(8)) for _ in range(slots * 2)]
        lines = [
            f"baris{chr(97 + i % 26)}{i} {{{words[2 * i]}|{words[2 * i + 1]}}} tetap\n"
            for i in range(slots)
        ]
        try:
            return parse_template("".join(lines))
        except TemplateError:
            continue


TEMPLATE = Path(__file__).resolve().parents[2] / "data" / "master_templates" / "naskah_demo.txt"


def excerpt(words: list[str], fraction: float, rng: random.Random) -> list[str]:
    n = max(1, int(len(words) * fraction))
    start = rng.randint(0, len(words) - n)
    return words[start : start + n]


def add_typos(text: str, rate: float, rng: random.Random) -> str:
    out = []
    for ch in text:
        if ch.isalpha() and rng.random() < rate:
            kind = rng.choice("dsi")
            if kind == "s":
                out.append(rng.choice(string.ascii_lowercase))
            elif kind == "i":
                out.extend([ch, rng.choice(string.ascii_lowercase)])
            continue  # 'd' = hapus
        out.append(ch)
    return "".join(out)


def replace_words(words: list[str], rate: float, pool: list[str], rng: random.Random) -> list[str]:
    return [rng.choice(pool) if rng.random() < rate else w for w in words]


def swap_synonyms(words: list[str], rate: float, template: Template, rng: random.Random):
    siblings = {}
    for slot in template.slots:
        for v in slot.variants:
            siblings[normalize(v)] = [normalize(o) for o in slot.variants if o != v]
    swapped = []
    for w in words:
        sibs = siblings.get(normalize(w))
        swapped.append(rng.choice(sibs) if sibs and rng.random() < rate else w)
    return swapped


def trial(template: Template, fraction, typo, subst, syn, rng) -> str:
    copy_id = rng.getrandbits(32)
    words = encode_text(template, encode_payload(copy_id)).split()
    pool = [w for w in words if len(w) > 3]
    words = excerpt(words, fraction, rng)
    words = swap_synonyms(words, syn, template, rng)
    words = replace_words(words, subst, pool, rng)
    text = add_typos(" ".join(words), typo, rng)
    try:
        decoded = decode_scores(extract_scores(template, text))[0]
    except PayloadDecodeError:
        return "tolak"
    return "benar" if decoded == copy_id else "SALAH"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=200)
    ap.add_argument("--synthetic-slots", type=int, help="pakai template sintetis N slot 1-bit")
    a = ap.parse_args()
    template = (
        synthetic_template(a.synthetic_slots) if a.synthetic_slots else load_template(TEMPLATE)
    )
    print(f"slot {len(template.slots)}, kapasitas {template.capacity_bits} bit, "
          f"{a.trials} percobaan per sel; sel = benar/salah (sisanya ditolak)")
    conditions = [
        ("bersih", 0, 0, 0), ("typo 2%", 0.02, 0, 0), ("typo 5%", 0.05, 0, 0),
        ("kata diganti 10%", 0, 0.10, 0), ("kata diganti 20%", 0, 0.20, 0),
        ("sinonim tertukar 5%", 0, 0, 0.05), ("sinonim tertukar 10%", 0, 0, 0.10),
    ]
    print(f"{'potongan':>9} | " + " | ".join(f"{c[0]:>20}" for c in conditions))
    for fraction in (1.0, 0.8, 0.6, 0.5, 0.4, 0.3):
        cells = []
        for _, typo, subst, syn in conditions:
            rng = random.Random(int(fraction * 100) + 1)
            res = [trial(template, fraction, typo, subst, syn, rng) for _ in range(a.trials)]
            cells.append(f"{res.count('benar') / a.trials:>11.0%} / {res.count('SALAH'):>3}")
        print(f"{fraction:>9.0%} | " + " | ".join(f"{c:>20}" for c in cells))
