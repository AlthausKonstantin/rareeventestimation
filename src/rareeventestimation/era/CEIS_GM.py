import numpy as np
import scipy as sp
from rareeventestimation.era.ERANataf import ERANataf
from rareeventestimation.era.ERADist import ERADist
from rareeventestimation.era.EMGM import EMGM

"""
---------------------------------------------------------------------------
Cross entropy-based importance sampling with Gaussian Mixture
---------------------------------------------------------------------------
Created by:
Sebastian Geyer (s.geyer@tum.de),
Felipe Uribe
Iason Papaioannou
Daniel Straub

Assistant Developers:
Matthias Willer
Peter Kaplan

Engineering Risk Analysis Group
Technische Universitat Munchen
www.era.bgu.tum.de
---------------------------------------------------------------------------
Version 2019-02
---------------------------------------------------------------------------
Comments:
* The LSF must be coded to accept the full set of samples and no one by one
  (see line 105)
* The CE method in combination with a Gaussian Mixture model can only be
  applied for low-dimensional problems, since its accuracy decreases
  dramatically in high dimensions.
* General convergence issues can be observed with linear LSFs.
---------------------------------------------------------------------------
Input:
* N      : number of samples per level
* p      : quantile value to select samples for parameter update
* g_fun  : limit state function
* distr  : Nataf distribution object or
           marginal distribution object of the input variables
* k_init : initial number of Gaussians in the mixture model
---------------------------------------------------------------------------
Output:
* Pr        : probability of failure
* lv        : total number of levels
* N_tot     : total number of samples
* gamma_hat : intermediate levels
* samplesU  : object with the samples in the standard normal space
* samplesX  : object with the samples in the original space
* k_fin     : final number of Gaussians in the mixture
---------------------------------------------------------------------------
Based on:
1."Cross entropy-based importance sampling using Gaussian densities revisited"
   Geyer et al.
   To appear in Structural Safety
2."A new flexible mixture model for cross entropy based importance sampling".
   Papaioannou et al. (2018)
   In preparation.
---------------------------------------------------------------------------
"""


def CEIS_GM(N, p, g_fun, distr, k_init):
    if (N * p != np.fix(N * p)) or (1 / p != np.fix(1 / p)):
        raise RuntimeError(
            "N*p and 1/p must be positive integers. Adjust N and p accordingly"
        )

    # initial check if there exists a Nataf object
    if isinstance(distr, ERANataf):  # use Nataf transform (dependence)
        dim = len(distr.Marginals)  # number of random variables (dimension)

        def u2x(u):
            return distr.U2X(u)  # from u to x

    elif isinstance(
        distr[0], ERADist
    ):  # use distribution information for the transformation (independence)
        # Here we are assuming that all the parameters have the same distribution !!!
        # Adjust accordingly otherwise
        dim = len(distr)  # number of random variables (dimension)

        def u2x(u):
            return distr[0].icdf(sp.stats.norm.cdf(u))  # from u to x

    else:
        raise RuntimeError(
            "Incorrect distribution. Please create an ERADist/Nataf object!"
        )

    # LSF in standard space
    def G_LSF(u):
        return g_fun(u2x(u))

    # Initialization of variables and storage
    j = 0  # initial level
    max_it = 50  # estimated number of iterations
    N_tot = 0  # total number of samples
    k = k_init  # number of Gaussians in mixture

    # Definition of parameters of the random variables (uncorrelated standard normal)
    mu_init = np.zeros([1, dim])
    Si_init = np.eye(dim)
    Pi_init = np.array([1.0])
    gamma_hat = np.zeros([max_it + 1])  # space for gamma
    samplesU = list()

    # CE Procedure
    # Initializing parameters
    gamma_hat[j] = 1.0
    mu_hat = mu_init
    Si_hat = Si_init
    Pi_hat = Pi_init

    # Iteration
    for j in range(max_it):
        # Generate samples
        X = GM_sample(mu_hat, Si_hat, Pi_hat, N).reshape(-1, dim)
        samplesU.append(X.T)

        # Count generated samples
        N_tot += N

        # Evatluation of the limit state function
        geval = G_LSF(X.T)

        # Calculating h for the likelihood ratio
        h = h_calc(X, mu_hat, Si_hat, Pi_hat)

        # check convergence
        if gamma_hat[j] == 0:
            break

        # obtaining estimator gamma
        gamma_hat[j + 1] = np.maximum(0, np.nanpercentile(geval, p * 100))
        # print('\nIntermediate failure threshold: ', gamma_hat[j+1])

        # Indicator function
        idx = geval <= gamma_hat[j + 1]

        # Likelihood ratio
        W = (
            sp.stats.multivariate_normal.pdf(X, mean=np.zeros((dim)), cov=np.eye((dim)))
            / h
        )

        # Parameter update: EM algorithm
        [mu_hat, Si_hat, Pi_hat] = EMGM(X[idx, :].T, W[idx], k_init)
        mu_hat = mu_hat.T
        k = len(Pi_hat)

    # store the needed steps
    lv = j
    k_fin = k
    gamma_hat = gamma_hat[: lv + 1]

    # Calculation of the Probability of failure
    W_final = (
        sp.stats.multivariate_normal.pdf(X, mean=np.zeros(dim), cov=np.eye((dim))) / h
    )
    I_final = geval <= 0
    Pr = 1 / N * sum(I_final * W_final)

    # transform the samples to the physical/original space
    samplesX = list()
    for i in range(lv):
        samplesX.append(u2x(samplesU[i][:, :]))

    return Pr, lv, N_tot, gamma_hat, samplesU, samplesX, k_fin


