from snappy import Manifold

# 結び目補空間の指定（例：4_1結び目）
M = Manifold('4_1')

# 双曲体積の計算
volume = M.volume()
print(volume)