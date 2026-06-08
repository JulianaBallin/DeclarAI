"""
Serviço de extração de texto e metadados de documentos fiscais.

Usa heurísticas baseadas em expressões regulares para identificar
informações relevantes como datas, valores monetários e emitentes.
"""

import logging
import re
from pathlib import Path
from typing import Optional

from app.services.document_kind_service import (
    texto_eh_recibo_aluguel,
    texto_eh_recibo_pensao_alimenticia,
    texto_recibo_comprovante_que_nao_e_nfs_e,
)
from app.utils.file_parsers import extrair_metadados_xml_fiscal, extrair_texto

logger = logging.getLogger(__name__)

_RE_SERV = r"servi[çc]o?s?"

# ---------------------------------------------------------------------------
# Padrões de expressões regulares para extração de metadados
# ---------------------------------------------------------------------------

PADROES_DATA = [
    r"\b(\d{2}/\d{2}/\d{4})\b",  # 31/12/2024
    r"\b(\d{2}-\d{2}-\d{4})\b",  # 31-12-2024
    r"\b(\d{4}-\d{2}-\d{2})\b",  # 2024-12-31
    r"\b(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})\b",  # 1 de janeiro de 2024
]

PADROES_VALOR = [
    r"(?i)total\s+contribu[íi]d[oa](?:\s+em\s+\d{2,4})?\s*:\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)total\s+de\s+contribui[çc][oõ]es[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)valor\s*pago[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)valor\s*l[ií]quido[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)valor\s+total\s*R?\$?\s*[\n\r\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)valor\s+dos\s+servi[çc]os\s*R?\$?\s*[\n\r\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)valor\s+recebido\s*R?\$?\s*[\n\r\s]*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)(?:total|subtotal)[:\s]+R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    r"(?i)(?:mensalidade|honorários)[:\s]+R?\$?\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
]

PADROES_EMITENTE = [
    r"([A-ZÀ-Ú][A-Za-zÀ-ú\s]{3,}(?:Ltda|LTDA|S\.A\.|SA|ME|EPP|EIRELI|LTDA\.))",
    r"(?i)(?:emitente|empresa|prestador|fornecedor|clínica|hospital|escola|"
    r"universidade|colégio|laboratório|farmácia|odontologia)[:\s]+([A-ZÀ-Ú][A-Za-zÀ-ú\s]+)",
    r"(?i)(?:CNPJ|CPF)[:\s]*[\d.\/\-]+\s*-?\s*([A-ZÀ-Ú][A-Za-zÀ-ú\s]+)",
]

# Chave de acesso NF-e: 44 dígitos, possivelmente com espaços/pontos entre grupos
PADRAO_CHAVE_ACESSO = re.compile(
    r"(?:chave[:\s]*(?:de\s+acesso)?[:\s]*)?((?:\d[\s.]?){44})", re.IGNORECASE
)

PADROES_CNPJ = [
    r"\b(\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})\b",  # CNPJ xx.xxx.xxx/xxxx-xx
]

PADROES_CPF_EMITENTE = [
    r"(?i)(?:CPF\s*do\s*emitente|CPF\s*emitente|emitente\s*CPF)[:\s]*([\d]{3}[.\s]?[\d]{3}[.\s]?[\d]{3}[-\s]?[\d]{2})",
]

PADROES_BENEFICIARIO = [
    r"(?i)recebi\s+do\(?a\)?\s+Sr\(?a\)?\s*\.\s*"
    r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,120}?)"
    r"(?=\s*(?:\n|CPF|R\$\b|VALOR|Valor)|$)",
    r"(?is)---\s*DESTINAT[ÁA]RIO\s*---\s*Nome:\s*([A-ZÀ-Ü0-9'.\-][^\n\r]{1,200})",
    r"(?i)participante\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){1,100}?)(?=\s*(?:\n|CPF\b)|$)",
    r"(?i)nome\s+do\s+aluno\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){1,100}?)(?=\s*(?:\n|CPF\b)|$)",
    r"(?i)aluno(?:\s*\([^)]{0,12}\))?\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){1,100}?)(?=\s*(?:\n|CPF\b)|$)",
    r"(?i)nome\s+do\s+benefici[aá]rio\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){1,100}?)(?=\s*(?:\n|CPF\b)|$)",
    r"(?i)nome\s+do\s+(?:paciente|aluno|cliente|tomador|destinat[aá]rio)\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){1,100}?)(?=\s*(?:\n|CPF\b)|$)",
    r"(?i)(?:pagador|paciente|respons[aá]vel(?:\s+financeiro)?)\s*:\s*"
    r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,100}?)(?=\s*(?:\n|CPF)|$)",
    r"(?i)(?:paciente|cliente|tomador|destinat[aá]rio|benefici[aá]rio)\s*:\s*"
    r"([A-ZÀ-Ú](?:[A-Za-zÀ-ú]|[\s'.-]){2,100}?)(?=\s*(?:\n|CPF\b)|$)",
]


def _formatar_cpf_onze_digitos(sem_formatacao: str) -> str:
    d = re.sub(r"\D", "", sem_formatacao)[:11]
    if len(d) != 11 or not d.isdigit():
        return sem_formatacao
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:11]}"


