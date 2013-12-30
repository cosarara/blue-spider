
def color(list pals, list t1data, list t2data):
    palette = [i for i in range(16)]
    col1data = []
    col2data = []
    for pal in pals:
        c = {}
        for i in range(16):
            c[i] = pal[i]
        colored1 = [c[i] if i in c else (0, 0, 0) for i in t1data]
        col1data.append(colored1)
        colored2 = [c[i] if i in c else (0, 0, 0) for i in t2data]
        col2data.append(colored2)
    return col1data, col2data
