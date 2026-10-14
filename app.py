"""
Importador de Tomadores de Serviço — Domínio Folha (Arquivo > Serviços)
App web, sem acesso ao banco: gera os arquivos da importação de tabelas (FOSERVICOS + FOVIGENCIAS_SERVICO).

1. CNPJ da empresa prestadora -> Receita (CNAE principal, regime) -> relação CNAE x FPAS da Domínio ->
   FPAS, terceiros, RAT, INSS, SEFIP e GPS (Soluções 136 e 3665).
2. Tomadores por digitação ou planilha: mesma lista, mesma limpeza, mesma consulta e a MESMA herança tributária.
3. Conferência linha a linha e arquivos para importar.

Executar:
    streamlit run app.py
"""
import datetime as dt
import hashlib
import json
import os
import time

import pandas as pd
import streamlit as st

import core

PASTA = os.path.dirname(os.path.abspath(__file__))
REF_DIR, LEI_DIR = os.path.join(PASTA, "referencia"), os.path.join(PASTA, "leiaute")
ST_OK, ST_REV, ST_ERR, ST_FILA = "✅ Pronto", "⚠️ Revisar", "❌ Erro", "⏳ Aguardando consulta"
ORCAMENTO_SEG = 8          # tempo de consulta por execução da tela (o restante continua na próxima)
ss = st.session_state

st.set_page_config(page_title="Importador de Tomadores — Domínio", page_icon="🏗️", layout="wide")
st.title("🏗️ Importador de Tomadores de Serviço — Domínio Folha")
st.caption("Informe o CNPJ da prestadora, inclua os tomadores (digitando ou por planilha) e baixe os arquivos da "
           "importação de tabelas. Todo tomador herda FPAS, terceiros, RAT, INSS, SEFIP e GPS da prestadora.")


def desenhar_passos(ph, atual: int):
    nomes = ["Prestadora", "Herança tributária", "Tomadores", "Conferência", "Arquivos"]
    with ph.container():
        cols = st.columns(len(nomes))
        for i, nome in enumerate(nomes, 1):
            if i < atual:
                cols[i - 1].markdown(f":green[✅ **{i}. {nome}**]")
            elif i == atual:
                cols[i - 1].markdown(f":blue[▶ **{i}. {nome}**]")
            else:
                cols[i - 1].markdown(f":gray[○ {i}. {nome}]")
        st.progress((atual - 1) / (len(nomes) - 1))


ph_passos = st.empty()
desenhar_passos(ph_passos, 1)


@st.cache_resource(show_spinner="Carregando as tabelas de referência…")
def referencia():
    return core.Referencia(REF_DIR)


try:
    ref = referencia()
except Exception as e:
    st.error(f"Não consegui ler a pasta 'referencia' ({e}). Gere com: python gerar_referencia.py")
    st.stop()

for k, v in (("prestadora", None), ("tomadores", {}), ("fila", []), ("processando", False), ("planilha", None),
             ("tentativas", {})):
    ss.setdefault(k, v)


def d(chave, **padrao):
    """Padrão do widget só quando ainda não há valor na sessão (evita conflito com o perfil carregado)."""
    return {"key": chave} if chave in ss else {"key": chave, **padrao}


def _pausar():
    ss["processando"] = False


def _retomar():
    ss["processando"] = True


def aplicar_perfil(dados: bytes):
    fid = hashlib.md5(dados).hexdigest()
    if ss.get("perfil_id") == fid:
        return
    try:
        p = json.loads(dados.decode("utf-8-sig"))
    except ValueError as e:
        st.sidebar.error(f"Perfil inválido: {e}")
        return
    ss["perfil_id"], ss["prestadora"] = fid, p["receita"]
    c = p["receita"]["cnpj"]
    for chave, wk in (("empresa", f"emp_{c}"), ("ultimo", f"ult_{c}"), ("filial", f"fil_{c}"),
                      ("descricao", f"desc_{c}"), ("regime", f"reg_{c}"), ("fpas", f"fpas_{c}"),
                      ("rat", f"rat_{c}"), ("sefip", f"sefip_{c}"), ("tipo_servico", "w_tserv"),
                      ("lotacao_cnpj", "w_lotj"), ("lotacao_cpf", "w_lotf"), ("cnae_cadastro", "w_cnae_cad"),
                      ("de_para", "w_depara"), ("destino", "w_destino")):
        if chave in p:
            ss[wk] = p[chave]
    reg, fp = p.get("regime"), p.get("fpas")
    for chave, wk in (("i_terceiros", f"terc_{c}_{fp}_{reg}"), ("inss", f"inss_{c}_{reg}"),
                      ("prolab", f"prolab_{c}_{reg}"), ("gps", f"gps_{c}_{reg}")):
        if chave in p:
            ss[wk] = p[chave]


