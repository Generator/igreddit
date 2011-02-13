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
from google.appengine.ext.webapp import template
import feedparser
import os
import re
import string

class MainHandler(webapp.RequestHandler):

  def get(self):
      
      subreddits = self.request.get('up_subreddits') # Pipe separated list of subreddits for top menu
      width = self.request.get('up_width', '60')     # Headline width (chars)
      imgur_switch = self.request.get('up_imgur')    # Imgur mirror switching enabled?
      feed = self.request.get('r', 'all')            # Current requested feed

      if feed == 'all':
        url = 'http://www.reddit.com/.rss'
      else:
        url = 'http://www.reddit.com/r/%s.rss' % (feed)
      
      rss = urlfetch.fetch(url)
      parsed = feedparser.parse(rss.content)
      stories = []

      for entry in parsed.entries:     
        # Handle inconsistency when there are no comments
        try:
          comment_count = re.findall(r"\[(\d*) comment[s]\]", entry.summary_detail.value)[0]
        except IndexError:
          comment_count = "0"
        
        # Extract the external link from RSS (WTF?)
        try:
          external_link = re.findall(r"href=\"(\S*)\">\[link\]", entry.summary_detail.value)[0]
        except IndexError:
          external_link = 'http://www.reddit.com/need_to_put_external_links_in_their_rss'

        # Use imgur_switch user prefs and switch domain to selected mirror
        imgur_mirror_id = int(imgur_switch)
        if imgur_mirror_id > 1:
          try:
            imgur_uri = re.findall(r"imgur\.com\/([A-Za-z0-9\.]+)", external_link)[0]
          except IndexError:
            imgur_uri = None
          
          if imgur_uri is not None:
            if imgur_mirror_id == 2:
              external_link = 'http://i.mirur.net/%s' % (imgur_uri)
            if imgur_mirror_id == 3:
              external_link = 'http://i.filmot.com/%s' % (imgur_uri)


        parsed_story_hash = {
          'full_title' : entry.title_detail.value, # Link alt text
          'fixed_width_title' : self.truncate(entry.title_detail.value, int(width)),
          'external_link' :  external_link,
          'comment_link' : entry.link,
          'comment_count' : comment_count
        }
        
        stories.append(parsed_story_hash)

      # Set template data for view
      template_data = {
        'subreddits' : subreddits.split('|'),
        'link_subreddits' : subreddits,
        'link_imgur' : imgur_switch,
        'width' : width,
        'current_feed' : str(feed),
        'stories' : stories
      }
      
      path = os.path.join(os.path.dirname(__file__), 'index.html')
      self.response.out.write(template.render(path, template_data))


  def truncate(self, value, arg):
    try:
        length = int(arg)
    except ValueError: # invalid literal for int()
      return value # Fail silently
    if not isinstance(value, basestring):
      value = str(value)
    if len(value) > (length):
      truncated = value[:length - 3]
      if not truncated.endswith('...'):
        truncated += '...'
      return truncated
    if len(value) <= length:
      padded = value
      spaces_needed = (length - len(value)) + 1
      for space_needed in range(1, spaces_needed):
          padded = "%s " % padded
      return padded
    return value

def main():
    application = webapp.WSGIApplication([('/', MainHandler)], debug=True)
    util.run_wsgi_app(application)

if __name__ == '__main__':
    main()
