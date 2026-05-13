#!/usr/bin/env python3
"""Advanced pattern and anomaly analysis for MKX matches."""
import json
from collections import Counter, defaultdict

print("Loading parsed matches...")
with open('/projects/sandbox/Test/data/parsed_matches.json', 'r') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")

# ============================================================
# SECTION 5: REPEAT/REVERSE/MIX ALGORITHM ANALYSIS
# ============================================================
print("\n" + "="*70)
print("SECTION 5: REPEAT/REVERSE/MIX PATTERNS (Cybernagual Algorithms)")
print("="*70)

def get_winner_sequence(m):
    """Get round winner sequence as string like 'P1P2P1P1P2'"""
    if 'rounds' not in m:
        return ''
    return ''.join(r['winner'] for r in m['rounds'])

def get_finish_sequence(m):
    if 'rounds' not in m:
        return ''
    return ''.join(r['finish'] for r in m['rounds'])

def similarity(seq1, seq2):
    """Calculate similarity between two sequences (same length)."""
    min_len = min(len(seq1), len(seq2))
    if min_len == 0:
        return 0
    matches_count = sum(1 for a, b in zip(seq1[:min_len], seq2[:min_len]) if a == b)
    return matches_count / min_len

def is_reverse(seq1, seq2):
    """Check if seq2 is reverse of seq1 (P1<->P2)."""
    min_len = min(len(seq1), len(seq2))
    if min_len == 0:
        return 0
    reverse_map = {'P1': 'P2', 'P2': 'P1'}
    # Split into P1/P2 tokens
    tokens1 = [seq1[i:i+2] for i in range(0, len(seq1), 2)]
    tokens2 = [seq2[i:i+2] for i in range(0, len(seq2), 2)]
    min_t = min(len(tokens1), len(tokens2))
    if min_t == 0:
        return 0
    rev_count = sum(1 for a, b in zip(tokens1[:min_t], tokens2[:min_t]) if reverse_map.get(a) == b)
    return rev_count / min_t

# Analyze consecutive matches (same lobby for better comparison)
print("\nAnalyzing consecutive match algorithms...")
repeat_count = 0
reverse_count = 0
mix_count = 0
total_pairs = 0

for i in range(1, len(matches)):
    prev = matches[i-1]
    curr = matches[i]
    
    # Only compare if same lobby or consecutive match numbers
    if prev.get('lobby') != curr.get('lobby'):
        continue
    
    seq_prev = get_winner_sequence(prev)
    seq_curr = get_winner_sequence(curr)
    
    if len(seq_prev) < 10 or len(seq_curr) < 10:  # at least 5 rounds (P1=2chars each)
        continue
    
    total_pairs += 1
    sim = similarity(seq_prev, seq_curr)
    rev = is_reverse(seq_prev, seq_curr)
    
    if sim >= 0.8:
        repeat_count += 1
    elif rev >= 0.8:
        reverse_count += 1
    else:
        mix_count += 1

print(f"Consecutive same-lobby pairs analyzed: {total_pairs}")
print(f"  Pure Repeat (>=80% same): {repeat_count} ({repeat_count/total_pairs*100:.2f}%)")
print(f"  Pure Reverse (>=80% opposite): {reverse_count} ({reverse_count/total_pairs*100:.2f}%)")
print(f"  Mix/Other: {mix_count} ({mix_count/total_pairs*100:.2f}%)")

# More granular breakdown
print("\nGranular similarity distribution (consecutive same-lobby):")
sim_bins = defaultdict(int)
for i in range(1, min(50000, len(matches))):
    prev = matches[i-1]
    curr = matches[i]
    if prev.get('lobby') != curr.get('lobby'):
        continue
    seq_prev = get_winner_sequence(prev)
    seq_curr = get_winner_sequence(curr)
    if len(seq_prev) < 10 or len(seq_curr) < 10:
        continue
    sim = similarity(seq_prev, seq_curr)
    bucket = int(sim * 10) / 10
    sim_bins[bucket] += 1

for b in sorted(sim_bins.keys()):
    total_b = sum(sim_bins.values())
    print(f"  Similarity {b:.1f}-{b+0.1:.1f}: {sim_bins[b]} ({sim_bins[b]/total_b*100:.1f}%)")

