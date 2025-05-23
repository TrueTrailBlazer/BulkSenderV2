import streamlit as st
import pandas as pd
import re
import time
from datetime import datetime
import io
import urllib.parse
from typing import List, Dict, Optional

st.set_page_config(
    page_title="WhatsApp Bulk Sender",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="expanded"
)

class WhatsAppSender:
    def __init__(self):
        self.sent_messages = []
        
    def validate_phone_number(self, number: str) -> bool:
        clean_number = re.sub(r'[^\d]', '', number)
        if len(clean_number) < 10 or len(clean_number) > 15:
            return False
        if clean_number.startswith('0'):
            clean_number = clean_number[1:]
        return True
    
    def format_phone_number(self, number: str) -> str:
        clean_number = re.sub(r'[^\d]', '', number)
        if clean_number.startswith('0'):
            clean_number = clean_number[1:]
        if len(clean_number) == 11 and clean_number.startswith('1'):
            clean_number = '55' + clean_number
        elif len(clean_number) == 10:
            clean_number = '55' + clean_number
        elif len(clean_number) == 11 and not clean_number.startswith('55'):
            clean_number = '55' + clean_number
        return clean_number
    
    def send_message_via_web(self, phone: str, message: str, file_path: Optional[str] = None):
        try:
            encoded_message = urllib.parse.quote(message)
            whatsapp_url = f"https://web.whatsapp.com/send?phone={phone}&text={encoded_message}"
            time.sleep(0.5)
            
            import random
            success_rate = random.random()
            
            if success_rate > 0.05:
                return True, "Mensagem enviada com sucesso"
            else:
                error_messages = [
                    "Numero nao encontrado no WhatsApp",
                    "Falha na conexao",
                    "Limite de mensagens atingido",
                    "Numero bloqueado"
                ]
                return False, random.choice(error_messages)
        except Exception as e:
            return False, f"Erro ao enviar mensagem: {str(e)}"
    
    def parse_contacts(self, contact_input: str) -> List[Dict]:
        contacts = []
        lines = contact_input.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            if ',' in line:
                parts = line.split(',', 1)
                name = parts[0].strip()
                phone = parts[1].strip()
            else:
                name = ""
                phone = line.strip()
            
            if self.validate_phone_number(phone):
                formatted_phone = self.format_phone_number(phone)
                contacts.append({
                    'name': name,
                    'phone': formatted_phone,
                    'original': line
                })
        
        return contacts
    
    def personalize_message(self, message: str, contact: Dict) -> str:
        personalized = message
        
        if contact['name']:
            personalized = personalized.replace('{nome}', contact['name'])
            personalized = personalized.replace('{name}', contact['name'])
        else:
            personalized = personalized.replace('Ola {nome}!', 'Ola!')
            personalized = personalized.replace('Oi {nome},', 'Oi,')
            personalized = personalized.replace('{nome}', 'Cliente')
            personalized = personalized.replace('{name}', 'Cliente')
        
        personalized = personalized.replace('{numero}', contact['phone'])
        personalized = personalized.replace('{phone}', contact['phone'])
        
        return personalized

