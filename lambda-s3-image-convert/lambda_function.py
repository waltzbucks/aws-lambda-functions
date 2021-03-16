#!/usr/bin/env python
import os
import uuid
import boto3
import logging
import ntpath, mimetypes
import PIL
from PIL import Image
import json
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def image_convert(profile, store_path, filename, convertformat):
    
    logging.info(f"imageConvert::{store_path}")

    new_width = profile["width"]
    new_height = profile["height"]
    calc_width = new_width
    calc_height = new_height
    convert_format = convertformat
    file_name, file_ext = os.path.splitext(filename)
    
    if convert_format.lower() == "jpeg":
        save_format = "jpg"
    else:
        save_format = convert_format.lower()
    
    save_path = "/tmp/" + profile["prefix"] + "_" + file_name + "." + save_format
    
    try:
        # Image file open
        logging.info(f"imageConvert:fileopen:{store_path}")
        im = Image.open(store_path)
        width, height = im.size   

        # Image ratio calculate
        image_ratio_width = float(width)/float(height)
        image_ratio_height = float(height)/float(width)
        logging.info(f"imageConvert:ratio_calculate:{store_path} ({float(image_ratio_width)}:{float(image_ratio_height)})")
        
        if image_ratio_width > image_ratio_height:
            calc_width = int(float(new_height * width) / height)
            
        elif image_ratio_width < image_ratio_height:
            calc_height = int(float(new_width * height) / width)
            
        if calc_width < new_width:
            calc_width = new_width
            calc_height = int(float(new_width * height) / width)
            
        elif calc_height < new_height:
            calc_height = new_height
            calc_width = int(float(new_height * width) / height)

        # resize        
        im = im.resize((calc_width,calc_height), PIL.Image.ANTIALIAS)
        logging.info(f"imageConvert:resize:{store_path} ({calc_width},{calc_height}) complete")

        # Crop the center of the image
        width, height = im.size
        if width != new_width or height != new_height:
            
            if width > new_width:
                # Get dimensions
                left = round((width - new_width)/2)
                top = round((height - new_height)/2)

                x_right = round(width - new_width) - left
                x_bottom = round(height - new_height) - top

                right = width - x_right
                bottom = height - x_bottom
            else:
                # Get dimensions
                left = round((new_width - width)/2)
                top = round((height - new_height)/2)

                x_right = round(new_width - width) - left
                x_bottom = round(height - new_height) - top

                right = new_width - x_right
                bottom = height - x_bottom
            
            logging.info(f"imageConvert:crop:{store_path} Get Dimensions of center: (left:{left}, top:{top}, right:{right}, bottom:{bottom})")
            
            # do Crop
            im = im.crop((left, top, right, bottom))
            logging.info(f"imageConvert:crop:{store_path} complete") 

        
        # Image format check then save
        if im.format == convert_format:
            im.save(save_path)
        else:
            im.save(save_path, format=convert_format)
            logging.info(f"imageConvert:format:{store_path} format convert to {convert_format} from {im.format}")
            logging.info(f"imageConvert:save:{store_path} save as {save_path}.")
        
        im.close
        logging.info(f"imageConvert:close:{store_path} complete")
        
    except Exception as e:
        logger.error('Exception: %s', e)
        raise

    return save_path, profile["prefix"]


def lambda_handler(event, context):
    # evet by SQS message
    logging.info('lambda_handler:event:{}'.format(event))
    _body = (event['Records'][0]['body'])
    event = json.loads(_body)
    
    sourceS3Key = event['Records'][0]['s3']['object']['key']
    outputS3 = 's3://' + os.environ['DestinationBucket'] + '/' + os.environ['OutputPrefix']
        
    Metadata = {
        "assetID": str(uuid.uuid4()),
        "region": os.environ['AWS_DEFAULT_REGION'],
        "sourceBucket": event['Records'][0]['s3']['bucket']['name'],
        "sourceKey": event['Records'][0]['s3']['object']['key'],
        "tailpath": ntpath.basename(ntpath.split(sourceS3Key)[0]),
        "filename": os.path.basename(sourceS3Key),
        "convertFormat": os.environ['ImageFormat'],
        "destinationBucket": os.environ['DestinationBucket'],
        "outputPrefix": os.environ['OutputPrefix'],
        'output': outputS3
    }
    
    # Image convert profiles
    r4x3_p1024 = { "width": 1024, "height": 768, "prefix": "1024_768" }
    r4x3_p640 = { "width": 640, "height": 480, "prefix": "640_480" }
    r16x9_p720 = { "width": 720, "height": 405, "prefix": "720_405" }
    r16x9_p320 = { "width": 320, "height": 180, "prefix": "320_180" }
    r4x5_p750 = { "width": 750, "height": 600, "prefix": "750_600" }
    
    global s3
    s3 = boto3.client('s3')
    
    try:
        # S3 File download
        logging.info("lambda_handler:s3:getObject s3://{bucketname}/{keyname}".format(bucketname=Metadata["sourceBucket"],keyname=Metadata["sourceKey"]))
        store_path = "/tmp/" + Metadata['filename']
        s3.download_file(Metadata["sourceBucket"], Metadata["sourceKey"], store_path)
        
        logging.info(f"lambda_handler:fileStored:{store_path}")

        # Image convert call        
        jobprofiles = [r4x3_p1024,r4x3_p640,r16x9_p720,r16x9_p320,r4x5_p750]

        for profile in jobprofiles:
            logging.info(f"lambda_handler:call: imageConvert({profile})")
            save_path, obj_prefix = image_convert(profile, store_path, Metadata["filename"], Metadata["convertFormat"])

            # S3 File upload
            # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-uploading-files.html
        
            object_name = "/".join([
                Metadata["outputPrefix"], 
                Metadata["tailpath"], 
                obj_prefix, Metadata['filename']
            ])
            
            logging.info('lambda_handler:s3:putObject s3://{dstbucket}/{object}'.format(dstbucket=Metadata["destinationBucket"],object=object_name))
        
            # do upload
            with open(save_path, "rb") as f:
                s3.upload_fileobj(
                    f,
                    Metadata["destinationBucket"],
                    object_name,
                    ExtraArgs={
                        "ContentType": mimetypes.guess_type(save_path)[0],
                        "ACL": "public-read"
                    }
                )

        
    except Exception as e:
        logger.error('Exception: %s', e)
        raise

    finally:
        return {
            "status": "complete"
        }