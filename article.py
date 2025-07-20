#!/usr/bin/env python3

import sys
import subprocess
import importlib.util
import os
import glob 

def install_package(package):
    """패키지가 없으면 설치"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except subprocess.CalledProcessError:
        print(f"Failed to install {package}")
        sys.exit(1)

def check_and_install_packages():
    """필요한 패키지들 확인 및 설치"""
    required_packages = {
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'numpy': 'numpy'
    }

    for module_name, package_name in required_packages.items():
        if importlib.util.find_spec(module_name) is None:
            print(f"Installing {package_name}...")
            install_package(package_name)

# 패키지 설치 확인
check_and_install_packages()

# 이제 패키지들을 import
import pandas as pd
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import numpy as np

def select_csv_file():
    """CSV 파일을 선택하는 함수"""
    print("=== CSV 파일 선택 ===")
    print("현재 디렉토리:", os.getcwd())

    # 현재 디렉토리와 하위 디렉토리에서 CSV 파일 찾기
    csv_files = list(set(glob.glob("*.csv") + glob.glob("**/*.csv", recursive=True)))

    if not csv_files:
        print("CSV 파일을 찾을 수 없습니다.")
        print("CSV 파일 경로를 직접 입력하세요:")
        user_input = input("CSV 파일 경로: ").strip()
        if os.path.exists(user_input):
            return user_input
        else:
            print("유효한 파일이 아닙니다.")
            return None

    print(f"\n발견된 CSV 파일 ({len(csv_files)}개):")
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")

    while True:
        try:
            choice = input(f"\n사용할 파일 번호를 선택하세요 (1-{len(csv_files)}): ").strip()
            if not choice:
                return None
            choice = int(choice)
            if 1 <= choice <= len(csv_files):
                selected_file = csv_files[choice - 1]
                print(f"선택된 파일: {selected_file}")
                return selected_file
            else:
                print("선택 범위를 벗어났습니다.")
        except ValueError:
            print("숫자를 입력해야 합니다.")
        except KeyboardInterrupt:
            print("작업을 취소합니다.")
            return None

def read_csv_robust(csv_file):
    """CSV 파일 인코딩 자동 재시도"""
    print(f"CSV 파일 '{csv_file}' 읽는 중...")
    encodings = ["utf-8", "cp949"]  # 최소한의 인코딩 후보

    for encoding in encodings:
        try:
            print(f"[시도] 인코딩: {encoding}")
            df = pd.read_csv(
                csv_file,
                encoding=encoding,
                sep=None,
                engine='python',
                on_bad_lines='skip',
                dtype=str
            )
            print(f"[성공] 인코딩: {encoding}")
            return df
        except Exception as e:
            print(f"[실패] 인코딩: {encoding} -> 오류: {e}")
            continue
    print("CSV 파일을 읽지 못했습니다.")
    return None

def extract_year_keywords(csv_file):
    """연도별 키워드 추출"""
    df = read_csv_robust(csv_file)
    if df is None:
        return defaultdict(list)

    year_keywords = defaultdict(list)
    df.columns = df.columns.str.lower().str.strip()

    year_columns = ['year', 'pubyear', 'publication_year', 'py', 'published_year', 'date', 'publication date']
    keyword_columns = ['keywords', 'author_keywords', 'de', 'id', 'keyword', 'kw', 'author keywords', 'index keywords']
    year_col = next((col for col in year_columns if col in df.columns), None)
    keyword_col = next((col for col in keyword_columns if col in df.columns), None)

    if year_col is None:
        print("연도 컬럼을 찾을 수 없습니다.")
        for i, col in enumerate(df.columns, 1):
            print(f"{i}. {col}")
        try:
            year_col = df.columns[int(input("연도 컬럼 번호 입력: ")) - 1]
        except:
            return year_keywords

    if keyword_col is None:
        print("키워드 컬럼을 찾을 수 없습니다.")
        for i, col in enumerate(df.columns, 1):
            print(f"{i}. {col}")
        try:
            keyword_col = df.columns[int(input("키워드 컬럼 번호 입력: ")) - 1]
        except:
            return year_keywords

    import re
    for idx, row in df.iterrows():
        try:
            year_str = str(row[year_col]).strip()
            kw_text = str(row[keyword_col]).strip()

            if not year_str or not kw_text:
                continue

            match = re.search(r'(19|20)\d{2}', year_str)
            year = match.group() if match else None
            if not year:
                continue

            for sep in [';', ',', '|', '\n', '\t']:
                if sep in kw_text:
                    keywords = [k.strip().lower() for k in kw_text.split(sep)]
                    break
            else:
                keywords = [kw_text.lower().strip()]

            keywords = [kw for kw in keywords if kw and len(kw) > 1]
            if keywords:
                year_keywords[year].extend(keywords)
        except:
            continue

    return year_keywords

def create_trend_analysis(year_keywords, top_n=10):
    """키워드 트렌드 분석 및 그래프 생성"""
    if not year_keywords:
        print("분석할 데이터가 없습니다.")
        return

    data = []
    for year, keywords in year_keywords.items():
        counter = Counter(keywords)
        for kw, count in counter.items():
            data.append({'year': year, 'keyword': kw, 'count': count})

    df = pd.DataFrame(data)
    if df.empty:
        print("데이터가 비어있습니다.")
        return

    try:
        df['year'] = pd.to_numeric(df['year'])
        df = df.sort_values('year')
    except:
        pass

    total_counts = df.groupby('keyword')['count'].sum().nlargest(top_n)
    top_keywords = total_counts.index.tolist()
    df_top = df[df['keyword'].isin(top_keywords)]

    pivot = df_top.pivot_table(index='year', columns='keyword', values='count', fill_value=0)

    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False

    plt.figure(figsize=(15, 8))
    colors = plt.cm.tab10(np.linspace(0, 1, len(top_keywords)))
    markers = ['o', 's', '^', 'v', 'D', 'P', '*', 'X', 'h', '+']

    for i, keyword in enumerate(top_keywords):
        plt.plot(pivot.index, pivot[keyword],
                 label=keyword,
                 color=colors[i],
                 marker=markers[i % len(markers)],
                 linewidth=2, markersize=6)

    plt.xlabel("Year")
    plt.ylabel("Frequency")
    plt.title(f"Top {top_n} Keywords Trend by Year")
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig("keyword_trend.png", dpi=300, bbox_inches='tight')
    plt.show()

    print(f"\n=== 분석 결과 요약 ===")
    print(f"총 연도 수: {len(pivot.index)}")
    print(f"총 키워드 수: {len(df['keyword'].unique())}")
    print(f"분석 기간: {pivot.index.min()} - {pivot.index.max()}")
    print("\n상위 키워드:")
    for i, (kw, count) in enumerate(total_counts.items(), 1):
        print(f"{i}. {kw}: {count}회")

# 실행 시작
if __name__ == "__main__":
    print("📊 Article Keyword Trend Analyzer 시작...")

    csv_file = select_csv_file()
    if not csv_file:
        print("CSV 파일을 선택하지 않았습니다. 종료합니다.")
        sys.exit(1)

    year_keywords = extract_year_keywords(csv_file)
    if not year_keywords:
        print("키워드를 추출할 수 없습니다. 종료합니다.")
        sys.exit(1)

    create_trend_analysis(year_keywords, top_n=10)
    print("🎉 분석 완료! 결과 그래프가 'keyword_trend.png'로 저장되었습니다.")
