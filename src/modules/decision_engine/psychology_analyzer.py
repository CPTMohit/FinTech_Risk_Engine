"""
=========================================================
FLOW Psychology Analyzer
=========================================================

Detects retail herd behavior, institutional traps, and
human emotion-driven market distortions.

Logic Chain:
  1. Bull Trap  -> Price breaks resistance but OI falls + PCR rising = fake breakout
  2. Bear Trap  -> Price breaks support but OI falls + PCR dropping = fake breakdown
  3. Liquidity Sweep -> RSI extreme + price at key level = stop-hunt sweep
  4. FOMO Exhaustion -> RSI > 75 + fear_greed > 80 = overbought retail rush
  5. Panic Selling Exhaustion -> RSI < 25 + fear_greed < 20 = oversold capitulation
  6. Clean Breakout -> Price at key level + OI expanding + RSI mid-range = genuine move

Output:
    AnalyzerResult (score range: -25 to +25)
"""

from .models import MarketFeatures, AnalyzerResult


class PsychologyAnalyzer:

    def analyze(self, features: MarketFeatures) -> AnalyzerResult:

        score = 0
        reasons = []
        warnings = []

        trap = features.trap_state.upper()
        fg = features.fear_greed_score       # 0-100
        rsi = features.rsi                   # 0-100
        pcr = features.pcr
        oi_structure = features.oi_structure.upper()
        institutional = features.institutional_bias.upper()
        spot = features.spot
        resistance = features.resistance
        support = features.support

        # ==============================================================
        # 1. TRAP DETECTION
        # ==============================================================

        if trap == "BULL_TRAP_REJECTION":
            # Price ran through resistance, trapped retail longs, now reversing
            score -= 20
            reasons.append("Bull Trap Detected: Resistance rejection with false breakout")
            warnings.append("Retail longs trapped above resistance — expect sharp reversal")

        elif trap == "BEAR_TRAP_REBOUND":
            # Price dipped below support, stopped out retail shorts, now rebounding
            score += 20
            reasons.append("Bear Trap Detected: Support sweep with swift rebound")
            reasons.append("Retail shorts stopped out — smart money absorbing supply")

        elif trap == "LIQUIDITY_SWEEP":
            # Stop-hunt candle at key level — institutional accumulation/distribution
            if rsi < 35:
                # Sweep below support at oversold = bullish intent
                score += 15
                reasons.append("Liquidity Sweep at Support: Smart money buying below retail stops")
            elif rsi > 65:
                # Sweep above resistance at overbought = bearish intent
                score -= 15
                reasons.append("Liquidity Sweep at Resistance: Smart money selling above retail stops")
                warnings.append("Sweep followed by distribution likely")
            else:
                score += 5
                reasons.append("Liquidity Sweep: Directional intent unclear — wait for confirmation")

        elif trap == "CLEAN_BREAKOUT":
            # Genuine breakout with OI expansion
            score += 18
            reasons.append("Clean Breakout Confirmed: Volume and OI expanding with price")

        # ==============================================================
        # 2. FEAR & GREED + RSI EXHAUSTION DETECTION
        # ==============================================================

        if fg > 80 and rsi > 72:
            # Extreme Greed: retail FOMO at peak — contrarian bearish signal
            score -= 18
            reasons.append(f"FOMO Exhaustion: Fear & Greed {fg:.0f} + RSI {rsi:.1f} — retail overextended")
            warnings.append("Extreme Greed near resistance = high reversal risk. Avoid fresh longs")

        elif fg > 65 and rsi > 60:
            # Elevated Greed: moderate overbought — caution for new longs
            score -= 8
            reasons.append(f"Elevated Greed (F&G: {fg:.0f}): Market running hot — trail stops tightly")
            warnings.append("Momentum may continue but risk/reward worsening for new entries")

        elif fg < 20 and rsi < 28:
            # Extreme Fear: capitulation zone — smart money accumulates
            score += 18
            reasons.append(f"Panic Capitulation: F&G {fg:.0f} + RSI {rsi:.1f} — institutional buying zone")
            reasons.append("Extreme Fear at support = high-probability bounce setup")

        elif fg < 35 and rsi < 42:
            # Moderate Fear: selling pressure easing — recovery setup forming
            score += 8
            reasons.append(f"Fear Zone (F&G: {fg:.0f}): Selling pressure easing — watch for reversal")

        elif 40 <= fg <= 60 and 40 <= rsi <= 60:
            # Neutral psychology — clean momentum, no emotional distortion
            score += 6
            reasons.append(f"Balanced Psychology (F&G: {fg:.0f}, RSI: {rsi:.1f}): Market rational — momentum reliable")

        # ==============================================================
        # 3. INSTITUTIONAL BIAS CONFIRMATION
        # ==============================================================

        if institutional == "ACCUMULATION":
            score += 10
            reasons.append("Institutional Accumulation Phase: Smart money building longs")
        elif institutional == "DISTRIBUTION":
            score -= 10
            reasons.append("Institutional Distribution Phase: Smart money offloading longs")
            warnings.append("Distribution phase = sell into strength, not buy dips")
        else:
            score += 3
            reasons.append("Institutional Bias Neutral: No directional conviction from large players")

        # ==============================================================
        # 4. PCR PSYCHOLOGY EXTREME READING
        # ==============================================================

        if pcr > 1.5:
            # Extreme put writing = crowd is too bearish = contrarian bullish
            score += 8
            reasons.append(f"Contrarian PCR Signal (PCR: {pcr:.2f}): Extreme put writing = crowd too bearish")
        elif pcr < 0.65:
            # Extreme call writing = crowd is too bullish = contrarian bearish
            score -= 8
            reasons.append(f"Contrarian PCR Signal (PCR: {pcr:.2f}): Extreme call buying = retail overleveraged")
            warnings.append("Call congestion = market makers have reason to push price lower")

        # Clamp score
        score = max(-25, min(25, score))

        return AnalyzerResult(
            score=score,
            reasons=reasons,
            warnings=warnings,
            metadata={
                "trap_state": trap,
                "fear_greed": fg,
                "rsi": rsi,
                "institutional_bias": institutional,
                "pcr_psychology": "CONTRARIAN_BULLISH" if pcr > 1.5 else ("CONTRARIAN_BEARISH" if pcr < 0.65 else "NORMAL")
            }
        )


psychology_analyzer = PsychologyAnalyzer()
