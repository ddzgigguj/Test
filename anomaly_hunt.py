#!/usr/bin/env python3
"""Hunt for REAL anomalies and exploitable edges in 221K MKX matches."""
import json
from collections import Counter, defaultdict

print("Loading parsed matches...")
with open('/projects/sandbox/Test/data/parsed_matches.json', 'r') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")

# ============================================================
# KEY INSIGHT: The bookmaker margin is ~4-5% on single bets.
# We need to find situations where actual probability
# EXCEEDS implied probability by MORE than the margin.
# ============================================================

# ============================================================
# ANOMALY 1: Conditional probability shifts
# After specific events, does the next round outcome deviate?
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 1: CONDITIONAL PROBABILITIES AFTER EVENTS")
print("="*70)

# After Fatality in R1 by P1, what happens in R2?
print("\n--- After P1 Fatality in R1, who wins R2? ---")
p1_fat_r1_then_r2 = {'P1': 0, 'P2': 0}
p2_fat_r1_then_r2 = {'P1': 0, 'P2': 0}
no_fat_r1_then_r2 = {'P1': 0, 'P2': 0}

for m in matches:
    if 'rounds' not in m or len(m['rounds']) < 2:
        continue
    r1 = m['rounds'][0]
    r2 = m['rounds'][1]
    
    if r1['finish'] == 'F' and r1['winner'] == 'P1':
        p1_fat_r1_then_r2[r2['winner']] += 1
    elif r1['finish'] == 'F' and r1['winner'] == 'P2':
        p2_fat_r1_then_r2[r2['winner']] += 1
    else:
        no_fat_r1_then_r2[r2['winner']] += 1

total_p1f = sum(p1_fat_r1_then_r2.values())
total_p2f = sum(p2_fat_r1_then_r2.values())
total_nf = sum(no_fat_r1_then_r2.values())
print(f"  After P1 Fat R1: P1 wins R2 = {p1_fat_r1_then_r2['P1']/total_p1f*100:.2f}% (n={total_p1f})")
print(f"  After P2 Fat R1: P2 wins R2 = {p2_fat_r1_then_r2['P2']/total_p2f*100:.2f}% (n={total_p2f})")
print(f"  After No-Fat R1: Same winner R2 = baseline check")

# Does fatality winner tend to keep winning?
print("\n--- Winner persistence after Fatality finish ---")
for from_r in range(1, 7):
    to_r = from_r + 1
    same_winner_after_fat = 0
    same_winner_after_brut = 0
    same_winner_after_reg = 0
    total_fat = 0
    total_brut = 0
    total_reg = 0
    
    for m in matches:
        if 'rounds' not in m or len(m['rounds']) < to_r:
            continue
        r_from = m['rounds'][from_r - 1]
        r_to = m['rounds'][to_r - 1]
        
        if r_from['finish'] == 'F':
            total_fat += 1
            if r_from['winner'] == r_to['winner']:
                same_winner_after_fat += 1
        elif r_from['finish'] == 'B':
            total_brut += 1
            if r_from['winner'] == r_to['winner']:
                same_winner_after_brut += 1
        else:
            total_reg += 1
            if r_from['winner'] == r_to['winner']:
                same_winner_after_reg += 1
    
    if total_fat > 0 and total_brut > 0 and total_reg > 0:
        print(f"  R{from_r}→R{to_r}: Same winner after F={same_winner_after_fat/total_fat*100:.2f}%, B={same_winner_after_brut/total_brut*100:.2f}%, R={same_winner_after_reg/total_reg*100:.2f}%")

# ============================================================
# ANOMALY 2: Score-based conditional patterns
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 2: SCORE-BASED PATTERNS")
print("="*70)

# After score 2:0 for one player, does underdog come back more often?
print("\n--- Comeback rates from 0:2 deficit ---")
# When score is 2:0 (P1 leads), what's P(P2 eventually wins)?
p1_leads_20 = 0
p2_comebacks_from_20 = 0
p1_leads_30 = 0
p2_comebacks_from_30 = 0

