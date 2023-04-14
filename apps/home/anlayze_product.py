import pandas as pd
def sepecify_product(df, company, product, start, end):
    df = df[df['업체분류'].isin(company)]
    mask = (df['일자'] >= start) & (df['일자'] <= end)
    filtered_df = df.loc[mask]
    product_data = []
    for i in product :
        temp = (i.rsplit("/", 1))
        if len(temp) == 1 :
            product_data.append(temp)
        else :
            product_data.append([temp[0], temp[1]])
    print(product_data)
    product_df = pd.DataFrame()
    for i in product_data :
        if len(i) == 1 :
            temp = (filtered_df[(filtered_df['제품명 업데이트'] == i[0])])
        else :
            temp = (filtered_df[(filtered_df['제품명 업데이트'] == i[0]) & (filtered_df['규격'] == i[1])])
        product_df = pd.concat([product_df, temp], ignore_index=True)
    return product_df

def sales_report_by_date_function(df, product) :
    product_data = []
    for i in product :
        temp = (i.rsplit("/", 1))
        if len(temp) == 1 :
            product_data.append(temp)
        else :
            product_data.append([temp[0], temp[1]])
    print(product_data)
    product_df = pd.DataFrame()
    for i in product_data :
        if len(i) == 1 :
            temp = (df[(df['제품명 업데이트'] == i[0])])
        else :
            temp = (df[(df['제품명 업데이트'] == i[0]) & (df['규격'] == i[1])])
        product_df = pd.concat([product_df, temp], ignore_index=True)
    return product_df