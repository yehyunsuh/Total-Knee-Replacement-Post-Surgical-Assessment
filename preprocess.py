import pydicom
import pandas as pd
import numpy as np
import os
import cv2
import torch
import random

from glob import glob
from tqdm import tqdm
from PIL import Image

def get_dataset(args):
    df = pd.read_excel(f'{args.excel_path}')
    df = df[df['annotation_image'].notna()]
    df = df.fillna(0)
    val_list = df.values.tolist()

    useful_dicom = []
    for i in range(len(val_list)):
        for j in range(len(val_list[i])):
            if val_list[i][j] != 0:
                useful_dicom.append(val_list[i][j].split("_")[-1])

    return useful_dicom, val_list

def get_path(useful_dicoms, args):
    tmp_dicom_lists = glob(f'{args.dicom_data_path}/*')
    tmp, tmp2, tmp3, dicom_lists = [], [], [], []
    for dicom_list in tmp_dicom_lists:
        tmp.append(glob(f'{dicom_list}/*')[0])
    for dicom_list in tmp:
        tmp2.append(glob(f'{dicom_list}/*')[0])
    for dicom_list in tmp2:
        tmp3.append(glob(f'{dicom_list}/*'))
    for list in tmp3:
        for dicom_list in list:
            dicom_lists.append(glob(f'{dicom_list}/*'))
    
    ## extract only useful paths from dicom_lists
    useful_dicoms_list = []

    for i in range(len(dicom_lists)):
        if dicom_lists[i][0].split("/")[-1] in useful_dicoms:
            useful_dicoms_list.append(dicom_lists[i][0])

    return sorted(useful_dicoms_list)

def get_pixel_array(dcm_info, path, data_name, count, args):
    dcm_img = dcm_info.pixel_array

    # # original image
    # show_img = Image.fromarray(dcm_img)

    # # normalized image
    norm = (dcm_img - np.min(dcm_img)) / (np.max(dcm_img) - np.min(dcm_img))
    norm_img = np.uint8(norm*255)
    show_img = Image.fromarray(norm_img)

    # show_img.save(f'{args.dicom_to_png_path}/original_image/{path[0]}_{path[1]}_{path[2]}_{count}_{data_name}.png')
    show_img.save(f'{args.dicom_to_png_path}/original_image/{path[0]}_{path[1]}_{path[2]}_{path[3]}_{data_name}.png')
    count += 1
    # show_img.show()
    return count

def get_overlay_array(dcm_info, path, data_name, count, args):
    dcm_img = dcm_info.overlay_array(0x6000)
    for i in range(len(dcm_img)):
        for j in range(len(dcm_img[i])):
            if dcm_img[i][j] == 1:
                dcm_img[i][j] = 254
    show_img = Image.fromarray(dcm_img)

    # show_img.save(f'{args.dicom_to_png_path}/annotation_image/{path[0]}_{path[1]}_{path[2]}_{count}_{data_name}.png')
    show_img.save(f'{args.dicom_to_png_path}/annotation_image/{path[0]}_{path[1]}_{path[2]}_{path[3]}_{data_name}.png')
    count += 1
    # show_img.show()
    return count
        
