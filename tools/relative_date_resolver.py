# tools/relative_date_resolver.py

from crewai.tools import BaseTool
from datetime import datetime, timedelta
import re

class RelativeDateTool(BaseTool):
    name: str = "resolve_relative_date"
    description: str = (
        "Converte expressões de data como 'hoje', 'ontem', '15/07', '01/08/2024' "
        "para o formato ISO (YYYY-MM-DD). "
        "Use fornecendo apenas um campo chamado 'input' com a string desejada. "
        "Exemplo de uso correto: {\"input\": \"ontem\"}."
    )

    def _run(self, input: str) -> str:
        input = input.strip().lower()
        hoje = datetime.now()

        if input == "hoje":
            return hoje.strftime('%Y-%m-%d')
        elif input == "ontem":
            return (hoje - timedelta(days=1)).strftime('%Y-%m-%d')
        elif input == "anteontem":
            return (hoje - timedelta(days=2)).strftime('%Y-%m-%d')

        # Match com datas no formato 15/07 ou 15/07/2025
        match = re.match(r'^(\d{1,2})/(\d{1,2})(/(\d{4}))?$', input)
        if match:
            dia = int(match.group(1))
            mes = int(match.group(2))
            ano = int(match.group(4)) if match.group(4) else hoje.year

            try:
                data = datetime(ano, mes, dia)
                return data.strftime('%Y-%m-%d')
            except ValueError:
                return "Data inválida"

        return "Formato não reconhecido"

resolve_relative_date = RelativeDateTool()
