"""N08 (candidate 5): the central zone as a shared, well-mixed auxin pool.

If all ring positions draw on one reservoir, an initiation at one azimuth lowers the supply
everywhere at once. Question: does that give the refractory period that the artificial
ring-wide secondary field provided (N02/N03), without that field?

The threshold is tied to the sink-free ring level (Th_rel) because these variants move it.
"""
import nexp

if __name__ == "__main__":
    T = dict(Th_rel=0.82)
    V = {
        "ref (no pool, no field)": dict(T),
        "mixed CZ": dict(T, cz_mix=1),
        "mixed CZ, low CZ PIN": dict(T, cz_mix=1, pin_cz=0.1),
        "mixed CZ, low PIN, exchange x3": dict(T, cz_mix=1, pin_cz=0.1, D_x=3.0),
        "CZ supplies (18/6), low PIN": dict(T, cz_mix=1, pin_cz=0.1, rho_cz=18.0, rho_pz=6.0),
        "CZ supplies (18/6), exch x3": dict(T, cz_mix=1, pin_cz=0.1, rho_cz=18.0, rho_pz=6.0, D_x=3.0),
        "CZ and ring equal (12/12)": dict(T, cz_mix=1, pin_cz=0.1, rho_cz=12.0, rho_pz=12.0),
        "CZ supplies (18/6), not mixed": dict(T, pin_cz=0.1, rho_cz=18.0, rho_pz=6.0),
    }
    nexp.run(V, ["lowG", "spiral"], range(1, 11), "out/n08.jsonl")