def overlay_two_images(original_annotation_list, args):
    count = 0

    for i in tqdm(range(len(original_annotation_list))):
    # for i in range(len(original_annotation_list)):
        # print(f"\n----- original: {original_annotation_list[i][0]}, annotation: {original_annotation_list[i][-1]} -----")

        try:
            split_original = original_annotation_list[i][0].split("_")
            split_annotation = original_annotation_list[i][-1].split("_")

            original_path = f"./data/{split_original[0]}/{split_original[1]}/{split_original[2]}/{split_original[3]}/{split_original[4]}"
            annotation_path = f"./data/{split_annotation[0]}/{split_annotation[1]}/{split_annotation[2]}/{split_annotation[3]}/{split_annotation[4]}"

            original_dcm = pydicom.dcmread(original_path)
            annotation_dcm = pydicom.dcmread(annotation_path)

            original_arr = original_dcm.pixel_array
            annotation_arr = annotation_dcm.overlay_array(0x6000)

            # print(f"original image size: \t{original_arr.shape}")
            # print(f"annotation image size: \t{annotation_arr.shape}")
            # print(f"annotation overlay range: \t {annotation_dcm[0x6000,0x0050]}")

            ## todo: filling width
            # if original_arr.shape[0] < annotation_arr.shape[0]:
            left_fill = annotation_dcm[0x6000,0x0050][1]-1
            middle_fill = len(annotation_arr[0])
            right_fill = len(original_arr[0])-(annotation_dcm[0x6000,0x0050][1]-1)-len(annotation_arr[0])

            new_arr = np.array(
                [[0]*(left_fill+middle_fill+right_fill) for _ in range(len(annotation_arr))]
            )

            for j in range(len(annotation_arr)):
                left = np.array([0]*left_fill)
                middle = annotation_arr[j]
                right = np.array([0]*right_fill)

                tmp = np.concatenate((left, middle), axis=0)
                new_arr[j] = np.concatenate((tmp, right), axis=0)

            ## todo: filling height
            if original_arr.shape[0] > annotation_arr.shape[0]:
                upper_fill = annotation_dcm[0x6000,0x0050][0]-1
                middle_fill = len(annotation_arr)
                lower_fill = len(original_arr)-(annotation_dcm[0x6000,0x0050][0]-1)-len(annotation_arr)
                # print(f'lower fill: {len(original_arr)} - {annotation_dcm[0x6000,0x0050][0]-1} - {len(annotation_arr)} = {lower_fill}')

                high = np.zeros((upper_fill, original_arr.shape[1]))
                low = np.zeros((lower_fill, original_arr.shape[1]))

                tmp = np.vstack([high, new_arr])
                new_arr = np.vstack([tmp, low])

            change_arr = np.asarray(new_arr, dtype = np.int32)

            for j in range(len(change_arr)):
                for k in range(len(change_arr[j])):
                    if change_arr[j][k] == 1:
                        change_arr[j][k] = 254

            # print(original_arr.shape)
            # print(f"annotation image size: \t{change_arr.shape}")

            original_img = Image.fromarray(original_arr)
            norm = (original_img - np.min(original_img)) / (np.max(original_img) - np.min(original_img))
            norm_img = np.uint8(norm*255)
            original = Image.fromarray(norm_img)
            original.save(f'{args.overlaid_image}/{i}_original.png')
            
            annotation_img = Image.fromarray(change_arr)
            norm = (annotation_img - np.min(annotation_img)) / (np.max(annotation_img) - np.min(annotation_img))
            norm_img = np.uint8(norm*255)
            annotation = Image.fromarray(norm_img)
            annotation.save(f'{args.overlaid_image}/{i}_annotation.png')
            # annotation.show()

            ## todo: if final annotation and original image size is same
            if original_arr.shape == change_arr.shape:
                org = cv2.imread(f'{args.overlaid_image}/{i}_original.png', cv2.IMREAD_COLOR)
                ann = cv2.imread(f'{args.overlaid_image}/{i}_annotation.png', cv2.IMREAD_COLOR)
                overlay = cv2.add(org, ann)
                cv2.imwrite(f'{args.overlaid_image_only}/{i}_overlay.png',overlay)
                cv2.imwrite(f'{args.overlaid_image}/{i}_overlay.png',overlay)

            ## todo: 
            ## 1. when height is different
            ## (2. when width is different)
            else:
                org = cv2.imread(f'{args.overlaid_image}/{i}_original.png', cv2.IMREAD_COLOR)
                ann = cv2.imread(f'{args.overlaid_image}/{i}_annotation.png', cv2.IMREAD_COLOR)
                cut = ann.shape[0] - org.shape[0]

                """
                ## upper and middle will not be used - only lower will be used

                ## todo: 1-1 crop upper
                upper_cropped = ann[cut:,:].copy()
                upper_overlay = cv2.add(org, upper_cropped)
                cv2.imwrite(f'./tmp/{i}_overlay_cut_upper.png',upper_overlay)

                ## todo: 1-2 crop up & low
                try:
                    middle_cropped = ann[int((cut/2)):len(ann)-int((cut/2)),:].copy()
                    middle_overlay = cv2.add(org, middle_cropped)
                except:
                    middle_cropped = ann[int((cut/2)):len(ann)-int((cut/2))-1,:].copy()
                    middle_overlay = cv2.add(org, middle_cropped)
                cv2.imwrite(f'./tmp/{i}_overlay_cut_up_low.png',middle_overlay)
                """

                ## todo: 1-3 crop lower 
                lower_cropped = ann[:len(ann)-cut,:].copy()
                lower_overlay = cv2.add(org, lower_cropped)
                # cv2.imwrite(f'./tmp/{i}_overlay_cut_lower.png',lower_overlay)
                cv2.imwrite(f'{args.overlaid_image_only}/{i}_overlay.png',lower_overlay)
                cv2.imwrite(f'{args.overlaid_image}/{i}_overlay.png',lower_overlay)

            count += 1
        
        except Exception as e:
            error_message = f'Error on {original_annotation_list[i]} -> {e}'
            print(error_message)
            # printsave(error_message)
            pass


