# ═══════════════════════════════════════════════════════════════════════════════
#  CLASSIFICADOR FPAS / TERCEIROS / SEFIP
#  Domínio Sistemas — Thomson Reuters
#  Desenvolvido em Python + Streamlit
# ═══════════════════════════════════════════════════════════════════════════════

import io
import re
import time
import requests
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────────────────────────────────────
# TEMA VISUAL — THOMSON REUTERS DARK
# ──────────────────────────────────────────────────────────────────────────────
TR_ORANGE      = "#FF8000"
TR_ORANGE_DARK = "#CC6600"
TR_BG          = "#1A1A1A"
TR_CARD        = "#242424"
TR_CARD2       = "#2E2E2E"
TR_BORDER      = "#3A3A3A"
TR_TEXT        = "#F0F0F0"
TR_TEXT_MUTED  = "#999999"
TR_SUCCESS     = "#2ECC71"
TR_ERROR       = "#E74C3C"
TR_WARNING     = "#F39C12"
TR_INFO        = "#3498DB"

CSS = f"""
<style>
  /* ── RESET GERAL ── */
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {TR_BG} !important;
      color: {TR_TEXT} !important;
      font-family: 'Segoe UI', Arial, sans-serif !important;
  }}

  /* ── SIDEBAR ── */
  [data-testid="stSidebar"] {{
      background-color: #111111 !important;
      border-right: 2px solid {TR_ORANGE} !important;
  }}
  [data-testid="stSidebar"] * {{ color: {TR_TEXT} !important; }}

  /* ── HEADER PRINCIPAL ── */
  .tr-header {{
      background: linear-gradient(135deg, #111111 0%, #1f1f1f 60%, #2a1500 100%);
      border-bottom: 3px solid {TR_ORANGE};
      padding: 18px 28px 14px 28px;
      border-radius: 10px;
      margin-bottom: 24px;
      display: flex;
      align-items: center;
      gap: 18px;
  }}
  .tr-logo-box {{
      background: {TR_ORANGE};
      border-radius: 8px;
      width: 52px; height: 52px;
      display: flex; align-items: center; justify-content: center;
      font-size: 26px; font-weight: 900; color: #fff;
      letter-spacing: -1px; flex-shrink: 0;
  }}
  .tr-title {{
      font-size: 22px; font-weight: 700;
      color: {TR_TEXT}; margin: 0; line-height: 1.2;
  }}
  .tr-subtitle {{
      font-size: 12px; color: {TR_TEXT_MUTED};
      margin: 2px 0 0 0; letter-spacing: 0.5px;
  }}
  .tr-badge {{
      margin-left: auto;
      background: {TR_ORANGE};
      color: #fff; font-size: 10px; font-weight: 700;
      padding: 4px 10px; border-radius: 20px;
      letter-spacing: 1px; text-transform: uppercase;
  }}

  /* ── CARDS ── */
  .tr-card {{
      background: {TR_CARD};
      border: 1px solid {TR_BORDER};
      border-radius: 10px;
      padding: 18px 20px;
      margin-bottom: 16px;
  }}
  .tr-card-title {{
      font-size: 13px; font-weight: 700;
      color: {TR_ORANGE}; text-transform: uppercase;
      letter-spacing: 1px; margin-bottom: 12px;
      border-bottom: 1px solid {TR_BORDER};
      padding-bottom: 8px;
  }}

  /* ── MÉTRICAS ── */
  .tr-metrics {{
      display: flex; gap: 12px; flex-wrap: wrap;
      margin-bottom: 20px;
  }}
  .tr-metric {{
      background: {TR_CARD};
      border: 1px solid {TR_BORDER};
      border-radius: 10px;
      padding: 14px 20px;
      flex: 1; min-width: 120px;
      text-align: center;
  }}
  .tr-metric-value {{
      font-size: 28px; font-weight: 800;
      color: {TR_ORANGE}; line-height: 1;
  }}
  .tr-metric-label {{
      font-size: 11px; color: {TR_TEXT_MUTED};
      margin-top: 4px; text-transform: uppercase;
      letter-spacing: 0.5px;
  }}
  .tr-metric.success .tr-metric-value {{ color: {TR_SUCCESS}; }}
  .tr-metric.error   .tr-metric-value {{ color: {TR_ERROR};   }}
  .tr-metric.warning .tr-metric-value {{ color: {TR_WARNING}; }}

  /* ── STEP INDICATOR ── */
  .tr-steps {{
      display: flex; gap: 0; margin-bottom: 24px;
      border-radius: 8px; overflow: hidden;
      border: 1px solid {TR_BORDER};
  }}
  .tr-step {{
      flex: 1; padding: 10px 8px; text-align: center;
      font-size: 12px; font-weight: 600;
      background: {TR_CARD2}; color: {TR_TEXT_MUTED};
      border-right: 1px solid {TR_BORDER};
  }}
  .tr-step:last-child {{ border-right: none; }}
  .tr-step.active {{
      background: {TR_ORANGE}; color: #fff;
  }}
  .tr-step.done {{
      background: #1a3a1a; color: {TR_SUCCESS};
  }}

  /* ── TABELA ── */
  [data-testid="stDataFrame"] {{
      border: 1px solid {TR_BORDER} !important;
      border-radius: 8px !important;
  }}

  /* ── BOTÕES ── */
  .stButton > button {{
      background: {TR_ORANGE} !important;
      color: #fff !important;
      border: none !important;
      border-radius: 6px !important;
      font-weight: 700 !important;
      letter-spacing: 0.5px !important;
      transition: background 0.2s !important;
  }}
  .stButton > button:hover {{
      background: {TR_ORANGE_DARK} !important;
  }}
  .stDownloadButton > button {{
      background: #1a3a1a !important;
      color: {TR_SUCCESS} !important;
      border: 1px solid {TR_SUCCESS} !important;
      border-radius: 6px !important;
      font-weight: 700 !important;
  }}
  .stDownloadButton > button:hover {{
      background: {TR_SUCCESS} !important;
      color: #fff !important;
  }}

  /* ── INPUTS ── */
  .stTextInput input, .stNumberInput input, .stSelectbox select {{
      background: {TR_CARD2} !important;
      color: {TR_TEXT} !important;
      border: 1px solid {TR_BORDER} !important;
      border-radius: 6px !important;
  }}
  .stMultiSelect [data-baseweb="select"] {{
      background: {TR_CARD2} !important;
      border: 1px solid {TR_BORDER} !important;
      border-radius: 6px !important;
  }}

  /* ── TABS ── */
  .stTabs [data-baseweb="tab-list"] {{
      background: {TR_CARD} !important;
      border-radius: 8px 8px 0 0 !important;
      border-bottom: 2px solid {TR_ORANGE} !important;
      gap: 4px !important;
  }}
  .stTabs [data-baseweb="tab"] {{
      color: {TR_TEXT_MUTED} !important;
      font-weight: 600 !important;
      border-radius: 6px 6px 0 0 !important;
  }}
  .stTabs [aria-selected="true"] {{
      background: {TR_ORANGE} !important;
      color: #fff !important;
  }}

  /* ── EXPANDER ── */
  .streamlit-expanderHeader {{
      background: {TR_CARD2} !important;
      border: 1px solid {TR_BORDER} !important;
      border-radius: 6px !important;
      color: {TR_TEXT} !important;
  }}

  /* ── PROGRESS ── */
  .stProgress > div > div {{
      background: {TR_ORANGE} !important;
  }}

  /* ── FILE UPLOADER ── */
  [data-testid="stFileUploader"] {{
      background: {TR_CARD} !important;
      border: 2px dashed {TR_ORANGE} !important;
      border-radius: 10px !important;
  }}

  /* ── ALERTS ── */
  .stSuccess {{ background: #0d2b0d !important; border-left: 4px solid {TR_SUCCESS} !important; }}
  .stError   {{ background: #2b0d0d !important; border-left: 4px solid {TR_ERROR}   !important; }}
  .stWarning {{ background: #2b1f0d !important; border-left: 4px solid {TR_WARNING} !important; }}
  .stInfo    {{ background: #0d1a2b !important; border-left: 4px solid {TR_INFO}    !important; }}

  /* ── SIDEBAR SEÇÃO ── */
  .tr-sidebar-section {{
      background: #1a1a1a;
      border: 1px solid {TR_BORDER};
      border-radius: 8px;
      padding: 12px 14px;
      margin-bottom: 12px;
  }}
  .tr-sidebar-title {{
      font-size: 10px; font-weight: 700;
      color: {TR_ORANGE}; text-transform: uppercase;
      letter-spacing: 1px; margin-bottom: 8px;
  }}

  /* ── TAG STATUS ── */
  .tag-ok      {{ background:#0d2b0d; color:{TR_SUCCESS}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700; }}
  .tag-erro    {{ background:#2b0d0d; color:{TR_ERROR};   padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700; }}
  .tag-alerta  {{ background:#2b1f0d; color:{TR_WARNING}; padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700; }}

  /* ── RESULTADO INDIVIDUAL ── */
  .result-grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 10px; margin-top: 12px;
  }}
  .result-item {{
      background: {TR_CARD2};
      border: 1px solid {TR_BORDER};
      border-radius: 8px;
      padding: 10px 14px;
  }}
  .result-item-label {{
      font-size: 10px; color: {TR_TEXT_MUTED};
      text-transform: uppercase; letter-spacing: 0.5px;
  }}
  .result-item-value {{
      font-size: 16px; font-weight: 700; color: {TR_TEXT};
      margin-top: 2px;
  }}
  .result-item-value.highlight {{ color: {TR_ORANGE}; }}

  /* ── ENTIDADE PILL ── */
  .ent-pill {{
      display: inline-block;
      background: #2a1500;
      border: 1px solid {TR_ORANGE};
      color: {TR_ORANGE};
      border-radius: 20px;
      padding: 3px 10px;
      font-size: 11px; font-weight: 700;
      margin: 3px 3px 3px 0;
  }}

  /* ── RODAPÉ ── */
  .tr-footer {{
      text-align: center;
      color: {TR_TEXT_MUTED};
      font-size: 11px;
      margin-top: 40px;
      padding: 16px;
      border-top: 1px solid {TR_BORDER};
  }}
  .tr-footer span {{ color: {TR_ORANGE}; font-weight: 700; }}

  /* ── SCROLLBAR ── */
  ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
  ::-webkit-scrollbar-track {{ background: {TR_BG}; }}
  ::-webkit-scrollbar-thumb {{ background: {TR_ORANGE}; border-radius: 3px; }}

  /* ── HIDE STREAMLIT DEFAULTS ── */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .block-container {{ padding-top: 1rem !important; }}
</style>
"""

