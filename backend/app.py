from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:hotside775@localhost:5432/votufacil'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ========================
# MODELOS
# ========================

class Usuario(db.Model):
    __tablename__ = 'usuario'
    id_usuario = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    tipo_perfil = db.Column(db.String(20), nullable=False)

class Categoria(db.Model):
    __tablename__ = 'categoria'
    id_categoria = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False)

class LocalServico(db.Model):
    __tablename__ = 'local_servico'
    id_local = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    endereco = db.Column(db.String(200))
    telefone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    id_responsavel = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))

class HorarioFuncionamento(db.Model):
    __tablename__ = 'horario_funcionamento'
    id_horario = db.Column(db.Integer, primary_key=True)
    dia_semana = db.Column(db.String(20))
    horario_abertura = db.Column(db.String(10))
    horario_fechamento = db.Column(db.String(10))
    tipo_horario = db.Column(db.String(20))
    id_local = db.Column(db.Integer, db.ForeignKey('local_servico.id_local'))

class Comentario(db.Model):
    __tablename__ = 'comentario'
    id_comentario = db.Column(db.Integer, primary_key=True)
    texto_comentario = db.Column(db.Text)
    data_comentario = db.Column(db.Date)
    status = db.Column(db.String(20))
    id_usuario = db.Column(db.Integer, db.ForeignKey('usuario.id_usuario'))
    id_local = db.Column(db.Integer, db.ForeignKey('local_servico.id_local'))

# ========================
# ROTAS — USUÁRIOS
# ========================

@app.route('/usuarios/cadastro', methods=['POST'])
def cadastrar_usuario():
    dados = request.get_json()
    if Usuario.query.filter_by(email=dados['email']).first():
        return jsonify({'erro': 'Email já cadastrado!'}), 400
    novo_usuario = Usuario(
        nome=dados['nome'],
        email=dados['email'],
        senha_hash=generate_password_hash(dados['senha']),
        tipo_perfil=dados.get('tipo_perfil', 'usuario')
    )
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({'mensagem': 'Usuário cadastrado com sucesso!', 'id': novo_usuario.id_usuario}), 201

@app.route('/usuarios/login', methods=['POST'])
def login():
    dados = request.get_json()
    usuario = Usuario.query.filter_by(email=dados['email']).first()
    if not usuario or not check_password_hash(usuario.senha_hash, dados['senha']):
        return jsonify({'erro': 'Email ou senha incorretos!'}), 401
    return jsonify({
        'mensagem': 'Login realizado com sucesso!',
        'id': usuario.id_usuario,
        'nome': usuario.nome,
        'tipo_perfil': usuario.tipo_perfil
    })

@app.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    return jsonify([{
        'id': u.id_usuario,
        'nome': u.nome,
        'email': u.email,
        'tipo_perfil': u.tipo_perfil
    } for u in usuarios])

# ========================
# ROTAS — LOCAIS
# ========================

@app.route('/locais', methods=['GET'])
def listar_locais():
    locais = LocalServico.query.all()
    return jsonify([{
        'id': local.id_local,
        'nome': local.nome,
        'descricao': local.descricao,
        'endereco': local.endereco,
        'telefone': local.telefone,
        'latitude': local.latitude,
        'longitude': local.longitude
    } for local in locais])

@app.route('/locais/<int:id>', methods=['GET'])
def detalhe_local(id):
    local = LocalServico.query.get_or_404(id)
    return jsonify({
        'id': local.id_local,
        'nome': local.nome,
        'descricao': local.descricao,
        'endereco': local.endereco,
        'telefone': local.telefone,
        'email': local.email,
        'latitude': local.latitude,
        'longitude': local.longitude
    })

@app.route('/locais', methods=['POST'])
def cadastrar_local():
    dados = request.get_json()
    novo_local = LocalServico(
        nome=dados['nome'],
        descricao=dados.get('descricao'),
        endereco=dados.get('endereco'),
        telefone=dados.get('telefone'),
        email=dados.get('email'),
        latitude=dados.get('latitude'),
        longitude=dados.get('longitude')
    )
    db.session.add(novo_local)
    db.session.flush()
    for h in dados.get('horarios', []):
        db.session.add(HorarioFuncionamento(
            dia_semana=h['dia_semana'],
            horario_abertura=h['horario_abertura'],
            horario_fechamento=h['horario_fechamento'],
            tipo_horario=h.get('tipo_horario', 'normal'),
            id_local=novo_local.id_local
        ))
    db.session.commit()
    return jsonify({'mensagem': 'Local cadastrado com sucesso!', 'id': novo_local.id_local}), 201

