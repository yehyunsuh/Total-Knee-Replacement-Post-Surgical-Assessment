"""
Reference:
    heatmap: 
        https://stackoverflow.com/questions/53467215/convert-pytorch-cuda-tensor-to-numpy-array
        https://stackoverflow.com/questions/33282368/plotting-a-2d-heatmap 
    tensor to image: 
        https://hello-bryan.tistory.com/429
    two tensor overlay:
        https://stackoverflow.com/questions/10640114/overlay-two-same-sized-images-in-python
        https://discuss.pytorch.org/t/create-heatmap-over-image/41408
    ValueError: pic should be 2/3 dimensional. Got 4 dimensions:
        https://stackoverflow.com/questions/64364239/pytorch-error-valueerror-pic-should-be-2-3-dimensional-got-4-dimensions
    1 channel to 3 channel:
        https://stackoverflow.com/questions/71957324/is-there-a-pytorch-transform-to-go-from-1-channel-data-to-3-channels    
    TypeError: Cannot handle this data type: (1, 1, 512), <f4:
        https://stackoverflow.com/questions/60138697/typeerror-cannot-handle-this-data-type-1-1-3-f4
    KeyError: ((1, 1, 512), '|u1'):
        https://stackoverflow.com/questions/57621092/keyerror-1-1-1280-u1-while-using-pils-image-fromarray-pil
    permute tensor:
        https://stackoverflow.com/questions/71880540/how-to-change-an-image-which-has-dimensions-512-512-3-to-a-tensor-of-size
    draw circle in image:
        https://dsbook.tistory.com/102
    >  - Expected Ptr<cv::UMat> for argument 'img':
        https://github.com/opencv/opencv/issues/18120
        cv2 functions expects numpy array
    draw line in image:
        https://antilibrary.org/2705
    draw text in image:
        https://www.geeksforgeeks.org/python-pil-imagedraw-draw-text/
    draw histogram using dataframe:
        https://ordo.tistory.com/69
    draw bland altman plot:
        https://datainsider.tistory.com/54
    calculate & visualize z-score:
        https://blog.naver.com/PostView.naver?blogId=youji4ever&logNo=222891886830&categoryNo=0&parentCategoryNo=0&viewDate=&currentPage=1&postListTopCurrentPage=1&from=postView
    statsmodel:
        https://github.com/statsmodels/statsmodels/blob/main/statsmodels/graphics/agreement.py
        https://github.com/statsmodels/statsmodels/blob/main/statsmodels/graphics/utils.py
"""

import torch
import torchvision
import matplotlib.pyplot as plt
import torchvision.transforms.functional as TF
import numpy as np
import cv2
import pandas as pd
import matplotlib.pyplot as plt  
import seaborn as sns

from tqdm import tqdm
from PIL import Image, ImageDraw, ImageFont


def save_label_image(args, label_tensor, data_path, label_list, epoch):
    original = Image.open(f'{args.padded_image}/{data_path}').resize((args.image_resize,args.image_resize)).convert("RGB")
    for i in range(args.output_channel):
        plt.imshow(label_tensor[0][i].detach().cpu().numpy(), cmap='hot', interpolation='nearest')
        plt.savefig(f'./plot_results/{args.wandb_name}/annotation/epoch{epoch}_label{i}.png')

        x, y = int(label_list[2*i+1]), int(label_list[2*i])
        pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(original), (x,y), 15, (0, 0, 255),-1))
        pixel_overlaid_image.save(f'./plot_results/{args.wandb_name}/annotation/pixel_label{i}.png')

        background = label_tensor[0][i].unsqueeze(0)
        background = TF.to_pil_image(torch.cat((background, background, background), dim=0))
        overlaid_image = Image.blend(original, background , 0.3)
        overlaid_image.save(f'./plot_results/{args.wandb_name}/annotation/epoch{epoch}_overlaid{i}.png')


def save_heatmap(preds, preds_binary, args, epoch):
    for i in range(len(preds[0])):
        plt.imshow(preds[0][i].detach().cpu().numpy(), cmap='hot', interpolation='nearest')
        plt.savefig(f'./plot_results/{args.wandb_name}/label{i}/epoch_{epoch}_heatmap.png')
        torchvision.utils.save_image(preds_binary[0][i], f'./plot_results/{args.wandb_name}/label{i}/epoch_{epoch}.png')


