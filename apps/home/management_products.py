import pandas as pd
from flask import request
from apps import db
from apps.authentication.models import Product_Data

def combine_2rd_columns(col_1, col_2):
    result = col_1
    if not pd.isna(col_2):
        result += " " + str(col_2)
    return result

# 등록된 데이터 파일 불러오기
def get_upload_files() :
    datas = Product_Data.query.filter_by(active=1).all()
    excel_file_names = []
    for i in datas :
        excel_file_names.append(i.filename)
    df = pd.DataFrame()
    for i in excel_file_names :
        temp = pd.read_excel("apps/upload_product/" + i, sheet_name='제품리스트', skiprows=[0,1,2])
        df = pd.concat([df, temp], ignore_index=True)
    df["제품명 업데이트"] = df.apply(lambda x: combine_2rd_columns(x['제품명'], x['옵션 1']), axis=1)
    df['구분'] = df['구분'].fillna(method='ffill')
    df['규격'] = df['규격'].fillna("None")
    return df

def get_products(df) :
    data = {}
    for i in range(len(df['제품명 업데이트'])) :
        try :
            data[df['구분'][i]].append([df['제품명 업데이트'][i], df['규격'][i], str(df['옵션 2'][i])])
            # data[df['제품명 업데이트'][i]].append(df['규격'][i])
        except :
            data[df['구분'][i]] = ([[df['제품명 업데이트'][i], df['규격'][i], str(df['옵션 2'][i])]])

    return data