@app.route('/locais/<int:id>', methods=['PUT'])
def atualizar_local(id):
    local = LocalServico.query.get_or_404(id)
    dados = request.get_json()
    local.nome = dados.get('nome', local.nome)
    local.descricao = dados.get('descricao', local.descricao)
    local.endereco = dados.get('endereco', local.endereco)
    local.telefone = dados.get('telefone', local.telefone)
    local.email = dados.get('email', local.email)
    local.latitude = dados.get('latitude', local.latitude)
    local.longitude = dados.get('longitude', local.longitude)
    if 'horarios' in dados:
        HorarioFuncionamento.query.filter_by(id_local=id).delete()
        for h in dados['horarios']:
            db.session.add(HorarioFuncionamento(
                dia_semana=h['dia_semana'],
                horario_abertura=h['horario_abertura'],
                horario_fechamento=h['horario_fechamento'],
                tipo_horario=h.get('tipo_horario', 'normal'),
                id_local=id
            ))
    db.session.commit()
    return jsonify({'mensagem': 'Local atualizado com sucesso!'})

@app.route('/locais/<int:id>', methods=['DELETE'])
def deletar_local(id):
    HorarioFuncionamento.query.filter_by(id_local=id).delete()
    local = LocalServico.query.get_or_404(id)
    db.session.delete(local)
    db.session.commit()
    return jsonify({'mensagem': 'Local removido com sucesso!'})

# ========================
# ROTAS — HORÁRIOS
# ========================

@app.route('/locais/<int:id>/horarios', methods=['GET'])
def listar_horarios(id):
    horarios = HorarioFuncionamento.query.filter_by(id_local=id).all()
    return jsonify([{
        'id': h.id_horario,
        'dia_semana': h.dia_semana,
        'horario_abertura': h.horario_abertura,
        'horario_fechamento': h.horario_fechamento,
        'tipo_horario': h.tipo_horario
    } for h in horarios])

@app.route('/locais/<int:id>/horarios', methods=['POST'])
def adicionar_horario(id):
    dados = request.get_json()
    novo = HorarioFuncionamento(
        dia_semana=dados['dia_semana'],
        horario_abertura=dados['horario_abertura'],
        horario_fechamento=dados['horario_fechamento'],
        tipo_horario=dados.get('tipo_horario', 'normal'),
        id_local=id
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'mensagem': 'Horário adicionado!', 'id': novo.id_horario}), 201

@app.route('/horarios/<int:id>', methods=['DELETE'])
def deletar_horario(id):
    horario = HorarioFuncionamento.query.get_or_404(id)
    db.session.delete(horario)
    db.session.commit()
    return jsonify({'mensagem': 'Horário removido!'})

# ========================
# ROTAS — CATEGORIAS
# ========================

@app.route('/categorias', methods=['GET'])
def listar_categorias():
    categorias = Categoria.query.all()
    return jsonify([{'id': c.id_categoria, 'nome': c.nome} for c in categorias])

@app.route('/categorias', methods=['POST'])
def cadastrar_categoria():
    dados = request.get_json()
    nova = Categoria(nome=dados['nome'])
    db.session.add(nova)
    db.session.commit()
    return jsonify({'mensagem': 'Categoria criada!', 'id': nova.id_categoria}), 201

# ========================
# ROTAS — COMENTÁRIOS
# ========================

@app.route('/locais/<int:id>/comentarios', methods=['GET'])
def listar_comentarios(id):
    comentarios = Comentario.query.filter_by(id_local=id).all()
    return jsonify([{
        'id': c.id_comentario,
        'texto': c.texto_comentario,
        'data': str(c.data_comentario),
        'status': c.status
    } for c in comentarios])

@app.route('/locais/<int:id>/comentarios', methods=['POST'])
def cadastrar_comentario(id):
    dados = request.get_json()
    novo = Comentario(
        texto_comentario=dados['texto'],
        data_comentario=date.today(),
        status='pendente',
        id_usuario=dados.get('id_usuario'),
        id_local=id
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'mensagem': 'Comentário enviado!'}), 201

# ========================
# INÍCIO
# ========================

@app.route('/')
def inicio():
    return 'VotuFácil - Back-end conectado ao banco! 🚀'

if __name__ == '__main__':
    app.run(debug=True)