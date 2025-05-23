"""
Versão alternativa usando Selenium para automação real do WhatsApp Web
IMPORTANTE: Esta versão requer configuração adicional do ChromeDriver
"""

import streamlit as st
import pandas as pd
import re
import time
from datetime import datetime
import io
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WhatsAppSeleniumSender:
    def __init__(self):
        self.driver = None
        self.is_logged_in = False
        
    def setup_driver(self):
        """Configura o driver do Chrome"""
        try:
            chrome_options = Options()
            
            # Configurações para evitar detecção
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Manter sessão do WhatsApp (opcional)
            chrome_options.add_argument("--user-data-dir=./whatsapp_session")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return True
        except Exception as e:
            st.error(f"Erro ao configurar Chrome: {e}")
            return False
    
    def login_whatsapp(self):
        """Inicia sessão no WhatsApp Web"""
        try:
            if not self.driver:
                if not self.setup_driver():
                    return False
            
            self.driver.get("https://web.whatsapp.com")
            
            # Aguarda QR Code ou login automático
            st.info("🔄 Aguardando login no WhatsApp Web...")
            
            # Verifica se já está logado ou aguarda login
            try:
                # Aguarda aparecer a interface principal (caixa de pesquisa)
                WebDriverWait(self.driver, 60).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
                )
                self.is_logged_in = True
                st.success("✅ Login realizado com sucesso!")
                return True
                
            except TimeoutException:
                st.error("❌ Timeout no login. Tente novamente.")
                return False
                
        except Exception as e:
            st.error(f"Erro no login: {e}")
            return False
    
    def send_message(self, phone: str, message: str, file_path: Optional[str] = None):
        """Envia mensagem para um número específico"""
        try:
            if not self.is_logged_in:
                return False, "Não logado no WhatsApp"
            
            # Navega para o chat
            url = f"https://web.whatsapp.com/send?phone={phone}"
            self.driver.get(url)
            
            # Aguarda carregar o chat
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]'))
                )
            except TimeoutException:
                return False, "Chat não carregou ou número inválido"
            
            # Localiza caixa de texto
            message_box = self.driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
            
            # Envia mensagem linha por linha (para preservar quebras)
            lines = message.split('\n')
            for i, line in enumerate(lines):
                message_box.send_keys(line)
                if i < len(lines) - 1:  # Não adiciona Shift+Enter na última linha
                    message_box.send_keys(Keys.SHIFT + Keys.ENTER)
            
            # Envia arquivo se fornecido
            if file_path:
                try:
                    # Clica no botão de anexo
                    attach_btn = self.driver.find_element(By.XPATH, '//div[@title="Anexar"]')
                    attach_btn.click()
                    
                    # Seleciona tipo de arquivo
                    file_input = self.driver.find_element(By.XPATH, '//input[@accept="*"]')
                    file_input.send_keys(file_path)
                    
                    # Aguarda carregar e clica em enviar
                    WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                    ).click()
                    
                    time.sleep(2)  # Aguarda envio do arquivo
                    
                except Exception as e:
                    return False, f"Erro ao enviar arquivo: {e}"
            
            # Envia mensagem
            send_button = self.driver.find_element(By.XPATH, '//span[@data-icon="send"]')
            send_button.click()
            
            time.sleep(1)  # Aguarda confirmação
            return True, "Mensagem enviada com sucesso"
            
        except NoSuchElementException:
            return False, "Elemento não encontrado na página"
        except Exception as e:
            return False, f"Erro inesperado: {str(e)}"
    
    def close(self):
        """Fecha o driver"""
        if self.driver:
            self.driver.quit()

def selenium_interface():
    """Interface específica para versão com Selenium"""
    st.header("🤖 Modo Selenium (Automação Real)")
    
    if 'selenium_sender' not in st.session_state:
        st.session_state.selenium_sender = WhatsAppSeleniumSender()
    
    sender = st.session_state.selenium_sender
    
    # Botão de login
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        if not sender.is_logged_in:
            if st.button("🔑 Conectar WhatsApp Web", use_container_width=True):
                with st.spinner("Abrindo WhatsApp Web..."):
                    success = sender.login_whatsapp()
                    if success:
                        st.experimental_rerun()
        else:
            st.success("✅ Conectado ao WhatsApp Web")
            if st.button("🔌 Desconectar", use_container_width=True):
                sender.close()
                st.session_state.selenium_sender = WhatsAppSeleniumSender()
                st.experimental_rerun()
    
    # Interface só aparece se estiver logado
    if sender.is_logged_in:
        st.markdown("---")
        
        # Resto da interface (similar ao código principal)
        contact_input = st.text_area(
            "📞 Números de telefone",
            placeholder="(11) 99999-9999\nJoão, 11888888888",
            height=100
        )
        
        message = st.text_area(
            "💬 Mensagem",
            placeholder="Olá {nome}! Mensagem personalizada.",
            height=80
        )
        
        interval = st.slider("⏱️ Intervalo (segundos)", 2, 30, 5)
        
        uploaded_file = st.file_uploader("📎 Arquivo opcional", type=['jpg', 'png', 'pdf', 'doc'])
        
        if st.button("🚀 Enviar com Selenium", disabled=not (contact_input and message)):
            # Processo de envio (similar ao código principal)
            # mas usando sender.send_message() real
            pass
    
    return sender

# Adicione esta função ao main() original como uma aba adicional:
"""
# No main(), adicione:
tab1, tab2 = st.tabs(["📱 Modo Simulação", "🤖 Modo Selenium"])

with tab1:
    # Código original aqui
    pass

with tab2:
    selenium_interface()
"""