# =====================================================================
# Barra lateral: perfil salvo, leiaute e opções
# =====================================================================
with st.sidebar:
    st.header("Configuração")
    with st.expander("💾 Carregar perfil salvo da prestadora"):
        f_perfil = st.file_uploader("Arquivo .json salvo antes", type=["json"])
        if f_perfil is not None:
            aplicar_perfil(f_perfil.getvalue())

    st.subheader("Leiaute da importação")
    lei_pasta = core.ler_leiaute_pasta(LEI_DIR)
    opcoes_lei = (["Leiaute da ferramenta"] if all(t in lei_pasta for t in core.TABELAS) else []) + \
                 ["Enviar arquivos de leiaute (.txt)"]
    esc_lei = st.radio("Origem do leiaute", opcoes_lei, label_visibility="collapsed",
                       help="O mesmo leiaute que será usado na importação de tabelas da Domínio.")
    if esc_lei == "Leiaute da ferramenta":
        leiaute = lei_pasta
    else:
        envios = st.file_uploader("Leiaute de FOSERVICOS e FOVIGENCIAS_SERVICO exportado da Domínio", type=["txt"],
                                  accept_multiple_files=True)
        leiaute = core.ler_leiaute_txt({f.name: f.getvalue() for f in envios or []})
    if not all(t in leiaute for t in core.TABELAS):
        st.info("Envie o leiaute das duas tabelas.")
        st.stop()
    numero_lei = str(leiaute[core.T_SERV]["linhas"][0][0]).strip()
    # Sem o campo na tela: usa o destino do perfil salvo ou, se não houver, o número do leiaute de origem
    destino_lei = int(ss.get("w_destino") or (int(numero_lei) if numero_lei.isdigit() else 1))

    with st.expander("Opções avançadas"):
        cnae_cad = st.radio("CNAE gravado no tomador", ["tomador", "prestadora"], **d("w_cnae_cad"),
                            format_func={"tomador": "CNAE principal do tomador (Receita)",
                                         "prestadora": "CNAE da prestadora"}.get)
        de_para_txt = st.text_input("Tipo de logradouro → código Domínio", **d("w_depara"),
                                    placeholder="RUA=?; AVENIDA=?",
                                    help="Código que a Domínio grava em TIPO_ENDERECO. Sem de-para, o tipo vai no "
                                         "início do endereço (ex.: 'AVENIDA PAULISTA').")
        cadastrados_txt = st.text_area("CNPJs/CPFs já cadastrados como serviço na empresa (opcional)",
                                       help="Um por linha. Eles ficam fora do arquivo, para não duplicar.")

de_para = {}
for parte in (de_para_txt or "").replace("\n", ";").split(";"):
    nome_tipo, _, cod = parte.partition("=")
    if core.norm(nome_tipo) and cod.strip().isdigit():
        de_para[core.norm(nome_tipo)] = int(cod)
cadastrados = {core.normalizar_inscricao(l)[0] for l in (cadastrados_txt or "").splitlines()} - {""}

# =====================================================================
# Passo 1 · Empresa prestadora
# =====================================================================
st.subheader("Passo 1 · Empresa prestadora")
with st.form("f_prestadora"):
    c1, c2 = st.columns([3, 1])
    cnpj_digitado = c1.text_input("CNPJ da empresa prestadora", placeholder="00.000.000/0001-00",
                                  value=core.formatar_inscricao(ss["prestadora"]["cnpj"]) if ss["prestadora"] else "")
    buscar = c2.form_submit_button("🔎 Consultar na Receita", type="primary", width="stretch")
