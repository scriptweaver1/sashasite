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
REDDIT_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTyRAJt0veFVXHIuaes_Fq9-KBNA006b0kgdPneyW-gyIGqB_y1m6ub0DMSoI38NyM9MCn74oGP-Xzv/pub?output=csv"
PATREON_SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vTb1Ch0Y8kXTN_zoH_3yaQDTiA2eIzh7tEfxO9Ao3d7qdK6kc_-IFDZcjbtgRsbPSQgIohJkmWs_3ig/pub?output=csv"
# ============================================

def fetch_csv(url):
    """Fetch CSV from Google Sheets published URL"""
    print(f"Fetching: {url[:60]}...")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode('utf-8')
            reader = csv.DictReader(content.splitlines())
            rows = list(reader)
            print(f"  Found {len(rows)} rows")
            if rows:
                print(f"  Columns: {list(rows[0].keys())}")
            return rows
    except Exception as e:
        print(f"  ERROR fetching: {e}")
        return []

def clean(val):
    """Clean cell value - treat 'x', 'X', empty, 'nan' as empty"""
    if val is None:
        return ''
    val = str(val).strip()
    if val.lower() in ['x', 'nan', '', 'none']:
        return ''
    return val

def parse_date(date_val):
    """Parse various date formats to YYYY-MM-DD"""
    if not date_val:
        return ''
    
    date_str = clean(date_val)
    if not date_str:
        return ''
    
    # Try different formats
    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d',
        '%d/%m/%Y',
        '%d/%m/%y',
        '%m/%d/%Y',
        '%m/%d/%y',
    ]
    
    for fmt in formats:
        try:
            dt = datetime.strptime(date_str.split()[0], fmt)
            return dt.strftime('%Y-%m-%d')
        except:
            continue
    
    # Return first 10 chars if nothing worked
    return date_str[:10] if len(date_str) >= 10 else date_str

def normalize_tag_key(tag):
    """Normalize tag for comparison"""
    return re.sub(r'[\s\-/]', '', tag.lower().strip())

def normalize_tags(tag_string):
    """Normalize all tags in a tag string"""
    if not tag_string:
        return ''
    
    tag_string = clean(tag_string)
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
    author = clean(author)
    if not author:
        return 'OC (Original Content)'
    
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
    
    return replacements.get(author, author)

def get_column(row, *possible_names):
    """Get value from row trying multiple possible column names"""
    for name in possible_names:
        if name in row:
            return row[name]
        # Try with/without trailing space
        if name.strip() in row:
            return row[name.strip()]
        if name + ' ' in row:
            return row[name + ' ']
    return ''

def extract_audio(row, source):
    """Extract audio data from a row"""
    link = clean(get_column(row, 'link'))
    
    # Determine platform from link
    is_reddit = 'reddit.com' in link.lower() if link else False
    is_patreon = 'patreon.com' in link.lower() if link else False
    
    audio = {
        'title': clean(get_column(row, 'title')),
        'category': clean(get_column(row, 'category')).lower().replace(' ', '-'),
        'tags': normalize_tags(get_column(row, 'tags')),
        'synopsis': clean(get_column(row, 'synopsis')),
        'duration': clean(get_column(row, 'duration')),
        'image': clean(get_column(row, 'image')),
        'redditLink': link if is_reddit else '',
        'patreonLink': link if is_patreon else '',
        'scriptAuthor': normalize_author(get_column(row, 'script author')),
        'scriptAuthorPage': clean(get_column(row, 'script author page')),
        'scriptLink': clean(get_column(row, 'script link')),
        'audioEditor': clean(get_column(row, 'audio editor', 'audio editor ')),
        'audioEditorPage': clean(get_column(row, 'audio editor page')),
        'datePosted': parse_date(get_column(row, 'Date Posted', 'date posted', 'Date posted')),
        'collabPartners': [],
        '_source': source
    }
    
    # Add collab partners
    for i in range(1, 5):
        name = clean(get_column(row, f'collab partner name {i}'))
        link = clean(get_column(row, f'collab partner link {i}'))
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
    print("=" * 50)
    print("Building audios.json from Google Sheets")
    print("=" * 50)
    
    reddit_data = fetch_csv(REDDIT_SHEET_URL)
    patreon_data = fetch_csv(PATREON_SHEET_URL)
    
    if not reddit_data and not patreon_data:
        print("\nERROR: No data fetched from either sheet!")
        print("Check that sheets are published to web as CSV")
        return
    
    # Build merged audio list
    audios = {}
    
    # Add Patreon audios first (primary source)
    for row in patreon_data:
        audio = extract_audio(row, 'patreon')
        if not audio['title']:
            continue
        norm_title = normalize_title(audio['title'])
        if norm_title and norm_title not in audios:
            audios[norm_title] = audio
    
    print(f"\nAfter Patreon: {len(audios)} audios")
    
    # Merge Reddit audios
    for row in reddit_data:
        audio = extract_audio(row, 'reddit')
        if not audio['title']:
            continue
        norm_title = normalize_title(audio['title'])
        
        if not norm_title:
            continue
        
        if norm_title in audios:
            # Merge - add Reddit link to existing entry
            if audio['redditLink']:
                audios[norm_title]['redditLink'] = audio['redditLink']
            if not audios[norm_title]['scriptLink'] and audio['scriptLink']:
                audios[norm_title]['scriptLink'] = audio['scriptLink']
            if not audios[norm_title]['scriptAuthor'] or audios[norm_title]['scriptAuthor'] == 'OC (Original Content)':
                if audio['scriptAuthor'] and audio['scriptAuthor'] != 'OC (Original Content)':
                    audios[norm_title]['scriptAuthor'] = audio['scriptAuthor']
                    audios[norm_title]['scriptAuthorPage'] = audio['scriptAuthorPage']
        else:
            audios[norm_title] = audio
    
    print(f"After Reddit merge: {len(audios)} audios")
    
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
    
    print(f"\n{'=' * 50}")
    print(f"SUCCESS: Generated audios.json with {len(audio_list)} audios")
    print(f"{'=' * 50}")
    print(f"  Both platforms: {both}")
    print(f"  Reddit only: {reddit_only}")
    print(f"  Patreon only: {patreon_only}")
    print(f"  Categories: {dict(categories)}")

if __name__ == '__main__':
    main()
