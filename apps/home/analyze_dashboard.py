from flask import request
from apps import db
import pandas as pd
from apps.authentication.models import Excel_Data

def combine_2rd_columns(col_1, col_2):
    result = col_1
    if not pd.isna(col_2):
        result += " " + str(col_2)
    return result

def combine_3rd_columns(col_1, col_2):
    result = col_1
    if not pd.isna(col_2):
        result += "//" + str(col_2)
    return result

def extract_month(date) :
    return str(date.year) + str(date.month).rjust(2, '0')

def extract_day(date) :
    return str(date.year) + str(date.month).rjust(2, '0') + str(date.day).rjust(2, '0')

# 등록된 데이터 파일 불러오기
def get_excel_files() :
    datas = Excel_Data.query.filter_by(active=1).all()
    if len(datas) == 0 :
        df = pd.DataFrame()
        return df
    excel_file_names = []
    for i in datas :
        excel_file_names.append(i.filename)
    df = pd.DataFrame()
    for i in excel_file_names :
        temp = pd.read_excel("apps/upload_excel/" + i)
        df = pd.concat([df, temp], ignore_index=True)
    df["제품명 업데이트"] = df.apply(lambda x: combine_2rd_columns(x['제품(명)'], x['옵션1']), axis=1)
    df["매출 분석 리포트"] = df.apply(lambda x: combine_2rd_columns(x['제품(명)'], x['옵션1']), axis=1)
    df["매출 분석 리포트"] = df.apply(lambda x: combine_3rd_columns(x['매출 분석 리포트'], x['규격']), axis=1)
    df['공급합계'] = df['공급합계'].astype(int)
    return df

# 매출액
def total_sales(df) :
    data  = ("전체매출", df['공급합계'].sum())
    return [data[0], format(int(data[1]), ',')]

# 매출 건수
def total_count(df) :
    data = df['공급합계'].count()
    return data

# Top 1 판매 제품
def top_1_product(df) :
    data = df.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)[:1]
    count = df.groupby('제품명 업데이트').count()['공급합계'].sort_values(ascending=False)[:1]
    data = (data.to_dict())
    key = (list(data.keys())[0])
    value = int(list(data.values())[0])
    count = (count.to_dict())
    count_value = (list(count.values())[0])
    return [key, format(value, ','), count_value]

# Top 매출 채널
def top_company(df) :
    data = df.groupby('업체분류')['공급합계'].sum().sort_values(ascending=False)[:1]
    count = df.groupby('업체분류')['공급합계'].count().sort_values(ascending=False)[:1]
    data = (data.to_dict())
    key = (list(data.keys())[0])
    value = int(list(data.values())[0])
    count = (count.to_dict())
    count_value = (list(count.values())[0])
    return [key, format(value, ','), count_value]

# 일별 매출
def days_sales(df) :
    df['일자'] = pd.to_datetime(df['일자'])
    rev_by_day = df.set_index("일자").groupby(extract_day).sum()['공급합계']
    data = (rev_by_day.to_dict())
    count = df.set_index("일자").groupby(extract_day).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 월별 매출
def monthly_sales(df) :
    rev_by_month = df.set_index("일자").groupby(extract_month).sum()['공급합계']
    data = (rev_by_month.to_dict())
    count = df.set_index("일자").groupby(extract_month).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 시간별 매출
def hourly_sales(df) :
    rev_by_hour = df.set_index("일자").groupby(lambda date:date.hour).sum()['공급합계']
    data = (rev_by_hour.to_dict())
    count = df.set_index("일자").groupby(lambda date:date.hour).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 특정 일자 매출 조회
def specify_sales(df, start, end) :
    mask = (df['일자'] >= start) & (df['일자'] <= end)
    filtered_df = df.loc[mask]
    rev_by_day = filtered_df.set_index("일자").groupby(extract_day).sum()['공급합계']
    data = (rev_by_day.to_dict())
    count = filtered_df.set_index("일자").groupby(extract_day).count()['공급합계']
    count = (count.to_dict())
    count_value = (list(count.values()))
    return list(data.keys()), list(data.values()), count_value

# 매출 분석 - 특정 일자 매출 조회
def sales_analysis_specify(df, start, end, companys) :
    df = df[df['업체분류'].isin(companys)]
    mask = (df['일자'] >= start) & (df['일자'] <= end)
    filtered_df = df.loc[mask]
    return filtered_df

# 매출 분석 - 최고 매출 일 조회
def sales_analysis_max_sales(df) :
    df['일자'] = pd.to_datetime(df['일자'])
    rev_by_day = df.set_index("일자").groupby(extract_day).sum()['공급합계']
    data = (rev_by_day.to_dict())
    max_data = max(data, key = data.get)
    return [max_data, format(int(data[max_data]), ',')]

# 매출 분석 - 매출 채널
def sales_analysis_companys(df) :
    data = df.groupby('업체분류').sum()['공급합계'].sort_values(ascending=False)
    data = (data.to_dict())
    key = (list(data.keys()))
    value = (list(data.values()))
    return [key, value]