def prediction_plot(args, idx, highest_probability_pixels_list, i, original):
    x, y = int(highest_probability_pixels_list[idx][i][0][1]), int(highest_probability_pixels_list[idx][i][0][0])
    pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(original), (x,y), 15, (255, 0, 0),-1))
    pixel_overlaid_image.save(f'./plot_results/{args.wandb_name}/overlaid/label{i}/val{idx}_pixel_overlaid.png')


def ground_truth_prediction_plot(args, idx, original, epoch, highest_probability_pixels_list, label_list, i):
    x, y = int(highest_probability_pixels_list[idx][i][0][1]), int(highest_probability_pixels_list[idx][i][0][0])
    pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(original), (x,y), 15, (255, 0, 0),-1))

    x, y = int(label_list[2*i+1]), int(label_list[2*i])
    pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(pixel_overlaid_image), (x,y), 15, (0, 0, 255),-1))

    pixel_overlaid_image.save(f'./plot_results/{args.wandb_name}/overlaid/label{i}/epoch{epoch}_val{idx}_pred_gt.png')
    

def save_overlaid_image(args, idx, predicted_label, data_path, highest_probability_pixels_list, label_list, epoch):
    image_path = f'{args.padded_image}/{data_path}'
    original = Image.open(image_path).resize((args.image_resize,args.image_resize)).convert("RGB")
    pixel_overlaid_image = Image.open(image_path).resize((args.image_resize,args.image_resize)).convert("RGB")
    count = 0
    # print(len(label_list))
    for i in range(args.output_channel):
        background = predicted_label[0][i].unsqueeze(0)
        background = TF.to_pil_image(torch.cat((background, background, background), dim=0))
        overlaid_image = Image.blend(original, background , 0.3)
        # overlaid_image.save(f'./plot_results/{args.wandb_name}/overlaid/label{i}/val{idx}_overlaid.png')
        # overlaid_image.save(f'./plot_results/{args.wandb_name}/label{i}/epoch_{epoch}_overlaid.png')
        if idx == 13: 
            # ground_truth_prediction_plot(args, idx, original, epoch, highest_probability_pixels_list, label_list, i)
            x, y = int(highest_probability_pixels_list[idx][i][0][1]), int(highest_probability_pixels_list[idx][i][0][0])
            pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(pixel_overlaid_image), (x,y), 10, (255, 0, 0),-1))
            
            # print(count)
            if i == 2 or i == 5:
                count += 1
            x, y = int(label_list[2*i+1]), int(label_list[2*i])
            count += 1
            pixel_overlaid_image = Image.fromarray(cv2.circle(np.array(pixel_overlaid_image), (x,y), 10, (0, 0, 255),-1))
            # pixel_overlaid_image.save(f'./plot_results/{args.wandb_name}/overlaid/label{i}/epoch{epoch}_val{idx}_pred_gt.png')

        # if i != args.output_channel:
        #     prediction_plot(args, idx, highest_probability_pixels_list, i, original)

            # if (epoch == 0 or epoch % args.dilation_epoch == (args.dilation_epoch-1)) and idx == 1:
            #     ground_truth_prediction_plot(args, idx, original, epoch, highest_probability_pixels_list, label_list, i)
    if idx == 13:
        pixel_overlaid_image.save(f'./plot_results/{args.wandb_name}/overlaid/all/epoch{epoch}_val{idx}.png')


def save_predictions_as_images(args, loader, model, epoch, highest_probability_pixels_list, label_list_total, device="cuda"):
    model.eval()

    for idx, (image, label, data_path, label_list) in enumerate(tqdm(loader)):
        image = image.to(device=device)
        label = label.to(device=device)
        data_path = data_path[0]

        with torch.no_grad():
            if args.pretrained: preds = model(image)
            else:               preds = torch.sigmoid(model(image))
            preds_binary = (preds > args.threshold).float()

        if epoch % 5 == 0:
            save_overlaid_image(args, idx, preds_binary, data_path, highest_probability_pixels_list, label_list, epoch)
        ## TODO: record heatmaps even if the loss hasn't decreased
        # if epoch % args.dilation_epoch == (args.dilation_epoch-1) and idx == 0: 
        if epoch % 50 == 0 and idx == 13:
            save_label_image(args, label, data_path, label_list, epoch)
        # if args.pixel_loss and (epoch % 10 == 0 or epoch % args.dilation_epoch == (args.dilation_epoch-1)):
        #     if args.dilation_epoch >= 10:
        #         save_overlaid_image(args, idx, preds_binary, data_path, highest_probability_pixels_list, label_list, epoch)
        #         if idx == 0:
        #             save_heatmap(preds, preds_binary, args, epoch)
        #     else:
        #         if epoch % 10 > 3 and epoch % 10 < 7:
        #             save_overlaid_image(args, idx, preds_binary, data_path, highest_probability_pixels_list, label_list, epoch)
        #             if idx == 0:
        #                 save_heatmap(preds, preds_binary, args, epoch)
                    

