"""Spike Lapis 1: ukur ketahanan modulasi spasi terhadap simulasi foto HP.

Jalankan dari backend/:  python -m scripts.spike_layer1 [--trials 8] [--save-sample DIR]
"""

import argparse
import itertools
import random
from pathlib import Path

import cv2
import numpy as np

from app.core import layer1_visual as l1
from app.core.payload import PayloadDecodeError, decode_scores, encode_payload
from app.core.vision_extractor import measure_slot_scores, rectify_page

DPI = 300


def simulate_camera(
    page: np.ndarray, long_side_px: int, tilt_deg: float, blur_sigma: float, jpeg_q: int,
    rng: random.Random, noise_sd: float = 3.0,
) -> np.ndarray:
    """Foto kertas di atas meja: perspektif, bayangan, blur, noise, kompresi JPEG."""
    out_h = int(long_side_px / 0.85)
    out_w = int(out_h * 0.75)
    pitch = np.radians(tilt_deg)
    yaw = np.radians(rng.uniform(-6, 6) + (tilt_deg * 0.3))
    roll = np.radians(rng.uniform(-5, 5))
    w, h = l1.PAGE_W, l1.PAGE_H
    pts = np.array([[-w / 2, -h / 2, 0], [w / 2, -h / 2, 0], [w / 2, h / 2, 0], [-w / 2, h / 2, 0]])
    cp, sp = np.cos(pitch), np.sin(pitch)
    rx = np.array([[1, 0, 0], [0, cp, -sp], [0, sp, cp]])
    ry = np.array([[np.cos(yaw), 0, np.sin(yaw)], [0, 1, 0], [-np.sin(yaw), 0, np.cos(yaw)]])
    c, s = np.cos(roll), np.sin(roll)
    rz = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
    cam = pts @ (rz @ rx @ ry).T + np.array([0, 0, 1.6 * h])
    uv = cam[:, :2] / cam[:, 2:3]
    span = uv.max(axis=0) - uv.min(axis=0)
    scale = min(0.85 * out_h / span[1], 0.85 * out_w / span[0])
    dst = ((uv - (uv.max(axis=0) + uv.min(axis=0)) / 2) * scale + [out_w / 2, out_h / 2]).astype(
        np.float32
    )

    px_per_pt = scale / (1.6 * h)
    k0 = min(1.0, px_per_pt / (DPI / 72))
    small = cv2.resize(page, None, fx=k0, fy=k0, interpolation=cv2.INTER_AREA).astype(np.float32)
    sh, sw = small.shape
    gx = np.linspace(rng.uniform(0.82, 1.0), rng.uniform(0.82, 1.0), sw)[None, :]
    gy = np.linspace(rng.uniform(0.85, 1.0), rng.uniform(0.85, 1.0), sh)[:, None]
    small = np.clip(small * gx * gy * 0.93, 0, 255)

    src = np.array([[0, 0], [sw - 1, 0], [sw - 1, sh - 1], [0, sh - 1]], np.float32)
    matrix = cv2.getPerspectiveTransform(src, dst)
    table = np.full((out_h, out_w), 60, np.float32)
    mask = cv2.warpPerspective(np.ones_like(small), matrix, (out_w, out_h), flags=cv2.INTER_NEAREST)
    warped = cv2.warpPerspective(small, matrix, (out_w, out_h), flags=cv2.INTER_LINEAR)
    img = np.where(mask > 0, warped, table)
    if blur_sigma > 0:
        img = cv2.GaussianBlur(img, (0, 0), blur_sigma)
    img = img + np.random.default_rng(rng.randrange(1 << 30)).normal(0, noise_sd, img.shape)
    img = np.clip(img, 0, 255).astype(np.uint8)
    _, enc = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, jpeg_q])
    return cv2.imdecode(enc, cv2.IMREAD_GRAYSCALE)


def run_condition(layout, delta, long_side, tilt, blur, trials, save_dir):
    ber_num = ber_den = ok = wrong = 0
    for t in range(trials):
        rng = random.Random(1000 * t + long_side + int(delta * 100))
        copy_id = rng.getrandbits(32)
        frame = encode_payload(copy_id)
        page = l1.rasterize_gray(l1.render_pdf(layout, frame, delta), DPI)
        photo = page if long_side == 0 else simulate_camera(page, long_side, tilt, blur, 80, rng)
        if long_side and save_dir and t == 0:
            cv2.imwrite(str(save_dir / f"d{delta}_L{long_side}_t{tilt}.jpg"), photo)
        flat = photo if long_side == 0 else rectify_page(photo, (page.shape[1], page.shape[0]))
        scores = measure_slot_scores(flat, layout, delta, DPI)
        bits = np.unpackbits(np.frombuffer(frame, dtype=np.uint8))
        for n, s in scores.items():
            ber_den += 1
            ber_num += (s > 0) != bool(bits[n % len(bits)])
        try:
            decoded = decode_scores(scores)[0]
            ok += decoded == copy_id
            wrong += decoded != copy_id
        except PayloadDecodeError:
            pass
        slots = len(scores)
    return ber_num / max(ber_den, 1), ok, wrong, slots


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--trials", type=int, default=8)
    ap.add_argument("--deltas", type=float, nargs="+", default=[0.3, 0.5, 0.8])
    ap.add_argument("--long-sides", type=int, nargs="+", default=[0, 3500, 2400, 1700])
    ap.add_argument("--tilts", type=float, nargs="+", default=[0, 35])
    ap.add_argument("--blur", type=float, default=0.8)
    ap.add_argument("--save-sample", type=Path)
    ap.add_argument("--layout", choices=("spike", "naskah"), default="spike")
    a = ap.parse_args()
    if a.save_sample:
        a.save_sample.mkdir(parents=True, exist_ok=True)

    layout = l1.naskah_layout() if a.layout == "naskah" else l1.spike_layout()
    print(f"tata letak {layout.name}: {layout.total_slots} slot per halaman, bit payload: 104")
    print(f"{'delta(pt)':>9} {'sisi-panjang':>12} {'tilt':>5} {'slot-BER':>9} "
          f"{'pulih':>6} {'salah':>6}")
    for delta, long_side, tilt in itertools.product(a.deltas, a.long_sides, a.tilts):
        if long_side == 0 and tilt != a.tilts[0]:
            continue
        ber, ok, wrong, _ = run_condition(
            layout, delta, long_side, tilt, a.blur, a.trials, a.save_sample
        )
        label = "ideal" if long_side == 0 else str(long_side)
        print(f"{delta:>9} {label:>12} {tilt:>5} {ber:>9.3f} {ok:>3}/{a.trials:<2} {wrong:>6}")
