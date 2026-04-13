"""
Persistent Jones多項式 実装テスト
"""

import numpy as np
import matplotlib.pyplot as plt
from persistent_jones_polynomial import PersistentJonesPolynomial

# シンプルなテスト曲線を作成
np.random.seed(42)
t = np.linspace(0, 2*np.pi, 40)

# 円形曲線
curve1 = np.stack([
    np.cos(t),
    np.sin(t),
    0.1 * np.sin(3*t)  # 若干の高さの変動
], axis=1)

# ずらした円形曲線
curve2 = np.stack([
    0.5 + 0.3 * np.cos(t),
    0.3 * np.sin(t),
    0.5 * np.ones_like(t)
], axis=1)

curves = [curve1, curve2]

print("="*70)
print("Persistent Jones多項式 実装テスト")
print("="*70)

# Persistent Jones多項式を構築
pjp = PersistentJonesPolynomial(curves)

# VRフィルトレーション構築
print("\nVRフィルトレーションを構築中...")
vr_filtration = pjp.build_filtration(max_radius=1.2)

print(f"VRフィルトレーションステージ数: {len(vr_filtration)}")

# 重み付き要約抽出
print("\n重み付きファセット要約を抽出中...")
weighted_barcode = pjp.extract_weighted_barcode(dimension=1)

print(f"1-ファセット（要約）数: {len(weighted_barcode)}")

# 2次元要約取得
print("\n2次元要約を計算中...")
diagram_points, weights, facets = pjp.get_persistent_diagram(dimension=1)

print(f"Diagram points shape: {diagram_points.shape}")
print(f"Weights shape: {weights.shape}")

# 合計情報表示
pjp.print_summary()

# Top 10 バーの詳細表示
print("\n" + "="*70)
print("1-ファセット 要約の詳細（上位10個）:")
print("="*70)
sorted_bars = sorted(weighted_barcode, key=lambda x: x['presence_span'], reverse=True)

for i, bar in enumerate(sorted_bars[:10]):
    print(f"\nFacet {i+1}:")
    print(f"  Facet (segments): {bar['facet']}")
    print(f"  First seen:  {bar['first_seen_radius']:.6f}")
    print(f"  Last seen:   {bar['last_seen_radius']:.6f}")
    print(f"  Span:        {bar['presence_span']:.6f}")
    print(f"  Weight:   {bar['weight']:.6f}")

# 2次元要約をテキストベースで確認
print("\n" + "="*70)
print("Facet Summary 統計:")
print("="*70)

first_seen = diagram_points[:, 0]
spans = diagram_points[:, 1]

print(f"\nFirst seen 値:")
print(f"  Min: {first_seen.min():.6f}")
print(f"  Max: {first_seen.max():.6f}")
print(f"  Mean: {first_seen.mean():.6f}")

print(f"\nSpan 値:")
print(f"  Min: {spans.min():.6f}")
print(f"  Max: {spans.max():.6f}")
print(f"  Mean: {spans.mean():.6f}")

print(f"\n重み（Jones多項式）:")
print(f"  Min: {weights.min():.6f}")
print(f"  Max: {weights.max():.6f}")
print(f"  Mean: {weights.mean():.6f}")

# Persistent diagram を2D散布図として保存（オプション）
try:
    import matplotlib.pyplot as plt
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    
    # Facet summary scatter
    ax = axes[0]
    scatter = ax.scatter(first_seen, spans, c=weights, cmap='viridis', s=100, alpha=0.6)
    ax.set_xlabel('First seen')
    ax.set_ylabel('Span')
    ax.set_title('Facet Summary (1-Facets)')
    plt.colorbar(scatter, ax=ax, label='Weight (Jones Polynomial)')
    
    # Span 分布
    ax = axes[1]
    ax.hist(spans, bins=30, alpha=0.7, color='steelblue', edgecolor='black')
    ax.set_xlabel('Span')
    ax.set_ylabel('Frequency')
    ax.set_title('Span Distribution')
    
    plt.tight_layout()
    plt.savefig('/Users/nobu/KDA/persistent_diagram.png', dpi=150, bbox_inches='tight')
    print("\n✅ Facet summary 図を保存: persistent_diagram.png")
    
except Exception as e:
    print(f"\n注意: 図の保存に失敗しました: {e}")

print("\n✅ Persistent Jones多項式テスト完了")
