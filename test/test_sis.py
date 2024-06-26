import rareeventestimation as ree
import pytest


def test_sis_lowdim():
    for m in ["vMFNM", "GM", "aCS"]:
        for p in ree.problems_lowdim:
            print(p.name)
            p.set_sample(5000, seed=5000)
            sis = ree.SIS(seed=1, mixture_model=m)
            sol = sis.solve(p)
            print(sol.get_rel_err(p)[-1])
            print(sol.costs)
            assert sol.get_rel_err(p)[-1] < 0.3, f"Error too large for {p.name}"


@pytest.mark.slow(reason="Ressource intense")
def test_sis_highdim():
    for m in ["vMFNM", "GM", "aCS"]:
        for p in [ree.make_fujita_rackwitz(50), ree.make_linear_problem(50)]:
            print(p.name)
            p.set_sample(5000, seed=5000)
            sis = ree.SIS(seed=1, mixture_model=m)
            sol = sis.solve(p)
            assert sol.get_rel_err(p)[-1] < 0.3, f"Error too large for {p.name}"
            print(sol.get_rel_err(p)[-1])
            print(sol.costs)
