from sopel.config.types import StaticSection, ChoiceAttribute, ValidatedAttribute
from sopel.module import commands, example
from sopel import web
import sopel.module

import requests
from bs4 import BeautifulSoup
import csv
import time
from functools import reduce

from .irc import *

def cache(fun):
  data = {"data": 0, "timestamp": 0}
  def new_fun():
      if time.time() - data['timestamp'] > 60 * 10:
          data['data'] = fun()
          data['timestamp'] = time.time()
      return data['data']
  return new_fun

def get_data(url):
  data = requests.get(url).text
  soup = BeautifulSoup(data, features="html.parser")
  try:
    table = [x for x in soup.find_all('table') if x.get_attribute_list('id')[0][-6:] == "_today"][0]
  except IndexError:
    return {"data": {}, "additional": {}}
  html_rows = table.find_all('tr')
  headers = [x.get_text(' ').replace('\xa0', ' ').replace('/ ', '/') for x in html_rows[0].find_all('th')]
  rows = [[y.get_text() for y in x.find_all('td')] for x in html_rows[1:]]
  additional = [(z[0].lower(), z[1].get_attribute_list('href')[0]) for z in [(y.get_text(), y.find('a')) for y in [x.find('td') for x in html_rows[1:]]] if z[1]]
  
  def str_conv(data, header):
      data = data.strip().replace(',', '')
      if not data:
          return 0
      elif header.find('pop') != -1:
          return float(data)
      else:
          try:
            return int(data)
          except:
            return data
  
  dict_data = dict([(x[0], dict(zip(headers[1:], x[1:]))) for x in rows])
  dict_data = {k1.lower().strip(): {"data": {k2.strip(): str_conv(v2, k2) for k2, v2 in v1.items()}} for k1,v1 in dict_data.items()}
  return dict_data, dict(additional)

start_url = 'https://www.worldometers.info/coronavirus/'

@cache
def get_world():
  data, additional = get_data(start_url)
  world_data = {"data": data, "additional": additional}
  return world_data

def lookup(value):
    values = [x.strip() for x in value.lower().split(',')]
    def lookup_recurse(lookup_data, values):
        if values[0] not in lookup_data['data']:
            return None
        d = lookup_data['data'][values[0]]
        if len(values) == 1:
            return d['data']
        else:
            if not 'subdata' in d:
                if values[0] in lookup_data['additional']:
                  new_data, new_add = get_data(start_url + lookup_data['additional'][values[0]])
                  d['subdata'] = {'data': new_data, 'additional': new_add}
                else:
                  d['subdata'] = {}
            return lookup_recurse(d['subdata'], values[1:])
    return lookup_recurse(get_world(), values)


@sopel.module.commands('worldmeters')
@sopel.module.example('.worldmeters corona USA')
@sopel.module.example('.worldmeters corona USA, New York')
def worldmeters_corona(bot, trigger):
    where = trigger.group(2)
    if where[0:7] != 'corona ':
        msg = "Bad command"
    else:
        where = where[7:]
        data = lookup(where)
        if data is None:
            msg = "Bad place"
        else:
            data = {k: v for k, v in data.items() if k.lower() != "source"}
            msg = f"{where} {' '.join('{}{}{}: {}'.format(BOLD, key, BOLD, val) for key, val in data.items())}"
    bot.say(msg)
