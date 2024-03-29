"""
reference:
    loss weight: 
        https://pytorch.org/docs/stable/generated/torch.nn.BCEWithLogitsLoss.html
        https://discuss.pytorch.org/t/weight-vs-pos-weight-in-nn-bcewithlogitsloss/114859/4
        https://www.dacon.io/competitions/open/235647/codeshare/1789
    multi gpu:
        https://medium.com/daangn/pytorch-multi-gpu-%ED%95%99%EC%8A%B5-%EC%A0%9C%EB%8C%80%EB%A1%9C-%ED%95%98%EA%B8%B0-27270617936b
    argparser list:
        https://stackoverflow.com/questions/15753701/how-can-i-pass-a-list-as-a-command-line-argument-with-argparse
"""

import argparse
import torch
import torch.nn as nn
import torch.optim as optim

import preprocess
from argument import arg_as_list
from dataset import load_data, create_dataset
from model import get_model, get_pretrained_model
from train import train
from log import initiate_wandb


def main(args):
    preprocess.customize_seed(args.seed)
    initiate_wandb(args)

    ## data preprocessing
    if args.data_preprocessing:
        useful_dicom_list, original_annotation_list = preprocess.get_dataset(args)
        print(original_annotation_list)
        exit()
        useful_dicom_path_list = preprocess.get_path(useful_dicom_list, args)
        
        preprocess.dicom2png(useful_dicom_path_list, args)
        preprocess.dicom2png_overlay(original_annotation_list, args)

    ## pad the original image & get annotation coordintaes
    if args.pad_image:
        preprocess.pad_original_image(args)
        preprocess.pad_overlaid_image(args)
        ## after padding, annotation should be manually done by using ./create data/select_point.py

    ## create dataset from padded images & annotation text file
    if args.create_dataset: 
        create_dataset(args)

    ## load data into a form that can be fed into the model
    if not args.progressive_erosion:
        train_loader, val_loader, _ = load_data(args)
    else:
        train_loader, val_loader = 0, 0
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    print(f'Torch is running on {DEVICE}')

    ## load model & use multi-gpu
    if args.pretrained:
        model = get_pretrained_model(args, DEVICE)
    else:
        model = get_model(args, DEVICE)

    if args.multi_gpu:
        model = nn.DataParallel(model)
        model.cuda()
    else:
        model.cuda()

    ## set loss function & optimizer
    if args.progressive_weight:
        loss_fn_pixel = None
    else:
        weight = 1
        loss_fn_pixel = nn.BCEWithLogitsLoss(pos_weight=torch.tensor([weight], device=DEVICE))
    loss_fn_geometry = nn.MSELoss()
    loss_fn_angle = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=args.lr)

    ## train model
    train(
        args, DEVICE, model, loss_fn_pixel, loss_fn_geometry, loss_fn_angle, 
        optimizer, train_loader, val_loader
    )


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    ## boolean arguments
    parser.add_argument('--data_preprocessing', action='store_true', help='whether to do data preprocessing or not')
    parser.add_argument('--pad_image', action='store_true', help='whether to pad the original image')
    parser.add_argument('--create_dataset', action='store_true', help='whether to create dataset or not')
    parser.add_argument('--multi_gpu', action='store_true', help='whether to use multiple gpus or not')
    parser.add_argument('--no_sigmoid', action='store_true', help='whether not to use sigmoid at the end of the model')
    parser.add_argument('--pixel_loss', action='store_true', help='whether to use only pixel loss')
    parser.add_argument('--geom_loss', action='store_true', help='whether to use only geometry loss')
    parser.add_argument('--angle_loss', action='store_true', help='whether to use only angular loss')
    parser.add_argument('--augmentation', action='store_true', help='whether to use augmentation')
    parser.add_argument('--patience', action='store_true', help='whether to stop when loss does not decrease')
    parser.add_argument('--progressive_erosion', action='store_true', help='whether to use progressive erosion')
    parser.add_argument('--progressive_weight', action='store_true', help='whether to use progressive weight')
    parser.add_argument('--pretrained', action='store_true', help='whether to pretrained model')
    parser.add_argument('--wandb', action='store_true', help='whether to use wandb or not')
    parser.add_argument('--wandb_sweep', action='store_true', help='whether to use wandb or not')
    parser.add_argument('--no_image_save', action='store_true', help='whether to save image or not')

    ## get dataset
    parser.add_argument('--excel_path', type=str, default="./xlsx/dataset.xlsx", help='path to dataset excel file')

    ## data preprocessing
    parser.add_argument('--dicom_data_path', type=str, default="./data/dicom_data", help='path to the dicom dataset')
    parser.add_argument('--dicom_to_png_path', type=str, default="./data/dicom_to_png", help='path to save dicom to png preprocessed data')
    parser.add_argument('--overlaid_image', type=str, default="./data/overlay_image_to_label", help='path to all the data from overlaying')
    parser.add_argument('--overlaid_image_only', type=str, default="./data/overlay_only", help='path to save overlaid data')
    parser.add_argument('--overlaid_padded_image', type=str, default="./data/overlay_padded_image", help='path to save padded data')
    parser.add_argument('--padded_image', type=str, default="./data/padded_image", help='path to save padded data')

    ## hyperparameters - data
    parser.add_argument('--dataset_path', type=str, default="./data/dataset", help='dataset path')
    parser.add_argument('--dataset_csv_path', type=str, default="./xlsx/dataset.csv", help='dataset excel file path')
    parser.add_argument('--test_dataset_csv_path', type=str, default="./xlsx/test_dataset.csv", help='dataset excel file path')
    parser.add_argument('--annotation_text_path', type=str, default="./data/annotation_text_files", help='annotation text file path')
    parser.add_argument('--annotation_text_name', type=str, default="annotation_label8.txt", help='annotation text file name')
    parser.add_argument('--test_annotation_text_name', type=str, default="annotation_label6_test.txt", help='annotation text file name')
    parser.add_argument('--dataset_split', type=int, default=9, help='dataset split ratio')
    parser.add_argument('--dilate', type=int, default=2, help='dilate iteration')
    parser.add_argument('--dilation_decrease', type=int, default=5, help='dilation decrease in progressive erosion')
    parser.add_argument('--dilation_epoch', type=int, default=50, help='dilation per epoch')
    parser.add_argument('--image_path', type=str, default="./overlay_only", help='path to save overlaid data')
    parser.add_argument('--image_resize', type=int, default=512, help='image resize value')
    parser.add_argument('--batch_size', type=int, default=24, help='batch size')
    parser.add_argument('--delete_method', type=str, default="", help='how to delete unnecessary data in the xray images ["", "letter", "box"]')
    
    ## hyperparameters - model
    parser.add_argument('--seed', type=int, default=2022, help='seed customization for result reproduction')
    parser.add_argument('--input_channel', type=int, default=3, help='input channel size for UNet')
    parser.add_argument('--output_channel', type=int, default=6, help='output channel size for UNet')
    parser.add_argument('--encoder_depth', type=int, default=5, help='model depth for UNet')
    parser.add_argument("--decoder_channel", type=arg_as_list, default=[256,128,64,32,16], help='model decoder channels')
    parser.add_argument('--lr', '--learning_rate', type=float, default=1e-4, help='learning rate')
    parser.add_argument('--epochs', type=int, default=1000, help='number of epochs')
    parser.add_argument('--patience_threshold', type=int, default=10, help='early stopping threshold')
    parser.add_argument('--geom_loss_weight', type=int, default=1, help='weight of the loss function')
    parser.add_argument('--angle_loss_weight', type=int, default=1, help='weight of the loss function')

    ## hyperparameters - results
    parser.add_argument('--threshold', type=float, default=0.5, help='threshold for binary prediction')

    ## wandb
    parser.add_argument('--wandb_project', type=str, default="joint-replacement", help='wandb project name')
    parser.add_argument('--wandb_entity', type=str, default="yehyun-suh", help='wandb entity name')
    parser.add_argument('--wandb_name', type=str, default="temporary", help='wandb name')

    args = parser.parse_args()
    main(args)