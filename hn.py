#! /usr/bin/env python3

import argparse, requests, shelve, urllib.parse, bs4, time, textwrap, webbrowser

API_ENDPOINTS = {
    'item': '/item',
    'top': '/topstories',
    'new': '/newstories',
    'best': '/beststories',
    'ask': '/askstories',
    'show': '/showstories',
    'jobs': '/jobstories'
}

SECONDS_IN_MIN = 60
SECONDS_IN_HOUR = 60 * 60
SECONDS_IN_DAY = 60 * 60 * 24

comment_count = 0

def time_since(timestamp):
    time_diff = time.time() - timestamp

    if time_diff >= SECONDS_IN_DAY:
        return str(round(time_diff / SECONDS_IN_DAY)) + ' days ago'
    if time_diff >= SECONDS_IN_HOUR:
        return str(round(time_diff / SECONDS_IN_HOUR)) + ' hours ago'
    return str(round(time_diff / SECONDS_IN_MIN)) + ' mins ago'

def get_endpoint_url(endpoint):
    return 'https://hacker-news.firebaseio.com/v0' + endpoint + '.json'

def get_item_url(item_id):
    return get_endpoint_url(API_ENDPOINTS['item'] + '/' + str(item_id))

def display_list(args):
    with shelve.open('hn') as shelf:
        story_ids = requests.get(get_endpoint_url(API_ENDPOINTS[args.category])).json()
        shelf['story_ids'] = story_ids

    for i in range(0, args.limit):
        story = requests.get(get_item_url(story_ids[i])).json()
        story_title = str(i + 1).rjust(2) + '. ' + textwrap.shorten(story['title'], 50, placeholder='...')
        if 'url' in story:
            domain_name = urllib.parse.urlparse(story['url']).hostname.lstrip('www.')
            story_title += ' (' + domain_name + ')'
        print(story_title)   

def display_story(args):
    with shelve.open('hn') as shelf:
        story_id = shelf['story_ids'][args.rank - 1]
    story = requests.get(get_item_url(story_id)).json()
    if args.open and 'url' in story:
        webbrowser.open(story['url'])
    story_title = story['title']
    if 'url' in story:
        domain_name = urllib.parse.urlparse(story['url']).hostname.lstrip('www.')
        story_title += ' (' + domain_name + ')'
    story_title += '\n' + str(story['score']) + ' pts by ' + story['by'] + ' ' + time_since(story['time'])
    if 'kids' in story:
        story_title += ' | ' + str(story['descendants']) + ' comments'
    print()
    print(story_title)
    print('-' * 70)

    if args.limit:
        print_comments(story, level=0, max_comments=args.limit)
    elif 'descendants' in story:
        print_comments(story, level=0, max_comments=story['descendants'])


def print_comments(parent_item, level, max_comments):
    for comment_id in parent_item.get('kids', []):
        child_item = requests.get(get_item_url(comment_id)).json()
        global comment_count
        if comment_count < max_comments:
            if 'text' in child_item and 'by' in child_item:
                comment_soup = bs4.BeautifulSoup(child_item['text'], 'html.parser')
                print('   ' * level + child_item['by'] + ' ' + time_since(child_item['time']))
                print(textwrap.indent(textwrap.fill(comment_soup.text), '   ' * level), end='\n\n')
                comment_count += 1
            print_comments(child_item, level=level + 1, max_comments=max_comments)

parser = argparse.ArgumentParser()
subparsers = parser.add_subparsers()

parser_list = subparsers.add_parser('list', help='Display posts by category')
parser_list.add_argument('category', choices=['top', 'best', 'new', 'ask', 'show', 'jobs'], nargs='?', type=str, default='top', help='Pick a category')
parser_list.add_argument('limit', nargs='?', type=int, default=10, help='Limit number of posts')
parser_list.set_defaults(func=display_list)

parser_view = subparsers.add_parser('view', help='View a specific post')
parser_view.add_argument('rank', type=int, help='Rank of post on most recent list')
parser_view.add_argument('limit', type=int, nargs='?', default=None, help='Limit number of comments')
parser_view.add_argument('-o', '--open', action='store_true', help='Open link in browser')
parser_view.set_defaults(func=display_story)


args = parser.parse_args()
args.func(args)