def printsave(path, *a):
    file = open(f'{path}.txt','a')
    print(*a,file=file)


def box_plot(args, mse_list):
    ## I can't make box plot of 3 different methods 
    ## I have to just save it as a file, and then create it from saved text files
    printsave(f'./plot_data/rmse_box_plot/txt_files/{args.wandb_name}_MSE_LIST', mse_list)


def draw_line(draw, line_pixel, rgb, line_width, pixels):
    draw.line(line_pixel[0], fill=rgb[0], width=line_width)
    draw.line(line_pixel[1], fill=rgb[0], width=line_width)
    draw.line(line_pixel[2], fill=rgb[2], width=line_width)
    draw.line(line_pixel[3], fill=rgb[2], width=line_width)
    draw.line(line_pixel[4], fill=rgb[1], width=line_width)
    return draw


def draw_text(draw, text_pixel, text, rgb, font):
    draw.text(text_pixel[0], text[0], fill=rgb[0], align ="left", font=font) 
    draw.text(text_pixel[1], text[1], fill=rgb[2], align ="left", font=font) 
    draw.text(text_pixel[2], text[2], fill=rgb[1], align ="left", font=font) 
    return draw


def angle_visualization(
        args, experiment, data_path, idx, epoch, highest_probability_pixels_list, label_list, i, angles, method, vis_type
    ):
    if method == "with label":
        image_path = f'{args.overlaid_padded_image}/{data_path[0]}'
        line_width, circle_size = 1, 4
    elif method == "without label":
        image_path = f'{args.padded_image}/{data_path[0]}'
        line_width, circle_size = 5, 8
    font_size = 30

    angle_overlaid_image = Image.open(image_path).resize((args.image_resize,args.image_resize)).convert("RGB")
    LDFA_text = f'dFA: {angles[0]:.2f}\nAnswer: {angles[3]:.2f}'
    MPTA_text = f'pTA: {angles[1]:.2f}\nAnswer: {angles[4]:.2f}'
    mHKA_text = f'FTA: {angles[2]:.2f}\nAnswer: {angles[5]:.2f}'
    red, green, blue = (255, 0, 0), (0,102,0), (0, 0, 255)

    rgb = [(255, 0, 0), (0,102,0), (0, 0, 255)]
    text = [LDFA_text, MPTA_text, mHKA_text]

    count, pixels = 0, []
    font = ImageFont.truetype("plot_data/font/Gidole-Regular.ttf", size=font_size)

    for i in range(args.output_channel):
        # x, y = int(highest_probability_pixels_list[idx][i][0][1]), int(highest_probability_pixels_list[idx][i][0][0])
        x, y = int(highest_probability_pixels_list[i][0][1]), int(highest_probability_pixels_list[i][0][0])
        pixels.append([x,y])
       
        if count <= 2: angle_overlaid_image = Image.fromarray(cv2.circle(np.array(angle_overlaid_image), (x,y), circle_size, red,-1))
        else:          angle_overlaid_image = Image.fromarray(cv2.circle(np.array(angle_overlaid_image), (x,y), circle_size, blue,-1))
        count += 1
    
    draw = ImageDraw.Draw(angle_overlaid_image)
    if args.output_channel == 6:
        line1 = ((pixels[0][0],pixels[0][1]),(pixels[2][0],pixels[2][1]))
        line2 = ((pixels[1][0],pixels[1][1]),(pixels[2][0],pixels[2][1]))
        line3 = ((pixels[3][0],pixels[3][1]),(pixels[4][0],pixels[4][1]))
        line4 = ((pixels[5][0],pixels[5][1]),(pixels[4][0],pixels[4][1]))
        line5 = ((pixels[5][0],pixels[5][1]),(pixels[2][0],pixels[2][1]))
        line_pixel = [line1, line2, line3, line4, line5]

        text_pixel = [
            (((pixels[0][0]+pixels[1][0])/2-170), (2*pixels[0][1]+5*pixels[1][1])/7),
            (((pixels[3][0]+pixels[5][0])/2-155), (4*pixels[3][1]+pixels[5][1])/5),
            (((pixels[0][0]+pixels[5][0])/2+30), (pixels[0][1]+pixels[5][1]*2)/3),   
        ]
    elif args.output_channel == 8:
        line1 = ((pixels[0][0],pixels[0][1]),(pixels[3][0],pixels[3][1]))
        line2 = ((pixels[1][0],pixels[1][1]),(pixels[3][0],pixels[3][1]))
        line3 = ((pixels[4][0],pixels[4][1]),(pixels[6][0],pixels[6][1]))
        line4 = ((pixels[7][0],pixels[7][1]),(pixels[6][0],pixels[6][1]))
        line5 = ((pixels[7][0],pixels[7][1]),(pixels[3][0],pixels[3][1]))
        line_pixel = [line1, line2, line3, line4, line5]

        text_pixel = [
            (((pixels[0][0]+pixels[1][0])/2-90), (2*pixels[0][1]+5*pixels[1][1])/7),
            (((pixels[4][0]+pixels[7][0])/2-90), (4*pixels[4][1]+pixels[7][1])/5),
            (((pixels[0][0]+pixels[7][0])/2+50), (pixels[0][1]+pixels[7][1])/2),   
        ]

    draw = draw_line(draw, line_pixel, rgb, line_width, pixels)

    if args.wandb_sweep:
        return angle_overlaid_image
    else:
        # draw = draw_text(draw, text_pixel, text, rgb, font)
        if method == "with label":
            angle_overlaid_image.save(f'./plot_results/{experiment}/angles/{epoch}_{vis_type}{idx}_angle_with_label.png')
        elif method == "without label":
            angle_overlaid_image.save(f'./plot_results/{experiment}/angles/{epoch}_{vis_type}{idx}_angle.png')
        return angle_overlaid_image


