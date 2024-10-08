"""Setup and preprocess data tools"""

import os
import tarfile
import shutil
import pandas as pd
import re


def extract_data(uri, output_directory) -> None:
    """Unpack and save datafrom archive URI"""
    os.makedirs(output_directory, exist_ok=True)

    # extract archive
    with tarfile.open(uri, "r") as tar:
        tar.extractall()
        # tar.extractall(path=output_directory)


def create_img_db(img_dir, annot_dir, output_uri) -> pd.DataFrame:
    """Create image and annotation database and export it to CSV file"""
    annot_infos_list = []

    # read folder and create dataframe
    breeds_dir = os.listdir(annot_dir)
    # features as they appear in annotation files
    annot_tags = [
        "filename",
        "name",
        "width",
        "height",
        "depth",
        "xmin",
        "ymin",
        "xmax",
        "ymax",
    ]

    # read inside each breed folder
    for breed in breeds_dir:
        annot_list = os.listdir(os.path.join(annot_dir, breed))

        for annot in annot_list:
            # create img URI from information
            img_uri = os.path.join(img_dir, breed, annot + ".jpg")
            # check if corresponding image exists
            if os.path.exists(img_uri):
                pass
            else:
                img_uri = ""

            annot_infos = []
            # read file
            with open(
                os.path.join(annot_dir, breed, annot), "r", encoding="utf-8"
            ) as f:
                annot_content = f.read()
            
            # loop over features & store regex result in a list
            for tag in annot_tags:
                pattern = f"<{tag}>(.*?)</{tag}>"
                result = re.search(pattern, annot_content, re.DOTALL).group(1)
                # bad filenames == "%s" (ID) -> replace by ID available in img_uri
                if tag == "filename" and result == "%s":
                    result = img_uri.split("/")[-1][:-4]

                annot_infos.append(result)

            # add image URI
            annot_infos.append(img_uri)

            # add list to annotations info list
            annot_infos_list.append(annot_infos)

    # store in DF
    db_cols = [
        "ID",
        "class_label",
        "width",
        "height",
        "depth",
        "bb_xmin",
        "bb_ymin",
        "bb_xmax",
        "bb_ymax",
        "img_uri",
    ]
    df = pd.DataFrame(annot_infos_list, columns=db_cols)

    # set to numeric values
    num_cols = ["width", "height", "depth", "bb_xmin", "bb_ymin", "bb_xmax", "bb_ymax"]
    df[num_cols] = df[num_cols].astype(int)

    # save CSV
    with open(output_uri, "wb") as f:
        df.to_csv(f)

    return df


def create_annot(x, o_dir, set_type, o_format="txt") -> None:
    """Create annotation folder from data

    x: Pandas Series with necessary columns (encoded class & bbox coordinates)
    o_dir: string, output directory
    set_type: string, data set type ("train", "val" or "test")
    o_format: string, default="txt"
    """

    # root labels folder
    output_root_dir = os.path.join(o_dir, "labels")
    os.makedirs(output_root_dir, exist_ok=True)
    # set folder
    output_dir = os.path.join(output_root_dir, set_type)
    os.makedirs(output_dir, exist_ok=True)

    # get data
    filename = x["ID"] + "." + o_format
    class_e = x["class_enc"]
    xmin = x["bb_xmin"]
    xmax = x["bb_xmax"]
    ymin = x["bb_ymin"]
    ymax = x["bb_ymax"]
    img_w = x["width"]
    img_h = x["height"]

    # convert to model format
    w = xmax - xmin
    h = ymax - ymin    
    x_center = xmin + (w / 2)
    y_center = ymin + (h / 2)

    w_rel = w / img_w
    h_rel = h / img_h
    x_c_rel = x_center / img_w
    y_c_rel = y_center / img_h
    
    # save file
    with open(os.path.join(output_dir, filename), 'w') as f:
        f.write(f"{class_e} {x_c_rel} {y_c_rel} {w_rel} {h_rel}")


def copy_images(x, o_dir, set_type) -> None:
    """Copy images to appropriate folder

    x: Pandas Series with necessary columns (encoded class & bbox coordinates)
    o_dir: string, output directory
    set_type: string, data set type ("train", "val" or "test")
    """

    # root labels folder
    output_root_dir = os.path.join(o_dir, "images")
    os.makedirs(output_root_dir, exist_ok=True)
    # set folder
    output_dir = os.path.join(output_root_dir, set_type)
    os.makedirs(output_dir, exist_ok=True)
    
    # images URI
    img_name = x["ID"] + ".jpg"
    src_uri = x["img_uri"]
    dest_uri = os.path.join(output_dir, img_name)

    # copy image
    if not os.path.exists(dest_uri):
        shutil.copy2(src_uri, dest_uri)


def copy_images_prev(X, dir) -> None:
    i = 0
    for src_uri in X:
        img_name = src_uri.split("/")[-1]
        img_class = src_uri.split("/")[-2].split("-")[-1]
        dest_uri = os.path.join(dir, img_class, img_name)
        # create folder if needed
        if not os.path.exists(os.path.join(dir, img_class)):
            os.makedirs(os.path.join(dir, img_class))
        # copy image
        if not os.path.exists(dest_uri):
            shutil.copy2(src_uri, dest_uri)
        # count processed images
        i += 1
    print(f"{i} images processed")


if __name__ == "__main__":
    help()
