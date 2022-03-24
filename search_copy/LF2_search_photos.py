import json
import boto3
import os
import sys
import uuid
import time
import requests
import logging

from requests_aws4auth import AWS4Auth

host = 'https://search-myphotos-qxixu6vspmzkpzb6aos7gnfare.us-east-1.es.amazonaws.com'
region = 'us-east-1'

service = 'es'
credentials = boto3.Session().get_credentials()
awsauth = AWS4Auth(credentials.access_key, credentials.secret_key, region, service, session_token=credentials.token)



def get_url(es_index, es_type, keyword):
    url = host + '/' + es_index + '/' + es_type + '/_search?q=' + keyword.lower()
    return url

def lambda_handler(event, context):
	
	headers = { "Content-Type": "application/json" }
	lex = boto3.client('lex-runtime')
	
	# print(event)
	# query = "show me dogs and cats"
	query = event["queryStringParameters"]["q"]
	# query = event["q"]
	print(query)
	query = query.replace("%20", " ")
	
	lex_response = lex.post_text(
		botName='SearchPhotos',
		botAlias='SearchPhotos',
		userId='jinyaowu1',
		inputText=query
	)
	
	print("lex_response:", json.dumps(lex_response))
	
	slots = lex_response['slots']
	
	print("slots:",slots)
	
	img_list = []
	for i, tag in slots.items():
		if tag:
			url = get_url('myphotos', 'Photo', tag)
			print("ES URL --- {}".format(url))

			es_response = requests.get(url, headers=headers, auth=awsauth).json()
			print("ES RESPONSE --- {}".format(json.dumps(es_response)))

			es_src = es_response['hits']['hits']
			print("ES HITS --- {}".format(json.dumps(es_src)))

			for photo in es_src:
				labels = [word.lower() for word in photo['_source']['labels']]
				if tag in labels:
					objectKey = photo['_source']['objectKey']
					img_url = 'https://store2photos.s3.amazonaws.com/' + objectKey
					img_list.append(img_url)

	# url = get_url('myphotos', 'Photo', 'cat')
	# resp = requests.get(url, auth=awsauth)  # requests.get, post, and delete have similar syntax
	# resp = resp.json()
	# print(resp)
	
	if img_list:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps(img_list)
		}
	else:
		return {
			'statusCode': 200,
			'headers': {
				"Access-Control-Allow-Origin": "*",
				'Content-Type': 'application/json'
			},
			'body': json.dumps("No such photos.")
		}
