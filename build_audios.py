#!/usr/bin/env python3
"""
Fetches audio data from Google Sheets and generates audios.json
Run manually or via GitHub Actions
"""

import csv
import json
import re
import urllib.request
from datetime import datetime
from collections import Counter

# ============================================
# CONFIGURE THESE URLs FROM YOUR GOOGLE SHEET
# ============================================
REDDIT_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTGQ_95RZSlRZtRysMG6Nh1vB5pG93R-mbU6WaoMF2Ci0aB8EMjrWrLsx1mDmGesj1gSLBs2TjSfQPk/pubhtml"
PATREON_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTj5CXHi3my2A5n1THsopOz4jh9x3rLJu3mLaEtHGjR8_9cFOG2NzYEuvwPBEJmwKZsZi9XPepwiaXr/pubhtml"
# ============================================

def fetch_csv(url):
    """Fetch CSV from Google Sheets published URL"""
    with urllib.request.urlopen(url) as response:
        content = response.read().decode('utf-8')
        reader = csv.DictReader(content.splitlines())
        return list(reader)

def clean(val):
    """Clean cell value"""
    if not val or str(val).strip().lower() in ['x', 'nan', '']:
        return ''
    return str(val).strip()

def parse_date(date_val):
    """Parse various date formats to YYYY-MM-DD"""
    if not date_val or not str(date_val).strip():
        return ''
    
    date_str = str(date_val).strip()
    
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d/%m/%y',
        '%m/%d/%Y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.split()[0], fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    
    return date_str[:10] if len(date_str) >= 10 else date_str

def normalize_tag_key(tag):
    """Normalize tag for comparison"""
    return re.sub(r'[\s\-]', '', tag.lower().strip())

def normalize_tags(tag_string):
    """Normalize all tags in a tag string"""
    if not tag_string:
        return ''
    
    # Canonical tag mappings
    canonical = {
        'deepthroat': 'Deepthroat', 'blowjob': 'Blowjob', 'creampie': 'Creampie',
        'facefuck': 'Facefuck', 'facefucking': 'Facefucking', 'handjob': 'Handjob',
        'doggystyle': 'Doggystyle', 'cowgirl': 'Cowgirl', 'cunnilingus': 'Cunnilingus',
        'throatpie': 'Throatpie', 'fdom': 'Fdom', 'fsub': 'Fsub', 'fswitch': 'Fswitch',
        'milf': 'MILF', 'bigtits': 'Big Tits', 'goodboy': 'Good Boy',
        'cockworship': 'Cock Worship', 'ballsucking': 'Ball Sucking',
        'facesitting': 'Facesitting', 'selfdegradation': 'Self-Degradation',
        'roughsex': 'Rough Sex', 'dirtytalk': 'Dirty Talk', 'holdthemoan': 'Hold the Moan',
        'gentlefdom': 'Gentle Fdom', 'mommydomme': 'Mommy Domme', 'lbombs': 'L-Bombs',
        'friendstolovers': 'Friends to Lovers', 'enemiestolovers': 'Enemies to Lovers',
        'strangerstolovers': 'Strangers to Lovers', 'multipleorgasms': 'Multiple Orgasms',
        'mutualorgasm': 'Mutual Orgasm', 'speakerorgasm': 'Speaker Orgasm',
        'listenerorgasm': 'Listener Orgasm', 'virginlistener': 'Virgin Listener',
        'sizedifference': 'Size Difference', 'freeuse': 'Free Use', 'dubcon': 'Dubcon',
        'olderwomanyoungerman': 'Older Woman/Younger Man', 'aggressivefsub': 'Aggressive Fsub',
        'sluttyfsub': 'Slutty Fsub', 'meanfdom': 'Mean Fdom',
    }
    
    tags = re.findall(r'\[([^\]]+)\]', tag_string)
    normalized = []
    seen = set()
    
    for tag in tags:
        tag = tag.strip()
        norm = normalize_tag_key(tag)
        
        if norm in seen:
            continue
        seen.add(norm)
        
        final_tag = canonical.get(norm, tag)
        normalized.append(f'[{final_tag}]')
    
    return ''.join(normalized)

def normalize_author(author):
    """Normalize script author names"""
    if not author:
        return 'OC (Original Content)'
    
    author = author.strip()
    
    # Author corrections
    replacements = {
        'u/Isapeth': 'u/The-Scriptweaver',
        'u/the-scriptwaever': 'u/The-Scriptweaver',
        '/SpaceCowboy_1999': 'u/SpaceCowboy_1999',
        'SpaceCowboy_1999': 'u/SpaceCowboy_1999',
        'u/SpaceCowboy_2000': 'u/SpaceCowboy_1999',
        '/ArthurWynne': 'u/ArthurWynne',
        'u/IceDrake402': 'u/Icedrake402',
        'u/Patron_of_Ravens': 'u/PatronofRavens',
        'u/TheShyTributeGuy.': 'u/TheShyTributeGuy',
        'u/StankyTofu': 'u/StankyTofu25',
    }
    
    return replacements.get(author, author) if author else 'OC (Original Content)'

