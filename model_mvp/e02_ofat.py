"""E02: one-factor-at-a-time scan around the baseline, 6 seeds each."""
from exp import run_grid

if __name__ == "__main__":
    base = dict(t_end=450.0, v_div=1.25)
    V = {"baseline": {}}
    for w in (1.5, 2.5, 3.0, 3.5):
        V[f"w={w}"] = dict(w=w)
    for g in (0.015, 0.02, 0.045, 0.06):
        V[f"gamma={g}"] = dict(gamma=g, t_end=450.0 * 0.03 / g)
    for th in (6.5, 7.5, 9.5):
        V[f"Th={th}"] = dict(Th=th)
    for b in (2.0, 4.0):
        V[f"b={b}"] = dict(b=b)
    for eta in (1.0, 6.0):
        V[f"eta={eta}"] = dict(eta=eta)
    for aq in (4.0, 12.0):
        V[f"A_q={aq}"] = dict(A_q=aq)
    for rc in (3.0, 5.0, 6.0):
        V[f"ring={rc}-{rc+2}"] = dict(R_c=rc, R_p=rc + 2.0, R_out=12.0 + (rc - 4.0) * 2)
    for D in (2.0, 8.0):
        V[f"D={D}"] = dict(D=D)
    for mu in (0.15, 0.6):
        V[f"mu={mu}"] = dict(mu=mu, rho_pz=18.0 * mu / 0.3, rho_cz=9.0 * mu / 0.3, rho_prox=9.0 * mu / 0.3, eta=3.0 * mu / 0.3)
    V["start=pair"] = dict(start="pair", init_frac=1.0)
    V["rex=2"] = dict(r_ex=2.0)
    V["rex=4"] = dict(r_ex=4.0)
    run_grid(V, seeds=range(1, 7), base=base, out="out/e02.jsonl", show_runs=False)
