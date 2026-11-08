"""Pipeline citra Lapis 1: luruskan foto halaman, daftarkan ke template, baca bit dari
pergeseran tiap kata."""

from dataclasses import dataclass
from functools import lru_cache

import cv2
import numpy as np

from app.core import layer1_visual as l1
from app.core.payload import PayloadDecodeError, decode_scores


def _order_corners(pts: np.ndarray) -> np.ndarray:
    s, d = pts.sum(axis=1), np.diff(pts, axis=1).ravel()
    order = [s.argmin(), d.argmin(), s.argmax(), d.argmax()]
    return pts[order].astype(np.float32)


def _warp_quad(gray: np.ndarray, quad: np.ndarray, dst_quad: np.ndarray, size) -> np.ndarray:
    m = cv2.getPerspectiveTransform(_order_corners(quad.astype(np.float32)), dst_quad)
    return cv2.warpPerspective(gray, m, size, flags=cv2.INTER_CUBIC)


def rectify_page(gray: np.ndarray, out_size: tuple[int, int]) -> np.ndarray:
    """Cari kertas (kontur terbesar), luruskan ke `out_size` = (lebar, tinggi) piksel."""
    sigma = max(gray.shape) / 400
    blur = cv2.GaussianBlur(gray, (0, 0), sigma)
    _, mask = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    page = max(contours, key=cv2.contourArea)
    approx = cv2.approxPolyDP(page, 0.02 * cv2.arcLength(page, True), True)
    quad = approx.reshape(-1, 2) if len(approx) == 4 else cv2.boxPoints(cv2.minAreaRect(page))
    w, h = out_size
    dst = np.array([[0, 0], [w - 1, 0], [w - 1, h - 1], [0, h - 1]], np.float32)
    return _warp_quad(gray, quad, dst, out_size)


def _ink_map(gray: np.ndarray, width: int = 640) -> tuple[np.ndarray, float]:
    """Peta tinta biner berukuran kecil dan faktor skalanya terhadap citra asli."""
    f = max(gray.shape) / width
    small = cv2.resize(gray, None, fx=1 / f, fy=1 / f, interpolation=cv2.INTER_AREA)
    ink = cv2.adaptiveThreshold(
        small, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 10
    )
    return ink, f


def _text_angle(ink: np.ndarray) -> float:
    """Sudut (derajat, berlawanan jarum jam) yang meluruskan baris teks: memaksimalkan
    ketajaman profil baris."""
    h, w = ink.shape
    ink = cv2.GaussianBlur(ink, (0, 0), 1.0).astype(np.float32)

    def sharpness(angle: float) -> float:
        rot = cv2.warpAffine(ink, cv2.getRotationMatrix2D((w / 2, h / 2), angle, 1.0), (w, h))
        return float((rot.sum(axis=1) ** 2).sum())

    coarse = max(np.arange(-70, 70.1, 1.0), key=sharpness)
    return float(max(np.arange(coarse - 1, coarse + 1.01, 0.1), key=sharpness))


def _template_text_box(layout: l1.Layout, dpi: int) -> tuple[float, float, float, float]:
    k = dpi / 72
    x1 = max(spans[-1][1] for spans in layout.spans)
    y0 = (layout.baselines[0] - 0.75 * layout.font_size) * k
    y1 = (layout.baselines[-1] + 0.2 * layout.font_size) * k
    return l1.MARGIN_L * k, y0, x1 * k, y1