# ──────────────────────────────────────────────────────────────────────────────
# MOTOR FPAS — ENTIDADES (BITMASK)
# ──────────────────────────────────────────────────────────────────────────────
ENTIDADES = {
    "FNDE":    {"codigo": 1,    "aliquota": 2.5,  "nome": "Salário-Educação"},
    "INCRA":   {"codigo": 2,    "aliquota": 0.2,  "nome": "INCRA"},
    "SENAI":   {"codigo": 4,    "aliquota": 1.0,  "nome": "SENAI"},
    "SESI":    {"codigo": 8,    "aliquota": 1.5,  "nome": "SESI"},
    "SENAC":   {"codigo": 16,   "aliquota": 1.0,  "nome": "SENAC"},
    "SESC":    {"codigo": 32,   "aliquota": 1.5,  "nome": "SESC"},
    "SEBRAE":  {"codigo": 64,   "aliquota": 0.6,  "nome": "SEBRAE"},
    "SENAR":   {"codigo": 128,  "aliquota": 2.5,  "nome": "SENAR"},
    "SEST":    {"codigo": 256,  "aliquota": 1.5,  "nome": "SEST"},
    "SENAT":   {"codigo": 512,  "aliquota": 1.0,  "nome": "SENAT"},
    "SESCOOP": {"codigo": 1024, "aliquota": 2.5,  "nome": "SESCOOP"},
}

# ──────────────────────────────────────────────────────────────────────────────
# FPAS CONFIG: fpas → (terceiros, rat, gps, gfip, descricao)
# ──────────────────────────────────────────────────────────────────────────────
FPAS_CONFIG = {
    507: (79,   2, "2100", "150", "Indústria Geral"),
    515: (115,  2, "2100", "150", "Comércio / Serviços em Geral"),
    566: (99,   2, "2100", "150", "Profissional Liberal / Autônomo PF"),
    574: (115,  1, "2100", "150", "Saúde"),
    582: (0,    1, "2100", "150", "Administração Pública"),
    604: (3,    2, "2631", "150", "Produtor Rural PF"),
    620: (145,  2, "2100", "150", "Transporte Rodoviário / Aéreo"),
    639: (0,    0, "2100", "150", "Entidade Beneficente Isenta"),
    647: (115,  1, "2100", "150", "Educação / Assistência Social"),
    655: (115,  2, "2100", "150", "Instituição Financeira"),
    663: (115,  2, "2100", "150", "Comunicação / Publicidade"),
    671: (115,  2, "2100", "150", "Hotéis / Turismo"),
    680: (115,  2, "2100", "150", "Limpeza / Conservação"),
    736: (115,  2, "2100", "150", "TI / Tecnologia da Informação"),
    744: (115,  2, "2100", "150", "Consultoria / Assessoria"),
    760: (115,  2, "2100", "150", "Segurança Privada"),
    779: (115,  2, "2100", "150", "Serviços Pessoais"),
    787: (3,    2, "2631", "150", "Produtor Rural PJ"),
    795: (115,  2, "2100", "150", "Cooperativa de Trabalho"),
    803: (115,  2, "2100", "150", "Cooperativa de Produção"),
    810: (1024, 2, "2100", "150", "Cooperativa de Crédito (SESCOOP)"),
    833: (115,  3, "2100", "150", "Construção Civil"),
    868: (0,    0, "2100", "150", "Missão Diplomática / Org. Internacional"),
    876: (0,    0, "2100", "150", "Doméstico / Contribuinte Individual"),
}

FPAS_SEMPRE_ZERO = {582, 868, 876}

