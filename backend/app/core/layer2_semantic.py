"""Lapis 2 (semantik): bit payload dikodekan ke pilihan varian frasa pada naskah dinas.

Template ditulis sebagai teks dengan grup varian `{a|b}` (2 varian = 1 bit) atau
`{a|b|c|d}` (4 varian = 2 bit). Baris yang diawali `#` adalah komentar. Pemilik naskah
(PM/ahli Jukminu) dapat menambah atau mengganti grup tanpa mengubah kode.

Dekoder TIDAK menyejajarkan posisi: tiap varian harus unik di seluruh naskah, sehingga
cukup dicari kemunculannya pada teks ketikan (fuzzy ringan untuk typo). Potongan sebagian,
urutan berubah, dan perubahan huruf/spasi/tanda baca tetap terbaca; slot yang tidak ditemukan
menjadi erasure bagi Reed-Solomon.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
from itertools import product
from pathlib import Path

from rapidfuzz import fuzz, process

from app.core.payload import DATA_BYTES, DEFAULT_NSYM

FRAME_BITS = (DATA_BYTES + DEFAULT_NSYM) * 8
_GROUP = re.compile(r"\{([^{}]*)\}")
_TOKEN = re.compile(r"\[\[([^\[\]]*)\]\]")  # honey-token Lapis 3: '#' = digit acak per salinan
MIN_TOKEN_DIGITS = 5  # cukup acak agar bocoran rekaan tak kebetulan sama dengan token terbit
MIN_FUZZY_LEN = 6  # varian lebih pendek dari ini harus cocok persis (fuzzy tak andal)
FUZZY_MIN_SCORE = 88.0


class TemplateError(ValueError):
    """Template tidak valid (jumlah varian, atau varian tidak unik)."""


def normalize(text: str) -> str:
    """Huruf kecil, hanya huruf/angka, spasi tunggal: tahan perubahan huruf, spasi, tanda baca."""
    return " ".join(re.sub(r"[^0-9a-z]+", " ", text.lower()).split())


@dataclass(frozen=True)
class Slot:
    index: int
    variants: tuple[str, ...]

    @property
    def bits(self) -> int:
        return len(self.variants).bit_length() - 1


@dataclass(frozen=True)
class HoneyToken:
    """Angka fiktif yang berbeda per salinan (Lapis 3). `pattern`: '#' diganti digit acak, karakter
    lain tetap (mis. '1##.###' -> '143.275'). Semua digit pada font naskah selebar sama, jadi
    tata letak tak berubah antar-salinan."""

    index: int
    pattern: str

    @property
    def placeholder(self) -> str:
        return self.pattern.replace("#", "0")


@dataclass(frozen=True)
class Template:
    parts: tuple[str | Slot | HoneyToken, ...]

    @property
    def slots(self) -> list[Slot]:
        return [p for p in self.parts if isinstance(p, Slot)]

    @property
    def tokens(self) -> list[HoneyToken]:
        return [p for p in self.parts if isinstance(p, HoneyToken)]

    @property
    def capacity_bits(self) -> int:
        return sum(s.bits for s in self.slots)


def _split_tokens(text: str, first_index: int) -> list[str | HoneyToken]:
    out: list[str | HoneyToken] = []
    pos = 0
    for match in _TOKEN.finditer(text):
        pattern = match.group(1)
        if pattern.count("#") < MIN_TOKEN_DIGITS or not re.fullmatch(r"[#0-9.,:/\-]+", pattern):
            raise TemplateError(
                f"token '{match.group(0)}': minimal {MIN_TOKEN_DIGITS} '#', hanya digit/tanda baca"
            )
        out += [text[pos : match.start()], HoneyToken(first_index + len(out) // 2, pattern)]
        pos = match.end()
    return out + [text[pos:]]


def parse_template(source: str) -> Template:
    """Urai teks template, lalu validasi keunikan varian."""
    text = "\n".join(ln for ln in source.splitlines() if not ln.lstrip().startswith("#"))
    parts: list[str | Slot | HoneyToken] = []
    n_slots = n_tokens = 0
    pos = 0

    def add_text(chunk: str) -> None:
        nonlocal n_tokens
        pieces = _split_tokens(chunk, n_tokens)
        n_tokens += sum(isinstance(p, HoneyToken) for p in pieces)
        parts.extend(pieces)

    for match in _GROUP.finditer(text):
        add_text(text[pos : match.start()])
        variants = tuple(v.strip() for v in match.group(1).split("|"))
        if len(variants) not in (2, 4) or not all(variants):
            raise TemplateError(f"grup '{match.group(0)}': jumlah varian harus 2 atau 4")
        parts.append(Slot(n_slots, variants))
        n_slots += 1
        pos = match.end()
    add_text(text[pos:])
    template = Template(tuple(parts))
    _validate_unique(template)
    return template


CONFUSABLE_SCORE = 86.0  # varian tak boleh semirip ini dengan kata lain mana pun di naskah


def _validate_unique(template: Template) -> None:
    """Tiap varian harus berupa satu kata yang unik dan tak mirip kata lain di naskah: tidak
    muncul di teks tetap atau varian lain, dan tak mudah tertukar saat dicocokkan fuzzy."""
    fixed_tokens = set(" ".join(normalize(p) for p in template.parts if isinstance(p, str)).split())
    owner: dict[str, int] = {}
    for slot in template.slots:
        for variant in slot.variants:
            norm = normalize(variant)
            if len(norm.split()) != 1:
                raise TemplateError(f"slot {slot.index}: '{variant}' harus satu kata")
            if norm in fixed_tokens:
                raise TemplateError(f"slot {slot.index}: '{variant}' muncul pada teks tetap")
            if norm in owner:
                raise TemplateError(
                    f"'{variant}' dipakai ganda (slot {owner[norm]} dan {slot.index})"
                )
            owner[norm] = slot.index
    for word, index in owner.items():
        if len(word) < MIN_FUZZY_LEN:
            continue
        for other in fixed_tokens | owner.keys():
            if other != word and fuzz.ratio(word, other) >= CONFUSABLE_SCORE:
                raise TemplateError(
                    f"slot {index}: '{word}' terlalu mirip '{other}' (rawan tertukar saat fuzzy)"
                )


def load_template(path: str | Path) -> Template:
    return parse_template(Path(path).read_text(encoding="utf-8"))


@lru_cache(maxsize=2)
def demo_template() -> Template:
    from app.config import settings

    return load_template(Path(settings.data_dir) / "master_templates" / "naskah_demo.txt")


def _frame_bit(frame: bytes, n: int) -> int:
    k = n % (len(frame) * 8)
    return (frame[k // 8] >> (7 - k % 8)) & 1


def variant_indices(template: Template, frame: bytes) -> tuple[int, ...]:
    """Varian terpilih tiap slot menurut bit frame (diulang bila slot > bit frame)."""
    out: list[int] = []
    n = 0
    for slot in template.slots:
        index = 0
        for j in range(slot.bits):
            index = (index << 1) | _frame_bit(frame, n + j)
        n += slot.bits
        out.append(index)
    return tuple(out)


def slot_bit_offsets(template: Template) -> tuple[int, ...]:
    """Posisi bit pertama tiap slot pada urutan bit naskah."""
    out, n = [], 0
    for slot in template.slots:
        out.append(n)
        n += slot.bits
    return tuple(out)


def variant_scores(template: Template, chosen: dict[int, int]) -> dict[int, float]:
    """Skor bit (+1/-1) dari varian yang teramati, {indeks slot: indeks varian}."""
    offsets = slot_bit_offsets(template)
    scores: dict[int, float] = {}
    for slot_index, variant in chosen.items():
        bits = template.slots[slot_index].bits
        for j in range(bits):
            bit = (variant >> (bits - 1 - j)) & 1
            scores[offsets[slot_index] + j] = 1.0 if bit else -1.0
    return scores


def encode_text(
    template: Template, frame: bytes, tokens: tuple[str, ...] | None = None
) -> str:
    """Render naskah dengan varian terpilih menurut bit frame. `tokens`: nilai honey-token
    salinan (Lapis 3), urut indeks token; None = angka nol (naskah tanpa registri)."""
    chosen = iter(variant_indices(template, frame))

    def render(p: str | Slot | HoneyToken) -> str:
        if isinstance(p, str):
            return p
        if isinstance(p, HoneyToken):
            return tokens[p.index] if tokens else p.placeholder
        return p.variants[next(chosen)]

    return "".join(render(p) for p in template.parts)


def _match_score(variant: str, vocab: set[str]) -> float:
    """Skor 0-100 kemunculan satu kata `variant` pada kosakata teks (fuzzy ringan bila panjang)."""
    if variant in vocab:
        return 100.0
    if len(variant) < MIN_FUZZY_LEN:
        return 0.0
    best = process.extractOne(variant, vocab, scorer=fuzz.ratio)
    return float(best[1]) if best else 0.0


MIN_SIMILARITY_WORDS = 6  # teks lebih pendek dari ini tak dinilai kemiripannya


@lru_cache(maxsize=4)
def _official_bigrams(template: Template) -> frozenset[tuple[str, str]]:
    """Semua pasangan kata berurutan yang mungkin muncul di naskah resmi (varian mana pun)."""
    alts: list[list[str]] = []
    for p in template.parts:
        if isinstance(p, str):
            alts += [[w] for w in normalize(p).split() if not w.isdigit()]
        elif isinstance(p, Slot):
            alts.append([normalize(v) for v in p.variants])
    return frozenset(b for a, c in zip(alts, alts[1:], strict=False) for b in product(a, c))


def official_similarity(template: Template, text: str) -> float | None:
    """Porsi pasangan kata berurutan di teks bukti yang juga ada di naskah resmi (pilihan varian
    apa pun; angka diabaikan). Tinggi (~0,7-1) = teks disalin/diketik ulang dari naskah resmi,
    walau penanda identitasnya tak cukup; rendah = bukan salinan naskah resmi (parafrase berat
    atau dokumen rekaan). Mengukur asal teks, bukan siapa pembocornya. None bila terlalu pendek."""
    words = [w for w in normalize(text).split() if not w.isdigit()]
    if len(words) < MIN_SIMILARITY_WORDS:
        return None
    pairs = list(zip(words, words[1:], strict=False))
    official = _official_bigrams(template)
    return sum(p in official for p in pairs) / len(pairs)


def extract_scores(template: Template, text: str) -> dict[int, float]:
    """Skor bit (+1 / -1) per posisi slot untuk slot yang varian-nya teridentifikasi tegas.

    Slot tanpa varian yang cocok, atau dengan lebih dari satu varian yang cocok sama baik,
    dilewati (erasure)."""
    vocab = set(normalize(text).split())
    chosen: dict[int, int] = {}
    for slot in template.slots:
        values = [_match_score(normalize(v), vocab) for v in slot.variants]
        best = max(range(len(values)), key=values.__getitem__)
        rivals = [v for i, v in enumerate(values) if i != best]
        if values[best] >= FUZZY_MIN_SCORE and max(rivals) < FUZZY_MIN_SCORE:
            chosen[slot.index] = best
    return variant_scores(template, chosen)
