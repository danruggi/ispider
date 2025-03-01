from ispider_core import ISpider

# Run only 'stage1'
data = ISpider(["deskydoo.com", "another.com"], stage="stage1").run()

print(data)  # {'emails': [...], 'social_links': [...]}