# ──────────────────────────────────────────────────────────────────────────────
# CNAE → FPAS  (tabela expandida ~400 CNAEs)
# ──────────────────────────────────────────────────────────────────────────────
CNAE_FPAS = {
    # AGRICULTURA / PECUÁRIA / RURAL
    "0111-3/01":604,"0111-3/02":604,"0111-3/03":604,"0112-1/01":604,
    "0113-0/00":604,"0115-6/00":604,"0116-4/00":604,"0119-9/01":604,
    "0119-9/99":604,"0121-1/01":604,"0122-9/00":604,"0131-8/00":604,
    "0132-6/00":604,"0133-4/01":604,"0134-2/00":604,"0135-1/00":604,
    "0139-3/01":604,"0139-3/99":604,"0141-5/01":604,"0142-3/00":604,
    "0151-2/01":604,"0151-2/02":604,"0152-1/01":604,"0153-9/01":604,
    "0154-7/00":604,"0155-5/01":604,"0155-5/02":604,"0159-8/01":604,
    "0159-8/99":604,"0161-0/00":604,"0162-8/00":604,"0163-6/00":604,
    "0170-9/00":604,"0210-1/01":604,"0210-1/02":604,"0220-9/01":604,
    "0220-9/02":604,"0230-6/00":604,"0240-3/00":604,"0311-6/01":604,
    "0312-4/00":604,"0321-3/01":604,"0322-1/00":604,
    # INDÚSTRIA GERAL
    "1011-2/01":507,"1011-2/02":507,"1012-1/01":507,"1013-9/01":507,
    "1020-1/01":507,"1020-1/02":507,"1031-7/00":507,"1032-5/01":507,
    "1033-3/01":507,"1041-4/00":507,"1042-2/00":507,"1043-1/00":507,
    "1051-1/00":507,"1052-0/00":507,"1061-9/01":507,"1062-7/00":507,
    "1063-5/00":507,"1064-3/00":507,"1065-1/01":507,"1066-0/00":507,
    "1069-4/00":507,"1071-6/00":507,"1072-4/01":507,"1073-2/01":507,
    "1081-3/01":507,"1082-1/00":507,"1083-0/00":507,"1084-8/00":507,
    "1085-6/00":507,"1086-4/00":507,"1087-2/00":507,"1088-1/00":507,
    "1089-9/00":507,"1091-1/01":507,"1091-1/02":507,"1092-9/00":507,
    "1093-7/01":507,"1094-5/00":507,"1095-3/00":507,"1096-1/00":507,
    "1099-6/01":507,"1099-6/99":507,"1111-9/01":507,"1111-9/02":507,
    "1112-7/00":507,"1113-5/01":507,"1121-6/00":507,"1122-4/01":507,
    "1122-4/03":507,"1210-7/00":507,"1220-4/01":507,"1311-1/00":507,
    "1312-0/00":507,"1313-8/00":507,"1314-6/00":507,"1321-9/00":507,
    "1322-7/00":507,"1323-5/00":507,"1330-8/00":507,"1340-5/01":507,
    "1351-1/00":507,"1352-9/00":507,"1353-7/00":507,"1354-5/00":507,
    "1359-6/00":507,"1411-8/01":507,"1411-8/02":507,"1412-6/01":507,
    "1413-4/01":507,"1414-2/00":507,"1421-5/00":507,"1422-3/00":507,
    "1510-6/00":507,"1521-1/00":507,"1529-7/00":507,"1531-9/01":507,
    "1532-7/00":507,"1533-5/00":507,"1539-4/00":507,"1540-8/00":507,
    "1610-2/01":507,"1610-2/02":507,"1621-8/00":507,"1622-6/01":507,
    "1710-9/00":507,"1721-4/00":507,"1722-2/00":507,"1731-1/00":507,
    "1732-0/00":507,"1733-8/00":507,"1741-9/01":507,"1742-7/00":507,
    "1749-4/00":507,"1811-3/01":507,"1811-3/02":507,"1812-1/00":507,
    "1813-0/00":507,"1821-1/00":507,"1822-9/01":507,"1830-0/01":507,
    "1830-0/02":507,"1830-0/03":507,"1910-1/00":507,"1921-7/00":507,
    "1922-5/00":507,"1931-4/00":507,"1932-2/00":507,"1933-1/00":507,
    "2011-8/00":507,"2012-6/00":507,"2013-4/01":507,"2021-5/00":507,
    "2022-3/00":507,"2023-1/00":507,"2029-1/00":507,"2031-2/00":507,
    "2032-1/00":507,"2033-9/00":507,"2040-1/00":507,"2051-7/00":507,
    "2052-5/00":507,"2061-4/00":507,"2062-2/00":507,"2063-1/00":507,
    "2064-9/00":507,"2065-7/00":507,"2066-5/00":507,"2067-3/00":507,
    "2068-1/00":507,"2091-6/00":507,"2092-4/01":507,"2093-2/00":507,
    "2094-1/00":507,"2099-1/01":507,"2099-1/99":507,"2110-6/00":507,
    "2121-1/01":507,"2121-1/02":507,"2122-0/00":507,"2123-8/00":507,
    "2211-1/00":507,"2212-9/00":507,"2219-6/00":507,"2221-8/00":507,
    "2222-6/00":507,"2223-4/00":507,"2229-3/01":507,"2311-7/00":507,
    "2312-5/00":507,"2319-2/00":507,"2320-6/00":507,"2330-3/01":507,
    "2341-9/00":507,"2342-7/00":507,"2349-4/00":507,"2350-8/00":507,
    "2391-5/00":507,"2392-3/00":507,"2399-1/01":507,"2410-1/00":507,
    "2421-1/00":507,"2422-9/01":507,"2423-7/01":507,"2424-5/00":507,
    "2431-8/00":507,"2439-3/00":507,"2441-5/01":507,"2442-3/00":507,
    "2443-1/00":507,"2444-0/00":507,"2445-8/00":507,"2446-6/00":507,
    "2449-1/99":507,"2451-2/00":507,"2452-1/00":507,"2511-0/00":507,
    "2512-8/00":507,"2513-6/00":507,"2521-7/00":507,"2522-5/00":507,
    "2531-4/01":507,"2532-2/00":507,"2539-0/01":507,"2541-1/00":507,
    "2542-0/00":507,"2543-8/00":507,"2550-1/00":507,"2591-8/00":507,
    "2592-6/01":507,"2593-4/00":507,"2599-3/01":507,"2599-3/99":507,
    "2610-8/00":507,"2621-3/00":507,"2622-1/00":507,"2631-1/00":507,
    "2632-9/00":507,"2640-0/00":507,"2651-5/00":507,"2652-3/00":507,
    "2660-4/00":507,"2670-1/01":507,"2680-9/00":507,"2710-4/01":507,
    "2710-4/02":507,"2721-0/00":507,"2722-8/00":507,"2731-7/00":507,
    "2732-5/00":507,"2733-3/00":507,"2740-6/01":507,"2751-1/00":507,
    "2759-7/01":507,"2790-2/01":507,"2811-9/00":507,"2812-7/00":507,
    "2813-5/00":507,"2814-3/00":507,"2815-1/00":507,"2821-6/00":507,
    "2822-4/01":507,"2823-2/00":507,"2824-1/01":507,"2825-9/00":507,
    "2829-1/01":507,"2830-5/00":507,"2840-2/00":507,"2851-8/00":507,
    "2852-6/00":507,"2853-4/00":507,"2854-2/00":507,"2861-5/00":507,
    "2862-3/00":507,"2863-1/00":507,"2864-0/00":507,"2865-8/00":507,
    "2866-6/00":507,"2869-1/00":507,"2910-7/01":507,"2920-4/01":507,
    "2930-1/01":507,"2941-7/00":507,"2942-5/00":507,"2943-3/00":507,
    "2944-1/00":507,"2945-0/00":507,"2949-2/01":507,"2950-6/00":507,
    "3011-3/01":507,"3012-1/00":507,"3031-8/00":507,"3032-6/00":507,
    "3041-5/00":507,"3042-3/00":507,"3050-4/00":507,"3091-1/00":507,
    "3092-0/00":507,"3099-7/00":507,"3101-2/00":507,"3102-1/00":507,
    "3103-9/00":507,"3104-7/00":507,"3211-6/01":507,"3212-4/00":507,
    "3220-5/00":507,"3230-2/00":507,"3240-0/01":507,"3291-4/00":507,
    "3292-2/00":507,"3299-0/05":507,
    # CONSTRUÇÃO CIVIL
    "4110-7/00":833,"4120-4/00":833,"4211-1/01":833,"4211-1/02":833,
    "4212-0/00":833,"4213-8/00":833,"4221-9/01":833,"4221-9/02":833,
    "4222-7/00":833,"4223-5/00":833,"4291-0/00":833,"4292-8/00":833,
    "4299-5/01":833,"4299-5/99":833,"4311-8/01":833,"4311-8/02":833,
    "4312-6/00":833,"4313-4/00":833,"4319-3/00":833,"4321-5/00":833,
    "4322-3/01":833,"4322-3/02":833,"4323-1/00":833,"4329-1/01":833,
    "4329-1/05":833,"4329-1/99":833,"4330-4/01":833,"4330-4/02":833,
    "4330-4/03":833,"4330-4/04":833,"4330-4/05":833,"4391-6/00":833,
    "4399-1/01":833,"4399-1/02":833,"4399-1/03":833,"4399-1/04":833,
    "4399-1/05":833,"4399-1/99":833,
    # COMÉRCIO
    "4511-1/01":515,"4511-1/02":515,"4512-9/01":515,"4512-9/02":515,
    "4520-0/01":515,"4520-0/02":515,"4530-7/01":515,"4530-7/02":515,
    "4530-7/03":515,"4541-2/01":515,"4541-2/02":515,"4541-2/03":515,
    "4542-1/00":515,"4543-9/00":515,"4611-7/00":515,"4612-5/00":515,
    "4613-3/00":515,"4614-1/00":515,"4615-0/00":515,"4616-8/00":515,
    "4617-6/00":515,"4618-4/01":515,"4619-2/00":515,"4621-4/00":515,
    "4622-2/00":515,"4623-1/01":515,"4623-1/08":515,"4631-1/00":515,
    "4632-0/01":515,"4633-8/01":515,"4634-6/01":515,"4635-4/01":515,
    "4636-2/01":515,"4637-1/01":515,"4639-7/01":515,"4641-9/01":515,
    "4642-7/01":515,"4643-5/01":515,"4644-3/01":515,"4645-1/01":515,
    "4646-0/01":515,"4647-8/01":515,"4649-4/01":515,"4651-6/01":515,
    "4652-4/00":515,"4661-3/00":515,"4662-1/00":515,"4663-0/00":515,
    "4664-8/00":515,"4665-6/00":515,"4669-9/01":515,"4671-1/00":515,
    "4672-9/00":515,"4673-7/00":515,"4674-5/00":515,"4679-6/01":515,
    "4681-8/01":515,"4682-6/00":515,"4683-4/00":515,"4684-2/01":515,
    "4685-1/00":515,"4686-9/00":515,"4687-7/01":515,"4689-3/00":515,
    "4691-5/00":515,"4692-3/00":515,"4693-1/00":515,"4711-3/01":515,
    "4711-3/02":515,"4712-1/00":515,"4713-0/01":515,"4713-0/02":515,
    "4721-1/01":515,"4721-1/02":515,"4722-9/01":515,"4723-7/00":515,
    "4724-5/00":515,"4729-6/01":515,"4731-8/00":515,"4732-6/00":515,
    "4741-5/00":515,"4742-3/00":515,"4743-1/00":515,"4744-0/01":515,
    "4744-0/02":515,"4744-0/03":515,"4744-0/04":515,"4744-0/05":515,
    "4744-0/06":515,"4744-0/99":515,"4751-2/01":515,"4751-2/02":515,
    "4752-1/00":515,"4753-9/00":515,"4754-7/01":515,"4755-5/01":515,
    "4756-3/00":515,"4757-1/00":515,"4759-8/01":515,"4761-0/01":515,
    "4762-8/00":515,"4763-6/01":515,"4771-7/01":515,"4771-7/02":515,
    "4771-7/03":515,"4772-5/00":515,"4773-3/00":515,"4774-1/00":515,
    "4781-4/00":515,"4782-2/01":515,"4783-1/01":515,"4784-9/00":515,
    "4785-7/01":515,"4789-0/01":515,"4789-0/99":515,"4791-1/00":515,
    "4792-8/00":515,"4793-6/00":515,
    # TRANSPORTE
    "4911-6/00":620,"4912-4/01":620,"4912-4/02":620,"4921-3/01":620,
    "4921-3/02":620,"4922-1/01":620,"4922-1/02":620,"4923-0/01":620,
    "4923-0/02":620,"4924-8/00":620,"4929-9/01":620,"4929-9/02":620,
    "4929-9/99":620,"4930-2/01":620,"4930-2/02":620,"4930-2/03":620,
    "4940-0/00":620,"4950-7/00":620,"5011-4/01":620,"5011-4/02":620,
    "5012-2/01":620,"5021-1/01":620,"5022-0/01":620,"5030-1/00":620,
    "5091-2/01":620,"5099-8/01":620,"5111-1/00":620,"5112-9/00":620,
    "5120-0/00":620,"5130-7/00":620,"5141-2/00":620,"5142-1/00":620,
    "5150-2/00":620,"5161-8/00":620,"5162-6/00":620,"5163-4/00":620,
    "5172-3/00":620,"5174-0/00":620,"5179-1/00":620,"5211-7/01":620,
    "5211-7/02":620,"5212-5/00":620,"5221-4/00":620,"5222-2/00":620,
    "5223-1/00":620,"5229-0/01":620,"5229-0/02":620,"5229-0/99":620,
    "5231-1/01":620,"5232-0/00":620,"5239-7/00":620,"5240-1/01":620,
    "5250-8/01":620,"5250-8/02":620,"5310-5/01":620,"5310-5/02":620,
    "5320-2/01":620,
    # TI / TECNOLOGIA
    "6201-5/00":736,"6201-5/01":736,"6201-5/02":736,"6202-3/00":736,
    "6203-1/00":736,"6204-0/00":736,"6209-1/00":736,"6311-9/00":736,
    "6319-4/00":736,"6391-7/00":736,"6399-2/00":736,
    # FINANCEIRO
    "6410-7/00":655,"6421-2/00":655,"6422-1/00":655,"6423-9/00":655,
    "6424-7/01":655,"6424-7/02":655,"6424-7/03":655,"6431-0/00":655,
    "6432-8/00":655,"6433-6/00":655,"6434-4/01":655,"6435-2/01":655,
    "6436-1/00":655,"6437-9/00":655,"6438-7/00":655,"6440-9/00":655,
    "6450-6/00":655,"6461-1/00":655,"6462-0/00":655,"6463-8/00":655,
    "6470-1/01":655,"6491-3/00":655,"6492-1/00":655,"6493-0/00":655,
    "6499-9/01":655,"6499-9/99":655,"6511-1/01":655,"6511-1/02":655,
    "6512-0/00":655,"6520-1/00":655,"6521-9/00":655,"6522-7/00":655,
    "6523-5/00":655,"6524-3/00":655,"6525-1/00":655,"6530-8/00":655,
    "6541-3/00":655,"6542-1/00":655,"6550-2/00":655,"6611-8/00":655,
    "6612-6/00":655,"6613-4/00":655,"6619-3/01":655,"6621-5/00":655,
    "6622-3/00":655,"6629-1/00":655,"6630-4/00":655,
    # SAÚDE
    "8610-1/01":647,"8610-1/02":647,"8621-6/01":647,"8621-6/02":647,
    "8622-4/00":647,"8630-5/01":647,"8630-5/02":647,"8630-5/03":647,
    "8630-5/04":647,"8630-5/06":647,"8630-5/07":647,"8630-5/08":647,
    "8640-2/01":647,"8640-2/02":647,"8640-2/03":647,"8640-2/04":647,
    "8640-2/05":647,"8640-2/06":647,"8640-2/07":647,"8640-2/08":647,
    "8640-2/09":647,"8640-2/10":647,"8640-2/11":647,"8640-2/12":647,
    "8640-2/13":647,"8650-0/01":647,"8650-0/02":647,"8650-0/03":647,
    "8650-0/04":647,"8650-0/05":647,"8650-0/06":647,"8650-0/07":647,
    "8660-7/00":647,
    # EDUCAÇÃO
    "8511-2/00":647,"8512-1/00":647,"8513-9/00":647,"8520-1/00":647,
    "8531-7/00":647,"8532-5/00":647,"8533-3/00":647,"8541-4/00":647,
    "8542-2/00":647,"8550-3/01":647,"8550-3/02":647,"8591-1/00":647,
    "8592-9/01":647,"8593-7/00":647,"8599-6/01":647,"8599-6/99":647,
    # ADM PÚBLICA
    "8411-6/00":582,"8412-4/00":582,"8413-2/00":582,"8421-3/00":582,
    "8422-1/00":582,"8423-0/00":582,"8424-8/00":582,"8425-6/00":582,
    "8430-2/00":582,
    # SERVIÇOS GERAIS
    "7711-0/00":515,"7719-5/99":515,"7721-7/00":515,"7722-5/00":515,
    "7723-3/00":515,"7729-2/01":515,"7731-4/00":515,"7732-2/00":515,
    "7733-1/00":515,"7739-0/01":515,"7740-3/00":515,"7810-8/00":515,
    "7820-5/00":515,"7830-2/00":515,"7911-2/00":671,"7912-1/00":671,
    "7990-2/00":671,"8011-1/01":760,"8011-1/02":760,"8012-9/00":760,
    "8020-0/01":760,"8021-8/00":760,"8030-7/00":760,"8111-7/00":680,
    "8112-5/00":680,"8121-4/00":680,"8122-2/00":680,"8129-0/00":680,
    "8130-3/00":680,"8211-3/00":515,"8219-9/01":515,"8219-9/99":515,
    "8220-2/00":515,"8230-0/01":515,"8291-1/00":515,"8292-0/00":515,
    "8299-7/01":515,"8299-7/99":515,
}

