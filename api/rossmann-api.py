import pandas as pd
import json
import requests
from flask import Flask, request, Response
import os

#constants
TOKEN = '6493569937:AAF_tjVyzyCVG_Sw1Smw7AjFC4uqhlmqpWc'

# Informações do BOT
# https://api.telegram.org/bot6493569937:AAF_tjVyzyCVG_Sw1Smw7AjFC4uqhlmqpWc/getMe

# Get Updates
# https://api.telegram.org/bot6493569937:AAF_tjVyzyCVG_Sw1Smw7AjFC4uqhlmqpWc/getUpdates

# enviar mensagem
# https://api.telegram.org/bot6493569937:AAF_tjVyzyCVG_Sw1Smw7AjFC4uqhlmqpWc/sendMessage?chat_id=840661273&text=Oi Usuario, to bem demais!

# webhook
# https://api.telegram.org/bot6493569937:AAF_tjVyzyCVG_Sw1Smw7AjFC4uqhlmqpWc/setWebhook?url=https://0c7a9df79114bb.lhr.life

# send message
def enviar_mensagens(chat_id, text ):
    url = 'https://api.telegram.org/bot{}/'.format(TOKEN)
    url = url + 'sendMessage?chat_id={}/'.format(chat_id)

    r = requests.post(url, json={'text' : text})
    print('Status Code {}'.format( r.status_code ) )    

    return None


def carregar(store_id):
# carregar o dataset de teste
    df10 = pd.read_csv( "../datasets/test.csv", low_memory=False )
    df_store_raw = pd.read_csv( '../datasets/store.csv', low_memory=False )

    # merge test dataset + store
    df_test = pd.merge( df10, df_store_raw, how='left', on='Store' )

    # choose store for prediction
    df_test = df_test[df_test['Store'] == store_id ]

    if not df_test.empty:
        # remove closed days
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop( 'Id', axis=1 )

        # convert Dataframe to json
        data = json.dumps( df_test.to_dict( orient='records' ) )

    else:
        data = 'error'
        
    return data

def predict(data):

    #url = 'https://rossmann-api-h4ab.onrender.com/rossmann/predict'
    url = 'https://arss-rossmann-api.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    data = data

    r = requests.post(url, data = data, headers = header)
    print('Status Code {}' .format(r.status_code))

    d1 = pd.DataFrame( r.json(), columns=r.json()[0].keys()  )

    return d1


def analisar_mensagem( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']

    store_id = store_id.replace( '/', '' )

    try:
        store_id = int( store_id )
    
    except ValueError:
        store_id = 'error'
    
    return chat_id, store_id

# API initialize
app = Flask( __name__ )

@app.route( '/', methods=['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()
                
        chat_id, store_id = analisar_mensagem( message )
        
        if store_id != 'error':
            # loading data
            data = carregar( store_id )

            if data != 'error':
                # prediction
                d1 = predict( data )

                # calculate
                d2 = d1[['store', 'prediction']].groupby( 'store' ).sum().reset_index()
                
                # send message    
                msg = f"A Loja {d2['store'].values[0]} deverá vender R$ {d2['prediction'].values[0]:,.2f} nas próximas 6 semanas."
                
                enviar_mensagens ( chat_id, msg )
                return Response( 'OK', status=200 )
            
            else:
                enviar_mensagens ( chat_id, 'Loja não Encontrada')
                return Response( 'OK', status=200 )
            
        else:
            enviar_mensagens ( chat_id, 'Este não é um ID de Loja válido.')
            return Response( 'OK', status=200 )
    else:
        return '<h1> Telegram BOT de previsão de vendas das lojas Rossmann</h1>'

if __name__ == '__main__':
    port = os.environ.get( 'PORT', 10000 )
    app.run( host='0.0.0.0', port=port )
