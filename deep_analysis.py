#!/usr/bin/env python3
"""Deep analysis of 221K MKX matches - patterns, anomalies, strategies."""
import json
import numpy as np
from collections import Counter, defaultdict
from datetime import datetime

print("Loading parsed matches...")
with open('/projects/sandbox/Test/data/parsed_matches.json', 'r') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")
print(f"Date range: {matches[0]['date']} - {matches[-1]['date']}")

# ============================================================
# SECTION 1: BASIC STATISTICS
# ============================================================
print("\n" + "="*70)
print("SECTION 1: BASIC STATISTICS")
print("="*70)

# Score distribution
scores = []
for m in matches:
    if 'score_p1' in m and 'score_p2' in m:
        scores.append(f"{m['score_p1']}:{m['score_p2']}")

score_counter = Counter(scores)
print("\nScore distribution (top):")
for score, count in score_counter.most_common(20):
    pct = count / len(scores) * 100
    print(f"  {score}: {count} ({pct:.2f}%)")

# Total rounds distribution
totals = [m.get('total_rounds', 0) for m in matches if 'total_rounds' in m]
total_counter = Counter(totals)
print("\nTotal rounds distribution:")
for t in sorted(total_counter.keys()):
    pct = total_counter[t] / len(totals) * 100
    print(f"  Total {t}: {total_counter[t]} ({pct:.2f}%)")

# Favorite win rate (P1 usually has lower coeff = favorite when p1_round_coeff < p2_round_coeff)
fav_wins_round1 = 0
total_with_rounds = 0
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 1 and 'p1_round_coeff' in m:
        total_with_rounds += 1
        rd1 = m['rounds'][0]
        if m['p1_round_coeff'] < m['p2_round_coeff']:
            # P1 is favorite
            if rd1['winner'] == 'P1':
                fav_wins_round1 += 1
        else:
            # P2 is favorite
            if rd1['winner'] == 'P2':
                fav_wins_round1 += 1

print(f"\nFavorite win rate in Round 1: {fav_wins_round1}/{total_with_rounds} = {fav_wins_round1/total_with_rounds*100:.2f}%")

# Favorite win rate by round
print("\nFavorite win rate by round:")
for rnd in range(1, 10):
    fav_wins = 0
    total_r = 0
    for m in matches:
        if 'rounds' in m and len(m['rounds']) >= rnd and 'p1_round_coeff' in m:
            total_r += 1
            rd = m['rounds'][rnd-1]
            if m['p1_round_coeff'] < m['p2_round_coeff']:
                if rd['winner'] == 'P1':
                    fav_wins += 1
            else:
                if rd['winner'] == 'P2':
                    fav_wins += 1
    if total_r > 0:
        print(f"  Round {rnd}: {fav_wins/total_r*100:.2f}% (n={total_r})")

# ============================================================
# SECTION 2: FINISHER ANALYSIS (Fatality/Brutality)
# ============================================================
print("\n" + "="*70)
print("SECTION 2: FINISHER ANALYSIS")
print("="*70)

finish_counter = Counter()
finish_by_round = defaultdict(Counter)
for m in matches:
    if 'rounds' in m:
        for rd in m['rounds']:
            finish_counter[rd['finish']] += 1
            finish_by_round[rd['num']][rd['finish']] += 1

total_rds = sum(finish_counter.values())
print(f"\nOverall finisher distribution (total rounds: {total_rds}):")
for f, c in finish_counter.most_common():
    print(f"  {f} ({'Fatality' if f=='F' else 'Brutality' if f=='B' else 'Regular'}): {c} ({c/total_rds*100:.2f}%)")

print("\nFinisher distribution by round:")
for rnd in sorted(finish_by_round.keys()):
    if rnd <= 10:
        total_r = sum(finish_by_round[rnd].values())
        f_pct = finish_by_round[rnd].get('F', 0) / total_r * 100
        b_pct = finish_by_round[rnd].get('B', 0) / total_r * 100
        r_pct = finish_by_round[rnd].get('R', 0) / total_r * 100
        print(f"  Round {rnd}: F={f_pct:.1f}% B={b_pct:.1f}% R={r_pct:.1f}% (n={total_r})")

# ============================================================
# SECTION 3: TIME CORRIDOR ANALYSIS
# ============================================================
print("\n" + "="*70)
print("SECTION 3: TIME CORRIDOR ANALYSIS")
print("="*70)

