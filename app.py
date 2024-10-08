from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from models.user import User
from models.diet import Diet
from database import db
from datetime import datetime
import bcrypt


app = Flask(__name__)
app.config['SECRET_KEY'] = "my_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:admin123@127.0.0.1:3306/Daily-diet'

jwt = JWTManager(app)

login_manager = LoginManager()
db.init_app(app)
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)
 

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        user = User.query.filter_by(username=username).first()

        if user and bcrypt.checkpw(str.encode(password), str.encode(user.password)):
            access_token = create_access_token(identity=user.id)
            login_user(user)
            print(current_user.is_authenticated)
            return jsonify({"message": "Logado","id": user.id, "token": access_token})
    
    return jsonify({"message": "Credenciais invalidas"}), 400

@app.route('/logout', methods=['GET'])
@login_required
def logout():

    logout_user()
    return jsonify({"message": "Logout realizado!"})

@app.route('/user', methods=['POST'])
def create_user():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if username and password:
        hashed_password = bcrypt.hashpw(str.encode(password), bcrypt.gensalt())
        user = User(username=username, password=hashed_password, role='user')
        db.session.add(user)
        db.session.commit()
        return jsonify({"message": "Cadastrado", "id": user.id})

    return jsonify({"message": "Dados invalidas"}), 400

@app.route('/user/<int:id_user>', methods=['GET'])
@login_required
def read_user(id_user):
    user = User.query.get(id_user)
    
    if user:
        return {"username": user.username}
    
    return jsonify({"message": "Usuário não encontrado"}), 404

@app.route('/user/<int:id_user>', methods=['PUT'])
@login_required
def update_user(id_user):
    data = request.json
    user = User.query.get(id_user)

    if id_user != current_user.id and current_user.role == "user":
        return jsonify({"message": "Não permitido"}), 403
    
    if user and data.get("password"):
        hashed_password = bcrypt.hashpw(str.encode(data.get("password")), bcrypt.gensalt())
        user.password = hashed_password
        db.session.commit()
        
        return jsonify({"message": f"senha do uário {user.id} atualizado"})
    
    return jsonify({"message": "Usuário não encontrado"}), 404

@app.route('/user/<int:id_user>', methods=['DELETE'])
@login_required
def delete_user(id_user):
    user = User.query.get(id_user)

    if current_user.role == "user":
        return jsonify({"message": "Acesso não permitido"}),403

    if id_user == current_user.id:
        return jsonify({"message": f"Usuário {user.username} está logado e não pode ser excluido"}), 403

    if user:
        db.session.delete(user)
        db.session.commit()
        return jsonify({"message": f"Usuárioário {user.id} Deletado"})
    
    return jsonify({"message": f"Usuário {user.username} não encontrado"}),404

@app.route('/diet', methods=['POST'])
@login_required
#@jwt_required
def create_diet():
    data = request.json
    title = data.get("title")
    description = data.get("description")
    consistent_diet = data.get("consistent_diet", True)

    if title and description:
        diet = Diet( user_id=current_user.id, title=title, description=description, consistent_diet=consistent_diet)
        db.session.add(diet)
        db.session.commit()
        return jsonify({"message": "Dieta cadastrada", "id": diet.id})

    return jsonify({"message": "Dados incompletos"}), 400

@app.route('/diet/<int:id_diet>', methods=['PUT'])
@login_required
def update_diet(id_diet):
    data = request.json
    diet = Diet.query.get(id_diet)

    if current_user.id == diet.user_id:
        diet.title = data.get("title")
        diet.description = data.get("description")
        diet.date_time = datetime.fromisoformat(data.get("date"))
        diet.consistent_diet = data.get("consistent_diet")
        db.session.commit()
        return jsonify({"message": f"Dieta foi alterada"})
    
    return jsonify({"message": "Não permitido: Usuário não é dono da dieta"}), 403

@app.route('/diet/<int:id_diet>', methods=['DELETE'])
@login_required
def delete_diet(id_diet):
    diet = Diet.query.get(id_diet)

    if current_user.id == diet.user_id:
        db.session.delete(diet)
        db.session.commit()    
        return jsonify({"message": f"Dieta {diet.title} Deletada"})
    
    return jsonify({"message": "Não permitido: Usuário não é dono da dieta"}), 403
    
@app.route('/diet/<int:id_diet>', methods=['GET'])
@login_required
def read_diet(id_diet):
    diet = Diet.query.get(id_diet)
    
    if current_user.id == diet.user_id:
        return jsonify({"titulo": diet.title, "Descrição": diet.description, "Data e Hora": diet.date_time, "Dentro da dieta?": diet.consistent_diet})
    
    return jsonify({"message": "Não permitido: Usuário não é dono da dieta"}), 403

@app.route('/diets/<int:id_user>', methods=['GET'])
@login_required
def read_diets(id_user):
    diets = Diet.query.filter_by(user_id=id_user).all()
    
    diets_list = []

    for diet in diets:
        diets_list.append({"titulo": diet.title, "Descrição": diet.description, "Data e Hora": diet.date_time,"Dentro da dieta?": diet.consistent_diet})

    if not diets_list:
        return jsonify({"message": "Não tem dietas"}), 404
        
    return  jsonify({"message": diets_list})
    

if __name__ == '__main__':
    app.run(debug=True)
    