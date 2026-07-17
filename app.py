import io
import os
import re
import time
import unicodedata
import zipfile
import requests
import pandas as pd
import streamlit as st
from datetime import date, datetime

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

CSS = f"""
<style>
  html, body, [data-testid="stAppViewContainer"] {{
      background-color: {TR_BG} !important;
      color: {TR_TEXT} !important;
      font-family: 'Segoe UI', Arial, sans-serif !important;
  }}
  section[data-testid="stSidebar"] {{
      background-color: #111111 !important;
      border-right: 2px solid {TR_ORANGE} !important;
      display: block !important;
      visibility: visible !important;
      min-width: 21rem !important;
      transform: translateX(0) !important;
      left: 0 !important;
  }}
  section[data-testid="stSidebar"] > div:first-child {{ background-color: #111111 !important; }}
  section[data-testid="stSidebar"] * {{ color: {TR_TEXT} !important; }}
  [data-testid="collapsedControl"] {{
      display: flex !important; visibility: visible !important;
      opacity: 1 !important; color: {TR_ORANGE} !important;
  }}
  .tr-header {{
      background: linear-gradient(135deg,#111 0%,#1f1f1f 60%,#2a1500 100%);
      border-bottom: 3px solid {TR_ORANGE}; padding: 18px 28px 14px;
      border-radius: 10px; margin-bottom: 24px; display: flex; align-items: center; gap: 18px;
  }}
  .tr-logo-box {{
      background:{TR_ORANGE}; border-radius:8px; width:52px; height:52px;
      display:flex; align-items:center; justify-content:center;
      font-size:26px; font-weight:900; color:#fff; flex-shrink:0;
  }}
  .tr-title   {{ font-size:22px; font-weight:700; color:{TR_TEXT}; margin:0; line-height:1.2; }}
  .tr-subtitle {{ font-size:12px; color:{TR_TEXT_MUTED}; margin:2px 0 0; letter-spacing:.5px; }}
  .tr-badge {{
      margin-left:auto; background:{TR_ORANGE}; color:#fff; font-size:10px; font-weight:700;
      padding:4px 10px; border-radius:20px; letter-spacing:1px; text-transform:uppercase;
  }}
  .tr-card {{
      background:{TR_CARD}; border:1px solid {TR_BORDER};
      border-radius:10px; padding:18px 20px; margin-bottom:16px;
  }}
  .tr-card-title {{
      font-size:13px; font-weight:700; color:{TR_ORANGE}; text-transform:uppercase;
      letter-spacing:1px; margin-bottom:12px; border-bottom:1px solid {TR_BORDER}; padding-bottom:8px;
  }}
  .tr-metrics {{ display:flex; gap:12px; flex-wrap:wrap; margin-bottom:20px; }}
  .tr-metric {{
      background:{TR_CARD}; border:1px solid {TR_BORDER}; border-radius:10px;
      padding:14px 20px; flex:1; min-width:120px; text-align:center;
  }}
  .tr-metric-value {{ font-size:28px; font-weight:800; color:{TR_ORANGE}; line-height:1; }}
  .tr-metric-label {{ font-size:11px; color:{TR_TEXT_MUTED}; margin-top:4px; text-transform:uppercase; letter-spacing:.5px; }}
  .tr-metric.success .tr-metric-value {{ color:{TR_SUCCESS}; }}
  .tr-metric.error   .tr-metric-value {{ color:{TR_ERROR};   }}
  .tr-metric.warning .tr-metric-value {{ color:{TR_WARNING}; }}
  [data-testid="stDataFrame"] {{ border:1px solid {TR_BORDER} !important; border-radius:8px !important; }}
  .stButton > button {{
      background:{TR_ORANGE} !important; color:#fff !important; border:none !important;
      border-radius:6px !important; font-weight:700 !important; letter-spacing:.5px !important;
  }}
  .stButton > button:hover {{ background:{TR_ORANGE_DARK} !important; }}
  .stDownloadButton > button {{
      background:#1a3a1a !important; color:{TR_SUCCESS} !important;
      border:1px solid {TR_SUCCESS} !important; border-radius:6px !important; font-weight:700 !important;
  }}
  .stDownloadButton > button:hover {{ background:{TR_SUCCESS} !important; color:#fff !important; }}
  .stTextInput input, .stNumberInput input {{
      background:{TR_CARD2} !important; color:{TR_TEXT} !important;
      border:1px solid {TR_BORDER} !important; border-radius:6px !important;
  }}
  .stTextArea textarea {{
      background:{TR_CARD2} !important; color:{TR_TEXT} !important;
      border:1px solid {TR_BORDER} !important; border-radius:6px !important;
      font-family:'Courier New',monospace !important; font-size:13px !important;
  }}
  .stTextArea textarea:focus {{ border-color:{TR_ORANGE} !important; box-shadow:0 0 0 2px rgba(255,128,0,.2) !important; }}
  .stMultiSelect [data-baseweb="select"], .stSelectbox [data-baseweb="select"] {{
      background:{TR_CARD2} !important; border:1px solid {TR_BORDER} !important; border-radius:6px !important;
  }}
  .stTabs [data-baseweb="tab-list"] {{
      background:{TR_CARD} !important; border-radius:8px 8px 0 0 !important;
      border-bottom:2px solid {TR_ORANGE} !important; gap:4px !important;
  }}
  .stTabs [data-baseweb="tab"] {{ color:{TR_TEXT_MUTED} !important; font-weight:600 !important; border-radius:6px 6px 0 0 !important; }}
  .stTabs [aria-selected="true"] {{ background:{TR_ORANGE} !important; color:#fff !important; }}
  .streamlit-expanderHeader {{
      background:{TR_CARD2} !important; border:1px solid {TR_BORDER} !important;
      border-radius:6px !important; color:{TR_TEXT} !important;
  }}
  .stProgress > div > div {{ background:{TR_ORANGE} !important; }}
  .result-grid {{
      display:grid; grid-template-columns:repeat(auto-fill,minmax(200px,1fr)); gap:10px; margin-top:12px;
  }}
  .result-item {{ background:{TR_CARD2}; border:1px solid {TR_BORDER}; border-radius:8px; padding:10px 14px; }}
  .result-item-label {{ font-size:10px; color:{TR_TEXT_MUTED}; text-transform:uppercase; letter-spacing:.5px; }}
  .result-item-value {{ font-size:16px; font-weight:700; color:{TR_TEXT}; margin-top:2px; }}
  .result-item-value.highlight {{ color:{TR_ORANGE}; }}
  .cnpj-preview-box {{
      background:{TR_CARD2}; border:1px solid {TR_BORDER}; border-radius:8px; padding:12px 16px; margin-top:10px;
  }}
  .cnpj-chip {{
      display:inline-block; background:#2a1500; border:1px solid {TR_ORANGE};
      color:{TR_TEXT}; border-radius:6px; padding:3px 10px;
      font-size:12px; font-family:'Courier New',monospace; margin:3px;
  }}
  .cnpj-chip.invalido {{ border-color:{TR_ERROR}; color:{TR_ERROR}; background:#2b0d0d; }}
  .tipo-row {{
      background:{TR_CARD2}; border:1px solid {TR_BORDER}; border-radius:8px; padding:12px 14px; margin-bottom:8px;
  }}
  .tr-footer {{
      text-align:center; color:{TR_TEXT_MUTED}; font-size:11px;
      margin-top:40px; padding:16px; border-top:1px solid {TR_BORDER};
  }}
  .tr-footer span {{ color:{TR_ORANGE}; font-weight:700; }}
  ::-webkit-scrollbar {{ width:6px; height:6px; }}
  ::-webkit-scrollbar-track {{ background:{TR_BG}; }}
  ::-webkit-scrollbar-thumb {{ background:{TR_ORANGE}; border-radius:3px; }}
  #MainMenu {{ visibility: hidden; height: 0; }}
  footer {{ visibility: hidden; height: 0; }}
  header {{ visibility: hidden; height: 0; }}
  .block-container {{ padding-top:1rem !important; }}
</style>

<script>
  (function() {{
    function abrirSidebar() {{
      try {{
        var doc = window.parent.document;
        var sidebar = doc.querySelector('section[data-testid="stSidebar"]');
        if (!sidebar) return;
        if (sidebar.getBoundingClientRect().width < 50) {{
          var btn = doc.querySelector('[data-testid="collapsedControl"] button');
          if (btn) btn.click();
        }}
      }} catch(e) {{}}
    }}
    if (document.readyState === 'complete') {{ setTimeout(abrirSidebar, 500); }}
    else {{ window.addEventListener('load', function() {{ setTimeout(abrirSidebar, 500); }}); }}
  }})();
</script>
"""

TIPOS_EMPRESA = {
    1: "Empresa",
    2: "Tomador de Servico",
    3: "Empreitada Parcial",
    4: "Obra Propria",
    5: "Empreitada Total",
    6: "Cooperativa de Trabalho",
}

