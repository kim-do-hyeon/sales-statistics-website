# -*- encoding: utf-8 -*-
import os
from apps import db
import datetime
from apps.home import blueprint
from flask import render_template, request, flash, redirect, jsonify
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename
from apps.authentication.models import Excel_Data, Product_Data, Product_Details, Option
from apps.home.analyze import *
from apps.home.management_products import *

def set_options() :
    try :
        user_selected_option = Option.query.filter_by(id=1).first()
        if user_selected_option.type == 'date' : 
            temp = '일자'
        elif user_selected_option.type == 'order_date' :
            temp = '발주일자'
        return temp
    except :
        data = Option(type = 'date')
        db.session.add(data)
        db.session.commit()
        return "일자"

@blueprint.route('/index', methods=['GET', 'POST'])
def index():
    # Basic
    global df
    df = get_excel_files()
    if len(df) == 0 :
        flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
        return redirect("/upload_excel")

    top_1_product_data = top_1_product(df)
    top_company_data = top_company(df)
    total_sales_data = total_sales(df)
    total_count_data = total_count(df)

    days_sales_keys, days_sales_values, days_sales_counts = days_sales(df)
    # Report 용 Key값
    date_list = []
    for date_str in days_sales_keys:
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:])
        date_obj = datetime.date(year, month, day)
        date_list.append(date_obj.strftime("%Y년 %m월 %d일"))

    # Graph 용 Key 값
    graph_days_sales_keys = []
    for i in days_sales_keys :
        graph_days_sales_keys.append(int(i))
    # Graph 용 Value 값
    graph_days_sales_values = []
    for i in days_sales_values :
        graph_days_sales_values.append(i)

    # Report 용 Value 값
    for i in range(len(days_sales_values)) :
        days_sales_values[i] = format(int(days_sales_values[i]), ",")

    return render_template('home/index.html', segment='index', 
                        total_sales_data = total_sales_data,
                        total_count_data = total_count_data,
                        top_1_product_data = top_1_product_data,
                        top_company_data = top_company_data,
                        report_keys = date_list,
                        report_values = days_sales_values,
                        report_counts = days_sales_counts,
                        graph_labels = graph_days_sales_keys,
                        graph_datas = graph_days_sales_values,
                        date_option = set_options()
    )

