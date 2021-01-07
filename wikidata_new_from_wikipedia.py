#!/usr/bin/python
# -*- coding: utf-8  -*-
# Create new Wikidata items for enwp articles and categories
# Mike Peel     03-Jan-2021      v1 - start
# Mike Peel		05-Jan-2021		 v2 - expand based on newitem.py

import pywikibot
from pywikibot import pagegenerators
from pywikibot.data import api
import datetime

wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()  # this is a DataSite object

wikipedias = ['en']
templates_to_skip = ['Q4847311','Q6687153','Q21528265','Q26004972','Q6838010','Q14446424','Q7926719','Q5849910','Q6535522','Q12857463','Q14397354','Q18198962','Q13107809','Q6916118','Q15630429','Q6868608','Q6868546','Q5931187','Q26021926','Q21684530','Q20310993','Q25970270','Q57620750','Q4844001','Q97159332','Q20765099','Q17586361','Q17588240','Q13420881','Q17589095','Q17586294','Q13421187','Q97709865','Q17586502','Q5828850']
maxnum = 100
nummodified = 0
days_since_last_edit = 1.0
days_since_last_edit_but_search = 7.0
days_since_creation = 14.0

debug = True

def search_entities(site, itemtitle):
	 params = { 'action' :'wbsearchentities', 
				'format' : 'json',
				'language' : 'en',
				'type' : 'item',
				'search': itemtitle}
	 request = api.Request(site=site, parameters=params)
	 return request.submit()


for prefix in wikipedias:
	wikipedia = pywikibot.Site(prefix, 'wikipedia')

	# Set up the list of templates to skip
	# Adapted from https://gerrit.wikimedia.org/g/pywikibot/core/+/HEAD/scripts/newitem.py
	skipping_templates = set()
	for item in templates_to_skip:
		template = wikipedia.page_from_repository(item)
		if template is None:
			continue
		skipping_templates.add(template)
		# also add redirect templates
		skipping_templates.update(template.getReferences(follow_redirects=False, with_template_inclusion=False, filter_redirects=True, namespaces=wikipedia.namespaces.TEMPLATE))
		print(template.title())

	# Start running through unconnected pages
	pages = wikipedia.querypage('UnconnectedPages')
	for page in pages:
		# page = pywikibot.Category(wikipedia, 'Category:Assessed-Class Gaul articles')
		# print("\n" + "http://"+prefix+".wikipedia.org/wiki/"+page.title().replace(' ','_'))

		## Part 1 - quick things to check

		# Articles and categories only
		if page.namespace() != wikipedia.namespaces.MAIN and page.namespace() != wikipedia.namespaces.CATEGORY:
			# print('bad namespace')
			continue
		# Exclude redirects
		if page.isRedirectPage():
			# print('is redirect')
			continue
		if page.isCategoryRedirect():
			# print('is redirect')
			continue

		## Part 2 - parse the page info
		print("\n" + "http://"+prefix+".wikipedia.org/wiki/"+page.title().replace(' ','_'))

		# Check to see if it contains templates we want to avoid
		trip = 0
		for template, _ in page.templatesWithParams():
			if template in skipping_templates:
				trip = template.title()
		if trip != 0:
			print('Page contains ' + str(trip) + ', skipping')
			continue

		# Check for the last edit time
		lastedited = page.editTime()
		lastedited_time = (datetime.datetime.now() - lastedited).seconds/(60*60*24)
		if lastedited_time < days_since_last_edit:
			print('Recently edited ('+str(lastedited_time)+')')
			continue

		# Check for the creation time
		created = page.oldest_revision.timestamp
		created_time = (datetime.datetime.now() - created).seconds/(60*60*24)
		if created_time < days_since_last_edit:
			print('Recently created ('+str(created_time)+')')
			continue

		## Part 3 - look up more information

		# Check if we have a Wikidata item already
		try:
			wd_item = pywikibot.ItemPage.fromPage(page)
			item_dict = wd_item.get()
			qid = wd_item.title()
			print("Has a sitelink already - " + qid)
			continue
		except:
			print(page.title() + ' - no page found')

		# If we have a category, make sure it isn't empty
		if page.namespace() == wikipedia.namespaces.CATEGORY:
			if page.isEmptyCategory():
				# print('Is empty')
				continue
			if page.isHiddenCategory():
				# print('Is hidden')
				continue

		# See if search returns any items
		wikidataEntries = search_entities(repo, page.title())
		if wikidataEntries['search'] != []:
			if lastedited_time < days_since_last_edit_but_search:
				print('Recently edited with search results ('+str(lastedited_time)+')')
				continue

		## Part 4 - editing

		# If we're here, then create a new item
		data = {'labels': {prefix: page.title()}, 'sitelinks': [{'site': prefix+'wiki', 'title': page.title()}]}
		test = 'y'
		if debug:
			print(data)
			test = input('Continue?')
		if test == 'y':
			new_item = pywikibot.ItemPage(repo)
			new_item.editEntity(data, summary="Creating item from " + prefix +"wiki")
			nummodified += 1
			if page.namespace() == wikipedia.namespaces.CATEGORY:
				# We have a category, also add a P31 value
				claim = pywikibot.Claim(repo,'P31')
				if page.isDisambig():
					claim.setTarget(pywikibot.ItemPage(repo, 'Q15407973')) # Wikimedia disambiguation category
				else:
					claim.setTarget(pywikibot.ItemPage(repo, 'Q4167836')) # Wikimedia category
				new_item.addClaim(claim, summary='Category item')
			else:
				if page.isDisambig():
					claim = pywikibot.Claim(repo,'P31')
					claim.setTarget(pywikibot.ItemPage(repo, 'Q4167410')) # Disambiguation page
					new_item.addClaim(claim, summary='Disambig page')

		## Part 5 - tidy up

		# Touch the page to force an update
		try:
			page.touch()
		except:
			null = 0

		# Cut-off at a maximum number of edits	
		print("")
		print(nummodified)
		if nummodified >= maxnum:
			print('Reached the maximum of ' + str(maxnum) + ' entries modified, quitting!')
			exit()

# EOF