import random
def genotp():
    otp=""
    u_l=[chr(I) for I in range(ord('A'),ord('Z')+1)]
    s_l=[chr(I) for I in range(ord('a'),ord('z')+1)]
    for I in range(2):

        otp=otp+random.choice(u_l)+str(random.randint(0,9))+random.choice(s_l)
    return otp