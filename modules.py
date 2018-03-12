# Copyright 2018 MakeMyTrip (Pradyumn Nand & Kunal Aggarwal)
#
# This file is part of Blitz.
#
# Blitz is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Blitz is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Blitz. If not, see <http://www.gnu.org/licenses/>.

import re
import json
import math
import MySQLdb
import requests
import commands
import textwrap
from bmail import send_mail
from mail_conf import mail_colors, security_key, from_email
from jira.client import JIRA
from Crypto.Cipher import AES
import base64
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# container class for all enrichement modules of the alerting framework 
class Modules:

	# initialise instance of class
	def __init__(self, conf, document):
		self.conf = conf
		self.document = document
		self.gray = False
		self.action_responses = {}

	# get WHOIS information of the IP
	def whois_info(self, ip):
		whois_information = ""
		whois_information = commands.getstatusoutput("whois %s" % ip)
		return whois_information
	
	# get access/httpd logs of the IP 
	def elastic_logs(self, ip):
		es = Elasticsearch([{'host': 'ELASTIC_HOST_IP', 'port': 8888}])
		query_result = es.search(index="ELASTIC_INDEX", body={"query": {"match": {'ip':'%s' % ip}}})
		#process query_result and return it   
		results = ""
		return results

	# perform reverse DNS lookup of the IP
	def reverse_dns(self, ip):
		dns = commands.getstatusoutput("host %s" % ip)
		return "%s<br>" % dns[1]

	# get database results for the IP if available
	def get_data_from_db(self, ip):
		db =  MySQLdb.connect("DB_HOST_IP","USERNAME","PASSWORD","DATABASE_NAME")
		cursor = db.cursor()
		cursor.execute("QUERY")
		results = ""
		#results = cursor.fetchall()
		#process results
		return results

	# get API results for the IP if available
	def get_data_from_api(self, api):
		response = requests.get("http://ip-api.com/json/%s"%(ip))
		# process response
		return response

	def pass_to_mail(self, conf):
        return conf
		print conf
		val = conf["data"]
		mail_keys = re.findall("{(.+?)}", val)
		for lvar in mail_keys:
			t_val = self.document.get(lvar, locals().get(lvar, "{%s}" % lvar))
			val = val.replace("{%s}" % lvar, str(t_val))
                return conf["return_name"], val

    # create a JIRA issue for the alert email
	def jira_create(self, conf):
		jira_options = {'server': conf["conn_details"]['server']}
                jira = JIRA(options=jira_options, basic_auth=(conf["conn_details"]['username'], conf["conn_details"]['password']))
		jira_data = conf['fields']
		new_issue = jira.create_issue(fields=jira_data)
		return str(new_issue)

	# forward the alert email to selected recipients
	def forward_mail(self, conf):
		send_mail(from_email, conf.get('to', []), conf.get("cc", []), conf.get("subject", "Forwarded Mail"), conf['body'])
		return True


	# method to generate body of the alert email
	# title  - email title
	# content - email body
	# device -  the source device for the alert 
	def generate_html(self, title, content, device):
	
		bgcolor = "FFFFFF"
		breakOn = 65
		if self.gray:
			bgcolor = "F8F8F8"
		self.gray = not self.gray

		try:
			if type(content) == type({}) or type(content) == type([]):
				
				content = json.dumps(content, indent = 4)
				content = content.split("\n")
				
				for i, line in enumerate(content):
					if len(line) > breakOn:
						content[i] = textwrap.fill(line, breakOn)
				
				content = "\n".join(content)
				content = content.replace("\n", "<br>").replace(" ", "&nbsp;")
			else:
				raise Exception("Not a valid data type")
		except:
			content = str(content)
			if False:
				content = content.split("\n")
				
				for i, line in enumerate(content):
					if len(line) > breakOn:
						content[i] = textwrap.fill(line, breakOn)
					
				content = "\n".join(content)
				content = content.replace("\n", "<br>")

		return '<tr><td align="center" valign="top"><table border="0" cellpadding="0" cellspacing="0" width="100%%" bgcolor="#%s"><tr><td align="center" valign="top"><table border="0" cellpadding="5" cellspacing="0" width="500" class="flexibleContainer"><tr><td valign="top" width="500" class="flexibleContainerCell"><table align="left" border="0" cellpadding="0" cellspacing="0" width="100%%"><tr><td align="left" valign="top" class="flexibleContainerBox"><table border="0" cellpadding="0" cellspacing="0" width="420" style="max-width: 100%%;"><tr><td align="left" class="textContent"><h3 style="color:#5F5F5F;line-height:125%%;font-family:Helvetica,Arial,sans-serif;font-size:17px;font-weight:normal;margin-top:0;margin-bottom:3px;text-align:left;">%s</h3><div style="text-align:left;font-family:Helvetica,Arial,sans-serif;font-size:13px;margin-bottom:0;color:#5F5F5F;line-height:135%%;">%s</div></td></tr></table></td></tr></table></td></tr></table></td></tr></table></td></tr>' % (bgcolor, title, content)


	# method to get action buttons for an email alert
	# button_conf - to be specified in the mail_conf file
	# mail_token_data - email specific data
	def get_buttons(self, button_conf, mail_token_data):
		base = """
					<tr>
						<td align="center" valign="top">
							<table border="0" cellpadding="0" cellspacing="0" width="100%%" style="color:#FFFFFF;" bgcolor="#FFFFFF">
								<tr>
									<td align="center" valign="top">
										<table border="0" cellpadding="0" cellspacing="0" width="500" class="flexibleContainer">
											%s
										</table>
									</td>
								</tr>
							</table>
						</td>
					</tr>
					"""
		number_of_buttons = len(button_conf)
		number_of_rows = math.ceil(number_of_buttons / 2.0)
		one_button = True if (number_of_buttons % 2) == 1 else False
		last_row = number_of_rows - 1
		row_html = ""
		width = "50%"
		cipher = AES.new(security_key,AES.MODE_ECB) 

		for i in xrange(int(number_of_rows)):
			row_html += """
							<tr>
								<td>
									<table border="0" cellpadding="0" cellspacing="0" width="100%" class="emailButton">
										<tr>
							"""
			if i == last_row and one_button:
				width = "100%"
			
			buttons = button_conf[i * 2 : (i * 2) + 2]
			for btn in buttons:
				t_d = mail_token_data.copy()
				t_d['action'] = btn[0]
				j_d = json.dumps(t_d)
				enc_len = int(math.ceil(len(j_d)/16.0) * 16)
				j_d = j_d.rjust(enc_len)
				action_enc = base64.b64encode(cipher.encrypt(j_d))


				row_html += """
				<td align="center" valign="middle" class="buttonContent" style="padding-top:5px;padding-bottom:5px;padding-right:15px;padding-left:15px;background-color: %s;" width="%s">
					<a style="color:#FFFFFF;text-decoration:none;font-family:Helvetica,Arial,sans-serif;font-size:15px;line-height:135%%;" href="mailto:soc-x@makemytrip.com?subject=Action %s&amp;cc=securityops@makemytrip.com&amp;body=%%0A%%0A%%5BEnter your comments above this line - please do not remove this line%%5D%%0A%%0A======== Please do not change the following section. Corrupted section may fail the operation =========%%0A@@%s@@%%0A%s%%0A=======================================================================================%%0A" target="_blank">%s</a>
				</td>			
				""" % (mail_colors.get(btn[1]['color'], "#1e88e5"), width, btn[0], mail_token_data['mail_id'], action_enc, btn[0])


			row_html += """
							</tr>
						</table>
					</td>
				</tr>
				"""
		
		return base % row_html

	

