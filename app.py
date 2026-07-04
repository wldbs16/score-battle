import streamlit as st
from datetime import date, datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import json

# 페이지 기본 설정
st.set_page_config(page_title="🤫 실시간 성적 배틀 (구글 로그인)", page_icon="🏆", layout="centered")

# -------------------------------------------------------------------------
# 🌍 데이터베이스 및 구글 로그인 세션 확인
# -------------------------------------------------------------------------
conn = st.connection("gsheets", type=GSheetsConnection)

def load_db():
    try:
        df = conn.read(ttl=0)
        return df.to_dict(orient="records")
    except:
        return []

def save_db(data_list):
    if not data_list:
        df = pd.DataFrame(columns=["room_id", "max_players", "subjects", "penalty", "d_day", "players", "scores", "player_emails"])
    else:
        df = pd.DataFrame(data_list)
    conn.update(data=df)

global_db = load_db()

# -------------------------------------------------------------------------
# 🔑 구글 로그인 상태 체크 및 로그인 유도
# -------------------------------------------------------------------------
if not st.user.is_logged_in:
    st.title("🏆 성적 서바이벌 온라인 배틀룸")
    st.subheader("🔒 이 앱은 안전한 구글 로그인이 필요합니다.")
    st.write("친구들과 공정하고 확실한 성적 배틀을 위해 구글 계정으로 인증해 주세요.")
    
    # 스트림릿 공식 구글 로그인 버튼 작동
    st.button("🔑 구글 계정으로 로그인하기", on_click=st.login, use_container_width=True)
    st.stop() # 로그인이 안 되어 있으면 아래 코드를 실행하지 않고 멈춤

# 로그인에 성공했다면 사용자의 구글 프로필 정보를 가져옴
user_email = st.user.email
user_name = st.user.name

# 기기 세션에 내 구글 정보 연동
if "my_room" not in st.session_state:
    st.session_state.my_room = None

# 상단 사이드바에 로그인 정보 표시 및 로그아웃 버튼 제공
with st.sidebar:
    st.markdown(f"### 👤 로그인 사용자\n**{user_name}** ({user_email})")
    if st.button("로그아웃"):
        st.logout()

# -------------------------------------------------------------------------
# 💡 [자동 이어하기 스캔] 이메일 주소로 과거에 참여하던 방이 있는지 체크
# -------------------------------------------------------------------------
if st.session_state.my_room is None:
    for r in global_db:
        # 구글 시트에 기록된 이메일 리스트 역직렬화
        emails = json.loads(r.get("player_emails", "[]"))
        if user_email in emails:
            st.session_state.my_room = str(r["room_id"])
            st.toast(f"🔄 하던 게임 발견! [{r['room_id']}]번 방으로 이어하기 접속합니다.")
            st.rerun()

# -------------------------------------------------------------------------
# [단계 1] 로그인 완료 후 방 입장/생성 선택 (참여 중인 방이 없을 때)
# -------------------------------------------------------------------------
if st.session_state.my_room is None:
    st.title("🏆 성적 서바이벌 멀티플레이 룸")
    st.write(f"👋 반가워요, **{user_name}**님! 방을 만들거나 이미 만들어진 방에 참여하세요.")
    st.markdown("---")
    
    menu = st.radio("원하는 작업을 선택하세요", ["👑 새 방 만들기 (대표자)", "🚪 만들어진 방 들어가기 (멤버)"])
    
    if menu == "👑 새 방 만들기 (대표자)":
        room_id = st.text_input("생성할 방 번호 (숫자/문자)", value="1234")
        max_p = st.number_input("총 인원 설정 (방장 포함)", min_value=2, max_value=10, value=3)
        
        st.markdown("#### 📝 이번 배틀에서 계산할 과목")
        subjects_input = st.text_input("과목 이름을 쉼표(,)로 구분해서 입력", value="국어, 영어, 수학")
        
        st.markdown("#### ☠️ 꼴등이 수행할 공포의 벌칙")
        penalty_input = st.text_input("벌칙 내용을 입력하세요", value="치킨 쏘기 🍗")
        
        st.markdown("#### 📅 성적 발표일 (D-Day) 지정")
        target_date = st.date_input("날짜를 선택하세요", value=date.today())
        
        if st.button("🔥 방 생성하고 입장", use_container_width=True):
            room_exists = any(str(r["room_id"]) == str(room_id) for r in global_db)
            
            if room_exists:
                st.error("이미 존재하는 방 번호입니다! 다른 번호를 쓰세요.")
            else:
                sub_list = [s.strip() for s in subjects_input.split(",") if s.strip()]
                if not sub_list:
                    st.error("과목을 최소 한 개 이상 입력해 주세요!")
                else:
                    new_room = {
                        "room_id": str(room_id),
                        "max_players": int(max_p),
                        "subjects": json.dumps(sub_list, ensure_ascii=False),
                        "penalty": penalty_input,
                        "d_day": target_date.strftime("%Y-%m-%d"),
                        "players": json.dumps([user_name], ensure_ascii=False), # 구글 닉네임 저장
                        "player_emails": json.dumps([user_email], ensure_ascii=False), # 구글 이메일 저장
                        "scores": json.dumps({}, ensure_ascii=False)
                    }
                    global_db.append(new_room)
                    save_db(global_db)
                    
                    st.session_state.my_room = str(room_id)
                    st.rerun()
                
    elif menu == "🚪 만들어진 방 들어가기 (멤버)":
        room_id = st.text_input("초대받은 방 번호 입력")
        
        if st.button("🚪 방 참가하기", use_container_width=True):
            target_room = None
            target_idx = -1
            for idx, r in enumerate(global_db):
                if str(r["room_id"]) == str(room_id):
                    target_room = r
                    target_idx = idx
                    break
            
            if target_room is None:
                st.error("존재하지 않는 방 번호입니다!")
            else:
                players = json.loads(target_room["players"])
                emails = json.loads(target_room.get("player_emails", "[]"))
                max_players = int(target_room["max_players"])
                
                # 중복 참가 방지 및 인원 체크
                if user_email in emails:
                    st.session_state.my_room = str(room_id)
                    st.rerun()
                elif len(players) >= max_players:
                    st.error("방 인원이 가득 찼습니다!")
                else:
                    players.append(user_name)
                    emails.append(user_email)
                    global_db[target_idx]["players"] = json.dumps(players, ensure_ascii=False)
                    global_db[target_idx]["player_emails"] = json.dumps(emails, ensure_ascii=False)
                    save_db(global_db)
                    
                    st.session_state.my_room = str(room_id)
                    st.rerun()