# ──────────────────────────────────────────────────────────────────────────────
# FUNÇÕES — MOTOR DE CLASSIFICAÇÃO
# ──────────────────────────────────────────────────────────────────────────────
def formatar_cnae(raw) -> str | None:
    if not raw:
        return None
    s = str(raw).strip().replace(".", "").replace(" ", "")
    if "-" in s and "/" in s:
        return s
    d = re.sub(r"\D", "", s)
    if len(d) == 7:
        return f"{d[:4]}-{d[4]}/{d[5:]}"
    return s

def decodificar_terceiros(codigo: int) -> list[dict]:
    return [
        {"sigla": s, "nome": d["nome"], "aliquota": d["aliquota"]}
        for s, d in ENTIDADES.items()
        if isinstance(codigo, int) and codigo & d["codigo"]
    ]

def classificar(cnae: str, simples: bool = False,
                fap: float = 1.0, convenios: list = None) -> dict:
    convenios = convenios or []
    cnae_fmt  = formatar_cnae(cnae)
    if not cnae_fmt or cnae_fmt not in CNAE_FPAS:
        return {"erro": f"CNAE '{cnae}' não mapeado na tabela FPAS."}
    fpas = CNAE_FPAS[cnae_fmt]
    if fpas not in FPAS_CONFIG:
        return {"erro": f"FPAS {fpas} sem configuração."}
    terceiros_base, rat_base, cod_gps, cod_gfip, descricao = FPAS_CONFIG[fpas]
    if simples:
        codigo_terceiro = None
        obs = "Simples Nacional — campo terceiros em branco"
    elif fpas in FPAS_SEMPRE_ZERO:
        codigo_terceiro = 0
        obs = f"FPAS {fpas}: terceiros sempre zero"
    else:
        codigo_terceiro = terceiros_base
        removidos = []
        for ent in convenios:
            bit = ENTIDADES.get(ent.upper(), {}).get("codigo", 0)
            if bit and (codigo_terceiro & bit):
                codigo_terceiro &= ~bit
                removidos.append(ent.upper())
        obs = f"Convênio direto: {', '.join(removidos)} removido(s)" if removidos else "Classificação padrão"
    rat_ajustado = round(rat_base * fap, 2)
    entidades    = decodificar_terceiros(codigo_terceiro) if codigo_terceiro else []
    total_terc   = sum(e["aliquota"] for e in entidades)
    return {
        "cnae": cnae_fmt, "fpas": fpas, "fpas_descricao": descricao,
        "codigo_terceiro": codigo_terceiro, "perc_acid_trabalho": rat_base,
        "codigo_sat": rat_ajustado, "codigo_gps": cod_gps,
        "codigo_gfip": cod_gfip, "entidades": entidades,
        "total_terceiros_pct": total_terc, "observacao": obs, "erro": None,
    }

