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


import smtplib
from os.path import basename
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText
from email.MIMEBase import MIMEBase
from email import encoders
 
def send_mail(from_email, to, cc, subject, b, files = None ):
	fromaddr = from_email
	toaddr = ", ".join(to)
	ccaddr = ", ".join(cc)
	msg = MIMEMultipart()
	 
	msg['From'] = fromaddr
	msg['To'] = toaddr
	msg['CC'] = ccaddr
	msg['Subject'] = subject
	 
	body = b
	 
	msg.attach(MIMEText(body, 'html'))
	
	if files: 
		filename = basename(files)
		attachment = open(files, "rb")
		 
		part = MIMEBase('application', 'octet-stream')
		part.set_payload((attachment).read())
		encoders.encode_base64(part)
		part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
	 
		msg.attach(part)
	 
	server = smtplib.SMTP('SMTP_DOMAIN_NAME')
	text = msg.as_string()
	server.sendmail(fromaddr, to + cc, text)
	server.quit()
