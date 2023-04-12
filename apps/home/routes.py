# -*- encoding: utf-8 -*-
import os
from apps import db
import datetime
from apps.home import blueprint
from flask import render_template, request, flash, redirect, jsonify
from flask_login import login_required
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename
from apps.authentication.models import Excel_Data, Product_Data
from apps.home.analyze_dashboard import *

@blueprint.route('/index', methods=['GET', 'POST'])
# @login_required
def index():
    # Basic
    global df
    df = get_excel_files()
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
                        graph_datas = graph_days_sales_values
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
        
'''
요약 일자를 선택합니다. 
- 매출요약_매출액 / 매출건수 / 기간내 최고 매출 채널 / 기간내 최고 매출 품목을 나타냅니다. 
- 품목별 매출 통계 그래프_ 일자별 매출(일자별 전체 매출 합) 을 꺾은선 그래프로 나타냅니다. 
- 품목별 매출 데이터_선택한 기간내 일별 매출액과 결제자수를 표로 나타냅니다. (최대 30일간 조회) 
- 판매채널을 선택합니다. (기본은 전체)   
- 첨부된 제품리스트와 같이 정리됩니다. 
'''
@blueprint.route('/sales_analysis', methods=['GET', 'POST'])
# @login_required
def analyze_sales() :
    if request.method == 'GET' :
        df = get_excel_files()
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
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', 'green', 'blue', 'purple', 'black', 'white']

        # 매출 분석 - Pi Chart
        companys_sales_data_for_pi_chart = sales_analysis_companys(df)
        print(companys_sales_data_for_pi_chart)
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
                            companys_sales_data_for_pi_chart = companys_sales_data_for_pi_chart)
    elif request.method == 'POST' :
        df = get_excel_files()
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
        colors = ['#9BD0F5', '#D09BF5', '#F59BD0', 'green', 'blue', 'purple', 'black', 'white']
        
        # 매출 분석 - Pi Chart
        companys_sales_data_for_pi_chart = sales_analysis_companys(df)
        print(companys_sales_data_for_pi_chart)


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
                            companys_sales_data_for_pi_chart = companys_sales_data_for_pi_chart)

@blueprint.route('/upload_excel', methods=['GET', 'POST'])
# @login_required
def upload_excel() :
    if request.method == 'GET' :
        data = Excel_Data.query.all()
        return render_template('home/upload_excel.html', data = data)
    elif request.method == 'POST' :
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join("apps/upload_excel", filename))
        data = Excel_Data(filename = str(filename), active = 1)
        db.session.add(data)
        db.session.commit()
        flash("엑셀 파일이 등록되었습니다.")
        return redirect('/upload_excel')

@blueprint.route('/upload_product', methods=['GET', 'POST'])
# @login_required
def upload_product() :
    if request.method == 'GET' :
        data = Product_Data.query.all()
        return render_template('home/upload_product.html', data = data)
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
# @login_required
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

@blueprint.route('/delete_excel/<path:subpath>')
# @login_required
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

@blueprint.route('/<template>')
@login_required
def route_template(template):
    try:
        if not template.endswith('.html'):
            template += '.html'
        segment = get_segment(request)
        return render_template("home/" + template, segment=segment)

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