# ──────────────────────────────────────────────────────────────────────────────
# FUNÇÕES — SERVIÇO CNPJ
# ──────────────────────────────────────────────────────────────────────────────
APIS = [
    "https://brasilapi.com.br/api/cnpj/v1/{cnpj}",
    "https://receitaws.com.br/v1/cnpj/{cnpj}",
    "https://minhareceita.org/{cnpj}",
]
HEADERS = {"User-Agent": "Mozilla/5.0 (classificador-fpas/2.0)"}

def limpar_cnpj(cnpj: str) -> str:
    return re.sub(r"\D", "", str(cnpj))

def validar_cnpj(cnpj: str) -> bool:
    c = limpar_cnpj(cnpj)
    if len(c) != 14 or len(set(c)) == 1:
        return False
    def calc(c, n):
        s = sum(int(c[i]) * ((n - i) % (n - 1) or (n - 1)) for i in range(n - 1))
        r = 11 - s % 11
        return 0 if r >= 10 else r
    return int(c[12]) == calc(c, 13) and int(c[13]) == calc(c, 14)

def normalizar_resposta(data: dict, cnpj: str) -> dict:
    cnae_codigo = (
        data.get("cnae_fiscal")
        or data.get("cnae_fiscal_codigo")
        or (data.get("atividade_principal", [{}])[0].get("code", "")
            if isinstance(data.get("atividade_principal"), list) else "")
    )
    cnae_descricao = (
        data.get("cnae_fiscal_descricao")
        or (data.get("atividade_principal", [{}])[0].get("text", "")
            if isinstance(data.get("atividade_principal"), list) else "")
    )
    cnae_str = str(cnae_codigo).zfill(7) if cnae_codigo else ""
    cnae_fmt = f"{cnae_str[:4]}-{cnae_str[4]}/{cnae_str[5:]}" if len(cnae_str) == 7 else cnae_str
    simples  = (data.get("opcao_pelo_simples")
                or (data.get("simples", {}).get("optante", False)
                    if isinstance(data.get("simples"), dict) else False))
    return {
        "cnpj":             cnpj,
        "razao_social":     data.get("razao_social") or data.get("nome", ""),
        "nome_fantasia":    data.get("nome_fantasia", ""),
        "situacao":         data.get("descricao_situacao_cadastral") or data.get("situacao", ""),
        "cnae_codigo":      cnae_fmt,
        "cnae_descricao":   cnae_descricao,
        "simples":          bool(simples),
        "natureza_juridica":data.get("descricao_natureza_juridica") or data.get("natureza_juridica", ""),
        "porte":            data.get("descricao_porte") or data.get("porte", ""),
        "logradouro":       data.get("logradouro", ""),
        "numero":           data.get("numero", ""),
        "bairro":           data.get("bairro", ""),
        "municipio":        data.get("municipio", ""),
        "uf":               data.get("uf", ""),
        "cep":              data.get("cep", ""),
        "data_inicio":      data.get("data_inicio_atividade") or data.get("abertura", ""),
        "erro":             None,
    }

