from numpy import eye, ones, sqrt, sum, diff, amin, log, exp, array
from scipy.stats import norm, gamma
from rareeventestimation.problem.problem import NormalProblem
sample_size = 1  # Does not really matter, will be changes by make_conv_analysis anyway


# Convex-Problem
prob_dim = 2
def lsf_convex(x): return 0.1*(x[...,0]-x[...,1])**2 - 1/sqrt(2)*sum(x,axis=-1)+2.5
prob_fail_convex = 4.21e-3
prob_convex = NormalProblem(
    lsf_convex, prob_dim, sample_size, prob_fail_true=prob_fail_convex,name="Convex Problem", mpp=5/(2*sqrt(2)) * ones(2))
prob_convex.matlab_str = "@(x) 0.1*(x(:,1)-x(:,2)).^2 - 1/sqrt(2)*(x(:,1)+x(:,2))+2.5"

# Linear-Problem
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

# Fujita-Rackwitz Problem
def make_fujita_rackwitz(d,pf=1e-04):
    c = gamma.ppf(pf,d)
    def lsf(x): return -sum(log(norm.cdf(-x)),axis=-1) -c
    pf = gamma.cdf(c,d)
    mpp = -norm.ppf(exp(-c/d))*ones(d) 
    prob = NormalProblem(lsf,d,1,pf,name=f"Fujita Rackwitz (d={d})", mpp=mpp)
    prob.matlab_str = f"@(x) -sum(log(normcdf(-x))) - {c}"
    return prob


# problem lists
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