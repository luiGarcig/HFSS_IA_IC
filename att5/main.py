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

xsize = 30
E = 1.65
W = 25.5
L = 19.3
b = 1.4
lambdaG = 41
y0 = 6.5
ysize = L + (lambdaG/2) - y0 + 3

hfss = Hfss(solution_type="Modal")

hfss.modeler.model_units = "mm"

p = hfss.modeler.primitives

gnd = p.create_rectangle(
    constants.PLANE.XY,
    (-xsize/2 ,-ysize/2 ,0) ,
    (xsize, ysize),
    name="gnd"
)

substract = p.create_box(
    [-xsize/2 ,-ysize/2 ,0],
    [xsize, ysize, E],
    material="FR4_Epoxy",
    name="substract"
)

feed = p.create_rectangle(
    constants.PLANE.XY,
    (-b/2 ,-ysize/2 ,E) ,
    (b, lambdaG/2),
    name="feed"
) 

patch = p.create_rectangle(
    constants.PLANE.XY,
    (-W/2 ,-ysize/2+(lambdaG/2)-y0 ,E) ,
    (W, L),
    name="patch"
) 

cut = p.create_rectangle(
    constants.PLANE.XY,
    (-(b+0.8)/2 ,-ysize/2+(lambdaG/2)-y0 ,E) ,
    (b+0.8, y0),
    name="cut"
) 

p.subtract(patch, cut)
p.unite([patch, feed])
p.delete(cut)

port = p.create_rectangle(
    constants.PLANE.ZX,
    (-b/2 ,-ysize/2 ,0) ,
    (E, b),
    name="port1"
)

hfss.assign_perfect_e(
    patch.name
)

hfss.assign_perfect_e(
    gnd.name
)

hfss.change_material_override()

hfss.lumped_port(
    assignment=port.name,                 
    reference=port,
    integration_line=hfss.AxisDir.ZNeg,    
    impedance=50,
    name=generate_unique_name("port1"),
    renormalize=False,
    terminals_rename=False
)

my_plot =hfss.plot(show=False, plot_air_objects=False)
my_plot.show_axes = False
my_plot.show_grid = False
my_plot.isometric_view = True
my_plot.plot(
    os.path.join(hfss.working_directory, "AntennaPatchGap.jpg")    
)

setup = hfss.create_setup("MySetup")

SingleFrequency("3.5GHz", 30,0.02)
LinearCountSweep(1.0,5.0)
SaveAnalyseSetup("AntennaPatchGap.aedt")

#S11-----------------------------------------------------------------------------

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
indexValueMin = dfRealGap['|$S_{11}$| [dB]'].idxmin()

dfRealGap.to_csv('S11_Gap.csv')

Grafico(
    dfRealGap,
    "Coeficiente de reflexao",
    "Frequency [GHz]",
    "|$S_{11}$| [dB]",
)

#Gain-----------------------------------------------------------------------------

new_report = hfss.post.reports_by_category.far_field(
    "GainTotal",
    hfss.nominal_adaptive,
    "3D"
)
variations = hfss.available_variations.nominal_w_values_dict
variations["Theta"] = ["All"]
variations["Phi"] = ["All"]
variations["Freq"] = ["3.5GHz"]

new_report.primary_sweep ="Theta"
new_report.secondary_sweep ="Phi"
new_report.far_field_sphere = "3D"
new_report.variations = variations
solutions = new_report.get_solution_data()


solutions.plot_3d(title="Ganho 3d")

solutions.plot(
     formula="db10",
     is_polar=True,
     show_legend=False,
     title="Ganho"
)

solutions.data_db10()

d.release_desktop()