def consultar_cnpj(cnpj_raw: str, delay: float = 1.0) -> dict:
    cnpj = limpar_cnpj(cnpj_raw)
    if not validar_cnpj(cnpj):
        return {"erro": f"CNPJ inválido: {cnpj_raw}"}
    time.sleep(delay)
    for url_tpl in APIS:
        try:
            r = requests.get(url_tpl.format(cnpj=cnpj), headers=HEADERS, timeout=12)
            if r.status_code == 200:
                return normalizar_resposta(r.json(), cnpj)
            if r.status_code == 429:
                time.sleep(60)
        except Exception:
            continue
    return {"erro": f"CNPJ {cnpj} não encontrado em nenhuma API."}

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS HTML
# ──────────────────────────────────────────────────────────────────────────────
def metric_card(value, label, cls=""):
    return f"""
    <div class="tr-metric {cls}">
        <div class="tr-metric-value">{value}</div>
        <div class="tr-metric-label">{label}</div>
    </div>"""

def result_item(label, value, highlight=False):
    cls = "highlight" if highlight else ""
    return f"""
    <div class="result-item">
        <div class="result-item-label">{label}</div>
        <div class="result-item-value {cls}">{value}</div>
    </div>"""

def entidade_pills(entidades: list) -> str:
    return "".join(
        f'<span class="ent-pill">{e["sigla"]} {e["aliquota"]}%</span>'
        for e in entidades
    )

# ──────────────────────────────────────────────────────────────────────────────
# APP STREAMLIT
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Classificador FPAS | Domínio Sistemas",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