def printsave(*a):
    file = open('error_log.txt','a')
    print(*a,file=file)
 

def dicom2png(dicom_lists, args):
    if not os.path.exists(f'{args.dicom_to_png_path}'):                  os.mkdir(f'{args.dicom_to_png_path}')
    if not os.path.exists(f'{args.dicom_to_png_path}/original_image'):   os.mkdir(f'{args.dicom_to_png_path}/original_image')
    if not os.path.exists(f'{args.dicom_to_png_path}/annotation_image'): os.mkdir(f'{args.dicom_to_png_path}/annotation_image')
    count = 0
    
    print("---------- Starting Preprocessing ----------")
    for dicom_list in tqdm(dicom_lists):
        path = dicom_list.split('/')[2:6]
        data_name = dicom_list.split('/')[-1]
        dcm_info = pydicom.read_file(dicom_list, force=True)
        
        try: 
            try:
                count = get_pixel_array(dcm_info, path, data_name, count, args)
            except:
                count = get_overlay_array(dcm_info, path, data_name, count, args)
        except Exception as e:
            print(f'Error on {dicom_list} -> {e}')

    print("---------- Preprocessing Done ----------\n")

def dicom2png_overlay(original_annotation_list, args):
    if not os.path.exists(f'{args.overlaid_image}'):      os.mkdir(f'{args.overlaid_image}')
    if not os.path.exists(f'{args.overlaid_image_only}'): os.mkdir(f'{args.overlaid_image_only}')

    print("---------- Starting Overlay Process ----------")
    overlay_two_images(original_annotation_list, args)
    print("---------- Overlay Process Done ----------\n")

def customize_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)  # if use multi-GPU
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False
    np.random.seed(seed)
    random.seed(seed)