@blueprint.route("/ajax", methods=['POST', 'GET'])
def ajax() :
    if request.method == 'POST' :
        global df
        data = request.get_json()
        if data['type'] == 'graph' :
            if data['value'] == 'days' :
                d_k, d_v, d_c = days_sales(df)
            elif data['value'] == 'monthly' :
                d_k, d_v, d_c = monthly_sales(df)
            elif data['value'] == 'hourly' :
                d_k, d_v, d_c = hourly_sales(df)
            elif data['value'] == 'weekly' :
                d_k, d_v, d_c = days_sales(df)
                d_k = d_k[-7:]
                d_v = d_v[-7:]
            elif data['value'] == 'days_30' :
                d_k, d_v, d_c = days_sales(df)
                d_k = d_k[-30:]
                d_v = d_v[-30:]
            elif data['value'] == 'specify' :
                d_k, d_v, d_c = specify_sales(df, data['start'], data['end'])

            # Graph 용 Key 값
            graph_label = []
            for i in d_k :
                graph_label.append(int(i))
            # Graph 용 Value 값
            graph_value = []
            for i in d_v :
                graph_value.append(i)
            return jsonify(result='success', label=graph_label, value=graph_value)
        elif data['type'] == "report" :
            value = data['value']
            if value == "hourly" :
                d_k, d_v, d_c = hourly_sales(df)
                for i in range(len(d_k)) :
                    d_k[i] = str(d_k[i]) + "시"
            elif value == "weekly" :
                d_k, d_v, d_c = days_sales(df)
                d_k = d_k[-7:]
                d_v = d_v[-7:]
                d_c = d_c[-7:]
            elif value == "monthly" :
                d_k, d_v, d_c = days_sales(df)
                d_k = d_k[-30:]
                d_v = d_v[-30:]
                d_c = d_c[-30:]
            elif value == "custom" :
                d_k, d_v, d_c = specify_sales(df, data['start'], data['end'])

            if value != "hourly" :
                for i in range(len(d_k)) :
                    year = int(d_k[i][:4])
                    month = int(d_k[i][4:6])
                    day = int(d_k[i][6:])
                    date_obj = datetime.date(year, month, day)
                    d_k[i] = (date_obj.strftime("%Y년 %m월 %d일"))
            for i in range(len(d_v)) :
                d_v[i] = str(format(int(d_v[i]), ',')) + "원"
            for i in range(len(d_c)) :
                d_c[i] = str(d_c[i]) + "건"
            
            return jsonify(result='success', table_key = d_k, table_value = d_v, table_count = d_c)
        elif data['type'] == 'report_selectbox' :
            value = data['value']
            product = Product_Details.query.filter_by(type=str(value)).all()
            product_name = []
            for i in product :
                if i.standard == "None" :
                    product_name.append(i.name)
                else :
                    product_name.append(i.name + "/" + i.standard)
            return jsonify(result='success', data = product_name)
        elif data['type'] == 'sales_report_by_date' :
            selected_company = list(set(data['companys']))
            selected_item = data['selected_products']
            start = (data['start'])
            end = (data['end'])
            df = get_excel_files()
            if len(df) == 0 :
                flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
                return redirect("/upload_excel")
            processed_df = sepecify_product(df, selected_company, selected_item, start, end)
            d_k, d_v, d_c = days_sales(processed_df)
            for i in range(len(d_v)) :
                d_v[i] = str(int(d_v[i]))
            data = processed_df.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)
            data = (data.to_dict())
            key_table = (list(data.keys()))
            value_table = (list(data.values()))
            for i in range(len(value_table)) :
                value_table[i] = format(int(value_table[i]), ",")
            data1 = {}
            for i in selected_company :
                selected_company_df = processed_df[processed_df['업체분류'] == i]
                for j in selected_item :
                    selected_item_df = sales_report_by_date_function(selected_company_df, [j])
                    a, b, c = days_sales(selected_item_df)
                    try :
                        data1[j].append([i, a, b])
                    except :
                        data1[j] = [[i, a, b]]            
            product_info = {}
            for product, company_info in data1.items():
                companies = []
                dates = []
                sales = []
                for company in company_info:
                    companies.append(company[0])
                    dates.append(company[1])
                    sales.append(company[2])
                date_list = sorted(list(set([date for sublist in dates for date in sublist])))
                company_sales = []
                for i in range(len(companies)):
                    company_sales.append([])
                    for date in date_list:
                        if date in dates[i]:
                            company_sales[i].append(sales[i][dates[i].index(date)])
                        else:
                            company_sales[i].append(0)
                product_info[product] = {
                    'companies': companies,
                    'date_list': date_list,
                    'sales_list': company_sales
                }
            html_data = {}
            for product, value in product_info.items():
                file_name = str(product).replace("/", "-")
                html_data[product] = '<table class="table align-items-center mb-0" id="mytable_{}"><h3>{}의 판매 데이터</h3><thead><th>날짜</th>'.format(file_name, product)
                html_data[product] += '<button class="btn bg-gradient-dark" onclick="download_excel(\'mytable_{}\')" style="float: right;">엑셀 다운로드</button>'.format(file_name)
                for company in value['companies']:
                    html_data[product] += '<th>{}</th>'.format(company)
                html_data[product] += '<th>합계</th>'
                html_data[product] += '</thead><tbody>'
                total = 0
                for i in range(len(value['date_list'])) :
                    html_data[product] += '<tr><td>{}</td>'.format(value['date_list'][i])
                    result = 0
                    for company in range(len(value['companies'])) :
                        if value['sales_list'][company][i] == 0 :
                            html_data[product] += '<td>-</td>'
                            result += 0
                            total += 0
                        else :
                            temp = format(int(value['sales_list'][company][i]), ",")
                            html_data[product] += '<td>{}</td>'.format(temp)
                            result += value['sales_list'][company][i]
                            total += value['sales_list'][company][i]
                    temp = format(int(result), ",")
                    html_data[product] += '<td>{}</td>'.format(temp)
                    html_data[product] += '</tr>'
                result = []
                for company in range(len(value['companies'])) :
                    result.append(sum(value['sales_list'][company]))
                html_data[product] += '<tr><td>합계</td>'
                for i in range(len(result)) :
                    if result[i] == 0 :
                        html_data[product] += '<td>-</td>'
                    else : 
                        temp = format(int(result[i]), ",")
                        html_data[product] += '<td>{}</td>'.format(temp)
                temp = format(int(total), ",")
                html_data[product] += '<td>{}</td>'.format(temp)
                html_data[product] += '</tr>'
                html_data[product] += '</tbody></table>'
            report_data_key = list(html_data.keys())
            report_data_value = list(html_data.values())
            return jsonify(result = 'success',
                           d_k = d_k,
                           d_v = d_v,
                           table_key = key_table,
                           table_value = value_table,
                           report_data_key = report_data_key,
                           report_data_value = report_data_value)
        elif data['type'] == 'sales_volume_report_by_date' :
            selected_company = list(set(data['companys']))
            selected_item = data['selected_products']
            start = (data['start'])
            end = (data['end'])
            df = get_excel_files()
            if len(df) == 0 :
                flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
                return redirect("/upload_excel")
            processed_df = sepecify_product(df, selected_company, selected_item, start, end)
            d_k, d_v, d_c = days_sales_sales_volume(processed_df)
            for i in range(len(d_c)) :
                d_c[i] = str(int(d_c[i]))
            data = processed_df.groupby('제품명 업데이트').sum()['수량'].sort_values(ascending=False)
            data = (data.to_dict())
            key = (list(data.keys()))
            value1 = (list(data.values()))
            data1 = {}
            for i in selected_company :
                selected_company_df = processed_df[processed_df['업체분류'] == i]
                for j in selected_item :
                    selected_item_df = sales_report_by_date_function(selected_company_df, [j])
                    a, b, c = days_sales_sales_volume(selected_item_df)
                    try :
                        data1[j].append([i, a, c])
                    except :
                        data1[j] = [[i, a, c]]
            product_info = {}
            for product, company_info in data1.items():
                companies = []
                dates = []
                sales = []
                for company in company_info:
                    companies.append(company[0])
                    dates.append(company[1])
                    sales.append(company[2])
                date_list = sorted(list(set([date for sublist in dates for date in sublist])))
                company_sales = []
                for i in range(len(companies)):
                    company_sales.append([])
                    for date in date_list:
                        if date in dates[i]:
                            company_sales[i].append(sales[i][dates[i].index(date)])
                        else:
                            company_sales[i].append(0)
                product_info[product] = {
                    'companies': companies,
                    'date_list': date_list,
                    'sales_list': company_sales
                }
            html_data = {}
            for product, value in product_info.items():
                file_name = str(product).replace("/", "-")
                html_data[product] = '<table class="table align-items-center mb-0" id="mytable_{}"><h3>{}의 판매 데이터</h3><thead><th>날짜</th>'.format(file_name, product)
                html_data[product] += '<button class="btn bg-gradient-dark" onclick="download_excel(\'mytable_{}\')" style="float: right;">엑셀 다운로드</button>'.format(file_name)
                for company in value['companies']:
                    html_data[product] += '<th>{}</th>'.format(company)
                html_data[product] += '<th>합계</th>'
                html_data[product] += '</thead><tbody>'
                total = 0
                for i in range(len(value['date_list'])) :
                    html_data[product] += '<tr><td>{}</td>'.format(value['date_list'][i])
                    result = 0
                    for company in range(len(value['companies'])) :
                        if value['sales_list'][company][i] == 0 :
                            html_data[product] += '<td>-</td>'
                            result += 0
                            total += 0
                        else :
                            temp = format(int(value['sales_list'][company][i]), ",")
                            html_data[product] += '<td>{}</td>'.format(temp)
                            result += value['sales_list'][company][i]
                            total += value['sales_list'][company][i]
                    result_format = format(int(result), ",")
                    html_data[product] += '<td>{}</td>'.format(result_format)
                    html_data[product] += '</tr>'
                result = []
                for company in range(len(value['companies'])) :
                    result.append(sum(value['sales_list'][company]))
                html_data[product] += '<tr><td>합계</td>'
                for i in range(len(result)) :
                    if result[i] == 0 :
                        html_data[product] += '<td>-</td>'
                    else : 
                        temp = format(int(result[i]), ",")
                        html_data[product] += '<td>{}</td>'.format(temp)
                temp = format(int(total), ",")
                html_data[product] += '<td>{}</td>'.format(temp)
                html_data[product] += '</tr>'
                html_data[product] += '</tbody></table>'
            report_data_key = list(html_data.keys())
            report_data_value = list(html_data.values())

            return jsonify(result = 'success', d_k = d_k, d_c = d_c, table_key = key, table_value = value1,
                           report_data_key = report_data_key,
                           report_data_value = report_data_value)
        elif data['type'] == 'set_option' :
            if data['option'] == 'date' :
                try :
                    Option.query.filter_by(id=1).update(dict(type='date'))
                    db.session.commit()
                except :
                    data = Option(type = 'date')
                    db.session.add(data)
                    db.session.commit()
            elif data['option'] == 'order_date' :
                try :
                    Option.query.filter_by(id=1).update(dict(type='order_date'))
                    db.session.commit()
                except :
                    data = Option(type = 'order_date')
                    db.session.add(data)
                    db.session.commit()
            return jsonify(result = 'success')

        