for m in matches:
    if 'rounds' not in m or len(m['rounds']) < 5:
        continue
    rounds = m['rounds']
    # Check score after 2 rounds
    r1_w = rounds[0]['winner']
    r2_w = rounds[1]['winner']
    
    if r1_w == 'P1' and r2_w == 'P1':
        p1_leads_20 += 1
        # Check if P2 eventually wins (score 5:X)
        p1_total = sum(1 for r in rounds if r['winner'] == 'P1')
        p2_total = sum(1 for r in rounds if r['winner'] == 'P2')
        if p2_total > p1_total:
            p2_comebacks_from_20 += 1
    
    if r1_w == 'P1' and r2_w == 'P1' and len(rounds) >= 3 and rounds[2]['winner'] == 'P1':
        p1_leads_30 += 1
        p1_total = sum(1 for r in rounds if r['winner'] == 'P1')
        p2_total = sum(1 for r in rounds if r['winner'] == 'P2')
        if p2_total > p1_total:
            p2_comebacks_from_30 += 1

print(f"  P2 comeback from 0:2: {p2_comebacks_from_20/p1_leads_20*100:.2f}% (n={p1_leads_20})")
print(f"  P2 comeback from 0:3: {p2_comebacks_from_30/p1_leads_30*100:.2f}% (n={p1_leads_30})")

# ============================================================
# ANOMALY 3: "Hot" and "Cold" periods
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 3: TEMPORAL PATTERNS (by month/weekday)")
print("="*70)

