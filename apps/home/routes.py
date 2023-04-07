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
def index():
    top_1_product_data = top_1_product()
    top_company_data = top_company()
    total_sales_data = total_sales()
    total_count_data = total_count()
    return render_template('home/index.html', segment='index', 
                           total_sales_data = total_sales_data,
                           total_count_data = total_count_data,
                           top_1_product_data = top_1_product_data,
                           top_company_data = top_company_data
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
