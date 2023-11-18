# -*- coding: utf-8 -*-
"""
Created on Sat Jan 14 00:29:38 2023

@author: aaron
"""
from bs4 import BeautifulSoup
import httpx
import pandas as pd

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64) AppleWebkit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36'
}

async def get_edgar_insider_url(filing_url):
    async with httpx.AsyncClient() as client:
        response = await client.get(filing_url, headers=headers)
        soup = BeautifulSoup(response.content, "html.parser")
        data = soup.find("table")
        url_segment = data.find("a")["href"]
        url = "https://www.sec.gov" + url_segment
        return url

async def scrape_insider_edgar(filing_url):
    insider_url = await get_edgar_insider_url(filing_url)
    async with httpx.AsyncClient() as client:
        response = await client.get(insider_url, headers=headers)
        soup = BeautifulSoup(response.content, 'lxml')
        data = soup.find("tbody")
        table = data.find_all("tr")
        rows = []
        for tr in table:
            td = tr.find_all("td")
            row = []
            for e in td:
                try:
                    row.append(e.find('span', class_='FormData').text)
                except:
                    row.append('')
            rows.append(row)
        df = pd.DataFrame(rows)
        df_direct = df[df[9] == 'D']
        if df_direct.shape[0] > 0:
            shares_direct = int(df.iloc[0, 8].replace(',', ''))
        else:
            shares_direct = 0
        df_indirect = df[df[9] == 'I']
        df_indirect = df_indirect.copy()
        df_indirect[8] = df_indirect[8].str.replace(',', '').astype(int)
        shares_indirect = df_indirect[8].sum()
        insider_shares = shares_direct + shares_indirect
        return insider_shares




