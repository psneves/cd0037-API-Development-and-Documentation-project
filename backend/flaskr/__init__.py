from flask import Flask, request, abort, jsonify
from flask_cors import CORS
import random

from models import setup_db, Question, Category, db

QUESTIONS_PER_PAGE = 10

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)
    """
    CORS Setup - Allow '*' for origins.
    """
    CORS(app, resources={r"/*": {"origins": "*"}})

    with app.app_context():
        db.create_all()

    """
    Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,true")
        response.headers.add("Access-Control-Allow-Methods", "GET,PUT,POST,DELETE,OPTIONS")
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

    """
    GET /categories 
    Endpoint to handle GET requests for all available categories.
    """
    @app.route('/categories', methods=['GET'])
    def get_categories():
        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        if len(formatted_categories) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'categories': formatted_categories
        })


    """    
    GET /questions
    Endpoint to handle GET requests for questions, including pagination (every 10 questions).
    This endpoint should return a list of questions, number of total questions, current category, categories.
    """
    @app.route('/questions', methods=['GET'])
    def get_questions():
        page = request.args.get('page', 1, type=int)
        start = (page - 1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = Question.query.all()
        formatted_questions = [question.format() for question in questions]
        current_questions = formatted_questions[start:end]

        categories = Category.query.all()
        formatted_categories = {category.id: category.type for category in categories}

        if len(current_questions) == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(formatted_questions),
            'current_category': None,
            'categories': formatted_categories
        })

    """
    An endpoint to DELETE question using a question ID.
    """
    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.get(question_id)
            if question is None:
                abort(404)

            question.delete()
            return jsonify({
                'success': True,
                'deleted': question_id
            })

        except:
            abort(422)

    """
    An endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.
    Also, endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.
    """
    @app.route('/questions', methods=['POST'])
    def add_question():
        body = request.get_json()

        question = body.get('question', None)
        answer = body.get('answer', None)
        difficulty = body.get('difficulty', None)
        category = body.get('category', None)
        searchTerm = body.get('searchTerm', None)

        if searchTerm is not None:
            questions = Question.query.filter(Question.question.ilike(f'%{searchTerm}%')).all()
            formatted_questions = [question.format() for question in questions]

            return jsonify({
                'success': True,
                'questions': formatted_questions,
                'total_questions': len(formatted_questions),
                'current_category': None
            })
        elif question is None or answer is None or category is None or difficulty is None:
            abort(400)

        try:
            question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
            question.insert()

            return jsonify({
                'success': True,
                'created': question.id
            })

        except:
            abort(422)

    """
    Endpoint to get questions based on category.
    """
    @app.route('/categories/<int:category_id>/questions', methods=['GET'])
    def get_questions_by_category(category_id):
        category = Category.query.get(category_id)
        if category is None:
            abort(404)

        questions = Question.query.filter_by(category=category_id).all()
        formatted_questions = [question.format() for question in questions]

        return jsonify({
            'success': True,
            'questions': formatted_questions,
            'total_questions': len(formatted_questions),
            'current_category': category.type
        })


    """
    Endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.
    """
    @app.route('/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()

        previous_questions = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', None)

        if quiz_category is None:
            abort(400)

        if quiz_category['id'] == 0:
            questions = Question.query.filter(Question.id.notin_(previous_questions)).all()
        else:
            category_filter = int(quiz_category['id'])
            questions = Question.query.filter_by(category=category_filter).filter(Question.id.notin_(previous_questions)).all()

        if len(questions) == 0:
            return jsonify({
                'success': True,
                'question': None
            })

        question = random.choice(questions).format()

        return jsonify({
            'success': True,
            'question': question
        })


    # Error Handling
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "error": 404, "message": "Not found"}), 404
    
    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"success": False, "error": 422, "message": "Unprocessable"}), 422
    
    @app.errorhandler(400)
    def unprocessable(error):
        return jsonify({"success": False, "error": 400, "message": "Bad response"}), 400
    
    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({"success": False, "error": 405, "message": "Method not allowed"}), 405

    return app

