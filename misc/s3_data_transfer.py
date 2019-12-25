
import boto3
import numpy as np
import os


boto3_connection = boto3.resource('s3')
all_files = np.array(os.listdir('../data/'))
# only the relevant data files, which share a string phrase. 
files_csv_type_mask = ['capitalbikeshare' in x for x in all_files]
# filter inappropriate out of the upload list. 
files_to_upload = all_files[files_csv_type_mask]

def print_s3_contents_boto3(connection, just_bucket_name = False):
    for bucket in connection.buckets.all():
        print(bucket.name)
        if not just_bucket_name:
            for key in bucket.objects.all():
                print('\t|___', key.key)

def s3_upload(bucketname, file_list):
    # write results back to s3
    count = 1
    s3_client = boto3.client('s3')
    for file in file_list:
        file = 'data/'+file
        with open(file, 'rb') as data:
            
            #remove data directory from filename
            file_basename = file.split('data/')[1]
            fname = file_basename.split('.csv')[0]+'.csv'
            #print(f'uploading {file} as {fname}' )
            #s3_client = boto3.client('s3')
            # s3_client.upload_file('file-on-my-local-machine.txt', bucket_name, 'upload-to-s3-as-this-filename.txt')
            s3_client.upload_file(file, bucketname,fname  )
            count+=1
        
