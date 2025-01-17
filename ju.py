import requests, re
from bs4 import BeautifulSoup
from datetime import datetime
from konlpy.tag import Okt
from nltk import FreqDist
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
import numpy as np
from matplotlib import font_manager, rc

path = '/Users/son_dahum/Library/Fonts/Seoulnamsan_B.otf'
font_name = font_manager.FontProperties(fname = path).get_name()
rc('font', family=font_name)

okt = Okt()


def setConstants():
    payload = {'dirId': '',
               'docId': '',
               'answerSortType': 'DEFAULT',
               'answerFilterType': 'ALL',
               'answerViewType': 'DETAIL',
               'page': '1',
               'count': '',
               }

    return re.compile(r'\s\s+'), payload


# ===================질문등록날짜===================#
def getRegisteredDate(soup, dates):
    now = datetime.now()
    for date in soup.select('ul.basic1 .txt_inline'):
        form = date.text.replace(' ', '')
        if form[-2] == '일':
            day = int(now.day) - int(form[:-2])
            form = '%s-%s-%s' % (now.year, str(now.month).zfill(2), str(day).zfill(2))
        else:
            form = form.replace('.', '-')[:-1]

        dates.append(form)

    return dates


def getTotalDocumentNumber(soup):
    num = soup.select('span.number').pop().text.split('/')[1].replace(',', '')[:-1]

    return int(num)


# ===================질문제목===================#
def getTitles(soup, titles):
    for title in soup.select('ul.basic1 ._searchListTitleAnchor'):
        titles.append(title.text)

    return titles


# ===================질문링크===================#
def getLinks(soup, links):
    for a_tag in soup.select('ul.basic1 a._searchListTitleAnchor'):
        links.append(a_tag.attrs['href'])

    return links


def getNumberOfAnswer(soup, answer_num):
    for span_tag in soup.select('ul.basic1 dd.txt_block span.hit'):
        answer_num.append(int(span_tag.text.split(' ')[1]))

    return answer_num


def getOuterInfo():
    html = requests.get(url).text
    soup = BeautifulSoup(html, 'html.parser')
    num = getTotalDocumentNumber(soup)
    titles = []
    links = []
    dates = []
    answer_num = []

    last_page = num // 10
    if num % 10 != 0: last_page += 1
    current_page = 1

    while current_page <= last_page:
        titles.extend(getTitles(soup, []))
        links.extend(getLinks(soup, []))
        dates.extend(getRegisteredDate(soup, []))
        answer_num.extend(getNumberOfAnswer(soup, []))

        current_page += 1
        html = requests.get(url + '&page=' + str(current_page)).text
        soup = BeautifulSoup(html, 'html.parser')

    return titles, links, dates, num, answer_num


def setPayload(link, answerNum):
    # payload = {'dirId': '',
    #            'docId': '',
    #            'answerSortType': 'DEFAULT',
    #            'answerFilterType': 'ALL',
    #            'answerViewType': 'DETAIL',
    #            'page': '1',
    #            'count': '',
    #            }
    dirId = link.split('dirId=')[1].split('&')[0]
    docId = link.split('docId=')[1].split('&')[0]
    count = str(answerNum)

    payload['dirId'] = dirId
    payload['docId'] = docId
    payload['count'] = count


