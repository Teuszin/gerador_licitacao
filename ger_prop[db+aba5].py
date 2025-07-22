# =============================================================================
# PARTE 1: IMPORTAÇÕES (TODAS JUNTAS)
# =============================================================================
import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from pprint import pprint
import pandas as pd
import docx
import locale
import re
import datetime
from num2words import num2words
from planilhas import *
import database as db # Importa o nosso novo arquivo
# TENTAR IMPORTAR tksheet
try:
    from tksheet import Sheet
except ImportError:
    messagebox.showerror("Erro de Dependência", "A biblioteca tksheet não está instalada.\nPor favor, execute: pip install tksheet")
    exit()


# Coloque esta nova classe no seu script principal



# No seu script principal, substitua a classe PlanilhaWidget por esta versão:

class PlanilhaWidget(ctk.CTkFrame):
    """
    Widget customizado. VERSÃO FINAL com rolagem por Enter/Leave.
    """
    def __init__(self, master, titulo, num_linhas_iniciais=20, parent_scroll_container=None):
        super().__init__(master, fg_color=("#dbdbdb", "#2b2b2b"), corner_radius=8)
        self.pack(fill="x", expand=True, padx=10, pady=15)
        
        # --- LÓGICA DE SCROLL ---
        self.parent_scroll_container = parent_scroll_container
        
        # Conecta os eventos de Entrada e Saída do mouse a todo o widget
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

        # O resto do seu __init__ (widgets internos) continua igual
        # ...
        self.titulo = titulo
        self.grid_columnconfigure(0, weight=1)
        self.label_titulo = ctk.CTkLabel(self, text=self.titulo, font=ctk.CTkFont(size=14, weight="bold"))
        self.label_titulo.grid(row=0, column=0, padx=15, pady=(10, 5), sticky="w")
        container_planilha = ctk.CTkFrame(self, fg_color="transparent")
        container_planilha.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        container_planilha.grid_columnconfigure(0, weight=1)
        tk_frame_interno = tk.Frame(container_planilha)
        tk_frame_interno.pack(fill="both", expand=True)
        headers = ['Tipo', 'Código', 'Banco', 'Descrição', 'Tipo', 'Und', 'Quant.', 'Valor Unit', 'Total']
        self.sheet = Sheet(tk_frame_interno, headers=headers, height=250)
        self.sheet.pack(expand=True, fill="both")
        #self.sheet.set_options(table_bg=("#f2f2f2", "#343638"), header_bg=("#4a4d50", "#4a4d50"))
        self.sheet.enable_bindings("all")
        if num_linhas_iniciais > 0:
            dados_em_branco = [["" for _ in range(len(headers))] for _ in range(num_linhas_iniciais)]
            self.sheet.set_sheet_data(data=dados_em_branco)
        frame_controles = ctk.CTkFrame(self, fg_color="transparent")
        frame_controles.grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.entry_num_linhas = ctk.CTkEntry(frame_controles, width=50, justify="center")
        self.entry_num_linhas.insert(0, "10")
        self.entry_num_linhas.pack(side="left", padx=5)
        botao_adicionar = ctk.CTkButton(frame_controles, text="Adicionar Linhas", width=120, command=self.adicionar_mais_linhas)
        botao_adicionar.pack(side="left", padx=5)

    def _on_enter(self, event):
        """Quando o mouse entra, desliga a rolagem do container pai."""
        if self.parent_scroll_container:
            self.parent_scroll_container.unbind_all("<MouseWheel>")

    def _on_leave(self, event):
        """Quando o mouse sai, liga a rolagem do container pai de volta."""
        if self.parent_scroll_container:
            # Re-liga a função de rolagem padrão do CTkScrollableFrame
            self.parent_scroll_container.bind_all("<MouseWheel>", self.parent_scroll_container._mouse_wheel_all)

    def adicionar_mais_linhas(self):
        # ... (esta função continua igual)
        try:
            num_a_adicionar = int(self.entry_num_linhas.get())
            total_linhas_atuais = self.sheet.get_total_rows()
            self.sheet.insert_rows(rows=num_a_adicionar, idx=total_linhas_atuais)
        except (ValueError, TypeError):
            messagebox.showerror("Erro", "Por favor, insira um número válido.")
    
    def get_dataframe(self):
        # ... (esta função continua igual)
        dados_brutos = self.sheet.get_sheet_data()
        dados_validos = [linha for linha in dados_brutos if any(celula not in [None, ''] for celula in linha)]
        if not dados_validos:
            return pd.DataFrame(columns=self.sheet.headers())
        
        return pd.DataFrame(dados_validos, columns=self.sheet.headers())
    



