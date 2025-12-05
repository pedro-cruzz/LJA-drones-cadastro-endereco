from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.models import Usuario, Solicitacao

# Print para confirmar que o servidor recarregou este arquivo
print("--- ROTAS CARREGADAS COM SUCESSO ---")

bp = Blueprint('main', __name__)

# --- Context Processor: Simula o 'current_user' para o HTML ---
@bp.context_processor
def inject_user():
    class MockUser:
        is_authenticated = 'user_id' in session
        name = session.get('user_nome')
        id = session.get('user_id')
        role = session.get('user_tipo')
    return dict(current_user=MockUser())

# --- DASHBOARD UVIS (Visão da Unidade) ---
@bp.route('/')
def dashboard():
    # 1. Login obrigatório
    if 'user_id' not in session:
        return redirect(url_for('main.login'))
    
    # 2. Se for admin, manda para o painel de admin
    if session.get('user_tipo') == 'admin':
        return redirect(url_for('main.admin_dashboard'))

    # 3. Busca apenas solicitações do próprio usuário logado
    user_id = session.get('user_id')
    lista_solicitacoes = Solicitacao.query.filter_by(usuario_id=user_id).order_by(Solicitacao.data_criacao.desc()).all()
    
    return render_template('dashboard.html', nome=session.get('user_nome'), solicitacoes=lista_solicitacoes)

# --- PAINEL ADMIN (Visualizar Pedidos) ---
@bp.route('/admin')
def admin_dashboard():
    # Verifica se é admin mesmo
    if 'user_id' not in session or session.get('user_tipo') != 'admin':
        return redirect(url_for('main.login'))

    # Busca TODOS os pedidos do banco (para o admin ver tudo)
    todos_pedidos = Solicitacao.query.order_by(Solicitacao.data_criacao.desc()).all()
    
    return render_template('admin.html', pedidos=todos_pedidos)

# --- ROTA DE ATUALIZAÇÃO (Salvar dados do Admin) ---
@bp.route('/admin/atualizar/<int:id>', methods=['POST'])
def atualizar(id):
    if session.get('user_tipo') != 'admin':
        return redirect(url_for('main.login'))
    
    # Pega o pedido no banco
    pedido = Solicitacao.query.get_or_404(id)
    
    # Atualiza com os dados vindos do formulário do Admin
    pedido.coords = request.form.get('coords')
    pedido.protocolo = request.form.get('protocolo')
    pedido.status = request.form.get('status')
    pedido.justificativa = request.form.get('justificativa')
    
    db.session.commit()
    flash(f'Pedido atualizado com sucesso!', 'success')
    
    return redirect(url_for('main.admin_dashboard'))

# --- NOVO PEDIDO (Cadastro da UVIS) ---
@bp.route('/novo_cadastro', methods=['GET', 'POST'], endpoint='novo')
def novo():
    if 'user_id' not in session:
        return redirect(url_for('main.login'))

    if request.method == 'POST':
        try:
            nova_solicitacao = Solicitacao(
                data_agendamento=request.form.get('data'),
                hora_agendamento=request.form.get('hora'),
                endereco=request.form.get('endereco'),
                foco=request.form.get('foco'),
                usuario_id=session['user_id'], # Vincula ao usuário logado
                status='EM ANÁLISE'
            )
            db.session.add(nova_solicitacao)
            db.session.commit()
            flash('Pedido enviado para análise!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            flash(f"Erro ao salvar: {e}", "danger")

    return render_template('cadastro.html')

# --- LOGIN ---
@bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já logado, redireciona
    if 'user_id' in session:
        if session.get('user_tipo') == 'admin':
            return redirect(url_for('main.admin_dashboard'))
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        user = Usuario.query.filter_by(login=request.form.get('login')).first()

        if user and user.check_senha(request.form.get('senha')):
            session['user_id'] = user.id
            session['user_nome'] = user.nome_uvis
            session['user_tipo'] = user.tipo_usuario
            
            # Redirecionamento Inteligente
            if user.tipo_usuario == 'admin':
                return redirect(url_for('main.admin_dashboard'))
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login incorreto.', 'danger')

    return render_template('login.html')

# --- LOGOUT ---
@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.login'))