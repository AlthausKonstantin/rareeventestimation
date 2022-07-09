import plotly.express as px
CMAP = px.colors.qualitative.Safe 
import plotly.io as pio
MY_TEMPLATE = pio.templates["plotly_white"]
MY_TEMPLATE.update({"layout.colorway": CMAP})
MY_LAYOUT = {
    "template":MY_TEMPLATE,
    "font_family":"Serif",
    "autosize":False,
    "width":700,
    "height":700*2/3,
    "margin":dict(
        l=50,
        r=50,
        b=50,
        t=10,
        pad=4
    )}

INDICATOR_APPROX_LATEX_NAME = {
    "sigmoid": f"$I_\\text{{sig}}$",
    "relu": f"$I_\\text{{ReLU}}$",
    "algebraic": f"$I_\\text{{alg}}$",
    "arctan": f"$I_\\text{{arctan}}$",
    "tanh": f"$I_\\text{{tanh}}$",
    "erf": f"$I_\\text{{erf}}$",
}

STR_BETA_N = "<i>\u03B2<sup>n</i></sup>"
STR_SIGMA_N = "<i>\u03C3<sup>n</i></sup>"
STR_H_N =  "<i>h<sup>n</i></sup>"
STR_J_ESS = f"<i>J</i><sub>ESS</sub>"

WRITE_SCALE=7


BM_SOLVER_SCATTER_STYLE = {
    "EnKF (vMFNM)":{
        "line_dash": "dash",
        "marker_symbol": "square",
        "marker_color": CMAP[0]},
    "EnKF (GM)":{
        "line_dash": "dash",
        "marker_symbol": "square",
        "marker_color": CMAP[1]},
    "SiS (GM)":{
        "line_dash": "dot",
        "marker_symbol": "diamond",
        "marker_color": CMAP[1]},
    "SiS (aCS)":{
        "line_dash": "dot",
        "marker_symbol": "diamond",
        "marker_color": CMAP[1]},
    
}


DF_COLUMNS_TO_LATEX = {
        "stepsize_tolerance": "$\\epsilon_{{\\text{{Target}}}}$",
        "cvar_tgt": "$\\Delta_{{\\text{{Target}}}}$",
        "lip_sigma": "Lip$(\\sigma)$",
        "tgt_fun": "Smoothing Function",
        "observation_window": "$N_{{ \\text{{obs}} }}$",
        "callback": "IS Density"}
LATEX_TO_HTML = {
    "$\\epsilon_{{\\text{{Target}}}}$": "<i>\u03B5</i><sub>Target</sub>" ,
    "$\\Delta_{{\\text{{Target}}}}$": "\u0394<sub>Target</sub>",
    "Lip$(\\sigma)$": "Lip(\u03C3)",
    "$N_{{ \\text{{obs}} }}$":"<i>N</i><sub>obs</sub>",
    "IS Density": "<i> \u03BC<sup>N</sup></i>"}