@blueprint.route('/sales_analysis', methods=['GET', 'POST'])
def sales_analysis() :
    if request.method == 'GET' :
        df = get_excel_files()
        if len(df) == 0 :
            flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
            return redirect("/upload_excel")
        top_1_product_data = top_1_product(df)
        top_company_data = top_company(df)
        total_sales_data = total_sales(df)
        total_count_data = total_count(df)
        max_sales_data = sales_analysis_max_sales(df)

        # 매출 분석 - 그래프
        companys = list(set(df['업체분류']))
        df['일자'] = pd.to_datetime(df['일자'])
        companys_sales_data = []
        for i in companys :
            data = df[df['업체분류'] == i]
            data = data.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)    
            data = (data.to_dict())
            a, b = list(data.keys()), list(data.values())
            companys_sales_data.append([a, b])
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', '#F95BD0', '#215d6e', '#fafa6e', '#089f8f', '#fafa6e', '#ddeef2']

        # 매출 분석 - Pi Chart
        companys_sales_data_for_pi_chart = sales_analysis_companys(df)

        # 매출 분석 - 표
        product_sql = Product_Details.query.all()
        report_sum = df.groupby('매출 분석 리포트').sum()['공급합계'].to_dict()
        report_name = list(report_sum.keys())
        report_sum = list(report_sum.values())
        report_count = list(df.groupby('매출 분석 리포트').count()['수량'].to_dict().values())
        
        product_data = []
        for i in product_sql :
            for j in range(len(report_name)) :
                temp = report_name[j].split("//")
                if len(temp) == 1 :
                    if i.name == temp[0] :
                        product_data.append([i.type, i.name, i.standard, report_count[j], format(int(report_sum[j]), ",")])
                else :
                    if i.name == temp[0] and i.standard == temp[1] :
                        product_data.append([i.type, i.name, i.standard, report_count[j], format(int(report_sum[j]), ",")])
        product_type = ["묘목", "깨비상토", "피트모스", "펄라이트", "화분", "블루마스터", "코코화이버",
                        "프로스트킵", "재노탄", "로도비트", "제초매트", "차압예냉기", "블루베리용기",
                        "종이상자", "스트로폼 박스", "용기 스티커", "기타", "세척마사", "질석",
                        "난석", "바크", "점적관수 4구세트", "점적관수 부속품", "관수자재"]
        product_data = sorted(product_data, key = lambda x: product_type)
        return render_template("home/sales_analysis.html",
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            max_sales_data = max_sales_data,
                            data = companys_sales_data,
                            company = companys,
                            selected_companys = companys,
                            colors =  colors,
                            companys_sales_data_for_pi_chart = companys_sales_data_for_pi_chart,
                            product_data = product_data,
                            date_option = set_options())
    elif request.method == 'POST' :
        df = get_excel_files()
        if len(df) == 0 :
            flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
            return redirect("/upload_excel")
        selected_companys = (request.form.getlist('company'))
        companys = list(set(df['업체분류']))
        if len(selected_companys) == 0 :
            flash("판매 채널이 선택되지 않았습니다.")
            return redirect('/sales_analysis')
        if (request.form['start']) != "" :
            start = request.form['start']
        else :
            start = ""
        if (request.form['end']) != "" :
            end = request.form['end']
        else :
            end = ""
        if start != "" and end != "" :
            df = sales_analysis_specify(df, start, end, selected_companys)
        
        top_1_product_data = top_1_product(df)
        top_company_data = top_company(df)
        total_sales_data = total_sales(df)
        total_count_data = total_count(df)
        max_sales_data = sales_analysis_max_sales(df)

        df['일자'] = pd.to_datetime(df['일자'])
        companys_sales_data = []
        for i in selected_companys :
            data = df[df['업체분류'] == i]
            data = data.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)    
            data = (data.to_dict())
            a, b = list(data.keys()), list(data.values())
            companys_sales_data.append([a, b])
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', '#F95BD0', '#215d6e', '#fafa6e', '#089f8f', '#fafa6e', '#ddeef2']
        
        # 매출 분석 - Pi Chart
        companys_sales_data_for_pi_chart = sales_analysis_companys(df)

        # 매출 분석 - 표
        product_sql = Product_Details.query.all()
        report_sum = df.groupby('매출 분석 리포트').sum()['공급합계'].to_dict()
        report_name = list(report_sum.keys())
        report_sum = list(report_sum.values())
        report_count = list(df.groupby('매출 분석 리포트').count()['수량'].to_dict().values())
        product_data = []
        for i in product_sql :
            for j in range(len(report_name)) :
                temp = report_name[j].split("//")
                if len(temp) == 1 :
                    if i.name == temp[0] :
                        product_data.append([i.type, i.name, i.standard, report_count[j], format(int(report_sum[j]), ",")])
                else :
                    if i.name == temp[0] and i.standard == temp[1] :
                        product_data.append([i.type, i.name, i.standard, report_count[j], format(int(report_sum[j]), ",")])
        product_type = ["묘목", "깨비상토", "피트모스", "펄라이트", "화분", "블루마스터", "코코화이버",
                        "프로스트킵", "재노탄", "로도비트", "제초매트", "차압예냉기", "블루베리용기",
                        "종이상자", "스트로폼 박스", "용기 스티커", "기타", "세척마사", "질석",
                        "난석", "바크", "점적관수 4구세트", "점적관수 부속품", "관수자재"]
        product_data = sorted(product_data, key = lambda x: product_type)

        return render_template("home/sales_analysis.html",
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            max_sales_data = max_sales_data,
                            data = companys_sales_data,
                            company = companys,
                            selected_companys = selected_companys,
                            colors =  colors,
                            companys_sales_data_for_pi_chart = companys_sales_data_for_pi_chart,
                            product_data = product_data,
                            date_option = set_options())