def draw_histogram(angle_name, df):
    title = angle_name.split("_")[0]

    plt.hist(df[angle_name], rwidth=0.9)
    plt.xlabel('Angle')
    plt.ylabel('Count')
    plt.title(f'Ground Truth {title}')

    plt.savefig(f'./plot_data/angle/{title}_histogram.png')
    plt.close()


def draw_scatterplot(y_name, x_name, df):
    x = np.linspace(min(df[x_name]),max(df[x_name]),100)
    y = np.linspace(min(df[y_name]),max(df[y_name]),100)

    plt.scatter(df[x_name], df[y_name], color='red', s=50)
    plt.plot(x, y, color='blue', linewidth=3, linestyle='--')
    plt.xlabel(f'Ground Truth {y_name}', fontsize=20)
    plt.ylabel(f'Predicted {y_name}', fontsize=20)
    plt.title(y_name, fontsize=30)
    plt.tick_params(labelsize=13)
    plt.tight_layout()
    plt.savefig(f'./plot_data/angle/{y_name}_scatter_pot.png')
    plt.close()


def draw_bland_altman(x_name, y_name, df):
    f, ax = plt.subplots(1)
    mean_diff_plot(df[x_name], df[y_name], ax = ax)
    plt.title(x_name, fontsize=30)
    plt.tight_layout()
    plt.savefig(f'./plot_data/angle/{x_name}_bland_altman.png')
    plt.close()


def draw_z_score(angle_list, df):
    # df = df.assign(LDFA_z_score = lambda x: x.LDFA.sub(x.LDFA.mean()).div(x.LDFA.std()))
    # df = df.assign(MPTA_z_score = lambda x: x.MPTA.sub(x.MPTA.mean()).div(x.MPTA.std()))
    # df = df.assign(mHKA_z_score = lambda x: x.mHKA.sub(x.mHKA.mean()).div(x.mHKA.std()))

    # df = df.assign(LDFA_GT_z_score = lambda x: x.LDFA_GT.sub(x.LDFA_GT.mean()).div(x.LDFA_GT.std()))
    # df = df.assign(MPTA_GT_z_score = lambda x: x.MPTA_GT.sub(x.MPTA_GT.mean()).div(x.MPTA_GT.std()))
    # df = df.assign(mHKA_GT_z_score = lambda x: x.mHKA_GT.sub(x.mHKA_GT.mean()).div(x.mHKA_GT.std()))

    df = df.assign(LDFA_z_score = lambda x: x.dFA.sub(x.dFA.mean()).div(x.dFA.std()))
    df = df.assign(MPTA_z_score = lambda x: x.pTA.sub(x.pTA.mean()).div(x.pTA.std()))
    df = df.assign(mHKA_z_score = lambda x: x.FTA.sub(x.FTA.mean()).div(x.FTA.std()))

    df = df.assign(LDFA_GT_z_score = lambda x: x.dFA_GT.sub(x.dFA_GT.mean()).div(x.dFA_GT.std()))
    df = df.assign(MPTA_GT_z_score = lambda x: x.pTA_GT.sub(x.pTA_GT.mean()).div(x.pTA_GT.std()))
    df = df.assign(mHKA_GT_z_score = lambda x: x.FTA_GT.sub(x.FTA_GT.mean()).div(x.FTA_GT.std()))

    for i in range(len(angle_list)):
        sns.displot(df[f'{angle_list[i]}_z_score'])
        plt.savefig(f'./plot_data/angle/{angle_list[i]}_z_score.png')
        plt.close()


