import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
import csv
import folium
from folium.plugins import MarkerCluster
from folium.plugins import HeatMap
import math
import json
import requests
import pprint
import ast
import streamlit as st
from streamlit_folium import st_folium

mpl.rc('font', family='Malgun Gothic')

### 데이터셋 읽어오기
df_cctv = pd.read_csv('data/서울시 cctv 위치 데이터.csv', header=None)
df_al = pd.read_excel('data/12_04_09_E_안전비상벨위치정보.xlsx')
df_child = pd.read_csv('data/어린이보호구역 위치도.csv', encoding='cp949')
# 서울시 경찰서 위치 데이터 컬럼 수가 안 맞아 pandas로 읽을 수 없음
f = open('data/경찰청_경찰관서위치정보(지구대 파출소포함)_20230630.csv', encoding='utf-8')
reader = csv.reader(f)
csv_list = []
for line in reader:
    if line[0][0] == '\\':
        tmp = line[0][1:]
        line = line[1:]
        line[0] = tmp + line[0][:-3]
    csv_list.append(line)
f.close()
df_p = pd.DataFrame(csv_list)
df_call = pd.read_csv('data/경찰청 서울특별시경찰청_경찰서별 112신고출동 현황_20230530.csv', encoding='cp949')
df_po = pd.read_csv('data/경찰청 서울특별시경찰청_경찰서별 경찰관 수 현황_20221231.csv', encoding='cp949')
df_age = pd.read_csv('data/범죄통계원표(경찰서별 피해자 연령대).csv', header=None)
df_pp = pd.read_csv('data/LOCAL_PEOPLE_GU_2019.csv', encoding='cp949')
# df_sz = pd.read_csv('data/12_22_schoolzone(스쿨존 어린이 사고다발지).csv', encoding='cp949')
df_wc = pd.read_csv('data/12_22_child(보행어린이 사고다발지).csv', encoding='cp949')
### -----

### 데이터 전처리
## df_cctv (서울시 CCTV 설치 현황) -> df_cctv2
# df_cctv의 컬럼명 변경
df_cctv.columns = ['번호', '자치구명', '안심주소', 'CCTV용도', '위도', '경도', 'CCTV수량', '수정일시',
       '경찰서명', '경찰서부서명', '경찰서부서코드', '시도경찰청명']
# 불필요한 컬럼 제거
df_cctv2 = df_cctv.drop(['번호', '수정일시', '경찰서부서코드', '경찰서부서명', '시도경찰청명'], axis=1)
# 컬럼명 통일 (자치구명 -> 자치구)
df_cctv2.rename(columns={'자치구명': '자치구'}, inplace=True)

## df_al (서울시 안전비상벨 위치 정보) -> df_al3
# 불필요한 컬럼 제거
df_al2 = df_al.drop(['안전비상벨관리번호', '소재지도로명주소', '소재지지번주소', '번호', '관리기관전화번호', '데이터기준일자'], axis=1)
# 안전비상벨 설치 연도가 2019년 이하인 데이터들만 사용
df_al3 = df_al2[df_al2['안전비상벨설치연도'] <= 2019]
# 자치구 컬럼 만들기 위한 딕셔너리
gu_dict = {'강남구청 재난안전과': '강남구', 
           '관악구청': '관악구',
           '서울특별시 강남구청 재난안전과': '강남구',
           '서울시성북구청도시안전과': '성북구',
           '서울특별시 영등포구청': '영등포구',
           '강동구청': '강동구',
           '서울특별시 중랑구청': '중랑구',
           '마포구청': '마포구',
           '서울특별시 강서구청': '강서구',
           '서울특별시 성동구청': '성동구',
           '서울특별시 구로구청': '구로구',
           '서울특별시 양천구청': '양천구',
           '광진구청': '광진구',
           '동대문구청 스마트도시과': '동대문구',
           '금천구 U-통합운영센터': '금천구',
           '서울특별시 동작구청': '동작구',
           '서울특별시 중구청': '중구',
           '용산구청': '용산구',
           '서울특별시 은평구청': '은평구',
           '서대문구청 자치행정과': '서대문구',
           '서대문구청 푸른도시과': '서대문구',
           '종로구청': '종로구',
           '노원구청': '노원구',
           '강남구청 공원녹지과': '강남구',
           '은평구청 자원순환과': '은평구',
           '동대문구청 청소행정과': '동대문구',
           '서대문구청 교통관리과': '서대문구',
           '서울특별시 강동구': '강동구',
           '서대문구청 교통행정과': '서대문구',
           '강북구청 공원녹지과': '강북구',
           '종로구청 청소행정과': '종로구',
           '서초구청': '서초구',
           '서울시성북구청청소행정과': '성북구',
           '서울시성북구청공원녹지과': '성북구',
           '서대문구청 교육지원과': '서대문구',
           '은평구청 공원녹지과': '은평구',
           '서대문구청 안전치수과': '서대문구',
           '서울시성북구청교통지도과': '성북구',
           '강남구청 청소행정과': '강남구'}