@blueprint.route('/sales_report_by_date', methods=['GET', 'POST'])
def sales_report_by_date() :
    if request.method == 'GET' :
        df = get_excel_files()
        if len(df) == 0 :
            flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
            return redirect("/upload_excel")
        companys = list(set(df['업체분류']))
        product_type_sql = Product_Details.query.with_entities(Product_Details.type).all()
        product_type = []
        for i in product_type_sql :
            product_type.append(i[0])
        product_type = list(set(product_type))
        product_type = sorted(product_type)
        d_k, d_v = [], []
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', 'green', 'blue', 'purple', 'black', 'white']
        return render_template("home/sales_report_by_date.html",
                            product_type = product_type,
                            companys = companys,
                            d_k = d_k, d_v = d_v,
                            colors = colors,
                            date_option = set_options())

@blueprint.route('/sales_volume_report_by_date', methods=['GET', 'POST'])
def sales_volume_report_by_date() :
    if request.method == 'GET' :
        df = get_excel_files()
        if len(df) == 0 :
            flash("등록된 엑셀파일이 없습니다. 등록을 먼저 해주세요.")
            return redirect("/upload_excel")
        companys = list(set(df['업체분류']))
        product_type_sql = Product_Details.query.with_entities(Product_Details.type).all()
        product_type = []
        for i in product_type_sql :
            product_type.append(i[0])
        product_type = list(set(product_type))
        product_type = sorted(product_type)
        d_k, d_v = [], []
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', 'green', 'blue', 'purple', 'black', 'white']
        return render_template("home/sales_volume_report_by_date.html",
                            product_type = product_type,
                            companys = companys,
                            d_k = d_k, d_v = d_v,
                            colors = colors,
                            date_option = set_options())