class EditorDeclaracoesWindow(ctk.CTkToplevel):
    def __init__(self, master, on_close_callback):
        super().__init__(master)
        self.title("Editor de Declarações")
        self.geometry("800x500")
        self.on_close_callback = on_close_callback
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        # --- Layout da Janela ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=1)

        # --- Frame da Esquerda (Lista) ---
        self.left_frame = ctk.CTkFrame(self)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.left_frame.grid_rowconfigure(0, weight=1)
        self.left_frame.grid_columnconfigure(0, weight=1)
        
        self.scrollable_list = ctk.CTkScrollableFrame(self.left_frame, label_text="Declarações")
        self.scrollable_list.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # --- Frame da Direita (Editor) ---
        self.right_frame = ctk.CTkFrame(self)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        ctk.CTkLabel(self.right_frame, text="Título:").pack(anchor="w", padx=10, pady=(10,0))
        self.title_entry = ctk.CTkEntry(self.right_frame)
        self.title_entry.pack(fill="x", padx=10)

        ctk.CTkLabel(self.right_frame, text="Texto da Declaração:").pack(anchor="w", padx=10, pady=(10,0))
        self.text_box = ctk.CTkTextbox(self.right_frame)
        self.text_box.pack(fill="both", expand=True, padx=10, pady=5)
        
        # --- Botões ---
        button_frame = ctk.CTkFrame(self.right_frame, fg_color="transparent")
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.save_button = ctk.CTkButton(button_frame, text="Salvar Alterações", command=self.salvar)
        self.save_button.pack(side="left", padx=5)
        
        self.add_button = ctk.CTkButton(button_frame, text="Adicionar Nova", command=self.adicionar)
        self.add_button.pack(side="left", padx=5)

        self.delete_button = ctk.CTkButton(button_frame, text="Excluir Selecionada", fg_color="#D81B60", hover_color="#C2185B", command=self.excluir)
        self.delete_button.pack(side="left", padx=5)

        # --- Lógica inicial ---
        self.dados_declaracoes = None
        self.botoes_declaracao = {} # <<< MUDANÇA: Usaremos um dicionário para fácil acesso
        self.id_selecionado = None
        self.carregar_lista()
    
    def carregar_lista(self):
        # Limpa a lista antiga
        for botao in self.botoes_declaracao.values():
            botao.destroy()
        self.botoes_declaracao.clear()
        
        # Limpa os campos de edição
        self.id_selecionado = None
        self.title_entry.delete(0, 'end')
        self.text_box.delete('1.0', 'end')

        # Carrega dados do banco
        self.dados_declaracoes = db.ler_todas_declaracoes()
        
        # <<< MUDANÇA 1: Definindo as cores padrão >>>
        # (Cor para modo claro, Cor para modo escuro) - o CTk vai escolher sozinho
        self.cor_texto_normal = ("gray10", "gray90") # Quase preto no modo claro
        self.cor_texto_selecionado = ("#FFFFFF", "#DCE4EE") # Branco/Cinza claro

        for titulo in self.dados_declaracoes.keys():
            botao = ctk.CTkButton(self.scrollable_list, 
                                  text=titulo, 
                                  fg_color="transparent", 
                                  text_color=self.cor_texto_normal, # <<< APLICA A COR PADRÃO
                                  anchor="w",
                                  command=lambda t=titulo: self.selecionar_item(t))
            botao.pack(fill="x", pady=2, padx=2)
            self.botoes_declaracao[titulo] = botao # Adiciona o botão ao dicionário

    def selecionar_item(self, titulo):
        item = self.dados_declaracoes[titulo]
        self.id_selecionado = item['id']
        
        # Preenche os campos de texto à direita
        self.title_entry.delete(0, 'end')
        self.title_entry.insert(0, titulo)
        self.text_box.delete('1.0', 'end')
        self.text_box.insert('1.0', item['texto'])
        
        # <<< MUDANÇA 2: Lógica para destacar o item selecionado >>>
        # Primeiro, redefine TODOS os botões para o estilo "normal"
        for btn in self.botoes_declaracao.values():
            btn.configure(fg_color="transparent", text_color=self.cor_texto_normal)
        
        # Depois, destaca APENAS o botão que foi clicado
        botao_clicado = self.botoes_declaracao[titulo]
        botao_clicado.configure(fg_color=("#3a7ebf", "#1f538d"), text_color=self.cor_texto_selecionado)

    def salvar(self):
        if self.id_selecionado is None:
            messagebox.showwarning("Atenção", "Nenhuma declaração selecionada para salvar.")
            return
        
        novo_titulo = self.title_entry.get()
        novo_texto = self.text_box.get('1.0', 'end-1c')
        db.atualizar_declaracao(self.id_selecionado, novo_titulo, novo_texto)
        self.carregar_lista()
        messagebox.showinfo("Sucesso", "Declaração atualizada!")

    def adicionar(self):
        titulo_padrao = "Nova Declaração"
        texto_padrao = "Escreva o texto aqui."
        
        # Chama a função e verifica o resultado
        sucesso = db.adicionar_declaracao(titulo_padrao, texto_padrao)
        
        if sucesso:
            # Se deu certo, recarrega a lista e seleciona o novo item
            self.carregar_lista()
            self.selecionar_item(titulo_padrao)
        else:
            # Se falhou, avisa o usuário
            messagebox.showwarning("Atenção", "Uma 'Nova Declaração' já existe.\n\nPor favor, renomeie a existente antes de adicionar outra.")
            # Tenta focar na declaração que já existe
            try:
                self.selecionar_item(titulo_padrao)
            except KeyError:
                # Apenas uma segurança caso o item não esteja na lista por algum motivo
                pass

    def excluir(self):
        if self.id_selecionado is None:
            messagebox.showwarning("Atenção", "Nenhuma declaração selecionada para excluir.")
            return
        
        if messagebox.askyesno("Confirmar Exclusão", "Tem certeza que deseja excluir esta declaração?"):
            db.excluir_declaracao(self.id_selecionado)
            self.carregar_lista()

    def on_close(self):
        """Função chamada ao fechar a janela."""
        self.on_close_callback()
        self.destroy()

class DeclarationItem(ctk.CTkFrame):
    def __init__(self, master, title, command):
        # --- Define todas as cores que vamos usar ---
        self.original_color = "transparent"
        self.hover_color = "#3a3a3a"
        # Cores para o texto (compatível com modo claro/escuro)
        self.text_original_color = ("gray10", "#DCE4EE") # Cinza claro padrão
        self.text_hover_color = "white"                  # Branco para destaque máximo

        # Inicializa o Frame
        super().__init__(master, fg_color=self.original_color, height=30, corner_radius=6)

        # --- Cria os widgets internos ---
        self.checkbox = ctk.CTkCheckBox(self, text="")
        self.checkbox.place(x=5, y=4)

        # O label já começa com a cor de texto original
        self.label = ctk.CTkLabel(self, text=title, anchor="w", text_color=self.text_original_color)
        self.label.place(x=35, y=3)

        # --- Associa os eventos (binds) ---
        self.bind("<Button-1>", lambda event: command())
        self.label.bind("<Button-1>", lambda event: command())

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.label.bind("<Enter>", self.on_enter)
        self.label.bind("<Leave>", self.on_leave)
        self.checkbox.bind("<Enter>", self.on_enter)
        self.checkbox.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        """Muda a cor de fundo E a cor do texto para o modo hover."""
        self.configure(fg_color=self.hover_color)
        # Adiciona a mudança de cor do texto
        self.label.configure(text_color=self.text_hover_color)

    def on_leave(self, event):
        """Reverte a cor de fundo E a cor do texto para o modo original."""
        self.configure(fg_color=self.original_color)
        # Reverte a cor do texto
        self.label.configure(text_color=self.text_original_color)


# =============================================================================
# PARTE 2: LÓGICA DE GERAÇÃO DO DOCUMENTO (O ANTIGO SCRIPT 1)
# <<< MODIFICADO >>>
# Esta parte foi transformada em funções para poderem ser chamadas pela interface.
# =============================================================================

# --- FUNÇÕES AUXILIARES DO DOCX ---
# (Estas funções provavelmente estavam no seu arquivo 'planilhas.py')


def formatar_frase_opcional(label_prefixo, entry_widget, combo_widget):
    """
    Verifica se um campo foi preenchido. Se sim, formata uma frase completa.
    Se não, retorna uma string vazia.
    Exemplo de retorno: "Prazo de Conclusão: 60 (sessenta) dias"
    """
    valor_numerico = entry_widget.get()
    
    # Se o campo estiver vazio, retorna uma string vazia (o campo é opcional)
    if not valor_numerico or not valor_numerico.strip():
        return f"{label_prefixo}: "
        
    try:
        # Tenta converter o valor para número para garantir que é válido
        valor_int = int(valor_numerico)
        valor_extenso = num2words(valor_int, lang='pt_BR')
        periodo = combo_widget.get()
        # Retorna a frase completa
        return f"{label_prefixo}: {valor_numerico} ({valor_extenso}) {periodo}"
    except ValueError:
        # Se o usuário digitar algo que não é um número, retorna vazio para não quebrar o programa
        return ""


