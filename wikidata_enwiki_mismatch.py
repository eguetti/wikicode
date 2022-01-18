#!/usr/bin/python
# -*- coding: utf-8  -*-
# Import coordinates from enwp
# 23 Dec 2020	Mike Peel	Started

import pywikibot
from pywikibot import pagegenerators
lang = 'en'
wiki = pywikibot.Site(lang, 'wikipedia')
repo = wiki.data_repository()
debug = False
maxpercat=5

cat = pywikibot.Category(wiki, 'Category:Wikipedia categories tracking Wikidata differences')
for subcat in pagegenerators.SubCategoriesPageGenerator(cat, recurse=False):
	if debug:
		print('# ' + str(subcat.title()))
	propid = ''
	templatename = ''
	for template in subcat.templatesWithParams():
		if 'Wikidata tracking category' in template[0].title():
			if debug:
				print('# ' + str(template))
			for val in template[1]:
				if 'property' in val:
					propid = val.split('=')[1].strip()
				if 'template' in val:
					templatename = val.split('=')[1].strip()
	if debug:
		print('#' + propid)
		print('#' + templatename)

	# If we haven't got a propid or template, then skip this category
	if propid == '' or template == '':
		continue

	i = 0
	for page in pagegenerators.CategorizedPageGenerator(subcat, recurse=False):
		i += 1
		if i > maxpercat:
			continue
		if debug:
			print('# ' + str(page))
		try:
			localid = ''
			for template in page.templatesWithParams():
				if debug:
					print(template[0].title())
				if templatename in template[0].title():
					for val in template[1]:
						if debug:
							print(val)
						if '=' not in val and localid == '':
							localid = val
						if 'id=' in val and localid == '':
							localid = val.split('=')[1].strip()
			if debug:
				print('#' + str(localid))
			if localid != '':
				# We have a local ID, check for a Wikidata value
				try:
					wd_item = pywikibot.ItemPage.fromPage(page)
					item_dict = wd_item.get()
				except:
					# print("No Wikidata sitelink found")
					continue
				wikidataval = ''
				snakid = ''
				try:
					wikidataval = item_dict['claims'][propid]
				except:
					null = 0
				if wikidataval != '':
					# print(wikidataval)
					count = 0
					for clm in wikidataval:
						# print(clm)
						snakid = clm.snak
						count += 1
						compval = clm.getTarget().title()
					if count == 1 and localid.strip() != compval.strip():
						# OK, we have a local ID, and a single Wikidata ID, return for mismatch
						print(snakid + ','+propid+','+compval+','+localid+',http://en.wikipedia.org/wiki/'+page.title().replace(' ','_'))
		except:
			continue
