import streamlit as st
from datetime import date

# 페이지 기본 설정
st.set_page_config(page_title="🤫 실시간 성적 배틀 앱", page_icon="🏆", layout="centered")

# -------------------------------------------------------------------------
# 🌍 전역 데이터베이스 역할 (인터넷으로 접속한 모든 기기가 이 메모리를 공유함)
# -------------------------------------------------------------------------
if "global_rooms" not in st.session_state:
    st.session_state.global_rooms = {} 

# 💻 현재 접속한 '내 기기'의 로그인 상태
if "my_room" not in st.session_state:
    st.session_state.my_room = None
    st.session_state.my_name = None

st.title("🏆 성적 서바이벌 멀티플레이 룸")
st.caption("방장이 정한 과목과 벌칙, 디데이를 보며 실시간으로 배틀을 즐기세요!")
st.markdown("---")

# -------------------------------------------------------------------------
# [단계 1] 로그인 / 방 입장 화면 (아직 방에 안 들어갔을 때)
# -------------------------------------------------------------------------
if st.session_state.my_room is None:
    menu = st.radio("원하는 작업을 선택하세요", ["👑 새 방 만들기 (대표자)", "🚪 만들어진 방 들어가기 (멤버)"])
    
    if menu == "👑 새 방 만들기 (대표자)":
        room_id = st.text_input("생성할 방 번호 (숫자/문자)", value="1234")
        max_p = st.number_input("총 인원 설정 (방장 포함)", min_value=2, max_value=10, value=3)
        
        # 📊 내기할 과목 직접 입력받기
        st.markdown("#### 📝 이번 배틀에서 계산할 과목")
        subjects_input = st.text_input("과목 이름을 쉼표(,)로 구분해서 입력", value="국어, 영어, 수학")
        
        # 🚨 공포의 벌칙 설정
        st.markdown("#### ☠️ 꼴등이 수행할 공포의 벌칙")
        penalty_input = st.text_input("벌칙 내용을 입력하세요", value="치킨 쏘기 🍗")
        
        # 📅 성적 발표일 (D-Day) 지정
        st.markdown("#### 📅 성적 발표일 (D-Day) 지정")
        target_date = st.date_input("날짜를 선택하세요", value=date.today())
        
        if st.button("🔥 방 생성하고 입장", use_container_width=True):
            if room_id in st.session_state.global_rooms:
                st.error("이미 존재하는 방 번호입니다! 다른 번호를 쓰세요.")
            else:
                sub_list = [s.strip() for s in subjects_input.split(",") if s.strip()]
                if not sub_list:
                    st.error("과목을 최소 한 개 이상 입력해 주세요!")
                else:
                    st.session_state.global_rooms[room_id] = {
                        "max_players": max_p,
                        "subjects": sub_list,
                        "penalty": penalty_input,
                        "d_day": target_date,
                        "players": ["방장"],
                        "scores": {}
                    }
                    st.session_state.my_room = room_id
                    st.session_state.my_name = "방장"
                    st.rerun()
                
    elif menu == "🚪 만들어진 방 들어가기 (멤버)":
        room_id = st.text_input("초대받은 방 번호 입력")
        my_name = st.text_input("내 이름(닉네임) 입력")
        
        if st.button("🚪 방 참가하기", use_container_width=True):
            if room_id not in st.session_state.global_rooms:
                st.error("존재하지 않는 방 번호입니다!")
            elif my_name in st.session_state.global_rooms[room_id]["players"]:
                st.error("이미 방에 존재하는 이름입니다! 다른 닉네임을 쓰세요.")
            elif len(st.session_state.global_rooms[room_id]["players"]) >= st.session_state.global_rooms[room_id]["max_players"]:
                st.error("방 인원이 가득 찼습니다!")
            elif room_id and my_name:
                st.session_state.global_rooms[room_id]["players"].append(my_name)
                st.session_state.my_room = room_id
                st.session_state.my_name = my_name
                st.rerun()

