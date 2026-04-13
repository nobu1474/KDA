"""
Persistent Jones多項式実装
論文 Section 3.2 に基づく
"""

import numpy as np
from typing import List
from functions import (
    build_vr_filtration,
    extract_facet_presence_from_filtration,
    distance_matrix,
)


class PersistentJonesPolynomial:
    """
    Persistent Jones多項式クラス
    
    セグメント集合からVRフィルトレーションを構築し、
    各ファセットに対応するセグメント部分集合のJones多項式を重みとして計算
    """
    
    def __init__(self, curves: List[np.ndarray], segmentation=None):
        """
        Parameters
        ----------
        curves : list of np.ndarray
            3D曲線の集合。各曲線は (n_i, 3) 形の座標配列
        segmentation : callable, optional
            セグメント化関数。デフォルトは隣接ポイント間セグメント
        """
        self.curves = curves
        self.segments = self._segmentize(curves, segmentation)
        self.vr_filtration = None
        self.distances = None
        self.facet_summary_weighted = None

    def _require_weighted_summary(self):
        """重み付きファセット要約が未計算なら計算し、共通参照を返す。"""
        if self.facet_summary_weighted is None:
            self.extract_weighted_barcode(dimension=1)
        return self.facet_summary_weighted

    def _summary_numeric_arrays(self):
        """重み付きファセット要約を数値配列へ変換して返す。"""
        bars = self._require_weighted_summary()
        first_seen = np.array([bar['first_seen_radius'] for bar in bars], dtype=float)
        last_seen = np.array([bar['last_seen_radius'] for bar in bars], dtype=float)
        weights = np.array([bar['weight'] for bar in bars], dtype=float)
        spans = np.array([bar['presence_span'] for bar in bars], dtype=float)
        return first_seen, last_seen, weights, spans
        
    def _segmentize(self, curves, segmentation_func=None):
        """曲線をセグメント化"""
        if segmentation_func is not None:
            return segmentation_func(curves)
        
        # デフォルト：隣接ポイント間をセグメントとする
        segments = []
        for curve in curves:
            for i in range(len(curve) - 1):
                segment = curve[i:i+2]
                segments.append(segment)
        return segments
    
    def build_filtration(self, max_radius=None):
        """VRフィルトレーションを構築"""
        self.vr_filtration, self.distances = build_vr_filtration(
            self.segments, max_radius=max_radius
        )
        return self.vr_filtration
    
    def compute_segment_subset_jones_polynomial(self, segment_indices):
        """
        セグメント部分集合に対応するJones多項式を計算
        
        現在は簡易版：セグメント数に基づいて重みを計算
        正式版では: Jones多項式計算関数を呼び出して実装
        
        Parameters
        ----------
        segment_indices : tuple or list
            セグメントインデックス
            
        Returns
        -------
        weight : float
            セグメント部分集合の複雑さを表す重み
        """
        # 簡易版：セグメント部分集合のサイズに基づく重み
        # 実装：Jones多項式の実際の計算
        # 現在は距離行列を基に複雑さスコアを計算

        if self.distances is None:
            self.distances = distance_matrix(self.segments)
        
        n_segments = len(segment_indices)
        if n_segments == 0:
            return 0.0
        
        # セグメント間の平均距離に基づくスコア
        idx = np.asarray(segment_indices, dtype=int)
        sub = self.distances[np.ix_(idx, idx)]
        tri = np.triu_indices(n_segments, k=1)
        upper_vals = sub[tri]
        avg_distance = float(upper_vals.mean()) if upper_vals.size > 0 else 0.0
        
        # 複雑さスコア：セグメント数と距離のバランス
        complexity_score = -n_segments * avg_distance
        return complexity_score
    
    def extract_weighted_barcode(self, dimension=1):
        """
        重み付きファセット要約を抽出
        
        各 facet に対応するセグメント部分集合の Jones 多項式を重みとして付与
        
        Parameters
        ----------
        dimension : int
            対象次元（1 = エッジ, 2 = 三角形）
            
        Returns
        -------
        weighted_barcode : list of dict
            各要素は {
                'facet': tuple（セグメントインデックス）, 
                'first_seen_radius': float,
                'last_seen_radius': float,
                'presence_span': float,
                'weight': float（Jones多項式の評価値）, 
                'active_stages': int
            }
        """
        if self.vr_filtration is None:
            raise ValueError("filtrationが構築されていません。先にbuild_filtration()を呼び出してください")
        
        summary = extract_facet_presence_from_filtration(
            self.vr_filtration, dimension=dimension
        )
        
        weighted_barcode = []
        for bar in summary:
            facet = bar['facet']
            weight = self.compute_segment_subset_jones_polynomial(facet)
            
            weighted_barcode.append({
                'facet': facet,
                'first_seen_radius': bar['first_seen_radius'],
                'last_seen_radius': bar['last_seen_radius'],
                'presence_span': bar['presence_span'],
                'weight': weight,
                'active_stages': bar['active_stages'],
            })
        
        self.facet_summary_weighted = weighted_barcode
        return weighted_barcode
    
    def get_persistent_diagram(self, dimension=1):
        """
        2次元のファセット要約散布図を取得
        
        各点 (first_seen_radius, presence_span) はファセットの
        フィルトレーション内での出現履歴を表す。
        色に相当する重みはセグメント部分集合の Jones 多項式。
        
        Returns
        -------
        diagram_points : np.ndarray
            (n_facets, 2) 配列。各行は (first_seen_radius, presence_span)
        weights : np.ndarray
            各点の重みベクトル
        facets : list
            各点に対応するファセット
        """
        if self.facet_summary_weighted is None:
            self.extract_weighted_barcode(dimension=dimension)

        bars = self.facet_summary_weighted
        diagram_points = np.array(
            [[bar['first_seen_radius'], bar['presence_span']] for bar in bars],
            dtype=float,
        )
        weights = np.array([bar['weight'] for bar in bars], dtype=float)
        facets = [bar['facet'] for bar in bars]

        return diagram_points, weights, facets
    
    def print_summary(self):
        """合計情報を表示"""
        bars = self._require_weighted_summary()
        first_seen, last_seen, weights, spans = self._summary_numeric_arrays()
        
        print("\n" + "="*70)
        print("Persistent Jones多項式 要約")
        print("="*70)
        
        print(f"\n曲線数: {len(self.curves)}")
        print(f"セグメント数: {len(self.segments)}")
        print(f"フィルトレーションステージ数: {len(self.vr_filtration)}")
        print(f"1-ファセット（要約）数: {len(bars)}")
        
        print(f"\nJones多項式重み統計:")
        print(f"  最小: {weights.min():.6f}")
        print(f"  最大: {weights.max():.6f}")
        print(f"  平均: {weights.mean():.6f}")
        print(f"  標準偏差: {weights.std():.6f}")
        
        print(f"\n出現履歴幅統計:")
        print(f"  最小: {spans.min():.6f}")
        print(f"  最大: {spans.max():.6f}")
        print(f"  平均: {spans.mean():.6f}")
        
        # top 5 長く現れる facet
        print(f"\n最も長く現れる facet TOP 5:")
        sorted_bars = sorted(bars, key=lambda x: x['presence_span'], reverse=True)
        for i, bar in enumerate(sorted_bars[:5]):
            print(
                f"  {i+1}. Facet {bar['facet']}: "
                f"first_seen={bar['first_seen_radius']:.6f}, "
                f"span={bar['presence_span']:.6f}, "
                f"weight={bar['weight']:.6f}"
            )