# ===================질문내용===================#
def getQnA():
    contents = []
    questions = []
    answers = []
    deleted = []
    userinfos = []
    answered_dates = []

    cnt = -1
    for idx in range(0, len(links)):
        setPayload(links[idx], answer_num[idx])
        # pprint.pprint(payload)
        content = requests.get(links[idx], headers=payload).text
        if "http://www.w3.org/1999/xhtml" in content:
            cnt += 1
            deleted.append(cnt)
            dates.remove(dates[len(contents) - cnt])
            titles.remove(titles[len(contents) - cnt])
            continue

        contents.append(content)

    for content in contents:
        soup = BeautifulSoup(content, 'html.parser')

        question = soup.select('#content .c-heading__content')
        if len(question) == 0:
            question = soup.select('#content .c-heading__title-inner')

        questions.append(re.sub(pattern, '', question.pop().text))

        answer = soup.select('._answerList .se-module')
        if len(question) == 0:
            answer = soup.select('._answerList ._endContents')

        answer_list = []
        for a in answer:
            answer_list.append(re.sub(pattern, '', a.text).replace('\u200b', ' ').replace('\xa0', ' '))

        answers.append(answer_list)

        user_list = []
        user = soup.select('._answer .c-userinfo')
        for usr in user:
            info = re.sub(pattern, '', usr.text)

            if '한의' in info or '한방' in info:
                usrType = 'o'
            elif '의' in info or '과' in info or '클리닉' in info:
                usrType = 'd'
            else:
                usrType = 'e'

            user_list.append(usrType)

        userinfos.append(user_list)

        date_list = []
        answered_date = soup.select('c-heading-answer__content-date')
        for date in answered_date:
            date_list.append(date)

        answered_dates.append(date_list)

    return contents, questions, answers, userinfos, answered_dates


def _print():
    print('-\n\n전체 문서 갯수 : ' + str(total_num), end='-\n\n')
    for idx in range(0, len(titles)):
        print(str(idx + 1) + '. ' + titles[idx] + '\t(' + dates[idx] + ')')
        print('-->' + links[idx])


def printQ():
    print('-\n\n전체 문서 갯수 : ' + str(total_num), end='\n-\n\n')
    for idx in range(0, len(titles)):
        print(str(idx + 1) + '. ' + titles[idx] + '\t답변갯수 : ' + str(answer_num[idx]) + '\t(' + dates[idx] + ')')
        print('--> Q.  ' + questions[idx])
        for answer in answers[idx]:
            print('--> A.  ' + answer)

        print('\n\n')


def makeAnswerData():
    pass


def makeQuestionData():
    pass


def makeJson():
    Adocument = {'date': answered_dates,
                 'writer': userInfos,
                 'content': answers
                 }
    Qdocument = {'date': dates,
                 'title': titles,
                 'link': links,
                 'content': questions,
                 'answer': Adocument
                 }
    data = {'keyword': query,
            'documents': Qdocument
            }


def data_in():
    query = input('검색어 : ')
    query.replace(' ', '+')
    _from = input('from (YYYY.MM.DD.) : ')
    _to = input('to (YYYY.MM.DD.) : ')
    url = 'https://kin.naver.com/search/list.nhn?sort=date' + '&query=' + query + '&period=' + _from + '%7C' + _to + '&section=kin'

    return query, _from + '.%7C' + _to, url


# ===================분석할 text 전처리===================#
def make_text(titles, questions):
    text = []
    for idx in range(0, len(titles)):
        temp = titles[idx] + questions[idx]
        text.append(temp)
    return text


#품사태깅
def make_tag(origin):
    result = []
    for i in range(0, len(origin)):
        result.append(okt.pos(origin[i]))
    return result


#명사, 숫자, 부사, 형용사, 동사만 남기기
def clean_text(origin, tag):
    result = []
    for i in range(0, len(origin)):
        for j in range(0, len(origin[i])):
            if origin[i][j][1] in tag:
                result.append(origin[i][j][0])
    return result


#불용어 제거 함수
def remove_stopwords(words):
    result = []
    for w in words:
        if w not in stop_words:
            result.append(w)
    return result


#단어 빈도수 측정
def frequency(word, num):
    fd_word = Counter(word)
    important_word = fd_word.most_common(num)

    return fd_word, important_word

# ===================데이터 시각화===================#
#단어 + 빈도수 인쇄
def print_wf(words):
    print("==================")
    for i in range(0, len(words)):
        print('%-10s %5s\n' %(words[i][0], words[i][1]))
    print("==================")


