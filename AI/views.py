from django.shortcuts import render, redirect
from django.http import HttpResponse
from AI.models import PotholeAI
import subprocess
import shutil
import os
import pandas as pd
import matplotlib.pyplot as plt
import io
import base64
from PIL import Image
import requests
import matplotlib as mpl


def pothole(request, name):
    # 실행할 명령
    command = [

        'python',  # 실행할 파이썬 인터프리터
        'D:/pothole_project/potholeAI/detect.py',  # 실행할 스크립트 파일
        '--weights', 'D:/pothole_project/potholeAI/train25000val5000AI.pt',
        '--img', '416',
        '--conf', '0.2',
        '--source',
        'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/pothole/' + name,
        '--name',
        'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI',
        '--save-txt',
        '--save-conf',
        '--exist-ok'
    ]

    source_path = 'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI/' + name

    destination_path = 'D:/pothole_project/static/img/' + name

    # 명령 실행
    subprocess.run(command)
    shutil.copy(source_path, destination_path)

    ai = 0
    find = 0

    f = open(
        "D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI/labels/" +
        os.path.splitext(name)[0] + '.txt', 'r')
    lines = f.readlines()
    for line in lines:
        if line[0] == '0':
            ai = 1
            find += 1
    f.close()

    try:
        # idx가 주어진 값과 일치하는 데이터 레코드 조회
        target_pothole = PotholeAI.objects.get(filename=name)

        # 조회한 데이터 레코드의 ai 값을 변경
        target_pothole.ai = ai
        target_pothole.find = find

        # 변경사항을 데이터베이스에 저장
        target_pothole.save()

        print("데이터 업데이트 완료")
    except PotholeAI.DoesNotExist:
        print(f"idx {name}에 해당하는 데이터가 없습니다.")
    except Exception as e:
        print(f"데이터 업데이트 중 오류 발생: {str(e)}")

    context = {
        'name': name,
        'find': find,
    }

    return render(request, 'pothole.html', context)


def graph(request, name):
    plt.rc('font', family='Gulim')
    mpl.rcParams['axes.unicode_minus'] = False

    try:
        # CSV 파일을 읽어옵니다. CSV 파일의 경로는 settings.py에 설정된 STATIC_URL에 포함됩니다.
        csv_file_path = f'D:/pothole_project/csv/{name}.csv'
        df = pd.read_csv(csv_file_path)

        # 'ai' 항목이 1인 데이터만 필터링합니다.
        df_filtered = df[df['ai'] == 1]

        # 주소를 기준으로 데이터를 그룹화하고 그룹별로 행의 개수를 세어줍니다.
        address_grouped = df_filtered.groupby('address').size()

        # 그래프를 그립니다.
        plt.figure(figsize=(10, 6))
        address_grouped.plot(kind='line', marker='o')  # 꺾은선 그래프로 변경하고 마커를 추가합니다.
        plt.title('포트홀 그래프')
        plt.xlabel('주소')
        plt.ylabel('발생 수')
        plt.grid(True)
        plt.xticks(rotation=45)

        # 그래프를 이미지로 변환하여 HTML에 전달합니다.
        img_data = io.BytesIO()
        plt.savefig(img_data, format='png')
        img_data.seek(0)
        img_base64 = base64.b64encode(img_data.read()).decode('utf-8')

        context = {
            'csv_filename': name,
            'graph_image': img_base64,
        }

        return render(request, 'graph.html', context)
    except Exception as e:
        return HttpResponse(f"Error: {str(e)}")

