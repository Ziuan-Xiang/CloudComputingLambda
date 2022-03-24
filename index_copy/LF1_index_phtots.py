import json
import boto3
import os
import sys
import uuid
import requests
from datetime import *
from requests_aws4auth import AWS4Auth

host = 'https://search-myphotos-qxixu6vspmzkpzb6aos7gnfare.us-east-1.es.amazonaws.com'
region = 'us-east-1'

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)


def get_url(index, type):
    url = host + '/' + index + '/' + type
    return url


def lambda_handler(event, context):
    headers = { "Content-Type": "application/json" }
    rek = boto3.client('rekognition')
    
    # get the image information from S3
    for record in event['Records']:
        print(record['s3'])
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        size = record['s3']['object']['size'] # up to 5MB
        
        # detect the labels of current image
        labels = rek.detect_labels(
            Image={
                'S3Object': {
                    'Bucket': bucket,
                    'Name': key
                }
            },
            MaxLabels=10
        )
        
    # prepare JSON object
    obj = {}
    obj['objectKey'] = key
    obj["bucket"] = bucket
    obj["createdTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    obj["labels"] = []
        
    # get custom label from s3
    s3 = boto3.client('s3')
    headObject = s3.head_object(Bucket=bucket, Key=key)
    metaData = headObject['Metadata']
    print(metaData)
    if len(metaData) != 0:
        custom_label = metaData['customlabels']
        print(custom_label)
        obj["labels"].append(custom_label)
    
    
    
    for label in labels['Labels']:
        obj["labels"].append(label['Name'])
    
    print(obj)
    
    
    
    # post the JSON object into ElasticSearch, _id is automaticlly increased
    url = get_url('myphotos', 'Photo')
    obj = json.dumps(obj)
    req = requests.post(url, data=obj, headers=headers, auth=awsauth)
        
    print("Success: ", req.json())
    
    
    return {
        'statusCode': 200,
        'headers': {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json'
        },
        'body': json.dumps("Image labels have been successfully detected!")
    }
