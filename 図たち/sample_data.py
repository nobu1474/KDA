# 2つの円

import numpy as np

def make_linked_circles(n=100):
    t = np.linspace(0, 2*np.pi, n)

    # xy平面の円
    circle1 = np.stack([
        np.cos(t),
        np.sin(t),
        np.zeros_like(t)
    ], axis=1)

    # yz平面の円（少しずらす）
    circle2 = np.stack([
        np.zeros_like(t) + 0.5,
        np.cos(t),
        np.sin(t)
    ], axis=1)

    return [circle1, circle2]



# 開曲線（linkoidらしい例）

def make_open_curves(n=50):
    t = np.linspace(0, 1, n)

    curve1 = np.stack([
        t,
        np.sin(2*np.pi*t),
        np.zeros_like(t)
    ], axis=1)

    curve2 = np.stack([
        t,
        np.cos(2*np.pi*t),
        0.5*np.ones_like(t)
    ], axis=1)

    return [curve1, curve2]





# 三つ編み風（交差多め）

def make_braided_curves(n=100):
    t = np.linspace(0, 4*np.pi, n)

    curve1 = np.stack([
        np.cos(t),
        np.sin(t),
        t / (4*np.pi)
    ], axis=1)

    curve2 = np.stack([
        np.cos(t + 2*np.pi/3),
        np.sin(t + 2*np.pi/3),
        t / (4*np.pi)
    ], axis=1)

    curve3 = np.stack([
        np.cos(t + 4*np.pi/3),
        np.sin(t + 4*np.pi/3),
        t / (4*np.pi)
    ], axis=1)

    return [curve1, curve2, curve3]



# ノイズ付き（現実データ風）

def add_noise(curves, sigma=0.05):
    noisy = []
    for c in curves:
        noise = sigma * np.random.randn(*c.shape)
        noisy.append(c + noise)
    return noisy



# 可視化（おすすめ）
import matplotlib.pyplot as plt

def plot_curves(curves):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    for c in curves:
        ax.plot(c[:,0], c[:,1], c[:,2])

    plt.show()


# curves = make_linked_circles()
curves = make_open_curves()
# curves = make_braided_curves()

#curves = add_noise(make_linked_circles())

# plot_curves(curves)


