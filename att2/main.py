# -*- coding: utf-8 -*-
from turtle import title
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
from ansys.aedt.core import generate_unique_name
from ansys.aedt.core import Desktop, Hfss, constants
from ansys.aedt.core.modeler.cad.object_3d import Object3d
from ansys.aedt.core.application.analysis import Analysis

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

def LinearStepSweep(
    fStart,
    fStop,
    stepSize=0.0125,
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

w0=100
l0=150
w=3
h=1.65

hfss = Hfss(solution_type="Modal")
hfss.modeler.model_units = "mm"

p = hfss.modeler.primitives

gnd = p.create_rectangle(
    constants.AXIS.Z,
    origin= (-w0/2, -l0/2,0) ,
    sizes= (w0, l0),
    name="ground"
)

substrate = p.create_box(
    [-w0/2,-l0/2,0],
    [w0,l0,h],
    material="FR4_epoxy",
    name="substrate"
)

path = p.create_rectangle(
    constants.AXIS.Z,
    origin=(-w/2,-l0/2, h) ,
    sizes=(w,l0),
    name="path"
)

port1 = p.create_rectangle(
    constants.AXIS.Y,
    origin=(-w/2,l0/2,0) ,
    sizes=(h,w),
    name="port1"
)

port2 = p.create_rectangle(
    constants.AXIS.Y,
    origin=(-w/2,-l0/2,0) ,
    sizes=(h,w),
    name="port2"
)

air = p.create_region(
    20,
    pad_type="Absolute Offset",
    name="airbox"    
)

hfss.assign_radiation_boundary_to_objects("airbox")
hfss.change_material_override()

hfss.lumped_port(
    assignment=port1.name,                 
    reference=port1,
    integration_line=hfss.AxisDir.ZPos,    
    impedance=50,
    name=generate_unique_name("port1"),
    renormalize=False,
    terminals_rename=False
)

hfss.lumped_port(
    assignment=port2.name,                 
    reference=port2,
    integration_line=hfss.AxisDir.ZPos,    
    impedance=50,
    name=generate_unique_name("port2"),
    renormalize=False,
    terminals_rename=False
)

hfss.assign_perfect_e(
    gnd.name
)

hfss.assign_perfect_e(
    path.name
)

my_plot =hfss.plot(show=False, plot_air_objects=False)
my_plot.show_axes = False
my_plot.show_grid = False
my_plot.isometric_view = True
my_plot.plot(
    os.path.join(hfss.working_directory, "MicroStrip.jpg")    
)

setup = hfss.create_setup("MySetup")

SingleFrequency("5GHz", 6,0.02)
LinearStepSweep(1.0,5.0)
SaveAnalyseSetup("MicroStrip.aedt")

#Z-----------------------------------------------

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="z")
)

Data =solutions._init_solution_data_real()
index = 0
real1 = Data[list(Data.keys())[index]]
lista = []
lista2 = []
dataVazioZGap = {}
dfVazioZGap = pd.DataFrame(dataVazioZGap)
for i in real1:
    a = i[0]
    lista.append(a)
    c=real1[i]
    lista2.append(c)
dfVazioZGap.insert(0, "Frequency [GHz]", lista, True)
dfVazioZGap.insert(1, "Re $Z_{in}$ (ohm)", lista2, True)
print(dfVazioZGap)

dfVazioZGap.to_csv('Z_Real_Gap.csv')

#S11-----------------------------------------------------------------------------

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="dB(S")
)

solutions.enable_pandas_output = True
""
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
    dfVazioZGap,
    "Impedancia de entrada",
    'Frequency [GHz]',
    'Re $Z_{in}$ (ohm)',
)

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
variations["Freq"] = ["10GHz"]

new_report.primary_sweep ="Theta"
new_report.secondary_sweep ="Phi"
new_report.far_field_sphere = "3D"
new_report.variations = variations
solutions = new_report.get_solution_data()

solutions.plot(
    formula="db10",
    is_polar=True,
    show_legend=False,
    title="Ganho"
)

solutions.plot_3d(title="Ganho 3d")

solutions.data_db10()

max(solutions.data_db10())
min(solutions.data_db10())


d.release_desktop()