# ============================================================
# SECTION 6: STREAK ANALYSIS (Vertical Waves)
# ============================================================
print("\n" + "="*70)
print("SECTION 6: STREAK ANALYSIS (Vertical Waves)")
print("="*70)

# Analyze favorite streaks in specific rounds across consecutive matches
print("\nFavorite streak analysis in Round 1 (consecutive matches in same lobby):")
lobby_matches = defaultdict(list)
for m in matches:
    if 'lobby' in m and 'rounds' in m and 'p1_round_coeff' in m:
        lobby_matches[m['lobby']].append(m)

streak_lengths = []
for lobby, lm in lobby_matches.items():
    current_streak = 0
    for m in lm:
        rd1 = m['rounds'][0]
        is_fav_win = (m['p1_round_coeff'] < m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
                     (m['p2_round_coeff'] < m['p1_round_coeff'] and rd1['winner'] == 'P2')
        if is_fav_win:
            current_streak += 1
        else:
            if current_streak > 0:
                streak_lengths.append(current_streak)
            current_streak = 0
    if current_streak > 0:
        streak_lengths.append(current_streak)

streak_counter = Counter(streak_lengths)
print(f"  Total streak observations: {len(streak_lengths)}")
print("  Streak length distribution:")
for length in sorted(streak_counter.keys())[:15]:
    pct = streak_counter[length] / len(streak_lengths) * 100
    print(f"    Streak {length}: {streak_counter[length]} ({pct:.1f}%)")

# Underdog streaks
print("\nUnderdog streak in Round 1:")
und_streak_lengths = []
for lobby, lm in lobby_matches.items():
    current_streak = 0
    for m in lm:
        rd1 = m['rounds'][0]
        is_und_win = (m['p1_round_coeff'] > m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
                     (m['p2_round_coeff'] > m['p1_round_coeff'] and rd1['winner'] == 'P2')
        if is_und_win:
            current_streak += 1
        else:
            if current_streak > 0:
                und_streak_lengths.append(current_streak)
            current_streak = 0
    if current_streak > 0:
        und_streak_lengths.append(current_streak)

und_streak_counter = Counter(und_streak_lengths)
print(f"  Total streak observations: {len(und_streak_lengths)}")
for length in sorted(und_streak_counter.keys())[:15]:
    pct = und_streak_counter[length] / len(und_streak_lengths) * 100
    print(f"    Streak {length}: {und_streak_counter[length]} ({pct:.1f}%)")

# ============================================================
# SECTION 7: CHARACTER PAIR ANALYSIS
# ============================================================
print("\n" + "="*70)
print("SECTION 7: CHARACTER PAIR ANALYSIS")
print("="*70)

pair_stats = defaultdict(lambda: {'total': 0, 'p1_wins': 0, 'fat_count': 0, 'brut_count': 0, 'total_5m': 0})
char_left_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'fat': 0})
char_right_stats = defaultdict(lambda: {'total': 0, 'wins': 0, 'fat': 0})

for m in matches:
    if 'char_left' not in m or 'char_right' not in m or 'rounds' not in m:
        continue
    pair = f"{m['char_left']}-{m['char_right']}"
    ps = pair_stats[pair]
    ps['total'] += 1
    
    p1_round_wins = sum(1 for r in m['rounds'] if r['winner'] == 'P1')
    p2_round_wins = sum(1 for r in m['rounds'] if r['winner'] == 'P2')
    if p1_round_wins > p2_round_wins:
        ps['p1_wins'] += 1
    
    fat_in_match = sum(1 for r in m['rounds'] if r['finish'] == 'F')
    brut_in_match = sum(1 for r in m['rounds'] if r['finish'] == 'B')
    ps['fat_count'] += fat_in_match
    ps['brut_count'] += brut_in_match
    
    total_r = m.get('total_rounds', 0)
    if total_r == 5:
        ps['total_5m'] += 1
    
    # Individual char stats
    cl = char_left_stats[m['char_left']]
    cl['total'] += 1
    if p1_round_wins > p2_round_wins:
        cl['wins'] += 1
    cl['fat'] += fat_in_match
    
    cr = char_right_stats[m['char_right']]
    cr['total'] += 1
    if p2_round_wins > p1_round_wins:
        cr['wins'] += 1
    cr['fat'] += fat_in_match

