import streamlit as st
import pandas as pd
from datetime import date, datetime
from streamlit_calendar import calendar
import database_2 as db
import os
import io

db.init_db()

st.set_page_config(page_title="Sala Reunião CSOL-3", page_icon="📅", layout="wide")

# --- ESTILIZAÇÃO CSS CORRIGIDA (COR DA FONTE DO DATE_INPUT) ---
st.markdown("""
    <style>
        /* Cor de fundo da barra lateral em azul corporativo */
        [data-testid="stSidebar"] {
            background-color: #0078d4;
        }
        
        /* Aumento do tamanho das fontes e títulos na barra lateral */
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3 {
            font-size: 1.2rem !important;
            color: #ffffff !important;
        }
        
        /* Textos gerais, parágrafos e spans na barra lateral */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            font-size: 1.05rem !important;
            color: #ffffff !important;
        }
        
        /* Rótulos de campos (labels) na barra lateral maiores e legíveis */
        [data-testid="stSidebar"] label {
            font-size: 1.05rem !important;
            color: #ffffff !important;
            font-weight: 600 !important;
        }
        
        /* Itens do menu de rádio (navegação) maiores */
        [data-testid="stSidebar"] .stRadio label p {
            font-size: 1.1rem !important;
            color: #ffffff !important;
        }
        
        /* --- CORREÇÃO DEFINITIVA DA FONTE DO SELETOR DE DATA --- */
        [data-testid="stSidebar"] input[aria-label*="Escolha o dia"] {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-weight: bold !important;
        }
        
        [data-testid="stSidebar"] div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border-radius: 4px;
        }
        
        [data-testid="stSidebar"] div[data-baseweb="input"] input {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            background-color: #ffffff !important;
            font-weight: bold !important;
            font-size: 1.05rem !important;
        }
        
        /* Estilização dos botões da barra lateral com texto maior */
        [data-testid="stSidebar"] button {
            background-color: #005a9e !important;
            color: #ffffff !important;
            border: 1px solid #ffffff !important;
            font-size: 1.05rem !important;
            font-weight: 600 !important;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #004578 !important;
        }
    </style>
""", unsafe_allow_html=True)

def render_header(title_text):
    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(title_text)
    with col2:
        if os.path.exists("Logo_Prodeb.jpeg"):
            st.image("Logo_Prodeb.jpeg", width=220)
        elif os.path.exists("logo_prodeb.jpeg"):
            st.image("logo_prodeb.jpeg", width=220)

# --- INICIALIZAÇÃO DA SESSÃO INTEGRADA COM A URL (PERSISTÊNCIA NO F5) ---
if "logged_in" not in st.session_state:
    if st.query_params.get("logged_in") == "true":
        st.session_state.logged_in = True
        st.session_state.username = st.query_params.get("username", "")
        st.session_state.full_name = st.query_params.get("full_name", "")
        st.session_state.must_change_password = False
    else:
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.must_change_password = False

