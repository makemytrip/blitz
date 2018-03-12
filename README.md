# Blitz - Incident Response Automation Framework

Blitz is an open source incident response automation framework to aimed at accelerating incident triage, tracking and response capabilities. The framework allows:

- Device agnostic alert ingest

- Alert enrichment from internal / external sources

- Automated / one-click response action - from the alert itself!


## How Blitz works:

Blitz assumes input as an alert data file structured in JSON format. The alert data can be further enriched with different enrichment modules. Blitz parses the input file and picks up information regarding the source, alert type, alert metadata etc. The output of the framework is an alert email configured for delivery to intended recipients - the framework can be extended to alternate delivery methods as well as long as a python module can be written. 

We recommend using Apache Nifi for creating and managing alert data files to the Blitz framework as it allows ingestion, parsing and structuring of information in a manner suitable for consumption by the framework. However one can choose any other suitable alternative.

The illustration below depicts the functioning of the framework.

[![image](blitz/images/blitz_illustration.png)]()

#### Sample use cases / implementations:

- Endpoint Incident Response & Automation
- Perimeter / Website Incident Response & Automation
- Incident Tracking (via JIRA)
- Alert Enrichment - the framework already contains multiple default enrichment methods (available in modules.py) such as reverse DNS, WhoIs

## Getting Started

Blitz requires Python 2.6.x to run. In order to deploy Blitz on your production system, you need to install the following additional modules.

<b>Requests</b>
```
  pipenv install requests
```
<b>Elastic Search</b>
```
  pip install elasticsearch
```
<b>MySQLdb</b> (assuming you have MySQL integration for fetching enrichment data)
```
  apt-get install python-dev libmysqlclient-dev
  pip install MySQL-python
```
<b>JIRA</b> (for raising ticket as alert action)
```
  pip install jira
```
<b>Crypto</b>
```
pip install crypto
```

<b>Clone the repository</b>

    git clone https://github.com/makemytrip/blitz.git


## Structure of Blitz
The blitz framework essentially comprises of the following files:

```
├── blitz/
|   ├── modules.py
|   ├── mail_conf
|   ├── template.html
|   ├── blitz.py
|   ├── bmail.py
```

### blitz.py

It is the heart of the framework, which is agnostic to alert source and data. This is the file to be executed by providing an alert data file and source (detector) as input to generate an incident notification & respective actions.

Usage example :

    blitz.py <detector> < path/to/alert_data_file

Here detector should be replaced by the name of the source configured in <b>mail_conf</b> and the path to the alert data file passed as the other argument.


### mail_conf

mail_conf stores configurations for all data sources. One can provide the source_name, the enrichments to execute, the intended recipients and the actions associated with the alert. A sample configuration is shown below:

    "device_1": {
      "subject": "Email Alert : {ip_src_addr} : {param2}",
      "mail_title": "{param3}""enrichment": True,
      "enrichment_conditional": False,
      "enrichments": [
        {
          "e_name": "Data from DB",
          "e_func": "get_data_from_db",
          "e_key": "ip_src_addr",
          "enabled": True
        },
        
      ],
      "custom_enrichment_data": [
        {
          "index": "ELASTIC_INDEX_NAME",
          "es_host": "ELASTIC_HOST_IP",
          "query_data": [
            {
              "method": "POST",
              "url": "/_msearch?timeout=0&ignore_unavailable=true",
              "query": '{"index":||list_indexes||,"search_type":"count","ignore_unavailable":true}\r\n{"size":0,"query":{"filtered":{"query":{"query_string":{"query":"*","analyze_wildcard":true}},"filter":{"bool":{"must":[{"query":{"match":{"ip_src_addr":{"query":||ip_src_addr||,"type":"phrase"}}}}],"must_not":[]}}}},"aggs":{"2":{"terms":{"field":"eventName","size":20,"order":{"_count":"desc"}}}}}\r\n'
            },
            
          ],
          
        }
      ],
      "send_mail_no_condition_match": True,
      "mailers": {
        "override": False,
        "to": [
          "PRIMARY_RECIPIENT"
        ],
        "cc": [
          "SECONDARY_RECIPIENT"
        ]
      },
      "include_json": True,
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
          
        ],
        
      },
      
    }

