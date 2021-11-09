import sys
sys.path.append("../DeepDDG_reconstruction")

import numpy as np
import torch
from torch import nn, optim
from torch.utils.data import DataLoader
from DeepDDG.models import SRP, FCNNS, count_params
from DeepDDG.dataset import DeepDDGDataset
import matplotlib.pyplot as plt

def train():
    srp_model.train()
    fcnn_model.train()
    losses = []
    for i, data in enumerate(train_loader):
        pair_tensors, ddG = data
        pair_tensors = pair_tensors.to(device=device)
        ddG = ddG.to(device=device) / 10
        # print(pair_tensors.dtype, pair_tensors.shape)
        # print(ddG.dtype, ddG.shape)
        
        
        # running the model
        srp_model.zero_grad()
        fcnn_model.zero_grad()
        srp_outs = srp_model(pair_tensors)
        ddg_pred = fcnn_model(srp_outs)
        # print(srp_outs.shape) #batch_size,15,20
        # print(ddg_pred.shape) #batch_size,1
        
        # computing loss, backpropagate and optimizing model
        loss = criterion(ddG, ddg_pred)
        # print(loss)
        loss.backward()
        optimizer.step()
        # srp_optimizer.step()
        # deepddg_optimizer.step()
        
        losses.append(loss)
        
    return torch.stack(losses).mean().item()

# learning_rates = [0.0001]
# eps=.01, weight_decay=0.01
learning_rates = [0.0001]
for i, learning_rate in enumerate(learning_rates):
    print("ith_start=", i)
    print("initializing variables ... ...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    beta1 = 0.5
    batch_size = 100
    n_epochs = 50
    N_neighbors = 15
    run_no = 2
    print("batch_size=", batch_size)
    print("n_epochs=", n_epochs)
    print("init_lr=", learning_rate) 
    print("beta1=", beta1)
    print("N_neighbors=", N_neighbors)
    
    print("initializing models, loss function and optimizers ... ...") 
    srp_model = SRP(in_features=51, out_features=20).to(device)
    fcnn_model = FCNNS(in_features=N_neighbors*20).to(device)
    criterion = nn.MSELoss()
    optimizer = optim.Adam([{"params":srp_model.parameters()}, {"params": fcnn_model.parameters()}], lr=learning_rate, eps=.01, weight_decay=0.01)
    # srp_optimizer = optim.Adam(srp_model.parameters(), lr=learning_rate, betas=(beta1, 0.999), weight_decay=0.01)
    # deepddg_optimizer = optim.Adam(fcnn_model.parameters(), lr=learning_rate, betas=(beta1, 0.999), weight_decay=0.01)
    
    print("Printing the number of parameters of SRP and FCNN.")
    count_params(srp_model)
    count_params(fcnn_model)
    
    print("loading training dataset ... ...")
    train_dataset = DeepDDGDataset(file="data/dataset_4_train_keep.csv", data_dir="data/features_train/")
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    print("train dataset len:", train_dataset.__len__())
    print("train loader size:", len(train_loader))
    print("successfully loaded training dataset ... ...")
    
    print("training models ... ...")
    best_loss = np.inf        
    train_losses = []
    for epoch in range(1, n_epochs+1):
        train_loss = train()    
        train_losses.append(train_loss)
        print("[{}/{}] loss: {:.4f}".format(epoch, n_epochs, train_loss))
        
        if train_loss < best_loss:
            torch.save(srp_model.state_dict(), "outputs/models/run_{}_srp_model_{}.pth".format(run_no, i))
            torch.save(fcnn_model.state_dict(), "outputs/models/run_{}_srp_model_{}.pth".format(run_no, i))
            
        if epoch%10==0:
            plt.plot(train_losses)
            plt.show()
        
        # print(optimizer.param_groups[0]['lr'])            
    print("train_losses=", train_losses)