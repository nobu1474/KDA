import numpy as np
import matplotlib.pyplot as plt


def make_linked_circles(n=100):
    t = np.linspace(0, 2 * np.pi, n)

    circle1 = np.stack([
        np.cos(t),
        np.sin(t),
        np.zeros_like(t)
    ], axis=1)

    circle2 = np.stack([
        np.zeros_like(t) + 0.5,
        np.cos(t),
        np.sin(t)
    ], axis=1)

    return [circle1, circle2]


def make_open_curves(n=50):
    t = np.linspace(0, 1, n)

    curve1 = np.stack([
        t,
        np.sin(2 * np.pi * t),
        np.zeros_like(t)
    ], axis=1)

    curve2 = np.stack([
        t,
        np.cos(2 * np.pi * t),
        0.5 * np.ones_like(t)
    ], axis=1)

    return [curve1, curve2]


def make_braided_curves(n=100):
    t = np.linspace(0, 4 * np.pi, n)

    curve1 = np.stack([
        np.cos(t),
        np.sin(t),
        t / (4 * np.pi)
    ], axis=1)

    curve2 = np.stack([
        np.cos(t + 2 * np.pi / 3),
        np.sin(t + 2 * np.pi / 3),
        t / (4 * np.pi)
    ], axis=1)

    curve3 = np.stack([
        np.cos(t + 4 * np.pi / 3),
        np.sin(t + 4 * np.pi / 3),
        t / (4 * np.pi)
    ], axis=1)

    return [curve1, curve2, curve3]


def add_noise(curves, sigma=0.05, seed=None):
    rng = np.random.default_rng(seed)
    noisy = []
    for curve in curves:
        noise = sigma * rng.normal(size=curve.shape)
        noisy.append(curve + noise)
    return noisy


def _rotation_matrix_xyz(ax, ay, az):
    cx, sx = np.cos(ax), np.sin(ax)
    cy, sy = np.cos(ay), np.sin(ay)
    cz, sz = np.cos(az), np.sin(az)

    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ ry @ rx


def _curve_template(kind, n_points, rng):
    t = np.linspace(0.0, 1.0, n_points)

    if kind == "helix":
        turns = rng.uniform(1.0, 4.0)
        radius = rng.uniform(0.6, 1.2)
        pitch = rng.uniform(0.5, 2.0)
        x = radius * np.cos(2 * np.pi * turns * t)
        y = radius * np.sin(2 * np.pi * turns * t)
        z = pitch * (t - 0.5)
        return np.stack([x, y, z], axis=1)

    if kind == "lissajous3d":
        a, b, c = rng.integers(1, 6, size=3)
        p1, p2, p3 = rng.uniform(0, 2 * np.pi, size=3)
        x = np.sin(2 * np.pi * a * t + p1)
        y = np.sin(2 * np.pi * b * t + p2)
        z = np.sin(2 * np.pi * c * t + p3)
        return np.stack([x, y, z], axis=1)

    if kind == "torus_knot":
        p = int(rng.integers(2, 6))
        q = int(rng.integers(2, 8))
        r_major = rng.uniform(1.4, 2.2)
        r_minor = rng.uniform(0.2, 0.7)
        theta = 2 * np.pi * t
        x = (r_major + r_minor * np.cos(q * theta)) * np.cos(p * theta)
        y = (r_major + r_minor * np.cos(q * theta)) * np.sin(p * theta)
        z = r_minor * np.sin(q * theta)
        return np.stack([x, y, z], axis=1)

    if kind == "random_walk":
        step = rng.normal(size=(n_points, 3))
        walk = np.cumsum(step, axis=0)
        walk -= walk.mean(axis=0, keepdims=True)
        scale = np.maximum(np.std(walk, axis=0, keepdims=True), 1e-8)
        return walk / scale

    if kind == "s_curve":
        x = 2 * t - 1
        y = np.sin(2 * np.pi * t)
        z = 0.5 * np.sin(4 * np.pi * t)
        return np.stack([x, y, z], axis=1)

    raise ValueError(f"Unsupported curve kind: {kind}")


def _random_rigid_transform(curve, rng, scale_range=(0.7, 1.3), shift_range=(-1.0, 1.0)):
    ax, ay, az = rng.uniform(0.0, 2 * np.pi, size=3)
    rot = _rotation_matrix_xyz(ax, ay, az)
    scale = float(rng.uniform(scale_range[0], scale_range[1]))
    shift = rng.uniform(shift_range[0], shift_range[1], size=3)
    return (curve @ rot.T) * scale + shift


def generate_curve_group(
    n_curves,
    n_points,
    kinds=None,
    noise_sigma=0.0,
    seed=None,
):
    """
    (N,3) 形状の曲線を複数本生成し、list[np.ndarray] を返す。

    Args:
        n_curves: 1つの曲線群に含める曲線本数。
        n_points: 各曲線の点数 N。
        kinds: 使用するテンプレート名の候補。
        noise_sigma: ガウスノイズ標準偏差。
        seed: 乱数シード。
    """
    if kinds is None:
        kinds = ["helix", "lissajous3d", "torus_knot", "random_walk", "s_curve"]

    rng = np.random.default_rng(seed)
    curves = []
    for _ in range(n_curves):
        kind = kinds[int(rng.integers(0, len(kinds)))]
        curve = _curve_template(kind, n_points=n_points, rng=rng)
        curve = _random_rigid_transform(curve, rng=rng)
        if noise_sigma > 0:
            curve += noise_sigma * rng.normal(size=curve.shape)
        curves.append(curve.astype(np.float64))

    return curves


def generate_curve_group_dataset(
    n_groups,
    n_curves,
    n_points,
    kinds=None,
    noise_sigma=0.0,
    seed=None,
):
    """
    曲線群データセットを生成する。

    Returns:
        list[list[np.ndarray]]
        外側: 曲線群 index
        内側: 各曲線群に含まれる曲線（各要素が (N,3) 配列）
    """
    rng = np.random.default_rng(seed)
    dataset = []
    for _ in range(n_groups):
        group_seed = int(rng.integers(0, 2**31 - 1))
        group = generate_curve_group(
            n_curves=n_curves,
            n_points=n_points,
            kinds=kinds,
            noise_sigma=noise_sigma,
            seed=group_seed,
        )
        dataset.append(group)
    return dataset


def plot_curves(curves):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    for curve in curves:
        ax.plot(curve[:, 0], curve[:, 1], curve[:, 2])

    plt.show()


if __name__ == "__main__":
    curves = generate_curve_group(n_curves=4, n_points=200, noise_sigma=0.01, seed=42)
    plot_curves(curves)