# ── HEADER ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="tr-header">
    <div class="tr-logo-box">TR</div>
    <div>
        <div class="tr-title">Classificador FPAS / Terceiros / SEFIP</div>
        <div class="tr-subtitle">DOMÍNIO SISTEMAS &nbsp;·&nbsp; Thomson Reuters &nbsp;·&nbsp; IN RFB nº 971/2009</div>
    </div>
    <div class="tr-badge">v2.0</div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div style="color:{TR_ORANGE};font-size:13px;font-weight:700;'
                f'letter-spacing:1px;margin-bottom:16px;">⚙ CONFIGURAÇÕES</div>',
                unsafe_allow_html=True)

    st.markdown('<div class="tr-sidebar-section"><div class="tr-sidebar-title">📊 Parâmetros SEFIP</div>',
                unsafe_allow_html=True)
    fap = st.number_input("FAP — Fator Acidentário", min_value=0.5,
                          max_value=2.0, value=1.0, step=0.01,
                          help="Multiplica o RAT. Padrão = 1,00")
    delay = st.number_input("Intervalo entre consultas (s)", min_value=0.3,
                            max_value=5.0, value=1.0, step=0.1,
                            help="Respeita o rate limit das APIs públicas")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="tr-sidebar-section"><div class="tr-sidebar-title">🤝 Convênios Diretos</div>',
                unsafe_allow_html=True)
    convenios = st.multiselect(
        "Entidades com convênio direto",
        options=["SENAI","SESI","SENAC","SESC","SEBRAE","SENAR","SEST","SENAT","SESCOOP"],
        help="Serão removidas do código de terceiros",
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="tr-sidebar-section"><div class="tr-sidebar-title">🔗 APIs Utilizadas</div>',
                unsafe_allow_html=True)
    st.markdown(f"""
    <div style="font-size:11px;color:{TR_TEXT_MUTED};line-height:1.8;">
        1️⃣ BrasilAPI<br>
        2️⃣ ReceitaWS<br>
        3️⃣ MinhaReceita<br>
        <span style="color:{TR_WARNING};">Fallback automático</span>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown(f"""
    <div style="font-size:10px;color:{TR_TEXT_MUTED};margin-top:20px;line-height:1.6;">
        <b style="color:{TR_ORANGE};">Base legal:</b><br>
        IN RFB nº 971/2009<br>
        IN RFB nº 2.110/2022<br>
        Decreto-Lei nº 1.146/1970<br>
        Lei nº 10.256/2001
    </div>
    """, unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab_lote, tab_individual, tab_tabela = st.tabs([
    "📂  Processamento em Lote",
    "🔍  Consulta Individual",
    "📖  Tabela FPAS / Terceiros",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — PROCESSAMENTO EM LOTE
# ══════════════════════════════════════════════════════════════════════════════
with tab_lote:

    st.markdown('<div class="tr-card"><div class="tr-card-title">📂 Upload da Planilha</div>',
                unsafe_allow_html=True)

    col_up, col_ex = st.columns([3, 1])
    with col_up:
        arquivo = st.file_uploader(
            "Arraste ou selecione o arquivo Excel com os CNPJs",
            type=["xlsx"],
            label_visibility="collapsed",
        )
    with col_ex:
        st.markdown(f'<div style="font-size:11px;color:{TR_TEXT_MUTED};">Formato esperado:</div>',
                    unsafe_allow_html=True)
        st.dataframe(
            pd.DataFrame({"cnpj": ["12.345.678/0001-99", "98.765.432/0001-10"]}),
            hide_index=True, use_container_width=True, height=90,
        )
    st.markdown('</div>', unsafe_allow_html=True)

    if arquivo:
        df_raw = pd.read_excel(arquivo, dtype=str)
        st.success(f"✅ **{len(df_raw)} registros** carregados com sucesso.")

        # Detecta coluna CNPJ
        col_cnpj = next(
            (c for c in df_raw.columns
             if c.lower() in ["cnpj","cgc","cnpj/cpf","documento","cpf_cnpj"]),
            None
        )
        if not col_cnpj:
            col_cnpj = st.selectbox(
                "⚠️ Selecione a coluna que contém os CNPJs:",
                df_raw.columns.tolist()
            )

        st.info(f"📌 Coluna CNPJ detectada: **{col_cnpj}**  |  "
                f"FAP configurado: **{fap}**  |  "
                f"Convênios: **{', '.join(convenios) if convenios else 'Nenhum'}**")

        with st.expander("👁️ Pré-visualização dos dados"):
            st.dataframe(df_raw.head(10), use_container_width=True)

        st.markdown("---")

        if st.button("🚀 Iniciar Classificação em Lote", type="primary",
                     use_container_width=True):

            resultados = []
            total      = len(df_raw)
            progress   = st.progress(0, text="Aguardando...")
            col_log, col_stat = st.columns([2, 1])

            with col_log:
                log_area = st.empty()
            with col_stat:
                stat_area = st.empty()

            logs   = []
            ok_n   = 0
            err_n  = 0

            for i, row in df_raw.iterrows():
                cnpj_raw = str(row[col_cnpj]).strip()
                pct      = int((i + 1) / total * 100)
                progress.progress(pct, text=f"⏳ Processando {i+1}/{total} — {cnpj_raw}")

                # Consulta RF
                dados_rf = consultar_cnpj(cnpj_raw, delay=delay)

                if dados_rf.get("erro"):
                    err_n += 1
                    logs.append(f"❌ {cnpj_raw}: {dados_rf['erro']}")
                    resultados.append({
                        "cnpj": cnpj_raw, "razao_social": "", "situacao_cadastral": "",
                        "cnae_codigo": "", "cnae_descricao": "", "simples_nacional": "",
                        "codigo_fpas": "", "fpas_descricao": "", "codigo_terceiro": "",
                        "perc_acid_trabalho": "", "codigo_sat": "", "codigo_gps": "",
                        "codigo_gfip": "", "total_terceiros_pct": "",
                        "observacao": dados_rf["erro"], "status": "ERRO_RF",
                    })
                else:
                    simples  = dados_rf.get("simples", False)
                    classif  = classificar(dados_rf.get("cnae_codigo",""),
                                           simples=simples, fap=fap, convenios=convenios)
                    if classif.get("erro"):
                        err_n += 1
                        status = "ERRO_FPAS"
                        logs.append(f"⚠️ {cnpj_raw} | {dados_rf.get('razao_social','')} "
                                    f"| {classif['erro']}")
                    else:
                        ok_n  += 1
                        status = "OK"
                        cod3   = classif['codigo_terceiro']
                        cod3_f = f"{cod3:04d}" if isinstance(cod3, int) else "—"
                        logs.append(f"✅ {cnpj_raw} | {dados_rf.get('razao_social','')[:30]} "
                                    f"| FPAS {classif['fpas']} | 3ºs {cod3_f}")

                    resultados.append({
                        "cnpj":              limpar_cnpj(cnpj_raw),
                        "razao_social":      dados_rf.get("razao_social",""),
                        "nome_fantasia":     dados_rf.get("nome_fantasia",""),
                        "situacao_cadastral":dados_rf.get("situacao",""),
                        "natureza_juridica": dados_rf.get("natureza_juridica",""),
                        "porte":             dados_rf.get("porte",""),
                        "data_inicio":       dados_rf.get("data_inicio",""),
                        "logradouro":        dados_rf.get("logradouro",""),
                        "numero":            dados_rf.get("numero",""),
                        "bairro":            dados_rf.get("bairro",""),
                        "municipio":         dados_rf.get("municipio",""),
                        "uf":                dados_rf.get("uf",""),
                        "cep":               dados_rf.get("cep",""),
                        "cnae_codigo":       dados_rf.get("cnae_codigo",""),
                        "cnae_descricao":    dados_rf.get("cnae_descricao",""),
                        "simples_nacional":  "SIM" if simples else "NÃO",
                        "codigo_fpas":       classif.get("fpas",""),
                        "fpas_descricao":    classif.get("fpas_descricao",""),
                        "codigo_terceiro":   (f"{classif['codigo_terceiro']:04d}"
                                              if isinstance(classif.get("codigo_terceiro"), int)
                                              else classif.get("codigo_terceiro","")),
                        "perc_acid_trabalho":classif.get("perc_acid_trabalho",""),
                        "codigo_sat":        classif.get("codigo_sat",""),
                        "codigo_gps":        classif.get("codigo_gps",""),
                        "codigo_gfip":       classif.get("codigo_gfip",""),
                        "total_terceiros_pct":classif.get("total_terceiros_pct",""),
                        "observacao":        classif.get("observacao",""),
                        "status":            status,
                    })

                log_area.text_area("📋 Log", "\n".join(logs[-12:]),
                                   height=260, label_visibility="collapsed")
                stat_area.markdown(f"""
                <div class="tr-metrics" style="flex-direction:column;">
                    {metric_card(i+1, "Processados")}
                    {metric_card(ok_n, "Sucesso", "success")}
                    {metric_card(err_n, "Erros", "error")}
                </div>
                """, unsafe_allow_html=True)

            progress.progress(100, text="✅ Processamento concluído!")

            # ── RESULTADO ─────────────────────────────────────────────────────
            df_res = pd.DataFrame(resultados)
            st.session_state["df_resultado"] = df_res

            st.markdown("---")
            st.markdown(f'<div class="tr-card-title">📊 Resultado Final</div>',
                        unsafe_allow_html=True)

            df_ok  = df_res[df_res["status"] == "OK"]
            df_err = df_res[df_res["status"] != "OK"]

            st.markdown(f"""
            <div class="tr-metrics">
                {metric_card(total, "Total")}
                {metric_card(len(df_ok), "Classificados", "success")}
                {metric_card(len(df_err), "Erros", "error")}
                {metric_card(f"{len(df_ok)/total*100:.0f}%", "Taxa de Sucesso",
                             "success" if len(df_ok)/total > 0.8 else "warning")}
            </div>
            """, unsafe_allow_html=True)

            st.dataframe(
                df_res[[
                    "cnpj","razao_social","situacao_cadastral",
                    "cnae_codigo","cnae_descricao","simples_nacional",
                    "codigo_fpas","fpas_descricao","codigo_terceiro",
                    "perc_acid_trabalho","codigo_sat","codigo_gps",
                    "codigo_gfip","total_terceiros_pct","status","observacao",
                ]],
                use_container_width=True, hide_index=True, height=380,
            )

            # Resumo por FPAS
            if len(df_ok) > 0:
                with st.expander("📈 Resumo por FPAS"):
                    resumo = (df_ok.groupby(["codigo_fpas","fpas_descricao"])
                              .size().reset_index(name="qtd_empresas")
                              .sort_values("qtd_empresas", ascending=False))
                    st.dataframe(resumo, use_container_width=True, hide_index=True)

            if len(df_err) > 0:
                with st.expander(f"⚠️ {len(df_err)} registro(s) com erro"):
                    st.dataframe(
                        df_err[["cnpj","razao_social","status","observacao"]],
                        use_container_width=True, hide_index=True,
                    )

            # ── DOWNLOADS ─────────────────────────────────────────────────────
            st.markdown("---")
            st.markdown(f'<div class="tr-card-title">⬇️ Download</div>',
                        unsafe_allow_html=True)

            col_d1, col_d2 = st.columns(2)
            with col_d1:
                buf = io.BytesIO()
                with pd.ExcelWriter(buf, engine="openpyxl") as w:
                    df_res.to_excel(w, sheet_name="Classificacao_FPAS", index=False)
                    if len(df_err) > 0:
                        df_err.to_excel(w, sheet_name="Erros", index=False)
                st.download_button(
                    "📥 Baixar Excel Completo (.xlsx)",
                    data=buf.getvalue(),
                    file_name="classificacao_fpas_dominio.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with col_d2:
                csv = df_res.to_csv(index=False, sep=";", encoding="utf-8-sig")
                st.download_button(
                    "📥 Baixar CSV (separador ;)",
                    data=csv,
                    file_name="classificacao_fpas_dominio.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — CONSULTA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_individual:

    st.markdown('<div class="tr-card"><div class="tr-card-title">🔍 Consulta Individual de CNPJ</div>',
                unsafe_allow_html=True)

    col_inp, col_btn = st.columns([3, 1])
    with col_inp:
        cnpj_input = st.text_input(
            "CNPJ", placeholder="00.000.000/0000-00",
            label_visibility="collapsed",
        )
    with col_btn:
        buscar = st.button("🔍 Consultar", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    if buscar and cnpj_input:
        with st.spinner("🔄 Consultando Receita Federal..."):
            dados_rf = consultar_cnpj(cnpj_input, delay=0.3)

        if dados_rf.get("erro"):
            st.error(f"❌ {dados_rf['erro']}")
        else:
            simples = dados_rf.get("simples", False)
            classif = classificar(dados_rf.get("cnae_codigo",""),
                                  simples=simples, fap=fap, convenios=convenios)

            # Card empresa
            st.markdown(f"""
            <div class="tr-card">
                <div class="tr-card-title">🏢 Dados da Empresa</div>
                <div class="result-grid">
                    {result_item("CNPJ", dados_rf['cnpj'])}
                    {result_item("Razão Social", dados_rf['razao_social'], True)}
                    {result_item("Nome Fantasia", dados_rf.get('nome_fantasia','—') or '—')}
                    {result_item("Situação Cadastral", dados_rf.get('situacao','—'))}
                    {result_item("Natureza Jurídica", dados_rf.get('natureza_juridica','—'))}
                    {result_item("Porte", dados_rf.get('porte','—'))}
                    {result_item("Simples Nacional", '✅ SIM' if simples else '❌ NÃO')}
                    {result_item("Data de Início", dados_rf.get('data_inicio','—'))}
                    {result_item("Município/UF", f"{dados_rf.get('municipio','—')}/{dados_rf.get('uf','—')}")}
                    {result_item("CEP", dados_rf.get('cep','—'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Card CNAE
            st.markdown(f"""
            <div class="tr-card">
                <div class="tr-card-title">🏭 CNAE Principal</div>
                <div class="result-grid">
                    {result_item("Código CNAE", dados_rf.get('cnae_codigo','—'), True)}
                    {result_item("Descrição", dados_rf.get('cnae_descricao','—'))}
                </div>
            </div>
            """, unsafe_allow_html=True)

            if classif.get("erro"):
                st.warning(f"⚠️ {classif['erro']}")
            else:
                cod3   = classif['codigo_terceiro']
                cod3_f = f"{cod3:04d}" if isinstance(cod3, int) else "Em branco (Simples)"

                # Card FPAS / SEFIP
                st.markdown(f"""
                <div class="tr-card">
                    <div class="tr-card-title">📋 Classificação FPAS / SEFIP</div>
                    <div class="result-grid">
                        {result_item("Código FPAS", classif['fpas'], True)}
                        {result_item("Descrição FPAS", classif['fpas_descricao'])}
                        {result_item("Código Terceiros", cod3_f, True)}
                        {result_item("RAT (base)", f"{classif['perc_acid_trabalho']}%")}
                        {result_item("SAT (RAT × FAP)", f"{classif['codigo_sat']}%", True)}
                        {result_item("Código GPS", classif['codigo_gps'])}
                        {result_item("Código GFIP", classif['codigo_gfip'])}
                        {result_item("Total Terceiros", f"{classif['total_terceiros_pct']:.1f}%", True)}
                    </div>
                    <div style="margin-top:14px;">
                        <div style="font-size:11px;color:{TR_TEXT_MUTED};
                                    text-transform:uppercase;letter-spacing:0.5px;
                                    margin-bottom:6px;">Entidades Beneficiadas</div>
                        {entidade_pills(classif['entidades']) or
                         f'<span style="color:{TR_TEXT_MUTED};font-size:12px;">Nenhuma</span>'}
                    </div>
                    <div style="margin-top:10px;font-size:11px;color:{TR_TEXT_MUTED};">
                        ℹ️ {classif['observacao']}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Tabela de entidades detalhada
                if classif["entidades"]:
                    with st.expander("📊 Detalhamento das Entidades e Alíquotas"):
                        df_ent = pd.DataFrame(classif["entidades"])
                        df_ent.columns = ["Sigla", "Entidade", "Alíquota (%)"]
                        total_row = pd.DataFrame([{
                            "Sigla": "TOTAL", "Entidade": "", "Alíquota (%)": classif["total_terceiros_pct"]
                        }])
                        df_ent = pd.concat([df_ent, total_row], ignore_index=True)
                        st.dataframe(df_ent, use_container_width=True, hide_index=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — TABELA DE REFERÊNCIA
# ══════════════════════════════════════════════════════════════════════════════
with tab_tabela:

    st.markdown('<div class="tr-card"><div class="tr-card-title">📖 Tabela de Referência FPAS / Terceiros</div>',
                unsafe_allow_html=True)

    # Monta tabela de referência
    ref_rows = []
    for fpas, (terc, rat, gps, gfip, desc) in FPAS_CONFIG.items():
        ents = decodificar_terceiros(terc)
        total_pct = sum(e["aliquota"] for e in ents)
        siglas = " + ".join(e["sigla"] for e in ents) if ents else "—"
        ref_rows.append({
            "FPAS": fpas,
            "Descrição": desc,
            "Cód. Terceiros": f"{terc:04d}",
            "Entidades": siglas,
            "Total 3ºs (%)": f"{total_pct:.1f}%",
            "RAT Base (%)": f"{rat}%",
            "Cód. GPS": gps,
            "Cód. GFIP": gfip,
        })
    df_ref = pd.DataFrame(ref_rows)

    col_f1, col_f2 = st.columns([2, 2])
    with col_f1:
        busca_fpas = st.text_input("🔎 Filtrar por FPAS ou Descrição",
                                   placeholder="Ex: 833 ou Construção")
    with col_f2:
        st.markdown(f'<div style="color:{TR_TEXT_MUTED};font-size:11px;margin-top:28px;">'
                    f'{len(df_ref)} registros na tabela FPAS</div>', unsafe_allow_html=True)

    if busca_fpas:
        mask = (df_ref["FPAS"].astype(str).str.contains(busca_fpas, case=False)
                | df_ref["Descrição"].str.contains(busca_fpas, case=False)
                | df_ref["Entidades"].str.contains(busca_fpas, case=False))
        df_ref = df_ref[mask]

    st.dataframe(df_ref, use_container_width=True, hide_index=True, height=480)
    st.markdown('</div>', unsafe_allow_html=True)

    # Tabela de entidades bitmask
    with st.expander("🔢 Tabela de Entidades — Lógica Bitmask"):
        ent_rows = [
            {"Código (bitmask)": d["codigo"], "Sigla": s,
             "Nome Completo": d["nome"], "Alíquota (%)": d["aliquota"]}
            for s, d in ENTIDADES.items()
        ]
        df_ent_ref = pd.DataFrame(ent_rows)
        st.dataframe(df_ent_ref, use_container_width=True, hide_index=True)
        st.markdown(f"""
        <div style="font-size:11px;color:{TR_TEXT_MUTED};margin-top:8px;">
        💡 O <b style="color:{TR_ORANGE};">Código de Terceiros</b> é a <b>soma dos códigos bitmask</b>
        das entidades ativas. Ex: FNDE(1) + INCRA(2) + SENAC(16) + SESC(32) + SEBRAE(64) = <b>0115</b>
        </div>
        """, unsafe_allow_html=True)

# ── RODAPÉ ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tr-footer">
    <span>DOMÍNIO SISTEMAS</span> &nbsp;·&nbsp; Thomson Reuters &nbsp;·&nbsp;
    Classificador FPAS / Terceiros / SEFIP &nbsp;·&nbsp;
    Base legal: IN RFB nº 971/2009 &nbsp;·&nbsp;
    <span>v2.0</span>
</div>
""", unsafe_allow_html=True)
