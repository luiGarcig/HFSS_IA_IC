# -*- coding: utf-8 -*-
import gymnasium as gym 
import numpy as np
from ansys.aedt.core import Hfss, constants

def SingleFrequency(
    hfss,
    setup,
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
    hfss,
    setup,
    fStart,
    fStop,
    freqPonts=201,
    units="MHz",
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
    hfss,
    setup="MySetup"
):
   return hfss.analyze_setup(setup)

def makeCombiner(p, x_substrate, y_substrate, width_port, height):

    substrate = p.create_box(
        [-x_substrate/2,-y_substrate/2,0],
        [x_substrate,y_substrate,height],
        material="FR4_epoxy",
        name="substrate"
    )

    port1 = p.create_rectangle(
        constants.AXIS.Y,
        [-width_port/2, -y_substrate/2, 0],
        [height, width_port], 
        "port1",
    )

    port2 = p.create_rectangle(
        constants.AXIS.Y,
        [-x_substrate/2, y_substrate/2, 0],
        [height, width_port], 
        "port2",
    )

    port3 = p.create_rectangle(
        constants.AXIS.Y,
        [(x_substrate/2 - width_port), y_substrate/2, 0],
        [height, width_port], 
        "port3",
    )

def findPath(matrix1, matrix2, x_substrate, y_substrate, matrix_size, hfss, p, position_X, position_X2, position_Y,height):

    w_pixel = (x_substrate/2) / matrix_size
    h_pixel = y_substrate / matrix_size

    initial_pos_Y = position_Y

    pixel_names1 = []
    for i in range(len(matrix1)):    
        for j in range(len(matrix1[0])):
            if matrix1[i][j] == 1:
                name = "pixel1_{}_{}".format(j, i)
                p.create_rectangle(
                    constants.AXIS.Z,
                    [position_X-w_pixel,position_Y, height],
                    [w_pixel, h_pixel], 
                    name,
                )
                pixel_names1.append(name)
            position_Y = position_Y + h_pixel   
        position_X = position_X - w_pixel 
        position_Y = initial_pos_Y
        
        initial_pos_Y = position_Y

    pixel_names2 = []
    for i in range(len(matrix2)):
        for j in range(len(matrix2[0])):
            if matrix2[i][j] == 1:
                name = "pixel2_{}_{}".format(j, i)
                p.create_rectangle(
                    constants.AXIS.Z,
                    [position_X2-w_pixel,position_Y, height],
                    [w_pixel, h_pixel], 
                    name,
                )
                pixel_names2.append(name)
            position_Y = position_Y + h_pixel
        position_X2 = position_X2 - w_pixel 
        position_Y = initial_pos_Y

    #if pixel_names1 and pixel_names2:
        #p.unite(pixel_names1)
        #p.unite(pixel_names2)

    hfss.assign_perfect_e(
        pixel_names1[0]
    )

    hfss.assign_perfect_e(
        pixel_names2[0]
    )


class CombinerEnv(gym.Env):
    def __init__(self, x_substrate, y_substrate, width_port, height, matrix_size, position_X, position_X2, position_Y, matrix1, matrix2):
        super(CombinerEnv, self).__init__()

        self.action_space = gym.spaces.Discrete(10) 
        self.observation_space = gym.spaces.Box(low=0, high=255, shape=(1, 10), dtype=np.uint8)

        self.x_substrate = x_substrate
        self.y_substrate = y_substrate
        self.width_port = width_port
        self.height = height 
        self.matrix_size = matrix_size 
        self.position_X = position_X
        self.position_X2 = position_X2
        self.position_Y = position_Y
        self.matrix1 = matrix1
        self.matrix2 = matrix2

        self.hfss = Hfss(solution_type="Modal")
        self.hfss.modeler.model_units = "mm"

        self.p = self.hfss.modeler.primitives

        makeCombiner(self.p, x_substrate, y_substrate, width_port, height)

    def reset(self):
        
        observation = np.zeros((1, 10), dtype=np.uint8)  
        return observation

    def step(self, action):

        findPath(self.matrix1, self.matrix2, self.x_substrate, self.y_substrate, self.matrix_size, self.hfss, self.p, self.position_X,  self.position_X2, self.position_Y, self.height)

        #SaveAnalyseSetup(self.hfss, setup=self.setup.name)
        
        reward = 0
        
        observation = np.zeros((1, 10), dtype=np.uint8)
        done = False
        
        info = {}

        return observation, reward, done, info

    def render(self, mode='human'):
        pass

    def close(self):
        if self.hfss:
            self.hfss.close_desktop()