## todo: currently padded images has the annotations. need to fix.
def pad_original_image(args):
    print("---------- Starting Padding Original Image Process ----------")
    if not os.path.exists(f'{args.padded_image}'): 
        os.mkdir(f'{args.padded_image}')
    original_image_path = sorted(glob(f'{args.overlaid_image}/*_original.png'))

    for overlaid_path in tqdm(original_image_path):
        image_num = overlaid_path.split('/')[-1].split('_')[0]
        overlaid_image_array = cv2.imread(overlaid_path)
        fill = abs(overlaid_image_array.shape[0] - overlaid_image_array.shape[1])
        
        ## when height > width
        if overlaid_image_array.shape[0] > overlaid_image_array.shape[1]:
            padded_array = np.zeros((
                overlaid_image_array.shape[0], overlaid_image_array.shape[0], 3
            ))
        
            for i in range(overlaid_image_array.shape[0]):
                left = np.zeros((int(fill/2),3))
                middle = np.array(overlaid_image_array[i])
                if fill % 2 == 0: right = np.zeros((int(fill/2),3))
                else:             right = np.zeros((int(fill/2)+1,3))

                tmp = np.concatenate((left, middle), axis=0)
                padded_array[i] = np.concatenate((tmp, right), axis=0)

        ## when height < width
        elif overlaid_image_array.shape[0] < overlaid_image_array.shape[1]:            
            padded_array = np.zeros((
                overlaid_image_array.shape[1], overlaid_image_array.shape[1], 3
            ))

            high = np.zeros((int(fill/2),overlaid_image_array.shape[1],3))
            if fill % 2 == 0: low = np.zeros((int(fill/2),overlaid_image_array.shape[1],3))
            else:             low = np.zeros((int(fill/2)+1,overlaid_image_array.shape[1],3))

            tmp = np.vstack([high, overlaid_image_array])
            padded_array = np.vstack([tmp, low])
        
        ## when height == width
        else: 
            padded_array = np.zeros((
                overlaid_image_array.shape[0], overlaid_image_array.shape[1], 3
            ))
            padded_array = overlaid_image_array[:]

        norm = (padded_array - np.min(padded_array)) / (np.max(padded_array) - np.min(padded_array))
        norm_img = np.uint8(norm*255)
        padded_image = Image.fromarray(norm_img)
        padded_image.save(f'{args.padded_image}/{image_num}_pad.png')
    print("---------- Padding Original Image Process Done ----------")


def pad_overlaid_image(args):
    print("---------- Starting Padding Overlaid Image Process ----------")
    if not os.path.exists(f'{args.overlaid_padded_image}'): 
        os.mkdir(f'{args.overlaid_padded_image}')
    overlaid_image_path = sorted(glob(f'{args.overlaid_image}/*_overlay.png'))

    for overlaid_path in tqdm(overlaid_image_path):
        image_num = overlaid_path.split('/')[-1].split('_')[0]
        overlaid_image_array = cv2.imread(overlaid_path)
        fill = abs(overlaid_image_array.shape[0] - overlaid_image_array.shape[1])
        
        ## when height > width
        if overlaid_image_array.shape[0] > overlaid_image_array.shape[1]:
            padded_array = np.zeros((
                overlaid_image_array.shape[0], overlaid_image_array.shape[0], 3
            ))
        
            for i in range(overlaid_image_array.shape[0]):
                left = np.zeros((int(fill/2),3))
                middle = np.array(overlaid_image_array[i])
                if fill % 2 == 0: right = np.zeros((int(fill/2),3))
                else:             right = np.zeros((int(fill/2)+1,3))

                tmp = np.concatenate((left, middle), axis=0)
                padded_array[i] = np.concatenate((tmp, right), axis=0)

        ## when height < width
        elif overlaid_image_array.shape[0] < overlaid_image_array.shape[1]:            
            padded_array = np.zeros((
                overlaid_image_array.shape[1], overlaid_image_array.shape[1], 3
            ))

            high = np.zeros((int(fill/2),overlaid_image_array.shape[1],3))
            if fill % 2 == 0: low = np.zeros((int(fill/2),overlaid_image_array.shape[1],3))
            else:             low = np.zeros((int(fill/2)+1,overlaid_image_array.shape[1],3))

            tmp = np.vstack([high, overlaid_image_array])
            padded_array = np.vstack([tmp, low])
        
        ## when height == width
        else: 
            padded_array = np.zeros((
                overlaid_image_array.shape[0], overlaid_image_array.shape[1], 3
            ))
            padded_array = overlaid_image_array[:]

        norm = (padded_array - np.min(padded_array)) / (np.max(padded_array) - np.min(padded_array))
        norm_img = np.uint8(norm*255)
        padded_image = Image.fromarray(norm_img)
        padded_image.save(f'{args.overlaid_padded_image}/{image_num}_pad.png')
    print("---------- Padding Original Image Process Done ----------")
