"""Pipeline citra Lapis 1: luruskan foto halaman, daftarkan ke template, baca bit dari
pergeseran tiap kata."""

from collections.abc import Iterator
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


PARTIAL_FACTOR = 4  # resolusi pencarian potongan pada template (1/4)


@dataclass(frozen=True)
class TextBlock:
    """Blok naskah pada peta tinta yang sudah diluruskan (koordinat peta tinta)."""

    box: tuple[int, int, int, int]  # x, y, lebar, tinggi
    pitch: float  # jarak antar-baris (px)
    ends: tuple[tuple[tuple[float, float], tuple[float, float]], ...]  # (ujung kiri, ujung kanan)


def _text_block(ink: np.ndarray) -> TextBlock | None:
    """Blok naskah: rantai baris rata-kiri terpanjang (naskah rata kiri, baris-barisnya bertumpuk
    dengan tepi kiri yang sama), jadi tinta lain di foto (taskbar, tab browser, bingkai layar,
    kertas lain) tidak ikut. Juga titik ujung kiri/kanan tiap baris untuk koreksi perspektif.
    None bila tak ada rantai minimal 3 baris."""
    h, w = ink.shape
    lines = cv2.morphologyEx(
        ink, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_RECT, (max(3, w // 40), 1))
    )
    n, labels, stats, _ = cv2.connectedComponentsWithStats(lines)
    cand = [
        (int(x), int(y), int(bw), int(bh), i)
        for i, (x, y, bw, bh, _) in enumerate(stats[1:n], start=1)
        if bw >= w // 10 and 2 <= bh <= h // 8
    ]
    if len(cand) < 3:
        return None
    cand.sort(key=lambda c: c[1] + c[3] / 2)
    med_h = float(np.median([c[3] for c in cand]))
    tol = max(3, w // 40)
    best: list[tuple[int, int, int, int, int]] = []
    for i in range(len(cand)):
        chain = [cand[i]]
        for c in cand[i + 1 :]:
            last = chain[-1]
            gap = (c[1] + c[3] / 2) - (last[1] + last[3] / 2)
            if gap > 6 * med_h:
                break
            if gap > 0.5 * med_h and abs(c[0] - last[0]) <= tol:
                chain.append(c)
        if len(chain) > len(best):
            best = chain
    if len(best) < 3:
        return None
    ends = []
    for x, y, bw, bh, idx in best:
        ys, xs = np.nonzero(labels[y : y + bh, x : x + bw] == idx)
        edge = max(2, bw // 10)
        left, right = xs < edge, xs >= bw - edge
        ends.append((  # x = tepi tinta, y = tinggi rata-rata tinta di dekat tepi itu
            (float(x + xs.min()), y + float(ys[left].mean())),
            (float(x + xs.max() + 1), y + float(ys[right].mean())),
        ))
    x0 = min(c[0] for c in best)
    y0 = min(c[1] for c in best)
    x1 = max(c[0] + c[2] for c in best)
    y1 = max(c[1] + c[3] for c in best)
    centres = np.array([c[1] + c[3] / 2 for c in best])
    return TextBlock(
        (x0, y0, x1 - x0, y1 - y0), float(np.median(np.diff(centres))), tuple(ends)
    )


def _normalizer(pts: np.ndarray) -> np.ndarray:
    c = pts.mean(axis=0)
    d = np.sqrt(((pts - c) ** 2).sum(axis=1)).mean() or 1.0
    s = np.sqrt(2) / d
    return np.array([[s, 0, -s * c[0]], [0, s, -s * c[1]], [0, 0, 1]])


def _apply(m: np.ndarray, pts: np.ndarray) -> np.ndarray:
    p = np.c_[pts, np.ones(len(pts))] @ m.T
    return p[:, :2] / p[:, 2:3]


def _perspective_from_lines(
    ends: np.ndarray, start: np.ndarray, layout: l1.Layout, dpi: int
) -> np.ndarray | None:
    """Homografi foto -> halaman dari geometri baris: ujung kiri tiap baris harus jatuh di
    margin kiri, dan kedua ujungnya pada ketinggian baris template yang sama (baris lurus).
    Ujung kanan hanya diberi bobot kecil untuk posisi mendatar karena panjang baris berbeda
    sedikit antar-salinan (lebar kata varian). `ends`: (n, 2, 2) titik pada foto; `start`:
    homografi awal untuk menentukan baris template mana yang dimaksud tiap baris foto.
    None bila baris yang cocok terlalu sedikit atau sisa galatnya besar."""
    k = dpi / 72
    pitch = layout.leading * k
    centres = np.array([(b - 0.275 * layout.font_size) * k for b in layout.baselines])
    right_x = np.array([spans[-1][1] * k for spans in layout.spans])
    h = start
    for _ in range(3):
        left_pg = _apply(h, ends[:, 0])
        idx = np.abs(centres[None, :] - left_pg[:, 1:2]).argmin(axis=1)
        ok = np.abs(centres[idx] - left_pg[:, 1]) < 0.35 * pitch
        dup = np.bincount(idx[ok], minlength=len(centres)) > 1
        ok &= ~dup[idx]
        if ok.sum() < 4:
            return None
        src = ends[ok].reshape(-1, 2)
        li = idx[ok]
        dst = np.empty_like(src)
        dst[0::2] = np.c_[np.full(len(li), l1.MARGIN_L * k), centres[li]]
        dst[1::2] = np.c_[right_x[li], centres[li]]
        ts, td = _normalizer(src), _normalizer(dst)
        sn, dn = _apply(ts, src), _apply(td, dst)
        rows = []
        for j, ((u, v), (x, y)) in enumerate(zip(sn, dn)):
            wx = 1.0 if j % 2 == 0 else 0.2  # ujung kanan: posisi mendatar kurang pasti
            rows.append(wx * np.array([u, v, 1, 0, 0, 0, -x * u, -x * v, -x]))
            rows.append(np.array([0, 0, 0, u, v, 1, -y * u, -y * v, -y]))
        _, _, vt = np.linalg.svd(np.array(rows))
        hn = vt[-1].reshape(3, 3)
        h = np.linalg.inv(td) @ hn @ ts
        h = h / h[2, 2]
    resid = np.abs(_apply(h, src)[:, 1] - dst[:, 1])
    return h if np.median(resid) < 0.15 * pitch else None


def rectify_partial(
    gray: np.ndarray, out_size: tuple[int, int], layout: l1.Layout, dpi: int
) -> tuple[np.ndarray, np.ndarray]:
    """Untuk foto yang hanya memuat sebagian halaman (potongan, atau halaman di layar yang
    sebagian tertutup taskbar): luruskan baris teks, cari blok naskah, perkirakan skala dari
    jarak antar-baris, lalu cari letaknya pada render template (template matching). Perspektif
    (mis. layar laptop yang condong) dikoreksi dari geometri baris. Bagian halaman di luar
    potongan diisi putih. Mengembalikan (citra, mask area potongan) agar penyelarasan halus
    hanya memakai area itu."""
    ink, f = _ink_map(gray)
    h, w = ink.shape
    rot_m = cv2.getRotationMatrix2D((w / 2, h / 2), _text_angle(ink), 1.0)
    rot = cv2.warpAffine(ink, rot_m, (w, h))
    block = _text_block(rot)
    if block is None:
        raise ValueError("blok naskah tak ditemukan")
    bx, by, bw, bh = block.box
    text = cv2.GaussianBlur(rot[by : by + bh, bx : bx + bw].astype(np.float32), (0, 0), 1.0)

    fr = PARTIAL_FACTOR
    ref = reference_flat(layout, dpi)
    ref_small = cv2.resize(
        255 - ref, (ref.shape[1] // fr, ref.shape[0] // fr), interpolation=cv2.INTER_AREA
    ).astype(np.float32)
    ref_small = cv2.GaussianBlur(ref_small, (0, 0), 1.0)
    base = layout.leading * dpi / 72 / fr / block.pitch
    best = (-1.0, 1.0, (0, 0))
    for s in base * np.arange(0.7, 1.3001, 0.02):  # jarak baris kasar (px bulat, foto kecil)
        tw, th = round(bw * s), round(bh * s)
        if not (8 <= tw <= ref_small.shape[1] and 4 <= th <= ref_small.shape[0]):
            continue
        tpl = cv2.resize(text, (tw, th), interpolation=cv2.INTER_AREA)
        _, score, _, loc = cv2.minMaxLoc(cv2.matchTemplate(ref_small, tpl, cv2.TM_CCOEFF_NORMED))
        best = max(best, (score, s, loc))
    score, s, (mx, my) = best
    if score <= 0:
        raise ValueError("potongan tak cocok dengan template")
    to_photo = np.linalg.inv(np.vstack([rot_m, [0, 0, 1]]) @ np.diag([1 / f, 1 / f, 1.0]))
    fit = np.array(
        [[fr * s, 0, fr * (mx - s * bx)], [0, fr * s, fr * (my - s * by)], [0, 0, 1]]
    )
    m = fit @ np.linalg.inv(to_photo)  # foto -> halaman (kemiripan)
    ends = _apply(to_photo, np.array(block.ends).reshape(-1, 2)).reshape(-1, 2, 2)
    m = _perspective_from_lines(ends, m, layout, dpi)
    if m is None:
        m = fit @ np.linalg.inv(to_photo)
    out = cv2.warpPerspective(
        gray, m, out_size, flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_CONSTANT, borderValue=255,
    )
    # di luar blok naskah (taskbar, latar meja, jari, dsb.) dibuat putih
    corners = np.array([[bx, by], [bx + bw, by], [bx + bw, by + bh], [bx, by + bh]], float)
    quad = _apply(m @ to_photo, corners)
    mask = np.zeros_like(out)
    cv2.fillConvexPoly(mask, np.round(quad).astype(np.int32), 255)
    pad = int(layout.leading * dpi / 72 / 2)
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (2 * pad + 1, 2 * pad + 1)))
    return np.where(mask > 0, out, 255).astype(np.uint8), mask


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
    mask: np.ndarray | None = None,
) -> tuple[np.ndarray, float, np.ndarray | None]:
    """Daftarkan citra yang sudah diluruskan kasar ke render template dengan ECC, bertahap dari
    resolusi rendah. Teks dipakai sebagai acuan, jadi lebih presisi daripada empat sudut kertas.
    `affine_first`: tahap pembuka affine pada resolusi sangat rendah (jangkauan konvergensi
    lebih lebar) sebelum homografi. `mask`: area citra yang sah (foto potongan); tanpa mask,
    area kosong ikut ditarik ke teks template dan penyelarasan bisa bergeser satu baris.
    Mengembalikan (citra selaras, korelasi ECC terakhir, mask yang ikut diselaraskan)."""
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
        small_mask = (
            None if mask is None else cv2.resize(mask, size, interpolation=cv2.INTER_NEAREST)
        )
        try:
            cc, warp = cv2.findTransformECC(
                _reference_ecc_input(layout, dpi, size), _ecc_input(current, size), init,
                motion,
                criteria, small_mask, 5,
            )
        except cv2.error:
            continue  # tidak konvergen pada skala ini; lanjut dengan citra apa adanya
        if motion == cv2.MOTION_AFFINE:
            warp = np.vstack([warp, [0, 0, 1]]).astype(np.float32)
        scale = np.diag([factor, factor, 1.0]).astype(np.float32)
        full = scale @ warp @ np.linalg.inv(scale)
        out_size = (ref.shape[1], ref.shape[0])
        current = cv2.warpPerspective(
            current, full, out_size,
            flags=cv2.INTER_CUBIC + cv2.WARP_INVERSE_MAP, borderMode=cv2.BORDER_REPLICATE,
        )
        if mask is not None:
            mask = cv2.warpPerspective(
                mask, full, out_size, flags=cv2.INTER_NEAREST + cv2.WARP_INVERSE_MAP,
                borderMode=cv2.BORDER_CONSTANT, borderValue=0,
            )
    return current, float(cc), mask


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
    if win.max() <= 1e-6:
        return None  # tak ada tinta (mis. di luar bagian halaman yang terfoto)
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
LINE_GATE = 0.3  # pusat baris boleh meleset maks. 0.3 jarak baris dari perkiraan


def track_lines(
    flat: np.ndarray, layout: l1.Layout, dpi: int, geom: RowGeometry
) -> list[tuple[int, int] | None]:
    """Baris piksel (y0, y1) tiap baris tata letak pada citra rata; None bila tak ditemukan.

    Baris dilacak satu per satu (posisi baris berikut dari baris sebelumnya) agar sisa
    distorsi vertikal tak menumpuk."""
    k = dpi / 72
    ratio = 1.0  # jarak baris terukur / jarak baris template (sisa distorsi vertikal)
    prev: float | None = None
    prev_line = 0
    step = 1.0
    out: list[tuple[int, int] | None] = []
    for li in range(len(layout.lines)):
        if prev is None:
            expect = _expected_centre(layout, li, dpi, geom, flat.shape[0])
        else:
            step = (layout.baselines[li] - layout.baselines[prev_line]) * k * geom.scale
            expect = prev + step * ratio
        found = _line_rows(flat, expect, geom.scale, layout, dpi)
        if found is not None and abs(found[1] - expect) > LINE_GATE * layout.leading * k * geom.scale:
            found = None  # baris terpotong di tepi foto, atau tinta baris tetangga: abaikan
        if found is None:
            prev, prev_line = expect, li
            out.append(None)
            continue
        rows, centre = found
        if prev is not None:
            ratio = float(np.clip(0.7 * ratio + 0.3 * (centre - prev) / step, 0.9, 1.1))
        prev, prev_line = centre, li
        out.append(rows)
    return out


def measure_slot_scores(
    gray: np.ndarray,
    layout: l1.Layout,
    delta_pt: float,
    dpi: int,
    geom: RowGeometry | None = None,
    tracked: list[tuple[int, int] | None] | None = None,
) -> dict[int, float]:
    """Skor per slot (~+1 untuk bit 1, ~-1 untuk bit 0) lewat registrasi kata ke template.

    Tiap kata dicocokkan seluruh bentuknya ke render referensi (lebih tahan blur daripada
    mengukur tepi celah). Bit = pergeseran kata ganjil terhadap rata-rata dua tetangganya,
    sehingga geseran/skala horizontal baris saling meniadakan. Slot dengan kecocokan buruk
    dilewati. `tracked`: hasil track_lines yang sudah ada (posisi baris sama untuk semua
    salinan naskah, jadi bisa dipakai ulang)."""
    k = dpi / 72
    flat = flatten_illumination(gray)
    geom = geom or locate_rows(flat, layout, dpi, flattened=True)
    tracked = tracked if tracked is not None else track_lines(flat, layout, dpi, geom)
    refs = _reference_columns(layout, dpi)
    cx = flat.shape[1] / 2
    amp = delta_pt * k
    scores: dict[int, float] = {}
    for li, rows in enumerate(tracked):
        if rows is None or layout.pairs(li) == 0:
            continue  # baris tak ditemukan, atau baris pendek (judul dsb.) yang tak membawa bit
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


def align_candidates(
    gray: np.ndarray, layout: l1.Layout, dpi: int, max_tries: int = 3
) -> Iterator[np.ndarray]:
    """Kandidat foto yang sudah diselaraskan ke tata letak, terbaik dulu.

    Kandidat pelurusan (4 cara awal, termasuk potongan sebagian halaman, x 4 rotasi) dinilai dengan ECC sampai resolusi 1/8
    (affine 1/16, lalu homografi 1/16 dan 1/8; tahap yang gagal konvergen dilewati).
    Penilaian di 1/16 saja terbukti menyingkirkan kandidat yang benar. `max_tries` teratas
    diselaraskan penuh, satu per satu saat diminta (pemanggil berhenti begitu terdekode).
    Kosong bila kertas/teks sama sekali tak ditemukan."""
    ref = reference_flat(layout, dpi)
    page_size = (ref.shape[1], ref.shape[0])
    ranked = []
    partial: tuple[float, np.ndarray] | None = None  # potongan terkoreksi perspektif, tanpa ECC
    for k in range(4):
        g = np.ascontiguousarray(np.rot90(gray, k))
        for rectifier in (
            lambda im: (rectify_page(im, page_size), None),
            lambda im: (rectify_by_text(im, page_size, layout, dpi), None),
            lambda im: (rectify_by_text(im, page_size, layout, dpi, method="minrect"), None),
            lambda im: rectify_partial(im, page_size, layout, dpi),
        ):
            try:
                flat, mask = rectifier(g)
            except (ValueError, cv2.error):
                continue
            rough, cc, refined_mask = refine_alignment(
                flat, layout, dpi, factors=(16, 8), affine_first=True, iterations=60, mask=mask
            )
            ranked.append((cc, rough, refined_mask))
            if mask is not None and (partial is None or cc > partial[0]):
                partial = (cc, flat)
    for _, rough, mask in sorted(ranked, key=lambda c: -c[0])[:max_tries]:
        aligned, _, mask = refine_alignment(rough, layout, dpi, factors=(8, 4, 2), mask=mask)
        if mask is not None:
            aligned = np.where(mask > 0, aligned, 255).astype(np.uint8)
        yield aligned
    # Foto layar/potongan dengan perspektif kuat: ECC bisa terkunci ke baris tetangga dan
    # merusak hasil koreksi perspektif dari geometri baris, jadi versi tanpa ECC dicoba terakhir.
    if partial is not None:
        yield partial[1]


def decode_photo(
    gray: np.ndarray,
    layout: l1.Layout,
    delta_pt: float,
    dpi: int,
    max_tries: int = 3,
) -> PhotoResult | None:
    """Baca foto halaman bertata letak tetap (Lapis 1 saja). Kandidat penyelarasan dicoba
    berurutan; mengembalikan yang pertama terdekode, atau yang slotnya terbanyak. None bila
    kertas/teks sama sekali tak ditemukan."""
    best: PhotoResult | None = None
    for aligned in align_candidates(gray, layout, dpi, max_tries):
        geom = locate_rows(aligned, layout, dpi)
        scores = measure_slot_scores(aligned, layout, delta_pt, dpi, geom)
        try:
            return PhotoResult(scores, aligned, geom, decode_scores(scores))
        except PayloadDecodeError:
            if best is None or len(scores) > len(best.scores):
                best = PhotoResult(scores, aligned, geom, None)
    return best