def folder(request, name):

    #위도 경도 날짜 DB에 입력
    img_path = 'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/pothole/' + name
    img_list = [f for f in os.listdir(img_path)]

    for i in img_list:
        image = 'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/pothole/' + name + '/' + i
        img = Image.open(image)
        img_info = img._getexif()
        img_date = img_info[306].split(':')
        img_date = img_date[0] + "-" + img_date[1] + "-" + img_date[2].split(' ')[0]
        lat = img_info[34853][2]
        lng = img_info[34853][4]
        lat = float(lat[0] + lat[1] / 60 + lat[2] / 3600)
        lng = float(lng[0] + lng[1] / 60 + lng[2] / 3600)

        # 주소 찾는 코드
        def get_address_from_coordinates(api_key, lat, lng):
            url = f"https://dapi.kakao.com/v2/local/geo/coord2address.json?x={lng}&y={lat}"
            headers = {"Authorization": f"KakaoAK {api_key}"}
            response = requests.get(url, headers=headers)
            data = response.json()

            if data.get("meta", {}).get("total_count", 0) > 0:
                address = data["documents"][0]['address']['region_2depth_name']
                return address
            else:
                return "주소를 찾을 수 없습니다."

        api_key = "44f1398008d1d8d3a49e09feef7fa327"

        address = get_address_from_coordinates(api_key, lat, lng)

        try:
            target_pothole = PotholeAI.objects.get(filename=i, folder=name)
            # 조회한 데이터 레코드의 ai 값을 변경
            target_pothole.latitude = lat
            target_pothole.longitude = lng
            target_pothole.date = img_date
            target_pothole.address = address
            # 변경사항을 데이터베이스에 저장
            target_pothole.save()
        except PotholeAI.DoesNotExist:
            print(f"해당하는 데이터가 없습니다.")
        except Exception as e:
            print(f"데이터 업데이트 중 오류 발생: {str(e)}")

    # 실행할 명령
    command = [
        'python',  # 실행할 파이썬 인터프리터
        'D:/pothole_project/potholeAI/detect.py',  # 실행할 스크립트 파일
        '--weights', 'D:/pothole_project/potholeAI/train25000val5000AI.pt',
        '--img', '416',
        '--conf', '0.2',
        '--source',
        'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/pothole/' + name,
        '--save-txt',
        '--save-conf',
        '--exist-ok',
        '--name',
        'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI/' + name
    ]

    # 명령 실행
    subprocess.run(command)

    ai = 0
    find = 0

    img_path = 'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI/' + name

    img_list = [f for f in os.listdir(img_path) if not f.startswith('labels')]

    folder_path = 'D:/pothole_project/pothole_java/.metadata/.plugins/org.eclipse.wst.server.core/tmp0/wtpwebapps/pothole/data/potholeAI/' + name + '/labels'

    # 폴더 내의 파일 목록을 얻습니다.
    file_list = [f for f in os.listdir(folder_path) if f.endswith('.txt')]

    # 이미지 파일과 텍스트 파일의 공통된 부분을 찾습니다.
    common_names = set([os.path.splitext(file)[0] for file in img_list]) & set(
        [os.path.splitext(file)[0] for file in file_list])

    # img_list에서 common_names에 없는 파일명을 제거합니다.
    img_list = [file for file in img_list if os.path.splitext(file)[0] in common_names]

    for index, file_name in enumerate(file_list):
        file_path = os.path.join(folder_path, file_name)
        with open(file_path, 'r') as file:
            lines = file.readlines()
            ai = 0
            find = 0

            for line in lines:
                if line.startswith('0'):
                    ai = 1
                    find += 1

            try:
                target_pothole = PotholeAI.objects.get(filename=img_list[index], folder=name)
                # 조회한 데이터 레코드의 ai 값을 변경
                target_pothole.ai = ai
                target_pothole.find = find
                # 변경사항을 데이터베이스에 저장
                target_pothole.save()
            except PotholeAI.DoesNotExist:
                print(f"해당하는 데이터가 없습니다.")
            except Exception as e:
                print(f"데이터 업데이트 중 오류 발생: {str(e)}")
    redirect_url = f'http://192.168.0.42:8080/pothole/folderlist.com?folder={name}'
    return redirect(redirect_url)
