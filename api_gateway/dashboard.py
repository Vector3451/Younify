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
    /* ── Cluster Summary Bar ────────────────────────────────────────── */
    .cluster-summary {
      display: flex;
      align-items: center;
      gap: 24px;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 16px 24px;
      margin-bottom: 24px;
      flex-wrap: wrap;
    }
    .cluster-stat-item {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .cluster-stat-item .cluster-stat-label {
      display: block;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: var(--text-muted);
    }
    .cluster-stat-item .cluster-stat-value {
      display: block;
      font-family: var(--font-title);
      font-size: 1.2rem;
      font-weight: 700;
      color: var(--text-primary);
      line-height: 1.2;
    }

    /* ── Infra Row ─────────────────────────────────────────────────── */
    .cluster-infra-row {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 16px;
      margin-bottom: 28px;
    }
    @media (max-width: 800px) { .cluster-infra-row { grid-template-columns: 1fr; } }
    .infra-card {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 16px 20px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      transition: border-color var(--transition-speed) var(--ease);
    }
    .infra-card:hover { border-color: rgba(255,255,255,0.12); }
    .infra-card-header {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .infra-card-header i {
      width: 20px; height: 20px;
      color: var(--accent);
    }
    .infra-card-name {
      font-weight: 600;
      font-size: 0.9rem;
    }
    .infra-card-role {
      font-size: 0.7rem;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }
    .infra-card-body {
      display: flex;
      flex-direction: column;
      gap: 6px;
      font-size: 0.8rem;
    }
    .infra-row {
      display: flex;
      justify-content: space-between;
      color: var(--text-secondary);
    }
    .infra-row span:first-child {
      color: var(--text-muted);
    }

    /* ── Worker Nodes Section ──────────────────────────────────────── */
    .cluster-workers-section {
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: var(--radius-md);
      padding: 20px 24px;
    }
    .cluster-section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid var(--border);
    }
    .cluster-section-header h3 {
      font-family: var(--font-title);
      font-size: 1.05rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 8px;
      margin: 0;
    }

    .wr-card {
      display: flex;
      align-items: center;
      gap: 16px;
      background: rgba(255,255,255,0.015);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 14px 18px;
      margin-bottom: 10px;
      transition: border-color var(--transition-speed) var(--ease);
    }
    .wr-card:hover { border-color: var(--border-glow); }
    .wr-card:last-child { margin-bottom: 0; }

    .wr-status-dot {
      width: 10px; height: 10px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .wr-status-dot.alive { background: var(--success); box-shadow: 0 0 8px var(--success-glow); }
    .wr-status-dot.dead  { background: var(--danger); box-shadow: 0 0 8px var(--danger-glow); }

    .wr-icon {
      width: 34px; height: 34px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
      background: rgba(99,102,241,0.1);
      color: var(--accent);
    }
    .wr-icon i { width: 17px; height: 17px; }

    .wr-body { flex: 1; min-width: 0; }
    .wr-name {
      font-weight: 600; font-size: 0.88rem;
    }
    .wr-host {
      font-size: 0.72rem;
      color: var(--text-muted);
      margin-top: 1px;
    }

    .wr-resources {
      display: flex;
      gap: 20px;
      flex-shrink: 0;
    }
    .wr-res-item {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 2px;
    }
    .wr-res-value {
      font-family: var(--font-mono);
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-primary);
    }
    .wr-res-label {
      font-size: 0.62rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
    }

    .wr-tokens {
      text-align: right;
      flex-shrink: 0;
    }
    .wr-tokens-value {
      font-family: var(--font-mono);
      font-size: 0.85rem;
      font-weight: 600;
      color: var(--warning);
    }
    .wr-tokens-label {
      font-size: 0.62rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--text-muted);
      display: block;
      text-align: right;
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

    #drawer-logs {
      background: rgba(0,0,0,0.6);
      border-color: var(--border);
      line-height: 1.6;
      max-height: 200px;
      overflow-y: auto;
      font-size: 0.75rem;
    }

    #drawer-logs .log-line {
      padding: 1px 0;
    }

    #drawer-logs .log-line.error {
      color: #fda4af;
    }

    #drawer-logs .log-line.warn {
      color: #fcd34d;
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

    /* ── Conversation Sidebar ────────────────────────────────────────── */
    .conv-sidebar {
      width: 240px;
      flex-shrink: 0;
      border-right: 1px solid var(--border);
      background: rgba(0,0,0,0.2);
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }

    .conv-header {
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-secondary);
    }

    .conv-new-btn {
      background: none;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      color: var(--text-secondary);
      cursor: pointer;
      padding: 4px 8px;
      display: flex;
      align-items: center;
      gap: 4px;
      font-size: 0.75rem;
      transition: all var(--transition-speed) var(--ease);
    }

    .conv-new-btn:hover {
      color: var(--text-primary);
      border-color: var(--accent);
      background: var(--accent-glow);
    }

    .conv-list {
      flex: 1;
      overflow-y: auto;
      padding: 8px;
    }

    .conv-item {
      padding: 10px 12px;
      border-radius: var(--radius-sm);
      cursor: pointer;
      font-size: 0.8rem;
      color: var(--text-secondary);
      margin-bottom: 4px;
      transition: all var(--transition-speed) var(--ease);
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
    }

    .conv-item:hover {
      background: var(--surface-hover);
      color: var(--text-primary);
    }

    .conv-item.active {
      background: var(--accent-glow);
      border: 1px solid var(--border-glow);
      color: var(--text-primary);
    }

    .conv-item-title {
      flex: 1;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .conv-item-delete {
      opacity: 0;
      background: none;
      border: none;
      color: var(--text-muted);
      cursor: pointer;
      padding: 2px;
      border-radius: 4px;
      transition: all var(--transition-speed) var(--ease);
      display: flex;
      align-items: center;
    }

    .conv-item:hover .conv-item-delete {
      opacity: 1;
    }

    .conv-item-delete:hover {
      color: var(--danger);
      background: rgba(239,68,68,0.1);
    }

    .chat-layout {
      flex-direction: row;
    }

    .chat-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      min-width: 0;
    }

    /* ── Code Blocks ─────────────────────────────────────────────────── */
    .chat-bubble pre {
      background: rgba(0, 0, 0, 0.5);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      margin: 8px 0;
      overflow-x: auto;
      position: relative;
    }

    .chat-bubble pre code {
      font-family: var(--font-mono);
      font-size: 0.82rem;
      line-height: 1.5;
      color: var(--text-primary);
      background: none;
      padding: 0;
    }

    .chat-bubble code {
      font-family: var(--font-mono);
      font-size: 0.85em;
      background: rgba(255, 255, 255, 0.06);
      padding: 1px 5px;
      border-radius: 4px;
      color: var(--accent);
    }

    .chat-bubble .copy-code-btn {
      position: absolute;
      top: 6px;
      right: 6px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--border);
      border-radius: 4px;
      color: var(--text-muted);
      cursor: pointer;
      padding: 3px 7px;
      font-size: 0.7rem;
      transition: all var(--transition-speed) var(--ease);
    }

    .chat-bubble .copy-code-btn:hover {
      color: var(--text-primary);
      background: rgba(255, 255, 255, 0.1);
    }

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

    /* ── Worker list ────────────────────────────────────────────────── */
    .worker-item {
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 8px 12px;
      border-radius: var(--radius-sm);
      background: rgba(255,255,255,0.02);
      border: 1px solid var(--border);
      margin-bottom: 6px;
    }
    .worker-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      flex-shrink: 0;
    }
    .worker-dot.alive { background: var(--success); box-shadow: 0 0 6px var(--success); }
    .worker-dot.stale { background: var(--warning); }
    .worker-info { display: flex; flex-direction: column; }
    .worker-host { font-size: 0.85rem; font-weight: 600; color: var(--text-primary); }
    .worker-model { font-size: 0.75rem; color: var(--text-muted); }
    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    .spin { animation: spin 1s linear infinite; display: inline-block; }
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
        <div id="nav-chat" class="nav-item active" onclick="switchTab('chat')" role="button" tabindex="0">
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

    <!-- ────────────────── PANEL 1: CHAT (default) ────────────────── -->

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
                <th>Tokens</th>
                <th>Status</th>
                <th>Time</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody id="jobs-history-list">
              <tr>
        <td colspan="7" style="text-align:center; color:var(--text-muted); padding:40px;">
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

      <!-- Cluster Stats Bar -->
      <div class="cluster-summary">
        <div class="cluster-stat-item">
          <i data-lucide="cpu" style="width:18px;height:18px;color:var(--accent)"></i>
          <div>
            <span class="cluster-stat-label">Workers</span>
            <span class="cluster-stat-value" id="cl-summary-workers">0</span>
          </div>
        </div>
        <div class="cluster-stat-item">
          <i data-lucide="activity" style="width:18px;height:18px;color:var(--success)"></i>
          <div>
            <span class="cluster-stat-label">Alive</span>
            <span class="cluster-stat-value" id="cl-summary-alive">0</span>
          </div>
        </div>
        <div class="cluster-stat-item">
          <i data-lucide="zap" style="width:18px;height:18px;color:var(--warning)"></i>
          <div>
            <span class="cluster-stat-label">Total Tokens</span>
            <span class="cluster-stat-value" id="cl-summary-tokens">0</span>
          </div>
        </div>
        <div class="cluster-stat-item">
          <i data-lucide="hard-drive" style="width:18px;height:18px;color:var(--accent)"></i>
          <div>
            <span class="cluster-stat-label">Total VRAM</span>
            <span class="cluster-stat-value" id="cl-summary-vram">—</span>
          </div>
        </div>
        <div class="cluster-stat-item">
          <i data-lucide="server" style="width:18px;height:18px;color:#a855f7"></i>
          <div>
            <span class="cluster-stat-label">Total RAM</span>
            <span class="cluster-stat-value" id="cl-summary-ram">—</span>
          </div>
        </div>
        <button class="btn" style="margin-left:auto" onclick="location.reload()">
          <i data-lucide="rotate-cw"></i> Refresh
        </button>
      </div>

      <!-- Infrastructure row -->
      <div class="cluster-infra-row">
        <div class="infra-card">
          <div class="infra-card-header">
            <i data-lucide="shield"></i>
            <div>
              <div class="infra-card-name">API Gateway</div>
              <div class="infra-card-role">Central Broker</div>
            </div>
          </div>
          <div class="infra-card-body">
            <div class="infra-row"><span>Host</span><span id="cluster-gw-host">localhost:3000</span></div>
            <div class="infra-row"><span>Engine</span><span>FastAPI</span></div>
            <div class="infra-row"><span>Version</span><span id="cluster-gw-version">1.0.0</span></div>
          </div>
        </div>
        <div class="infra-card">
          <div class="infra-card-header">
            <i data-lucide="database"></i>
            <div>
              <div class="infra-card-name">Queue Broker</div>
              <div class="infra-card-role">Redis</div>
            </div>
          </div>
          <div class="infra-card-body">
            <div class="infra-row"><span>Port</span><span>6379</span></div>
            <div class="infra-row"><span>DB</span><span>0</span></div>
            <div class="infra-row">
              <span>Status</span>
              <span id="cluster-redis-badge" class="badge-status badge-QUEUED" style="font-size:0.7rem;padding:2px 8px">CHECK</span>
            </div>
          </div>
        </div>
        <div class="infra-card">
          <div class="infra-card-header">
            <i data-lucide="server"></i>
            <div>
              <div class="infra-card-name">Coordinator</div>
              <div class="infra-card-role">Orchestrator</div>
            </div>
          </div>
          <div class="infra-card-body">
            <div class="infra-row"><span>Status</span><span id="cluster-coord-status">—</span></div>
            <div class="infra-row"><span>Workers</span><span id="cluster-coord-workers">—</span></div>
            <div class="infra-row">
              <span>Health</span>
              <span id="cluster-coord-badge" class="badge-status badge-QUEUED" style="font-size:0.7rem;padding:2px 8px">WAIT</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Worker Nodes Section -->
      <div class="cluster-workers-section">
        <div class="cluster-section-header">
          <h3><i data-lucide="cpu" style="width:18px;height:18px;color:var(--accent)"></i> Worker Nodes</h3>
          <span id="cluster-workers-badge" class="badge-status badge-QUEUED" style="font-size:0.75rem">CHECKING</span>
        </div>
        <div id="cluster-worker-list">
          <div style="color:var(--text-muted);font-size:0.85rem;padding:24px 0;text-align:center;">
            Waiting for worker data...
          </div>
        </div>
      </div>

    </div>



    <!-- ─────────────────── PANEL 6: CHAT ─────────────────── -->
    <div id="panel-chat" class="panel active">
      <div class="chat-layout">

        <!-- Conversation Sidebar -->
        <div class="conv-sidebar">
          <div class="conv-header">
            <span>Conversations</span>
            <button class="conv-new-btn" onclick="newConversation()" title="New conversation">
              <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
              New
            </button>
          </div>
          <div class="conv-list" id="conv-list"></div>
        </div>

        <!-- Chat Main Area -->
        <div class="chat-main">

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

      <div class="detail-group" id="drawer-logs-group" style="display:none;">
        <span class="detail-label">Worker Logs</span>
        <div class="detail-value detail-value-pre" id="drawer-logs" style="max-height:200px; font-size:0.75rem;"></div>
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
      setInterval(checkClusterHealth, 10000);
      
      // Initial job list render
      renderJobsHistory();
      
      // Start polling status loop
      startPollingLoop();

      // Initialize chat panel (it's the default active tab)
      initChatPanel();
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
      
      if (tabId === 'jobs') {
        viewTitle.innerText = "Jobs History Log";
        viewSubtitle.innerText = "Audit queue contents and completed outputs";
        renderJobsHistory();
      } else if (tabId === 'cluster') {
        viewTitle.innerText = "Cluster Topology & Status";
        viewSubtitle.innerText = "View connected hardware and network nodes";
        renderClusterTopology();
      } else {
        // clear cluster poll when leaving cluster tab
        if (_clusterInterval) { clearInterval(_clusterInterval); _clusterInterval = null; }
      }
      if (tabId === 'chat') {
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
              jobs[job.job_id].logs = data.logs;
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
        renderJobsHistory();
        
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
            jobs[key].logs = data.logs;
            jobs[key].started = data.started;
            jobs[key].completed = data.completed;
            updated++;
          }
        } catch (e) {
          console.error(e);
        }
      }
      
      persistJobs();
      renderJobsHistory();
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
        tbody.innerHTML = `<tr><td colspan="7" style="text-align:center; color:var(--text-muted); padding:40px;">No jobs match criteria.</td></tr>`;
        return;
      }

      tbody.innerHTML = items.map(job => {
        const idShort = `${job.job_id.slice(0, 8)}...${job.job_id.slice(-4)}`;
        const durationText = getDurationText(job);
        const timeAgoText = getTimeAgo(job.submitted_at);
        const promptTokens = job.result ? (job.result.prompt_tokens || 0) : 0;
        const completionTokens = job.result ? (job.result.completion_tokens || 0) : 0;
        const tokenStr = (promptTokens || completionTokens) ? `${promptTokens}↑ ${completionTokens}↓` : '—';
        
        return `
          <tr onclick="openInspectDrawer('${job.job_id}')">
            <td class="job-id-cell">${idShort}</td>
            <td><code class="node-tag">${esc(job.model_id)}</code></td>
            <td class="prompt-cell">${esc(job.prompt)}</td>
            <td style="font-family:var(--font-mono);font-size:0.8rem;color:var(--text-secondary);white-space:nowrap;">${tokenStr}</td>
            <td><span class="badge-status badge-${job.status}">${job.status}</span></td>
            <td style="white-space:nowrap;">${timeAgoText}</td>
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
        renderJobsHistory();
        showToast("Removed job from browser history.", "success");
      }
    }

    function clearHistory() {
      if (confirm("Are you sure you want to clear your local history of jobs? This cannot be undone.")) {
        jobs = {};
        persistJobs();
        renderJobsHistory();
        showToast("History cleared.", "info");
      }
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

      // Load logs
      const logsGroup = document.getElementById('drawer-logs-group');
      const logsContainer = document.getElementById('drawer-logs');
      if (job.logs && job.logs.length > 0) {
        logsGroup.style.display = 'block';
        logsContainer.innerHTML = job.logs.map(line => {
          const cls = line.includes('FAILED') || line.includes('Error') ? 'error' :
                     line.includes('WARN') ? 'warn' : '';
          return `<div class="log-line${cls ? ' ' + cls : ''}">${esc(line)}</div>`;
        }).join('');
      } else {
        logsGroup.style.display = 'none';
      }
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
    let _clusterInterval = null;
    let _healthInterval = null;

    async function renderClusterTopology() {
      checkClusterHealth();
      await fetchWorkerResources();
      if (!_clusterInterval) {
        _clusterInterval = setInterval(fetchWorkerResources, 5000);
      }
      if (!_healthInterval) {
        _healthInterval = setInterval(checkClusterHealth, 10000);
      }
    }

    function fmtMB(mb) {
      if (!mb || mb <= 0) return '—';
      if (mb >= 1024) return (mb / 1024).toFixed(1) + ' GB';
      return mb + ' MB';
    }

    async function fetchWorkerResources() {
      const badge = document.getElementById('cluster-coord-badge');
      const coordStatus = document.getElementById('cluster-coord-status');
      const coordWorkers = document.getElementById('cluster-coord-workers');
      const workersBadge = document.getElementById('cluster-workers-badge');
      const workerList = document.getElementById('cluster-worker-list');

      try {
        const resp = await fetch(API + '/cluster/status');
        if (!resp.ok) throw new Error('Coordinator unreachable');
        const data = await resp.json();

        const alive = data.alive_workers || 0;
        const total = data.total_workers || 0;
        const workers = data.workers || [];

        // Update summary bar
        document.getElementById('cl-summary-workers').innerText = total;
        document.getElementById('cl-summary-alive').innerText = alive;
        const totalVram = workers.reduce((s, w) => s + (w.vram_mb || 0), 0);
        const totalRam = workers.reduce((s, w) => s + (w.ram_mb || 0), 0);
        const totalTokens = workers.reduce((s, w) => s + (w.tokens_processed || 0), 0);
        document.getElementById('cl-summary-tokens').innerText = totalTokens;
        document.getElementById('cl-summary-vram').innerText = fmtMB(totalVram);
        document.getElementById('cl-summary-ram').innerText = fmtMB(totalRam);

        if (badge) {
          badge.className = alive > 0 ? 'badge-status badge-COMPLETED' : 'badge-status badge-QUEUED';
          badge.innerText = alive > 0 ? 'ONLINE' : 'NO WORKERS';
        }
        if (coordStatus) {
          coordStatus.innerText = alive > 0 ? 'Active' : 'Idle';
        }
        if (coordWorkers) {
          coordWorkers.innerText = total > 0 ? `${alive} alive / ${total} total` : '—';
        }

        if (workersBadge) {
          workersBadge.className = alive > 0 ? 'badge-status badge-COMPLETED' : 'badge-status badge-QUEUED';
          workersBadge.innerText = alive > 0 ? `${alive} ACTIVE` : 'IDLE';
        }

        if (workerList) {
          if (workers.length === 0) {
            workerList.innerHTML = '<div style="color:var(--text-muted);font-size:0.85rem;padding:24px 0;text-align:center;">No workers connected. Start a worker with:<br><code style="background:rgba(255,255,255,0.05);padding:2px 6px;border-radius:4px;font-size:0.78rem;margin-top:6px;display:inline-block;">bash start.sh --worker &lt;head-ip&gt;</code></div>';
          } else {
            workerList.innerHTML = workers.map(w => {
              const isAlive = w.alive;
              const vramStr = fmtMB(w.vram_mb);
              const ramStr = fmtMB(w.ram_mb);
              const tokens = w.tokens_processed || 0;
              const statusLabel = isAlive ? 'alive' : 'dead';
              const name = esc(w.label || w.host || w.worker_id);
              const host = esc(w.host || '—');
              return `
                <div class="wr-card">
                  <span class="wr-status-dot ${statusLabel}"></span>
                  <div class="wr-icon"><i data-lucide="cpu"></i></div>
                  <div class="wr-body">
                    <div class="wr-name">${name}</div>
                    <div class="wr-host">${host}</div>
                  </div>
                  <div class="wr-resources">
                    <div class="wr-res-item">
                      <span class="wr-res-value">${vramStr}</span>
                      <span class="wr-res-label">VRAM</span>
                    </div>
                    <div class="wr-res-item">
                      <span class="wr-res-value">${ramStr}</span>
                      <span class="wr-res-label">RAM</span>
                    </div>
                  </div>
                  <div class="wr-tokens">
                    <span class="wr-tokens-value">${tokens}</span>
                    <span class="wr-tokens-label">tokens</span>
                  </div>
                </div>
              `;
            }).join('');
            lucide.createIcons();
          }
        }
      } catch (e) {
        if (badge) {
          badge.className = 'badge-status badge-FAILED';
          badge.innerText = 'OFFLINE';
        }
        if (coordStatus) coordStatus.innerText = 'Coordinator Down';
        if (workersBadge) {
          workersBadge.className = 'badge-status badge-FAILED';
          workersBadge.innerText = 'OFFLINE';
        }
        if (workerList) {
          workerList.innerHTML = '<div style="color:var(--danger);font-size:0.85rem;padding:16px 0;text-align:center;">Coordinator unreachable. Ensure the cluster coordinator is running on port 8050.</div>';
        }
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
        console.log('[Health] Fetching', API + '/health');
        const response = await fetch(API + '/health');
        console.log('[Health] Response status:', response.status);
        
        if (response.ok) {
          const data = await response.json();
          console.log('[Health] Data:', JSON.stringify(data));
          
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
            if (clusterQueueSize) {
              clusterQueueSize.innerHTML = `<span style="color:var(--success); font-weight:600">Active Listener (FIFO)</span>`;
            }
          } else {
            console.log('[Health] redis_connected is FALSE');
            redisDot.className = 'status-dot inactive';
            redisText.innerText = 'Offline';
            
            if (clusterRedisBadge) {
              clusterRedisBadge.className = 'badge-status badge-FAILED';
              clusterRedisBadge.innerText = 'OFFLINE';
            }
            if (clusterQueueSize) clusterQueueSize.innerText = 'Redis Unreachable';
          }
          
          if (document.getElementById('cluster-gw-version')) {
            document.getElementById('cluster-gw-version').innerText = data.version || '1.0.0';
          }
        } else {
          console.log('[Health] Response not OK, status:', response.status);
          setHealthStatusFailed();
        }
      } catch (e) {
        console.log('[Health] Fetch error:', e.message);
        setHealthStatusFailed();
      }
    }

    function setHealthStatusFailed() {
      const gwDot = document.getElementById('gateway-status-dot');
      const gwText = document.getElementById('gateway-status-text');
      if (gwDot) { gwDot.className = 'status-dot inactive'; }
      if (gwText) { gwText.innerText = 'Offline'; }

      const redisDot = document.getElementById('redis-status-dot');
      const redisText = document.getElementById('redis-status-text');
      if (redisDot) { redisDot.className = 'status-dot inactive'; }
      if (redisText) { redisText.innerText = 'Offline'; }
      
      const clusterRedisBadge = document.getElementById('cluster-redis-badge');
      if (clusterRedisBadge) {
        clusterRedisBadge.className = 'badge-status badge-FAILED';
        clusterRedisBadge.innerText = 'OFFLINE';
      }
    }



    /* ── Chat Logic ─────────────────────────────────────────────────── */
    let chatHistory = [];
    let chatBusy = false;
    let chatConversations = [];
    let activeConvId = null;
    const CONV_STORAGE_KEY = 'younify_chat_conversations';

    function saveConversations() {
      localStorage.setItem(CONV_STORAGE_KEY, JSON.stringify(chatConversations));
    }

    function loadConversations() {
      try {
        const raw = localStorage.getItem(CONV_STORAGE_KEY);
        return raw ? JSON.parse(raw) : [];
      } catch { return []; }
    }

    function renderConvList() {
      const list = document.getElementById('conv-list');
      if (chatConversations.length === 0) {
        list.innerHTML = '<div style="padding:16px;text-align:center;color:var(--text-muted);font-size:0.75rem;">No saved conversations</div>';
        return;
      }
      list.innerHTML = chatConversations.map(c => `
        <div class="conv-item${c.id === activeConvId ? ' active' : ''}" onclick="switchConversation('${c.id}')">
          <span class="conv-item-title">${esc(c.title || 'Untitled')}</span>
          <button class="conv-item-delete" onclick="event.stopPropagation();deleteConversation('${c.id}')" title="Delete">
            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4h6v2"/></svg>
          </button>
        </div>
      `).join('');
    }

    function getActiveConversation() {
      return chatConversations.find(c => c.id === activeConvId);
    }

    function saveActiveConversation() {
      const conv = getActiveConversation();
      if (!conv) return;
      conv.messages = [...chatHistory];
      conv.updatedAt = Date.now();
      if (chatHistory.length > 0 && chatHistory[0].role === 'user') {
        conv.title = chatHistory[0].content.slice(0, 60) + (chatHistory[0].content.length > 60 ? '...' : '');
      }
      saveConversations();
      renderConvList();
    }

    function newConversation() {
      saveActiveConversation();
      const id = 'conv_' + Date.now() + '_' + Math.random().toString(36).slice(2, 6);
      const conv = {
        id,
        title: 'New conversation',
        modelId: document.getElementById('chat-model-select').value || 'ollama/llama3',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now(),
      };
      chatConversations.unshift(conv);
      activeConvId = id;
      chatHistory = [];
      saveConversations();
      renderConvList();
      renderChatHistory();
      document.getElementById('chat-input').focus();
    }

    function switchConversation(id) {
      saveActiveConversation();
      const conv = chatConversations.find(c => c.id === id);
      if (!conv) return;
      activeConvId = id;
      chatHistory = conv.messages ? [...conv.messages] : [];
      renderConvList();
      renderChatHistory();
    }

    function deleteConversation(id) {
      chatConversations = chatConversations.filter(c => c.id !== id);
      if (activeConvId === id) {
        activeConvId = null;
        chatHistory = [];
        renderChatHistory();
      }
      saveConversations();
      renderConvList();
      showToast('Conversation deleted.', 'info');
    }

    function formatMessage(content) {
      if (!content) return '';
      let html = esc(content);
      html = html.replace(/```(\\w*)\\n?([\\s\\S]*?)```/g, (_, lang, code) => {
        const langAttr = lang ? ` class="language-${esc(lang)}"` : '';
        return `<pre><button class="copy-code-btn" onclick="navigator.clipboard.writeText(this.parentNode.querySelector('code').textContent);showToast('Copied!','success')">Copy</button><code${langAttr}>${esc(code.trim())}</code></pre>`;
      });
      html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
      html = html.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
      html = html.replace(/\\n/g, '<br>');
      return html;
    }

    async function initChatPanel() {
      chatConversations = loadConversations();
      renderConvList();
      await chatFetchModels();

      if (chatConversations.length === 0 || activeConvId) {
        if (!activeConvId && chatConversations.length > 0) {
          activeConvId = chatConversations[0].id;
        }
      }

      if (activeConvId) {
        const conv = getActiveConversation();
        if (conv) {
          chatHistory = conv.messages ? [...conv.messages] : [];
          renderConvList();
        } else {
          activeConvId = null;
        }
      }

      if (chatConversations.length === 0) {
        newConversation();
      } else {
        renderChatHistory();
      }
    }

    async function chatFetchModels() {
      const provider = document.getElementById('chat-provider-select').value;
      const sel = document.getElementById('chat-model-select');
      sel.innerHTML = '<option value="">Loading…</option>';
      try {
        const resp = await fetch(API + '/models');
        if (!resp.ok) throw new Error('HTTP ' + resp.status);
        const data = await resp.json();
        const models = data[provider] || [];
        const status = data.status || 'ok';
        if (models.length === 0) {
          if (status !== 'ok' && !status.startsWith('ollama returned')) {
            sel.innerHTML = `<option value="">⚠ ${esc(status)}</option>`;
            showToast('Ollama: ' + status, 'error');
          } else {
            sel.innerHTML = `<option value="">— no models for ${provider} —</option>`;
          }
        } else {
          sel.innerHTML = models.map(m =>
            `<option value="${provider}/${esc(m)}">${esc(m)}</option>`
          ).join('');
        }
      } catch (err) {
        sel.innerHTML = '<option value="">— failed to load —</option>';
        showToast('Failed to fetch models: ' + err.message, 'error');
      }
    }

    function chatProviderChange() {
      chatFetchModels();
    }

    function renderChatHistory() {
      const container = document.getElementById('chat-messages');
      const emptyState = document.getElementById('chat-empty');

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

      const formattedContent = isUser ? esc(msg.content) : formatMessage(msg.content);

      wrap.innerHTML = `
        <div class="chat-avatar ${isUser ? 'user-avatar' : 'model-avatar'}">${avatarInner}</div>
        <div>
          <div class="chat-bubble ${isUser ? 'user' : (msg.role === 'error' ? 'error' : 'assistant')}">${formattedContent}</div>
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
      if (!getActiveConversation()) newConversation();

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

      const userMsg = { role: 'user', content: text };
      chatHistory.push(userMsg);
      appendChatBubble(userMsg);

      inputEl.value = '';
      inputEl.style.height = 'auto';

      chatBusy = true;
      document.getElementById('chat-send-btn').disabled = true;
      addTypingIndicator();

      const payload = {
        prompt: text,
        model_id: modelId,
        max_tokens: maxTokens,
        temperature: temperature,
      };

      try {
        const resp = await fetch(API + '/generate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
        if (!resp.ok) throw new Error((await resp.json()).detail || 'Gateway error');
        const { job_id } = await resp.json();

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
        saveActiveConversation();
      }
    }

    async function pollChatJob(jobId, maxWaitMs = 600000, intervalMs = 1500) {
      const deadline = Date.now() + maxWaitMs;
      const startTime = Date.now();
      // Update the last assistant bubble to show elapsed time
      const typingEl = document.getElementById('chat-typing');
      const elapsedInterval = setInterval(() => {
        const el = document.getElementById('chat-typing');
        if (!el) { clearInterval(elapsedInterval); return; }
        const secs = Math.floor((Date.now() - startTime) / 1000);
        const min = Math.floor(secs / 60);
        const label = min > 0 ? `${min}m ${secs % 60}s` : `${secs}s`;
        el.querySelector('.typing-indicator').title = `Generating for ${label}`;
      }, 1000);
      try {
        while (Date.now() < deadline) {
          await new Promise(r => setTimeout(r, intervalMs));
          const resp = await fetch(`${API}/status/${jobId}`);
          if (!resp.ok) throw new Error('Status check failed');
          const data = await resp.json();
          if (data.status === 'COMPLETED') return data;
          if (data.status === 'FAILED') throw new Error(data.error || 'Job failed on worker');
        }
        throw new Error('Timed out waiting for model response');
      } finally {
        clearInterval(elapsedInterval);
      }
    }

    function clearChat() {
      if (getActiveConversation()) {
        saveActiveConversation();
      }
      newConversation();
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
