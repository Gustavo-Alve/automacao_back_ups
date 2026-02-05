from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import time, datetime
import os
import pandas as pd
import requests
from requests.exceptions import RequestException


while True:
    #back_ups
    back_up_ax3000 = os.path.abspath('F6600P.bin')
    back_up_f670 = os.path.abspath('F670L V1.bin')
    back_up_V9 = os.path.abspath('F670L V9.bin')
    IPS = [
        "http://192.168.1.1/",
        "http://192.168.0.252/",
    ]

    
    #(url = endereço que vamos testar ) (#time connect = tempo maximo pra conectar) (#time_read = tempo maximo pra esperar alguma resposta)
    #Responsavel por validar se o ip responde ou nao
    def ip_disponivel(url: str, timeout_connect=1.5, timeout_read=2.5) -> tuple[bool, str]: #retorna True Ou False 
        try:
            try:
                r = requests.head(url, timeout=(timeout_connect, timeout_read), allow_redirects=True) #fazendo apenas a requisição do head
                return True, f"HEAD status={r.status_code}"
            except RequestException:
                r = requests.get(url, timeout=(timeout_connect, timeout_read), allow_redirects=True) #fazendo requisição get caso o head falhe
                return True, f"GET status={r.status_code}"

        except RequestException as e:
            return False, f"{type(e).__name__}: {e}" #pra retornar falhas se ambos derem errado
        

    #percorre a lista de ips, e retorna oque foi marcado como True na funçao acima
    def escolher_primeiro_ip_disponivel(urls) -> str | None: #passa por cada ip da lista e verifica qual est
        for url in urls:
            ok, detalhe = ip_disponivel(url)
            if ok:
                return url #se Ok retorna a url que esta True ou seja respondendo
            else:
                print(f"[OFF] {url} -> {detalhe}")
        return None

    #funçao para salvar modelo e mac do equipamento em uma arquivo excel
    def salvar_equipamento(modelo, mac ,data):
        arquivo = "relatorio_equip.xlsx"

        novo_registro = pd.DataFrame([{
            "Modelo": modelo,
            "N° Mac": mac,
            "Data": data
        }])

        if os.path.exists(arquivo):
            df_existente = pd.read_excel(arquivo)
            df_final = pd.concat([df_existente, novo_registro], ignore_index=True)
        else:
            df_final = novo_registro


        df_final.to_excel(arquivo, index=False) #salva as novas alterações e se, criar um novo arquivo


    #função pra executar o playwright
    def executar_playwright(url: str):
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(
            permissions=["clipboard-read", "clipboard-write"] #permissao para ler e escrever dentro das URLS
        )
            pagina = context.new_page()

            try:
                pagina.goto(url, timeout=15000)
                pagina.wait_for_load_state("domcontentloaded", timeout=15000)
                print(f"[PLAYWRIGHT] Acessando: {url}")
                nome_equip = ""
                nome_header = ""
                nome_header_ptbr = ""
                # --- Protege leitura do nome do equipamento ---
                equip_locator = pagina.locator('//*[@id="loginWrapper"]/div[1]')
                if equip_locator.count() > 0:
                    nome_equip = equip_locator.text_content().strip()

                # --- Protege leitura do header ---
                header_locator = pagina.get_by_text("Please login to continue...")
                if header_locator.count() > 0:
                    nome_header = header_locator.text_content().strip()
                
                header_locator = pagina.get_by_text("Por favor faça o login para")
                if header_locator.count() > 0:
                    nome_header_ptbr = header_locator.text_content().strip()


                #Equipamento F670-V9
                if 'aF670L' in nome_equip:
                    pagina.get_by_role("textbox", name="Usuário").fill('multipro')
                    time.sleep(0.5)
                    pagina.get_by_role("textbox", name="Senha").fill('multipro')
                    time.sleep(1)
                    pagina.get_by_role("button", name="Entrar").click()
                    time.sleep(1)
                    elemento_locator = pagina.locator('//*[@id="Outquicksetup"]')
                    if elemento_locator.is_visible():
                        elemento_locator.click()
                    else:
                        print('Elemento nao existe ')

                        
                    senha_2 = pagina.locator("#login_error")
                    if senha_2.is_visible():
                        pagina.get_by_role("textbox", name="Senha").fill('another')
                        time.sleep(1)   
                        pagina.get_by_role("button", name="Entrar").click()
                        time.sleep(1)
                        pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                        modelo_equip = pagina.get_by_text("F670L", exact=True).text_content()
                        time.sleep(0.5)
                        pagina.get_by_role("link", name="Rede local").click()
                        pagina.get_by_role("heading", name="Estado da WLAN", exact=True).click()
                        endereco_mac = pagina.locator('//*[@id="Bssid:0"]').text_content()
                        time.sleep(0.5)
                        pagina.locator("#BackToTop").click()
                        time.sleep(0.5)
                        pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                        hora = datetime.datetime.now()
                        salvar_equipamento(
                            modelo= modelo_equip,
                            mac = endereco_mac,
                            data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                        )
                        pagina.get_by_role("link", name="Administração de sistema").click()
                        time.sleep(1)
                        pagina.get_by_text("Gerenciamento de configuração").click()
                        time.sleep(1)
                        pagina.get_by_role("heading", name="Restaurar configuração padrão").click()
                        time.sleep(1)
                        pagina.locator("#DefCfgUpload").set_input_files(back_up_V9)
                        time.sleep(1)
                        pagina.get_by_role("button", name="Restaurando uma configuração").click()
                        time.sleep(1)
                        pagina.get_by_role("button", name="OK").click()
                        time.sleep(2)
                    else:
                        print('senha padrao')

                
                    time.sleep(1)
                    pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                    modelo_equip = pagina.locator('//*[@id="ModelName"]').text_content()
                    time.sleep(0.5)
                    pagina.get_by_role("link", name="Rede local").click()
                    pagina.get_by_role("heading", name="Estado da WLAN", exact=True).click()
                    endereco_mac = pagina.locator('//*[@id="Bssid:0"]').text_content()
                    time.sleep(0.5)
                    pagina.locator("#BackToTop").click()
                    time.sleep(0.5)
                    pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                    hora = datetime.datetime.now()
                    salvar_equipamento(
                        modelo= modelo_equip,
                        mac = endereco_mac,
                        data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                    )
                    pagina.get_by_role("link", name="Administração de sistema").click()
                    time.sleep(1)
                    pagina.get_by_text("Gerenciamento de configuração").click()
                    time.sleep(1)
                    pagina.get_by_role("heading", name="Restaurar configuração padrão").click()
                    time.sleep(1)
                    pagina.locator("#DefCfgUpload").set_input_files(back_up_V9)
                    time.sleep(1)
                    pagina.get_by_role("button", name="Restaurando uma configuração").click()
                    time.sleep(1)
                    pagina.get_by_role("button", name="OK").click()
                    time.sleep(2)


                #Equipamento AX3000
                elif 'aF6600P' in nome_equip:
                    pagina.get_by_role("textbox", name="Usuário").fill('multipro')
                    time.sleep(0.5)
                    pagina.get_by_role("textbox", name="Senha").fill('multipro')
                    time.sleep(1)
                    pagina.get_by_role("button", name="Entrar").click()
                    time.sleep(1)
                    elemento_locator = pagina.locator('//*[@id="Outquicksetup"]')  
                    if elemento_locator.is_visible():
                        elemento_locator.click()
                    else:
                        print('Elemento nao existe ')
                    senha_2 = pagina.locator("#login_error")
                    if senha_2.is_visible():
                        pagina.get_by_role("textbox", name="Senha").fill('another')
                        pagina.get_by_role("button", name="Entrar").click()
                        elemento_locator = pagina.locator('//*[@id="Outquicksetup"]') 
                        if elemento_locator.is_visible():
                            elemento_locator.click()
                        else:
                            print('Elemento nao existe ')
                        time.sleep(1)
                        pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                        time.sleep(1)
                        modelo_equip = pagina.locator('//*[@id="ModelName"]').text_content()
                        time.sleep(0.5)
                        pagina.get_by_role("link", name="Rede local").click()
                        pagina.get_by_role("heading", name="Estado da WLAN", exact=True).click()
                        endereco_mac = pagina.locator('//*[@id="Bssid:0"]').text_content() 
                        time.sleep(0.5)
                        pagina.locator("#BackToTop").click()
                        time.sleep(0.5)
                        hora = datetime.datetime.now()
                        salvar_equipamento(
                            modelo= modelo_equip,
                            mac = endereco_mac,
                            data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                        )
                        pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                        time.sleep(0.5)
                        pagina.get_by_role("link", name="Administração de sistema").click()
                        time.sleep(1)
                        pagina.get_by_text("Gerenciamento de configuração").click()
                        time.sleep(1)
                        pagina.get_by_role("heading", name="Restaurar configuração padrão").click()
                        time.sleep(1)
                        pagina.locator("#DefCfgUpload").set_input_files(back_up_ax3000)
                        time.sleep(1)
                        pagina.get_by_role("button", name="Restaurando uma configuração").click()
                        time.sleep(1)
                        pagina.get_by_role("button", name="OK").click()
                        time.sleep(2)
                    else:
                        print('senha padrao')


                    pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                    time.sleep(1)
                    modelo_equip = pagina.locator('//*[@id="ModelName"]').text_content()
                    time.sleep(0.5)
                    pagina.get_by_role("link", name="Rede local").click()
                    pagina.get_by_role("heading", name="Estado da WLAN", exact=True).click()
                    endereco_mac = pagina.locator('//*[@id="Bssid:0"]').text_content() 
                    time.sleep(0.5)
                    pagina.locator("#BackToTop").click()
                    time.sleep(0.5)
                    hora = datetime.datetime.now()
                    salvar_equipamento(
                        modelo= modelo_equip,
                        mac = endereco_mac,
                        data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                    )
                    pagina.get_by_role("link", name="Gerência & Diagnóstico").click()
                    time.sleep(0.5)
                    pagina.get_by_role("link", name="Administração de sistema").click()
                    time.sleep(1)
                    pagina.get_by_text("Gerenciamento de configuração").click()
                    time.sleep(1)
                    pagina.get_by_role("heading", name="Restaurar configuração padrão").click()
                    time.sleep(1)
                    pagina.locator("#DefCfgUpload").set_input_files(back_up_ax3000)
                    time.sleep(1)
                    pagina.get_by_role("button", name="Restaurando uma configuração").click()
                    time.sleep(1)
                    pagina.get_by_role("button", name="OK").click()
                    time.sleep(2)

                
                #equipamento F670L
                elif "Please login to continue..." in nome_header:
                    pagina.locator("#Frm_Username").fill('multipro')
                    pagina.locator("#Frm_Password").fill('multipro')
                    time.sleep(1)
                    pagina.get_by_role("button", name="Login").click()
                    time.sleep(1)
                    senha_2_f670 = pagina.locator("#layer_login_title div")
                    if senha_2_f670.is_visible():
                        pagina.locator("#Frm_Username").fill('multipro')
                        pagina.locator("#Frm_Password").fill('wgodwl810')
                        time.sleep(2)
                        pagina.locator("#Frm_Password").press("Enter")
                        time.sleep(1)
                        pagina.wait_for_selector('iframe[name="mainFrame"]')
                        frame = pagina.frame(name="mainFrame")
                        frame.locator('#Frm_ModelName').wait_for(state="visible") #frame utilizado para validar os campos onde estao armazenados as informações como (MODELO - MAC)
                        modelo_equip = frame.locator('#Frm_ModelName').inner_text()
                        frame = pagina.frame(name="mainFrame")
                        frame.get_by_text("User Interface").click()
                        time.sleep(1)
                        endereco_mac = frame.locator('#td_Bssid0').inner_text()
                        time.sleep(1)
                        hora = datetime.datetime.now()
                        salvar_equipamento(
                            modelo=modelo_equip,
                            mac=endereco_mac,
                            data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                        )
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("Administration").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("System Management").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("cell", name="Default Configuration Management", exact=True).click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Choose File").set_input_files(back_up_f670)
                        time.sleep(2)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Restore Configuration").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Confirm").click()
                        time.sleep(1)
                    else:
                        print('Senha padrao')


                    pagina.wait_for_selector('iframe[name="mainFrame"]')
                    frame = pagina.frame(name="mainFrame")
                    frame.locator('#Frm_ModelName').wait_for(state="visible") #frame utilizado para validar os campos onde estao armazenados as informações como (MODELO - MAC)
                    modelo_equip = frame.locator('#Frm_ModelName').inner_text()
                    frame = pagina.frame(name="mainFrame")
                    frame.get_by_text("User Interface").click()
                    time.sleep(1)
                    endereco_mac = frame.locator('#td_Bssid0').inner_text()
                    time.sleep(1)
                    hora = datetime.datetime.now()
                    salvar_equipamento(
                        modelo=modelo_equip,
                        mac=endereco_mac,
                        data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                    )
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("Administration").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("System Management").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("cell", name="Default Configuration Management", exact=True).click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Choose File").set_input_files(back_up_f670)
                    time.sleep(2)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Restore Configuration").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Confirm").click()
                    time.sleep(1)

                #elif adiconado pois em alguns equipamentos do Modelo F670L estao em portugues e causa divergência nos botoes
                elif "Por favor faça o login para" in nome_header_ptbr: 
                    pagina.locator("#TestLang01").click()
                    time.sleep(0.5)
                    pagina.locator("#Frm_Username").fill('multipro')
                    pagina.locator("#Frm_Password").fill('multipro')
                    time.sleep(1)
                    pagina.get_by_role("button", name="Login").click()
                    time.sleep(1)
                    senha_2_f670 = pagina.locator("#layer_login_title div")
                    if senha_2_f670.is_visible():
                        pagina.locator("#Frm_Username").fill('multipro')
                        pagina.locator("#Frm_Password").fill('wgodwl810')
                        time.sleep(2)
                        pagina.locator("#Frm_Password").press("Enter")
                        pagina.wait_for_selector('iframe[name="mainFrame"]')
                        frame = pagina.frame(name="mainFrame")
                        frame.locator('#Frm_ModelName').wait_for(state="visible") #frame utilizado para validar os campos onde estao armazenados as informações como (MODELO - MAC)
                        modelo_equip = frame.locator('#Frm_ModelName').inner_text()
                        frame = pagina.frame(name="mainFrame")
                        frame.get_by_text("User Interface").click()
                        time.sleep(1)
                        endereco_mac = frame.locator('#td_Bssid0').inner_text()
                        time.sleep(1)
                        hora = datetime.datetime.now()
                        salvar_equipamento(
                            modelo=modelo_equip,
                            mac=endereco_mac,
                            data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                        )
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("Administration").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("System Management").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("cell", name="Default Configuration Management", exact=True).click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Choose File").set_input_files(back_up_f670)
                        time.sleep(2)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Restore Configuration").click()
                        time.sleep(1)
                        pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Confirm").click()
                        time.sleep(1)
                    else:
                        print('Senha padrao')

                    pagina.wait_for_selector('iframe[name="mainFrame"]')
                    frame = pagina.frame(name="mainFrame")
                    frame.locator('#Frm_ModelName').wait_for(state="visible") #frame utilizado para validar os campos onde estao armazenados as informações como (MODELO - MAC)
                    modelo_equip = frame.locator('#Frm_ModelName').inner_text()
                    frame = pagina.frame(name="mainFrame")
                    frame.get_by_text("User Interface").click()
                    time.sleep(1)
                    endereco_mac = frame.locator('#td_Bssid0').inner_text()
                    time.sleep(1)
                    hora = datetime.datetime.now()
                    salvar_equipamento(
                        modelo=modelo_equip,
                        mac=endereco_mac,
                        data= f'{hora.year}/{hora.month}/{hora.hour}:{hora.minute}'
                    )
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("Administration").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_text("System Management").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("cell", name="Default Configuration Management", exact=True).click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Choose File").set_input_files(back_up_f670)
                    time.sleep(2)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Restore Configuration").click()
                    time.sleep(1)
                    pagina.locator("iframe[name=\"mainFrame\"]").content_frame.get_by_role("button", name="Confirm").click()
                    time.sleep(1)


            except PWTimeout:
                    print(f"[PLAYWRIGHT] Timeout ao abrir: {url}") #caso passe do tempo 
            finally:
                    context.close()
                    time.sleep(5)
                    browser.close()
    def main():
        escolhido = escolher_primeiro_ip_disponivel(IPS)
        if not escolhido:
            print("Nenhum IP disponível. Encerrando.")
            return

        executar_playwright(escolhido) #chamando minha função que executa meus comandos



    #fecha minha funçao main()
    if __name__ == "__main__":
        main()
