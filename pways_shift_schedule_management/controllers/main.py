# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import content_disposition, request
# from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape


class XLSXReportController(http.Controller):

    @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def get_report_xlsx(self, **kw):
        try:
            model = kw.get('model')
            options = json.loads(kw.get('options', '{}'))
            output_format = kw.get('output_format')
            token = kw.get('token') or 'dummy-because-api-expects-one'
            report_name = kw.get('report_name') or 'report'

            uid = request.session.uid
            report_obj = request.env[model].with_user(uid)

            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.get_xlsx_report(options, response)
                response.set_cookie('fileToken', token)
                return response

            return request.make_response('Invalid output format.', status=400)
        except Exception as e:
            return request.make_response(str(e), status=500)

   
    # @http.route('/xlsx_reports', type='http', auth='user', methods=['POST'], csrf=False)
    # def get_report_xlsx(self, model, options, output_format, token, report_name, **kw):
    #     uid = request.session.uid
    #     report_obj = request.env[model].with_user(uid)
    #     options = json.loads(options)
    #     token = 'dummy-because-api-expects-one'
    #     try:
    #         if output_format == 'xlsx':
    #             response = request.make_response(
    #                 None,
    #                 headers=[
    #                     ('Content-Type', 'application/vnd.ms-excel'),
    #                     ('Content-Disposition', content_disposition(report_name + '.xlsx'))
    #                 ]
    #             )
    #             report_obj.get_xlsx_report(options, response)
    #         response.set_cookie('fileToken', token)
    #         return response
    #     except Exception as e:
    #         # se = _serialize_exception(e)
    #         # error = {
    #         #     'code': 200,
    #         #     'message': 'Odoo Server Error',
    #         #     'data': e
    #         # }
    #         return e