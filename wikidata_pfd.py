#!/usr/bin/python
# -*- coding: utf-8  -*-
# Archive closed bot requests
# Mike Peel     11-Oct-2021      v1 - start

import pywikibot
import numpy as np
import time
import string
from pywikibot import pagegenerators
from pywikibot.data import api
import urllib
import random
from datetime import datetime

def rebuild_watchnotice(props):
	text = "<ul class='hlist' style='display: inline; margin: 0;'><onlyinclude>"
	for prop in props:
		text = text + "{{PropertyRFD|" + prop.replace('P','').replace('p','') + "}} "
	text = text + "</onlyinclude></ul>"
	return text

# Sites
wikidata_site = pywikibot.Site("wikidata", "wikidata")
repo = wikidata_site.data_repository()  # this is a DataSite object

# Get the current archive page
if datetime.now().strftime('%Y') == '2022':
	archivepagename = 'Wikidata:Properties for deletion/Archive/2022/4'
else:
	archivepagename = 'Wikidata:Requests for permissions/RfBot/'+datetime.now().strftime('%Y')
archivepage = pywikibot.Page(wikidata_site, archivepagename)
newarchivepage = archivepage.text

# Get the list of open PfD requests
listpage = pywikibot.Page(wikidata_site, 'Wikidata:Properties for deletion')
split_text = '<!-- Below are request currently on hold, means consensus has been reached and they are waiting for deletion -->'
newpage = listpage.text.split(split_text)[0]
newpage_part2 = split_text + listpage.text.split('split_text')[1]
lines = newpage.splitlines()

# Get the watchlist notice code
watchlist = pywikibot.Page(wikidata_site, 'Template:Watchlist summary/PFD')
split = watchlist.text.split('{{PropertyRFD|')
pfd_on_notice = []
for pfd_line in split:
	prop = pfd_line.split('}}')[0]
	if prop not in pfd_on_notice and len(prop) < 5:
		pfd_on_notice.append(prop)
print(pfd_on_notice)

# Now let's run through the list and see what has been approved or withdrawn
for line in lines:
	if ('Wikidata:Properties for deletion' in line) and 'Header' not in line and 'text/' not in line: and 'text2/' not in line and "<!--" not in line:
		pagetitle = line.strip().replace('{{','').replace('}}','')
		print(pagetitle)
		pid = pagetitle.split('/')[1].replace('P','').replace('p','')
		pfdpage = pywikibot.Page(wikidata_site, pagetitle)

		# Check the last 3 lines of the proposal to see if it's closed
		pfdlines = pfdpage.text.splitlines()
		if '{{discussion bottom}}' in pfdlines[-1].lower() or '{{discussion bottom}}' in pfdlines[-2].lower() or '{{discussion bottom}}' in pfdlines[-3].lower():
			# Add to the archive
			newarchivepage = newarchivepage + '\n' + line
			# Remove from PfD
			newpage = newpage.replace(line, '')

			# Remove it from the watchlist
			if pid in pfd_on_notice:
				pfd_on_notice.remove(pid)
				watchlist.text = rebuild_watchnotice(pfd_on_notice)
				watchlist.save('- [[Property:P'+pid+']] ([[Wikidata:Properties_for_deletion/P'+pid+'|discussion]]')
		else:
			# If it's not on the PfD list, add it
			if pid not in pfd_on_notice:
				pfd_on_notice.append(pid)
				watchlist.text = rebuild_watchnotice(pfd_on_notice)
				watchlist.save('+ [[Property:P'+pid+']] ([[Wikidata:Properties_for_deletion/P'+pid+'|discussion]]')

# Do some last tidying up
newpage = newpage.replace('Properties_for_deletion','Properties for deletion')
newpage = newpage.replace('\n\n\n','\n')

# And save things
archivepage.text = newarchivepage
archivepage.save('Archiving from [[Wikidata:Properties for deletion]]')
listpage.text = newpage + newpage_part2
listpage.save('Archiving closed requests to [['+archivepagename+']]')
