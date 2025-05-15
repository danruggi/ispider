from ispider_core import ISpider

doms = ["another.com", 'hostelworld.com', 'test.com']
ISpider(domains=doms, stage="stage1").run()
ISpider(domains=doms, stage="stage2").run()