def extract_audio(row, source):
    """Extract audio data from a row"""
    link = clean(row.get('link', ''))
    
    audio = {
        'title': clean(row.get('title', '')),
        'category': clean(row.get('category', '')).lower().replace(' ', '-'),
        'tags': normalize_tags(clean(row.get('tags', ''))),
        'synopsis': clean(row.get('synopsis', '')),
        'duration': clean(row.get('duration', '')),
        'image': clean(row.get('image', '')),
        'redditLink': link if 'reddit.com' in link.lower() else '',
        'patreonLink': link if 'patreon.com' in link.lower() else '',
        'scriptAuthor': normalize_author(clean(row.get('script author', ''))),
        'scriptAuthorPage': clean(row.get('script author page', '')),
        'scriptLink': clean(row.get('script link', '')),
        'audioEditor': clean(row.get('audio editor ', '') or row.get('audio editor', '')),
        'audioEditorPage': clean(row.get('audio editor page', '')),
        'datePosted': parse_date(row.get('Date Posted', '')),
        'collabPartners': [],
        '_source': source
    }
    
    # Add collab partners
    for i in range(1, 5):
        name = clean(row.get(f'collab partner name {i}', ''))
        link = clean(row.get(f'collab partner link {i}', ''))
        if name:
            audio['collabPartners'].append({'name': name, 'link': link})
    
    return audio

def normalize_title(title):
    """Normalize title for matching"""
    if not title:
        return ""
    title = str(title).lower()
    title = re.sub(r'[^\w\s]', '', title)
    title = re.sub(r'\s+', ' ', title).strip()
    return title

def fix_future_dates(audios):
    """Fix any dates that are in the future (likely typos)"""
    today = datetime.now()
    
    for audio in audios:
        if audio['datePosted']:
            try:
                date = datetime.strptime(audio['datePosted'], '%Y-%m-%d')
                if date > today:
                    # Assume year typo - subtract 1 year
                    audio['datePosted'] = date.replace(year=date.year - 1).strftime('%Y-%m-%d')
            except:
                pass
    
    return audios

def main():
    print("Fetching Reddit sheet...")
    reddit_data = fetch_csv(REDDIT_SHEET_URL)
    print(f"  Found {len(reddit_data)} rows")
    
    print("Fetching Patreon sheet...")
    patreon_data = fetch_csv(PATREON_SHEET_URL)
    print(f"  Found {len(patreon_data)} rows")
    
    # Build merged audio list
    audios = {}
    
    # Add Patreon audios first (primary source)
    for row in patreon_data:
        audio = extract_audio(row, 'patreon')
        norm_title = normalize_title(audio['title'])
        if norm_title and norm_title not in audios:
            audios[norm_title] = audio
    
    # Merge Reddit audios
    for row in reddit_data:
        audio = extract_audio(row, 'reddit')
        norm_title = normalize_title(audio['title'])
        
        if not norm_title:
            continue
        
        if norm_title in audios:
            # Merge - add Reddit link to existing entry
            audios[norm_title]['redditLink'] = audio['redditLink']
            if not audios[norm_title]['scriptLink'] and audio['scriptLink']:
                audios[norm_title]['scriptLink'] = audio['scriptLink']
        else:
            audios[norm_title] = audio
    
    # Convert to list and clean up
    audio_list = list(audios.values())
    
    # Fix future dates
    audio_list = fix_future_dates(audio_list)
    
    # Sort by date (newest first)
    audio_list.sort(key=lambda x: x['datePosted'] if x['datePosted'] else '0000-00-00', reverse=True)
    
    # Assign IDs and remove temp fields
    for i, audio in enumerate(audio_list):
        audio['id'] = i + 1
        del audio['_source']
    
    # Save
    with open('audios.json', 'w', encoding='utf-8') as f:
        json.dump(audio_list, f, indent=2, ensure_ascii=False)
    
    # Stats
    categories = Counter(a['category'] for a in audio_list)
    both = sum(1 for a in audio_list if a['redditLink'] and a['patreonLink'])
    reddit_only = sum(1 for a in audio_list if a['redditLink'] and not a['patreonLink'])
    patreon_only = sum(1 for a in audio_list if a['patreonLink'] and not a['redditLink'])
    
    print(f"\nGenerated audios.json with {len(audio_list)} audios")
    print(f"  Both platforms: {both}")
    print(f"  Reddit only: {reddit_only}")
    print(f"  Patreon only: {patreon_only}")
    print(f"  Categories: {dict(categories)}")

if __name__ == '__main__':
    main()
