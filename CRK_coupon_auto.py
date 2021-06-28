# -*- coding: utf-8 -*-

import os, sys, time, csv, datetime, re, json, requests
import twitter
from selenium import webdriver
import configparser

######################################################################

# Twitter API token
config = configparser.ConfigParser()
config.read('config.ini')

# CRK_coupon_auto > Consumer Keys > API Key and Secret
CONSUMERAPIKEY = config['twitterAPI']['CONSUMERAPIKEY']
CONSUMERSECRETKEY = config['twitterAPI']['CONSUMERSECRETKEY']

# CRK_coupon_auto > Authentication Tokens > Access Token and Secret
AUTHACCESSTOKEN = config['twitterAPI']['AUTHACCESSTOKEN']
AUTHACCESSSECRET = config['twitterAPI']['AUTHACCESSSECRET']

######################################################################

# Kakao API token

# KAKAOAPIURL = "https://kapi.kakao.com/v2/api/talk/memo/default/send"
# 
# KAKAO_headers = {
# 	"Authorization": "Bearer " + ""
# }
# 
# KAKAO_data = {
# 	"template_object" : json.dumps({
# 		"object_type" : "text",
# 		"text" : "helloworld",
# 		"link" : {
# 			"web_url" : ""
# 		}
# 	})
# }

######################################################################

Emails = config['Users']['Emails'].split(',')

HOMEPATH = ""

######################################################################

def couponcodeParsing():
	couponlist = []
	twt_api = twitter.Api(
		consumer_key=CONSUMERAPIKEY,
		consumer_secret=CONSUMERSECRETKEY,
		access_token_key=AUTHACCESSTOKEN,
		access_token_secret=AUTHACCESSSECRET
	)
	
	account = "@CRKingdom_TIPS"
	statuses = twt_api.GetUserTimeline(screen_name=account, count=500, include_rts=True, exclude_replies=False)

	reg = re.compile(r'[A-Z0-9]')
	couponlist = []
	couponcodelist = []
	for status in statuses:
		iscoupontwt = False
		textsplit = status.text.split()
		for word in textsplit:
			if len(word) == 16 and reg.match(word):
				twtlink = "https://twitter.com/CRKingdom_TIPS/status/" + status.id_str
				couponcode = word
				tmp = [couponcode, status.created_at, twtlink]
				if couponcode not in couponcodelist:
					couponcodelist.append(couponcode)
					couponlist.append(tmp)
	
	couponlist.reverse()
	return couponlist


def main():
	homepath = HOMEPATH
	if homepath == "":
		homepath = os.getcwd()
	couponlist_csv = homepath + "\\couponlist.csv"

	if os.path.exists(homepath + ".\\log") != True:
		os.mkdir(homepath + ".\\log")
	
	logfile = homepath + "\\log\\" + (datetime.datetime.now()).strftime("%y%m%d") + ".log"
	flog = open(logfile, 'a')

	log_couponlist = []

	if os.path.exists(couponlist_csv) == False:
		ftmp = open(couponlist_csv, 'w')
		ftmp.close()
	else:
		fr = open(couponlist_csv, 'r', newline='')
		reader = csv.reader(fr, delimiter=',')

		for line in reader:
			if not line:
				break
			log_couponlist.append(line)
		#print("log_couponlist")
		#print(log_couponlist)
		fr.close()

	couponlist = couponcodeParsing()
	loggingstr = "[" + (datetime.datetime.now()).strftime("%H:%M:%S") + "] "
	loggingstr = loggingstr + "reading twitter completed - last coupon: " + couponlist[-1][0]
	flog.write(loggingstr + "\n")
	new_couponlist = []
	
	if len(log_couponlist) == 0:	# couponlist.csv가 신규 생성됨
		new_couponlist = couponlist
	else:	# couponlist는 이미 있었고
		for coupon in couponlist:
			if coupon in log_couponlist:	# twitter에서 읽어온 것 중에 신규 쿠폰은 없다
				continue
			else:	# 신규 쿠폰 있음!
				print("new coupon: ", str(coupon))
				new_couponlist.append(coupon)

	if len(new_couponlist) != 0:
		fa = open(couponlist_csv, 'a', newline='')
		writer = csv.writer(fa, delimiter=',')

		options = webdriver.ChromeOptions()
		options.add_argument("headless")
		driver = webdriver.Chrome("./chromedriver.exe", options=options)

		for new_coupon in new_couponlist:
			writer.writerow(new_coupon)
			for email in Emails:
				try:
					driver.get("https://game.devplay.com/coupon/ck/ko")
					driver.find_element_by_id("email-box").send_keys(email)
					driver.find_element_by_id("code-box").send_keys(new_coupon[0])
					driver.find_element_by_xpath("/html/body/div/div[1]/div[2]/form/div[4]/div").click()
					time.sleep(5)
					try:
						alert = driver.switch_to_alert()
						loggingstr = "[{datetimenow}] {couponcode} {email} {alerttext}".format(datetimenow=(datetime.datetime.now()).strftime("%H:%M:%S"), couponcode=new_coupon[0], email=email, alerttext=alert.text)
						flog.write(loggingstr + "\n")
						alert.accept()
						print
					except Exception as e:
						loggingstr = "[{datetimenow}] {couponcode} {email} {errmessage}".format(datetimenow=(datetime.datetime.now()).strftime("%H:%M:%S"), couponcode=new_coupon[0], email=email, errmessage=str(e))
						flog.write(loggingstr + "\n")
				except Exception as e:
					loggingstr = "[{datetimenow}] {couponcode} {email} {errmessage}".format(datetimenow=(datetime.datetime.now()).strftime("%H:%M:%S"), couponcode=new_coupon[0], email=email, errmessage=str(e))
					flog.write(loggingstr + "\n")
				print(loggingstr)
	
		driver.close()
		fa.close()
		
	loggingstr = "[{datetimenow}] script runned.".format(datetimenow=(datetime.datetime.now()).strftime("%H:%M:%S"))
	flog.write(loggingstr + "\n")
	flog.close()

if __name__ == "__main__":
	main()
	sys.exit(0)
