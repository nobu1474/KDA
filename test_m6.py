def formula_expanded_reversed(m):
    # Returns the list of terms with reversed t exponents.
    # formula = ( -t^((3m+1)/2) + t^((m-1)/2) (t^2+t+1) * (-1)^(m-1) ) / (t+1)
    pass
# Actually let's just do m=6 formula:
# num: -t^(19/2) - t^(5/2)(t^2+t+1)
# =  -t^(19/2) - t^(9/2) - t^(7/2) - t^(5/2)
# div by (t+1):
# t^9 + t^4 + t^3 + t^2 divided by t+1
# t^9+1 + t^2(t^2+t+1) - 1 ... wait, sympy is not available.