# 자치구 컬럼 생성
df_al3['자치구'] = df_al3['관리기관명'].apply(lambda x: gu_dict[x])

## df_child (서울시 어린이보호구역 위치 정보) -> df_child2
# 불필요한 컬럼 제거
df_child2 = df_child.drop(['아이디', '관리번호'], axis=1)
df_child2.rename(columns={'y좌표': '위도', 'x좌표': '경도'}, inplace=True)
# 자치구 컬럼 만들기 위한 딕셔너리
gu_dict_child = {'노원서': '노원구',
                 '양천경찰서': '양천구',
                 '송파경찰서': '송파구',
                 '강동경찰서': '강동구',
                 '광진경찰서': '광진구',
                 '강서경찰서': '강서구',
                 '수서경찰서': '강남구',
                 '영등포경찰서': '영등포구',
                 '서울관악경찰서': '관악구',
                 '도봉경찰서': '도봉구',
                 '동대문경찰서': '동대문구',
                 '구로경찰서': '구로구',
                 '동작경찰서': '동작구',
                 '서울특별시 성북경찰서': '성북구',
                 '마포경찰서': '마포구',
                 '금천경찰서': '금천구',
                 '성동경찰서': '성동구',
                 '은평경찰서': '은평구',
                 '중랑경찰서': '중랑구',
                 '강북경찰서': '강북구',
                 '서초경찰서': '서초구',
                 '서울특별시 서대문경찰서': '서대문구',
                 '서울특별시 종암경찰서': '성북구',
                 '서부경찰서': '은평구',
                 '용산': '용산구',
                 '강남경찰서': '강남구',
                 '서울중부경찰서': '중구',
                 '종로경찰서': '종로구',
                 '방배경찰서': '서초구',
                 '혜화경찰서': '종로구',
                 '서울남대문경찰서': '중구',
                 '용산서': '용산구'}
# 자치구 컬럼 생성
df_child2['자치구'] = df_child2['관할경찰서'].apply(lambda x: gu_dict_child[x])

## df_p (서울시 경찰서 위치 정보) -> df_p5
# 컬럼명 설정
df_p.columns = df_p.loc[0]
df_p2 = df_p[1:]
# 불필요한 컬럼 삭제
df_p3 = df_p2[['\ufeffinputaddr', 'lng', 'lat']]
df_p3.rename(columns={'\ufeffinputaddr': '주소', 'lng': '경도', 'lat': '위도'}, inplace=True)
# 서울시에 해당하는 데이터만 사용
df_p4 = df_p3[df_p3['주소'].str.contains('서울특별시')]
# 위도 혹은 경도가 공백인 행은 삭제
df_p5 = df_p4.drop(df_p4[(df_p4['위도'] == '') | (df_p4['경도'] == '')].index)
# 자치구 컬럼  생성
df_p5['자치구'] = df_p5['주소'].apply(lambda x: x.split(' ')[1])

## df_call (서울시 경찰서별 112신고출동 현황) -> df_call2
gu = ['서초구', '금천구', '관악구', '강남구', '송파구', '구로구', '동작구', '영등포구', '양천구',
       '용산구', '강동구', '광진구', '강서구', '성동구', '마포구', '중구', '서대문구', '동대문구',
       '종로구', '중랑구', '은평구', '성북구', '강북구', '노원구', '도봉구']
