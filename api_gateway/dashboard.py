"""
Web UI — Younify Dashboard
===========================
Single-page application served directly by FastAPI.
No build step, no node_modules, no framework needed.

Just vanilla HTML + CSS + JS that hits /api/v1/* endpoints.
"""

DASHBOARD_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="Younify is a distributed, high-performance AI inference system utilizing networked computing nodes for parallel model processing.">
  <title>Younify — Distributed AI Inference Platform</title>
  
  <!-- Fonts -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap" rel="stylesheet">
  
  <!-- Icons -->
  <script src="https://unpkg.com/lucide@latest"></script>
  
  <!-- Charts.js -->
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>

  <style>
    /* ── Design System & Variables ────────────────────────────────────── */
    :root {
      --bg: #060609;
      --bg-gradient: radial-gradient(circle at 50% -20%, #1e1b4b 0%, #060609 75%);
      --surface: rgba(15, 15, 23, 0.7);
      --surface-hover: rgba(25, 25, 38, 0.8);
      --surface-active: rgba(35, 35, 50, 0.95);
      --border: rgba(255, 255, 255, 0.08);
      --border-glow: rgba(99, 102, 241, 0.25);
      
      --text-primary: #f8fafc;
      --text-secondary: #94a3b8;
      --text-muted: #64748b;
      
      --accent-hsl: 245, 82%, 65%;
      --accent: hsl(var(--accent-hsl));
      --accent-hover: hsl(245, 82%, 58%);
      --accent-glow: rgba(99, 102, 241, 0.4);
      --accent-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
      
      --success: #10b981;
      --success-glow: rgba(16, 185, 129, 0.15);
      --warning: #f59e0b;
      --warning-glow: rgba(245, 158, 11, 0.15);
      --danger: #ef4444;
      --danger-glow: rgba(239, 68, 68, 0.15);
      
      --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      --font-title: 'Outfit', sans-serif;
      --font-mono: 'Fira Code', 'JetBrains Mono', monospace;
      
      --radius-sm: 8px;
      --radius-md: 14px;
      --radius-lg: 20px;
      
      --sidebar-width: 280px;
      --transition-speed: 0.25s;
      --ease: cubic-bezier(0.4, 0, 0.2, 1);
    }

    /* ── Base Styles ─────────────────────────────────────────────────── */
    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }
    
    body {
      font-family: var(--font-sans);
      background: var(--bg);
      background-image: var(--bg-gradient);
      color: var(--text-primary);
      line-height: 1.6;
      min-height: 100vh;
      overflow-x: hidden;
      display: flex;
    }

    /* ── Custom Scrollbar ────────────────────────────────────────────── */
    ::-webkit-scrollbar {
      width: 8px;
      height: 8px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(0, 0, 0, 0.2);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(255, 255, 255, 0.1);
      border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: rgba(255, 255, 255, 0.2);
    }

    /* ── Sidebar Layout ─────────────────────────────────────────────── */
    aside {
      width: var(--sidebar-width);
      height: 100vh;
      position: fixed;
      left: 0;
      top: 0;
      background: rgba(8, 8, 12, 0.7);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border-right: 1px solid var(--border);
      padding: 32px 24px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      z-index: 100;
      transition: transform var(--transition-speed) var(--ease);
    }

    .brand-logo {
      display: flex;
      align-items: center;
      gap: 12px;
      text-decoration: none;
      margin-bottom: 40px;
    }

    .brand-logo svg {
      width: 32px;
      height: 32px;
      stroke: url(#brand-gradient);
      filter: drop-shadow(0 0 8px rgba(99, 102, 241, 0.5));
    }

    .brand-logo h1 {
      font-family: var(--font-title);
      font-size: 1.6rem;
      font-weight: 800;
      background: var(--accent-gradient);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      letter-spacing: -0.02em;
    }

    .nav-menu {
      display: flex;
      flex-direction: column;
      gap: 8px;
      flex-grow: 1;
    }

    .nav-item {
      display: flex;
      align-items: center;
      gap: 14px;
      padding: 12px 16px;
      border-radius: var(--radius-sm);
      color: var(--text-secondary);
      text-decoration: none;
      font-weight: 500;
      font-size: 0.95rem;
      cursor: pointer;
      border: 1px solid transparent;
      transition: all var(--transition-speed) var(--ease);
    }

    .nav-item:hover {
      color: var(--text-primary);
      background: var(--surface-hover);
      border-color: var(--border);
    }

    .nav-item.active {
      color: var(--text-primary);
      background: var(--accent-glow);
      border-color: var(--border-glow);
      box-shadow: inset 0 0 12px rgba(99, 102, 241, 0.15);
    }

    .nav-item i {
      width: 18px;
      height: 18px;
    }

    .sidebar-footer {
      border-top: 1px solid var(--border);
      padding-top: 24px;
      display: flex;
      flex-direction: column;
      gap: 16px;
    }

    .status-panel {
      font-size: 0.8rem;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .status-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-secondary);
    }

    .status-dot-container {
      display: flex;
      align-items: center;
      gap: 6px;
      font-weight: 600;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      box-shadow: 0 0 8px currentColor;
    }

    .status-dot.active {
      background-color: var(--success);
      color: var(--success);
    }

    .status-dot.inactive {
      background-color: var(--danger);
      color: var(--danger);
    }

    .status-dot.checking {
      background-color: var(--warning);
      color: var(--warning);
      animation: pulse 1.5s infinite;
    }

    /* ── Main Layout ────────────────────────────────────────────────── */
    main {
      flex-grow: 1;
      margin-left: var(--sidebar-width);
      min-height: 100vh;
      padding: 40px 48px;
      display: flex;
      flex-direction: column;
      max-width: 1300px;
      transition: margin var(--transition-speed) var(--ease);
    }

    header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 36px;
    }

    .header-title h2 {
      font-family: var(--font-title);
      font-size: 2rem;
      font-weight: 700;
      letter-spacing: -0.01em;
      margin-bottom: 4px;
    }

    .header-title p {
      color: var(--text-secondary);
      font-size: 0.95rem;
    }

    .header-actions {
      display: flex;
      gap: 12px;
    }

    /* ── Buttons ────────────────────────────────────────────────────── */
    .btn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      padding: 10px 20px;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      font-weight: 600;
      cursor: pointer;
      border: 1px solid transparent;
      color: var(--text-primary);
      background: var(--surface-hover);
      border-color: var(--border);
      transition: all var(--transition-speed) var(--ease);
    }

    .btn:hover {
      background: var(--surface-active);
      border-color: var(--text-muted);
    }

    .btn-primary {
      background: var(--accent-gradient);
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
      border: none;
    }

    .btn-primary:hover {
      opacity: 0.9;
      transform: translateY(-1px);
      box-shadow: 0 6px 20px rgba(99, 102, 241, 0.45);
    }

    .btn-primary:active {
      transform: translateY(0);
    }

    .btn:disabled {
      opacity: 0.5;
      cursor: not-allowed;
      transform: none !important;
      box-shadow: none !important;
    }

    /* ── Cards & Panels ──────────────────────────────────────────────── */
    .panel {
      display: none;
      animation: fadeIn var(--transition-speed) var(--ease);
    }

    .panel.active {
      display: block;
    }

    .card {
      background: var(--surface);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 24px;
      margin-bottom: 24px;
      position: relative;
      overflow: hidden;
      transition: border-color var(--transition-speed) var(--ease), box-shadow var(--transition-speed) var(--ease);
    }

    .card:hover {
      border-color: rgba(255, 255, 255, 0.12);
    }

    .card.glow-hover:hover {
      border-color: var(--border-glow);
      box-shadow: 0 0 25px rgba(99, 102, 241, 0.08);
    }

    .card h3 {
      font-family: var(--font-title);
      font-size: 1.2rem;
      font-weight: 600;
      margin-bottom: 20px;
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .card h3 i {
      color: var(--accent);
      width: 20px;
      height: 20px;
    }

    /* ── Dashboard Stats ─────────────────────────────────────────────── */
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .stat-card {
      display: flex;
      align-items: center;
      gap: 20px;
    }

    .stat-icon {
      width: 48px;
      height: 48px;
      border-radius: var(--radius-sm);
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid var(--border);
      display: flex;
      align-items: center;
      justify-content: center;
      color: var(--accent);
    }

    .stat-card:hover .stat-icon {
      background: var(--accent-glow);
      border-color: var(--border-glow);
      color: var(--text-primary);
    }

    .stat-info {
      display: flex;
      flex-direction: column;
    }

    .stat-label {
      font-size: 0.8rem;
      color: var(--text-secondary);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .stat-value {
      font-family: var(--font-title);
      font-size: 1.8rem;
      font-weight: 700;
      line-height: 1.2;
      margin-top: 4px;
    }

    /* ── Analytics Charts ───────────────────────────────────────────── */
    .charts-grid {
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 24px;
      margin-bottom: 30px;
    }

    @media (max-width: 1000px) {
      .charts-grid {
        grid-template-columns: 1fr;
      }
    }

    .chart-container {
      position: relative;
      height: 280px;
      width: 100%;
    }

    /* ── Form Design ─────────────────────────────────────────────────── */
    .form-row {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
      margin-bottom: 20px;
    }

    .form-group {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .form-group.full-width {
      grid-column: 1 / -1;
    }

    label {
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-secondary);
    }

    input[type="text"],
    input[type="number"],
    input[type="password"],
    select,
    textarea {
      background: rgba(0, 0, 0, 0.3);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 0.95rem;
      outline: none;
      transition: all var(--transition-speed) var(--ease);
    }

    input:focus,
    select:focus,
    textarea:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 2px var(--accent-glow);
      background: rgba(0, 0, 0, 0.45);
    }

    textarea {
      min-height: 140px;
      resize: vertical;
    }

    /* Range Slider Styling */
    .slider-container {
      display: flex;
      align-items: center;
      gap: 16px;
    }

    .slider-container input[type="range"] {
      flex-grow: 1;
      accent-color: var(--accent);
      height: 6px;
      border-radius: 3px;
      outline: none;
      cursor: pointer;
    }

    .slider-value {
      font-family: var(--font-mono);
      font-size: 0.9rem;
      font-weight: 600;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: var(--radius-sm);
      min-width: 45px;
      text-align: center;
    }

    /* Password field wrapper with eye toggle */
    .pw-field-wrap {
      position: relative;
      display: flex;
      align-items: center;
    }
    .pw-field-wrap input[type="password"],
    .pw-field-wrap input[type="text"] {
      width: 100%;
      padding-right: 44px;
      box-sizing: border-box;
    }
    .pw-toggle {
      position: absolute;
      right: 12px;
      background: none;
      border: none;
      cursor: pointer;
      color: var(--text-muted);
      display: flex;
      align-items: center;
      padding: 0;
      transition: color var(--transition-speed) var(--ease);
    }
    .pw-toggle:hover { color: var(--text-primary); }
    .pw-toggle svg { width: 16px; height: 16px; }

    /* Settings panel layout */
    .settings-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    @media (max-width: 700px) { .settings-grid { grid-template-columns: 1fr; } }
    .settings-notice {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 14px 18px;
      background: rgba(99,102,241,0.08);
      border: 1px solid rgba(99,102,241,0.25);
      border-radius: var(--radius-sm);
      margin-bottom: 24px;
    }
    .settings-notice svg { flex-shrink: 0; color: var(--accent); margin-top: 2px; }
    .settings-notice p { font-size: 0.82rem; color: var(--text-secondary); margin: 0; line-height: 1.55; }
    .settings-notice strong { color: var(--text-primary); }

    /* ── Chat Panel ─────────────────────────────────────────────────── */
    #panel-chat {
      display: none;
      flex-direction: column;
      height: calc(100vh - 80px);
      overflow: hidden;
    }
    #panel-chat.active {
      display: flex;
    }
    .chat-layout {
      display: flex;
      flex-direction: column;
      height: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      overflow: hidden;
    }
    .chat-toolbar {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      background: rgba(0,0,0,0.25);
      flex-shrink: 0;
      flex-wrap: wrap;
    }
    .chat-toolbar label { font-size:0.8rem; color:var(--text-secondary); white-space:nowrap; }
    .chat-toolbar select {
      background: rgba(0,0,0,0.4);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 6px 10px;
      color: var(--text-primary);
      font-size: 0.85rem;
      cursor: pointer;
      outline: none;
    }
    .chat-param {
      display: flex;
      align-items: center;
      gap: 8px;
      font-size: 0.8rem;
      color: var(--text-secondary);
    }
    .chat-param input[type="range"] {
      width: 80px;
      accent-color: var(--accent);
      cursor: pointer;
    }
    .chat-param span {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      min-width: 30px;
      color: var(--text-primary);
    }
    .chat-clear-btn {
      margin-left: auto;
      background: none;
      border: 1px solid var(--border);
      color: var(--text-muted);
      border-radius: var(--radius-sm);
      padding: 5px 10px;
      font-size: 0.78rem;
      cursor: pointer;
      transition: all var(--transition-speed) var(--ease);
      display: flex;
      align-items: center;
      gap: 5px;
    }
    .chat-clear-btn:hover { color: var(--danger); border-color: var(--danger); background: rgba(239,68,68,0.08); }
    .chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 24px 20px;
      display: flex;
      flex-direction: column;
      gap: 18px;
      scroll-behavior: smooth;
    }
    .chat-messages::-webkit-scrollbar { width: 5px; }
    .chat-messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
    .chat-bubble-wrap {
      display: flex;
      align-items: flex-end;
      gap: 10px;
      max-width: 82%;
      animation: fadeIn 0.25s ease;
    }
    .chat-bubble-wrap.user { align-self: flex-end; flex-direction: row-reverse; }
    .chat-bubble-wrap.assistant { align-self: flex-start; }
    .chat-avatar {
      width: 30px;
      height: 30px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      font-size: 0.75rem;
      font-weight: 700;
    }
    .chat-avatar.user-avatar {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      color: #fff;
    }
    .chat-avatar.model-avatar {
      background: rgba(255,255,255,0.07);
      border: 1px solid var(--border);
      color: var(--text-secondary);
    }
    .chat-bubble {
      padding: 12px 16px;
      border-radius: 16px;
      font-size: 0.92rem;
      line-height: 1.65;
      max-width: 100%;
      word-break: break-word;
    }
    .chat-bubble.user {
      background: linear-gradient(135deg, rgba(99,102,241,0.6), rgba(168,85,247,0.5));
      border: 1px solid rgba(99,102,241,0.4);
      border-bottom-right-radius: 4px;
      color: #fff;
    }
    .chat-bubble.assistant {
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-bottom-left-radius: 4px;
      color: var(--text-primary);
      white-space: pre-wrap;
    }
    .chat-bubble.error {
      background: rgba(239,68,68,0.08);
      border: 1px solid rgba(239,68,68,0.3);
      color: var(--danger);
    }
    .chat-meta {
      font-size: 0.7rem;
      color: var(--text-muted);
      margin-top: 5px;
      padding: 0 4px;
    }
    .chat-bubble-wrap.user .chat-meta { text-align: right; }
    /* Typing indicator */
    .typing-indicator {
      display: flex;
      align-items: center;
      gap: 5px;
      padding: 12px 16px;
      background: rgba(255,255,255,0.04);
      border: 1px solid var(--border);
      border-radius: 16px;
      border-bottom-left-radius: 4px;
      width: fit-content;
    }
    .typing-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--text-muted);
      animation: typingBounce 1.2s infinite ease-in-out;
    }
    .typing-dot:nth-child(2) { animation-delay: 0.2s; }
    .typing-dot:nth-child(3) { animation-delay: 0.4s; }
    @keyframes typingBounce {
      0%, 80%, 100% { transform: translateY(0); opacity: 0.4; }
      40% { transform: translateY(-5px); opacity: 1; }
    }
    /* Chat input bar */
    .chat-input-bar {
      display: flex;
      align-items: flex-end;
      gap: 12px;
      padding: 16px 20px;
      border-top: 1px solid var(--border);
      background: rgba(0,0,0,0.2);
      flex-shrink: 0;
    }
    #chat-input {
      flex: 1;
      background: rgba(0,0,0,0.3);
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px 16px;
      color: var(--text-primary);
      font-family: var(--font-sans);
      font-size: 0.95rem;
      resize: none;
      outline: none;
      min-height: 44px;
      max-height: 160px;
      overflow-y: auto;
      transition: border-color var(--transition-speed) var(--ease);
      line-height: 1.5;
    }
    #chat-input:focus { border-color: rgba(99,102,241,0.5); }
    #chat-send-btn {
      width: 44px;
      height: 44px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      border: none;
      color: #fff;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      transition: all var(--transition-speed) var(--ease);
      box-shadow: 0 0 16px rgba(99,102,241,0.35);
    }
    #chat-send-btn:hover:not(:disabled) { transform: scale(1.08); box-shadow: 0 0 24px rgba(99,102,241,0.55); }
    #chat-send-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }
    #chat-send-btn svg { width: 18px; height: 18px; }
    .chat-empty-state {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      flex: 1;
      gap: 12px;
      color: var(--text-muted);
      text-align: center;
      padding: 40px 20px;
    }
    .chat-empty-state svg { opacity: 0.2; width: 56px; height: 56px; }
    .chat-empty-state h4 { font-size: 1rem; color: var(--text-secondary); margin: 0; }
    .chat-empty-state p  { font-size: 0.82rem; margin: 0; }

    /* Presets list */
    .presets-container {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }

    .preset-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      cursor: pointer;
      display: flex;
      align-items: flex-start;
      gap: 12px;
      transition: all var(--transition-speed) var(--ease);
    }

    .preset-card:hover {
      background: var(--surface-hover);
      border-color: var(--border-glow);
      transform: translateX(4px);
    }

    .preset-card i {
      color: var(--accent);
      margin-top: 3px;
      width: 16px;
      height: 16px;
    }

    .preset-details h4 {
      font-size: 0.9rem;
      font-weight: 600;
      margin-bottom: 2px;
    }

    .preset-details p {
      font-size: 0.75rem;
      color: var(--text-secondary);
      line-height: 1.4;
    }

    /* ── Jobs Log & History ──────────────────────────────────────────── */
    .filters-bar {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 16px;
      margin-bottom: 20px;
      flex-wrap: wrap;
    }

    .search-box {
      position: relative;
      flex-grow: 1;
      max-width: 400px;
    }

    .search-box input {
      width: 100%;
      padding-left: 44px;
    }

    .search-box i {
      position: absolute;
      left: 16px;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      width: 18px;
      height: 18px;
    }

    .filter-tabs {
      display: flex;
      background: rgba(255, 255, 255, 0.03);
      padding: 4px;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
    }

    .filter-tab {
      padding: 6px 14px;
      border-radius: 4px;
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--text-secondary);
      border: none;
      background: transparent;
      cursor: pointer;
      transition: all var(--transition-speed) var(--ease);
    }

    .filter-tab.active {
      background: var(--accent);
      color: #fff;
    }

    .jobs-table-container {
      overflow-x: auto;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: rgba(0, 0, 0, 0.2);
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.9rem;
    }

    th {
      background: rgba(255, 255, 255, 0.02);
      border-bottom: 1px solid var(--border);
      padding: 14px 20px;
      font-weight: 600;
      color: var(--text-secondary);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    td {
      padding: 16px 20px;
      border-bottom: 1px solid var(--border);
      color: var(--text-primary);
      vertical-align: middle;
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background: rgba(255, 255, 255, 0.015);
      cursor: pointer;
    }

    .job-id-cell {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      color: var(--accent);
    }

    .prompt-cell {
      max-width: 250px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .badge-status {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 99px;
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      border: 1px solid transparent;
    }

    .badge-QUEUED {
      background: rgba(99, 102, 241, 0.1);
      border-color: rgba(99, 102, 241, 0.3);
      color: #a5b4fc;
    }

    .badge-PROCESSING {
      background: rgba(245, 158, 11, 0.1);
      border-color: rgba(245, 158, 11, 0.3);
      color: #fde047;
    }

    .badge-COMPLETED {
      background: rgba(16, 185, 129, 0.1);
      border-color: rgba(16, 185, 129, 0.3);
      color: #6ee7b7;
    }

    .badge-FAILED {
      background: rgba(239, 68, 68, 0.1);
      border-color: rgba(239, 68, 68, 0.3);
      color: #fca5a5;
    }

    /* ── Cluster Topology Map ───────────────────────────────────────── */
    .nodes-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }

    .node-card {
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      background: rgba(255, 255, 255, 0.02);
      padding: 20px;
      display: flex;
      flex-direction: column;
      gap: 16px;
      position: relative;
    }

    .node-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .node-title-group {
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .node-title-group i {
      color: var(--accent);
    }

    .node-name {
      font-weight: 600;
      font-size: 0.95rem;
    }

    .node-role {
      font-size: 0.75rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .node-status-glow {
      position: absolute;
      top: 0;
      right: 0;
      width: 100px;
      height: 100px;
      background: radial-gradient(circle at 100% 0%, var(--accent-glow) 0%, transparent 70%);
      pointer-events: none;
    }

    .node-info-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 0.8rem;
    }

    .node-info-item {
      display: flex;
      justify-content: space-between;
      color: var(--text-secondary);
    }

    .node-info-item span:first-child {
      color: var(--text-muted);
    }

    .tag-container {
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
      margin-top: 4px;
    }

    .node-tag {
      font-size: 0.7rem;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      padding: 2px 8px;
      border-radius: 4px;
      color: var(--text-secondary);
    }

    /* ── Slide-Out Inspect Drawer ───────────────────────────────────── */
    .drawer {
      position: fixed;
      right: -550px;
      top: 0;
      width: 500px;
      max-width: 90vw;
      height: 100vh;
      background: rgba(10, 10, 15, 0.85);
      backdrop-filter: blur(25px);
      -webkit-backdrop-filter: blur(25px);
      border-left: 1px solid var(--border);
      z-index: 200;
      box-shadow: -10px 0 40px rgba(0, 0, 0, 0.5);
      transition: right var(--transition-speed) var(--ease);
      display: flex;
      flex-direction: column;
    }

    .drawer.open {
      right: 0;
    }

    .drawer-header {
      padding: 24px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .drawer-header h3 {
      font-family: var(--font-title);
      font-size: 1.3rem;
      font-weight: 700;
    }

    .drawer-close {
      cursor: pointer;
      background: none;
      border: none;
      color: var(--text-secondary);
      transition: color 0.2s;
    }

    .drawer-close:hover {
      color: var(--text-primary);
    }

    .drawer-content {
      padding: 24px;
      overflow-y: auto;
      flex-grow: 1;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .detail-group {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .detail-label {
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
      font-weight: 700;
    }

    .detail-value {
      font-size: 0.95rem;
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      word-break: break-word;
    }

    .detail-value-pre {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      white-space: pre-wrap;
      max-height: 250px;
      overflow-y: auto;
      background: rgba(0, 0, 0, 0.4);
    }

    .performance-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 12px;
    }

    /* ── Toast Notifications ────────────────────────────────────────── */
    #toast-container {
      position: fixed;
      bottom: 24px;
      right: 24px;
      display: flex;
      flex-direction: column;
      gap: 10px;
      z-index: 1000;
    }

    .toast {
      background: rgba(15, 15, 23, 0.9);
      backdrop-filter: blur(8px);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 20px;
      color: var(--text-primary);
      display: flex;
      align-items: center;
      gap: 12px;
      box-shadow: 0 4px 12px rgba(0,0,0,0.3);
      min-width: 250px;
      transform: translateY(100px);
      opacity: 0;
      animation: toastIn 0.3s forwards var(--ease);
    }

    .toast-success { border-left: 4px solid var(--success); }
    .toast-error { border-left: 4px solid var(--danger); }
    .toast-info { border-left: 4px solid var(--accent); }

    /* ── Keyframe Animations ────────────────────────────────────────── */
    @keyframes fadeIn {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes toastIn {
      to { transform: translateY(0); opacity: 1; }
    }
    
    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.5; }
    }

    /* ── Responsive Adaptation ──────────────────────────────────────── */
    @media (max-width: 900px) {
      aside {
        transform: translateX(-100%);
        width: 240px;
      }
      
      aside.open {
        transform: translateX(0);
      }
      
      main {
        margin-left: 0;
        padding: 24px;
      }
      
      .hamburger-btn {
        display: flex !important;
      }
    }

    .hamburger-btn {
      display: none;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      width: 40px;
      height: 40px;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      color: var(--text-primary);
    }

    /* Background brand gradient helper */
    #svg-def-gradient {
      position: absolute;
      width: 0;
      height: 0;
    }
  </style>
</head>
<body>

  <!-- SVG Gradient definition for Lucide icons -->
  <svg id="svg-def-gradient">
    <defs>
      <linearGradient id="brand-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="#6366f1" />
        <stop offset="100%" stop-color="#ec4899" />
      </linearGradient>
    </defs>
  </svg>

  <!-- Sidebar Navigation -->
  <aside id="sidebar-nav">
    <div>
      <a href="#" class="brand-logo">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>
        </svg>
        <h1>Younify</h1>
      </a>
      
      <nav class="nav-menu">
        <div id="nav-dashboard" class="nav-item active" onclick="switchTab('dashboard')" role="button" tabindex="0">
          <i data-lucide="layout-dashboard"></i>
          <span>Dashboard</span>
        </div>
        <div id="nav-chat" class="nav-item" onclick="switchTab('chat')" role="button" tabindex="0">
          <i data-lucide="message-square"></i>
          <span>Chat</span>
        </div>

        <div id="nav-jobs" class="nav-item" onclick="switchTab('jobs')" role="button" tabindex="0">
          <i data-lucide="history"></i>
          <span>Jobs History</span>
        </div>
        <div id="nav-cluster" class="nav-item" onclick="switchTab('cluster')" role="button" tabindex="0">
          <i data-lucide="server"></i>
          <span>Cluster Topology</span>
        </div>
        <div id="nav-settings" class="nav-item" onclick="switchTab('settings')" role="button" tabindex="0">
          <i data-lucide="key-round"></i>
          <span>Settings</span>
        </div>
      </nav>
    </div>

    <div class="sidebar-footer">
      <div class="status-panel">
        <div class="status-row">
          <span>Gateway API</span>
          <span class="status-dot-container">
            <span id="gateway-status-dot" class="status-dot checking"></span>
            <span id="gateway-status-text">Checking...</span>
          </span>
        </div>
        <div class="status-row">
          <span>Redis Broker</span>
          <span class="status-dot-container">
            <span id="redis-status-dot" class="status-dot checking"></span>
            <span id="redis-status-text">Checking...</span>
          </span>
        </div>
      </div>
      <button class="btn" id="btn-sync" onclick="syncAllJobs()" title="Synchronize job states with API">
        <i data-lucide="refresh-cw"></i> Sync Cluster
      </button>
    </div>
  </aside>

  <!-- Mobile Overlay for Sidebar -->
  <div id="sidebar-overlay" onclick="toggleMobileSidebar()" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.6); z-index:90;"></div>

  <!-- Main Container -->
  <main>
    
    <!-- Topbar / Header -->
    <header>
      <div style="display:flex; align-items:center; gap:16px;">
        <button class="hamburger-btn" onclick="toggleMobileSidebar()" aria-label="Toggle Navigation">
          <i data-lucide="menu"></i>
        </button>
        <div class="header-title">
          <h2 id="view-title">Dashboard</h2>
          <p id="view-subtitle">Real-time distributed system metrics</p>
        </div>
      </div>
      
      <div class="header-actions">
        <button class="btn" onclick="location.reload()" aria-label="Reload Dashboard">
          <i data-lucide="rotate-cw"></i> Reload
        </button>
      </div>
    </header>

    <!-- ────────────────── PANEL 1: DASHBOARD ────────────────── -->
    <div id="panel-dashboard" class="panel active">
      <div class="stats-grid">
        <div class="card stat-card glow-hover">
          <div class="stat-icon"><i data-lucide="activity"></i></div>
          <div class="stat-info">
            <span class="stat-label">Total Submissions</span>
            <span class="stat-value" id="stat-total-jobs">0</span>
          </div>
        </div>
        <div class="card stat-card glow-hover">
          <div class="stat-icon"><i data-lucide="hourglass"></i></div>
          <div class="stat-info">
            <span class="stat-label">Active Tasks</span>
            <span class="stat-value" id="stat-active-jobs">0</span>
          </div>
        </div>
        <div class="card stat-card glow-hover">
          <div class="stat-icon"><i data-lucide="check-circle2"></i></div>
          <div class="stat-info">
            <span class="stat-label">Successful Jobs</span>
            <span class="stat-value" id="stat-success-jobs">0</span>
          </div>
        </div>
        <div class="card stat-card glow-hover">
          <div class="stat-icon"><i data-lucide="zap"></i></div>
          <div class="stat-info">
            <span class="stat-label">Success Rate</span>
            <span class="stat-value" id="stat-success-rate">0%</span>
          </div>
        </div>
      </div>

      <div class="charts-grid">
        <div class="card">
          <h3><i data-lucide="trending-up"></i> Job Inference Volume</h3>
          <div class="chart-container">
            <canvas id="chart-volume"></canvas>
          </div>
        </div>
        <div class="card">
          <h3><i data-lucide="pie-chart"></i> Status Distribution</h3>
          <div class="chart-container">
            <canvas id="chart-statuses"></canvas>
          </div>
        </div>
      </div>

      <div class="card">
        <h3><i data-lucide="align-left"></i> Recent Activity Feed</h3>
        <div class="jobs-table-container">
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Model</th>
                <th>Prompt Preview</th>
                <th>Status</th>
                <th>Submitted</th>
              </tr>
            </thead>
            <tbody id="dashboard-recent-jobs">
              <tr>
                <td colspan="5" style="text-align:center; color:var(--text-muted); padding:32px;">
                  No jobs logged in this session yet. Submit one!
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ────────────────── PANEL 3: JOBS HISTORY ────────────────── -->
    <div id="panel-jobs" class="panel">
      <div class="card">
        <div class="filters-bar">
          <div class="search-box">
            <i data-lucide="search"></i>
            <input type="text" id="jobs-search-input" placeholder="Search by Job ID, model, or prompt..." oninput="renderJobsHistory()">
          </div>
          
          <div class="filter-tabs">
            <button class="filter-tab active" id="filter-all" onclick="setJobFilter('all')">All</button>
            <button class="filter-tab" id="filter-queued" onclick="setJobFilter('QUEUED')">Queued</button>
            <button class="filter-tab" id="filter-processing" onclick="setJobFilter('PROCESSING')">Running</button>
            <button class="filter-tab" id="filter-completed" onclick="setJobFilter('COMPLETED')">Done</button>
            <button class="filter-tab" id="filter-failed" onclick="setJobFilter('FAILED')">Failed</button>
          </div>
          
          <div style="display:flex; gap:10px;">
            <button class="btn" onclick="syncAllJobs()"><i data-lucide="refresh-cw"></i> Refresh Status</button>
            <button class="btn" onclick="clearHistory()"><i data-lucide="x-circle"></i> Clear History</button>
          </div>
        </div>

        <div class="jobs-table-container">
          <table>
            <thead>
              <tr>
                <th>Job ID</th>
                <th>Model</th>
                <th>Prompt Context</th>
                <th>Status</th>
                <th>Time Incurred</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="jobs-history-list">
              <tr>
                <td colspan="6" style="text-align:center; color:var(--text-muted); padding:40px;">
                  No jobs found matching criteria.
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- ────────────────── PANEL 4: CLUSTER ────────────────── -->
    <div id="panel-cluster" class="panel">
      <div class="nodes-grid">
        <!-- Gateway Card -->
        <div class="node-card">
          <div class="node-status-glow"></div>
          <div class="node-header">
            <div class="node-title-group">
              <i data-lucide="shield"></i>
              <div>
                <div class="node-name">API Gateway</div>
                <div class="node-role">Central Broker Node</div>
              </div>
            </div>
            <span class="badge-status badge-COMPLETED">ONLINE</span>
          </div>
          <div class="node-info-list">
            <div class="node-info-item">
              <span>Host IP</span>
              <span id="cluster-gw-host">localhost</span>
            </div>
            <div class="node-info-item">
              <span>Service Engine</span>
              <span>FastAPI (Python)</span>
            </div>
            <div class="node-info-item">
              <span>Platform Version</span>
              <span id="cluster-gw-version">1.0.0</span>
            </div>
          </div>
        </div>

        <!-- Redis Broker Card -->
        <div class="node-card">
          <div class="node-status-glow"></div>
          <div class="node-header">
            <div class="node-title-group">
              <i data-lucide="database"></i>
              <div>
                <div class="node-name">Queue Broker</div>
                <div class="node-role">Redis Persistence</div>
              </div>
            </div>
            <span id="cluster-redis-badge" class="badge-status badge-QUEUED">CHECKING</span>
          </div>
          <div class="node-info-list">
            <div class="node-info-item">
              <span>Broker Engine</span>
              <span>Valkey / Redis 7+</span>
            </div>
            <div class="node-info-item">
              <span>Socket Port</span>
              <span>6379</span>
            </div>
            <div class="node-info-item">
              <span>DB Index</span>
              <span>0</span>
            </div>
          </div>
        </div>

        <!-- Cluster Coordinator Card -->
        <div class="node-card">
          <div class="node-status-glow"></div>
          <div class="node-header">
            <div class="node-title-group">
              <i data-lucide="server"></i>
              <div>
                <div class="node-name">Cluster Coordinator</div>
                <div class="node-role">Distributed Inference Orchestrator</div>
              </div>
            </div>
            <span id="cluster-coord-badge" class="badge-status badge-QUEUED">CHECKING</span>
          </div>
          <div class="node-info-list">
            <div class="node-info-item">
              <span>Coordinator Status</span>
              <span id="cluster-coord-status">Checking...</span>
            </div>
            <div class="node-info-item">
              <span>Cluster Workers</span>
              <span id="cluster-coord-workers">-</span>
            </div>
            <div class="node-info-item">
              <span>RPC Nodes</span>
              <span id="cluster-coord-rpc">-</span>
            </div>
          </div>
        </div>

        <!-- Active Worker Status Card -->
        <div class="node-card">
          <div class="node-status-glow"></div>
          <div class="node-header">
            <div class="node-title-group">
              <i data-lucide="cpu"></i>
              <div>
                <div class="node-name">System Workers</div>
                <div class="node-role">Inference Nodes</div>
              </div>
            </div>
            <span id="cluster-workers-badge" class="badge-status badge-COMPLETED">ACTIVE</span>
          </div>
          <div class="node-info-list">
            <div class="node-info-item">
              <span>Queue Status</span>
              <span id="cluster-broker-queue">Checking...</span>
            </div>
            <div class="node-info-item">
              <span>Workers Running</span>
              <span>1 Node (Local Daemon)</span>
            </div>
            <div class="node-info-item">
              <span>Node Hardware</span>
              <span>CPU/GPU Parallelized</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3><i data-lucide="package"></i> Installed Ollama Models</h3>
        <p style="font-size:0.85rem; color:var(--text-secondary); margin-bottom:16px;">
          The local worker has access to the following pre-downloaded LLMs via Ollama. You can submit jobs using these IDs.
        </p>
        <div class="tag-container" id="cluster-installed-models">
          <span style="color:var(--text-muted); font-size:0.85rem;">Scanning local Ollama registry...</span>
        </div>
        
        <div style="margin-top: 24px; padding: 16px; background: rgba(0, 0, 0, 0.2); border-radius: var(--radius-sm); border: 1px solid var(--border)">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
            <div>
              <h4 style="font-size:0.9rem; font-weight:600; margin-bottom:4px;">Want to add a model?</h4>
              <p style="font-size:0.75rem; color:var(--text-secondary);">
                Run the pull command on your worker host terminal. The list will update automatically.
              </p>
            </div>
            <div style="display:flex; gap:8px; align-items:center;">
              <code style="background:#000; padding:6px 12px; border-radius:4px; font-size:0.8rem; border:1px solid var(--border)">ollama pull tinyllama</code>
              <button class="btn" style="padding:6px 12px; font-size:0.8rem;" onclick="navigator.clipboard.writeText('ollama pull tinyllama'); showToast('Command copied to clipboard!', 'info')">
                <i data-lucide="copy" style="width:14px; height:14px;"></i> Copy
              </button>
            </div>
          </div>
        </div>
      </div>
      
      <div class="card">
        <h3><i data-lucide="network"></i> Supported Backend Integrations</h3>
        <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px;">
          <div style="padding:16px; background:rgba(255,255,255,0.01); border:1px solid var(--border); border-radius:var(--radius-sm)">
            <h4 style="font-size:0.9rem; margin-bottom:4px; font-weight:600; display:flex; align-items:center; gap:8px;"><span style="width:6px; height:6px; border-radius:50%; background:var(--success)"></span> Ollama</h4>
            <p style="font-size:0.75rem; color:var(--text-secondary)">Local inference. The default provider. Auto-discovers installed models.</p>
          </div>
          <div style="padding:16px; background:rgba(255,255,255,0.01); border:1px solid var(--border); border-radius:var(--radius-sm)">
            <h4 style="font-size:0.9rem; margin-bottom:4px; font-weight:600; display:flex; align-items:center; gap:8px;"><span style="width:6px; height:6px; border-radius:50%; background:#a855f7"></span> Cluster (Distributed)</h4>
            <p style="font-size:0.75rem; color:var(--text-secondary)">Pool VRAM across machines via Tailscale. Uses llama.cpp RPC to run models collaboratively.</p>
          </div>
        </div>
      </div>
    </div>

    <!-- ────────────────── PANEL 5: SETTINGS ────────────────── -->
    <div id="panel-settings" class="panel">

      <div class="card">
        <h3 style="margin-bottom:18px;"><i data-lucide="shield-check"></i> API Credentials</h3>

        <div class="settings-notice">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
          <p>
            <strong>Stored locally only.</strong> These keys are saved in your browser's <code>localStorage</code> and are <strong>never persisted on the server</strong>. They are injected only at the moment a job is dispatched, and only to the matching provider. Clearing your browser data will remove them.
          </p>
        </div>

        <div class="settings-notice" style="margin-bottom:18px;">
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>
          <p>
            Younify uses <strong>Ollama</strong> for local inference. No API keys needed.
            Install Ollama from <a href="https://ollama.com" target="_blank" rel="noopener" style="color:var(--accent)">ollama.com</a>
            and pull a model to get started.
          </p>
        </div>
      </div>

    </div>

    <!-- ─────────────────── PANEL 6: CHAT ─────────────────── -->
    <div id="panel-chat" class="panel">
      <div class="chat-layout">

        <!-- Toolbar: model selector + params -->
        <div class="chat-toolbar">
          <label for="chat-provider-select">Provider</label>
          <select id="chat-provider-select" onchange="chatProviderChange()">
            <option value="ollama">Ollama</option>
          </select>

          <label for="chat-model-select">Model</label>
          <select id="chat-model-select">
            <option value="">— loading —</option>
          </select>

          <button class="chat-clear-btn" onclick="clearChat()">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
            Clear chat
          </button>
        </div>

        <!-- Messages container -->
        <div class="chat-messages" id="chat-messages">
          <div class="chat-empty-state" id="chat-empty">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
            <h4>Start a conversation</h4>
            <p>Select a model above and type your message below.</p>
          </div>
        </div>

        <!-- Input bar -->
        <div class="chat-input-bar">
          <textarea id="chat-input" rows="1" placeholder="Type a message… (Shift+Enter for new line, Enter to send)"
                    onkeydown="chatKeyHandler(event)" oninput="autoResizeChatInput(this)"></textarea>
          <button id="chat-send-btn" onclick="sendChatMessage()" title="Send message">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
          </button>
        </div>

      </div>
    </div>

  </main>

  <!-- Slide-out Inspect Drawer -->
  <div id="drawer-inspect" class="drawer">
    <div class="drawer-header">
      <h3 id="drawer-job-title">Job Details</h3>
      <button class="drawer-close" onclick="closeInspectDrawer()" aria-label="Close details panel">
        <i data-lucide="x" style="width:24px; height:24px;"></i>
      </button>
    </div>
    
    <div class="drawer-content">
      <div class="detail-group">
        <span class="detail-label">Status Details</span>
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span id="drawer-status-badge" class="badge-status badge-QUEUED">QUEUED</span>
          <span id="drawer-time" style="font-size:0.8rem; color:var(--text-secondary)">—</span>
        </div>
      </div>

      <div class="detail-group">
        <span class="detail-label">Job UUID</span>
        <div class="detail-value" id="drawer-uuid" style="font-family:var(--font-mono); font-size:0.8rem; color:var(--accent);">—</div>
      </div>

      <div class="detail-group">
        <span class="detail-label">Model Target</span>
        <div class="detail-value" id="drawer-model">—</div>
      </div>

      <div class="detail-group">
        <span class="detail-label">Prompt Context Input</span>
        <div class="detail-value" id="drawer-prompt" style="max-height:150px; overflow-y:auto; white-space:pre-wrap;">—</div>
      </div>

      <div class="detail-group">
        <span class="detail-label">Model Inference Output</span>
        <div class="detail-value detail-value-pre" id="drawer-completion">—</div>
      </div>

      <div class="performance-grid">
        <div class="detail-group">
          <span class="detail-label">Prompt Tokens</span>
          <div class="detail-value" id="drawer-prompt-tokens" style="font-family:var(--font-mono)">0</div>
        </div>
        <div class="detail-group">
          <span class="detail-label">Generated Tokens</span>
          <div class="detail-value" id="drawer-completion-tokens" style="font-family:var(--font-mono)">0</div>
        </div>
      </div>

      <div style="display:flex; gap:12px; margin-top:16px;">
        <button class="btn btn-primary" style="flex-grow:1" id="drawer-copy-btn" onclick="copyDrawerCompletion()">
          <i data-lucide="copy"></i> Copy Output
        </button>
        <button class="btn" style="flex-grow:1" id="drawer-json-btn" onclick="toggleRawJson()">
          <i data-lucide="braces"></i> Toggle Raw JSON
        </button>
      </div>

      <div class="detail-group" id="drawer-raw-json-group" style="display:none;">
        <span class="detail-label">Raw Server Response</span>
        <div class="detail-value detail-value-pre" id="drawer-raw-json" style="max-height:200px; font-size:0.75rem;">—</div>
      </div>
    </div>
  </div>

  <!-- Toast Notification Container -->
  <div id="toast-container"></div>

  <!-- ── Script Interactivity ────────────────────────────────────────── -->
  <script>
    const API = '/api/v1';
    
    // Persistent job store (synchronized from localStorage on load)
    let jobs = {};
    let activeFilter = 'all';
    let pollIntervalId = null;
    
    // Chart instances
    let volumeChart = null;
    let statusesChart = null;

    /* ── Initializer ───────────────────────────────────────────────── */
    window.addEventListener('DOMContentLoaded', () => {
      // Initialize icons
      lucide.createIcons();
      
      // Load saved jobs
      try {
        const saved = localStorage.getItem('younify_jobs_history');
        if (saved) {
          jobs = JSON.parse(saved);
        }
      } catch (e) {
        console.error("Failed to load local storage jobs", e);
      }
      
      // Start services
      checkClusterHealth();
      
      // Initial stats & job list render
      updateDashboardStats();
      renderJobsHistory();
      initCharts();
      
      // Start polling status loop
      startPollingLoop();
      
      // Periodic health check (every 5 seconds)
      setInterval(checkClusterHealth, 5000);
    });

    /* ── Tab Navigation ────────────────────────────────────────────── */
    function switchTab(tabId) {
      // Hide all panels
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
      // Remove active class from nav
      document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
      
      // Activate selected panel
      document.getElementById('panel-' + tabId).classList.add('active');
      document.getElementById('nav-' + tabId).classList.add('active');
      
      // Close side inspect drawer
      closeInspectDrawer();
      
      // Update headings
      const viewTitle = document.getElementById('view-title');
      const viewSubtitle = document.getElementById('view-subtitle');
      
      if (tabId === 'dashboard') {
        viewTitle.innerText = "Dashboard";
        viewSubtitle.innerText = "Real-time distributed system metrics";
        updateDashboardStats();
        updateChartsData();
      } else if (tabId === 'jobs') {
        viewTitle.innerText = "Jobs History Log";
        viewSubtitle.innerText = "Audit queue contents and completed outputs";
        renderJobsHistory();
      } else if (tabId === 'cluster') {
        viewTitle.innerText = "Cluster Topology & Status";
        viewSubtitle.innerText = "View connected hardware and network nodes";
        renderClusterTopology();
      } else if (tabId === 'settings') {
        viewTitle.innerText = "API Credentials Settings";
        viewSubtitle.innerText = "Manage security keys stored locally on your device";
        loadApiKeysForm();
      } else if (tabId === 'chat') {
        viewTitle.innerText = "Chat";
        viewSubtitle.innerText = "Converse with any connected model in real-time";
        initChatPanel();
      }
      
      // Close mobile sidebar if open
      const sidebar = document.getElementById('sidebar-nav');
      if (sidebar.classList.contains('open')) {
        toggleMobileSidebar();
      }
      
      lucide.createIcons();
    }

    function toggleMobileSidebar() {
      const sidebar = document.getElementById('sidebar-nav');
      const overlay = document.getElementById('sidebar-overlay');
      if (sidebar.classList.contains('open')) {
        sidebar.classList.remove('open');
        overlay.style.display = 'none';
      } else {
        sidebar.classList.add('open');
        overlay.style.display = 'block';
      }
    }

    /* ── Toast Notifications ───────────────────────────────────────── */
    function showToast(message, type = 'info') {
      const container = document.getElementById('toast-container');
      const toast = document.createElement('div');
      toast.className = `toast toast-${type}`;
      
      let icon = 'info';
      if (type === 'success') icon = 'check-circle';
      if (type === 'error') icon = 'alert-triangle';
      
      toast.innerHTML = `<i data-lucide="${icon}"></i> <span>${message}</span>`;
      container.appendChild(toast);
      lucide.createIcons();
      
      // Auto-dismiss
      setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s forwards var(--ease)';
        setTimeout(() => toast.remove(), 300);
      }, 3500);
    }

    /* ── Poll & Sync Management ────────────────────────────────────── */
    function persistJobs() {
      localStorage.setItem('younify_jobs_history', JSON.stringify(jobs));
    }

    function startPollingLoop() {
      if (pollIntervalId) clearInterval(pollIntervalId);
      
      // Adapt speed of poll dynamically. 
      // If there are active tasks, check every 1.5 seconds. If none, check every 6 seconds.
      const runPoll = async () => {
        const activeCount = Object.values(jobs).filter(j => j.status === 'QUEUED' || j.status === 'PROCESSING').length;
        await pollActiveJobs();
        
        const nextInterval = activeCount > 0 ? 1500 : 6000;
        setTimeout(runPoll, nextInterval);
      };
      
      setTimeout(runPoll, 1000);
    }

    async function pollActiveJobs() {
      const activeJobs = Object.values(jobs).filter(j => j.status === 'QUEUED' || j.status === 'PROCESSING');
      if (activeJobs.length === 0) return;
      
      let changed = false;
      for (const job of activeJobs) {
        try {
          const response = await fetch(`${API}/status/${job.job_id}`);
          if (response.ok) {
            const data = await response.json();
            
            // If status changed
            if (jobs[job.job_id].status !== data.status || JSON.stringify(jobs[job.job_id].result) !== JSON.stringify(data.result)) {
              jobs[job.job_id].status = data.status;
              jobs[job.job_id].result = data.result;
              jobs[job.job_id].error = data.error;
              jobs[job.job_id].started = data.started;
              jobs[job.job_id].completed = data.completed;
              changed = true;
              
              if (data.status === 'COMPLETED') {
                showToast(`Job ${job.job_id.slice(0, 8)} Completed!`, 'success');
              } else if (data.status === 'FAILED') {
                showToast(`Job ${job.job_id.slice(0, 8)} Failed!`, 'error');
              }
            }
          } else if (response.status === 404) {
            // Delete jobs no longer in remote registry
            delete jobs[job.job_id];
            changed = true;
          }
        } catch (e) {
          console.error(`Status check failed for ${job.job_id}`, e);
        }
      }
      
      if (changed) {
        persistJobs();
        updateDashboardStats();
        renderJobsHistory();
        updateChartsData();
        
        // If drawer inspect is open on this job, update it
        const openDrawerUuid = document.getElementById('drawer-uuid').innerText;
        if (openDrawerUuid && jobs[openDrawerUuid]) {
          populateInspectDrawer(jobs[openDrawerUuid]);
        }
      }
    }

    async function syncAllJobs() {
      showToast("Syncing database records...", "info");
      const jobKeys = Object.keys(jobs);
      if (jobKeys.length === 0) {
        showToast("No local records to sync.", "info");
        return;
      }
      
      let updated = 0;
      for (const key of jobKeys) {
        try {
          const response = await fetch(`${API}/status/${key}`);
          if (response.ok) {
            const data = await response.json();
            jobs[key].status = data.status;
            jobs[key].result = data.result;
            jobs[key].error = data.error;
            jobs[key].started = data.started;
            jobs[key].completed = data.completed;
            updated++;
          }
        } catch (e) {
          console.error(e);
        }
      }
      
      persistJobs();
      updateDashboardStats();
      renderJobsHistory();
      updateChartsData();
      showToast(`Synced ${updated} records successfully!`, "success");
    }

    /* ── Render Log History ───────────────────────────────────────── */
    function setJobFilter(filter) {
      activeFilter = filter;
      document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
      
      const tabMap = {
        'all': 'filter-all',
        'QUEUED': 'filter-queued',
        'PROCESSING': 'filter-processing',
        'COMPLETED': 'filter-completed',
        'FAILED': 'filter-failed'
      };
      
      document.getElementById(tabMap[filter]).classList.add('active');
      renderJobsHistory();
    }

    function renderJobsHistory() {
      const tbody = document.getElementById('jobs-history-list');
      const search = document.getElementById('jobs-search-input').value.toLowerCase();
      
      let items = Object.values(jobs);
      
      // Apply status filter
      if (activeFilter !== 'all') {
        items = items.filter(j => j.status === activeFilter);
      }
      
      // Apply text search
      if (search) {
        items = items.filter(j => 
          j.job_id.toLowerCase().includes(search) || 
          j.model_id.toLowerCase().includes(search) || 
          j.prompt.toLowerCase().includes(search)
        );
      }
      
      // Sort: submitted_at descending
      items.sort((a, b) => (b.submitted_at || 0) - (a.submitted_at || 0));

      if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align:center; color:var(--text-muted); padding:40px;">No jobs match criteria.</td></tr>`;
        return;
      }

      tbody.innerHTML = items.map(job => {
        const idShort = `${job.job_id.slice(0, 8)}...${job.job_id.slice(-4)}`;
        const durationText = getDurationText(job);
        const timeAgoText = getTimeAgo(job.submitted_at);
        
        return `
          <tr onclick="openInspectDrawer('${job.job_id}')">
            <td class="job-id-cell">${idShort}</td>
            <td><code class="node-tag">${esc(job.model_id)}</code></td>
            <td class="prompt-cell">${esc(job.prompt)}</td>
            <td><span class="badge-status badge-${job.status}">${job.status}</span></td>
            <td>${timeAgoText}</td>
            <td>
              <div style="display:flex; gap:8px;" onclick="event.stopPropagation()">
                <button class="btn" style="padding:4px 8px; font-size:0.75rem;" onclick="openInspectDrawer('${job.job_id}')" title="Inspect output text">
                  <i data-lucide="eye" style="width:14px; height:14px;"></i> Inspect
                </button>
                <button class="btn" style="padding:4px 8px; font-size:0.75rem; color:var(--danger);" onclick="deleteJobLocal('${job.job_id}')" title="Remove locally">
                  <i data-lucide="trash" style="width:14px; height:14px;"></i>
                </button>
              </div>
            </td>
          </tr>
        `;
      }).join('');
      
      lucide.createIcons();
    }

    function deleteJobLocal(jobId) {
      if (jobs[jobId]) {
        delete jobs[jobId];
        persistJobs();
        updateDashboardStats();
        renderJobsHistory();
        updateChartsData();
        showToast("Removed job from browser history.", "success");
      }
    }

    function clearHistory() {
      if (confirm("Are you sure you want to clear your local history of jobs? This cannot be undone.")) {
        jobs = {};
        persistJobs();
        updateDashboardStats();
        renderJobsHistory();
        updateChartsData();
        showToast("History cleared.", "info");
      }
    }

    /* ── Dashboard Stats updates ───────────────────────────────────── */
    function updateDashboardStats() {
      const items = Object.values(jobs);
      const total = items.length;
      const queued = items.filter(j => j.status === 'QUEUED').length;
      const processing = items.filter(j => j.status === 'PROCESSING').length;
      const completed = items.filter(j => j.status === 'COMPLETED').length;
      const failed = items.filter(j => j.status === 'FAILED').length;
      
      document.getElementById('stat-total-jobs').innerText = total;
      document.getElementById('stat-active-jobs').innerText = queued + processing;
      document.getElementById('stat-success-jobs').innerText = completed;
      
      const successRate = total > 0 ? Math.round((completed / (completed + failed || 1)) * 100) : 0;
      document.getElementById('stat-success-rate').innerText = total > 0 ? `${successRate}%` : '0%';
      
      // Update recent jobs table in dashboard home
      const recentTbody = document.getElementById('dashboard-recent-jobs');
      const sorted = [...items].sort((a,b) => (b.submitted_at || 0) - (a.submitted_at || 0)).slice(0, 5);
      
      if (sorted.length === 0) {
        recentTbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:var(--text-muted); padding:32px;">No jobs logged in this session yet. Submit one!</td></tr>`;
        return;
      }
      
      recentTbody.innerHTML = sorted.map(job => `
        <tr onclick="openInspectDrawer('${job.job_id}')">
          <td class="job-id-cell">${job.job_id.slice(0,8)}...</td>
          <td><code class="node-tag">${esc(job.model_id)}</code></td>
          <td class="prompt-cell">${esc(job.prompt)}</td>
          <td><span class="badge-status badge-${job.status}">${job.status}</span></td>
          <td>${getTimeAgo(job.submitted_at)}</td>
        </tr>
      `).join('');
      
      lucide.createIcons();
    }

    /* ── Slide Inspect Drawer Manager ────────────────────────────── */
    function openInspectDrawer(jobId) {
      const job = jobs[jobId];
      if (!job) return;
      
      populateInspectDrawer(job);
      document.getElementById('drawer-inspect').classList.add('open');
    }

    function populateInspectDrawer(job) {
      document.getElementById('drawer-uuid').innerText = job.job_id;
      document.getElementById('drawer-model').innerHTML = `<code class="node-tag">${esc(job.model_id)}</code>`;
      document.getElementById('drawer-prompt').innerText = job.prompt;
      
      const badge = document.getElementById('drawer-status-badge');
      badge.className = `badge-status badge-${job.status}`;
      badge.innerText = job.status;
      
      document.getElementById('drawer-time').innerText = job.submitted_at ? getTimeAgo(job.submitted_at) : '—';
      
      const completionContainer = document.getElementById('drawer-completion');
      const copyBtn = document.getElementById('drawer-copy-btn');
      
      if (job.status === 'COMPLETED' && job.result) {
        completionContainer.innerText = job.result.completion || '(empty response)';
        completionContainer.style.borderColor = 'var(--border)';
        completionContainer.style.color = 'var(--text-primary)';
        
        document.getElementById('drawer-prompt-tokens').innerText = job.result.prompt_tokens || 0;
        document.getElementById('drawer-completion-tokens').innerText = job.result.completion_tokens || 0;
        copyBtn.disabled = false;
      } else if (job.status === 'FAILED') {
        completionContainer.innerText = job.error || 'Server error occurred during execution.';
        completionContainer.style.borderColor = 'var(--danger)';
        completionContainer.style.color = '#fda4af';
        
        document.getElementById('drawer-prompt-tokens').innerText = 0;
        document.getElementById('drawer-completion-tokens').innerText = 0;
        copyBtn.disabled = true;
      } else {
        completionContainer.innerHTML = `<span style="color:var(--text-muted);"><i data-lucide="loader" class="spin" style="width:16px; height:16px; vertical-align:middle; margin-right:8px;"></i> Processing task in background queue...</span>`;
        lucide.createIcons();
        completionContainer.style.borderColor = 'var(--warning)';
        
        document.getElementById('drawer-prompt-tokens').innerText = 0;
        document.getElementById('drawer-completion-tokens').innerText = 0;
        copyBtn.disabled = true;
      }
      
      // Load raw json
      document.getElementById('drawer-raw-json').innerText = JSON.stringify(job, null, 2);
    }

    function closeInspectDrawer() {
      document.getElementById('drawer-inspect').classList.remove('open');
      document.getElementById('drawer-raw-json-group').style.display = 'none';
    }

    function toggleRawJson() {
      const el = document.getElementById('drawer-raw-json-group');
      el.style.display = el.style.display === 'none' ? 'block' : 'none';
    }

    function copyDrawerCompletion() {
      const text = document.getElementById('drawer-completion').innerText;
      if (!text) return;
      navigator.clipboard.writeText(text);
      showToast("Response output copied to clipboard!", "success");
    }

    /* ── Cluster Topology Renderer ────────────────────────────────── */
    async function renderClusterTopology() {
      checkClusterHealth();
      updateCoordinatorStatus();
      
      // Fetch models tag container
      const modelsContainer = document.getElementById('cluster-installed-models');
      try {
        const response = await fetch(API + '/models');
        if (response.ok) {
          const data = await response.json();
          const ollamaModels = data.ollama || [];
          
          if (ollamaModels.length === 0) {
            modelsContainer.innerHTML = `<span style="color:var(--text-muted); font-size:0.85rem;">No local models loaded on host yet. Use 'ollama pull' command.</span>`;
          } else {
            modelsContainer.innerHTML = ollamaModels.map(modelName => `
              <span class="node-tag" style="display:flex; align-items:center; gap:6px;">
                <span class="status-dot active" style="width:6px; height:6px;"></span>
                ${esc(modelName)}
              </span>
            `).join('');
          }
        }
      } catch (e) {
        modelsContainer.innerHTML = `<span style="color:var(--danger); font-size:0.85rem;">Unable to check registry.</span>`;
      }
    }

    async function checkClusterHealth() {
      const gwDot = document.getElementById('gateway-status-dot');
      const gwText = document.getElementById('gateway-status-text');
      
      const redisDot = document.getElementById('redis-status-dot');
      const redisText = document.getElementById('redis-status-text');
      
      const clusterRedisBadge = document.getElementById('cluster-redis-badge');
      const clusterQueueSize = document.getElementById('cluster-broker-queue');

      try {
        const response = await fetch(API + '/health');
        
        if (response.ok) {
          const data = await response.json();
          
          gwDot.className = 'status-dot active';
          gwText.innerText = 'Connected';
          
          if (data.redis_connected) {
            redisDot.className = 'status-dot active';
            redisText.innerText = 'Connected';
            
            if (clusterRedisBadge) {
              clusterRedisBadge.className = 'badge-status badge-COMPLETED';
              clusterRedisBadge.innerText = 'ONLINE';
            }
            
            // Check queue sizes
            clusterQueueSize.innerHTML = `<span style="color:var(--success); font-weight:600">Active Listener (FIFO)</span>`;
          } else {
            redisDot.className = 'status-dot inactive';
            redisText.innerText = 'Offline';
            
            if (clusterRedisBadge) {
              clusterRedisBadge.className = 'badge-status badge-FAILED';
              clusterRedisBadge.innerText = 'OFFLINE';
            }
            clusterQueueSize.innerText = 'Redis Unreachable';
          }
          
          if (document.getElementById('cluster-gw-version')) {
            document.getElementById('cluster-gw-version').innerText = data.version || '1.0.0';
          }
        } else {
          setHealthStatusFailed();
        }
      } catch (e) {
        setHealthStatusFailed();
      }
    }

    async function updateCoordinatorStatus() {
      const coordBadge = document.getElementById('cluster-coord-badge');
      const coordStatus = document.getElementById('cluster-coord-status');
      const coordWorkers = document.getElementById('cluster-coord-workers');
      const coordRpc = document.getElementById('cluster-coord-rpc');
      try {
        const resp = await fetch(API + '/cluster/status');
        if (resp.ok) {
          const data = await resp.json();
          if (data.error) {
            coordBadge.className = 'badge-status badge-FAILED';
            coordBadge.innerText = 'OFFLINE';
            coordStatus.innerText = 'Unreachable';
            coordWorkers.innerText = '-';
            coordRpc.innerText = '-';
          } else {
            coordBadge.className = 'badge-status badge-COMPLETED';
            coordBadge.innerText = 'ONLINE';
            coordStatus.innerText = data.alive_workers > 0 ? 'Active' : 'No Workers';
            coordWorkers.innerText = `${data.alive_workers} / ${data.total_workers} alive`;
            coordRpc.innerText = data.alive_workers > 0 ? `${data.alive_workers} node(s)` : 'None';
          }
        } else {
          coordBadge.className = 'badge-status badge-FAILED';
          coordBadge.innerText = 'OFFLINE';
          coordStatus.innerText = 'Coordinator Down';
        }
      } catch (e) {
        if (coordBadge) {
          coordBadge.className = 'badge-status badge-FAILED';
          coordBadge.innerText = 'OFFLINE';
          coordStatus.innerText = 'Coordinator Unreachable';
        }
      }
    }

    function setHealthStatusFailed() {
      const gwDot = document.getElementById('gateway-status-dot');
      const gwText = document.getElementById('gateway-status-text');
      
      const redisDot = document.getElementById('redis-status-dot');
      const redisText = document.getElementById('redis-status-text');
      
      gwDot.className = 'status-dot inactive';
      gwText.innerText = 'Offline';
      
      redisDot.className = 'status-dot inactive';
      redisText.innerText = 'Offline';
      
      const clusterRedisBadge = document.getElementById('cluster-redis-badge');
      if (clusterRedisBadge) {
        clusterRedisBadge.className = 'badge-status badge-FAILED';
        clusterRedisBadge.innerText = 'OFFLINE';
        document.getElementById('cluster-broker-queue').innerText = 'System Connection Error';
      }
    }

    /* ── Charts.js Visualization ───────────────────────────────────── */
    function initCharts() {
      // 1. Line Chart Volume
      const ctxVolume = document.getElementById('chart-volume').getContext('2d');
      volumeChart = new Chart(ctxVolume, {
        type: 'line',
        data: {
          labels: ['1h ago', '45m ago', '30m ago', '15m ago', 'Now'],
          datasets: [{
            label: 'Inference Jobs',
            data: [0, 0, 0, 0, 0],
            borderColor: '#6366f1',
            backgroundColor: 'rgba(99, 102, 241, 0.1)',
            fill: true,
            tension: 0.4,
            borderWidth: 2
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            y: {
              grid: { color: 'rgba(255, 255, 255, 0.05)' },
              ticks: { color: '#94a3b8', stepSize: 1 },
              beginAtZero: true
            },
            x: {
              grid: { display: false },
              ticks: { color: '#94a3b8' }
            }
          }
        }
      });

      // 2. Pie Chart Statuses
      const ctxStatuses = document.getElementById('chart-statuses').getContext('2d');
      statusesChart = new Chart(ctxStatuses, {
        type: 'doughnut',
        data: {
          labels: ['Completed', 'Failed', 'Running', 'Queued'],
          datasets: [{
            data: [0, 0, 0, 0],
            backgroundColor: ['#10b981', '#ef4444', '#f59e0b', '#6366f1'],
            borderWidth: 1,
            borderColor: 'rgba(6, 6, 9, 0.8)'
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'right',
              labels: { color: '#f8fafc', font: { family: 'Inter', size: 11 } }
            }
          },
          cutout: '65%'
        }
      });
      
      updateChartsData();
    }

    function updateChartsData() {
      if (!volumeChart || !statusesChart) return;
      
      const items = Object.values(jobs);
      
      // Update doughnut data
      const completed = items.filter(j => j.status === 'COMPLETED').length;
      const failed = items.filter(j => j.status === 'FAILED').length;
      const processing = items.filter(j => j.status === 'PROCESSING').length;
      const queued = items.filter(j => j.status === 'QUEUED').length;
      
      statusesChart.data.datasets[0].data = [completed, failed, processing, queued];
      statusesChart.update();

      // Update line chart with some dynamic mock timestamps based on local submissions
      // In a real application, this maps server history. We construct a 5-bucket volume count.
      const nowMs = Date.now();
      const buckets = [0, 0, 0, 0, 0]; // representing 1h, 45m, 30m, 15m, current
      
      items.forEach(j => {
        if (!j.submitted_at) return;
        const diffMins = (nowMs / 1000 - j.submitted_at) / 60;
        if (diffMins <= 15) buckets[4]++;
        else if (diffMins <= 30) buckets[3]++;
        else if (diffMins <= 45) buckets[2]++;
        else if (diffMins <= 60) buckets[1]++;
        else buckets[0]++;
      });
      
      volumeChart.data.datasets[0].data = buckets;
      volumeChart.update();
    }

    /* ── Chat Logic ─────────────────────────────────────────────────── */
    let chatHistory = [];   // [{role, content, meta}]
    let chatBusy = false;

    async function initChatPanel() {
      await chatFetchModels();
      renderChatHistory();
    }

    async function chatFetchModels() {
      const provider = document.getElementById('chat-provider-select').value;
      const sel = document.getElementById('chat-model-select');
      sel.innerHTML = '<option value="">Loading…</option>';
      try {
        const resp = await fetch(API + '/models');
        if (!resp.ok) throw new Error();
        const data = await resp.json();
        const models = data[provider] || [];
        if (models.length === 0) {
          sel.innerHTML = `<option value="">— no models for ${provider} —</option>`;
        } else {
          sel.innerHTML = models.map(m =>
            `<option value="${provider}/${esc(m)}">${esc(m)}</option>`
          ).join('');
        }
      } catch {
        sel.innerHTML = '<option value="">— failed to load —</option>';
      }
    }

    function chatProviderChange() {
      chatFetchModels();
    }

    function renderChatHistory() {
      const container = document.getElementById('chat-messages');
      const emptyState = document.getElementById('chat-empty');

      // Clear all but the empty-state div
      [...container.children].forEach(el => {
        if (el.id !== 'chat-empty') el.remove();
      });

      if (chatHistory.length === 0) {
        emptyState.style.display = 'flex';
        return;
      }
      emptyState.style.display = 'none';

      chatHistory.forEach(msg => appendChatBubble(msg, false));
      scrollChatToBottom();
    }

    function appendChatBubble(msg, scroll = true) {
      const container = document.getElementById('chat-messages');
      const emptyState = document.getElementById('chat-empty');
      emptyState.style.display = 'none';

      const isUser = msg.role === 'user';
      const wrap = document.createElement('div');
      wrap.className = `chat-bubble-wrap ${isUser ? 'user' : 'assistant'}`;
      if (msg.id) wrap.dataset.msgId = msg.id;

      const avatarInner = isUser
        ? 'Y'
        : `<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>`;

      const metaText = msg.meta
        ? `${msg.meta.model || ''} · ${msg.meta.tokens || ''} tokens · ${msg.meta.duration || ''}`
        : '';

      wrap.innerHTML = `
        <div class="chat-avatar ${isUser ? 'user-avatar' : 'model-avatar'}">${avatarInner}</div>
        <div>
          <div class="chat-bubble ${isUser ? 'user' : (msg.role === 'error' ? 'error' : 'assistant')}">${esc(msg.content)}</div>
          ${metaText ? `<div class="chat-meta">${esc(metaText)}</div>` : ''}
        </div>`;

      container.appendChild(wrap);
      if (scroll) scrollChatToBottom();
    }

    function addTypingIndicator() {
      const container = document.getElementById('chat-messages');
      const wrap = document.createElement('div');
      wrap.className = 'chat-bubble-wrap assistant';
      wrap.id = 'chat-typing';
      wrap.innerHTML = `
        <div class="chat-avatar model-avatar">
          <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        </div>
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>`;
      container.appendChild(wrap);
      scrollChatToBottom();
    }

    function removeTypingIndicator() {
      const el = document.getElementById('chat-typing');
      if (el) el.remove();
    }

    function scrollChatToBottom() {
      const c = document.getElementById('chat-messages');
      c.scrollTop = c.scrollHeight;
    }

    function autoResizeChatInput(el) {
      el.style.height = 'auto';
      el.style.height = Math.min(el.scrollHeight, 160) + 'px';
    }

    function chatKeyHandler(event) {
      if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
      }
    }

    async function sendChatMessage() {
      if (chatBusy) return;
      const inputEl = document.getElementById('chat-input');
      const text = inputEl.value.trim();
      if (!text) return;

      const modelId = document.getElementById('chat-model-select').value;
      if (!modelId || modelId === '') {
        showToast('Please select a model first.', 'error');
        return;
      }

      const maxTokens = 2048;
      const temperature = 0.7;

      // Display user message immediately
      const userMsg = { role: 'user', content: text };
      chatHistory.push(userMsg);
      appendChatBubble(userMsg);

      // Clear input
      inputEl.value = '';
      inputEl.style.height = 'auto';

      // Lock UI
      chatBusy = true;
      document.getElementById('chat-send-btn').disabled = true;
      addTypingIndicator();

      const payload = {
        prompt: text,
        model_id: modelId,
        max_tokens: maxTokens,
        temperature: temperature
      };

      try {
        const resp = await fetch(API + '/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error((await resp.json()).detail || 'Gateway error');
        const { job_id } = await resp.json();

        // Poll until done
        const result = await pollChatJob(job_id);
        removeTypingIndicator();

        const duration = result.completed && result.started
          ? `${(result.completed - result.started).toFixed(2)}s`
          : '';
        const r = result.result || {};
        const assistantMsg = {
          role: 'assistant',
          content: r.completion || '(empty response)',
          meta: {
            model: r.model || modelId,
            tokens: (r.prompt_tokens || 0) + (r.completion_tokens || 0),
            duration
          }
        };
        chatHistory.push(assistantMsg);
        appendChatBubble(assistantMsg);

      } catch (err) {
        removeTypingIndicator();
        const errMsg = { role: 'error', content: `Error: ${err.message}` };
        chatHistory.push(errMsg);
        appendChatBubble(errMsg);
      } finally {
        chatBusy = false;
        document.getElementById('chat-send-btn').disabled = false;
        inputEl.focus();
      }
    }

    async function pollChatJob(jobId, maxWaitMs = 120000, intervalMs = 1500) {
      const deadline = Date.now() + maxWaitMs;
      while (Date.now() < deadline) {
        await new Promise(r => setTimeout(r, intervalMs));
        const resp = await fetch(`${API}/status/${jobId}`);
        if (!resp.ok) throw new Error('Status check failed');
        const data = await resp.json();
        if (data.status === 'COMPLETED') return data;
        if (data.status === 'FAILED') throw new Error(data.error || 'Job failed on worker');
      }
      throw new Error('Timed out waiting for model response');
    }

    function clearChat() {
      chatHistory = [];
      renderChatHistory();
      showToast('Chat cleared.', 'info');
    }

    /* ── Settings Logic ────────────────────────────────────────────── */
    function togglePw(inputId, btn) {
      const input = document.getElementById(inputId);
      const isHidden = input.type === 'password';
      input.type = isHidden ? 'text' : 'password';
      // Swap eye icon
      btn.innerHTML = isHidden
        ? `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/></svg>`
        : `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>`;
    }

    function loadApiKeysForm() {
    }

    function saveApiKeys(event) {
      if (event) event.preventDefault();
      showToast("No API keys needed — Younify uses Ollama.", "info");
    }

    function clearSettingsForm() {
      showToast("Nothing to clear — Younify uses Ollama.", "info");
    }

    /* ── Utilities ────────────────────────────────────────────────── */
    function esc(str) {
      if (!str) return '';
      const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#x27;' };
      return str.replace(/[&<>"']/g, m => map[m]);
    }

    function getDurationText(job) {
      if (job.started && job.completed) {
        const diff = (job.completed - job.started).toFixed(2);
        return `${diff}s`;
      }
      return '—';
    }

    function getTimeAgo(timestamp) {
      if (!timestamp) return '—';
      const seconds = Math.floor((Date.now() / 1000) - timestamp);
      if (seconds < 5) return 'Just now';
      if (seconds < 60) return `${seconds}s ago`;
      const minutes = Math.floor(seconds / 60);
      if (minutes < 60) return `${minutes}m ago`;
      const hours = Math.floor(minutes / 60);
      if (hours < 24) return `${hours}h ago`;
      return new Date(timestamp * 1000).toLocaleDateString();
    }
  </script>
</body>
</html>
"""