#워드 클라우드
def make_wordcloud(words, word_count):
    result = []
    for i in range(0, len(words)):
        if words[i][1] >= word_count :
            result.append(words[i])

    wc = WordCloud(font_path=path, background_color='white', width=800, height=600)
    cloud = wc.generate_from_frequencies(dict(result))
    plt.figure(figsize=(10, 8))
    plt.axis('off')
    plt.imshow(cloud)
    plt.show()
    return result


def make_graph(words):
    word_name = []
    word_frequency = []
    for i in range(0, len(words)):
        word_name.append(words[i][0])
        word_frequency.append(words[i][1])

    n_groups = len(word_name)
    index = np.arange(n_groups)
    plt.figure(figsize=(10, 8))
    plt.bar(index, word_frequency, tick_label = word_name)
    plt.title('단어의 빈도수', fontsize = 14)
    plt.xlabel('단어', fontsize=11)
    plt.ylabel('빈도수', fontsize=11)
    plt.xticks(fontsize=6, rotation = 45)
    plt.yticks(fontsize=10)

    plt.show()


if __name__ == "__main__":
    global links, contents, titles, total_num, pages, amount, questions, answers, \
        url, pattern, html, soup, query, dates, userInfos, answered_dates, answer_num, payload

    stop_words = ['보험', '태아', '가입', '제', '입니다', '때', '좀', '저', '지금', '요', '정도', \
                  '너무', '중', '것', '더', '살', '많이', '안녕하세요', '세', '해서', '하는', '수',\
                  '질문', '해', '해야', '하는데', '합니다', '추천', '보장', '현재', '어떻게', '생각', \
                  '설계', '하면', '만', '개월', '알려주세요', '했는데', '만기', '이제', '전', '다', \
                  '말', '비교', '그래서', '근데', '답변', '있는', '할', '건지', '방법', '부탁드립니다',\
                  '이', '있을까요', '거', '잘', '혹시', '실비', '안', '아직', '하고', '문의', '받아', '가요', \
                  '대해', '때문', '있나요', '조금', '되는', '법', '분', '내공', '상품', '진짜', '곳', '100'\
                  '했어요', '해주세요', '같아요', '알', '같은데', '주차', '해상', '좋을까요', '그', '보니'\
                  '요즘', '있는데', '된', '했습니다', '부탁드려요', '궁금합니다', '보험료', '얼마', '할까'\
                  '한', '한번', '우리', '쪽', '비', '한', '데', '차', '어떤', '보고', '주', '싶은데'\
                  '싶은데', '있습니다', '하는게', '꼭', '또', '정말', '있어서', '알아보고', '쯤', '엄청'\
                  '편이', '하나', '하게', '받고', '건가', '가지', '등', '걸', '싶습니다', '할지', '있으면'\
                  '이렇게', '받을', '받을', '됩니다', '번', '있다고', '특약', '같아서', '하려고', '되나요'\
                  '될까', '도', '글', '하네요', '건']

    possible_tag = ['Noun', 'Verb', 'Number', 'Adjective', 'Adverb']

    #정보 가져오기
    pattern, payload = setConstants()
    query, period, url = data_in() #검색기간, URL
    titles, links, dates, total_num, answer_num = getOuterInfo()
    contents, questions, answers, userInfos, answered_dates = getQnA()

    #제목, 내용 리스트에 추가
    Question_text = make_text(titles, questions)

    #품사 태깅하기
    tagged_text = make_tag(Question_text)

    #필요없는 품사태깅된 단어 없애기
    treated_text = clean_text(tagged_text, possible_tag)

    #불용어 제거하기
    text = remove_stopwords(treated_text)

    #단어 빈도수 측정(빈도수가 많은 단어 100개 추출)
    fd_word, important_words_count = frequency(text, 100)
    print(fd_word)   #important_words_count : 단어+빈도수

    #단어 + 빈도수 출력
    print_wf(important_words_count)

    #워드클라우드
    final_words = make_wordcloud(important_words_count, 30)

    #히스토그램
    make_graph(final_words)