# --- FUNÇÃO PRINCIPAL DE GERAÇÃO ---
# <<< NOVA FUNÇÃO >>>
def gerar_documento_word(contexto_formulario, df_planilha, df_cronograma, valor_numerico_total, titulos_declaracoes,dados_das_declaracoes):
    """
    Função principal que gera o documento Word a partir dos dados da interface.
    Recebe o dicionário 'contexto' e o DataFrame 'df_planilha'.
    Retorna uma tupla (sucesso, mensagem).
    """
    try:
        # --- A. PREPARAÇÃO DOS DADOS ---
        print("Preparando dados recebidos da interface...")
        
        # Altera o locale para Português (Brasil) para formatar a moeda e a data.
        try:
            locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252') # Alternativa para Windows
            except locale.Error:
                print("Aviso: Não foi possível definir o locale para pt_BR. A formatação de moeda pode estar incorreta.")
                pass # Continua a execução mesmo que o locale falhe

        # Monta o dicionário de contexto para o template.
        # Agora, a maioria dos valores vem diretamente do formulário, já formatados.
        contexto = {
            '{{PRP}}': contexto_formulario.get('PRP', ''),
            '{{OFICIO}}': contexto_formulario.get('OFICIO', ''),
            '{{PREGAO}}': contexto_formulario.get('PREGAO', ''),
            '{{CLIENTE}}': contexto_formulario.get('CLIENTE', ''),
            #'{{TAXA_BDI}}': contexto_formulario.get('TAXA_BDI', ''), # Novo campo
            '{{OBJETO}}': contexto_formulario.get('OBJETO', ''), # Corrigido de 'OBJETIVO'
            
            # Estes campos já vêm formatados ou vazios da função de coleta
            '{{VALIDADE_PROPOSTA}}': contexto_formulario.get('VALIDADE_PROPOSTA', ''),
            '{{VIGENCIA}}': contexto_formulario.get('VIGENCIA', ''),
            '{{PRAZO_DE_CONCLUSAO}}': contexto_formulario.get('PRAZO_DE_CONCLUSAO', ''), # Novo campo
            
            # Estes campos ainda precisam ser calculados aqui
            '{{VALOR_TOTAL}}': locale.currency(valor_numerico_total, grouping=True),
            '{{VALOR_TOTAL_EXTENSO}}': num2words(valor_numerico_total, to='currency', lang='pt_BR').capitalize(),
            '{{DATA_EXTENSO}}': datetime.date.today().strftime("%d de %B de %Y"),
        }

        # =============================================================
        # <<< INÍCIO DA NOVA LÓGICA DAS DECLARAÇÕES >>>
        # =============================================================
        # 1. Criamos uma lista para guardar o texto de cada declaração selecionada
        textos_das_declaracoes = []
        
        # 2. Percorremos os títulos que vieram da interface
        for titulo in titulos_declaracoes:
            # 3. Buscamos o texto completo de cada declaração no nosso dicionário principal
            texto_completo = dados_das_declaracoes.get(titulo, "")
            if texto_completo:
                textos_das_declaracoes.append(texto_completo)
        
        # 4. Juntamos todos os textos em um único bloco, separados por duas quebras de linha (um parágrafo)
        texto_final_declaracoes = "\n\n".join(textos_das_declaracoes)
        
        # 5. Adicionamos esse bloco de texto ao nosso dicionário de substituições!
        contexto['{{DECLARACOES}}'] = texto_final_declaracoes
        # =============================================================
        # <<< FIM DA NOVA LÓGICA DAS DECLARAÇÕES >>>
        # =============================================================


        
        # --- B. GERANDO O DOCUMENTO ---
        print("Carregando o template 'Template.docx'...")
        doc = docx.Document('Template.docx')

        print("Substituindo placeholders no documento...")
        for key, value in contexto.items():
            # A substituição continua a mesma
            # Apenas garantimos que o valor é uma string para evitar erros
            docx_replace_regex(doc, re.compile(re.escape(str(key))), str(value))

        print("Primeira página gerada com sucesso.")

       
        
        if not df_planilha.empty:
            print("Adicionando o orcamento sintetico ao documento...")
            doc.add_page_break()
            # Chamando a função que você já tem, passando todos os dados necessários
            adicionar_planilha_ao_documento(doc, df_planilha, contexto_formulario)
        else:
            print("Página de orcamento sintetico pulada pois não há dados.")

        if not df_cronograma.empty:
            print("Adicionando o cronograma ao documento...")
            doc.add_page_break()
            # Chamando a função que você já tem, passando todos os dados necessários
            adicionar_cronograma_fisico_financeiro(doc, df_cronograma, df_planilha, contexto_formulario,valor_numerico_total)
        else:
            print("Página de cronograma pulada pois não há dados.")

        

        # Você ainda precisará do seu df_itens original para o total geral
        # Exemplo de df_itens (necessário para o 'Valor Total com BDI')
        dados_itens = {
            'Valor Total com BDI': [122715.75, 85000.00] # Supondo que esses sejam os totais
        }
        df_itens = pd.DataFrame(dados_itens)


        # --- C. SALVANDO O DOCUMENTO FINAL ---
        nome_arquivo_saida = f"Proposta_Final_PRP_{contexto['{{PRP}}']}.docx"
        doc.save(nome_arquivo_saida)
        
        mensagem_sucesso = f"SUCESSO! Documento final '{nome_arquivo_saida}' foi criado."
        print("-" * 50)
        print(mensagem_sucesso)
        print("-" * 50)
        return True, mensagem_sucesso

    except FileNotFoundError:
        erro = "ERRO CRÍTICO: O arquivo 'Template.docx' não foi encontrado."
        print(erro)
        return False, erro
    except Exception as e:
        erro = f"Ocorreu um erro inesperado durante a geração do documento: {e}"
        print(erro)
        return False, erro
        
    finally:
        # <<< CORREÇÃO FINAL >>>
        # Restaura o locale para o padrão "C", que é seguro para o Tkinter.
        # Isso é executado sempre, garantindo que a interface não trave mais.
        try:
            locale.setlocale(locale.LC_ALL, 'C')
        except locale.Error:
            print("Aviso: Não foi possível restaurar o locale para 'C'.")
            pass

# =============================================================================
# PARTE 3: INTERFACE GRÁFICA (O ANTIGO SCRIPT 2)
# =============================================================================

