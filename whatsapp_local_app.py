import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time
import os

st.set_page_config(page_title="Envio em Massa - WhatsApp", layout="centered")

st.title("📤 Envio em Massa no WhatsApp")

with st.form("envio_form"):
    numeros_raw = st.text_area("📱 Números de telefone (com DDD)", placeholder="Ex: 41999999999, 11988888888")
    mensagem = st.text_area("💬 Mensagem a ser enviada", placeholder="Digite sua mensagem aqui...")
    arquivo = st.file_uploader("📎 Anexar arquivo (opcional)", type=None)
    intervalo = st.slider("⏱️ Intervalo entre envios (segundos)", 1, 60, 5)
    enviar = st.form_submit_button("🚀 Enviar mensagens")

def iniciar_driver():
    options = Options()
    options.add_argument('--user-data-dir=./User_Data')  # Mantém login entre sessões
    driver = webdriver.Chrome(options=options)
    driver.get("https://web.whatsapp.com")
    return driver

def enviar_mensagem(driver, numero, mensagem, caminho_arquivo=None):
    url = f"https://web.whatsapp.com/send?phone={numero}&text={mensagem}"
    driver.get(url)
    time.sleep(10)

    try:
        if caminho_arquivo:
            clip_button = driver.find_element(By.CSS_SELECTOR, "span[data-icon='clip']")
            clip_button.click()
            time.sleep(1)
            attach_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
            attach_input.send_keys(caminho_arquivo)
            time.sleep(3)
        send_button = driver.find_element(By.CSS_SELECTOR, "span[data-icon='send']")
        send_button.click()
        return True
    except Exception as e:
        print(f"Erro ao enviar para {numero}: {e}")
        return False

if enviar:
    if not numeros_raw or not mensagem:
        st.error("Por favor, preencha todos os campos obrigatórios.")
    else:
        numeros = [n.strip().replace("+", "").replace(" ", "").replace("-", "") for n in numeros_raw.split(",")]
        driver = iniciar_driver()
        st.info("Escaneie o QR Code no WhatsApp Web e aguarde o carregamento...")

        with st.spinner("Aguardando escaneamento do QR Code..."):
            time.sleep(15)

        temp_path = None
        if arquivo:
            temp_path = os.path.join("/tmp", arquivo.name)
            with open(temp_path, "wb") as f:
                f.write(arquivo.read())

        progresso = st.progress(0)
        status_area = st.empty()
        total = len(numeros)

        for i, numero in enumerate(numeros):
            sucesso = enviar_mensagem(driver, numero, mensagem, temp_path)
            status_area.write(f"Enviando para {numero}: {'✅ Sucesso' if sucesso else '❌ Falha'}")
            progresso.progress((i + 1) / total)
            time.sleep(intervalo)

        driver.quit()
        st.success("Mensagens enviadas!")
