
def color(list pals, list t1data, list t2data):
    col1data = []
    col2data = []
    for c in pals:
        colored1 = [c[i] for i in t1data]
        col1data.append(colored1)
        colored2 = [c[i] for i in t2data]
        col2data.append(colored2)
    return col1data, col2data

