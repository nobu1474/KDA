"""
VRフィルトレーション実装の簡易テスト
"""

import numpy as np
from functions import (
    build_vr_filtration, 
    extract_facet_presence_from_filtration,
    print_vr_filtration_summary,
    distance_matrix,
)

# シンプルなテスト曲線を作成
np.random.seed(42)
t = np.linspace(0, 2*np.pi, 30)

# 円形曲線
curve1 = np.stack([
    np.cos(t),
    np.sin(t),
    np.zeros_like(t)
], axis=1)

# ずらした円形曲線
curve2 = np.stack([
    0.5 + 0.3 * np.cos(t),
    0.3 * np.sin(t),
    0.5 * np.ones_like(t)
], axis=1)

curves = [curve1, curve2]

# セグメント化
segments = []
for curve in curves:
    for i in range(len(curve) - 1):
        segment = curve[i:i+2]
        segments.append(segment)

print("="*70)
print("VRフィルトレーション テスト")
print("="*70)
print(f"\n接続された曲線数: {len(curves)}")
print(f"セグメント数: {len(segments)}")
print(f"セグメント形状例: {segments[0].shape}")

# VRフィルトレーション構築
print("\nVRフィルトレーションを構築中...")
vr_filtration = build_vr_filtration(segments, max_radius=1.0)
distances = distance_matrix(segments)

# 概要表示
print_vr_filtration_summary(vr_filtration)

# 要約抽出
facet_summary_1d = extract_facet_presence_from_filtration(vr_filtration, dimension=1)

print("\n" + "="*70)
print("1-ファセット（エッジ）出現要約:")
print("="*70)
for i, bar in enumerate(facet_summary_1d[:10]):
    print(f"\nFacet {i}: 頂点 {bar['facet']}")
    print(f"  First seen:  {bar['first_seen_radius']:.6f}")
    print(f"  Last seen:   {bar['last_seen_radius']:.6f}")
    print(f"  Span:        {bar['presence_span']:.6f}")
    print(f"  Stages:      {bar['active_stages']}")

if len(facet_summary_1d) > 10:
    print(f"\n... ({len(facet_summary_1d) - 10} その他)")

# 距離行列統計
print("\n" + "="*70)
print("セグメント間距離統計:")
print("="*70)
print(f"最小距離: {distances[distances > 0].min():.6f}")
print(f"最大距離: {distances.max():.6f}")
print(f"平均距離: {distances[distances > 0].mean():.6f}")
print(f"中央距離: {np.median(distances[distances > 0]):.6f}")

print("\n✅ VRフィルトレーション構築完了")
