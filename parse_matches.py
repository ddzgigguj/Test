#!/usr/bin/env python3
"""Parse MKX match data from Telegram channel export."""
import json
import re
import sys
from datetime import datetime

def parse_text(msg):
    """Extract text from message (handles mixed text/entities)."""
    text = msg.get('text', '')
    if isinstance(text, list):
        parts = []
        for t in text:
            if isinstance(t, str):
                parts.append(t)
            elif isinstance(t, dict):
                parts.append(t.get('text', ''))
        return ''.join(parts)
    return text

def parse_match(text):
    """Parse a single match message into structured data."""
    match = {}
    lines = text.strip().split('\n')
    if not lines:
        return None
    
    # Parse time and date from first line
    time_date = re.match(r'(\d{2}:\d{2})\s+(\d{2}-\d{2}-\d{4})', lines[0])
    if not time_date:
        return None
    match['time'] = time_date.group(1)
    match['date'] = time_date.group(2)
    
    # Parse match number and lobby
    n_match = re.search(r'#N(\d+)', lines[0])
    l_match = re.search(r'#L(\d+)', lines[0])
    if n_match:
        match['match_num'] = int(n_match.group(1))
    if l_match:
        match['lobby'] = int(l_match.group(1))
    
    # Parse characters (from hashtag line)
    char_line = None
    for line in lines[1:5]:
        chars = re.findall(r'#([А-Яа-яA-Za-z]+)', line)
        if len(chars) >= 2:
            # Filter out common non-character hashtags
            filtered = [c for c in chars if c not in ['N', 'L', 'T', 't']]
            if len(filtered) >= 2:
                match['char_left'] = filtered[0]
                match['char_right'] = filtered[1]
                break
    
    # Parse P1m|P2m coefficients (match winner odds)
    p1m_p2m = re.search(r'P1m\|P2m\s*-\s*([\d.]+)\|([\d.]+)', text)
    if p1m_p2m:
        match['p1m_coeff'] = float(p1m_p2m.group(1))
        match['p2m_coeff'] = float(p1m_p2m.group(2))
    
    # Parse P1/P2 round win coefficients
    p1p2 = re.search(r'P1/P2\s*-\s*([\d.]+)/([\d.]+)', text)
    if p1p2:
        match['p1_round_coeff'] = float(p1p2.group(1))
        match['p2_round_coeff'] = float(p1p2.group(2))
    
    # Parse FBR (Fatality, Brutality, R-no finish)
    fbr = re.search(r'FBR\s*-\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)', text)
    if fbr:
        match['fat_coeff'] = float(fbr.group(1))
        match['brut_coeff'] = float(fbr.group(2))
        match['no_finish_coeff'] = float(fbr.group(3))
    
    # Parse atv (average time)
    atv = re.search(r'atv\s*:\s*([\d.]+)', text)
    if atv:
        match['avg_time'] = float(atv.group(1))
    
    # Parse time corridor tag
    tc = re.search(r'#t(\d+)v(\d+)', text)
    if tc:
        match['time_corridor_t'] = int(tc.group(1))
        match['time_corridor_v'] = int(tc.group(2))
    
    # Parse TimeStat lines (over/under)
    time_stats = re.findall(r'([\d.]+)\s*\(([\d.]+)\s*-\s*([\d.]+)\)\s*#([msbMSB]\d+)', text)
    if time_stats:
        match['time_lines'] = []
        for ts in time_stats:
            match['time_lines'].append({
                'line': float(ts[0]),
                'over': float(ts[1]),
                'under': float(ts[2]),
                'tag': ts[3]
            })
    
    # Parse score
    score = re.search(r'\n(\d+):(\d+)\s*\n', text)
    if score:
        match['score_p1'] = int(score.group(1))
        match['score_p2'] = int(score.group(2))
        match['total_rounds'] = match['score_p1'] + match['score_p2']
    
    # Parse rounds
    rounds = re.findall(r'(\d+)\.\s*(P[12])\s*--\s*([FBR])\s*--\s*(\d+)\s*(T[MB]+)?', text)
    if rounds:
        match['rounds'] = []
        for r in rounds:
            rd = {
                'num': int(r[0]),
                'winner': r[1],
                'finish': r[2],  # F=Fatality, B=Brutality, R=Regular
                'time': int(r[3]),
            }
            if r[4]:
                rd['time_result'] = r[4]
            match['rounds'].append(rd)
    
    # Parse total rounds tag
    total_tag = re.search(r'#T(\d+)', text)
    if total_tag:
        match['total_tag'] = int(total_tag.group(1))
    
    return match

def main():
    print("Loading data...")
    with open('/projects/sandbox/Test/data/result (2).json', 'r') as f:
        data = json.load(f)
    
    msgs = data['messages']
    print(f"Total messages: {len(msgs)}")
    
    matches = []
    failed = 0
    for msg in msgs:
        text = parse_text(msg)
        if not text or len(text) < 50:
            continue
        # Skip non-match messages
        if '#N' not in text or 'P1' not in text:
            continue
        parsed = parse_match(text)
        if parsed and 'rounds' in parsed and len(parsed['rounds']) >= 5:
            matches.append(parsed)
        else:
            failed += 1
    
    print(f"Successfully parsed: {len(matches)} matches")
    print(f"Failed/skipped: {failed}")
    
    # Save parsed data
    with open('/projects/sandbox/Test/data/parsed_matches.json', 'w') as f:
        json.dump(matches, f, ensure_ascii=False)
    
    print("Saved to parsed_matches.json")
    
    # Quick stats
    if matches:
        print(f"\nDate range: {matches[0].get('date')} to {matches[-1].get('date')}")
        print(f"Sample match: {json.dumps(matches[0], indent=2, ensure_ascii=False)[:500]}")

if __name__ == '__main__':
    main()
