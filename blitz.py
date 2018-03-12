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
import sys
import json
import time
import uuid
import requests
import commands
import mail_conf
import elasticsearch
from modules import Modules
from bmail import send_mail


def preprocessFlowFileJson(document, device):
	#pre-process flowfile basis source device
 	return document

es = elasticsearch.Elasticsearch([{"host": mail_conf.mail_framework_es_index["host"], "port": mail_conf.mail_framework_es_index["port"]}])

device = sys.argv[1]

document = json.loads(sys.stdin.read().strip())

document  = preprocessFlowFileJson(document, device)

mail_id = str(uuid.uuid4()).upper()

any_cond_match = False
send_email = True

mail_config = mail_conf.devices.get(device, None)

#if alert configuration for the device is present
if mail_config:
		
	subject = mail_config['subject']
	mail_title = mail_config['mail_title']
	mail_keys = re.findall("{(.+?)}", subject)
	
	#construction email subject using configuration
	for key in mail_keys:
		t_val = document.get(key, "{%s}" % key)
		subject = subject.replace("{%s}" % key, str(t_val))
	
	#construction email title using configuration
	mail_keys = re.findall("{(.+?)}", mail_title)
	for key in mail_keys:
		t_val = document.get(key, "{%s}" % key)
		mail_title = mail_title.replace("{%s}" % key, str(t_val))

	mail_html = ""
	
	#getting list of enrichment modules for the email alert					
	modu = Modules(mail_config.get("custom_enrichment_data", {}), document)

	if mail_config["enrichment"]:
		if mail_config["enrichment_conditional"]:
			for i, j in mail_config["enrichments"].iteritems():
				if eval(i):
					any_cond_match = True
					for e in j:
						e_enable = e.get("enabled", True)
						if e_enable:
							params = e["e_key"].split(",")
							fn_params = []
							for p in params:
								if p.strip():
									fn_params.append(document[p.strip()])
							e_func = getattr(modu, e['e_func'])
							print "Running Enrichment: %s" % e['e_func']
							data = e_func(*fn_params)
							module_html = modu.generate_html(e['e_name'], data, device)
							mail_html += module_html
					break
			
			if not any_cond_match:
				mail_html += "<i>No Condition matched for Enrichment</i><br><br>"
		else:
			for e in mail_config["enrichments"]:
				e_enable = e.get("enabled", True)
				
				if e_enable:
					params = e["e_key"].split(",")
					fn_params = []
			
					for p in params:
						if p.strip():
							fn_params.append(document[p.strip()])

					e_func = getattr(modu, e['e_func'])
					print "Running Enrichment: %s" % e['e_func']
					data = e_func(*fn_params)
					module_html = modu.generate_html(e['e_name'], data, device)
					mail_html += module_html

	if mail_config["include_json"]:
		mail_html += modu.generate_html("ML MODEL", document, device)

	to_receps = []
	cc_receps = []
	
	if mail_config["mailers"]["override"]:
		to_receps = mail_config["mailers"]["to"]
		cc_receps = mail_config["mailers"]["cc"]
	else:
		to_receps = mail_conf.to + mail_config["mailers"]["to"]
		cc_receps = mail_conf.cc + mail_config["mailers"]["cc"]

	if not any_cond_match and mail_config["send_mail_no_condition_match"] and mail_config["enrichment_conditional"]:
		mail_html += "<i>This mail was sent because the config flag specified mail to be sent when no enrichment condition was fulfilled.</i>"
	
	if not any_cond_match and not mail_config["send_mail_no_condition_match"]:
		send_email = False

	mail_actions_resp = {}
	mail_token_data = {"mail_id": mail_id, "device": device, "reply": False, "in_progress": False, "reply_meta": {}, "actions": []}

	#if send_email option is set to true in the configuraration for the device
	if send_email:
		
		actions = mail_config.get("actions", None)
		buttons_html = ""
		
		#if mail actions specified in configuration
		if actions:
			send_actions = actions.get("send", None)
			if send_actions:	
				
				for s_action in send_actions:
					if s_action[1].get('enabled', True):
						print "Running Action: %s" % s_action[0]
						keyword, retval = modu._call_to_action(s_action[0], s_action[1])
						mail_actions_resp[keyword] = retval
						modu.action_responses[keyword] = retval
					else:
						"Skipping Action: %s" % s_action[0]

			mail_token_data["data"] = mail_actions_resp

			reply_actions = actions.get("reply", None)
			if reply_actions:
				for i in reply_actions:
					mail_token_data["actions"].append(i[0])
			
				buttons_html = modu.get_buttons(reply_actions, mail_token_data)

		fh = open("template.html")
		out_html = fh.read()
		fh.close()
		
		#replacing placeholders in email template
		out_html = out_html.replace("{{{{{button_html}}}}}", buttons_html)
		out_html = out_html.replace("{{{{{mail_html}}}}}", mail_html)
		out_html = out_html.replace("{{{{{mail_title}}}}}", mail_title)
		out_html = out_html.replace("{{{{{summary_text}}}}}", "")
		
		#creating email header data
		mail_token_data['mail_attributes'] = {}
		mail_token_data['mail_attributes']['subject'] = subject
		mail_token_data['mail_attributes']['to'] = to_receps
		mail_token_data['mail_attributes']['cc'] = cc_receps
		epoch = int(time.time())
		mail_token_data['timestamp'] = epoch
		mail_token_data['utc_timestamp'] = epoch - 19800
		print es.index(index = mail_conf.mail_framework_es_index.get("index", "mail_framework"), doc_type = mail_conf.mail_framework_es_index.get("doc_type", "data"), body = mail_token_data, id=mail_id)
		
		#sending alert email to recipients
		send_mail(mail_conf.from_email, to_receps, cc_receps, subject, out_html)