if buscar:
    cnpj, _, erro_insc = core.normalizar_inscricao(cnpj_digitado)
    if erro_insc or not core.cnpj_valido(cnpj):
        st.error(erro_insc or "CNPJ inválido (dígito verificador não confere).")
    else:
        with st.spinner("Consultando a Receita…"):
            rec = core.consultar_cnpj(cnpj)
        if rec.get("erro"):
            st.error(rec["erro"])
        else:
            ss["prestadora"] = {**rec, "cnpj": cnpj}
prest = ss["prestadora"]
if not prest:
    st.info("Informe o CNPJ da prestadora para começar.")
    st.stop()

kp = prest["cnpj"]
ibge_p, mun_p = ref.municipio(prest.get("ibge"), prest.get("srf"), prest.get("cidade"), prest.get("uf"))
with st.container(border=True):
    a, b, c = st.columns([3, 3, 2])
    a.markdown(f"**{prest['razao']}**  \n{core.formatar_inscricao(kp)} · {prest.get('situacao') or '?'}")
    b.markdown(f"**CNAE principal:** {prest.get('cnae')} — {prest.get('cnae_desc') or ref.cnae.get(prest.get('cnae'), '')}"
               f"  \n**Natureza:** {prest.get('natureza_desc') or prest.get('natureza') or '—'}")
    c.markdown(f"**Município:** {mun_p[1] + '/' + mun_p[2] if mun_p else prest.get('cidade', '—')}"
               f"  \n**Fonte:** {prest.get('fonte', '')}")

c1, c2, c3, c4, c5 = st.columns([1.2, 1.2, 0.8, 1.2, 2])
empresa = c1.number_input("Código da empresa na Domínio", min_value=1, step=1, placeholder="obrigatório",
                          **d(f"emp_{kp}", value=None))
ultimo = c2.number_input("Último código de serviço já usado", min_value=0, step=1, placeholder="obrigatório",
                         help="Veja em Arquivo > Serviços. Os tomadores recebem os códigos seguintes.",
                         **d(f"ult_{kp}", value=None))
filial = c3.number_input("Filial", min_value=1, step=1, **d(f"fil_{kp}", value=1))
data_padrao = c4.date_input("Data de início (padrão)", format="DD/MM/YYYY",
                            **d(f"dt_{kp}", value=dt.date.today().replace(day=1)))
descricao = c5.text_input("Descrição da vigência", max_chars=80, **d(f"desc_{kp}", value="Cadastro inicial"))
if empresa is None or ultimo is None:
    st.info("Informe o código da empresa na Domínio e o último código de serviço já usado.")
    st.stop()
desenhar_passos(ph_passos, 2)

# =====================================================================
# Passo 2 · Herança tributária
# =====================================================================
st.subheader("Passo 2 · Herança tributária (igual para todos os tomadores)")
sug = core.sugerir_perfil(prest, ref, data_padrao)
regs = list(core.REGIMES)
c1, c2 = st.columns([1, 2])
regime = c1.selectbox("Regime da prestadora", regs, format_func=lambda r: core.REGIMES[r]["rotulo"],
                      **d(f"reg_{kp}", index=regs.index(sug["regime"])))
c2.caption(f"Sugestão pela Receita: {sug['motivo_regime']}.")
cfg_reg = core.REGIMES[regime]

opcoes_fpas = list(dict.fromkeys(([sug["fpas"]] if sug["fpas"] else []) + sug["alternativas"] + sorted(ref.fpas)))
c1, c2 = st.columns([1, 2])
fpas = c1.selectbox("FPAS", opcoes_fpas, placeholder="escolha o FPAS",
                    **d(f"fpas_{kp}", index=0 if sug["fpas"] else None),
                    format_func=lambda f: f"{f} — {ref.fpas.get(f, {}).get('descricao', '')[:70]}")
if sug["fpas"]:
    atividade = sug["atividade"] or ref.cnae.get(prest.get("cnae"), "")
    c2.caption(f"Relacao CNAE x FPAS da Dominio: CNAE {prest.get('cnae')} -> atividade '{atividade}' "
               f"-> FPAS {sug['fpas']} ({sug['ligacao']}).")
if fpas is None:
    for a_ in sug["alertas"]:
        st.warning(a_)
    st.stop()