def police_to_gu(data):   
    if data + '구' in gu:
        return data + '구'
    elif data == '남대문':
        return '중구'
    elif data == '방배':
        return '서초구'
    elif data == '서부':
        return '은평구'
    elif data == '수서':
        return '강남구'
    elif data == '종암':
        return '성북구'
    elif data == '중부':
        return '중구'
    elif data == '혜화':
        return '종로구'
# 2019년도 데이터만 사용
df_call2 = df_call[['경찰서', '2019']]
# 자치구 컬럼 생성
df_call2['자치구'] = df_call2['경찰서'].apply(police_to_gu)

## df_po (서울시 경찰서별 경찰관 수 현황) -> df_po2
# 2019년도 데이터만 사용
df_po2 = df_po[['경찰서', '2019년']]
# 자치구 컬럼 생성
df_po2['자치구'] = df_po2['경찰서'].apply(police_to_gu)

## df_age (경찰서별 연령대별 피해자) -> df_age3
def police_to_gu_age(data):
    tmp = data[2:-3]
   
    if tmp + '구' in gu:
        return tmp + '구'
    elif tmp == '남대문':
        return '중구'
    elif tmp == '방배':
        return '서초구'
    elif tmp == '서부':
        return '은평구'
    elif tmp == '수서':
        return '강남구'
    elif tmp == '종암':
        return '성북구'
    elif tmp == '중부':
        return '중구'
    elif tmp == '혜화':
        return '종로구'
# 컬럼명 변경
col = ['작성년월',
       '작성경찰서명',
       '발생건수전체',
       '피해자성별남성',
       '피해자성별여성',
       '피해자성별불상',
       '피해자연령6이하',
       '피해자연령12이하',
       '피해자연령15이하',
       '피해자연령20이하',
       '피해자연령30이하',
       '피해자연령40이하',
       '피해자연령50이하',
       '피해자연령60이하',
       '피해자연령60초과',
       '피해자연령건수',
       '범죄유형강력',
       '범죄유형폭력',
       '범죄유형절도',
       '범죄유형지능',
       '범죄유형기타',
       '수사단서정보고발',
       '수사단서정보고소',
       '수사단서정보진정',
       '수사단서정보탄원',
       '수사단서정보피해자신고',
       '수사단서정보타인신고',
       '수사단서정보탐문정보',
       '수사단서정보검문',
       '수사단서정보자수',
       '수사단서정보여죄',
       '수사단서정보변사체',
       '수사단서정보현행범',
       '수사단서정보기타',
       '발생요일일요일',
       '발생요일월요일',
       '발생요일화요일',
       '발생요일수요일',
       '발생요일목요일',
       '발생요일금요일',
       '발생요일토요일']
df_age.columns = col
# 불필요한 컬럼 제외
df_age2 = df_age.drop(['작성년월'], axis=1)
# 서울 경찰서만 선택
df_age3 = df_age2[df_age2['작성경찰서명'].str.contains('서울')]
# 파생변수 생성
df_age3['어린이 대상 범죄 건수'] = df_age3['피해자연령6이하'] + df_age3['피해자연령12이하']
df_age3['전체 범죄 대비 어린이 범죄 비율'] = df_age3['어린이 대상 범죄 건수'] / df_age3['발생건수전체']
df_age3['자치구'] = df_age3['작성경찰서명'].apply(police_to_gu_age)