# ──────────────────────────────────────────────────────────────────────────────
# MUNICIPIOS
# ──────────────────────────────────────────────────────────────────────────────
def _normalizar(s: str) -> str:
    s = str(s).strip().upper()
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = re.sub(r"['\-]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s

def _resolver_caminho_arquivo(nome_arquivo: str) -> str | None:
    """
    Tenta localizar o arquivo em múltiplos caminhos:
    1. Caminho absoluto do Streamlit Cloud (/mount/src/foservicos/)
    2. Diretório do próprio app.py (__file__)
    3. Diretório de trabalho atual (os.getcwd())
    4. Nome direto (relativo)
    Retorna o primeiro caminho válido encontrado ou None.
    """
    candidatos = [
        os.path.join("/mount/src/foservicos", nome_arquivo),
        os.path.join(os.path.dirname(os.path.abspath(__file__)), nome_arquivo),
        os.path.join(os.getcwd(), nome_arquivo),
        nome_arquivo,
    ]
    for c in candidatos:
        if os.path.isfile(c):
            return c
    return None

def _carregar_municipios():

    DIRETORIOS = [
        "/mount/src/foservicos",
        os.path.dirname(os.path.abspath(__file__)),
        os.getcwd(),
        ".",
    ]

    # Nomes exatos para tentar primeiro (do mais provavel ao menos)
    NOMES_CANDIDATOS = [
        "RELACAO DE MUNICIPIOS.xlsx",
        "RELAÇÃO DE MUNICÍPIOS.xlsx",
        "Relação de Municípios.xlsx",
        "Relacao de Municipios.xlsx",
        "RELAÇÃO DE MUNICIPIOS.xlsx",
        "RELACAO DE MUNICÍPIOS.xlsx",
        "relacao de municipios.xlsx",
    ]

    caminho_encontrado = None

    # Tentativa 1: nomes exatos
    for pasta in DIRETORIOS:
        for nome in NOMES_CANDIDATOS:
            tentativa = os.path.join(pasta, nome)
            if os.path.isfile(tentativa):
                caminho_encontrado = tentativa
                break
        if caminho_encontrado:
            break

    # Tentativa 2: varredura por similaridade (pega qualquer xlsx com MUNICIPIO no nome)
    if not caminho_encontrado:
        for pasta in DIRETORIOS:
            if not os.path.isdir(pasta):
                continue
            try:
                for arq in os.listdir(pasta):
                    if not arq.lower().endswith(".xlsx"):
                        continue
                    arq_norm = unicodedata.normalize("NFD", arq.upper())
                    arq_norm = "".join(
                        c for c in arq_norm if unicodedata.category(c) != "Mn"
                    )
                    if "MUNICIPIO" in arq_norm:
                        caminho_encontrado = os.path.join(pasta, arq)
                        break
            except Exception:
                continue
            if caminho_encontrado:
                break

    # Tentativa 3: qualquer xlsx no diretório (último recurso)
    if not caminho_encontrado:
        for pasta in DIRETORIOS:
            if not os.path.isdir(pasta):
                continue
            try:
                xlsx_list = [
                    os.path.join(pasta, f)
                    for f in os.listdir(pasta)
                    if f.lower().endswith(".xlsx")
                ]
                if xlsx_list:
                    # Registra todos encontrados no debug para o usuário escolher
                    caminho_encontrado = xlsx_list[0]
                    break
            except Exception:
                continue

    if not caminho_encontrado:
        # Monta lista de todos os arquivos para debug
        _todos = {}
        for pasta in DIRETORIOS:
            try:
                _todos[pasta] = os.listdir(pasta)
            except Exception as e:
                _todos[pasta] = [str(e)]
        return {}, {
            "erro_fatal": "Nenhum arquivo .xlsx encontrado. Verifique o repositorio.",
            "total": 0,
            "diretorios_listados": _todos,
        }

    try:
        df = pd.read_excel(
            caminho_encontrado,
            sheet_name=0,
            engine="openpyxl",
            dtype=str,
            header=0,
        )
        df.columns = [
            unicodedata.normalize("NFC", str(c)).strip()
            .lstrip("\ufeff").replace("\xa0", " ").replace("\u200b", "")
            for c in df.columns
        ]

        col_codigo = col_nome = col_uf = None
        for col in df.columns:
            col_n = _normalizar(col)
            if col_n in ("CODIGO", "COD", "CODIGO MUNICIPIO", "CODIGO_MUNICIPIO") and col_codigo is None:
                col_codigo = col
            elif col_n in ("NOME", "MUNICIPIO", "NOME MUNICIPIO") and col_nome is None:
                col_nome = col
            elif col_n in ("ESTADO", "UF", "SIGLA", "SIGLA UF") and col_uf is None:
                col_uf = col

        if col_codigo is None and len(df.columns) >= 1: col_codigo = df.columns[0]
        if col_nome   is None and len(df.columns) >= 2: col_nome   = df.columns[1]
        if col_uf     is None and len(df.columns) >= 5: col_uf     = df.columns[4]
        elif col_uf   is None and len(df.columns) >= 3: col_uf     = df.columns[2]

        mapa, erros = {}, []
        for idx, row in df.iterrows():
            try:
                uf_raw   = str(row[col_uf]).strip()
                nome_raw = str(row[col_nome]).strip()
                cod_raw  = str(row[col_codigo]).strip()
                if cod_raw.lower()  in ("nan", "none", "", "0"): continue
                if uf_raw.lower()   in ("nan", "none", ""):      continue
                if nome_raw.lower() in ("nan", "none", ""):      continue
                if "." in cod_raw:
                    try: cod_raw = str(int(float(cod_raw)))
                    except: pass
                uf_n   = _normalizar(uf_raw)
                nome_n = _normalizar(nome_raw)
                if uf_n and nome_n and cod_raw:
                    mapa[(uf_n, nome_n)] = cod_raw
            except Exception as e:
                erros.append(f"Linha {idx}: {e}")

        return mapa, {
            "total":      len(mapa),
            "caminho":    caminho_encontrado,
            "col_codigo": col_codigo,
            "col_nome":   col_nome,
            "col_uf":     col_uf,
            "colunas":    list(df.columns),
            "amostra":    [f"({u},{n})->{c}" for (u, n), c in list(mapa.items())[:8]],
            "erros":      erros[:5],
        }

    except Exception as e:
        return {}, {
            "erro_fatal": str(e),
            "caminho_tentado": caminho_encontrado,
            "total": 0,
        }

def buscar_codigo_municipio(municipio: str, uf: str) -> str:
    mapa = st.session_state.get("MUNICIPIOS_MAP", {})
    if not mapa:
        return ""
    uf_n      = _normalizar(uf)
    nome_orig = _normalizar(municipio)
    if not uf_n or not nome_orig: return ""

    uf_n      = _normalizar(uf)
    nome_orig = _normalizar(municipio)
    if not uf_n or not nome_orig: return ""
    cod = mapa.get((uf_n, nome_orig))
    if cod: return str(cod)
    variacoes = set()
    variacoes.add(re.sub(r"^(DO|DE|DA|DOS|DAS)\s+", "", nome_orig).strip())
    variacoes.add(re.sub(r"\s+(DO|DE|DA|DOS|DAS)\s+", " ", nome_orig).strip())
    variacoes.add(nome_orig.replace("STO ", "SANTO ").replace("STA ", "SANTA "))
    variacoes.add(nome_orig.replace("SANTO ", "STO ").replace("SANTA ", "STA "))
    variacoes.add(re.sub(r"['\-]", " ", nome_orig).strip())
    variacoes.add(nome_orig.replace("D ", "DE ").replace("D'", "DE "))
    variacoes.discard(nome_orig)
    for v in variacoes:
        if not v: continue
        cod = mapa.get((uf_n, v))
        if cod: return str(cod)
    for (u, n), c in mapa.items():
        if u != uf_n: continue
        if nome_orig in n or n in nome_orig: return str(c)
    prefixo = nome_orig[:5]
    if len(prefixo) >= 4:
        for (u, n), c in mapa.items():
            if u == uf_n and n.startswith(prefixo): return str(c)
    return ""

# ──────────────────────────────────────────────────────────────────────────────
# MOTOR FPAS
# ──────────────────────────────────────────────────────────────────────────────
ENTIDADES = {
    "FNDE":    {"codigo": 1,    "aliquota": 2.5,  "nome": "Salario-Educacao"},
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

FPAS_CONFIG = {
    507: (79,   2, "2100", "150", "Industria Geral"),
    515: (115,  2, "2100", "150", "Comercio / Servicos em Geral"),
    566: (99,   2, "2100", "150", "Profissional Liberal / Autonomo PF"),
    574: (115,  1, "2100", "150", "Saude"),
    582: (0,    1, "2100", "150", "Administracao Publica"),
    604: (3,    2, "2631", "150", "Produtor Rural PF"),
    620: (145,  2, "2100", "150", "Transporte Rodoviario / Aereo"),
    639: (0,    0, "2100", "150", "Entidade Beneficente Isenta"),
    647: (115,  1, "2100", "150", "Educacao / Assistencia Social"),
    655: (115,  2, "2100", "150", "Instituicao Financeira"),
    663: (115,  2, "2100", "150", "Comunicacao / Publicidade"),
    671: (115,  2, "2100", "150", "Hoteis / Turismo"),
    680: (115,  2, "2100", "150", "Limpeza / Conservacao"),
    736: (115,  2, "2100", "150", "TI / Tecnologia da Informacao"),
    744: (115,  2, "2100", "150", "Consultoria / Assessoria"),
    760: (115,  2, "2100", "150", "Seguranca Privada"),
    779: (115,  2, "2100", "150", "Servicos Pessoais"),
    787: (3,    2, "2631", "150", "Produtor Rural PJ"),
    795: (115,  2, "2100", "150", "Cooperativa de Trabalho"),
    803: (115,  2, "2100", "150", "Cooperativa de Producao"),
    810: (1024, 2, "2100", "150", "Cooperativa de Credito (SESCOOP)"),
    833: (115,  3, "2100", "150", "Construcao Civil"),
    868: (0,    0, "2100", "150", "Missao Diplomatica / Org. Internacional"),
    876: (0,    0, "2100", "150", "Domestico / Contribuinte Individual"),
}

FPAS_SEMPRE_ZERO = {582, 868, 876}

CNAE_FPAS = {
    "0111-3/01":604,"0111-3/02":604,"0111-3/03":604,"0112-1/01":604,"0113-0/00":604,
    "0115-6/00":604,"0116-4/00":604,"0119-9/01":604,"0119-9/99":604,"0121-1/01":604,
    "0122-9/00":604,"0131-8/00":604,"0132-6/00":604,"0133-4/01":604,"0134-2/00":604,
    "0135-1/00":604,"0139-3/01":604,"0139-3/99":604,"0141-5/01":604,"0142-3/00":604,
    "0151-2/01":604,"0151-2/02":604,"0152-1/01":604,"0153-9/01":604,"0154-7/00":604,
    "0155-5/01":604,"0155-5/02":604,"0159-8/01":604,"0159-8/99":604,"0161-0/00":604,
    "0162-8/00":604,"0163-6/00":604,"0170-9/00":604,"0210-1/01":604,"0210-1/02":604,
    "0220-9/01":604,"0220-9/02":604,"0230-6/00":604,"0240-3/00":604,"0311-6/01":604,
    "0312-4/00":604,"0321-3/01":604,"0322-1/00":604,
    "1011-2/01":507,"1011-2/02":507,"1012-1/01":507,"1013-9/01":507,"1020-1/01":507,
    "1020-1/02":507,"1031-7/00":507,"1032-5/01":507,"1033-3/01":507,"1041-4/00":507,
    "1042-2/00":507,"1043-1/00":507,"1051-1/00":507,"1052-0/00":507,"1061-9/01":507,
    "1062-7/00":507,"1063-5/00":507,"1064-3/00":507,"1065-1/01":507,"1066-0/00":507,
    "1069-4/00":507,"1071-6/00":507,"1072-4/01":507,"1073-2/01":507,"1081-3/01":507,
    "1082-1/00":507,"1083-0/00":507,"1084-8/00":507,"1085-6/00":507,"1086-4/00":507,
    "1087-2/00":507,"1088-1/00":507,"1089-9/00":507,"1091-1/01":507,"1091-1/02":507,
    "1092-9/00":507,"1093-7/01":507,"1094-5/00":507,"1095-3/00":507,"1096-1/00":507,
    "1099-6/01":507,"1099-6/99":507,"1111-9/01":507,"1111-9/02":507,"1112-7/00":507,
    "1113-5/01":507,"1121-6/00":507,"1122-4/01":507,"1122-4/03":507,"1210-7/00":507,
    "1220-4/01":507,"1311-1/00":507,"1312-0/00":507,"1313-8/00":507,"1314-6/00":507,
    "1321-9/00":507,"1322-7/00":507,"1323-5/00":507,"1330-8/00":507,"1340-5/01":507,
    "1351-1/00":507,"1352-9/00":507,"1353-7/00":507,"1354-5/00":507,"1359-6/00":507,
    "1411-8/01":507,"1411-8/02":507,"1412-6/01":507,"1413-4/01":507,"1414-2/00":507,
    "1421-5/00":507,"1422-3/00":507,"1510-6/00":507,"1521-1/00":507,"1529-7/00":507,
    "1531-9/01":507,"1532-7/00":507,"1533-5/00":507,"1539-4/00":507,"1540-8/00":507,
    "1610-2/01":507,"1610-2/02":507,"1621-8/00":507,"1622-6/01":507,"1710-9/00":507,
    "1721-4/00":507,"1722-2/00":507,"1731-1/00":507,"1732-0/00":507,"1733-8/00":507,
    "1741-9/01":507,"1742-7/00":507,"1749-4/00":507,"1811-3/01":507,"1811-3/02":507,
    "1812-1/00":507,"1813-0/00":507,"1821-1/00":507,"1822-9/01":507,"1830-0/01":507,
    "1830-0/02":507,"1830-0/03":507,"1910-1/00":507,"1921-7/00":507,"1922-5/00":507,
    "1931-4/00":507,"1932-2/00":507,"1933-1/00":507,"2011-8/00":507,"2012-6/00":507,
    "2013-4/01":507,"2021-5/00":507,"2022-3/00":507,"2023-1/00":507,"2029-1/00":507,
    "2031-2/00":507,"2032-1/00":507,"2033-9/00":507,"2040-1/00":507,"2051-7/00":507,
    "2052-5/00":507,"2061-4/00":507,"2062-2/00":507,"2063-1/00":507,"2064-9/00":507,
    "2065-7/00":507,"2066-5/00":507,"2067-3/00":507,"2068-1/00":507,"2091-6/00":507,
    "2092-4/01":507,"2093-2/00":507,"2094-1/00":507,"2099-1/01":507,"2099-1/99":507,
    "2110-6/00":507,"2121-1/01":507,"2121-1/02":507,"2122-0/00":507,"2123-8/00":507,
    "2211-1/00":507,"2212-9/00":507,"2219-6/00":507,"2221-8/00":507,"2222-6/00":507,
    "2223-4/00":507,"2229-3/01":507,"2311-7/00":507,"2312-5/00":507,"2319-2/00":507,
    "2320-6/00":507,"2330-3/01":507,"2341-9/00":507,"2342-7/00":507,"2349-4/00":507,
    "2350-8/00":507,"2391-5/00":507,"2392-3/00":507,"2399-1/01":507,"2410-1/00":507,
    "2421-1/00":507,"2422-9/01":507,"2423-7/01":507,"2424-5/00":507,"2431-8/00":507,
    "2439-3/00":507,"2441-5/01":507,"2442-3/00":507,"2443-1/00":507,"2444-0/00":507,
    "2445-8/00":507,"2446-6/00":507,"2449-1/99":507,"2451-2/00":507,"2452-1/00":507,
    "2511-0/00":507,"2512-8/00":507,"2513-6/00":507,"2521-7/00":507,"2522-5/00":507,
    "2531-4/01":507,"2532-2/00":507,"2539-0/01":507,"2541-1/00":507,"2542-0/00":507,
    "2543-8/00":507,"2550-1/00":507,"2591-8/00":507,"2592-6/01":507,"2593-4/00":507,
    "2599-3/01":507,"2599-3/99":507,"2610-8/00":507,"2621-3/00":507,"2622-1/00":507,
    "2631-1/00":507,"2632-9/00":507,"2640-0/00":507,"2651-5/00":507,"2652-3/00":507,
    "2660-4/00":507,"2670-1/01":507,"2680-9/00":507,"2710-4/01":507,"2710-4/02":507,
    "2721-0/00":507,"2722-8/00":507,"2731-7/00":507,"2732-5/00":507,"2733-3/00":507,
    "2740-6/01":507,"2751-1/00":507,"2759-7/01":507,"2790-2/01":507,"2811-9/00":507,
    "2812-7/00":507,"2813-5/00":507,"2814-3/00":507,"2815-1/00":507,"2821-6/00":507,
    "2822-4/01":507,"2823-2/00":507,"2824-1/01":507,"2825-9/00":507,"2829-1/01":507,
    "2830-5/00":507,"2840-2/00":507,"2851-8/00":507,"2852-6/00":507,"2853-4/00":507,
    "2854-2/00":507,"2861-5/00":507,"2862-3/00":507,"2863-1/00":507,"2864-0/00":507,
    "2865-8/00":507,"2866-6/00":507,"2869-1/00":507,"2910-7/01":507,"2920-4/01":507,
    "2930-1/01":507,"2941-7/00":507,"2942-5/00":507,"2943-3/00":507,"2944-1/00":507,
    "2945-0/00":507,"2949-2/01":507,"2950-6/00":507,"3011-3/01":507,"3012-1/00":507,
    "3031-8/00":507,"3032-6/00":507,"3041-5/00":507,"3042-3/00":507,"3050-4/00":507,
    "3091-1/00":507,"3092-0/00":507,"3099-7/00":507,"3101-2/00":507,"3102-1/00":507,
    "3103-9/00":507,"3104-7/00":507,"3211-6/01":507,"3212-4/00":507,"3220-5/00":507,
    "3230-2/00":507,"3240-0/01":507,"3291-4/00":507,"3292-2/00":507,"3299-0/05":507,
    "4110-7/00":833,"4120-4/00":833,"4211-1/01":833,"4211-1/02":833,"4212-0/00":833,
    "4213-8/00":833,"4221-9/01":833,"4221-9/02":833,"4222-7/00":833,"4223-5/00":833,
    "4291-0/00":833,"4292-8/00":833,"4299-5/01":833,"4299-5/99":833,"4311-8/01":833,
    "4311-8/02":833,"4312-6/00":833,"4313-4/00":833,"4319-3/00":833,"4321-5/00":833,
    "4322-3/01":833,"4322-3/02":833,"4323-1/00":833,"4329-1/01":833,"4329-1/05":833,
    "4329-1/99":833,"4330-4/01":833,"4330-4/02":833,"4330-4/03":833,"4330-4/04":833,
    "4330-4/05":833,"4391-6/00":833,"4399-1/01":833,"4399-1/02":833,"4399-1/03":833,
    "4399-1/04":833,"4399-1/05":833,"4399-1/99":833,
    "4511-1/01":515,"4511-1/02":515,"4512-9/01":515,"4512-9/02":515,"4520-0/01":515,
    "4520-0/02":515,"4530-7/01":515,"4530-7/02":515,"4530-7/03":515,"4541-2/01":515,
    "4541-2/02":515,"4541-2/03":515,"4542-1/00":515,"4543-9/00":515,"4611-7/00":515,
    "4612-5/00":515,"4613-3/00":515,"4614-1/00":515,"4615-0/00":515,"4616-8/00":515,
    "4617-6/00":515,"4618-4/01":515,"4619-2/00":515,"4621-4/00":515,"4622-2/00":515,
    "4623-1/01":515,"4623-1/08":515,"4631-1/00":515,"4632-0/01":515,"4633-8/01":515,
    "4634-6/01":515,"4635-4/01":515,"4636-2/01":515,"4637-1/01":515,"4639-7/01":515,
    "4641-9/01":515,"4642-7/01":515,"4643-5/01":515,"4644-3/01":515,"4645-1/01":515,
    "4646-0/01":515,"4647-8/01":515,"4649-4/01":515,"4651-6/01":515,"4652-4/00":515,
    "4661-3/00":515,"4662-1/00":515,"4663-0/00":515,"4664-8/00":515,"4665-6/00":515,
    "4669-9/01":515,"4671-1/00":515,"4672-9/00":515,"4673-7/00":515,"4674-5/00":515,
    "4679-6/01":515,"4681-8/01":515,"4682-6/00":515,"4683-4/00":515,"4684-2/01":515,
    "4685-1/00":515,"4686-9/00":515,"4687-7/01":515,"4689-3/00":515,"4691-5/00":515,
    "4692-3/00":515,"4693-1/00":515,"4711-3/01":515,"4711-3/02":515,"4712-1/00":515,
    "4713-0/01":515,"4713-0/02":515,"4721-1/01":515,"4721-1/02":515,"4722-9/01":515,
    "4723-7/00":515,"4724-5/00":515,"4729-6/01":515,"4731-8/00":515,"4732-6/00":515,
    "4741-5/00":515,"4742-3/00":515,"4743-1/00":515,"4744-0/01":515,"4744-0/02":515,
    "4744-0/03":515,"4744-0/04":515,"4744-0/05":515,"4744-0/06":515,"4744-0/99":515,
    "4751-2/01":515,"4751-2/02":515,"4752-1/00":515,"4753-9/00":515,"4754-7/01":515,
    "4755-5/01":515,"4756-3/00":515,"4757-1/00":515,"4759-8/01":515,"4761-0/01":515,
    "4762-8/00":515,"4763-6/01":515,"4771-7/01":515,"4771-7/02":515,"4771-7/03":515,
    "4772-5/00":515,"4773-3/00":515,"4774-1/00":515,"4781-4/00":515,"4782-2/01":515,
    "4783-1/01":515,"4784-9/00":515,"4785-7/01":515,"4789-0/01":515,"4789-0/99":515,
    "4791-1/00":515,"4792-8/00":515,"4793-6/00":515,
    "4911-6/00":620,"4912-4/01":620,"4912-4/02":620,"4921-3/01":620,"4921-3/02":620,
    "4922-1/01":620,"4922-1/02":620,"4923-0/01":620,"4923-0/02":620,"4924-8/00":620,
    "4929-9/01":620,"4929-9/02":620,"4929-9/99":620,"4930-2/01":620,"4930-2/02":620,
    "4930-2/03":620,"4940-0/00":620,"4950-7/00":620,"5011-4/01":620,"5011-4/02":620,
    "5012-2/01":620,"5021-1/01":620,"5022-0/01":620,"5030-1/00":620,"5091-2/01":620,
    "5099-8/01":620,"5111-1/00":620,"5112-9/00":620,"5120-0/00":620,"5130-7/00":620,
    "5141-2/00":620,"5142-1/00":620,"5150-2/00":620,"5161-8/00":620,"5162-6/00":620,
    "5163-4/00":620,"5172-3/00":620,"5174-0/00":620,"5179-1/00":620,"5211-7/01":620,
    "5211-7/02":620,"5212-5/00":620,"5221-4/00":620,"5222-2/00":620,"5223-1/00":620,
    "5229-0/01":620,"5229-0/02":620,"5229-0/99":620,"5231-1/01":620,"5232-0/00":620,
    "5239-7/00":620,"5240-1/01":620,"5250-8/01":620,"5250-8/02":620,"5310-5/01":620,
    "5310-5/02":620,"5320-2/01":620,
    "6201-5/00":736,"6201-5/01":736,"6201-5/02":736,"6202-3/00":736,"6203-1/00":736,
    "6204-0/00":736,"6209-1/00":736,"6311-9/00":736,"6319-4/00":736,"6391-7/00":736,
    "6399-2/00":736,
    "6410-7/00":655,"6421-2/00":655,"6422-1/00":655,"6423-9/00":655,"6424-7/01":655,
    "6424-7/02":655,"6424-7/03":655,"6431-0/00":655,"6432-8/00":655,"6433-6/00":655,
    "6434-4/01":655,"6435-2/01":655,"6436-1/00":655,"6437-9/00":655,"6438-7/00":655,
    "6440-9/00":655,"6450-6/00":655,"6461-1/00":655,"6462-0/00":655,"6463-8/00":655,
    "6470-1/01":655,"6491-3/00":655,"6492-1/00":655,"6493-0/00":655,"6499-9/01":655,
    "6499-9/99":655,"6511-1/01":655,"6511-1/02":655,"6512-0/00":655,"6520-1/00":655,
    "6521-9/00":655,"6522-7/00":655,"6523-5/00":655,"6524-3/00":655,"6525-1/00":655,
    "6530-8/00":655,"6541-3/00":655,"6542-1/00":655,"6550-2/00":655,"6611-8/00":655,
    "6612-6/00":655,"6613-4/00":655,"6619-3/01":655,"6621-5/00":655,"6622-3/00":655,
    "6629-1/00":655,"6630-4/00":655,
    "8610-1/01":647,"8610-1/02":647,"8621-6/01":647,"8621-6/02":647,"8622-4/00":647,
    "8630-5/01":647,"8630-5/02":647,"8630-5/03":647,"8630-5/04":647,"8630-5/06":647,
    "8630-5/07":647,"8630-5/08":647,"8640-2/01":647,"8640-2/02":647,"8640-2/03":647,
    "8640-2/04":647,"8640-2/05":647,"8640-2/06":647,"8640-2/07":647,"8640-2/08":647,
    "8640-2/09":647,"8640-2/10":647,"8640-2/11":647,"8640-2/12":647,"8640-2/13":647,
    "8650-0/01":647,"8650-0/02":647,"8650-0/03":647,"8650-0/04":647,"8650-0/05":647,
    "8650-0/06":647,"8650-0/07":647,"8660-7/00":647,
    "8511-2/00":647,"8512-1/00":647,"8513-9/00":647,"8520-1/00":647,"8531-7/00":647,
    "8532-5/00":647,"8533-3/00":647,"8541-4/00":647,"8542-2/00":647,"8550-3/01":647,
    "8550-3/02":647,"8591-1/00":647,"8592-9/01":647,"8593-7/00":647,"8599-6/01":647,
    "8599-6/99":647,
    "8411-6/00":582,"8412-4/00":582,"8413-2/00":582,"8421-3/00":582,"8422-1/00":582,
    "8423-0/00":582,"8424-8/00":582,"8425-6/00":582,"8430-2/00":582,
    "7711-0/00":515,"7719-5/99":515,"7721-7/00":515,"7722-5/00":515,"7723-3/00":515,
    "7729-2/01":515,"7731-4/00":515,"7732-2/00":515,"7733-1/00":515,"7739-0/01":515,
    "7740-3/00":515,"7810-8/00":515,"7820-5/00":515,"7830-2/00":515,"7911-2/00":671,
    "7912-1/00":671,"7990-2/00":671,"8011-1/01":760,"8011-1/02":760,"8012-9/00":760,
    "8020-0/01":760,"8021-8/00":760,"8030-7/00":760,"8111-7/00":680,"8112-5/00":680,
    "8121-4/00":680,"8122-2/00":680,"8129-0/00":680,"8130-3/00":680,"8211-3/00":515,
    "8219-9/01":515,"8219-9/99":515,"8220-2/00":515,"8230-0/01":515,"8291-1/00":515,
    "8292-0/00":515,"8299-7/01":515,"8299-7/99":515,
}

# ──────────────────────────────────────────────────────────────────────────────
# CLASSIFICACAO FPAS
# ──────────────────────────────────────────────────────────────────────────────
def formatar_cnae(raw) -> str | None:
    if not raw: return None
    s = str(raw).strip().replace(".", "").replace(" ", "")
    if "-" in s and "/" in s: return s
    d = re.sub(r"\D", "", s)
    if len(d) == 7: return f"{d[:4]}-{d[4]}/{d[5:]}"
    return s

def decodificar_terceiros(codigo: int) -> list:
    return [{"sigla": s, "nome": d["nome"], "aliquota": d["aliquota"]}
            for s, d in ENTIDADES.items()
            if isinstance(codigo, int) and codigo & d["codigo"]]

def classificar(cnae: str, simples: bool = False, fap: float = 1.0, convenios: list = None) -> dict:
    convenios = convenios or []
    cnae_fmt  = formatar_cnae(cnae)
    if not cnae_fmt or cnae_fmt not in CNAE_FPAS:
        return {"erro": f"CNAE '{cnae}' nao mapeado."}
    fpas = CNAE_FPAS[cnae_fmt]
    if fpas not in FPAS_CONFIG:
        return {"erro": f"FPAS {fpas} sem configuracao."}
    terceiros_base, rat_base, cod_gps, cod_gfip, descricao = FPAS_CONFIG[fpas]
    if simples:
        codigo_terceiro, obs = None, "Simples Nacional - campo terceiros em branco"
    elif fpas in FPAS_SEMPRE_ZERO:
        codigo_terceiro, obs = 0, f"FPAS {fpas}: terceiros sempre zero"
    else:
        codigo_terceiro = terceiros_base
        removidos = []
        for ent in convenios:
            bit = ENTIDADES.get(ent.upper(), {}).get("codigo", 0)
            if bit and (codigo_terceiro & bit):
                codigo_terceiro &= ~bit
                removidos.append(ent.upper())
        obs = f"Convenio: {', '.join(removidos)} removido(s)" if removidos else "Classificacao padrao"
    rat_ajustado = round(rat_base * fap, 2)
    entidades    = decodificar_terceiros(codigo_terceiro) if codigo_terceiro else []
    total_terc   = sum(e["aliquota"] for e in entidades)
    return {
        "cnae": cnae_fmt, "fpas": fpas, "fpas_descricao": descricao,
        "codigo_terceiro": codigo_terceiro, "perc_acid_trabalho": rat_base,
        "codigo_sat": rat_ajustado, "codigo_gps": cod_gps, "codigo_gfip": cod_gfip,
        "entidades": entidades, "total_terceiros_pct": total_terc,
        "observacao": obs, "erro": None,
    }

# ──────────────────────────────────────────────────────────────────────────────
# CNPJ
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
    if len(c) != 14 or len(set(c)) == 1: return False
    def calc_dv(digits, pesos):
        soma  = sum(int(d) * p for d, p in zip(digits, pesos))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto
    return (int(c[12]) == calc_dv(c[:12], [5,4,3,2,9,8,7,6,5,4,3,2]) and
            int(c[13]) == calc_dv(c[:13], [6,5,4,3,2,9,8,7,6,5,4,3,2]))

def normalizar_resposta(data: dict, cnpj: str) -> dict:
    cnae_codigo = (
        data.get("cnae_fiscal") or data.get("cnae_fiscal_codigo")
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
    simples  = (
        data.get("opcao_pelo_simples")
        or (data.get("simples", {}).get("optante", False)
            if isinstance(data.get("simples"), dict) else False)
    )
    return {
        "cnpj":              cnpj,
        "razao_social":      data.get("razao_social") or data.get("nome", ""),
        "nome_fantasia":     data.get("nome_fantasia", ""),
        "situacao":          data.get("descricao_situacao_cadastral") or data.get("situacao", ""),
        "cnae_codigo":       cnae_fmt,
        "cnae_descricao":    cnae_descricao,
        "simples":           bool(simples),
        "natureza_juridica": data.get("descricao_natureza_juridica") or data.get("natureza_juridica", ""),
        "porte":             data.get("descricao_porte") or data.get("porte", ""),
        "logradouro":        data.get("logradouro", ""),
        "numero":            data.get("numero", ""),
        "bairro":            data.get("bairro", ""),
        "municipio":         data.get("municipio", "") or "",
        "uf":                data.get("uf", ""),
        "cep":               data.get("cep", ""),
        "data_inicio":       data.get("data_inicio_atividade") or data.get("abertura", ""),
        "erro":              None,
    }

def consultar_cnpj(cnpj_raw: str, delay: float = 1.0) -> dict:
    cnpj = limpar_cnpj(cnpj_raw)
    if not validar_cnpj(cnpj):
        return {"erro": f"CNPJ invalido: {cnpj_raw}"}
    time.sleep(delay)
    for url_tpl in APIS:
        try:
            r = requests.get(url_tpl.format(cnpj=cnpj), headers=HEADERS, timeout=12)
            if r.status_code == 200: return normalizar_resposta(r.json(), cnpj)
            if r.status_code == 429: time.sleep(60)
        except Exception:
            continue
    return {"erro": f"CNPJ {cnpj} nao encontrado em nenhuma API."}

def extrair_cnpjs_do_texto(texto: str) -> list:
    encontrados = re.findall(r"\d{2}[\.\s]?\d{3}[\.\s]?\d{3}[\/\s]?\d{4}[-\s]?\d{2}", texto)
    vistos, unicos = set(), []
    for c in encontrados:
        limpo = limpar_cnpj(c)
        if limpo not in vistos:
            vistos.add(limpo)
            unicos.append(c.strip())
    return unicos

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS DE DATA
# CORRECAO: sem sufixo 00:00:00 em nenhuma data dos arquivos gerados
# ──────────────────────────────────────────────────────────────────────────────
def _formatar_data(data_raw: str) -> str:
    """Converte qualquer data para DD/MM/AAAA (foservicos.txt)."""
    s = str(data_raw or "01/01/2020")[:10]
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return "01/01/2020"

def _data_para_vigencia(d: date) -> str:
    """date -> DD/MM/AAAA (formato FOVIGENCIAS — sem sufixo de hora)."""
    return d.strftime("%d/%m/%Y")

# Competencia fim fixa: 31/12/3000 (vigencia aberta — sem sufixo de hora)
COMP_FIM = "31/12/3000"

# ──────────────────────────────────────────────────────────────────────────────
# LEIAUTE FOSERVICOS - 25 colunas
# ──────────────────────────────────────────────────────────────────────────────
COLUNAS_LEIAUTE = [
    "Codigo_empresa", "Codigo_Servicos", "CNPJ_CPF", "Tipo_Inscricao",
    "Codigo_Terceiro", "Perc_Acidente_Trabalho", "Codigo_FPAS", "CNAE",
    "Codigo_GFIP", "Codigo_GPS", "Nome", "Endereco", "Numero", "Bairro",
    "CEP", "Cidade", "Estado", "Codigo_Filial", "Sequencia_GPS", "Tipo",
    "Codigo_Municipio", "Data_Inicio", "Situacao", "Codigo_eSocial", "Origem_Reg",
]

def montar_linha_dominio(r: dict, tipo_cod: int, cod_servico: int, codigo_empresa: int = 1) -> list:
    cnpj_limpo = limpar_cnpj(r.get("cnpj", ""))

    # Codigo terceiro: sempre inteiro formatado 4 digitos
    cod_terc_raw = r.get("codigo_terceiro", 0)
    if isinstance(cod_terc_raw, int):
        cod_terc_str = f"{cod_terc_raw:04d}"
        i_terceiros  = cod_terc_raw
    elif cod_terc_raw is None:
        cod_terc_str = "0000"
        i_terceiros  = 0
    else:
        s = str(cod_terc_raw).strip()
        try:
            i_terceiros  = int(s) if s else 0
            cod_terc_str = f"{i_terceiros:04d}"
        except Exception:
            i_terceiros  = 0
            cod_terc_str = "0000"

    cep       = re.sub(r"\D", "", str(r.get("cep", "") or ""))
    municipio = str(r.get("municipio", "") or "")
    uf        = str(r.get("uf", "") or "")
    cod_mun   = buscar_codigo_municipio(municipio, uf)
    data_ini  = _formatar_data(r.get("data_inicio", ""))

    rat  = r.get("perc_acid_trabalho", 0) or 0
    fpas = r.get("codigo_fpas", 0) or 0
    gfip = str(r.get("codigo_gfip", "") or "115")
    gps  = str(r.get("codigo_gps",  "") or "2100")

    return [
        codigo_empresa,   # 1  codi_emp
        cod_servico,      # 2  i_servicos
        cnpj_limpo,       # 3  cgc
        1,                # 4  tipo_insc
        cod_terc_str,     # 5  codigo_terceiro
        rat,              # 6  perc_acid_trabalho
        fpas,             # 7  codigo_fpas
        str(r.get("cnae_codigo", "") or ""),  # 8  codigo_atividade
        gfip,             # 9  codigo_gfip
        gps,              # 10 codigo_gps
        str(r.get("razao_social", "") or ""),
        str(r.get("logradouro", "") or ""),
        str(r.get("numero", "") or ""),
        str(r.get("bairro", "") or ""),
        cep, municipio, uf,
        cod_servico,      # 18 i_filiais
        1,                # 19 sequencia_gps
        tipo_cod,         # 20 tipo
        cod_mun,          # 21 codigo_municipio
        data_ini,         # 22 DATA_INICIO
        1,                # 23 SITUACAO
        cod_servico,      # 24 CODIGO_ESOCIAL
        "",               # 25 origem_reg
    ]


def montar_linha_vigencia(
    r: dict,
    cod_servico: int,
    tipo_cod: int,
    codigo_empresa: int,
    vigencia: str,
    descricao_vigencia: str,
    cod_mun: str,
) -> list:
    cnpj_limpo = limpar_cnpj(r.get("cnpj", ""))

    cod_terc_raw = r.get("codigo_terceiro", 0)
    if isinstance(cod_terc_raw, int):
        cod_terc_str = f"{cod_terc_raw:04d}"
        i_terceiros  = cod_terc_raw
    elif cod_terc_raw is None:
        cod_terc_str = "0000"
        i_terceiros  = 0
    else:
        s = str(cod_terc_raw).strip()
        try:
            i_terceiros  = int(s) if s else 0
            cod_terc_str = f"{i_terceiros:04d}"
        except Exception:
            i_terceiros  = 0
            cod_terc_str = "0000"

    entidades = r.get("entidades", []) or []
    perc_terc = sum(e.get("aliquota", 0) for e in entidades)

    rat  = r.get("perc_acid_trabalho", 0) or 0
    fpas = r.get("codigo_fpas", 0) or 0
    gfip = str(r.get("codigo_gfip", "") or "115")
    gps  = str(r.get("codigo_gps",  "") or "2100")

    endereco  = str(r.get("logradouro", "") or "")
    numero    = str(r.get("numero", "")    or "0")
    bairro    = str(r.get("bairro", "")    or "")
    cep       = re.sub(r"\D", "", str(r.get("cep", "") or ""))
    municipio = str(r.get("municipio", "") or "")
    uf        = str(r.get("uf", "")        or "")

    cnae_fmt = str(r.get("cnae_codigo", "") or "")
    cnae_num = re.sub(r"\D", "", cnae_fmt)

    return [
        codigo_empresa,     # 1  codi_emp
        cod_servico,        # 2  i_servicos
        vigencia,           # 3  VIGENCIA
        descricao_vigencia, # 4  DESCRICAO
        cnpj_limpo,         # 5  cgc
        1,                  # 6  tipo_insc
        cod_terc_str,       # 7  codigo_terceiro
        perc_terc,          # 8  perc_terceiro
        0,                  # 9  perc_inss_empresa
        rat,                # 10 perc_acid_trabalho
        0,                  # 11 codigo_sat
        0,                  # 12 perc_autonomos
        fpas,               # 13 codigo_fpas
        0,                  # 14 codigo_atividade
        gfip,               # 15 codigo_gfip
        gps,                # 16 codigo_gps
        0,                  # 17 i_bancos
        0,                  # 18 numero_fgts
        endereco,           # 19 endereco
        numero,             # 20 numero
        bairro,             # 21 bairro
        cep,                # 22 cep
        municipio,          # 23 cidade
        uf,                 # 24 estado
        1,                  # 25 i_filiais
        0,                  # 26 sequencia_gps
        0,                  # 27 filantropia
        0,                  # 28 origem_reg
        tipo_cod,           # 29 tipo
        0,                  # 30 codi_mun
        cod_mun,            # 31 codigo_municipio
        0,                  # 32 I_FPAS
        0,                  # 33 CALCULA_INSS_EMPRESA_LEI_12546
        0,                  # 34 TIPO_SERVICO_TOMADOR
        0,                  # 35 TIPO_ENDERECO
        "",                 # 36 COMPLEMENTO
        "",                 # 37 INSCRICAO_CONTRATANTE_EMPREITADA_PARCIAL
        "",                 # 38 NOME_CONTRATANTE_EMPREITADA_PARCIAL
        "",                 # 39 INSCRICAO_PROPRIETARIO_CEI_EMPREITADA_PARCIAL
        "",                 # 40 NOME_PROPRIETARIO_CEI_EMPREITADA_PARCIAL
        cnae_num,           # 41 I_CNAE20
        1,                  # 42 TIPO_INFORMACAO_ALIQUOTA_ACIDENTE_TRABALHO
        0,                  # 43 I_PROCESSO
        0,                  # 44 I_SCP
        "",                 # 45 DDD
        "",                 # 46 TELEFONE
        COMP_FIM,           # 47 COMPETENCIA_FIM_VIGENCIA
        0,                  # 48 I_PROCESSO_TERCEIROS
        "",                 # 49 CAEPF
        0,                  # 50 REGISTRO_PONTO
        1,                  # 51 CONTRATACAO_APRENDIZ
        0,                  # 52 I_PROCESSO_CONTRATACAO_APRENDIZ
        0,                  # 53 REALIZA_CONTRATACAO_APRENDIZ_INTERMEDIO_ENTIDADE_EDUCATIVA_SEM_FINS_LUCRATIVOS
        "",                 # 54 CODIGO_SUSPENSAO_PROCESSO_RAT
        0,                  # 55 SOMA_CODIGOS_SUSPENSAO_TERCEIROS
        perc_terc,          # 56 PERCENTUAL_TERCEIRO_BRUTO
        cnae_num,           # 57 I_CNAE_ESOCIAL
        i_terceiros,        # 58 I_TERCEIROS
        0,                  # 59 EFETUAR_RETENCAO_INSS_NOTAS_FISCAIS_INSCRICAO_OUTROS_CLIENTES
        "{00000000-0000-0000-0000-000000000000}",  # 60 COMPANY_ID
        "",                 # 61 NUMERO_PROCESSO_APRENDIZ
        0,                  # 62 INEXIGIBILIDADE_RAT
        0,                  # 63 CALCULAR_APOIO_FINANCEIRO_FOLHA_COLABORADOR_RS_MTE_991_2024
    ]

def _linha_vigencia_vazia(
    cnpj: str, cod_servico: int, tipo_cod: int,
    codigo_empresa: int, vigencia: str, descricao_vigencia: str,
) -> list:
    return montar_linha_vigencia(
        r={
            "cnpj": cnpj, "codigo_terceiro": 0, "perc_acid_trabalho": 0,
            "codigo_fpas": 0, "codigo_gfip": "115", "codigo_gps": "2100",
            "logradouro": "", "numero": "0", "bairro": "", "cep": "",
            "municipio": "", "uf": "", "cnae_codigo": "", "entidades": [],
        },
        cod_servico=cod_servico, tipo_cod=tipo_cod,
        codigo_empresa=codigo_empresa,
        vigencia=vigencia, descricao_vigencia=descricao_vigencia,
        cod_mun="",
    )
def gerar_txt_leiaute(linhas: list) -> bytes:
    linhas_txt = []
    for campos in linhas:
        row = [str(v) if v is not None else "" for v in campos]
        linhas_txt.append("\t".join(row))
    return ("\r\n".join(linhas_txt) + "\r\n").encode("utf-8")

def gerar_txt_vigencias(linhas: list) -> bytes:
    linhas_txt = []
    for campos in linhas:
        row = [str(v) if v is not None else "" for v in campos]
        linhas_txt.append("\t".join(row))
    return ("\r\n".join(linhas_txt) + "\r\n").encode("utf-8")

def gerar_zip(txt_fo: bytes, txt_vig: bytes) -> bytes:
    """Empacota foservicos.txt e fovigencias_servicos.txt num unico .zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("foservicos.txt", txt_fo)
        zf.writestr("fovigencias_servicos.txt", txt_vig)
    return buf.getvalue()

def _ler_leiaute(nome_arquivo: str) -> bytes | None:
    """Le arquivo de leiaute do repositorio tentando multiplos caminhos."""
    caminho = _resolver_caminho_arquivo(nome_arquivo)
    if not caminho:
        return None
    try:
        with open(caminho, "rb") as f:
            return f.read()
    except Exception:
        return None

def gerar_excel_conferencia(df, df_err) -> bytes:
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Importacao_Dominio", index=False)
        if df_err is not None and len(df_err) > 0:
            df_err.to_excel(writer, sheet_name="Erros", index=False)
        wb = writer.book
        ws = wb["Importacao_Dominio"]
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        from openpyxl.utils import get_column_letter
        HDR_FILL  = PatternFill("solid", fgColor="FF8000")
        OK_FILL   = PatternFill("solid", fgColor="0D2B0D")
        ERR_FILL  = PatternFill("solid", fgColor="2B0D0D")
        ODD_FILL  = PatternFill("solid", fgColor="242424")
        EVEN_FILL = PatternFill("solid", fgColor="2E2E2E")
        HDR_FONT  = Font(bold=True, color="FFFFFF", size=9)
        CELL_FONT = Font(color="F0F0F0", size=9)
        THIN      = Side(style="thin", color="3A3A3A")
        BORDER    = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
        for col_idx, cell in enumerate(ws[1], start=1):
            cell.fill = HDR_FILL
            cell.font = HDR_FONT
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = BORDER
            ws.column_dimensions[get_column_letter(col_idx)].width = 18
        ws.row_dimensions[1].height = 36
        try:
            status_col = df.columns.tolist().index("_status") + 1
        except ValueError:
            status_col = None
        for row_idx, row in enumerate(ws.iter_rows(min_row=2), start=2):
            sv = str(ws.cell(row=row_idx, column=status_col).value or "") if status_col else ""
            bg = OK_FILL if sv == "OK" else (ERR_FILL if "ERRO" in sv else (EVEN_FILL if row_idx % 2 == 0 else ODD_FILL))
            for cell in row:
                cell.fill = bg
                cell.font = CELL_FONT
                cell.alignment = Alignment(vertical="center")
                cell.border = BORDER
        ws.freeze_panes = "A2"
    return buf.getvalue()

# ──────────────────────────────────────────────────────────────────────────────
# HELPERS UI
# ──────────────────────────────────────────────────────────────────────────────
def metric_card(value, label, cls=""):
    return f'<div class="tr-metric {cls}"><div class="tr-metric-value">{value}</div><div class="tr-metric-label">{label}</div></div>'

def result_item(label, value, highlight=False):
    cls = "highlight" if highlight else ""
    return f'<div class="result-item"><div class="result-item-label">{label}</div><div class="result-item-value {cls}">{value}</div></div>'

# ──────────────────────────────────────────────────────────────────────────────
# APP
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Classificador FPAS | Dominio Sistemas",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("""
<div class="tr-header">
    <div class="tr-logo-box">TR</div>
    <div>
        <div class="tr-title">Classificador FPAS / Terceiros / SEFIP</div>
        <div class="tr-subtitle">DOMINIO SISTEMAS &nbsp;.&nbsp; Thomson Reuters &nbsp;.&nbsp; IN RFB no 971/2009</div>
    </div>
    <div class="tr-badge">v8.4</div>
</div>
""", unsafe_allow_html=True)

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        f'<p style="color:{TR_ORANGE};font-size:13px;font-weight:700;letter-spacing:1px;margin-bottom:16px;">CONFIGURACOES</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<p style="font-size:10px;font-weight:700;color:{TR_ORANGE};text-transform:uppercase;letter-spacing:1px;">Empresa no Dominio</p>',
        unsafe_allow_html=True,
    )
    codigo_empresa_dom = st.number_input(
        "Codigo Interno da Empresa",
        min_value=1, max_value=999999,
        value=st.session_state.get("codigo_empresa_dom_val", 1),
        step=1,
        key="codigo_empresa_dom_input",
        help="Codigo da empresa no Dominio Sistemas.",
    )
    st.session_state["codigo_empresa_dom_val"] = codigo_empresa_dom

    st.divider()
    st.markdown(
        f'<p style="font-size:10px;font-weight:700;color:{TR_ORANGE};text-transform:uppercase;letter-spacing:1px;">Parametros SEFIP</p>',
        unsafe_allow_html=True,
    )
    fap   = st.number_input("FAP",           min_value=0.5, max_value=2.0, value=1.0, step=0.01)
    delay = st.number_input("Intervalo (s)", min_value=0.3, max_value=5.0, value=1.0, step=0.1)

    st.markdown(
        f'<p style="font-size:10px;font-weight:700;color:{TR_ORANGE};text-transform:uppercase;letter-spacing:1px;margin-top:12px;">Convenios</p>',
        unsafe_allow_html=True,
    )
    convenios = st.multiselect(
        "Entidades", label_visibility="collapsed",
        options=["SENAI","SESI","SENAC","SESC","SEBRAE","SENAR","SEST","SENAT","SESCOOP"],
    )

    st.divider()
    st.markdown(
        f'<p style="font-size:10px;font-weight:700;color:{TR_ORANGE};text-transform:uppercase;letter-spacing:1px;">Vigencia (FOVIGENCIAS)</p>',
        unsafe_allow_html=True,
    )
    vigencia_data = st.date_input("Data de inicio da vigencia", value=date(2020, 1, 1))
    vigencia_str  = _data_para_vigencia(vigencia_data)
    descricao_vig = st.text_input("Descricao da vigencia", value="Vigencia Inicial")

    st.divider()

    # CORRECAO: recarrega se vazio (evita cache de erro entre deploys)
    if "MUNICIPIOS_MAP" not in st.session_state or not st.session_state["MUNICIPIOS_MAP"]:
        _mapa, _debug = _carregar_municipios()
        st.session_state["MUNICIPIOS_MAP"] = _mapa
        st.session_state["_mun_debug"]     = _debug

    mapa  = st.session_state.get("MUNICIPIOS_MAP", {})
    debug = st.session_state.get("_mun_debug", {})

    if mapa:
        st.success(f"OK {len(mapa):,} municipios carregados")
    else:
        st.warning(f"Municipios nao carregados: {debug.get('erro_fatal', 'arquivo nao encontrado')}")

    with st.expander("Debug municipios"):
        _dirs_debug = [
            "/mount/src/foservicos",
            os.path.dirname(os.path.abspath(__file__)),
            os.getcwd(),
        ]
        for _d in _dirs_debug:
            try:
                _lista = os.listdir(_d)
                st.markdown(
                    f'<p style="font-size:10px;color:{TR_TEXT_MUTED};">'
                    f'<b style="color:{TR_ORANGE};">{_d}</b><br>'
                    + "<br>".join(
                        f'<span style="color:{"#2ECC71" if f.endswith(".xlsx") else TR_TEXT_MUTED};">{f}</span>'
                        for f in sorted(_lista)
                        if not f.startswith("__") and not f.startswith(".")
                    )
                    + "</p>",
                    unsafe_allow_html=True,
                )
            except Exception as _e:
                st.markdown(
                    f'<p style="font-size:10px;color:{TR_ERROR};">{_d}: {_e}</p>',
                    unsafe_allow_html=True,
                )

        st.json({
            "total":      debug.get("total", 0),
            "caminho":    debug.get("caminho", "nao encontrado"),
            "col_codigo": debug.get("col_codigo", ""),
            "col_nome":   debug.get("col_nome", ""),
            "col_uf":     debug.get("col_uf", ""),
            "colunas":    debug.get("colunas", []),
            "amostra":    debug.get("amostra", []),
            "erros":      debug.get("erros", []),
            "erro_fatal": debug.get("erro_fatal", ""),
        })
        teste_mun = st.text_input("Testar municipio", placeholder="SAO PAULO")
        teste_uf  = st.text_input("UF", placeholder="SP")
        if teste_mun and teste_uf:
            cod_teste = buscar_codigo_municipio(teste_mun, teste_uf)
            if cod_teste:
                st.success(f"Codigo: {cod_teste}")
            else:
                st.error("Nao encontrado")
                uf_n   = _normalizar(teste_uf)
                nome_n = _normalizar(teste_mun)
                sugestoes = [
                    f"{n}->{c}"
                    for (u, n), c in list(mapa.items())
                    if u == uf_n and nome_n[:4] in n
                ][:8]
                if sugestoes:
                    st.write("Sugestoes:", sugestoes)

    if st.button("Recarregar municipios"):
        for k in ["MUNICIPIOS_MAP", "_mun_debug"]:
            st.session_state.pop(k, None)
        st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_lote, tab_individual, tab_tabela, tab_importacao = st.tabs([
    "Consulta em Lote",
    "Consulta Individual",
    "Tabela FPAS",
    "Importacao Dominio",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 - CONSULTA EM LOTE
# ══════════════════════════════════════════════════════════════════════════════
with tab_lote:
    st.markdown(
        f'<div class="tr-card"><div class="tr-card-title">Passo 1 - Cole os CNPJs</div>',
        unsafe_allow_html=True,
    )
    col_input, col_dica = st.columns([3, 1])
    with col_input:
        texto_cnpjs = st.text_area(
            "CNPJs", label_visibility="collapsed", height=180,
            placeholder="Cole aqui os CNPJs - um por linha, virgula, ponto-e-virgula ou espaco.",
        )
    with col_dica:
        st.markdown(f"""
        <div style="background:{TR_CARD2};border:1px solid {TR_BORDER};border-radius:8px;padding:14px;font-size:11px;color:{TR_TEXT_MUTED};line-height:1.8;">
            <b style="color:{TR_ORANGE};">Formatos aceitos:</b><br>
            OK 00.000.000/0000-00<br>
            OK 00000000000000<br>
            OK Virgula, ponto-e-virgula, quebra de linha<br>
            OK Duplicatas removidas
        </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if texto_cnpjs and texto_cnpjs.strip():
        lista_cnpjs = extrair_cnpjs_do_texto(texto_cnpjs)
        if lista_cnpjs:
            validos   = [c for c in lista_cnpjs if validar_cnpj(c)]
            invalidos = [c for c in lista_cnpjs if not validar_cnpj(c)]
            chips_html = "".join(
                f'<span class="cnpj-chip {"" if validar_cnpj(c) else "invalido"}">{"OK" if validar_cnpj(c) else "X"} {c}</span>'
                for c in lista_cnpjs
            )
            err_html = f'<span style="color:{TR_ERROR};">{len(invalidos)} invalido(s)</span>' if invalidos else ""
            st.markdown(f"""
            <div class="cnpj-preview-box">
                <div style="font-size:11px;color:{TR_TEXT_MUTED};text-transform:uppercase;letter-spacing:.5px;margin-bottom:8px;">
                    {len(lista_cnpjs)} detectado(s) - <span style="color:{TR_SUCCESS};">{len(validos)} valido(s)</span> {err_html}
                </div>
                {chips_html}
            </div>""", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_b1, col_b2 = st.columns([3, 1])
            with col_b1:
                iniciar = st.button(
                    f"Passo 2 - Consultar e Classificar {len(validos)} CNPJ(s)",
                    type="primary", use_container_width=True, disabled=len(validos) == 0,
                )
            with col_b2:
                if st.button("Limpar", use_container_width=True):
                    for k in ["resultados_proc", "dados_brutos", "seq_confirmada",
                              "seq_inicio_val", "_txt", "_xlsx", "_vig", "_zip"]:
                        st.session_state.pop(k, None)
                    st.rerun()

            if iniciar and validos:
                resultados_proc = []
                dados_brutos    = {}
                total    = len(validos)
                progress = st.progress(0, text="Iniciando...")
                col_log, col_stat = st.columns([2, 1])
                log_area  = col_log.empty()
                stat_area = col_stat.empty()
                logs, ok_n, err_n = [], 0, 0

                for i, cnpj_raw in enumerate(validos):
                    progress.progress(
                        int((i + 1) / total * 100),
                        text=f"Processando {i+1}/{total} - {cnpj_raw}",
                    )
                    dados_rf = consultar_cnpj(cnpj_raw, delay=delay)

                    if dados_rf.get("erro"):
                        err_n += 1
                        logs.append(f"ERRO {cnpj_raw}: {dados_rf['erro']}")
                        resultados_proc.append({
                            "cnpj": limpar_cnpj(cnpj_raw), "razao_social": "",
                            "municipio": "", "uf": "", "cod_municipio_dom": "",
                            "cnae_codigo": "", "fpas_descricao": "", "codigo_fpas": "",
                            "codigo_terceiro": "", "perc_acid_trabalho": "",
                            "codigo_gps": "", "codigo_gfip": "",
                            "_status": "ERRO_RF", "_obs": dados_rf["erro"],
                        })
                        dados_brutos[i] = None
                    else:
                        simples = dados_rf.get("simples", False)
                        classif = classificar(
                            dados_rf.get("cnae_codigo", ""),
                            simples=simples, fap=fap, convenios=convenios,
                        )
                        status = "ERRO_FPAS" if classif.get("erro") else "OK"
                        if status == "OK":
                            ok_n += 1
                            cod3 = classif["codigo_terceiro"]
                            logs.append(
                                f"OK {cnpj_raw} | {dados_rf.get('razao_social','')[:26]}"
                                f" | FPAS {classif['fpas']}"
                                f" | 3s {f'{cod3:04d}' if isinstance(cod3, int) else '-'}"
                            )
                        else:
                            err_n += 1
                            logs.append(f"AVISO {cnpj_raw} | {dados_rf.get('razao_social','')[:28]} | {classif['erro']}")

                        municipio = dados_rf.get("municipio", "")
                        uf        = dados_rf.get("uf", "")
                        cod_mun   = buscar_codigo_municipio(municipio, uf)
                        r_merged  = {
                            "cnpj":               limpar_cnpj(cnpj_raw),
                            "razao_social":       dados_rf.get("razao_social", ""),
                            "cnae_codigo":        dados_rf.get("cnae_codigo", ""),
                            "logradouro":         dados_rf.get("logradouro", ""),
                            "numero":             dados_rf.get("numero", ""),
                            "bairro":             dados_rf.get("bairro", ""),
                            "municipio":          municipio,
                            "uf":                 uf,
                            "cep":                dados_rf.get("cep", ""),
                            "data_inicio":        dados_rf.get("data_inicio", ""),
                            "codigo_fpas":        classif.get("fpas", ""),
                            "codigo_terceiro":    classif.get("codigo_terceiro", ""),
                            "perc_acid_trabalho": classif.get("perc_acid_trabalho", ""),
                            "codigo_gps":         classif.get("codigo_gps", ""),
                            "codigo_gfip":        classif.get("codigo_gfip", ""),
                            "entidades":          classif.get("entidades", []),
                        }
                        dados_brutos[i] = r_merged
                        resultados_proc.append({
                            "cnpj":               limpar_cnpj(cnpj_raw),
                            "razao_social":       dados_rf.get("razao_social", ""),
                            "municipio":          municipio,
                            "uf":                 uf,
                            "cod_municipio_dom":  cod_mun or "nao encontrado",
                            "cnae_codigo":        dados_rf.get("cnae_codigo", ""),
                            "fpas_descricao":     classif.get("fpas_descricao", ""),
                            "codigo_fpas":        classif.get("fpas", ""),
                            "codigo_terceiro": (
                                f"{classif['codigo_terceiro']:04d}"
                                if isinstance(classif.get("codigo_terceiro"), int)
                                else classif.get("codigo_terceiro", "")
                            ),
                            "perc_acid_trabalho": classif.get("perc_acid_trabalho", ""),
                            "codigo_gps":         classif.get("codigo_gps", ""),
                            "codigo_gfip":        classif.get("codigo_gfip", ""),
                            "_status":            status,
                            "_obs":               classif.get("observacao", "") if status == "OK" else classif.get("erro", ""),
                        })

                    log_area.text_area(
                        "log", "\n".join(logs[-12:]),
                        height=240, label_visibility="collapsed",
                    )
                    stat_area.markdown(f"""
                    <div class="tr-metrics" style="flex-direction:column;">
                        {metric_card(i+1, "Processados")}
                        {metric_card(ok_n, "Sucesso", "success")}
                        {metric_card(err_n, "Erros", "error")}
                    </div>""", unsafe_allow_html=True)

                progress.progress(100, text="Concluido!")
                st.session_state["resultados_proc"] = resultados_proc
                st.session_state["dados_brutos"]    = dados_brutos
                for k in ["seq_confirmada", "seq_inicio_val", "_txt", "_xlsx", "_vig", "_zip"]:
                    st.session_state.pop(k, None)
        else:
            st.warning("Nenhum CNPJ detectado. Verifique o formato.")

    if "resultados_proc" in st.session_state:
        resultados_proc = st.session_state["resultados_proc"]
        dados_brutos    = st.session_state.get("dados_brutos", {})
        df_proc = pd.DataFrame(resultados_proc)
        ok_n    = len(df_proc[df_proc["_status"] == "OK"])
        err_n   = len(df_proc[df_proc["_status"] != "OK"])

        st.markdown("---")
        st.markdown(f"""
        <div class="tr-metrics">
            {metric_card(len(resultados_proc), "Total")}
            {metric_card(ok_n, "Classificados", "success")}
            {metric_card(err_n, "Erros", "error")}
        </div>""", unsafe_allow_html=True)

        cols_show = [c for c in df_proc.columns if not c.startswith("_")]
        st.dataframe(df_proc[cols_show], use_container_width=True, hide_index=True, height=300)

        st.markdown(f"""
        <div class="tr-card">
            <div class="tr-card-title">Passo 3 - Codigo de Servico, Tipo e Revisao</div>
            <div style="font-size:12px;color:{TR_TEXT_MUTED};margin-bottom:16px;">
                Informe o numero inicial da sequencia e clique em Confirmar.<br>
                Codigo de Servico = Codigo_Servicos = Codigo_eSocial
            </div>
        """, unsafe_allow_html=True)

        col_seq1, col_seq2, _ = st.columns([1, 1, 2])
        with col_seq1:
            seq_inicio = st.number_input(
                "Numero inicial da sequencia",
                min_value=1, max_value=999999,
                value=st.session_state.get("seq_inicio_val", 1),
                step=1, key="seq_inicio_input",
            )
            confirmar_seq = st.button("Confirmar sequencia", use_container_width=True)
            if confirmar_seq:
                for i in range(len(resultados_proc)):
                    st.session_state.pop(f"cod_srv_{i}", None)
                st.session_state["seq_inicio_val"] = seq_inicio
                st.session_state["seq_confirmada"] = True
                st.rerun()
        with col_seq2:
            seq_val = st.session_state.get("seq_inicio_val", None)
            if seq_val and st.session_state.get("seq_confirmada"):
                st.markdown(f"""
                <div style="background:{TR_CARD2};border:1px solid {TR_BORDER};border-radius:8px;
                            padding:12px;margin-top:28px;font-size:11px;color:{TR_TEXT_MUTED};">
                    Sequencia confirmada:<br>
                    <b style="color:{TR_ORANGE};font-size:14px;">
                        {seq_val} ate {seq_val + len(resultados_proc) - 1}
                    </b>
                </div>""", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        if not st.session_state.get("seq_confirmada"):
            st.info("Informe e confirme o numero inicial da sequencia para exibir os campos de Codigo de Servico.")
        else:
            seq_inicio = st.session_state["seq_inicio_val"]
            st.markdown(f"""
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr;gap:8px;
                        padding:6px 12px;background:{TR_CARD};border-radius:6px;
                        font-size:10px;font-weight:700;color:{TR_ORANGE};
                        text-transform:uppercase;letter-spacing:.5px;margin-bottom:4px;">
                <div>Empresa</div><div>Cod. Servico</div><div>Tipo</div>
            </div>""", unsafe_allow_html=True)

            tipos_selecionados = {}
            codigos_servico    = {}

            for idx, row in enumerate(resultados_proc):
                status   = row.get("_status", "")
                mun      = row.get("municipio", "") or ""
                uf       = row.get("uf", "") or ""
                cod_mun  = row.get("cod_municipio_dom", "")
                cor_mun  = TR_SUCCESS if cod_mun and "nao" not in str(cod_mun) else TR_ERROR
                cor_st   = TR_SUCCESS if status == "OK" else TR_ERROR
                icone    = "OK" if status == "OK" else "X"
                seq_auto = seq_inicio + idx

                col_info, col_cod_srv, col_tipo = st.columns([2, 1, 1])
                with col_info:
                    st.markdown(f"""
                    <div class="tipo-row">
                        <div style="font-size:12px;font-weight:700;color:{TR_TEXT};">
                            {icone} <code style="color:{TR_ORANGE};">{row['cnpj']}</code>
                            &nbsp; {(row.get('razao_social','') or 'sem nome')[:40]}
                        </div>
                        <div style="font-size:10px;color:{TR_TEXT_MUTED};margin-top:3px;">
                            FPAS <b style="color:{TR_ORANGE};">{row.get('codigo_fpas','?')}</b>
                            &nbsp; {mun}/{uf}
                            &nbsp; Cod.Mun: <b style="color:{cor_mun};">{cod_mun or 'nao encontrado'}</b>
                            &nbsp; <span style="color:{cor_st};">{status}</span>
                        </div>
                    </div>""", unsafe_allow_html=True)
                with col_cod_srv:
                    cod_srv = st.number_input(
                        f"Cod. Servico #{idx+1}",
                        min_value=1, max_value=999999,
                        value=seq_auto, step=1,
                        key=f"cod_srv_{idx}",
                        label_visibility="collapsed",
                    )
                    codigos_servico[idx] = int(cod_srv)
                with col_tipo:
                    tipos_selecionados[idx] = st.selectbox(
                        f"Tipo #{idx+1}",
                        options=list(TIPOS_EMPRESA.keys()),
                        format_func=lambda k: f"{k} - {TIPOS_EMPRESA[k]}",
                        key=f"tipo_{idx}",
                        label_visibility="collapsed",
                    )

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown(
                f'<div class="tr-card"><div class="tr-card-title">Passo 4 - Gerar e Baixar Arquivos</div></div>',
                unsafe_allow_html=True,
            )

            col_d1, _ = st.columns(2)
            with col_d1:
                if st.button("Gerar Arquivos", type="primary", use_container_width=True):
                    codigo_empresa_dom = st.session_state.get("codigo_empresa_dom_val", 1)
                    linhas_fo  = []
                    linhas_vig = []

                    for idx, row in enumerate(resultados_proc):
                        cod_srv  = codigos_servico.get(idx, seq_inicio + idx)
                        tipo_cod = tipos_selecionados.get(idx, 1)
                        r_merged = dados_brutos.get(idx)

                        if r_merged:
                            linha_fo = montar_linha_dominio(
                                r_merged, tipo_cod=tipo_cod,
                                cod_servico=cod_srv, codigo_empresa=codigo_empresa_dom,
                            )
                        else:
                            linha_fo = [""] * 25
                            linha_fo[0]  = codigo_empresa_dom
                            linha_fo[1]  = cod_srv
                            linha_fo[2]  = row["cnpj"]
                            linha_fo[3]  = 1
                            linha_fo[17] = cod_srv
                            linha_fo[18] = 1
                            linha_fo[19] = tipo_cod
                            linha_fo[21] = "01/01/2020"
                            linha_fo[22] = 1
                            linha_fo[23] = cod_srv
                        linhas_fo.append(linha_fo)

                        if r_merged:
                            cod_mun_v = buscar_codigo_municipio(
                                r_merged.get("municipio", ""), r_merged.get("uf", "")
                            )
                            linha_vig = montar_linha_vigencia(
                                r_merged,
                                cod_servico=cod_srv,
                                tipo_cod=tipo_cod,
                                codigo_empresa=codigo_empresa_dom,
                                vigencia=vigencia_str,
                                descricao_vigencia=descricao_vig,
                                cod_mun=cod_mun_v,
                            )
                        else:
                            linha_vig = _linha_vigencia_vazia(
                                row["cnpj"], cod_srv, tipo_cod,
                                codigo_empresa_dom, vigencia_str, descricao_vig,
                            )
                        linhas_vig.append(linha_vig)

                    df_conf = pd.DataFrame(linhas_fo, columns=COLUNAS_LEIAUTE)
                    df_conf["_status"] = [r["_status"] for r in resultados_proc]
                    df_err  = df_conf[df_conf["_status"] != "OK"]
                    cols_xl = [c for c in df_conf.columns if c != "_status"]

                    _txt  = gerar_txt_leiaute(linhas_fo)
                    _vig  = gerar_txt_vigencias(linhas_vig)
                    _xlsx = gerar_excel_conferencia(
                        df_conf[cols_xl + ["_status"]],
                        df_err[cols_xl + ["_status"]] if len(df_err) > 0 else None,
                    )
                    _zip  = gerar_zip(_txt, _vig)

                    st.session_state["_txt"]  = _txt
                    st.session_state["_vig"]  = _vig
                    st.session_state["_xlsx"] = _xlsx
                    st.session_state["_zip"]  = _zip
                    st.success("Arquivos gerados com sucesso!")

            if "_zip" in st.session_state:
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        "Baixar Tudo (.zip)\nfoservicos + fovigencias",
                        data=st.session_state["_zip"],
                        file_name="dominio_importacao.zip",
                        mime="application/zip",
                        use_container_width=True,
                    )
                with col_dl2:
                    st.download_button(
                        "Excel Conferencia\n(.xlsx formatado)",
                        data=st.session_state["_xlsx"],
                        file_name="dominio_conferencia.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True,
                    )

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 - CONSULTA INDIVIDUAL
# ══════════════════════════════════════════════════════════════════════════════
with tab_individual:
    st.markdown(
        '<div class="tr-card"><div class="tr-card-title">Consulta Individual de CNPJ</div>',
        unsafe_allow_html=True,
    )
    col_inp, col_btn = st.columns([3, 1])
    with col_inp:
        cnpj_input = st.text_input(
            "CNPJ", placeholder="00.000.000/0000-00", label_visibility="collapsed"
        )
    with col_btn:
        buscar = st.button("Consultar", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if buscar and cnpj_input:
        with st.spinner("Consultando..."):
            dados_rf = consultar_cnpj(cnpj_input, delay=0.3)
        if dados_rf.get("erro"):
            st.error(f"Erro: {dados_rf['erro']}")
        else:
            simples = dados_rf.get("simples", False)
            classif = classificar(
                dados_rf.get("cnae_codigo", ""),
                simples=simples, fap=fap, convenios=convenios,
            )
            mun    = dados_rf.get("municipio", "")
            uf_val = dados_rf.get("uf", "")
            cod_mun = buscar_codigo_municipio(mun, uf_val)
            st.markdown(f"""
            <div class="tr-card">
                <div class="tr-card-title">Dados</div>
                <div class="result-grid">
                    {result_item("CNPJ",                     dados_rf["cnpj"])}
                    {result_item("Razao Social",              dados_rf["razao_social"], True)}
                    {result_item("Situacao",                  dados_rf.get("situacao", "?"))}
                    {result_item("Simples Nacional",          "SIM" if simples else "NAO")}
                    {result_item("Municipio/UF",              f"{mun}/{uf_val}")}
                    {result_item("Cod. Municipio (Dominio)",  cod_mun or "nao encontrado", True)}
                    {result_item("CNAE",                      dados_rf.get("cnae_codigo", "?"), True)}
                </div>
            </div>""", unsafe_allow_html=True)
            if not classif.get("erro"):
                cod3 = classif["codigo_terceiro"]
                st.markdown(f"""
                <div class="tr-card">
                    <div class="tr-card-title">Classificacao FPAS</div>
                    <div class="result-grid">
                        {result_item("FPAS",           classif["fpas"], True)}
                        {result_item("Descricao",      classif["fpas_descricao"])}
                        {result_item("Cod. Terceiros", f"{cod3:04d}" if isinstance(cod3, int) else "?", True)}
                        {result_item("RAT",            f"{classif['perc_acid_trabalho']}%")}
                        {result_item("GPS",            classif["codigo_gps"])}
                        {result_item("GFIP",           classif["codigo_gfip"])}
                    </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.warning(f"Aviso: {classif['erro']}")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 - TABELA FPAS
# ══════════════════════════════════════════════════════════════════════════════
with tab_tabela:
    st.markdown(
        '<div class="tr-card"><div class="tr-card-title">Tabela FPAS / Terceiros</div>',
        unsafe_allow_html=True,
    )
    ref_rows = []
    for fpas, (terc, rat, gps, gfip, desc) in FPAS_CONFIG.items():
        ents      = decodificar_terceiros(terc)
        total_pct = sum(e["aliquota"] for e in ents)
        siglas    = " + ".join(e["sigla"] for e in ents) if ents else "nenhuma"
        ref_rows.append({
            "FPAS":           fpas,
            "Descricao":      desc,
            "Cod. Terceiros": f"{terc:04d}",
            "Entidades":      siglas,
            "Total 3s (%)":   f"{total_pct:.1f}%",
            "RAT Base (%)":   f"{rat}%",
            "Cod. GPS":       gps,
            "Cod. GFIP":      gfip,
        })
    df_ref     = pd.DataFrame(ref_rows)
    busca_fpas = st.text_input("Filtrar", placeholder="Ex: 833 ou Construcao")
    if busca_fpas:
        mask = (
            df_ref["FPAS"].astype(str).str.contains(busca_fpas, case=False)
            | df_ref["Descricao"].str.contains(busca_fpas, case=False)
            | df_ref["Entidades"].str.contains(busca_fpas, case=False)
        )
        df_ref = df_ref[mask]
    st.dataframe(df_ref, use_container_width=True, hide_index=True, height=480)
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 - IMPORTACAO DOMINIO
# ══════════════════════════════════════════════════════════════════════════════
with tab_importacao:

    st.markdown(f"""
    <div class="tr-card">
        <div class="tr-card-title">Como Importar os Arquivos no Dominio Sistemas</div>
        <div style="font-size:12px;color:{TR_TEXT_MUTED};line-height:2;">
            Siga o caminho abaixo no menu do Dominio Folha de Pagamento:
        </div>
    </div>
    """, unsafe_allow_html=True)

    passos = [
        ("1", "Utilitarios",       "Menu principal superior"),
        ("2", "Importacao",        "Submenu lateral"),
        ("3", "de Arquivo Texto",  "Submenu lateral"),
        ("4", "de Tabelas",        "Opcao final"),
    ]
    setas_html = ""
    for num, titulo, sub in passos:
        setas_html += f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="background:{TR_ORANGE};color:#fff;font-weight:900;font-size:13px;
                        border-radius:50%;width:26px;height:26px;display:flex;
                        align-items:center;justify-content:center;flex-shrink:0;">{num}</div>
            <div style="background:{TR_CARD2};border:1px solid {TR_BORDER};border-radius:8px;
                        padding:8px 16px;flex:1;">
                <span style="color:{TR_ORANGE};font-weight:700;font-size:13px;">{titulo}</span>
                <span style="color:{TR_TEXT_MUTED};font-size:11px;margin-left:10px;">{sub}</span>
            </div>
        </div>"""
    st.markdown(setas_html, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{TR_CARD2};border:1px dashed {TR_ORANGE};border-radius:8px;
                padding:14px 18px;margin:16px 0;font-size:12px;color:{TR_TEXT_MUTED};line-height:2;">
        <b style="color:{TR_ORANGE};">Caminho completo:</b><br>
        <code style="color:{TR_TEXT};font-size:13px;">
            Utilitarios &nbsp;&rarr;&nbsp; Importacao &nbsp;&rarr;&nbsp;
            de Arquivo Texto &nbsp;&rarr;&nbsp; de Tabelas
        </code><br><br>
        <b style="color:{TR_ORANGE};">Configuracoes na janela de importacao:</b><br>
        Delimitador: <b style="color:{TR_TEXT};">Com Separador</b> &nbsp;|&nbsp;
        Separador: <b style="color:{TR_TEXT};">Tab</b>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="tr-card" style="margin-top:8px;">
        <div class="tr-card-title">Ordem de Importacao</div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
            <div style="background:{TR_CARD2};border:1px solid {TR_BORDER};border-radius:8px;padding:14px 18px;">
                <div style="font-size:11px;color:{TR_TEXT_MUTED};text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">1 Importar primeiro</div>
                <div style="font-size:16px;font-weight:700;color:{TR_ORANGE};">foservicos.txt</div>
                <div style="font-size:11px;color:{TR_TEXT_MUTED};margin-top:4px;">
                    Tabela: <b style="color:{TR_TEXT};">FOSERVICOS</b><br>
                    Cadastro principal do prestador de servico.<br>
                    25 colunas &nbsp;|&nbsp; TAB-delimitado
                </div>
            </div>
            <div style="background:{TR_CARD2};border:1px solid {TR_BORDER};border-radius:8px;padding:14px 18px;">
                <div style="font-size:11px;color:{TR_TEXT_MUTED};text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px;">2 Importar segundo</div>
                <div style="font-size:16px;font-weight:700;color:{TR_ORANGE};">fovigencias_servicos.txt</div>
                <div style="font-size:11px;color:{TR_TEXT_MUTED};margin-top:4px;">
                    Tabela: <b style="color:{TR_TEXT};">FOVIGENCIAS_SERVICO</b><br>
                    Vigencias e aliquotas FPAS / Terceiros / eSocial.<br>
                    90 colunas &nbsp;|&nbsp; TAB-delimitado
                </div>
            </div>
        </div>
        <div style="margin-top:12px;padding:10px 14px;background:#1a1200;
                    border:1px solid {TR_WARNING};border-radius:6px;
                    font-size:11px;color:{TR_WARNING};">
            ATENCAO: Importe sempre o <b>foservicos.txt primeiro</b>.
            O FOVIGENCIAS depende do registro pai ja existir na tabela FOSERVICOS.
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Download dos arquivos de leiaute ──────────────────────────────────────
    st.markdown(f"""
    <div class="tr-card" style="margin-top:8px;">
        <div class="tr-card-title">Arquivos de Leiaute (Definicao das Colunas)</div>
        <div style="font-size:12px;color:{TR_TEXT_MUTED};margin-bottom:14px;">
            Estes arquivos definem o leiaute de importacao aceito pelo Dominio.
            Faca o download e mantenha-os salvos para configurar ou reconfigurar a importacao.
        </div>
    </div>
    """, unsafe_allow_html=True)

    leiaute_fo  = _ler_leiaute("FOSERVICOS.txt")
    leiaute_vig = _ler_leiaute("FOVIGENCIAS_SERVICO.txt")

    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        if leiaute_fo:
            st.download_button(
                label="Leiaute FOSERVICOS.txt\n(25 colunas - referencia)",
                data=leiaute_fo,
                file_name="FOSERVICOS.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.error("FOSERVICOS.txt nao encontrado no repositorio.")

    with col_l2:
        if leiaute_vig:
            st.download_button(
                label="Leiaute FOVIGENCIAS_SERVICO.txt\n(90 colunas - referencia)",
                data=leiaute_vig,
                file_name="FOVIGENCIAS_SERVICO.txt",
                mime="text/plain",
                use_container_width=True,
            )
        else:
            st.error("FOVIGENCIAS_SERVICO.txt nao encontrado no repositorio.")

    with col_l3:
        if leiaute_fo and leiaute_vig:
            buf_leiautes = io.BytesIO()
            with zipfile.ZipFile(buf_leiautes, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr("FOSERVICOS.txt", leiaute_fo)
                zf.writestr("FOVIGENCIAS_SERVICO.txt", leiaute_vig)
            st.download_button(
                label="Baixar Ambos os Leiautes (.zip)",
                data=buf_leiautes.getvalue(),
                file_name="leiautes_dominio.zip",
                mime="application/zip",
                use_container_width=True,
            )
        else:
            st.warning("Um ou mais arquivos de leiaute nao encontrados no repositorio.")

    # ── Resumo das colunas ────────────────────────────────────────────────────
    with st.expander("Ver resumo das colunas - FOSERVICOS (25 colunas)"):
        colunas_fo = [
            ("1",  "codi_emp",           "integer",  "Codigo da empresa no Dominio"),
            ("2",  "i_servicos",         "integer",  "Codigo do servico (sequencial)"),
            ("3",  "cgc",                "char 14",  "CNPJ sem mascara (so digitos)"),
            ("4",  "tipo_insc",          "smallint", "1=CNPJ / 2=CPF / 3=CEI"),
            ("5",  "codigo_terceiro",    "numeric",  "Codigo terceiros (ex: 0115)"),
            ("6",  "perc_acid_trabalho", "numeric",  "RAT (%)"),
            ("7",  "codigo_fpas",        "numeric",  "Codigo FPAS (ex: 515)"),
            ("8",  "codigo_atividade",   "numeric",  "CNAE so digitos (ex: 6201500)"),
            ("9",  "codigo_gfip",        "numeric",  "Codigo SEFIP (ex: 115)"),
            ("10", "codigo_gps",         "numeric",  "Codigo GPS (ex: 2100)"),
            ("11", "nome",               "char 40",  "Razao social"),
            ("12", "endereco",           "char 31",  "Logradouro"),
            ("13", "numero",             "integer",  "Numero do endereco"),
            ("14", "bairro",             "char 20",  "Bairro"),
            ("15", "cep",                "char 8",   "CEP so digitos"),
            ("16", "cidade",             "char 20",  "Municipio"),
            ("17", "estado",             "char 2",   "UF"),
            ("18", "i_filiais",          "integer",  "Filial (= i_servicos)"),
            ("19", "sequencia_gps",      "integer",  "Sequencia GPS (= 1)"),
            ("20", "tipo",               "integer",  "1=Empresa / 2=Tomador..."),
            ("21", "codigo_municipio",   "integer",  "Codigo municipio Dominio"),
            ("22", "DATA_INICIO",        "date",     "DD/MM/AAAA"),
            ("23", "SITUACAO",           "smallint", "0=Inativo / 1=Ativo"),
            ("24", "CODIGO_ESOCIAL",     "varchar",  "Codigo eSocial (= i_servicos)"),
            ("25", "origem_reg",         "tinyint",  "1 = Imp. Tabelas"),
        ]
        st.dataframe(
            pd.DataFrame(colunas_fo, columns=["Col", "Campo", "Tipo", "Descricao"]),
            use_container_width=True, hide_index=True,
        )

    with st.expander("Ver resumo das colunas principais - FOVIGENCIAS_SERVICO (90 colunas)"):
        colunas_vig = [
            ("1",  "codi_emp",                 "integer",  "Codigo da empresa"),
            ("2",  "i_servicos",               "integer",  "Codigo do servico (FK -> FOSERVICOS)"),
            ("3",  "VIGENCIA",                 "date",     "DD/MM/AAAA - inicio da vigencia"),
            ("4",  "DESCRICAO",                "char 80",  "Descricao da vigencia"),
            ("5",  "cgc",                      "char 14",  "CNPJ so digitos"),
            ("6",  "tipo_insc",                "smallint", "1=CNPJ"),
            ("7",  "codigo_terceiro",          "numeric",  "Codigo terceiros"),
            ("8",  "perc_terceiro",            "numeric",  "Total % terceiros"),
            ("9",  "perc_inss_empresa",        "numeric",  "INSS Empresa % (0)"),
            ("10", "perc_acid_trabalho",       "numeric",  "RAT %"),
            ("13", "codigo_fpas",              "numeric",  "Codigo FPAS"),
            ("15", "codigo_gfip",              "numeric",  "Codigo SEFIP"),
            ("16", "codigo_gps",               "numeric",  "Codigo GPS"),
            ("25", "i_filiais",                "integer",  "Filial (sempre 1)"),
            ("28", "origem_reg",               "tinyint",  "0=Sistema"),
            ("29", "tipo",                     "integer",  "Tipo servico"),
            ("31", "codigo_municipio",         "integer",  "Codigo municipio Dominio"),
            ("43", "I_CNAE20",                 "char 15",  "CNAE so digitos"),
            ("49", "COMPETENCIA_FIM_VIGENCIA", "date",     "DD/MM/AAAA - fim vigencia (31/12/3000)"),
            ("64", "ENVIAR_ESOCIAL_S_1005",    "smallint", "1=Sim"),
            ("70", "ENVIAR_ESOCIAL_S_1020",    "smallint", "1=Sim"),
            ("73", "I_CNAE_ESOCIAL",           "varchar",  "= I_CNAE20"),
            ("74", "I_TERCEIROS",              "integer",  "Valor inteiro codigo_terceiro"),
            ("77", "ORIGEM_ALTERACAO",         "smallint", "1=Sistema"),
            ("81", "ENVIAR_ESOCIAL_S_1080",    "smallint", "1=Sim"),
        ]
        st.dataframe(
            pd.DataFrame(colunas_vig, columns=["Col", "Campo", "Tipo", "Descricao"]),
            use_container_width=True, hide_index=True,
        )

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="tr-footer">
    <span>DOMINIO SISTEMAS</span> &nbsp;.&nbsp; Thomson Reuters &nbsp;.&nbsp;
    Classificador FPAS / Terceiros / SEFIP &nbsp;.&nbsp; IN RFB no 971/2009 &nbsp;.&nbsp; <span>v8.4</span>
</div>""", unsafe_allow_html=True)
