"""Operasi basis data Lapis 4: isi data personel demo, ekspor bersisip honey-record, korpus data
publik, dan analisis dump bocoran."""

import csv
import io
import random
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core import layer4_honeyrecord as l4
from app.db.models import CorpusFingerprint, DataExport, HoneyRecord, Personnel, PublicCorpus

CSV_COLUMNS = ("nrp", "nama", "pangkat", "satuan", "nik", "no_hp", "tanggal_lahir")
_CHUNK = 900  # batas aman jumlah parameter IN per kueri


def _taken(session: Session) -> set[str]:
    out: set[str] = set()
    for model in (Personnel, HoneyRecord):
        for row in session.execute(select(model.nrp, model.nik, model.no_hp)):
            out.update(row)
    return out


def _fresh(rng: random.Random, taken: set[str], satuan: str | None = None) -> l4.Persona:
    """Persona yang NRP, NIK, dan nomor HP-nya belum dipakai siapa pun di basis data."""
    while True:
        p = l4.make_persona(rng, satuan)
        if not {p.nrp, p.nik, p.no_hp} & taken:
            taken.update((p.nrp, p.nik, p.no_hp))
            return p


def _fields(p: l4.Persona) -> dict:
    return {c: getattr(p, c) for c in CSV_COLUMNS}


def seed_personnel(session: Session, count: int = 400, seed: int | None = None) -> tuple[int, int]:
    """Isi tabel personel demo bila masih kosong: `count` persona plus honey-record tertanam
    (sekitar 1 per 50) yang disisipkan di antaranya. Mengembalikan (jumlah baris, honey-record)."""
    if session.scalar(select(func.count()).select_from(Personnel)):
        raise ValueError("tabel personel sudah berisi data")
    rng = random.Random(seed)
    taken = _taken(session)
    people = [_fresh(rng, taken) for _ in range(count)]
    sentinels = [_fresh(random.SystemRandom(), taken) for _ in range(l4.sentinel_count(count))]
    rows = people + sentinels
    rng.shuffle(rows)  # honey-record tak berada di ujung tabel / id berurutan
    session.add_all(Personnel(**_fields(p)) for p in rows)
    session.add_all(HoneyRecord(export_id=None, **_fields(p)) for p in sentinels)
    session.flush()
    return len(rows), len(sentinels)


def create_export(
    session: Session, username: str, satuan: str | None, purpose: str
) -> tuple[DataExport, str]:
    """Ekspor data personel ke CSV dengan honey-record khusus ekspor ini diselipkan acak."""
    query = select(Personnel).order_by(Personnel.satuan, Personnel.nama)
    if satuan:
        query = query.where(Personnel.satuan == satuan)
    people = list(session.scalars(query))
    if not people:
        raise ValueError("tidak ada data personel untuk diekspor")
    rng = random.SystemRandom()
    taken = _taken(session)
    sentinels = [_fresh(rng, taken, satuan) for _ in range(l4.sentinel_count(len(people)))]
    export = DataExport(
        username=username, satuan=satuan, purpose=purpose, row_count=len(people) + len(sentinels)
    )
    session.add(export)
    session.flush()
    session.add_all(HoneyRecord(export_id=export.id, **_fields(p)) for p in sentinels)

    rows = [{c: getattr(p, c) for c in CSV_COLUMNS} for p in people]
    for p in sentinels:  # diselipkan di posisi acak, bukan di akhir
        rows.insert(rng.randrange(len(rows) + 1), _fields(p))
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    session.flush()
    return export, buf.getvalue()


def register_corpus(session: Session, label: str, note: str, text: str) -> PublicCorpus:
    """Daftarkan data publik/bocoran lama: hanya hash NIK dan nomor HP yang disimpan."""
    ids = l4.extract_identifiers(text)
    fps = {l4.fingerprint(i) for i in ids.niks | ids.phones}
    if not fps:
        raise ValueError("tidak ada NIK atau nomor HP di berkas")
    corpus = PublicCorpus(label=label, note=note, entries=len(fps))
    session.add(corpus)
    session.flush()
    session.add_all(CorpusFingerprint(corpus_id=corpus.id, fp=fp) for fp in fps)
    session.flush()
    return corpus