terceiros = ref.terceiros_do_fpas(fpas)
if not terceiros:
    st.error(f"Nenhum código de terceiros para o FPAS {fpas} na tabela da Domínio.")
    st.stop()
ids_terc = [t["i_terceiros"] for t in terceiros]
por_id = {t["i_terceiros"]: t for t in terceiros}
padrao_terc = ref.terceiro_padrao(fpas, cfg_reg["terceiros"])
rat_sug = sug["rat"] if fpas == sug["fpas"] else ref.rat_do_cnae(prest.get("cnae"), data_padrao)
c1, c2, c3, c4, c5, c6 = st.columns([3, 0.8, 0.9, 0.9, 0.8, 0.8])
i_terc = c1.selectbox("Código de terceiros", ids_terc,
                      **d(f"terc_{kp}_{fpas}_{regime}", index=ids_terc.index(padrao_terc["i_terceiros"])),
                      format_func=lambda i: f"{por_id[i]['codigo']:04d} — {por_id[i]['descricao']} — "
                                            f"{por_id[i]['percentual']:.2f}%".replace(".", ","))
rats = [1, 2, 3]
rat = c2.selectbox("RAT (%)", rats,
                   **d(f"rat_{kp}", index=rats.index(int(rat_sug)) if rat_sug is not None and int(rat_sug) in rats
                       else None),
                   help="Alíquota do CNAE principal da prestadora (tabela da Domínio). Vai como RAT informado.")
inss = c3.number_input("INSS Empresa (%)", min_value=0.0, max_value=30.0, step=0.5,
                       **d(f"inss_{kp}_{regime}", value=float(cfg_reg["inss"])))
prolab = c4.number_input("Pró-lab./Aut. (%)", min_value=0.0, max_value=30.0, step=0.5,
                         **d(f"prolab_{kp}_{regime}", value=float(cfg_reg["prolab"])))
sefip = c5.number_input("SEFIP", min_value=0, step=1, help="Solução 136: tomador de serviço = 150.",
                        **d(f"sefip_{kp}", value=core.SEFIP_TOMADOR))
gps = c6.number_input("GPS", min_value=0, step=1, help="Conforme o regime da prestadora (Solução 3665).",
                      **d(f"gps_{kp}_{regime}", value=cfg_reg["gps"]))
terc = por_id[i_terc]
if terc.get("composicao"):
    st.caption(f"Terceiros {terc['codigo']:04d}: {terc['composicao']}")
alertas = list(sug["alertas"])
if fpas != sug["fpas"] and sug["fpas"]:
    alertas.append(f"FPAS {fpas} diferente do sugerido pelo CNAE ({sug['fpas']}).")
if cfg_reg["terceiros"] == "zero" and terc["codigo"] != 0:
    alertas.append("No Simples/MEI o código de terceiros costuma ser 0000 (Solução 3665).")
for a_ in alertas:
    st.warning(a_)
if rat is None:
    st.info("Escolha a alíquota RAT.")
    st.stop()

perfil = {"fpas": fpas, "terceiro": terc, "rat": rat, "inss": inss, "prolab": prolab, "sefip": int(sefip),
          "gps": int(gps), "i_fpas": sug["i_fpas"] if fpas == sug["fpas"] and sug["i_fpas"]
          else int(ref.fpas[fpas]["i_fpas"])}
encargos = core.encargos_do_perfil(perfil)
perfil_txt = (f"Regime: {cfg_reg['rotulo']} · FPAS {fpas} · Terceiros {terc['codigo']:04d} ({terc['descricao']}, "
              f"{str(terc['percentual']).replace('.', ',')}%) · RAT {rat}% informado · INSS Empresa {inss:g}% · "
              f"Pró-lab./Aut. {prolab:g}% · SEFIP {int(sefip)} · GPS {int(gps)}")