@blueprint.route('/upload_excel', methods=['GET', 'POST'])
def upload_excel() :
    if request.method == 'GET' :
        data = Excel_Data.query.all()
        return render_template('home/upload_excel.html', data = data,
                               date_option = set_options())
    elif request.method == 'POST' :
        upload = request.files.getlist("file[]")
        for f in upload :
            filename = secure_filename(f.filename)
            f.save(os.path.join("apps/upload_excel", filename))
            data = Excel_Data(filename = str(filename), active = 0)
            db.session.add(data)
        db.session.commit()
        flash("엑셀 파일이 등록되었습니다.")
        return redirect('/upload_excel')

@blueprint.route('/apply_excel/<path:subpath>')
def apply_excel(subpath) :
    subpath = subpath.split("/")
    if subpath[0] == "apply" :
        data = Excel_Data.query.filter_by(id = subpath[1]).update(dict(active=1))
        db.session.commit()
        flash("엑셀 파일의 권한이 수정되었습니다.")
        return redirect('/upload_excel')
    elif subpath[0] == "unapply" :
        data = Excel_Data.query.filter_by(id = subpath[1]).update(dict(active=0))
        db.session.commit()
        flash("엑셀 파일의 권한이 수정되었습니다.")
        return redirect('/upload_excel')