def angle_graph(angles):
    # angle_list = ['LDFA', 'MPTA', 'mHKA', 'LDFA_GT', 'MPTA_GT', 'mHKA_GT']
    angle_list = ['dFA', 'pTA', 'FTA', 'dFA_GT', 'pTA_GT', 'FTA_GT']
    for i in range(len(angles)):
        for j in range(len(angles[i])):
            if j != 2 and j != 5:
                angles[i][j] = angles[i][j] - 90  
    
    df = pd.DataFrame(angles, columns=angle_list)
    for i in range(int(len(angle_list)/2)):
        draw_histogram(angle_list[i+3], df)
        draw_scatterplot(angle_list[i], angle_list[i+3], df)
        draw_bland_altman(angle_list[i], angle_list[i+3], df)
    # draw_z_score(angle_list, df)


def create_mpl_ax(ax=None):
    if ax is None:
        plt = _import_mpl()
        fig = plt.figure()
        ax = fig.add_subplot(111)
    else:
        fig = ax.figure

    return fig, ax


def mean_diff_plot(m1, m2, sd_limit=1.96, ax=None, scatter_kwds=None,
                   mean_line_kwds=None, limit_lines_kwds=None):
    fontsize = 20
    scattersize = 50
    fig, ax = create_mpl_ax(ax)

    if len(m1) != len(m2):
        raise ValueError('m1 does not have the same length as m2.')
    if sd_limit < 0:
        raise ValueError('sd_limit ({}) is less than 0.'.format(sd_limit))

    means = np.mean([m1, m2], axis=0)
    diffs = m1 - m2
    mean_diff = np.mean(diffs)
    std_diff = np.std(diffs, axis=0)

    scatter_kwds = scatter_kwds or {}
    if 's' not in scatter_kwds:
        scatter_kwds['s'] = scattersize
    mean_line_kwds = mean_line_kwds or {}
    limit_lines_kwds = limit_lines_kwds or {}
    for kwds in [mean_line_kwds, limit_lines_kwds]:
        if 'color' not in kwds:
            kwds['color'] = 'gray'
        if 'linewidth' not in kwds:
            kwds['linewidth'] = 1
    if 'linestyle' not in mean_line_kwds:
        kwds['linestyle'] = '--'
    if 'linestyle' not in limit_lines_kwds:
        kwds['linestyle'] = ':'

    ax.scatter(means, diffs, **scatter_kwds) 
    ax.axhline(mean_diff, **mean_line_kwds)  
    ax.annotate('mean diff:\n{}'.format(np.round(mean_diff, 2)),
                xy=(0.99, 0.5),
                horizontalalignment='right',
                verticalalignment='center',
                fontsize=fontsize,
                xycoords='axes fraction')

    if sd_limit > 0:
        half_ylim = (1.5 * sd_limit) * std_diff
        ax.set_ylim(mean_diff - half_ylim,
                    mean_diff + half_ylim)
        limit_of_agreement = sd_limit * std_diff
        lower = mean_diff - limit_of_agreement
        upper = mean_diff + limit_of_agreement
        for j, lim in enumerate([lower, upper]):
            ax.axhline(lim, **limit_lines_kwds)
        ax.annotate(f'-{sd_limit} SD: {lower:0.2g}',
                    xy=(0.99, 0.07),
                    horizontalalignment='right',
                    verticalalignment='bottom',
                    fontsize=fontsize,
                    xycoords='axes fraction')
        ax.annotate(f'+{sd_limit} SD: {upper:0.2g}',
                    xy=(0.99, 0.92),
                    horizontalalignment='right',
                    fontsize=fontsize,
                    xycoords='axes fraction')

    elif sd_limit == 0:
        half_ylim = 3 * std_diff
        ax.set_ylim(mean_diff - half_ylim,
                    mean_diff + half_ylim)

    ax.set_ylabel('Difference', fontsize=fontsize)
    ax.set_xlabel('Means', fontsize=fontsize)
    ax.tick_params(labelsize=13)
    fig.tight_layout()
    return fig