/**
 * Project: FLOW - Algorithmic Options & Paper Trading Terminal
 * Module: Application Logic, Chart Engine & Paper Trading Suite
 * Author: Mohit Singh
 */

// Global State
const state = {
  currentSymbol: 'NIFTY',
  timeframe: '1m',
  showEMA: true,
  showSR: true,
  showSignals: true,
  chartBars: [],
  marketStates: {},
  positions: [],
  selectedLots: 2,
  wsConnected: false,
  ws: null,
  apiUrl: window.location.origin,

  // Paper Trading State
  paperSide: 'BUY',
  paperOptType: 'CE',
  paperLots: 2,
  paperWallet: {},
  paperPositions: []
};

// ================= INITIALIZATION =================
document.addEventListener('DOMContentLoaded', () => {
  initClock();
  initWebSocket();
  fetchInitialData();
  initCanvasChart();
  initPaperTradingPad();
  
  // Polling fallback & Paper updates
  setInterval(() => {
    if (!state.wsConnected) {
      fetchLiveMarketState();
    }
  }, 1000);

  setInterval(fetchPositions, 1500);
  setInterval(fetchPaperPortfolio, 1500);
});

// ================= CLOCK HUD =================
function initClock() {
  const clockEl = document.getElementById('live-clock');
  function update() {
    const now = new Date();
    clockEl.innerText = now.toTimeString().split(' ')[0] + ' IST';
  }
  update();
  setInterval(update, 1000);
}

