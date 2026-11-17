"""Procedural textures for the Quicreate guide book: seamless category backgrounds, parallax star layers and
planet portraits. Everything is generated from noise, so there is nothing copied from other mods or Mojang.

    python guide/book/textures.py <assets/quicreate/textures/gui/book>
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

S = 512


def noise(shape, scale, seed, power=2.0):
    """Seamless fractal noise: random spectrum shaped by 1/f^power, inverse FFT (periodic by construction)."""
    rng = np.random.default_rng(seed)
    h, w = shape
    fy = np.fft.fftfreq(h)[:, None]
    fx = np.fft.fftfreq(w)[None, :]
    f = np.sqrt(fx * fx + fy * fy)
    f[0, 0] = 1
    amp = 1.0 / (f * scale) ** power
    amp[0, 0] = 0
    ph = rng.uniform(0, 2 * np.pi, (h, w))
    spec = amp * np.exp(1j * ph)
    n = np.real(np.fft.ifft2(spec))
    n -= n.min()
    n /= n.max() or 1
    return n


def ramp(n, stops):
    """Map 0..1 noise to colours through (pos, (r,g,b)) stops."""
    pos = np.array([s[0] for s in stops])
    cols = np.array([s[1] for s in stops], dtype=float)
    out = np.zeros(n.shape + (3,))
    for c in range(3):
        out[..., c] = np.interp(n, pos, cols[:, c])
    return out


def save(arr, path, alpha=None):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    if alpha is not None:
        a = np.clip(alpha, 0, 255).astype(np.uint8)
        img = Image.fromarray(np.dstack([arr, a]), 'RGBA')
    else:
        img = Image.fromarray(arr, 'RGB')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def pixelate(arr, f=2):
    """Chunky look that sits with Minecraft textures."""
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    img = img.resize((S // f, S // f), Image.BILINEAR).resize((S, S), Image.NEAREST)
    return np.asarray(img).astype(float)


def craters(arr, seed, count, rmin, rmax, dark=0.75, rim=1.12):
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:S, 0:S]
    for _ in range(count):
        cx, cy, r = rng.uniform(0, S), rng.uniform(0, S), rng.uniform(rmin, rmax)
        for ox in (-S, 0, S):
            for oy in (-S, 0, S):
                d = np.sqrt((xx - cx - ox) ** 2 + (yy - cy - oy) ** 2) / r
                inside = d < 1
                ring = (d >= 1) & (d < 1.18)
                arr[inside] *= (dark + (1 - dark) * d[inside] ** 2)[:, None]
                arr[ring] *= rim
    return arr


def stars(seed, count, size_max, bright):
    rng = np.random.default_rng(seed)
    a = np.zeros((S, S))
    rgb = np.zeros((S, S, 3))
    for _ in range(count):
        x, y = rng.integers(0, S), rng.integers(0, S)
        s = rng.integers(1, size_max + 1)
        tint = rng.choice([(255, 255, 255), (200, 220, 255), (255, 235, 200), (255, 210, 230)])
        b = rng.uniform(0.5, 1.0) * bright
        for dx in range(s):
            for dy in range(s):
                a[(y + dy) % S, (x + dx) % S] = 255 * b
                rgb[(y + dy) % S, (x + dx) % S] = tint
        if s >= 2 and rng.random() < 0.4:      # little cross sparkle
            for d in (-1, s):
                a[(y + s // 2) % S, (x + d) % S] = 140 * b
                a[(y + d) % S, (x + s // 2) % S] = 140 * b
                rgb[(y + s // 2) % S, (x + d) % S] = tint
                rgb[(y + d) % S, (x + s // 2) % S] = tint
    return rgb, a


def backgrounds(out):
    bg = os.path.join(out, 'background')
    # --- The Sky: deep blue with soft clouds
    n = noise((S, S), 3, 1, 2.2)
    sky = ramp(n, [(0, (24, 44, 74)), (0.55, (36, 64, 101)), (0.75, (70, 101, 140)), (1, (118, 146, 180))])
    save(pixelate(sky, 4), f'{bg}/sky.png')
    # --- Sifting: sand and gravel grains
    n = 0.6 * noise((S, S), 4, 2, 1.6) + 0.4 * np.random.default_rng(3).random((S, S))
    sand = ramp(n, [(0, (58, 46, 30)), (0.5, (82, 66, 42)), (1, (110, 92, 60))])
    save(pixelate(sand, 2), f'{bg}/sifting.png')
    # --- New Age: dark copper with verdigris
    n = noise((S, S), 2, 4, 1.9)
    m = noise((S, S), 1, 5, 1.3)
    cu = ramp(n, [(0, (44, 26, 20)), (0.6, (78, 44, 30)), (1, (112, 64, 40))])
    cu = cu * (1 - 0.5 * (m > 0.8)[..., None]) + np.array([40, 92, 82]) * 0.5 * (m > 0.8)[..., None]
    save(pixelate(cu, 2), f'{bg}/new_age.png')
    # --- Improvements: steel plates with rivets
    n = noise((S, S), 2, 6, 1.5)
    st = ramp(n, [(0, (38, 44, 46)), (1, (66, 74, 76))])
    for k in range(0, S, 64):
        st[k:k + 2, :] *= 0.6
        st[:, k:k + 2] *= 0.6
        for j in range(0, S, 64):
            for (dx, dy) in ((8, 8), (54, 8), (8, 54), (54, 54)):
                st[k + dy:k + dy + 3, j + dx:j + dx + 3] = (110, 118, 120)
    save(pixelate(st, 2), f'{bg}/improvements.png')
    # --- Space and planets share a starfield parallax
    space = ramp(noise((S, S), 2, 7, 2.3), [(0, (6, 8, 20)), (0.7, (14, 16, 38)), (1, (34, 22, 56))])
    save(space, f'{bg}/space.png')
    rgb, a = stars(8, 260, 1, 0.8)
    save(rgb, f'{bg}/stars_far.png', a)
    rgb, a = stars(9, 70, 2, 1.0)
    save(rgb, f'{bg}/stars_near.png', a)
    # --- Moon: grey regolith, craters
    n = noise((S, S), 3, 10, 1.8)
    moon = ramp(n, [(0, (54, 56, 62)), (0.5, (78, 80, 88)), (1, (104, 106, 114))])
    moon = craters(moon, 11, 28, 10, 46)
    save(pixelate(moon, 2), f'{bg}/moon.png')
    # --- Mars: rust dunes
    n = noise((S, S), 3, 12, 2.0)
    d = (np.sin(np.mgrid[0:S, 0:S][1] / S * 2 * np.pi * 6 + n * 9) + 1) / 2
    mars = ramp(0.65 * n + 0.35 * d, [(0, (66, 24, 16)), (0.5, (104, 40, 24)), (1, (140, 62, 36))])
    mars = craters(mars, 13, 8, 10, 30, 0.8, 1.06)
    save(pixelate(mars, 2), f'{bg}/mars.png')
    # --- Venus & Mercury: sulphur haze swirls
    yy, xx = np.mgrid[0:S, 0:S] / S * 2 * np.pi
    n = noise((S, S), 2, 14, 2.1)
    sw = (np.sin(xx * 3 + n * 8) * np.cos(yy * 2 + n * 6) + 1) / 2
    ven = ramp(0.5 * n + 0.5 * sw, [(0, (70, 40, 12)), (0.5, (118, 72, 20)), (1, (160, 112, 40))])
    save(pixelate(ven, 2), f'{bg}/venus.png')
    # --- Glacio: ice with cracks
    n = noise((S, S), 3, 15, 1.8)
    c = noise((S, S), 1.5, 16, 1.2)
    ice = ramp(n, [(0, (30, 58, 78)), (0.6, (52, 92, 116)), (1, (96, 140, 160))])
    crack = np.abs(c - 0.5) < 0.012
    ice[crack] = (170, 210, 225)
    save(pixelate(ice, 2), f'{bg}/glacio.png')
    # --- Creative: nebula
    n1, n2 = noise((S, S), 2, 17, 2.2), noise((S, S), 2, 18, 2.2)
    neb = ramp(n1, [(0, (12, 8, 24)), (0.6, (40, 16, 60)), (1, (110, 40, 120))])
    neb += ramp(n2, [(0, (0, 0, 0)), (0.7, (0, 0, 0)), (1, (30, 80, 110))])
    save(neb, f'{bg}/creative.png')
    # --- Side paths
    n = noise((S, S), 2, 19, 1.7)
    bricks = ramp(n, [(0, (46, 44, 42)), (1, (74, 70, 66))])
    for y in range(0, S, 32):
        bricks[y:y + 2, :] *= 0.55
        off = 0 if (y // 32) % 2 == 0 else 32
        for x in range(off, S + 64, 64):
            bricks[y:y + 32, x % S:(x % S) + 2] *= 0.55
    save(pixelate(bricks, 2), f'{bg}/builders.png')
    n = noise((S, S), 2, 20, 2.0)
    topo = ramp(n, [(0, (36, 44, 34)), (1, (62, 72, 52))])
    lines = (np.abs((n * 14) % 1 - 0.5) < 0.05)
    topo[lines] *= 1.35
    save(pixelate(topo, 2), f'{bg}/explorer.png')
    n = noise((S, S), 4, 21, 1.4)
    leather = ramp(n, [(0, (48, 20, 16)), (1, (84, 36, 28))])
    save(pixelate(leather, 2), f'{bg}/bestiary.png')
    n = noise((S, S), 2, 22, 1.8)
    brass = ramp(n, [(0, (54, 40, 16)), (1, (98, 76, 34))])
    yy, xx = np.mgrid[0:S, 0:S]
    for (cx, cy, r) in ((128, 128, 70), (384, 384, 90), (384, 110, 40), (110, 400, 50)):
        d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
        ang = np.arctan2(yy - cy, xx - cx)
        teeth = r + 8 * (np.sin(ang * 12) > 0)
        ring = (d < teeth) & (d > r * 0.45)
        brass[ring] *= 1.22
    save(pixelate(brass, 2), f'{bg}/workshop.png')
    n = noise((S, S), 3, 23, 1.7)
    kitchen = ramp(n, [(0, (34, 46, 24)), (1, (66, 82, 40))])
    save(pixelate(kitchen, 2), f'{bg}/kitchen.png')
    n = noise((S, S), 6, 24, 1.2)
    felt = ramp(n, [(0, (18, 52, 40)), (1, (32, 78, 60))])
    save(pixelate(felt, 2), f'{bg}/cards.png')
    n = noise((S, S), 2, 25, 1.9)
    hub = ramp(n, [(0, (40, 32, 24)), (1, (72, 58, 42))])
    save(pixelate(hub, 2), f'{bg}/side_paths.png')


def planet(path, seed, stops, bands=0.0, craters_n=0, ice_caps=False, clouds=False, glow=(255, 255, 255)):
    """256x256 texture, planet drawn in the upper-left 200x200 (Patchouli-style image page)."""
    R = 200
    n = noise((R, R), 2, seed, 1.9)
    yy, xx = np.mgrid[0:R, 0:R]
    if bands:
        n = 0.5 * n + 0.5 * (np.sin(yy / R * np.pi * bands + n * 4) + 1) / 2
    col = ramp(n, stops)
    if craters_n:
        rng = np.random.default_rng(seed + 1)
        for _ in range(craters_n):
            cx, cy, r = rng.uniform(20, 180), rng.uniform(20, 180), rng.uniform(4, 16)
            d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
            col[d < 1] *= 0.78
            col[(d >= 1) & (d < 1.2)] *= 1.1
    if ice_caps:
        cap = (yy < 26 + 6 * np.sin(xx / 13)) | (yy > 174 + 6 * np.sin(xx / 17))
        col[cap] = col[cap] * 0.3 + np.array([230, 238, 245]) * 0.7
    if clouds:
        c = noise((R, R), 2, seed + 7, 2.2)
        m = np.clip((c - 0.55) * 3, 0, 1)[..., None]
        col = col * (1 - m) + 240 * m
    cx = cy = R / 2
    rad = R / 2 - 8
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    nx, ny = (xx - cx) / rad, (yy - cy) / rad
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0, 1))
    light = np.clip(0.25 + 0.85 * (-0.55 * nx - 0.45 * ny + 0.7 * nz), 0.12, 1.15)
    col = col * light[..., None]
    alpha = np.where(d <= rad, 255, 0).astype(float)
    halo = (d > rad) & (d < rad + 5)
    col[halo] = glow
    alpha[halo] = 90 * (1 - (d[halo] - rad) / 5)
    img = np.zeros((256, 256, 4))
    img[:R, :R, :3] = col
    img[:R, :R, 3] = alpha
    # pixel-art feel
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8), 'RGBA')
    small = pil.resize((128, 128), Image.BILINEAR)
    pil = small.resize((256, 256), Image.NEAREST)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pil.save(path, optimize=True)


def planets(out):
    p = os.path.join(out, 'planet')
    planet(f'{p}/island.png', 31, [(0, (24, 60, 120)), (0.55, (40, 96, 160)), (0.6, (70, 130, 60)), (1, (120, 160, 80))], clouds=True,
           glow=(170, 210, 255))
    planet(f'{p}/moon.png', 32, [(0, (90, 92, 100)), (1, (190, 192, 200))], craters_n=26)
    planet(f'{p}/mars.png', 33, [(0, (110, 40, 20)), (0.6, (180, 80, 40)), (1, (220, 130, 80))], craters_n=8, ice_caps=True,
           glow=(255, 160, 120))
    planet(f'{p}/venus.png', 34, [(0, (150, 100, 30)), (1, (240, 200, 110))], bands=7, clouds=True, glow=(255, 220, 140))
    planet(f'{p}/mercury.png', 35, [(0, (70, 60, 58)), (1, (160, 140, 130))], craters_n=34, glow=(255, 200, 160))
    planet(f'{p}/glacio.png', 36, [(0, (70, 120, 150)), (0.6, (150, 200, 220)), (1, (230, 245, 250))], ice_caps=True, clouds=True,
           glow=(190, 230, 255))
    planet(f'{p}/creative.png', 37, [(0, (60, 20, 90)), (0.5, (160, 60, 170)), (1, (90, 210, 230))], bands=4, glow=(255, 180, 255))


if __name__ == '__main__':
    out = sys.argv[1]
    backgrounds(out)
    planets(out)
    print('textures written to', out)
