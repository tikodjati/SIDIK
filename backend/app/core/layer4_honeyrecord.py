"""Lapis 4 (honey-record): baris data personel sintetis untuk menjebak dan mengatribusi kebocoran
basis data, plus pemeriksa klaim dump (anti-psywar).

Dua jenis honey-record:
- tertanam di tabel personel (sumber "DB langsung"): ikut tercuri bila basis data dibobol;
- unik per ekspor: diselipkan acak ke berkas ekspor; menunjuk ekspor itu (akun, waktu, satuan).

Semua identitas di modul ini rekaan dengan format realistis (NIK 16 digit berstruktur, nomor HP
seluler Indonesia). Di produksi, nomor HP honey-record adalah SIM perangkap milik satuan.
"""

import hashlib
import random
import re
from dataclasses import dataclass
from datetime import date

# --- generator persona -------------------------------------------------------------------

_DEPAN = (
    "Agus", "Ahmad", "Andi", "Arif", "Bambang", "Budi", "Dedi", "Dimas", "Eko", "Fajar",
    "Gilang", "Hendra", "Heru", "Imam", "Indra", "Joko", "Kurniawan", "Lukman", "Mulyadi",
    "Nugroho", "Rahmat", "Rizki", "Sigit", "Slamet", "Taufik", "Teguh", "Wahyu", "Yudi",
    "Ayu", "Dewi", "Fitri", "Indah", "Maya", "Nur", "Putri", "Rina", "Sari", "Wulan",
)
_BELAKANG = (
    "Pratama", "Saputra", "Wibowo", "Santoso", "Hidayat", "Setiawan", "Nugraha", "Kusuma",
    "Purnomo", "Gunawan", "Siregar", "Nasution", "Lubis", "Simanjuntak", "Harahap", "Sitompul",
    "Hakim", "Rahman", "Firmansyah", "Ramadhan", "Wijaya", "Hutapea", "Sinaga", "Prasetyo",
)
_PANGKAT = (
    ("Prajurit Dua", 3), ("Prajurit Satu", 3), ("Kopral Dua", 3), ("Kopral Satu", 3),
    ("Sersan Dua", 2), ("Sersan Satu", 2), ("Sersan Kepala", 2), ("Pembantu Letnan Dua", 2),
    ("Letnan Dua", 1), ("Letnan Satu", 1), ("Kapten", 1), ("Mayor", 1),
)
SATUAN = (
    "Korem 051/Wijayakarta",
    "Kodim 0501/Jakarta Pusat",
    "Kodim 0502/Jakarta Utara",
    "Kodim 0503/Jakarta Barat",
    "Yonif 201/Jaya Yudha",
    "Yonif 202/Tajimalela",
    "Denintel Kodam Jaya",
    "Hubdam Jaya",
)
_PREFIX_HP = ("0811", "0812", "0813", "0821", "0822", "0852", "0853", "0857", "0878", "0896")
_PROVINSI = (
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "21", "31", "32", "33", "34", "35", "36",
    "51", "52", "53", "61", "62", "63", "64", "65", "71", "72", "73", "74", "75", "76", "81", "82",
    "91", "92", "94",
)  # kode provinsi pada NIK (Kemendagri)


@dataclass(frozen=True)
class Persona:
    nrp: str
    nama: str
    pangkat: str
    satuan: str
    nik: str
    no_hp: str
    tanggal_lahir: date


def make_persona(rng: random.Random, satuan: str | None = None) -> Persona:
    """Satu persona rekaan dengan format realistis. `rng` menentukan hasil (bisa diulang)."""
    pangkat, golongan = rng.choice(_PANGKAT)
    lahir = date(rng.randint(1975, 2004), rng.randint(1, 12), rng.randint(1, 28))
    wanita = rng.random() < 0.08
    tgl = lahir.day + (40 if wanita else 0)  # aturan NIK: tanggal lahir wanita + 40
    nik = (
        "31" + f"{rng.randint(71, 75):02d}" + f"{rng.randint(1, 10):02d}"
        + f"{tgl:02d}{lahir.month:02d}{lahir.year % 100:02d}" + f"{rng.randint(1, 9999):04d}"
    )
    nrp = f"{golongan}{lahir.year % 100:02d}{rng.randint(0, 9999999):07d}"
    hp = rng.choice(_PREFIX_HP) + "".join(str(rng.randint(0, 9)) for _ in range(rng.choice((7, 8))))
    depan = rng.choice(_DEPAN[-10:] if wanita else _DEPAN[:-10])
    return Persona(
        nrp=nrp,
        nama=f"{depan} {rng.choice(_BELAKANG)}",
        pangkat=pangkat,
        satuan=satuan or rng.choice(SATUAN),
        nik=nik,
        no_hp=hp,
        tanggal_lahir=lahir,
    )


