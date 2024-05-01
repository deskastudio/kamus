import os
from posixpath import dirname, join
from bson import ObjectId
from flask import (
    Flask,
    app, 
    request, 
    render_template, 
    redirect, 
    url_for, 
    jsonify
)
from pymongo import MongoClient
import requests
from datetime import datetime

from dotenv import load_dotenv

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

MONGODB_URL = os.environ.get("MONGODB_URL")
DB_NAME =  os.environ.get("DB_NAME")

client = MongoClient(MONGODB_URL)
db = client[DB_NAME]

@app.route('/')
def main():
    words_result = db.words.find({}, {'_id': False})
    words = []
    for word in words_result:
        definitions = word['definitions'][0]['shortdef']
        definitions = definitions if type(definitions) is str else definitions [0]
        words.append ({
            'word': word['word'],
            'definitions': definitions
        })
    
    msg = request.args.get('msg')
    return render_template('index.html', words=words, msg=msg)

@app.route('/detail/<keyword>')
def detail(keyword):
    api_key = "3eff3c25-b3ba-418e-b87a-bbf404471031"
    url = f'https://www.dictionaryapi.com/api/v3/references/collegiate/json/{keyword}?key={api_key}'
    response = requests.get(url)
    definitions = response.json()
    
    if not definitions:
        return redirect(url_for('not_found'))
        
    if type(definitions[0]) is str:
        suggestions = definitions
        return render_template('not_found.html', suggestions=suggestions)
        
    status = request.args.get('status_give', 'new')
    return render_template(
        'detail.html', 
        word=keyword,
        definitions=definitions,
        status=status
    )

@app.route('/api/save_word', methods=['POST'])
def save_word():
    json_data = request.get_json()
    word = json_data.get('word_give')
    definitions = json_data.get('definitions_give')
    doc = {
        'word': word,
        'definitions': definitions,
        'date': datetime.now().strftime('%Y-%m-%d'),
    }
    db.words.insert_one(doc)
    return jsonify({
        'result': 'success',
        'msg': f'the word, {word}, was saved!!!',
    })
    
@app.route('/api/delete_word', methods=['POST'])
def delete_word():
    word = request.form.get('word_give')
    # Hapus kata dari koleksi words
    db.words.delete_one({'word': word})
    # Hapus contoh dari koleksi examples yang terkait dengan kata yang dihapus
    db.examples.delete_many({'word': word})
    return jsonify({
        'result': 'success',
        'msg': f'the word {word} was deleted along with its examples'
    })
    
@app.route('/api/get_exs', methods=['GET'])
def get_exs():
    word = request.args.get('word')
    example_data = db.examples.find({'word':word})
    examples = []
    for example in example_data:
        examples.append({
            'example':example.get('example'),
            'id':str(example.get('_id')),
        })
    return jsonify({
        'result':'success',
        'examples':examples,
        })

@app.route('/api/save_ex', methods=['POST'])
def save_exs():
    word = request.form.get('word')
    example = request.form.get('example')
    doc={
        'word':word,
        'example':example
    }
    db.examples.insert_one(doc)
    return jsonify({
        'result':'success',
        'msg':f'{example} anda sudah disimpan dengan kata {word}'
        })

@app.route('/api/delete_ex', methods=['POST'])
def delete_exs():
    id = request.form.get('id')
    word = request.form.get('word')
    db.examples.delete_one({'_id':ObjectId(id)})
    return jsonify({
        'result':'success',
        'msg':f'Your examaaple for the word {word} kamu sudah dihapus'})

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
