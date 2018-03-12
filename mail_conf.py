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


# add default email information - from, to and CC fields of the alert email
from_email = ""
to = [""]
cc = []
#add security key for encryption mail actions 
security_key = "SECURITY_KEY"

#add/edit color scheme of the email
mail_colors = {
        "red":    "#f44336",
        "blue":   "#1e88e5",
        "green":  "#4caf50",
        "orange": "#ff9800"
}

mail_framework_es_index = {
        #edit IP and port to point to the elastic index 
	"host": "ELASTIC_HOST_IP",
	"port": 8080,
	"index": "mail_framework",
	"doc_type": "data"
}

# this is the consolidated configuration of the all devices hooked  to the email alerting framework
devices = {
        
        "device_1" : {

                #email subject and title with appropriate placeholders for dynamic data
                "subject" : "Email Alert : {ip_src_addr} : {param2}",
                "mail_title" : "{param3}"
                
                "enrichment" : True,
                #whether the enrichments are executed basis key being evaluated as a conditional expression 
                "enrichment_conditional" : False,
                # list to enrichments to be fetched for the alert basis parameter input
                "enrichments" : [
                        {"e_name" : "Data from DB", "e_func" : "get_data_from_db", "e_key" : "ip_src_addr", "enabled": True},
                        {"e_name" : "Data from API", "e_func" : "get_data_from_api", "e_key" : "ip_src_addr", "enabled": True},
                        {"e_name" : "WhoIs lookup", "e_func" : "whois_info", "e_key" : "ip_src_addr", "enabled": True},
                        {"e_name" : "Reverse DNS lookup", "e_func" : "reverse_dns" , "e_key" : "ip_src_addr", "enabled": True},
                        {"e_name" : "Access Log Summary", "e_func" : "elastic_logs", "e_key" : "ip_src_addr", "enabled": True}
                ], 

                #custom data to execute enrichments
                "custom_enrichment_data": [{
                        "index": "ELASTIC_INDEX_NAME",
                        "es_host": "ELASTIC_HOST_IP",
                        "query_data": [
                                {
                                        "method": "POST",
                                        "url": "/_msearch?timeout=0&ignore_unavailable=true",
                                        "query": '{"index":||list_indexes||,"search_type":"count","ignore_unavailable":true}\r\n{"size":0,"query":{"filtered":{"query":{"query_string":{"query":"*","analyze_wildcard":true}},"filter":{"bool":{"must":[{"query":{"match":{"ip_src_addr":{"query":||ip_src_addr||,"type":"phrase"}}}}],"must_not":[]}}}},"aggs":{"2":{"terms":{"field":"eventName","size":20,"order":{"_count":"desc"}}}}}\r\n'
                                },
                        ],
                }],
                
                "send_mail_no_condition_match": True,
                
                "mailers": {
                #if existing mailer list (To and CC should be overriden)
                "override": False,
                #list of primary recipients
                "to": ["PRIMARY_RECIPIENT"],
                #list of secondary recipients
                "cc": ["SECONDARY_RECIPIENT"]
                },
                
                #append the input json to the alert mail
                "include_json": True,

                #action configurations 
                "actions": {
        
                    "send": [
                              ("pass_to_mail",
                              {
                                "return_name": "ip_src_addr",
                                "data": "{ip_src_addr}",
                                "enabled": True
                              }),
                              ("pass_to_mail",
                              {
                                "return_name": "parameter 2",
                                "data": "{param2}",
                                "enabled": True
                              }),  
                    ],
                    "reply": [
                              ("Create JIRA",
                                {
                                "color": "orange",
                                "actions": [
                                  ("jira_create",
                                  {
                                    "enabled": True,
                                    "return_name": "jira_id",
                                    "data": {
                                      "conn_details": {
                                        "server": "JIRA_URL",
                                        "username": "XXXXXXXX",
                                        "password": "XXXXXXXX",
                                        
                                      },
                                      "fields": {
                                        'project': 'JIRA_PROJECT_NAME',
                                        'issuetype': {
                                          'name': 'Task'
                                        },
                                        'summary': 'device1 - {ip_src_addr}',
                                        'customfield_13106': {
                                          'id': '12309'
                                        },
                                        'customfield_13111': 'NA',
                                        'customfield_13104': '{ip_src_addr}',
                                        'description': "EVENT_DESCRIPTION"
                                      }
                                    }
                                  }),
                                  
                                ]
                              }),
                              ("forward_mail", {
                                                        "return_name": "fmail",
                                                        "data": {               
                                                                "to": ["PRIMARY_RECIPIENT"],
                                                                "subject": "Block IP on Firewall - {ip_src_addr}",
                                                                "body": "Please Block IP on Firewall - {ip_src_addr}",
                                                        },
                                                }),
                    ],
                    
                  },
        
        },
}
