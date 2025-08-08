# -*- coding: utf-8 -*-
from turtle import title
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
from ansys.aedt.core import generate_unique_name
from ansys.aedt.core import Desktop, Hfss, constants

def SingleFrequency(
    freq,
    maxPasses,
    maxDeltaS= 0.02,
    name="MySetup"
):
    hfss.create_open_region(frequency=freq)
    setup.props["Frequency"] = freq
    setup.props["MaximumPasses"] = maxPasses
    setup.props["MaxDeltaS"] =maxDeltaS
    setup.props["UseIterativeSolver"] = True
    setup.props["SaveRadFieldsOnly"] = True
    setup.props["RadiationSetup"] = "3D"
    setup.props["ComputeFarFields"] = True

def LinearCountSweep(
    fStart,
    fStop,
    freqPonts=401,
    units="GHz",
    saveFields=True,
    saveRadFields=True
):
    sweep = hfss.create_linear_count_sweep(
        setup=setup.name,
        units=units,
        start_frequency=fStart,
        stop_frequency=fStop,
        num_of_freq_points = freqPonts,
        name= "sweep",
        sweep_type="Interpolating",
        save_fields=saveFields,
        save_rad_fields=saveRadFields
    )

def SaveAnalyseSetup(
    nameFolder= "MicroStrip.aedt",
    setup="MySetup"
):
    hfss.save_project(os.path.join(temp_folder, nameFolder))
    hfss.analyze_setup(setup)

def Grafico(
    df,
    title,
    nameX='Frequency [GHz]',
    nameY='Result',
    colorGraf='red'
):
    valorEixoY = df[nameY].to_numpy()
    valorEixoX = df[nameX].to_numpy()
    fig, ax = plt.subplots()
    ax.plot(valorEixoX, valorEixoY, color='red', linewidth = 5)
    ax.set_xlabel(nameX, fontsize = 22)
    ax.set_ylabel(nameY, fontsize = 22)
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.title(title, fontsize=24)
    plt.show()



tmpfold = tempfile.gettempdir()

temp_folder = os.path.join(
    tmpfold,
    generate_unique_name("Antenna")
)

if not os.path.exists(temp_folder):
    os.mkdir(temp_folder)

non_graphical = os.getenv(
    "PYAEDT_NON_GRAPHICAL",
    "False"
).lower() in ("true", "1", "t")

d = Desktop(
    "2025.1",
    non_graphical=non_graphical,
    new_desktop=True
)

L = 17.55
dR = 1.65
gL = 1
xSize = 17
ySize = 43
D = 3   
g = 0.434
L2 = 7.2

hfss = Hfss(solution_type="Modal")
hfss.modeler.model_units = "mm"

p = hfss.modeler.primitives

box = p.create_box(
    [-xSize/2, -ySize/2, 0],
    [xSize, ySize, dR],
    name="box",
    material="FR4_epoxy"
)

haste_1_horizontal = p.create_rectangle(
    constants.AXIS.Z,
    [L2-(xSize/2), -D/2, dR],
    (D, L),
    name="haste_1_h",
)

haste_1_vertical = p.create_rectangle(
    constants.AXIS.Z,
    [-xSize/2, -D/2, dR],
    (L2, D),
    name="haste_1_v",
)

haste_1 = p.unite([haste_1_horizontal, haste_1_vertical])

hfss.assign_perfect_e(
    haste_1_horizontal.name
)


haste_2_horizontal = p.create_rectangle(
    constants.AXIS.Z,
    [L2-(xSize/2), -L+D/2, 0],
    (D, L),
    name="haste_2_h",
)

haste_2_vertical = p.create_rectangle(
    constants.AXIS.Z,
    [-xSize/2, -D/2, 0],
    (L2, D),
    name="haste_2_v",
)

haste_2 = p.unite([haste_2_horizontal, haste_2_vertical])

hfss.assign_perfect_e(
    haste_2_horizontal.name
)

port = p.create_rectangle(
    constants.AXIS.X,
    [-xSize/2, -D/2, 0],
    (D, dR),
    name="port",
)

hfss.lumped_port(
    assignment=port.name,                 
    reference=port,
    integration_line=hfss.AxisDir.ZNeg,    
    impedance=50,
    name=generate_unique_name("port1"),
    renormalize=False,
    terminals_rename=False
)

setup = hfss.create_setup("MySetup")

SingleFrequency("5GHz", 30, 0.02) 
LinearCountSweep(1.0,5.0)
SaveAnalyseSetup("dipoloAntenna.aedt")

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="dB(S")
)

solutions.enable_pandas_output = True


S_Real = solutions._init_solution_data_real()
index = 0
S_real1 = S_Real[list(S_Real.keys())[index]]
listaReal = []
listaReal2 = []
dataVazioGap = {}
dfRealGap = pd.DataFrame(dataVazioGap)
for i,c in S_real1.items():
    #a = i[0]
    #listaReal.append(a)
    listaReal.append(float(i[0]))
    #c=S_real1[i]
    listaReal2.append(float(c))
dfRealGap.insert(0, "Frequency [GHz]", listaReal, True)
dfRealGap.insert(1, "|$S_{11}$| [dB]", listaReal2, True)
print(dfRealGap)
indexValueMin = dfRealGap['|$S_{11}$| [dB]'].idxmin()
print(dfRealGap.loc[indexValueMin])

dfRealGap.to_csv('S11_Gap.csv')

Grafico(
    dfRealGap,
    "Coeficiente de reflexao",
    "Frequency [GHz]",
    "|$S_{11}$| [dB]",
)


new_report = hfss.post.reports_by_category.far_field(
    "GainTotal",
    hfss.nominal_adaptive,
    "3D"
)
variations = hfss.available_variations.nominal_w_values_dict
variations["Theta"] = ["All"]
variations["Phi"] = ["All"]
variations["Freq"] = ["5GHz"]

new_report.primary_sweep ="Theta"
new_report.secondary_sweep ="Phi"
new_report.far_field_sphere = "3D"
new_report.variations = variations
new_report.expressions = ["GainTotal"]
solutions = new_report.get_solution_data()


solutions.plot(
    formula="db10",
    is_polar=True,
    show_legend=False,
    title="Ganho"
)


d.release_desktop()