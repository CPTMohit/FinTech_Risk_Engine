"""
Utility Functions Module
Contains helper functions for calculations and analysis
"""

import numpy as np
import torch


def compute_finbert_sentiment(text_list, tokenizer, nlp_model, device):
    """
    Compute FinBERT sentiment scores for a list of text inputs.
    
    Args:
        text_list: List of text strings to analyze
        tokenizer: FinBERT tokenizer
        nlp_model: FinBERT model
        device: torch device (cpu or cuda)
    
    Returns:
        Tuple of (mean_sentiment_score, list_of_interpreted_data)
    """
    if not text_list:
        return 0.0, []
    
    inputs = tokenizer(text_list, padding=True, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = nlp_model(**inputs)
        probs = torch.nn.functional.softmax(outputs.logits, dim=-1).cpu().numpy()
    
    scores, interpreted_data = [], []
    for idx, p in enumerate(probs):
        net_score = p[0] - p[1] 
        scores.append(net_score)
        label = "🟢 BULL" if net_score > 0.15 else ("🔴 BEAR" if net_score < -0.15 else "⚖️ NEUT")
        interpreted_data.append({"text": text_list[idx], "score": net_score, "label": label})
    
    return float(np.mean(scores)), interpreted_data


def calculate_rsi(prices, period=14):
    """
    Calculate Relative Strength Index (RSI).
    
    Args:
        prices: Array of price values
        period: RSI period (default 14)
    
    Returns:
        RSI value as float
    """
    if len(prices) < period:
        return 50.0
    
    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period
    
    if down == 0:
        return 100.0
    
    rs = up / down
    rsi = np.zeros_like(prices)
    rsi[:period] = 100.0 - (100.0 / (1.0 + rs))

    for i in range(period, len(prices)):
        delta = deltas[i - 1]
        if delta > 0:
            upval = delta
            downval = 0.0
        else:
            upval = 0.0
            downval = -delta
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        if down == 0:
            return 100.0
        rs = up / down
        rsi[i] = 100.0 - (100.0 / (1.0 + rs))
    
    return float(rsi[-1])
