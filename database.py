import sqlite3
import os

DB_FILE = "declaracoes.db"

def conectar_db():
    """Cria uma conexão com o banco de dados."""
    return sqlite3.connect(DB_FILE)

def inicializar_db(dados_iniciais=None):
    """
    Cria a tabela de declarações se ela não existir.
    Se o banco de dados for novo e dados iniciais forem fornecidos,
    popula a tabela com eles.
    """
    db_novo = not os.path.exists(DB_FILE)

    conn = conectar_db()
    cursor = conn.cursor()
    
    # Cria a tabela
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS declaracoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL UNIQUE,
        texto TEXT NOT NULL
    )
    """)
    
    # Se o banco de dados acabou de ser criado, popula com os dados iniciais
    if db_novo and dados_iniciais:
        print("Banco de dados novo. Populando com dados iniciais...")
        for titulo, texto in dados_iniciais.items():
            try:
                cursor.execute("INSERT INTO declaracoes (titulo, texto) VALUES (?, ?)", (titulo, texto))
            except sqlite3.IntegrityError:
                print(f"Aviso: Título '{titulo}' já existe. Pulando inserção inicial.")
    
    conn.commit()
    conn.close()

def ler_todas_declaracoes():
    """Lê todas as declarações do banco de dados e retorna como um dicionário."""
    conn = conectar_db()
    # Usamos um dict_factory para facilitar o manuseio dos dados
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, titulo, texto FROM declaracoes ORDER BY titulo ASC")
    rows = cursor.fetchall()
    conn.close()
    
    # Converte o resultado para um dicionário de dicionários para fácil acesso
    return {row['titulo']: {'id': row['id'], 'texto': row['texto']} for row in rows}

def atualizar_declaracao(dec_id, novo_titulo, novo_texto):
    """Atualiza o título e o texto de uma declaração existente."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("UPDATE declaracoes SET titulo = ?, texto = ? WHERE id = ?", (novo_titulo, novo_texto, dec_id))
    conn.commit()
    conn.close()
    print(f"Declaração ID {dec_id} atualizada.")

def adicionar_declaracao(titulo, texto):
    """
    Adiciona uma nova declaração ao banco de dados.
    Retorna True se foi bem-sucedido, False se o título já existe.
    """
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        # Tenta inserir a nova declaração
        cursor.execute("INSERT INTO declaracoes (titulo, texto) VALUES (?, ?)", (titulo, texto))
        conn.commit()
        print(f"Nova declaração '{titulo}' adicionada.")
        return True # Sucesso!
    except sqlite3.IntegrityError:
        # Este erro acontece se o título já existir (devido à restrição UNIQUE)
        print(f"Erro de integridade: O título '{titulo}' já existe.")
        return False # Falha!
    finally:
        # Garante que a conexão seja sempre fechada, não importa o que aconteça.
        conn.close()

def excluir_declaracao(dec_id):
    """Exclui uma declaração do banco de dados pelo seu ID."""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM declaracoes WHERE id = ?", (dec_id,))
    conn.commit()
    conn.close()
    print(f"Declaração ID {dec_id} excluída.")