## df_pp (서울시 생활인구) -> df_pp8
col = df_pp.columns.tolist()
# 기준일ID를 인덱스에서 컬럼으로 변경
df_pp2 = df_pp.reset_index()
# 컬럼이 밀려있음 (마지막 컬럼은 불필요한 컬럼으로 삭제)
df_pp3 = df_pp2.drop(['여자70세이상생활인구수'], axis=1)
# 밀려있던 컬럼명을 다시 설정
df_pp3.columns = col
# 자치구명 표시를 위해 매핑 데이터 읽어옴
df_gu = pd.read_excel('data/법정동 기준 시군구 단위(자치구 코드).xlsx')
# 서울에 해당하는 데이터만 사용
df_gu2 = df_gu[:25]
# 앞에 서울 적혀있는 것 삭제
df_gu2['시군구명'] = df_gu2['시군구명'].apply(lambda x: x.split(' ')[1])
# 매핑 데이터와 병합
df_pp4 = pd.merge(df_pp3, df_gu2, how='left', left_on='자치구코드', right_on='시군구_코드_법정동기준')
# 어린이 생활인구수 파생변수 생성
df_pp4['어린이 생활인구수'] = df_pp4['남자0세부터9세생활인구수'] + df_pp4['남자10세부터14세생활인구수'] + df_pp4['여자0세부터9세생활인구수'] + df_pp4['여자10세부터14세생활인구수']
# 유치원, 초등학교가 시작하고 끝나는 시간대의 어린이 생활인구수 계산
df_pp5 = df_pp4[df_pp4['시간대구분'].isin([8, 9, 14, 15])]
df_pp6 = df_pp5.pivot_table(index='시군구명', values='어린이 생활인구수', aggfunc='mean').reset_index()
df_pp6.rename(columns={'어린이 생활인구수': '등하교시간 평균 어린이 생활인구수'}, inplace=True)
# 00-23시의 어린이 생활인구수 계산
df_pp7 = df_pp4.pivot_table(index='시군구명', values='어린이 생활인구수', aggfunc='mean').reset_index()
df_pp7.rename(columns={'어린이 생활인구수': '전체시간 평균 어린이 생활인구수'}, inplace=True)
# 전체 시간 어린이 생활인구수와 등하교 시간 어린이 생활인구수 데이터 병합
df_pp8 = pd.merge(df_pp7, df_pp6, how='inner', on='시군구명')

## df_wc (보행어린이 사고다발지) -> df_wc4
# 필요한 컬럼만 선택
df_wc2 = df_wc[['지점명', '사고건수', '사상자수', '사망자수', '중상자수', '경상자수', '부상신고자수']]
# 서울에 해당하는 로우만 사용
df_wc3 = df_wc2[df_wc2['지점명'].str.contains('서울특별시')]
# 자치구 컬럼 생성
df_wc3['자치구'] = df_wc3['지점명'].apply(lambda x: x.split(' ')[1])
# 자치구별로 사고건수, 사상자수, 중상자수, 경상자수, 부상신고자수의 합을 계산 (사망자수 총합은 강남구 총 2명, 서대문구 총 1명 제외하고는 0명이어서 제외)
# 사상자수 = 부상신고자수 + 경상자수 + 중상자수 + 사망자수
df_wc4 = df_wc3.pivot_table(index='자치구', values=['사고건수', '사상자수', '중상자수', '경상자수', '부상신고자수'], aggfunc='sum').reset_index()
# 중상자 비율 컬럼 생성 (중상자수 / 사상자수)
df_wc4['중상자 비율'] = df_wc4['중상자수'] / df_wc4['사상자수']
### -----

### streamlit
# 구 선택
gu_selected = []

st.title('어린이 시설 및 CCTV 시각화')
# 생성된 각 구의 체크박스를 저장하는 리스트
cb_lst = []
gu_name = ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구',
           '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구']
# 체크박스를 5x5로 보여주기 위한 columns
st_cols = st.columns(5)

# 각 구마다 체크박스 생성
for i in range(len(gu_name)):
    with st_cols[i % 5]:
        cb_lst.append(st.checkbox(gu_name[i]))

# 체크박스가 체크되어 있다면 선택된 구 리스트에 추가
for i in range(len(gu_name)):    
    if cb_lst[i]:
        gu_selected.append(gu_name[i])

