import rareeventestimation as ree
import pytest


def test_cbree_lowdim():
    for p in ree.problems_lowdim:
        p.set_sample(5000, seed=5000)
        cbree = ree.CBREE(seed=1, divergence_check=False, verbose=True)
        sol = cbree.solve(p)
        assert sol.get_rel_err(p)[-1] < 0.08, f"Error too large for {p.name}"


@pytest.mark.slow(reason="Ressource intense")
def test_cbree_high():
    for p in [ree.make_fujita_rackwitz(50), ree.make_linear_problem(50)]:
        p.set_sample(5000, seed=5000)
        cbree = ree.CBREE(
            seed=1,
            resample=True,
            mixture_model="vMFNM",
            # cvar_tgt=3,
            verbose=True,
        )
        sol = cbree.solve(p)
        assert sol.get_rel_err(p)[-1] < 0.08, f"Error too large for {p.name}"
