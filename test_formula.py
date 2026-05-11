import math

def formula(m, t_val):
    num1 = - (t_val**2.5) * (t_val**1.5)**(m-1)
    num2 = (t_val**2.5 + t_val**1.5 + t_val**0.5) * (- t_val**0.5)**(m-1)
    den = t_val**0.5 + t_val**1.5
    return (num1 + num2) / den

for m in [2, 4, 6]:
    print(f"m={m}, t=2: {formula(m, 2.0)}")
