#!/bin/python


def colorRainbow(timefraction):
    Stage = timefraction / 10 * 70
    if Stage > 4:
        R = 1
    elif Stage < 2:
        R = 0.2
    else:
        R = timefraction ** 2
    G = max(0, -(1.5 - 3 * timefraction) ** 2 + 1.6)
    B = 1 if timefraction < 3/7 else (1-timefraction) ** 2

    def t(x):
        x = min(1, x)
        V = hex(int(255 * x))[2:]
        if len(V) < 2:
            V = '0' + V
        return V

    return(t(R), t(G), t(B))


def colorFaintRed(timefraction):
    R = int(255 * timefraction)
    R = hex(R)[2:]
    G = '00'
    B = '00'
    return (R, G, B)


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    for fcolor in [
            colorRainbow,
            colorFaintRed]:
        for x in range(20, -1, -1):
            x = x / 20
            plt.scatter(x=x, y=0, color="#" + "".join(fcolor(x)))

        plt.show()