# -------------------------------------------------------------------------
# [단계 2] 방 입장 후 화면
# -------------------------------------------------------------------------
else:
    r_id = st.session_state.my_room
    
    room_data = None
    room_idx = -1
    for idx, r in enumerate(global_db):
        if str(r["room_id"]) == str(r_id):
            room_data = r
            room_idx = idx
            break
            
    if room_data is None:
        st.error("방 정보가 서버에서 유실되었거나 삭제되었습니다.")
        if st.button("처음으로 돌아가기"):
            st.session_state.my_room = None
            st.rerun()
    else:
        subjects = json.loads(room_data["subjects"])
        players = json.loads(room_data["players"])
        scores = json.loads(room_data["scores"])
        penalty = room_data["penalty"]
        max_players = int(room_data["max_players"])
        
        # 디데이 로직
        d_day_date = datetime.strptime(room_data["d_day"], "%Y-%m-%d").date()
        today = date.today()
        days_left = (d_day_date - today).days
        dday_text = f"D-{days_left}" if days_left > 0 else ("D-Day 당일!! 🔥" if days_left == 0 else f"정산일 지남 (+{abs(days_left)}일)")

        st.markdown(f"""<div style="background-color: #2ecc71; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 20px;"><h2 style="color: white; margin: 0;">⏳ 심판의 날: {dday_text}</h2></div>""", unsafe_allow_html=True)
        st.header(f"🏠 방 번호: [{r_id}]")
        st.markdown(f"💀 **이번 내기 벌칙:** <span style='color: #e74c3c; font-weight: bold;'>{penalty}</span>", unsafe_allow_html=True)
        st.write(f"📊 **배틀 과목:** {', '.join(subjects)}")
        st.markdown("---")
        
        if len(players) < max_players:
            st.warning("⏳ 다른 친구들이 접속하기를 기다리는 중입니다...")
            st.subheader("👥 현재 접속 완료한 멤버 목록")
            for idx, p in enumerate(players):
                st.write(f"{idx+1}. 👤 {p} (접속됨)")
            if st.button("🔄 새로고침 (친구 들어왔는지 확인)", use_container_width=True):
                st.rerun()
        else:
            st.success("✅ 인원이 모두 모였습니다! 점수를 입력하세요.")
            
            # 구글 이메일을 고유 키로 사용하여 성적 제출 여부 판단
            if user_email in scores:
                st.info("🔒 당신은 이미 성적을 최종 제출했습니다. 다른 사람의 마감을 기다리세요.")
                my_scores = scores[user_email]
            else:
                st.subheader(f"📝 [{user_name}] 님의 성적 입력")
                my_scores = {}
                for sub in subjects:
                    my_scores[sub] = st.number_input(f"점수 입력 ➡️ {sub}", min_value=0, max_value=100, value=80, key=f"score_{sub}")
                    
                if st.button("🔒 내 성적 최종 제출 (수정 불가)", use_container_width=True):
                    scores[user_email] = my_scores
                    global_db[room_idx]["scores"] = json.dumps(scores, ensure_ascii=False)
                    save_db(global_db)
                    st.success("성적이 안전하게 서버에 저장되었습니다!")
                    st.rerun()
            
            submitted_count = len(scores)
            st.markdown("---")
            st.subheader("📊 현재 성적 제출 현황")
            st.write(f"총 {max_players}명 중 {submitted_count}명 제출 완료")
            
            if submitted_count == max_players:
                st.error("🎉 모든 멤버가 성적을 제출했습니다!")
                if st.button("🏆 최종 결과 전광판 열기", use_container_width=True):
                    st.balloons()
                    results = {}
                    
                    # 이메일 기반 저장 구조를 이름 매칭 결과로 파싱
                    emails_list = json.loads(room_data["player_emails"])
                    for idx, email in enumerate(emails_list):
                        p_name = players[idx]
                        p_scores = scores.get(email, {})
                        avg = sum(p_scores.values()) / len(subjects) if p_scores else 0
                        results[p_name] = avg
                        
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
                        global_db.pop(room_idx)
                        save_db(global_db)
                        st.session_state.clear()
                        st.rerun()
            else:
                if st.button("🔄 친구들이 제출했는지 새로고침", use_container_width=True):
                    st.rerun()