if st.button('지도 보기'):
    ### folium
    df_cctv_gu = df_cctv2[df_cctv2['자치구'].isin(gu_selected)]
    df_child_gu = df_child2[df_child2['자치구'].isin(gu_selected)]
    df_al_gu = df_al3[df_al3['자치구'].isin(gu_selected)]
    df_p_gu = df_p5[df_p5['자치구'].isin(gu_selected)]

    # folium에서 marker cluster로 표시하기 위해 cctv와 비상벨을 하나의 데이터프레임으로 합침
    df_al_gu.rename(columns={'WGS84위도': '위도', 'WGS84경도': '경도'}, inplace=True)
    df_sec_gu = pd.concat([df_cctv_gu, df_al_gu])
    # cctv와 비상벨을 구별하기 위해 설치목적 컬럼의 결측치를 채워줌 (cctv는 모두 결측치이므로 둘을 구별할 수 있음)
    df_sec_gu['설치목적'].fillna('None', inplace=True)

    df_wc_seoul = df_wc[df_wc['지점명'].str.contains('서울특별시')]
    df_wc_seoul['중상자 비율'] = df_wc_seoul['중상자수'] / df_wc_seoul['사상자수']
    df_wc_seoul['자치구'] = df_wc_seoul['지점명'].apply(lambda x: x.split(' ')[1])
    df_wc_seoul2 = df_wc_seoul.reset_index()
    df_wc_seoul2 = df_wc_seoul2[['사고다발지FID', '자치구', '지점명', '사상자수', '중상자 비율', '위도', '경도', '다발지역폴리곤']]

    df_wc_gu = df_wc_seoul2[df_wc_seoul2['자치구'].isin(gu_selected)]
    df_wc_gu2 = df_wc_gu.reset_index()
    df_wc_gu2.drop('index', axis=1, inplace=True)

    # 행정동 표시를 위한 geo data 읽어오기
    geo_path = 'geo_data/hangjeongdong_서울특별시.geojson'
    # key_on='feature.properties.sggnm'
    geo_data = json.load(open(geo_path, encoding='utf-8'))

    # gu_selected 변수에 해당하는 구만 선택
    gu_features = []
    for i in geo_data['features']:
        if i['properties']['sggnm'] in gu_selected:
            gu_features.append(i)

    geo_data_gu = geo_data.copy()
    geo_data_gu['features'] = gu_features

    # 보행어린이 사고다발지역 표시를 위해 df_wc_seoul2 데이터프레임 값들로 json 파일 만들기
    geo_wc_features = []
    for i in range(len(df_wc_gu2)):
        features_dict = {}
        properties_dict = {}
        geometry_dict = {}
        
        # features 딕셔너리 내 properties key값에 해당하는 딕셔너리 부분
        properties_dict['OBJECTID'] = int(i + 1)
        properties_dict['fid'] = str(df_wc_gu2['사고다발지FID'][i])
        properties_dict['adm_nm'] = df_wc_gu2['지점명'][i]
        properties_dict['sggnm'] = df_wc_gu2['자치구'][i]
        properties_dict['casualties'] = int(df_wc_gu2['사상자수'][i])
        properties_dict['si_per'] = float(df_wc_gu2['중상자 비율'][i])
        
        # features 딕셔너리 내 geometry key값에 해당하는 딕셔너리 부분
        geometry_dict['type'] = 'Polygon'
        coordinates_string = df_wc_gu2['다발지역폴리곤'][i].split(':')[2][:-1]
        coordinates_lst = ast.literal_eval(coordinates_string)
        geometry_dict['coordinates'] = coordinates_lst
        
        # features 딕셔너리에 합치는 작업
        features_dict['type'] = 'Feature'
        features_dict['properties'] = properties_dict
        features_dict['geometry'] = geometry_dict
        
        # df_wc_seoul2의 각 행마다 딕셔너리 형태로 변환 후 리스트에 저장
        geo_wc_features.append(features_dict)

    geo_wc = geo_data.copy()
    geo_wc['features'] = geo_wc_features

    # 시작 좌표
    latitude = 37.56637
    longitude = 126.97795
    r = 100
    r2 = 0.00101

    m = folium.Map(location=[latitude, longitude],
                tiles='CartoDB positron',
                zoom_start=14,
                width=900,
                height=600)

    # cctv, 안전비상벨 지도에 표시
    marker_cluster = MarkerCluster().add_to(m)
    for lat, lon, check in zip(df_sec_gu['위도'], df_sec_gu['경도'], df_sec_gu['설치목적']):
        if check == 'None':
            typ = 'CCTV'
        else:
            typ = '비상벨'
        folium.Marker([lat, lon], icon = folium.Icon(color='green'), tooltip=typ).add_to(marker_cluster)
        
    # 경찰서(지구대, 파출소 포함) 지도에 표시
    for lat, lon, addr in zip(df_p_gu['위도'], df_p_gu['경도'], df_p_gu['주소']):
        folium.Marker([lat, lon], icon = folium.Icon(color='blue', icon='star'), tooltip=addr).add_to(m)

    # 보행어린이 사고다발지역 폴리곤 지도에 표시
    fm = folium.Choropleth(geo_data=geo_wc,
                            # key_on='feature.properties.sggnm',
                            line_color='red',
                            line_opacity=1,
                            fill_color='red',
                            fill_opacity=0.3
                            ).add_to(m)

    # 보행어린이 사고다발지역 포인트 지도에 표시
    for lat, lon, cas, per in zip(df_wc_gu2['위도'], df_wc_gu2['경도'], df_wc_gu2['사상자수'], df_wc_gu2['중상자 비율']):
        folium.Marker([lat, lon], icon = folium.Icon(color='red', icon='flag'), tooltip=f'사상자 수:{cas}', popup=f'중상자 비율:{per:.2f}').add_to(m)

    # 자치구 어린이시설마다 100미터 이내 CCTV, 비상벨 수 계산
    colors_i = 1
    colors = {-1: 'gray', 1: 'black'}
    for g in gu_selected:
        colors_i *= -1
        
        # g 변수에 해당하는 구만 선택
        gu_features = []
        for i in geo_data_gu['features']:
            if i['properties']['sggnm'] == g:
                gu_features.append(i)
        geo_data_gu2 = geo_data.copy()
        geo_data_gu2['features'] = gu_features
        
        df_child_gu2 = df_child_gu[df_child_gu['자치구'] == g]
        
        df_sec_gu2 = df_sec_gu[df_sec_gu['자치구'] == g]
        
        # sec_cnt_lst : 해당 자치구(g) 안에 있는 어린이시설별 100미터 이내 CCTV 및 비상벨 수가 들어있는 리스트
        sec_cnt_lst = []
        
        # 행정동 경계 지도에 표시
        fm = folium.Choropleth(geo_data=geo_data_gu2,
                            # key_on='feature.properties.sggnm',
                            line_color='black',
                            line_opacity=1,
                            fill_color=colors[colors_i],
                            fill_opacity=0.3
                            ).add_to(m)

        # 영역 정보 표시하는 부분
        for idx, dict in enumerate(geo_data_gu2['features']):
            # 자치구 행정동 표시
            name = dict['properties']['adm_nm'].split(' ')[1] + ' ' + dict['properties']['adm_nm'].split(' ')[2]
            # 추가할 정보
            # cctv_cnt = df_cctv[df_cctv['구분'] == name]['총계'].values[0]
            txt = f'<b><h5>{name}</h5></b>'
            geo_data_gu2['features'][idx]['properties']['tooltip'] = txt
        fm.geojson.add_child(folium.features.GeoJsonTooltip(['tooltip'], labels=False))
        
        # 각 어린이시설별 100미터 이내 CCTV, 비상벨 수 계산
        for lat, lon, name in zip(df_child_gu2['위도'], df_child_gu2['경도'], df_child_gu2['시설명']):
            # sec_cnt : 각 어린이시설별 100미터 이내 CCTV, 비상벨 수
            sec_cnt = 0
            # 해당 자치구 내 모든 CCTV 및 비상벨을 확인
            for lat2, lon2 in zip(df_sec_gu2['위도'], df_sec_gu2['경도']):
                if math.pow(r2, 2) >= (math.pow(lat - lat2, 2) + math.pow(lon - lon2, 2)):
                    sec_cnt += 1
            sec_cnt_lst.append(sec_cnt)   

        # 어린이시설 지도에 표시
        for lat, lon, name, sec_cnt in zip(df_child_gu2['위도'], df_child_gu2['경도'], df_child_gu2['시설명'], sec_cnt_lst):
            # 어린이시설 100미터 이내 CCTV, 비상벨 수가 평균 미만은 빨간색 평균 이상은 초록색으로 표시 
            if sec_cnt < np.mean(sec_cnt_lst):
                c = 'pink'
            else:
                c = 'pink'
            folium.Marker([lat, lon], icon = folium.Icon(color=c, icon='home'), tooltip=name, popup=f'100미터 내 CCTV, 비상벨 수:{sec_cnt}').add_to(m)
            folium.Circle([lat, lon], radius=r, color=c).add_to(m)
    ### -----
    st_map = st_folium(m, width=750, height=500)
### -----