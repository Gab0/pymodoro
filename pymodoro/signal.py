from . import routine_control, session_control, configuration
import math


def sigmoid(x, k=1.2):
    return 1 / (1 + math.exp(-x * k))


def score_to_color(score):
    v = sigmoid(score)

    k = 80
    B = round(v * (255 + k)) - k

    return hex(B)[-2:]


def calculate_colors(score):
    R = -min(0, score)
    G = max(0, score)

    return map(score_to_color, (R, G))


def main():
    required = routine_control.main(Verbose=False)
    done = session_control.check_entries(
        configuration.Config(),
        past_days=1,
        Verbose=0)[-1]

    n_done = len(done)
    score = n_done - required
    R, G = calculate_colors(score)

    S = round(score)

    ss = str(S)
    if len(ss) < 2:
        ss = "+" + ss
    if n_done >= routine_control.DPD * 2:
        ss = "OK"

    print(f"<fc=#{R}{G}22>{ss}</fc>")
    print(score, R, G)