// ================= VIEW NAVIGATION =================
function showTab(viewId) {
  document.querySelectorAll('.view-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
  
  const target = document.getElementById(viewId);
  if (target) target.classList.add('active');

  const tabBtn = Array.from(document.querySelectorAll('.nav-tab')).find(b => 
    b.getAttribute('onclick')?.includes(viewId)
  );
  if (tabBtn) tabBtn.classList.add('active');

  if (viewId === 'paper-trading-view') {
    fetchPaperPortfolio();
    populatePaperStrikes();
  }
  if (viewId === 'option-chain-view') loadOptionChain(state.currentSymbol);
  if (viewId === 'positions-view') fetchPositions();
  if (viewId === 'journal-view') fetchJournal();
  if (viewId === 'diagnostics-view') fetchDiagnostics();
  if (viewId === 'terminal-view') renderCanvasChart();
}

function switchSymbol(sym) {
  state.currentSymbol = sym;
  document.querySelectorAll('.ticker-box').forEach(b => b.classList.remove('active'));
  const activeBox = document.getElementById(`ticker-${sym.toLowerCase()}`);
  if (activeBox) activeBox.classList.add('active');

  fetchChartData();
  updateTerminalUI();
  populatePaperStrikes();
}

function setTimeframe(tf) {
  state.timeframe = tf;
  document.querySelectorAll('.tf-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  fetchChartData();
}

function toggleEMA() {
  state.showEMA = !state.showEMA;
  document.getElementById('btn-toggle-ema').classList.toggle('active', state.showEMA);
  renderCanvasChart();
}

function toggleSR() {
  state.showSR = !state.showSR;
  document.getElementById('btn-toggle-sr').classList.toggle('active', state.showSR);
  renderCanvasChart();
}

function toggleSignals() {
  state.showSignals = !state.showSignals;
  document.getElementById('btn-toggle-signals').classList.toggle('active', state.showSignals);
  renderCanvasChart();
}

// ================= WEBSOCKET STREAMING =================
function initWebSocket() {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/live`;

  try {
    state.ws = new WebSocket(wsUrl);

    state.ws.onopen = () => {
      state.wsConnected = true;
      fetchSystemStatus();
    };

    state.ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'TICK_UPDATE' && payload.assets) {
          state.marketStates = payload.assets;
          updateTopTickers();
          updateTerminalUI();
          updateLiveChartTick();
        }
      } catch (err) {
        console.error('WS Parse error:', err);
      }
    };

    state.ws.onclose = () => {
      state.wsConnected = false;
      setTimeout(initWebSocket, 3000);
    };

    state.ws.onerror = () => {
      state.wsConnected = false;
    };
  } catch (e) {
    console.log('WS init fallback to REST polling');
  }
}

// ================= DATA FETCHING =================
async function fetchInitialData() {
  await fetchSystemStatus();
  await fetchLiveMarketState();
  await fetchChartData();
  await fetchPositions();
  await fetchPaperPortfolio();
}

async function fetchSystemStatus() {
  try {
    const res = await fetch(`${state.apiUrl}/api/status`);
    const data = await res.json();
    if (data.status === 'success') {
      const statusLabel = document.getElementById('gateway-status');
      const latencyMeter = document.getElementById('latency-meter');
      const dot = document.getElementById('gateway-dot');

      if (!data.market_open) {
        if (data.simulation_active) {
          statusLabel.innerText = 'Sandbox Mode';
          latencyMeter.innerText = '⚡ Testing Simulator (Moving)';
          dot.style.background = '#00d2ff';
          dot.style.boxShadow = '0 0 10px #00d2ff';
        } else {
          statusLabel.innerText = 'Market Closed';
          latencyMeter.innerText = '🔴 Real Market (Frozen)';
          dot.style.background = '#ff3366';
          dot.style.boxShadow = '0 0 10px #ff3366';
        }
      } else {
        statusLabel.innerText = 'NSE SmartAPI Live';
        latencyMeter.innerText = '🟢 18ms Realtime Stream';
        dot.style.background = 'var(--bullish)';
        dot.style.boxShadow = '0 0 10px var(--bullish)';
      }
    }
  } catch (e) {
    console.error('Status fetch error:', e);
  }
}

async function toggleSimulationMode() {
  try {
    const res = await fetch(`${state.apiUrl}/api/mode/toggle-simulation`, { method: 'POST' });
    const data = await res.json();
    if (data.status === 'success') {
      showToast(data.message, 'info');
      await fetchSystemStatus();
      await fetchLiveMarketState();
      await fetchChartData();
    }
  } catch (err) {
    showToast(`Mode switch error: ${err.message}`, 'error');
  }
}

async function fetchLiveMarketState() {
  try {
    const res = await fetch(`${state.apiUrl}/api/market/live`);
    const data = await res.json();
    if (data.status === 'success') {
      state.marketStates = data.assets;
      updateTopTickers();
      updateTerminalUI();
    }
  } catch (e) {
    console.error('Fetch live market error:', e);
  }
}

async function fetchChartData() {
  try {
    const res = await fetch(`${state.apiUrl}/api/chart/${state.currentSymbol}?timeframe=${state.timeframe}`);
    const data = await res.json();
    if (data.status === 'success') {
      state.chartBars = data.bars || [];
      renderCanvasChart();
    }
  } catch (e) {
    console.error('Fetch chart error:', e);
  }
}

// ================= UI UPDATERS =================
function updateTopTickers() {
  const nifty = state.marketStates['NIFTY 50 INDEX'];
  const bank = state.marketStates['BANK NIFTY INDEX'];

  if (nifty) {
    document.getElementById('nifty-price').innerText = `₹${nifty.spot.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    const nChg = document.getElementById('nifty-change');
    nChg.innerText = `${nifty.change_7d >= 0 ? '+' : ''}${nifty.change_7d.toFixed(2)}%`;
    nChg.className = `ticker-change ${nifty.change_7d >= 0 ? 'bullish' : 'bearish'}`;
    document.getElementById('nifty-pcr').innerText = `PCR: ${nifty.pcr.toFixed(2)}`;
  }

  if (bank) {
    document.getElementById('banknifty-price').innerText = `₹${bank.spot.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
    const bChg = document.getElementById('banknifty-change');
    bChg.innerText = `${bank.change_7d >= 0 ? '+' : ''}${bank.change_7d.toFixed(2)}%`;
    bChg.className = `ticker-change ${bank.change_7d >= 0 ? 'bullish' : 'bearish'}`;
    document.getElementById('banknifty-pcr').innerText = `PCR: ${bank.pcr.toFixed(2)}`;
  }
}

function updateTerminalUI() {
  const assetKey = state.currentSymbol === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX';
  const asset = state.marketStates[assetKey];
  if (!asset) return;

  // Chart Header
  document.getElementById('current-asset-title').innerText = asset.asset_title;
  document.getElementById('chart-spot-display').innerText = `₹${asset.spot.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
  
  const chgEl = document.getElementById('chart-change-display');
  chgEl.innerText = `${asset.change_7d >= 0 ? '+' : ''}${asset.change_7d.toFixed(2)}%`;
  chgEl.className = `change-badge ${asset.change_7d >= 0 ? 'bullish' : 'bearish'}`;
  
  document.getElementById('chart-regime-tag').innerText = asset.market_regime;

  // Chart Footer Metrics
  document.getElementById('chart-support-val').innerText = `₹${asset.support.toLocaleString('en-IN')}`;
  document.getElementById('chart-resistance-val').innerText = `₹${asset.resistance.toLocaleString('en-IN')}`;
  document.getElementById('chart-maxpain-val').innerText = `₹${asset.max_pain.toLocaleString('en-IN')}`;
  document.getElementById('chart-oi-val').innerText = `${(asset.oi / 10000000).toFixed(2)} Cr`;
  
  const oiBiasEl = document.getElementById('chart-oibias-val');
  oiBiasEl.innerText = asset.oi_bias;
  oiBiasEl.className = `m-val ${asset.oi_bias === 'BULLISH' ? 'bullish' : 'bearish'}`;

  // AI Hub
  document.getElementById('ai-confidence-val').innerText = `${asset.trade_confidence}%`;
  
  const offset = 427 - (427 * (asset.trade_confidence / 100));
  const circle = document.getElementById('ai-gauge-circle');
  circle.style.strokeDashoffset = offset;
  circle.style.stroke = asset.action.includes('CALL') ? 'var(--bullish)' : (asset.action.includes('PUT') ? 'var(--bearish)' : 'var(--accent-blue)');

  const scoreEl = document.getElementById('ai-score-val');
  scoreEl.innerText = `${asset.signal_score >= 0 ? '+' : ''}${asset.signal_score} / 100`;
  scoreEl.className = `score-val ${asset.signal_score >= 0 ? 'bullish' : 'bearish'}`;

  const meterFill = document.getElementById('ai-meter-fill');
  meterFill.style.width = `${Math.min(100, Math.max(10, Math.abs(asset.signal_score)))}%`;
  meterFill.className = `meter-fill ${asset.signal_score >= 0 ? 'bullish' : 'bearish'}`;

  document.getElementById('ai-decision-title').innerText = asset.action;
  const actionBox = document.getElementById('ai-action-box');
  actionBox.className = `action-highlight-box ${asset.action.includes('CALL') ? 'action-buy-call' : (asset.action.includes('PUT') ? 'action-buy-put' : '')}`;

  // 6 Specialists
  const sp = asset.specialist_scores || {};
  if (sp.trend) {
    document.getElementById('sp-trend-val').innerText = sp.trend.status;
    document.getElementById('sp-trend-score').innerText = `${sp.trend.score >= 0 ? '+' : ''}${sp.trend.score}`;
  }
  if (sp.pcr) {
    document.getElementById('sp-pcr-val').innerText = `${asset.pcr.toFixed(2)} (${asset.pcr > 1.0 ? 'Bullish Bias' : 'Bearish Bias'})`;
    document.getElementById('sp-pcr-score').innerText = `${sp.pcr.score >= 0 ? '+' : ''}${sp.pcr.score}`;
  }
  if (sp.oi_buildup) {
    document.getElementById('sp-oi-val').innerText = sp.oi_buildup.structure;
    document.getElementById('sp-oi-score').innerText = `${sp.oi_buildup.score >= 0 ? '+' : ''}${sp.oi_buildup.score}`;
  }
  if (sp.market_regime) {
    document.getElementById('sp-regime-val').innerText = sp.market_regime.regime;
  }
  if (sp.volume_flow) {
    document.getElementById('sp-volume-val').innerText = `${sp.volume_flow.bias} Flow`;
  }

  // Greeks
  document.getElementById('greek-delta').innerText = asset.delta.toFixed(2);
  document.getElementById('greek-gamma').innerText = asset.gamma.toFixed(4);
  document.getElementById('greek-theta').innerText = asset.theta.toFixed(2);
  document.getElementById('greek-vega').innerText = asset.vega.toFixed(2);
  document.getElementById('g-fill-delta').style.width = `${Math.min(100, Math.abs(asset.delta) * 100)}%`;

  // AI Reasons
  const reasonsList = document.getElementById('ai-reasons-list');
  reasonsList.innerHTML = (asset.trade_reasons || []).map(r => `<li><i class="fa-solid fa-circle-check"></i> ${r}</li>`).join('');

  // Order Ticket
  document.getElementById('ticket-contract-name').innerText = asset.opt_symbol;
  const ticketBadge = document.getElementById('ticket-action-badge');
  ticketBadge.innerHTML = `<i class="fa-solid ${asset.action.includes('CALL') ? 'fa-arrow-trend-up' : 'fa-arrow-trend-down'}"></i> ${asset.action}`;
  ticketBadge.className = `ticket-action-badge ${asset.action.includes('CALL') ? 'action-buy-call' : 'action-buy-put'}`;

  document.getElementById('ticket-entry').innerText = `₹${asset.entry_price.toFixed(2)}`;
  document.getElementById('ticket-sl').innerText = `₹${asset.stop_loss.toFixed(2)}`;
  document.getElementById('ticket-tp').innerText = `₹${asset.target.toFixed(2)}`;
  document.getElementById('ticket-rr').innerText = `${asset.risk_reward.toFixed(2)} : 1`;

  recalcOrderSizing();
}

function adjustLots(delta) {
  state.selectedLots = Math.max(1, Math.min(50, state.selectedLots + delta));
  document.getElementById('input-lots').value = state.selectedLots;
  recalcOrderSizing();
}

function recalcOrderSizing() {
  const lotsInput = document.getElementById('input-lots');
  state.selectedLots = parseInt(lotsInput.value) || 1;
  
  const assetKey = state.currentSymbol === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX';
  const asset = state.marketStates[assetKey];
  if (!asset) return;

  const lotSize = state.currentSymbol === 'NIFTY' ? 75 : 35;
  const qty = state.selectedLots * lotSize;
  const capital = qty * asset.opt_price;
  const maxLoss = Math.max(0, (asset.entry_price - asset.stop_loss) * qty);
  const expProfit = Math.max(0, (asset.target - asset.entry_price) * qty);
  const riskPct = ((maxLoss / 1000000) * 100).toFixed(1);

  document.getElementById('display-quantity').innerText = `${qty} Qty`;
  document.getElementById('ticket-capital').innerText = `₹${capital.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
  document.getElementById('ticket-maxloss').innerText = `₹${maxLoss.toLocaleString('en-IN', {maximumFractionDigits: 0})} (${riskPct}%)`;
  document.getElementById('ticket-expprofit').innerText = `₹${expProfit.toLocaleString('en-IN', {maximumFractionDigits: 0})}`;
}

// ================= FLOW PAPER TRADING SUITE =================
function initPaperTradingPad() {
  populatePaperStrikes();
  recalcPaperOrder();
}

function setPaperSide(side) {
  state.paperSide = side;
  document.getElementById('btn-side-buy').classList.toggle('active', side === 'BUY');
  document.getElementById('btn-side-sell').classList.toggle('active', side === 'SELL');
  recalcPaperOrder();
}

function setPaperOptType(type) {
  state.paperOptType = type;
  document.getElementById('btn-opt-ce').classList.toggle('active', type === 'CE');
  document.getElementById('btn-opt-pe').classList.toggle('active', type === 'PE');
  document.getElementById('btn-opt-spot').classList.toggle('active', type === 'FUT');
  populatePaperStrikes();
  recalcPaperOrder();
}

function onPaperAssetChange() {
  const assetSelect = document.getElementById('paper-asset-select').value;
  const multiplierEl = document.getElementById('paper-lot-multiplier');
  multiplierEl.innerText = assetSelect === 'NIFTY' ? '75 Qty/Lot' : '35 Qty/Lot';
  populatePaperStrikes();
  recalcPaperOrder();
}

function populatePaperStrikes() {
  const assetSym = document.getElementById('paper-asset-select')?.value || state.currentSymbol;
  const strikeSelect = document.getElementById('paper-strike-select');
  if (!strikeSelect) return;

  const base = assetSym === 'NIFTY' ? 23900 : 57400;
  const step = assetSym === 'NIFTY' ? 50 : 100;
  
  strikeSelect.innerHTML = '';
  for (let i = -5; i <= 5; i++) {
    const s = base + (i * step);
    const opt = document.createElement('option');
    opt.value = s;
    opt.innerText = `${s} ${state.paperOptType} ${i === 0 ? '★ ATM' : (i < 0 ? 'ITM' : 'OTM')}`;
    if (i === 0) opt.selected = true;
    strikeSelect.appendChild(opt);
  }
}

function onPaperStrikeChange() {
  const strike = parseInt(document.getElementById('paper-strike-select').value);
  const assetSym = document.getElementById('paper-asset-select').value;
  const spot = assetSym === 'NIFTY' ? 23897.70 : 57369.65;
  const dist = Math.abs(spot - strike);
  
  // Dynamic estimated premium
  let prem = 150.0;
  if (state.paperOptType === 'CE') {
    prem = Math.max(20.0, (spot - strike > 0 ? spot - strike : 0) + (spot * 0.006) - (dist * 0.3));
  } else {
    prem = Math.max(20.0, (strike - spot > 0 ? strike - spot : 0) + (spot * 0.006) - (dist * 0.3));
  }
  
  document.getElementById('paper-entry-price').value = prem.toFixed(2);
  document.getElementById('paper-sl-price').value = (prem * 0.85).toFixed(2);
  document.getElementById('paper-tp-price').value = (prem * 1.30).toFixed(2);
  recalcPaperOrder();
}

function adjustPaperLots(delta) {
  state.paperLots = Math.max(1, Math.min(100, state.paperLots + delta));
  document.getElementById('paper-lots-input').value = state.paperLots;
  recalcPaperOrder();
}

function recalcPaperOrder() {
  const assetSym = document.getElementById('paper-asset-select')?.value || 'NIFTY';
  const lotSize = assetSym === 'NIFTY' ? 75 : 35;
  const lots = parseInt(document.getElementById('paper-lots-input')?.value || 2);
  const entryP = parseFloat(document.getElementById('paper-entry-price')?.value || 150.0);
  const slP = parseFloat(document.getElementById('paper-sl-price')?.value || 130.0);
  const tpP = parseFloat(document.getElementById('paper-tp-price')?.value || 190.0);

  const qty = lots * lotSize;
  const margin = qty * entryP;
  const maxRisk = Math.max(0, Math.abs(entryP - slP) * qty);
  const expProfit = Math.max(0, Math.abs(tpP - entryP) * qty);
  const rr = (Math.abs(tpP - entryP) / (Math.abs(entryP - slP) || 1)).toFixed(2);

  if (document.getElementById('paper-summary-qty')) {
    document.getElementById('paper-summary-qty').innerText = `${qty} Qty (${lots} Lots)`;
    document.getElementById('paper-summary-margin').innerText = `₹${margin.toLocaleString('en-IN', {maximumFractionDigits: 2})}`;
    document.getElementById('paper-summary-loss').innerText = `₹${maxRisk.toLocaleString('en-IN', {maximumFractionDigits: 2})}`;
    document.getElementById('paper-summary-profit').innerText = `₹${expProfit.toLocaleString('en-IN', {maximumFractionDigits: 2})}`;
    document.getElementById('paper-summary-rr').innerText = `${rr} : 1`;
  }
}

async function submitPaperOrder() {
  const assetSym = document.getElementById('paper-asset-select').value;
  const strike = parseInt(document.getElementById('paper-strike-select').value);
  const lots = parseInt(document.getElementById('paper-lots-input').value);
  const lotSize = assetSym === 'NIFTY' ? 75 : 35;
  const qty = lots * lotSize;
  const price = parseFloat(document.getElementById('paper-entry-price').value);
  const sl = parseFloat(document.getElementById('paper-sl-price').value);
  const tp = parseFloat(document.getElementById('paper-tp-price').value);
  const orderType = document.getElementById('paper-ordertype-select').value;

  const payload = {
    asset: assetSym === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX',
    symbol: assetSym,
    side: state.paperSide,
    instrument: 'OPTION',
    strike: strike,
    option_type: state.paperOptType,
    order_type: orderType,
    price: price,
    lots: lots,
    quantity: qty,
    stop_loss: sl,
    target: tp
  };

  try {
    const res = await fetch(`${state.apiUrl}/api/paper/order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.status === 'success') {
      playAudioChime();
      showToast(result.message, 'success');
      fetchPaperPortfolio();
      fetchPositions();
    } else {
      showToast(result.detail || 'Paper order rejected', 'error');
    }
  } catch (err) {
    showToast(`Order failed: ${err.message}`, 'error');
  }
}

async function fetchPaperPortfolio() {
  try {
    const res = await fetch(`${state.apiUrl}/api/paper/portfolio`);
    const data = await res.json();
    if (data.status === 'success') {
      state.paperWallet = data.wallet || {};
      state.paperPositions = data.open_positions || [];

      // Top Wallet HUD
      document.getElementById('hud-paper-balance').innerText = `₹${(data.wallet.total_balance || 1000000).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;

      // Paper Suite Cards
      if (document.getElementById('paper-tot-balance')) {
        document.getElementById('paper-tot-balance').innerText = `₹${data.wallet.total_balance.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        document.getElementById('paper-avail-margin').innerText = `₹${data.wallet.available_margin.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        document.getElementById('paper-used-margin').innerText = `₹${data.wallet.used_margin.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        
        const floatPnl = document.getElementById('paper-floating-pnl');
        floatPnl.innerText = `₹${data.wallet.unrealized_pnl >= 0 ? '+' : ''}${data.wallet.unrealized_pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        floatPnl.className = `f-val ${data.wallet.unrealized_pnl >= 0 ? 'bullish' : 'bearish'}`;

        document.getElementById('paper-realized-pnl').innerText = `₹${data.wallet.realized_pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
        
        const roiEl = document.getElementById('paper-roi-pct');
        roiEl.innerText = `${data.wallet.pnl_pct >= 0 ? '+' : ''}${data.wallet.pnl_pct.toFixed(2)}%`;
        roiEl.className = `f-val ${data.wallet.pnl_pct >= 0 ? 'bullish' : 'bearish'}`;

        document.getElementById('paper-open-count').innerText = data.open_positions.length;
        renderPaperPositionsTable(data.open_positions);
      }
    }
  } catch (err) {
    console.error('Paper portfolio error:', err);
  }
}

function renderPaperPositionsTable(positions) {
  const tbody = document.getElementById('paper-positions-tbody');
  if (!tbody) return;

  if (!positions || positions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="empty-state">No active paper positions. Submit an order from the pad.</td></tr>`;
    return;
  }

  tbody.innerHTML = positions.map(p => {
    const pnlClass = p.unrealized_pnl >= 0 ? 'bullish' : 'bearish';
    return `
      <tr>
        <td><b>${p.trade_id}</b></td>
        <td>${p.symbol} ${p.strike} ${p.option_type}</td>
        <td><span class="${p.side === 'BUY' ? 'bullish' : 'bearish'}">${p.side}</span></td>
        <td>${p.quantity} (${p.lots}L)</td>
        <td>₹${p.entry_price.toFixed(2)}</td>
        <td>₹${p.current_price.toFixed(2)}</td>
        <td>SL: ₹${p.stop_loss} | TP: ₹${p.target}</td>
        <td class="${pnlClass}"><b>₹${p.unrealized_pnl >= 0 ? '+' : ''}${p.unrealized_pnl.toFixed(2)}</b></td>
        <td><button class="btn-close-pos" onclick="closePaperPosition('${p.trade_id}')">Square Off</button></td>
      </tr>
    `;
  }).join('');
}

async function closePaperPosition(tradeId) {
  try {
    const res = await fetch(`${state.apiUrl}/api/paper/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ trade_id: tradeId })
    });
    const result = await res.json();
    if (result.status === 'success') {
      showToast(result.message, 'success');
      fetchPaperPortfolio();
      fetchPositions();
    }
  } catch (err) {
    showToast(`Close error: ${err.message}`, 'error');
  }
}

