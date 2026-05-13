#!/usr/bin/env python3
"""Refined strategy analysis with realistic odds modeling."""
import json
from collections import Counter, defaultdict

print("Loading parsed matches...")
with open('/projects/sandbox/Test/data/parsed_matches.json', 'r') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")

# ============================================================
# IMPORTANT CLARIFICATION ON ODDS
# ============================================================
# fat_coeff = coefficient on Fatality happening in a SINGLE round
# If fat_coeff = 3.0, the implied prob for 1 round = 33%
# P(at least 1 fat in 3 rounds) = 1 - (1-1/3)^3 = 70.4%
# So the REAL odds for "Fat in R1-3" market would be ~1.42
# But bookmakers may not offer exactly "Fat in R1-3" market
# They offer per-round bets: Fat in R1, Fat in R2, etc.
# So each individual round bet has odds = fat_coeff

# ============================================================
# SECTION 13: REALISTIC FATALITY STRATEGIES
# ============================================================
print("\n" + "="*70)
print("SECTION 13: REALISTIC FATALITY STRATEGIES (per-round bets)")
print("="*70)

# Strategy B1: Bet on Fatality in specific round (R5) with fat-prone chars
print("\n--- B1: Fat R5 on fat-prone chars, fat_coeff<4.0 ---")
fat_chars = {'ЛюКенг', 'Милина', 'КэссиКейдж', 'Скорпион'}
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 5:
        if m.get('char_left') not in fat_chars and m.get('char_right') not in fat_chars:
            continue
        if m['fat_coeff'] >= 4.0:
            continue
        r5 = m['rounds'][4]
        if r5['finish'] == 'F':
            profit += (m['fat_coeff'] - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy B2: Dogon (martingale) on Fatality - bet R4, if miss → R5, if miss → R6
print("\n--- B2: Fatality Dogon R4→R5→R6, fat-prone chars, fat_coeff<3.5 ---")
profit = 0
wins = 0
losses = 0
total_dogons = 0
dogon_wins_r4 = 0
dogon_wins_r5 = 0
dogon_wins_r6 = 0
dogon_losses = 0

for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 6:
        if m.get('char_left') not in fat_chars and m.get('char_right') not in fat_chars:
            continue
        if m['fat_coeff'] >= 3.5:
            continue
        
        total_dogons += 1
        fc = m['fat_coeff']
        
        # Dogon: bet 1 on R4. If lose, bet 2 on R5. If lose, bet 4 on R6.
        r4_fat = m['rounds'][3]['finish'] == 'F'
        r5_fat = m['rounds'][4]['finish'] == 'F'
        r6_fat = m['rounds'][5]['finish'] == 'F'
        
        if r4_fat:
            profit += 1 * (fc - 1)  # Win on R4
            wins += 1
            dogon_wins_r4 += 1
        elif r5_fat:
            profit += 2 * (fc - 1) - 1  # Win on R5, lost R4 bet
            wins += 1
            dogon_wins_r5 += 1
        elif r6_fat:
            profit += 4 * (fc - 1) - 1 - 2  # Win on R6, lost R4 and R5
            wins += 1
            dogon_wins_r6 += 1
        else:
            profit -= (1 + 2 + 4)  # Lost all 3 steps
            losses += 1
            dogon_losses += 1

total_bets = wins + losses
if total_bets > 0:
    total_staked = total_dogons * 1 + (total_dogons - dogon_wins_r4) * 2 + dogon_losses * 4 + dogon_wins_r6 * 4
    print(f"  Dogon attempts: {total_dogons}")
    print(f"  Won at R4: {dogon_wins_r4}, R5: {dogon_wins_r5}, R6: {dogon_wins_r6}")
    print(f"  Lost all 3: {dogon_losses} ({dogon_losses/total_dogons*100:.2f}%)")
    print(f"  Net Profit (units): {profit:.2f}")
    print(f"  WR (at least 1 hit in R4-6): {wins/total_dogons*100:.2f}%")
    print(f"  ROI (per attempt): {profit/total_dogons*100:.3f}%")

# Strategy B3: Same but with top-performing specific fat_coeff range
print("\n--- B3: Dogon R4→R5→R6, fat chars, fat_coeff [2.5-3.0) ---")
profit = 0
total_dogons = 0
dogon_wins = 0
dogon_losses = 0

for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 6:
        if m.get('char_left') not in fat_chars and m.get('char_right') not in fat_chars:
            continue
        if not (2.5 <= m['fat_coeff'] < 3.0):
            continue
        
        total_dogons += 1
        fc = m['fat_coeff']
        
        r4_fat = m['rounds'][3]['finish'] == 'F'
        r5_fat = m['rounds'][4]['finish'] == 'F'
        r6_fat = m['rounds'][5]['finish'] == 'F'
        
        if r4_fat:
            profit += 1 * (fc - 1)
            dogon_wins += 1
        elif r5_fat:
            profit += 2 * (fc - 1) - 1
            dogon_wins += 1
        elif r6_fat:
            profit += 4 * (fc - 1) - 1 - 2
            dogon_wins += 1
        else:
            profit -= 7
            dogon_losses += 1

if total_dogons > 0:
    print(f"  Dogon attempts: {total_dogons}")
    print(f"  Wins: {dogon_wins} ({dogon_wins/total_dogons*100:.2f}%)")
    print(f"  Losses: {dogon_losses} ({dogon_losses/total_dogons*100:.2f}%)")
    print(f"  Net Profit: {profit:.2f} | ROI: {profit/total_dogons*100:.3f}%")

# ============================================================
# SECTION 14: NIGHT CORRIDOR FATALITY DOGON
# ============================================================
print("\n" + "="*70)
print("SECTION 14: NIGHT CORRIDOR + FAT DOGON STRATEGIES")
print("="*70)

# Best corridors from earlier: 00:00-06:00 has higher fat rates
print("\n--- C1: Night (00-06) Fatality Dogon R1→R2→R3, fat_coeff<3.5 ---")
profit = 0
total_dogons = 0
dogon_wins = 0
dogon_losses = 0

for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and 'time' in m and len(m['rounds']) >= 3:
        hour = int(m['time'].split(':')[0])
        if hour >= 6:
            continue
        if m['fat_coeff'] >= 3.5:
            continue
        
        total_dogons += 1
        fc = m['fat_coeff']
        
        r1_fat = m['rounds'][0]['finish'] == 'F'
        r2_fat = m['rounds'][1]['finish'] == 'F'
        r3_fat = m['rounds'][2]['finish'] == 'F'
        
        if r1_fat:
            profit += 1 * (fc - 1)
            dogon_wins += 1
        elif r2_fat:
            profit += 2 * (fc - 1) - 1
            dogon_wins += 1
        elif r3_fat:
            profit += 4 * (fc - 1) - 1 - 2
            dogon_wins += 1
        else:
            profit -= 7
            dogon_losses += 1

if total_dogons > 0:
    print(f"  Dogon attempts: {total_dogons}")
    print(f"  Wins: {dogon_wins} ({dogon_wins/total_dogons*100:.2f}%)")
    print(f"  Losses: {dogon_losses} ({dogon_losses/total_dogons*100:.2f}%)")
    print(f"  Net Profit: {profit:.2f} | ROI: {profit/total_dogons*100:.3f}%")

# With character filter
print("\n--- C2: Night (00-06) + Fat chars + Dogon R1→R2→R3, fat_coeff [2.0-3.0) ---")
profit = 0
total_dogons = 0
dogon_wins = 0
dogon_losses = 0

for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and 'time' in m and len(m['rounds']) >= 3:
        hour = int(m['time'].split(':')[0])
        if hour >= 6:
            continue
        if m.get('char_left') not in fat_chars and m.get('char_right') not in fat_chars:
            continue
        if not (2.0 <= m['fat_coeff'] < 3.0):
            continue
        
        total_dogons += 1
        fc = m['fat_coeff']
        
        r1_fat = m['rounds'][0]['finish'] == 'F'
        r2_fat = m['rounds'][1]['finish'] == 'F'
        r3_fat = m['rounds'][2]['finish'] == 'F'
        
        if r1_fat:
            profit += 1 * (fc - 1)
            dogon_wins += 1
        elif r2_fat:
            profit += 2 * (fc - 1) - 1
            dogon_wins += 1
        elif r3_fat:
            profit += 4 * (fc - 1) - 1 - 2
            dogon_wins += 1
        else:
            profit -= 7
            dogon_losses += 1

if total_dogons > 0:
    print(f"  Dogon attempts: {total_dogons}")
    print(f"  Wins: {dogon_wins} ({dogon_wins/total_dogons*100:.2f}%)")
    print(f"  Losses: {dogon_losses} ({dogon_losses/total_dogons*100:.2f}%)")
    print(f"  Net Profit: {profit:.2f} | ROI: {profit/total_dogons*100:.3f}%")

# ============================================================
# SECTION 15: AVERAGE TIME STRATEGIES
# ============================================================
print("\n" + "="*70)
print("SECTION 15: AVERAGE TIME (TM/TB) STRATEGIES")
print("="*70)

# Time under/over analysis using time_lines data
print("\n--- D1: Bet Under (TM) on middle line when R1 was fast ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 2 and 'time_lines' in m and len(m['time_lines']) >= 2:
        r1_time = m['rounds'][0]['time']
        if r1_time > 18:  # Only very fast R1
            continue
        r2_time = m['rounds'][1]['time']
        mid_line = m['time_lines'][1]['line']
        under_coeff = m['time_lines'][1]['under']
        
        if r2_time < mid_line:
            profit += (under_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Time wave: if R1 and R2 both were TM, bet TM on R3
print("\n--- D2: If R1 and R2 both under middle line → bet Under on R3 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 3 and 'time_lines' in m and len(m['time_lines']) >= 2:
        mid_line = m['time_lines'][1]['line']
        under_coeff = m['time_lines'][1]['under']
        
        r1_under = m['rounds'][0]['time'] < mid_line
        r2_under = m['rounds'][1]['time'] < mid_line
        
        if not (r1_under and r2_under):
            continue
        
        r3_time = m['rounds'][2]['time']
        if r3_time < mid_line:
            profit += (under_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Time wave: R1+R2 both OVER → bet OVER on R3
print("\n--- D3: If R1 and R2 both over middle line → bet Over on R3 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 3 and 'time_lines' in m and len(m['time_lines']) >= 2:
        mid_line = m['time_lines'][1]['line']
        over_coeff = m['time_lines'][1]['over']
        
        r1_over = m['rounds'][0]['time'] >= mid_line
        r2_over = m['rounds'][1]['time'] >= mid_line
        
        if not (r1_over and r2_over):
            continue
        
        r3_time = m['rounds'][2]['time']
        if r3_time >= mid_line:
            profit += (over_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# ============================================================
# SECTION 16: COMBINED OPTIMAL STRATEGY
# ============================================================
print("\n" + "="*70)
print("SECTION 16: OPTIMAL COMBINED STRATEGY")
print("="*70)

# The best strategy seems to be fatality-based dogon with character + time filters
# Let's find the absolute best combination

print("\n--- OPTIMAL: All fat chars + all hours + Dogon R1-R3 by fat_coeff range ---")
all_fat_chars = {'ЛюКенг', 'Милина', 'КэссиКейдж', 'Скорпион', 'КунгЛао', 'ДжэкиБриггс'}

for fc_low, fc_high in [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5)]:
    profit = 0
    total_dogons = 0
    dogon_wins = 0
    dogon_losses = 0
    
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 3:
            if m.get('char_left') not in all_fat_chars and m.get('char_right') not in all_fat_chars:
                continue
            if not (fc_low <= m['fat_coeff'] < fc_high):
                continue
            
            total_dogons += 1
            fc = m['fat_coeff']
            
            r1_fat = m['rounds'][0]['finish'] == 'F'
            r2_fat = m['rounds'][1]['finish'] == 'F'
            r3_fat = m['rounds'][2]['finish'] == 'F'
            
            if r1_fat:
                profit += 1 * (fc - 1)
                dogon_wins += 1
            elif r2_fat:
                profit += 2 * (fc - 1) - 1
                dogon_wins += 1
            elif r3_fat:
                profit += 4 * (fc - 1) - 1 - 2
                dogon_wins += 1
            else:
                profit -= 7
                dogon_losses += 1
    
    if total_dogons > 0:
        print(f"  fat_coeff [{fc_low}-{fc_high}): attempts={total_dogons}, WR={dogon_wins/total_dogons*100:.1f}%, ROI={profit/total_dogons*100:.2f}%, profit={profit:.0f}")

# Same but for R4-R6
print("\n--- OPTIMAL: Fat chars + Dogon R4-R6 by fat_coeff range ---")
for fc_low, fc_high in [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5)]:
    profit = 0
    total_dogons = 0
    dogon_wins = 0
    dogon_losses = 0
    
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 6:
            if m.get('char_left') not in all_fat_chars and m.get('char_right') not in all_fat_chars:
                continue
            if not (fc_low <= m['fat_coeff'] < fc_high):
                continue
            
            total_dogons += 1
            fc = m['fat_coeff']
            
            r4_fat = m['rounds'][3]['finish'] == 'F'
            r5_fat = m['rounds'][4]['finish'] == 'F'
            r6_fat = m['rounds'][5]['finish'] == 'F'
            
            if r4_fat:
                profit += 1 * (fc - 1)
                dogon_wins += 1
            elif r5_fat:
                profit += 2 * (fc - 1) - 1
                dogon_wins += 1
            elif r6_fat:
                profit += 4 * (fc - 1) - 1 - 2
                dogon_wins += 1
            else:
                profit -= 7
                dogon_losses += 1
    
    if total_dogons > 0:
        print(f"  fat_coeff [{fc_low}-{fc_high}): attempts={total_dogons}, WR={dogon_wins/total_dogons*100:.1f}%, ROI={profit/total_dogons*100:.2f}%, profit={profit:.0f}")

# Without char filter (universal)
print("\n--- UNIVERSAL: NO char filter, Dogon R1-R3 by fat_coeff range ---")
for fc_low, fc_high in [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 5.0)]:
    profit = 0
    total_dogons = 0
    dogon_wins = 0
    dogon_losses = 0
    
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 3:
            if not (fc_low <= m['fat_coeff'] < fc_high):
                continue
            
            total_dogons += 1
            fc = m['fat_coeff']
            
            r1_fat = m['rounds'][0]['finish'] == 'F'
            r2_fat = m['rounds'][1]['finish'] == 'F'
            r3_fat = m['rounds'][2]['finish'] == 'F'
            
            if r1_fat:
                profit += 1 * (fc - 1)
                dogon_wins += 1
            elif r2_fat:
                profit += 2 * (fc - 1) - 1
                dogon_wins += 1
            elif r3_fat:
                profit += 4 * (fc - 1) - 1 - 2
                dogon_wins += 1
            else:
                profit -= 7
                dogon_losses += 1
    
    if total_dogons > 0:
        print(f"  fat_coeff [{fc_low}-{fc_high}): attempts={total_dogons}, WR={dogon_wins/total_dogons*100:.1f}%, ROI={profit/total_dogons*100:.2f}%, profit={profit:.0f}")

print("\n--- UNIVERSAL: NO char filter, Dogon R4-R6 by fat_coeff range ---")
for fc_low, fc_high in [(2.0, 2.5), (2.5, 3.0), (3.0, 3.5), (3.5, 4.0), (4.0, 4.5), (4.5, 5.0)]:
    profit = 0
    total_dogons = 0
    dogon_wins = 0
    dogon_losses = 0
    
    for m in matches:
        if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 6:
            if not (fc_low <= m['fat_coeff'] < fc_high):
                continue
            
            total_dogons += 1
            fc = m['fat_coeff']
            
            r4_fat = m['rounds'][3]['finish'] == 'F'
            r5_fat = m['rounds'][4]['finish'] == 'F'
            r6_fat = m['rounds'][5]['finish'] == 'F'
            
            if r4_fat:
                profit += 1 * (fc - 1)
                dogon_wins += 1
            elif r5_fat:
                profit += 2 * (fc - 1) - 1
                dogon_wins += 1
            elif r6_fat:
                profit += 4 * (fc - 1) - 1 - 2
                dogon_wins += 1
            else:
                profit -= 7
                dogon_losses += 1
    
    if total_dogons > 0:
        print(f"  fat_coeff [{fc_low}-{fc_high}): attempts={total_dogons}, WR={dogon_wins/total_dogons*100:.1f}%, ROI={profit/total_dogons*100:.2f}%, profit={profit:.0f}")

print("\nDone!")
