import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **population trends dataset**  
                  
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded)

        tabs = st.tabs([
            "1. 기초 통계",
            "2. 연도별 추이",
            "3. 지역별 분석",
            "4. 변화량 분석",
            "5. 시각화"
        ])

        # 1. 기초 통계
        with tabs[0]:
            st.header("✅ 원본 데이터 미리보기")
            st.dataframe(df.head())

            # '세종' 지역 필터링
            sejong_df = df[df['지역'].str.contains('세종', na=False)].copy()
            sejong_df.replace('-', 0, inplace=True)

            numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
            for col in numeric_cols:
                sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0)

            st.subheader("🧹 전처리된 '세종' 데이터")
            st.dataframe(sejong_df)

            st.subheader("📌 요약 통계")
            st.write(sejong_df[numeric_cols].describe())

            st.subheader("📌 데이터프레임 구조")
            buffer = io.StringIO()
            sejong_df.info(buf=buffer)
            st.text(buffer.getvalue())

        # 2. 연도별 추이
        with tabs[1]:
            st.header("📈 전국 인구 추이 및 2035 예측")

            df.replace('-', 0, inplace=True)
            for col in ['인구', '출생아수(명)', '사망자수(명)']:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

            nat_df = df[df['지역'] == '전국']
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.plot(nat_df['연도'], nat_df['인구'], marker='o', label='인구')

            recent = nat_df.sort_values('연도', ascending=False).head(3)
            net_growth = recent['출생아수(명)'].mean() - recent['사망자수(명)'].mean()
            last_year = nat_df['연도'].max()
            last_pop = nat_df[nat_df['연도'] == last_year]['인구'].values[0]
            predicted_pop = last_pop + net_growth * (2035 - last_year)

            ax.scatter(2035, predicted_pop, color='red', label='2035 예측')
            ax.annotate(f'{int(predicted_pop):,}', (2035, predicted_pop), textcoords="offset points", xytext=(0, 10), ha='center', color='red')

            ax.set_title('전국 인구 추이 및 2035 예측')
            ax.set_xlabel('연도')
            ax.set_ylabel('인구 수')
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)

        # 3. 지역별 분석
        with tabs[2]:
            st.header("📊 최근 5년 지역별 인구 변화")

            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            df.replace('-', 0, inplace=True)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df = df[df['지역'] != '전국']

            latest_year = df['연도'].max()
            recent_df = df[df['연도'].between(latest_year - 5, latest_year)]

            pivot = recent_df.pivot(index='지역', columns='연도', values='인구').dropna()
            pivot['Change'] = (pivot[latest_year] - pivot[latest_year - 5]) / 1000
            pivot['Rate (%)'] = ((pivot[latest_year] - pivot[latest_year - 5]) / pivot[latest_year - 5]) * 100
            pivot['Region'] = pivot.index.map(region_map)

            st.subheader("📉 인구 변화량 (천 명 단위)")
            fig1, ax1 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=pivot.sort_values('Change', ascending=False), y='Region', x='Change', palette='Blues_r', ax=ax1)
            st.pyplot(fig1)

            st.subheader("📈 인구 변화율 (%)")
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=pivot.sort_values('Rate (%)', ascending=False), y='Region', x='Rate (%)', palette='coolwarm', ax=ax2)
            st.pyplot(fig2)

        # 4. 변화량 분석
        with tabs[3]:
            st.header("📊 연도별 인구 증감 상위 100")

            df.replace('-', 0, inplace=True)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
            df = df[df['지역'] != '전국']
            df_sorted = df.sort_values(['지역', '연도'])
            df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()

            top_diff = df_sorted.dropna().sort_values('증감', key=lambda x: abs(x), ascending=False).head(100).copy()
            top_diff['인구'] = top_diff['인구'].apply(lambda x: f"{int(x):,}")
            top_diff['증감'] = top_diff['증감'].apply(lambda x: f"{int(x):,}")

            def color_diff(val):
                try:
                    val_num = int(val.replace(",", ""))
                    return f'background-color: {"#FFCCCC" if val_num < 0 else "#CCFFCC"}'
                except:
                    return ''

            st.dataframe(top_diff[['연도', '지역', '인구', '증감']].style.applymap(color_diff, subset=['증감']), use_container_width=True)

        # 5. 시각화
        with tabs[4]:
            st.header("📊 지역별 인구 추이 누적 그래프")

            df.replace('-', 0, inplace=True)
            df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)

            region_map = {
                "전국": "Total", "서울": "Seoul", "부산": "Busan", "대구": "Daegu",
                "인천": "Incheon", "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan",
                "세종": "Sejong", "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk",
                "충남": "Chungnam", "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk",
                "경남": "Gyeongnam", "제주": "Jeju"
            }
            df['Region'] = df['지역'].map(region_map)

            pivot_df = df[df['지역'] != '전국'].pivot(index='연도', columns='Region', values='인구').dropna(axis=1)
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df.plot.area(ax=ax, cmap="tab20", alpha=0.85)

            ax.set_title("지역별 인구 추이 (누적)", fontsize=16)
            ax.set_xlabel("연도")
            ax.set_ylabel("인구 수")
            ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()
            st.pyplot(fig)


        


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()