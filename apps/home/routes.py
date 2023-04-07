# -*- encoding: utf-8 -*-
import os
from apps import db
from apps.home import blueprint
from flask import render_template, request, flash, redirect
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
    top_1_product_data = top_1_product()
    top_company_data = top_company()
    total_sales_data = total_sales()
    total_count_data = total_count()

    if path == "main" :
        days_sales_keys, days_sales_values, days_sales_counts = days_sales()
        for i in range(len(days_sales_values)) :
            days_sales_values[i] = format(days_sales_values[i], ",")
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            report_keys = days_sales_keys,
                            report_values = days_sales_values,
                            report_counts = days_sales_counts
                            )
    # 시간별 매출
    elif path == "hourly_report" :
        hourly_sales_keys, hourly_sales_values, hourly_sales_counts = hourly_sales()
        for i in range(len(hourly_sales_values)) :
            hourly_sales_values[i] = format(hourly_sales_values[i], ",")
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            report_keys = hourly_sales_keys,
                            report_values = hourly_sales_values,
                            report_counts = hourly_sales_counts
                            )
    # 7일 매출
    elif path == "weekly_report" :
        days_sales_keys, days_sales_values, days_sales_counts = days_sales()
        days_sales_keys = days_sales_keys[:7]
        days_sales_values = days_sales_values[:7]
        days_sales_counts = days_sales_counts[:7]
        for i in range(len(days_sales_values)) :
            days_sales_values[i] = format(days_sales_values[i], ",")
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            report_keys = days_sales_keys,
                            report_values = days_sales_values,
                            report_counts = days_sales_counts
                            )
    # 30일 매출
    elif path == "monthly_report" :
        days_sales_keys, days_sales_values, days_sales_counts = days_sales()
        days_sales_keys = days_sales_keys[:30]
        days_sales_values = days_sales_values[:30]
        days_sales_counts = days_sales_counts[:30]
        for i in range(len(days_sales_values)) :
            days_sales_values[i] = format(days_sales_values[i], ",")
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            report_keys = days_sales_keys,
                            report_values = days_sales_values,
                            report_counts = days_sales_counts
                            )
    elif path == "setting_report" :
        start = (request.form['start'])
        end = (request.form['end'])
        if start == "" :
            flash("시작일이 선택되지 않았습니다.")
            return redirect("/index/main")
        elif end == "" :
            flash("종료일이 선택되지 않았습니다.")
            return redirect("/index/main")
        specify_sales_key, specify_sales_values, specify_sales_counts = specify_sales(start, end)
        for i in range(len(specify_sales_values)) :
            specify_sales_values[i] = format(specify_sales_values[i], ",")
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            report_keys = specify_sales_key,
                            report_values = specify_sales_values,
                            report_counts = specify_sales_counts
                            )
    elif path == "hourly_graph" :
        hourly_sales_keys, hourly_sales_values, hourly_sales_counts = hourly_sales()
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            graph_labels = hourly_sales_keys,
                            graph_datas = hourly_sales_values
                            )
    elif path == "weekly_graph" :
        days_sales_keys, days_sales_values, days_sales_counts = days_sales()
        days_sales_keys = days_sales_keys[:7]
        days_sales_values = days_sales_values[:7]
        days_sales_counts = days_sales_counts[:7]
        for i in range(len(days_sales_keys)) :
            days_sales_keys[i] = int(days_sales_keys[i])
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            graph_labels = days_sales_keys,
                            graph_datas = days_sales_values
                            )
    elif path == "monthly_graph" :
        days_sales_keys, days_sales_values, days_sales_counts = days_sales()
        days_sales_keys = days_sales_keys[:30]
        days_sales_values = days_sales_values[:30]
        days_sales_counts = days_sales_counts[:30]
        for i in range(len(days_sales_keys)) :
            days_sales_keys[i] = int(days_sales_keys[i])
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            graph_labels = days_sales_keys,
                            graph_datas = days_sales_values
                            )
    elif path == "setting_graph" :
        start = (request.form['start'])
        end = (request.form['end'])
        if start == "" :
            flash("시작일이 선택되지 않았습니다.")
            return redirect("/index/main")
        elif end == "" :
            flash("종료일이 선택되지 않았습니다.")
            return redirect("/index/main")
        specify_sales_key, specify_sales_values, specify_sales_counts = specify_sales(start, end)
        for i in range(len(specify_sales_key)) :
            specify_sales_key[i] = int(specify_sales_key[i])
        return render_template('home/index.html', segment='index', 
                            total_sales_data = total_sales_data,
                            total_count_data = total_count_data,
                            top_1_product_data = top_1_product_data,
                            top_company_data = top_company_data,
                            graph_labels = specify_sales_key,
                            graph_datas = specify_sales_values,
                            )



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
