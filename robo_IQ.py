"""
Esse codigo é um robô que faz operações no IQ Option usando a estrategia MHI

By: George Telles
+55 11 93290-7425
"""

from iqoptionapi.stable_api import IQ_Option
import time
from configobj import ConfigObj
import json,sys
from datetime import datetime


caminho_arquivo = r'G:\Meu Drive\2. Documentos\dock\Finance\1 - RoboIQ\config.txt'
config = ConfigObj(caminho_arquivo)

email = config["LOGIN"]["email"]
senha = config["LOGIN"]["senha"]

tipo = config["AJUSTES"]["tipo"]
valor_entrada = float(config["AJUSTES"]["valor_entrada"])

stop_win = float(config["AJUSTES"]["stop_win"])
stop_loss = float(config["AJUSTES"]["stop_loss"])

lucro_total = 0
stop = True

if config["MARTINGALE"]["usar_martingale"] == "S":
    martingale = int(config["MARTINGALE"]["niveis_martingale"])
else:
    martingale = 0

fator_mg = float(config["MARTINGALE"]["fator_martingale"])


print("Iniciando conexão com a IQ Option...")
API = IQ_Option(email,senha)

#conectando
check, reason = API.connect()
if check:
    print("\nConectado com sucesso")
else:
    print("Houve um problema na conexão")
    print(reason)
    sys.exit()

#DEMO OU REAL
while True:
    escolha = input("Selecione a conta em que desaja conectar: demo ou real: ")
    if escolha == "demo":
        conta = "PRACTICE"
        print("Conta demo selecionada")
        break
    if escolha == "real":
        conta = "REAL"
        print("Conta REAL selecionada")
        break
    else:
        print("Escolha uma opção válida, digite demo ou real!")

API.change_balance(conta)

#função para checar stop
def check_stop():
    global stop, lucro_total
    if lucro_total <= float("-"+str(abs(stop_loss))):
        stop = False
        print(f"\n##################################")
        print(f"STOP LOSS BATIDO", {str(cifrao),str(lucro_total)})
        sys.exit()

    if lucro_total >= float(str(abs(stop_win))):
        stop = False
        print(f"\n##################################")
        print(f"TAKE PROFIT BATIDO", {str(cifrao),str(lucro_total)})
        sys.exit()
        

#ABRIR ORDENS
def compra(ativo,entrada,direcao,exp,tipo):
    global stop, lucro_total

    entrada = valor_entrada
    for i in range(martingale + 1):
        if stop == True:
            if tipo == "digital":
                check, id = API.buy_digital_spot_v2(ativo,entrada,direcao,exp)
            else:
                check, id = API.buy(entrada,ativo,direcao,exp)

            if check:
                if i == 0:
                    print(f"Ordem Executada\nPar: {ativo}\nExpiração: {exp}\nEntrada de:{cifrao}{entrada}")
                if i >= 1:
                    print(f"Ordem Executada com martingale {i}\nPar: {ativo}\nExpiração: {exp}\nEntrada de:{cifrao}{entrada}")

                while True:
                    time.sleep(0.1)
                    status, resultado = API.check_win_digital_v2(id) if tipo == "digital" else API.check_win_v4(id)

                    if status:
                        lucro_total += round(resultado,2)
                        if resultado > 0:
                            if i == 0:
                                print("Resultado: WIN\nLucro:", round(resultado,2), "\nPar:", ativo,"\nLucro total", round(lucro_total,2))
                            if i >= 1:
                                print("Resultado: WIN no martingale {i}\nLucro:", round(resultado,2), "\nPar:", ativo, "\nLucro total", round(lucro_total,2))
                        elif resultado == 0:
                            if i == 0:
                                print("Resultado: EMPATE\nLucro:", round(resultado,2), "\nPar:", ativo)
                            if i >= 1:
                                print("Resultado: EMPATE no martingale {i}\nLucro:", round(resultado,2), "\nPar:", ativo,"\nLucro total", round(lucro_total,2))
                            if i + 1 <= martingale:
                                gale = float(entrada)
                                entrada = round(abs(gale),2)
                        else:
                            if i == 0:
                                print("Resultado: LOSS\nPerda:", round(resultado,2), "\nPar:", ativo,"\nLucro total", round(lucro_total,2))
                            if i >= 1:
                                print("Resultado: LOSS no martingale {i}\nPerda:", round(resultado,2), "\nPar:", ativo,"\nLucro total", round(lucro_total,2))
                            if i + 1 <= martingale:
                                gale = float(entrada) * float(fator_mg)
                                entrada = round(abs(gale),2)

                        check_stop()        
                        break
                if resultado > 0:
                    break


            else:
                print("erro na abertura da ordem", id)

def estrategia_mhi():
    while True:
        time.sleep(0.1)

        #horario do computador
        #minutos = float(datetime.now().strftime("%M.%S")[1:])

        #horario da Iqoption
        minutos = float(datetime.fromtimestamp(API.get_server_timestamp()).strftime("%M.%S")[1:])

        entrar = True if (minutos >= 4.59 and minutos <= 5.00) or minutos >= 9.59 else False

        print("Aguardando Hórario de entrada. ",minutos, end = "\r")

        if entrar:
            print(f"\nIniciando análise da estrategia MHI")

            direcao = False

            timeframe = 60

            qnt_velas = 3

            velas = API.get_candles(ativo, timeframe, qnt_velas, time.time())

            velas[0] = "Verde" if velas[0]["open"] < velas[0]["close"] else "Vermelha" if velas[0]["open"] > velas[0]["close"] else "doji"
            velas[1] = "Verde" if velas[1]["open"] < velas[1]["close"] else "Vermelha" if velas[1]["open"] > velas[1]["close"] else "doji"
            velas[2] = "Verde" if velas[2]["open"] < velas[2]["close"] else "Vermelha" if velas[2]["open"] > velas[2]["close"] else "doji"

            cores = velas[0], velas[1], velas[2]

            if cores.count('Verde') > cores.count("Vermelha") and cores.count("doji") == 0: direcao = "put"
            if cores.count('Verde') < cores.count("Vermelha") and cores.count("doji") == 0: direcao = "call"

            if direcao:
                print("Velas: ", velas[0], velas[1], velas[2], "Entrada para ", direcao)
                compra(ativo,valor_entrada,direcao,1,tipo)
            else:
                print("Entrada Abortada - tem um Doji")








ativo = input("Digite o ativo que você deseja operar: ").upper()
#exp = input("Qual tempo da operação?: ")
#direcao = input("entrada call ou put: ")

perfil = json.loads(json.dumps(API.get_profile_ansyc()))
cifrao = str(perfil["currency_char"])
nome = str(perfil["name"])
valorconta = float(API.get_balance())

print(f"#"*60)
print(f"\n\nOlá, {nome}\nSeja bem vindo ao Robô XYZ")
print(f"\nSeu saldo na CONTA {escolha} é de {cifrao}{valorconta}")
print(f"\nSeu valor de entrada é de {cifrao}{valor_entrada}")
print(f"STOP LOSS: -{cifrao}{stop_loss}")
print(f"TAKE PROFIT: {cifrao}{stop_win}")
print(f"#"*60)


#compra(ativo,valor_entrada,direcao,exp,tipo)
estrategia_mhi()