## Writing a configuration

A configuration describes an alert source, associated enrichments, intended recipients and alert actions. The template shown above can be interpreted and modified by understanding the following key terms:

- <b>device_1</b> : name of the source/device for which the alert has to be generated

- <b>subject</b> : subject of the email alert, here ip_src_addr and param2 are placeholders for keys that are assumed to be present in the input alert data and will be subsequently replaced by their corresponding values.

- <b>mail_title</b> : title of the email HTML, with provision for placeholder keys from input data

- <b>enrichment_conditional</b> : boolean to indicate if the enrichment is to be performed conditionally, if True then the list of enrichment will be executed basis a condition specified in the key for which the list of enrichments is mapped.

Example of conditional enrichment : 

    "enrichment_conditional": True,
    "enrichments": {
      "python conditional expression": [
        {
          "e_name": "Data from DB",
          "e_func": "get_data_from_db",
          "e_key": "ip_src_addr",
          "enabled": True
        },
        
      ],
      
    }

We can have multiple comma separated conditional enrichment blocks in the configuration file.

  - <b>enrichments</b> : a list of JSONs representing enrichment methods written in modules.py which are fired and return additional information about the alert. 
    The structure of the JSON includes:<br>
    - <b>e_name</b> : descriptive name of the enrichment<br>
    - <b>e_func</b> : method name as specified in modules.py<br>
    - <b>e_key</b> : comma separated method parameters that are present in the alert input data<br>
    - <b>enabled</b> : boolean representing if the enrichment is to be executed.<br>

  - <b>send_mail_no_condition_match</b> : boolean to decide if mail is to be sent in case no conditional enrichment matches the alert

  - <b>mailers</b> : this node is used to store additional recipients of the alert email apart from the default recipients configured in the initial stage. The 'override' key specifies if the default recipient list is to be overidden for the given source, else the list provided in this node is appended to the default list.

  - <b>include_json</b> : boolean to indicate if the input alert data is to be included in the alert email

  - <b>actions</b> : the 'actions' node is used to configure actions for the alert. Examples of actions can be forwarding of email, creating JIRA ticket, launching scan, blocking IP etc. The 'actions' node has outer level nodes 'send' and 'reply'. 


### modules.py

It is a container class for all enrichment methods. It is instantiated in blitz.py with the input alert data so that the data is available to all the enrichment methods. One can write a variety of enrichments to suit their needs. These enrichments can then be mapped to sources in the configuration (mail_conf)

### template.html

It is a generic HTML template to build an email alert. It has placeholders where title, body, action buttons are replaced with actual data according to the configuration. One can also write a custom template with specific layouts/schemes etc.


## Integrating your own source in Blitz

The best approach for integrating a source is to visualise the output i.e. alert email itself with all the enrichments needed to make the alert more useful and actionable. 

  1. Use the mail_conf template provided above to create a configuration for your source. Add details in the configuration as per the organisation's infrastructure. Add the configuration in the mail_conf (replace the default one if present).

  2. Categorise enrichments logically into modules and add methods for each module in modules.py. Enrichments could be database, API, cache lookups etc. The output of an enrichment module should either be a list or dictionary so that HTML can be generated from it easily.

  3. Add module details in the enrichment section of the configuration.

  4. Configure script execution with the required inputs for the incoming alerts and test with a few input cases to tweak output as desired. 

  5. Voila ! you have successfully configured a new source in the alerting framework.


## License
This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details. http://www.gnu.org/licenses/.

[![](https://www.gnu.org/graphics/gplv3-127x51.png)](https://www.gnu.org/licenses/gpl.txt)


## Authors
- <b>Pradyumn Nand</b>
- <b>Kunal Aggarwal</b>
