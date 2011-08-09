#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import Error
from google.appengine.ext.webapp import template

import os
import re
import string
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), 'lib'))
from lib import feedparser

class MainHandler(webapp.RequestHandler):
  def get(self):
   
      # Incoming url parameters
      # iGoogle prepends var names with 'up_' for some reason...
      subreddits = self.request.get('up_subreddits')    # Pipe separated list of subreddits for top menu
      width = self.request.get('up_width', '500')       # Truncate headline chars, default 500
      imgur_switch = self.request.get('up_imgur', 1)    # Imgur mirror, 1=imgur, 2=mirur, 3=filmot
      feed = self.request.get('r', 'all')               # Current requested subreddit feed
      
      try:
        # Fetch and parse the feed
        rss = urlfetch.fetch(self.feed_to_url(feed), headers = {'Cache-Control' : 'max-age=0'})
        parsed = feedparser.parse(rss.content)
        stories = []

        for entry in parsed.entries:     
          comment_count = self.get_comment_count(entry.summary_detail)
    
          # Extract the external link url, and transform imgur links to requested mirror
          external_link = self.transform_url(self.get_external_link(entry.summary_detail), int(imgur_switch))

          # Build a hash object for each story...
          parsed_story_hash = {
            'full_title' : entry.title_detail.value, # Full, non-truncated title just in case
            'fixed_width_title' : self.truncate(entry.title_detail.value, int(width)),
            'external_link' :  external_link,
            'comment_link' : entry.link,
            'comment_count' : comment_count
          }
          
          # ... and append to the stories list
          stories.append(parsed_story_hash)

        # The main data is 'stories'.  Everything else is 
        # there to persist the URL parameters.
        template_data = {
          'subreddits' : subreddits.split('|'),
          'link_subreddits' : subreddits,
          'link_imgur' : imgur_switch,
          'width' : width,
          'current_feed' : str(feed),
          'stories' : stories
        }
        
        # Finally, render the template with the data
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        self.response.out.write(template.render(path, template_data))

      except:
        self.response.out.write('<a style="font-size:1em;font-weight:bold;text-decoration:none;" href="http://www.downforeveryoneorjustme.com/reddit.com">is reddit down?</a>')

  def feed_to_url(self, feed):
    ''' Return URL for subreddit feed '''
    if feed == 'all':
      return 'http://www.reddit.com/.rss'
    else:
      return 'http://www.reddit.com/r/%s.rss' % (feed)

  def get_comment_count(self, summary_detail):
    ''' Extract comment count from the hideous summary detail HTML '''
    try:
      return re.findall(r"\[(\d*) comment[s]\]", summary_detail.value)[0]
    except IndexError:
      return "0"

  def get_external_link(self, summary_detail):
    ''' Extract external link from the ungainly summary detail HTML '''
    try:
      return re.findall(r"href=\"(\S*)\">\[link\]", summary_detail.value)[0]
    except IndexError:
      return 'http://www.reddit.com/need_to_separate_out_external_links_in_their_rss_feed'

  def transform_url(self, url, mirror_id):
    ''' Check and tranform imgur links to selected mirror '''
    if mirror_id == 1:
      return url
    else:
      try:
        imgur_uri = re.findall(r"imgur\.com\/([A-Za-z0-9\.]+)", url)[0]
        if mirror_id == 2:
          url = 'http://i.filmot.com/%s' % (imgur_uri)
        if mirror_id == 3:
          url = 'http://i.filmot.org/%s' % (imgur_uri)

        return url
      except:
        return url

  def truncate(self, headline, width):
    if len(headline) > width:
      return headline[:width] + '...'
    else:
      return headline

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
