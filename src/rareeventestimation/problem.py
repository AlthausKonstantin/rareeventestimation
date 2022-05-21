
#TODO: change e_fun to logpdf

from typing import Callable

from numpy import apply_along_axis, array, ndarray, ndenumerate, zeros, nan, prod, eye, ones, sqrt, sum, diff, amin, log, exp
from scipy.stats import multivariate_normal, norm, gamma

from rareeventestimation.era.ERANataf import ERANataf
from rareeventestimation.era.ERADist import ERADist
from rareeventestimation.utilities import gaussian_logpdf

class Problem:
    """"The Problem class formulates a rare event estimation problem."""
    
    def __init__(self, lsf: Callable, e_fun: Callable, sample: ndarray, sample_gen=None, prob_fail_true=None, mpp=None, eranataf_dist=None, hints=None, name=None):
        """Make an instance of the Problem class.

        Args:
            lsf (Callable):  Handle to limit state function.
            e_fun (Callable): Energy function of target distribution, i.e. the negative logarithm of the pdf without normalization.
            sample (ndarray): Sample of the target distribution. Each row is one sample
            sample_gen ([calable], optional): Handle to generate a sample of target distribution. Takes sample size as its only argument and an optional kwarg seed. Defaults to None.
            prob_fail_true ([float], optional): True probability of failure. If provided error plos can be made. Defaults to None.
            eranataf_dist ([type], optional): Target distribution as an instance of the ERANataf class. Defaults to None.
            hints (dict, optional): Dictionary with keyword arguments for solver
            name ([str],optional): Name of problem for stringification
        """
        self.lsf = lsf
        self.e_fun = e_fun
        self.sample = sample
        self.prob_fail_true = prob_fail_true
        self.mpp = mpp
        if sample_gen is not None:
            self.sample_gen = sample_gen
        if isinstance(eranataf_dist, ERANataf):
            self.eranataf_dist = eranataf_dist
        if isinstance(hints, dict):
            self.hints = hints
        else:
            self.hints = {}
        if name is None:
            self.name = f"Unknown Problem at {id(self)}"
        else:
            self.name = name


    def set_sample(self, arg,seed=None):
        """Reset self.sample.

        Args:
            arg ([int] or [ndarray]): If int, try to call self.sample_gen. If ndarray,
            assume arg to be collection of samples. Each row is one sample
            ssed (optional): provides the seed to sample_gen.
        """
        if isinstance(arg, int):
            assert hasattr(
                self, "sample_gen"), "Problem has no sample generator. Provide a sample as a ndarray!"
            self.sample = self.sample_gen(arg, seed=seed)
        elif isinstance(arg, ndarray) and arg.shape[-1] == self.sample[-1]:
            self.sample = arg
        else:
            print("arg is no integer or sample of correct dimension.")
        return self


class NormalProblem(Problem):
    """ This class defines a special kind of rare event estimation problem.
    It assumes that the lsf operates on the standard normal space.
    Thus the energy function and the sample distrubtion are known (standard normal).
    """

    def __init__(self, lsf: Callable, dim: int, sample_size: int, prob_fail_true=None, mpp=None, hints=None,name=None):
        """Construcor if distribution is standard normal.

        Args:
            lsf (Callable): Handle to limit state function.
            dim (int): Dimension of the multivariate normal distribution.
            sample_size (int): Initial sample size.
            prob_fail_true ([type], optional): True probability of failure. Defaults to None.
        """

        # Define distribution as an ERANataf
        marginals = [ERADist('standardnormal', 'PAR', nan) for _ in range(dim)]
        eranataf_dist = ERANataf(marginals, eye(dim))

        def e_fun(x): return -gaussian_logpdf(x)

        def sample_gen(sample_size,seed=None): return eranataf_dist.random(n=sample_size,seed=seed)
        sample = sample_gen(sample_size)

        super().__init__(lsf, e_fun, sample, sample_gen=sample_gen,
                         prob_fail_true=prob_fail_true, mpp=mpp, eranataf_dist=eranataf_dist, hints=hints,name=name)


