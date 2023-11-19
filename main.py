# -*- coding: utf-8 -*-
"""
Created on Fri Nov 17 13:39:54 2023

@author: aaron
"""

import os
from fastapi import FastAPI, HTTPException
from typing import Optional
from insider_ownership import insider_owner_table
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
load_dotenv()  # This loads the .env file variables into the environment



app = FastAPI()

@app.get("/insider-ownership/{symbol}")
async def get_insider_ownership(symbol: str):
    try:

        
        data = await insider_owner_table(symbol)
        return data
        #return data.to_dict(orient='records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
        
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity, adjust in production
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