async function closeAllPaperPositions() {
  if (!confirm('Are you sure you want to close ALL open paper positions?')) return;
  try {
    const res = await fetch(`${state.apiUrl}/api/paper/close-all`, { method: 'POST' });
    const result = await res.json();
    if (result.status === 'success') {
      showToast(result.message, 'info');
      fetchPaperPortfolio();
      fetchPositions();
    }
  } catch (err) {
    showToast(`Close all error: ${err.message}`, 'error');
  }
}

async function promptResetWallet() {
  const val = prompt('Enter starting virtual funds (₹):', '1000000');
  if (!val) return;
  const num = parseFloat(val);
  if (isNaN(num) || num <= 0) return alert('Invalid amount');

  try {
    const res = await fetch(`${state.apiUrl}/api/paper/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ capital: num })
    });
    const result = await res.json();
    if (result.status === 'success') {
      showToast(result.message, 'success');
      fetchPaperPortfolio();
      fetchPositions();
    }
  } catch (err) {
    showToast(`Reset error: ${err.message}`, 'error');
  }
}

// ================= ORDER EXECUTION FROM TERMINAL =================
async function executeAlgorithmicOrder() {
  const assetKey = state.currentSymbol === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX';
  const asset = state.marketStates[assetKey];
  if (!asset) return;

  const lotSize = state.currentSymbol === 'NIFTY' ? 75 : 35;
  const qty = state.selectedLots * lotSize;

  const payload = {
    asset: asset.asset_title,
    symbol: state.currentSymbol,
    side: 'BUY',
    instrument: 'OPTION',
    strike: asset.atm_strike,
    option_type: asset.action.includes('CALL') ? 'CE' : 'PE',
    order_type: 'MARKET',
    price: asset.entry_price,
    lots: state.selectedLots,
    quantity: qty,
    stop_loss: asset.stop_loss,
    target: asset.target
  };

  try {
    const res = await fetch(`${state.apiUrl}/api/paper/order`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();
    if (result.status === 'success') {
      playAudioChime();
      showToast(`⚡ Paper Order Executed: BUY ${qty} Qty @ ₹${asset.entry_price}`, 'success');
      fetchPositions();
      fetchPaperPortfolio();
    }
  } catch (err) {
    showToast(`Order failed: ${err.message}`, 'error');
  }
}

// ================= POSITIONS & JOURNAL =================
async function fetchPositions() {
  try {
    const res = await fetch(`${state.apiUrl}/api/paper/portfolio`);
    const data = await res.json();
    if (data.status === 'success') {
      state.positions = data.open_positions.concat(data.closed_positions) || [];
      const wallet = data.wallet || {};
      
      document.getElementById('open-positions-badge').innerText = data.open_positions.length || 0;
      
      const unPnl = document.getElementById('pos-unrealized-pnl');
      unPnl.innerText = `₹${wallet.unrealized_pnl >= 0 ? '+' : ''}${wallet.unrealized_pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      unPnl.className = `stat-pnl ${wallet.unrealized_pnl >= 0 ? 'bullish' : 'bearish'}`;

      document.getElementById('pos-realized-pnl').innerText = `₹${wallet.realized_pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      
      const totPnl = document.getElementById('pos-total-pnl');
      totPnl.innerText = `₹${wallet.total_pnl >= 0 ? '+' : ''}${wallet.total_pnl.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      totPnl.className = `stat-pnl ${wallet.total_pnl >= 0 ? 'bullish' : 'bearish'}`;

      renderPositionsTable();
    }
  } catch (e) {
    console.error('Fetch positions error:', e);
  }
}

function renderPositionsTable() {
  const tbody = document.getElementById('positions-table-tbody');
  if (!tbody) return;

  if (!state.positions || state.positions.length === 0) {
    tbody.innerHTML = `<tr><td colspan="12" class="empty-state">No active positions. Execute a paper order from the terminal or paper pad.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.positions.map(p => {
    const isClosed = p.status === 'CLOSED';
    const pnlVal = isClosed ? p.realized_pnl : p.unrealized_pnl;
    const pnlClass = pnlVal >= 0 ? 'bullish' : 'bearish';

    return `
      <tr>
        <td><b>${p.trade_id}</b></td>
        <td>${p.timestamp.split(' ')[1] || p.timestamp}</td>
        <td><b>${p.symbol} ${p.strike} ${p.option_type}</b></td>
        <td><span class="${p.side === 'BUY' ? 'bullish' : 'bearish'}">${p.side || 'BUY'}</span></td>
        <td>${p.quantity} (${p.lots}L)</td>
        <td>₹${p.entry_price.toFixed(2)}</td>
        <td>₹${(p.current_price || p.entry_price).toFixed(2)}</td>
        <td class="bearish">₹${p.stop_loss.toFixed(2)}</td>
        <td class="bullish">₹${p.target.toFixed(2)}</td>
        <td class="${pnlClass}"><b>₹${pnlVal >= 0 ? '+' : ''}${pnlVal.toFixed(2)}</b></td>
        <td><span class="stage-status live">${p.status}</span></td>
        <td>
          ${!isClosed ? `<button class="btn-close-pos" onclick="closePaperPosition('${p.trade_id}')">Square Off</button>` : `<span style="color:var(--text-dim)">Closed</span>`}
        </td>
      </tr>
    `;
  }).join('');
}

async function fetchJournal() {
  try {
    const res = await fetch(`${state.apiUrl}/api/journal`);
    const data = await res.json();
    if (data.status === 'success') {
      const stats = data.stats || {};
      document.getElementById('journal-total-trades').innerText = stats.total_trades || 0;
      document.getElementById('journal-win-rate').innerText = `${stats.win_rate || 0}%`;
      document.getElementById('journal-profit-factor').innerText = stats.profit_factor || '2.45';
      
      const netPnlEl = document.getElementById('journal-net-pnl');
      netPnlEl.innerText = `₹${(stats.net_pnl || 0) >= 0 ? '+' : ''}${(stats.net_pnl || 0).toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      netPnlEl.className = (stats.net_pnl || 0) >= 0 ? 'bullish' : 'bearish';

      const tbody = document.getElementById('journal-table-tbody');
      tbody.innerHTML = (data.trades || []).map(t => `
        <tr>
          <td>${t.timestamp || '--'}</td>
          <td><b>${t.asset || '--'}</b></td>
          <td><span class="${(t.signal || '').includes('CALL') ? 'bullish' : 'bearish'}">${t.signal || '--'}</span></td>
          <td>₹${Number(t.entry || 0).toFixed(2)}</td>
          <td class="bearish">₹${Number(t.stop_loss || 0).toFixed(2)}</td>
          <td class="bullish">₹${Number(t.target || 0).toFixed(2)}</td>
          <td>${t.confidence || 0}%</td>
          <td>${t.quantity || 0}</td>
          <td>₹${Number(t.capital_required || 0).toLocaleString('en-IN')}</td>
          <td><span class="stage-status live">${t.status || 'CLOSED'}</span></td>
          <td class="${Number(t.pnl || 0) >= 0 ? 'bullish' : 'bearish'}"><b>₹${Number(t.pnl || 0).toFixed(2)}</b></td>
        </tr>
      `).join('');
    }
  } catch (e) {
    console.error('Fetch journal error:', e);
  }
}

// ================= OPTION CHAIN MATRIX =================
async function loadOptionChain(sym) {
  document.getElementById('oc-btn-nifty').classList.toggle('active', sym === 'NIFTY');
  document.getElementById('oc-btn-banknifty').classList.toggle('active', sym === 'BANKNIFTY');

  try {
    const res = await fetch(`${state.apiUrl}/api/option-chain/${sym}`);
    const data = await res.json();
    if (data.status === 'success') {
      document.getElementById('oc-spot-val').innerText = `₹${data.spot.toLocaleString('en-IN', {minimumFractionDigits: 2})}`;
      document.getElementById('oc-pcr-val').innerText = data.pcr.toFixed(2);
      document.getElementById('oc-maxpain-val').innerText = data.max_pain.toLocaleString('en-IN');
      document.getElementById('oc-calloi-val').innerText = `${(data.total_call_oi / 1000000).toFixed(1)}M`;
      document.getElementById('oc-putoi-val').innerText = `${(data.total_put_oi / 1000000).toFixed(1)}M`;

      const tbody = document.getElementById('option-chain-tbody');
      tbody.innerHTML = (data.strikes || []).map(s => {
        const atmClass = s.is_atm ? 'row-atm' : '';
        const itmCall = s.is_itm_call ? 'itm-call' : '';
        const itmPut = s.is_itm_put ? 'itm-put' : '';

        return `
          <tr class="${atmClass}">
            <td class="${itmCall}">${s.call.oi.toLocaleString('en-IN')}</td>
            <td class="${itmCall} ${s.call.oi_change >= 0 ? 'bullish' : 'bearish'}">${s.call.oi_change >= 0 ? '+' : ''}${s.call.oi_change.toLocaleString('en-IN')}</td>
            <td class="${itmCall}">${s.call.volume.toLocaleString('en-IN')}</td>
            <td class="${itmCall}">${s.call.iv}%</td>
            <td class="${itmCall} bullish"><b>₹${s.call.ltp.toFixed(2)}</b></td>
            <td class="strike-col">${s.strike.toLocaleString('en-IN')} ${s.is_atm ? '★ ATM' : ''}</td>
            <td class="${itmPut} bearish"><b>₹${s.put.ltp.toFixed(2)}</b></td>
            <td class="${itmPut}">${s.put.iv}%</td>
            <td class="${itmPut}">${s.put.volume.toLocaleString('en-IN')}</td>
            <td class="${itmPut} ${s.put.oi_change >= 0 ? 'bullish' : 'bearish'}">${s.put.oi_change >= 0 ? '+' : ''}${s.put.oi_change.toLocaleString('en-IN')}</td>
            <td class="${itmPut}">${s.put.oi.toLocaleString('en-IN')}</td>
          </tr>
        `;
      }).join('');
    }
  } catch (err) {
    console.error('Option chain error:', err);
  }
}

// ================= BACKEND DIAGNOSTICS =================
async function fetchDiagnostics() {
  try {
    const res = await fetch(`${state.apiUrl}/api/diagnostics`);
    const data = await res.json();
    if (data.status === 'success') {
      document.getElementById('diag-json-features').innerText = JSON.stringify(data.ai_pipeline, null, 2);
      
      const endpointList = document.getElementById('diag-endpoint-list');
      endpointList.innerHTML = (data.endpoints || []).map(e => `
        <div class="endpoint-item">
          <div>
            <span class="method-tag ${e.method}">${e.method}</span>
            <span style="color:#fff; margin-left:8px;">${e.path}</span>
          </div>
          <span style="color:var(--text-muted)">${e.desc}</span>
        </div>
      `).join('');
    }
  } catch (e) {
    console.error('Diagnostics error:', e);
  }
}

// ================= INTERACTIVE CANVAS CHART ENGINE =================
let canvas, ctx;
let hoveredBarIndex = -1;

function initCanvasChart() {
  canvas = document.getElementById('trading-chart');
  if (!canvas) return;
  ctx = canvas.getContext('2d');

  function resize() {
    const rect = canvas.parentElement.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);
    renderCanvasChart();
  }

  window.addEventListener('resize', resize);
  resize();

  canvas.addEventListener('mousemove', (e) => {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    handleChartMouseMove(x, y);
  });

  canvas.addEventListener('mouseleave', () => {
    document.getElementById('chart-tooltip').classList.add('hidden');
    hoveredBarIndex = -1;
    renderCanvasChart();
  });
}

function updateLiveChartTick() {
  const assetKey = state.currentSymbol === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX';
  const asset = state.marketStates[assetKey];
  if (!asset || !state.chartBars.length) return;

  const lastBar = state.chartBars[state.chartBars.length - 1];
  lastBar.close = asset.spot;
  lastBar.high = Math.max(lastBar.high, asset.spot);
  lastBar.low = Math.min(lastBar.low, asset.spot);
  renderCanvasChart();
}

function renderCanvasChart() {
  if (!canvas || !ctx || !state.chartBars.length) return;

  const width = canvas.width / window.devicePixelRatio;
  const height = canvas.height / window.devicePixelRatio;
  const chartHeight = height - 80;
  const volumeHeight = 60;

  ctx.clearRect(0, 0, width, height);

  const bars = state.chartBars.slice(-60);
  const count = bars.length;
  if (count === 0) return;

  const barWidth = Math.max(4, (width - 80) / count);
  const candleGap = barWidth * 0.25;

  let minPrice = Infinity;
  let maxPrice = -Infinity;
  let maxVol = 0;

  bars.forEach(b => {
    minPrice = Math.min(minPrice, b.low);
    maxPrice = Math.max(maxPrice, b.high);
    maxVol = Math.max(maxVol, b.volume);
  });

  const priceRange = (maxPrice - minPrice) || 1;
  const padding = priceRange * 0.1;
  const adjustedMin = minPrice - padding;
  const adjustedMax = maxPrice + padding;
  const adjustedRange = adjustedMax - adjustedMin;

  function getY(p) {
    return chartHeight - ((p - adjustedMin) / adjustedRange) * chartHeight;
  }

  // Draw Grid Lines
  ctx.strokeStyle = '#151c28';
  ctx.lineWidth = 1;
  for (let i = 1; i <= 4; i++) {
    const gy = (chartHeight / 5) * i;
    ctx.beginPath();
    ctx.moveTo(0, gy);
    ctx.lineTo(width - 70, gy);
    ctx.stroke();

    const gPrice = adjustedMax - (adjustedRange / 5) * i;
    ctx.fillStyle = '#64748b';
    ctx.font = '10px "JetBrains Mono"';
    ctx.fillText(`₹${gPrice.toFixed(1)}`, width - 65, gy + 3);
  }

  // Draw Support & Resistance
  if (state.showSR) {
    const assetKey = state.currentSymbol === 'NIFTY' ? 'NIFTY 50 INDEX' : 'BANK NIFTY INDEX';
    const asset = state.marketStates[assetKey];
    if (asset) {
      const rY = getY(asset.resistance);
      ctx.strokeStyle = 'rgba(255, 51, 102, 0.4)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, rY);
      ctx.lineTo(width - 70, rY);
      ctx.stroke();
      ctx.fillStyle = 'var(--bearish)';
      ctx.fillText(`R1: ${asset.resistance}`, 10, rY - 4);

      const sY = getY(asset.support);
      ctx.strokeStyle = 'rgba(0, 242, 169, 0.4)';
      ctx.beginPath();
      ctx.moveTo(0, sY);
      ctx.lineTo(width - 70, sY);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = 'var(--bullish)';
      ctx.fillText(`S1: ${asset.support}`, 10, sY - 4);
    }
  }

  // Draw Candlesticks & Volumes
  bars.forEach((b, i) => {
    const x = i * barWidth + 10;
    const isBullish = b.close >= b.open;
    const color = isBullish ? '#00f2a9' : '#ff3366';

    const yOpen = getY(b.open);
    const yClose = getY(b.close);
    const yHigh = getY(b.high);
    const yLow = getY(b.low);

    // Wick
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(x + (barWidth - candleGap) / 2, yHigh);
    ctx.lineTo(x + (barWidth - candleGap) / 2, yLow);
    ctx.stroke();

    // Body
    ctx.fillStyle = color;
    const bodyTop = Math.min(yOpen, yClose);
    const bodyHeight = Math.max(2, Math.abs(yClose - yOpen));
    ctx.fillRect(x, bodyTop, barWidth - candleGap, bodyHeight);

    // Volume Bar
    const vY = height - ((b.volume / (maxVol || 1)) * volumeHeight);
    ctx.fillStyle = isBullish ? 'rgba(0, 242, 169, 0.25)' : 'rgba(255, 51, 102, 0.25)';
    ctx.fillRect(x, vY, barWidth - candleGap, height - vY);
  });

  // Draw EMA 9 & 21
  if (state.showEMA && count > 5) {
    drawEMA(bars, 9, '#38bdf8', barWidth, candleGap, getY);
    drawEMA(bars, 21, '#a855f7', barWidth, candleGap, getY);
  }
}

function drawEMA(bars, period, color, barWidth, candleGap, getY) {
  const k = 2 / (period + 1);
  let ema = bars[0].close;
  const points = [];

  bars.forEach((b, i) => {
    ema = (b.close * k) + (ema * (1 - k));
    const x = i * barWidth + 10 + (barWidth - candleGap) / 2;
    const y = getY(ema);
    points.push({ x, y });
  });

  ctx.strokeStyle = color;
  ctx.lineWidth = 1.8;
  ctx.beginPath();
  points.forEach((pt, i) => {
    if (i === 0) ctx.moveTo(pt.x, pt.y);
    else ctx.lineTo(pt.x, pt.y);
  });
  ctx.stroke();
}

function handleChartMouseMove(mouseX, mouseY) {
  const bars = state.chartBars.slice(-60);
  const width = canvas.width / window.devicePixelRatio;
  const barWidth = Math.max(4, (width - 80) / bars.length);
  
  const idx = Math.floor((mouseX - 10) / barWidth);
  if (idx >= 0 && idx < bars.length) {
    const bar = bars[idx];
    const tooltip = document.getElementById('chart-tooltip');
    tooltip.classList.remove('hidden');
    
    document.getElementById('tt-time').innerText = new Date(bar.time * 1000).toLocaleTimeString();
    document.getElementById('tt-open').innerText = bar.open.toFixed(2);
    document.getElementById('tt-high').innerText = bar.high.toFixed(2);
    document.getElementById('tt-low').innerText = bar.low.toFixed(2);
    document.getElementById('tt-close').innerText = bar.close.toFixed(2);
    document.getElementById('tt-vol').innerText = bar.volume.toLocaleString('en-IN');
  }
}

// ================= AUDIO & TOAST NOTIFICATIONS =================
function playAudioChime() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    
    osc.type = 'sine';
    osc.frequency.setValueAtTime(587.33, audioCtx.currentTime); // D5
    osc.frequency.exponentialRampToValueAtTime(880.00, audioCtx.currentTime + 0.15); // A5
    
    gain.gain.setValueAtTime(0.15, audioCtx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.01, audioCtx.currentTime + 0.3);
    
    osc.connect(gain);
    gain.connect(audioCtx.destination);
    
    osc.start();
    osc.stop(audioCtx.currentTime + 0.3);
  } catch (e) {
    // audio not supported or blocked
  }
}

function showToast(msg, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<i class="fa-solid ${type === 'success' ? 'fa-circle-check' : 'fa-triangle-exclamation'}"></i> ${msg}`;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
