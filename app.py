from flask import Flask, jsonify, request
from flasgger import Swagger, LazyString, LazyJSONEncoder
from flasgger import swag_from
import pandas as pd
import sqlite3

app = Flask(__name__)

#Swagger 
app.json_encoder = LazyJSONEncoder
swagger_template = dict(
    info = {
        'title': LazyString(lambda:'API Documentation for Data Processing and Modeling'),
        'version': LazyString(lambda:'1.0.0'),
        'description': LazyString(lambda:'Dokumentasi API untuk Data Processing dan Modeling')
        }, host = LazyString(lambda: request.host)
    )
swagger_config = {
        "headers":[],
        "specs":[
            {
            "endpoint":'docs',
            "route":'/docs.json'
            }
        ],
        "static_url_path":"/flasgger_static",
        "swagger_ui":True,
        "specs_route":"/docs/"
    }
swagger = Swagger(app, template=swagger_template, config=swagger_config)

#koneksi ke databases

conn = sqlite3.connect('gold.db')
#ambil data tweet
query = ''' select * from tweet '''
#read sql to dataframe
df = pd.read_sql_query(query, conn)
#funsion frame df
def frame(df):
    df_abusive = pd.read_csv('abusive.csv')
    df_get = df.copy()
    list_abusive = df_abusive['ABUSIVE'].str.lower().tolist()
    list_old = df_get['Tweet'].str.lower().tolist()
    for i in list_old:
        for j in list_abusive:
            if j in i:
                k = list_old[list_old.index(i)].replace(j,'***')
                list_old[list_old.index(i)] = k
                i = k
    list_old = pd.Series(list_old)
    list_old= pd.DataFrame(list_old,columns =['new'])
    df_get['new'] = list_old['new'].str.lower()
    
    json = df_get.to_dict(orient='index')

    return json
#flask get dan swagger untuk tampil
@swag_from("docs/index.yml", methods=['GET'])
@app.route('/', methods=['GET'])
def test():
	return jsonify({'message' : 'It works!'})

@swag_from("docs/index.yml", methods=['GET'])
@app.route('/lang', methods=['GET'])
def returnAll():

    json = frame(df)

    return jsonify(json)

#flask dan swagger untuk mengambil data id
@swag_from("docs/lang_get.yml", methods=['GET'])
@app.route('/lang/<id>', methods=['GET'])
def returnOne(id):
    
    df_get = df.filter(items = [int(id)], axis=0)

    json = frame(df_get)

    return jsonify(json)

#flask swagger untuk upload
@swag_from("docs/lang_post.yml", methods=['POST'])
@app.route('/lang', methods=['POST'])
def addOne():
    old = {'Tweet': request.json['Tweet']}
    df.loc[len(df) + 1] = [max(df['index'])+1, old['Tweet']]
    df.index = df['index']
   
    json = frame(df.tail(1))


    return  jsonify(json)

@swag_from("docs/lang_upload.yml", methods=['POST'])
@app.route('/lang/upload', methods=['POST'])
def addUpload():
    file = request.files['file']
    try:
        data = pd.read_csv(file, encoding='iso-8859-1')
    except:
        data = pd.read_csv(file, encoding='utf-8')
    
    for i in range(0,len(data)):
        df.loc[len(df) + 1] = [max(df['index'])+1, data['Tweet'][i]]

    json = frame(df.tail(len(data)))

    return  jsonify(json)


if __name__ == "__main__":
    app.run()