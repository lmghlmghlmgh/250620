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
                **Bike Sharing Demand 데이터셋**  
                - 제공처: [Kaggle Bike Sharing Demand Competition](https://www.kaggle.com/c/bike-sharing-demand)  
                - 설명: 2011–2012년 캘리포니아 주의 수도인 미국 워싱턴 D.C. 인근 도시에서 시간별 자전거 대여량을 기록한 데이터  
                - 주요 변수:  
                  - `datetime`: 날짜 및 시간  
                  - `season`: 계절  
                  - `holiday`: 공휴일 여부  
                  - `workingday`: 근무일 여부  
                  - `weather`: 날씨 상태  
                  - `temp`, `atemp`: 기온 및 체감온도  
                  - `humidity`, `windspeed`: 습도 및 풍속  
                  - `casual`, `registered`, `count`: 비등록·등록·전체 대여 횟수  
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
        st.title("📊 population EDA")
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

        # 1. 목적 & 분석 절차
        with tabs[0]:
            
            st.title("📊 인구 통계 데이터 전처리 및 분석")

            uploaded_file = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])

            if uploaded_file is not None:
                # 파일 읽기
                df = pd.read_csv(uploaded_file)

                st.subheader("✅ 원본 데이터 미리보기")
                st.dataframe(df.head())

                # '세종' 지역 필터링
                sejong_df = df[df['행정구역'].str.contains('세종', na=False)].copy()

                # '-'를 0으로 바꾸기
                sejong_df.replace('-', 0, inplace=True)

                # 숫자로 변환할 열
                numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']

                for col in numeric_cols:
                    if col in sejong_df.columns:
                        sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0)

                st.subheader("🧹 전처리된 '세종' 데이터")
                st.dataframe(sejong_df)

                st.subheader("📌 데이터 요약 통계 (`describe()`)")
                st.write(sejong_df[numeric_cols].describe())

                st.subheader("📌 데이터프레임 구조 (`info()`)")
                # df.info()는 콘솔 출력만 가능하므로 문자열로 캡처
                buffer = io.StringIO()
                sejong_df.info(buf=buffer)
                info_str = buffer.getvalue()
                st.text(info_str)

        # 2. 데이터셋 설명
        with tabs[1]:
            
            st.title("📈 National Population Trend and 2035 Projection")

            uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

                # '-' 처리 및 숫자 변환
                df.replace('-', 0, inplace=True)
                for col in ['인구', '출생아수(명)', '사망자수(명)']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

                # 전국 데이터 필터링
                nat_df = df[df['지역'] == '전국'].copy()

                # 연도별 인구 추이 그래프
                fig, ax = plt.subplots(figsize=(10, 6))
                ax.plot(nat_df['연도'], nat_df['인구'], marker='o', label='Population')

                # 최근 3년 평균 출생아수, 사망자수 계산
                recent = nat_df.sort_values('연도', ascending=False).head(3)
                avg_birth = recent['출생아수(명)'].mean()
                avg_death = recent['사망자수(명)'].mean()
                net_growth = avg_birth - avg_death

                # 예측: 2035년 = 마지막 연도 기준 + (net_growth * 연도 수)
                last_year = nat_df['연도'].max()
                last_pop = nat_df[nat_df['연도'] == last_year]['인구'].values[0]
                years_to_project = 2035 - last_year
                predicted_pop = last_pop + net_growth * years_to_project

                # 2035년 예측값 그래프에 추가
                ax.scatter(2035, predicted_pop, color='red', label='2035 Projection')
                ax.annotate(f'{int(predicted_pop):,}', (2035, predicted_pop), textcoords="offset points",
                            xytext=(0, 10), ha='center', color='red')

                # 그래프 스타일
                ax.set_title('Population Trend (National)')
                ax.set_xlabel('Year')
                ax.set_ylabel('Population')
                ax.legend()
                ax.grid(True)

                st.pyplot(fig)

        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            
            st.set_option('deprecation.showPyplotGlobalUse', False)
            st.title("📈 Regional Population Trends (Last 5 Years)")

            uploaded_file = st.file_uploader("Upload your population_trends.csv file", type=["csv"])

            # 지역명 매핑
            region_map = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
    
                # 전처리
                df.replace('-', 0, inplace=True)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
                df = df[df['지역'] != '전국']

                latest_year = df['연도'].max()
                five_years_ago = latest_year - 5
                df_recent = df[df['연도'].between(five_years_ago, latest_year)]

                pivot = df_recent.pivot(index='지역', columns='연도', values='인구')
                pivot = pivot.dropna()

                pivot['Change'] = (pivot[latest_year] - pivot[five_years_ago]) / 1000  # 천명 단위
                pivot['Rate (%)'] = ((pivot[latest_year] - pivot[five_years_ago]) / pivot[five_years_ago]) * 100
                pivot['Region'] = pivot.index.map(region_map)
    
                # ===== 📊 인구 변화량 그래프 =====
                sorted_by_change = pivot.sort_values('Change', ascending=False)

                st.subheader("Population Change by Region (in thousands)")
                fig1, ax1 = plt.subplots(figsize=(10, 8))
                sns.barplot(data=sorted_by_change, y='Region', x='Change', palette='Blues_r', ax=ax1)
                for i, val in enumerate(sorted_by_change['Change']):
                    ax1.text(val + 1, i, f"{val:.1f}", va='center')
                ax1.set_title("Population Change (Last 5 Years)", fontsize=14)
                ax1.set_xlabel("Change (in thousands)")
                ax1.set_ylabel("Region")
                st.pyplot(fig1)

                # ===== 📊 인구 변화율 그래프 =====
                sorted_by_rate = pivot.sort_values('Rate (%)', ascending=False)

                st.subheader("Population Change Rate by Region (%)")
                fig2, ax2 = plt.subplots(figsize=(10, 8))
                sns.barplot(data=sorted_by_rate, y='Region', x='Rate (%)', palette='coolwarm', ax=ax2)
                for i, val in enumerate(sorted_by_rate['Rate (%)']):
                    ax2.text(val + 0.5, i, f"{val:.1f}%", va='center')
                ax2.set_title("Population Growth Rate (%)", fontsize=14)
                ax2.set_xlabel("Growth Rate (%)")
                ax2.set_ylabel("Region")
                st.pyplot(fig2)

                # ===== 📘 해설 =====
                st.markdown("### 📘 Interpretation")
                st.write(f"- Region **{sorted_by_rate.iloc[0]['Region']}** showed the highest population growth rate in the past 5 years.")
                st.write(f"- Region **{sorted_by_rate.iloc[-1]['Region']}** experienced the largest decline in population rate.")
                st.write("- This analysis reflects regional demographic trends and may relate to factors such as migration, birth rates, and local policies.")


            

        # 4. Datetime 특성 추출
        with tabs[3]:
            
            st.title("📊 Top 100 Population Changes by Year and Region")

            uploaded_file = st.file_uploader("Upload population_trends.csv", type=["csv"])

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)
    
                # 전처리
                df.replace('-', 0, inplace=True)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0)
                df = df[df['지역'] != '전국']  # 전국 제외
    
                # 연도순 정렬 후 diff 계산
                df_sorted = df.sort_values(['지역', '연도'])
                df_sorted['증감'] = df_sorted.groupby('지역')['인구'].diff()

                # 상위 100개 추출 (증가/감소 포함)
                top_diff = df_sorted.dropna().sort_values('증감', key=lambda x: abs(x), ascending=False).head(100).copy()

                # 천 단위 콤마 추가
                top_diff['인구'] = top_diff['인구'].apply(lambda x: f"{int(x):,}")
                top_diff['증감'] = top_diff['증감'].apply(lambda x: f"{int(x):,}")

                # 컬러바 스타일 함수 정의
                def color_diff(val):
                    try:
                        val_num = int(val.replace(",", ""))
                        color = f'background-color: rgb({255 if val_num < 0 else 0}, {0 if val_num < 0 else 128}, {0 if val_num < 0 else 255}, 0.3)'
                        return color
                    except:
                        return ''
    
                st.subheader("📌 Top 100 Yearly Population Changes (excluding national data)")

                styled_df = top_diff[['연도', '지역', '인구', '증감']].style.applymap(color_diff, subset=['증감'])
                st.dataframe(styled_df, use_container_width=True)

        # 5. 시각화
        with tabs[4]:
            
            # 앱 제목
            st.title("Population Trends by Region (Stacked Area Chart)")

            # CSV 파일 로드
            csv_file = "population_trends.csv"  # 파일 경로를 여기에 맞게 설정
            df = pd.read_csv(csv_file)

            # 한글 컬럼명 → 영문 컬럼명 변경
            df.rename(columns={
                "연도": "Year",
                "지역": "Region",
                "인구": "Population",
                "출생아수(명)": "Births",
                "사망자수(명)": "Deaths"
            }, inplace=True)

            # 지역명 한글 → 영문 매핑
            region_map = {
                "전국": "Total",
                "서울": "Seoul",
                "부산": "Busan",
                "대구": "Daegu",
                "인천": "Incheon",
                "광주": "Gwangju",
                "대전": "Daejeon",
                "울산": "Ulsan",
                "세종": "Sejong",
                "경기": "Gyeonggi",
                "강원": "Gangwon",
                "충북": "Chungbuk",
                "충남": "Chungnam",
                "전북": "Jeonbuk",
                "전남": "Jeonnam",
                "경북": "Gyeongbuk",
                "경남": "Gyeongnam",
                "제주": "Jeju"
            }
            df["Region"] = df["Region"].map(region_map)

            # 피벗 테이블 생성 (행: 연도, 열: 지역)
            pivot_df = df.pivot(index="Year", columns="Region", values="Population")

            # NaN 값 제거
            pivot_df.dropna(axis=1, inplace=True)

            # 누적 영역 그래프 그리기
            fig, ax = plt.subplots(figsize=(12, 6))
            pivot_df.plot.area(ax=ax, cmap="tab20", alpha=0.85)

            ax.set_title("Population Trends by Region", fontsize=16)
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
            plt.tight_layout()

            # 그래프 출력
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