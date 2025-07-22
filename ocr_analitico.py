import tabula
import os
from contextlib import redirect_stderr

# Prepara um "ralo" para onde os avisos serão enviados
devnull = open(os.devnull, 'w')

# Usa o redirect_stderr para enviar qualquer aviso para o "ralo"
# Apenas o código dentro deste bloco 'with' será silenciado
with redirect_stderr(devnull):
    try:
        print("Iniciando a leitura do PDF de forma silenciosa...")
        lista_tabela = tabula.read_pdf(
            "Planilha _orcamentaria_analitica.pdf", 
            pages="1"
        )
        print(len(lista_tabela))
        print("Leitura concluída com sucesso!")
    except Exception as e:
        # Se um erro REAL acontecer, ele ainda será capturado aqui
        print(f"Ocorreu um erro inesperado durante a leitura: {e}")

# Fecha o "ralo"
devnull.close()

# A partir daqui, qualquer erro ou aviso no restante do seu código
# voltará a ser exibido normalmente no console.
if 'lista_tabela' in locals():
    print("\nA variável 'lista_tabela' foi criada.")
    # print(lista_tabela) # Descomente para ver o resultado

print(lista_tabela[0])