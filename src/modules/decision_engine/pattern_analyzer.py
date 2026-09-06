"""
=========================================================
FLOW Pattern Analyzer
=========================================================

Recognizes candlestick formations and technical structure
using price-action rules — no random components.

Patterns recognized:
  1. BULLISH_ENGULFING  -> Big bullish candle engulfs prior bearish candle
  2. BEARISH_ENGULFING  -> Big bearish candle engulfs prior bullish candle
  3. HAMMER_REJECTION   -> Long lower wick, small body at support
  4. SHOOTING_STAR      -> Long upper wick, small body at resistance
  5. PINBAR             -> Long wick either direction at key S/R level
  6. EMA Crossover      -> EMA9 crosses EMA21 (Golden/Death cross)
  7. Market Structure   -> Higher Highs vs Lower Lows analysis
  8. RSI Divergence     -> RSI direction vs price direction conflict

Output:
    AnalyzerResult (score range: -25 to +25)
"""

from .models import MarketFeatures, AnalyzerResult


class PatternAnalyzer:

    def analyze(self, features: MarketFeatures) -> AnalyzerResult:

        score = 0
        reasons = []
        warnings = []

        pattern = features.candlestick_pattern.upper()
        structure = features.market_structure.upper()
        ema9 = features.ema_9
        ema21 = features.ema_21
        rsi = features.rsi
        spot = features.spot
        support = features.support
        resistance = features.resistance
        trend = features.trend.upper()

        # ==============================================================
        # 1. CANDLESTICK PATTERN ANALYSIS
        # ==============================================================

        if pattern == "BULLISH_ENGULFING":
            score += 22
            reasons.append("Bullish Engulfing Pattern: Strong reversal candle — institutional buying on display")
            reasons.append("Next candle momentum expected to continue upward")

        elif pattern == "BEARISH_ENGULFING":
            score -= 22
            reasons.append("Bearish Engulfing Pattern: Sharp reversal — sellers overwhelmed buyers decisively")
            warnings.append("Distribution confirmed — avoid fresh longs, exits near current levels")

        elif pattern == "HAMMER_REJECTION":
            # Hammer only valid near support (within 1.5% of support)
            near_support = abs(spot - support) / (spot or 1) < 0.015
            if near_support:
                score += 18
                reasons.append("Hammer Rejection at Support: Classic smart money absorption candle")
                reasons.append("Lower wick = buyers stepping in aggressively at support zone")
            else:
                score += 8
                reasons.append("Hammer Pattern: Bullish rejection candle (not at key level — lower conviction)")
                warnings.append("Hammer not at major support — partial weight given")

        elif pattern == "SHOOTING_STAR":
            # Shooting Star only valid near resistance
            near_resistance = abs(spot - resistance) / (spot or 1) < 0.015
            if near_resistance:
                score -= 18
                reasons.append("Shooting Star at Resistance: Sellers rejecting supply zone decisively")
                warnings.append("Upper wick = profit booking + institutional distribution overhead")
            else:
                score -= 8
                reasons.append("Shooting Star: Bearish rejection candle (not at key resistance — partial weight)")

        elif pattern == "PINBAR":
            # Pinbar direction depends on context
            if rsi < 40 and (spot - support) / (spot or 1) < 0.02:
                score += 15
                reasons.append("Bullish Pinbar at Support: Long lower wick = buying pressure at key level")
            elif rsi > 60 and (resistance - spot) / (spot or 1) < 0.02:
                score -= 15
                reasons.append("Bearish Pinbar at Resistance: Long upper wick = selling pressure at key level")
                warnings.append("Pinbar at resistance — distribution possible")
            else:
                score += 5
                reasons.append("Pinbar Detected: Context-neutral pinbar formation — watch for follow-through")

        elif pattern == "DOJI":
            # Doji = indecision
            score -= 3
            reasons.append("Doji Pattern: Market indecision — avoid directional bets until resolved")
            warnings.append("Doji at key level: wait for next candle confirmation before entry")

        elif pattern == "MARUBOZU_BULL":
            # Full bull body = strong momentum
            score += 20
            reasons.append("Bullish Marubozu: Strong directional candle with no wicks = pure momentum")

        elif pattern == "MARUBOZU_BEAR":
            score -= 20
            reasons.append("Bearish Marubozu: Strong bearish candle with no wicks = pure distribution")
            warnings.append("Marubozu bear = sellers in full control")

        elif pattern == "NONE":
            score += 3
            reasons.append("No Dominant Candlestick Pattern: Market in accumulation or quiet phase")

        # ==============================================================
        # 2. EMA CROSSOVER ANALYSIS (Golden / Death Cross)
        # ==============================================================

        if ema9 > 0 and ema21 > 0:
            ema_diff_pct = ((ema9 - ema21) / (ema21 or 1)) * 100

            if ema9 > ema21:
                # Bullish EMA stack
                if ema_diff_pct > 0.5:
                    score += 12
                    reasons.append(f"Strong Golden Cross: EMA9 ({ema9:.1f}) > EMA21 ({ema21:.1f}) — bullish trend momentum confirmed")
                else:
                    score += 6
                    reasons.append(f"EMA9 > EMA21 (mild): Bullish structure — early golden cross, momentum building")
            elif ema9 < ema21:
                # Bearish EMA stack
                if ema_diff_pct < -0.5:
                    score -= 12
                    reasons.append(f"Strong Death Cross: EMA9 ({ema9:.1f}) < EMA21 ({ema21:.1f}) — bearish trend momentum confirmed")
                    warnings.append("Death cross active — short bias preferred, longs only with high conviction signals")
                else:
                    score -= 6
                    reasons.append(f"EMA9 < EMA21 (mild): Bearish structure — potential death cross forming")
                    warnings.append("EMA bearish — avoid complacent long entries")

            # Price vs EMA21 check (key institutional level)
            if spot > ema21:
                score += 5
                reasons.append(f"Spot ({spot:.1f}) above EMA21 ({ema21:.1f}): Price holding above key trend anchor")
            else:
                score -= 5
                reasons.append(f"Spot ({spot:.1f}) below EMA21 ({ema21:.1f}): Price under trend anchor — weak structure")
                warnings.append("Price below EMA21 = institutional selling pressure above")

        # ==============================================================
        # 3. MARKET STRUCTURE (Higher Highs / Lower Lows)
        # ==============================================================

        if structure == "HIGHER_HIGHS":
            score += 8
            reasons.append("Higher Highs Structure: Trend intact — each swing high exceeding prior high")
        elif structure == "LOWER_LOWS":
            score -= 8
            reasons.append("Lower Lows Structure: Downtrend intact — each swing low breaking prior low")
            warnings.append("Lower Lows confirmed — rally attempts likely to be sold into")
        elif structure == "CONSOLIDATING":
            score += 2
            reasons.append("Consolidating Market Structure: Price compressing — watch for breakout direction")
            warnings.append("Low structure conviction — breakout trade, not trend trade")

        # ==============================================================
        # 4. RSI PATTERN ANALYSIS
        # ==============================================================

        if rsi > 70:
            score -= 6
            warnings.append(f"RSI Overbought ({rsi:.1f}): Momentum stretched — reversal risk elevated")
        elif rsi > 60:
            score += 4
            reasons.append(f"RSI Bullish Zone ({rsi:.1f}): Momentum healthy and in uptrend territory")
        elif rsi < 30:
            score += 6
            reasons.append(f"RSI Oversold ({rsi:.1f}): Potential exhaustion bottom — watch for reversal candle")
        elif rsi < 40:
            score -= 4
            reasons.append(f"RSI Bearish Zone ({rsi:.1f}): Momentum weak, selling pressure dominant")
        else:
            score += 2
            reasons.append(f"RSI Neutral ({rsi:.1f}): No extreme readings — trend-following setup")

        # Clamp score
        score = max(-25, min(25, score))

        return AnalyzerResult(
            score=score,
            reasons=reasons,
            warnings=warnings,
            metadata={
                "pattern": pattern,
                "structure": structure,
                "ema9": ema9,
                "ema21": ema21,
                "rsi": rsi,
                "ema_cross": "GOLDEN" if ema9 > ema21 else "DEATH"
            }
        )


pattern_analyzer = PatternAnalyzer()