st.success("🔒 Herança aplicada a todos os tomadores — " + perfil_txt)
st.download_button("💾 Salvar perfil da prestadora (.json)",
                   json.dumps({"receita": prest, "empresa": int(empresa), "ultimo": int(ultimo),
                               "filial": int(filial), "descricao": descricao, "regime": regime, "fpas": fpas,
                               "i_terceiros": i_terc, "rat": rat, "inss": inss, "prolab": prolab,
                               "sefip": int(sefip), "gps": int(gps), "tipo_servico": ss.get("w_tserv", 1),
                               "lotacao_cnpj": ss.get("w_lotj", 4), "lotacao_cpf": ss.get("w_lotf", 3),
                               "cnae_cadastro": cnae_cad, "de_para": de_para_txt, "destino": int(destino_lei)},
                              ensure_ascii=False, indent=2).encode("utf-8"),
                   file_name=f"perfil_prestadora_{kp}.json", mime="application/json")
desenhar_passos(ph_passos, 3)

# =====================================================================
# Passo 3 · Tomadores (digitação e planilha alimentam a mesma lista)
# =====================================================================
st.subheader("Passo 3 · Tomadores")
with st.expander("Padrões do cadastro do tomador"):
    c1, c2, c3 = st.columns(3)
    tipo_serv = c1.selectbox("Tipo de serviço do tomador", list(core.TIPOS_SERVICO_TOMADOR), **d("w_tserv"),
                             format_func=core.TIPOS_SERVICO_TOMADOR.get)
    ajuda_lot = "Código gravado em TIPO_LOTACAO_ESOCIAL. Tabela 10 do eSocial: " + "; ".join(core.LOTACOES.values())
    lot_cnpj = c2.number_input("Lotação eSocial — tomador CNPJ", min_value=1, step=1, help=ajuda_lot,
                               **d("w_lotj", value=4))
    lot_cpf = c3.number_input("Lotação eSocial — tomador CPF", min_value=1, step=1, help=ajuda_lot,
                              **d("w_lotf", value=3))
    st.caption("⚠️ Confirme o código de lotação num tomador cadastrado pela tela: a Domínio pode gravar um código "
               "próprio.")


def adicionar(lista, consultar, substituir=False):
    if substituir:
        ss["tomadores"], ss["fila"], ss["tentativas"] = {}, [], {}
    do_lote = {}
    for t in lista:
        chave = t["inscricao"] or f"linha {t.get('linha')}"
        if chave in do_lote:
            t = {**t, "erro_insc": f"repetido no lote (linha {do_lote[chave]})" if do_lote[chave] else "repetido"}
            chave = f"{chave} #{t.get('linha') or len(ss['tomadores'])}"
        do_lote[chave] = t.get("linha")
        t.setdefault("exportar", True)
        ss["tomadores"][chave] = t
        if consultar and not t["erro_insc"]:
            if chave not in ss["fila"]:
                ss["fila"].append(chave)
        else:
            ss["tomadores"][chave]["consultado"] = True
    ss["processando"] = bool(ss["fila"])
    ss["fila_total"] = len(ss["fila"])


aba_dig, aba_plan = st.tabs(["⌨️ Digitar CNPJ", "📄 Planilha do cliente"])
with aba_dig:
    with st.form("f_tomador", clear_on_submit=True):
        dig = st.text_area("CNPJ do tomador (um por linha)", height=90, placeholder="00.000.000/0001-91")
        if st.form_submit_button("Consultar e adicionar à lista", type="primary"):
            novos = [core.tomador_vazio(l) for l in dig.splitlines() if core.txt(l)]
            if novos:
                adicionar(novos, True)
with aba_plan:
    c1, c2 = st.columns([1, 3])
    c1.download_button("⬇️ Planilha modelo", core.modelo_planilha(), file_name="modelo_tomadores.xlsx")
    f_plan = c2.file_uploader("Planilha preenchida (.xlsx ou .csv)", type=["xlsx", "xls", "csv"])
    c1, c2 = st.columns(2)
    usar_api = c1.checkbox("Completar campos vazios pela Receita e pelo CEP", value=True)
    modo = c2.radio("Na lista atual", ["Substituir", "Acrescentar"], horizontal=True)
    if f_plan is not None and st.button("Ler planilha", type="primary"):
        try:
            lote, info = core.ler_planilha(f_plan.getvalue(), f_plan.name)
        except Exception as e:
            st.error(f"Erro na leitura da planilha: {e}")
        else:
            ss["planilha"] = {"dados": f_plan.getvalue(), "nome": f_plan.name, "cab": info["cabecalho"]}
            adicionar(lote, usar_api, substituir=(modo == "Substituir"))
            st.toast(f"{len(lote)} linha(s) lida(s); {info['em_branco']} em branco ignorada(s).")
            if info["nao_lidas"]:
                st.info("Colunas ignoradas (nome não reconhecido): " + ", ".join(info["nao_lidas"]))

