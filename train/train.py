import argparse
import os
import pandas as pd
import torch
import torch.nn as nn
import pytorch_lightning as pl
from pytorch_lightning import Trainer
from pytorch_lightning import seed_everything
import wandb
from datetime import datetime

from model import FloodModel


if __name__ =='__main__':
    
    # Removing this for Udacity, but useful for further usage
#     wandb.login() # This will look for WANDB_API_KEY env variable provided by secrets.env
#     wandb.init(project="Driven-Data-Floodwater-Mapping", entity="effective-altruism-techs")

    parser = argparse.ArgumentParser()

    # our hyperparameters all in a hparams dictionary
    parser.add_argument('--hparams', type=dict, default={
        # Optional hparams, set these in the hparams dictionary in the main notebook before training
        "architecture": "Unet",
        "backbone": "resnet34",
        "weights": "imagenet",
        "lr": 1e-3,
        "min_epochs": 6,
        "max_epochs": 30,
        "patience": 4,
        "batch_size": 32,
        "num_workers": 0,
        "val_sanity_checks": 0,
        "fast_dev_run": False,
        "output_path": "model-outputs",
        "log_path": "tensorboard_logs",
        "gpu": 1,
    })
    
    # no need for the args below for hyperparameter tuning.
    
#     # hyperparameters sent by the client are passed as command-line arguments to the script.
#     parser.add_argument('--architecture', type=str, default='Unet')
#     parser.add_argument('--gpus', type=int, default=1) # could be used for multi-GPU as well
#     parser.add_argument('--backbone', type=str, default='resnet34')
#     parser.add_argument('--weights', type=str, default="imagenet")
#     parser.add_argument('--lr', type=float, default=1e-3)
#     parser.add_argument('--min_epochs', type=int, default=6)
#     parser.add_argument('--max_epochs', type=int, default=30)
#     parser.add_argument('--patience', type=int, default=4)
#     parser.add_argument('--batch_size', type=int, default=32)
#     parser.add_argument('--num_workers', type=int, default=0)
#     parser.add_argument('--val_sanity_checks', type=int, default=0)
#     parser.add_argument('--fast_dev_run', type=bool, default=False)
#     parser.add_argument('--log_path', type=str, default="tensorboard_logs")

    # Data, model, and output directories. Passed by sagemaker with default to os env variables
    parser.add_argument('-o','--output-data-dir', type=str, default=os.environ['SM_OUTPUT_DATA_DIR'])
    parser.add_argument('-m','--model-dir', type=str, default=os.environ['SM_MODEL_DIR'])
    parser.add_argument('--data_s3_uri', type=str, default='s3://sagemaker-us-east-1-209161541854/floodwater_data')
    parser.add_argument('--train_features', type=str, default='s3://sagemaker-us-east-1-209161541854/floodwater_data/train_features')
    parser.add_argument('--train_labels', type=str, default='s3://sagemaker-us-east-1-209161541854/floodwater_data/train_labels')
    

    args, _ = parser.parse_known_args()
    print(args)
    
    seed_everything(9) # set a seed for reproducibility, seeds torch, numpy, python.random
    
    data_dir = "/opt/ml/input/data/data_s3_uri"
    
#     print(os.listdir("/opt/ml/input/data/"))
#     print(os.listdir("/opt/ml/input/data/data_s3_uri"))
#     print(os.listdir("/opt/ml/input/data/data_s3_uri/train_features"))  
    
    # Read csv for training
    train_df = pd.read_csv(os.path.join(data_dir, "train_df.csv"))
    train_x = train_df[['chip_id', 'vv_path', 'vh_path']]
    train_y = train_df[['chip_id', 'label_path']]
    
    # Read csv for validation
    val_df = pd.read_csv(os.path.join(data_dir, "val_df.csv"))
    val_x = val_df[['chip_id', 'vv_path', 'vh_path']]
    val_y = val_df[['chip_id', 'label_path']]
        
    data_dict = {
        "x_train": train_x,
        "x_val": val_x,
        "y_train": train_y,
        "y_val": val_y,
    }
    
    hparams = args.hparams
    hparams.update(data_dict)
    
    print(hparams)
    
#     # Now we have all parameters and hyperparameters available and we need to match them with sagemaker 
#     # structure. default_root_dir is set to out_put_data_dir to retrieve from training instances all the 
#     # checkpoint and intermediary data produced by lightning
#     mnistTrainer=pl.Trainer(hparams=args.hparams)

    # Set up our classifier class, passing params to the constructor
    ss_flood_model = FloodModel(hparams=hparams)
    
    # Runs model training 
    ss_flood_model.fit() # orchestrates our model training
    
    now = datetime.now() # current date and time
    date_time = now.strftime("%Y-%m-%d-%H-%M-%S")
    
    # architecture and backbone names
    architecture_name = hparams['architecture']
    backbone_name = hparams['backbone']
    
    # After model has been trained, save its state into model_dir which is then copied to back S3
    with open(os.path.join(args.model_dir, f'model_{architecture_name}_{backbone_name}_{date_time}.pth'), 'wb') as f:
        torch.save(ss_flood_model.state_dict(), f)
        
#     wandb.finish()