def rectify_by_text(
    gray: np.ndarray,
    out_size: tuple[int, int],
    layout: l1.Layout,
    dpi: int,
    method: str = "deskew",
) -> np.ndarray:
    """Alternatif `rectify_page` yang tak bergantung pada tepi kertas (bisa terpotong, tertutup
    jari, atau menyatu dengan kertas lain): kotak teks foto dicocokkan ke kotak teks template.

    `deskew`: estimasi sudut baris teks, putar lurus, ambil kotak pembatas.
    `minrect`: persegi panjang berotasi minimum dari blok tinta (lebih baik untuk beberapa foto)."""
    tx0, ty0, tx1, ty1 = _template_text_box(layout, dpi)
    if method == "minrect":
        side = max(gray.shape)
        ink = cv2.adaptiveThreshold(
            cv2.GaussianBlur(gray, (0, 0), side / 800),
            255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, side // 40 | 1, 12,
        )
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (side // 50, side // 50))
        blob = cv2.morphologyEx(ink, cv2.MORPH_CLOSE, kernel)
        contours, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        box = cv2.boxPoints(cv2.minAreaRect(max(contours, key=cv2.contourArea)))
        dst = np.array([[tx0, ty0], [tx1, ty0], [tx1, ty1], [tx0, ty1]], np.float32)
        return _warp_quad(gray, box, dst, out_size)

    ink, f = _ink_map(gray)
    h, w = ink.shape
    rot_m = cv2.getRotationMatrix2D((w / 2, h / 2), _text_angle(ink), 1.0)
    rot = cv2.warpAffine(ink, rot_m, (w, h))
    side = max(h, w)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (side // 40, side // 40))
    blob = cv2.morphologyEx(rot, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(blob, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bx, by, bw, bh = cv2.boundingRect(max(contours, key=cv2.contourArea))
    sx, sy = (tx1 - tx0) / bw, (ty1 - ty0) / bh
    to_small = np.diag([1 / f, 1 / f, 1.0])
    rotate = np.vstack([rot_m, [0, 0, 1]])
    fit = np.array([[sx, 0, tx0 - sx * bx], [0, sy, ty0 - sy * by], [0, 0, 1]])
    return cv2.warpPerspective(gray, fit @ rotate @ to_small, out_size, flags=cv2.INTER_CUBIC)


def flatten_illumination(gray: np.ndarray, window_div: int = 160) -> np.ndarray:
    """Buang gradien bayangan/pencahayaan: bagi dengan estimasi latar kertas lokal.

    Latar = dilasi (nilai paling terang = kertas) dengan jendela sisi terpanjang/`window_div`,
    lalu dihaluskan. Dilasi dilakukan pada resolusi citra itu sendiri: bila citra diperkecil
    dulu, area teks padat tak lagi punya piksel kertas murni dan latarnya terlalu gelap (terbukti
    merusak penyelarasan foto miring). Hanya penghalusan yang dilakukan pada <= 640 px, karena
    latar berubah halus dan blur besar pada resolusi penuh mahal."""
    k = max(3, max(gray.shape) // window_div | 1)
    peak = cv2.dilate(gray, cv2.getStructuringElement(cv2.MORPH_RECT, (k, k)))
    f = max(1.0, max(gray.shape) / 640)
    if f == 1.0:
        bg = cv2.GaussianBlur(peak, (0, 0), k * 2)
    else:
        small = cv2.resize(peak, None, fx=1 / f, fy=1 / f, interpolation=cv2.INTER_AREA)
        small = cv2.GaussianBlur(small, (0, 0), max(1.0, k * 2 / f))
        bg = cv2.resize(small, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_LINEAR)
    return np.clip(
        gray.astype(np.float32) / np.maximum(bg.astype(np.float32), 1) * 255, 0, 255
    ).astype(np.uint8)


@lru_cache(maxsize=4)
def reference_flat(layout: l1.Layout, dpi: int) -> np.ndarray:
    return flatten_illumination(l1.rasterize_gray(l1.render_pdf(layout, None, 0), dpi))


def _ecc_input(img: np.ndarray, size: tuple[int, int]) -> np.ndarray:
    """Citra kecil untuk ECC. Cahaya diratakan pada resolusi 1/2 (bukan penuh: jauh lebih cepat)
    dengan jendela lebih dari satu jarak baris, baru diperkecil. Meratakan setelah diperkecil
    membuat latar di area teks padat terlalu gelap; terbukti merusak penyelarasan foto miring."""
    mid_w = max(size[0], img.shape[1] // 2)
    mid = cv2.resize(img, (mid_w, round(img.shape[0] * mid_w / img.shape[1])),
                     interpolation=cv2.INTER_AREA)
    small = cv2.resize(flatten_illumination(mid, window_div=60), size, interpolation=cv2.INTER_AREA)
    return cv2.GaussianBlur(255 - small.astype(np.float32), (0, 0), 1.5)


@lru_cache(maxsize=16)
def _reference_ecc_input(layout: l1.Layout, dpi: int, size: tuple[int, int]) -> np.ndarray:
    return _ecc_input(reference_flat(layout, dpi), size)


def refine_alignment(
    flat: np.ndarray,
    layout: l1.Layout,
    dpi: int,
    factors: tuple[int, ...] = (8, 4, 2),
    affine_first: bool = False,
    iterations: int = 150,
) -> tuple[np.ndarray, float]:
    """Daftarkan citra yang sudah diluruskan kasar ke render template dengan ECC, bertahap dari
    resolusi rendah. Teks dipakai sebagai acuan, jadi lebih presisi daripada empat sudut kertas.
    `affine_first`: tahap pembuka affine pada resolusi sangat rendah (jangkauan konvergensi
    lebih lebar) sebelum homografi. Mengembalikan (citra selaras, korelasi ECC terakhir)."""
    ref = reference_flat(layout, dpi)
    stages = [(16, cv2.MOTION_AFFINE)] if affine_first else []
    stages += [(f, cv2.MOTION_HOMOGRAPHY) for f in factors]
    current, cc = flat, 0.0
    for factor, motion in stages:
        size = (ref.shape[1] // factor, ref.shape[0] // factor)
        init = np.eye(2, 3, dtype=np.float32) if motion == cv2.MOTION_AFFINE else np.eye(
            3, dtype=np.float32
        )
        criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, iterations, 1e-5)
        try:
            cc, warp = cv2.findTransformECC(
                _reference_ecc_input(layout, dpi, size), _ecc_input(current, size), init,
                motion,
                criteria, None, 5,
            )
        except cv2.error:
            continue  # tidak konvergen pada skala ini; lanjut dengan citra apa adanya
        if motion == cv2.MOTION_AFFINE:
            warp = np.vstack([warp, [0, 0, 1]]).astype(np.float32)
        scale = np.diag([factor, factor, 1.0]).astype(np.float32)
        current = cv2.warpPerspective(
            current, scale @ warp @ np.linalg.inv(scale), (ref.shape[1], ref.shape[0]),
            flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE,
        )
    return current, float(cc)


def _row_profile(flat: np.ndarray) -> np.ndarray:
    ink = (255 - flat.astype(np.float32)) / 255
    prof = ink.sum(axis=1)
    return (prof - prof.mean()) / (prof.std() + 1e-6)


@dataclass(frozen=True)
class RowGeometry:
    """Posisi baris di foto terhadap template: y_img = cy + scale*(y_ref - cy) + dy (px)."""

    scale: float
    dy: float
    score: float  # korelasi profil baris, 1 = identik


def locate_rows(
    flat: np.ndarray, layout: l1.Layout, dpi: int, flattened: bool = False
) -> RowGeometry:
    """Cocokkan profil baris foto dengan template (cetakan sering diperkecil 'fit to page').
    `flattened`: citra sudah melalui flatten_illumination."""
    img = _row_profile(flat if flattened else flatten_illumination(flat))
    ref = _row_profile(reference_flat(layout, dpi))
    ys = np.arange(len(img), dtype=np.float32)
    cy = len(img) / 2

    def corr(s: float, dy: float) -> float:
        u = cy + (ys - cy - dy) / s
        return float(np.mean(img * np.interp(u, np.arange(len(ref)), ref, left=0, right=0)))

    best = max(
        ((corr(s, dy), s, dy) for s in np.arange(0.85, 1.101, 0.005) for dy in range(-90, 91, 3)),
    )
    _, s0, dy0 = best
    best = max(
        (corr(s, dy), s, dy)
        for s in np.arange(s0 - 0.006, s0 + 0.0061, 0.001)
        for dy in np.arange(dy0 - 3, dy0 + 3.01, 0.5)
    )
    return RowGeometry(scale=float(best[1]), dy=float(best[2]), score=best[0])


def _darkness(band: np.ndarray) -> np.ndarray:
    paper = max(float(np.percentile(band, 95)), 1.0)
    return np.clip((paper - band.astype(np.float32)) / paper, 0, 1)


def _expected_centre(
    layout: l1.Layout, line: int, dpi: int, geom: RowGeometry, height: int
) -> float:
    k = dpi / 72
    base = height / 2 + geom.scale * (layout.baselines[line] * k - height / 2) + geom.dy
    return base - 0.275 * layout.font_size * k * geom.scale


def _line_rows(
    gray: np.ndarray, expect: float, scale: float, layout: l1.Layout, dpi: int
) -> tuple[tuple[int, int], float] | None:
    """Baris piksel (y0, y1) satu baris teks, dipusatkan pada tinta sebenarnya di sekitar posisi
    perkiraan `expect` (koreksi lokal). Mengembalikan juga pusat baris yang ditemukan."""
    k = dpi / 72
    half = int(0.5 * layout.leading * k * scale)
    w0, w1 = int(expect) - half, int(expect) + half
    if w0 < 0 or w1 > gray.shape[0]:
        return None
    cols = slice(int(0.05 * gray.shape[1]), int(0.95 * gray.shape[1]))
    win = _darkness(gray[w0:w1, cols]).sum(axis=1)
    body = win >= 0.4 * win.max()
    centre = w0 + float((np.arange(len(win))[body] * win[body]).sum() / win[body].sum())
    y0 = int(centre - 0.525 * layout.font_size * k * scale)
    y1 = int(centre + 0.525 * layout.font_size * k * scale)
    return ((y0, y1), centre) if y0 >= 0 and y1 <= gray.shape[0] else None


def _column_profile(gray: np.ndarray, rows: tuple[int, int]) -> np.ndarray:
    return _darkness(gray[rows[0] : rows[1]]).sum(axis=0)


@lru_cache(maxsize=4)
def _reference_columns(layout: l1.Layout, dpi: int) -> list[np.ndarray]:
    """Profil kolom tiap baris pada render template tanpa modulasi (skala 1, tanpa geseran)."""
    flat = reference_flat(layout, dpi)
    identity = RowGeometry(1.0, 0.0, 1.0)
    out = []
    for li in range(len(layout.lines)):
        expect = _expected_centre(layout, li, dpi, identity, flat.shape[0])
        rows, _ = _line_rows(flat, expect, 1.0, layout, dpi)
        out.append(_column_profile(flat, rows))
    return out


def _zncc_shift(
    ref: np.ndarray, img: np.ndarray, pos: np.ndarray, shifts: np.ndarray
) -> tuple[float, float]:
    """Geser (px citra) yang memaksimalkan korelasi silang ternormalisasi antara profil
    referensi `ref` dan profil citra yang disampel di `pos + shift`; sub-piksel (parabola)."""
    cand = np.interp((pos[None, :] + shifts[:, None]).ravel(), np.arange(len(img)), img)
    cand = cand.reshape(len(shifts), len(ref))
    a = ref - ref.mean()
    b = cand - cand.mean(axis=1, keepdims=True)
    z = (b @ a) / (np.linalg.norm(b, axis=1) * np.linalg.norm(a) + 1e-9)
    i = int(z.argmax())
    step = float(shifts[1] - shifts[0])
    if 0 < i < len(z) - 1:
        denom = z[i - 1] - 2 * z[i] + z[i + 1]
        if denom < 0:
            return float(shifts[i] + 0.5 * (z[i - 1] - z[i + 1]) / denom * step), float(z[i])
    return float(shifts[i]), float(z[i])


MIN_WORD_CORR = 0.5
LINE_SCALE_RANGE = 0.07  # sisa skala horizontal per baris (foto miring kuat butuh lebar)


def measure_slot_scores(
    gray: np.ndarray,
    layout: l1.Layout,
    delta_pt: float,
    dpi: int,
    geom: RowGeometry | None = None,
) -> dict[int, float]:
    """Skor per slot (~+1 untuk bit 1, ~-1 untuk bit 0) lewat registrasi kata ke template.

    Tiap kata dicocokkan seluruh bentuknya ke render referensi (lebih tahan blur daripada
    mengukur tepi celah). Bit = pergeseran kata ganjil terhadap rata-rata dua tetangganya,
    sehingga geseran/skala horizontal baris saling meniadakan. Baris dilacak satu per satu
    (posisi baris berikut dari baris sebelumnya) agar sisa distorsi vertikal tak menumpuk.
    Slot dengan kecocokan buruk dilewati.
    """
    k = dpi / 72
    flat = flatten_illumination(gray)
    geom = geom or locate_rows(flat, layout, dpi, flattened=True)
    refs = _reference_columns(layout, dpi)
    cx = flat.shape[1] / 2
    amp = delta_pt * k
    ratio = 1.0  # jarak baris terukur / jarak baris template (sisa distorsi vertikal)
    prev: float | None = None
    prev_line = 0
    step = 1.0
    scores: dict[int, float] = {}
    for li in range(len(layout.lines)):
        if prev is None:
            expect = _expected_centre(layout, li, dpi, geom, flat.shape[0])
        else:
            step = (layout.baselines[li] - layout.baselines[prev_line]) * k * geom.scale
            expect = prev + step * ratio
        found = _line_rows(flat, expect, geom.scale, layout, dpi)
        if found is None:
            prev, prev_line = expect, li
            continue
        rows, centre = found
        if prev is not None:
            ratio = float(np.clip(0.7 * ratio + 0.3 * (centre - prev) / step, 0.9, 1.1))
        prev, prev_line = centre, li
        if layout.pairs(li) == 0:
            continue  # baris pendek (judul dsb.): ikut dilacak, tapi tak membawa bit
        img = _column_profile(flat, rows)
        spans = [(int(a * k), int(b * k)) for a, b in layout.spans[li]]

        # skala + geseran horizontal baris (sisa distorsi berbeda tiap baris): kasar lalu halus
        xs = np.arange(spans[0][0] - 3, spans[-1][1] + 4, dtype=np.float32)
        line_ref = refs[li][xs.astype(int)]
        best = (-1.0, 1.0, 0.0)
        for sx in np.arange(1 - LINE_SCALE_RANGE, 1 + LINE_SCALE_RANGE + 1e-9, 0.01):
            dx, z = _zncc_shift(line_ref, img, cx + sx * (xs - cx), np.arange(-90, 90.1, 3.0))
            best = max(best, (z, sx, dx))
        _, sx0, dx0 = best
        for sx in np.arange(sx0 - 0.01, sx0 + 0.0101, 0.002):  # halus di sekitar yang terbaik
            near = np.arange(dx0 - 9, dx0 + 9.1, 1.0)
            dx, z = _zncc_shift(line_ref, img, cx + sx * (xs - cx), near)
            best = max(best, (z, sx, dx))
        _, sx, dx = best
        dx, _ = _zncc_shift(line_ref, img, cx + sx * (xs - cx), np.arange(dx - 3, dx + 3.01, 0.25))

        offsets, corrs = [], []
        taus = np.arange(-6, 6.01, 0.25)
        for a, b in spans:
            xw = np.arange(a - 2, b + 3, dtype=np.float32)
            pos = cx + sx * (xw - cx) + dx
            shift, z = _zncc_shift(refs[li][xw.astype(int)], img, pos, sx * taus)
            offsets.append(shift / sx)
            corrs.append(z)
        for p in range(layout.pairs(li)):
            i = 2 * p + 1
            if min(corrs[i - 1 : i + 2]) < MIN_WORD_CORR:
                continue
            scores[layout.slot_base[li] + p] = float(
                (offsets[i] - 0.5 * (offsets[i - 1] + offsets[i + 1])) / amp
            )
    return scores


@dataclass(frozen=True)
class PhotoResult:
    """Hasil analisis foto: skor slot, citra selaras, dan (copy_id, flags) bila terdekode."""

    scores: dict[int, float]
    aligned: np.ndarray
    geom: RowGeometry
    decoded: tuple[int, int] | None


def decode_photo(
    gray: np.ndarray,
    layout: l1.Layout,
    delta_pt: float,
    dpi: int,
    max_tries: int = 3,
) -> PhotoResult | None:
    """Luruskan dan baca foto halaman. Kandidat pelurusan (3 cara awal x 4 rotasi) dinilai
    dengan ECC sampai resolusi 1/8 (affine 1/16, lalu homografi 1/16 dan 1/8; tahap yang gagal
    konvergen dilewati). Penilaian di 1/16 saja terbukti menyingkirkan kandidat yang benar.
    `max_tries` teratas diselaraskan penuh dan didekode berurutan. Mengembalikan yang pertama
    terdekode, atau yang slotnya terbanyak. None bila kertas/teks sama sekali tak ditemukan."""
    ref = reference_flat(layout, dpi)
    page_size = (ref.shape[1], ref.shape[0])
    ranked = []
    for k in range(4):
        g = np.ascontiguousarray(np.rot90(gray, k))
        for rectifier in (
            lambda im: rectify_page(im, page_size),
            lambda im: rectify_by_text(im, page_size, layout, dpi),
            lambda im: rectify_by_text(im, page_size, layout, dpi, method="minrect"),
        ):
            try:
                flat = rectifier(g)
            except (ValueError, cv2.error):
                continue
            rough, cc = refine_alignment(
                flat, layout, dpi, factors=(16, 8), affine_first=True, iterations=60
            )
            ranked.append((cc, rough))
    best: PhotoResult | None = None
    for _, rough in sorted(ranked, key=lambda c: -c[0])[:max_tries]:
        aligned, _ = refine_alignment(rough, layout, dpi, factors=(8, 4, 2))
        geom = locate_rows(aligned, layout, dpi)
        scores = measure_slot_scores(aligned, layout, delta_pt, dpi, geom)
        try:
            return PhotoResult(scores, aligned, geom, decode_scores(scores))
        except PayloadDecodeError:
            if best is None or len(scores) > len(best.scores):
                best = PhotoResult(scores, aligned, geom, None)
    return best