# Consulta em blocos: cada execução consulta por alguns segundos e salva o progresso; o restante continua sozinho.
if ss["fila"]:
    total = max(ss.get("fila_total", len(ss["fila"])), len(ss["fila"]))
    feitos = total - len(ss["fila"])
    rapido = core.PROVEDORES["BrasilAPI"].disponivel()
    eta = len(ss["fila"]) * (0.7 if rapido else core.PROVEDORES["CNPJá"].intervalo)
    with st.container(border=True):
        c1, c2 = st.columns([4, 1])
        barra = c1.progress(feitos / total if total else 0.0,
                            text=f"Consultando a Receita: {feitos} de {total} · faltam ~{max(1, round(eta / 60))} min"
                            + ("" if rapido else " (BrasilAPI em pausa: usando serviço com limite de 5/min)"))
        if ss["processando"]:
            c2.button("⏸️ Pausar", on_click=_pausar, width="stretch")
        else:
            c2.button("▶️ Retomar", on_click=_retomar, type="primary", width="stretch")
            st.caption(f"Consulta pausada: {len(ss['fila'])} tomador(es) aguardando. A lista já pode ser conferida.")
    if ss["processando"]:
        t0 = time.time()
        while ss["fila"] and time.time() - t0 < ORCAMENTO_SEG:
            chave = ss["fila"][0]
            t = core.completar(ss["tomadores"][chave], True)
            if not t["consultado"]:
                ss["tentativas"][chave] = ss["tentativas"].get(chave, 0) + 1
                if ss["tentativas"][chave] < 3:
                    ss["fila"].append(ss["fila"].pop(0))
                    ss["tomadores"][chave] = t
                    continue
                t["consultado"] = True
            ss["tomadores"][chave] = t
            ss["fila"].pop(0)
            feitos += 1
            barra.progress(feitos / total, text=f"Consultando a Receita: {feitos} de {total}")
        if ss["fila"]:
            st.rerun()
        ss["processando"] = False
        st.rerun()

if not ss["tomadores"]:
    st.info("Digite os CNPJs dos tomadores ou envie a planilha.")
    st.stop()
desenhar_passos(ph_passos, 4)

# =====================================================================
# Passo 4 · Conferência
# =====================================================================
st.subheader("Passo 4 · Conferência")
larg = {c["up"]: c["largura"] for c in ref.meta[core.T_VIG]}
ctx = {"ref": ref, "cadastrados": cadastrados, "cnpj_prestadora": kp, "data_padrao": data_padrao,
       "tipo_servico": tipo_serv, "lotacao_cnpj": int(lot_cnpj), "lotacao_cpf": int(lot_cpf),
       "de_para_logradouro": de_para, "cnae_cadastro": cnae_cad, "cnae_prestadora": prest.get("cnae"),
       "limites": {"nome": next((c["largura"] for c in ref.meta[core.T_SERV] if c["up"] == "NOME"), 40),
                   "endereco": larg.get("ENDERECO"), "complemento": larg.get("COMPLEMENTO"),
                   "bairro": larg.get("BAIRRO"), "cidade": larg.get("CIDADE"), "ddd": larg.get("DDD"),
                   "telefone": larg.get("TELEFONE")}}

EDITAVEIS = [k for k, _, _ in core.CAMPOS if k != "inscricao"]
resultados = {}
for chave, t in ss["tomadores"].items():
    v = core.validar(t, ctx)
    if chave in ss["fila"]:
        v["status"] = ST_FILA
    resultados[chave] = v

linhas_df = []
for chave, t in ss["tomadores"].items():
    v = resultados[chave]
    linhas_df.append({"chave": chave, "Exportar": bool(t.get("exportar", True)), "Status": v["status"],
                      "Motivo": v["obs"], "Linha": str(t.get("linha") or ""),
                      "CNPJ/CPF": core.formatar_inscricao(t["inscricao"]) or t.get("original", ""),
                      **{core.ROTULO[k]: core.txt(t.get(k)) for k in EDITAVEIS},
                      "Razão social (Receita)": t.get("razao", ""), "Situação": t.get("situacao", ""),
                      "Fonte": t.get("fonte", "")})