# Most "fatality-prone" characters
print("\nMost Fatality-prone characters (left, min 500 matches):")
fat_chars = [(c, s['fat']/s['total']) for c, s in char_left_stats.items() if s['total'] >= 500]
fat_chars.sort(key=lambda x: x[1], reverse=True)
for c, rate in fat_chars[:15]:
    n = char_left_stats[c]['total']
    print(f"  {c}: {rate:.3f} fat/match (n={n})")

print("\nLeast Fatality-prone characters (left, min 500 matches):")
for c, rate in fat_chars[-10:]:
    n = char_left_stats[c]['total']
    print(f"  {c}: {rate:.3f} fat/match (n={n})")

# Best pairs for Total 5.5M
print("\nPairs with highest Total 5.5M rate (min 200 matches):")
total5m_pairs = [(p, s['total_5m']/s['total']) for p, s in pair_stats.items() if s['total'] >= 200]
total5m_pairs.sort(key=lambda x: x[1], reverse=True)
for p, rate in total5m_pairs[:15]:
    n = pair_stats[p]['total']
    print(f"  {p}: {rate*100:.2f}% (n={n})")

# ============================================================
# SECTION 8: TIME-BASED ANOMALIES (Average Round Time)
# ============================================================
print("\n" + "="*70)
print("SECTION 8: TIME PATTERNS IN ROUNDS")
print("="*70)

# Average round time distribution
round_times = []
for m in matches:
    if 'rounds' in m:
        for r in m['rounds']:
            round_times.append(r['time'])

avg_time = sum(round_times) / len(round_times)
print(f"\nOverall average round time: {avg_time:.2f} seconds")
print(f"Total round observations: {len(round_times)}")