# -------------------------------------------------------------------------
# [단계 2] 로그인 후 화면 (자기 기기 화면)
# -------------------------------------------------------------------------
else:
    r_id = st.session_state.my_room
    m_name = st.session_state.my_name
    room_data = st.session_state.global_rooms[r_id]
    
    subjects = room_data["subjects"]
    penalty = room_data["penalty"]
    d_day_date = room_data["d_day"]
    
    # 디데이 실시간 계산 및 색상 변경 로직
    today = date.today()
    days_left = (d_day_date - today).days
    
    if days_left > 7:
        dday_color = "#2ecc71"  # 초록색
        dday_text = f"D-{days_left}"
    elif 0 < days_left <= 7:
        dday_color = "#e67e22"  # 주황색
        dday_text = f"D-{days_left} (얼마 안 남음!)"
    elif days_left == 0:
        dday_color = "#e74c3c"  # 빨간색
        dday_text = "D-Day 당일!! 🔥"
    else:
        dday_color = "#7f8c8d"  # 지난 날짜
        dday_text = f"정산일 지남 (+{abs(days_left)}일)"

    st.markdown(
        f"""
        <div style="background-color: {dday_color}; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;">
            <h2 style="color: white; margin: 0;">⏳ 심판의 날: {dday_text}</h2>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    st.header(f"🏠 방 번호: [{r_id}] | 나의 계정: [{m_name}]")
    st.markdown(f"💀 **이번 내기 벌칙:** <span style='color: #e74c3c; font-weight: bold;'>{penalty}</span>", unsafe_allow_html=True)
    st.write(f"📊 **배틀 과목:** {', '.join(subjects)}")
    st.markdown("---")
    
    # 인원이 다 찰 때까지 대기
    if len(room_data["players"]) < room_data["max_players"]:
        st.warning("⏳ 다른 친구들이 접속하기를 기다리는 중입니다...")
        st.subheader("👥 현재 접속 완료한 멤버 목록")
        for idx, p in enumerate(room_data["players"]):
            st.write(f"{idx+1}. 👤 {p} (접속됨)")
            
        st.info(f"💡 설정 인원 {room_data['max_players']}명이 다 차면 자동으로 점수 입력창이 열립니다.")
        
        if st.button("🔄 새로고침 (친구 들어왔는지 확인)"):
            st.rerun()
            
    # 인원이 다 차면 점수 입력
    else:
        st.success("✅ 인원이 모두 모였습니다! 점수를 입력하세요.")
        st.subheader(f"📝 [{m_name}] 님의 성적 입력")
        st.write("오직 당신의 입력창만 보입니다. 비밀번호 치듯 조용히 입력하세요!")
        
        my_scores = {}
        for sub in subjects:
            my_scores[sub] = st.number_input(f"점수 입력 ➡️ {sub}", min_value=0, max_value=100, value=80, key=f"score_{sub}")
            
        if st.button("🔒 내 성적 최종 제출 (수정 불가)", use_container_width=True):
            st.session_state.global_rooms[r_id]["scores"][m_name] = my_scores
            st.success("성적이 안전하게 저장되었습니다! 다른 사람들의 제출을 기다리세요.")
            
        submitted_count = len(room_data["scores"])
        
        st.markdown("---")
        st.subheader("📊 현재 성적 제출 현황")
        st.write(f"총 {room_data['max_players']}명 중 {submitted_count}명 제출 완료")
        
        # 모두 제출했다면 결과 공개
        if submitted_count == room_data["max_players"]:
            st.error("🎉 모든 멤버가 성적을 제출했습니다!")
            if st.button("🏆 최종 결과 전광판 열기", use_container_width=True):
                st.balloons()
                
                results = {}
                for name in room_data["players"]:
                    p_scores = room_data["scores"][name]
                    avg = sum(p_scores.values()) / len(subjects)
                    results[name] = avg
                    
                sorted_res = sorted(results.items(), key=lambda x: x[1], reverse=True)
                
                st.markdown("---")
                st.markdown("## 👑 최종 배틀 결과 순위 👑")
                
                for rank, (name, avg) in enumerate(sorted_res):
                    if rank == 0:
                        st.success(f"🥇 1등: {name} (평균 {avg:.1f}점) - 벌칙 대면제!! 🥳")
                    elif rank == len(sorted_res) - 1:
                        st.error(f"💀 꼴등: {name} (평균 {avg:.1f}점) ➡️ 당첨된 벌칙: [{penalty}]")
                    else:
                        st.write(f"• {rank+1}등: {name} (평균 {avg:.1f}점)")
                        
                if st.button("🔄 방 폭파 및 처음으로 돌아가기"):
                    st.session_state.clear()
                    st.rerun()
        else:
            if st.button("🔄 친구들이 제출했는지 새로고침"):
                st.rerun()