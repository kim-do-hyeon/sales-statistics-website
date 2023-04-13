# -*- encoding: utf-8 -*-
import os
from apps import db
import datetime
from apps.home import blueprint
from flask import render_template, request, flash, redirect, jsonify
from flask_login import login_required
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename
from apps.authentication.models import Excel_Data, Product_Data, Product_Details
from apps.home.analyze_dashboard import *
from apps.home.management_products import *
from apps.home.anlayze_product import *

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
            selected_company = (data['companys'])
            selected_item = data['selected_products']
            start = (data['start'])
            end = (data['end'])
            df = get_excel_files()
            processed_df = sepecify_product(df, selected_company, selected_item, start, end)
            d_k, d_v, d_c = days_sales(processed_df)
            for i in range(len(d_v)) :
                d_v[i] = str(int(d_v[i]))
            print(d_k, d_v)

            data = processed_df.groupby('제품명 업데이트').sum()['공급합계'].sort_values(ascending=False)
            data = (data.to_dict())
            key = (list(data.keys()))
            value = (list(data.values()))
            return jsonify(result = 'success', d_k =d_k, d_v = d_v, table_key = key, table_value = value)

        
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
def sales_analysis() :
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

'''
일자별 매출 리포트 (품목별 일자별 매출 자료를 나타냅니다.) 
- 리포트 조건을 선택합니다.　(기간 /품목 개별, 통합 선택) 
*개별 선택시 품목별로 나눠 리포트가 작성되며 통합 선택시 선택한 품목들의 각 데이터의 합으로 리포트가 작성됩니다. 
- 판매 채널을 선택 합니다. (전체_통합 / 일부 선택 가능)
- 품목을 선택합니다. (전체 / 일부 선택 가능)
* 구분 / 제품명 / 옵션 1 / 옵션 2 각 단계별 선택할 수 있도록 하며 상위 조건 선택만으로도 조회 가능하도록 합니다. 
- 품목별 판매량 통계 그래프_ 선택한 조건의 매출(일자별 전체 매출 합)을 막대 그래프로 나타냅니다. (기간내 그래프는 일별, 주별, 월별로 선택할 수 있도록 합니다.) 
- 품목별 판매량 데이터_ 선택한 기간내 품목별 일별 매출액을 표로 나타냅니다. (최대 30일간 조회) 
'''
@blueprint.route('/sales_report_by_date', methods=['GET', 'POST'])
def sales_report_by_date() :
    if request.method == 'GET' :
        print("일자별 매출 리포트")
        df = get_excel_files()
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
                            colors = colors)



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

@blueprint.route('/management_product', methods=['GET', 'POST'])
def management_proudct() :
    df = get_upload_files()
    data = get_products(df)
    product_data = Product_Details.query.all()
    return render_template("home/management_product.html",
                           data = data,
                           product_data = product_data)

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
                print(key, id)
                df = get_upload_files()
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
# @login_required
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