# Analyze by time of day (5-min corridors)
corridor_stats = defaultdict(lambda: {'total': 0, 'fav_win_r1': 0, 'fat_r1_3': 0, 'total_5m': 0, 'total_6m': 0})
for m in matches:
    if 'time' in m and 'rounds' in m and 'p1_round_coeff' in m:
        t = m['time']
        cs = corridor_stats[t]
        cs['total'] += 1
        
        # Fav win in R1
        rd1 = m['rounds'][0]
        if m['p1_round_coeff'] < m['p2_round_coeff']:
            if rd1['winner'] == 'P1':
                cs['fav_win_r1'] += 1
        else:
            if rd1['winner'] == 'P2':
                cs['fav_win_r1'] += 1
        
        # Fatality in rounds 1-3
        fat_13 = any(r['finish'] == 'F' for r in m['rounds'][:3])
        if fat_13:
            cs['fat_r1_3'] += 1
        
        # Total 5.5M (5 rounds) and 6.5M
        total = m.get('total_rounds', 0)
        if total == 5:
            cs['total_5m'] += 1
        if total <= 6:
            cs['total_6m'] += 1

# Find best corridors for various strategies
print("\nBest time corridors for Favorite R1 win (top 15):")
sorted_corr = sorted(corridor_stats.items(), key=lambda x: x[1]['fav_win_r1']/x[1]['total'] if x[1]['total'] > 100 else 0, reverse=True)
for t, s in sorted_corr[:15]:
    if s['total'] > 100:
        print(f"  {t}: {s['fav_win_r1']/s['total']*100:.2f}% (n={s['total']})")

print("\nBest time corridors for Fatality in R1-3 (top 15):")
sorted_corr = sorted(corridor_stats.items(), key=lambda x: x[1]['fat_r1_3']/x[1]['total'] if x[1]['total'] > 100 else 0, reverse=True)
for t, s in sorted_corr[:15]:
    if s['total'] > 100:
        print(f"  {t}: {s['fat_r1_3']/s['total']*100:.2f}% (n={s['total']})")

print("\nBest time corridors for Total 5.5M (top 15):")
sorted_corr = sorted(corridor_stats.items(), key=lambda x: x[1]['total_5m']/x[1]['total'] if x[1]['total'] > 100 else 0, reverse=True)
for t, s in sorted_corr[:15]:
    if s['total'] > 100:
        print(f"  {t}: {s['total_5m']/s['total']*100:.2f}% (n={s['total']})")

# ============================================================
# SECTION 4: COEFFICIENT ANALYSIS - BASE PATTERN
# ============================================================
print("\n" + "="*70)
print("SECTION 4: COEFFICIENT-BASED PATTERNS")
print("="*70)

# Favorite coefficient ranges and win rates
fav_ranges = [(1.0, 1.2), (1.2, 1.4), (1.4, 1.6), (1.6, 1.8), (1.8, 2.0), (2.0, 2.2), (2.2, 2.5)]
print("\nFavorite round win rate by coefficient range:")
for low, high in fav_ranges:
    wins = 0
    total = 0
    for m in matches:
        if 'p1_round_coeff' in m and 'rounds' in m:
            fav_coeff = min(m['p1_round_coeff'], m['p2_round_coeff'])
            if low <= fav_coeff < high:
                for rd in m['rounds']:
                    total += 1
                    if m['p1_round_coeff'] < m['p2_round_coeff']:
                        if rd['winner'] == 'P1':
                            wins += 1
                    else:
                        if rd['winner'] == 'P2':
                            wins += 1
    if total > 0:
        print(f"  Fav coeff [{low:.1f}-{high:.1f}): WR={wins/total*100:.2f}% (n={total})")

# Fatality coefficient and actual hit rate
print("\nFatality actual hit rate by coefficient range:")
fat_ranges = [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 5.0), (5.0, 6.0), (6.0, 8.0)]
for low, high in fat_ranges:
    hits = 0
    total = 0
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m:
            if low <= m['fat_coeff'] < high:
                total += 1
                if any(r['finish'] == 'F' for r in m['rounds']):
                    hits += 1
    if total > 0:
        implied = 1/((low+high)/2) * 100
        print(f"  Fat coeff [{low:.1f}-{high:.1f}): Actual={hits/total*100:.2f}% Implied={implied:.1f}% Edge={hits/total*100 - implied:.2f}% (n={total})")

print("\nDone with basic analysis!")