def main():
    st.title("📱 WhatsApp Bulk Sender")
    st.markdown("**Envio de mensagens em massa para WhatsApp - Versao Demo**")
    st.markdown("---")
    
    if 'sender' not in st.session_state:
        st.session_state.sender = WhatsAppSender()
    
    with st.sidebar:
        st.header("ℹ️ Como Usar")
        st.info("""
        **Passo a passo:**
        1. Cole os numeros com DDD
        2. Escreva sua mensagem
        3. Configure o intervalo
        4. Faca upload de arquivo (opcional)
        5. Clique em enviar
        
        **Formato dos numeros:**
        - (11) 99999-9999
        - 11999999999
        - Nome, 11999999999
        """)
        
        st.header("📋 Variaveis")
        st.code("{nome} - Nome do contato")
        st.code("{numero} - Numero formatado")
        
        st.header("📊 Estatisticas")
        if hasattr(st.session_state, 'stats'):
            st.metric("✅ Enviados", st.session_state.stats.get('sent', 0))
            st.metric("❌ Erros", st.session_state.stats.get('errors', 0))
            st.metric("📈 Taxa Sucesso", f"{st.session_state.stats.get('success_rate', 0):.1f}%")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📞 Lista de Contatos")
        
        contact_input = st.text_area(
            "Cole os numeros de telefone (um por linha)",
            placeholder="""Exemplos de formatos aceitos:
Joao Silva, (11) 99999-9999
Maria, 11988888888
(11) 97777-7777
11966666666""",
            height=150,
            help="Voce pode incluir nomes separados por virgula antes do numero"
        )
        
        if contact_input:
            contacts = st.session_state.sender.parse_contacts(contact_input)
            
            if contacts:
                st.success(f"✅ {len(contacts)} numeros validos encontrados")
                
                with st.expander("👀 Visualizar lista de contatos"):
                    df_preview = pd.DataFrame([
                        {
                            'Nome': contact['name'] or 'Sem nome',
                            'Numero': contact['phone'],
                            'Original': contact['original']
                        } for contact in contacts[:20]
                    ])
                    st.dataframe(df_preview, use_container_width=True)
                    
                    if len(contacts) > 20:
                        st.info(f"Mostrando primeiros 20 de {len(contacts)} contatos")
            else:
                st.error("❌ Nenhum numero valido encontrado. Verifique o formato.")
                contacts = []
        else:
            contacts = []
    
    with col2:
        st.header("⚙️ Configuracoes")
        
        interval = st.slider(
            "⏱️ Intervalo entre envios",
            min_value=1,
            max_value=60,
            value=3,
            help="Tempo em segundos entre cada envio (recomendado: 3-5s)"
        )
        
        st.metric("Tempo estimado", f"{len(contacts or []) * interval}s" if contacts else "0s")
        
        uploaded_file = st.file_uploader(
            "📎 Anexar arquivo (opcional)",
            type=['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'mp4', 'mp3', 'txt'],
            help="Arquivo que sera enviado junto com a mensagem"
        )
        
        if uploaded_file:
            file_size = len(uploaded_file.getvalue()) / (1024*1024)
            st.success(f"✅ **{uploaded_file.name}**")
            st.info(f"📊 Tamanho: {file_size:.1f} MB")
    
    st.header("💬 Composicao da Mensagem")
    
    col3, col4 = st.columns([3, 1])
    
    with col3:
        message = st.text_area(
            "Digite sua mensagem",
            placeholder="""Ola {nome}! 👋

Esta e uma mensagem personalizada enviada para o numero {numero}.

Espero que esteja tudo bem!

Atenciosamente,
Sua Empresa""",
            height=120,
            help="Use {nome} para personalizar com o nome e {numero} para incluir o numero"
        )
    
    with col4:
        st.markdown("**💡 Dicas de Personalizacao:**")
        st.markdown("• Use {nome} para o nome do contato")
        st.markdown("• Use {numero} para o numero")
        st.markdown("• Seja educado e direto")
        st.markdown("• Evite spam")
        
        if contacts and message:
            st.markdown("**🧪 Teste de Personalizacao:**")
            if st.button("Ver preview", use_container_width=True):
                test_contact = contacts[0]
                test_message = st.session_state.sender.personalize_message(message, test_contact)
                st.text_area("Preview da mensagem:", test_message, height=100, disabled=True)
    
    st.markdown("---")
    
    col5, col6, col7 = st.columns([1, 2, 1])
    
    with col6:
        can_send = bool(contacts and message.strip())
        
        if not can_send:
            missing = []
            if not contacts:
                missing.append("numeros validos")
            if not message.strip():
                missing.append("mensagem")
            
            st.warning(f"⚠️ Ainda falta: **{' e '.join(missing)}**")
        
        send_button = st.button(
            f"🚀 Enviar para {len(contacts or [])} contatos",
            disabled=not can_send,
            use_container_width=True,
            type="primary"
        )
    
    if send_button and can_send:
        st.header("📤 Enviando Mensagens...")
        
        with st.container():
            st.warning(f"""
            **⚠️ Confirmacao de Envio:**
            • **{len(contacts)} mensagens** serao enviadas
            • **Intervalo:** {interval}s entre cada envio
            • **Tempo estimado:** {len(contacts) * interval}s
            • **Arquivo anexo:** {'Sim' if uploaded_file else 'Nao'}
            """)
            
            col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 1])
            
            with col_confirm2:
                if st.button("✅ Confirmar Envio", use_container_width=True, type="primary"):
                    st.session_state.confirmed_send = True
                    st.rerun()
        
        if hasattr(st.session_state, 'confirmed_send') and st.session_state.confirmed_send:
            progress_bar = st.progress(0)
            status_text = st.empty()
            results_container = st.container()
            
            results = []
            successful_sends = 0
            failed_sends = 0
            
            with results_container:
                result_cols = st.columns(2)
                success_container = result_cols[0].container()
                error_container = result_cols[1].container()
                
                success_container.markdown("**✅ Sucessos:**")
                error_container.markdown("**❌ Falhas:**")
            
            for i, contact in enumerate(contacts):
                progress = (i + 1) / len(contacts)
                progress_bar.progress(progress)
                
                contact_display = contact['name'] if contact['name'] else contact['phone'][-4:]
                status_text.text(f"📤 Enviando para {contact_display}... ({i+1}/{len(contacts)})")
                
                personalized_message = st.session_state.sender.personalize_message(message, contact)
                
                success, error_msg = st.session_state.sender.send_message_via_web(
                    contact['phone'], 
                    personalized_message,
                    uploaded_file.name if uploaded_file else None
                )
                
                result = {
                    'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'name': contact['name'],
                    'phone': contact['phone'],
                    'message': personalized_message[:100] + '...' if len(personalized_message) > 100 else personalized_message,
                    'status': 'Sucesso' if success else 'Erro',
                    'error': error_msg if not success else '',
                    'file_attached': 'Sim' if uploaded_file else 'Nao'
                }
                results.append(result)
                
                if success:
                    successful_sends += 1
                    with success_container:
                        st.text(f"• {contact_display}")
                else:
                    failed_sends += 1
                    with error_container:
                        st.text(f"• {contact_display}: {error_msg}")
                
                if i < len(contacts) - 1:
                    for countdown in range(interval, 0, -1):
                        status_text.text(f"⏳ Aguardando {countdown}s para proximo envio...")
                        time.sleep(1)
            
            progress_bar.progress(1.0)
            status_text.text("🎉 Envio concluido com sucesso!")
            
            if hasattr(st.session_state, 'confirmed_send'):
                del st.session_state.confirmed_send
            
            success_rate = (successful_sends / len(contacts)) * 100
            st.session_state.stats = {
                'sent': successful_sends,
                'errors': failed_sends,
                'success_rate': success_rate
            }
            
            st.markdown("### 📊 Relatorio Final")
            
            col8, col9, col10, col11 = st.columns(4)
            with col8:
                st.metric("✅ Sucessos", successful_sends)
            with col9:
                st.metric("❌ Falhas", failed_sends)
            with col10:
                st.metric("📊 Total", len(contacts))
            with col11:
                st.metric("📈 Taxa de Sucesso", f"{success_rate:.1f}%")
            
            if results:
                df_results = pd.DataFrame(results)
                csv_buffer = io.StringIO()
                df_results.to_csv(csv_buffer, index=False, encoding='utf-8')
                
                st.download_button(
                    label="📥 Baixar Relatorio Completo (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"whatsapp_relatorio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666; font-size: 0.9em;'>
            <p>🚨 <strong>Importante:</strong> Esta e uma versao demonstrativa. Use com responsabilidade e respeite os termos de uso do WhatsApp.</p>
            <p>📱 WhatsApp Bulk Sender v2.0 - Desenvolvido com Streamlit</p>
            <p>💡 Para implementacao real, considere usar APIs oficiais ou automacao com Selenium</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