def _chunks(values: Iterable[str]) -> Iterable[list[str]]:
    items = sorted(values)
    for i in range(0, len(items), _CHUNK):
        yield items[i : i + _CHUNK]


@dataclass(frozen=True)
class DumpAnalysis:
    status: str
    ids: l4.Identifiers
    hits: list[l4.RecordHit]
    proven: list[int | None]  # sumber terbukti: id ekspor, atau None = DB langsung
    personnel_ratio: float
    corpus_ratio: float
    corpus_label: str | None
    invalid_ratio: float


def analyse_dump(session: Session, text: str) -> DumpAnalysis:
    ids = l4.extract_identifiers(text)

    # honey-record: kolom mana saja yang cocok per baris
    matched: dict[int, set[str]] = defaultdict(set)
    sources: dict[int, int | None] = {}
    for column, values in (("nik", ids.niks), ("no_hp", ids.phones), ("nrp", ids.nrps)):
        for chunk in _chunks(values):
            attr = getattr(HoneyRecord, column)
            for rec_id, export_id in session.execute(
                select(HoneyRecord.id, HoneyRecord.export_id).where(attr.in_(chunk))
            ):
                matched[rec_id].add(column)
                sources[rec_id] = export_id
    hits = [l4.RecordHit(r, sources[r], tuple(sorted(f))) for r, f in sorted(matched.items())]
    by_source: dict[int | None, list[l4.RecordHit]] = defaultdict(list)
    for h in hits:
        by_source[h.source].append(h)
    proven = sorted(
        (s for s, hs in by_source.items() if l4.source_proven(hs)), key=lambda s: (s is None, s)
    )
    if any(s is not None for s in proven):
        # honey-record tertanam ikut terbawa di setiap ekspor; sumber yang lebih spesifik
        # (ekspor) sudah terbukti, jadi "DB langsung" bukan sumber tersendiri
        proven = [s for s in proven if s is not None]

    # porsi identitas yang cocok dengan data personel kita (NIK, atau NRP bila tak ada NIK)
    key_col, keys = ("nik", ids.niks) if ids.niks else ("nrp", ids.nrps)
    ours = 0
    for chunk in _chunks(keys):
        column = getattr(Personnel, key_col)
        ours += session.scalar(select(func.count()).select_from(Personnel).where(column.in_(chunk)))
    personnel_ratio = ours / len(keys) if keys else 0.0

    # porsi identitas yang ada di korpus data publik lama (per korpus, ambil yang terbesar)
    idents = ids.niks | ids.phones
    per_corpus: dict[int, int] = defaultdict(int)
    for chunk in _chunks(l4.fingerprint(i) for i in idents):
        for corpus_id, n in session.execute(
            select(CorpusFingerprint.corpus_id, func.count())
            .where(CorpusFingerprint.fp.in_(chunk))
            .group_by(CorpusFingerprint.corpus_id)
        ):
            per_corpus[corpus_id] += n
    corpus_ratio, corpus_label = 0.0, None
    if per_corpus and idents:
        best = max(per_corpus, key=per_corpus.get)
        corpus_ratio = per_corpus[best] / len(idents)
        corpus_label = session.get(PublicCorpus, best).label

    invalid_ratio = (
        sum(not l4.nik_valid(n) for n in ids.niks) / len(ids.niks) if ids.niks else 0.0
    )
    status = l4.verdict(proven, ids, personnel_ratio, corpus_ratio, invalid_ratio)
    return DumpAnalysis(
        status, ids, hits, proven, personnel_ratio, corpus_ratio, corpus_label, invalid_ratio
    )
