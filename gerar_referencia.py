"""
Gera a pasta referencia/ do Importador de Tomadores a partir de um banco da Domínio (somente leitura).
O app web não acessa o banco: ele usa só estes arquivos. Rode de novo quando a Domínio for atualizada.

    python gerar_referencia.py --dsn Contabil --usuario externo
    (senha: variável DOMINIO_DB_PASSWORD ou digitada; --leiaute N também exporta o leiaute N para leiaute/)
"""
import argparse
import csv
import datetime as dt
import getpass
import json
import os
import re
import unicodedata
from collections import defaultdict
from difflib import SequenceMatcher

import pyodbc

PASTA = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(PASTA, "referencia")
TABELAS = ("FOSERVICOS", "FOVIGENCIAS_SERVICO")
UF_IBGE = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI",
           "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
           "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
LIMIAR_APROXIMADA = 0.88


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c)).upper()
    return re.sub(r"[^A-Z0-9]+", " ", s).strip()


def txt(v):
    return "" if v is None else str(v).strip()


def gravar(nome, cab, linhas):
    with open(os.path.join(REF, nome), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(cab)
        w.writerows(linhas)
    print(f"  {nome}: {len(linhas)} linha(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dsn", default="Contabil")
    ap.add_argument("--usuario", default=os.environ.get("DOMINIO_DB_USER", "externo"))
    ap.add_argument("--leiaute", type=int, default=None)
    a = ap.parse_args()
    senha = os.environ.get("DOMINIO_DB_PASSWORD") or getpass.getpass("Senha do banco: ")
    cur = pyodbc.connect(f"DSN={a.dsn};UID={a.usuario};PWD={senha}", timeout=30, readonly=True,
                         autocommit=True).cursor()
    os.makedirs(REF, exist_ok=True)
    banco = cur.execute("select db_name()").fetchone()[0]
    print(f"Banco {banco} — gerando {REF}")

    # CNAE 2.3 e CNAE eSocial (anterior a 12/2018)
    cnae = {txt(i): txt(d) for i, d in cur.execute("select i_cnae20, descricao from bethadba.gecnae20").fetchall()}
    prev = {txt(r[0]) for r in cur.execute("select I_CNAE from bethadba.GECNAE_PREVIDENCIA_SOCIAL").fetchall()}
    gravar("cnae.csv", ["cnae", "descricao", "cnae_esocial_antigo"],
           [[c, d, "S" if c in prev else "N"] for c, d in sorted(cnae.items())])

    # FPAS (códigos) e relação CNAE x FPAS pelas atividades da FOFPAS
    fofpas = cur.execute("select I_FPAS, CODIGO_FPAS, DESCRICAO from bethadba.FOFPAS order by I_FPAS").fetchall()
    gerais = {}
    for i, f, d in fofpas:
        gerais.setdefault(int(f), (int(i), txt(d)))
    gravar("fpas.csv", ["fpas", "i_fpas", "descricao"], [[f, i, d] for f, (i, d) in sorted(gerais.items())])
    ativ = [(int(i), int(f), txt(d)) for i, f, d in fofpas if int(i) != gerais[int(f)][0]]
    por_desc = defaultdict(list)
    for c, d in cnae.items():
        por_desc[norm(d)].append(c)
    ligado, usadas = defaultdict(list), set()
    for i, f, d in ativ:
        for c in por_desc.get(norm(d), []):
            ligado[c].append((f, i, d, "exata"))
            usadas.add(i)
    sobra = [(i, f, d) for i, f, d in ativ if i not in usadas]
    for c, d in cnae.items():
        if c in ligado:
            continue
        melhor = max(((SequenceMatcher(None, norm(d), norm(ad)).ratio(), f, i, ad) for i, f, ad in sobra),
                     default=(0, None, None, None))
        if melhor[0] >= LIMIAR_APROXIMADA:
            ligado[c].append((melhor[1], melhor[2], melhor[3], f"aproximada ({melhor[0]:.0%})"))
    classe = defaultdict(set)
    for c, v in ligado.items():
        classe[c[:5]].update(f for f, *_ in v)
    linhas = []
    for c, d in sorted(cnae.items()):
        v = ligado.get(c, [])
        fpas_set = sorted({f for f, *_ in v})
        if len(fpas_set) == 1:
            f, i, ad, lig = v[0]
            linhas.append([c, d, f, i, ad, lig, ""])
        elif len(fpas_set) > 1:
            linhas.append([c, d, "", "", "", "ambígua", "|".join(map(str, fpas_set))])
        elif len(classe.get(c[:5], ())) == 1:
            linhas.append([c, d, next(iter(classe[c[:5]])), "", "", "pela classe CNAE", ""])
        else:
            linhas.append([c, d, "", "", "", "sem FPAS", "|".join(map(str, sorted(classe.get(c[:5], ()))))])
    gravar("cnae_fpas.csv", ["cnae", "descricao", "fpas", "i_fpas", "atividade_fofpas", "ligacao", "alternativas"],
           linhas)

    # Terceiros: FOTABELA_TERCEIROS (é a que a tela grava em I_TERCEIROS) + soma das alíquotas por entidade
    entidades = {int(c): txt(d) for c, d in cur.execute(
        "select CODIGO_CONVENIO, DESCRICAO from bethadba.FOCONVENIOS_TERCEIROS").fetchall()}
    comp = defaultdict(list)
    for i, conv, aliq in cur.execute("select I_TERCEIROS, CODIGO_CONVENIO, ALIQUOTA "
                                     "from bethadba.FOTABELA_TERCEIROS_CONVENIOS").fetchall():
        comp[int(i)].append((int(conv), float(aliq or 0)))
    terc = []
    for i, f, cod, d in cur.execute("select I_TERCEIROS, CODIGO_FPAS, CODIGO_TERCEIROS, DESCRICAO "
                                    "from bethadba.FOTABELA_TERCEIROS order by CODIGO_FPAS, CODIGO_TERCEIROS").fetchall():
        partes = sorted(comp.get(int(i), []))
        terc.append([int(i), int(f or 0), int(cod or 0), txt(d), f"{sum(p for _, p in partes):.2f}",
                     " + ".join(f"{entidades.get(c, c)} {p:.2f}%" for c, p in partes)])
    gravar("terceiros.csv", ["i_terceiros", "fpas", "codigo", "descricao", "percentual", "composicao"], terc)

    # RAT por CNAE
    gravar("rat_cnae.csv", ["vigencia", "cnae", "aliquota"],
           [[v.strftime("%Y-%m-%d"), txt(c), f"{float(al):.3f}"] for v, c, al in cur.execute(
               "select VIGENCIA, I_CNAE20, ALIQUOTA from bethadba.FOALIQUOTA_ACIDENTE_TRABALHO_CNAE "
               "order by I_CNAE20, VIGENCIA").fetchall()])

    # Municípios (código Domínio, código Receita, IBGE, UF)
    gravar("municipios.csv", ["codigo_municipio", "nome", "codigo_srf", "codigo_ibge", "uf"],
           [[int(c), txt(n), txt(s), txt(i), UF_IBGE.get(txt(i)[:2], "")] for c, n, s, i in cur.execute(
               "select codigo_municipio, nome_municipio, codigo_srf, codigo_ibge from bethadba.gemunicipio "
               "order by codigo_municipio").fetchall()])

    # Colunas e chaves estrangeiras das duas tabelas
    gravar("colunas.csv", ["tabela", "coluna", "tipo", "largura", "escala", "nulo", "pk", "padrao"],
           [[t.upper(), c, (tp or "").lower(), int(w or 0), int(e or 0), n, p, "" if d is None else d]
            for t, c, tp, w, e, n, p, d in cur.execute(
               'select t.table_name, c.column_name, d.domain_name, c.width, c.scale, c.nulls, c.pkey, c."default" '
               "from sys.syscolumn c join sys.systable t on t.table_id = c.table_id "
               "join sys.sysuser u on u.user_id = t.creator join sys.sysdomain d on d.domain_id = c.domain_id "
               "where u.user_name = 'bethadba' and upper(t.table_name) in ('FOSERVICOS', 'FOVIGENCIAS_SERVICO') "
               "order by t.table_name, c.column_id").fetchall()])
    fks = []
    for f, p, cols in cur.execute("select foreign_tname, primary_tname, columns from sys.sysforeignkeys "
                                  "where upper(foreign_tname) in ('FOSERVICOS', 'FOVIGENCIAS_SERVICO')").fetchall():
        for par in str(cols).split(","):
            col = par.split(" IS ")[0].strip().upper()
            if col != "CODI_EMP":
                fks.append([f.upper(), col, p])
    gravar("fks.csv", ["tabela", "coluna", "tabela_mae"], fks)

    if a.leiaute is not None:
        pasta_lei = os.path.join(PASTA, "leiaute")
        os.makedirs(pasta_lei, exist_ok=True)
        for tab in TABELAS:
            rows = cur.execute(
                "select i_layout, i_nome, i_sequencial, campo, descricao, tipo_dado, tipo_campo, tamanho, mascara, "
                "origem_valor, valor_fixo, nro_dec from bethadba.gelayout_campos "
                "where i_layout = ? and upper(i_nome) = ? order by i_sequencial", a.leiaute, tab).fetchall()
            with open(os.path.join(pasta_lei, f"{tab}.txt"), "w", encoding="cp1252", errors="replace",
                      newline="") as f:
                f.write("\r\n".join("\t".join("" if v is None else str(v) for v in r) for r in rows) + "\r\n")
            print(f"  leiaute/{tab}.txt: {len(rows)} campo(s) do leiaute {a.leiaute}")

    with open(os.path.join(REF, "versao.json"), "w", encoding="utf-8") as f:
        json.dump({"banco": banco, "dsn": a.dsn, "gerado_em": dt.datetime.now().strftime("%d/%m/%Y %H:%M")}, f,
                  ensure_ascii=False, indent=2)
    print("Pronto.")


if __name__ == "__main__":
    main()