@blueprint.route('/delete_excel/<path:subpath>')
def delete_excel(subpath) :
    if subpath == 'all' :
        data = Excel_Data.query.all()
        for i in data :
            db.session.delete(i)
        db.session.commit()
    else :
        data = Excel_Data.query.filter_by(id = subpath).first()
        db.session.delete(data)
        db.session.commit()
    flash("파일이 삭제되었습니다.")
    return redirect('/upload_excel')

@blueprint.route('/management_product', methods=['GET', 'POST'])
def management_proudct() :
    df = get_upload_files()
    if len(df) == 0 :
        flash("등록된 제품이 없습니다. 제품 등록을 먼저 해주세요.")
        return redirect("/upload_product") 
    data = get_products(df)
    product_data = Product_Details.query.all()
    return render_template("home/management_product.html",
                           data = data,
                           product_data = product_data,
                           date_option = set_options())

@blueprint.route('/product/<path:subpath>', methods=['GET', 'POST'])
def product(subpath) :
    subpath = subpath.split("/")
    if request.method == 'POST' :
        form_data_type = (request.form['type'])
        form_data_name = request.form['name']
        form_data_standard = request.form['standard']
        form_data_standard_secondary = request.form['standard_secondary']
        data = Product_Details(type = form_data_type, name = form_data_name, standard = form_data_standard, standard_secondary = form_data_standard_secondary)
        db.session.add(data)
        db.session.commit()
        flash("데이터가 등록되었습니다.")
        return redirect('/management_product')
    else :
        if subpath[0] == 'register' :
            if subpath[1] == "all" :
                df = get_upload_files()
                if len(df) == 0 :
                    flash("등록된 제품이 없습니다. 제품 등록을 먼저 해주세요.")
                    return redirect('/upload_product')
                data = get_products(df)
                for key, value in data.items() :
                    for i in value :
                        data = Product_Details(type = str(key), name = i[0], standard = i[1], standard_secondary = i[2])
                        db.session.add(data)
                db.session.commit()
                flash("모든 데이터가 등록되었습니다.")
                return redirect('/management_product')
            elif subpath[1] == "custom" :
                key = subpath[2]
                id = int(subpath[3])
                df = get_upload_files()
                if len(df) == 0 :
                    flash("등록된 제품이 없습니다. 제품 등록을 먼저 해주세요.")
                    return redirect('/upload_product')
                data = get_products(df)
                custom_data = (data[key][id])
                data = Product_Details(type = str(key), name = custom_data[0], standard = custom_data[1], standard_secondary = custom_data[2])
                db.session.add(data)
                db.session.commit()
                flash("데이터가 등록되었습니다.")
                return redirect('/management_product')
        elif subpath[0] == 'delete' :
            if subpath[1] == 'all' :
                data = Product_Details.query.all()
                for i in data :
                    db.session.delete(i)
                db.session.commit()
                flash("모든 데이터가 삭제되었습니다.")
                return redirect('/management_product')
            elif subpath[1] == 'custom' :
                data = Product_Details.query.filter_by(id = subpath[2]).first()
                db.session.delete(data)
                db.session.commit()
                flash("데이터가 삭제되었습니다.")
                return redirect('/management_product')

@blueprint.route('/upload_product', methods=['GET', 'POST'])
def upload_product() :
    if request.method == 'GET' :
        data = Product_Data.query.all()
        return render_template('home/upload_product.html', data = data, date_option = set_options())
    elif request.method == 'POST' :
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join("apps/upload_product", filename))
        data = Product_Data(filename = str(filename), active = 1)
        db.session.add(data)
        db.session.commit()
        flash("엑셀 파일이 등록되었습니다.")
        return redirect('/upload_product')

@blueprint.route('/delete_product/<path:subpath>')
def delete_product(subpath) :
    if subpath == 'all' :
        data = Product_Data.query.all()
        for i in data :
            db.session.delete(i)
        db.session.commit()
    else :
        data = Product_Data.query.filter_by(id = subpath).first()
        db.session.delete(data)
        db.session.commit()
    flash("파일이 삭제되었습니다.")
    return redirect('/upload_product')

@blueprint.route('/<template>')
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        segment = get_segment(request)
        return render_template("home/" + template, segment=segment, date_option = set_options())

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500

def get_segment(request):
    try:
        segment = request.path.split('/')[-1]
        if segment == '':
            segment = 'index'
        return segment
    except:
        return None