df = pd.DataFrame(linhas_df).set_index("chave")

contagem = {s: sum(1 for k, v in resultados.items() if v["status"] == s and ss["tomadores"][k].get("exportar", True))
            for s in (ST_OK, ST_REV, ST_ERR, ST_FILA)}
m = st.columns(5)
for col, s in zip(m, (ST_OK, ST_REV, ST_ERR, ST_FILA)):
    col.metric(s, contagem[s])
m[4].metric("Desmarcados", sum(1 for t in ss["tomadores"].values() if not t.get("exportar", True)))

filtro = st.radio("Mostrar", ["Todos", ST_OK, ST_REV, ST_ERR, ST_FILA], horizontal=True,
                  label_visibility="collapsed")
vis = df if filtro == "Todos" else df[df["Status"] == filtro]
st.caption("🔒 FPAS, terceiros, RAT, INSS, SEFIP e GPS não aparecem aqui porque vêm da prestadora (Passo 2). "
           "Corrija os dados do tomador direto na tabela; o status é recalculado na hora.")
ed = st.data_editor(vis, key=f"ed_{hashlib.md5(vis.to_json().encode()).hexdigest()[:10]}", hide_index=True,
                    disabled=["Status", "Motivo", "Linha", "CNPJ/CPF", "Razão social (Receita)", "Situação", "Fonte"],
                    column_config={"Exportar": st.column_config.CheckboxColumn(),
                                   "Motivo": st.column_config.TextColumn(width="large")},
                    width="stretch")
mudou = False
for chave, row in ed.iterrows():
    t = ss["tomadores"][chave]
    novos = {k: core.txt(row[core.ROTULO[k]]) for k in EDITAVEIS}
    if any(core.txt(t.get(k)) != novos[k] for k in EDITAVEIS) or bool(t.get("exportar", True)) != bool(row["Exportar"]):
        ss["tomadores"][chave] = {**t, **novos, "exportar": bool(row["Exportar"])}
        mudou = True
if mudou:
    st.rerun()

c1, c2, c3 = st.columns(3)
if c1.button("🔁 Consultar de novo os que falharam"):
    for chave, v in resultados.items():
        if "Receita:" in v["obs"] and chave not in ss["fila"]:
            ss["fila"].append(chave)
            ss["tentativas"].pop(chave, None)
    ss["processando"], ss["fila_total"] = bool(ss["fila"]), len(ss["fila"])
    st.rerun()
if c2.button("🗑️ Limpar a lista"):
    ss["tomadores"], ss["fila"], ss["planilha"], ss["tentativas"] = {}, [], None, {}
    st.rerun()
if ss["planilha"]:
    res_linha = {t["linha"]: (resultados[k]["status"].split(" ", 1)[-1], resultados[k]["obs"])
                 for k, t in ss["tomadores"].items() if t.get("linha")}
    c3.download_button("📋 Devolver a planilha com Status e Motivo",
                       core.planilha_resultado(ss["planilha"]["dados"], ss["planilha"]["nome"],
                                               ss["planilha"]["cab"], res_linha),
                       file_name=f"resultado_{os.path.splitext(ss['planilha']['nome'])[0]}.xlsx")

itens, cod = [], int(ultimo) + 1
for chave, t in ss["tomadores"].items():
    v = resultados[chave]
    if t.get("exportar", True) and v["status"] in (ST_OK, ST_REV):
        itens.append((cod, v["dados"]))
        v["servico"] = cod
        cod += 1
if not itens:
    st.warning("Nenhum tomador pronto para o arquivo.")
    st.stop()
desenhar_passos(ph_passos, 5)

# =====================================================================
# Passo 5 · Arquivos
# =====================================================================
st.subheader("Passo 5 · Arquivos para a importação de tabelas")
cfg = {"empresa": int(empresa), "descricao": descricao.strip() or "Cadastro inicial", "filial": int(filial),
       "cnae_prev": ref.cnae_prev}
