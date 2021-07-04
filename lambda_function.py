import json
import urllib
import urllib.request
import boto3
import os

# S3 高レベルAPI
s3 = boto3.resource('s3')
client = boto3.client('ses', region_name=os.environ['REGION'])

pattern_confirmed = ''
pattern_unconfirmed = ''

def post_slack(webfook_url, user_name, message):
    
    send_data = {
        "username": user_name,
        "text": message,
    }
    
    send_text = json.dumps(send_data)
    request = urllib.request.Request(
        webfook_url, 
        data=send_text.encode('utf-8'), 
        method="POST"
    )
    with urllib.request.urlopen(request) as response:
        response.read().decode('utf-8')


def lambda_handler(event, context):
    
    # バケット名取得
    bucket = event['Records'][0]['s3']['bucket']['name']
    
    # オブジェクトのkey取得
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'])
    
    # オブジェクトを取得する
    s3_object = s3.Object(bucket, key)
 
    # オブジェクトの内容を取得
    s3_object_response = s3_object.get()
    
    info_body = s3_object_response['Body'].read()
    
    bodystr = info_body.decode('utf-8')
    array = bodystr.split('\n')
    
    li = array[-2].split(',')
    
    if li[3].replace('\"', '') == 'EstimatedDisclaimer':
        # 確定前
        cost_idx = -3
        
        whens = array[-2].split(',')
        wi = whens[18].replace('This report reflects your estimated monthly bill for activity through approximately ', '').replace('\"', '')
        estimated = '\n' + wi + '時点情報'
        
    else:
        # 確定後
        cost_idx = -2
        
        estimated = '\n確定情報'
    
    costs = array[cost_idx].split(',')
    currency = costs[23].replace('\"', '')
    to = costs[24].replace('\"', '')
    ti = costs[28].replace('\"', '')
    period = costs[18].replace('Total statement amount for period ', '').replace('\"', '')
    
    u = os.environ['SLACK_URL']
    user = 'aws billing : ' + os.environ['ACCOUNT']
    m = period
    m += '\n'
    m += '税抜 : '+ to + currency
    m += '\n'
    m += '税込 : '+ ti + currency
    m += estimated
    
    post_slack(u, user, m)