def abrir_janela_principal():
    janela_principal = ctk.CTk()
    janela_principal.title("Gerador de Documentos")
    janela_principal.geometry("800x600")
    janela_principal.resizable(True, True)

    # Centralizar
    largura_tela = janela_principal.winfo_screenwidth()
    altura_tela = janela_principal.winfo_screenheight()
    pos_x = (largura_tela // 2) - (800 // 2)
    pos_y = (altura_tela // 2) - (600 // 2)
    janela_principal.geometry(f"800x600+{pos_x}+{pos_y}")

    def coletar_e_gerar():
         # 1. Coleta dos dados do formulário
         # 1. Coleta dos dados do formulário
        contexto_formulario = {
        'PRP': entries['PRP'].get(),
        'OFICIO': entries['OFICIO'].get(),
        'PREGAO': entries['PREGAO'].get(),
        'CLIENTE': entries['CLIENTE'].get(),
        'TAXA_BDI': entries['TAXA_BDI'].get(),
        'VALOR_TOTAL_MANUAL': entry_valor_total_manual.get(),
        'OBJETO': textbox_objeto.get("1.0", "end-1c"),
        
        # Campos com formatação condicional
        'VALIDADE_PROPOSTA': formatar_frase_opcional("Validade da Proposta", entry_validade, combobox_validade_periodo),
        'PRAZO_DE_CONCLUSAO': formatar_frase_opcional("Prazo de Conclusão", entry_prazo, combobox_prazo_periodo),
        'VIGENCIA': formatar_frase_opcional("Vigência Contratual", entry_vigencia, combobox_vigencia_periodo),
        }

        selected_titles = []
        for title in sorted_titles:
            item_widget = declaration_widgets[title]
            if item_widget.checkbox.get() == 1:
                selected_titles.append(title)

        # Exemplo de como você pode usar os dados (apenas para teste)
        print("--- DADOS COLETADOS ---")
        for chave, valor in contexto_formulario.items():
            print(f"'{chave}': '{valor}'")
        print("------------------------")
    
        try:
            # =============================================================
            # 2. Processa a Planilha de Orçamento (AQUI CRIAMOS df_planilha)
            # =============================================================
            dados_brutos_orcamento = sheet_orcamento.get_sheet_data()
            dados_validos_orcamento = [linha for linha in dados_brutos_orcamento if any(celula not in [None, ''] for celula in linha)]
            
            # Se não houver dados no orçamento, criamos um DataFrame vazio mas com as colunas certas
            if not dados_validos_orcamento:
                df_planilha = pd.DataFrame(columns=headers_orcamento)
            else:
                df_planilha = pd.DataFrame(dados_validos_orcamento, columns=sheet_orcamento.headers())
                # Faz a limpeza numérica
                colunas_numericas_orcamento = ['Quant', 'Valor Unit', 'Valor Unit com BDI', 'Valor Total sem BDI', 'Valor Total com BDI']
                for col in colunas_numericas_orcamento:
                    if col in df_planilha.columns:
                        numeros_limpos = (df_planilha[col].astype(str)
                                        .str.replace('R$', '', regex=False).str.strip()
                                        .str.replace('.', '', regex=False)
                                        .str.replace(',', '.', regex=False))
                        df_planilha[col] = pd.to_numeric(numeros_limpos, errors='coerce').fillna(0)
            
            # =============================================================
            # 3. Processa a Planilha de Cronograma
            # =============================================================
            dados_brutos_cronograma = sheet_cronograma.get_sheet_data()
            dados_validos_cronograma = [linha for linha in dados_brutos_cronograma if any(celula not in [None, ''] for celula in linha)]
            if not dados_validos_cronograma:
                df_cronograma = pd.DataFrame(columns=headers_cronograma)
            else:
                df_cronograma = pd.DataFrame(dados_validos_cronograma, columns=sheet_cronograma.headers())

            # =======================================================================
            # 4. AGORA que df_planilha existe, calcula o total e decide a "fonte da verdade"
            # =======================================================================
            df_apenas_itens = df_planilha[df_planilha['Valor Unit'] > 0]
            soma_orcamento = df_apenas_itens['Valor Total com BDI'].sum()

            valor_manual_str = entry_valor_total_manual.get()
            valor_manual_limpo = valor_manual_str.replace('.', '').replace(',', '.')
            try:
                valor_manual_num = float(valor_manual_limpo if valor_manual_limpo else 0)
            except ValueError:
                valor_manual_num = 0

            if soma_orcamento > 0:
                valor_total_final = soma_orcamento
                print(f"Usando valor total da planilha de orçamento: {valor_total_final}")
            else:
                valor_total_final = valor_manual_num
                print(f"Planilha de orçamento vazia. Usando valor total manual: {valor_total_final}")

            if valor_total_final <= 0:
                messagebox.showwarning("Atenção", "Nenhum valor total definido (nem na planilha de orçamento, nem no campo manual).")
                return

        except Exception as e:
            # Mostra o erro real que aconteceu durante o processamento
            messagebox.showerror("Erro no Processamento de Dados", f"Ocorreu um erro ao processar as planilhas:\n\n{e}")
            return
    
        # 5. Chama a próxima função com todos os dados prontos
        messagebox.showinfo("Iniciando", "Dados coletados. A geração do documento será iniciada agora.")
        sucesso, mensagem = gerar_documento_word(contexto_formulario, df_planilha, df_cronograma, valor_total_final,selected_titles,declaracoes_data)
        
        if sucesso:
            messagebox.showinfo("Sucesso!", mensagem)
        else:
            messagebox.showerror("Erro na Geração", mensagem)
        

    # --- CRIAÇÃO DO FORMULÁRIO ---
    tabview = ctk.CTkTabview(master=janela_principal, corner_radius=0)
    tabview.pack(pady=10, padx=10, fill="both", expand=True)
    tab_1 = tabview.add("Dados da Proposta")
    tab_2 = tabview.add("Declarações")
    tab_3 = tabview.add("Planilha Sintética")
    tab_4 = tabview.add("Cronograma Físico-Financeiro")
    tab_5 = tabview.add("Planilha Analítica")
    

    # --- Frame principal para conter tudo na aba ---
    main_frame_analitica = ctk.CTkFrame(tab_5, fg_color="transparent")
    main_frame_analitica.pack(fill="both", expand=True)
    main_frame_analitica.grid_columnconfigure(0, weight=1)

    # --- Frame para os controles de topo ---
    top_controls_frame = ctk.CTkFrame(main_frame_analitica)
    top_controls_frame.pack(fill="x", padx=10, pady=10)

    # --- Lista para guardar nossas instâncias de PlanilhaWidget ---
    lista_de_planilhas = []

    # --- Função para adicionar uma nova planilha dinamicamente ---
    
    def adicionar_nova_planilha():
        # --- 1. VERIFICAÇÃO: A planilha de orçamento está preenchida? (Lógica mantida) ---
        dados_brutos_orcamento = sheet_orcamento.get_sheet_data()
        dados_validos_orcamento = [linha for linha in dados_brutos_orcamento if any(celula not in [None, ''] for celula in linha)]

        if not dados_validos_orcamento:
            messagebox.showwarning("Ação Bloqueada", "A Planilha Orçamentária está vazia.\n\nPreencha-a primeiro para poder adicionar uma planilha analítica.")
            return

        # =======================================================================
        # <<< INÍCIO DA NOVA LÓGICA AUTOMÁTICA >>>
        # =======================================================================
        # --- 2. EXTRAÇÃO DE ITENS: Pega todos os itens do orçamento ---
        df_orcamento_temp = pd.DataFrame(dados_validos_orcamento, columns=sheet_orcamento.headers())
        itens_brutos = df_orcamento_temp['Item'].astype(str).str.strip()
        todos_os_itens_do_orcamento = sorted(list(set([item for item in itens_brutos if item])))

        if not todos_os_itens_do_orcamento:
            messagebox.showinfo("Aviso", "Nenhum número de item encontrado na Planilha Orçamentária.")
            return

        # --- 3. VERIFICAÇÃO DE ESTADO: Descobre qual é o próximo item ---
        # Pega os títulos das planilhas que já foram criadas
        titulos_ja_criados = [planilha.titulo for planilha in lista_de_planilhas]
        
        proximo_item_para_adicionar = None
        # Procura o primeiro item do orçamento que ainda não tem uma planilha analítica
        for item_orcamento in todos_os_itens_do_orcamento:
            titulo_esperado = f"Análise do Item {item_orcamento}"
            if titulo_esperado not in titulos_ja_criados:
                proximo_item_para_adicionar = item_orcamento
                break # Para o loop assim que encontrar o próximo

        # --- 4. CRIAÇÃO AUTOMÁTICA ---
        if proximo_item_para_adicionar:
            titulo_final = f"Análise do Item {proximo_item_para_adicionar}"
            
            # Cria a nova instância do nosso widget de planilha
            nova_planilha = PlanilhaWidget(master=scroll_container_analitica, titulo=titulo_final)
            
            # Adiciona a nova planilha à nossa lista para controle
            lista_de_planilhas.append(nova_planilha)
            print(f"Adicionada automaticamente: {titulo_final}. Total: {len(lista_de_planilhas)}")
        else:
            # Se o loop terminar e não encontrar um próximo item
            messagebox.showinfo("Concluído", "Todas as planilhas analíticas para os itens do orçamento já foram criadas!")


    # --- Botão principal para adicionar novas planilhas ---
    botao_adicionar_planilha = ctk.CTkButton(top_controls_frame, text="Adicionar Nova Planilha Analítica", command=adicionar_nova_planilha)
    botao_adicionar_planilha.pack(pady=10)

    # --- Container rolável que vai abrigar todas as planilhas ---
    scroll_container_analitica = ctk.CTkScrollableFrame(main_frame_analitica, fg_color="transparent")
    scroll_container_analitica.pack(fill="both", expand=True, padx=5, pady=5)

    # --- Inicia com uma planilha já na tela ---
    #adicionar_nova_planilha()


    # Adicionando um texto temporário na nova aba

    def show_declaration_text(title):
        text = declaracoes_data.get(title, "Texto não encontrado.")
        right_title_label.configure(text=f"{title}:")
        
        right_textbox.configure(state="normal")
        right_textbox.delete("1.0", "end")
        right_textbox.insert("1.0", text)
        right_textbox.configure(state="disabled")

    def filter_declarations(event=None):
        search_term = search_entry.get().lower()
        for title, item_widget in declaration_widgets.items():
            if search_term in title.lower():
                item_widget.pack(fill="x", pady=4, padx=2)
            else:
                item_widget.pack_forget()

    def toggle_all():
        is_checked = select_all_checkbox.get()
        for title in sorted_titles:
            item_widget = declaration_widgets[title]
            if item_widget.winfo_viewable():
                if is_checked:
                    item_widget.checkbox.select()
                else:
                    item_widget.checkbox.deselect()
                    

    paned_window = tk.PanedWindow(tab_2, orient=tk.HORIZONTAL, sashrelief=tk.FLAT,
                              bg="#333333", sashwidth=6, borderwidth=0)
    paned_window.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)

    # --- Frame da Esquerda ---
    left_frame = ctk.CTkFrame(paned_window, corner_radius=0)
    paned_window.add(left_frame, width=350, minsize=250)

    # --- Frame da Direita ---
    right_frame = ctk.CTkFrame(paned_window, corner_radius=0)
    paned_window.add(right_frame, minsize=300)

    # --- Widgets do Frame da Esquerda ---
    search_entry = ctk.CTkEntry(left_frame, placeholder_text="Pesquisar...")
    search_entry.pack(pady=10, padx=10, fill="x")
    search_entry.bind("<KeyRelease>", filter_declarations)

    select_all_checkbox = ctk.CTkCheckBox(left_frame, text="Selecionar Tudo", command=toggle_all)
    select_all_checkbox.pack(pady=5, padx=10, anchor="w")

    scrollable_frame = ctk.CTkScrollableFrame(left_frame, label_text="Declarações")
    scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

    declaration_widgets = {} 
    declaracoes_data = {}      # <<< COMEÇA VAZIO
    sorted_titles = []
    sorted_titles = sorted(declaracoes_data.keys())

    def recarregar_declaracoes_ui():
            print("Recarregando a lista de declarações da UI principal...")
            # Limpa os widgets antigos
            for widget in declaration_widgets.values():
                widget.destroy()
            declaration_widgets.clear()

            # Lê os dados mais recentes do banco de dados
            dados_db = db.ler_todas_declaracoes()

            # Reescreve o dicionário e os títulos que o resto do programa usa
            declaracoes_data.clear()
            sorted_titles.clear()

            for titulo, data in dados_db.items():
                declaracoes_data[titulo] = data['texto']

            sorted_titles.extend(sorted(declaracoes_data.keys()))

            # Recria os itens na lista rolável
            for title in sorted_titles:
                callback = lambda t=title: show_declaration_text(t)
                item = DeclarationItem(scrollable_frame, title=title, command=callback)
                item.pack(fill="x", pady=4, padx=2)
                declaration_widgets[title] = item

        # E finalmente, chame esta função uma vez ao criar a interface
        # para a carga inicial
    recarregar_declaracoes_ui()


    # --- Widgets do Frame da Direita ---
    right_title_label = ctk.CTkLabel(right_frame, text="Selecione uma declaração para ver o texto", font=ctk.CTkFont(size=16, weight="bold"), wraplength=500, justify="left")
    right_title_label.pack(pady=10, padx=20, anchor="w")

    right_textbox = ctk.CTkTextbox(right_frame, wrap="word", font=("Calibri", 14))
    right_textbox.pack(pady=10, padx=20, fill="both", expand=True)
    right_textbox.configure(state="disabled")


    # Adicione este botão no frame da esquerda
    

    # E adicione a função que abre a janela
    editor_window = None
    def abrir_editor():
        nonlocal editor_window
        if editor_window is None or not editor_window.winfo_exists():
            editor_window = EditorDeclaracoesWindow(janela_principal, on_close_callback=recarregar_declaracoes_ui)
            editor_window.transient(janela_principal) # Mantém a janela do editor na frente
        else:
            editor_window.focus()


    edit_button = ctk.CTkButton(left_frame, text="Gerenciar Declarações", command=abrir_editor)
    edit_button.pack(side="bottom", fill="x", padx=10, pady=10)

    
    # --- ABA 1: FORMULÁRIO DE DADOS ---
    content_frame_1 = ctk.CTkScrollableFrame(master=tab_1, fg_color="transparent")
    content_frame_1.pack(fill="both", expand=True, padx=10, pady=10)
    content_frame_1.grid_columnconfigure(0, weight=1)

    entries = {}
    current_row = 0

    # --- LINHA 1: PRP | OFICIO | PREGAO ---
    frame_top_fields = ctk.CTkFrame(master=content_frame_1, fg_color="transparent")
    frame_top_fields.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))
    frame_top_fields.grid_columnconfigure((0, 1, 2), weight=1)
    current_row += 1

    campos_horizontais_1 = ['PRP', 'OFICIO', 'PREGAO']
    for i, nome_campo in enumerate(campos_horizontais_1):
        label = ctk.CTkLabel(master=frame_top_fields, text=f"{nome_campo}:", anchor="w")
        label.grid(row=0, column=i, padx=(10, 5), pady=(5, 0), sticky="ew")
        entry = ctk.CTkEntry(master=frame_top_fields, placeholder_text=f"Valor de {nome_campo}")
        entry.grid(row=1, column=i, padx=(10, 5), pady=(0, 5), sticky="ew")
        entries[nome_campo] = entry

    # --- LINHA 2: CLIENTE | TAXA DE BDI (%) ---
    frame_cliente_bdi = ctk.CTkFrame(master=content_frame_1, fg_color="transparent")
    frame_cliente_bdi.grid(row=current_row, column=0, sticky="ew", pady=(0, 10))
    frame_cliente_bdi.grid_columnconfigure((0, 1), weight=1)
    current_row += 1

    # Campo CLIENTE
    label_cliente = ctk.CTkLabel(master=frame_cliente_bdi, text="CLIENTE:", anchor="w")
    label_cliente.grid(row=0, column=0, padx=(10, 5), pady=(5, 0), sticky="ew")
    entry_cliente = ctk.CTkEntry(master=frame_cliente_bdi, placeholder_text="Insira o valor para CLIENTE")
    entry_cliente.grid(row=1, column=0, padx=(10, 5), pady=(0, 5), sticky="ew")
    entries['CLIENTE'] = entry_cliente

    # Campo TAXA DE BDI (Opcional)
    label_bdi = ctk.CTkLabel(master=frame_cliente_bdi, text="TAXA DE BDI (%):", anchor="w")
    label_bdi.grid(row=0, column=1, padx=(5, 10), pady=(5, 0), sticky="ew")
    entry_bdi = ctk.CTkEntry(master=frame_cliente_bdi, placeholder_text="Opcional. Ex: 25.5")
    entry_bdi.grid(row=1, column=1, padx=(5, 10), pady=(0, 5), sticky="ew")
    entries['TAXA_BDI'] = entry_bdi

    # --- LINHA 3: VALOR TOTAL MANUAL (Opcional) ---
    label_valor_total_manual = ctk.CTkLabel(master=content_frame_1, text="VALOR TOTAL MANUAL (Opcional):", anchor="w")
    label_valor_total_manual.grid(row=current_row, column=0, padx=10, pady=(10, 0), sticky="ew")
    entry_valor_total_manual = ctk.CTkEntry(master=content_frame_1, placeholder_text="Insira se não houver planilha de orçamento. Ex: 12345,67")
    entry_valor_total_manual.grid(row=current_row + 1, column=0, padx=10, pady=(0, 10), sticky="ew")
    current_row += 2

    # --- FUNÇÃO AUXILIAR PARA CRIAR CAMPOS COM PERÍODO ---
    def criar_campo_com_periodo(master, label_text, default_value, row):
        label = ctk.CTkLabel(master=master, text=label_text, anchor="w")
        label.grid(row=row, column=0, padx=10, pady=(10, 0), sticky="ew")
        
        frame = ctk.CTkFrame(master=master, fg_color="transparent")
        frame.grid(row=row + 1, column=0, padx=0, pady=(0, 10), sticky="ew")
        frame.grid_columnconfigure(0, weight=3) # Entry ocupa mais espaço
        frame.grid_columnconfigure(1, weight=1) # Combobox ocupa menos espaço
        
        entry = ctk.CTkEntry(master=frame)
        if default_value:
            entry.insert(0, default_value)
        
        combobox = ctk.CTkComboBox(master=frame, values=["dias", "meses"])
        combobox.set("dias")
        
        entry.grid(row=0, column=0, padx=(10, 5), sticky="ew")
        combobox.grid(row=0, column=1, padx=(5, 10), sticky="ew")
        
        return entry, combobox

    # --- LINHA 4: VALIDADE DA PROPOSTA ---
    entry_validade, combobox_validade_periodo = criar_campo_com_periodo(content_frame_1, "VALIDADE DA PROPOSTA:", "60", current_row)
    current_row += 2

    # --- LINHA 5: PRAZO DE CONCLUSÃO (Opcional) ---
    entry_prazo, combobox_prazo_periodo = criar_campo_com_periodo(content_frame_1, "PRAZO DE CONCLUSÃO (Opcional):", "", current_row)
    current_row += 2

    # --- LINHA 6: VIGENCIA (Opcional) ---
    entry_vigencia, combobox_vigencia_periodo = criar_campo_com_periodo(content_frame_1, "VIGÊNCIA (Opcional):", "", current_row)
    current_row += 2

    # --- LINHA 7: OBJETO ---
    label_objeto = ctk.CTkLabel(master=content_frame_1, text="OBJETO:", anchor="w")
    label_objeto.grid(row=current_row, column=0, padx=10, pady=(10, 0), sticky="ew")
    textbox_objeto = ctk.CTkTextbox(master=content_frame_1, height=120, border_width=2)
    textbox_objeto.grid(row=current_row + 1, column=0, padx=10, pady=(0, 10), sticky="ew")
    current_row += 2
    
    # --- ABA 2: PLANILHA ORÇAMENTÁRIA (USANDO tksheet) ---
    content_frame_3 = ctk.CTkFrame(tab_3, fg_color="transparent")
    content_frame_3.pack(fill="both", expand=True, padx=10, pady=0)
    
    tk_frame_container = tk.Frame(content_frame_3)
    tk_frame_container.pack(expand=True, fill="both")
    headers_orcamento = ['Item', 'Código', 'Banco', 'Descrição', 'Und', 'Quant', 'Valor Unit', 'Valor Unit com BDI', 'Valor Total sem BDI', 'Valor Total com BDI']
    sheet_orcamento = Sheet(tk_frame_container, headers=headers_orcamento)
    sheet_orcamento.pack(expand=True, fill="both")
    # (Configurações da planilha, sem alterações)
    sheet_orcamento.set_options(set_index_width=0)
    sheet_orcamento.column_width({ 'Descrição': 300, 'Valor Unit': 120, 'Valor Unit com BDI': 120, 'Valor Total sem BDI': 120, 'Valor Total com BDI': 120 })
    num_linhas_vazias = 30
    dados_em_branco = [["" for _ in range(len(headers_orcamento))] for _ in range(num_linhas_vazias)]
    sheet_orcamento.set_sheet_data(data=dados_em_branco)
    sheet_orcamento.enable_bindings("all")

    # =======================================================================
    # <<< CÓDIGO FALTANDO ADICIONADO AQUI >>>
    # =======================================================================
    def adicionar_mais_linhas_orcamento():
        valor_digitado = entry_num_linhas_orcamento.get()
        try:
            num_a_adicionar = int(valor_digitado)
            if num_a_adicionar <= 0:
                messagebox.showwarning("Entrada Inválida", "Por favor, insira um número positivo.")
                return
            total_linhas_atuais = sheet_orcamento.get_total_rows()
            sheet_orcamento.insert_rows(rows=num_a_adicionar, idx=total_linhas_atuais)
        except ValueError:
            messagebox.showerror("Erro", f"'{valor_digitado}' não é um número válido.")
        except Exception as e:
            print(f"Erro ao adicionar linhas: {e}")
    # =======================================================================

    frame_add_linhas = ctk.CTkFrame(master=content_frame_3, fg_color="transparent")
    frame_add_linhas.pack(side="bottom", fill="x", padx=10, pady=10)
    
    # Este botão agora encontrará a função 'adicionar_mais_linhas'
    botao_adicionar_orcamento = ctk.CTkButton(master=frame_add_linhas, text="Adicionar",command=adicionar_mais_linhas_orcamento) # O comando agora funciona
    botao_adicionar_orcamento.pack(side="left", padx=(0, 5))

    entry_num_linhas_orcamento = ctk.CTkEntry(master=frame_add_linhas, 
                                    width=70, 
                                    justify="center")
    entry_num_linhas_orcamento.insert(0, "30")
    entry_num_linhas_orcamento.pack(side="left", padx=5)

    label_add_linhas = ctk.CTkLabel(master=frame_add_linhas, 
                                    text="mais linhas na parte de baixo")
    label_add_linhas.pack(side="left", padx=5)

    # =======================================================================
    # <<< NOVO: CÓDIGO COMPLETO PARA A ABA 3 >>>
    # =======================================================================
    content_frame_4 = ctk.CTkFrame(tab_4, fg_color="transparent")
    content_frame_4.pack(fill="both", expand=True, padx=10, pady=0)

    tk_frame_container_4 = tk.Frame(content_frame_4)
    tk_frame_container_4.pack(expand=True, fill="both")

    # --- Defina os cabeçalhos para a sua planilha de cronograma ---
    # !!! ATENÇÃO: Ajuste estes cabeçalhos conforme sua necessidade !!!
    headers_cronograma = [
    'Item', 'Descrição', 'Total da Etapa', 
    '30 Dias', '60 Dias', '90 Dias', '120 Dias' 
    # Adapte os nomes e a quantidade de etapas conforme sua necessidade
]
    # Crie uma nova instância da planilha para o cronograma
    sheet_cronograma = Sheet(tk_frame_container_4, headers=headers_cronograma)
    sheet_cronograma.pack(expand=True, fill="both")

    # Configurações visuais (pode personalizar)
    sheet_cronograma.set_options(set_index_width=0)#, table_bg="#2B2B2B", table_fg="#DCE4EE", header_bg="#212121", header_fg="#DCE4EE", table_grid_color="#4A4A4A")
    sheet_cronograma.column_width({'Descrição': 300, 'Valor Total': 120})

    # Popula com linhas vazias
    num_linhas_vazias_crono = 20
    dados_em_branco_crono = [["" for _ in range(len(headers_cronograma))] for _ in range(num_linhas_vazias_crono)]
    sheet_cronograma.set_sheet_data(data=dados_em_branco_crono)
    sheet_cronograma.enable_bindings("all")

    # --- Controles para adicionar linhas na planilha de cronograma ---
    # Função específica para a planilha de cronograma
    def adicionar_mais_linhas_cronograma():
        valor_digitado = entry_num_linhas_cronograma.get()
        try:
            num_a_adicionar = int(valor_digitado)
            if num_a_adicionar <= 0:
                messagebox.showwarning("Entrada Inválida", "Por favor, insira um número positivo.")
                return
            total_linhas_atuais = sheet_cronograma.get_total_rows()
            sheet_cronograma.insert_rows(rows=num_a_adicionar, idx=total_linhas_atuais)
        except ValueError:
            messagebox.showerror("Erro", f"'{valor_digitado}' não é um número válido.")


    # Frame para os widgets de controle
    frame_add_linhas_cronograma = ctk.CTkFrame(master=content_frame_4, fg_color="transparent")
    frame_add_linhas_cronograma.pack(side="bottom", fill="x", padx=10, pady=10)

    # Botão
    botao_adicionar_cronograma = ctk.CTkButton(master=frame_add_linhas_cronograma,
                                            text="Adicionar",
                                            width=100,
                                            command=adicionar_mais_linhas_cronograma)
    botao_adicionar_cronograma.pack(side="left", padx=(0, 5))

    # Entry para o número de linhas
    entry_num_linhas_cronograma = ctk.CTkEntry(master=frame_add_linhas_cronograma,
                                            width=70,
                                            justify="center")
    entry_num_linhas_cronograma.insert(0, "20")
    entry_num_linhas_cronograma.pack(side="left", padx=5)

    # Label
    label_add_linhas_cronograma = ctk.CTkLabel(master=frame_add_linhas_cronograma,
                                            text="mais linhas na parte de baixo")
    label_add_linhas_cronograma.pack(side="left", padx=5)
    


    # <<< NOVA LÓGICA PARA A PLANILHA ANALÍTICA >>
    lista_de_dataframes_analiticos = []
    print("\n--- Coletando dados das Planilhas Analíticas ---")
    for i, planilha_widget in enumerate(lista_de_planilhas):
        df = planilha_widget.get_dataframe()
        if not df.empty:
            print(f"Dados da Planilha Analítica {i+1} coletados.")
            lista_de_dataframes_analiticos.append(df)



    # --- BOTÃO GERAL ---
    botao_gerar = ctk.CTkButton(master=janela_principal, text="Gerar Documento Final", command=coletar_e_gerar, height=40)
    botao_gerar.pack(pady=10, padx=10, fill="x")


    # Crie esta função de recarregamento

    janela_principal.mainloop()


