# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import os
from ansys.aedt.core import Hfss, constants, generate_unique_name
import math

def SingleFrequency(
    hfss,
    setup,
    freq,
    maxPasses,
    maxDeltaS= 0.01,
    name="MySetup"
):
    setup.props["Frequency"] = freq
    setup.props["MaximumPasses"] = maxPasses
    setup.props["MaxDeltaS"] =maxDeltaS
    setup.props["MinimumPasses"] = 2
    setup.props["MinimumConvergedPasses"] = 2
    setup.props["UseDirectSolver"] = True
    setup.props["SaveRadFieldsOnly"] = True
    setup.props["RadiationSetup"] = "3D"
    setup.props["ComputeFarFields"] = True
    setup.props["BasisOrder"] = -1
    setup.update()

def LinearStepSweep(
    hfss,
    setup,
    fStart,
    fStop,
    stepSize=0.01,
    units="GHz",
    saveFields=True,
    saveRadFields=True
):
    hfss.create_linear_step_sweep(
        setup=setup.name,
        unit=units,
        start_frequency=fStart,
        stop_frequency=fStop,
        step_size = stepSize,
        name= "sweep",
        sweep_type="Interpolating",
        save_fields=saveFields,
        save_rad_fields=saveRadFields
    )

def SaveAnalyseSetup(
    hfss,
    setup="MySetup"
):
   return hfss.analyze_setup(setup)

def makeAntenna(a1, a2, n1, n2, n3, n4, perc, r, temp_folder):
    
    x_sub = 200
    y_sub = 280
    h = 1.65
    w = 3

    l = (y_sub * perc)
    h_cut = (r*2) - (y_sub - l)

    min_ang = 1.3888888889 * math.pi
    max_ang = 1.6111111111 * math.pi

    def rho(theta):
        c = abs(math.cos(n1 * theta / 4) / a1)**n3
        s = abs(math.sin(n1 * theta / 4) / a2)**n4
        return (c + s)**(-1/n2)

    thetas = np.linspace(0, 2 * math.pi, 2000, endpoint=True)
    rho_max = max(rho(t) for t in thetas)

    scale_mm = r / rho_max

    thetas_limited = np.linspace(min_ang, max_ang, 2000, endpoint=True)
    rho_min_limited = min(rho(t) for t in thetas_limited)
    rho_max_limited = max(rho(t) for t in thetas_limited)
    diff_rho = rho_max_limited - rho_min_limited

    hfss = Hfss(solution_type="Modal")
    hfss.modeler.model_units = "mm"

    p = hfss.modeler.primitives

    expr =f"(abs(cos({n1}*_t/4)/{a1})^{n3} + abs(sin({n1}*_t/4)/{a2})^{n4})^(-1/{n2})"
    #para 0<= u <= 2*pi
    x_expr = f"({scale_mm}mm)*{expr}*cos(_t)"
    y_expr = f"({scale_mm}mm)*{expr}*sin(_t)"

    monopole = p.create_equationbased_curve(
        x_t=x_expr,
        y_t=y_expr,
        z_t="0mm",
        t_start="0deg",
        t_end= "360deg",
        num_points=800,
        name="monopole"
    )

    if(not monopole):
        raise Exception("valores da equacao nao sao validos")

    p.cover_lines(
        assignment=monopole.name,
    )

    monopole.move([0, -y_sub/2 + l + r - 15,h])

    substrate = p.create_box(
        [-x_sub/2,-y_sub/2,0],
        [x_sub,y_sub,h],
        material="FR4_epoxy",
        name="substrate"
    )

    gnd = p.create_rectangle(
        constants.AXIS.Z,
        [-x_sub/2, -y_sub/2,0] ,
        [x_sub,l - (diff_rho*scale_mm)/2 - 5],
        "ground"
    )

    path = p.create_rectangle(
        constants.AXIS.Z,
        [-w/2, -y_sub/2, h],
        [w, l+80],
        "path",
    ) 

    port = p.create_rectangle(
        constants.AXIS.Y,
        [-w/2, -y_sub/2, 0],
        [h, w], 
        "port",
    )

    if h_cut > 0:
        cut1 = p.create_rectangle(
            constants.AXIS.Z,
            [-x_sub/2, y_sub/2, h],
            [x_sub, h_cut], 
            "cut",
        )
        p.subtract(monopole, cut1)
        p.subtract(path, cut1)
        p.delete(cut1)

    cut2 = p.create_rectangle(
        constants.AXIS.Z,
        [-x_sub-x_sub/2, -y_sub/2, h],
        [x_sub, y_sub + h_cut], 
        "cut2",
    )
    cut3 = p.create_rectangle(
        constants.AXIS.Z,
        [x_sub/2, -y_sub/2, h],
        [x_sub, y_sub + h_cut], 
        "cut3",
    )
    p.subtract(monopole, cut2)
    p.subtract(monopole, cut3)
    p.delete(cut2)
    p.delete(cut3)
    monopole_unite = p.unite([monopole, path])

    w_airbox = (500*2)+x_sub
    h_airbox = (500*2)+y_sub
    d_airbox = (500*2)+h

    airbox = p.create_box(
        [-w_airbox/2, -h_airbox/2, -d_airbox/2],
        [w_airbox, h_airbox, d_airbox],
        name="airbox",
        material="air"
    )
    

    hfss.lumped_port(
        assignment=port.name, 
        reference=gnd.name,
        integration_line=hfss.AxisDir.ZNeg, 
        impedance=50,
        name=generate_unique_name("port"),
        renormalize=False,
    )

    hfss.assign_perfect_e(
        gnd.name
    )

    hfss.assign_perfect_e(  
        monopole.name
    )

    hfss.assign_radiation_boundary_to_objects(  
        airbox.name
    )

    setup = hfss.create_setup("MySetup")
    
    SingleFrequency(hfss, setup, "1.6GHz", 30,0.02)
    LinearStepSweep(hfss, setup, 0.2, 1.6)
    SaveAnalyseSetup(hfss)



    try:
        solutions = hfss.post.get_solution_data(
            expressions=hfss.get_traces_for_plot(category="dB(S")
        )
        solutions.enable_pandas_output = True
    except Exception as e:
        print(f"Error getting solution data: {e}")
        hfss.close_project()
    
        return pd.DataFrame()

    S_Real = solutions._init_solution_data_real()
    index = 0
    S_real1 = S_Real[list(S_Real.keys())[index]]
    listaReal = []
    listaReal2 = []
    dataVazioGap = {}
    dfRealGap = pd.DataFrame(dataVazioGap)
    for i,c in S_real1.items():
        listaReal.append(float(i[0]))
        listaReal2.append(float(c))
    dfRealGap.insert(0, "Frequency [MHz]", listaReal, True)
    dfRealGap.insert(1, "|$S_{11}$| [dB]", listaReal2, True)


    hfss.close_project()
    return dfRealGap