# Time distribution
time_bins = Counter()
for t in round_times:
    bucket = (t // 5) * 5
    time_bins[bucket] += 1

print("\nRound time distribution (5-sec buckets):")
for b in sorted(time_bins.keys()):
    if time_bins[b] > 1000:
        pct = time_bins[b] / len(round_times) * 100
        print(f"  {b}-{b+4}s: {time_bins[b]} ({pct:.1f}%)")

# Correlation: round time and next round outcome
print("\nDoes round 1 time predict round 2 winner?")
r1_time_to_r2 = defaultdict(lambda: {'total': 0, 'fav_win': 0})
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 2 and 'p1_round_coeff' in m:
        r1_time = m['rounds'][0]['time']
        bucket = 'short' if r1_time <= 20 else ('medium' if r1_time <= 35 else 'long')
        r2_winner = m['rounds'][1]['winner']
        s = r1_time_to_r2[bucket]
        s['total'] += 1
        if m['p1_round_coeff'] < m['p2_round_coeff']:
            if r2_winner == 'P1':
                s['fav_win'] += 1
        else:
            if r2_winner == 'P2':
                s['fav_win'] += 1

for bucket in ['short', 'medium', 'long']:
    s = r1_time_to_r2[bucket]
    if s['total'] > 0:
        print(f"  R1 time={bucket}: Fav wins R2 in {s['fav_win']/s['total']*100:.2f}% (n={s['total']})")

# ============================================================
# SECTION 9: AFTER-PATTERN ANALYSIS (Key Finding!)
# ============================================================
print("\n" + "="*70)
print("SECTION 9: AFTER-STREAK PATTERNS (Key Strategy Indicator)")
print("="*70)

# After N consecutive favorite wins in round X, what happens next?
print("\nAfter N consecutive FAVORITE wins in R1, what's the probability of next R1 also being favorite?")
for streak_target in [2, 3, 4, 5, 6, 7, 8]:
    next_fav = 0
    next_und = 0
    for lobby, lm in lobby_matches.items():
        streak = 0
        for i, m in enumerate(lm):
            rd1 = m['rounds'][0]
            is_fav = (m['p1_round_coeff'] < m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
                     (m['p2_round_coeff'] < m['p1_round_coeff'] and rd1['winner'] == 'P2')
            if is_fav:
                streak += 1
            else:
                if streak == streak_target and i < len(lm):
                    next_und += 1
                elif streak > streak_target:
                    pass  # counted at streak_target already
                streak = 0
            
            if streak == streak_target + 1:
                next_fav += 1
                streak = streak_target  # keep counting
    
    total_after = next_fav + next_und
    if total_after > 0:
        print(f"  After {streak_target} fav wins: next is also fav={next_fav/total_after*100:.2f}% (n={total_after})")

# After N consecutive UNDERDOG wins
print("\nAfter N consecutive UNDERDOG wins in R1, what's the probability of next R1 also being underdog?")
for streak_target in [2, 3, 4, 5, 6]:
    next_und_cont = 0
    next_fav_break = 0
    for lobby, lm in lobby_matches.items():
        streak = 0
        for i, m in enumerate(lm):
            rd1 = m['rounds'][0]
            is_und = (m['p1_round_coeff'] > m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
                     (m['p2_round_coeff'] > m['p1_round_coeff'] and rd1['winner'] == 'P2')
            if is_und:
                streak += 1
            else:
                if streak == streak_target:
                    next_fav_break += 1
                streak = 0
            
            if streak == streak_target + 1:
                next_und_cont += 1
                streak = streak_target
    
    total_after = next_und_cont + next_fav_break
    if total_after > 0:
        print(f"  After {streak_target} und wins: next is also und={next_und_cont/total_after*100:.2f}% (n={total_after})")

# ============================================================
# SECTION 10: FATALITY PATTERNS AFTER SPECIFIC SEQUENCES
# ============================================================
print("\n" + "="*70)
print("SECTION 10: FATALITY PREDICTION PATTERNS")
print("="*70)

# After Fatality in R1, what's prob of Fatality in R2?
print("\nFatality conditional probabilities:")
for r_from in range(1, 6):
    for r_to in [r_from + 1]:
        fat_then_fat = 0
        fat_then_not = 0
        nofat_then_fat = 0
        nofat_then_not = 0
        for m in matches:
            if 'rounds' in m and len(m['rounds']) >= r_to:
                r1_fat = m['rounds'][r_from-1]['finish'] == 'F'
                r2_fat = m['rounds'][r_to-1]['finish'] == 'F'
                if r1_fat and r2_fat:
                    fat_then_fat += 1
                elif r1_fat and not r2_fat:
                    fat_then_not += 1
                elif not r1_fat and r2_fat:
                    nofat_then_fat += 1
                else:
                    nofat_then_not += 1
        
        total_after_fat = fat_then_fat + fat_then_not
        total_after_nofat = nofat_then_fat + nofat_then_not
        if total_after_fat > 0 and total_after_nofat > 0:
            print(f"  R{r_from}->R{r_to}: P(Fat|prev_Fat)={fat_then_fat/total_after_fat*100:.2f}% vs P(Fat|prev_NoFat)={nofat_then_fat/total_after_nofat*100:.2f}%")

# Fatality in match after Fatality coeff ranges  
print("\nFatality hit rate by decimal portion of coefficient (Cybernagual's base pattern):")
for whole in [2, 3, 4, 5]:
    for dec_range in [(0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0)]:
        low = whole + dec_range[0]
        high = whole + dec_range[1]
        hits = 0
        total = 0
        for m in matches:
            if 'fat_coeff' in m and 'rounds' in m:
                if low <= m['fat_coeff'] < high:
                    total += 1
                    if any(r['finish'] == 'F' for r in m['rounds']):
                        hits += 1
        if total > 100:
            print(f"  Fat coeff [{low:.2f}-{high:.2f}): {hits/total*100:.2f}% (n={total})")

# Cross-boundary analysis (end of one range vs start of next)
print("\nCROSS-BOUNDARY ANOMALY (Cybernagual Base Pattern):")
boundaries = [(2.8, 3.0, 3.0, 3.2), (3.8, 4.0, 4.0, 4.2), (4.8, 5.0, 5.0, 5.2)]
for low1, high1, low2, high2 in boundaries:
    hits1 = total1 = hits2 = total2 = 0
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m:
            if low1 <= m['fat_coeff'] < high1:
                total1 += 1
                if any(r['finish'] == 'F' for r in m['rounds']):
                    hits1 += 1
            elif low2 <= m['fat_coeff'] < high2:
                total2 += 1
                if any(r['finish'] == 'F' for r in m['rounds']):
                    hits2 += 1
    if total1 > 0 and total2 > 0:
        print(f"  [{low1}-{high1}): {hits1/total1*100:.2f}% (n={total1}) vs [{low2}-{high2}): {hits2/total2*100:.2f}% (n={total2}) | EDGE={hits2/total2*100 - hits1/total1*100:.2f}pp")

print("\nAnalysis complete!")
