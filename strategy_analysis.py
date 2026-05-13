#!/usr/bin/env python3
"""Strategy development and backtesting for MKX."""
import json
from collections import Counter, defaultdict

print("Loading parsed matches...")
with open('/projects/sandbox/Test/data/parsed_matches.json', 'r') as f:
    matches = json.load(f)

print(f"Total matches: {len(matches)}")

# ============================================================
# SECTION 11: PROFIT SIMULATION - VARIOUS STRATEGIES
# ============================================================
print("\n" + "="*70)
print("SECTION 11: STRATEGY BACKTESTING")
print("="*70)

# Strategy 1: Bet on favorite to win each round (flat bet)
print("\n--- Strategy 1: Flat bet on FAVORITE in R1 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'p1_round_coeff' in m and 'rounds' in m and len(m['rounds']) >= 1:
        rd1 = m['rounds'][0]
        if m['p1_round_coeff'] < m['p2_round_coeff']:
            fav_coeff = m['p1_round_coeff']
            if rd1['winner'] == 'P1':
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1
        else:
            fav_coeff = m['p2_round_coeff']
            if rd1['winner'] == 'P2':
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1

total_bets = wins + losses
print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy 2: Bet on favorite in R1 ONLY when coeff <= 1.5
print("\n--- Strategy 2: Favorite R1 when coeff <= 1.5 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'p1_round_coeff' in m and 'rounds' in m and len(m['rounds']) >= 1:
        fav_coeff = min(m['p1_round_coeff'], m['p2_round_coeff'])
        if fav_coeff > 1.5:
            continue
        rd1 = m['rounds'][0]
        if m['p1_round_coeff'] < m['p2_round_coeff']:
            if rd1['winner'] == 'P1':
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1
        else:
            if rd1['winner'] == 'P2':
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy 3: Bet on UNDERDOG in R1 when coeff >= 2.5
print("\n--- Strategy 3: Underdog R1 when coeff >= 2.5 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'p1_round_coeff' in m and 'rounds' in m and len(m['rounds']) >= 1:
        und_coeff = max(m['p1_round_coeff'], m['p2_round_coeff'])
        if und_coeff < 2.5:
            continue
        rd1 = m['rounds'][0]
        if m['p1_round_coeff'] > m['p2_round_coeff']:
            if rd1['winner'] == 'P1':
                profit += (und_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1
        else:
            if rd1['winner'] == 'P2':
                profit += (und_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy 4: Total under 5.5 (bet that match ends in exactly 5 rounds)
print("\n--- Strategy 4: Total Under 5.5 (5 rounds total) with strong fav ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'p1m_coeff' in m and 'total_rounds' in m:
        fav_match_coeff = min(m.get('p1m_coeff', 99), m.get('p2m_coeff', 99))
        if fav_match_coeff > 1.4:  # Only when there's a strong match favorite
            continue
        total = m['total_rounds']
        # Approximate odds for total 5.5M around 3.0 typically
        bet_coeff = 2.5
        if total == 5:
            profit += (bet_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy 5: Fatality bet when coeff is low (2.0-2.5) - bet that FAT happens in match
print("\n--- Strategy 5: Fatality YES when coeff [2.0-2.5) ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'rounds' in m:
        if 2.0 <= m['fat_coeff'] < 2.5:
            has_fat = any(r['finish'] == 'F' for r in m['rounds'])
            # Use midpoint of coeff range as average payout
            avg_coeff = m['fat_coeff']
            # Actually the "FYes" coeff is what we bet on
            # From data structure: FBR = fat_coeff | brut_coeff | no_finish_coeff
            # fat_coeff IS the Fatality odds directly
            if has_fat:
                # But wait - fat_coeff is the odds FOR fatality happening
                # So if we bet 1 unit at fat_coeff and it hits, profit = fat_coeff - 1
                # Actually looking at data: FYes -4.8 means coeff on Fat YES is 4.8
                # But FBR first value is also the fat coeff
                # Let me reconsider: "FBR - 4.8 | 7.75 | 1.315" and "FYes -4.8"
                # So fat_coeff is the YES coeff for any fatality in the match
                # Wait that doesn't make sense with 97% hit rate...
                # Let me look again: fat_coeff is per ROUND fatality coeff, not per match
                # Actually from the data: "FBR - 4.8 | 7.75 | 1.315" means
                # F(atality)=4.8, B(rutality)=7.75, R(egular/no finish)=1.315
                # These are per-round odds! Each round has these odds.
                # And FYes -4.8 / FNo -1.18 confirms: 4.8 is the odds for Fatality IN A ROUND
                # So fat_coeff is the round-level fatality odds
                
                # For per-match Fatality presence, we need different approach
                # Let's just track: if fat_coeff is low, fatality happens more in individual rounds
                pass
            # Skip this strategy - need to reconsider
            break

# Let me reconsider the data structure
print("\n--- Recalibrating: fat_coeff is PER-ROUND Fatality odds ---")
print("  FBR = Fatality | Brutality | Regular (no finish) coefficients PER ROUND")

# Strategy 5 revised: Bet on Fatality in specific round when coeff is good
print("\n--- Strategy 5 (revised): Bet Fatality in R5 when fat_coeff [2.0-3.0) ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 5:
        if 2.0 <= m['fat_coeff'] < 3.0:
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

# Strategy 6: Bet on Fatality at any point in rounds 1-3 (Fatality "YES" market)
# Using no_finish_coeff as the "no fatality/no brutality" odds
print("\n--- Strategy 6: Bet 'Any Finish in R1-3' (using no_finish_coeff odds) ---")
# When no_finish_coeff is high (e.g. >2), it means finish is UNLIKELY
# When no_finish_coeff is low (e.g. <1.5), it means finish is LIKELY (good to bet finish)
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'no_finish_coeff' in m and 'rounds' in m and len(m['rounds']) >= 3:
        # Bet on fatality happening in at least one of first 3 rounds
        # Only when fat_coeff is low enough
        if m['fat_coeff'] > 3.5:
            continue
        has_fat_13 = any(m['rounds'][i]['finish'] == 'F' for i in range(3))
        # Estimate the "Fatality in R1-3" coeff (not directly available, approximate)
        # With fat_coeff ~ 3.0, per-round fat prob ~ 33%
        # P(at least 1 in 3) ~ 1 - (1-0.33)^3 ~ 70%
        # Fair coeff would be ~1.43, but bookmaker might offer ~1.6
        # Let's use a flat bet approach checking profitability
        if has_fat_13:
            wins += 1
        else:
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Hit rate for Fat in R1-3 (fat_coeff<3.5): {wins/total_bets*100:.2f}% (n={total_bets})")

# ============================================================
# SECTION 12: BEST COMBINED STRATEGY
# ============================================================
print("\n" + "="*70)
print("SECTION 12: ADVANCED COMBINED STRATEGIES")
print("="*70)

# Strategy A: After 3+ underdog wins in R1, bet FAVORITE in next R1
print("\n--- Strategy A: After 3+ und wins in lobby R1 → bet FAV next R1 ---")
profit = 0
wins = 0
losses = 0
# Group by lobby
lobby_matches = defaultdict(list)
for m in matches:
    if 'lobby' in m and 'rounds' in m and 'p1_round_coeff' in m:
        lobby_matches[m['lobby']].append(m)

for lobby, lm in lobby_matches.items():
    und_streak = 0
    for m in lm:
        rd1 = m['rounds'][0]
        fav_coeff = min(m['p1_round_coeff'], m['p2_round_coeff'])
        is_fav_win = (m['p1_round_coeff'] < m['p2_round_coeff'] and rd1['winner'] == 'P1') or \
                     (m['p2_round_coeff'] < m['p1_round_coeff'] and rd1['winner'] == 'P2')
        
        if und_streak >= 3:
            # Place bet on favorite
            if is_fav_win:
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1
        
        if not is_fav_win:
            und_streak += 1
        else:
            und_streak = 0

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy B: Fatality-focused with character filter
print("\n--- Strategy B: Fatality on 'fat-prone' chars (LiuKang, Mileena, Cassie) R4-6 ---")
fat_chars = {'ЛюКенг', 'Милина', 'КэссиКейдж', 'Скорпион'}
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and len(m['rounds']) >= 6:
        if m.get('char_left') not in fat_chars and m.get('char_right') not in fat_chars:
            continue
        if m['fat_coeff'] > 4.0:
            continue
        has_fat_46 = any(m['rounds'][i]['finish'] == 'F' for i in range(3, 6))
        if has_fat_46:
            profit += (m['fat_coeff'] - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy C: Time corridor + Fatality
print("\n--- Strategy C: Night corridors (00:00-06:00) + Fatality bet in R1-3 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'fat_coeff' in m and 'rounds' in m and 'time' in m and len(m['rounds']) >= 3:
        hour = int(m['time'].split(':')[0])
        if hour >= 6:
            continue
        if m['fat_coeff'] > 3.5:
            continue
        has_fat_13 = any(m['rounds'][i]['finish'] == 'F' for i in range(3))
        if has_fat_13:
            profit += (m['fat_coeff'] - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy D: Total 5.5M on strong-fav pairs
print("\n--- Strategy D: Total 5.5M on pairs with high 5M rate + strong fav ---")
# First identify good pairs
pair_5m = defaultdict(lambda: {'total': 0, '5m': 0})
for m in matches:
    if 'char_left' in m and 'char_right' in m and 'total_rounds' in m:
        pair = f"{m['char_left']}-{m['char_right']}"
        pair_5m[pair]['total'] += 1
        if m['total_rounds'] == 5:
            pair_5m[pair]['5m'] += 1

good_pairs = {p for p, s in pair_5m.items() if s['total'] >= 100 and s['5m']/s['total'] >= 0.30}
print(f"  Good pairs (>30% 5M rate, n>=100): {len(good_pairs)}")

profit = 0
wins = 0
losses = 0
for m in matches:
    if 'char_left' in m and 'char_right' in m and 'total_rounds' in m and 'p1m_coeff' in m:
        pair = f"{m['char_left']}-{m['char_right']}"
        if pair not in good_pairs:
            continue
        fav_match = min(m.get('p1m_coeff', 99), m.get('p2m_coeff', 99))
        if fav_match > 1.5:
            continue
        # Bet at estimated odds of 2.2 for total 5.5M
        bet_coeff = 2.2
        if m['total_rounds'] == 5:
            profit += (bet_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy E: Repeat algorithm exploitation
print("\n--- Strategy E: Match-Donor Repeat Strategy (same pair, recent) ---")
# Group matches by character pair
pair_history = defaultdict(list)
for m in matches:
    if 'char_left' in m and 'char_right' in m and 'rounds' in m:
        pair = f"{m['char_left']}-{m['char_right']}"
        pair_history[pair].append(m)

profit = 0
wins = 0
losses = 0
for pair, pair_matches in pair_history.items():
    for i in range(1, len(pair_matches)):
        prev = pair_matches[i-1]
        curr = pair_matches[i]
        
        # Check if coefficients are similar (within 0.1)
        if 'p1_round_coeff' not in prev or 'p1_round_coeff' not in curr:
            continue
        if abs(prev['p1_round_coeff'] - curr['p1_round_coeff']) > 0.15:
            continue
        
        # Strategy: if prev match was 5:0 or 0:5, bet on repeat (total 5.5M)
        prev_total = prev.get('total_rounds', 0)
        if prev_total != 5:
            continue
        
        # Bet on total 5.5M in current match
        curr_total = curr.get('total_rounds', 0)
        bet_coeff = 2.5
        if curr_total == 5:
            profit += (bet_coeff - 1)
            wins += 1
        else:
            profit -= 1
            losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy F: Low coeff favorite win in match
print("\n--- Strategy F: Match winner bet on fav with coeff [1.05-1.2] ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'p1m_coeff' in m and 'score_p1' in m and 'score_p2' in m:
        fav_coeff = min(m['p1m_coeff'], m['p2m_coeff'])
        if not (1.05 <= fav_coeff <= 1.2):
            continue
        if m['p1m_coeff'] < m['p2m_coeff']:
            if m['score_p1'] > m['score_p2']:
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1
        else:
            if m['score_p2'] > m['score_p1']:
                profit += (fav_coeff - 1)
                wins += 1
            else:
                profit -= 1
                losses += 1

total_bets = wins + losses
if total_bets > 0:
    print(f"  Bets: {total_bets}, Wins: {wins} ({wins/total_bets*100:.2f}%), Losses: {losses}")
    print(f"  Profit (units): {profit:.2f} | ROI: {profit/total_bets*100:.3f}%")

# Strategy G: Time-based over/under (average time patterns)
print("\n--- Strategy G: Avg time patterns - short R1 (<=20s) → bet TM on R2 ---")
profit = 0
wins = 0
losses = 0
for m in matches:
    if 'rounds' in m and len(m['rounds']) >= 2 and 'time_lines' in m:
        r1_time = m['rounds'][0]['time']
        if r1_time > 20:
            continue
        r2_time = m['rounds'][1]['time']
        # Get the "middle" time line for over/under
        if m['time_lines'] and len(m['time_lines']) >= 2:
            mid_line = m['time_lines'][1]['line']  # Usually the "sredneye" line
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

print("\n" + "="*70)
print("ANALYSIS COMPLETE")
print("="*70)
