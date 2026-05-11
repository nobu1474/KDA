def divide_by_t_plus_1(m):
    # num: -t^((3m+1)/2) + t^((m-1)/2) (t^2+t+1) (-1)^(m-1)
    # let offset = (m-1)/2 if it's smaller. Actually just use dict with integer keys for half-integer exponents (multiply by 2)
    # let P = -t^(3m+1) ... no, P(t) = num / t^(some_power). Let's just use array of coefficients.
    degree = (3*m+1) // 2
    coeffs = [0] * (degree + 1)
    # let's set num coefficients
    coeffs[degree] = -1
    if m % 2 == 0:
        sign = -1
    else:
        sign = 1
    # + sign * t^((m-1)/2) (t^2 + t + 1)
    base = (m-1) // 2
    coeffs[base + 2] += sign
    coeffs[base + 1] += sign
    coeffs[base] += sign
    
    # divide by t+1
    # since we know it exactly divides:
    ans = [0] * degree
    for i in range(degree, 0, -1):
        ans[i-1] = coeffs[i]
        coeffs[i-1] -= ans[i-1]
    
    # print string
    terms = []
    for p, c in enumerate(ans):
        if c == 0: continue
        power = p
        sign_str = '+' if c > 0 else '-'
        if abs(c) == 1:
            c_str = ''
        else:
            c_str = str(abs(c))
        
        # we reverse the index
        rev_power = - (power * 2 + 1) # wait, what was the actual t power? It's half-integer + 1/2?
        # we mapped x to x - 1/2 ?? No.
        # the original powers are integers + half.
        # we factored out some half integer?
        pass

import math
for m in [2, 4, 6]:
    num_t_pow = (3*m+1)//2
    # print user formula output
    num = [0] * (num_t_pow + 1)
    num[num_t_pow] = -1
    pw2 = (m-1)// 2
    # The term is t^((m-1)/2)(t^2+t+1)(-1)^(m-1)
    c = -1 if m % 2 == 0 else 1
    num[pw2+2] += c
    num[pw2+1] += c
    num[pw2] += c
    
    # divide by 1 + t
    ans = [0]*num_t_pow
    for i in range(num_t_pow, 0, -1):
        ans[i-1] = num[i]
        num[i-1] -= ans[i-1]
        
    print(f"m={m}:")
    for i, coeff in enumerate(ans):
        if coeff != 0:
            # actual power: i + 0.5. reverse it: -(i + 0.5) = -(2i+1)/2
            print(f"  {coeff}*t^({-(2*i+1)}/2)")