# --- TELA DE LOGIN CENTRALIZADA ---
if not st.session_state.logged_in:
    _, col_center, _ = st.columns([1, 1.3, 1])
    
    with col_center:
        st.markdown("<h1 style='text-align: center;'>🔐 Sala de Reunião CSOL-3</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Faça login para acessar a agenda.</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.subheader("Identificação de Acesso")
        with st.form("login_form"):
            username_input = st.text_input("Usuário")
            password_input = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if submit:
                user_data, error_msg = db.verify_user(username_input, password_input)
                if user_data:
                    st.session_state.logged_in = True
                    st.session_state.username = username_input
                    st.session_state.full_name = user_data["full_name"]
                    st.session_state.must_change_password = user_data["must_change_password"]
                    
                    st.query_params["logged_in"] = "true"
                    st.query_params["username"] = username_input
                    st.query_params["full_name"] = user_data["full_name"]
                    
                    st.rerun()
                else:
                    st.error(error_msg)
                    
        st.info("💡 **Atenção:** Caso não tenha acesso, solicite à Coordenação da CSOL-3")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if os.path.exists("Logo_Prodeb.jpeg"):
            st.image("Logo_Prodeb.jpeg", use_container_width=True)
        elif os.path.exists("logo_prodeb.jpeg"):
            st.image("logo_prodeb.jpeg", use_container_width=True)

# --- OBRIGAR TROCA DE SENHA NO PRIMEIRO LOGIN ---
elif st.session_state.must_change_password:
    render_header("⚠️ Primeiro Acesso - Alteração de Senha")
    st.warning("Você está acessando com uma senha temporária. É obrigatório alterá-la para continuar.")
    
    _, col_center, _ = st.columns([1, 1.2, 1])
    with col_center:
        with st.form("change_pwd_first"):
            new_pwd = st.text_input("Nova Senha", type="password")
            confirm_pwd = st.text_input("Confirme a Nova Senha", type="password")
            submit_pwd = st.form_submit_button("Alterar Senha e Continuar", use_container_width=True)
            
            if submit_pwd:
                if not new_pwd or len(new_pwd) < 4:
                    st.error("A senha deve conter pelo menos 4 caracteres.")
                elif new_pwd != confirm_pwd:
                    st.error("As senhas não coincidem.")
                else:
                    db.update_password(st.session_state.username, new_pwd)
                    st.session_state.must_change_password = False
                    st.success("Senha alterada com sucesso!")
                    st.rerun()

# --- APLICAÇÃO PRINCIPAL ---
else:
    @st.dialog("🔔 Minhas Notificações", width="large")
    def show_notifications_dialog():
        user_notifs = db.get_user_notifications(st.session_state.username)
        if user_notifs:
            st.markdown("### 📬 Histórico de Avisos")
            for idx, n in enumerate(user_notifs):
                status_icon = "🟢 Nova" if n[3] == 0 else "⚪ Lida"
                with st.container():
                    st.markdown(f"**{status_icon}** — *{n[2]}*")
                    st.info(n[1])
                    st.markdown("---")
            db.mark_notifications_as_read(st.session_state.username)
        else:
            st.info("Você não possui notificações gravadas.")

    col_user, col_bell = st.sidebar.columns([4, 1])
    with col_user:
        st.sidebar.markdown(f"**Olá, {st.session_state.full_name}**")
    with col_bell:
        notifications = db.get_user_notifications(st.session_state.username)
        unread_count = sum(1 for n in notifications if n[3] == 0)
        bell_icon = f"🔔 ({unread_count})" if unread_count > 0 else "🔔"
        if st.sidebar.button(bell_icon, key="btn_bell"):
            show_notifications_dialog()

    menu_options = ["📅 Calendário Geral", "📊 Relatório de Agendamentos", "🔑 Alterar Senha"]
    if st.session_state.username == "admin":
        menu_options.append("⚙️ Gerenciar Usuários (Admin)")
        
    menu = st.sidebar.radio("Navegação", menu_options)
    
    st.sidebar.markdown("---")

    @st.dialog("🗓️ Agendamentos do Dia", width="large")
    def show_day_dialog(date_str):
        dt_obj = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = dt_obj.strftime("%d/%m/%Y")
        
        st.subheader(f"Data selecionada: {formatted_date}")
        
        all_bookings = db.get_all_bookings()
        day_bookings = [b for b in all_bookings if b[4] == date_str]
        day_bookings.sort(key=lambda x: x[5])
        
        st.markdown("### 📌 Reservas (Por Ordem de Horário)")
        if day_bookings:
            for b in day_bookings:
                b_id, b_user, b_fullname, b_title, b_date, b_start, b_end = b
                with st.expander(f"⏰ {b_start} às {b_end} — {b_title} ({b_fullname})"):
                    
                    if st.session_state.username == "admin" or st.session_state.username == b_user:
                        if st.button("❌ Cancelar Reserva", key=f"pop_del_{b_id}"):
                            success, msg = db.delete_booking(b_id, st.session_state.username)
                            if success:
                                st.success(msg)
                                st.rerun()
                            else:
                                st.error(msg)
                    else:
                        st.caption("Apenas o proprietário ou administrador podem cancelar.")
                        
                    if st.session_state.username == b_user:
                        with st.form(f"pop_edit_{b_id}"):
                            st.markdown("**Editar Detalhes**")
                            new_title = st.text_input("Novo Assunto", value=b_title, key=f"pop_t_{b_id}")
                            c1, c2 = st.columns(2)
                            with c1:
                                new_start = st.time_input("Início", value=datetime.strptime(b_start, "%H:%M").time(), key=f"pop_s_{b_id}")
                            with c2:
                                new_end = st.time_input("Término", value=datetime.strptime(b_end, "%H:%M").time(), key=f"pop_e_{b_id}")
                                
                            submit_edit = st.form_submit_button("Salvar Alterações")
                            if submit_edit:
                                if new_start >= new_end:
                                    st.error("O horário de término deve ser posterior ao início.")
                                else:
                                    s_ok, s_msg = db.update_booking(
                                        b_id, st.session_state.username, new_title, 
                                        date_str, new_start.strftime("%H:%M"), new_end.strftime("%H:%M")
                                    )
                                    if s_ok:
                                        st.success(s_msg)
                                        st.rerun()
                                    else:
                                        st.error(s_msg)
        else:
            st.info("Nenhum agendamento registrado para este dia.")

        st.markdown("---")
        st.markdown("### ➕ Realizar Nova Reserva")
        with st.form("pop_new_booking"):
            q_title = st.text_input("Assunto / Motivo da Reunião")
            qc1, qc2 = st.columns(2)
            with qc1:
                q_start = st.time_input("Horário de Início")
            with qc2:
                q_end = st.time_input("Horário de Término")
                
            q_guests = st.text_input("E-mails dos convidados (separados por vírgula, opcional)")
                
            q_submit = st.form_submit_button("Confirmar Reserva")
            if q_submit:
                if not q_title:
                    st.warning("Preencha o assunto.")
                elif q_start >= q_end:
                    st.error("O horário de término deve ser posterior ao início.")
                else:
                    ok, msg = db.add_booking(
                        st.session_state.username, q_title, date_str, 
                        q_start.strftime("%H:%M"), q_end.strftime("%H:%M"), q_guests
                    )
                    if ok:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)

    st.sidebar.markdown("### 🔍 Gerenciar Reserva")
    sidebar_date = st.sidebar.date_input("Escolha o dia:", value=date.today(), format="DD/MM/YYYY", key="sb_date")
    if st.sidebar.button("Abrir", use_container_width=True):
        show_day_dialog(sidebar_date.strftime("%Y-%m-%d"))

    st.sidebar.markdown("---")
    if st.sidebar.button("Sair (Logout)", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.session_state.full_name = ""
        st.session_state.must_change_password = False
        st.query_params.clear()
        st.rerun()

    if menu == "📅 Calendário Geral":
        render_header("📅 Calendário da Sala de Reunião - CSOL-3")
        st.markdown("Visualize as reuniões agendadas. **Clique em qualquer dia do calendário** para abrir os agendamentos da data ou gerenciar pela barra lateral.")
        
        events = db.get_calendar_events()
        
        calendar_options = {
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek,timeGridDay"
            },
            "initialView": "dayGridMonth",
            "selectable": True,
            "editable": False,
            "locale": "pt-br",
            "buttonText": {
                "today": "Hoje",
                "month": "Mês",
                "week": "Semana",
                "day": "Dia"
            },
            "height": 600
        }
        
        cal_data = calendar(events=events, options=calendar_options, key="calendar_csol3")
        
        if cal_data:
            selected_date_str = None
            if "dateClick" in cal_data:
                selected_date_str = cal_data["dateClick"].get("date", "").split("T")[0]
            elif "eventClick" in cal_data:
                clicked_event = cal_data["eventClick"]["event"]
                event_start = clicked_event.get("start", "")
                selected_date_str = event_start.split("T")[0]
            
            if selected_date_str:
                show_day_dialog(selected_date_str)

    elif menu == "📊 Relatório de Agendamentos":
        render_header("📊 Relatório de Agendamentos - Sala CSOL-3")
        st.markdown("Selecione o período desejado para gerar o relatório consolidado de reuniões com pré-visualização.")
        
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            start_per = st.date_input("Data Inicial", value=date.today(), format="DD/MM/YYYY")
        with col_r2:
            end_per = st.date_input("Data Final", value=date.today(), format="DD/MM/YYYY")
            
        start_str = start_per.strftime("%Y-%m-%d")
        end_str = end_per.strftime("%Y-%m-%d")
        
        report_data = db.get_bookings_by_period(start_str, end_str)
        
        st.markdown("### 🔎 Pré-visualização do Relatório")
        if report_data:
            df_report = pd.DataFrame(report_data, columns=["ID", "Usuário", "Responsável", "Assunto", "Data", "Início", "Fim"])
            df_report["Data"] = pd.to_datetime(df_report["Data"]).dt.strftime("%d/%m/%Y")
            st.dataframe(df_report[["Responsável", "Assunto", "Data", "Início", "Fim"]], use_container_width=True)
            
            if st.button("📥 Baixar Relatório em PDF"):
                try:
                    from reportlab.lib.pagesizes import letter
                    from reportlab.pdfgen import canvas
                    
                    buffer = io.BytesIO()
                    p = canvas.Canvas(buffer, pagesize=letter)
                    p.drawString(50, 750, "RELATÓRIO DE AGENDAMENTOS - SALA CSOL-3")
                    p.drawString(50, 730, f"Período: {start_per.strftime('%d/%m/%Y')} a {end_per.strftime('%d/%m/%Y')}")
                    
                    y = 690
                    for r in report_data:
                        linha = f"Data: {r[4][8:10]}/{r[4][5:7]}/{r[4][:4]} | {r[5]} às {r[6]} - {r[3]} ({r[2]})"
                        p.drawString(50, y, linha)
                        y -= 20
                        if y < 50:
                            p.showPage()
                            y = 750
                    p.save()
                    buffer.seek(0)
                    
                    st.download_button(
                        label="💾 Clique aqui para baixar o PDF gerado",
                        data=buffer,
                        file_name=f"relatorio_csol3_{start_str}_to_{end_str}.pdf",
                        mime="application/pdf"
                    )
                except ImportError:
                    st.error("A biblioteca ReportLab não está instalada. Execute `pip install reportlab`.")
        else:
            st.info("Nenhum agendamento encontrado no período selecionado.")

    elif menu == "🔑 Alterar Senha":
        render_header("🔑 Alterar Minha Senha")
        with st.form("change_my_password"):
            current_pwd = st.text_input("Senha Atual", type="password")
            new_pwd = st.text_input("Nova Senha", type="password")
            confirm_pwd = st.text_input("Confirme a Nova Senha", type="password")
            submit_cp = st.form_submit_button("Atualizar Senha")
            
            if submit_cp:
                val, _ = db.verify_user(st.session_state.username, current_pwd)
                if not val:
                    st.error("A senha atual está incorreta.")
                elif not new_pwd or len(new_pwd) < 4:
                    st.error("A nova senha deve ter pelo menos 4 caracteres.")
                elif new_pwd != confirm_pwd:
                    st.error("As novas senhas não coincidem.")
                else:
                    db.update_password(st.session_state.username, new_pwd)
                    st.success("Senha alterada com sucesso!")

    elif menu == "⚙️ Gerenciar Usuários (Admin)":
        if st.session_state.username != "admin":
            st.warning("Acesso restrito ao administrador.")
        else:
            render_header("⚙️ Gestão de Usuários")
            
            # Abas para Separar Cadastro, Edição e Status
            tab1, tab2, tab3 = st.tabs(["➕ Cadastrar Novo", "✏️ Editar Cadastro", "🔄 Ativar / Inativar"])
            
            users_list = db.get_all_users()
            
            with tab1:
                st.subheader("Cadastrar Novo Usuário")
                with st.form("new_user_form"):
                    new_user = st.text_input("Nome de Usuário (Login)")
                    new_email = st.text_input("E-mail do Usuário")
                    default_pass = st.text_input("Senha Padrão Inicial", value="mudar123", type="password")
                    new_name = st.text_input("Nome Completo")
                    submit_user = st.form_submit_button("Cadastrar Usuário")
                    
                    if submit_user:
                        if new_user and new_email and default_pass and new_name:
                            created, msg = db.add_user_by_admin(new_user, default_pass, new_name, new_email)
                            if created:
                                st.success(f"{msg} (Senha padrão: {default_pass} - exigirá troca no primeiro login).")
                                st.rerun()
                            else:
                                st.error(msg)
                        else:
                            st.warning("Preencha todos os campos, incluindo o e-mail.")

            with tab2:
                st.subheader("Editar Dados de Usuário Existente")
                edit_target = st.selectbox("Selecione o usuário para editar:", options=[u[0] for u in users_list])
                
                if edit_target:
                    # Busca os dados atuais do usuário selecionado
                    u_data = next((u for u in users_list if u[0] == edit_target), None)
                    if u_data:
                        curr_name = u_data[1]
                        curr_email = u_data[2] if u_data[2] else ""
                        
                        with st.form("edit_user_form"):
                            ed_name = st.text_input("Nome Completo", value=curr_name)
                            ed_email = st.text_input("E-mail", value=curr_email)
                            ed_pass = st.text_input("Nova Senha (Deixe em branco para não alterar)", type="password")
                            submit_edit_user = st.form_submit_button("Salvar Alterações")
                            
                            if submit_edit_user:
                                if not ed_name or not ed_email:
                                    st.warning("Nome e e-mail são obrigatórios.")
                                else:
                                    ok_ed, msg_ed = db.update_user_by_admin(edit_target, ed_name, ed_email, ed_pass)
                                    if ok_ed:
                                        st.success(msg_ed)
                                        st.rerun()
                                    else:
                                        st.error(msg_ed)

            with tab3:
                st.subheader("Ativar ou Inativar Usuários")
                df_users = pd.DataFrame(users_list, columns=["Usuário", "Nome Completo", "E-mail", "Ativo", "Troca Obrigatória"])
                st.dataframe(df_users, use_container_width=True)
                
                target_user = st.selectbox("Selecione o usuário para alterar status:", options=[u[0] for u in users_list if u[0] != "admin"], key="status_select")
                if target_user:
                    current_status = next((u[3] for u in users_list if u[0] == target_user), 1)
                    action_label = "Inativar Usuário" if current_status == 1 else "Reativar Usuário"
                    
                    if st.button(action_label):
                        new_status = 0 if current_status == 1 else 1
                        db.toggle_user_status(target_user, new_status)
                        st.success(f"Status do usuário {target_user} alterado com sucesso!")
                        st.rerun()