linhas, atribuidos = core.montar_linhas(itens, encargos, cfg, ref.meta)
ctx_lay = {"codigos_municipio": {v[0] for v in ref.municipios.values()}, "cnae20": ref.cnae,
           "terceiros_ids": set(ids_terc), "manter": {"TIPO_ENDERECO"} if de_para else set()}
pacote, checks, _tirados, info_imp = core.gerar_pacote(linhas, atribuidos, ref.meta, leiaute, ref.fks, ctx_lay,
                                                       int(destino_lei), perfil_txt, int(empresa))
erros = [c for c in checks if c["Nível"] == "Erro" and c["Resultado"] == "❌"]
avisos = [c for c in checks if c["Nível"] == "Aviso" and c["Resultado"] == "⚠️"]

e1, e2, e3 = st.columns(3)
e1.metric("Tomadores no arquivo", len(itens))
e2.metric("Códigos de serviço", f"{itens[0][0]} a {itens[-1][0]}")
e3.metric("Fora do arquivo", len(ss["tomadores"]) - len(itens))

# As tabelas continuam sendo montadas: são usadas na planilha de conferência
nomes_real = {t: {c["up"]: c["nome"] for c in ref.meta[t]} for t in core.TABELAS}
prev_tabs = {t: pd.DataFrame([{nomes_real[t][k]: v for k, v in r.items()} for r in linhas[t]]) for t in core.TABELAS}

if erros:
    st.error("⛔ O arquivo não está conforme o leiaute — download bloqueado.  \n"
             + "  \n".join(f"• {c['Verificação']}: {c['Detalhe']}" for c in erros))
elif contagem[ST_FILA]:
    st.warning(f"⏳ {contagem[ST_FILA]} tomador(es) ainda aguardam consulta e ficaram fora do arquivo.")
elif avisos or contagem[ST_REV]:
    st.warning("⚠️ Arquivo gerado. Confira os tomadores marcados como 'Revisar' antes de importar "
               "(os avisos de conformidade estão na aba 'conformidade' da planilha de conferência).")
else:
    st.success("✅ Tudo certo: o arquivo está pronto para a importação de tabelas da Domínio.")

conf = pd.DataFrame([{"Serviço": resultados[k].get("servico", ""), "Linha": str(t.get("linha") or ""),
                      "CNPJ/CPF": core.formatar_inscricao(t["inscricao"]) or t.get("original", ""),
                      "Status": resultados[k]["status"], "Motivo": resultados[k]["obs"],
                      "Nome": resultados[k]["dados"]["nome"], "CNAE": resultados[k]["dados"]["cnae"],
                      "Município": resultados[k]["dados"]["codigo_municipio"]}
                     for k, t in ss["tomadores"].items()])
c1, c2 = st.columns(2)
c1.download_button(f"⬇️ Baixar arquivos da importação ({len(itens)} tomador(es))", pacote,
                   file_name=f"tomadores_emp{int(empresa)}_{dt.datetime.now():%Y%m%d_%H%M}.zip",
                   mime="application/zip", disabled=bool(erros), type="primary")
c2.download_button("📋 Planilha de conferência",
                   core.planilha_conferencia({"tomadores": conf, "foservicos": prev_tabs[core.T_SERV],
                                              "fovigencias_servico": prev_tabs[core.T_VIG],
                                              "conformidade": pd.DataFrame(checks),
                                              "heranca": pd.DataFrame([{"Herança": perfil_txt}])}),
                   file_name=f"conferencia_tomadores_emp{int(empresa)}.xlsx")
st.caption("O .zip traz os arquivos para importar e um LEIA-ME.txt com este mesmo passo a passo.")

st.divider()
st.subheader("📘 Como importar na Domínio")
st.caption("São 3 etapas. A etapa 1 só é feita na primeira vez; nas próximas importações, comece pela etapa 2.")
for etapa in core.passos_importacao(info_imp):
    with st.container(border=True):
        st.markdown(f"##### {etapa['icone']} {etapa['titulo']}")
        st.caption(etapa["quando"])
        st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(etapa["passos"], 1)))
        if etapa.get("dica"):
            st.info(etapa["dica"], icon="💡")
