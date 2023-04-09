# -*- encoding: utf-8 -*-
import os
from apps import db
import datetime
from apps.home import blueprint
from flask import render_template, request, flash, redirect, jsonify
from flask_login import login_required
from jinja2 import TemplateNotFound
from werkzeug.utils import secure_filename
from apps.authentication.models import Excel_Data
from apps.home.analyze_dashboard import *

@blueprint.route('/index')
# @login_required
def index_redirect() :
    return redirect("/index/main")

@blueprint.route('/index/<path:path>', methods=['GET', 'POST'])
# @login_required
def index(path):
    # Basic
    global df
    df = get_excel_files()
    top_1_product_data = top_1_product(df)
    top_company_data = top_company(df)
    total_sales_data = total_sales(df)
    total_count_data = total_count(df)

    if path == "main" :
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

        for i in range(len(days_sales_values)) :
            days_sales_values[i] = format(days_sales_values[i], ",")
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
    # Ajax 통신으로 변경

@blueprint.route("/ajax", methods=['POST', 'GET'])
def ajax() :
    if request.method == 'POST' :
        global df
        data = request.get_json()
        if data['value'] == 'days' :
            d_k, d_v, d_c = days_sales(df)
        elif data['value'] == 'monthly' :
            d_k, d_v, d_c = monthly_sales(df)
        elif data['value'] == 'hourly' :
            d_k, d_v, d_c = hourly_sales(df)
        elif data['value'] == 'weekly' :
            d_k, d_v, d_c = days_sales(df)
            d_k = d_k[:7]
            d_v = d_v[:7]
        elif data['value'] == 'days_30' :
            d_k, d_v, d_c = days_sales(df)
            d_k = d_k[:30]
            d_v = d_v[:30]
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
        


@blueprint.route('/upload_excel', methods=['GET', 'POST'])
@login_required
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

@blueprint.route('/delete_excel/<path:subpath>')
@login_required
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