# ===========================================================================
# =============================AUX FUNCTIONS=================================
# ===========================================================================
def GM_sample(mu, si, pi, N):
    # ---------------------------------------------------------------------------
    # Algorithm to draw samples from a Gaussian-Mixture (GM) distribution
    # ---------------------------------------------------------------------------
    # Input:
    # * mu : [npi x d]-array of means of Gaussians in the Mixture
    # * Si : [d x d x npi]-array of cov-matrices of Gaussians in the Mixture
    # * Pi : [npi]-array of weights of Gaussians in the Mixture (sum(Pi) = 1)
    # * N  : number of samples to draw from the GM distribution
    # ---------------------------------------------------------------------------
    # Output:
    # * X  : samples from the GM distribution
    # ---------------------------------------------------------------------------
    if np.size(mu, axis=0) == 1:
        mu = mu.squeeze()
        si = si.squeeze()
        X = sp.stats.multivariate_normal.rvs(mean=mu, cov=si, size=N)
    else:
        # Determine number of samples from each distribution
        z = np.round(pi * N)
        if np.sum(z) != N:
            dif = np.sum(z) - N
            ind = np.argmax(z)
            z[ind] = z[ind] - dif

        z = z.astype(int)  # integer conversion

        # Generate samples
        d = np.size(mu, axis=1)
        X = np.zeros([N, d])
        ind = 0
        for p in range(len(pi)):
            X[ind : ind + z[p], :] = sp.stats.multivariate_normal.rvs(
                mean=mu[p, :], cov=si[:, :, p], size=z[p]
            ).reshape(-1, d)
            ind = ind + z[p]

    return X


# ===========================================================================
def h_calc(X, mu, si, Pi):
    # ---------------------------------------------------------------------------
    # Basic algorithm to calculate h for the likelihood ratio
    # ---------------------------------------------------------------------------
    # Input:
    # * X  : input samples
    # * mu : [npi x d]-array of means of Gaussians in the Mixture
    # * Si : [d x d x npi]-array of cov-matrices of Gaussians in the Mixture
    # * Pi : [npi]-array of weights of Gaussians in the Mixture (sum(Pi) = 1)
    # ---------------------------------------------------------------------------
    # Output:
    # * h  : parameters h (IS density)
    # ---------------------------------------------------------------------------
    N = len(X)
    k_tmp = len(Pi)
    if k_tmp == 1:
        mu = mu.squeeze()
        si = si.squeeze()
        h = sp.stats.multivariate_normal.pdf(X, mu, si)
    else:
        h_pre = np.zeros((N, k_tmp))
        for q in range(k_tmp):
            h_pre[:, q] = Pi[q] * sp.stats.multivariate_normal.pdf(
                X, mu[q, :], si[:, :, q]
            )

        h = np.sum(h_pre, axis=1)

    return h