def sentinel_count(rows: int) -> int:
    """Jumlah honey-record untuk sekumpulan `rows` baris: kira-kira 1 per 50, minimal 3, agar
    potongan dump berukuran sedang pun hampir pasti memuat lebih dari satu."""
    return max(3, -(-rows // 50))


# --- ekstraksi identitas dari dump -------------------------------------------------------

_DIGITS = re.compile(r"(?<![\d])\+?\d[\d\-\s.]*\d(?![\d])")


def _normalize_phone(digits: str) -> str:
    return "0" + digits[2:] if digits.startswith("62") else digits


@dataclass(frozen=True)
class Identifiers:
    niks: frozenset[str]
    phones: frozenset[str]
    nrps: frozenset[str]

    @property
    def total(self) -> int:
        return len(self.niks) + len(self.phones) + len(self.nrps)


def extract_identifiers(text: str) -> Identifiers:
    """Identitas berbentuk angka di dump (CSV, SQL INSERT, JSON, teks): NIK 16 digit, nomor HP
    seluler (08.., +628.., 628..; boleh bertanda pisah), dan kandidat NRP 8-14 digit."""
    niks: set[str] = set()
    phones: set[str] = set()
    nrps: set[str] = set()
    def as_phone(chunk: str) -> str | None:
        phone = _normalize_phone(re.sub(r"\D", "", chunk))
        return phone if phone.startswith("08") and 10 <= len(phone) <= 13 else None

    for match in _DIGITS.finditer(text):
        raw = match.group()
        # angka bertanda pisah (0812-3456-7890, 0812 3456 7890) dianggap satu nomor HP;
        # selain itu tiap kelompok (dipisah spasi, lalu tanda baca) dinilai sendiri-sendiri
        if phone := as_phone(raw):
            phones.add(phone)
            continue
        chunks = raw.split()
        i = 0
        while i < len(chunks):
            # nomor HP bisa terpecah spasi: coba gabungkan hingga 4 kelompok berurutan
            joined = next(
                (j for j in range(min(len(chunks), i + 4), i, -1)
                 if as_phone("".join(chunks[i:j]))),
                None,
            )
            if joined is not None:
                phones.add(as_phone("".join(chunks[i:joined])))
                i = joined
                continue
            chunk = chunks[i]
            i += 1
            for part in re.findall(r"\d+", chunk):
                if len(part) == 16:
                    niks.add(part)
                elif 8 <= len(part) <= 14:
                    nrps.add(part)
    return Identifiers(frozenset(niks), frozenset(phones), frozenset(nrps))


def nik_valid(nik: str) -> bool:
    """Struktur NIK: kode provinsi dikenal, kabupaten/kecamatan bukan 00, tanggal lahir mungkin
    (wanita + 40), bulan 1-12, nomor urut bukan 0000. Bukan cek ke Dukcapil."""
    if len(nik) != 16 or not nik.isdigit() or nik[:2] not in _PROVINSI:
        return False
    if nik[2:4] == "00" or nik[4:6] == "00" or nik[12:] == "0000":
        return False
    day, month = int(nik[6:8]), int(nik[8:10])
    return (1 <= day <= 31 or 41 <= day <= 71) and 1 <= month <= 12


def fingerprint(identifier: str) -> str:
    """Sidik identitas untuk korpus data publik: hanya hash yang disimpan, bukan data aslinya."""
    return hashlib.sha256(identifier.encode()).hexdigest()


# --- penilaian -------------------------------------------------------------------------

MIN_ROWS_ALONE = 2  # baris honey-record cocok agar satu sumber terbukti (atau 1 baris, >= 2 kolom)
MIN_FIELDS_ONE_ROW = 2
GENUINE_RATIO = 0.5  # porsi identitas dump yang cocok dengan data kita / korpus publik
FABRICATED_RATIO = 0.3  # porsi NIK berformat tidak valid


@dataclass(frozen=True)
class RecordHit:
    record_id: int
    source: int | None  # id ekspor; None = tertanam langsung di DB
    fields: tuple[str, ...]  # kolom yang cocok: nik / nrp / no_hp


def source_proven(hits: list[RecordHit]) -> bool:
    """Bukti cukup untuk satu sumber: >= 2 baris honey-record, atau 1 baris cocok di >= 2 kolom.
    Satu kolom saja bisa kebetulan (NIK rekaan dapat sama dengan NIK orang sungguhan)."""
    return len(hits) >= MIN_ROWS_ALONE or any(len(h.fields) >= MIN_FIELDS_ONE_ROW for h in hits)


def verdict(
    proven_sources: list[int | None],
    ids: Identifiers,
    personnel_ratio: float,
    corpus_ratio: float,
    invalid_ratio: float,
) -> str:
    """Status dump. Urutan: honey-record (terbukti asli) > cocok data kita > daur ulang data
    publik > format rekaan > bukan dari basis data kita."""
    if proven_sources:
        return "AUTHENTIC_LEAK"
    if ids.total == 0:
        return "INSUFFICIENT_DATA"
    if personnel_ratio >= GENUINE_RATIO:
        return "UNTRACED_MATCH"
    if corpus_ratio >= GENUINE_RATIO:
        return "RECYCLED_PUBLIC"
    if ids.niks and invalid_ratio >= FABRICATED_RATIO:
        return "FABRICATED"
    return "NOT_FROM_OUR_DB"