class Vectorizer:
    """
    A wrapper class for the limit state function.
    Dispatches calls based on arguments. Arguments can be:
        A 1-d array specifying a point in the domain of the lsf. Returns a single value: The lsf evaluation in that point.
        A 2-d arrray. Each row represents a point in the domain of the lsf. Returns a 1d array: The lsf evaluations in the rows.
        A k tuple `xi' of k-d arrays: Returns a k-d array of a meshgrid evaulation.
    """
    num_evals = 0

    def __init__(self, lsf: Callable, d: int, lsf_2d=None, lsf_msh=None) -> None:
        """Write the the callable method for dispatching based on `lsf`.
        Very slow implementation of the array and mehsgird evaluations!
        Args:
            lsf (Callable[[1-d array], float]): The limit state function with a single argument corresponding to a point evaluation
            d [int]: Dimension of `lsf`'s domain.
            lsf_2d (Callable[[2-d array], 1-d array]): The limit state function with a single argument corresponding to a 2-d array of shape `(n,d)`, returning a 1-d array of length `n` with the lsf evaluations in the points defined by the rows of the 2-d array.
        """

        if lsf_2d is None:
            def lsf_2d(xx): return apply_along_axis(lsf, 1, xx)
        if lsf_msh is None:
            def lsf_msh(*xi):
                dims = xi[0].shape
                out = zeros(dims)
                for (idx, _) in ndenumerate(out):
                    val = array([x[idx] for x in xi])
                    out[idx] = lsf(val)
        self.d = d
        self.lsf_1d = lsf
        self.lsf_2d = lsf_2d
        self.lsf_msh = lsf_msh

    def __call__(self, *args):
        """Dispatch to different versions of the limit state function.

        If args is a 1-d array of lenght `d`, return a single value: The lsf evaluation in that `d`-dimensional point.
        If args is a 2-d array of shape `(n,d)`, return a 1-d array of length `n` with the lsf evaluations in the points defined by the rows of args.
        If args is a tuple of d `d`-d arrays, return a `d`-d array. The outputs's value at the index `idx` corresponds to the `d`-dimensional point whose `k`th component is specifyied by `args[k][idx]`.
        """
        if len(args) == 1 and args[0].shape == (self.d,):
            # Single point evaluation
            self.num_evals = self.num_evals + 1
            return self.lsf_1d(args[0])
        if len(args) == 1 and args[0].ndim == 2 and args[0].shape[1] == self.d:
            # Evaluation of rows
            self.num_evals = self.num_evals + args[0].shape[0]
            return self.lsf_2d(args[0])
        if len(args) == self.d and all([x.ndim == self.d and x.shape == args[0].shape for x in args]):
            # Meshgrid evaluation
            self.num_evals = self.num_evals + prod(args[0].shape)
            self.lsf_msh(args)

sample_size = 1  # Does not really matter, will be changes by make_conv_analysis anyway
prob_dim = 2


def lsf_convex(x): return 0.1*(x[...,0]-x[...,1])**2 - 1/sqrt(2)*sum(x,axis=-1)+2.5
prob_fail_convex = 4.21e-3
prob_convex = NormalProblem(
    lsf_convex, prob_dim, sample_size, prob_fail_true=prob_fail_convex,name="Convex Problem", mpp=5/(2*sqrt(2)) * ones(2))
prob_convex.matlab_str = "@(x) 0.1*(x(:,1)-x(:,2)).^2 - 1/sqrt(2)*(x(:,1)+x(:,2))+2.5"

def lsf_par(x): return 5-x[...,1]-0.5*(x[...,0]-0.1)**2
prob_fail_par = 3.01e-3
hints_par = {"num_comps":2}
prob_par = NormalProblem(lsf_par, prob_dim, sample_size,
                         prob_fail_true=prob_fail_par,hints=hints_par)



def lsf_series(x):
    plus = sum(x,axis=-1)
    minus = diff(x,axis=-1)
    comp = [
        .1*minus**2 - plus/sqrt(2) + 3,
        .1*minus**2 + plus/sqrt(2) + 3,
        minus + 7/sqrt(2),
        - minus + 7/sqrt(2),
    ]
    return amin(array(comp))
prob_fail_series = 2.2e-3
hints_series = {"num_comps":4}
prob_series = NormalProblem(
    lsf_series, prob_dim, sample_size, prob_fail_true=prob_fail_series, hints=hints_series,name="Series Problem")

beta = 3.5
def lsf_lin(x): return -sum(x,axis=-1) / sqrt(x.shape[-1]) + beta
def make_linear_problem(d, beta=3.5):
    def lsf_lin(x): return -sum(x,axis=-1) / sqrt(x.shape[-1]) + beta
    p = NormalProblem(lsf_lin,
                      d,
                      1,
                    prob_fail_true=norm.cdf(-beta),
                    name=f"Linear Problem (d={d})",
                    mpp = beta/ sqrt(d) * ones(d))
    p.matlab_str = f"@(x) -sum(x)/sqrt(length(x)) + {beta}"
    return p 


def make_fujita_rackwitz(d,pf=1e-04):
    c = gamma.ppf(pf,d)
    def lsf(x): return -sum(log(norm.cdf(-x)),axis=-1) -c
    pf = gamma.cdf(c,d)
    mpp = -norm.ppf(exp(-c/d))*ones(d) 
    prob = NormalProblem(lsf,d,1,pf,name=f"Fujita Rackwitz (d={d})", mpp=mpp)
    prob.matlab_str = f"@(x) -sum(log(normcdf(-x))) - {c}"
    return prob



problems_lowdim = [
    prob_convex,
    make_linear_problem(2),
    make_fujita_rackwitz(2)
]


problems_highdim = [
    make_linear_problem(d)
    for d in [10,20,30,40,50,75,100,150,200]
]

problems_highdim.extend([
    make_fujita_rackwitz(d)
    for d in [10,20,30,40,50,75,100,150,200]
])