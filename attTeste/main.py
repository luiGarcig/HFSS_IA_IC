# -*- coding: utf-8 -*-
from turtle import title
import numpy as numpy
import pandas as pd
import matplotlib.pyplot as plt
import tempfile
import os
from ansys.aedt.core import generate_unique_name
from ansys.aedt.core import Desktop, Hfss, constants
from ansys.aedt.core.modeler.cad.object_3d import Object3d

def SingleFrequency(
    freq,
    maxPasses,
    maxDeltaS= 0.01,
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

def LinearStepSweep(
    fStart,
    fStop,
    stepSize=0.001,
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
    nameFolder= "AntennaPatch.aedt",
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

L= 9661.15
W= 11858.54
L0= 5425.85
W0= 2420.98
sub_x= 20512.85
sub_y= 23717.08
sub_z= 787
gnd= 18
L_gap = 1812

hfss = Hfss(solution_type="Modal")

hfss.modeler.model_units = "um"

p = hfss.modeler.primitives

microstrip = p.create_box(
    [L/2, -W0/2, sub_z],
    [L0, W0, gnd],
    material="copper",
    name="microstrip"
)

port = p.create_rectangle(
    constants.PLANE.YZ,
    (sub_x/2, -W0/2, sub_z) ,
    (W0, -sub_z),
    name="port1"
)

substract = p.create_box(
    (-sub_x/2, -sub_y/2, 0),
    [sub_x, sub_y, sub_z],
    material="Rogers RT/duroid 5880 (tm)",
    name="substrato"
)

gndBox = p.create_box(
    [-sub_x/2, -sub_y/2, -gnd],
    [sub_x, sub_y, gnd],
    material="copper",
    name="terra"
)

box = p.create_box(
    [(-sub_x/2),(-sub_y/2), (-gnd)],
    [(sub_x), (sub_y), sub_z*10],
    name="airbox",
    material="air"
)

N = 5
Warray = [11858.54, 11858.54, 11858.54, 11858.54, 11858.54]
for Waux in range(N):
    W = Warray[Waux]
    patch = p.create_box(
        (-L/2+Waux*L/N, -W/2, sub_z),
        (L/N, W, gnd), 
        material="copper", 
        name="patch")
    p.unite([microstrip, patch])

gap_1 = p.create_box(
    (L/2, W0/2, sub_z),
    (-L_gap, W*0.07, gnd),
    material="air",
    name="gap"
)
gap_2 = p.create_box(
    (L/2, -W0/2 , sub_z),
    (-L_gap, -W*0.07, gnd),
    material="air",
    name="gap"
)

p.subtract(microstrip, gap_1)
p.subtract(microstrip, gap_2 )
hfss.assign_radiation_boundary_to_objects("airbox")
hfss.change_material_override()

hfss.lumped_port(
    port.name,                 
    microstrip,            
)

my_plot =hfss.plot(show=False, plot_air_objects=False)
my_plot.show_axes = False
my_plot.show_grid = False
my_plot.isometric_view = True
my_plot.plot(
    os.path.join(hfss.working_directory, "AntennaPatchGap.jpg")    
)

setup = hfss.create_setup("MySetup")

SingleFrequency("10GHz", 15,0.01)
LinearStepSweep(9.0,11.0)
SaveAnalyseSetup("AntennaPatchGap.aedt")

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

print(solutions)

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


#d.release_desktop()