def criar_janela_login():
    """
    Cria e configura a janela de login inicial.
    """
    # --- Configuração da Janela de Login ---
    janela_login = ctk.CTk()
    janela_login.title("Sistema de Login")
    janela_login.resizable(False, False)

    # Centralizar a janela de login
    largura_janela = 400
    altura_janela = 350
    largura_tela = janela_login.winfo_screenwidth()
    altura_tela = janela_login.winfo_screenheight()
    pos_x = (largura_tela // 2) - (largura_janela // 2)
    pos_y = (altura_tela // 2) - (altura_janela // 2)
    janela_login.geometry(f"{largura_janela}x{altura_janela}+{pos_x}+{pos_y}")

    # --- Função de Login (aninhada para ter acesso à janela_login) ---
    def fazer_login():
        usuario = entry_usuario.get()
        senha = entry_senha.get()

        if usuario == "1" and senha == "1":
            messagebox.showinfo("Sucesso", "Login realizado com sucesso!")
            # AÇÃO PRINCIPAL: FECHA A JANELA DE LOGIN E ABRE A PRINCIPAL
            janela_login.destroy()
            abrir_janela_principal()
        elif usuario == "" or senha == "":
            messagebox.showwarning("Atenção", "Por favor, preencha todos os campos.")
        else:
            messagebox.showerror("Erro", "Usuário ou senha inválidos.")

    # --- Widgets na Janela de Login ---
    frame_login = ctk.CTkFrame(master=janela_login)
    frame_login.pack(pady=20, padx=40, fill="both", expand=True)

    label_titulo = ctk.CTkLabel(master=frame_login, text="Faça o Login", font=("Roboto", 24, "bold"))
    label_titulo.pack(pady=12, padx=10)

    entry_usuario = ctk.CTkEntry(master=frame_login, placeholder_text="Usuário", width=220)
    entry_usuario.pack(pady=12, padx=10)

    entry_senha = ctk.CTkEntry(master=frame_login, placeholder_text="Senha", show="*", width=220)
    entry_senha.pack(pady=12, padx=10)

    button_login = ctk.CTkButton(master=frame_login, text="Login", command=fazer_login)
    button_login.pack(pady=12, padx=10)

    checkbox_lembrar = ctk.CTkCheckBox(master=frame_login, text="Lembrar-me")
    checkbox_lembrar.pack(pady=12, padx=10)
    
    janela_login.mainloop()

# =============================================================================
# PONTO DE ENTRADA DA APLICAÇÃO
# =============================================================================
if __name__ == "__main__":

    declaracoes_data_inicial = {
    "Declaração 01": "DECLARA que a proposta econômica compreende a integralidade dos custos para atendimento dos direitos trabalhistas assegurados na constituição federal, nas leis trabalhistas, nas normas infralegais, nas convenções coletivas de trabalho e nos termos de ajustamento de conduta vigentes na data de entrega das propostas;",
    "Declaração 02": "DECLARA que cumpre o disposto no inciso XXXIII do art. 7º da Constituição Federal;",
    "Declaração 03": "DECLARA que atende aos requisitos de habilitação.",
    "Declaração 04": "DECLARA sob as penas da lei e para os fins dispostos neste Edital, possuir conhecimento pleno das condições e peculiaridades inerentes à natureza dos serviços;",
    "Declaração 05": "DECLARA que cumpre as exigências de reserva de cargos para pessoa com deficiência e para reabilitado da Previdência Social, previstas em lei e em outras normas específicas",
    "Declaração 06": "DECLARA que não possui em seu quadro societário ou de pessoal agente público do órgão ou entidade licitante ou contratante, nos termos do art. 9º, §1º da Lei 14.133/2021",
    "Declaração 07": "DECLARA que não incorre em qualquer uma das vedações impostas no art. 14 da Lei 14.133/2021 aplicáveis ao objeto da presente licitação",
    "Declaração 08": "DECLARA que atende às disposições da Lei Geral de Proteção de Dados (LGPD);",
    "Declaração 09": "Em atendimento ao Processo Licitatório nº 001/2024, a NM CONSTRUÇÕES E ENGENHARIA LTDA inscrita no CNPJ sob o nº 37.568.597/0001-85 sediada Av. Gov. Agamenon Magalhães, 2936 - Sala 407 - Espinheiro, Recife - PE, 52020-000, por intermédio de sua representante legal a Sra. NATALY SANTOS NASCIMENTO DE MELO, brasileira, solteira, engenheira civil, portadora da cédula de identidade nº 9.291.474 SDS/PE, inscrita no CPF nº 102.860.614-14 e inscrita no CREA/PE nº 181792219-0, dispensou nesta a visita técnica ao e que tem pleno conhecimento das condições e peculiaridades inerentes a natureza dos trabalhos, assumindo total responsabilidade por este fato e informando que não utilizará para quaisquer questionamentos futuros que ensejem avenças técnicas ou financeiras, conforme solicitado neste certame licitatório.",
    "Declaração 10": "Declaramos para os devidos fins que a NM CONSTRUCOES E ENGENHARIA LTDA inscrita no CNPJ sob o nº 37.568.597/0001-85, com sede à Rua Dona Maria César, nº 170, Sala 203, Recife, Recife-PE, possui escrituração contábil regular de acordo com os princípios fundamentais de contabilidade e com as Normas Brasileiras de contabilidade. ",
    "Declaração 11": "A NM CONSTRUÇÕES E ENGENHARIA LTDA, empresa de pequeno porte (EPP), regularmente inscrita no CNPJ sob o nº 37.568.597/0001-85, com sede na Av. Governador Agamenon Magalhães, 2936, Sala 407, Espinheiro, Recife/PE, vem, por meio de sua sócia-administradora e responsável técnica, Nataly Melo, engenheira civil e engenheira de segurança do trabalho, com pós-graduação em engenharia de custos e pós-graduação em gerenciamento de obras, apresentar a presente Declaração de Exequibilidade da proposta apresentada para o processo licitatório em referência",
    "Declaração 12": "Declaramos que nos preços cotados estão incluídas todas as despesas que, direta ou indiretamente, fazem parte do presente objeto, tais como gastos da empresa com suporte técnico e administrativo, impostos, seguros, taxas, ou quaisquer outros que possam incidir sobre gastos da empresa, sem quaisquer acréscimos em virtude de expectativa inflacionária e deduzidos os descontos eventualmente concedidos.",
    "Declaração 13": "Declaramos que estamos de pleno acordo com todas as condições estabelecidas no Edital e seus Anexos."
    }

    db.inicializar_db(declaracoes_data_inicial)

    ctk.set_appearance_mode("light") 
    ctk.set_default_color_theme("blue")
    # Você pode reativar sua tela de login se quiser, ela já chama a 'abrir_janela_principal'
    #criar_janela_login() 
    abrir_janela_principal() # Para testar diretamente a janela principal