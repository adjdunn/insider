# -*- coding: utf-8 -*-
"""
Created on Fri Jan 13 23:40:52 2023

@author: aaron
"""
import os
import pandas as pd
import httpx
from datetime import datetime, timedelta
from insider_scrape import scrape_insider_edgar

from dotenv import load_dotenv
load_dotenv()  # This loads the .env file variables into the environment




async def insider_transactions(symbol):
    api_key = os.getenv('FMP_API_KEY')
    url = 'https://fmpcloud.io/api/v4/insider-trading?symbol=%s&limit=100&apikey=%s' % (symbol, api_key)
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        data = response.json()
    return pd.DataFrame(data)

async def shares_outstanding(symbol):
    api_key = os.getenv('FMP_API_KEY')
    url_shares = "https://fmpcloud.io/api/v4/shares_float?symbol=%s&apikey=%s" % (symbol, api_key)
    async with httpx.AsyncClient() as client:
        response = await client.get(url_shares)
        data_shares = response.json()
    return data_shares[0]['outstandingShares']

async def share_price(symbol):
    api_key = os.getenv('FMP_API_KEY')
    url_price = "https://fmpcloud.io/api/v3/quote/%s?apikey=%s" % (symbol, api_key)
    async with httpx.AsyncClient() as client:
        response = await client.get(url_price)
        data_price = response.json()
    return data_price[0]['price']

def insider_transactions_df(df):
    transaction_df = df[(df.transactionType == 'P-Purchase') | (df.transactionType == 'S-Sale')]
    transaction_df = transaction_df.copy()
    transaction_df['transaction_value'] = transaction_df['securitiesTransacted'] * transaction_df['price']
    transaction_df['transaction_value'] = transaction_df.apply(lambda x: x['transaction_value'] if x['transactionType'] == 'P-Purchase' else -1 * x['transaction_value'], axis=1)
    transaction_df['transactionDate'] = pd.to_datetime(transaction_df['transactionDate'])
    one_year_ago = datetime.now() - timedelta(days=365)
    transaction_df = transaction_df[transaction_df['transactionDate'] >= one_year_ago]
    return transaction_df

def insider_title(df, name):
    title = df[df.reportingName == name]['typeOfOwner'].values[0]
    return title

async def shares_owned(df, name):
#    try:
    filing_url = df[(df.reportingName == name) & (df.securityName.str.contains('Common Stock'))]['link'].values[0]
    total_shares_owned = await scrape_insider_edgar(filing_url)
#    except:
#        total_shares_owned = 0
    return total_shares_owned

def last_transaction(df, name):
    try:
        last_trans = df[(df.reportingName == name) & (df.securityName.str.contains('Common Stock'))]['transactionDate'].values[0]
    except:
        last_trans = None
    return last_trans

async def insider_owner_table(symbol):
    df = await insider_transactions(symbol)
    
    names = set(df.reportingName.values.tolist())
    transaction_df = insider_transactions_df(df)
    

    shares_out = await shares_outstanding(symbol)
    stock_price = await share_price(symbol)
    insider_dataset = []
    
    for name in names:
        title = insider_title(df, name)
        shares_owned_insider = await shares_owned(df, name)
        percent_total = shares_owned_insider / shares_out
        share_value = shares_owned_insider * stock_price
        last_trans = last_transaction(df, name)
        share_value_purchased_1Y = transaction_df[transaction_df["reportingName"] == name]['transaction_value'].sum()
        insider_dataset.append([name, title, shares_owned_insider, percent_total, share_value, share_value_purchased_1Y, last_trans])
    
    columns = ['name', 'title', 'shares_owned', 'percent_total', 'share_value', 'share_value_purchased_1Y', 'last_transaction']
    insider_df = pd.DataFrame(insider_dataset, columns=columns)
    insider_df.sort_values(by='percent_total', ascending=False, inplace=True)
    
    #insider_df = insider_df[insider_df.percent_total > 0]
    
    return insider_df
