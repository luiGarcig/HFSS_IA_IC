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
    setup.props["Frequency"] = freq
    setup.props["MaximumPasses"] = maxPasses
    setup.props["MaxDeltaS"] =maxDeltaS
    setup.props["UseIterativeSolver"] = True
    setup.props["SaveRadFieldsOnly"] = True

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
    colorGraf='red',

):
    valorEixoY = df[nameY].to_numpy()
    valorEixoX = df[nameX].to_numpy()
    fig, ax = plt.subplots()
    ax.plot(valorEixoX, valorEixoY, color=colorGraf, linewidth = 5)
    ax.set_xlabel(nameX, fontsize = 22)
    ax.set_ylabel(nameY, fontsize = 22)
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.title(title, fontsize=24)
    plt.show()

def Grafico_Sparametros(
    df,
    title,
    nameX='Frequency [GHz]',
    nameY1='|$S_{11}$| [dB]',
    nameY2='|$S_{21}$| [dB]',

):
    x = df[nameX].to_numpy()
    y1 = df[nameY1].to_numpy()
    y2 = df[nameY2].to_numpy()

    fig, ax = plt.subplots()
    ax.plot(x, y1, color="red", linewidth = 5, label=nameY1)
    ax.plot(x, y2, color="green", linewidth = 5, label=nameY2)
    ax.set_xlabel(nameX, fontsize = 22)
    ax.set_ylabel("Magnitude [dB]", fontsize = 22)
    plt.title(title, fontsize=24)
    plt.legend(fontsize=20)
    plt.tick_params(axis='both', which='major', labelsize=20)
    plt.grid(True)
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

a=7.11
b=3.56
c=50
t=1

hfss = Hfss(solution_type="Modal")
hfss.modeler.model_units = "mm"

p = hfss.modeler.primitives

outer_WG = p.create_box(
    [-(a + 5)/2 ,-c ,-(b + 5)/2],
    [(a + 5),c,(b + 5)],
    material="copper",
    name="outer_WG"
)

inner_WG_cut = p.create_box(
    [-a/2 ,-c ,-b/2],
    [a,c,b],
    name="inner_WG_cut"
)

p.subtract(
    outer_WG, 
    inner_WG_cut
)

inner_WG = p.create_box(
    [-a/2 ,-c ,-b/2],
    [a,c,b],
    name="inner_WG"
)

port1 = p.create_rectangle(
    constants.AXIS.Y,
    origin=(-a/2,-c,1.78) ,
    sizes=(-b, a),
    name="port1"
)

port2 = p.create_rectangle(
    constants.AXIS.Y,
    origin=(-a/2,0,1.78) ,
    sizes=(-b, a),
    name="port2"
)

hfss.wave_port(
    assignment=port1.name,                 
    reference=port1,
    integration_line=hfss.AxisDir.ZNeg,    
    impedance=50,
    name=generate_unique_name("port1"),
    renormalize=False,
    terminals_rename=False
)

hfss.wave_port(
    assignment=port2.name,                 
    reference=port2,
    integration_line=hfss.AxisDir.ZNeg,    
    impedance=50,
    name=generate_unique_name("port2"),
    renormalize=False,
    terminals_rename=False
)

my_plot =hfss.plot(show=False, plot_air_objects=False)
my_plot.show_axes = False
my_plot.show_grid = False
my_plot.isometric_view = True
my_plot.plot(
    os.path.join(hfss.working_directory, "WaveGuide.jpg")    
)

setup = hfss.create_setup("MySetup")

SingleFrequency("42GHz", 6, 0.02) 
LinearCountSweep(21.0,43.0)
SaveAnalyseSetup("WaveGuide.aedt")

#Z-----------------------------------------------

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="z")
)


Data = solutions._init_solution_data_real()
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
# print(dfVazioZGap)

dfVazioZGap.to_csv('Z_Real_Gap.csv')

Grafico(
    dfVazioZGap,
    "Impedancia de entrada",
    'Frequency [GHz]',
    'Re $Z_{in}$ (ohm)',
)


#S11-----------------------------------------------------------------------------

solutions = hfss.post.get_solution_data(
    expressions=hfss.get_traces_for_plot(category="dB(S")
)

solutions.enable_pandas_output = True
S_Real = solutions._init_solution_data_real()
trace_names = list(S_Real.keys())

s11_trace = next(t for t in trace_names if ":1,port1" in t and t.endswith(":1))"))
s21_trace = next(t for t in trace_names if ":1,port2" in t and t.endswith(":1))"))

freqs = []
s11_values = []
s21_values = []

for freq_points in S_Real[trace_names[0]].keys():
    freq = float(freq_points[0])
    freqs.append(freq)
    s11_val = float(S_Real[s11_trace].get(freq_points, float('nan')))
    s21_val = float(S_Real[s21_trace].get(freq_points, float('nan')))

    s11_values.append(s11_val)
    s21_values.append(s21_val)

dfRealGap = pd.DataFrame({
    "Frequency [GHz]": freqs,
    "|$S_{11}$| [dB]": s11_values,
    "|$S_{21}$| [dB]": s21_values   
})

Grafico_Sparametros(
    dfRealGap,
    "Coeficientes de Reflexão e Transmissão",
    "Frequency [GHz]",
    "|$S_{11}$| [dB]",
    "|$S_{21}$| [dB]"
)


d.release_desktop()