def _linha_limpa_nome_locacao(s: str) -> str:
    s = s.strip()
    s = re.sub(r"(?i)(cpf|cnpj|endere[çc]o|rua|cep|residen)\b.*$", "", s).strip()
    s = re.sub(r"^[\s,;:-]+", "", s)
    return re.sub(r"\s+", " ", s) if s else ""


def _normalizar_valor_exibicao_br(s: Optional[str]) -> Optional[str]:
    if not s:
        return s
    t = s.strip()
    m = re.match(r"^R\$\s*(\d+)$", t)
    if m:
        return f"R$ {m.group(1)},00"
    return t


class ServicoExtracao:
    """
    Extrai texto e metadados estruturados de documentos enviados pelo usuário.

    As heurísticas são otimizadas para documentos fiscais brasileiros comuns:
    recibos médicos, notas fiscais, informes de rendimento e comprovantes educacionais.
    """

    def processar_arquivo(self, caminho: str) -> dict:
        """
        Lê e processa um arquivo, retornando texto e metadados detectados.

        Args:
            caminho: Caminho para o arquivo (PDF, TXT ou HTML).

        Returns:
            Dicionário com texto extraído, tipo do arquivo e metadados.

        Raises:
            RuntimeError: Se ocorrer erro durante extração ou tipo não suportado.
        """
        path = Path(caminho)

        try:
            texto, tipo_arquivo = extrair_texto(caminho)
        except Exception as erro:
            logger.error(f"Falha ao extrair texto de '{path.name}': {erro}")
            raise RuntimeError(str(erro)) from erro

        if not texto.strip():
            logger.warning(f"Arquivo '{path.name}' extraído com texto vazio.")

        informe = self._eh_informe_rendimentos(texto)
        rec_aluguel = texto_eh_recibo_aluguel(texto)
        rec_pensao = texto_eh_recibo_pensao_alimenticia(texto)
        nfse = (
            self._texto_eh_nfse(texto)
            and not informe
            and not rec_aluguel
            and not rec_pensao
        )
        tomador_nfse = self._razao_tomador_nfse(texto) if nfse else None
        if rec_pensao:
            p_rec, p_alim, p_alit, _ = self._partes_recibo_pensao(texto)
            if p_alit:
                tomador_nfse = self._ajustar_caixa_nome_proprio(p_alit)[:120]
        codigo_mun = self._extrair_codigo_verificacao_nfse(texto) if nfse else None
        chave = self._extrair_chave_acesso(
            texto,
            tem_codigo_municipal=bool(codigo_mun and len(codigo_mun) >= 45),
        )
        if rec_aluguel or rec_pensao:
            chave = None
        id_fiscal = (codigo_mun or chave or "") or None
        if rec_pensao:
            id_fiscal = None
        res_informe = (self._resumo_informe_valores(texto) or None) if informe else None
        data_det = self._extrair_data(texto)
        valor_det = self._extrair_valor(texto, nfse=nfse, informe=informe)
        benef_det = self._extrair_nome_beneficiario(
            texto,
            nfse=nfse,
            informe=informe,
            recibo_aluguel=rec_aluguel,
            recibo_pensao=rec_pensao,
        )
        emit_intermediario = self._extrair_emitente(
            texto,
            nfse=nfse,
            informe=informe,
            recibo_aluguel=rec_aluguel,
            recibo_pensao=rec_pensao,
        )
        cnpj_inter = self._extrair_cnpj_emitente(
            texto, nfse=nfse, recibo_aluguel=rec_aluguel, recibo_pensao=rec_pensao
        )
        meta_xml = (
            extrair_metadados_xml_fiscal(caminho) if tipo_arquivo == "xml" else None
        )
        if meta_xml:
            if meta_xml.get("data_documento"):
                data_det = meta_xml["data_documento"]
            if meta_xml.get("nome_beneficiario"):
                benef_det = self._ajustar_caixa_nome_proprio(
                    meta_xml["nome_beneficiario"]
                )[:120]
            if meta_xml.get("valor_detectado"):
                valor_det = meta_xml["valor_detectado"]
            elif valor_det:
                valor_det = _normalizar_valor_exibicao_br(valor_det)
            cmeta = (meta_xml.get("chave_44") or "").strip()
            if (
                cmeta
                and len(cmeta) == 44
                and not (chave and len(re.sub(r"\D", "", chave or "")) == 44)
            ):
                chave = cmeta
                id_fiscal = (codigo_mun or chave or "") or None
        elif valor_det:
            valor_det = _normalizar_valor_exibicao_br(valor_det)

        return {
            "nome_arquivo": path.name,
            "tipo_arquivo": tipo_arquivo,
            "texto_extraido": texto,
            "data_detectada": data_det,
            "valor_detectado": valor_det,
            "emitente_detectado": emit_intermediario,
            "chave_acesso": chave,
            "codigo_verificacao": codigo_mun,
            "identificador_fiscal": id_fiscal,
            "cnpj_emitente": cnpj_inter,
            "nome_beneficiario": benef_det,
            "nome_tomador_nfs_e": tomador_nfse,
            "resumo_informe_valores": res_informe,
            "caminho_arquivo": caminho,
        }

    # -----------------------------------------------------------------------
    # Métodos privados de extração por heurísticas
    # -----------------------------------------------------------------------

    def _extrair_data(self, texto: str) -> Optional[str]:
        m_emi = re.search(
            r"(?i)Data de Emissão:\s*(\d{4})-(\d{2})-(\d{2})",
            texto,
        )
        if m_emi:
            return f"{m_emi.group(3)}/{m_emi.group(2)}/{m_emi.group(1)}"
        m_iso = re.search(
            r"(?:^|[^0-9-])(\d{4})-(\d{2})-(\d{2})(?=[T\szZ+\-\s,;]|$)",
            texto,
        )
        if m_iso:
            return f"{m_iso.group(3)}/{m_iso.group(2)}/{m_iso.group(1)}"
        prioridade = [
            r"(?i)data\s+de\s+pagamento[:\s]+(\d{2}/\d{2}/\d{4})",
            r"(?i)data\s*pagamento[:\s]+(\d{2}/\d{2}/\d{4})",
            r"(?i)vencimento[:\s]+(\d{2}/\d{2}/\d{4})",
        ]
        for padrao in prioridade:
            m = re.search(padrao, texto)
            if m:
                return m.group(1)
        m = re.search(
            r",\s*(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})\b",
            texto,
            re.IGNORECASE,
        )
        if m:
            return m.group(1)
        for padrao in PADROES_DATA:
            correspondencia = re.search(padrao, texto, re.IGNORECASE)
            if correspondencia:
                return correspondencia.group(1)
        return None

    @staticmethod
    def _eh_informe_rendimentos(texto: str) -> bool:
        t = texto[:15000].lower()
        if not re.search(
            r"informe\s+de\s+rendimentos|dirf\b|informe\s+anual|comprovante\s+de\s+rendimentos",
            t,
        ):
            return False
        return bool(
            re.search(
                r"rendimentos\s+tribut|fonte\s+pagadora|irrf|inss|retid|"
                r"empregad|v[ií]nculo|clt|sal[áa]rios|ordenad",
                t,
            )
        )

    def _texto_eh_nfse(self, texto: str) -> bool:
        if texto_recibo_comprovante_que_nao_e_nfs_e(texto):
            return False
        t = texto.lower()
        return bool(
            re.search(
                r"nota\s+fiscal\s+de\s+servi[çc]os\s+eletr",
                t,
            )
            or re.search(r"\bnfs[\s.-]*e\b", t)
        )

    @staticmethod
    def _resumo_informe_valores(texto: str) -> str:
        def one(rx: str) -> Optional[str]:
            m = re.search(rx, texto, re.IGNORECASE | re.DOTALL)
            if not m or not m.group(1):
                return None
            g = m.group(1).strip()
            if re.match(r"^[\d.]+,\d{2}$", g):
                return g
            return None

        # INSS, IRRF, plano de saúde, FGTS, vale - alternativas por rótulo (leiautes variam).
        blocos: list[tuple[str, tuple[str, ...]]] = [
            (
                "INSS",
                (
                    r"(?i)inss\s*(?:\([^)]{0,100}\))?\s*[:=.]?\s*R\$\s*([\d.]+,\d{2})",
                    r"(?i)inss.{0,200}?R\$\s*([\d.]+,\d{2})",
                ),
            ),
            (
                "IRRF",
                (
                    r"(?i)irrf\s*(?:\([^)]{0,80}\))?\s*[:=.]?\s*R\$\s*([\d.]+,\d{2})",
                    r"(?i)ir\s*retid[^\d.]{0,50}R\$\s*([\d.]+,\d{2})",
                    r"(?i)imposto\s+retid[^\d.]{0,50}R\$\s*([\d.]+,\d{2})",
                ),
            ),
            (
                "Plano de saúde (coletivo)",
                (
                    r"(?i)plano\s+de\s+sa[úu]de.{0,200}?R\$\s*([\d.]+,\d{2})",
                    r"(?i)plano\s+de\s+sa[úu]de.{0,100}?coletiv.{0,120}?"
                    r"R\$\s*([\d.]+,\d{2})",
                    r"(?i)sa[úu]de\s+coletiv.{0,120}?R\$\s*([\d.]+,\d{2})",
                ),
            ),
            (
                "FGTS",
                (
                    r"(?i)fgts\s*(?:\([^)]{0,100}\))?\s*[:=.]?\s*R\$\s*([\d.]+,\d{2})",
                    r"(?i)fgts.{0,200}?R\$\s*([\d.]+,\d{2})",
                ),
            ),
            (
                "Vale-refeição (isento)",
                (r"(?i)vale[-\s]?refei\w*.{0,200}?R\$\s*([\d.]+,\d{2})",),
            ),
        ]

        partes: list[str] = []
        for rot, padroes in blocos:
            for padr in padroes:
                v = one(padr)
                if v:
                    partes.append(f"**{rot}** R$ {v}")
                    break
        if not partes:
            return ""
        return "  \n".join(partes)

    @staticmethod
    def _extrair_valor_tributaveis_informe(texto: str) -> Optional[str]:
        for p in (
            r"(?i)total(?:\s+de)?\s+rendimentos\s+tribut[áa]veis\s*:\s*R\$\s*([\d.]+,\d{2})",
            r"(?i)total(?:\s+de)?\s+de\s+rendimentos\s+tribut[áa]veis\s*:\s*R\$\s*([\d.]+,\d{2})",
            r"(?i)total\s+de\s+rendimentos\s+tribut[áa]veis\s*R\$\s*([\d.]+,\d{2})",
        ):
            m = re.search(p, texto)
            if m:
                return f"R$ {m.group(1).strip()}"
        return None

    def _extrair_benef_informe(self, texto: str) -> Optional[str]:
        m = re.search(
            r"(?is)benefici[áa]rio.{0,2000}?"
            r"\b(?:nome|raz[aã]o)\s*:\s*"
            r"([A-ZÀ-ÜA-Z\'.-]+(?:\s+[A-ZÀ-ÜA-Z\'.-]+){2,12})"
            r"(?=\s*[\n\r](?:.|\n){0,80}(?:cpf|cargo|v[ií]nculo|cn))",
            texto,
        )
        if m:
            n = re.sub(r"\s+", " ", m.group(1).strip())
            if 8 <= len(n) < 100 and "LTDA" not in n.upper():
                return self._ajustar_caixa_nome_proprio(n)
        m2 = re.search(
            r"(?is)benefici[áa]rio.{0,2500}?"
            r"\b[Nn]ome\s*:\s*"
            r"([A-ZÀ-ÜA-Z\'.-]+(?:\s+[A-ZÀ-ÜA-Z\'.-]+){2,12})",
            texto,
        )
        if m2:
            n2 = m2.group(1).strip()
            if 8 <= len(n2) < 100 and "LTDA" not in n2.upper():
                return self._ajustar_caixa_nome_proprio(n2)
        return None

    def _emitente_fonte_pag_informe(self, texto: str) -> Optional[str]:
        m = re.search(
            r"(?is)fonte\s+pagadora.{0,1200}?" r"raz[ãa]o\s+social\s*:\s*([^\n\r]+)",
            texto,
        )
        if m:
            return self._sanear_razao_social(
                re.sub(r"\s+", " ", m.group(1).strip())[:120]
            )
        return None

    def _valor_principal_nfse(self, texto: str) -> Optional[str]:
        pats = [
            r"(?i)valor\s+total\s+(?:da\s+)?nota\s*[:=]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            r"(?i)vlr\.?\s*total\s+(?:da\s+)?nota\s*[:=]?\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            r"(?i)valor\s+total\s+da\s+nfs-?e\s*=\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            r"(?i)valor\s+total\s+da\s+nfs-?e\s*:\s*R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            r"(?i)valor\s+l[ií]quido[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            r"(?i)valor\s+do\s+servi[çc]o[:\s]+R\$\s*(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
        ]
        for p in pats:
            m = re.search(p, texto, re.IGNORECASE | re.MULTILINE)
            if m:
                v = m.group(1).strip()
                if v in ("0,00", "0.00", "0"):
                    continue
                return f"R$ {v}"
        return None

    def _bloco_prestador_nfse(self, texto: str) -> str:
        m = re.search(
            r"(?is)prestador(?:\s+de\s+" + _RE_SERV + r")?"
            r".{0,3500}?"
            r"(?=tomador(?:\s+de\s+" + _RE_SERV + r")?|destinat)",
            texto,
        )
        return m.group(0) if m else ""

    def _bloco_tomador_nfse(self, texto: str) -> str:
        m = re.search(
            r"(?is)(?:tomador|destinat[aá]rio)(?:\s+de\s+" + _RE_SERV + r")?"
            r".{0,4000}?"
            r"(?=(?:prestador|discrimina[çc]|atividade|valor\s+total\s+da))",
            texto,
        )
        if m:
            return m.group(0)
        m2 = re.search(
            r"(?is)(?:tomador|destinat[aá]rio)(?:\s+de\s+"
            + _RE_SERV
            + r")?[\s\S]{0,4000}",
            texto,
        )
        return m2.group(0) if m2 else ""

    @staticmethod
    def _sanear_razao_social(nome: str) -> str:
        original = nome
        n = nome.strip()
        n = re.sub(r"(?i)^\s*nome\s+do\s*emitente\s+", "", n)
        n = re.sub(r"(?i)^\s*raz[ãa]o\s+social\s*:\s*", "", n)
        n = re.sub(
            r"(?i)^nota\s+fiscal(\s+de\s+servi[çc]o?s?)?(\s+eletr[ôo]nica)?\s*",
            "",
            n,
        )
        n = re.sub(r"(?i)^recebi(?:emos)?\s+de\s+", "", n)
        n = re.sub(r"\s+", " ", n).strip(" -")
        if len(n) < 3:
            return original
        return n

    def _razao_social_prestador_nfse(self, texto: str) -> Optional[str]:
        bloco = self._bloco_prestador_nfse(texto) or texto
        for p in (
            r"(?is)nome\s*/\s*raz[aã]o\s*social(?:\s+do\s+prestador)?\s*:\s*([^\n\r]+)",
            r"(?is)raz[aã]o\s+social(?:\s+do\s+prestador)?\s*:\s*([^\n\r]+)",
        ):
            m = re.search(p, bloco)
            if m:
                nome = re.sub(r"\s+", " ", m.group(1).strip())
                nome = re.sub(
                    r"(?i)^recebi(?:emos)?\s+de\s*",
                    "",
                    nome,
                ).strip()
                nome = self._sanear_razao_social(nome)
                if len(nome) >= 4 and not nome[0].isdigit():
                    return nome[:120]
        return None

    def _razao_tomador_nfse(self, texto: str) -> Optional[str]:
        bl = self._bloco_tomador_nfse(texto)
        trechos = list(dict.fromkeys([x for x in (bl, texto) if x]))
        for trecho in trechos:
            for rx in (
                r"(?is)tomador(?:\s+de\s+" + _RE_SERV + r")?"
                r".{0,3200}?"
                r"(?:nome\s*[/\s~]*\s*)?raz[aã]o\s*social"
                r"(?:\s+do\s+tomador)?\s*:\s*([^\n\r]+)",
                r"(?is)destinat[aá]rio(?:\s+de\s+" + _RE_SERV + r")?"
                r".{0,3200}?"
                r"(?:nome\s*[/\s~]*\s*)?raz[aã]o\s*social\s*:\s*([^\n\r]+)",
                r"(?is)tomador(?:\s+de\s+" + _RE_SERV + r")?[\s\S]{0,2000}?"
                r"nome(?:\s*[/\s~]+\s*)?raz[aã]o(?:\s+social)?\s*:\s*([^\n\r]+)",
                r"(?is)tomador(?:\s+de\s+" + _RE_SERV + r")?[\s\S]{0,2500}?"
                r"\bnome\s*:\s*([A-ZÀ-Úa-z][^\n\r]{2,200}?)"
                r"(?=\s*[\n\r](?:\s*|\n)*(?:cpf|cnpj|inscri[çc][aã]o|endere[cç]o|telefone|e-?mail|municip))",
                r"(?is)tomador(?:\s+de\s+" + _RE_SERV + r")?[\s\S]{0,2500}?"
                r"\bnome\s*:\s*([A-ZÀ-Úa-z][^\n\r]{2,200}?)(?=\s*[\n\r](?:.|\n){0,400}cpf)",
            ):
                m = re.search(rx, trecho)
                if m:
                    nome = re.sub(r"\s+", " ", m.group(1).strip().rstrip(":;|"))
                    nome = self._sanear_razao_social(nome)
                    if len(nome) >= 4 and not re.match(
                        r"^[\d./\s-]+(?!.*[A-Za-zÀ-ú])$", nome
                    ):
                        return nome[:120]
        return None

    def _cnpj_prestador_nfse(self, texto: str) -> Optional[str]:
        bloco = self._bloco_prestador_nfse(texto)
        if not bloco:
            return None
        c = re.search(
            r"\b(\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2})\b",
            bloco,
        )
        if c:
            return re.sub(r"[\s]", "", c.group(1))
        return None

    def _limpar_nome_fiscal(self, nome: str) -> str:
        n = re.sub(
            r"(?i)^recebi(?:emos)?\s+de\s*",
            "",
            nome.strip(),
        )
        if not n[0:1].isdigit():
            return n
        return nome.strip()

    def _extrair_valor(
        self, texto: str, nfse: bool = False, informe: bool = False
    ) -> Optional[str]:
        if informe:
            v = self._extrair_valor_tributaveis_informe(texto)
            if v:
                return v
        if nfse:
            v = self._valor_principal_nfse(texto)
            if v:
                return v
        for padrao in PADROES_VALOR:
            for correspondencia in re.finditer(
                padrao, texto, re.IGNORECASE | re.MULTILINE
            ):
                valor_bruto = correspondencia.group(1).strip()
                if valor_bruto in ("0,00", "0.00", "0"):
                    continue
                inicio = max(0, correspondencia.start() - 80)
                contexto = texto[inicio : correspondencia.end() + 40].lower()
                if nfse and any(
                    x in contexto
                    for x in (
                        "tributos aproxim",
                        "lei 12.741",
                        "aproximadamente",
                    )
                ):
                    continue
                return f"R$ {valor_bruto}"
        return None

    def _partes_recibo_aluguel(
        self, texto: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        loc_n, locat_n, cpf_l = None, None, None
        t = texto

        m = re.search(
            r"(?m)^\s*Locad(?:ora|or)\s*:\s*([^\n\r]+?)\s*(?:$|\n)", t, re.IGNORECASE
        )
        if m:
            loc_n = _linha_limpa_nome_locacao(m.group(1))[:200]

        if (not loc_n) or len(loc_n) < 3:
            m2 = re.search(
                r"(?m)^\s*Locad(?:ora|or)\s*$\s*\n\s*"
                r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Üa-z'.\-]|\s){2,200})",
                t,
            )
            if m2:
                loc_n = _linha_limpa_nome_locacao(m2.group(1))[:200]

        m_eu = re.search(
            r"(?is)\bEu,\s*([A-ZÀ-Ü][^,\n\r]{1,200}?)\s*,\s*CPF",
            t,
        )
        if m_eu and (not loc_n or len(loc_n) < 3):
            loc_n = re.sub(r"\s+", " ", m_eu.group(1).strip())[:200]

        m_l = re.search(
            r"(?m)^\s*Locat[áaA]rio\s*:\s*([^\n\r]+?)\s*(?:$|\n)", t, re.IGNORECASE
        )
        if not m_l:
            m_l = re.search(r"(?is)Locat[áaA]rio\s*:\s*([^\n\r]+?)(?=\n\s*CPF|\n|$)", t)
        if m_l:
            locat_n = _linha_limpa_nome_locacao(m_l.group(1))[:200]

        if (not locat_n) or len(locat_n) < 3:
            m_l2 = re.search(
                r"(?m)^\s*Locat[áaA]rio\s*$\s*\n\s*"
                r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Üa-z'.\-]|\s){2,200})",
                t,
            )
            if m_l2:
                locat_n = _linha_limpa_nome_locacao(m_l2.group(1))[:200]

        corte = re.search(r"(?i)locat[áa]rio", t)
        trecho_antes = t[: corte.start()] if corte else t
        cps_antes = re.findall(
            r"\b(\d{3}[\s.]?\d{3}[\s.]?\d{3}[-\s/]?\d{2})\b", trecho_antes
        )
        for raw in cps_antes:
            d = re.sub(r"\D", "", raw)
            if len(d) == 11:
                cpf_l = d
                break
        if not cpf_l:
            cps = re.findall(r"\b(\d{3}[\s.]?\d{3}[\s.]?\d{3}[-\s/]?\d{2})\b", t)
            for raw in cps:
                d = re.sub(r"\D", "", raw)
                if len(d) == 11:
                    cpf_l = d
                    break
        if cpf_l and len(cpf_l) != 11:
            cpf_l = None
        return (loc_n, locat_n, cpf_l)

    def _partes_recibo_pensao(
        self, texto: str
    ) -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
        rec = alim = alit = cpf_r = None
        t = texto
        m0 = re.search(
            r"(?s)(?i:eu)\s*,\s*(?-i:)([A-ZÀ-Ü'.\-](?:[A-Za-zÀ-ú'.\-]|\s){2,100}?)\s*,"
            r"\s*(?i:cpf)",
            t,
        )
        if m0:
            rec = _linha_limpa_nome_locacao(m0.group(1))[:200]
        m = (
            None
            if rec
            else re.search(
                r"(?is)(?:recebedor[ao]?\s*[/,]\s*representante(?:\s+legal)?|"
                r"representante\s+legal|recebedor[ao]?\b)(?:\s*[:,.])?\s*"
                r"(?-i:)([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,100}?)"
                r"(?=\s*(?:,|\n|CPF)|$)",
                t,
            )
        )
        if m and not rec:
            cand = _linha_limpa_nome_locacao(m.group(1))[:200]
            if not re.search(
                r"(?i)\b(da|de|do|dos|das|na)\s+alimentand",
                cand,
            ):
                rec = cand
        m2 = re.search(
            r"(?is)alimentando\s*[:,.]?\s*"
            r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,100}?)"
            r"(?=\s*(?:\(|,|\n|menor|nasc|CPF|filh)|$)",
            t,
        )
        if not m2:
            m2 = re.search(
                r"(?is)[^\n]{0,100}\(\s*alimentando\s*\)\s*[:,.]?\s*"
                r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,100}?)"
                r"(?=\s*(?:\(|,|\n|menor|nasc|CPF|filh)|$)",
                t,
            )
        if m2:
            alim = re.sub(r"\s*\([^)]{0,80}\).*$", "", m2.group(1).strip()).strip()
            alim = _linha_limpa_nome_locacao(alim)[:200]
        m3 = re.search(
            r"(?is)alimentante\s*[:,.]?\s*"
            r"([A-ZÀ-Ü'.\-](?:[A-ZÀ-Úa-z'.\-]|\s){2,100}?)"
            r"(?=\s*(?:,|\n|CPF|valor|R\$\b)|$)",
            t,
        )
        if m3:
            alit = _linha_limpa_nome_locacao(m3.group(1))[:200]
        corte = re.search(r"(?i)alimentando", t)
        trecho_antes = t[: corte.start()] if corte else t[:3000]
        for raw in re.findall(
            r"\b(\d{3}[\s.]?\d{3}[\s.]?\d{3}[-\s/]?\d{2})\b", trecho_antes
        ):
            d = re.sub(r"\D", "", raw)
            if len(d) == 11:
                cpf_r = d
                break
        if cpf_r and len(cpf_r) != 11:
            cpf_r = None
        return (rec, alim, alit, cpf_r)

    def _emitente_linha_antes_cnpj(self, texto: str) -> Optional[str]:
        m = re.search(
            r"CNPJ[:\s]*\d{2}[.\s]?\d{3}[.\s]?\d{3}[/\s]?\d{4}[-\s]?\d{2}",
            texto,
            re.IGNORECASE,
        )
        if not m:
            return None
        antes = texto[: m.start()]
        linhas = [ln.strip() for ln in antes.splitlines() if ln.strip()]
        for linha in reversed(linhas):
            if re.match(r"^={3,}$", linha) or re.match(r"^#{3,}$", linha):
                continue
            if re.match(r"(?i)^comprovante\b", linha):
                continue
            if re.match(r"(?i)^nome\s+do\s+emitente\s*$", linha):
                continue
            if len(linha) < 5 or re.match(r"^N[º°]?\s*\d", linha, re.IGNORECASE):
                continue
            if re.search(
                r"(?i)nota\s+fiscal(?!.+(?:ltda|ltda\.|s\.a|me\b|eireli))",
                linha,
            ) and not re.search(r"(?i)(ltda|eireli|ltda\.|s\.\s*a\.)", linha):
                continue
            return linha[:120]
        return None

    def _extrair_emitente(
        self,
        texto: str,
        nfse: bool = False,
        informe: bool = False,
        recibo_aluguel: bool = False,
        recibo_pensao: bool = False,
    ) -> Optional[str]:
        if recibo_aluguel:
            loc, _, _ = self._partes_recibo_aluguel(texto)
            if loc:
                return self._ajustar_caixa_nome_proprio(self._sanear_razao_social(loc))[
                    :120
                ]
            return None
        if recibo_pensao:
            r, _, _, _ = self._partes_recibo_pensao(texto)
            if r:
                return self._ajustar_caixa_nome_proprio(self._sanear_razao_social(r))[
                    :120
                ]
            return None
        if informe:
            e = self._emitente_fonte_pag_informe(texto)
            if e:
                return e
        if nfse:
            r = self._razao_social_prestador_nfse(texto)
            if r:
                return r
        inst = self._emitente_linha_antes_cnpj(texto)
        if inst:
            lim = self._limpar_nome_fiscal(inst)
            lim = self._sanear_razao_social(lim)
            if len(lim) >= 4:
                return lim[:120]
        for padrao in PADROES_EMITENTE:
            correspondencia = re.search(padrao, texto)
            if correspondencia:
                nome = self._limpar_nome_fiscal(correspondencia.group(1).strip())
                nome = self._sanear_razao_social(nome)
                if re.match(r"(?i)^comprovante\b", nome):
                    continue
                if re.match(r"(?i)^recibo\s+de\b", nome):
                    continue
                if len(nome) >= 4 and not nome.isspace():
                    return nome[:120]
        return None

    def _extrair_codigo_verificacao_nfse(self, texto: str) -> Optional[str]:
        m = re.search(
            r"(?is)c[oó]digo\s+de\s+verifica[çc][aã]o",
            texto,
        )
        if not m:
            return None
        trecho = texto[m.end() : m.end() + 500]
        digitos = re.sub(r"\D", "", trecho)
        if 45 <= len(digitos) <= 64:
            return digitos
        return None

    def _extrair_chave_acesso(
        self,
        texto: str,
        tem_codigo_municipal: bool = False,
    ) -> Optional[str]:
        if texto_eh_recibo_aluguel(texto) or texto_eh_recibo_pensao_alimenticia(texto):
            return None
        if tem_codigo_municipal:
            return None
        tl = texto.lower()
        boleto = "linha digit" in tl or "boleto banc" in tl
        nfe = (
            "chave de acesso" in tl
            or "danfe" in tl
            or bool(re.search(r"\bnf[\s-]?e\b", tl, re.IGNORECASE))
            or "nota fiscal eletrônica" in tl
            or "nota fiscal eletronica" in tl
        )
        if boleto and not nfe:
            return None
        correspondencia = PADRAO_CHAVE_ACESSO.search(texto)
        if correspondencia:
            chave = re.sub(r"\D", "", correspondencia.group(1))
            if len(chave) == 44:
                return chave
        apenas_digitos = re.sub(r"[\s.]", "", texto)
        correspondencia = re.search(r"\d{44}", apenas_digitos)
        if correspondencia:
            return correspondencia.group(0)
        return None

    def _extrair_cnpj_emitente(
        self,
        texto: str,
        nfse: bool = False,
        recibo_aluguel: bool = False,
        recibo_pensao: bool = False,
    ) -> Optional[str]:
        if recibo_aluguel:
            _, _, cpf = self._partes_recibo_aluguel(texto)
            if cpf and len(cpf) == 11:
                return _formatar_cpf_onze_digitos(cpf)
            return None
        if recibo_pensao:
            _, _, _, cpf = self._partes_recibo_pensao(texto)
            if cpf and len(cpf) == 11:
                return _formatar_cpf_onze_digitos(cpf)
            return None
        if nfse:
            c = self._cnpj_prestador_nfse(texto)
            if c:
                return c
        for padrao in PADROES_CNPJ:
            correspondencia = re.search(padrao, texto)
            if correspondencia:
                return re.sub(r"[\s]", "", correspondencia.group(1))
        for padrao in PADROES_CPF_EMITENTE:
            correspondencia = re.search(padrao, texto, re.IGNORECASE)
            if correspondencia:
                return re.sub(r"[\s]", "", correspondencia.group(1))
        return None

    @staticmethod
    def _ajustar_caixa_nome_proprio(nome: str) -> str:
        s = re.sub(r"\s+", " ", nome.strip())
        if not s:
            return s
        particulas = {
            "de",
            "da",
            "do",
            "das",
            "dos",
            "e",
            "del",
            "della",
            "dalla",
        }
        partes: list[str] = []
        for w in s.split():
            pl = w.lower()
            if pl in particulas and partes:
                partes.append(pl)
            else:
                partes.append(
                    w[:1].upper() + w[1:].lower() if len(w) > 1 else w.upper()
                )
        return " ".join(partes)[:120]

    def _nome_benef_nfe_ou_nfce(self, texto: str) -> Optional[str]:
        if not re.search(
            r"(?i)nfc-?e|nota fiscal de consum|danfe\s*nfc|consumidor",
            texto,
        ):
            return None
        tl = texto.lower()
        idx = tl.rfind("consumidor")
        trecho = texto[idx + 10 :] if idx != -1 else texto
        m = re.search(
            r"(?is)(?:cpf/cnpj/id|estrangeiro)[^\n]{0,120}?\n?\s*"
            r"(\d{11,14})\s+([A-ZÀ-Ü](?:[A-ZÀ-Úa-z\'.-]|\s){2,120}?)"
            r"(?=\s*(?:$|\n|protocolo|qr|chave|consulta|autentica|danfe|emitente|emit))",
            trecho,
        ) or re.search(
            r"(?is)\b(\d{11})\s+([A-ZÀ-Ü](?:[A-ZÀ-Úa-z\'.-]|\s){2,100}?)"
            r"(?=\s*(?:$|\n|protocolo|qr|chave|consulta))",
            trecho,
        )
        if m:
            nome = re.sub(r"\s+", " ", m.group(2).strip().rstrip("|"))
            if len(nome) >= 4:
                return self._ajustar_caixa_nome_proprio(nome)
        m2 = re.search(
            r"(?m)^\s*(\d{11})\s+([A-ZÀ-Ü][A-ZÀ-Úa-z\'.-]+(?:\s+[A-ZÀ-Úa-z\'.-]+){1,12})\s*$",
            trecho,
        )
        if m2:
            nome = re.sub(r"\s+", " ", m2.group(2).strip())
            if len(nome) >= 4:
                return self._ajustar_caixa_nome_proprio(nome)
        return None

    def _texto_eh_mensalidade_escolar_nao_pensao(self, texto: str) -> bool:
        if texto_eh_recibo_pensao_alimenticia(texto) or texto_eh_recibo_aluguel(texto):
            return False
        t = (texto or "")[:20000].lower()
        if not re.search(
            r"comprovante|mensalidade|escola|col[eé]gio|ensino",
            t,
        ):
            return False
        if not re.search(
            r"aluno|respons[aá]vel\s+financeiro|matr[íi]cula|ano\s+letivo|turma",
            t,
        ):
            return False
        return True

    def _nome_aluno_ou_titular_educacao_nfse(self, texto: str) -> Optional[str]:
        for rx in (
            r"(?is)aluno\s*[:.]\s*([A-ZÀ-Ü](?:[A-ZÀ-Úa-z\'.-]|\s){2,100}?)(?=[\n\r<]|$|\s*cpf)",
            r"(?is)nome\s+do\s+aluno\s*[:.]\s*([^\n\r<]{4,120})",
        ):
            m = re.search(rx, texto)
            if m:
                nome = re.sub(r"<[^>]+>", " ", m.group(1))
                nome = re.sub(r"\s+", " ", nome.strip().rstrip(":;|"))
                nome = re.sub(
                    r"(?i)\s*(cpf|cnpj|endere[çc]o|telefone|e-?mail).*$", "", nome
                ).strip()
                if len(nome) >= 4 and not re.match(
                    r"^[\d./\s-]+(?!.*[A-Za-zÀ-ü])$", nome
                ):
                    return self._ajustar_caixa_nome_proprio(nome)[:120]
        return None

    def _nome_paciente_saude(self, texto: str) -> Optional[str]:
        if not re.search(
            r"(?i)\b(paciente|consulta|m[eé]dic|odont|dentista|cl[ií]nica|hospital)",
            texto[:20000],
        ):
            return None
        for rx in (
            r"(?is)paciente\s*[:.]\s*([A-ZÀ-Ü](?:[A-ZÀ-Úa-z\'.-]|\s){2,120}?)(?=\s*(?:\(|\n|CPF\b|$))",
            r"(?is)nome\s+do\s+paciente\s*[:.]\s*([^\n\r(]{4,120})",
        ):
            m = re.search(rx, texto)
            if m:
                nome = re.sub(r"\s+", " ", m.group(1).strip().rstrip(":;|"))
                nome = re.sub(
                    r"(?i)\s*(cpf|data\s+de\s+nascimento|procedimento).*$",
                    "",
                    nome,
                ).strip()
                if len(nome) >= 4 and not re.match(
                    r"^[\d./\s-]+(?!.*[A-Za-zÀ-ü])$", nome
                ):
                    return self._ajustar_caixa_nome_proprio(nome)[:120]
        return None

    def _extrair_nome_beneficiario(
        self,
        texto: str,
        nfse: bool = False,
        informe: bool = False,
        recibo_aluguel: bool = False,
        recibo_pensao: bool = False,
    ) -> Optional[str]:
        if recibo_aluguel:
            _, locat, _ = self._partes_recibo_aluguel(texto)
            if locat:
                return self._ajustar_caixa_nome_proprio(locat)[:120]
            return None
        if recibo_pensao:
            _, alim, _, _ = self._partes_recibo_pensao(texto)
            if alim:
                return self._ajustar_caixa_nome_proprio(alim)[:120]
            return None
        if self._texto_eh_mensalidade_escolar_nao_pensao(texto):
            aluno = self._nome_aluno_ou_titular_educacao_nfse(texto)
            if aluno:
                return aluno
        if informe:
            bi = self._extrair_benef_informe(texto)
            if bi:
                return bi
        if nfse:
            aluno = self._nome_aluno_ou_titular_educacao_nfse(texto)
            if aluno:
                return aluno
            t = self._razao_tomador_nfse(texto)
            if t:
                return t
        paciente = self._nome_paciente_saude(texto)
        if paciente:
            return paciente
        nb = self._nome_benef_nfe_ou_nfce(texto)
        if nb:
            return nb
        for padrao in PADROES_BENEFICIARIO:
            correspondencia = re.search(padrao, texto)
            if correspondencia:
                nome = correspondencia.group(1).strip().rstrip(".,;:")
                if len(nome) >= 4:
                    return self._ajustar_caixa_nome_proprio(nome)[:120]
        return None
