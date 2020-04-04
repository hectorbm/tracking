import numpy as np
from keras.utils import to_categorical
from physical_models.models_ctrw import CTRW
from physical_models.models_fbm import FBM
from physical_models.models_two_state_diffusion import TwoStateDiffusion

def axis_adaptation_to_net(axis_data,track_length):
    axis_reshaped = np.reshape(axis_data,[1,len(axis_data)])
    axis_reshaped = axis_reshaped - np.mean(axis_reshaped)
    axis_diff = np.diff(axis_reshaped[0,:track_length])
    return axis_diff 

def generate_batch_of_samples_l1(batchsize,track_length,track_time,sigma):
    out = np.zeros([batchsize,track_length-1,2])
    label = np.zeros([batchsize,1])
    T_sample = np.random.choice(np.arange(track_time,track_time+1,0.5))
    steps_sample = int(np.random.choice(np.arange(track_length, np.ceil(track_length*1.05),1)))

    for i in range(batchsize):
        model_sample = np.random.choice(["fbm","ctrw","two-state"])
        if model_sample == "fbm":
            model = FBM.create_random()
            x,y,t = model.simulate_track(steps_sample,T_sample)
            label[i,0] = 0
        elif model_sample == "ctrw":
            model = CTRW.create_random()
            x,y,t = model.simulate_track(steps_sample,T_sample)
            label[i,0] = 1
        else: 
            model = TwoStateDiffusion.create_random()
            switching = False
            while not switching:
                x,y,t,state,switching = model.simulate_track(steps_sample,T_sample)
            label[i,0] = 2

        out[i,:,0] = axis_adaptation_to_net(x,track_length)
        out[i,:,1] = axis_adaptation_to_net(y,track_length)

    return out,label

def generate_batch_of_samples_l2(batchsize,track_length,track_time,sigma):
    out = np.zeros([batchsize,track_length-1,2])
    label = np.zeros([batchsize,1])
    T_sample = np.random.choice(np.arange(track_time,track_time+1,0.5))
    steps_sample = int(np.random.choice(np.arange(track_length, np.ceil(track_length*1.05),1)))

    for i in range(batchsize):
        model_sample = np.random.choice(["sub","brownian","super"])
        if model_sample == "sub":
            model = FBM.create_random_subdiffusive()
            label[i,0] = 0

        elif model_sample == "brownian":
            model = FBM.create_random_brownian()
            label[i,0] = 1

        else: 
            model = FBM.create_random_superdiffusive()
            label[i,0] = 2

        x,y,t = model.simulate_track(steps_sample,T_sample)
        
        out[i,:,0] = axis_adaptation_to_net(x,track_length)
        out[i,:,1] = axis_adaptation_to_net(y,track_length)

    return out,label

def generator_first_layer(batchsize,track_length,track_time,sigma):
    while True:
        out, label = generate_batch_of_samples_l1(batchsize,track_length,track_time,sigma)
        label = to_categorical(label,num_classes=3)
        input_net = np.zeros([batchsize,track_length-1,1])
        for i in range(batchsize):
            input_net[i,:,0] = out[i,:,0]
        yield input_net, label

def generator_second_layer(batchsize,track_length,track_time,sigma):
    while True:
        out, label = generate_batch_of_samples_l2(batchsize,track_length,track_time,sigma)
        label = to_categorical(label,num_classes=3)
        input_net = np.zeros([batchsize,track_length-1,1])
        for i in range(batchsize):
            input_net[i,:,0] = out[i,:,0]
        yield input_net, label



def generate_batch_of_samples_state_net(batchsize,track_length,track_time,sigma):
    out = np.zeros([batchsize,track_length,2])
    label = np.zeros([batchsize,track_length])
    T_sample = np.random.choice(np.arange(track_time,track_time+1,0.5))
    steps_sample = int(np.random.choice(np.arange(track_length, np.ceil(track_length*1.05),1)))

    for i in range(batchsize):
        model = TwoStateDiffusion.create_random()
        switching = False
        while not switching:
            x,y,t,state,switching = model.simulate_track(steps_sample,T_sample)

        axis_reshaped = np.reshape(x,[1,len(x)])[:,:track_length]
        out[i,:,0] = axis_reshaped - np.mean(axis_reshaped)

        axis_reshaped = np.reshape(y,[1,len(y)])[:,:track_length]
        out[i,:,1] = axis_reshaped - np.mean(axis_reshaped)

        label[i,:] = state[:track_length]

    return out, label


def generator_state_net(batchsize,track_length,track_time,sigma):
    while True:
        out, label = generate_batch_of_samples_state_net(batchsize,track_length,track_time,sigma)
        input_net = np.zeros([batchsize,track_length,1])
        for i in range(batchsize):
            input_net[i,:,0] = out[i,:,0]
        yield input_net, label
