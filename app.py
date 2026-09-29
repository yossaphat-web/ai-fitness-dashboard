import streamlit as st
import pandas as pd
import plotly.express as px
import google.generativeai as genai

# 1. ตั้งค่าหน้าเพจ
st.set_page_config(page_title="AI Fitness Matrix", layout="wide", page_icon="⚡")
st.title("⚡ AI-Powered Fitness & Recovery Matrix")

# 2. แถบเมนูด้านข้างสำหรับใส่ข้อมูลส่วนตัว
with st.sidebar:
    st.header("⚙️ System Settings")
    st.write("ใส่กุญแจ 2 ดอกที่คุณเตรียมไว้ที่นี่")
    csv_url = st.text_input("🔗 Google Sheets CSV Link", type="password")
    api_key = st.text_input("🔑 Gemini API Key", type="password")
    st.markdown("---")
    st.info("แดชบอร์ดนี้ใช้ AI วิเคราะห์ข้อมูลสุขภาพและการฝึกซ้อมของคุณแบบ Real-time")

# 3. ตรวจสอบว่าใส่ข้อมูลครบหรือยัง
if csv_url and api_key:
    try:
        # ดึงข้อมูลจาก Google Sheets
        df = pd.read_csv(csv_url)
        
        # จัดการข้อมูลเบื้องต้น
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        latest_data = df.iloc[-1] # ดึงข้อมูลวันล่าสุด
        
        # 4. ส่วนแสดงผล KPI ด้านบน
        st.subheader("📊 ภาวะร่างกายปัจจุบัน (Latest Status)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("ความสดชื่น (Readiness)", f"{latest_data['Readiness_Score']}/100", 
                    delta=f"{int(latest_data['Readiness_Score'] - df.iloc[-2]['Readiness_Score'])}")
        col2.metric("ความล้ากล้ามเนื้อ (Fatigue)", f"{latest_data['Muscle_Fatigue_1_to_10']}/10", 
                    delta=f"{round(latest_data['Muscle_Fatigue_1_to_10'] - df.iloc[-2]['Muscle_Fatigue_1_to_10'], 1)}", delta_color="inverse")
        col3.metric("โปรตีนล่าสุด", f"{latest_data['Protein_Intake_g']} g")
        col4.metric("เวลานอนล่าสุด", f"{latest_data['Sleep_Hours']} hrs")

        st.markdown("---")

        # 5. กราฟฟิก (Visualizations)
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("📈 แนวโน้มความพร้อมของร่างกาย")
            fig1 = px.line(df, x='Date', y='Readiness_Score', markers=True, template="plotly_dark", line_shape="spline")
            fig1.update_traces(line_color='#00FFAA')
            st.plotly_chart(fig1, use_container_width=True)

        with col_chart2:
            st.subheader("💪 ปริมาณโปรตีนเทียบกับความล้า")
            fig2 = px.scatter(df, x='Protein_Intake_g', y='Muscle_Fatigue_1_to_10', size='Workout_Duration_min', 
                              color='Workout_Type', template="plotly_dark", hover_name='Date')
            st.plotly_chart(fig2, use_container_width=True)

        # 6. ส่วนของ AI วิเคราะห์ (Gemini AI Brain)
        st.markdown("---")
        st.header("🧠 AI Personal Coach Analysis")
        
        if st.button("วิเคราะห์ตารางฝึกด้วย AI ตอนนี้!"):
            with st.spinner("AI กำลังวิเคราะห์ข้อมูลร่างกายย้อนหลัง 30 วันของคุณ..."):
                genai.configure(api_key=api_key)
                # ให้ระบบค้นหาโมเดลที่ API Key นี้มีสิทธิ์ใช้งานได้อัตโนมัติ
                valid_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                
                if not valid_models:
                    st.error("API Key นี้ไม่ได้รับสิทธิ์ให้ใช้งาน AI (อาจต้องตรวจสอบการตั้งค่าใน Google AI Studio)")
                    st.stop()
                
                # เลือกใช้งานโมเดลตัวแรกที่ระบบอนุญาต
                model = genai.GenerativeModel(valid_models[0])
                
                prompt = f"""
                คุณคือโค้ชฟิตเนสผู้เชี่ยวชาญด้านวิทยาศาสตร์การกีฬา
                นี่คือข้อมูลสรุปร่างกายของฉัน:
                - ความสดชื่นล่าสุด: {latest_data['Readiness_Score']}/100
                - ความล้าสะสม: {latest_data['Muscle_Fatigue_1_to_10']}/10
                - การนอนล่าสุด: {latest_data['Sleep_Hours']} ชั่วโมง
                - การกินโปรตีนเฉลี่ยสัปดาห์นี้: {df.tail(7)['Protein_Intake_g'].mean():.0f} กรัม
                
                จากข้อมูลนี้:
                1. ร่างกายฉันตอนนี้อยู่ในสภาวะไหน? (Overtraining, พร้อมฝึก, หรือต้องพัก)
                2. แนะนำตารางออกกำลังกายสำหรับวันนี้ให้หน่อย ควรเล่นแนวไหน (คาร์ดิโอ, เวทเทรนนิ่ง หรือพัก) พร้อมเหตุผลสั้นๆ
                ขอคำตอบแบบมืออาชีพ กระชับ และอ่านง่าย (ใช้ภาษาไทย)
                """
                
                response = model.generate_content(prompt)
                st.success("AI วิเคราะห์เสร็จสิ้น!")
                st.info(response.text)

    except Exception as e:
        st.error(f"เกิดข้อผิดพลาดในการดึงข้อมูล กรุณาตรวจสอบลิงก์ CSV อีกครั้ง (Error: {e})")
else:
    st.warning("👈 กรุณาใส่ Google Sheets CSV Link และ Gemini API Key ที่แถบด้านซ้ายเพื่อเริ่มต้นระบบ")
