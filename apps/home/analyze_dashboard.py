from flask import request
from apps import db
import pandas as pd

def combine_2rd_columns(col_1, col_2):
    result = col_1
    if not pd.isna(col_2):
        result += " " + str(col_2)
    return result

def extract_month(date) :
    return str(date.year) + str(date.month).rjust(2, '0')

def extract_day(date) :
    return str(date.year) + str(date.month) + str(date.day).rjust(2, '0')

df = pd.read_excel("sample_data1.xlsx")
df["제품명 업데이트"] = df.apply(lambda x: combine_2rd_columns(x['제품(명)'], x['옵션1']), axis=1)

# 매출액
def total_sales() :
    data  = ("전체매출", df['공급합계'].sum())
    return [data[0], format(data[1], ',')]

# 매출 건수
def total_count() :
    data = df['공급합계'].count()
    return data

# Top 1 판매 제품
def top_1_product() :
    data = df.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)[:1]
    count = df.groupby('제품명 업데이트').count()['공급합계'].sort_values(ascending=False)[:1]
    data = (data.to_dict())
    key = (list(data.keys())[0])
    value = (list(data.values())[0])
    count = (count.to_dict())
    count_value = (list(count.values())[0])
    return [key, format(value, ','), count_value]

# Top 매출 채널
def top_company() :
    data = df.groupby('업체분류').sum()['공급합계'].sort_values(ascending=False)[:1]
    count = df.groupby('업체분류').count()['공급합계'].sort_values(ascending=False)[:1]
    data = (data.to_dict())
    key = (list(data.keys())[0])
    value = (list(data.values())[0])
    count = (count.to_dict())
    count_value = (list(count.values())[0])
    return [key, format(value, ','), count_value]

# 일별 매출
def days_sales() :
    rev_by_day = df.set_index("일자").groupby(extract_day).sum()['공급합계']
    data = (rev_by_day.to_dict())
    count = df.set_index("일자").groupby(extract_day).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 월별 매출
def monthly_sales() :
    rev_by_month = df.set_index("일자").groupby(extract_month).sum()['공급합계']
    data = (rev_by_month.to_dict())
    count = df.set_index("일자").groupby(extract_month).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 시간별 매출
def hourly_sales() :
    rev_by_hour = df.set_index("일자").groupby(lambda date:date.hour).sum()['공급합계']
    data = (rev_by_hour.to_dict())
    count = df.set_index("일자").groupby(lambda date:date.hour).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 특정 일자 매출 조회
def specify_sales(start, end) :
    mask = (df['일자'] >= start) & (df['일자'] <= end)
    filtered_df = df.loc[mask]
    rev_by_day = filtered_df.set_index("일자").groupby(extract_day).sum()['공급합계']
    data = (rev_by_day.to_dict())
    count = df.set_index("일자").groupby(extract_day).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value