# Parse dates and check monthly patterns
monthly_stats = defaultdict(lambda: {'total': 0, 'fav_wr': 0, 'fat_rate': 0, 'avg_total': 0})
for m in matches:
    if 'date' in m and 'rounds' in m and 'p1_round_coeff' in m:
        parts = m['date'].split('-')
        month_key = f"{parts[2]}-{parts[1]}"  # YYYY-MM
        s = monthly_stats[month_key]
        s['total'] += 1
        
        # Fav win R1
        rd1 = m['rounds'][0]
        if (m['p1_round_coeff'] < m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
           (m['p2_round_coeff'] < m['p1_round_coeff'] and rd1['winner'] == 'P2'):
            s['fav_wr'] += 1
        
        # Fat in any round
        s['fat_rate'] += sum(1 for r in m['rounds'] if r['finish'] == 'F')
        s['avg_total'] += m.get('total_rounds', 0)

print("\nMonthly stats:")
for month in sorted(monthly_stats.keys()):
    s = monthly_stats[month]
    if s['total'] > 100:
        fav_pct = s['fav_wr'] / s['total'] * 100
        fat_per_match = s['fat_rate'] / s['total']
        avg_total = s['avg_total'] / s['total']
        print(f"  {month}: n={s['total']}, Fav_R1={fav_pct:.2f}%, Fat/match={fat_per_match:.3f}, AvgTotal={avg_total:.2f}")

# ============================================================
# ANOMALY 4: P1m vs actual match winner accuracy
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 4: COEFFICIENT ACCURACY (Is bookmaker wrong?)")
print("="*70)

# Check if the match winner coefficient accurately predicts outcomes
print("\n--- Match winner accuracy by P1m coefficient range ---")
coeff_ranges = [(1.0, 1.1), (1.1, 1.2), (1.2, 1.3), (1.3, 1.4), (1.4, 1.5),
                (1.5, 1.6), (1.6, 1.7), (1.7, 1.8), (1.8, 1.9), (1.9, 2.0),
                (2.0, 2.2), (2.2, 2.5), (2.5, 3.0), (3.0, 4.0), (4.0, 7.0)]

for low, high in coeff_ranges:
    wins = 0
    total = 0
    for m in matches:
        if 'p1m_coeff' in m and 'score_p1' in m and 'score_p2' in m:
            if low <= m['p1m_coeff'] < high:
                total += 1
                if m['score_p1'] > m['score_p2']:
                    wins += 1
    if total > 100:
        implied_prob = 1 / ((low + high) / 2) * 100
        actual_prob = wins / total * 100
        edge = actual_prob - implied_prob
        print(f"  P1m [{low:.1f}-{high:.1f}): Actual P1 WR={actual_prob:.2f}%, Implied={implied_prob:.1f}%, Edge={edge:+.2f}% (n={total})")

# ============================================================
# ANOMALY 5: Round time as predictor for total
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 5: R1+R2 TIME → TOTAL ROUNDS PREDICTION")
print("="*70)

print("\n--- Sum of R1+R2 time → probability of Total 5M (5 rounds) ---")
time_sum_bins = defaultdict(lambda: {'total': 0, 't5': 0, 't6': 0, 't9': 0})
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 2 and 'total_rounds' in m:
        time_sum = m['rounds'][0]['time'] + m['rounds'][1]['time']
        bucket = (time_sum // 10) * 10
        s = time_sum_bins[bucket]
        s['total'] += 1
        if m['total_rounds'] == 5:
            s['t5'] += 1
        if m['total_rounds'] <= 6:
            s['t6'] += 1
        if m['total_rounds'] == 9:
            s['t9'] += 1

for bucket in sorted(time_sum_bins.keys()):
    s = time_sum_bins[bucket]
    if s['total'] > 500:
        print(f"  R1+R2 sum [{bucket}-{bucket+10}s): T5={s['t5']/s['total']*100:.1f}%, T≤6={s['t6']/s['total']*100:.1f}%, T9={s['t9']/s['total']*100:.1f}% (n={s['total']})")

# ============================================================
# ANOMALY 6: Brutality patterns (less studied)
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 6: BRUTALITY PATTERNS")
print("="*70)

# Brutality per-round rate by brut_coeff
print("\n--- Brutality hit rate by brut_coeff range ---")
brut_ranges = [(2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 6.0), (6.0, 8.0), (8.0, 12.0), (12.0, 20.0)]
for low, high in brut_ranges:
    hits_per_round = 0
    total_rounds_checked = 0
    for m in matches:
        if 'brut_coeff' in m and 'rounds' in m:
            if low <= m['brut_coeff'] < high:
                for r in m['rounds']:
                    total_rounds_checked += 1
                    if r['finish'] == 'B':
                        hits_per_round += 1
    if total_rounds_checked > 0:
        implied = 1/((low+high)/2) * 100
        actual = hits_per_round / total_rounds_checked * 100
        edge = actual - implied
        print(f"  brut_coeff [{low:.0f}-{high:.0f}): Actual={actual:.2f}%, Implied={implied:.1f}%, Edge={edge:+.2f}% (n_rounds={total_rounds_checked})")

# Brutality Dogon
print("\n--- Brutality Dogon R1→R2→R3, brut_coeff ranges ---")
for bc_low, bc_high in [(2.0, 3.0), (3.0, 4.0), (4.0, 5.0), (5.0, 7.0)]:
    profit = 0
    total_dogons = 0
    dogon_wins = 0
    dogon_losses = 0
    
    for m in matches:
        if 'brut_coeff' in m and 'rounds' in m and len(m['rounds']) >= 3:
            if not (bc_low <= m['brut_coeff'] < bc_high):
                continue
            
            total_dogons += 1
            bc = m['brut_coeff']
            
            r1_brut = m['rounds'][0]['finish'] == 'B'
            r2_brut = m['rounds'][1]['finish'] == 'B'
            r3_brut = m['rounds'][2]['finish'] == 'B'
            
            if r1_brut:
                profit += 1 * (bc - 1)
                dogon_wins += 1
            elif r2_brut:
                profit += 2 * (bc - 1) - 1
                dogon_wins += 1
            elif r3_brut:
                profit += 4 * (bc - 1) - 1 - 2
                dogon_wins += 1
            else:
                profit -= 7
                dogon_losses += 1
    
    if total_dogons > 0:
        print(f"  brut_coeff [{bc_low}-{bc_high}): attempts={total_dogons}, WR={dogon_wins/total_dogons*100:.1f}%, ROI={profit/total_dogons*100:.2f}%")

# ============================================================
# ANOMALY 7: Combined finish + winner patterns
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 7: FINISH TYPE + WINNER SEQUENCES")
print("="*70)

# Pattern: F-F-R in rounds → what happens in R4?
print("\n--- After R1=Fat, R2=Fat, R3=Reg → R4 outcome? ---")
r4_after_FFR = {'F': 0, 'B': 0, 'R': 0}
r4_after_RRR = {'F': 0, 'B': 0, 'R': 0}
r4_after_FFF = {'F': 0, 'B': 0, 'R': 0}

for m in matches:
    if 'rounds' not in m or len(m['rounds']) < 4:
        continue
    r1f = m['rounds'][0]['finish']
    r2f = m['rounds'][1]['finish']
    r3f = m['rounds'][2]['finish']
    r4f = m['rounds'][3]['finish']
    
    if r1f == 'F' and r2f == 'F' and r3f == 'R':
        r4_after_FFR[r4f] += 1
    if r1f == 'R' and r2f == 'R' and r3f == 'R':
        r4_after_RRR[r4f] += 1
    if r1f == 'F' and r2f == 'F' and r3f == 'F':
        r4_after_FFF[r4f] += 1

total_FFR = sum(r4_after_FFR.values())
total_RRR = sum(r4_after_RRR.values())
total_FFF = sum(r4_after_FFF.values())

if total_FFR > 0:
    print(f"  After FFR (n={total_FFR}): R4 Fat={r4_after_FFR['F']/total_FFR*100:.1f}%, Brut={r4_after_FFR['B']/total_FFR*100:.1f}%, Reg={r4_after_FFR['R']/total_FFR*100:.1f}%")
if total_RRR > 0:
    print(f"  After RRR (n={total_RRR}): R4 Fat={r4_after_RRR['F']/total_RRR*100:.1f}%, Brut={r4_after_RRR['B']/total_RRR*100:.1f}%, Reg={r4_after_RRR['R']/total_RRR*100:.1f}%")
if total_FFF > 0:
    print(f"  After FFF (n={total_FFF}): R4 Fat={r4_after_FFF['F']/total_FFF*100:.1f}%, Brut={r4_after_FFF['B']/total_FFF*100:.1f}%, Reg={r4_after_FFF['R']/total_FFF*100:.1f}%")

# General fatality frequency patterns
print(f"\n  Baseline R4 rates: Fat={28.8}%, Brut={14.6}%, Reg={56.6}%")

# ============================================================
# ANOMALY 8: VALUE BETTING - where bookmaker is most wrong
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 8: VALUE BETTING OPPORTUNITIES")
print("="*70)

# For each market type, find where actual > implied by most
print("\n--- Round winner: Actual WR vs Implied (per round, by coefficient) ---")
for rnd in [1, 3, 5, 7]:
    print(f"\n  Round {rnd}:")
    for low, high in [(1.0, 1.3), (1.3, 1.5), (1.5, 1.7), (1.7, 1.9), (1.9, 2.1), (2.1, 2.5), (2.5, 3.5)]:
        wins = 0
        total = 0
        total_profit = 0
        for m in matches:
            if 'p1_round_coeff' in m and 'rounds' in m and len(m['rounds']) >= rnd:
                if low <= m['p1_round_coeff'] < high:
                    total += 1
                    if m['rounds'][rnd-1]['winner'] == 'P1':
                        wins += 1
                        total_profit += (m['p1_round_coeff'] - 1)
                    else:
                        total_profit -= 1
        if total > 500:
            actual = wins/total*100
            mid = (low+high)/2
            implied = 1/mid*100
            edge = actual - implied
            roi = total_profit/total*100
            print(f"    P1 coeff [{low:.1f}-{high:.1f}): Actual={actual:.2f}%, Implied={implied:.1f}%, Edge={edge:+.2f}%, ROI={roi:+.2f}% (n={total})")

# ============================================================
# ANOMALY 9: Lobby-specific patterns
# ============================================================
print("\n" + "="*70)
print("ANOMALY HUNT 9: LOBBY-SPECIFIC PATTERNS")
print("="*70)

lobby_data = defaultdict(lambda: {'total': 0, 'fav_wr': 0, 'fat_rate': 0, 'total5': 0})
for m in matches:
    if 'lobby' in m and 'rounds' in m and 'p1_round_coeff' in m:
        l = lobby_data[m['lobby']]
        l['total'] += 1
        rd1 = m['rounds'][0]
        if (m['p1_round_coeff'] < m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
           (m['p2_round_coeff'] < m['p1_round_coeff'] and rd1['winner'] == 'P2'):
            l['fav_wr'] += 1
        l['fat_rate'] += sum(1 for r in m['rounds'] if r['finish'] == 'F')
        if m.get('total_rounds') == 5:
            l['total5'] += 1

print("\nLobby stats:")
for lobby in sorted(lobby_data.keys()):
    s = lobby_data[lobby]
    if s['total'] > 1000:
        print(f"  Lobby {lobby}: n={s['total']}, Fav_R1={s['fav_wr']/s['total']*100:.2f}%, Fat/match={s['fat_rate']/s['total']:.3f}, T5={s['total5']/s['total']*100:.2f}%")

print("\nDone!")
