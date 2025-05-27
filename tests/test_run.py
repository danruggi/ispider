from ispider_core import ISpider

if __name__ == '__main__':
	doms = ["https://www.hostelworld.com/"]
	ISpider(domains=doms, stage="crawl").run()
	ISpider(domains=doms, stage="spider").run()
	quit()
